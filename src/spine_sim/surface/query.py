"""Public deterministic query facade for M01 surface geometry.

This module deliberately exposes only surface geometry.  It does not infer a
finite-cap legality, contact, engagement, friction, force, or failure state.
"""

from __future__ import annotations

import heapq
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation

from .analytic import (
    AnalyticEvaluation,
    AnalyticEvaluator,
    _graph_curvature,
    _normal_from_gradient,
    _readonly,
)
from .contracts import (
    QUERY_CONTRACT_VERSION,
    BoundaryMode,
    ClosestFeature,
    ConvergenceLevel,
    Domain2D,
    DomainStatus,
    FieldQueryResult,
    M01ReasonCode,
    QualityStatus,
    QueryCapability,
    QueryResponse,
    SurfaceFamily,
    SurfaceRealization,
    supported_status,
    unavailable_status,
)
from .synthetic import SyntheticEvaluator

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]


class _SyntheticEvaluatorAdapter:
    """Expose a synthetic finite-mode field through the common graph geometry API."""

    __slots__ = (
        "definition_manifest",
        "family",
        "is_synthetic",
        "original",
        "parameters",
        "spec",
    )

    def __init__(self, evaluator: SyntheticEvaluator) -> None:
        self.original = evaluator
        self.spec = evaluator.spec
        self.family = evaluator.spec.family
        self.parameters: dict[str, Any] = {}
        self.definition_manifest = evaluator.definition_manifest
        self.is_synthetic = True

    def evaluate(
        self,
        x: ArrayLike,
        y: ArrayLike,
        derivative_order: int = 2,
        q_max_rad_per_mm: float | None = None,
    ) -> AnalyticEvaluation:
        raw = self.original.evaluate(
            x,
            y,
            derivative_order=derivative_order,
            q_max_rad_per_mm=q_max_rad_per_mm,
        )
        x_array, y_array = np.broadcast_arrays(
            np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
        )
        height = np.asarray(raw.height, dtype=np.float64)
        count = height.size
        gradient = (
            np.zeros((count, 2), dtype=np.float64)
            if raw.gradient is None
            else np.asarray(raw.gradient, dtype=np.float64)
        )
        hessian = None if raw.hessian is None else np.asarray(raw.hessian, dtype=np.float64)
        normal = _normal_from_gradient(gradient)
        valid = np.ones(count, dtype=np.bool_)
        hessian_validity = np.full(count, hessian is not None, dtype=np.bool_)
        curvature_validity = hessian_validity.copy()
        principal: FloatArray | None = None
        mean: FloatArray | None = None
        gaussian: FloatArray | None = None
        if hessian is not None:
            mean, gaussian, principal = _graph_curvature(gradient, hessian)
        points = np.column_stack((x_array.reshape(-1), y_array.reshape(-1), height))
        empty_features = tuple(() for _ in range(count))
        return AnalyticEvaluation(
            input_shape=raw.query_shape,
            height=_readonly(height),
            points=_readonly(points),
            gradient=_readonly(gradient),
            normal=_readonly(normal),
            hessian=None if hessian is None else _readonly(hessian),
            hessian_validity=_readonly(hessian_validity, dtype=np.bool_),
            principal_curvatures=None if principal is None else _readonly(principal),
            mean_curvature=None if mean is None else _readonly(mean),
            gaussian_curvature=None if gaussian is None else _readonly(gaussian),
            curvature_validity=_readonly(curvature_validity, dtype=np.bool_),
            validity=_readonly(valid, dtype=np.bool_),
            nonsmooth_mask=_readonly(np.zeros(count, dtype=np.bool_), dtype=np.bool_),
            feature_sets=empty_features,
            one_sided_gradients=empty_features,
            one_sided_normals=empty_features,
        )

    def global_slope_bound(self) -> float:
        coefficient_radius = np.hypot(
            self.original.coefficient_cos_mm,
            self.original.coefficient_sin_mm,
        )
        q = np.hypot(
            self.original.mode_coordinates[:, 0],
            self.original.mode_coordinates[:, 1],
        ) * (math.tau / self.spec.logical_domain.width_mm)
        return float(np.sum(coefficient_radius * q, dtype=np.float64))

    def omitted_band_bounds(self, q_max_rad_per_mm: float | None):  # type: ignore[no-untyped-def]
        return self.original.omitted_band_bounds(q_max_rad_per_mm)


GraphEvaluator = AnalyticEvaluator | _SyntheticEvaluatorAdapter


@dataclass(frozen=True, slots=True)
class DomainClassification:
    """Cardinality-preserving logical-domain mapping result."""

    original_coordinates_mm: FloatArray
    mapped_coordinates_mm: FloatArray
    status: tuple[DomainStatus, ...]
    validity: BoolArray

    def __post_init__(self) -> None:
        for array in (self.original_coordinates_mm, self.mapped_coordinates_mm, self.validity):
            array.setflags(write=False)


@dataclass(frozen=True, slots=True)
class _Candidate:
    point: tuple[float, float, float]
    normals: tuple[tuple[float, float, float], ...]
    feature_id: str
    feature_type: str
    residual: float
    error_bound: float


def _xy_points(x: ArrayLike, y: ArrayLike | None = None) -> FloatArray:
    if y is None:
        points = np.asarray(x, dtype=np.float64)
        if points.shape == (2,):
            result = points.reshape(1, 2)
        elif points.ndim == 2 and points.shape[1] == 2:
            result = points
        else:
            raise ContractViolation("2D query points must have shape (2,) or (N, 2)")
    else:
        xa = np.asarray(x, dtype=np.float64)
        ya = np.asarray(y, dtype=np.float64)
        if xa.shape != ya.shape:
            raise ContractViolation(
                "paired x/y batches must have identical shapes; broadcasting is forbidden"
            )
        if xa.ndim > 1:
            raise ContractViolation(
                "paired x/y inputs must be scalar or one-dimensional typed batches"
            )
        result = np.column_stack((xa.reshape(-1), ya.reshape(-1)))
    if not np.isfinite(result).all():
        raise ContractViolation("query coordinates must be finite")
    return np.array(result, dtype=np.float64, copy=True)


def _xyz_points(points: ArrayLike) -> FloatArray:
    value = np.asarray(points, dtype=np.float64)
    if value.shape == (3,):
        result = value.reshape(1, 3)
    elif value.ndim == 2 and value.shape[1] == 3:
        result = value
    else:
        raise ContractViolation("3D query points must have shape (3,) or (N, 3)")
    if not np.isfinite(result).all():
        raise ContractViolation("query coordinates must be finite")
    return np.array(result, dtype=np.float64, copy=True)


def classify_domain_coordinates(
    domain: Domain2D,
    coordinates_mm: ArrayLike,
    *,
    boundary_mode: BoundaryMode,
    periodic_compatible: bool,
    tolerance_mm: float = 1.0e-12,
) -> DomainClassification:
    """Classify without clamping or implicit wrapping."""

    if not math.isfinite(tolerance_mm) or tolerance_mm < 0.0:
        raise ContractViolation("domain tolerance must be finite and non-negative")
    original = _xy_points(coordinates_mm)
    mapped = original.copy()
    statuses: list[DomainStatus] = []
    validity = np.ones(len(original), dtype=np.bool_)
    if boundary_mode is BoundaryMode.PERIODIC and not periodic_compatible:
        raise ContractViolation(
            "PERIODIC was requested for a family that did not declare compatibility"
        )
    for index, (x_mm, y_mm) in enumerate(original):
        inside = domain.contains(float(x_mm), float(y_mm), tolerance_mm=tolerance_mm)
        if not inside:
            if boundary_mode is BoundaryMode.ERROR:
                statuses.append(DomainStatus.OUT_OF_DOMAIN)
                validity[index] = False
            else:
                mapped[index] = domain.map_periodic(float(x_mm), float(y_mm))
                statuses.append(DomainStatus.WRAPPED)
            continue
        on_boundary = (
            math.isclose(float(x_mm), domain.x_min_mm, abs_tol=tolerance_mm, rel_tol=0.0)
            or math.isclose(float(x_mm), domain.x_max_mm, abs_tol=tolerance_mm, rel_tol=0.0)
            or math.isclose(float(y_mm), domain.y_min_mm, abs_tol=tolerance_mm, rel_tol=0.0)
            or math.isclose(float(y_mm), domain.y_max_mm, abs_tol=tolerance_mm, rel_tol=0.0)
        )
        statuses.append(DomainStatus.ON_BOUNDARY if on_boundary else DomainStatus.IN_DOMAIN)
    original.setflags(write=False)
    mapped.setflags(write=False)
    validity.setflags(write=False)
    return DomainClassification(original, mapped, tuple(statuses), validity)


