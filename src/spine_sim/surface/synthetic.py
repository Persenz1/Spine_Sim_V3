"""Coordinate-anchored hierarchical self-affine Gaussian surfaces.

The evaluator represents a periodic 150 mm parent as a deterministic sum of
real Fourier mode pairs.  Low frequencies use every lattice pair when small;
higher octaves use a frozen area-weighted representative lattice.  This is the
random-access spectral alternative allowed by the M01 contract: evaluation is
local, has no full-domain fine grid or dense FFT, and a tile/crop/order never
enters either the random key or normalization.

For one representative half-plane mode ``q`` the field contribution is

``a_q cos(q.x) + b_q sin(q.x)``,

where ``a_q`` and ``b_q`` are independent keyed normals.  Its ensemble point
variance is therefore the mode's target weight.  The omitted conjugate mode is
implicit, making Hermitian and imaginary residuals exactly zero by
construction.  Analytic derivatives follow from the same modes.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .contracts import (
    GENERATOR_ID,
    GENERATOR_VERSION,
    LOGICAL_PARENT_SIZE_MM,
    LatentNoiseIdentity,
    QualityStatus,
    RoughnessTier,
    StatisticsScope,
    SurfaceFamily,
    SurfaceSourceKind,
    SurfaceSpec,
    TrustedScaleBand,
)
from .rng import Philox4x64

__all__ = [
    "DirectionalSpectrumStatistic",
    "OmittedBandBounds",
    "PSDStatistic",
    "SpectralBandManifest",
    "SpectralStatistics",
    "SyntheticEvaluation",
    "SyntheticEvaluator",
    "SyntheticParameters",
    "synthetic_parameters_for_tier",
    "validate_synthetic_parameters",
]

_NORMALIZATION_PROFILE = "M01_ZERO_DC_ENSEMBLE_SQ_1"
_QUADRATURE_PROFILE = "M01_PERIODIC_OCTAVE_REPRESENTATIVE_LATTICE_1"
_REAL_CONSTRUCTION_RULE = "a*cos(q.x)+b*sin(q.x); implicit conjugate pair"
_COEFFICIENT_ROLE = "real_fourier_cos_sin_pair_v1"
_DEFAULT_REFERENCE_RT_MM = 0.05
_DEFAULT_MODES_PER_BAND = 32
_BAND_RATIO = 2.0
_EVALUATION_CHUNK_POINTS = 65_536
_DIRECTION_BIN_COUNT = 12
_MISSING = object()

_TIER_DEFAULTS: dict[RoughnessTier, tuple[float, float, float]] = {
    RoughnessTier.GENTLE: (0.9, 0.25, 80.0),
    RoughnessTier.MEDIUM: (0.7, 1.0, 20.0),
    RoughnessTier.SHARP: (0.5, 4.0, 5.0),
}


def _finite_float(value: Any, field_name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be a real number")
    try:
        converted = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{field_name} must be a real number") from exc
    if not math.isfinite(converted):
        raise ValueError(f"{field_name} must be finite")
    return converted


def _pick(parameters: Mapping[str, Any], *names: str, default: Any = _MISSING) -> Any:
    for name in names:
        if name in parameters:
            return parameters[name]
    if default is _MISSING:
        joined = " or ".join(names)
        raise ValueError(f"missing required synthetic parameter: {joined}")
    return default


def _as_tier(value: RoughnessTier | str) -> RoughnessTier:
    if isinstance(value, RoughnessTier):
        return value
    try:
        return RoughnessTier(str(value))
    except ValueError as exc:
        allowed = ", ".join(item.value for item in RoughnessTier)
        raise ValueError(f"roughness_tier must be one of {allowed}") from exc


def synthetic_parameters_for_tier(
    tier: RoughnessTier | str = RoughnessTier.MEDIUM,
    *,
    surface_scale_reference_Rt_mm: float = _DEFAULT_REFERENCE_RT_MM,
    reference_rt_mm: float | None = None,
    anisotropy_ratio: float = 1.0,
    anisotropy_direction_rad: float | None = None,
    lambda_min_declared_trust_mm: float | None = None,
    modes_per_band: int = _DEFAULT_MODES_PER_BAND,
) -> dict[str, Any]:
    """Materialize one frozen DEV tier as explicit, identity-ready parameters.

    The result contains both dimensionless policy inputs and their absolute
    millimetre values.  It does not contain a seed and never assigns a material
    name.  ``reference_rt_mm`` is accepted as a concise alias; the reference is
    a surface scale and is not a query probe radius.
    """

    selected = _as_tier(tier)
    if selected is RoughnessTier.EXPLICIT:
        raise ValueError("the explicit tier requires caller-supplied H, Sq, and lc")
    if reference_rt_mm is not None:
        alias = _finite_float(reference_rt_mm, "reference_rt_mm")
        declared = _finite_float(
            surface_scale_reference_Rt_mm,
            "surface_scale_reference_Rt_mm",
        )
        if surface_scale_reference_Rt_mm != _DEFAULT_REFERENCE_RT_MM and not math.isclose(
            alias, declared, rel_tol=0.0, abs_tol=0.0
        ):
            raise ValueError("reference_rt_mm aliases a conflicting reference value")
        surface_scale_reference_Rt_mm = alias
    reference = _finite_float(
        surface_scale_reference_Rt_mm,
        "surface_scale_reference_Rt_mm",
    )
    if reference <= 0.0:
        raise ValueError("surface_scale_reference_Rt_mm must be positive")
    H, sq_ratio, lc_ratio = _TIER_DEFAULTS[selected]
    wavelength = (
        reference / 2.0
        if lambda_min_declared_trust_mm is None
        else _finite_float(
            lambda_min_declared_trust_mm,
            "lambda_min_declared_trust_mm",
        )
    )
    if wavelength <= 0.0:
        raise ValueError("lambda_min_declared_trust_mm must be positive")
    q_min = math.tau / LOGICAL_PARENT_SIZE_MM
    q_max = math.tau / wavelength
    return {
        "H": H,
        "Sq_mm": sq_ratio * reference,
        "Sq_over_reference_Rt": sq_ratio,
        "anisotropy_direction_rad": anisotropy_direction_rad,
        "anisotropy_ratio": anisotropy_ratio,
        "band_ratio": _BAND_RATIO,
        "lc_mm": lc_ratio * reference,
        "lc_over_reference_Rt": lc_ratio,
        "lambda_min_declared_trust_mm": wavelength,
        "modes_per_band": modes_per_band,
        "normalization_profile": _NORMALIZATION_PROFILE,
        "q_max_rad_per_mm": q_max,
        "q_min_rad_per_mm": q_min,
        "quadrature_profile": _QUADRATURE_PROFILE,
        "roughness_tier": selected.value,
        "surface_scale_reference_Rt_mm": reference,
    }


@dataclass(frozen=True, slots=True)
class SyntheticParameters:
    """Validated physical/filter definition of one synthetic realization."""

    roughness_tier: RoughnessTier
    H: float
    Sq_mm: float
    lc_mm: float
    surface_scale_reference_Rt_mm: float
    Sq_over_reference_Rt: float
    lc_over_reference_Rt: float
    anisotropy_ratio: float
    anisotropy_direction_rad: float | None
    q_min_rad_per_mm: float
    q_max_rad_per_mm: float
    lambda_min_declared_trust_mm: float
    normalization_profile: str
    quadrature_profile: str
    modes_per_band: int
    band_ratio: float

    @property
    def target_variance_mm2(self) -> float:
        return self.Sq_mm * self.Sq_mm

    @property
    def direction_for_filter_rad(self) -> float:
        return 0.0 if self.anisotropy_direction_rad is None else self.anisotropy_direction_rad


def validate_synthetic_parameters(
    parameters_or_spec: Mapping[str, Any] | SurfaceSpec,
) -> SyntheticParameters:
    """Resolve and strictly validate a synthetic parameter mapping or spec."""

    if isinstance(parameters_or_spec, SurfaceSpec):
        spec = parameters_or_spec
        if spec.source_kind is not SurfaceSourceKind.SYNTHETIC:
            raise ValueError("SyntheticEvaluator requires a synthetic SurfaceSpec")
        if spec.family is not SurfaceFamily.SELF_AFFINE_GAUSSIAN:
            raise ValueError("SyntheticEvaluator only supports self_affine_gaussian")
        if spec.generator_id != GENERATOR_ID or spec.generator_version != GENERATOR_VERSION:
            raise ValueError("synthetic spec uses an unsupported generator ID or version")
        parameters: Mapping[str, Any] = spec.parameter_map()
    elif isinstance(parameters_or_spec, Mapping):
        parameters = parameters_or_spec
    else:
        raise TypeError("synthetic parameters must be a mapping or SurfaceSpec")

    tier = _as_tier(_pick(parameters, "roughness_tier", default=RoughnessTier.EXPLICIT))
    defaults = _TIER_DEFAULTS.get(tier)
    default_H = defaults[0] if defaults is not None else _MISSING
    default_sq_ratio = defaults[1] if defaults is not None else _MISSING
    default_lc_ratio = defaults[2] if defaults is not None else _MISSING

    H = _finite_float(_pick(parameters, "H", "hurst_exponent", default=default_H), "H")
    if not 0.0 < H < 1.0:
        raise ValueError("H must lie strictly between zero and one")

    reference = _finite_float(
        _pick(
            parameters,
            "surface_scale_reference_Rt_mm",
            "reference_Rt_mm",
            "reference_rt_mm",
            default=_DEFAULT_REFERENCE_RT_MM,
        ),
        "surface_scale_reference_Rt_mm",
    )
    if reference <= 0.0:
        raise ValueError("surface_scale_reference_Rt_mm must be positive")

    sq_direct = _pick(parameters, "Sq_mm", "target_Sq_mm", default=None)
    if sq_direct is None:
        sq_ratio = _finite_float(
            _pick(
                parameters,
                "Sq_over_reference_Rt",
                "sq_over_reference_rt",
                default=default_sq_ratio,
            ),
            "Sq_over_reference_Rt",
        )
        Sq_mm = sq_ratio * reference
    else:
        Sq_mm = _finite_float(sq_direct, "Sq_mm")
        sq_ratio = Sq_mm / reference
    if Sq_mm <= 0.0 or sq_ratio <= 0.0:
        raise ValueError("Sq and Sq_over_reference_Rt must be positive")

    lc_direct = _pick(parameters, "lc_mm", "correlation_length_mm", default=None)
    if lc_direct is None:
        lc_ratio = _finite_float(
            _pick(
                parameters,
                "lc_over_reference_Rt",
                "lc_over_reference_rt",
                default=default_lc_ratio,
            ),
            "lc_over_reference_Rt",
        )
        lc_mm = lc_ratio * reference
    else:
        lc_mm = _finite_float(lc_direct, "lc_mm")
        lc_ratio = lc_mm / reference
    if lc_mm <= 0.0 or lc_ratio <= 0.0:
        raise ValueError("lc and lc_over_reference_Rt must be positive")

    ratio = _finite_float(
        _pick(parameters, "anisotropy_ratio", default=1.0),
        "anisotropy_ratio",
    )
    if ratio < 1.0:
        raise ValueError("anisotropy_ratio must be at least one")
    direction_raw = _pick(parameters, "anisotropy_direction_rad", default=None)
    if direction_raw is None:
        direction = None
    else:
        direction = _finite_float(direction_raw, "anisotropy_direction_rad")
        direction %= math.pi
    if ratio > 1.0 and direction is None:
        raise ValueError("anisotropic surfaces require anisotropy_direction_rad")
    if ratio == 1.0:
        # Direction is semantically N/A for an isotropic spectrum.
        direction = None

    fundamental_q = math.tau / LOGICAL_PARENT_SIZE_MM
    q_min = _finite_float(
        _pick(parameters, "q_min_rad_per_mm", "q_min", default=fundamental_q),
        "q_min_rad_per_mm",
    )
    if q_min < fundamental_q * (1.0 - 1.0e-14):
        raise ValueError("q_min cannot be below the 150 mm parent fundamental")

    wavelength_raw = _pick(parameters, "lambda_min_declared_trust_mm", default=None)
    q_max_raw = _pick(parameters, "q_max_rad_per_mm", "q_max", default=None)
    if q_max_raw is None and wavelength_raw is None:
        wavelength = reference / 2.0
        q_max = math.tau / wavelength
    elif q_max_raw is None:
        wavelength = _finite_float(wavelength_raw, "lambda_min_declared_trust_mm")
        if wavelength <= 0.0:
            raise ValueError("lambda_min_declared_trust_mm must be positive")
        q_max = math.tau / wavelength
    else:
        q_max = _finite_float(q_max_raw, "q_max_rad_per_mm")
        if q_max <= 0.0:
            raise ValueError("q_max_rad_per_mm must be positive")
        wavelength = math.tau / q_max
        if wavelength_raw is not None:
            declared_wavelength = _finite_float(
                wavelength_raw,
                "lambda_min_declared_trust_mm",
            )
            if not math.isclose(
                declared_wavelength,
                wavelength,
                rel_tol=2.0e-13,
                abs_tol=0.0,
            ):
                raise ValueError("q_max and lambda_min_declared_trust_mm disagree")
    if q_max <= q_min:
        raise ValueError("q_max must be strictly greater than q_min")
    if q_max / fundamental_q >= 1 << 62:
        raise ValueError("q_max exceeds the signed lattice-coordinate profile")

    normalization = str(_pick(parameters, "normalization_profile", default=_NORMALIZATION_PROFILE))
    if normalization != _NORMALIZATION_PROFILE:
        raise ValueError(f"unsupported normalization_profile: {normalization}")
    quadrature = str(_pick(parameters, "quadrature_profile", default=_QUADRATURE_PROFILE))
    if quadrature != _QUADRATURE_PROFILE:
        raise ValueError(f"unsupported quadrature_profile: {quadrature}")

    modes_raw = _pick(parameters, "modes_per_band", default=_DEFAULT_MODES_PER_BAND)
    if isinstance(modes_raw, bool) or not isinstance(modes_raw, int):
        raise TypeError("modes_per_band must be an integer")
    if not 4 <= modes_raw <= 512:
        raise ValueError("modes_per_band must lie in [4, 512]")
    band_ratio = _finite_float(
        _pick(parameters, "band_ratio", default=_BAND_RATIO),
        "band_ratio",
    )
    if band_ratio != _BAND_RATIO:
        raise ValueError("M01 generator version 1 freezes band_ratio at 2")

    return SyntheticParameters(
        roughness_tier=tier,
        H=H,
        Sq_mm=Sq_mm,
        lc_mm=lc_mm,
        surface_scale_reference_Rt_mm=reference,
        Sq_over_reference_Rt=sq_ratio,
        lc_over_reference_Rt=lc_ratio,
        anisotropy_ratio=ratio,
        anisotropy_direction_rad=direction,
        q_min_rad_per_mm=q_min,
        q_max_rad_per_mm=q_max,
        lambda_min_declared_trust_mm=wavelength,
        normalization_profile=normalization,
        quadrature_profile=quadrature,
        modes_per_band=modes_raw,
        band_ratio=band_ratio,
    )


@dataclass(frozen=True, slots=True)
class SpectralBandManifest:
    """Complete numerical definition and realized summary of one octave band."""

    band_id: int
    q_min_rad_per_mm: float
    q_max_rad_per_mm: float
    lambda_max_mm: float
    lambda_min_mm: float
    mode_count: int
    first_mode_ordinal: int
    last_mode_ordinal_exclusive: int
    global_mode_coordinate_hash: str
    target_variance_mm2: float
    realized_variance_mm2: float
    filter_rule: str
    quadrature_rule: str
    kernel_rule: str
    interpolation_rule: str
    derivative_rule: str
    fft_normalization: str
    spectral_normalization: str
    hermitian_rule: str
    real_construction_rule: str
    truncation_error_bound_mm: float


@dataclass(frozen=True, slots=True)
class PSDStatistic:
    """One integrated radial PSD bin with explicit units."""

    band_id: int
    q_min_rad_per_mm: float
    q_max_rad_per_mm: float
    representative_q_rad_per_mm: float
    psd_mm4: float
    integrated_variance_mm2: float
    mode_count: int


@dataclass(frozen=True, slots=True)
class DirectionalSpectrumStatistic:
    """Half-plane material-axis spectrum bin (directions are pi-periodic)."""

    direction_min_rad: float
    direction_max_rad: float
    integrated_variance_mm2: float
    fraction_of_variance: float
    mode_count: int


@dataclass(frozen=True, slots=True)
class SpectralStatistics:
    """Target and realized coefficient statistics for the complete parent."""

    scopes: tuple[StatisticsScope, ...]
    target_mean_mm: float
    target_Sq_mm: float
    target_variance_mm2: float
    represented_target_variance_mm2: float
    realized_mean_mm: float
    realized_Sq_mm: float
    realized_variance_mm2: float
    zero_mode_coefficient_mm: float
    target_psd: tuple[PSDStatistic, ...]
    realized_psd: tuple[PSDStatistic, ...]
    target_directional_spectrum: tuple[DirectionalSpectrumStatistic, ...]
    realized_directional_spectrum: tuple[DirectionalSpectrumStatistic, ...]
    coefficient_pair_count: int
    hermitian_relative_residual: float
    imaginary_relative_residual: float
    parseval_variance_mm2: float
    parseval_absolute_error_mm2: float
    parseval_relative_error: float
    target_normalization_relative_error: float
    psd_units: str
    wavenumber_units: str
    fft_normalization: str
    real_construction_rule: str

    @property
    def real_valued_relative_error(self) -> float:
        return self.imaginary_relative_residual

    @property
    def variance_parseval_relative_error(self) -> float:
        return self.parseval_relative_error


@dataclass(frozen=True, slots=True)
class OmittedBandBounds:
    """Conservative coefficient-amplitude bounds above a requested cutoff."""

    q_cutoff_rad_per_mm: float
    omitted_mode_count: int
    height_bound_mm: float
    slope_bound: float
    hessian_bound_per_mm: float


@dataclass(frozen=True, slots=True)
class SyntheticEvaluation:
    """Flattened random-access values and analytic derivatives.

    ``query_shape`` records the broadcast input shape.  Flattening gives one
    unambiguous ``N``, ``N x 2``, and ``N x 2 x 2`` contract for scalar, point
    batch, and grid callers.  Iteration yields ``height, gradient, hessian`` for
    concise tuple-style use.
    """

    height: NDArray[np.float64]
    gradient: NDArray[np.float64] | None
    hessian: NDArray[np.float64] | None
    query_shape: tuple[int, ...]
    q_max_rad_per_mm: float
    active_band_ids: tuple[int, ...]
    omitted_bounds: OmittedBandBounds

    def __post_init__(self) -> None:
        height = np.array(self.height, dtype=np.float64, copy=True)
        if height.ndim != 1 or not np.isfinite(height).all():
            raise ValueError("synthetic height must be a finite flat float64 array")
        height.setflags(write=False)
        object.__setattr__(self, "height", height)
        if self.gradient is not None:
            gradient = np.array(self.gradient, dtype=np.float64, copy=True)
            if gradient.shape != (height.size, 2) or not np.isfinite(gradient).all():
                raise ValueError("synthetic gradient must have shape (N, 2)")
            gradient.setflags(write=False)
            object.__setattr__(self, "gradient", gradient)
        if self.hessian is not None:
            hessian = np.array(self.hessian, dtype=np.float64, copy=True)
            if hessian.shape != (height.size, 2, 2) or not np.isfinite(hessian).all():
                raise ValueError("synthetic Hessian must have shape (N, 2, 2)")
            hessian.setflags(write=False)
            object.__setattr__(self, "hessian", hessian)
        expected_size = math.prod(self.query_shape) if self.query_shape else 1
        if expected_size != height.size:
            raise ValueError("query_shape does not match flattened evaluation cardinality")

    def __iter__(
        self,
    ) -> Iterator[NDArray[np.float64] | None,]:
        yield self.height
        yield self.gradient
        yield self.hessian

    def height_in_query_shape(self) -> NDArray[np.float64]:
        return self.height.reshape(self.query_shape)


@dataclass(frozen=True, slots=True)
class _SelectedBand:
    band_id: int
    q_min: float
    q_max: float
    coordinates: tuple[tuple[int, int], ...]
    multiplicity: float


def _in_half_plane(mode_x: int, mode_y: int) -> bool:
    return mode_y > 0 or (mode_y == 0 and mode_x > 0)


def _enumerated_band_coordinates(
    radius_min: float,
    radius_max: float,
    *,
    include_upper: bool,
) -> tuple[tuple[int, int], ...]:
    limit = math.ceil(radius_max)
    selected: list[tuple[int, int]] = []
    low_squared = radius_min * radius_min
    high_squared = radius_max * radius_max
    tolerance = 4.0 * np.finfo(np.float64).eps * max(1.0, high_squared)
    for mode_y in range(0, limit + 1):
        for mode_x in range(-limit, limit + 1):
            if not _in_half_plane(mode_x, mode_y):
                continue
            radius_squared = mode_x * mode_x + mode_y * mode_y
            above_low = radius_squared + tolerance >= low_squared
            below_high = (
                radius_squared <= high_squared + tolerance
                if include_upper
                else radius_squared < high_squared - tolerance
            )
            if above_low and below_high:
                selected.append((mode_x, mode_y))
    selected.sort(key=lambda item: (item[0] * item[0] + item[1] * item[1], item[1], item[0]))
    return tuple(selected)


def _representative_band_coordinates(
    radius_min: float,
    radius_max: float,
    count: int,
    band_id: int,
    *,
    include_upper: bool,
) -> tuple[tuple[int, int], ...]:
    # Area-stratified radii and a low-discrepancy angular sequence.  Neither
    # surface filters nor random values enter this frozen lattice selection.
    golden_fraction = (math.sqrt(5.0) - 1.0) / 2.0
    selected: set[tuple[int, int]] = set()
    attempts = 0
    maximum_attempts = max(4096, count * 256)
    low_squared = radius_min * radius_min
    high_squared = radius_max * radius_max
    while len(selected) < count and attempts < maximum_attempts:
        stratum = attempts % count
        cycle = attempts // count
        fraction = (stratum + 0.5 + 0.17320508075688773 * cycle) / count
        fraction %= 1.0
        radius = math.sqrt(low_squared + (high_squared - low_squared) * fraction)
        angular_fraction = (
            (attempts + 1) * golden_fraction + (band_id + 1) * 0.13750352374993502
        ) % 1.0
        angle = math.pi * angular_fraction
        mode_x = round(radius * math.cos(angle))
        mode_y = round(radius * math.sin(angle))
        if _in_half_plane(mode_x, mode_y):
            radius_actual = math.hypot(mode_x, mode_y)
            below_upper = (
                radius_actual <= radius_max if include_upper else radius_actual < radius_max
            )
            if radius_min <= radius_actual and below_upper:
                selected.add((mode_x, mode_y))
        attempts += 1
    if not selected:
        raise RuntimeError("failed to select any global mode in a spectral band")
    return tuple(
        sorted(
            selected,
            key=lambda item: (item[0] * item[0] + item[1] * item[1], item[1], item[0]),
        )
    )


def _select_bands(parameters: SyntheticParameters) -> tuple[_SelectedBand, ...]:
    fundamental_q = math.tau / LOGICAL_PARENT_SIZE_MM
    bands: list[_SelectedBand] = []
    q_low = parameters.q_min_rad_per_mm
    band_id = 0
    while q_low < parameters.q_max_rad_per_mm * (1.0 - 8.0e-16):
        q_high = min(q_low * parameters.band_ratio, parameters.q_max_rad_per_mm)
        radius_min = q_low / fundamental_q
        radius_max = q_high / fundamental_q
        include_upper = math.isclose(
            q_high,
            parameters.q_max_rad_per_mm,
            rel_tol=8.0e-16,
            abs_tol=0.0,
        )
        exact: tuple[tuple[int, int], ...] = ()
        # Enumeration is bounded independently of q_max, and is used only when
        # the complete band fits the frozen representative budget.
        if radius_max <= 20.0:
            candidate = _enumerated_band_coordinates(
                radius_min,
                radius_max,
                include_upper=include_upper,
            )
            if len(candidate) <= parameters.modes_per_band:
                exact = candidate
        if exact:
            coordinates = exact
            multiplicity = 1.0
        else:
            approximate_pair_count = max(
                1.0,
                0.5 * math.pi * (radius_max * radius_max - radius_min * radius_min),
            )
            requested_count = min(
                parameters.modes_per_band,
                max(1, math.ceil(approximate_pair_count)),
            )
            coordinates = _representative_band_coordinates(
                radius_min,
                radius_max,
                requested_count,
                band_id,
                include_upper=include_upper,
            )
            multiplicity = approximate_pair_count / len(coordinates)
        bands.append(
            _SelectedBand(
                band_id,
                q_low,
                q_high,
                coordinates,
                multiplicity,
            )
        )
        q_low = q_high
        band_id += 1
        if band_id > 128:
            raise ValueError("synthetic q range would require more than 128 octave bands")
    return tuple(bands)


def _readonly(array: NDArray[np.float64] | NDArray[np.int64]) -> None:
    array.setflags(write=False)


class SyntheticEvaluator:
    """Immutable random-access evaluator for one synthetic surface definition."""

    __slots__ = (
        "_amplitude_cos",
        "_amplitude_sin",
        "_band_ids",
        "_mode_coordinates",
        "_mode_q",
        "_qx",
        "_qy",
        "_spectral_measure",
        "_target_mode_variance",
        "band_manifests",
        "latent_identity",
        "parameters",
        "spec",
        "statistics",
    )

    def __init__(self, spec: SurfaceSpec, latent_identity: LatentNoiseIdentity) -> None:
        self.spec = spec
        self.latent_identity = latent_identity
        self.parameters = validate_synthetic_parameters(spec)
        selected_bands = _select_bands(self.parameters)

        mode_coordinates: list[tuple[int, int]] = []
        band_ids: list[int] = []
        multiplicities: list[float] = []
        for band in selected_bands:
            mode_coordinates.extend(band.coordinates)
            band_ids.extend([band.band_id] * len(band.coordinates))
            multiplicities.extend([band.multiplicity] * len(band.coordinates))
        if not mode_coordinates:
            raise ValueError("the declared q band contains no parent-periodic mode")

        coordinate_array = np.asarray(mode_coordinates, dtype=np.int64)
        band_array = np.asarray(band_ids, dtype=np.int64)
        fundamental_q = math.tau / LOGICAL_PARENT_SIZE_MM
        qx = coordinate_array[:, 0].astype(np.float64) * fundamental_q
        qy = coordinate_array[:, 1].astype(np.float64) * fundamental_q
        mode_q = np.hypot(qx, qy)

        theta = self.parameters.direction_for_filter_rad
        cosine = math.cos(theta)
        sine = math.sin(theta)
        q_parallel = cosine * qx + sine * qy
        q_perpendicular = -sine * qx + cosine * qy
        ratio_root = math.sqrt(self.parameters.anisotropy_ratio)
        length_parallel = self.parameters.lc_mm * ratio_root
        length_perpendicular = self.parameters.lc_mm / ratio_root
        q_effective_squared = (length_parallel * q_parallel) ** 2 + (
            length_perpendicular * q_perpendicular
        ) ** 2
        unnormalized_psd = (1.0 + q_effective_squared) ** (-(1.0 + self.parameters.H))

        # One representative stands for ``multiplicity`` conjugate lattice
        # pairs.  The factor two is the +/-q measure of a half-plane pair.
        spectral_measure = (
            2.0
            * np.asarray(multiplicities, dtype=np.float64)
            * fundamental_q
            * fundamental_q
            / (math.tau * math.tau)
        )
        raw_mode_variance = unnormalized_psd * spectral_measure
        raw_total = float(np.sum(raw_mode_variance, dtype=np.float64))
        if not math.isfinite(raw_total) or raw_total <= 0.0:
            raise ValueError("synthetic PSD normalization has no finite positive mass")
        psd_scale = self.parameters.target_variance_mm2 / raw_total
        target_mode_variance = raw_mode_variance * psd_scale

        amplitude_cos = np.empty(target_mode_variance.size, dtype=np.float64)
        amplitude_sin = np.empty(target_mode_variance.size, dtype=np.float64)
        rngs = {
            band.band_id: Philox4x64.from_latent_identity(
                latent_identity,
                band.band_id,
                _COEFFICIENT_ROLE,
            )
            for band in selected_bands
        }
        for index, ((mode_x, mode_y), band_id) in enumerate(
            zip(mode_coordinates, band_ids, strict=True)
        ):
            normal_cos, normal_sin = rngs[band_id].normal_pair(mode_x, mode_y)
            standard_deviation = math.sqrt(float(target_mode_variance[index]))
            amplitude_cos[index] = standard_deviation * normal_cos
            amplitude_sin[index] = standard_deviation * normal_sin

        for array in (
            coordinate_array,
            band_array,
            qx,
            qy,
            mode_q,
            spectral_measure,
            target_mode_variance,
            amplitude_cos,
            amplitude_sin,
        ):
            _readonly(array)
        self._mode_coordinates = coordinate_array
        self._band_ids = band_array
        self._qx = qx
        self._qy = qy
        self._mode_q = mode_q
        self._spectral_measure = spectral_measure
        self._target_mode_variance = target_mode_variance
        self._amplitude_cos = amplitude_cos
        self._amplitude_sin = amplitude_sin

        realized_mode_variance = 0.5 * (amplitude_cos**2 + amplitude_sin**2)
        self.band_manifests = self._make_band_manifests(
            selected_bands,
            realized_mode_variance,
        )
        self.statistics = self._make_statistics(psd_scale, realized_mode_variance)

    @property
    def mode_count(self) -> int:
        return int(self._mode_q.size)

    @property
    def mode_coordinates(self) -> NDArray[np.int64]:
        """Read-only ``(mode_x, mode_y)`` global lattice coordinates."""

        return self._mode_coordinates

    @property
    def target_mode_variance_mm2(self) -> NDArray[np.float64]:
        return self._target_mode_variance

    @property
    def coefficient_cos_mm(self) -> NDArray[np.float64]:
        return self._amplitude_cos

    @property
    def coefficient_sin_mm(self) -> NDArray[np.float64]:
        return self._amplitude_sin

    @property
    def trusted_bands(self) -> tuple[TrustedScaleBand, ...]:
        """Typed trust bands derived from the immutable spectral definition."""

        return tuple(
            TrustedScaleBand(
                band_id=f"band-{band.band_id:02d}",
                q_min_rad_per_mm=band.q_min_rad_per_mm,
                q_max_rad_per_mm=band.q_max_rad_per_mm,
                lambda_max_mm=band.lambda_max_mm,
                lambda_min_mm=band.lambda_min_mm,
                direction_rad=self.parameters.anisotropy_direction_rad,
                uncertainty_bound_mm=band.truncation_error_bound_mm,
                status=QualityStatus.TRUSTED_FOR_DECLARED_SCALE,
            )
            for band in self.band_manifests
        )

    @property
    def definition_manifest(self) -> dict[str, Any]:
        """Identity-bearing generator rules without any materialized query grid."""

        return {
            "generator_id": self.spec.generator_id,
            "generator_version": self.spec.generator_version,
            "latent_noise_id": self.latent_identity.latent_noise_id,
            "normalization_profile": self.parameters.normalization_profile,
            "quadrature_profile": self.parameters.quadrature_profile,
            "zero_mode": "exactly_zero",
            "hermitian_rule": "implicit_exact_conjugate_pairs",
            "real_construction_rule": _REAL_CONSTRUCTION_RULE,
            "derivative_rule": "analytic_periodic_fourier_derivatives",
            "bands": self.band_manifests,
        }

    def _make_band_manifests(
        self,
        selected_bands: tuple[_SelectedBand, ...],
        realized_mode_variance: NDArray[np.float64],
    ) -> tuple[SpectralBandManifest, ...]:
        manifests: list[SpectralBandManifest] = []
        for band in selected_bands:
            indices = np.flatnonzero(self._band_ids == band.band_id)
            first = int(indices[0])
            last = int(indices[-1]) + 1
            coordinate_hash = hashlib.sha256(
                b"M01_GLOBAL_MODE_COORDINATES_1\x00"
                + self._mode_coordinates[first:last].astype("<i8", copy=False).tobytes(order="C")
            ).hexdigest()
            manifests.append(
                SpectralBandManifest(
                    band_id=band.band_id,
                    q_min_rad_per_mm=band.q_min,
                    q_max_rad_per_mm=band.q_max,
                    lambda_max_mm=math.tau / band.q_min,
                    lambda_min_mm=math.tau / band.q_max,
                    mode_count=last - first,
                    first_mode_ordinal=first,
                    last_mode_ordinal_exclusive=last,
                    global_mode_coordinate_hash=coordinate_hash,
                    target_variance_mm2=float(
                        np.sum(self._target_mode_variance[first:last], dtype=np.float64)
                    ),
                    realized_variance_mm2=float(
                        np.sum(realized_mode_variance[first:last], dtype=np.float64)
                    ),
                    filter_rule=(
                        "C=A*[1+(lc*sqrt(r)*q_parallel)^2+(lc/sqrt(r)*q_perpendicular)^2]^(-(1+H))"
                    ),
                    quadrature_rule=self.parameters.quadrature_profile,
                    kernel_rule="not_applicable_direct_periodic_fourier_modes",
                    interpolation_rule="not_applicable_continuous_mode_evaluation",
                    derivative_rule="analytic_first_and_second_fourier_derivatives",
                    fft_normalization="no_fft; explicit real-mode sum",
                    spectral_normalization=(
                        "variance=sum_half_plane(mode_variance); C integral uses dqx*dqy/(2*pi)^2"
                    ),
                    hermitian_rule="negative mode coefficient is exact conjugate",
                    real_construction_rule=_REAL_CONSTRUCTION_RULE,
                    truncation_error_bound_mm=0.0,
                )
            )
        return tuple(manifests)

    def _psd_statistics(
        self,
        mode_variance: NDArray[np.float64],
    ) -> tuple[PSDStatistic, ...]:
        bins: list[PSDStatistic] = []
        for manifest in self.band_manifests:
            start = manifest.first_mode_ordinal
            stop = manifest.last_mode_ordinal_exclusive
            variance = float(np.sum(mode_variance[start:stop], dtype=np.float64))
            measure = float(np.sum(self._spectral_measure[start:stop], dtype=np.float64))
            weighted_q = float(
                np.sum(
                    self._mode_q[start:stop] * self._spectral_measure[start:stop],
                    dtype=np.float64,
                )
                / measure
            )
            bins.append(
                PSDStatistic(
                    band_id=manifest.band_id,
                    q_min_rad_per_mm=manifest.q_min_rad_per_mm,
                    q_max_rad_per_mm=manifest.q_max_rad_per_mm,
                    representative_q_rad_per_mm=weighted_q,
                    psd_mm4=variance / measure,
                    integrated_variance_mm2=variance,
                    mode_count=stop - start,
                )
            )
        return tuple(bins)

    def _directional_statistics(
        self,
        mode_variance: NDArray[np.float64],
    ) -> tuple[DirectionalSpectrumStatistic, ...]:
        angles = np.mod(np.arctan2(self._qy, self._qx), math.pi)
        width = math.pi / _DIRECTION_BIN_COUNT
        total = float(np.sum(mode_variance, dtype=np.float64))
        bins: list[DirectionalSpectrumStatistic] = []
        for index in range(_DIRECTION_BIN_COUNT):
            low = index * width
            high = (index + 1) * width
            if index == _DIRECTION_BIN_COUNT - 1:
                mask = (angles >= low) & (angles <= high)
            else:
                mask = (angles >= low) & (angles < high)
            variance = float(np.sum(mode_variance[mask], dtype=np.float64))
            bins.append(
                DirectionalSpectrumStatistic(
                    direction_min_rad=low,
                    direction_max_rad=high,
                    integrated_variance_mm2=variance,
                    fraction_of_variance=0.0 if total == 0.0 else variance / total,
                    mode_count=int(np.count_nonzero(mask)),
                )
            )
        return tuple(bins)

    def _make_statistics(
        self,
        psd_scale: float,
        realized_mode_variance: NDArray[np.float64],
    ) -> SpectralStatistics:
        del psd_scale  # The scaled per-mode variance is the canonical record.
        represented_target = float(np.sum(self._target_mode_variance, dtype=np.float64))
        realized_variance = float(np.sum(realized_mode_variance, dtype=np.float64))
        # In the implicit complex representation c+=(a-i*b)/2 and c-=conj(c+),
        # hence sum |c|^2 over both half-planes equals this same expression.
        parseval_variance = float(
            np.sum(
                0.5 * (self._amplitude_cos**2 + self._amplitude_sin**2),
                dtype=np.float64,
            )
        )
        parseval_error = abs(parseval_variance - realized_variance)
        target_variance = self.parameters.target_variance_mm2
        return SpectralStatistics(
            scopes=(
                StatisticsScope.TARGET_ANALYTIC,
                StatisticsScope.REALIZED_COEFFICIENT_FULL_PARENT,
            ),
            target_mean_mm=0.0,
            target_Sq_mm=self.parameters.Sq_mm,
            target_variance_mm2=target_variance,
            represented_target_variance_mm2=represented_target,
            realized_mean_mm=0.0,
            realized_Sq_mm=math.sqrt(realized_variance),
            realized_variance_mm2=realized_variance,
            zero_mode_coefficient_mm=0.0,
            target_psd=self._psd_statistics(self._target_mode_variance),
            realized_psd=self._psd_statistics(realized_mode_variance),
            target_directional_spectrum=self._directional_statistics(self._target_mode_variance),
            realized_directional_spectrum=self._directional_statistics(realized_mode_variance),
            coefficient_pair_count=self.mode_count,
            hermitian_relative_residual=0.0,
            imaginary_relative_residual=0.0,
            parseval_variance_mm2=parseval_variance,
            parseval_absolute_error_mm2=parseval_error,
            parseval_relative_error=(
                0.0 if realized_variance == 0.0 else parseval_error / realized_variance
            ),
            target_normalization_relative_error=(
                abs(represented_target - target_variance) / target_variance
            ),
            psd_units="mm^4",
            wavenumber_units="rad/mm",
            fft_normalization="no_fft; C(q)*dqx*dqy/(2*pi)^2",
            real_construction_rule=_REAL_CONSTRUCTION_RULE,
        )

    def omitted_band_bounds(self, q_max_rad_per_mm: float | None) -> OmittedBandBounds:
        """Return deterministic sup-norm bounds for represented modes above cutoff."""

        cutoff = (
            self.parameters.q_max_rad_per_mm
            if q_max_rad_per_mm is None
            else _finite_float(q_max_rad_per_mm, "q_max_rad_per_mm")
        )
        if cutoff < 0.0:
            raise ValueError("q_max_rad_per_mm cannot be negative")
        omitted = self._mode_q > min(cutoff, self.parameters.q_max_rad_per_mm)
        coefficient_radius = np.hypot(
            self._amplitude_cos[omitted],
            self._amplitude_sin[omitted],
        )
        omitted_q = self._mode_q[omitted]
        return OmittedBandBounds(
            q_cutoff_rad_per_mm=cutoff,
            omitted_mode_count=int(np.count_nonzero(omitted)),
            height_bound_mm=float(np.sum(coefficient_radius, dtype=np.float64)),
            slope_bound=float(np.sum(coefficient_radius * omitted_q, dtype=np.float64)),
            hessian_bound_per_mm=float(
                np.sum(coefficient_radius * omitted_q * omitted_q, dtype=np.float64)
            ),
        )

    def evaluate(
        self,
        x: ArrayLike,
        y: ArrayLike,
        derivative_order: int = 2,
        q_max_rad_per_mm: float | None = None,
    ) -> SyntheticEvaluation:
        """Evaluate height and analytic derivatives at arbitrary coordinate arrays.

        Input arrays follow NumPy broadcasting and output is flattened.  The
        periodic canonicalization here belongs to the generator definition; a
        public query handle must still enforce its independent ERROR/PERIODIC
        boundary contract before calling this method.
        """

        if derivative_order not in (0, 1, 2):
            raise ValueError("derivative_order must be 0, 1, or 2")
        x_array = np.asarray(x, dtype=np.float64)
        y_array = np.asarray(y, dtype=np.float64)
        try:
            x_broadcast, y_broadcast = np.broadcast_arrays(x_array, y_array)
        except ValueError as exc:
            raise ValueError("x and y coordinates must be broadcast-compatible") from exc
        if not np.isfinite(x_broadcast).all() or not np.isfinite(y_broadcast).all():
            raise ValueError("synthetic query coordinates must be finite")
        query_shape = x_broadcast.shape
        domain = self.spec.logical_domain
        # Canonicalizing both ends of the parent gives exactly identical mode
        # arguments at periodic equivalents, including x=0 and x=150 mm.
        x_flat = (
            np.remainder(x_broadcast.reshape(-1) - domain.x_min_mm, domain.width_mm)
            + domain.x_min_mm
        )
        y_flat = (
            np.remainder(y_broadcast.reshape(-1) - domain.y_min_mm, domain.height_mm)
            + domain.y_min_mm
        )

        if q_max_rad_per_mm is None:
            cutoff = self.parameters.q_max_rad_per_mm
        else:
            cutoff = _finite_float(q_max_rad_per_mm, "q_max_rad_per_mm")
            if cutoff < 0.0:
                raise ValueError("q_max_rad_per_mm cannot be negative")
            cutoff = min(cutoff, self.parameters.q_max_rad_per_mm)
        active = self._mode_q <= cutoff
        active_indices = np.flatnonzero(active)

        count = x_flat.size
        height = np.zeros(count, dtype=np.float64)
        gradient = np.zeros((count, 2), dtype=np.float64) if derivative_order >= 1 else None
        hessian = np.zeros((count, 2, 2), dtype=np.float64) if derivative_order >= 2 else None

        # The mode loop is deliberately the inner reduction order.  Every point
        # sees the same ordered scalar accumulation regardless of crop size,
        # point order, or chunk boundaries; BLAS batch-dependent reductions are
        # avoided to preserve locked-backend bitwise replay.
        for start in range(0, count, _EVALUATION_CHUNK_POINTS):
            stop = min(start + _EVALUATION_CHUNK_POINTS, count)
            x_chunk = x_flat[start:stop]
            y_chunk = y_flat[start:stop]
            height_chunk = height[start:stop]
            gradient_chunk = None if gradient is None else gradient[start:stop]
            hessian_chunk = None if hessian is None else hessian[start:stop]
            for mode_index in active_indices:
                qx = self._qx[mode_index]
                qy = self._qy[mode_index]
                amplitude_cos = self._amplitude_cos[mode_index]
                amplitude_sin = self._amplitude_sin[mode_index]
                phase = qx * x_chunk + qy * y_chunk
                cosine = np.cos(phase)
                sine = np.sin(phase)
                in_phase = amplitude_cos * cosine + amplitude_sin * sine
                height_chunk += in_phase
                if gradient_chunk is not None:
                    quadrature = -amplitude_cos * sine + amplitude_sin * cosine
                    gradient_chunk[:, 0] += qx * quadrature
                    gradient_chunk[:, 1] += qy * quadrature
                if hessian_chunk is not None:
                    hessian_chunk[:, 0, 0] -= qx * qx * in_phase
                    mixed = -qx * qy * in_phase
                    hessian_chunk[:, 0, 1] += mixed
                    hessian_chunk[:, 1, 0] += mixed
                    hessian_chunk[:, 1, 1] -= qy * qy * in_phase

        active_band_ids = tuple(int(value) for value in np.unique(self._band_ids[active_indices]))
        return SyntheticEvaluation(
            height=height,
            gradient=gradient,
            hessian=hessian,
            query_shape=query_shape,
            q_max_rad_per_mm=cutoff,
            active_band_ids=active_band_ids,
            omitted_bounds=self.omitted_band_bounds(cutoff),
        )

    def evaluate_grid(
        self,
        x_coordinates_mm: ArrayLike,
        y_coordinates_mm: ArrayLike,
        derivative_order: int = 2,
        q_max_rad_per_mm: float | None = None,
    ) -> SyntheticEvaluation:
        """Evaluate the Cartesian product of two one-dimensional coordinates."""

        x_array = np.asarray(x_coordinates_mm, dtype=np.float64)
        y_array = np.asarray(y_coordinates_mm, dtype=np.float64)
        if x_array.ndim != 1 or y_array.ndim != 1:
            raise ValueError("evaluate_grid coordinates must be one-dimensional")
        grid_x, grid_y = np.meshgrid(x_array, y_array, indexing="xy")
        return self.evaluate(
            grid_x,
            grid_y,
            derivative_order=derivative_order,
            q_max_rad_per_mm=q_max_rad_per_mm,
        )
