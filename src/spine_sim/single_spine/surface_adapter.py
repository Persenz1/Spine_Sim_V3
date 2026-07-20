"""M03 adapter from composite single-spine geometry to the public M01 API.

M01 owns immutable surface geometry and returns geometric evidence only.  This
adapter adds the M03-specific finite-cap, empty-ball, full-candidate, quality
and forbidden-body interpretations.  It never creates contact multipliers or
calls a beam/contact solver.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from spine_sim.foundation.canonical import stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.surface import (
    ConvergenceLevel,
    DomainStatus,
    FootprintGuard,
    M01ReasonCode,
    QualityStatus,
    QueryCapability,
    QueryFootprint,
    QueryResponse,
    SurfaceQueryHandle,
    derive_query_footprint,
    query_closest_features,
    query_height_differential,
    query_neighborhood,
    query_spherical_envelope_or_clearance,
)

from .contracts import SURFACE_SCALE_REFERENCE_RT_MM, LODPurpose, M03ReasonCode, Vector3
from .geometry import (
    CollisionRole,
    NeedlePart,
    SweptNeedleGeometry,
    TipPose,
    finite_cap_legality_margin_mm,
)

FloatArray = NDArray[np.float64]

SURFACE_ADAPTER_ID = "M03_M01_SURFACE_ADAPTER_1"
FOOTPRINT_DERIVATION_ID = "M03_FULL_COMPOSITE_SWEPT_GEOMETRY_TO_M01_AABB_1"


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ContractViolation(f"{name} must be a finite number")
    return float(value)


def _positive(value: float, name: str) -> float:
    result = _finite(value, name)
    if result <= 0.0:
        raise ContractViolation(f"{name} must be positive")
    return result


def _vector(value: Sequence[float] | FloatArray, name: str) -> FloatArray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ContractViolation(f"{name} must be a finite three-vector")
    return np.array(result, dtype=np.float64, copy=True)


def _unit(value: Sequence[float] | FloatArray, name: str) -> FloatArray:
    result = _vector(value, name)
    norm = float(np.linalg.norm(result))
    if norm <= np.finfo(np.float64).eps:
        raise ContractViolation(f"{name} cannot be the zero vector")
    return result / norm


def _points(value: Sequence[Sequence[float]] | FloatArray, name: str) -> FloatArray:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 2 or result.shape[1] != 3 or len(result) == 0:
        raise ContractViolation(f"{name} must have shape (N, 3), N >= 1")
    if not np.isfinite(result).all():
        raise ContractViolation(f"{name} must contain only finite values")
    return np.array(result, dtype=np.float64, copy=True)


def _tuple3(value: Sequence[float] | FloatArray) -> Vector3:
    array = _vector(value, "vector")
    return float(array[0]), float(array[1]), float(array[2])


@dataclass(frozen=True, slots=True)
class SurfaceFrameTransform:
    """Explicit rigid map; no implicit GLOBAL/M01-frame equivalence is assumed."""

    global_frame_id: str
    surface_frame_id: str
    rotation_global_from_surface: tuple[Vector3, Vector3, Vector3]
    surface_origin_global_mm: Vector3
    transform_id: str

    def __post_init__(self) -> None:
        rotation = np.asarray(self.rotation_global_from_surface, dtype=np.float64)
        if rotation.shape != (3, 3) or not np.isfinite(rotation).all():
            raise ContractViolation("rotation_global_from_surface must be a finite 3x3 matrix")
        if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1.0e-10, rtol=1.0e-10):
            raise ContractViolation("surface/global frame rotation must be orthonormal")
        if not math.isclose(float(np.linalg.det(rotation)), 1.0, abs_tol=1.0e-10):
            raise ContractViolation("surface/global frame rotation must be right handed")
        _vector(self.surface_origin_global_mm, "surface_origin_global_mm")
        expected = stable_content_id("m03_surface_frame_transform", self.identity_payload())
        if self.transform_id != expected:
            raise ContractViolation("surface frame transform identity mismatch")

    def identity_payload(self) -> dict[str, object]:
        return {
            "global_frame_id": self.global_frame_id,
            "surface_frame_id": self.surface_frame_id,
            "rotation_global_from_surface": self.rotation_global_from_surface,
            "surface_origin_global_mm": self.surface_origin_global_mm,
        }

    def global_to_surface_points(self, points_global_mm: FloatArray) -> FloatArray:
        points = _points(points_global_mm, "points_global_mm")
        rotation = np.asarray(self.rotation_global_from_surface, dtype=np.float64)
        origin = np.asarray(self.surface_origin_global_mm, dtype=np.float64)
        return (rotation.T @ (points - origin[None, :]).T).T

    def surface_to_global_point(self, point_surface_mm: Vector3) -> Vector3:
        rotation = np.asarray(self.rotation_global_from_surface, dtype=np.float64)
        origin = np.asarray(self.surface_origin_global_mm, dtype=np.float64)
        return _tuple3(origin + rotation @ _vector(point_surface_mm, "point_surface_mm"))

    def surface_to_global_vector(self, vector_surface: Vector3) -> Vector3:
        rotation = np.asarray(self.rotation_global_from_surface, dtype=np.float64)
        return _tuple3(rotation @ _vector(vector_surface, "vector_surface"))


def make_identity_surface_frame_transform(
    handle: SurfaceQueryHandle,
    *,
    global_frame_id: str = "GLOBAL",
) -> SurfaceFrameTransform:
    """Create an explicit identity registration for analytic/synthetic fixtures."""

    surface_frame_id = handle.realization.surface_frame_id
    payload: dict[str, object] = {
        "global_frame_id": global_frame_id,
        "surface_frame_id": surface_frame_id,
        "rotation_global_from_surface": (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        "surface_origin_global_mm": (0.0, 0.0, 0.0),
    }
    return SurfaceFrameTransform(
        **payload,  # type: ignore[arg-type]
        transform_id=stable_content_id("m03_surface_frame_transform", payload),
    )


@dataclass(frozen=True, slots=True)
class GeometryQueryPolicy:
    lod_purpose: LODPurpose
    surface_scale_reference_rt_mm: float
    declared_spacing_mm: float
    requested_tolerance_mm: float
    co_minimal_tolerance_mm: float
    finite_cap_tolerance_mm: float
    candidate_merge_tolerance_mm: float
    maximum_global_cells: int
    derivative_search_halo_mm: float
    trusted_scale_halo_mm: float
    tile_halo_mm: float
    declared_clearance_guard_mm: float
    policy_id: str

    def __post_init__(self) -> None:
        if self.surface_scale_reference_rt_mm != SURFACE_SCALE_REFERENCE_RT_MM:
            raise ContractViolation("M03 surface scale reference Rt must remain 0.05 mm")
        for name in (
            "declared_spacing_mm",
            "requested_tolerance_mm",
            "co_minimal_tolerance_mm",
            "finite_cap_tolerance_mm",
            "candidate_merge_tolerance_mm",
        ):
            if _finite(getattr(self, name), name) < 0.0:
                raise ContractViolation(f"{name} cannot be negative")
        for name in (
            "derivative_search_halo_mm",
            "trusted_scale_halo_mm",
            "tile_halo_mm",
            "declared_clearance_guard_mm",
        ):
            if _finite(getattr(self, name), name) < 0.0:
                raise ContractViolation(f"{name} cannot be negative")
        maximum_spacing = self.surface_scale_reference_rt_mm * self.lod_purpose.spacing_over_rt
        if self.declared_spacing_mm > maximum_spacing + 1.0e-15:
            raise ContractViolation(
                f"declared spacing exceeds frozen {self.lod_purpose.value} M03 LOD gate"
            )
        if not isinstance(self.maximum_global_cells, int) or self.maximum_global_cells < 16:
            raise ContractViolation("maximum_global_cells must be an integer >= 16")
        expected = stable_content_id("m03_geometry_query_policy", self.identity_payload())
        if self.policy_id != expected:
            raise ContractViolation("geometry query policy identity mismatch")

    def identity_payload(self) -> dict[str, object]:
        return {
            "lod_purpose": self.lod_purpose,
            "surface_scale_reference_rt_mm": self.surface_scale_reference_rt_mm,
            "declared_spacing_mm": self.declared_spacing_mm,
            "requested_tolerance_mm": self.requested_tolerance_mm,
            "co_minimal_tolerance_mm": self.co_minimal_tolerance_mm,
            "finite_cap_tolerance_mm": self.finite_cap_tolerance_mm,
            "candidate_merge_tolerance_mm": self.candidate_merge_tolerance_mm,
            "maximum_global_cells": self.maximum_global_cells,
            "derivative_search_halo_mm": self.derivative_search_halo_mm,
            "trusted_scale_halo_mm": self.trusted_scale_halo_mm,
            "tile_halo_mm": self.tile_halo_mm,
            "declared_clearance_guard_mm": self.declared_clearance_guard_mm,
        }


def make_geometry_query_policy(
    lod_purpose: LODPurpose = LODPurpose.EVENT_SUPPORT,
    *,
    maximum_global_cells: int = 20_000,
) -> GeometryQueryPolicy:
    reference = SURFACE_SCALE_REFERENCE_RT_MM
    spacing = reference * lod_purpose.spacing_over_rt
    payload: dict[str, object] = {
        "lod_purpose": lod_purpose,
        "surface_scale_reference_rt_mm": reference,
        "declared_spacing_mm": spacing,
        "requested_tolerance_mm": 0.01 * reference,
        "co_minimal_tolerance_mm": 0.002 * reference,
        "finite_cap_tolerance_mm": 0.002 * reference,
        "candidate_merge_tolerance_mm": 0.002 * reference,
        "maximum_global_cells": maximum_global_cells,
        "derivative_search_halo_mm": 2.0 * spacing,
        "trusted_scale_halo_mm": reference,
        "tile_halo_mm": spacing,
        "declared_clearance_guard_mm": reference,
    }
    return GeometryQueryPolicy(
        **payload,  # type: ignore[arg-type]
        policy_id=stable_content_id("m03_geometry_query_policy", payload),
    )


def _validate_handle_and_transform(
    handle: SurfaceQueryHandle,
    transform: SurfaceFrameTransform,
) -> None:
    if transform.surface_frame_id != handle.realization.surface_frame_id:
        raise ContractViolation("surface transform does not target the query realization frame")
    required_operations = {
        "height_differential",
        "closest_features",
        "signed_distance",
        "spherical_envelope_or_clearance",
    }
    unavailable = tuple(
        sorted(
            operation
            for operation in required_operations
            if handle.realization.capability_manifest.for_operation(operation) is None
        )
    )
    if unavailable:
        raise ContractViolation(
            "M01 realization lacks required M03 geometry capabilities",
            details={"operations": unavailable},
        )


def derive_complete_query_footprint(
    handle: SurfaceQueryHandle,
    swept_geometry: SweptNeedleGeometry,
    transform: SurfaceFrameTransform,
    policy: GeometryQueryPolicy,
) -> QueryFootprint:
    """Derive an M01 footprint from all current/swept tip/body/mount witnesses."""

    _validate_handle_and_transform(handle, transform)
    points_surface = transform.global_to_surface_points(swept_geometry.all_witness_points_global_mm)
    guard = FootprintGuard(
        probe_radius_mm=swept_geometry.maximum_cover_radius_mm,
        trusted_scale_halo_mm=policy.trusted_scale_halo_mm,
        derivative_search_halo_mm=policy.derivative_search_halo_mm,
        tile_halo_mm=policy.tile_halo_mm,
        declared_clearance_guard_mm=policy.declared_clearance_guard_mm,
    )
    footprint = derive_query_footprint(
        swept_points_mm=points_surface[:, :2],
        guard_mm=guard,
        logical_domain=handle.realization.logical_domain,
        derivation_method=FOOTPRINT_DERIVATION_ID,
    )
    if not _footprint_covers_points(footprint, points_surface, guard.effective_mm):
        raise ContractViolation("derived footprint does not cover complete swept geometry")
    return footprint


def _footprint_covers_points(
    footprint: QueryFootprint,
    points_surface_mm: FloatArray,
    guard_mm: float,
) -> bool:
    points = _points(points_surface_mm, "points_surface_mm")
    tolerance = 1.0e-12
    return bool(
        footprint.x_min_mm <= float(np.min(points[:, 0])) - guard_mm + tolerance
        and footprint.x_max_mm >= float(np.max(points[:, 0])) + guard_mm - tolerance
        and footprint.y_min_mm <= float(np.min(points[:, 1])) - guard_mm + tolerance
        and footprint.y_max_mm >= float(np.max(points[:, 1])) + guard_mm - tolerance
    )


class CandidateOrigin(StrEnum):
    CURRENT_NEAREST = "CURRENT_NEAREST"
    CURRENT_CO_MINIMAL = "CURRENT_CO_MINIMAL"
    PREVIOUS_ACTIVE = "PREVIOUS_ACTIVE"
    NEARBY_SWITCH_PROBE = "NEARBY_SWITCH_PROBE"


class GeometryGateStatus(StrEnum):
    PASSED = "PASSED"
    PASSED_NONSMOOTH_GRAPH = "PASSED_NONSMOOTH_GRAPH"
    OUT_OF_DOMAIN = "OUT_OF_DOMAIN"
    GEOMETRY_UNCERTAIN = "GEOMETRY_UNCERTAIN"


@dataclass(frozen=True, slots=True)
class SupportCandidate:
    candidate_id: str
    surface_realization_id: str
    feature_id: str
    feature_type: str
    chart_id: str
    point_global_mm: Vector3
    outward_normals_global: tuple[Vector3, ...]
    radial_normal_global: Vector3 | None
    signed_distance_from_current_center_mm: float
    sphere_gap_mm: float
    cap_legality_margin_mm: float
    finite_cap_legal: bool
    local_minimum_verified: bool
    empty_ball_verified: bool
    query_quality_passed: bool
    origins: tuple[CandidateOrigin, ...]
    query_receipt_ids: tuple[str, ...]
    residual_mm: float
    error_bound_mm: float
    rejection_reasons: tuple[str, ...]

    @property
    def admissible_support_candidate(self) -> bool:
        return (
            self.finite_cap_legal
            and self.local_minimum_verified
            and self.empty_ball_verified
            and self.query_quality_passed
            and self.radial_normal_global is not None
        )


@dataclass(frozen=True, slots=True)
class CandidateSetEvaluation:
    evaluation_id: str
    surface_realization_id: str
    footprint_id: str
    policy_id: str
    gate_status: GeometryGateStatus
    reason_code: str
    candidates: tuple[SupportCandidate, ...]
    active_graph_candidate_ids: tuple[str, ...]
    current_query_receipt_id: str
    all_query_receipt_ids: tuple[str, ...]
    minimum_signed_distance_mm: float | None
    error_bound_mm: float | None
    nonsmooth_or_nonunique: bool


@dataclass(frozen=True, slots=True)
class _RawCandidate:
    feature_id: str
    feature_type: str
    point_global_mm: Vector3
    outward_normals_global: tuple[Vector3, ...]
    origin: CandidateOrigin
    query_receipt_ids: tuple[str, ...]
    residual_mm: float
    error_bound_mm: float
    signed_distance_for_probe_mm: float
    current_query_member: bool


def _response_gate(response: QueryResponse) -> tuple[GeometryGateStatus, str]:
    if any(item is DomainStatus.OUT_OF_DOMAIN for item in response.domain_status):
        return GeometryGateStatus.OUT_OF_DOMAIN, M01ReasonCode.OUT_OF_DOMAIN.value
    if response.capability is QueryCapability.UNAVAILABLE or not response.quality_mask.all():
        return GeometryGateStatus.GEOMETRY_UNCERTAIN, response.status.reason_code
    if response.convergence_level in {
        ConvergenceLevel.REFINEMENT_REQUIRED,
        ConvergenceLevel.FAILED,
    }:
        return (
            GeometryGateStatus.GEOMETRY_UNCERTAIN,
            M01ReasonCode.RESOLUTION_REFINEMENT_REQUIRED.value,
        )
    if response.trusted_scale_status is not QualityStatus.TRUSTED_FOR_DECLARED_SCALE:
        return GeometryGateStatus.GEOMETRY_UNCERTAIN, M01ReasonCode.TRUST_SCALE_INSUFFICIENT.value
    nonsmooth = any(item is QualityStatus.NONSMOOTH_FEATURE_SET for item in response.quality_status)
    return (
        GeometryGateStatus.PASSED_NONSMOOTH_GRAPH if nonsmooth else GeometryGateStatus.PASSED,
        M01ReasonCode.OK.value,
    )


def _combined_response_gate(
    responses: Sequence[QueryResponse],
) -> tuple[GeometryGateStatus, str]:
    gates = tuple(_response_gate(response) for response in responses)
    for target in (
        GeometryGateStatus.OUT_OF_DOMAIN,
        GeometryGateStatus.GEOMETRY_UNCERTAIN,
    ):
        match = next((item for item in gates if item[0] is target), None)
        if match is not None:
            return match
    if any(item[0] is GeometryGateStatus.PASSED_NONSMOOTH_GRAPH for item in gates):
        return GeometryGateStatus.PASSED_NONSMOOTH_GRAPH, M01ReasonCode.OK.value
    return GeometryGateStatus.PASSED, M01ReasonCode.OK.value


def _nearby_probe_centers(
    tip_center_global_mm: Vector3,
    probe_radius_mm: float,
) -> tuple[Vector3, ...]:
    center = _vector(tip_center_global_mm, "tip_center_global_mm")
    radius = _positive(probe_radius_mm, "probe_radius_mm")
    offsets = (
        (radius, 0.0, 0.0),
        (-radius, 0.0, 0.0),
        (0.0, radius, 0.0),
        (0.0, -radius, 0.0),
    )
    return tuple(_tuple3(center + np.asarray(offset)) for offset in offsets)


def collect_support_candidates(
    handle: SurfaceQueryHandle,
    *,
    tip_pose: TipPose,
    tip_radius_mm: float,
    cap_blend_coordinate_mm: float,
    footprint: QueryFootprint,
    transform: SurfaceFrameTransform,
    policy: GeometryQueryPolicy,
    previous_active_candidates: Sequence[SupportCandidate] = (),
    nearby_probe_centers_global_mm: Sequence[Vector3] | None = None,
) -> CandidateSetEvaluation:
    """Merge current co-minimal, previous-active and nearby-switch evidence."""

    _validate_handle_and_transform(handle, transform)
    radius = _positive(tip_radius_mm, "tip_radius_mm")
    current_center = tip_pose.current_tip_center_global_mm
    nearby = (
        tuple(nearby_probe_centers_global_mm)
        if nearby_probe_centers_global_mm is not None
        else _nearby_probe_centers(current_center, radius)
    )
    probe_global = np.asarray((current_center, *nearby), dtype=np.float64)
    probe_surface = transform.global_to_surface_points(probe_global)
    if not _footprint_covers_points(footprint, probe_surface, 0.0):
        raise ContractViolation("support probes lie outside the certified query footprint")
    closest_response = query_closest_features(
        handle,
        probe_surface,
        requested_tolerance_mm=policy.requested_tolerance_mm,
        co_minimal_tolerance_mm=policy.co_minimal_tolerance_mm,
        maximum_global_cells=policy.maximum_global_cells,
    )
    spherical_response = query_spherical_envelope_or_clearance(
        handle,
        probe_surface,
        radius,
        path="phi_minus_radius",
        requested_tolerance_mm=policy.requested_tolerance_mm,
        co_minimal_tolerance_mm=policy.co_minimal_tolerance_mm,
        maximum_global_cells=policy.maximum_global_cells,
        _precomputed_closest_response=closest_response,
    )
    gate_status, reason_code = _combined_response_gate((closest_response, spherical_response))
    metadata = dict(closest_response.metadata)
    global_coverage = bool(metadata.get("global_candidate_coverage", False))

    raw: list[_RawCandidate] = []
    # The complete-sphere public path owns the support/gap evidence.  The
    # direct closest query remains an independent full-candidate/global-search
    # receipt because the spherical wrapper intentionally exposes only its
    # radius/path metadata.
    for probe_index, feature_set in enumerate(spherical_response.feature_sets):
        for feature in feature_set:
            origin = (
                CandidateOrigin.CURRENT_CO_MINIMAL
                if probe_index == 0 and len(feature_set) > 1
                else CandidateOrigin.CURRENT_NEAREST
                if probe_index == 0
                else CandidateOrigin.NEARBY_SWITCH_PROBE
            )
            raw.append(
                _RawCandidate(
                    feature.feature_id,
                    feature.feature_type,
                    transform.surface_to_global_point(feature.point_mm),
                    tuple(
                        transform.surface_to_global_vector(normal)
                        for normal in feature.outward_normals
                    ),
                    origin,
                    (closest_response.query_id, spherical_response.query_id),
                    feature.residual_mm,
                    feature.error_bound_mm,
                    feature.signed_distance_mm,
                    probe_index == 0,
                )
            )
    for previous in previous_active_candidates:
        if previous.surface_realization_id != handle.realization.surface_realization_id:
            raise ContractViolation("previous support candidate belongs to another realization")
        if not previous.query_receipt_ids:
            raise ContractViolation("previous support candidate has no M01 query receipt")
        raw.append(
            _RawCandidate(
                previous.feature_id,
                previous.feature_type,
                previous.point_global_mm,
                previous.outward_normals_global,
                CandidateOrigin.PREVIOUS_ACTIVE,
                previous.query_receipt_ids,
                previous.residual_mm,
                previous.error_bound_mm,
                previous.signed_distance_from_current_center_mm,
                False,
            )
        )

    current_features = [item for item in raw if item.current_query_member]
    current_minimum = min(
        (item.signed_distance_for_probe_mm for item in current_features), default=None
    )
    merged = _merge_raw_candidates(raw, policy.candidate_merge_tolerance_mm)
    candidates = tuple(
        _resolve_candidate(
            item,
            surface_realization_id=handle.realization.surface_realization_id,
            tip_pose=tip_pose,
            tip_radius_mm=radius,
            cap_blend_coordinate_mm=cap_blend_coordinate_mm,
            policy=policy,
            gate_status=gate_status,
            global_coverage=global_coverage,
            current_minimum_signed_distance_mm=current_minimum,
        )
        for item in merged
    )
    active = tuple(item.candidate_id for item in candidates if item.admissible_support_candidate)
    nonsmooth = len(active) > 1 or gate_status is GeometryGateStatus.PASSED_NONSMOOTH_GRAPH
    all_receipts = tuple(
        sorted(
            {
                closest_response.query_id,
                spherical_response.query_id,
                *(receipt for item in candidates for receipt in item.query_receipt_ids),
            }
        )
    )
    payload = {
        "surface_realization_id": handle.realization.surface_realization_id,
        "footprint_id": footprint.footprint_id,
        "policy_id": policy.policy_id,
        "gate_status": gate_status,
        "reason_code": reason_code,
        "candidate_ids": tuple(item.candidate_id for item in candidates),
        "active_graph_candidate_ids": active,
        "current_query_receipt_id": spherical_response.query_id,
        "minimum_signed_distance_mm": current_minimum,
        "error_bound_mm": max(
            closest_response.error_bound or 0.0,
            spherical_response.error_bound or 0.0,
        ),
    }
    return CandidateSetEvaluation(
        stable_content_id("m03_candidate_set_evaluation", payload),
        handle.realization.surface_realization_id,
        footprint.footprint_id,
        policy.policy_id,
        gate_status,
        reason_code,
        candidates,
        active,
        spherical_response.query_id,
        all_receipts,
        current_minimum,
        max(
            closest_response.error_bound or 0.0,
            spherical_response.error_bound or 0.0,
        ),
        nonsmooth,
    )


def _merge_raw_candidates(
    raw: Sequence[_RawCandidate],
    tolerance_mm: float,
) -> tuple[tuple[_RawCandidate, ...], ...]:
    tolerance = _finite(tolerance_mm, "tolerance_mm")
    ordered = sorted(
        raw, key=lambda item: (item.feature_id, item.point_global_mm, item.origin.value)
    )
    groups: list[list[_RawCandidate]] = []
    for candidate in ordered:
        point = np.asarray(candidate.point_global_mm, dtype=np.float64)
        match = next(
            (
                group
                for group in groups
                if group[0].feature_id == candidate.feature_id
                and np.linalg.norm(point - np.asarray(group[0].point_global_mm)) <= tolerance
            ),
            None,
        )
        if match is None:
            groups.append([candidate])
        else:
            match.append(candidate)
    return tuple(tuple(group) for group in groups)


def _select_outward_contact_normal(
    outward_normals_global: Sequence[Vector3],
    radial_center_minus_support: FloatArray,
    signed_distance_mm: float,
) -> Vector3 | None:
    if not outward_normals_global:
        return None
    normals = tuple(
        sorted({_tuple3(_unit(normal, "M01 outward normal")) for normal in outward_normals_global})
    )
    radial_norm = float(np.linalg.norm(radial_center_minus_support))
    if radial_norm <= np.finfo(np.float64).eps:
        return normals[0]
    target = radial_center_minus_support / radial_norm
    if signed_distance_mm < 0.0:
        target = -target
    return min(
        normals,
        key=lambda normal: (
            -float(np.dot(np.asarray(normal, dtype=np.float64), target)),
            normal,
        ),
    )


def _resolve_candidate(
    group: tuple[_RawCandidate, ...],
    *,
    surface_realization_id: str,
    tip_pose: TipPose,
    tip_radius_mm: float,
    cap_blend_coordinate_mm: float,
    policy: GeometryQueryPolicy,
    gate_status: GeometryGateStatus,
    global_coverage: bool,
    current_minimum_signed_distance_mm: float | None,
) -> SupportCandidate:
    representative = min(group, key=lambda item: (item.point_global_mm, item.origin.value))
    point = np.asarray(representative.point_global_mm, dtype=np.float64)
    center = np.asarray(tip_pose.current_tip_center_global_mm, dtype=np.float64)
    radial = center - point
    radial_norm = float(np.linalg.norm(radial))
    current_members = tuple(item for item in group if item.current_query_member)
    if current_members:
        signed_distance = min(item.signed_distance_for_probe_mm for item in current_members)
    else:
        signed_distance = radial_norm
    normals = tuple(
        sorted(
            {normal for item in group for normal in item.outward_normals_global},
            key=lambda item: item,
        )
    )
    radial_normal = _select_outward_contact_normal(normals, radial, signed_distance)
    cap_margin = finite_cap_legality_margin_mm(
        _tuple3(point),
        tip_pose.current_tip_center_global_mm,
        tip_pose.current_axis_global,
        cap_blend_coordinate_mm,
    )
    local_minimum = bool(
        current_members
        and global_coverage
        and max(item.residual_mm for item in current_members) <= policy.requested_tolerance_mm
    )
    empty_ball = bool(
        local_minimum
        and current_minimum_signed_distance_mm is not None
        and abs(signed_distance)
        <= abs(current_minimum_signed_distance_mm)
        + policy.co_minimal_tolerance_mm
        + max(item.error_bound_mm for item in current_members)
    )
    quality_passed = (
        gate_status
        in {
            GeometryGateStatus.PASSED,
            GeometryGateStatus.PASSED_NONSMOOTH_GRAPH,
        }
        and max(item.error_bound_mm for item in group) <= policy.requested_tolerance_mm
    )
    finite_cap = cap_margin >= -policy.finite_cap_tolerance_mm
    rejection: list[str] = []
    if radial_normal is None:
        rejection.append("M01_OUTWARD_NORMAL_UNAVAILABLE")
    if not finite_cap:
        rejection.append("FINITE_CAP_ILLEGAL")
    if not local_minimum:
        rejection.append("LOCAL_MINIMUM_UNVERIFIED")
    if not empty_ball:
        rejection.append("EMPTY_BALL_UNVERIFIED")
    if not quality_passed:
        rejection.append("QUERY_QUALITY_UNCERTAIN")
    origins = tuple(sorted({item.origin for item in group}, key=lambda item: item.value))
    receipts = tuple(sorted({receipt for item in group for receipt in item.query_receipt_ids}))
    residual = max(item.residual_mm for item in group)
    error_bound = max(item.error_bound_mm for item in group)
    # M01's public ClosestFeature contract exposes a deterministic feature set,
    # not a second chart token.  M03 therefore uses that feature set as its
    # explicit chart and binds both it and the complete sorted receipt/evidence
    # set into candidate identity.  Query repetition with distinct evidence can
    # never silently reuse an older support identity, while cache/order changes
    # that preserve the content-addressed receipts remain deterministic.
    chart_id = representative.feature_id
    payload = {
        "surface_realization_id": surface_realization_id,
        "feature_id": representative.feature_id,
        "feature_type": representative.feature_type,
        "chart_id": chart_id,
        "point_global_mm": _tuple3(point),
        "outward_normals_global": normals,
        "radial_normal_global": radial_normal,
        "signed_distance_from_current_center_mm": signed_distance,
        "query_receipt_ids": receipts,
        "residual_mm": residual,
        "error_bound_mm": error_bound,
    }
    return SupportCandidate(
        stable_content_id("m03_support_candidate", payload),
        surface_realization_id,
        representative.feature_id,
        representative.feature_type,
        chart_id,
        _tuple3(point),
        normals,
        radial_normal,
        signed_distance,
        signed_distance - tip_radius_mm,
        cap_margin,
        finite_cap,
        local_minimum,
        empty_ball,
        quality_passed,
        origins,
        receipts,
        residual,
        error_bound,
        tuple(rejection),
    )


class BodyCollisionStatus(StrEnum):
    CLEAR = "CLEAR"
    BODY_COLLISION_INVALID = "BODY_COLLISION_INVALID"
    GEOMETRY_UNCERTAIN = "GEOMETRY_UNCERTAIN"
    OUT_OF_DOMAIN = "OUT_OF_DOMAIN"


@dataclass(frozen=True, slots=True)
class PartClearance:
    part: NeedlePart
    collision_role: CollisionRole
    sampled_minimum_vertical_clearance_mm: float | None
    certified_euclidean_clearance_lower_bound_mm: float | None
    declared_clearance_mm: float
    geometry_cover_radius_mm: float
    surface_error_bound_mm: float | None
    collided_at_witness: bool
    continuously_certified_clear: bool


@dataclass(frozen=True, slots=True)
class BodyCollisionEvaluation:
    evaluation_id: str
    surface_realization_id: str
    footprint_id: str
    status: BodyCollisionStatus
    reason_code: str
    part_clearances: tuple[PartClearance, ...]
    minimum_forbidden_body_clearance_lower_bound_mm: float | None
    query_receipt_ids: tuple[str, ...]
    controlling_part: NeedlePart | None


def evaluate_body_collision(
    handle: SurfaceQueryHandle,
    *,
    swept_geometry: SweptNeedleGeometry,
    footprint: QueryFootprint,
    transform: SurfaceFrameTransform,
    policy: GeometryQueryPolicy,
    cone_clearance_mm: float = 0.0,
    shaft_clearance_mm: float = 0.0,
    mount_clearance_mm: float = 0.0,
) -> BodyCollisionEvaluation:
    """Certify complete tip/body/mount sweep against an M01 height-field solid.

    Surface witness points use the exact membership test ``z-h(x,y)``.  A
    global M01 slope bound converts positive vertical separation to a
    conservative Euclidean lower bound; the part/sweep cover and M01 error are
    then subtracted.  Thus a positive lower bound certifies the continuous
    envelope, while an unresolved cover returns ``GEOMETRY_UNCERTAIN`` rather
    than silently declaring clearance.
    """

    _validate_handle_and_transform(handle, transform)
    clearances = {
        NeedlePart.TIP_CAP: 0.0,
        NeedlePart.CONE: _finite(cone_clearance_mm, "cone_clearance_mm"),
        NeedlePart.SHAFT: _finite(shaft_clearance_mm, "shaft_clearance_mm"),
        NeedlePart.MOUNT: _finite(mount_clearance_mm, "mount_clearance_mm"),
    }
    if any(item < 0.0 for item in clearances.values()):
        raise ContractViolation("declared body clearances cannot be negative")
    all_points_surface = transform.global_to_surface_points(
        swept_geometry.all_witness_points_global_mm
    )
    if not _footprint_covers_points(footprint, all_points_surface, 0.0):
        raise ContractViolation("body witnesses lie outside the certified footprint")
    height_response = query_height_differential(
        handle,
        all_points_surface[:, :2],
        derivative_order=1,
    )
    neighborhood_response = query_neighborhood(
        handle,
        (
            footprint.x_min_mm,
            footprint.x_max_mm,
            footprint.y_min_mm,
            footprint.y_max_mm,
        ),
        grid_size=9,
    )
    height_gate, height_reason = _response_gate(height_response)
    neighborhood_gate, neighborhood_reason = _response_gate(neighborhood_response)
    receipt_ids = (height_response.query_id, neighborhood_response.query_id)
    if (
        height_gate is GeometryGateStatus.OUT_OF_DOMAIN
        or neighborhood_gate is GeometryGateStatus.OUT_OF_DOMAIN
    ):
        return _body_failure_result(
            handle,
            footprint,
            BodyCollisionStatus.OUT_OF_DOMAIN,
            M01ReasonCode.OUT_OF_DOMAIN.value,
            receipt_ids,
        )
    if (
        height_gate is GeometryGateStatus.GEOMETRY_UNCERTAIN
        or neighborhood_gate is GeometryGateStatus.GEOMETRY_UNCERTAIN
    ):
        reason = (
            height_reason
            if height_gate is GeometryGateStatus.GEOMETRY_UNCERTAIN
            else neighborhood_reason
        )
        return _body_failure_result(
            handle,
            footprint,
            BodyCollisionStatus.GEOMETRY_UNCERTAIN,
            reason,
            receipt_ids,
        )
    heights_field = height_response.field("height_mm")
    slope_field = neighborhood_response.field("slope_norm_upper_bound")
    if heights_field.values is None or slope_field.values is None:
        return _body_failure_result(
            handle,
            footprint,
            BodyCollisionStatus.GEOMETRY_UNCERTAIN,
            M01ReasonCode.QUERY_CAPABILITY_UNAVAILABLE.value,
            receipt_ids,
        )
    heights = np.asarray(heights_field.values, dtype=np.float64)
    slope_bound = float(np.asarray(slope_field.values, dtype=np.float64)[0])
    denominator = math.sqrt(1.0 + slope_bound * slope_bound)
    error_bound = max(
        height_response.error_bound or 0.0,
        neighborhood_response.error_bound or 0.0,
    )
    vertical = all_points_surface[:, 2] - heights

    results: list[PartClearance] = []
    offset = 0
    for part in swept_geometry.parts:
        count = len(part.witness_points_global_mm)
        values = vertical[offset : offset + count]
        offset += count
        declared = clearances[part.part]
        sampled = float(np.min(values)) - declared
        lower = (sampled - error_bound) / denominator - part.continuous_cover_radius_mm
        collided = sampled <= 0.0
        results.append(
            PartClearance(
                part.part,
                part.collision_role,
                sampled,
                lower,
                declared,
                part.continuous_cover_radius_mm,
                error_bound,
                collided,
                lower > 0.0,
            )
        )
    forbidden = tuple(
        item for item in results if item.collision_role is CollisionRole.FORBIDDEN_BODY
    )
    witnessed = tuple(item for item in forbidden if item.collided_at_witness)
    unresolved = tuple(item for item in forbidden if not item.continuously_certified_clear)
    if witnessed:
        status = BodyCollisionStatus.BODY_COLLISION_INVALID
        reason_code = M03ReasonCode.BODY_COLLISION_INVALID.value
        controlling = min(
            witnessed,
            key=lambda item: (
                item.sampled_minimum_vertical_clearance_mm
                if item.sampled_minimum_vertical_clearance_mm is not None
                else math.inf
            ),
        ).part
    elif unresolved:
        status = BodyCollisionStatus.GEOMETRY_UNCERTAIN
        reason_code = M03ReasonCode.GEOMETRY_UNCERTAIN.value
        controlling = min(
            unresolved,
            key=lambda item: (
                item.certified_euclidean_clearance_lower_bound_mm
                if item.certified_euclidean_clearance_lower_bound_mm is not None
                else math.inf
            ),
        ).part
    else:
        status = BodyCollisionStatus.CLEAR
        reason_code = M03ReasonCode.OK.value
        controlling = min(
            forbidden,
            key=lambda item: (
                item.certified_euclidean_clearance_lower_bound_mm
                if item.certified_euclidean_clearance_lower_bound_mm is not None
                else math.inf
            ),
        ).part
    minimum = min(
        (
            item.certified_euclidean_clearance_lower_bound_mm
            for item in forbidden
            if item.certified_euclidean_clearance_lower_bound_mm is not None
        ),
        default=None,
    )
    payload = {
        "surface_realization_id": handle.realization.surface_realization_id,
        "footprint_id": footprint.footprint_id,
        "sweep_id": swept_geometry.sweep_id,
        "status": status,
        "reason_code": reason_code,
        "part_clearances": tuple(results),
        "query_receipt_ids": receipt_ids,
    }
    return BodyCollisionEvaluation(
        stable_content_id("m03_body_collision_evaluation", payload),
        handle.realization.surface_realization_id,
        footprint.footprint_id,
        status,
        reason_code,
        tuple(results),
        minimum,
        receipt_ids,
        controlling,
    )


def _body_failure_result(
    handle: SurfaceQueryHandle,
    footprint: QueryFootprint,
    status: BodyCollisionStatus,
    reason_code: str,
    receipt_ids: tuple[str, ...],
) -> BodyCollisionEvaluation:
    payload = {
        "surface_realization_id": handle.realization.surface_realization_id,
        "footprint_id": footprint.footprint_id,
        "status": status,
        "reason_code": reason_code,
        "query_receipt_ids": receipt_ids,
    }
    return BodyCollisionEvaluation(
        stable_content_id("m03_body_collision_evaluation", payload),
        handle.realization.surface_realization_id,
        footprint.footprint_id,
        status,
        reason_code,
        (),
        None,
        receipt_ids,
        None,
    )


__all__ = [
    "FOOTPRINT_DERIVATION_ID",
    "SURFACE_ADAPTER_ID",
    "BodyCollisionEvaluation",
    "BodyCollisionStatus",
    "CandidateOrigin",
    "CandidateSetEvaluation",
    "GeometryGateStatus",
    "GeometryQueryPolicy",
    "PartClearance",
    "SupportCandidate",
    "SurfaceFrameTransform",
    "collect_support_candidates",
    "derive_complete_query_footprint",
    "evaluate_body_collision",
    "make_geometry_query_policy",
    "make_identity_surface_frame_transform",
]