class SurfaceQueryHandle:
    """Logical read-only query handle for analytic or finite-mode synthetic geometry."""

    __slots__ = ("evaluator", "realization")

    def __init__(self, realization: SurfaceRealization | Any, evaluator: Any | None = None):
        if evaluator is None:
            source_handle = realization
            if not hasattr(source_handle, "realization") or not hasattr(source_handle, "evaluator"):
                raise ContractViolation("query facade requires a realization/evaluator handle")
            realization = source_handle.realization
            evaluator = source_handle.evaluator
        if isinstance(evaluator, SyntheticEvaluator):
            evaluator = _SyntheticEvaluatorAdapter(evaluator)
        if not isinstance(realization, SurfaceRealization) or not isinstance(
            evaluator, AnalyticEvaluator | _SyntheticEvaluatorAdapter
        ):
            raise ContractViolation(
                "query facade requires an analytic or M01 synthetic realization/evaluator"
            )
        if realization.surface_spec_id != evaluator.spec.surface_spec_id:
            raise ContractViolation("query evaluator/spec identity does not match realization")
        if realization.family is not evaluator.family:
            raise ContractViolation("query evaluator family does not match realization")
        if realization.query_contract_version != QUERY_CONTRACT_VERSION:
            raise ContractViolation("query handle contract version mismatch")
        self.realization = realization
        self.evaluator = evaluator

    @property
    def spec(self):  # type: ignore[no-untyped-def]
        return self.evaluator.spec

    def _domain(self, coordinates: FloatArray) -> DomainClassification:
        entry = self.realization.capability_manifest.for_operation("height_differential")
        compatible = entry is not None and BoundaryMode.PERIODIC in entry.boundary_compatibility
        return classify_domain_coordinates(
            self.realization.logical_domain,
            coordinates,
            boundary_mode=self.realization.boundary_mode,
            periodic_compatible=compatible,
        )

    def classify_domain(self, coordinates_mm: ArrayLike) -> QueryResponse:
        coordinates = _xy_points(coordinates_mm)
        classified = self._domain(coordinates)
        validity = classified.validity
        values: FloatArray | None = classified.mapped_coordinates_mm if validity.any() else None
        field = _field_result(
            "mapped_coordinates_mm",
            values,
            validity,
            QueryCapability.EXACT,
            "mm",
            self.realization.surface_frame_id,
            "surface_frame_origin",
            QualityStatus.TRUSTED_FOR_DECLARED_SCALE,
        )
        return self._response(
            operation="classify_domain",
            requested={"coordinates_mm": coordinates},
            capability=QueryCapability.EXACT if validity.any() else QueryCapability.UNAVAILABLE,
            method_id="M01_LOGICAL_DOMAIN_CLASSIFIER",
            domain=classified,
            quality_status=tuple(
                QualityStatus.TRUSTED_FOR_DECLARED_SCALE
                if item
                else QualityStatus.GEOMETRY_UNCERTAIN
                for item in validity
            ),
            quality_mask=validity,
            fields=(field,),
            convergence=ConvergenceLevel.ANALYTIC,
            mapped_if_wrapped=True,
        )

    def query_height_differential(
        self,
        x: ArrayLike,
        y: ArrayLike | None = None,
        *,
        derivative_order: int = 2,
        q_max_rad_per_mm: float | None = None,
    ) -> QueryResponse:
        coordinates = _xy_points(x, y)
        classified = self._domain(coordinates)
        count = len(coordinates)
        valid_indices = np.flatnonzero(classified.validity)
        evaluated: AnalyticEvaluation | None = None
        omitted_height_bound = 0.0
        omitted_slope_bound = 0.0
        refinement_required = False
        if len(valid_indices):
            mapped = classified.mapped_coordinates_mm[valid_indices]
            evaluated = self.evaluator.evaluate(
                mapped[:, 0], mapped[:, 1], derivative_order, q_max_rad_per_mm
            )
            if isinstance(self.evaluator, _SyntheticEvaluatorAdapter):
                omitted = self.evaluator.omitted_band_bounds(q_max_rad_per_mm)
                omitted_height_bound = omitted.height_bound_mm
                omitted_slope_bound = omitted.slope_bound
                refinement_required = omitted.omitted_mode_count > 0
        height = np.zeros(count, dtype=np.float64)
        points = np.zeros((count, 3), dtype=np.float64)
        gradient = np.zeros((count, 2), dtype=np.float64)
        normal = np.zeros((count, 3), dtype=np.float64)
        height_validity = classified.validity.copy()
        nonsmooth = np.zeros(count, dtype=np.bool_)
        hessian = np.zeros((count, 2, 2), dtype=np.float64)
        hessian_validity = np.zeros(count, dtype=np.bool_)
        principal = np.zeros((count, 2), dtype=np.float64)
        mean = np.zeros(count, dtype=np.float64)
        gaussian = np.zeros(count, dtype=np.float64)
        curvature_validity = np.zeros(count, dtype=np.bool_)
        feature_sets: list[tuple[ClosestFeature, ...]] = [() for _ in range(count)]
        feature_id_sets: list[tuple[str, ...]] = [() for _ in range(count)]
        if evaluated is not None:
            height[valid_indices] = evaluated.height
            points[valid_indices] = evaluated.points
            gradient[valid_indices] = evaluated.gradient
            normal[valid_indices] = evaluated.normal
            height_validity[valid_indices] &= evaluated.validity
            nonsmooth[valid_indices] = evaluated.nonsmooth_mask
            if evaluated.hessian is not None:
                hessian[valid_indices] = evaluated.hessian
                hessian_validity[valid_indices] = evaluated.hessian_validity
            if evaluated.principal_curvatures is not None:
                principal[valid_indices] = evaluated.principal_curvatures
                mean[valid_indices] = evaluated.mean_curvature
                gaussian[valid_indices] = evaluated.gaussian_curvature
                curvature_validity[valid_indices] = evaluated.curvature_validity
            for local_index, global_index in enumerate(valid_indices):
                feature_id_sets[global_index] = evaluated.feature_sets[local_index]
                if not evaluated.feature_sets[local_index]:
                    continue
                normals = evaluated.one_sided_normals[local_index]
                if not normals:
                    vector = evaluated.normal[local_index]
                    normals = ((float(vector[0]), float(vector[1]), float(vector[2])),)
                point = evaluated.points[local_index]
                feature_sets[global_index] = (
                    ClosestFeature(
                        feature_id="+".join(evaluated.feature_sets[local_index]),
                        feature_type="nonsmooth_height_feature_set",
                        point_mm=(float(point[0]), float(point[1]), float(point[2])),
                        outward_normals=normals,
                        signed_distance_mm=0.0,
                        domain_status=classified.status[global_index],
                        quality_status=QualityStatus.NONSMOOTH_FEATURE_SET,
                        residual_mm=0.0,
                        error_bound_mm=0.0,
                    ),
                )
        quality = tuple(
            QualityStatus.GEOMETRY_UNCERTAIN
            if not height_validity[index]
            else QualityStatus.NONSMOOTH_FEATURE_SET
            if nonsmooth[index]
            else QualityStatus.RESOLUTION_REFINEMENT_REQUIRED
            if refinement_required
            else QualityStatus.TRUSTED_FOR_DECLARED_SCALE
            for index in range(count)
        )
        represented_quality = (
            QualityStatus.RESOLUTION_REFINEMENT_REQUIRED
            if refinement_required
            else QualityStatus.TRUSTED_FOR_DECLARED_SCALE
        )
        fields: list[FieldQueryResult] = [
            _field_result(
                "height_mm",
                height if height_validity.any() else None,
                height_validity,
                QueryCapability.EXACT,
                "mm",
                self.realization.surface_frame_id,
                "surface_frame_origin",
                represented_quality,
                omitted_height_bound,
            ),
            _field_result(
                "surface_point_mm",
                points if height_validity.any() else None,
                height_validity,
                QueryCapability.EXACT,
                "mm",
                self.realization.surface_frame_id,
                "surface_frame_origin",
                represented_quality,
                omitted_height_bound,
            ),
        ]
        if derivative_order >= 1:
            fields.extend(
                (
                    _field_result(
                        "gradient",
                        gradient if height_validity.any() else None,
                        height_validity,
                        QueryCapability.EXACT,
                        "1",
                        self.realization.surface_frame_id,
                        "surface_frame_origin",
                        represented_quality,
                        omitted_slope_bound,
                    ),
                    _field_result(
                        "outward_normal",
                        normal if height_validity.any() else None,
                        height_validity,
                        QueryCapability.EXACT,
                        "1",
                        self.realization.surface_frame_id,
                        "surface_frame_origin",
                        represented_quality,
                        omitted_slope_bound,
                    ),
                )
            )
        if derivative_order >= 2:
            fields.extend(
                (
                    _field_result(
                        "hessian_per_mm",
                        hessian if hessian_validity.any() else None,
                        hessian_validity,
                        QueryCapability.EXACT,
                        "mm^-1",
                        self.realization.surface_frame_id,
                        "surface_frame_origin",
                        QualityStatus.NONSMOOTH_FEATURE_SET
                        if nonsmooth.any()
                        else represented_quality,
                    ),
                    _field_result(
                        "principal_curvature_per_mm",
                        principal if curvature_validity.any() else None,
                        curvature_validity,
                        QueryCapability.EXACT,
                        "mm^-1",
                        self.realization.surface_frame_id,
                        "surface_frame_origin",
                        QualityStatus.NONSMOOTH_FEATURE_SET
                        if nonsmooth.any()
                        else represented_quality,
                    ),
                    _field_result(
                        "mean_curvature_per_mm",
                        mean if curvature_validity.any() else None,
                        curvature_validity,
                        QueryCapability.EXACT,
                        "mm^-1",
                        self.realization.surface_frame_id,
                        "surface_frame_origin",
                        QualityStatus.NONSMOOTH_FEATURE_SET
                        if nonsmooth.any()
                        else represented_quality,
                    ),
                    _field_result(
                        "gaussian_curvature_per_mm2",
                        gaussian if curvature_validity.any() else None,
                        curvature_validity,
                        QueryCapability.EXACT,
                        "mm^-2",
                        self.realization.surface_frame_id,
                        "surface_frame_origin",
                        QualityStatus.NONSMOOTH_FEATURE_SET
                        if nonsmooth.any()
                        else represented_quality,
                    ),
                )
            )
        fields.append(
            _field_result(
                "nonsmooth_mask",
                nonsmooth,
                height_validity,
                QueryCapability.EXACT,
                "1",
                self.realization.surface_frame_id,
                "surface_frame_origin",
                QualityStatus.NONSMOOTH_FEATURE_SET if nonsmooth.any() else represented_quality,
            )
        )
        return self._response(
            operation="height_differential",
            requested={
                "coordinates_mm": coordinates,
                "derivative_order": derivative_order,
                "q_max_rad_per_mm": q_max_rad_per_mm,
            },
            capability=QueryCapability.EXACT
            if height_validity.any()
            else QueryCapability.UNAVAILABLE,
            method_id=(
                "M01_RANDOM_ACCESS_BAND_LIMITED_EVALUATOR"
                if isinstance(self.evaluator, _SyntheticEvaluatorAdapter)
                else f"M01_ANALYTIC_{self.evaluator.family.value.upper()}"
            ),
            domain=classified,
            quality_status=quality,
            quality_mask=height_validity,
            fields=tuple(fields),
            convergence=(
                ConvergenceLevel.REFINEMENT_REQUIRED
                if refinement_required
                else ConvergenceLevel.CONVERGED
                if isinstance(self.evaluator, _SyntheticEvaluatorAdapter)
                else ConvergenceLevel.ANALYTIC
            ),
            error_bound=omitted_height_bound,
            feature_sets=tuple(feature_sets),
            metadata=(
                ("nonsmooth_feature_ids", tuple(feature_id_sets)),
                ("omitted_height_bound_mm", omitted_height_bound),
                ("omitted_slope_bound", omitted_slope_bound),
                (
                    "represented_band",
                    "synthetic_q_cutoff"
                    if isinstance(self.evaluator, _SyntheticEvaluatorAdapter)
                    else "analytic_full_definition",
                ),
            ),
            mapped_if_wrapped=True,
        )

    def query_closest_features(
        self,
        points_mm: ArrayLike,
        *,
        requested_tolerance_mm: float | None = None,
        co_minimal_tolerance_mm: float = 1.0e-9,
        maximum_global_cells: int = 20_000,
    ) -> QueryResponse:
        points = _xyz_points(points_mm)
        _validate_closest_options(
            requested_tolerance_mm, co_minimal_tolerance_mm, maximum_global_cells
        )
        classified = self._domain(points[:, :2])
        entry = self.realization.capability_manifest.for_operation("closest_features")
        declared = QueryCapability.UNAVAILABLE if entry is None else entry.capability
        all_features: list[tuple[ClosestFeature, ...]] = [() for _ in points]
        representative = np.zeros((len(points), 3), dtype=np.float64)
        minimum_distance = np.zeros(len(points), dtype=np.float64)
        validity = np.zeros(len(points), dtype=np.bool_)
        residuals: list[float] = []
        errors: list[float] = []
        global_cells: list[int] = []
        valid_indices = np.flatnonzero(classified.validity)
        approximate_results: dict[int, tuple[list[_Candidate], float, float, int]] = {}
        if declared is not QueryCapability.EXACT and valid_indices.size:
            mapped_points = points[valid_indices].copy()
            mapped_points[:, :2] = classified.mapped_coordinates_mm[valid_indices]
            approximate_results = dict(
                zip(
                    (int(index) for index in valid_indices),
                    _approximate_candidates_many(
                        self.evaluator,
                        mapped_points,
                        requested_tolerance_mm=requested_tolerance_mm,
                        co_minimal_tolerance_mm=co_minimal_tolerance_mm,
                        maximum_global_cells=maximum_global_cells,
                    ),
                    strict=True,
                )
            )
        for index in valid_indices:
            point = points[index].copy()
            point[:2] = classified.mapped_coordinates_mm[index]
            if declared is QueryCapability.EXACT:
                candidates = _exact_candidates(self.evaluator, point, co_minimal_tolerance_mm)
                residual = 0.0
                error = 0.0
                cells = 0
            else:
                candidates, residual, error, cells = approximate_results[int(index)]
            if not candidates:
                continue
            signed_sign = _inside_sign(self.evaluator, point)
            distances = [math.dist(item.point, tuple(point)) for item in candidates]
            minimum = min(distances)
            selected = [
                item
                for item, distance in zip(candidates, distances, strict=True)
                if distance <= minimum + co_minimal_tolerance_mm
            ]
            selected.sort(key=lambda item: (item.feature_id, item.point))
            converted = tuple(
                ClosestFeature(
                    feature_id=item.feature_id,
                    feature_type=item.feature_type,
                    point_mm=item.point,
                    outward_normals=item.normals,
                    signed_distance_mm=signed_sign * minimum,
                    domain_status=classified.status[index],
                    quality_status=(
                        QualityStatus.NONSMOOTH_FEATURE_SET
                        if len(item.normals) > 1 or len(selected) > 1
                        else QualityStatus.TRUSTED_FOR_DECLARED_SCALE
                    ),
                    residual_mm=item.residual if declared is QueryCapability.EXACT else residual,
                    error_bound_mm=item.error_bound if declared is QueryCapability.EXACT else error,
                )
                for item in selected
            )
            all_features[index] = converted
            representative[index] = converted[0].point_mm
            minimum_distance[index] = minimum
            validity[index] = True
            residuals.append(residual)
            errors.append(error)
            global_cells.append(cells)
        quality = tuple(
            QualityStatus.GEOMETRY_UNCERTAIN
            if not validity[index]
            else QualityStatus.NONSMOOTH_FEATURE_SET
            if len(all_features[index]) > 1
            or any(len(item.outward_normals) > 1 for item in all_features[index])
            else QualityStatus.TRUSTED_FOR_DECLARED_SCALE
            for index in range(len(points))
        )
        achieved = max(residuals, default=None)
        error_bound = max(errors, default=None)
        convergence = ConvergenceLevel.ANALYTIC
        if declared is QueryCapability.APPROXIMATE:
            if not validity.any():
                convergence = ConvergenceLevel.FAILED
            elif requested_tolerance_mm is not None and (
                achieved is None
                or error_bound is None
                or max(achieved, error_bound) > requested_tolerance_mm
            ):
                convergence = ConvergenceLevel.REFINEMENT_REQUIRED
            else:
                convergence = ConvergenceLevel.CONVERGED
        capability = declared if validity.any() else QueryCapability.UNAVAILABLE
        fields = (
            _field_result(
                "closest_point_mm",
                representative if validity.any() else None,
                validity,
                capability,
                "mm",
                self.realization.surface_frame_id,
                "surface_frame_origin",
                QualityStatus.NONSMOOTH_FEATURE_SET
                if any(len(item) > 1 for item in all_features)
                else QualityStatus.TRUSTED_FOR_DECLARED_SCALE,
                error_bound,
            ),
            _field_result(
                "minimum_distance_mm",
                minimum_distance if validity.any() else None,
                validity,
                capability,
                "mm",
                self.realization.surface_frame_id,
                "query_point",
                QualityStatus.TRUSTED_FOR_DECLARED_SCALE,
                error_bound,
            ),
        )
        method_id = entry.method_id if entry is not None else "M01_QUERY_UNAVAILABLE"
        return self._response(
            operation="closest_features",
            requested={"points_mm": points, "co_minimal_tolerance_mm": co_minimal_tolerance_mm},
            capability=capability,
            method_id=method_id,
            domain=classified,
            quality_status=quality,
            quality_mask=validity,
            fields=fields,
            convergence=convergence,
            requested_tolerance=requested_tolerance_mm,
            achieved_residual=achieved,
            error_bound=error_bound,
            feature_sets=tuple(all_features),
            metadata=(
                ("global_candidate_coverage", declared is not QueryCapability.UNAVAILABLE),
                ("global_bound_cells_by_point", tuple(global_cells)),
                (
                    "representative_policy",
                    "first canonical feature; co-minimal features are never averaged",
                ),
            ),
            mapped_if_wrapped=True,
        )

    def query_signed_distance(
        self,
        points_mm: ArrayLike,
        *,
        requested_tolerance_mm: float | None = None,
        co_minimal_tolerance_mm: float = 1.0e-9,
        maximum_global_cells: int = 20_000,
        _precomputed_closest_response: QueryResponse | None = None,
    ) -> QueryResponse:
        points = _xyz_points(points_mm)
        if _precomputed_closest_response is None:
            closest = self.query_closest_features(
                points,
                requested_tolerance_mm=requested_tolerance_mm,
                co_minimal_tolerance_mm=co_minimal_tolerance_mm,
                maximum_global_cells=maximum_global_cells,
            )
        else:
            closest = _validate_precomputed_closest_response(
                self,
                points,
                _precomputed_closest_response,
                requested_tolerance_mm=requested_tolerance_mm,
                co_minimal_tolerance_mm=co_minimal_tolerance_mm,
                maximum_global_cells=maximum_global_cells,
            )
        values = np.zeros(len(closest.domain_status), dtype=np.float64)
        validity = closest.quality_mask.copy()
        for index, items in enumerate(closest.feature_sets):
            if items:
                values[index] = items[0].signed_distance_mm
        field = _field_result(
            "signed_distance_mm",
            values if validity.any() else None,
            validity,
            closest.capability,
            "mm",
            self.realization.surface_frame_id,
            "solid_omega_h_outside_positive",
            closest.trusted_scale_status,
            closest.error_bound,
        )
        return self._response(
            operation="signed_distance",
            requested={"points_mm": points},
            capability=closest.capability,
            method_id=closest.method_id,
            domain=DomainClassification(
                points[:, :2],
                closest.mapped_coordinates_mm
                if closest.mapped_coordinates_mm is not None
                else points[:, :2],
                closest.domain_status,
                closest.quality_mask,
            ),
            quality_status=closest.quality_status,
            quality_mask=validity,
            fields=(field,),
            convergence=closest.convergence_level,
            requested_tolerance=closest.requested_tolerance,
            achieved_residual=closest.achieved_residual,
            error_bound=closest.error_bound,
            feature_sets=closest.feature_sets,
            metadata=closest.metadata,
            mapped_if_wrapped=closest.mapped_coordinates_mm is not None,
            reference_semantics="signed distance to Omega_h={z<=h}; outside positive",
        )

    def query_neighborhood(
        self,
        bounds_mm: tuple[float, float, float, float],
        *,
        grid_size: int = 33,
    ) -> QueryResponse:
        if len(bounds_mm) != 4 or not all(math.isfinite(item) for item in bounds_mm):
            raise ContractViolation("neighborhood bounds must be four finite numbers")
        x_min, x_max, y_min, y_max = bounds_mm
        if x_max <= x_min or y_max <= y_min:
            raise ContractViolation("neighborhood bounds must have positive extent")
        if grid_size < 3 or grid_size > 1025:
            raise ContractViolation("neighborhood grid_size must be in [3, 1025]")
        corners = np.array(
            [[x_min, y_min], [x_min, y_max], [x_max, y_min], [x_max, y_max]],
            dtype=np.float64,
        )
        classified = self._domain(corners)
        valid = np.array([classified.validity.all()], dtype=np.bool_)
        height_bounds = np.zeros(2, dtype=np.float64)
        slope_bound = np.array([self.evaluator.global_slope_bound()], dtype=np.float64)
        covering_error = 0.0
        if valid[0]:
            xs = np.linspace(x_min, x_max, grid_size, dtype=np.float64)
            ys = np.linspace(y_min, y_max, grid_size, dtype=np.float64)
            xx, yy = np.meshgrid(xs, ys)
            evaluation = self.evaluator.evaluate(xx.ravel(), yy.ravel(), derivative_order=1)
            radius = 0.5 * math.hypot(
                (x_max - x_min) / (grid_size - 1),
                (y_max - y_min) / (grid_size - 1),
            )
            covering_error = self.evaluator.global_slope_bound() * radius
            height_bounds[:] = (
                float(np.min(evaluation.height)) - covering_error,
                float(np.max(evaluation.height)) + covering_error,
            )
        fields = (
            _field_result(
                "height_bounds_mm",
                height_bounds if valid[0] else None,
                valid,
                QueryCapability.APPROXIMATE,
                "mm",
                self.realization.surface_frame_id,
                "surface_frame_origin",
                QualityStatus.TRUSTED_FOR_DECLARED_SCALE,
                covering_error if valid[0] else None,
            ),
            _field_result(
                "slope_norm_upper_bound",
                slope_bound if valid[0] else None,
                valid,
                QueryCapability.EXACT,
                "1",
                self.realization.surface_frame_id,
                "surface_frame_origin",
                QualityStatus.TRUSTED_FOR_DECLARED_SCALE,
            ),
            _field_result(
                "omitted_height_bound_mm",
                np.array([0.0]) if valid[0] else None,
                valid,
                QueryCapability.EXACT,
                "mm",
                self.realization.surface_frame_id,
                "analytic_definition",
                QualityStatus.TRUSTED_FOR_DECLARED_SCALE,
            ),
        )
        point_domain = DomainClassification(
            corners,
            classified.mapped_coordinates_mm,
            (DomainStatus.IN_DOMAIN if valid[0] else DomainStatus.OUT_OF_DOMAIN,),
            valid,
        )
        return self._response(
            operation="neighborhood",
            requested={"bounds_mm": bounds_mm, "grid_size": grid_size},
            capability=QueryCapability.APPROXIMATE if valid[0] else QueryCapability.UNAVAILABLE,
            method_id=(
                "M01_SYNTHETIC_LIPSCHITZ_NEIGHBORHOOD"
                if isinstance(self.evaluator, _SyntheticEvaluatorAdapter)
                else "M01_ANALYTIC_LIPSCHITZ_NEIGHBORHOOD"
            ),
            domain=point_domain,
            quality_status=(
                QualityStatus.TRUSTED_FOR_DECLARED_SCALE
                if valid[0]
                else QualityStatus.GEOMETRY_UNCERTAIN,
            ),
            quality_mask=valid,
            fields=fields,
            convergence=ConvergenceLevel.CONVERGED if valid[0] else ConvergenceLevel.FAILED,
            achieved_residual=0.0 if valid[0] else None,
            error_bound=covering_error if valid[0] else None,
            metadata=(
                ("candidate_feature_ids", _family_feature_ids(self.evaluator.family)),
                (
                    "represented_band",
                    "synthetic_full_declared_band"
                    if isinstance(self.evaluator, _SyntheticEvaluatorAdapter)
                    else "analytic_full_definition",
                ),
                ("recommended_next_lod", None),
                (
                    "no_surface_intersection_certification",
                    "requires a caller-supplied query volume",
                ),
            ),
        )

    def query_spherical_envelope_or_clearance(self, *args: Any, **kwargs: Any) -> QueryResponse:
        """Dispatch to the pure complete-sphere geometry module lazily."""

        from .sphere import query_spherical_envelope_or_clearance

        return query_spherical_envelope_or_clearance(self, *args, **kwargs)

    def _response(
        self,
        *,
        operation: str,
        requested: dict[str, Any],
        capability: QueryCapability,
        method_id: str,
        domain: DomainClassification,
        quality_status: tuple[QualityStatus, ...],
        quality_mask: BoolArray,
        fields: tuple[FieldQueryResult, ...],
        convergence: ConvergenceLevel,
        requested_tolerance: float | None = None,
        achieved_residual: float | None = None,
        error_bound: float | None = None,
        feature_sets: tuple[tuple[ClosestFeature, ...], ...] = (),
        metadata: tuple[tuple[str, Any], ...] = (),
        mapped_if_wrapped: bool = False,
        reference_semantics: str = "height-field surface in the declared surface frame",
    ) -> QueryResponse:
        requested_hash = semantic_hash(requested)
        query_id = stable_content_id(
            "surface_query",
            {
                "surface_realization_id": self.realization.surface_realization_id,
                "operation": operation,
                "requested_hash": requested_hash,
                "query_contract_version": QUERY_CONTRACT_VERSION,
                "method_id": method_id,
            },
        )
        if capability is QueryCapability.UNAVAILABLE:
            if any(item is DomainStatus.OUT_OF_DOMAIN for item in domain.status):
                status = unavailable_status(
                    M01ReasonCode.OUT_OF_DOMAIN,
                    "query is outside the logical domain and ERROR boundary mode forbids mapping",
                )
            else:
                status = unavailable_status(
                    M01ReasonCode.QUERY_CAPABILITY_UNAVAILABLE,
                    "the requested surface geometry field is unavailable",
                )
        else:
            status = supported_status(
                M01ReasonCode.RESOLUTION_REFINEMENT_REQUIRED
                if QualityStatus.RESOLUTION_REFINEMENT_REQUIRED in quality_status
                else M01ReasonCode.OK
            )
        mapped = None
        if mapped_if_wrapped and any(item is DomainStatus.WRAPPED for item in domain.status):
            mapped = domain.mapped_coordinates_mm
        return QueryResponse(
            surface_realization_id=self.realization.surface_realization_id,
            surface_spec_id=self.realization.surface_spec_id,
            query_contract_version=QUERY_CONTRACT_VERSION,
            query_id=query_id,
            operation=operation,
            requested_points_or_region_hash=requested_hash,
            capability=capability,
            reference_semantics=reference_semantics,
            method_id=method_id,
            method_version="1.0.0",
            status=status,
            domain_status=domain.status,
            mapped_coordinates_mm=mapped,
            quality_status=quality_status,
            quality_mask=quality_mask,
            trusted_scale_status=(
                QualityStatus.RESOLUTION_REFINEMENT_REQUIRED
                if QualityStatus.RESOLUTION_REFINEMENT_REQUIRED in quality_status
                else QualityStatus.MISSING_SOURCE_DATA
                if QualityStatus.MISSING_SOURCE_DATA in quality_status
                else QualityStatus.TRUSTED_FOR_DECLARED_SCALE
                if quality_mask.any()
                else QualityStatus.GEOMETRY_UNCERTAIN
            ),
            requested_tolerance=requested_tolerance,
            achieved_residual=achieved_residual,
            error_bound=error_bound,
            convergence_level=convergence,
            units="N-mm-MPa",
            frame_id=self.realization.surface_frame_id,
            reference_point="surface_frame_origin",
            fields=fields,
            feature_sets=feature_sets,
            metadata=tuple(sorted(metadata, key=lambda item: item[0])),
        )


