"""Pure complete-sphere geometry over M01 surfaces.

``radius_mm`` is a query probe and is never part of a surface identity.  This
module intentionally has no needle-axis, finite-cap, force, friction, contact,
engagement, or material-failure inputs or outputs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

import numpy as np
from numpy.typing import ArrayLike, NDArray

from spine_sim.foundation.errors import ContractViolation

from .analytic import AnalyticEvaluation
from .contracts import (
    ClosestFeature,
    ConvergenceLevel,
    DomainStatus,
    QualityStatus,
    QueryCapability,
    QueryResponse,
    SurfaceFamily,
    SurfaceSpec,
)
from .query import DomainClassification, _field_result, _xy_points, _xyz_points, as_surface_query

if TYPE_CHECKING:
    from .query import SurfaceQueryHandle

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]


class HeightFieldEvaluator(Protocol):
    """Structural geometry interface shared by analytic and synthetic adapters."""

    @property
    def spec(self) -> SurfaceSpec: ...

    @property
    def family(self) -> SurfaceFamily: ...

    def evaluate(
        self,
        x: ArrayLike,
        y: ArrayLike,
        derivative_order: int = 2,
        q_max_rad_per_mm: float | None = None,
    ) -> AnalyticEvaluation: ...

    def global_slope_bound(self) -> float: ...


@dataclass(frozen=True, slots=True)
class SphereEnvelopeResult:
    """Lowest complete-sphere center heights and all resolved co-max supports."""

    center_xy_mm: FloatArray
    radius_mm: float
    envelope_height_mm: FloatArray
    validity: BoolArray
    supports: tuple[tuple[ClosestFeature, ...], ...]
    capability: QueryCapability
    achieved_residual_mm: float
    error_bound_mm: float
    convergence_level: ConvergenceLevel
    method_id: str

    def __post_init__(self) -> None:
        for array in (self.center_xy_mm, self.envelope_height_mm, self.validity):
            array.setflags(write=False)


def _validate_radius(radius_mm: float) -> float:
    if not math.isfinite(radius_mm) or radius_mm <= 0.0:
        raise ContractViolation("complete-sphere radius_mm must be finite and positive")
    return float(radius_mm)


def height_field_spherical_envelope(
    evaluator: HeightFieldEvaluator,
    center_xy_mm: ArrayLike,
    radius_mm: float,
    *,
    requested_tolerance_mm: float = 1.0e-7,
    co_maximal_tolerance_mm: float = 1.0e-8,
    sample_count: int = 65,
) -> SphereEnvelopeResult:
    """Evaluate accepted-A ``H_R`` for a height field.

    The affine families use their closed form.  Other analytic families use a
    coordinate-anchored global disk covering followed by analytic Newton
    refinement; the returned bound includes the complete covering radius.
    """

    radius = _validate_radius(radius_mm)
    centers = _xy_points(center_xy_mm)
    if not math.isfinite(requested_tolerance_mm) or requested_tolerance_mm <= 0.0:
        raise ContractViolation("requested_tolerance_mm must be finite and positive")
    if not math.isfinite(co_maximal_tolerance_mm) or co_maximal_tolerance_mm < 0.0:
        raise ContractViolation("co_maximal_tolerance_mm must be finite and non-negative")
    if sample_count < 9 or sample_count > 1025 or sample_count % 2 == 0:
        raise ContractViolation("sample_count must be an odd integer in [9, 1025]")
    domain = evaluator.spec.logical_domain
    validity = np.array(
        [
            domain.contains(x - radius, y - radius) and domain.contains(x + radius, y + radius)
            for x, y in centers
        ],
        dtype=np.bool_,
    )
    envelopes = np.zeros(len(centers), dtype=np.float64)
    supports: list[tuple[ClosestFeature, ...]] = [() for _ in centers]
    affine = evaluator.family.value in {"plane", "slope_plane"}
    maximum_residual = 0.0
    maximum_error = 0.0
    for index in np.flatnonzero(validity):
        center = centers[index]
        if affine:
            evaluation = evaluator.evaluate(center[0], center[1], derivative_order=1)
            gradient = evaluation.gradient[0]
            denominator = math.sqrt(1.0 + float(np.dot(gradient, gradient)))
            displacement = radius * gradient / denominator
            support_xy = center + displacement
            support_eval = evaluator.evaluate(support_xy[0], support_xy[1], derivative_order=1)
            envelopes[index] = float(support_eval.height[0] + radius / denominator)
            normal = (
                float(support_eval.normal[0, 0]),
                float(support_eval.normal[0, 1]),
                float(support_eval.normal[0, 2]),
            )
            supports[index] = (
                ClosestFeature(
                    feature_id="affine_sphere_support",
                    feature_type="height_envelope_support",
                    point_mm=(
                        float(support_eval.points[0, 0]),
                        float(support_eval.points[0, 1]),
                        float(support_eval.points[0, 2]),
                    ),
                    outward_normals=(normal,),
                    signed_distance_mm=0.0,
                    domain_status=DomainStatus.IN_DOMAIN,
                    quality_status=QualityStatus.TRUSTED_FOR_DECLARED_SCALE,
                    residual_mm=0.0,
                    error_bound_mm=0.0,
                ),
            )
            continue
        envelope, candidates, residual, error = _approximate_envelope_one(
            evaluator, center, radius, sample_count, co_maximal_tolerance_mm
        )
        envelopes[index] = envelope
        supports[index] = candidates
        maximum_residual = max(maximum_residual, residual)
        maximum_error = max(maximum_error, error)
    capability = QueryCapability.EXACT if affine else QueryCapability.APPROXIMATE
    if not validity.any():
        capability = QueryCapability.UNAVAILABLE
    convergence = ConvergenceLevel.ANALYTIC if affine else ConvergenceLevel.CONVERGED
    if not validity.any():
        convergence = ConvergenceLevel.FAILED
    elif not affine and max(maximum_residual, maximum_error) > requested_tolerance_mm:
        convergence = ConvergenceLevel.REFINEMENT_REQUIRED
    for array in (centers, envelopes, validity):
        array.setflags(write=False)
    return SphereEnvelopeResult(
        centers,
        radius,
        envelopes,
        validity,
        tuple(supports),
        capability,
        maximum_residual,
        maximum_error,
        convergence,
        "M01_AFFINE_HEIGHT_SPHERE_ENVELOPE" if affine else "M01_GLOBAL_HEIGHT_SPHERE_ENVELOPE",
    )


def _approximate_envelope_one(
    evaluator: HeightFieldEvaluator,
    center: FloatArray,
    radius: float,
    sample_count: int,
    co_maximal_tolerance: float,
) -> tuple[float, tuple[ClosestFeature, ...], float, float]:
    axis = np.linspace(-radius, radius, sample_count, dtype=np.float64)
    dx, dy = np.meshgrid(axis, axis)
    radial2 = dx * dx + dy * dy
    inside = radial2 <= radius * radius
    displacements = np.column_stack((dx[inside], dy[inside]))
    evaluation = evaluator.evaluate(
        center[0] + displacements[:, 0], center[1] + displacements[:, 1], derivative_order=2
    )
    sphere_term = np.sqrt(np.maximum(radius * radius - np.sum(displacements**2, axis=1), 0.0))
    objective = evaluation.height + sphere_term
    best_indices = np.argsort(objective)[-min(24, len(objective)) :]
    refined: list[tuple[float, FloatArray, float]] = []
    for seed_index in best_indices:
        displacement, residual = _refine_envelope(
            evaluator, center, radius, displacements[seed_index]
        )
        value = evaluator.evaluate(
            center[0] + displacement[0], center[1] + displacement[1], derivative_order=1
        )
        root = math.sqrt(max(radius * radius - float(np.dot(displacement, displacement)), 0.0))
        refined.append((float(value.height[0] + root), displacement, residual))
    maximum = max(item[0] for item in refined)
    chosen = [item for item in refined if maximum - item[0] <= co_maximal_tolerance]
    unique: list[tuple[float, FloatArray, float]] = []
    for item in sorted(chosen, key=lambda value: tuple(value[1])):
        if not any(np.linalg.norm(item[1] - other[1]) <= co_maximal_tolerance for other in unique):
            unique.append(item)
    spacing = 2.0 * radius / (sample_count - 1)
    cover = math.sqrt(2.0) * spacing / 2.0
    error = evaluator.global_slope_bound() * cover + math.sqrt(2.0 * radius * cover)
    supports: list[ClosestFeature] = []
    for feature_index, (_, displacement, residual) in enumerate(unique):
        value = evaluator.evaluate(
            center[0] + displacement[0], center[1] + displacement[1], derivative_order=1
        )
        feature_ids = value.feature_sets[0] or (f"envelope_support_{feature_index}",)
        normals = value.one_sided_normals[0] or (
            (
                float(value.normal[0, 0]),
                float(value.normal[0, 1]),
                float(value.normal[0, 2]),
            ),
        )
        supports.append(
            ClosestFeature(
                feature_id="+".join(feature_ids),
                feature_type="height_envelope_support",
                point_mm=(
                    float(value.points[0, 0]),
                    float(value.points[0, 1]),
                    float(value.points[0, 2]),
                ),
                outward_normals=normals,
                signed_distance_mm=0.0,
                domain_status=DomainStatus.IN_DOMAIN,
                quality_status=(
                    QualityStatus.NONSMOOTH_FEATURE_SET
                    if len(normals) > 1
                    else QualityStatus.TRUSTED_FOR_DECLARED_SCALE
                ),
                residual_mm=residual,
                error_bound_mm=error,
            )
        )
    return maximum, tuple(supports), max(item[2] for item in unique), error


def _refine_envelope(
    evaluator: HeightFieldEvaluator,
    center: FloatArray,
    radius: float,
    seed: FloatArray,
) -> tuple[FloatArray, float]:
    displacement = np.array(seed, dtype=np.float64, copy=True)
    interior_radius = radius * (1.0 - 1.0e-12)
    norm = float(np.linalg.norm(displacement))
    if norm >= interior_radius:
        displacement *= interior_radius / max(norm, np.finfo(float).tiny)
    for _ in range(48):
        value = evaluator.evaluate(
            center[0] + displacement[0], center[1] + displacement[1], derivative_order=2
        )
        root = math.sqrt(
            max(radius * radius - float(np.dot(displacement, displacement)), np.finfo(float).tiny)
        )
        gradient = value.gradient[0] - displacement / root
        if np.linalg.norm(gradient) <= 1.0e-12:
            break
        hessian = -np.eye(2) / root - np.outer(displacement, displacement) / root**3
        if value.hessian is not None and value.hessian_validity[0]:
            hessian += value.hessian[0]
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            step = -gradient / max(np.linalg.norm(gradient), 1.0)
        current = float(value.height[0] + root)
        scale = 1.0
        accepted = False
        for _ in range(24):
            trial = displacement - scale * step
            trial_norm = float(np.linalg.norm(trial))
            if trial_norm >= interior_radius:
                trial *= interior_radius / max(trial_norm, np.finfo(float).tiny)
            trial_value = evaluator.evaluate(
                center[0] + trial[0], center[1] + trial[1], derivative_order=0
            )
            trial_root = math.sqrt(max(radius * radius - float(np.dot(trial, trial)), 0.0))
            if float(trial_value.height[0] + trial_root) >= current:
                displacement = trial
                accepted = True
                break
            scale *= 0.5
        if not accepted or np.linalg.norm(scale * step) <= 1.0e-13:
            break
    value = evaluator.evaluate(
        center[0] + displacement[0], center[1] + displacement[1], derivative_order=1
    )
    root = math.sqrt(
        max(radius * radius - float(np.dot(displacement, displacement)), np.finfo(float).tiny)
    )
    residual = float(np.linalg.norm(value.gradient[0] - displacement / root))
    return displacement, residual


def generic_sphere_clearance(
    handle: SurfaceQueryHandle | Any,
    center_xyz_mm: ArrayLike,
    radius_mm: float,
    **closest_options: Any,
) -> QueryResponse:
    """Return accepted-A generic-path ``phi(center)-radius``."""

    handle = as_surface_query(handle)
    radius = _validate_radius(radius_mm)
    centers = _xyz_points(center_xyz_mm)
    distance = handle.query_signed_distance(centers, **closest_options)
    validity = distance.quality_mask.copy()
    values = np.zeros(len(centers), dtype=np.float64)
    if distance.fields and distance.field("signed_distance_mm").values is not None:
        values[:] = np.asarray(distance.field("signed_distance_mm").values) - radius
    field = _field_result(
        "sphere_clearance_mm",
        values if validity.any() else None,
        validity,
        distance.capability,
        "mm",
        handle.realization.surface_frame_id,
        "complete_sphere_center",
        distance.trusted_scale_status,
        distance.error_bound,
    )
    classified = handle._domain(centers[:, :2])
    return handle._response(
        operation="spherical_envelope_or_clearance",
        requested={"center_xyz_mm": centers, "radius_mm": radius, "path": "phi_minus_radius"},
        capability=distance.capability,
        method_id="M01_GENERIC_PHI_MINUS_RADIUS",
        domain=classified,
        quality_status=distance.quality_status,
        quality_mask=validity,
        fields=(field,),
        convergence=distance.convergence_level,
        requested_tolerance=distance.requested_tolerance,
        achieved_residual=distance.achieved_residual,
        error_bound=distance.error_bound,
        feature_sets=distance.feature_sets,
        metadata=(("radius_is_query_probe", True), ("sphere_path", "phi_omega_minus_radius")),
        mapped_if_wrapped=True,
        reference_semantics="g_R(c)=phi_Omega_h(c)-R; outside positive",
    )


def query_spherical_envelope_or_clearance(
    handle: SurfaceQueryHandle | Any,
    centers_mm: ArrayLike,
    radius_mm: float,
    *,
    path: str = "height_envelope",
    **options: Any,
) -> QueryResponse:
    """Query either ``H_R`` (2D centers) or generic ``phi-R`` (3D centers)."""

    handle = as_surface_query(handle)
    if path == "phi_minus_radius":
        return generic_sphere_clearance(handle, centers_mm, radius_mm, **options)
    if path != "height_envelope":
        raise ContractViolation("sphere path must be height_envelope or phi_minus_radius")
    centers = _xy_points(centers_mm)
    classified = handle._domain(centers)
    result = height_field_spherical_envelope(
        handle.evaluator, classified.mapped_coordinates_mm, radius_mm, **options
    )
    validity = classified.validity & result.validity
    representative = np.zeros((len(centers), 3), dtype=np.float64)
    for index, support_set in enumerate(result.supports):
        if support_set:
            representative[index] = support_set[0].point_mm
    fields = (
        _field_result(
            "sphere_envelope_height_mm",
            result.envelope_height_mm if validity.any() else None,
            validity,
            result.capability,
            "mm",
            handle.realization.surface_frame_id,
            "complete_sphere_center",
            QualityStatus.TRUSTED_FOR_DECLARED_SCALE,
            result.error_bound_mm,
        ),
        _field_result(
            "sphere_support_point_mm",
            representative if validity.any() else None,
            validity,
            result.capability,
            "mm",
            handle.realization.surface_frame_id,
            "surface_frame_origin",
            QualityStatus.NONSMOOTH_FEATURE_SET
            if any(len(item) > 1 for item in result.supports)
            else QualityStatus.TRUSTED_FOR_DECLARED_SCALE,
            result.error_bound_mm,
        ),
    )
    domain = DomainClassification(
        classified.original_coordinates_mm,
        classified.mapped_coordinates_mm,
        classified.status,
        validity,
    )
    quality = tuple(
        QualityStatus.GEOMETRY_UNCERTAIN
        if not validity[index]
        else QualityStatus.NONSMOOTH_FEATURE_SET
        if len(result.supports[index]) > 1
        else QualityStatus.TRUSTED_FOR_DECLARED_SCALE
        for index in range(len(centers))
    )
    return handle._response(
        operation="spherical_envelope_or_clearance",
        requested={"center_xy_mm": centers, "radius_mm": radius_mm, "path": "height_envelope"},
        capability=result.capability if validity.any() else QueryCapability.UNAVAILABLE,
        method_id=result.method_id,
        domain=domain,
        quality_status=quality,
        quality_mask=validity,
        fields=fields,
        convergence=result.convergence_level,
        requested_tolerance=options.get("requested_tolerance_mm", 1.0e-7),
        achieved_residual=result.achieved_residual_mm,
        error_bound=result.error_bound_mm,
        feature_sets=result.supports,
        metadata=(("radius_is_query_probe", True), ("sphere_path", "height_field_H_R")),
        mapped_if_wrapped=True,
        reference_semantics="H_R(xc,yc)=sup[h(u,v)+sqrt(R^2-rho^2)]",
    )


def validate_sphere_path_consistency(
    handle: SurfaceQueryHandle | Any,
    center_xy_mm: ArrayLike,
    radius_mm: float,
    *,
    tolerance_mm: float = 1.0e-6,
) -> BoolArray:
    """Compare ``H_R`` zero-boundary centers with the generic ``phi-R`` path."""

    handle = as_surface_query(handle)
    envelope = height_field_spherical_envelope(
        handle.evaluator, center_xy_mm, radius_mm, requested_tolerance_mm=tolerance_mm
    )
    centers = np.column_stack((envelope.center_xy_mm, envelope.envelope_height_mm))
    generic = generic_sphere_clearance(
        handle, centers, radius_mm, requested_tolerance_mm=tolerance_mm
    )
    values = generic.field("sphere_clearance_mm").values
    if values is None:
        result = np.zeros(len(centers), dtype=np.bool_)
    else:
        result = np.asarray(np.abs(values) <= tolerance_mm, dtype=np.bool_)
        result &= envelope.validity
    result.setflags(write=False)
    return result


__all__ = [
    "SphereEnvelopeResult",
    "generic_sphere_clearance",
    "height_field_spherical_envelope",
    "query_spherical_envelope_or_clearance",
    "validate_sphere_path_consistency",
]
