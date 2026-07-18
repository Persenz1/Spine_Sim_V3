"""Deterministic analytic height-field library for M01.

The functions in this module are pure geometry.  In particular they know
nothing about a needle, a finite cap, contact, friction, force, or material
failure.  Every evaluator is immutable and all returned arrays are detached,
read-only ``float64`` arrays.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, TypedDict

import numpy as np
from numpy.typing import ArrayLike, NDArray

from spine_sim.foundation.canonical import stable_content_id
from spine_sim.foundation.errors import ContractViolation

from .contracts import (
    QUERY_CONTRACT_VERSION,
    BoundaryMode,
    CapabilityEntry,
    CapabilityManifest,
    QueryCapability,
    SurfaceFamily,
    SurfaceSourceKind,
    SurfaceSpec,
    thaw_parameter,
)

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]


@dataclass(frozen=True, slots=True)
class ParameterSchema:
    """Human- and machine-readable parameter contract for one family."""

    required: tuple[str, ...]
    optional: tuple[str, ...]
    aliases: tuple[tuple[str, str], ...]
    domain: str


class _CapabilityCommon(TypedDict):
    """Shared, precisely typed constructor fields for capability entries."""

    method_version: str
    parameter_domain: str
    smoothness: str
    nonsmooth_set: str
    boundary_compatibility: tuple[BoundaryMode, ...]


_COMMON_LOCAL: Final[tuple[str, ...]] = (
    "offset_mm",
    "center_x_mm",
    "center_y_mm",
    "direction_rad",
)

UNIVERSAL_PARAMETER_ALIASES: Final[Mapping[str, str]] = MappingProxyType({"z0_mm": "offset_mm"})


ANALYTIC_PARAMETER_SCHEMAS: Final[Mapping[SurfaceFamily, ParameterSchema]] = MappingProxyType(
    {
        SurfaceFamily.PLANE: ParameterSchema(
            (),
            ("height_mm", "offset_mm"),
            (("height_mm", "offset_mm"),),
            "finite offset_mm",
        ),
        SurfaceFamily.SLOPE_PLANE: ParameterSchema(
            (),
            ("offset_mm", "height_mm", "slope_x", "slope_y"),
            (("height_mm", "offset_mm"),),
            "finite offset and slopes",
        ),
        SurfaceFamily.SINUSOID_1D: ParameterSchema(
            ("amplitude_mm", "wavelength_mm"),
            ("offset_mm", "direction_rad", "phase_rad", "origin_x_mm", "origin_y_mm"),
            (),
            "amplitude_mm >= 0; wavelength_mm > 0; finite angles",
        ),
        SurfaceFamily.SINUSOID_2D: ParameterSchema(
            (),
            (
                "offset_mm",
                "direction_rad",
                "amplitude_mm",
                "wavelength_mm",
                "amplitude_x_mm",
                "amplitude_y_mm",
                "wavelength_x_mm",
                "wavelength_y_mm",
                "phase_x_rad",
                "phase_y_rad",
                "origin_x_mm",
                "origin_y_mm",
            ),
            (),
            "one amplitude and wavelength form (shared or x/y); amplitudes >= 0; wavelengths > 0",
        ),
        SurfaceFamily.GAUSSIAN_BUMP: ParameterSchema(
            ("amplitude_mm",),
            (*_COMMON_LOCAL, "sigma_mm", "sigma_x_mm", "sigma_y_mm"),
            (),
            "amplitude_mm > 0; one positive sigma form",
        ),
        SurfaceFamily.GAUSSIAN_PIT: ParameterSchema(
            ("amplitude_mm",),
            (*_COMMON_LOCAL, "sigma_mm", "sigma_x_mm", "sigma_y_mm"),
            (),
            "amplitude_mm > 0; one positive sigma form",
        ),
        SurfaceFamily.MULTI_GAUSSIAN_FEATURE: ParameterSchema(
            ("features",),
            ("offset_mm",),
            (),
            "non-empty feature sequence; signed finite amplitude_mm and positive sigma",
        ),
        SurfaceFamily.GROOVE_COSINE: ParameterSchema(
            ("depth_mm",),
            (*_COMMON_LOCAL, "half_width_mm", "width_mm"),
            (("width_mm", "half_width_mm"),),
            "depth_mm > 0; half_width_mm > 0",
        ),
        SurfaceFamily.GROOVE_SMOOTH: ParameterSchema(
            ("depth_mm",),
            (*_COMMON_LOCAL, "sigma_mm", "half_width_mm"),
            (),
            "depth_mm > 0; sigma_mm (or half_width_mm scale) > 0",
        ),
        SurfaceFamily.GROOVE_CIRCULAR: ParameterSchema(
            ("depth_mm",),
            (*_COMMON_LOCAL, "half_width_mm", "width_mm"),
            (("width_mm", "half_width_mm"),),
            "0 < depth_mm <= half_width_mm; circular arc joins a plane",
        ),
        SurfaceFamily.GROOVE_V: ParameterSchema(
            ("depth_mm",),
            (*_COMMON_LOCAL, "half_width_mm", "width_mm"),
            (("width_mm", "half_width_mm"),),
            "depth_mm > 0; half_width_mm > 0",
        ),
        SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH: ParameterSchema(
            (),
            (*_COMMON_LOCAL, "ridge_slope", "slope", "switch_tolerance_mm"),
            (("slope", "ridge_slope"),),
            "ridge_slope > 0; switch_tolerance_mm >= 0",
        ),
        SurfaceFamily.SPHERICAL_CAP: ParameterSchema(
            ("radius_mm",),
            ("offset_mm", "center_x_mm", "center_y_mm", "aperture_radius_mm"),
            (),
            "radius_mm > 0; 0 < aperture_radius_mm < radius_mm",
        ),
        SurfaceFamily.SPHERICAL_BOWL: ParameterSchema(
            ("radius_mm",),
            ("offset_mm", "center_x_mm", "center_y_mm", "aperture_radius_mm"),
            (),
            "radius_mm > 0; 0 < aperture_radius_mm < radius_mm",
        ),
    }
)


@dataclass(frozen=True, slots=True)
class AnalyticEvaluation:
    """A cardinality-preserving analytic height/differential evaluation."""

    input_shape: tuple[int, ...]
    height: FloatArray
    points: FloatArray
    gradient: FloatArray
    normal: FloatArray
    hessian: FloatArray | None
    hessian_validity: BoolArray
    principal_curvatures: FloatArray | None
    mean_curvature: FloatArray | None
    gaussian_curvature: FloatArray | None
    curvature_validity: BoolArray
    validity: BoolArray
    nonsmooth_mask: BoolArray
    feature_sets: tuple[tuple[str, ...], ...]
    one_sided_gradients: tuple[tuple[tuple[float, float], ...], ...]
    one_sided_normals: tuple[tuple[tuple[float, float, float], ...], ...]

    def __post_init__(self) -> None:
        for value in (
            self.height,
            self.points,
            self.gradient,
            self.normal,
            self.hessian_validity,
            self.curvature_validity,
            self.validity,
            self.nonsmooth_mask,
        ):
            value.setflags(write=False)
        for optional_value in (
            self.hessian,
            self.principal_curvatures,
            self.mean_curvature,
            self.gaussian_curvature,
        ):
            if optional_value is not None:
                optional_value.setflags(write=False)


def _number(parameters: Mapping[str, Any], name: str, default: float | None = None) -> float:
    if name not in parameters:
        if default is None:
            raise ContractViolation(f"missing analytic parameter: {name}")
        return default
    value = parameters[name]
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ContractViolation(f"analytic parameter {name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ContractViolation(f"analytic parameter {name} must be finite")
    return result


def _apply_aliases(
    family: SurfaceFamily, parameters: Mapping[str, Any], schema: ParameterSchema
) -> dict[str, Any]:
    result = dict(parameters)
    if "z0_mm" in result:
        if "offset_mm" in result or "height_mm" in result:
            raise ContractViolation(
                f"{family.value} parameters cannot combine z0_mm with offset_mm/height_mm"
            )
        result["offset_mm"] = result.pop("z0_mm")
    for alias, canonical in schema.aliases:
        if alias in result and canonical in result:
            raise ContractViolation(
                f"{family.value} parameters cannot contain both {alias} and {canonical}"
            )
        if alias in result:
            value = result.pop(alias)
            if alias == "width_mm" and canonical == "half_width_mm":
                value = _number({alias: value}, alias) / 2.0
            result[canonical] = value
    return result


def _validate_keys(
    family: SurfaceFamily, parameters: Mapping[str, Any], schema: ParameterSchema
) -> None:
    allowed = set(schema.required) | set(schema.optional)
    aliases = {item[0] for item in schema.aliases} | {"z0_mm"}
    unknown = sorted(set(parameters) - allowed - aliases)
    if unknown:
        raise ContractViolation(
            f"unknown {family.value} analytic parameter(s): {', '.join(unknown)}"
        )
    missing = sorted(set(schema.required) - set(parameters))
    if missing:
        raise ContractViolation(
            f"missing {family.value} analytic parameter(s): {', '.join(missing)}"
        )


def _validate_sigma(parameters: dict[str, Any]) -> None:
    shared = "sigma_mm" in parameters
    directional = "sigma_x_mm" in parameters or "sigma_y_mm" in parameters
    if shared and directional:
        raise ContractViolation("sigma_mm cannot be combined with sigma_x_mm/sigma_y_mm")
    if shared:
        sigma = _number(parameters, "sigma_mm")
        parameters["sigma_x_mm"] = sigma
        parameters["sigma_y_mm"] = sigma
        del parameters["sigma_mm"]
    elif directional:
        if "sigma_x_mm" not in parameters or "sigma_y_mm" not in parameters:
            raise ContractViolation("both sigma_x_mm and sigma_y_mm are required")
    else:
        raise ContractViolation("one sigma form is required")
    if _number(parameters, "sigma_x_mm") <= 0.0 or _number(parameters, "sigma_y_mm") <= 0.0:
        raise ContractViolation("Gaussian sigma must be positive")


def validate_analytic_parameters(
    family: SurfaceFamily, parameters: Mapping[str, Any]
) -> MappingProxyType[str, Any]:
    """Validate and normalize a family parameter map.

    Unknown keys and ambiguous aliases are rejected.  Returned defaults are part
    of the evaluator definition but do not rewrite the caller's ``SurfaceSpec``.
    """

    if family not in ANALYTIC_PARAMETER_SCHEMAS:
        raise ContractViolation(f"family is not an M01 analytic family: {family.value}")
    schema = ANALYTIC_PARAMETER_SCHEMAS[family]
    _validate_keys(family, parameters, schema)
    result = _apply_aliases(family, parameters, schema)
    domain_center = 75.0
    result.setdefault("offset_mm", 0.0)

    if family is SurfaceFamily.PLANE:
        pass
    elif family is SurfaceFamily.SLOPE_PLANE:
        result.setdefault("slope_x", 0.0)
        result.setdefault("slope_y", 0.0)
    elif family is SurfaceFamily.SINUSOID_1D:
        if _number(result, "amplitude_mm") < 0.0:
            raise ContractViolation("sinusoid amplitude_mm cannot be negative")
        if _number(result, "wavelength_mm") <= 0.0:
            raise ContractViolation("sinusoid wavelength_mm must be positive")
        result.setdefault("direction_rad", 0.0)
        result.setdefault("phase_rad", 0.0)
        result.setdefault("origin_x_mm", 0.0)
        result.setdefault("origin_y_mm", 0.0)
    elif family is SurfaceFamily.SINUSOID_2D:
        shared_a = "amplitude_mm" in result
        split_a = "amplitude_x_mm" in result or "amplitude_y_mm" in result
        shared_w = "wavelength_mm" in result
        split_w = "wavelength_x_mm" in result or "wavelength_y_mm" in result
        if shared_a == split_a or shared_w == split_w:
            raise ContractViolation(
                "sinusoid_2d requires exactly one shared or x/y amplitude and wavelength form"
            )
        if shared_a:
            amplitude = _number(result, "amplitude_mm")
            result["amplitude_x_mm"] = amplitude
            result["amplitude_y_mm"] = amplitude
            del result["amplitude_mm"]
        elif "amplitude_x_mm" not in result or "amplitude_y_mm" not in result:
            raise ContractViolation("both amplitude_x_mm and amplitude_y_mm are required")
        if shared_w:
            wavelength = _number(result, "wavelength_mm")
            result["wavelength_x_mm"] = wavelength
            result["wavelength_y_mm"] = wavelength
            del result["wavelength_mm"]
        elif "wavelength_x_mm" not in result or "wavelength_y_mm" not in result:
            raise ContractViolation("both wavelength_x_mm and wavelength_y_mm are required")
        if min(_number(result, "amplitude_x_mm"), _number(result, "amplitude_y_mm")) < 0:
            raise ContractViolation("sinusoid amplitudes cannot be negative")
        if min(_number(result, "wavelength_x_mm"), _number(result, "wavelength_y_mm")) <= 0:
            raise ContractViolation("sinusoid wavelengths must be positive")
        result.setdefault("direction_rad", 0.0)
        result.setdefault("phase_x_rad", 0.0)
        result.setdefault("phase_y_rad", 0.0)
        result.setdefault("origin_x_mm", 0.0)
        result.setdefault("origin_y_mm", 0.0)
    elif family in (SurfaceFamily.GAUSSIAN_BUMP, SurfaceFamily.GAUSSIAN_PIT):
        if _number(result, "amplitude_mm") <= 0.0:
            raise ContractViolation("Gaussian bump/pit amplitude_mm must be positive")
        _validate_sigma(result)
        result.setdefault("center_x_mm", domain_center)
        result.setdefault("center_y_mm", domain_center)
        result.setdefault("direction_rad", 0.0)
    elif family is SurfaceFamily.MULTI_GAUSSIAN_FEATURE:
        features = result.get("features")
        if not isinstance(features, Sequence) or isinstance(features, str | bytes) or not features:
            raise ContractViolation("multi_gaussian_feature requires a non-empty feature sequence")
        normalized: list[MappingProxyType[str, Any]] = []
        allowed = {
            "feature_id",
            "amplitude_mm",
            "center_x_mm",
            "center_y_mm",
            "direction_rad",
            "sigma_mm",
            "sigma_x_mm",
            "sigma_y_mm",
        }
        for index, raw in enumerate(features):
            if not isinstance(raw, Mapping):
                raise ContractViolation("each multi-Gaussian feature must be a mapping")
            unknown = sorted(set(raw) - allowed)
            if unknown:
                raise ContractViolation(f"unknown multi-Gaussian feature parameter(s): {unknown}")
            feature = dict(raw)
            amplitude = _number(feature, "amplitude_mm")
            if amplitude == 0.0:
                raise ContractViolation("multi-Gaussian feature amplitude cannot be zero")
            _validate_sigma(feature)
            feature.setdefault("center_x_mm", domain_center)
            feature.setdefault("center_y_mm", domain_center)
            feature.setdefault("direction_rad", 0.0)
            feature.setdefault("feature_id", f"gaussian_{index}")
            if not isinstance(feature["feature_id"], str) or not feature["feature_id"]:
                raise ContractViolation("multi-Gaussian feature_id must be a non-empty string")
            normalized.append(MappingProxyType(feature))
        if len({item["feature_id"] for item in normalized}) != len(normalized):
            raise ContractViolation("multi-Gaussian feature IDs must be unique")
        result["features"] = tuple(normalized)
    elif family in (
        SurfaceFamily.GROOVE_COSINE,
        SurfaceFamily.GROOVE_CIRCULAR,
        SurfaceFamily.GROOVE_V,
    ):
        depth = _number(result, "depth_mm")
        width = _number(result, "half_width_mm", 1.0)
        if depth <= 0.0 or width <= 0.0:
            raise ContractViolation("groove depth and half-width must be positive")
        if family is SurfaceFamily.GROOVE_CIRCULAR and depth > width:
            raise ContractViolation("circular groove requires depth_mm <= half_width_mm")
        result["half_width_mm"] = width
        result.setdefault("center_x_mm", domain_center)
        result.setdefault("center_y_mm", domain_center)
        result.setdefault("direction_rad", 0.0)
    elif family is SurfaceFamily.GROOVE_SMOOTH:
        if _number(result, "depth_mm") <= 0.0:
            raise ContractViolation("smooth groove depth_mm must be positive")
        if "sigma_mm" in result and "half_width_mm" in result:
            raise ContractViolation("smooth groove accepts sigma_mm or half_width_mm, not both")
        sigma = _number(result, "sigma_mm", _number(result, "half_width_mm", 1.0) / 2.0)
        if sigma <= 0.0:
            raise ContractViolation("smooth groove scale must be positive")
        result["sigma_mm"] = sigma
        result.pop("half_width_mm", None)
        result.setdefault("center_x_mm", domain_center)
        result.setdefault("center_y_mm", domain_center)
        result.setdefault("direction_rad", 0.0)
    elif family is SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH:
        slope = _number(result, "ridge_slope", 1.0)
        if slope <= 0.0:
            raise ContractViolation("known switch ridge_slope must be positive")
        tolerance = _number(result, "switch_tolerance_mm", 1.0e-12)
        if tolerance < 0.0:
            raise ContractViolation("switch_tolerance_mm cannot be negative")
        result["ridge_slope"] = slope
        result["switch_tolerance_mm"] = tolerance
        result.setdefault("center_x_mm", domain_center)
        result.setdefault("center_y_mm", domain_center)
        result.setdefault("direction_rad", 0.0)
    elif family in (SurfaceFamily.SPHERICAL_CAP, SurfaceFamily.SPHERICAL_BOWL):
        radius = _number(result, "radius_mm")
        aperture = _number(result, "aperture_radius_mm", 0.8 * radius)
        if radius <= 0.0 or aperture <= 0.0 or aperture >= radius:
            raise ContractViolation("sphere fixture requires 0 < aperture_radius_mm < radius_mm")
        result["aperture_radius_mm"] = aperture
        result.setdefault("center_x_mm", domain_center)
        result.setdefault("center_y_mm", domain_center)

    for name, value in result.items():
        if name == "features":
            continue
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ContractViolation(f"analytic parameter {name} must be numeric")
        if not math.isfinite(float(value)):
            raise ContractViolation(f"analytic parameter {name} must be finite")
    return MappingProxyType(result)


def _unit_vectors(direction_rad: float) -> tuple[FloatArray, FloatArray]:
    along = np.array([math.cos(direction_rad), math.sin(direction_rad)], dtype=np.float64)
    across = np.array([-along[1], along[0]], dtype=np.float64)
    return along, across


def _normal_from_gradient(gradient: FloatArray) -> FloatArray:
    normal = np.column_stack((-gradient[:, 0], -gradient[:, 1], np.ones(len(gradient))))
    normal /= np.linalg.norm(normal, axis=1)[:, None]
    return normal


def _readonly(array: ArrayLike, *, dtype: Any = np.float64) -> NDArray[Any]:
    result = np.array(array, dtype=dtype, copy=True)
    result.setflags(write=False)
    return result


class AnalyticEvaluator:
    """Immutable evaluator for one strict analytic :class:`SurfaceSpec`."""

    __slots__ = ("definition_manifest", "family", "parameters", "spec")

    def __init__(self, spec: SurfaceSpec):
        if spec.source_kind is not SurfaceSourceKind.ANALYTIC:
            raise ContractViolation("AnalyticEvaluator requires an analytic SurfaceSpec")
        if spec.family is SurfaceFamily.SELF_AFFINE_GAUSSIAN:
            raise ContractViolation("self_affine_gaussian is not an analytic evaluator family")
        raw = {name: thaw_parameter(value) for name, value in spec.parameters}
        parameters = validate_analytic_parameters(spec.family, raw)
        self.spec = spec
        self.family = spec.family
        self.parameters = parameters
        self.definition_manifest = MappingProxyType(
            {
                "evaluator_id": "M01_ANALYTIC_SURFACE_LIBRARY",
                "evaluator_version": "1.0.0",
                "family": spec.family,
                "normalized_parameters": parameters,
            }
        )
        compatibility = capability_manifest(spec).for_operation("height_differential")
        if compatibility is None or spec.boundary_mode not in compatibility.boundary_compatibility:
            raise ContractViolation(
                f"{spec.family.value} is incompatible with {spec.boundary_mode.value} boundary queries"
            )

    def evaluate(
        self,
        x: ArrayLike,
        y: ArrayLike,
        derivative_order: int = 2,
        q_max_rad_per_mm: float | None = None,
    ) -> AnalyticEvaluation:
        """Evaluate height and requested differential order at paired coordinates."""

        if derivative_order not in (0, 1, 2):
            raise ContractViolation("derivative_order must be 0, 1, or 2")
        if q_max_rad_per_mm is not None and (
            not math.isfinite(q_max_rad_per_mm) or q_max_rad_per_mm <= 0.0
        ):
            raise ContractViolation("q_max_rad_per_mm must be finite and positive")
        x_array, y_array = np.broadcast_arrays(
            np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
        )
        if not np.isfinite(x_array).all() or not np.isfinite(y_array).all():
            raise ContractViolation("analytic query coordinates must be finite")
        input_shape = x_array.shape
        xf = np.ravel(x_array)
        yf = np.ravel(y_array)
        result = self._evaluate_flat(xf, yf)
        height, gradient, hessian, nonsmooth, validity, feature_sets, one_sided = result
        normal = _normal_from_gradient(gradient)
        hessian_validity = validity & ~nonsmooth
        curvature_validity = hessian_validity.copy()
        principal: FloatArray | None = None
        mean: FloatArray | None = None
        gaussian: FloatArray | None = None
        returned_hessian: FloatArray | None = hessian
        if derivative_order >= 2:
            mean, gaussian, principal = _graph_curvature(gradient, hessian)
            mean[~curvature_validity] = 0.0
            gaussian[~curvature_validity] = 0.0
            principal[~curvature_validity] = 0.0
        else:
            returned_hessian = None
            hessian_validity[:] = False
            curvature_validity[:] = False
        one_sided_normals: list[tuple[tuple[float, float, float], ...]] = []
        for gradients in one_sided:
            normals: list[tuple[float, float, float]] = []
            for gx, gy in gradients:
                vector = np.array([-gx, -gy, 1.0], dtype=np.float64)
                vector /= np.linalg.norm(vector)
                normals.append((float(vector[0]), float(vector[1]), float(vector[2])))
            one_sided_normals.append(tuple(normals))
        points = np.column_stack((xf, yf, height))
        return AnalyticEvaluation(
            input_shape=input_shape,
            height=_readonly(height),
            points=_readonly(points),
            gradient=_readonly(gradient),
            normal=_readonly(normal),
            hessian=None if returned_hessian is None else _readonly(returned_hessian),
            hessian_validity=_readonly(hessian_validity, dtype=np.bool_),
            principal_curvatures=None if principal is None else _readonly(principal),
            mean_curvature=None if mean is None else _readonly(mean),
            gaussian_curvature=None if gaussian is None else _readonly(gaussian),
            curvature_validity=_readonly(curvature_validity, dtype=np.bool_),
            validity=_readonly(validity, dtype=np.bool_),
            nonsmooth_mask=_readonly(nonsmooth, dtype=np.bool_),
            feature_sets=tuple(feature_sets),
            one_sided_gradients=tuple(one_sided),
            one_sided_normals=tuple(one_sided_normals),
        )

    def _evaluate_flat(
        self, x: FloatArray, y: FloatArray
    ) -> tuple[
        FloatArray,
        FloatArray,
        FloatArray,
        BoolArray,
        BoolArray,
        list[tuple[str, ...]],
        list[tuple[tuple[float, float], ...]],
    ]:
        count = len(x)
        p = self.parameters
        family = self.family
        offset = float(p["offset_mm"])
        height = np.full(count, offset, dtype=np.float64)
        gradient = np.zeros((count, 2), dtype=np.float64)
        hessian = np.zeros((count, 2, 2), dtype=np.float64)
        nonsmooth = np.zeros(count, dtype=np.bool_)
        validity = np.ones(count, dtype=np.bool_)
        features: list[tuple[str, ...]] = [() for _ in range(count)]
        one_sided: list[tuple[tuple[float, float], ...]] = [() for _ in range(count)]

        if family is SurfaceFamily.PLANE:
            return height, gradient, hessian, nonsmooth, validity, features, one_sided
        if family is SurfaceFamily.SLOPE_PLANE:
            gradient[:] = (float(p["slope_x"]), float(p["slope_y"]))
            height += gradient[:, 0] * x + gradient[:, 1] * y
            return height, gradient, hessian, nonsmooth, validity, features, one_sided
        if family is SurfaceFamily.SINUSOID_1D:
            direction, _ = _unit_vectors(float(p["direction_rad"]))
            coordinate = direction[0] * (x - float(p["origin_x_mm"])) + direction[1] * (
                y - float(p["origin_y_mm"])
            )
            wave = 2.0 * math.pi / float(p["wavelength_mm"])
            phase = wave * coordinate + float(p["phase_rad"])
            amplitude = float(p["amplitude_mm"])
            height += amplitude * np.sin(phase)
            gradient[:] = (amplitude * wave * np.cos(phase))[:, None] * direction
            hessian[:] = (-amplitude * wave * wave * np.sin(phase))[:, None, None] * np.outer(
                direction, direction
            )
            return height, gradient, hessian, nonsmooth, validity, features, one_sided
        if family is SurfaceFamily.SINUSOID_2D:
            first, second = _unit_vectors(float(p["direction_rad"]))
            dx = x - float(p["origin_x_mm"])
            dy = y - float(p["origin_y_mm"])
            coordinates = (first[0] * dx + first[1] * dy, second[0] * dx + second[1] * dy)
            for suffix, direction, coordinate in (
                ("x", first, coordinates[0]),
                ("y", second, coordinates[1]),
            ):
                amplitude = float(p[f"amplitude_{suffix}_mm"])
                wave = 2.0 * math.pi / float(p[f"wavelength_{suffix}_mm"])
                phase = wave * coordinate + float(p[f"phase_{suffix}_rad"])
                height += amplitude * np.sin(phase)
                gradient += (amplitude * wave * np.cos(phase))[:, None] * direction
                hessian += (-amplitude * wave * wave * np.sin(phase))[:, None, None] * np.outer(
                    direction, direction
                )
            return height, gradient, hessian, nonsmooth, validity, features, one_sided
        if family in (SurfaceFamily.GAUSSIAN_BUMP, SurfaceFamily.GAUSSIAN_PIT):
            sign = 1.0 if family is SurfaceFamily.GAUSSIAN_BUMP else -1.0
            _add_gaussian(
                height,
                gradient,
                hessian,
                x,
                y,
                p,
                sign * float(p["amplitude_mm"]),
            )
            return height, gradient, hessian, nonsmooth, validity, features, one_sided
        if family is SurfaceFamily.MULTI_GAUSSIAN_FEATURE:
            for feature in p["features"]:
                _add_gaussian(
                    height,
                    gradient,
                    hessian,
                    x,
                    y,
                    feature,
                    float(feature["amplitude_mm"]),
                )
            return height, gradient, hessian, nonsmooth, validity, features, one_sided

        if family in (
            SurfaceFamily.GROOVE_COSINE,
            SurfaceFamily.GROOVE_SMOOTH,
            SurfaceFamily.GROOVE_CIRCULAR,
            SurfaceFamily.GROOVE_V,
            SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH,
        ):
            _, across = _unit_vectors(float(p["direction_rad"]))
            cross = across[0] * (x - float(p["center_x_mm"])) + across[1] * (
                y - float(p["center_y_mm"])
            )
            if family is SurfaceFamily.GROOVE_SMOOTH:
                sigma = float(p["sigma_mm"])
                depth = float(p["depth_mm"])
                exponent = np.exp(-0.5 * (cross / sigma) ** 2)
                height -= depth * exponent
                first = depth * exponent * cross / (sigma * sigma)
                second = depth * exponent * (1.0 / sigma**2 - cross**2 / sigma**4)
                gradient[:] = first[:, None] * across
                hessian[:] = second[:, None, None] * np.outer(across, across)
                return height, gradient, hessian, nonsmooth, validity, features, one_sided
            if family is SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH:
                slope = float(p["ridge_slope"])
                height += slope * np.abs(cross)
                sign = np.sign(cross)
                gradient[:] = (slope * sign)[:, None] * across
                at_switch = np.abs(cross) <= float(p["switch_tolerance_mm"])
                nonsmooth[at_switch] = True
                for index in np.flatnonzero(at_switch):
                    features[index] = (
                        "switch_face_negative",
                        "switch_face_positive",
                        "switch_edge",
                    )
                    one_sided[index] = (
                        (float(-slope * across[0]), float(-slope * across[1])),
                        (float(slope * across[0]), float(slope * across[1])),
                    )
                return height, gradient, hessian, nonsmooth, validity, features, one_sided

            width = float(p["half_width_mm"])
            depth = float(p["depth_mm"])
            inside = np.abs(cross) < width
            at_left = np.isclose(cross, -width, rtol=0.0, atol=1.0e-12)
            at_right = np.isclose(cross, width, rtol=0.0, atol=1.0e-12)
            if family is SurfaceFamily.GROOVE_COSINE:
                phase = math.pi * cross[inside] / width
                height[inside] -= 0.5 * depth * (1.0 + np.cos(phase))
                first = 0.5 * depth * math.pi / width * np.sin(phase)
                second = 0.5 * depth * (math.pi / width) ** 2 * np.cos(phase)
                gradient[inside] = first[:, None] * across
                hessian[inside] = second[:, None, None] * np.outer(across, across)
                nonsmooth |= at_left | at_right
            elif family is SurfaceFamily.GROOVE_CIRCULAR:
                radius = (width * width + depth * depth) / (2.0 * depth)
                root = np.sqrt(np.maximum(radius * radius - cross[inside] ** 2, 0.0))
                height[inside] += radius - depth - root
                first = cross[inside] / root
                second = radius * radius / root**3
                gradient[inside] = first[:, None] * across
                hessian[inside] = second[:, None, None] * np.outer(across, across)
                nonsmooth |= at_left | at_right
            else:
                slope = depth / width
                height[inside] += -depth + slope * np.abs(cross[inside])
                gradient[inside] = (slope * np.sign(cross[inside]))[:, None] * across
                at_center = np.isclose(cross, 0.0, rtol=0.0, atol=1.0e-12)
                nonsmooth |= at_left | at_right | at_center
                for index in np.flatnonzero(at_center):
                    features[index] = ("v_left_face", "v_right_face", "v_bottom_edge")
                    one_sided[index] = (
                        (float(-slope * across[0]), float(-slope * across[1])),
                        (float(slope * across[0]), float(slope * across[1])),
                    )
            for index in np.flatnonzero(at_left):
                features[index] = ("groove_left_shoulder", "outside_plane")
            for index in np.flatnonzero(at_right):
                features[index] = ("groove_right_shoulder", "outside_plane")
            return height, gradient, hessian, nonsmooth, validity, features, one_sided

        if family in (SurfaceFamily.SPHERICAL_CAP, SurfaceFamily.SPHERICAL_BOWL):
            sign = 1.0 if family is SurfaceFamily.SPHERICAL_CAP else -1.0
            radius = float(p["radius_mm"])
            aperture = float(p["aperture_radius_mm"])
            dx = x - float(p["center_x_mm"])
            dy = y - float(p["center_y_mm"])
            radial2 = dx * dx + dy * dy
            inside = radial2 < aperture * aperture
            at_ring = np.isclose(radial2, aperture * aperture, rtol=0.0, atol=1.0e-10)
            root_aperture = math.sqrt(radius * radius - aperture * aperture)
            root = np.sqrt(radius * radius - radial2[inside])
            height[inside] += sign * (root - root_aperture)
            local = np.column_stack((dx[inside], dy[inside]))
            gradient[inside] = sign * (-local / root[:, None])
            eye = np.eye(2, dtype=np.float64)
            hessian[inside] = sign * (
                -eye[None, :, :] / root[:, None, None]
                - local[:, :, None] * local[:, None, :] / root[:, None, None] ** 3
            )
            nonsmooth |= at_ring
            for index in np.flatnonzero(at_ring):
                features[index] = ("spherical_patch", "outside_plane", "aperture_ring")
            return height, gradient, hessian, nonsmooth, validity, features, one_sided

        raise AssertionError(f"unhandled analytic family {family}")

    def global_slope_bound(self) -> float:
        """Return a conservative global ``||grad h||`` bound."""

        p = self.parameters
        family = self.family
        if family is SurfaceFamily.PLANE:
            return 0.0
        if family is SurfaceFamily.SLOPE_PLANE:
            return math.hypot(float(p["slope_x"]), float(p["slope_y"]))
        if family is SurfaceFamily.SINUSOID_1D:
            return float(p["amplitude_mm"]) * 2.0 * math.pi / float(p["wavelength_mm"])
        if family is SurfaceFamily.SINUSOID_2D:
            return sum(
                float(p[f"amplitude_{axis}_mm"]) * 2.0 * math.pi / float(p[f"wavelength_{axis}_mm"])
                for axis in ("x", "y")
            )
        if family in (SurfaceFamily.GAUSSIAN_BUMP, SurfaceFamily.GAUSSIAN_PIT):
            return (
                float(p["amplitude_mm"])
                * math.exp(-0.5)
                / min(float(p["sigma_x_mm"]), float(p["sigma_y_mm"]))
            )
        if family is SurfaceFamily.MULTI_GAUSSIAN_FEATURE:
            return sum(
                abs(float(feature["amplitude_mm"]))
                * math.exp(-0.5)
                / min(float(feature["sigma_x_mm"]), float(feature["sigma_y_mm"]))
                for feature in p["features"]
            )
        if family is SurfaceFamily.GROOVE_SMOOTH:
            return float(p["depth_mm"]) * math.exp(-0.5) / float(p["sigma_mm"])
        if family is SurfaceFamily.GROOVE_COSINE:
            return 0.5 * math.pi * float(p["depth_mm"]) / float(p["half_width_mm"])
        if family is SurfaceFamily.GROOVE_V:
            return float(p["depth_mm"]) / float(p["half_width_mm"])
        if family is SurfaceFamily.GROOVE_CIRCULAR:
            width = float(p["half_width_mm"])
            depth = float(p["depth_mm"])
            radius = (width * width + depth * depth) / (2.0 * depth)
            return width / math.sqrt(max(radius * radius - width * width, np.finfo(float).tiny))
        if family is SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH:
            return float(p["ridge_slope"])
        if family in (SurfaceFamily.SPHERICAL_CAP, SurfaceFamily.SPHERICAL_BOWL):
            radius = float(p["radius_mm"])
            aperture = float(p["aperture_radius_mm"])
            return aperture / math.sqrt(radius * radius - aperture * aperture)
        raise AssertionError(f"unhandled analytic family {family}")


def _add_gaussian(
    height: FloatArray,
    gradient: FloatArray,
    hessian: FloatArray,
    x: FloatArray,
    y: FloatArray,
    parameters: Mapping[str, Any],
    amplitude: float,
) -> None:
    direction, across = _unit_vectors(float(parameters["direction_rad"]))
    rotation = np.column_stack((direction, across))
    inverse_variance = (
        rotation
        @ np.diag(
            [1.0 / float(parameters["sigma_x_mm"]) ** 2, 1.0 / float(parameters["sigma_y_mm"]) ** 2]
        )
        @ rotation.T
    )
    displacement = np.column_stack(
        (x - float(parameters["center_x_mm"]), y - float(parameters["center_y_mm"]))
    )
    mapped = displacement @ inverse_variance
    value = amplitude * np.exp(-0.5 * np.einsum("ij,ij->i", mapped, displacement))
    height += value
    gradient -= value[:, None] * mapped
    hessian += value[:, None, None] * (
        mapped[:, :, None] * mapped[:, None, :] - inverse_variance[None, :, :]
    )


def _graph_curvature(
    gradient: FloatArray, hessian: FloatArray
) -> tuple[FloatArray, FloatArray, FloatArray]:
    hx = gradient[:, 0]
    hy = gradient[:, 1]
    hxx = hessian[:, 0, 0]
    hxy = hessian[:, 0, 1]
    hyy = hessian[:, 1, 1]
    metric = 1.0 + hx * hx + hy * hy
    mean = (1.0 + hy * hy) * hxx - 2.0 * hx * hy * hxy + (1.0 + hx * hx) * hyy
    mean /= 2.0 * metric**1.5
    gaussian = (hxx * hyy - hxy * hxy) / metric**2
    discriminant = np.maximum(mean * mean - gaussian, 0.0)
    root = np.sqrt(discriminant)
    principal = np.column_stack((mean - root, mean + root))
    return mean, gaussian, principal


def _manifest_entries(spec: SurfaceSpec) -> tuple[CapabilityEntry, ...]:
    family = spec.family
    schema = ANALYTIC_PARAMETER_SCHEMAS[family]
    periodic: tuple[BoundaryMode, ...] = (BoundaryMode.ERROR,)
    if family is SurfaceFamily.PLANE:
        periodic = (BoundaryMode.ERROR, BoundaryMode.PERIODIC)
    nonsmooth = {
        SurfaceFamily.GROOVE_COSINE: "shoulder lines |s|=half_width_mm (C1, not C2)",
        SurfaceFamily.GROOVE_CIRCULAR: "circular-arc/plane shoulder lines",
        SurfaceFamily.GROOVE_V: "bottom and shoulder lines",
        SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH: "switch ridge s=0",
        SurfaceFamily.SPHERICAL_CAP: "aperture ring",
        SurfaceFamily.SPHERICAL_BOWL: "aperture ring",
    }.get(family, "empty")
    smoothness = "piecewise C-infinity" if nonsmooth != "empty" else "C-infinity"
    exact_closest = family in {
        SurfaceFamily.PLANE,
        SurfaceFamily.SLOPE_PLANE,
        SurfaceFamily.GROOVE_V,
        SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH,
        SurfaceFamily.GROOVE_CIRCULAR,
        SurfaceFamily.SPHERICAL_CAP,
        SurfaceFamily.SPHERICAL_BOWL,
    }
    closest = QueryCapability.EXACT if exact_closest else QueryCapability.APPROXIMATE
    envelope = (
        QueryCapability.EXACT
        if family in (SurfaceFamily.PLANE, SurfaceFamily.SLOPE_PLANE)
        else QueryCapability.APPROXIMATE
    )
    common: _CapabilityCommon = {
        "method_version": "1.0.0",
        "parameter_domain": schema.domain,
        "smoothness": smoothness,
        "nonsmooth_set": nonsmooth,
        "boundary_compatibility": periodic,
    }
    return (
        CapabilityEntry(
            operation="height_differential",
            capability=QueryCapability.EXACT,
            method_id=f"M01_ANALYTIC_{family.value.upper()}",
            field_capabilities=(
                ("height", QueryCapability.EXACT),
                ("surface_point", QueryCapability.EXACT),
                ("gradient", QueryCapability.EXACT),
                ("normal", QueryCapability.EXACT),
                ("hessian", QueryCapability.EXACT),
                ("curvature", QueryCapability.EXACT),
            ),
            **common,
        ),
        CapabilityEntry(
            operation="neighborhood",
            capability=QueryCapability.APPROXIMATE,
            method_id="M01_ANALYTIC_LIPSCHITZ_NEIGHBORHOOD",
            field_capabilities=(
                ("height_bounds", QueryCapability.APPROXIMATE),
                ("slope_bound", QueryCapability.EXACT),
            ),
            **common,
        ),
        CapabilityEntry(
            operation="signed_distance",
            capability=closest,
            method_id=(
                "M01_ANALYTIC_PRIMITIVE_CLOSEST"
                if exact_closest
                else "M01_ANALYTIC_GLOBAL_CANDIDATE_CLOSEST"
            ),
            field_capabilities=(("signed_distance", closest),),
            **common,
        ),
        CapabilityEntry(
            operation="closest_features",
            capability=closest,
            method_id=(
                "M01_ANALYTIC_PRIMITIVE_CLOSEST"
                if exact_closest
                else "M01_ANALYTIC_GLOBAL_CANDIDATE_CLOSEST"
            ),
            field_capabilities=(("closest_point", closest), ("outward_normal", closest)),
            **common,
        ),
        CapabilityEntry(
            operation="spherical_envelope_or_clearance",
            capability=envelope,
            method_id=(
                "M01_AFFINE_HEIGHT_SPHERE_ENVELOPE"
                if envelope is QueryCapability.EXACT
                else "M01_GLOBAL_HEIGHT_SPHERE_ENVELOPE"
            ),
            field_capabilities=(
                ("envelope_height", envelope),
                ("support_set", envelope),
                ("phi_minus_radius", closest),
            ),
            **common,
        ),
    )


def capability_manifest(spec: SurfaceSpec) -> CapabilityManifest:
    """Build the canonical family capability manifest for ``spec``."""

    if (
        spec.source_kind is not SurfaceSourceKind.ANALYTIC
        or spec.family not in ANALYTIC_PARAMETER_SCHEMAS
    ):
        raise ContractViolation("analytic capability manifest requires an analytic SurfaceSpec")
    entries = _manifest_entries(spec)
    preimage = {
        "family": spec.family,
        "query_contract_version": QUERY_CONTRACT_VERSION,
        "entries": entries,
        "source_identity": spec.source_identity,
    }
    return CapabilityManifest(
        manifest_id=stable_content_id("surface_capability_manifest", preimage),
        family=spec.family,
        query_contract_version=QUERY_CONTRACT_VERSION,
        entries=entries,
        source_identity=spec.source_identity,
    )


__all__ = [
    "ANALYTIC_PARAMETER_SCHEMAS",
    "UNIVERSAL_PARAMETER_ALIASES",
    "AnalyticEvaluation",
    "AnalyticEvaluator",
    "ParameterSchema",
    "capability_manifest",
    "validate_analytic_parameters",
]