AnalyticQueryHandle = SurfaceQueryHandle
SurfaceQuery = SurfaceQueryHandle


def as_surface_query(handle: Any) -> SurfaceQueryHandle:
    """Adapt a provider handle without importing or depending on its class."""

    return handle if isinstance(handle, SurfaceQueryHandle) else SurfaceQueryHandle(handle)


def _field_result(
    field_id: str,
    values: ArrayLike | None,
    validity: BoolArray,
    capability: QueryCapability,
    unit: str,
    frame_id: str,
    reference_point: str,
    quality: QualityStatus,
    error_bound: float | None = None,
) -> FieldQueryResult:
    valid = np.array(validity, dtype=np.bool_, copy=True)
    if values is None:
        status = unavailable_status(
            M01ReasonCode.QUERY_CAPABILITY_UNAVAILABLE,
            f"field {field_id} is unavailable at every requested item",
        )
        actual_capability = QueryCapability.UNAVAILABLE
    else:
        status = supported_status()
        actual_capability = capability
    return FieldQueryResult(
        field_id=field_id,
        values=None if values is None else np.asarray(values),
        validity=valid,
        status=status,
        capability=actual_capability,
        unit=unit,
        frame_id=frame_id,
        reference_point=reference_point,
        quality_status=quality,
        error_bound=error_bound,
    )


