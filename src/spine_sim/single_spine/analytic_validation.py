"""Analytic geometry validation for the M03 composite single spine.

The suite in this module is deliberately narrower than a standalone mechanics
run.  It exercises immutable M01 analytic realizations through their public
query API and then passes the same evidence through the M03 composite-geometry
surface adapter.  It does not invoke a trial solver, synthesize solver output,
or claim evidence from a measured wall, a brick surface, or an experiment.

Every case returns its individual checks, observables, query receipts, and
quality/status fields so a failed or uncertain geometry assertion cannot be
hidden behind a composite score.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from spine_sim.foundation.canonical import stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.surface import (
    ConvergenceLevel,
    DomainStatus,
    QueryCapability,
    QueryResponse,
    SurfaceFamily,
    SurfaceProvider,
    SurfaceQueryHandle,
    make_analytic_source_descriptor,
    query_closest_features,
    query_spherical_envelope_or_clearance,
)

from .contracts import (
    SingleSpineParameterBundle,
    Vector3,
    canonical_local_frame,
    make_baseline_parameter_bundle,
)
from .geometry import (
    NeedlePart,
    TipPose,
    build_composite_needle_geometry,
    engineering_initial_axis,
    finite_cap_legality_margin_mm,
    make_swept_needle_geometry,
    resolve_tip_pose,
)
from .surface_adapter import (
    CandidateOrigin,
    GeometryGateStatus,
    SupportCandidate,
    collect_support_candidates,
    derive_complete_query_footprint,
    make_geometry_query_policy,
    make_identity_surface_frame_transform,
)

FloatArray = NDArray[np.float64]

ANALYTIC_VALIDATION_SCHEMA_VERSION = "1.0.0"
ANALYTIC_VALIDATION_SUITE_ID = "M03_ANALYTIC_SURFACE_GEOMETRY_SUITE_1"
_PASS_REASON = "M03_ANALYTIC_GEOMETRY_VALIDATION_PASSED"
_FAIL_REASON = "M03_ANALYTIC_GEOMETRY_VALIDATION_FAILED"


class AnalyticValidationStatus(StrEnum):
    """Outcome of a case or of the whole analytic suite."""

    PASSED = "PASSED"
    FAILED = "FAILED"


def _jsonable(value: object) -> object:
    """Return a JSON-safe detached representation of validation evidence."""

    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return _jsonable(value.tolist())
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, Sequence):
        return [_jsonable(item) for item in value]
    return str(value)


@dataclass(frozen=True, slots=True)
class AnalyticValidationCheck:
    """One independently inspectable validation assertion."""

    check_id: str
    passed: bool
    expected: object
    observed: object
    tolerance_mm: float | None
    explanation: str

    def __post_init__(self) -> None:
        if not self.check_id or not self.explanation:
            raise ContractViolation(
                "analytic validation check identity/explanation cannot be empty"
            )
        if self.tolerance_mm is not None and (
            not math.isfinite(self.tolerance_mm) or self.tolerance_mm < 0.0
        ):
            raise ContractViolation("analytic validation check tolerance must be nonnegative")

    def to_dict(self) -> dict[str, object]:
        return {
            "check_id": self.check_id,
            "passed": self.passed,
            "expected": _jsonable(self.expected),
            "observed": _jsonable(self.observed),
            "tolerance_mm": self.tolerance_mm,
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class QueryReceiptEvidence:
    """Status-bearing summary of one real public M01 query response."""

    query_id: str
    operation: str
    method_id: str
    capability: str
    convergence_level: str
    reason_code: str
    domain_status: tuple[str, ...]
    quality_status: tuple[str, ...]
    trusted_scale_status: str
    achieved_residual_mm: float | None
    error_bound_mm: float | None
    metadata: Mapping[str, object]

    @classmethod
    def from_response(cls, response: QueryResponse) -> QueryReceiptEvidence:
        return cls(
            response.query_id,
            response.operation,
            response.method_id,
            response.capability.value,
            response.convergence_level.value,
            response.status.reason_code,
            tuple(item.value for item in response.domain_status),
            tuple(item.value for item in response.quality_status),
            response.trusted_scale_status.value,
            response.achieved_residual,
            response.error_bound,
            dict(response.metadata),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "query_id": self.query_id,
            "operation": self.operation,
            "method_id": self.method_id,
            "capability": self.capability,
            "convergence_level": self.convergence_level,
            "reason_code": self.reason_code,
            "domain_status": list(self.domain_status),
            "quality_status": list(self.quality_status),
            "trusted_scale_status": self.trusted_scale_status,
            "achieved_residual_mm": self.achieved_residual_mm,
            "error_bound_mm": self.error_bound_mm,
            "metadata": _jsonable(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class SupportCandidateEvidence:
    """M03 interpretation of one M01 feature, with no force semantics."""

    candidate_id: str
    feature_id: str
    feature_type: str
    point_global_mm: Vector3
    outward_normals_global: tuple[Vector3, ...]
    radial_normal_global: Vector3 | None
    signed_center_distance_mm: float
    sphere_gap_mm: float
    cap_legality_margin_mm: float
    finite_cap_legal: bool
    local_minimum_verified: bool
    empty_ball_verified: bool
    query_quality_passed: bool
    admissible_support_candidate: bool
    origins: tuple[str, ...]
    query_receipt_ids: tuple[str, ...]
    residual_mm: float
    error_bound_mm: float
    rejection_reasons: tuple[str, ...]

    @classmethod
    def from_candidate(cls, candidate: SupportCandidate) -> SupportCandidateEvidence:
        return cls(
            candidate.candidate_id,
            candidate.feature_id,
            candidate.feature_type,
            candidate.point_global_mm,
            candidate.outward_normals_global,
            candidate.radial_normal_global,
            candidate.signed_distance_from_current_center_mm,
            candidate.sphere_gap_mm,
            candidate.cap_legality_margin_mm,
            candidate.finite_cap_legal,
            candidate.local_minimum_verified,
            candidate.empty_ball_verified,
            candidate.query_quality_passed,
            candidate.admissible_support_candidate,
            tuple(item.value for item in candidate.origins),
            candidate.query_receipt_ids,
            candidate.residual_mm,
            candidate.error_bound_mm,
            candidate.rejection_reasons,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "feature_id": self.feature_id,
            "feature_type": self.feature_type,
            "point_global_mm": list(self.point_global_mm),
            "outward_normals_global": [list(item) for item in self.outward_normals_global],
            "radial_normal_global": (
                None if self.radial_normal_global is None else list(self.radial_normal_global)
            ),
            "signed_center_distance_mm": self.signed_center_distance_mm,
            "sphere_gap_mm": self.sphere_gap_mm,
            "cap_legality_margin_mm": self.cap_legality_margin_mm,
            "finite_cap_legal": self.finite_cap_legal,
            "local_minimum_verified": self.local_minimum_verified,
            "empty_ball_verified": self.empty_ball_verified,
            "query_quality_passed": self.query_quality_passed,
            "admissible_support_candidate": self.admissible_support_candidate,
            "origins": list(self.origins),
            "query_receipt_ids": list(self.query_receipt_ids),
            "residual_mm": self.residual_mm,
            "error_bound_mm": self.error_bound_mm,
            "rejection_reasons": list(self.rejection_reasons),
        }


@dataclass(frozen=True, slots=True)
class AnalyticValidationCaseResult:
    """Machine-readable outcome for one analytic fixture."""

    case_id: str
    surface_family: str
    surface_parameters: Mapping[str, object]
    status: AnalyticValidationStatus
    reason_code: str
    surface_spec_id: str | None
    surface_realization_id: str | None
    geometry_evidence: Mapping[str, object]
    query_receipts: tuple[QueryReceiptEvidence, ...]
    adapter_gate_status: str | None
    adapter_reason_code: str | None
    adapter_current_query_receipt_id: str | None
    adapter_all_query_receipt_ids: tuple[str, ...]
    active_graph_candidate_ids: tuple[str, ...]
    observables: Mapping[str, object]
    candidates: tuple[SupportCandidateEvidence, ...]
    checks: tuple[AnalyticValidationCheck, ...]

    def __post_init__(self) -> None:
        if not self.case_id or not self.surface_family or not self.reason_code:
            raise ContractViolation("analytic validation case identity/status cannot be empty")
        if self.status is AnalyticValidationStatus.PASSED and not all(
            item.passed for item in self.checks
        ):
            raise ContractViolation("a passed analytic case cannot contain a failed check")

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "surface_family": self.surface_family,
            "surface_parameters": _jsonable(self.surface_parameters),
            "status": self.status.value,
            "reason_code": self.reason_code,
            "evidence_scope": {
                "surface_source_kind": "analytic",
                "source_identity": "VALIDATION_ONLY",
                "measured_surface_used": False,
                "target_brick_surface_claimed": False,
                "experimental_evidence": "NOT_ASSESSED",
                "solver_invoked": False,
            },
            "surface_spec_id": self.surface_spec_id,
            "surface_realization_id": self.surface_realization_id,
            "geometry_evidence": _jsonable(self.geometry_evidence),
            "query_receipts": [item.to_dict() for item in self.query_receipts],
            "adapter": {
                "gate_status": self.adapter_gate_status,
                "reason_code": self.adapter_reason_code,
                "current_query_receipt_id": self.adapter_current_query_receipt_id,
                "all_query_receipt_ids": list(self.adapter_all_query_receipt_ids),
                "active_graph_candidate_ids": list(self.active_graph_candidate_ids),
            },
            "observables": _jsonable(self.observables),
            "candidates": [item.to_dict() for item in self.candidates],
            "checks": [item.to_dict() for item in self.checks],
        }


@dataclass(frozen=True, slots=True)
class AnalyticValidationSuiteResult:
    """Deterministic aggregate whose cases retain all individual evidence."""

    suite_id: str
    status: AnalyticValidationStatus
    cases: tuple[AnalyticValidationCaseResult, ...]

    def __post_init__(self) -> None:
        expected_status = (
            AnalyticValidationStatus.PASSED
            if self.cases
            and all(item.status is AnalyticValidationStatus.PASSED for item in self.cases)
            else AnalyticValidationStatus.FAILED
        )
        if self.status is not expected_status:
            raise ContractViolation("analytic suite status does not match its case outcomes")
        expected_id = stable_content_id(
            "m03_analytic_validation_suite",
            {
                "schema_version": ANALYTIC_VALIDATION_SCHEMA_VERSION,
                "suite_definition_id": ANALYTIC_VALIDATION_SUITE_ID,
                "status": self.status,
                "cases": tuple(item.to_dict() for item in self.cases),
            },
        )
        if self.suite_id != expected_id:
            raise ContractViolation("analytic validation suite identity mismatch")

    @property
    def passed_count(self) -> int:
        return sum(item.status is AnalyticValidationStatus.PASSED for item in self.cases)

    @property
    def failed_count(self) -> int:
        return len(self.cases) - self.passed_count

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": ANALYTIC_VALIDATION_SCHEMA_VERSION,
            "suite_definition_id": ANALYTIC_VALIDATION_SUITE_ID,
            "suite_id": self.suite_id,
            "task_id": "M03_SINGLE_SPINE_IMPLEMENTATION",
            "status": self.status.value,
            "case_count": len(self.cases),
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "scope": {
                "surface_evidence": "M01 public API over analytic VALIDATION_ONLY fixtures",
                "geometry_evidence": "M03 finite-cap composite needle and surface adapter",
                "mechanics_solver": "NOT_INVOKED",
                "measured_target_surface": "NOT_USED",
                "target_brick_claim": "NOT_MADE",
                "experimental_validation": "NOT_ASSESSED",
                "certification": "NOT_CERTIFIABLE",
            },
            "cases": [item.to_dict() for item in self.cases],
        }


@dataclass(frozen=True, slots=True)
class _AnalyticFixture:
    case_id: str
    family: SurfaceFamily
    parameters: Mapping[str, object]
    tip_center_global_mm: Vector3
    expected_points: tuple[tuple[str, Vector3], ...]
    expected_normals: tuple[tuple[str, Vector3], ...]
    expected_signed_center_distance_mm: float
    expected_gate_statuses: tuple[GeometryGateStatus, ...]
    absolute_tolerance_mm: float


def _vector3(value: Sequence[float] | FloatArray) -> Vector3:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (3,) or not np.isfinite(array).all():
        raise ContractViolation("analytic validation expected a finite three-vector")
    return float(array[0]), float(array[1]), float(array[2])


def _fixtures() -> tuple[_AnalyticFixture, ...]:
    offset = 0.0
    center_xy = np.array((75.0, 75.0), dtype=np.float64)
    clearance = 0.1

    slope_x, slope_y = 0.2, -0.1
    slope_height = offset + slope_x * center_xy[0] + slope_y * center_xy[1]
    slope_normal = np.array((-slope_x, -slope_y, 1.0), dtype=np.float64)
    slope_normal /= np.linalg.norm(slope_normal)
    slope_support = np.array((center_xy[0], center_xy[1], slope_height))
    slope_center = slope_support + clearance * slope_normal

    sphere_radius = 3.0
    aperture_radius = 1.5
    aperture_root = math.sqrt(sphere_radius**2 - aperture_radius**2)
    cap_height = offset - aperture_root + sphere_radius
    bowl_height = offset + aperture_root - sphere_radius

    peak_amplitude = 0.3
    peak_sigma = 0.25
    peak_offset = 0.3
    multi_height = 2.0 * peak_amplitude * math.exp(-0.5 * (peak_offset / peak_sigma) ** 2)
    multi_center_height = 0.4

    switch_slope = 0.5
    switch_signed_distance = math.sqrt(0.8)
    switch_normal_scale = math.sqrt(1.0 + switch_slope**2)
    return (
        _AnalyticFixture(
            "analytic_plane",
            SurfaceFamily.PLANE,
            {"offset_mm": offset},
            (75.0, 75.0, clearance),
            (("plane_face", (75.0, 75.0, offset)),),
            (("plane_face", (0.0, 0.0, 1.0)),),
            clearance,
            (GeometryGateStatus.PASSED,),
            1.0e-10,
        ),
        _AnalyticFixture(
            "analytic_slope_plane",
            SurfaceFamily.SLOPE_PLANE,
            {"offset_mm": offset, "slope_x": slope_x, "slope_y": slope_y},
            _vector3(slope_center),
            (("plane_face", _vector3(slope_support)),),
            (("plane_face", _vector3(slope_normal)),),
            clearance,
            (GeometryGateStatus.PASSED,),
            2.0e-10,
        ),
        _AnalyticFixture(
            "analytic_convex_spherical_cap",
            SurfaceFamily.SPHERICAL_CAP,
            {
                "offset_mm": offset,
                "radius_mm": sphere_radius,
                "aperture_radius_mm": aperture_radius,
            },
            (75.0, 75.0, cap_height + clearance),
            (("spherical_patch", (75.0, 75.0, cap_height)),),
            (("spherical_patch", (0.0, 0.0, 1.0)),),
            clearance,
            (GeometryGateStatus.PASSED,),
            2.0e-10,
        ),
        _AnalyticFixture(
            "analytic_concave_spherical_bowl",
            SurfaceFamily.SPHERICAL_BOWL,
            {
                "offset_mm": offset,
                "radius_mm": sphere_radius,
                "aperture_radius_mm": aperture_radius,
            },
            (75.0, 75.0, bowl_height + clearance),
            (("spherical_patch", (75.0, 75.0, bowl_height)),),
            (("spherical_patch", (0.0, 0.0, 1.0)),),
            clearance,
            (GeometryGateStatus.PASSED,),
            2.0e-10,
        ),
        _AnalyticFixture(
            "analytic_constructed_multi_peak",
            SurfaceFamily.MULTI_GAUSSIAN_FEATURE,
            {
                "features": (
                    {
                        "feature_id": "peak_left",
                        "amplitude_mm": peak_amplitude,
                        "center_x_mm": 75.0 - peak_offset,
                        "center_y_mm": 75.0,
                        "sigma_mm": peak_sigma,
                    },
                    {
                        "feature_id": "peak_right",
                        "amplitude_mm": peak_amplitude,
                        "center_x_mm": 75.0 + peak_offset,
                        "center_y_mm": 75.0,
                        "sigma_mm": peak_sigma,
                    },
                )
            },
            (75.0, 75.0, multi_center_height),
            (("multi_gaussian_feature_smooth_face", (75.0, 75.0, multi_height)),),
            (("multi_gaussian_feature_smooth_face", (0.0, 0.0, 1.0)),),
            multi_center_height - multi_height,
            (
                GeometryGateStatus.PASSED,
                GeometryGateStatus.PASSED_NONSMOOTH_GRAPH,
            ),
            1.1e-3,
        ),
        _AnalyticFixture(
            "analytic_known_nearest_switch",
            SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH,
            {"offset_mm": offset, "ridge_slope": switch_slope},
            (75.0, 75.0, 1.0),
            (
                ("switch_face_negative", (75.0, 74.6, 0.2)),
                ("switch_face_positive", (75.0, 75.4, 0.2)),
            ),
            (
                (
                    "switch_face_negative",
                    (0.0, switch_slope / switch_normal_scale, 1.0 / switch_normal_scale),
                ),
                (
                    "switch_face_positive",
                    (0.0, -switch_slope / switch_normal_scale, 1.0 / switch_normal_scale),
                ),
            ),
            switch_signed_distance,
            (GeometryGateStatus.PASSED_NONSMOOTH_GRAPH,),
            2.0e-10,
        ),
    )


def _surface_handle(fixture: _AnalyticFixture) -> SurfaceQueryHandle:
    provider = SurfaceProvider()
    descriptor = make_analytic_source_descriptor()
    specification = provider.create_surface_spec(
        descriptor,
        fixture.family,
        dict(fixture.parameters),
    )
    if specification.spec is None:
        raise ContractViolation(
            f"analytic fixture spec was unavailable: {specification.status.reason_code}"
        )
    realization = provider.create_realization(descriptor, specification.spec)
    handle = provider.open_query_handle(realization)
    if handle is None:
        raise ContractViolation(
            f"analytic fixture realization was unavailable: {realization.status.reason_code}"
        )
    return handle


def _tip_pose(
    center_global_mm: Vector3,
    bundle: SingleSpineParameterBundle,
) -> TipPose:
    frame = canonical_local_frame()
    axis = np.asarray(
        engineering_initial_axis(frame, bundle.needle.alpha_rad, bundle.needle.beta_rad),
        dtype=np.float64,
    )
    center = np.asarray(center_global_mm, dtype=np.float64)
    root = center - bundle.needle.exposed_length_mm * axis
    return resolve_tip_pose(
        rigid_root_global_mm=_vector3(root),
        local_frame=frame,
        needle=bundle.needle,
    )


def _check(
    check_id: str,
    passed: bool,
    *,
    expected: object,
    observed: object,
    explanation: str,
    tolerance_mm: float | None = None,
) -> AnalyticValidationCheck:
    return AnalyticValidationCheck(
        check_id,
        bool(passed),
        expected,
        observed,
        tolerance_mm,
        explanation,
    )


def _maximum_point_error(
    expected: Mapping[str, Vector3],
    observed: Mapping[str, Sequence[float]],
) -> float:
    errors = [
        float(np.linalg.norm(np.asarray(observed[name]) - np.asarray(point)))
        for name, point in expected.items()
        if name in observed
    ]
    return max(errors, default=math.inf)


def _maximum_normal_error(
    expected: Mapping[str, Vector3],
    observed: Mapping[str, Sequence[Vector3]],
) -> float:
    errors: list[float] = []
    for name, normal in expected.items():
        alternatives = observed.get(name, ())
        errors.append(
            min(
                (
                    float(np.linalg.norm(np.asarray(item) - np.asarray(normal)))
                    for item in alternatives
                ),
                default=math.inf,
            )
        )
    return max(errors, default=math.inf)


def _current_candidates(candidates: Sequence[SupportCandidate]) -> tuple[SupportCandidate, ...]:
    current_origins = {
        CandidateOrigin.CURRENT_NEAREST,
        CandidateOrigin.CURRENT_CO_MINIMAL,
    }
    return tuple(item for item in candidates if current_origins.intersection(item.origins))


def _execute_fixture(fixture: _AnalyticFixture) -> AnalyticValidationCaseResult:
    bundle = make_baseline_parameter_bundle()
    needle = bundle.needle
    handle = _surface_handle(fixture)
    transform = make_identity_surface_frame_transform(handle)
    policy = make_geometry_query_policy()
    pose = _tip_pose(fixture.tip_center_global_mm, bundle)
    geometry = build_composite_needle_geometry(
        tip_pose=pose,
        needle=needle,
        axial_sample_count=17,
        radial_sample_count=8,
    )
    sweep = make_swept_needle_geometry((geometry,))
    footprint = derive_complete_query_footprint(handle, sweep, transform, policy)

    # Use the resolved pose value for both the independent public query and the
    # adapter.  The root-to-tip round trip can differ from the decimal fixture
    # literal by a few ulps; query identities intentionally preserve that
    # distinction.
    center = np.asarray(pose.current_tip_center_global_mm, dtype=np.float64)
    radius = needle.tip_radius_mm
    nearby = tuple(
        _vector3(center + np.asarray(offset, dtype=np.float64))
        for offset in (
            (radius, 0.0, 0.0),
            (-radius, 0.0, 0.0),
            (0.0, radius, 0.0),
            (0.0, -radius, 0.0),
        )
    )
    probes_global = np.asarray((pose.current_tip_center_global_mm, *nearby), dtype=np.float64)
    probes_surface = transform.global_to_surface_points(probes_global)
    closest = query_closest_features(
        handle,
        probes_surface,
        requested_tolerance_mm=policy.requested_tolerance_mm,
        co_minimal_tolerance_mm=policy.co_minimal_tolerance_mm,
        maximum_global_cells=policy.maximum_global_cells,
    )
    sphere = query_spherical_envelope_or_clearance(
        handle,
        probes_surface,
        radius,
        path="phi_minus_radius",
        requested_tolerance_mm=policy.requested_tolerance_mm,
        co_minimal_tolerance_mm=policy.co_minimal_tolerance_mm,
        maximum_global_cells=policy.maximum_global_cells,
    )
    adapter = collect_support_candidates(
        handle,
        tip_pose=pose,
        tip_radius_mm=radius,
        cap_blend_coordinate_mm=needle.cap_blend_coordinate_mm,
        footprint=footprint,
        transform=transform,
        policy=policy,
        nearby_probe_centers_global_mm=nearby,
    )

    direct_features = closest.feature_sets[0]
    current = _current_candidates(adapter.candidates)
    expected_points = dict(fixture.expected_points)
    expected_normals = dict(fixture.expected_normals)
    direct_points = {item.feature_id: item.point_mm for item in direct_features}
    direct_normals = {item.feature_id: item.outward_normals for item in direct_features}
    direct_ids = tuple(sorted(item.feature_id for item in direct_features))
    expected_ids = tuple(sorted(expected_points))
    current_ids = tuple(sorted(item.feature_id for item in current))

    sphere_values = sphere.field("sphere_clearance_mm").values
    sphere_gap = None if sphere_values is None else float(sphere_values[0])
    expected_gap = fixture.expected_signed_center_distance_mm - radius
    observed_candidate_gaps = tuple(item.sphere_gap_mm for item in current)
    point_error = _maximum_point_error(expected_points, direct_points)
    normal_error = _maximum_normal_error(expected_normals, direct_normals)
    signed_distances = tuple(item.signed_distance_mm for item in direct_features)
    signed_distance_error = max(
        (abs(item - fixture.expected_signed_center_distance_mm) for item in signed_distances),
        default=math.inf,
    )
    gap_error = max(
        (
            *(abs(item - expected_gap) for item in observed_candidate_gaps),
            math.inf if sphere_gap is None else abs(sphere_gap - expected_gap),
        )
    )

    comparison_tolerance = max(
        fixture.absolute_tolerance_mm,
        (closest.error_bound or 0.0) + policy.candidate_merge_tolerance_mm,
    )
    unmatched_direct = tuple(
        item.feature_id
        for item in direct_features
        if not any(
            candidate.feature_id == item.feature_id
            and math.dist(candidate.point_global_mm, item.point_mm) <= comparison_tolerance
            for candidate in current
        )
    )
    unmatched_adapter = tuple(
        item.feature_id
        for item in current
        if not any(
            feature.feature_id == item.feature_id
            and math.dist(item.point_global_mm, feature.point_mm) <= comparison_tolerance
            for feature in direct_features
        )
    )
    stored_cap_errors = tuple(
        abs(
            item.cap_legality_margin_mm
            - finite_cap_legality_margin_mm(
                item.point_global_mm,
                pose.current_tip_center_global_mm,
                pose.current_axis_global,
                needle.cap_blend_coordinate_mm,
            )
        )
        for item in current
    )
    rear_point = _vector3(center - radius * np.asarray(pose.current_axis_global, dtype=np.float64))
    rear_margin = finite_cap_legality_margin_mm(
        rear_point,
        pose.current_tip_center_global_mm,
        pose.current_axis_global,
        needle.cap_blend_coordinate_mm,
    )
    closest_metadata = dict(closest.metadata)

    checks = (
        _check(
            "m01_query_status_and_quality",
            closest.status.reason_code == "M01_OK"
            and sphere.status.reason_code == "M01_OK"
            and closest.capability is not QueryCapability.UNAVAILABLE
            and sphere.capability is not QueryCapability.UNAVAILABLE
            and closest.convergence_level
            not in {ConvergenceLevel.REFINEMENT_REQUIRED, ConvergenceLevel.FAILED}
            and sphere.convergence_level
            not in {ConvergenceLevel.REFINEMENT_REQUIRED, ConvergenceLevel.FAILED}
            and bool(closest.quality_mask.all())
            and bool(sphere.quality_mask.all()),
            expected="supported, quality-passing, non-failed M01 responses",
            observed={
                "closest_reason_code": closest.status.reason_code,
                "closest_capability": closest.capability.value,
                "closest_convergence": closest.convergence_level.value,
                "sphere_reason_code": sphere.status.reason_code,
                "sphere_capability": sphere.capability.value,
                "sphere_convergence": sphere.convergence_level.value,
            },
            explanation="M01 quality and capability status stay explicit for both public queries.",
        ),
        _check(
            "queries_are_in_domain",
            all(
                item in {DomainStatus.IN_DOMAIN, DomainStatus.ON_BOUNDARY}
                for item in closest.domain_status
            )
            and all(
                item in {DomainStatus.IN_DOMAIN, DomainStatus.ON_BOUNDARY}
                for item in sphere.domain_status
            ),
            expected="IN_DOMAIN or ON_BOUNDARY",
            observed={
                "closest": tuple(item.value for item in closest.domain_status),
                "sphere": tuple(item.value for item in sphere.domain_status),
            },
            explanation="No implicit coordinate clamp or wrap is accepted by this fixture.",
        ),
        _check(
            "expected_full_nearest_feature_set",
            direct_ids == expected_ids,
            expected=expected_ids,
            observed=direct_ids,
            explanation="The complete current-center M01 feature set matches the constructed fixture.",
        ),
        _check(
            "nearest_point",
            point_error <= fixture.absolute_tolerance_mm,
            expected=expected_points,
            observed=direct_points,
            tolerance_mm=fixture.absolute_tolerance_mm,
            explanation="M01 nearest points agree with the independent analytic construction.",
        ),
        _check(
            "signed_center_distance",
            signed_distance_error <= fixture.absolute_tolerance_mm,
            expected=fixture.expected_signed_center_distance_mm,
            observed=signed_distances,
            tolerance_mm=fixture.absolute_tolerance_mm,
            explanation="Outside-positive M01 center distance agrees with the analytic fixture.",
        ),
        _check(
            "sphere_gap_phi_minus_radius",
            gap_error <= fixture.absolute_tolerance_mm,
            expected=expected_gap,
            observed={"public_query": sphere_gap, "adapter_candidates": observed_candidate_gaps},
            tolerance_mm=fixture.absolute_tolerance_mm,
            explanation="The public phi-minus-radius gap and M03 candidate gaps agree.",
        ),
        _check(
            "outward_normal",
            normal_error <= fixture.absolute_tolerance_mm,
            expected=expected_normals,
            observed=direct_normals,
            tolerance_mm=fixture.absolute_tolerance_mm,
            explanation="Normals use M01 outward-from-height-field-solid orientation.",
        ),
        _check(
            "finite_cap_legality",
            bool(current)
            and all(item.finite_cap_legal for item in current)
            and max(stored_cap_errors, default=math.inf) <= 1.0e-12,
            expected="all current supports legal with independently reproduced margins",
            observed={
                item.feature_id: {
                    "finite_cap_legal": item.finite_cap_legal,
                    "margin_mm": item.cap_legality_margin_mm,
                }
                for item in current
            },
            tolerance_mm=1.0e-12,
            explanation="Only the finite forward spherical cap is eligible for tip support.",
        ),
        _check(
            "rear_sphere_is_not_finite_cap",
            rear_margin < -policy.finite_cap_tolerance_mm,
            expected=f"margin < {-policy.finite_cap_tolerance_mm}",
            observed=rear_margin,
            tolerance_mm=policy.finite_cap_tolerance_mm,
            explanation="A rear-sphere point is explicitly rejected by the cap half-space gate.",
        ),
        _check(
            "local_minimum_and_empty_ball",
            bool(current)
            and all(item.local_minimum_verified and item.empty_ball_verified for item in current),
            expected=True,
            observed={
                item.feature_id: {
                    "local_minimum_verified": item.local_minimum_verified,
                    "empty_ball_verified": item.empty_ball_verified,
                }
                for item in current
            },
            explanation="Each retained current support carries both local-minimum and empty-ball evidence.",
        ),
        _check(
            "global_candidate_coverage",
            closest_metadata.get("global_candidate_coverage") is True,
            expected=True,
            observed=closest_metadata.get("global_candidate_coverage"),
            explanation="The M01 receipt declares comparison against its complete candidate search.",
        ),
        _check(
            "public_to_adapter_full_candidate_comparison",
            not unmatched_direct and not unmatched_adapter and direct_ids == current_ids,
            expected={"feature_ids": direct_ids, "unmatched": ()},
            observed={
                "adapter_feature_ids": current_ids,
                "unmatched_public": unmatched_direct,
                "unmatched_adapter": unmatched_adapter,
            },
            tolerance_mm=comparison_tolerance,
            explanation="The adapter neither drops nor invents a current co-minimal M01 feature.",
        ),
        _check(
            "query_receipt_linkage",
            adapter.current_query_receipt_id == sphere.query_id
            and closest.query_id in adapter.all_query_receipt_ids
            and sphere.query_id in adapter.all_query_receipt_ids
            and all(item.query_receipt_ids for item in current),
            expected=(closest.query_id, sphere.query_id),
            observed={
                "adapter_current": adapter.current_query_receipt_id,
                "adapter_all": adapter.all_query_receipt_ids,
            },
            explanation="Every M03 support remains linked to the public M01 query receipts.",
        ),
        _check(
            "adapter_quality_and_status",
            adapter.gate_status in fixture.expected_gate_statuses
            and adapter.reason_code == "M01_OK"
            and all(item.query_quality_passed for item in current),
            expected={
                "gate_status": tuple(item.value for item in fixture.expected_gate_statuses),
                "reason_code": "M01_OK",
            },
            observed={
                "gate_status": adapter.gate_status.value,
                "reason_code": adapter.reason_code,
                "current_candidate_quality": tuple(item.query_quality_passed for item in current),
            },
            explanation="Smooth and nonsmooth accepted graphs are distinguished without a binary alias.",
        ),
    )
    status = (
        AnalyticValidationStatus.PASSED
        if all(item.passed for item in checks)
        else AnalyticValidationStatus.FAILED
    )
    geometry_evidence: dict[str, object] = {
        "composite_geometry_id": geometry.geometry_id,
        "composite_geometry_hash": geometry.geometry_hash,
        "sweep_id": sweep.sweep_id,
        "sweep_hash": sweep.sweep_hash,
        "part_order": tuple(item.value for item in NeedlePart),
        "part_witness_counts": {
            item.part.value: len(item.witness_points_global_mm) for item in sweep.parts
        },
        "part_cover_radii_mm": {
            item.part.value: item.continuous_cover_radius_mm for item in sweep.parts
        },
        "footprint_id": footprint.footprint_id,
        "footprint_bounds_mm": (
            footprint.x_min_mm,
            footprint.x_max_mm,
            footprint.y_min_mm,
            footprint.y_max_mm,
        ),
        "footprint_guard_mm": footprint.guard_mm,
        "surface_transform_id": transform.transform_id,
        "geometry_query_policy_id": policy.policy_id,
        "finite_cap_blend_coordinate_mm": needle.cap_blend_coordinate_mm,
    }
    observables: dict[str, object] = {
        "tip_center_global_mm": fixture.tip_center_global_mm,
        "tip_axis_global": pose.current_axis_global,
        "sphere_radius_mm": radius,
        "expected_signed_center_distance_mm": fixture.expected_signed_center_distance_mm,
        "expected_sphere_gap_mm": expected_gap,
        "public_nearest_points_global_mm": tuple(item.point_mm for item in direct_features),
        "public_outward_normals_global": tuple(item.outward_normals for item in direct_features),
        "public_signed_center_distances_mm": signed_distances,
        "public_sphere_gap_mm": sphere_gap,
        "adapter_minimum_signed_distance_mm": adapter.minimum_signed_distance_mm,
        "rear_cap_test_point_global_mm": rear_point,
        "rear_cap_legality_margin_mm": rear_margin,
        "global_candidate_coverage": closest_metadata.get("global_candidate_coverage"),
    }
    return AnalyticValidationCaseResult(
        fixture.case_id,
        fixture.family.value,
        fixture.parameters,
        status,
        _PASS_REASON if status is AnalyticValidationStatus.PASSED else _FAIL_REASON,
        handle.spec.surface_spec_id,
        handle.realization.surface_realization_id,
        geometry_evidence,
        (QueryReceiptEvidence.from_response(closest), QueryReceiptEvidence.from_response(sphere)),
        adapter.gate_status.value,
        adapter.reason_code,
        adapter.current_query_receipt_id,
        adapter.all_query_receipt_ids,
        adapter.active_graph_candidate_ids,
        observables,
        tuple(SupportCandidateEvidence.from_candidate(item) for item in adapter.candidates),
        checks,
    )


def _failed_fixture(
    fixture: _AnalyticFixture,
    error: Exception,
) -> AnalyticValidationCaseResult:
    check = _check(
        "fixture_execution",
        False,
        expected="fixture completes with explicit M01/M03 evidence",
        observed={"exception_type": type(error).__name__, "message": str(error)},
        explanation="The fixture failed before its complete evidence set could be assembled.",
    )
    return AnalyticValidationCaseResult(
        fixture.case_id,
        fixture.family.value,
        fixture.parameters,
        AnalyticValidationStatus.FAILED,
        _FAIL_REASON,
        None,
        None,
        {},
        (),
        None,
        None,
        None,
        (),
        (),
        {},
        (),
        (check,),
    )


def run_analytic_surface_validation_suite() -> AnalyticValidationSuiteResult:
    """Run the six M01/M03 analytic geometry fixtures and retain all evidence."""

    outcomes: list[AnalyticValidationCaseResult] = []
    for fixture in _fixtures():
        try:
            outcomes.append(_execute_fixture(fixture))
        except Exception as error:  # The CLI must preserve a machine-readable failed case.
            outcomes.append(_failed_fixture(fixture, error))
    cases = tuple(outcomes)
    status = (
        AnalyticValidationStatus.PASSED
        if cases and all(item.status is AnalyticValidationStatus.PASSED for item in cases)
        else AnalyticValidationStatus.FAILED
    )
    payload = {
        "schema_version": ANALYTIC_VALIDATION_SCHEMA_VERSION,
        "suite_definition_id": ANALYTIC_VALIDATION_SUITE_ID,
        "status": status,
        "cases": tuple(item.to_dict() for item in cases),
    }
    return AnalyticValidationSuiteResult(
        stable_content_id("m03_analytic_validation_suite", payload),
        status,
        cases,
    )


__all__ = [
    "ANALYTIC_VALIDATION_SCHEMA_VERSION",
    "ANALYTIC_VALIDATION_SUITE_ID",
    "AnalyticValidationCaseResult",
    "AnalyticValidationCheck",
    "AnalyticValidationStatus",
    "AnalyticValidationSuiteResult",
    "QueryReceiptEvidence",
    "SupportCandidateEvidence",
    "run_analytic_surface_validation_suite",
]
