"""Frozen standalone single-spine operation driver.

The driver is an outer physical-operation owner.  It supplies prescribed base
poses to the intrinsic A-M0 kernel and delegates signed-root localization,
earliestness, simultaneous grouping, and event/pre/post orchestration to the
public M02 API.  It never adds ``Pz`` to the embedded A-to-B request.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, fields
from typing import Protocol, runtime_checkable

import numpy as np

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import MaturityStatus, SourceIdentity
from spine_sim.numerics.config import NumericsConfig
from spine_sim.numerics.contracts import (
    EventAdmissibleSide,
    EventCertificateKind,
    EventChannelRegistration,
    EventDetectionMode,
    EventTriggerDirection,
    M02ReasonCode,
    ReturnPathCapability,
    ReturnPathMode,
)
from spine_sim.numerics.events import (
    EquilibriumGuardSnapshot,
    EventCoverageDeclaration,
    EventEngine,
    EventSearchRequest,
    EventSearchResult,
)
from spine_sim.surface import query_height_differential

from .contracts import (
    M03_SCHEMA_VERSION,
    AcceptedSupportState,
    EmbeddedErrorClass,
    EmbeddedSingleSpineTrialRequest,
    FailureAxis,
    ImmutableSingleSpineState,
    MaterialSubstate,
    NeedleStrengthSubstate,
    OperationPhase,
    PrescribedBaseIncrement,
    PrimaryMechanicalState,
    RigidPose,
    SemanticMetadata,
    SingleSpineTrialResponse,
    StandaloneSingleSpineRunRequest,
    StandaloneSingleSpineRunResponse,
    StandaloneTerminalStatus,
    TrialIdentity,
    Vector3,
    make_embedded_request,
    make_initial_single_spine_state,
    make_metadata,
    make_rigid_pose,
)
from .events import (
    M03EventKind,
    M03EventPostReassemblyEvidence,
    evaluate_m03_event_post_reassembly,
    m03_event_registrations,
    m03_event_spec,
)
from .geometry import engineering_initial_axis
from .kernel import IntrinsicSingleSpineKernel, KernelEvaluation, make_needle_identity

STANDALONE_DRIVER_VERSION = "M03_STANDALONE_DRIVER_1.0.0"
RELEASE_PROTOCOL_VERSION = "LIFT_OFF_RESEARCH_V1"


class StandaloneTrialKernel(Protocol):
    """Dependency-injection boundary for the side-effect-free intrinsic kernel."""

    def evaluate_trial(
        self,
        request: EmbeddedSingleSpineTrialRequest,
    ) -> SingleSpineTrialResponse: ...


@runtime_checkable
class StandaloneArtifactTrialKernel(StandaloneTrialKernel, Protocol):
    """Optional richer boundary implemented by the intrinsic M03 kernel."""

    def evaluate_trial_with_artifacts(
        self,
        request: EmbeddedSingleSpineTrialRequest,
    ) -> KernelEvaluation: ...


ReturnPathProvider = Callable[
    [StandaloneSingleSpineRunRequest, ImmutableSingleSpineState, SingleSpineTrialResponse],
    ReturnPathCapability,
]


@dataclass(frozen=True, slots=True)
class StandaloneDriverConfig:
    """Fully expanded outer-operation numerical policy."""

    initial_retreat_step_mm: float
    maximum_initial_retreat_mm: float
    drag_step_mm: float
    event_scan_subdivisions: int
    minimum_z_bracket_mm: float
    maximum_preload_z_travel_mm: float
    maximum_lift_z_travel_mm: float
    bracket_expansion_factor: float
    event_side_offset_mm: float
    maximum_release_cycles: int
    config_id: str
    config_hash: str

    @classmethod
    def resolved(cls, request: StandaloneSingleSpineRunRequest) -> StandaloneDriverConfig:
        radius = request.parameter_bundle.needle.tip_radius_mm
        length = request.parameter_bundle.needle.exposed_length_mm
        mount_travel = request.parameter_bundle.mount.maximum_compression_mm
        initial_retreat_step_mm = radius
        maximum_initial_retreat_mm = 2.0 * length + mount_travel
        drag_step_mm = 1.0
        # Five scan cells keep the canonical contact and preload roots inside
        # brackets instead of on shared scan endpoints.  M02 still performs
        # the native-tolerance root solve and earliestness proof.
        event_scan_subdivisions = 5
        minimum_z_bracket_mm = 2.0 * radius
        maximum_preload_z_travel_mm = mount_travel + length
        maximum_lift_z_travel_mm = mount_travel + length
        bracket_expansion_factor = 2.0
        event_side_offset_mm = max(
            radius * request.parameter_bundle.numerical.event_position_tolerance_over_rt * 0.25,
            np.finfo(float).eps,
        )
        maximum_release_cycles = request.parameter_bundle.numerical.maximum_same_position_cascade
        payload = {
            "driver_version": STANDALONE_DRIVER_VERSION,
            "request_resolved_config_hash": request.resolved_config_hash,
            "initial_retreat_step_mm": initial_retreat_step_mm,
            "maximum_initial_retreat_mm": maximum_initial_retreat_mm,
            "drag_step_mm": drag_step_mm,
            "event_scan_subdivisions": event_scan_subdivisions,
            "minimum_z_bracket_mm": minimum_z_bracket_mm,
            "maximum_preload_z_travel_mm": maximum_preload_z_travel_mm,
            "maximum_lift_z_travel_mm": maximum_lift_z_travel_mm,
            "bracket_expansion_factor": bracket_expansion_factor,
            "event_side_offset_mm": event_side_offset_mm,
            "maximum_release_cycles": maximum_release_cycles,
        }
        digest = semantic_hash(payload)
        return cls(
            initial_retreat_step_mm=initial_retreat_step_mm,
            maximum_initial_retreat_mm=maximum_initial_retreat_mm,
            drag_step_mm=drag_step_mm,
            event_scan_subdivisions=event_scan_subdivisions,
            minimum_z_bracket_mm=minimum_z_bracket_mm,
            maximum_preload_z_travel_mm=maximum_preload_z_travel_mm,
            maximum_lift_z_travel_mm=maximum_lift_z_travel_mm,
            bracket_expansion_factor=bracket_expansion_factor,
            event_side_offset_mm=event_side_offset_mm,
            maximum_release_cycles=maximum_release_cycles,
            config_id=stable_content_id("m03_standalone_driver_config", payload),
            config_hash=digest,
        )

    def __post_init__(self) -> None:
        for name in (
            "initial_retreat_step_mm",
            "maximum_initial_retreat_mm",
            "drag_step_mm",
            "minimum_z_bracket_mm",
            "maximum_preload_z_travel_mm",
            "maximum_lift_z_travel_mm",
            "bracket_expansion_factor",
            "event_side_offset_mm",
        ):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0.0:
                raise ContractViolation(f"standalone driver {name} must be finite and positive")
        if self.event_scan_subdivisions < 2 or self.maximum_release_cycles < 1:
            raise ContractViolation("standalone event subdivisions/cycle limit are invalid")
        if self.bracket_expansion_factor <= 1.0:
            raise ContractViolation("standalone bracket expansion factor must exceed one")
        if len(self.config_hash) != 64 or not self.config_id:
            raise ContractViolation("standalone driver config requires stable identity/hash")


@dataclass(frozen=True, slots=True)
class ResolvedInitialPose:
    resolved_pose_id: str
    pose: RigidPose
    required_start_gap_mm: float
    actual_minimum_clearance_mm: float
    controlling_feature: str
    query_receipt_ids: tuple[str, ...]
    response_hash: str
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.required_start_gap_mm <= 0.0:
            raise ContractViolation("resolved initial pose requires positive g_start")
        if self.actual_minimum_clearance_mm < self.required_start_gap_mm:
            raise ContractViolation("resolved initial pose does not satisfy certified clearance")
        if not self.controlling_feature or not self.query_receipt_ids:
            raise ContractViolation("resolved initial pose requires feature/query evidence")


@dataclass(frozen=True, slots=True)
class UnavailableInitialPose:
    """Typed evidence that the standalone initial pose was not resolved.

    A terminal run still needs a deterministic reference pose for its immutable
    zero-history state.  That reference is not a certified clearance result:
    no clearance value, controlling feature, or query receipt is synthesized.
    Any receipt/response identity below is retained only when a real failed
    trial produced it.
    """

    evidence_id: str
    terminal_reference_pose: RigidPose
    reason_code: str
    failure_axis: FailureAxis
    query_receipt_ids: tuple[str, ...]
    response_hash: str | None
    explanation: str
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if not self.evidence_id or not self.reason_code or not self.explanation:
            raise ContractViolation("unavailable initial pose needs explicit terminal evidence")
        if self.failure_axis is FailureAxis.NONE:
            raise ContractViolation("unavailable initial pose requires a failure axis")
        if any(not item for item in self.query_receipt_ids):
            raise ContractViolation("unavailable initial pose cannot contain empty receipt IDs")
        if self.response_hash is not None and len(self.response_hash) != 64:
            raise ContractViolation("unavailable initial pose response hash must be canonical")


@dataclass(frozen=True, slots=True)
class StandaloneAcceptedPointRecord:
    accepted_point_id: str
    run_id: str
    case_id: str
    sequence_index: int
    operation_phase: OperationPhase
    state: ImmutableSingleSpineState
    response_id: str
    response_hash: str
    pose_id: str
    operation_coordinate: float
    operation_coordinate_unit: str
    preload_eta: float | None
    normal_load_n: float
    drag_path_x_mm: float
    drag_elapsed_time_s: float
    query_receipt_ids: tuple[str, ...]
    opaque_trial_state_handle: str
    provisional_commit_intent: str
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.sequence_index < 0 or not math.isfinite(self.operation_coordinate):
            raise ContractViolation("accepted standalone point has invalid sequence/coordinate")
        if self.preload_eta is not None and not 0.0 <= self.preload_eta <= 1.0:
            raise ContractViolation("accepted preload eta must lie in [0,1]")
        if self.drag_path_x_mm != self.state.total_path_x_mm:
            raise ContractViolation("accepted record path must match immutable state")
        if self.drag_elapsed_time_s != self.state.drag_elapsed_time_s:
            raise ContractViolation("accepted record clock must match immutable state")


@dataclass(frozen=True, slots=True)
class StandaloneCommittedEventRecord:
    committed_event_id: str
    run_id: str
    case_id: str
    event_sequence_number: int
    event_kind: str
    operation_phase: OperationPhase
    operation_coordinate: float
    coordinate_unit: str
    raw_guard: float
    raw_guard_unit: str
    accepted_state_id: str
    accepted_point_id: str
    response_hash: str
    pre_event_response_hash: str | None
    post_event_response_hash: str | None
    simultaneous_group_id: str | None
    earliestness_certificate_id: str | None
    path_bracket: tuple[float, float]
    localization_error_mm: float
    probe_refs: tuple[str, ...]
    dependency_layer: int
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.event_sequence_number < 1 or self.dependency_layer < 0:
            raise ContractViolation("committed standalone event sequence/layer is invalid")
        if not math.isfinite(self.operation_coordinate) or not math.isfinite(self.raw_guard):
            raise ContractViolation("committed standalone event values must be finite")
        if (
            len(self.path_bracket) != 2
            or not all(math.isfinite(item) for item in self.path_bracket)
            or self.path_bracket[1] < self.path_bracket[0]
            or not math.isfinite(self.localization_error_mm)
            or self.localization_error_mm < 0.0
        ):
            raise ContractViolation("committed standalone event bracket is invalid")
        if self.pre_event_response_hash is None or self.post_event_response_hash is None:
            raise ContractViolation("committed standalone event requires pre/event/post evidence")
        if (
            len(
                {
                    self.pre_event_response_hash,
                    self.response_hash,
                    self.post_event_response_hash,
                }
            )
            != 3
        ):
            raise ContractViolation(
                "committed standalone event cannot reuse a pre/event/post response"
            )


@dataclass(frozen=True, slots=True)
class StandaloneRejectedTrialRecord:
    rejected_trial_id: str
    run_id: str
    case_id: str
    operation_phase: OperationPhase
    parent_state_id: str
    parent_state_version: int
    trial_request_id: str | None
    trial_response_hash: str | None
    reason_code: str
    failure_axis: FailureAxis
    pose_id: str
    accepted_history_advanced: bool
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.accepted_history_advanced:
            raise ContractViolation("rejected standalone trial cannot advance accepted history")


@dataclass(frozen=True, slots=True)
class StandaloneTrialSnapshot:
    """Immutable request/response evidence retained for canonical persistence.

    The outer driver previously retained only hashes.  Hashes are sufficient
    for audit comparison, but they cannot reconstruct the raw M03 accepted,
    work, contact, or rejected-diagnostic rows.  This snapshot therefore keeps
    the exact side-effect-free A-to-B exchange in execution history.  A kernel
    exception has ``response=None`` and an explicit exception detail.
    """

    trial_sequence: int
    operation_phase: OperationPhase
    parent_state_id: str
    target_pose_id: str
    request: EmbeddedSingleSpineTrialRequest
    response: SingleSpineTrialResponse | None
    exception_detail: str | None
    kernel_evaluation: KernelEvaluation | None = None

    def __post_init__(self) -> None:
        if self.trial_sequence < 0 or not self.parent_state_id or not self.target_pose_id:
            raise ContractViolation("standalone trial snapshot identity is invalid")
        if self.request.immutable_single_spine_state_n.state_id != self.parent_state_id:
            raise ContractViolation("standalone trial snapshot parent/request disagree")
        if self.response is None:
            if not self.exception_detail:
                raise ContractViolation("failed standalone trial snapshot needs exception detail")
        else:
            if self.exception_detail is not None:
                raise ContractViolation("successful standalone trial snapshot cannot own exception")
            if self.response.transaction.request_hash != self.request.request_hash:
                raise ContractViolation("standalone trial snapshot request/response disagree")
            if self.kernel_evaluation is not None and (
                self.kernel_evaluation.response.response_hash != self.response.response_hash
                or self.kernel_evaluation.response.response_id != self.response.response_id
            ):
                raise ContractViolation("standalone artifact/response snapshot disagree")


@dataclass(frozen=True, slots=True)
class OperationSegmentRecord:
    operation_segment_id: str
    run_id: str
    case_id: str
    segment_sequence: int
    phase: OperationPhase
    interpolation: str
    path_coordinate_id: str
    coordinate_unit: str
    start_coordinate: float
    end_coordinate: float
    start_pose_id: str
    end_pose_id: str
    swept_envelope_ref: str
    signed_guard_channel_ids: tuple[str, ...]
    quality_gate_id: str
    termination_condition: str
    termination_reason: str
    operation_speed_mm_per_s: float | None
    physical_operation_time_available: bool
    operation_elapsed_time_s: float | None
    drag_clock_start_s: float
    drag_clock_end_s: float
    accepted_point_ids: tuple[str, ...]
    committed_event_ids: tuple[str, ...]
    query_receipt_ids: tuple[str, ...]
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.segment_sequence < 0:
            raise ContractViolation("operation segment sequence cannot be negative")
        if not all(math.isfinite(item) for item in (self.start_coordinate, self.end_coordinate)):
            raise ContractViolation("operation segment coordinates must be finite")
        if self.physical_operation_time_available != (
            self.operation_speed_mm_per_s is not None and self.operation_elapsed_time_s is not None
        ):
            raise ContractViolation("operation time availability conflicts with speed/time fields")
        if self.operation_speed_mm_per_s is not None and self.operation_speed_mm_per_s <= 0.0:
            raise ContractViolation("declared operation speed must be positive")
        if self.operation_elapsed_time_s is not None and self.operation_elapsed_time_s < 0.0:
            raise ContractViolation("operation elapsed time cannot be negative")
        if self.drag_clock_end_s < self.drag_clock_start_s:
            raise ContractViolation("release/search operations cannot reset the drag clock")
        if not self.interpolation or not self.swept_envelope_ref:
            raise ContractViolation("operation segment requires interpolation/sweep evidence")
        if not self.signed_guard_channel_ids or not self.quality_gate_id:
            raise ContractViolation("operation segment requires guard and quality declarations")
        if not self.termination_condition or not self.termination_reason:
            raise ContractViolation("operation segment requires explicit termination semantics")


@dataclass(frozen=True, slots=True)
class StandaloneExecution:
    response: StandaloneSingleSpineRunResponse
    resolved_initial_pose: ResolvedInitialPose | UnavailableInitialPose
    resolved_driver_config: StandaloneDriverConfig
    accepted_points: tuple[StandaloneAcceptedPointRecord, ...]
    committed_events: tuple[StandaloneCommittedEventRecord, ...]
    rejected_trials: tuple[StandaloneRejectedTrialRecord, ...]
    operation_segments: tuple[OperationSegmentRecord, ...]
    trial_snapshots: tuple[StandaloneTrialSnapshot, ...]
    trial_call_count: int
    event_probe_count: int
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.trial_call_count < 0 or self.event_probe_count < 0:
            raise ContractViolation("standalone execution counters are invalid")
        if len(self.trial_snapshots) != self.trial_call_count:
            raise ContractViolation("standalone execution trial history/count disagree")
        if tuple(item.trial_sequence for item in self.trial_snapshots) != tuple(
            range(self.trial_call_count)
        ):
            raise ContractViolation("standalone execution trial history is not contiguous")
        if tuple(item.accepted_point_id for item in self.accepted_points) != (
            self.response.accepted_point_ids
        ):
            raise ContractViolation("standalone response/accepted records disagree")
        if tuple(item.committed_event_id for item in self.committed_events) != (
            self.response.committed_event_ids
        ):
            raise ContractViolation("standalone response/event records disagree")
        if tuple(item.rejected_trial_id for item in self.rejected_trials) != (
            self.response.rejected_trial_ids
        ):
            raise ContractViolation("standalone response/rejected records disagree")
        if isinstance(self.resolved_initial_pose, UnavailableInitialPose):
            evidence = self.resolved_initial_pose
            if self.accepted_points or self.response.completed_travel:
                raise ContractViolation(
                    "unavailable initial pose cannot own accepted points or completed travel"
                )
            if (
                self.response.failure_axis is not evidence.failure_axis
                or self.response.terminal_reason_code != evidence.reason_code
                or self.response.final_pose.pose_id != evidence.terminal_reference_pose.pose_id
            ):
                raise ContractViolation("unavailable initial pose/terminal response disagree")
        elif self.trial_call_count == 0:
            raise ContractViolation("resolved initial pose requires at least one real trial")


class _DriverFailure(Exception):
    def __init__(
        self,
        reason_code: str,
        failure_axis: FailureAxis,
        explanation: str,
    ) -> None:
        super().__init__(explanation)
        self.reason_code = reason_code
        self.failure_axis = failure_axis
        self.explanation = explanation


def _terminal_status_for_failure(failure_axis: FailureAxis) -> StandaloneTerminalStatus:
    """Map every frozen failure axis without collapsing domain/capability failures."""

    return {
        FailureAxis.PHYSICAL_INFEASIBLE: StandaloneTerminalStatus.PHYSICAL_TERMINATION,
        FailureAxis.DOMAIN_ERROR: StandaloneTerminalStatus.DOMAIN_TERMINATION,
        FailureAxis.CAPABILITY_UNAVAILABLE: StandaloneTerminalStatus.CAPABILITY_TERMINATION,
        FailureAxis.CONTRACT_REJECTION: StandaloneTerminalStatus.CAPABILITY_TERMINATION,
        FailureAxis.TRANSACTION_FAILURE: StandaloneTerminalStatus.TRANSACTION_TERMINATION,
        FailureAxis.NUMERICAL_FAILURE: StandaloneTerminalStatus.NUMERICAL_TERMINATION,
        FailureAxis.NONE: StandaloneTerminalStatus.NUMERICAL_TERMINATION,
    }[failure_axis]


@dataclass(slots=True)
class _ExecutionContext:
    request: StandaloneSingleSpineRunRequest
    config: StandaloneDriverConfig
    kernel: StandaloneTrialKernel
    event_engine: EventEngine
    accepted: list[StandaloneAcceptedPointRecord]
    events: list[StandaloneCommittedEventRecord]
    rejected: list[StandaloneRejectedTrialRecord]
    operations: list[OperationSegmentRecord]
    trials: list[StandaloneTrialSnapshot]
    trial_call_count: int = 0
    event_probe_count: int = 0
    current_response: SingleSpineTrialResponse | None = None
    committed_response: SingleSpineTrialResponse | None = None


@dataclass(frozen=True, slots=True)
class _LocatedGuard:
    position: float
    response: SingleSpineTrialResponse
    result: EventSearchResult


@dataclass(frozen=True, slots=True)
class _DragStepOutcome:
    state: ImmutableSingleSpineState
    response: SingleSpineTrialResponse
    released: bool


@dataclass(frozen=True, slots=True)
class _PreloadBalanceOutcome:
    state: ImmutableSingleSpineState
    response: SingleSpineTrialResponse
    endpoint_post_evidence: M03EventPostReassemblyEvidence | None


def _m02_config(request: StandaloneSingleSpineRunRequest) -> NumericsConfig:
    numerical = request.parameter_bundle.numerical
    return NumericsConfig.resolved(
        initial_step_over_lref=numerical.initial_step_over_rt,
        maximum_step_over_lref=numerical.maximum_step_over_rt,
        minimum_step_over_lref=numerical.minimum_step_over_rt,
        force_atol_n=numerical.force_absolute_tolerance_n,
        default_rtol=numerical.force_relative_tolerance,
        max_newton_iterations=numerical.maximum_newton_iterations,
        event_position_tol_over_lref=numerical.event_position_tolerance_over_rt,
        max_bracket_iterations=numerical.maximum_event_iterations,
        max_same_position_cascade=numerical.maximum_same_position_cascade,
    )


def _default_return_path_provider(
    request: StandaloneSingleSpineRunRequest,
    state: ImmutableSingleSpineState,
    response: SingleSpineTrialResponse,
) -> ReturnPathCapability:
    payload = {
        "policy_id": request.release_policy.policy_id,
        "state_id": state.state_id,
        "response_hash": response.response_hash,
    }
    return ReturnPathCapability.create(
        owner_id="M03_STANDALONE_SINGLE_SPINE",
        release_event_id=stable_content_id("m03_release_event", payload),
        mode=ReturnPathMode.EXPLICIT_RETURN_PATH,
        path_mapping_id=stable_content_id("m03_release_path_mapping", payload),
        pose_path_ref=stable_content_id("m03_release_pose_path", payload),
        swept_geometry_ref=stable_content_id("m03_release_swept_geometry", payload),
        reason_code="M03_LIFT_OFF_RESEARCH_V1_AVAILABLE",
        metadata_unit="1",
    )


class StandaloneSingleSpineDriver:
    """Execute the frozen clearance/search/preload/drag/release workflow."""

    def __init__(
        self,
        *,
        kernel: StandaloneTrialKernel | None = None,
        event_engine: EventEngine | None = None,
        config: StandaloneDriverConfig | None = None,
        return_path_provider: ReturnPathProvider | None = None,
    ) -> None:
        self._kernel = kernel or IntrinsicSingleSpineKernel()
        self._event_engine = event_engine
        self._config = config
        self._return_path_provider = return_path_provider or _default_return_path_provider

    def run(
        self,
        request: StandaloneSingleSpineRunRequest,
    ) -> StandaloneSingleSpineRunResponse:
        """Return the frozen public response; use :meth:`execute` for raw records."""

        return self.execute(request).response

    def execute(self, request: StandaloneSingleSpineRunRequest) -> StandaloneExecution:
        if not isinstance(request, StandaloneSingleSpineRunRequest):
            raise ContractViolation("standalone driver requires StandaloneSingleSpineRunRequest")
        if request.release_policy.policy_id != RELEASE_PROTOCOL_VERSION:
            raise ContractViolation("standalone release protocol identity changed")
        config = self._config or StandaloneDriverConfig.resolved(request)
        engine = self._event_engine or EventEngine(_m02_config(request))
        context = _ExecutionContext(request, config, self._kernel, engine, [], [], [], [], [])
        resolved: ResolvedInitialPose | UnavailableInitialPose

        try:
            resolved, state, response = self._resolve_initial_pose(context)
            state, response = self._search_zero_load_contact(
                context,
                state,
                response,
                phase=OperationPhase.INITIAL_SEARCH,
                maximum_depth_mm=None,
                recontact=False,
            )
            state, response = self._preload(
                context,
                state,
                response,
                phase=OperationPhase.INITIAL_PRELOAD,
                reengagement=False,
            )
        except _DriverFailure as failure:
            if not context.accepted:
                # The public terminal response still needs an immutable state,
                # but its pose must not be represented as certified clearance.
                # Use the latest actual trial target when one exists; otherwise
                # use a deterministic, explicitly unavailable reference pose.
                terminal_pose = self._terminal_reference_pose(context)
                state = make_initial_single_spine_state(terminal_pose)
                current_response = context.current_response
                resolved = self._unavailable_initial_pose(
                    terminal_pose,
                    current_response,
                    failure,
                )
                remaining_energy = (
                    0.0 if current_response is None else _remaining_energy(current_response)
                )
            else:
                # This branch is defensive: initial-search/preload failures can
                # occur after the clearance point was committed.
                assert context.committed_response is not None
                state = context.accepted[-1].state
                response = context.committed_response
                remaining_energy = _remaining_energy(response)
            return self._execution(
                context,
                resolved,
                state,
                _terminal_status_for_failure(failure.failure_axis),
                failure.reason_code,
                failure.failure_axis,
                failure.explanation,
                remaining_energy,
            )

        release_cycles = 0
        while state.total_path_x_mm < request.drag_policy.travel_mm - 1.0e-12:
            try:
                outcome = self._drag_step(context, state, response)
            except _DriverFailure as failure:
                return self._execution(
                    context,
                    resolved,
                    state,
                    _terminal_status_for_failure(failure.failure_axis),
                    failure.reason_code,
                    failure.failure_axis,
                    failure.explanation,
                    _remaining_energy(response),
                )
            state, response = outcome.state, outcome.response
            if not outcome.released:
                continue
            release_cycles += 1
            if release_cycles > config.maximum_release_cycles:
                return self._execution(
                    context,
                    resolved,
                    state,
                    StandaloneTerminalStatus.NUMERICAL_TERMINATION,
                    M02ReasonCode.ZENO_CANDIDATE.value,
                    FailureAxis.NUMERICAL_FAILURE,
                    "same-position release cascade exceeded the frozen M02 limit",
                    _remaining_energy(response),
                )
            capability = self._return_path_provider(request, state, response)
            if capability.mode is not ReturnPathMode.EXPLICIT_RETURN_PATH:
                self._append_operation(
                    context,
                    phase=OperationPhase.HOLD_RELEASE_POSE,
                    interpolation="constant_pose",
                    path_coordinate_id="release_pose_hold",
                    coordinate_unit="1",
                    start_coordinate=0.0,
                    end_coordinate=0.0,
                    start_state=state,
                    end_state=state,
                    response=response,
                    guards=(m03_event_spec(M03EventKind.CONTACT_RELEASE).channel_id,),
                    termination_condition="explicit_return_path_capability",
                    termination_reason=capability.mode.value,
                )
                return self._execution(
                    context,
                    resolved,
                    state,
                    StandaloneTerminalStatus.HOLD_AT_RELEASE_POSE,
                    "M03_RELEASE_RETURN_PATH_UNAVAILABLE",
                    FailureAxis.CAPABILITY_UNAVAILABLE,
                    capability.reason_code,
                    _remaining_energy(response),
                )
            try:
                state, response = self._release_return_research_reload(
                    context,
                    resolved,
                    state,
                    response,
                    capability,
                )
            except _DriverFailure as failure:
                # A release operation may already have accepted a lift/reverse
                # point before a later research or reload trial fails.  HOLD is
                # always anchored to that last committed operation point, never
                # to a probe and never by resetting to the earlier release pose.
                if context.accepted:
                    state = context.accepted[-1].state
                if context.committed_response is not None:
                    response = context.committed_response
                self._append_operation(
                    context,
                    phase=OperationPhase.HOLD_RELEASE_POSE,
                    interpolation="constant_pose",
                    path_coordinate_id="release_pose_hold",
                    coordinate_unit="1",
                    start_coordinate=0.0,
                    end_coordinate=0.0,
                    start_state=state,
                    end_state=state,
                    response=response,
                    guards=(m03_event_spec(M03EventKind.CONTACT_RELEASE).channel_id,),
                    termination_condition="release_protocol_quality_and_coverage",
                    termination_reason=failure.reason_code,
                )
                return self._execution(
                    context,
                    resolved,
                    state,
                    StandaloneTerminalStatus.HOLD_AT_RELEASE_POSE,
                    "M03_RELEASE_RETURN_PATH_UNAVAILABLE",
                    failure.failure_axis,
                    failure.explanation,
                    _remaining_energy(response),
                )

        if state.primary_state is not PrimaryMechanicalState.TRAVEL_COMPLETE:
            return self._execution(
                context,
                resolved,
                state,
                StandaloneTerminalStatus.CAPABILITY_TERMINATION,
                "M03_TRAVEL_COMPLETION_EVENT_UNAVAILABLE",
                FailureAxis.CAPABILITY_UNAVAILABLE,
                "100 mm was reached without a separately assembled travel-complete event",
                _remaining_energy(response),
            )
        self._append_operation(
            context,
            phase=OperationPhase.COMPLETE,
            interpolation="constant_pose",
            path_coordinate_id="x_total_mm",
            coordinate_unit="mm",
            start_coordinate=state.total_path_x_mm,
            end_coordinate=state.total_path_x_mm,
            start_state=state,
            end_state=state,
            response=response,
            guards=(m03_event_spec(M03EventKind.TRAVEL_COMPLETE).channel_id,),
            termination_condition="x_total_mm == 100 mm",
            termination_reason="M03_TRAVEL_COMPLETE",
        )
        return self._execution(
            context,
            resolved,
            state,
            StandaloneTerminalStatus.TRAVEL_COMPLETE,
            "M03_OK",
            FailureAxis.NONE,
            None,
            _remaining_energy(response),
        )

    def _seed_pose(
        self,
        context: _ExecutionContext,
    ) -> tuple[RigidPose, float, tuple[str, ...]]:
        request = context.request
        domain = request.surface_query_handle.realization.logical_domain
        frame = request.local_frame
        axis = np.asarray(
            engineering_initial_axis(
                frame,
                request.parameter_bundle.needle.alpha_rad,
                request.parameter_bundle.needle.beta_rad,
            ),
            dtype=np.float64,
        )
        local_x = np.asarray(frame.e_x_global, dtype=np.float64)
        path_mid_xy = np.asarray(
            (
                0.5 * (domain.x_min_mm + domain.x_max_mm),
                0.5 * (domain.y_min_mm + domain.y_max_mm),
            )
        )
        tip_start_xy = path_mid_xy - 0.5 * request.drag_policy.travel_mm * local_x[:2]
        if not domain.contains(float(tip_start_xy[0]), float(tip_start_xy[1])):
            raise _DriverFailure(
                "M03_INITIAL_POSE_INFEASIBLE",
                FailureAxis.DOMAIN_ERROR,
                "the declared 100 mm local-x path cannot fit the M01 logical domain",
            )
        query = query_height_differential(
            request.surface_query_handle,
            [tip_start_xy],
            derivative_order=1,
        )
        height = query.field("height_mm")
        if height.values is None or not bool(np.asarray(height.validity).all()):
            raise _DriverFailure(
                "M03_INITIAL_POSE_INFEASIBLE",
                FailureAxis.DOMAIN_ERROR,
                "M01 could not resolve the standalone path anchor height",
            )
        surface_height = float(np.asarray(height.values, dtype=np.float64)[0])
        epsilon = float(query.error_bound or 0.0)
        radius = request.parameter_bundle.needle.tip_radius_mm
        g_start = max(0.20 * radius, epsilon + 0.01 * radius)
        tip_center_z = surface_height + radius + g_start
        length = request.parameter_bundle.needle.exposed_length_mm
        root = np.asarray(
            (
                tip_start_xy[0] - length * axis[0],
                tip_start_xy[1] - length * axis[1],
                tip_center_z - length * axis[2],
            ),
            dtype=np.float64,
        )
        pose = make_rigid_pose(
            _tuple3(root),
            reference_point_id=request.reference_point_id,
        )
        return pose, g_start, (query.query_id,)

    def _resolve_initial_pose(
        self,
        context: _ExecutionContext,
    ) -> tuple[ResolvedInitialPose, ImmutableSingleSpineState, SingleSpineTrialResponse]:
        seed_pose, g_start, anchor_receipts = self._seed_pose(context)
        maximum = context.config.maximum_initial_retreat_mm
        step = context.config.initial_retreat_step_mm
        last_response: SingleSpineTrialResponse | None = None
        last_failure: _DriverFailure | None = None
        offset = 0.0
        while offset <= maximum + 1.0e-12:
            pose = _translated_pose(seed_pose, (0.0, 0.0, offset))
            probe_state = make_initial_single_spine_state(pose)
            try:
                response = self._evaluate(
                    context,
                    probe_state,
                    pose,
                    OperationPhase.INITIAL_CLEARANCE,
                    "FULL_BODY_CLEARANCE_PROBE",
                    permit_rejected_response=True,
                )
            except _DriverFailure as failure:
                last_failure = failure
                if failure.failure_axis in {
                    FailureAxis.CONTRACT_REJECTION,
                    FailureAxis.DOMAIN_ERROR,
                    FailureAxis.CAPABILITY_UNAVAILABLE,
                    FailureAxis.TRANSACTION_FAILURE,
                }:
                    raise
                offset += step
                continue
            last_response = response
            # A rejected geometry/query response cannot own a certified
            # clearance scalar.  In particular, asking ``_full_clearance``
            # first would replace the original M01 capability reason with a
            # secondary "missing event guard" error when the uncertain
            # response correctly omitted that guard.  Preserve authoritative
            # contract/domain/capability/transaction axes at the probe where
            # they occurred; physical/numerical rejected poses may still be
            # escaped by the next +Z retreat.
            if not _response_eligible(response):
                failure_axis = response.diagnostics.failure_axis
                if failure_axis in {
                    FailureAxis.CONTRACT_REJECTION,
                    FailureAxis.DOMAIN_ERROR,
                    FailureAxis.CAPABILITY_UNAVAILABLE,
                    FailureAxis.TRANSACTION_FAILURE,
                }:
                    reason = (
                        response.diagnostics.original_reason_codes[0]
                        if response.diagnostics.original_reason_codes
                        else response.diagnostics.error_class.value
                    )
                    raise _DriverFailure(
                        reason,
                        failure_axis,
                        response.diagnostics.error_detail,
                    )
                offset += step
                continue
            actual = _full_clearance(response)
            if actual >= g_start:
                initial_parent = make_initial_single_spine_state(pose)
                payload = {
                    "pose_id": pose.pose_id,
                    "g_start_mm": g_start,
                    "actual_clearance_mm": actual,
                    "response_hash": response.response_hash,
                    "query_receipts": tuple(
                        dict.fromkeys(
                            (*anchor_receipts, *response.geometry_contact.query_receipt_ids)
                        )
                    ),
                }
                controlling = _controlling_clearance_feature(response)
                resolved = ResolvedInitialPose(
                    stable_content_id("m03_resolved_initial_pose", payload),
                    pose,
                    g_start,
                    actual,
                    controlling,
                    payload["query_receipts"],  # type: ignore[arg-type]
                    response.response_hash,
                    make_metadata(
                        "m03_resolved_initial_pose",
                        payload,
                        source_identity=SourceIdentity.PROPOSED_SUPPLEMENT,
                    ),
                )
                state = self._commit(
                    context,
                    initial_parent,
                    pose,
                    response,
                    OperationPhase.INITIAL_CLEARANCE,
                    operation_coordinate=offset,
                    coordinate_unit="mm",
                    preload_eta=None,
                    primary_override=PrimaryMechanicalState.OPEN,
                    path_delta_mm=0.0,
                    event_increment=0,
                    contact_cycle_id=0,
                )
                self._append_operation(
                    context,
                    phase=OperationPhase.INITIAL_CLEARANCE,
                    interpolation="linear_translation_global:+Z",
                    path_coordinate_id="initial_retreat_z_mm",
                    coordinate_unit="mm",
                    start_coordinate=0.0,
                    end_coordinate=offset,
                    start_state=make_initial_single_spine_state(seed_pose),
                    end_state=state,
                    response=response,
                    guards=(
                        m03_event_spec(M03EventKind.SWEPT_COLLISION).channel_id,
                        m03_event_spec(M03EventKind.GEOMETRY_UNCERTAIN).channel_id,
                    ),
                    termination_condition="minimum_complete_clearance_mm >= g_start_mm",
                    termination_reason="M03_INITIAL_CLEARANCE_CERTIFIED",
                )
                return resolved, state, response
            offset += step
        if last_response is None:
            if last_failure is not None:
                raise last_failure
            raise _DriverFailure(
                "M03_INITIAL_POSE_INFEASIBLE",
                FailureAxis.PHYSICAL_INFEASIBLE,
                "no evaluable full-body clearance pose was found",
            )
        if last_response.diagnostics.failure_axis in {
            FailureAxis.CONTRACT_REJECTION,
            FailureAxis.DOMAIN_ERROR,
            FailureAxis.CAPABILITY_UNAVAILABLE,
            FailureAxis.TRANSACTION_FAILURE,
        }:
            reason = (
                last_response.diagnostics.original_reason_codes[0]
                if last_response.diagnostics.original_reason_codes
                else last_response.diagnostics.error_class.value
            )
            raise _DriverFailure(
                reason,
                last_response.diagnostics.failure_axis,
                last_response.diagnostics.error_detail,
            )
        raise _DriverFailure(
            "M03_INITIAL_POSE_INFEASIBLE",
            last_response.diagnostics.failure_axis,
            "maximum +global-Z retreat did not certify the frozen initial clearance",
        )

    def _terminal_reference_pose(self, context: _ExecutionContext) -> RigidPose:
        """Return a real attempted target, or a deterministic unresolved anchor."""

        if context.trials:
            embedded = context.trials[-1].request
            return _translated_pose(
                embedded.base_pose_n,
                embedded.prescribed_base_increment.translation_global_mm,
            )
        domain = context.request.surface_query_handle.realization.logical_domain
        return make_rigid_pose(
            (
                0.5 * (domain.x_min_mm + domain.x_max_mm),
                0.5 * (domain.y_min_mm + domain.y_max_mm),
                0.0,
            ),
            reference_point_id=context.request.reference_point_id,
        )

    def _unavailable_initial_pose(
        self,
        pose: RigidPose,
        response: SingleSpineTrialResponse | None,
        failure: _DriverFailure,
    ) -> UnavailableInitialPose:
        query_receipts = (
            ()
            if response is None
            else tuple(dict.fromkeys(response.geometry_contact.query_receipt_ids))
        )
        payload = {
            "pose_id": pose.pose_id,
            "evidence_status": "UNAVAILABLE",
            "reason_code": failure.reason_code,
            "failure_axis": failure.failure_axis,
            "query_receipts": query_receipts,
            "response_hash": None if response is None else response.response_hash,
        }
        return UnavailableInitialPose(
            stable_content_id("m03_unavailable_initial_pose", payload),
            pose,
            failure.reason_code,
            failure.failure_axis,
            query_receipts,
            None if response is None else response.response_hash,
            failure.explanation,
            make_metadata(
                "m03_unavailable_initial_pose",
                payload,
                source_identity=SourceIdentity.PROPOSED_SUPPLEMENT,
            ),
        )

    def _search_zero_load_contact(
        self,
        context: _ExecutionContext,
        state: ImmutableSingleSpineState,
        response: SingleSpineTrialResponse,
        *,
        phase: OperationPhase,
        maximum_depth_mm: float | None,
        recontact: bool,
    ) -> tuple[ImmutableSingleSpineState, SingleSpineTrialResponse]:
        start_gap = max(_contact_gap(response), 0.0)
        radius = context.request.parameter_bundle.needle.tip_radius_mm
        tolerance = _position_tolerance(context.request)
        depth = (
            start_gap + max(8.0 * tolerance, 0.10 * radius)
            if maximum_depth_mm is None
            else maximum_depth_mm
        )
        registration = m03_event_registrations((M03EventKind.TIP_CONTACT_ESTABLISH,))[0]
        located = self._locate_guard(
            context,
            state,
            phase,
            "NESTED_Z_SEARCH",
            direction_global=(0.0, 0.0, -1.0),
            maximum_distance=depth,
            registration=registration,
            raw_guard=lambda item, _position: _contact_gap(item),
            raw_zero_tolerance=tolerance,
        )
        if located is None:
            raise _DriverFailure(
                "M03_FINITE_CAP_SUPPORT_UNAVAILABLE",
                FailureAxis.PHYSICAL_INFEASIBLE,
                "NESTED_Z_SEARCH did not locate a certified finite-cap contact",
            )
        event_pose = _translated_pose(state.base_pose, (0.0, 0.0, -located.position))
        event_response = self._evaluate(
            context,
            state,
            event_pose,
            phase,
            "ZERO_LOAD_EVENT_POINT",
        )
        post_evidence = self._event_post_evidence(
            context,
            state,
            phase,
            event_coordinate=located.position,
            direction_global=(0.0, 0.0, -1.0),
            event_position=located.position,
            purpose="ZERO_LOAD_CONTACT_EVENT_POST",
            channel_ids=(registration.channel_id,),
        )
        cycle = state.contact_cycle_id + 1
        event_state = self._commit(
            context,
            state,
            event_pose,
            event_response,
            phase,
            operation_coordinate=located.position,
            coordinate_unit="mm",
            preload_eta=0.0,
            primary_override=PrimaryMechanicalState.TIP_ZERO_LOAD,
            path_delta_mm=0.0,
            event_increment=1,
            contact_cycle_id=cycle,
        )
        point_id = context.accepted[-1].accepted_point_id
        event_kind = (
            M03EventKind.RECONTACT_ZERO_LOAD.value
            if recontact
            else M03EventKind.TIP_CONTACT_ESTABLISH.value
        )
        self._append_event(
            context,
            state=event_state,
            accepted_point_id=point_id,
            response=event_response,
            event_kind=event_kind,
            phase=phase,
            coordinate=located.position,
            coordinate_unit="mm",
            raw_guard=_contact_gap(event_response),
            raw_guard_unit="mm",
            sequence_number=event_state.event_sequence_number,
            post_evidence=post_evidence,
            search_result=located.result,
        )
        self._append_operation(
            context,
            phase=phase,
            interpolation="linear_translation_global:-Z",
            path_coordinate_id="nested_z_search_depth_mm",
            coordinate_unit="mm",
            start_coordinate=0.0,
            end_coordinate=located.position,
            start_state=state,
            end_state=event_state,
            response=event_response,
            guards=(registration.channel_id,),
            termination_condition="earliest legal finite-cap gap == 0",
            termination_reason=event_kind,
        )
        return event_state, event_response

    def _preload(
        self,
        context: _ExecutionContext,
        state: ImmutableSingleSpineState,
        response: SingleSpineTrialResponse,
        *,
        phase: OperationPhase,
        reengagement: bool,
    ) -> tuple[ImmutableSingleSpineState, SingleSpineTrialResponse]:
        request = context.request
        policy = request.preload_policy
        eta_values = np.linspace(
            policy.homotopy_start,
            policy.homotopy_end,
            policy.minimum_homotopy_points,
        )
        start_state = state
        start_accepted = len(context.accepted)
        start_events = len(context.events)
        previous_load = _normal_load(response)
        endpoint_post_evidence: M03EventPostReassemblyEvidence | None = None
        for eta in eta_values[1:]:
            target = float(eta) * policy.target_normal_force_n
            force_resolution = request.parameter_bundle.numerical.acceptance_force_resolution_n
            if previous_load <= force_resolution < target:
                state, response = self._commit_contact_load_onset(
                    context,
                    state,
                    phase=phase,
                    eta=float(eta),
                )
                previous_load = _normal_load(response)
            outcome = self._balance_normal_target(
                context,
                state,
                response,
                phase=phase,
                eta=float(eta),
                target_normal_load_n=target,
                reengagement=reengagement,
            )
            state, response = outcome.state, outcome.response
            endpoint_post_evidence = outcome.endpoint_post_evidence
            previous_load = _normal_load(response)

        event_count = 2 if reengagement else 1
        if endpoint_post_evidence is None:
            raise _DriverFailure(
                "M03_EVENT_POST_REASSEMBLY_UNAVAILABLE",
                FailureAxis.CAPABILITY_UNAVAILABLE,
                "preload endpoint was reached without complete event/post evidence",
            )
        final_point_id = context.accepted[-1].accepted_point_id
        first_sequence = state.event_sequence_number - event_count + 1
        if reengagement:
            self._append_event(
                context,
                state=state,
                accepted_point_id=final_point_id,
                response=response,
                event_kind=M03EventKind.RELOAD_TARGET_REACHED.value,
                phase=phase,
                coordinate=1.0,
                coordinate_unit="1",
                raw_guard=0.0,
                raw_guard_unit="1",
                sequence_number=first_sequence,
                post_evidence=endpoint_post_evidence,
            )
            first_sequence += 1
        self._append_event(
            context,
            state=state,
            accepted_point_id=final_point_id,
            response=response,
            event_kind=(
                M03EventKind.REENGAGEMENT.value
                if reengagement
                else M03EventKind.PRELOAD_TARGET_REACHED.value
            ),
            phase=phase,
            coordinate=1.0,
            coordinate_unit="1",
            raw_guard=(
                _normal_load(response)
                - request.parameter_bundle.numerical.acceptance_force_resolution_n
                if reengagement
                else 0.0
            ),
            raw_guard_unit="N" if reengagement else "1",
            sequence_number=first_sequence,
            post_evidence=endpoint_post_evidence,
        )
        self._append_operation(
            context,
            phase=phase,
            interpolation="nested_z_balance_at_fixed_local_x",
            path_coordinate_id="preload_eta",
            coordinate_unit="1",
            start_coordinate=0.0,
            end_coordinate=1.0,
            start_state=start_state,
            end_state=state,
            response=response,
            guards=(m03_event_spec(M03EventKind.PRELOAD_TARGET_REACHED).channel_id,),
            termination_condition="eta == 1 and normal_load == 0.5 N",
            termination_reason=(
                "M03_REENGAGEMENT_COMMITTED" if reengagement else "M03_INITIAL_PRELOAD_COMPLETE"
            ),
            accepted_point_ids=tuple(
                item.accepted_point_id for item in context.accepted[start_accepted:]
            ),
            committed_event_ids=tuple(
                item.committed_event_id for item in context.events[start_events:]
            ),
        )
        return state, response

    def _commit_contact_load_onset(
        self,
        context: _ExecutionContext,
        state: ImmutableSingleSpineState,
        *,
        phase: OperationPhase,
        eta: float,
    ) -> tuple[ImmutableSingleSpineState, SingleSpineTrialResponse]:
        """Locate and commit the scale-aware load-onset event before preload advances."""

        request = context.request
        force_resolution = request.parameter_bundle.numerical.acceptance_force_resolution_n
        intrinsic_spec = m03_event_spec(M03EventKind.CONTACT_LOAD_ONSET)
        registration = _standalone_channel(
            "m03.standalone.contact_load_onset",
            M03EventKind.CONTACT_LOAD_ONSET.value,
            intrinsic_spec.raw_guard_unit,
            intrinsic_spec.admissible_side,
            intrinsic_spec.trigger_direction,
        )
        located = self._locate_guard(
            context,
            state,
            phase,
            "CONTACT_LOAD_ONSET_EARLIEST_EVENT",
            direction_global=(0.0, 0.0, -1.0),
            maximum_distance=context.config.maximum_preload_z_travel_mm,
            registration=registration,
            raw_guard=lambda item, _position: _normal_load(item) - force_resolution,
            raw_zero_tolerance=request.parameter_bundle.numerical.force_absolute_tolerance_n,
        )
        if located is None:
            raise _DriverFailure(
                "M03_EVENT_MONITORING_CAPABILITY_UNAVAILABLE",
                FailureAxis.CAPABILITY_UNAVAILABLE,
                "preload would cross contact load onset without a certified event root",
            )
        pose = _translated_pose(state.base_pose, (0.0, 0.0, -located.position))
        event_response = self._evaluate(
            context,
            state,
            pose,
            phase,
            "CONTACT_LOAD_ONSET_EVENT_POINT",
        )
        post_evidence = self._event_post_evidence(
            context,
            state,
            phase,
            event_coordinate=located.position,
            direction_global=(0.0, 0.0, -1.0),
            event_position=located.position,
            purpose="CONTACT_LOAD_ONSET_EVENT_POST",
            channel_ids=(intrinsic_spec.channel_id,),
        )
        onset_eta = min(
            eta,
            force_resolution / request.preload_policy.target_normal_force_n,
        )
        event_state = self._commit(
            context,
            state,
            pose,
            event_response,
            phase,
            operation_coordinate=onset_eta,
            coordinate_unit="1",
            preload_eta=onset_eta,
            primary_override=PrimaryMechanicalState.PRELOAD_BUILD,
            path_delta_mm=0.0,
            event_increment=1,
            contact_cycle_id=state.contact_cycle_id,
        )
        self._append_event(
            context,
            state=event_state,
            accepted_point_id=context.accepted[-1].accepted_point_id,
            response=event_response,
            event_kind=M03EventKind.CONTACT_LOAD_ONSET.value,
            phase=phase,
            coordinate=onset_eta,
            coordinate_unit="1",
            raw_guard=_normal_load(event_response) - force_resolution,
            raw_guard_unit="N",
            sequence_number=event_state.event_sequence_number,
            post_evidence=post_evidence,
            search_result=located.result,
        )
        return event_state, event_response

    def _balance_normal_target(
        self,
        context: _ExecutionContext,
        state: ImmutableSingleSpineState,
        response: SingleSpineTrialResponse,
        *,
        phase: OperationPhase,
        eta: float,
        target_normal_load_n: float,
        reengagement: bool,
    ) -> _PreloadBalanceOutcome:
        current = _normal_load(response)
        tolerance = (
            context.request.parameter_bundle.numerical.force_absolute_tolerance_n
            + context.request.parameter_bundle.numerical.force_relative_tolerance
            * max(target_normal_load_n, 1.0)
        )
        if abs(current - target_normal_load_n) <= tolerance:
            located_response = response
            distance = 0.0
        else:
            stiffness = context.request.parameter_bundle.mount.spring_stiffness_n_per_mm
            nominal = (
                abs(target_normal_load_n - current) / stiffness
                if stiffness is not None and stiffness > 0.0
                else context.config.minimum_z_bracket_mm
            )
            distance_limit = max(
                context.config.minimum_z_bracket_mm,
                2.0 * nominal,
            )
            located: _LocatedGuard | None = None
            while distance_limit <= context.config.maximum_preload_z_travel_mm + 1.0e-12:
                registration = _standalone_channel(
                    channel_id=f"m03.standalone.preload_balance.eta_{eta:.12g}",
                    event_kind="PRELOAD_FORCE_BALANCE",
                    raw_unit="N",
                    admissible_side=EventAdmissibleSide.NONNEGATIVE,
                    direction=EventTriggerDirection.FALLING,
                )
                located = self._locate_guard(
                    context,
                    state,
                    phase,
                    f"PRELOAD_BALANCE_ETA_{eta:.12g}",
                    direction_global=(0.0, 0.0, -1.0),
                    maximum_distance=distance_limit,
                    registration=registration,
                    raw_guard=lambda item, _position: target_normal_load_n - _normal_load(item),
                    raw_zero_tolerance=tolerance,
                )
                if located is not None:
                    break
                distance_limit *= context.config.bracket_expansion_factor
            if located is None:
                raise _DriverFailure(
                    "M03_PRELOAD_INFEASIBLE",
                    FailureAxis.PHYSICAL_INFEASIBLE,
                    f"no certified z balance was found for preload eta={eta:.6g}",
                )
            distance = located.position
            pose = _translated_pose(state.base_pose, (0.0, 0.0, -distance))
            located_response = self._evaluate(
                context,
                state,
                pose,
                phase,
                f"PRELOAD_ACCEPT_ETA_{eta:.12g}",
            )
        load_error = abs(_normal_load(located_response) - target_normal_load_n)
        if load_error > tolerance:
            raise _DriverFailure(
                "M02_EVENT_ROOT_NONCONVERGENCE",
                FailureAxis.NUMERICAL_FAILURE,
                "preload z root did not satisfy the native N tolerance",
            )
        pose = (
            state.base_pose
            if distance == 0.0
            else _translated_pose(state.base_pose, (0.0, 0.0, -distance))
        )
        primary = (
            PrimaryMechanicalState.PRELOAD_BUILD
            if eta < 1.0
            else PrimaryMechanicalState.REATTACHED_ENTRY
            if reengagement
            else PrimaryMechanicalState.ATTACHED_STICK
        )
        endpoint_kinds: tuple[M03EventKind, ...] = ()
        endpoint_post_evidence: M03EventPostReassemblyEvidence | None = None
        if math.isclose(eta, 1.0, rel_tol=0.0, abs_tol=1.0e-15):
            endpoint_kinds = (
                (M03EventKind.RELOAD_TARGET_REACHED, M03EventKind.REENGAGEMENT)
                if reengagement
                else (M03EventKind.PRELOAD_TARGET_REACHED,)
            )
            endpoint_post_evidence = self._event_post_evidence(
                context,
                state,
                phase,
                event_coordinate=distance,
                direction_global=(0.0, 0.0, -1.0),
                event_position=distance,
                purpose="PRELOAD_ENDPOINT_EVENT_POST",
                channel_ids=tuple(m03_event_spec(item).channel_id for item in endpoint_kinds),
            )
        next_state = self._commit(
            context,
            state,
            pose,
            located_response,
            phase,
            operation_coordinate=eta,
            coordinate_unit="1",
            preload_eta=eta,
            primary_override=primary,
            path_delta_mm=0.0,
            event_increment=len(endpoint_kinds),
            contact_cycle_id=state.contact_cycle_id,
        )
        return _PreloadBalanceOutcome(next_state, located_response, endpoint_post_evidence)

    def _drag_step(
        self,
        context: _ExecutionContext,
        state: ImmutableSingleSpineState,
        response: SingleSpineTrialResponse,
    ) -> _DragStepOutcome:
        request = context.request
        remaining = request.drag_policy.travel_mm - state.total_path_x_mm
        step = min(context.config.drag_step_mm, remaining)
        direction = request.local_frame.e_x_global
        registrations = (
            _standalone_channel(
                "m03.standalone.contact_release",
                M03EventKind.CONTACT_RELEASE.value,
                "N",
                EventAdmissibleSide.NONNEGATIVE,
                EventTriggerDirection.FALLING,
            ),
            _standalone_channel(
                "m03.standalone.cap_legality",
                M03EventKind.CAP_LEGALITY_LOSS.value,
                "mm",
                EventAdmissibleSide.NONNEGATIVE,
                EventTriggerDirection.FALLING,
            ),
            _standalone_channel(
                "m03.standalone.swept_collision",
                M03EventKind.SWEPT_COLLISION.value,
                "mm",
                EventAdmissibleSide.NONNEGATIVE,
                EventTriggerDirection.FALLING,
                detection=EventDetectionMode.SWEPT_COLLISION,
                certificates=(
                    EventCertificateKind.SWEPT_NO_EVENT,
                    EventCertificateKind.ADAPTIVE_PROBE_SPACING,
                ),
            ),
        )
        force_resolution = request.parameter_bundle.numerical.acceptance_force_resolution_n
        located = self._locate_multiple_guards(
            context,
            state,
            OperationPhase.DRAG,
            "DRAG_EARLIEST_EVENT",
            direction_global=direction,
            maximum_distance=step,
            registrations=registrations,
            raw_guards={
                registrations[0].channel_id: lambda item, _position: (
                    _normal_load(item) - force_resolution
                ),
                registrations[1].channel_id: lambda item, _position: _cap_margin(item),
                registrations[2].channel_id: lambda item, _position: _body_clearance(item),
            },
            zero_tolerances={
                registrations[
                    0
                ].channel_id: request.parameter_bundle.numerical.force_absolute_tolerance_n,
                registrations[1].channel_id: _position_tolerance(request),
                registrations[2].channel_id: _position_tolerance(request),
            },
        )
        start_accepted = len(context.accepted)
        start_events = len(context.events)
        if located is None:
            pose = _translated_pose(state.base_pose, _scale3(direction, step))
            target_response = self._evaluate(
                context,
                state,
                pose,
                OperationPhase.DRAG,
                "DRAG_ACCEPTED_TARGET",
            )
            final = math.isclose(
                state.total_path_x_mm + step,
                request.drag_policy.travel_mm,
                abs_tol=1.0e-12,
            )
            completion_post_evidence = (
                self._event_post_evidence(
                    context,
                    state,
                    OperationPhase.DRAG,
                    event_coordinate=state.total_path_x_mm + step,
                    direction_global=direction,
                    event_position=step,
                    purpose="TRAVEL_COMPLETE_EVENT_POST",
                    channel_ids=(m03_event_spec(M03EventKind.TRAVEL_COMPLETE).channel_id,),
                )
                if final
                else None
            )
            next_state = self._commit(
                context,
                state,
                pose,
                target_response,
                OperationPhase.DRAG,
                operation_coordinate=state.total_path_x_mm + step,
                coordinate_unit="mm",
                preload_eta=None,
                primary_override=(
                    PrimaryMechanicalState.TRAVEL_COMPLETE
                    if final
                    else target_response.state_events.primary_mechanical_state
                ),
                path_delta_mm=step,
                event_increment=1 if final else 0,
                contact_cycle_id=state.contact_cycle_id,
            )
            if final:
                assert completion_post_evidence is not None
                self._append_event(
                    context,
                    state=next_state,
                    accepted_point_id=context.accepted[-1].accepted_point_id,
                    response=target_response,
                    event_kind=M03EventKind.TRAVEL_COMPLETE.value,
                    phase=OperationPhase.COMPLETE,
                    coordinate=next_state.total_path_x_mm,
                    coordinate_unit="mm",
                    raw_guard=request.drag_policy.travel_mm - next_state.total_path_x_mm,
                    raw_guard_unit="mm",
                    sequence_number=next_state.event_sequence_number,
                    post_evidence=completion_post_evidence,
                )
            self._append_operation(
                context,
                phase=OperationPhase.DRAG,
                interpolation="linear_translation_global:+local-x",
                path_coordinate_id="x_total_mm",
                coordinate_unit="mm",
                start_coordinate=state.total_path_x_mm,
                end_coordinate=next_state.total_path_x_mm,
                start_state=state,
                end_state=next_state,
                response=target_response,
                guards=tuple(item.channel_id for item in registrations),
                termination_condition="accepted drag target or earliest signed event",
                termination_reason="M03_DRAG_TARGET_ACCEPTED",
                operation_speed=request.drag_policy.speed_mm_per_s,
                accepted_point_ids=tuple(
                    item.accepted_point_id for item in context.accepted[start_accepted:]
                ),
                committed_event_ids=tuple(
                    item.committed_event_id for item in context.events[start_events:]
                ),
            )
            return _DragStepOutcome(next_state, target_response, False)

        simultaneous = located.result.simultaneous_group
        channel_ids = (
            simultaneous.channel_ids
            if simultaneous is not None
            else located.result.located_group.channel_ids  # type: ignore[union-attr]
        )
        release_channel = registrations[0].channel_id
        if release_channel not in channel_ids:
            reason = (
                "M03_BODY_COLLISION_INVALID"
                if registrations[2].channel_id in channel_ids
                else "M03_FINITE_CAP_SUPPORT_UNAVAILABLE"
            )
            raise _DriverFailure(
                reason,
                FailureAxis.PHYSICAL_INFEASIBLE,
                "drag encountered a fatal body/cap event before release",
            )
        pose = _translated_pose(state.base_pose, _scale3(direction, located.position))
        release_response = self._evaluate(
            context,
            state,
            pose,
            OperationPhase.DRAG,
            "CONTACT_RELEASE_EVENT_POINT",
        )
        post_evidence = self._event_post_evidence(
            context,
            state,
            OperationPhase.DRAG,
            event_coordinate=state.total_path_x_mm + located.position,
            direction_global=direction,
            event_position=located.position,
            purpose="CONTACT_RELEASE_EVENT_POST",
            channel_ids=(m03_event_spec(M03EventKind.CONTACT_RELEASE).channel_id,),
        )
        release_state = self._commit(
            context,
            state,
            pose,
            release_response,
            OperationPhase.DRAG,
            operation_coordinate=state.total_path_x_mm + located.position,
            coordinate_unit="mm",
            preload_eta=None,
            primary_override=PrimaryMechanicalState.RELEASE_TRANSITION,
            path_delta_mm=located.position,
            event_increment=1,
            contact_cycle_id=state.contact_cycle_id,
            preserve_deformation_if_released=True,
        )
        self._append_event(
            context,
            state=release_state,
            accepted_point_id=context.accepted[-1].accepted_point_id,
            response=release_response,
            event_kind=M03EventKind.CONTACT_RELEASE.value,
            phase=OperationPhase.DRAG,
            coordinate=release_state.total_path_x_mm,
            coordinate_unit="mm",
            raw_guard=_normal_load(release_response) - force_resolution,
            raw_guard_unit="N",
            sequence_number=release_state.event_sequence_number,
            post_evidence=post_evidence,
            search_result=located.result,
        )
        self._append_operation(
            context,
            phase=OperationPhase.DRAG,
            interpolation="linear_translation_global:+local-x",
            path_coordinate_id="x_total_mm",
            coordinate_unit="mm",
            start_coordinate=state.total_path_x_mm,
            end_coordinate=release_state.total_path_x_mm,
            start_state=state,
            end_state=release_state,
            response=release_response,
            guards=tuple(item.channel_id for item in registrations),
            termination_condition="earliest signed event",
            termination_reason=M03EventKind.CONTACT_RELEASE.value,
            operation_speed=request.drag_policy.speed_mm_per_s,
            accepted_point_ids=tuple(
                item.accepted_point_id for item in context.accepted[start_accepted:]
            ),
            committed_event_ids=tuple(
                item.committed_event_id for item in context.events[start_events:]
            ),
        )
        return _DragStepOutcome(release_state, release_response, True)

    def _release_return_research_reload(
        self,
        context: _ExecutionContext,
        resolved: ResolvedInitialPose,
        state: ImmutableSingleSpineState,
        response: SingleSpineTrialResponse,
        capability: ReturnPathCapability,
    ) -> tuple[ImmutableSingleSpineState, SingleSpineTrialResponse]:
        del capability
        # Release already pre-empted the decreasing load target.  The unload
        # segment therefore terminates at the committed physical release.
        self._append_operation(
            context,
            phase=OperationPhase.UNLOAD,
            interpolation="normal_target_homotopy_at_fixed_x",
            path_coordinate_id="unload_eta",
            coordinate_unit="1",
            start_coordinate=1.0,
            end_coordinate=0.0,
            start_state=state,
            end_state=state,
            response=response,
            guards=(m03_event_spec(M03EventKind.CONTACT_RELEASE).channel_id,),
            termination_condition="normal target reaches zero or contact releases first",
            termination_reason="CONTACT_RELEASE_PREEMPTED_UNLOAD_TARGET",
        )
        self._append_operation(
            context,
            phase=OperationPhase.DRIVE_OFF_UNLOCK,
            interpolation="constant_pose_controller_mode_switch",
            path_coordinate_id="controller_mode",
            coordinate_unit="1",
            start_coordinate=1.0,
            end_coordinate=0.0,
            start_state=state,
            end_state=state,
            response=response,
            guards=(m03_event_spec(M03EventKind.RELEASE_PATH_START).channel_id,),
            termination_condition="normal-force controller disabled with pose continuity",
            termination_reason="M03_UNLOCK_AT_RELEASE",
        )

        lift_start = state
        start_accepted = len(context.accepted)
        clearance_position = self._locate_release_threshold(
            context,
            state,
            OperationPhase.LIFT_OFF,
            response,
            channel_id="m03.standalone.lift_clearance",
            event_kind=M03EventKind.LIFT_OFF_CLEARANCE_REACHED.value,
            raw_unit="mm",
            value=lambda item: _full_clearance(item) - resolved.required_start_gap_mm,
            tolerance=_position_tolerance(context.request),
        )
        energy_position = self._locate_release_threshold(
            context,
            state,
            OperationPhase.LIFT_OFF,
            response,
            channel_id="m03.standalone.return_energy",
            event_kind=M03EventKind.RETURN_ENERGY_RESOLVED.value,
            raw_unit="N*mm",
            value=lambda item: (
                context.request.parameter_bundle.numerical.acceptance_work_resolution_n_mm
                - _remaining_energy(item)
            ),
            tolerance=context.request.parameter_bundle.numerical.work_absolute_tolerance_n_mm,
        )
        lift_distance = max(clearance_position, energy_position)
        lift_pose = _translated_pose(state.base_pose, (0.0, 0.0, lift_distance))
        lift_response = self._evaluate(
            context,
            state,
            lift_pose,
            OperationPhase.LIFT_OFF,
            "LIFT_OFF_ACCEPTED_END",
        )
        if (
            _full_clearance(lift_response) + _position_tolerance(context.request)
            < resolved.required_start_gap_mm
            or _remaining_energy(lift_response)
            > context.request.parameter_bundle.numerical.acceptance_work_resolution_n_mm
            + context.request.parameter_bundle.numerical.work_absolute_tolerance_n_mm
        ):
            raise _DriverFailure(
                "M03_RELEASE_RETURN_PATH_UNAVAILABLE",
                FailureAxis.CAPABILITY_UNAVAILABLE,
                "lift-off endpoint did not close clearance and recoverable-energy guards",
            )
        state = self._commit(
            context,
            state,
            lift_pose,
            lift_response,
            OperationPhase.LIFT_OFF,
            operation_coordinate=lift_distance,
            coordinate_unit="mm",
            preload_eta=None,
            primary_override=PrimaryMechanicalState.REVERSIBLE_RETURN,
            path_delta_mm=0.0,
            event_increment=0,
            contact_cycle_id=state.contact_cycle_id,
        )
        self._append_operation(
            context,
            phase=OperationPhase.LIFT_OFF,
            interpolation="linear_translation_global:+Z",
            path_coordinate_id="lift_off_z_mm",
            coordinate_unit="mm",
            start_coordinate=0.0,
            end_coordinate=lift_distance,
            start_state=lift_start,
            end_state=state,
            response=lift_response,
            guards=(
                m03_event_spec(M03EventKind.LIFT_OFF_CLEARANCE_REACHED).channel_id,
                m03_event_spec(M03EventKind.RETURN_ENERGY_RESOLVED).channel_id,
                m03_event_spec(M03EventKind.SWEPT_COLLISION).channel_id,
            ),
            termination_condition="full clearance >= g_start and remaining energy <= resolution",
            termination_reason="M03_LIFT_OFF_COMPLETE",
            accepted_point_ids=tuple(
                item.accepted_point_id for item in context.accepted[start_accepted:]
            ),
        )

        state, response = self._search_zero_load_contact(
            context,
            state,
            lift_response,
            phase=OperationPhase.RESEARCH,
            maximum_depth_mm=lift_distance + context.config.minimum_z_bracket_mm,
            recontact=True,
        )
        state, response = self._preload(
            context,
            state,
            response,
            phase=OperationPhase.RELOAD,
            reengagement=True,
        )
        return state, response

    def _locate_release_threshold(
        self,
        context: _ExecutionContext,
        state: ImmutableSingleSpineState,
        phase: OperationPhase,
        start_response: SingleSpineTrialResponse,
        *,
        channel_id: str,
        event_kind: str,
        raw_unit: str,
        value: Callable[[SingleSpineTrialResponse], float],
        tolerance: float,
    ) -> float:
        if value(start_response) >= -tolerance:
            return 0.0
        registration = _standalone_channel(
            channel_id,
            event_kind,
            raw_unit,
            EventAdmissibleSide.NONNEGATIVE,
            EventTriggerDirection.RISING,
        )
        located = self._locate_guard(
            context,
            state,
            phase,
            event_kind,
            direction_global=(0.0, 0.0, 1.0),
            maximum_distance=context.config.maximum_lift_z_travel_mm,
            registration=registration,
            raw_guard=lambda item, _position: value(item),
            raw_zero_tolerance=tolerance,
        )
        if located is None:
            raise _DriverFailure(
                "M03_RELEASE_RETURN_PATH_UNAVAILABLE",
                FailureAxis.CAPABILITY_UNAVAILABLE,
                f"release threshold {event_kind} was not located on the explicit +Z path",
            )
        return located.position

    def _locate_guard(
        self,
        context: _ExecutionContext,
        parent: ImmutableSingleSpineState,
        phase: OperationPhase,
        purpose: str,
        *,
        direction_global: Vector3,
        maximum_distance: float,
        registration: EventChannelRegistration,
        raw_guard: Callable[[SingleSpineTrialResponse, float], float],
        raw_zero_tolerance: float,
    ) -> _LocatedGuard | None:
        return self._locate_multiple_guards(
            context,
            parent,
            phase,
            purpose,
            direction_global=direction_global,
            maximum_distance=maximum_distance,
            registrations=(registration,),
            raw_guards={registration.channel_id: raw_guard},
            zero_tolerances={registration.channel_id: raw_zero_tolerance},
        )

    def _locate_multiple_guards(
        self,
        context: _ExecutionContext,
        parent: ImmutableSingleSpineState,
        phase: OperationPhase,
        purpose: str,
        *,
        direction_global: Vector3,
        maximum_distance: float,
        registrations: tuple[EventChannelRegistration, ...],
        raw_guards: dict[str, Callable[[SingleSpineTrialResponse, float], float]],
        zero_tolerances: dict[str, float],
    ) -> _LocatedGuard | None:
        if maximum_distance <= 0.0 or not math.isfinite(maximum_distance):
            raise ContractViolation("event search distance must be finite and positive")
        request = context.request
        search_payload = {
            "run_id": request.run_id,
            "case_id": request.case_id,
            "parent_state_id": parent.state_id,
            "phase": phase,
            "purpose": purpose,
            "maximum_distance": maximum_distance,
            "channels": tuple(item.channel_id for item in registrations),
        }
        spacing = maximum_distance / context.config.event_scan_subdivisions
        coverage = tuple(
            EventCoverageDeclaration(
                certificate_id=stable_content_id(
                    "m03_standalone_event_coverage",
                    {**search_payload, "channel_id": item.channel_id},
                ),
                channel_id=item.channel_id,
                kind=(
                    EventCertificateKind.SWEPT_NO_EVENT
                    if item.detection_mode is EventDetectionMode.SWEPT_COLLISION
                    else EventCertificateKind.ADAPTIVE_PROBE_SPACING
                ),
                certificate_hash=semantic_hash(
                    {**search_payload, "channel_id": item.channel_id, "spacing": spacing}
                ),
                complete=True,
                certifies_no_event=False,
                maximum_probe_spacing_mm=spacing,
                raw_guard_zero_tolerance=zero_tolerances[item.channel_id],
                requires_balance_recompute=False,
            )
            for item in registrations
        )
        search = EventSearchRequest(
            search_id=stable_content_id("m03_standalone_event_search", search_payload),
            target_id=stable_content_id("m03_standalone_operation_target", search_payload),
            trial_id=stable_content_id("m03_standalone_event_trial", search_payload),
            parent_accepted_state_id=parent.state_id,
            interval_start_mm=0.0,
            interval_end_mm=maximum_distance,
            characteristic_length_mm=request.parameter_bundle.needle.tip_radius_mm,
            channels=registrations,
            coverage=coverage,
        )
        responses: dict[float, SingleSpineTrialResponse] = {}

        def probe(
            oriented_path_position_mm: float,
            channel_ids: tuple[str, ...],
        ) -> EquilibriumGuardSnapshot:
            context.event_probe_count += 1
            position = oriented_path_position_mm
            pose = _translated_pose(parent.base_pose, _scale3(direction_global, position))
            response = self._evaluate(
                context,
                parent,
                pose,
                phase,
                purpose,
                permit_event_reduction=True,
            )
            values = {
                channel_id: raw_guards[channel_id](response, position) for channel_id in channel_ids
            }
            if any(not math.isfinite(item) for item in values.values()):
                raise _DriverFailure(
                    "M02_EVENT_COVERAGE_UNAVAILABLE",
                    FailureAxis.NUMERICAL_FAILURE,
                    "standalone owner returned a nonfinite raw event guard",
                )
            responses[position] = response
            return EquilibriumGuardSnapshot(
                oriented_path_position_mm=position,
                raw_guard_values=values,
                raw_guard_units={item.channel_id: item.raw_guard_unit for item in registrations},
                equilibrium_quality_passed=True,
                equilibrium_response_hash=response.response_hash,
                quality_hashes=(semantic_hash(response.diagnostics),),
                balance_response_hash=None,
                balance_recomputed=False,
                coverage_refs=tuple(item.certificate_id for item in coverage),
            )

        try:
            result = context.event_engine.search(search, probe)
        except _DriverFailure:
            raise
        except ContractViolation as exc:
            raise _DriverFailure(
                "M02_EVENT_CHANNEL_CONTRACT_INVALID",
                FailureAxis.CONTRACT_REJECTION,
                str(exc),
            ) from exc
        if not result.success:
            reason = (
                result.failure.reason_code.value
                if result.failure is not None
                else M02ReasonCode.EVENT_EARLIESTNESS_UNPROVEN.value
            )
            raise _DriverFailure(
                reason,
                FailureAxis.NUMERICAL_FAILURE,
                "M02 could not close standalone event coverage/earliestness",
            )
        if result.no_event:
            return None
        assert result.located_group is not None
        position = result.located_group.oriented_path_position_mm
        pose = _translated_pose(parent.base_pose, _scale3(direction_global, position))
        response = self._evaluate(context, parent, pose, phase, purpose)
        return _LocatedGuard(position, response, result)

    def _event_post_evidence(
        self,
        context: _ExecutionContext,
        parent: ImmutableSingleSpineState,
        phase: OperationPhase,
        *,
        event_coordinate: float,
        direction_global: Vector3,
        event_position: float,
        purpose: str,
        channel_ids: tuple[str, ...],
    ) -> M03EventPostReassemblyEvidence:
        offset = context.config.event_side_offset_mm

        def solve(side: str, position: float) -> SingleSpineTrialResponse:
            pose = _translated_pose(parent.base_pose, _scale3(direction_global, position))
            return self._evaluate(context, parent, pose, phase, f"{purpose}_{side}")

        try:
            return evaluate_m03_event_post_reassembly(
                event_coordinate_mm=event_coordinate,
                simultaneous_channel_ids=channel_ids,
                parent_accepted_state_id=parent.state_id,
                pre_solver=lambda _coordinate, _channels: solve(
                    "PRE_EVENT", event_position - offset
                ),
                transition=lambda channels: tuple(
                    stable_content_id(
                        "m03_standalone_transition_intent",
                        {
                            "parent_state_id": parent.state_id,
                            "event_coordinate": event_coordinate,
                            "purpose": purpose,
                            "channel_id": channel_id,
                        },
                    )
                    for channel_id in channels
                ),
                post_solver=lambda _coordinate, _channels, _intents: solve(
                    "POST_EVENT", event_position + offset
                ),
            )
        except ContractViolation as exc:
            raise _DriverFailure(
                "M03_EVENT_POST_REASSEMBLY_UNAVAILABLE",
                FailureAxis.CAPABILITY_UNAVAILABLE,
                str(exc),
            ) from exc

    def _evaluate(
        self,
        context: _ExecutionContext,
        parent: ImmutableSingleSpineState,
        target_pose: RigidPose,
        phase: OperationPhase,
        purpose: str,
        *,
        permit_rejected_response: bool = False,
        permit_event_reduction: bool = False,
    ) -> SingleSpineTrialResponse:
        request = context.request
        delta = tuple(
            float(target_pose.position_mm[index] - parent.base_pose.position_mm[index])
            for index in range(3)
        )
        increment = PrescribedBaseIncrement(
            delta,  # type: ignore[arg-type]
            (0.0, 0.0, 0.0),
            "linear_translation_global",
            ("ux", "uy", "uz", "rx", "ry", "rz"),
            "GLOBAL",
            parent.base_pose.reference_point_id,
        )
        identity_payload = {
            "run_id": request.run_id,
            "case_id": request.case_id,
            "parent_state_id": parent.state_id,
            "target_pose_id": target_pose.pose_id,
            "phase": phase,
            "purpose": purpose,
        }
        trial_identity = TrialIdentity(
            global_step_id=stable_content_id("m03_standalone_global_step", identity_payload),
            global_trial_id=stable_content_id("m03_standalone_global_trial", identity_payload),
            newton_iteration_id="M02_OWNER_FULL_REASSEMBLY",
            caller_sequence_id=stable_content_id(
                "m03_standalone_caller_sequence", identity_payload
            ),
        )
        embedded = make_embedded_request(
            needle_identity=make_needle_identity(
                request.parameter_bundle,
                needle_id=f"{request.run_id}:single-spine",
                unit_id=request.case_id,
            ),
            surface_query_handle=request.surface_query_handle,
            base_pose_n=parent.base_pose,
            prescribed_base_increment=increment,
            immutable_single_spine_state_n=parent,
            parameter_bundle=request.parameter_bundle,
            trial_identity=trial_identity,
            local_frame=request.local_frame,
            task_direction_global=request.task_direction_global,
        )
        # ``EmbeddedSingleSpineTrialRequest`` has no standalone load field;
        # guard against accidental schema expansion at this boundary.
        embedded_names = {item.name for item in fields(embedded)}
        if embedded_names.intersection(
            {"Pz", "pz", "per_spine_normal_force", "normal_force_target"}
        ):
            raise ContractViolation("standalone must not add Pz to the embedded request")
        trial_sequence = context.trial_call_count
        context.trial_call_count += 1
        kernel_evaluation: KernelEvaluation | None = None
        try:
            if isinstance(context.kernel, StandaloneArtifactTrialKernel):
                kernel_evaluation = context.kernel.evaluate_trial_with_artifacts(embedded)
                if not isinstance(kernel_evaluation, KernelEvaluation):
                    raise ContractViolation(
                        "artifact-capable standalone kernel returned an invalid evaluation"
                    )
                response = kernel_evaluation.response
            else:
                response = context.kernel.evaluate_trial(embedded)
        except ContractViolation as exc:
            context.trials.append(
                StandaloneTrialSnapshot(
                    trial_sequence,
                    phase,
                    parent.state_id,
                    target_pose.pose_id,
                    embedded,
                    None,
                    f"{type(exc).__name__}: {exc}",
                )
            )
            self._record_rejected(
                context,
                parent,
                phase,
                target_pose,
                embedded.request_id,
                None,
                "M03_KERNEL_CONTRACT_REJECTION",
                FailureAxis.CONTRACT_REJECTION,
            )
            raise _DriverFailure(
                "M03_KERNEL_CONTRACT_REJECTION",
                FailureAxis.CONTRACT_REJECTION,
                str(exc),
            ) from exc
        except Exception as exc:
            context.trials.append(
                StandaloneTrialSnapshot(
                    trial_sequence,
                    phase,
                    parent.state_id,
                    target_pose.pose_id,
                    embedded,
                    None,
                    f"{type(exc).__name__}: {exc}",
                )
            )
            self._record_rejected(
                context,
                parent,
                phase,
                target_pose,
                embedded.request_id,
                None,
                "M03_KERNEL_TRIAL_EXCEPTION",
                FailureAxis.NUMERICAL_FAILURE,
            )
            raise _DriverFailure(
                "M03_KERNEL_TRIAL_EXCEPTION",
                FailureAxis.NUMERICAL_FAILURE,
                str(exc),
            ) from exc
        context.trials.append(
            StandaloneTrialSnapshot(
                trial_sequence,
                phase,
                parent.state_id,
                target_pose.pose_id,
                embedded,
                response,
                None,
                kernel_evaluation,
            )
        )
        context.current_response = response
        if not _response_eligible(response):
            self._record_rejected(
                context,
                parent,
                phase,
                target_pose,
                embedded.request_id,
                response.response_hash,
                response.diagnostics.original_reason_codes[0]
                if response.diagnostics.original_reason_codes
                else response.diagnostics.error_class.value,
                response.diagnostics.failure_axis,
            )
            reduction_probe = (
                permit_event_reduction
                and response.diagnostics.error_class is EmbeddedErrorClass.EVENT_REDUCTION_REQUIRED
                and _response_probe_eligible(response)
            )
            if not permit_rejected_response and not reduction_probe:
                failure_axis = response.diagnostics.failure_axis
                if failure_axis is FailureAxis.NONE:
                    failure_axis = FailureAxis.NUMERICAL_FAILURE
                raise _DriverFailure(
                    response.diagnostics.original_reason_codes[0]
                    if response.diagnostics.original_reason_codes
                    else response.diagnostics.error_class.value,
                    failure_axis,
                    response.diagnostics.error_detail,
                )
        return response

    def _record_rejected(
        self,
        context: _ExecutionContext,
        parent: ImmutableSingleSpineState,
        phase: OperationPhase,
        pose: RigidPose,
        request_id: str | None,
        response_hash: str | None,
        reason: str,
        failure_axis: FailureAxis,
    ) -> None:
        payload = {
            "run_id": context.request.run_id,
            "case_id": context.request.case_id,
            "phase": phase,
            "parent_state_id": parent.state_id,
            "pose_id": pose.pose_id,
            "request_id": request_id,
            "response_hash": response_hash,
            "reason": reason,
            "occurrence": len(context.rejected),
        }
        context.rejected.append(
            StandaloneRejectedTrialRecord(
                stable_content_id("m03_standalone_rejected_trial", payload),
                context.request.run_id,
                context.request.case_id,
                phase,
                parent.state_id,
                parent.state_version,
                request_id,
                response_hash,
                reason,
                failure_axis,
                pose.pose_id,
                False,
                make_metadata(
                    "m03_standalone_rejected_trial",
                    payload,
                    source_identity=SourceIdentity.PROPOSED_SUPPLEMENT,
                ),
            )
        )

    def _commit(
        self,
        context: _ExecutionContext,
        parent: ImmutableSingleSpineState,
        pose: RigidPose,
        response: SingleSpineTrialResponse,
        phase: OperationPhase,
        *,
        operation_coordinate: float,
        coordinate_unit: str,
        preload_eta: float | None,
        primary_override: PrimaryMechanicalState,
        path_delta_mm: float,
        event_increment: int,
        contact_cycle_id: int,
        preserve_deformation_if_released: bool = False,
    ) -> ImmutableSingleSpineState:
        if not _response_eligible(response):
            raise ContractViolation("rejected trial cannot be committed by standalone")
        supports = tuple(
            AcceptedSupportState(
                item.support_id,
                item.candidate_id,
                item.point_global_mm,
                item.normal_global,
                item.tangent_basis_global,
                item.normal_multiplier_n,
                item.tangential_multiplier_n,
                item.accumulated_slip_if_committed_preview_mm,
                item.motion_state,
            )
            for item in response.geometry_contact.supports
        )
        beam_translation = response.structure.beam_tip_translation_global_mm
        beam_rotation = response.structure.beam_tip_rotation_global_rad
        spring_state = response.structure.spring_state
        spring_compression = response.structure.spring_compression_mm
        if preserve_deformation_if_released and not supports:
            beam_translation = parent.beam_tip_translation_global_mm
            beam_rotation = parent.beam_tip_rotation_global_rad
            spring_state = parent.spring_state
            spring_compression = parent.spring_compression_mm
        path = parent.total_path_x_mm + path_delta_mm
        clock = parent.drag_elapsed_time_s + (
            path_delta_mm / context.request.drag_policy.speed_mm_per_s
        )
        payload = {
            "parent_state_id": parent.state_id,
            "state_version": parent.state_version + 1,
            "pose_id": pose.pose_id,
            "primary_state": primary_override,
            "supports": supports,
            "beam_translation": beam_translation,
            "beam_rotation": beam_rotation,
            "spring_state": spring_state,
            "spring_compression": spring_compression,
            "total_path_x_mm": path,
            "drag_elapsed_time_s": clock,
            "contact_cycle_id": contact_cycle_id,
            "event_sequence_number": parent.event_sequence_number + event_increment,
            "response_hash": response.response_hash,
        }
        state = ImmutableSingleSpineState(
            stable_content_id("m03_single_spine_state", payload),
            parent.state_version + 1,
            pose,
            primary_override,
            supports,
            beam_translation,
            beam_rotation,
            spring_state,
            spring_compression,
            path,
            clock,
            contact_cycle_id,
            parent.event_sequence_number + event_increment,
            parent.cumulative_friction_dissipation_n_mm
            + max(response.work.friction_dissipation_n_mm, 0.0),
            parent.cumulative_input_work_n_mm + response.work.base_or_actuator_input_work_n_mm,
            response.response_hash,
            make_metadata(
                "m03_committed_single_spine_state",
                payload,
                source_identity=SourceIdentity.PROPOSED_SUPPLEMENT,
            ),
        )
        point = self._accepted_record(
            context,
            state,
            response,
            phase,
            operation_coordinate=operation_coordinate,
            coordinate_unit=coordinate_unit,
            preload_eta=preload_eta,
        )
        context.accepted.append(point)
        context.current_response = response
        context.committed_response = response
        return state

    def _accepted_record(
        self,
        context: _ExecutionContext,
        state: ImmutableSingleSpineState,
        response: SingleSpineTrialResponse,
        phase: OperationPhase,
        *,
        operation_coordinate: float,
        coordinate_unit: str,
        preload_eta: float | None,
    ) -> StandaloneAcceptedPointRecord:
        payload = {
            "run_id": context.request.run_id,
            "case_id": context.request.case_id,
            "sequence": len(context.accepted),
            "state_id": state.state_id,
            "response_hash": response.response_hash,
            "phase": phase,
        }
        return StandaloneAcceptedPointRecord(
            stable_content_id("m03_standalone_accepted_point", payload),
            context.request.run_id,
            context.request.case_id,
            len(context.accepted),
            phase,
            state,
            response.response_id,
            response.response_hash,
            state.base_pose.pose_id,
            operation_coordinate,
            coordinate_unit,
            preload_eta,
            _normal_load(response),
            state.total_path_x_mm,
            state.drag_elapsed_time_s,
            response.geometry_contact.query_receipt_ids,
            response.transaction.opaque_trial_state_handle,
            response.transaction.provisional_commit_intent,
            make_metadata(
                "m03_standalone_accepted_point",
                payload,
                source_identity=SourceIdentity.PROPOSED_SUPPLEMENT,
            ),
        )

    def _append_event(
        self,
        context: _ExecutionContext,
        *,
        state: ImmutableSingleSpineState,
        accepted_point_id: str,
        response: SingleSpineTrialResponse,
        event_kind: str,
        phase: OperationPhase,
        coordinate: float,
        coordinate_unit: str,
        raw_guard: float,
        raw_guard_unit: str,
        sequence_number: int,
        post_evidence: M03EventPostReassemblyEvidence,
        search_result: EventSearchResult | None = None,
        dependency_layer: int = 0,
    ) -> None:
        response_hashes = {
            response.response_hash,
            post_evidence.pre_response_hash,
            post_evidence.post_response_hash,
        }
        if len(response_hashes) != 3:
            raise ContractViolation(
                "committed standalone event requires distinct pre/event/post responses"
            )
        if (
            post_evidence.result.pre_side.event_coordinate_mm
            != post_evidence.result.post_side.event_coordinate_mm
        ):
            raise ContractViolation("standalone event/post coordinate evidence is inconsistent")
        payload = {
            "run_id": context.request.run_id,
            "case_id": context.request.case_id,
            "event_kind": event_kind,
            "sequence_number": sequence_number,
            "state_id": state.state_id,
            "coordinate": coordinate,
            "response_hash": response.response_hash,
        }
        simultaneous = search_result.simultaneous_group if search_result is not None else None
        certificate = search_result.earliestness_certificate if search_result is not None else None
        bracket = search_result.brackets[0] if search_result is not None else None
        probe_refs = (
            tuple(item.probe_id for item in search_result.probes)
            if search_result is not None
            else (response.response_id,)
        )
        context.events.append(
            StandaloneCommittedEventRecord(
                stable_content_id("m03_standalone_committed_event", payload),
                context.request.run_id,
                context.request.case_id,
                sequence_number,
                event_kind,
                phase,
                coordinate,
                coordinate_unit,
                raw_guard,
                raw_guard_unit,
                state.state_id,
                accepted_point_id,
                response.response_hash,
                post_evidence.pre_response_hash,
                post_evidence.post_response_hash,
                simultaneous.simultaneous_group_id if simultaneous is not None else None,
                certificate.certificate_id if certificate is not None else None,
                (
                    (bracket.left_position_mm, bracket.right_position_mm)
                    if bracket is not None
                    else (coordinate, coordinate)
                ),
                bracket.localization_error_mm if bracket is not None else 0.0,
                probe_refs,
                dependency_layer,
                make_metadata(
                    "m03_standalone_committed_event",
                    payload,
                    source_identity=SourceIdentity.PROPOSED_SUPPLEMENT,
                ),
            )
        )

    def _append_operation(
        self,
        context: _ExecutionContext,
        *,
        phase: OperationPhase,
        interpolation: str,
        path_coordinate_id: str,
        coordinate_unit: str,
        start_coordinate: float,
        end_coordinate: float,
        start_state: ImmutableSingleSpineState,
        end_state: ImmutableSingleSpineState,
        response: SingleSpineTrialResponse,
        guards: tuple[str, ...],
        termination_condition: str,
        termination_reason: str,
        operation_speed: float | None = None,
        accepted_point_ids: tuple[str, ...] | None = None,
        committed_event_ids: tuple[str, ...] | None = None,
    ) -> None:
        elapsed = (
            abs(end_coordinate - start_coordinate) / operation_speed
            if operation_speed is not None
            else None
        )
        accepted_ids = (
            accepted_point_ids
            if accepted_point_ids is not None
            else (context.accepted[-1].accepted_point_id,)
            if context.accepted
            else ()
        )
        event_ids = committed_event_ids if committed_event_ids is not None else ()
        payload = {
            "run_id": context.request.run_id,
            "case_id": context.request.case_id,
            "segment_sequence": len(context.operations),
            "phase": phase,
            "start_state_id": start_state.state_id,
            "end_state_id": end_state.state_id,
            "start_coordinate": start_coordinate,
            "end_coordinate": end_coordinate,
            "termination_reason": termination_reason,
        }
        context.operations.append(
            OperationSegmentRecord(
                stable_content_id("m03_operation_segment", payload),
                context.request.run_id,
                context.request.case_id,
                len(context.operations),
                phase,
                interpolation,
                path_coordinate_id,
                coordinate_unit,
                start_coordinate,
                end_coordinate,
                start_state.base_pose.pose_id,
                end_state.base_pose.pose_id,
                response.geometry_contact.footprint_id or "M03_SWEEP_REF_UNAVAILABLE",
                guards,
                "M03_HARD_RESIDUAL_GRAPH_GEOMETRY_QUALITY_GATE_1",
                termination_condition,
                termination_reason,
                operation_speed,
                operation_speed is not None,
                elapsed,
                start_state.drag_elapsed_time_s,
                end_state.drag_elapsed_time_s,
                accepted_ids,
                event_ids,
                response.geometry_contact.query_receipt_ids,
                make_metadata(
                    "m03_operation_segment",
                    payload,
                    source_identity=SourceIdentity.PROPOSED_SUPPLEMENT,
                ),
            )
        )

    def _execution(
        self,
        context: _ExecutionContext,
        resolved: ResolvedInitialPose | UnavailableInitialPose,
        state: ImmutableSingleSpineState,
        terminal: StandaloneTerminalStatus,
        reason: str,
        failure_axis: FailureAxis,
        unavailable_reason: str | None,
        remaining_energy: float,
    ) -> StandaloneExecution:
        request = context.request
        completed = terminal is StandaloneTerminalStatus.TRAVEL_COMPLETE
        if completed:
            unavailable_reason = None
        payload = {
            "run_id": request.run_id,
            "case_id": request.case_id,
            "request_hash": request.request_hash,
            "config_hash": context.config.config_hash,
            "terminal": terminal,
            "reason": reason,
            "final_state_id": state.state_id,
            "accepted_ids": tuple(item.accepted_point_id for item in context.accepted),
            "event_ids": tuple(item.committed_event_id for item in context.events),
            "rejected_ids": tuple(item.rejected_trial_id for item in context.rejected),
        }
        response = StandaloneSingleSpineRunResponse(
            M03_SCHEMA_VERSION,
            request.run_id,
            request.case_id,
            request.request_hash,
            context.config.config_hash,
            request.surface_query_handle.realization.surface_realization_id,
            request.parameter_bundle.parameter_bundle_id,
            terminal,
            reason,
            completed,
            state,
            payload["accepted_ids"],  # type: ignore[arg-type]
            payload["event_ids"],  # type: ignore[arg-type]
            payload["rejected_ids"],  # type: ignore[arg-type]
            (
                "m03.accepted_state_history",
                "m03.committed_event_payloads",
                "m03.release_operation_history",
                "m03.rejected_diagnostics",
                "m03.work_ledger",
            ),
            (),
            None,
            state.base_pose,
            max(0.0, request.drag_policy.travel_mm - state.total_path_x_mm),
            max(0.0, remaining_energy),
            unavailable_reason,
            MaturityStatus.NOT_ASSESSED,
            True,
            MaterialSubstate.NO_DAMAGE_MODEL,
            NeedleStrengthSubstate.NEEDLE_STRENGTH_UNAVAILABLE,
            failure_axis,
            make_metadata(
                "m03_standalone_response",
                payload,
                source_identity=SourceIdentity.PROPOSED_SUPPLEMENT,
            ),
        )
        execution_payload = {
            "response": payload,
            "initial_pose_evidence_id": (
                resolved.resolved_pose_id
                if isinstance(resolved, ResolvedInitialPose)
                else resolved.evidence_id
            ),
            "initial_pose_evidence_status": (
                "RESOLVED" if isinstance(resolved, ResolvedInitialPose) else "UNAVAILABLE"
            ),
            "operation_ids": tuple(item.operation_segment_id for item in context.operations),
            "trial_request_hashes": tuple(item.request.request_hash for item in context.trials),
            "trial_response_hashes": tuple(
                item.response.response_hash if item.response is not None else None
                for item in context.trials
            ),
            "trial_call_count": context.trial_call_count,
            "event_probe_count": context.event_probe_count,
        }
        return StandaloneExecution(
            response,
            resolved,
            context.config,
            tuple(context.accepted),
            tuple(context.events),
            tuple(context.rejected),
            tuple(context.operations),
            tuple(context.trials),
            context.trial_call_count,
            context.event_probe_count,
            make_metadata(
                "m03_standalone_execution",
                execution_payload,
                source_identity=SourceIdentity.PROPOSED_SUPPLEMENT,
            ),
        )


def _standalone_channel(
    channel_id: str,
    event_kind: str,
    raw_unit: str,
    admissible_side: EventAdmissibleSide,
    direction: EventTriggerDirection,
    *,
    detection: EventDetectionMode = EventDetectionMode.SIGN_CHANGE,
    certificates: tuple[EventCertificateKind, ...] = (EventCertificateKind.ADAPTIVE_PROBE_SPACING,),
) -> EventChannelRegistration:
    return EventChannelRegistration.create(
        channel_id=channel_id,
        owner_id="M03_STANDALONE_SINGLE_SPINE",
        entity_ids=("M03_SINGLE_SPINE",),
        event_kind=event_kind,
        guard_id=f"{channel_id}.raw",
        guard_version=STANDALONE_DRIVER_VERSION,
        raw_guard_unit=raw_unit,
        zero_level=0.0,
        admissible_side=admissible_side,
        trigger_direction=direction,
        applicability_predicate_id=f"{channel_id}.applicability",
        branch_state_scope=("STANDALONE_OPERATION",),
        detection_mode=detection,
        no_event_certificate_capabilities=certificates,
        dependency_predecessors=(),
        transition_owner="M03_STANDALONE_SINGLE_SPINE",
        post_event_side_request_id=f"{channel_id}.post",
        metadata_unit=raw_unit,
    )


def _response_eligible(response: SingleSpineTrialResponse) -> bool:
    if response.diagnostics.failure_axis is not FailureAxis.NONE:
        return False
    if response.diagnostics.error_class not in {
        EmbeddedErrorClass.OK,
        EmbeddedErrorClass.OPEN_RESPONSE,
        EmbeddedErrorClass.EQUILIBRIUM_DEGENERATE,
    }:
        return False
    return (
        bool(response.diagnostics.residual_blocks)
        and response.state_events.quality_solve_state != "QUALITY_REJECTED"
        and all(item.passed for item in response.diagnostics.residual_blocks if item.hard)
    )


def _response_probe_eligible(response: SingleSpineTrialResponse) -> bool:
    """Allow reduction requests only as noncommitting event-search samples."""

    return (
        response.diagnostics.failure_axis is FailureAxis.NONE
        and bool(response.diagnostics.residual_blocks)
        and response.state_events.quality_solve_state != "QUALITY_REJECTED"
        and all(item.passed for item in response.diagnostics.residual_blocks if item.hard)
    )


def _normal_load(response: SingleSpineTrialResponse) -> float:
    return max(
        0.0,
        sum(item.normal_multiplier_n for item in response.geometry_contact.supports),
    )


def _candidate_raw(response: SingleSpineTrialResponse, names: tuple[str, ...]) -> float | None:
    for item in response.state_events.all_event_candidates:
        if item.event_kind in names:
            return item.raw_guard
    return None


def _contact_gap(response: SingleSpineTrialResponse) -> float:
    value = _candidate_raw(
        response,
        (M03EventKind.TIP_CONTACT_ESTABLISH.value, "contact"),
    )
    if value is not None:
        return value
    if response.geometry_contact.supports:
        return min(item.legal_cap_gap_mm for item in response.geometry_contact.supports)
    if response.state_events.primary_mechanical_state is PrimaryMechanicalState.TIP_ZERO_LOAD:
        return 0.0
    raise _DriverFailure(
        "M02_EVENT_COVERAGE_UNAVAILABLE",
        FailureAxis.CAPABILITY_UNAVAILABLE,
        "intrinsic response omitted the raw finite-cap contact guard",
    )


def _cap_margin(response: SingleSpineTrialResponse) -> float:
    value = _candidate_raw(
        response,
        (M03EventKind.CAP_LEGALITY_LOSS.value, "finite_cap"),
    )
    if value is not None:
        return value
    return min(
        (item.cap_legality_margin_mm for item in response.geometry_contact.supports),
        default=1.0,
    )


def _body_clearance(response: SingleSpineTrialResponse) -> float:
    value = response.geometry_contact.minimum_full_body_clearance_mm
    if value is not None:
        return value
    legacy = _candidate_raw(response, (M03EventKind.SWEPT_COLLISION.value, "body_collision"))
    if legacy is not None:
        return legacy
    raise _DriverFailure(
        "M02_EVENT_COVERAGE_UNAVAILABLE",
        FailureAxis.CAPABILITY_UNAVAILABLE,
        "intrinsic response omitted the full-body clearance guard",
    )


def _full_clearance(response: SingleSpineTrialResponse) -> float:
    return min(_contact_gap(response), _body_clearance(response))


def _remaining_energy(response: SingleSpineTrialResponse) -> float:
    return max(
        0.0,
        response.work.remaining_stored_energy_n_mm,
        response.structure.beam_energy_n_mm + response.structure.spring_energy_n_mm,
    )


def _controlling_clearance_feature(response: SingleSpineTrialResponse) -> str:
    values = {
        "TIP_CAP": _contact_gap(response),
        "CONE": response.geometry_contact.cone_gap_mm,
        "SHAFT": response.geometry_contact.shaft_gap_mm,
        "MOUNT": response.geometry_contact.mount_gap_mm,
    }
    finite = {key: value for key, value in values.items() if value is not None}
    return min(finite, key=lambda key: float(finite[key])) if finite else "FULL_BODY"


def _position_tolerance(request: StandaloneSingleSpineRunRequest) -> float:
    return (
        request.parameter_bundle.needle.tip_radius_mm
        * request.parameter_bundle.numerical.event_position_tolerance_over_rt
    )


def _translated_pose(pose: RigidPose, translation: Vector3) -> RigidPose:
    return make_rigid_pose(
        tuple(float(pose.position_mm[index] + translation[index]) for index in range(3)),  # type: ignore[arg-type]
        rotation_global_from_local=pose.rotation_global_from_local,
        expressed_frame_id=pose.expressed_frame_id,
        reference_point_id=pose.reference_point_id,
    )


def _scale3(value: Vector3, scale: float) -> Vector3:
    return tuple(float(item * scale) for item in value)  # type: ignore[return-value]


def _tuple3(value: np.ndarray[tuple[int, ...], np.dtype[np.float64]]) -> Vector3:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (3,) or not np.isfinite(array).all():
        raise ContractViolation("standalone expected a finite three-vector")
    return tuple(float(item) for item in array)  # type: ignore[return-value]


def run_standalone_single_spine(
    request: StandaloneSingleSpineRunRequest,
    *,
    kernel: StandaloneTrialKernel | None = None,
    event_engine: EventEngine | None = None,
    config: StandaloneDriverConfig | None = None,
    return_path_provider: ReturnPathProvider | None = None,
) -> StandaloneExecution:
    """Functional entry point returning the response and all canonical records."""

    return StandaloneSingleSpineDriver(
        kernel=kernel,
        event_engine=event_engine,
        config=config,
        return_path_provider=return_path_provider,
    ).execute(request)


__all__ = [
    "RELEASE_PROTOCOL_VERSION",
    "STANDALONE_DRIVER_VERSION",
    "OperationSegmentRecord",
    "ResolvedInitialPose",
    "StandaloneAcceptedPointRecord",
    "StandaloneArtifactTrialKernel",
    "StandaloneCommittedEventRecord",
    "StandaloneDriverConfig",
    "StandaloneExecution",
    "StandaloneRejectedTrialRecord",
    "StandaloneSingleSpineDriver",
    "StandaloneTrialKernel",
    "StandaloneTrialSnapshot",
    "UnavailableInitialPose",
    "run_standalone_single_spine",
]