def _validate_closest_options(
    tolerance: float | None, co_minimal: float, maximum_global_cells: int
) -> None:
    if tolerance is not None and (not math.isfinite(tolerance) or tolerance <= 0.0):
        raise ContractViolation("requested_tolerance_mm must be finite and positive")
    if not math.isfinite(co_minimal) or co_minimal < 0.0:
        raise ContractViolation("co_minimal_tolerance_mm must be finite and non-negative")
    if maximum_global_cells < 16 or maximum_global_cells > 1_000_000:
        raise ContractViolation("maximum_global_cells must be in [16, 1000000]")


def _validate_precomputed_closest_response(
    handle: SurfaceQueryHandle,
    points: FloatArray,
    response: QueryResponse,
    *,
    requested_tolerance_mm: float | None,
    co_minimal_tolerance_mm: float,
    maximum_global_cells: int,
) -> QueryResponse:
    """Validate an internal same-call closest result before deterministic reuse."""

    _validate_closest_options(
        requested_tolerance_mm,
        co_minimal_tolerance_mm,
        maximum_global_cells,
    )
    expected_request_hash = semantic_hash(
        {
            "points_mm": points,
            "co_minimal_tolerance_mm": co_minimal_tolerance_mm,
        }
    )
    metadata = dict(response.metadata)
    cells = metadata.get("global_bound_cells_by_point")
    if isinstance(cells, tuple):
        valid_cells = len(cells) <= len(points) and all(
            isinstance(value, int) and 0 <= value <= maximum_global_cells + 3 for value in cells
        )
    else:
        valid_cells = False
    if (
        response.operation != "closest_features"
        or response.surface_realization_id != handle.realization.surface_realization_id
        or response.surface_spec_id != handle.realization.surface_spec_id
        or response.requested_points_or_region_hash != expected_request_hash
        or response.requested_tolerance != requested_tolerance_mm
        or len(response.domain_status) != len(points)
        or not valid_cells
    ):
        raise ContractViolation(
            "precomputed closest response does not match the signed-distance request"
        )
    return response


def _inside_sign(evaluator: GraphEvaluator, query: FloatArray) -> float:
    height = float(evaluator.evaluate(query[0], query[1], derivative_order=0).height[0])
    return 1.0 if query[2] >= height else -1.0


def _normal_tuple(gradient: FloatArray) -> tuple[float, float, float]:
    vector = np.array([-gradient[0], -gradient[1], 1.0], dtype=np.float64)
    vector /= np.linalg.norm(vector)
    return float(vector[0]), float(vector[1]), float(vector[2])


def _exact_candidates(
    evaluator: GraphEvaluator, query: FloatArray, tolerance: float
) -> list[_Candidate]:
    family = evaluator.family
    if family in (SurfaceFamily.PLANE, SurfaceFamily.SLOPE_PLANE):
        p = evaluator.parameters
        gradient = np.array(
            [float(p.get("slope_x", 0.0)), float(p.get("slope_y", 0.0))], dtype=np.float64
        )
        return _affine_piece_candidates(
            evaluator, query, [("plane_face", None, None, gradient)], tolerance
        )
    if family in (SurfaceFamily.GROOVE_V, SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH):
        return _piecewise_affine_candidates(evaluator, query, tolerance)
    if family is SurfaceFamily.GROOVE_CIRCULAR:
        return _circular_groove_candidates(evaluator, query, tolerance)
    if family in (SurfaceFamily.SPHERICAL_CAP, SurfaceFamily.SPHERICAL_BOWL):
        return _spherical_fixture_candidates(evaluator, query, tolerance)
    raise ContractViolation(f"family {family.value} did not declare exact primitive closest")


def _domain_polygon(domain: Domain2D) -> list[FloatArray]:
    return [
        np.array([domain.x_min_mm, domain.y_min_mm]),
        np.array([domain.x_max_mm, domain.y_min_mm]),
        np.array([domain.x_max_mm, domain.y_max_mm]),
        np.array([domain.x_min_mm, domain.y_max_mm]),
    ]


def _clip_polygon(
    polygon: list[FloatArray], normal: FloatArray, bound: float, *, keep_greater: bool
) -> list[FloatArray]:
    if not polygon:
        return []

    def inside(point: FloatArray) -> bool:
        value = float(np.dot(normal, point) - bound)
        return value >= -1.0e-12 if keep_greater else value <= 1.0e-12

    result: list[FloatArray] = []
    previous = polygon[-1]
    previous_inside = inside(previous)
    for current in polygon:
        current_inside = inside(current)
        if current_inside != previous_inside:
            direction = current - previous
            denominator = float(np.dot(normal, direction))
            if denominator != 0.0:
                fraction = (bound - float(np.dot(normal, previous))) / denominator
                result.append(previous + np.clip(fraction, 0.0, 1.0) * direction)
        if current_inside:
            result.append(current)
        previous = current
        previous_inside = current_inside
    return result


def _point_in_convex_polygon(point: FloatArray, polygon: list[FloatArray]) -> bool:
    if len(polygon) < 3:
        return False
    signs: list[float] = []
    for first, second in zip(polygon, (*polygon[1:], polygon[0]), strict=True):
        edge = second - first
        signs.append(float(edge[0] * (point[1] - first[1]) - edge[1] * (point[0] - first[0])))
    return min(signs) >= -1.0e-10 or max(signs) <= 1.0e-10


def _closest_segment(query: FloatArray, first: FloatArray, second: FloatArray) -> FloatArray:
    direction = second - first
    denominator = float(np.dot(direction, direction))
    fraction = 0.0 if denominator == 0.0 else float(np.dot(query - first, direction) / denominator)
    fraction = min(1.0, max(0.0, fraction))
    return np.asarray(first + fraction * direction, dtype=np.float64)


def _affine_polygon_candidate(
    query: FloatArray,
    polygon: list[FloatArray],
    intercept: float,
    gradient: FloatArray,
    feature_id: str,
) -> _Candidate | None:
    if len(polygon) < 3:
        return None
    matrix = np.eye(2) + np.outer(gradient, gradient)
    projected_xy = np.linalg.solve(matrix, query[:2] + gradient * (query[2] - intercept))
    normal = _normal_tuple(gradient)
    if _point_in_convex_polygon(projected_xy, polygon):
        point = np.array(
            [projected_xy[0], projected_xy[1], intercept + float(np.dot(gradient, projected_xy))]
        )
        normal_component = float(np.dot(query - point, np.array(normal)))
        residual = float(np.linalg.norm(query - point - normal_component * np.array(normal)))
        return _Candidate(tuple(point), (normal,), feature_id, "analytic_face", residual, 0.0)
    lifted = [
        np.array([item[0], item[1], intercept + float(np.dot(gradient, item))]) for item in polygon
    ]
    candidates = [
        _closest_segment(query, first, second)
        for first, second in zip(lifted, (*lifted[1:], lifted[0]), strict=True)
    ]
    point = min(candidates, key=lambda item: float(np.linalg.norm(item - query)))
    return _Candidate(tuple(point), (normal,), feature_id, "analytic_patch_edge", 0.0, 0.0)


def _affine_piece_candidates(
    evaluator: GraphEvaluator,
    query: FloatArray,
    pieces: Iterable[tuple[str, float | None, float | None, FloatArray]],
    tolerance: float,
) -> list[_Candidate]:
    base_polygon = _domain_polygon(evaluator.spec.logical_domain)
    p = evaluator.parameters
    center = np.array([float(p.get("center_x_mm", 0.0)), float(p.get("center_y_mm", 0.0))])
    _, across = (np.array([1.0, 0.0]), np.array([1.0, 0.0]))
    if "direction_rad" in p:
        direction = float(p["direction_rad"])
        across = np.array([-math.sin(direction), math.cos(direction)])
    result: list[_Candidate] = []
    for feature_id, lower, upper, gradient in pieces:
        polygon = [item.copy() for item in base_polygon]
        center_projection = float(np.dot(across, center))
        if lower is not None:
            polygon = _clip_polygon(polygon, across, center_projection + lower, keep_greater=True)
        if upper is not None:
            polygon = _clip_polygon(polygon, across, center_projection + upper, keep_greater=False)
        if evaluator.family is SurfaceFamily.SLOPE_PLANE:
            intercept = float(p["offset_mm"])
        elif evaluator.family is SurfaceFamily.PLANE:
            intercept = float(p["offset_mm"])
        else:
            sample = polygon[0] if polygon else np.zeros(2)
            height = float(evaluator.evaluate(sample[0], sample[1], derivative_order=0).height[0])
            intercept = height - float(np.dot(gradient, sample))
        candidate = _affine_polygon_candidate(query, polygon, intercept, gradient, feature_id)
        if candidate is not None:
            result.append(candidate)
    return _co_minimal_candidates(result, query, tolerance)


def _piecewise_affine_candidates(
    evaluator: GraphEvaluator, query: FloatArray, tolerance: float
) -> list[_Candidate]:
    p = evaluator.parameters
    direction = float(p["direction_rad"])
    across = np.array([-math.sin(direction), math.cos(direction)], dtype=np.float64)
    if evaluator.family is SurfaceFamily.GROOVE_V:
        width = float(p["half_width_mm"])
        slope = float(p["depth_mm"]) / width
        pieces = [
            ("outside_left_face", None, -width, np.zeros(2)),
            ("v_left_face", -width, 0.0, -slope * across),
            ("v_right_face", 0.0, width, slope * across),
            ("outside_right_face", width, None, np.zeros(2)),
        ]
    else:
        slope = float(p["ridge_slope"])
        pieces = [
            ("switch_face_negative", None, 0.0, -slope * across),
            ("switch_face_positive", 0.0, None, slope * across),
        ]
    return _affine_piece_candidates(evaluator, query, pieces, tolerance)


def _circular_groove_candidates(
    evaluator: GraphEvaluator, query: FloatArray, tolerance: float
) -> list[_Candidate]:
    p = evaluator.parameters
    direction = float(p["direction_rad"])
    along = np.array([math.cos(direction), math.sin(direction)])
    across = np.array([-along[1], along[0]])
    center = np.array([float(p["center_x_mm"]), float(p["center_y_mm"])])
    relative = query[:2] - center
    t_value = float(np.dot(along, relative))
    s_value = float(np.dot(across, relative))
    width = float(p["half_width_mm"])
    depth = float(p["depth_mm"])
    radius = (width * width + depth * depth) / (2.0 * depth)
    z_center = float(p["offset_mm"]) + radius - depth
    candidates: list[_Candidate] = []
    radial = np.array([s_value, query[2] - z_center])
    norm = float(np.linalg.norm(radial))
    if norm > 0.0:
        projected = radius * radial / norm
        if projected[1] <= 0.0 and abs(projected[0]) <= width + tolerance:
            xy = center + t_value * along + projected[0] * across
            point = (float(xy[0]), float(xy[1]), float(z_center + projected[1]))
            gradient = (projected[0] / -projected[1]) * across
            candidates.append(
                _Candidate(
                    point,
                    (_normal_tuple(gradient),),
                    "circular_groove_arc",
                    "cylindrical_arc_face",
                    0.0,
                    0.0,
                )
            )
    for sign, feature_id in ((-1.0, "groove_left_shoulder"), (1.0, "groove_right_shoulder")):
        xy = center + t_value * along + sign * width * across
        candidates.append(
            _Candidate(
                (float(xy[0]), float(xy[1]), float(p["offset_mm"])),
                ((0.0, 0.0, 1.0),),
                feature_id,
                "cylindrical_arc_edge",
                0.0,
                0.0,
            )
        )
    if abs(s_value) >= width:
        candidates.append(
            _Candidate(
                (float(query[0]), float(query[1]), float(p["offset_mm"])),
                ((0.0, 0.0, 1.0),),
                "outside_plane",
                "analytic_face",
                0.0,
                0.0,
            )
        )
    return _co_minimal_candidates(candidates, query, tolerance)


def _spherical_fixture_candidates(
    evaluator: GraphEvaluator, query: FloatArray, tolerance: float
) -> list[_Candidate]:
    p = evaluator.parameters
    center_xy = np.array([float(p["center_x_mm"]), float(p["center_y_mm"])])
    radius = float(p["radius_mm"])
    aperture = float(p["aperture_radius_mm"])
    root_aperture = math.sqrt(radius * radius - aperture * aperture)
    sign = 1.0 if evaluator.family is SurfaceFamily.SPHERICAL_CAP else -1.0
    center = np.array([center_xy[0], center_xy[1], float(p["offset_mm"]) - sign * root_aperture])
    radial = query - center
    norm = float(np.linalg.norm(radial))
    candidates: list[_Candidate] = []
    if norm > 0.0:
        projected = radius * radial / norm
        if sign * projected[2] >= 0.0 and np.linalg.norm(projected[:2]) <= aperture + tolerance:
            point = center + projected
            normal = sign * projected / radius
            candidates.append(
                _Candidate(
                    (float(point[0]), float(point[1]), float(point[2])),
                    ((float(normal[0]), float(normal[1]), float(normal[2])),),
                    "spherical_patch",
                    "spherical_face",
                    0.0,
                    0.0,
                )
            )
    radial_xy = query[:2] - center_xy
    radial_xy_norm = float(np.linalg.norm(radial_xy))
    directions = [np.array([1.0, 0.0])]
    if radial_xy_norm > 0.0:
        directions = [radial_xy / radial_xy_norm]
    elif tolerance > 0.0:
        directions = [
            np.array([1.0, 0.0]),
            np.array([-1.0, 0.0]),
            np.array([0.0, 1.0]),
            np.array([0.0, -1.0]),
        ]
    for direction in directions:
        xy = center_xy + aperture * direction
        candidates.append(
            _Candidate(
                (float(xy[0]), float(xy[1]), float(p["offset_mm"])),
                ((0.0, 0.0, 1.0),),
                "aperture_ring",
                "circular_edge",
                0.0,
                0.0,
            )
        )
    if radial_xy_norm >= aperture:
        candidates.append(
            _Candidate(
                (float(query[0]), float(query[1]), float(p["offset_mm"])),
                ((0.0, 0.0, 1.0),),
                "outside_plane",
                "analytic_face",
                0.0,
                0.0,
            )
        )
    return _co_minimal_candidates(candidates, query, tolerance)


def _co_minimal_candidates(
    candidates: Sequence[_Candidate], query: FloatArray, tolerance: float
) -> list[_Candidate]:
    if not candidates:
        return []
    distances = [math.dist(item.point, tuple(query)) for item in candidates]
    minimum = min(distances)
    selected = [
        item
        for item, distance in zip(candidates, distances, strict=True)
        if distance <= minimum + tolerance
    ]
    grouped: list[_Candidate] = []
    for candidate in selected:
        match = next(
            (item for item in grouped if math.dist(item.point, candidate.point) <= tolerance), None
        )
        if match is None:
            grouped.append(candidate)
            continue
        normals = tuple(sorted(set((*match.normals, *candidate.normals))))
        grouped.remove(match)
        grouped.append(
            _Candidate(
                match.point,
                normals,
                "+".join(sorted(set((match.feature_id, candidate.feature_id)))),
                "coincident_primitive_feature_set",
                max(match.residual, candidate.residual),
                max(match.error_bound, candidate.error_bound),
            )
        )
    return grouped


def _approximate_candidates(
    evaluator: GraphEvaluator,
    query: FloatArray,
    *,
    requested_tolerance_mm: float | None,
    co_minimal_tolerance_mm: float,
    maximum_global_cells: int,
) -> tuple[list[_Candidate], float, float, int]:
    return _approximate_candidates_many(
        evaluator,
        np.asarray(query, dtype=np.float64).reshape(1, 3),
        requested_tolerance_mm=requested_tolerance_mm,
        co_minimal_tolerance_mm=co_minimal_tolerance_mm,
        maximum_global_cells=maximum_global_cells,
    )[0]


def _approximate_candidates_many(
    evaluator: GraphEvaluator,
    queries: FloatArray,
    *,
    requested_tolerance_mm: float | None,
    co_minimal_tolerance_mm: float,
    maximum_global_cells: int,
) -> tuple[tuple[list[_Candidate], float, float, int], ...]:
    query_array = np.asarray(queries, dtype=np.float64)
    if query_array.ndim != 2 or query_array.shape[1] != 3 or len(query_array) == 0:
        raise ValueError("approximate closest queries must have shape (N, 3), N >= 1")
    local_results = _approximate_local_candidates_many(
        evaluator,
        query_array,
        co_minimal_tolerance_mm=co_minimal_tolerance_mm,
    )
    best_distances = np.asarray(
        [
            min(math.dist(item.point, tuple(query)) for item in local)
            for query, (local, _) in zip(query_array, local_results, strict=True)
        ],
        dtype=np.float64,
    )
    target = requested_tolerance_mm if requested_tolerance_mm is not None else 1.0e-6
    global_results = _adaptive_global_lower_bounds(
        evaluator,
        query_array,
        best_distances,
        target,
        maximum_global_cells,
    )
    results: list[tuple[list[_Candidate], float, float, int]] = []
    for (local, residual), best_distance, (lower, cells) in zip(
        local_results,
        best_distances,
        global_results,
        strict=True,
    ):
        global_error = max(
            float(best_distance) - lower,
            np.finfo(np.float64).eps * max(1.0, float(best_distance)),
        )
        results.append((local, residual, global_error, cells))
    return tuple(results)


def _approximate_local_candidates(
    evaluator: GraphEvaluator,
    query: FloatArray,
    *,
    co_minimal_tolerance_mm: float,
) -> tuple[list[_Candidate], float]:
    starts = _approximate_newton_starts(evaluator, query)
    projected, residuals = _project_graph_newton_many(evaluator, query, starts)
    evaluation = evaluator.evaluate(projected[:, 0], projected[:, 1], derivative_order=2)
    return _projected_local_candidates(
        evaluator,
        query,
        evaluation,
        residuals,
        range(len(projected)),
        co_minimal_tolerance_mm,
    )


def _approximate_local_candidates_many(
    evaluator: GraphEvaluator,
    queries: FloatArray,
    *,
    co_minimal_tolerance_mm: float,
) -> tuple[tuple[list[_Candidate], float], ...]:
    starts_by_query = tuple(_approximate_newton_starts(evaluator, query) for query in queries)
    combined_starts = np.concatenate(starts_by_query, axis=0)
    targets = np.concatenate(
        tuple(
            np.repeat(query[np.newaxis, :], len(starts), axis=0)
            for query, starts in zip(queries, starts_by_query, strict=True)
        ),
        axis=0,
    )
    projected, residuals = _project_graph_newton_pairs(
        evaluator,
        targets,
        combined_starts,
    )
    evaluation = evaluator.evaluate(projected[:, 0], projected[:, 1], derivative_order=2)
    results: list[tuple[list[_Candidate], float]] = []
    offset = 0
    for query, starts in zip(queries, starts_by_query, strict=True):
        stop = offset + len(starts)
        results.append(
            _projected_local_candidates(
                evaluator,
                query,
                evaluation,
                residuals,
                range(offset, stop),
                co_minimal_tolerance_mm,
            )
        )
        offset = stop
    return tuple(results)


def _approximate_newton_starts(
    evaluator: GraphEvaluator,
    query: FloatArray,
) -> FloatArray:
    domain = evaluator.spec.logical_domain
    seeds = [query[:2].copy()]
    p = evaluator.parameters
    if evaluator.family is SurfaceFamily.MULTI_GAUSSIAN_FEATURE:
        seeds.extend(
            np.array([float(item["center_x_mm"]), float(item["center_y_mm"])])
            for item in p["features"]
        )
    elif "center_x_mm" in p:
        seeds.append(np.array([float(p["center_x_mm"]), float(p["center_y_mm"])]))
    grid_axis = np.linspace(0.0, 1.0, 9)
    for alpha in grid_axis:
        for beta in grid_axis:
            seeds.append(
                np.array(
                    [
                        domain.x_min_mm + alpha * domain.width_mm,
                        domain.y_min_mm + beta * domain.height_mm,
                    ]
                )
            )
    seed_array = np.unique(
        np.clip(
            np.array(seeds), [domain.x_min_mm, domain.y_min_mm], [domain.x_max_mm, domain.y_max_mm]
        ),
        axis=0,
    )
    seed_eval = evaluator.evaluate(seed_array[:, 0], seed_array[:, 1])
    seed_distance2 = np.sum((seed_eval.points - query) ** 2, axis=1)
    return seed_array[np.argsort(seed_distance2)[: min(16, len(seed_array))]]


def _projected_local_candidates(
    evaluator: GraphEvaluator,
    query: FloatArray,
    evaluation: AnalyticEvaluation,
    residuals: FloatArray,
    indices: Iterable[int],
    co_minimal_tolerance_mm: float,
) -> tuple[list[_Candidate], float]:
    local: list[_Candidate] = []
    for index in indices:
        evaluated_point = evaluation.points[index]
        point = (
            float(evaluated_point[0]),
            float(evaluated_point[1]),
            float(evaluated_point[2]),
        )
        evaluated_normal = evaluation.normal[index]
        normals = evaluation.one_sided_normals[index] or (
            (
                float(evaluated_normal[0]),
                float(evaluated_normal[1]),
                float(evaluated_normal[2]),
            ),
        )
        feature_ids = evaluation.feature_sets[index] or (f"{evaluator.family.value}_smooth_face",)
        local.append(
            _Candidate(
                point,
                normals,
                "+".join(feature_ids),
                "analytic_graph_candidate",
                float(residuals[index]),
                0.0,
            )
        )
    local = _co_minimal_candidates(local, query, co_minimal_tolerance_mm)
    residual = max((item.residual for item in local), default=0.0)
    return local, residual


def _project_graph_newton(
    evaluator: GraphEvaluator, query: FloatArray, start: FloatArray
) -> tuple[FloatArray, float]:
    domain = evaluator.spec.logical_domain
    lower = np.array([domain.x_min_mm, domain.y_min_mm])
    upper = np.array([domain.x_max_mm, domain.y_max_mm])
    uv = np.clip(np.array(start, dtype=np.float64), lower, upper)
    for _ in range(64):
        value = evaluator.evaluate(uv[0], uv[1], derivative_order=2)
        height = float(value.height[0])
        gradient = value.gradient[0]
        delta_z = height - query[2]
        objective_gradient = uv - query[:2] + delta_z * gradient
        if np.linalg.norm(objective_gradient) <= 1.0e-13 * max(1.0, np.linalg.norm(query)):
            break
        objective_hessian = np.eye(2) + np.outer(gradient, gradient)
        if value.hessian is not None and value.hessian_validity[0]:
            objective_hessian += delta_z * value.hessian[0]
        try:
            step = np.linalg.solve(objective_hessian, objective_gradient)
        except np.linalg.LinAlgError:
            step = objective_gradient / max(np.linalg.norm(objective_gradient), 1.0)
        current_point = value.points[0]
        current_objective = 0.5 * float(np.dot(current_point - query, current_point - query))
        scale = 1.0
        accepted = False
        for _ in range(24):
            trial = np.clip(uv - scale * step, lower, upper)
            trial_value = evaluator.evaluate(trial[0], trial[1], derivative_order=0)
            objective = 0.5 * float(
                np.dot(trial_value.points[0] - query, trial_value.points[0] - query)
            )
            if objective <= current_objective - 1.0e-4 * scale * float(
                np.dot(objective_gradient, step)
            ):
                uv = trial
                accepted = True
                break
            scale *= 0.5
        if not accepted:
            break
        if np.linalg.norm(scale * step) <= 1.0e-13 * max(1.0, np.linalg.norm(uv)):
            break
    value = evaluator.evaluate(uv[0], uv[1], derivative_order=1)
    surface_delta = value.points[0] - query
    normal = value.normal[0]
    tangent = surface_delta - np.dot(surface_delta, normal) * normal
    return uv, float(np.linalg.norm(tangent))


def _project_graph_newton_many(
    evaluator: GraphEvaluator,
    query: FloatArray,
    starts: FloatArray,
) -> tuple[FloatArray, FloatArray]:
    targets = np.repeat(
        np.asarray(query, dtype=np.float64).reshape(1, 3),
        len(starts),
        axis=0,
    )
    return _project_graph_newton_pairs(evaluator, targets, starts)


def _project_graph_newton_pairs(
    evaluator: GraphEvaluator,
    queries: FloatArray,
    starts: FloatArray,
) -> tuple[FloatArray, FloatArray]:
    """Project independent starts while batching evaluator calls.

    The Newton, clipping, Armijo, and stopping rules are deliberately the same
    as :func:`_project_graph_newton`.  Only surface evaluation is batched.  This
    matters for finite-mode synthetic fields: their locked reduction order is
    over modes, so evaluating all active starts together preserves each
    point's ordered sum while avoiding one Python mode loop per start.
    """

    domain = evaluator.spec.logical_domain
    lower = np.array([domain.x_min_mm, domain.y_min_mm])
    upper = np.array([domain.x_max_mm, domain.y_max_mm])
    uv = np.clip(np.asarray(starts, dtype=np.float64), lower, upper).copy()
    query_array = np.asarray(queries, dtype=np.float64)
    if uv.ndim != 2 or uv.shape[1] != 2:
        raise ValueError("Newton starts must have shape (N, 2)")
    if query_array.shape != (len(uv), 3):
        raise ValueError("Newton query targets must have shape (N, 3)")
    active = np.ones(len(uv), dtype=np.bool_)
    query_scales = 1.0e-13 * np.maximum(
        1.0,
        np.linalg.norm(query_array, axis=1),
    )

    for _ in range(64):
        active_indices = np.flatnonzero(active)
        if active_indices.size == 0:
            break
        value = evaluator.evaluate(
            uv[active_indices, 0],
            uv[active_indices, 1],
            derivative_order=2,
        )
        search_indices: list[int] = []
        search_steps: list[FloatArray] = []
        search_gradients: list[FloatArray] = []
        search_objectives: list[float] = []
        for local_index, global_index in enumerate(active_indices):
            query = query_array[global_index]
            height = float(value.height[local_index])
            gradient = value.gradient[local_index]
            delta_z = height - query[2]
            objective_gradient = uv[global_index] - query[:2] + delta_z * gradient
            if np.linalg.norm(objective_gradient) <= query_scales[global_index]:
                active[global_index] = False
                continue
            objective_hessian = np.eye(2) + np.outer(gradient, gradient)
            if value.hessian is not None and value.hessian_validity[local_index]:
                objective_hessian += delta_z * value.hessian[local_index]
            try:
                step = np.linalg.solve(objective_hessian, objective_gradient)
            except np.linalg.LinAlgError:
                step = objective_gradient / max(np.linalg.norm(objective_gradient), 1.0)
            current_point = value.points[local_index]
            current_objective = 0.5 * float(np.dot(current_point - query, current_point - query))
            search_indices.append(int(global_index))
            search_steps.append(step)
            search_gradients.append(objective_gradient)
            search_objectives.append(current_objective)

        if not search_indices:
            continue
        indices = np.asarray(search_indices, dtype=np.int64)
        steps = np.asarray(search_steps, dtype=np.float64)
        gradients = np.asarray(search_gradients, dtype=np.float64)
        objectives = np.asarray(search_objectives, dtype=np.float64)
        scales = np.ones(len(indices), dtype=np.float64)
        accepted = np.zeros(len(indices), dtype=np.bool_)
        pending = np.ones(len(indices), dtype=np.bool_)
        for _ in range(24):
            pending_positions = np.flatnonzero(pending)
            if pending_positions.size == 0:
                break
            pending_indices = indices[pending_positions]
            trials = np.clip(
                uv[pending_indices]
                - scales[pending_positions, np.newaxis] * steps[pending_positions],
                lower,
                upper,
            )
            trial_value = evaluator.evaluate(
                trials[:, 0],
                trials[:, 1],
                derivative_order=0,
            )
            for local_index, position in enumerate(pending_positions):
                query = query_array[indices[position]]
                delta = trial_value.points[local_index] - query
                objective = 0.5 * float(np.dot(delta, delta))
                armijo = objectives[position] - 1.0e-4 * scales[position] * float(
                    np.dot(gradients[position], steps[position])
                )
                if objective <= armijo:
                    uv[indices[position]] = trials[local_index]
                    accepted[position] = True
                    pending[position] = False
                else:
                    scales[position] *= 0.5

        for final_position in range(len(indices)):
            final_global_index = int(indices[final_position])
            if not accepted[final_position] or np.linalg.norm(
                scales[final_position] * steps[final_position]
            ) <= 1.0e-13 * max(1.0, np.linalg.norm(uv[final_global_index])):
                active[final_global_index] = False

    value = evaluator.evaluate(uv[:, 0], uv[:, 1], derivative_order=1)
    residuals = np.empty(len(uv), dtype=np.float64)
    for index in range(len(uv)):
        # Keep the scalar arithmetic order of ``_project_graph_newton`` so
        # receipt-bearing residuals remain bitwise stable.
        surface_delta = value.points[index] - query_array[index]
        normal = value.normal[index]
        tangent = surface_delta - np.dot(surface_delta, normal) * normal
        residuals[index] = np.linalg.norm(tangent)
    return uv, residuals


def _interval_distance(value: float, lower: float, upper: float) -> float:
    if value < lower:
        return lower - value
    if value > upper:
        return value - upper
    return 0.0


def _adaptive_global_lower_bound(
    evaluator: GraphEvaluator,
    query: FloatArray,
    upper_distance: float,
    tolerance: float,
    maximum_cells: int,
) -> tuple[float, int]:
    return _adaptive_global_lower_bounds(
        evaluator,
        np.asarray(query, dtype=np.float64).reshape(1, 3),
        np.asarray([upper_distance], dtype=np.float64),
        tolerance,
        maximum_cells,
    )[0]


def _adaptive_global_lower_bounds(
    evaluator: GraphEvaluator,
    queries: FloatArray,
    upper_distances: FloatArray,
    tolerance: float,
    maximum_cells: int,
) -> tuple[tuple[float, int], ...]:
    """Run independent best-first bounds with cross-query evaluator batches."""

    query_array = np.asarray(queries, dtype=np.float64)
    upper_array = np.asarray(upper_distances, dtype=np.float64)
    if query_array.ndim != 2 or query_array.shape[1] != 3 or len(query_array) == 0:
        raise ValueError("global-bound queries must have shape (N, 3), N >= 1")
    if upper_array.shape != (len(query_array),):
        raise ValueError("global-bound upper distances must have shape (N,)")
    domain = evaluator.spec.logical_domain
    slope_bound = evaluator.global_slope_bound()
    serials = [0 for _ in query_array]
    heaps: list[list[tuple[float, int, tuple[float, float, float, float]]]] = [
        [] for _ in query_array
    ]
    created = [1 for _ in query_array]

    def bounds(
        cells: Sequence[tuple[float, float, float, float]],
        query_indices: Sequence[int],
    ) -> tuple[float, ...]:
        centers = np.asarray(
            [(0.5 * (x0 + x1), 0.5 * (y0 + y1)) for x0, x1, y0, y1 in cells],
            dtype=np.float64,
        )
        heights = evaluator.evaluate(
            centers[:, 0],
            centers[:, 1],
            derivative_order=0,
        ).height
        result: list[float] = []
        for cell, height_value, query_index in zip(
            cells,
            heights,
            query_indices,
            strict=True,
        ):
            x0, x1, y0, y1 = cell
            height = float(height_value)
            radius = 0.5 * math.hypot(x1 - x0, y1 - y0)
            z0 = height - slope_bound * radius
            z1 = height + slope_bound * radius
            query = query_array[query_index]
            dx = _interval_distance(float(query[0]), x0, x1)
            dy = _interval_distance(float(query[1]), y0, y1)
            dz = _interval_distance(float(query[2]), z0, z1)
            result.append(math.sqrt(dx * dx + dy * dy + dz * dz))
        return tuple(result)

    initial = (domain.x_min_mm, domain.x_max_mm, domain.y_min_mm, domain.y_max_mm)
    initial_cells = tuple(initial for _ in query_array)
    initial_bounds = bounds(initial_cells, tuple(range(len(query_array))))
    for query_index, initial_bound in enumerate(initial_bounds):
        heapq.heappush(heaps[query_index], (initial_bound, 0, initial))

    active = np.ones(len(query_array), dtype=np.bool_)
    while active.any():
        work: list[tuple[int, tuple[tuple[float, float, float, float], ...]]] = []
        for active_query_index in np.flatnonzero(active):
            query_index = int(active_query_index)
            heap = heaps[query_index]
            if not heap or created[query_index] >= maximum_cells:
                active[query_index] = False
                continue
            lower_bound, _, cell = heap[0]
            if upper_array[query_index] - lower_bound <= tolerance:
                active[query_index] = False
                continue
            heapq.heappop(heap)
            x0, x1, y0, y1 = cell
            if max(x1 - x0, y1 - y0) <= np.finfo(np.float64).eps * 1024:
                heapq.heappush(heap, (lower_bound, serials[query_index], cell))
                active[query_index] = False
                continue
            xm = 0.5 * (x0 + x1)
            ym = 0.5 * (y0 + y1)
            work.append(
                (
                    int(query_index),
                    (
                        (x0, xm, y0, ym),
                        (xm, x1, y0, ym),
                        (x0, xm, ym, y1),
                        (xm, x1, ym, y1),
                    ),
                )
            )
        if not work:
            break
        cells = tuple(child for _, children in work for child in children)
        query_indices = tuple(query_index for query_index, children in work for _ in children)
        child_bounds = iter(bounds(cells, query_indices))
        for query_index, children in work:
            for child in children:
                child_bound = next(child_bounds)
                created[query_index] += 1
                serials[query_index] += 1
                if child_bound <= upper_array[query_index]:
                    heapq.heappush(
                        heaps[query_index],
                        (child_bound, serials[query_index], child),
                    )

    return tuple(
        (min((item[0] for item in heap), default=float(upper_array[index])), created[index])
        for index, heap in enumerate(heaps)
    )


def _family_feature_ids(family: SurfaceFamily) -> tuple[str, ...]:
    if family is SurfaceFamily.GROOVE_V:
        return (
            "outside_left_face",
            "v_left_face",
            "v_bottom_edge",
            "v_right_face",
            "outside_right_face",
        )
    if family is SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH:
        return ("switch_face_negative", "switch_edge", "switch_face_positive")
    if family in (SurfaceFamily.SPHERICAL_CAP, SurfaceFamily.SPHERICAL_BOWL):
        return ("spherical_patch", "aperture_ring", "outside_plane")
    return (f"{family.value}_smooth_face",)


def query_height_differential(
    handle: Any, x: ArrayLike, y: ArrayLike | None = None, **kwargs: Any
) -> QueryResponse:
    return as_surface_query(handle).query_height_differential(x, y, **kwargs)


def query_closest_features(handle: Any, points_mm: ArrayLike, **kwargs: Any) -> QueryResponse:
    return as_surface_query(handle).query_closest_features(points_mm, **kwargs)


def query_signed_distance(handle: Any, points_mm: ArrayLike, **kwargs: Any) -> QueryResponse:
    return as_surface_query(handle).query_signed_distance(points_mm, **kwargs)


def query_neighborhood(
    handle: Any,
    bounds_mm: tuple[float, float, float, float],
    **kwargs: Any,
) -> QueryResponse:
    return as_surface_query(handle).query_neighborhood(bounds_mm, **kwargs)


__all__ = [
    "AnalyticQueryHandle",
    "DomainClassification",
    "SurfaceQuery",
    "SurfaceQueryHandle",
    "as_surface_query",
    "classify_domain_coordinates",
    "query_closest_features",
    "query_height_differential",
    "query_neighborhood",
    "query_signed_distance",
]
