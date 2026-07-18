"""Frozen M02 result extension and diagnostic-persistence contract.

The records in this module are additive evidence owned by M02.  They reference
M00 point, event, rejected-trial, and receipt identities; they never replace
those canonical identities.  Diagnostic retention is deliberately expressed
as a pure policy so selecting ``COMPACT``, ``STANDARD``, or ``FULL`` cannot
feed back into a solve.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from spine_sim.foundation.canonical import stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    CertificationStatus,
    Maturity,
    MaturityEvidence,
    MaturityStatus,
    RecordBase,
    SourceIdentity,
    StatusTuple,
)
from spine_sim.foundation.registry import (
    CompatibilityClass,
    DataClassification,
    DatasetClass,
    DatasetDescriptor,
    FieldMetadata,
    RelationDescriptor,
    ResultExtensionDescriptor,
)

from .contracts import DiagnosticLevel as DiagnosticLevel

M02_EXTENSION_SCHEMA_VERSION = "1.0.0"

CONTINUATION_TARGETS_DATASET = "m02.continuation_targets"
CONTINUATION_ATTEMPTS_DATASET = "m02.continuation_attempts"
ACCEPTED_STEP_NUMERICS_DATASET = "m02.accepted_step_numerics"
RESIDUAL_BLOCK_SUMMARIES_DATASET = "m02.residual_block_summaries"
ITERATION_TRACES_DATASET = "m02.iteration_traces"
REJECTED_ITERATION_TRACES_DATASET = "m02.rejected_iteration_traces"
EVENT_CHANNEL_REGISTRATIONS_DATASET = "m02.event_channel_registrations"
EVENT_PROBES_DATASET = "m02.event_probes"
EVENT_BRACKETS_DATASET = "m02.event_brackets"
REJECTED_EVENT_BRACKETS_DATASET = "m02.rejected_event_brackets"
EVENT_EARLIESTNESS_CERTIFICATES_DATASET = "m02.event_earliestness_certificates"
SIMULTANEOUS_EVENT_GROUPS_DATASET = "m02.simultaneous_event_groups"
EVENT_DEPENDENCIES_DATASET = "m02.event_dependencies"
CASCADE_ROUNDS_DATASET = "m02.cascade_rounds"
REJECTED_TRIAL_DIAGNOSTICS_DATASET = "m02.rejected_trial_diagnostics"
TRANSACTION_TRACE_DATASET = "m02.transaction_trace"
REPLAY_STEPS_DATASET = "m02.replay_steps"
FAILURE_DIAGNOSTICS_DATASET = "m02.failure_diagnostics"
REFINEMENT_STUDIES_DATASET = "m02.refinement_studies"
M01_COMPATIBILITY_RESULTS_DATASET = "m02.m01_compatibility_results"

M02_REGISTERED_DATASET_IDS = (
    CONTINUATION_TARGETS_DATASET,
    CONTINUATION_ATTEMPTS_DATASET,
    ACCEPTED_STEP_NUMERICS_DATASET,
    RESIDUAL_BLOCK_SUMMARIES_DATASET,
    ITERATION_TRACES_DATASET,
    REJECTED_ITERATION_TRACES_DATASET,
    EVENT_CHANNEL_REGISTRATIONS_DATASET,
    EVENT_PROBES_DATASET,
    EVENT_BRACKETS_DATASET,
    REJECTED_EVENT_BRACKETS_DATASET,
    EVENT_EARLIESTNESS_CERTIFICATES_DATASET,
    SIMULTANEOUS_EVENT_GROUPS_DATASET,
    EVENT_DEPENDENCIES_DATASET,
    CASCADE_ROUNDS_DATASET,
    REJECTED_TRIAL_DIAGNOSTICS_DATASET,
    TRANSACTION_TRACE_DATASET,
    REPLAY_STEPS_DATASET,
    FAILURE_DIAGNOSTICS_DATASET,
    REFINEMENT_STUDIES_DATASET,
    M01_COMPATIBILITY_RESULTS_DATASET,
)
M02_DATASET_IDS = M02_REGISTERED_DATASET_IDS

CORE_ACCEPTED_POINTS_DATASET = "core.accepted_points.common"
CORE_COMMITTED_EVENTS_DATASET = "core.committed_events.events"
CORE_REJECTED_TRIALS_DATASET = "core.rejected_trials.diagnostics"
CORE_COMMIT_RECEIPTS_DATASET = "core.transactions.receipts"


@dataclass(frozen=True, slots=True)
class M02ResultRecord(RecordBase):
    """Metadata carried by every persisted M02 row."""

    run_id: str
    case_id: str
    schema_version: str
    status: StatusTuple
    source_identity: SourceIdentity
    maturity: Maturity
    certification_status: CertificationStatus

    def __post_init__(self) -> None:
        if self.schema_version != M02_EXTENSION_SCHEMA_VERSION:
            raise ContractViolation(
                "M02 result record uses an unsupported schema version",
                details={
                    "expected": M02_EXTENSION_SCHEMA_VERSION,
                    "actual": self.schema_version,
                },
            )
        if self.status.certification_status is not self.certification_status:
            raise ContractViolation("M02 row status and certification metadata disagree")
        if self.certification_status is CertificationStatus.CERTIFIED_FOR_DECLARED_SCOPE:
            raise ContractViolation("M02 1.0.0 software evidence is not experimentally certifiable")


@dataclass(frozen=True, slots=True)
class ContinuationTargetRecord(M02ResultRecord):
    __dataset_id__ = CONTINUATION_TARGETS_DATASET

    target_id: str
    parent_accepted_state_id: str
    parent_commit_receipt_id: str
    coordinate_id: str
    coordinate_unit: str
    start_coordinate: float
    target_coordinate: float
    direction: str
    characteristic_length_mm: float
    resolved_config_hash: str
    request_hash: str


@dataclass(frozen=True, slots=True)
class ContinuationAttemptRecord(M02ResultRecord):
    __dataset_id__ = CONTINUATION_ATTEMPTS_DATASET

    attempt_id: str
    target_id: str
    trial_id: str
    parent_accepted_state_id: str
    attempt_index: int
    retry_index: int
    trial_phase: str
    attempted_coordinate: float
    coordinate_unit: str
    requested_step: float
    growth_shrink_reason: str
    event_marker_id: str | None
    newton_iterations: int
    backtrack_count: int
    outcome: str
    accepted_state_advanced: bool
    commit_receipt_id: str | None

    def __post_init__(self) -> None:
        M02ResultRecord.__post_init__(self)
        if self.accepted_state_advanced or self.commit_receipt_id is not None:
            raise ContractViolation(
                "continuation attempts are diagnostic trials and cannot publish accepted state"
            )


@dataclass(frozen=True, slots=True)
class AcceptedStepNumericsRecord(M02ResultRecord):
    __dataset_id__ = ACCEPTED_STEP_NUMERICS_DATASET

    numerics_record_id: str
    point_id: str
    accepted_state_id: str
    # None is legal only while the row is staged inside an M00 transaction.
    # ResultTransaction.commit atomically patches the authoritative receipt ID
    # before the immutable accepted shard is published.
    commit_receipt_id: str | None
    target_id: str
    trial_request_hash: str
    accepted_point_index: int
    attempted_coordinate: float
    accepted_coordinate: float
    coordinate_unit: str
    requested_step: float
    accepted_step: float
    step_reason: str
    retry_count: int
    newton_iterations: int
    backtrack_count: int
    difficulty: str
    final_merit: float
    event_id: str | None
    replay_step_id: str
    resolved_config_hash: str


@dataclass(frozen=True, slots=True)
class ResidualBlockSummaryRecord(M02ResultRecord):
    __dataset_id__ = RESIDUAL_BLOCK_SUMMARIES_DATASET

    residual_summary_id: str
    point_id: str
    # Staging-only null; M00 atomically supplies the receipt before publication.
    commit_receipt_id: str | None
    trial_request_hash: str
    iteration: int
    block_id: str
    owner_module_id: str
    block_semantics: str
    raw_norm: float
    raw_unit: str
    reference_norm: float
    absolute_tolerance: float
    relative_tolerance: float
    scale_id: str
    tolerance: float
    normalized_norm: float
    merit: float
    hard: bool
    passed: bool


@dataclass(frozen=True, slots=True)
class _IterationTraceRecordBase(M02ResultRecord):
    trace_id: str
    trial_id: str | None
    point_id: str | None
    commit_receipt_id: str | None
    trial_request_hash: str
    iteration: int
    block_id: str
    raw_norm: float
    raw_unit: str
    tolerance: float
    normalized_norm: float
    merit: float
    linear_residual: float
    line_search_factor: float
    algorithm_id: str
    backtrack_count: int
    owner_response_hash: str
    outcome: str
    accepted_state_advanced: bool

    def __post_init__(self) -> None:
        M02ResultRecord.__post_init__(self)


@dataclass(frozen=True, slots=True)
class IterationTraceRecord(_IterationTraceRecordBase):
    """Receipt-backed iteration evidence from a solve that was accepted."""

    __dataset_id__ = ITERATION_TRACES_DATASET

    def __post_init__(self) -> None:
        _IterationTraceRecordBase.__post_init__(self)
        if not self.accepted_state_advanced:
            raise ContractViolation(
                "iteration trace rows are reserved for receipt-backed accepted solves"
            )
        if self.point_id is None:
            raise ContractViolation("accepted iteration evidence requires a core point reference")


@dataclass(frozen=True, slots=True)
class RejectedIterationTraceRecord(_IterationTraceRecordBase):
    """FULL nonlinear/line-search detail isolated under an M00 rejected marker."""

    __dataset_id__ = REJECTED_ITERATION_TRACES_DATASET

    def __post_init__(self) -> None:
        _IterationTraceRecordBase.__post_init__(self)
        if self.trial_id is None:
            raise ContractViolation("rejected iteration evidence requires a rejected trial")
        if self.point_id is not None:
            raise ContractViolation(
                "rejected iteration evidence cannot reference an accepted point"
            )
        if self.accepted_state_advanced or self.commit_receipt_id is not None:
            raise ContractViolation("rejected iteration evidence cannot publish accepted state")


@dataclass(frozen=True, slots=True)
class EventChannelRegistrationRecord(M02ResultRecord):
    __dataset_id__ = EVENT_CHANNEL_REGISTRATIONS_DATASET

    registration_id: str
    channel_id: str
    owner_module_id: str
    entity_id: str
    event_kind: str
    raw_guard_unit: str
    zero_value: float
    admissible_side: str
    direction: str
    applicability_contract: str
    detection_capability: str
    certificate_capability: str
    dependency_channel_ids: tuple[str, ...]
    post_side_callback_id: str
    registration_hash: str


@dataclass(frozen=True, slots=True)
class EventProbeRecord(M02ResultRecord):
    __dataset_id__ = EVENT_PROBES_DATASET

    probe_id: str
    trial_id: str | None
    channel_id: str
    path_coordinate: float
    coordinate_unit: str
    raw_guard: float
    raw_guard_unit: str
    equilibrium_quality: float
    equilibrium_passed: bool
    owner_response_hash: str
    coverage_certificate_id: str | None
    valid_bracket: bool
    release_pose_ref: str | None
    path_mode: str | None
    pre_accepted_state_id: str
    post_accepted_state_id: str | None
    event_id: str | None
    commit_receipt_id: str | None
    accepted_state_advanced: bool

    def __post_init__(self) -> None:
        M02ResultRecord.__post_init__(self)
        if self.accepted_state_advanced:
            raise ContractViolation("event probes cannot advance accepted state")


@dataclass(frozen=True, slots=True)
class _EventBracketRecordBase(M02ResultRecord):
    bracket_id: str
    trial_id: str | None
    channel_id: str
    left_coordinate: float
    right_coordinate: float
    coordinate_unit: str
    left_raw_guard: float
    right_raw_guard: float
    raw_guard_unit: str
    root_coordinate: float | None
    root_method: str
    root_solver_level: int
    root_iterations: int
    position_tolerance: float
    localization_error: float | None
    direction: str
    simultaneous_tolerance: float
    coverage_certificate_id: str
    event_id: str | None
    commit_receipt_id: str | None
    final_bracket: bool
    accepted_state_advanced: bool

    def __post_init__(self) -> None:
        M02ResultRecord.__post_init__(self)


@dataclass(frozen=True, slots=True)
class EventBracketRecord(_EventBracketRecordBase):
    """Receipt-backed bracket evidence for a committed event."""

    __dataset_id__ = EVENT_BRACKETS_DATASET

    def __post_init__(self) -> None:
        _EventBracketRecordBase.__post_init__(self)
        if self.accepted_state_advanced:
            raise ContractViolation("event bracket diagnostics cannot advance accepted state")
        if self.event_id is None:
            raise ContractViolation(
                "persisted event brackets are reserved for receipt-backed committed events"
            )


@dataclass(frozen=True, slots=True)
class RejectedEventBracketRecord(_EventBracketRecordBase):
    """STANDARD/FULL bracket evidence isolated under an M00 rejected marker."""

    __dataset_id__ = REJECTED_EVENT_BRACKETS_DATASET

    def __post_init__(self) -> None:
        _EventBracketRecordBase.__post_init__(self)
        if self.trial_id is None:
            raise ContractViolation("rejected event bracket requires a rejected trial")
        if self.accepted_state_advanced or self.commit_receipt_id is not None:
            raise ContractViolation("rejected event bracket cannot publish accepted state")


@dataclass(frozen=True, slots=True)
class EventEarliestnessCertificateRecord(M02ResultRecord):
    __dataset_id__ = EVENT_EARLIESTNESS_CERTIFICATES_DATASET

    earliestness_certificate_id: str
    trial_id: str | None
    candidate_bracket_id: str
    covered_start_coordinate: float
    covered_end_coordinate: float
    coordinate_unit: str
    applicable_channel_ids: tuple[str, ...]
    coverage_certificate_ids: tuple[str, ...]
    candidate_root_coordinate: float
    simultaneous_tolerance: float
    earliest: bool
    proof_hash: str
    event_id: str | None
    commit_receipt_id: str | None


@dataclass(frozen=True, slots=True)
class SimultaneousEventGroupRecord(M02ResultRecord):
    __dataset_id__ = SIMULTANEOUS_EVENT_GROUPS_DATASET

    simultaneous_group_id: str
    event_id: str
    point_id: str
    # As for accepted-step evidence, the M00 transaction owns this identity and
    # fills it atomically at commit; callers may not predeclare a receipt.
    commit_receipt_id: str | None
    event_kind: str
    channel_id: str
    path_coordinate: float
    coordinate_unit: str
    simultaneous_tolerance: float
    dependency_layer: int
    group_hash: str


@dataclass(frozen=True, slots=True)
class EventDependencyRecord(M02ResultRecord):
    __dataset_id__ = EVENT_DEPENDENCIES_DATASET

    dependency_record_id: str
    event_id: str
    depends_on_event_id: str
    simultaneous_group_id: str
    dependency_kind: str
    topological_layer: int
    # Staging-only null; M00 atomically supplies the receipt before publication.
    commit_receipt_id: str | None


@dataclass(frozen=True, slots=True)
class CascadeRoundRecord(M02ResultRecord):
    __dataset_id__ = CASCADE_ROUNDS_DATASET

    cascade_record_id: str
    cascade_id: str
    event_id: str
    point_id: str
    # Staging-only null; M00 atomically supplies the receipt before publication.
    commit_receipt_id: str | None
    round_index: int
    state_hash: str
    event_signature_hash: str
    residual_margin: float
    zero_progress_intent_count: int
    zeno_candidate: bool


@dataclass(frozen=True, slots=True)
class RejectedTrialDiagnosticRecord(M02ResultRecord):
    __dataset_id__ = REJECTED_TRIAL_DIAGNOSTICS_DATASET

    diagnostic_id: str
    trial_id: str
    parent_accepted_state_id: str
    request_hash: str
    candidate_hash: str
    failure_family: str
    reason_code: str
    failure_stage: str
    attempt_index: int
    retry_index: int
    requested_path_target: float | None
    coordinate_unit: str
    last_valid_state_id: str
    diagnostic_level: str
    full_payload_ref: str | None
    retryable: bool
    next_requested_step: float | None
    accepted_state_advanced: bool
    commit_receipt_id: str | None

    def __post_init__(self) -> None:
        M02ResultRecord.__post_init__(self)
        if self.accepted_state_advanced or self.commit_receipt_id is not None:
            raise ContractViolation(
                "rejected trial diagnostics cannot carry accepted publication evidence"
            )


@dataclass(frozen=True, slots=True)
class TransactionTraceRecord(M02ResultRecord):
    __dataset_id__ = TRANSACTION_TRACE_DATASET

    transaction_trace_id: str
    transaction_id: str
    point_id: str | None
    event_id: str | None
    trial_id: str | None
    parent_accepted_state_id: str
    candidate_hash: str
    phase: str
    ordered_intents_hash: str
    prepare_token_ref: str | None
    commit_receipt_id: str | None
    rollback_token_ref: str | None
    read_set_hash: str
    write_set_hash: str
    idempotency_key: str
    outcome: str
    fault_stage: str | None
    accepted_state_advanced: bool

    def __post_init__(self) -> None:
        M02ResultRecord.__post_init__(self)
        if self.accepted_state_advanced and (
            self.point_id is None or self.commit_receipt_id is None
        ):
            raise ContractViolation(
                "published transaction trace requires core point and receipt references"
            )


@dataclass(frozen=True, slots=True)
class ReplayStepRecord(M02ResultRecord):
    __dataset_id__ = REPLAY_STEPS_DATASET

    replay_step_id: str
    target_id: str
    point_id: str | None
    event_id: str | None
    trial_id: str | None
    commit_receipt_id: str | None
    decision_index: int
    decision_kind: str
    decision_hash: str
    replay_mode: str
    backend_id: str
    operation_profile_id: str
    resolved_config_hash: str
    owner_contract_hash: str
    canonical_reduction_hash: str
    thread_settings_hash: str
    expected_semantic_hash: str
    observed_semantic_hash: str
    matched: bool


@dataclass(frozen=True, slots=True)
class FailureDiagnosticRecord(M02ResultRecord):
    __dataset_id__ = FAILURE_DIAGNOSTICS_DATASET

    failure_diagnostic_id: str
    trial_id: str
    parent_accepted_state_id: str
    last_valid_state_id: str
    failure_family: str
    reason_code: str
    failure_stage: str
    capability_status: str
    owner_proof_ref: str | None
    design_id: str
    surface_realization_id: str
    footprint_id: str
    path_coordinate: float | None
    coordinate_unit: str
    wall_time_s: float
    runtime_cost_units: float
    diagnostic_level: str
    denominator_scope: str
    includes_capability_unavailable: bool
    full_trace_ref: str | None
    accepted_state_advanced: bool
    commit_receipt_id: str | None

    def __post_init__(self) -> None:
        M02ResultRecord.__post_init__(self)
        if self.accepted_state_advanced or self.commit_receipt_id is not None:
            raise ContractViolation("failure diagnostics cannot publish accepted state")


@dataclass(frozen=True, slots=True)
class RefinementStudyRecord(M02ResultRecord):
    __dataset_id__ = REFINEMENT_STUDIES_DATASET

    study_id: str
    sample_id: str
    point_id: str | None
    event_id: str | None
    step_size: float
    event_tolerance: float
    coordinate_unit: str
    m01_lod: int
    root_solver_level: int
    event_position: float | None
    force_summary_n: float | None
    work_summary_n_mm: float | None
    event_order_hash: str
    event_position_error: float | None
    force_relative_error: float | None
    work_relative_error: float | None
    observed_order: float | None
    event_order_matched: bool
    passed: bool

    @property
    def summary_id(self) -> str:
        """Stable public identity consumed by M00's versioned-summary writer."""

        return stable_content_id(
            "m02-refinement-summary",
            {"study_id": self.study_id, "sample_id": self.sample_id},
        )

    @property
    def summary_kind(self) -> str:
        """Public M00 summary classification for refinement evidence."""

        return "M02_REFINEMENT_VALIDATION_SUMMARY"

    @property
    def included_dataset_classes(self) -> tuple[str, ...]:
        """Only receipt-backed accepted/event rows feed refinement summaries."""

        return ("accepted", "event")


@dataclass(frozen=True, slots=True)
class M01CompatibilityResultRecord(M02ResultRecord):
    __dataset_id__ = M01_COMPATIBILITY_RESULTS_DATASET

    compatibility_result_id: str
    panel_id: str
    scenario_id: str
    design_id: str
    geometry_fixture_id: str
    surface_realization_id: str
    footprint_id: str
    path_length_mm: float
    query_count: int
    step_count: int
    event_count: int
    cache_mode: str
    diagnostic_level: str
    m01_lod: int
    witness_lod: int
    event_position_error_mm: float
    unique_support_error_mm: float | None
    normal_error_deg: float | None
    force_relative_error: float | None
    work_relative_error: float | None
    event_order_matched: bool
    reason_code: str
    wall_time_s: float
    peak_rss_bytes: int
    artifact_size_bytes: int
    passed: bool

    @property
    def summary_id(self) -> str:
        """Stable public identity consumed by M00's versioned-summary writer."""

        return self.compatibility_result_id

    @property
    def summary_kind(self) -> str:
        """Declare that failed/rejected compatibility paths are diagnostic evidence."""

        return "M02_M01_COMPATIBILITY_DIAGNOSTIC_SUMMARY"

    @property
    def included_dataset_classes(self) -> tuple[str, ...]:
        """Compatibility panels report accepted/event paths and isolated failures."""

        return ("accepted", "event", "rejected")


class DiagnosticRecordKind(StrEnum):
    SEMANTIC_DECISION = "SEMANTIC_DECISION"
    ACCEPTED_FINAL_BLOCK_SUMMARY = "ACCEPTED_FINAL_BLOCK_SUMMARY"
    COMMITTED_EVENT_FINAL_BRACKET = "COMMITTED_EVENT_FINAL_BRACKET"
    RETRY_FAILURE_COUNT = "RETRY_FAILURE_COUNT"
    RECEIPT_REFERENCE = "RECEIPT_REFERENCE"
    ACCEPTED_FINAL_ITERATION = "ACCEPTED_FINAL_ITERATION"
    EVENT_PROBE = "EVENT_PROBE"
    EVENT_BRACKET = "EVENT_BRACKET"
    REJECTED_RETRY_SUMMARY = "REJECTED_RETRY_SUMMARY"
    FINAL_FAILURE_TRACE = "FINAL_FAILURE_TRACE"
    NONLINEAR_ITERATION = "NONLINEAR_ITERATION"
    LINE_SEARCH_ITERATION = "LINE_SEARCH_ITERATION"
    OWNER_TRIAL_RESPONSE = "OWNER_TRIAL_RESPONSE"
    TEMPORARY_BRANCH = "TEMPORARY_BRANCH"
    TRANSACTION_DETAIL = "TRANSACTION_DETAIL"


@dataclass(frozen=True, slots=True)
class DiagnosticStorageContext:
    """Facts about a candidate diagnostic row, not inputs to the solver."""

    accepted: bool = False
    final_iteration: bool = False
    committed_event: bool = False
    final_bracket: bool = False
    rejected_retry: bool = False
    terminal_failure: bool = False


_EMPTY_DIAGNOSTIC_CONTEXT = DiagnosticStorageContext()


@dataclass(frozen=True, slots=True)
class DiagnosticPersistencePolicy:
    """Pure retention decision implementing M02 requirements section 14.1."""

    level: DiagnosticLevel
    preserves_semantic_decisions: bool = True
    affects_solver_decisions: bool = False

    def should_store(
        self,
        kind: DiagnosticRecordKind,
        context: DiagnosticStorageContext = _EMPTY_DIAGNOSTIC_CONTEXT,
    ) -> bool:
        if kind in {
            DiagnosticRecordKind.SEMANTIC_DECISION,
            DiagnosticRecordKind.RETRY_FAILURE_COUNT,
            DiagnosticRecordKind.RECEIPT_REFERENCE,
        }:
            return True
        if kind is DiagnosticRecordKind.ACCEPTED_FINAL_BLOCK_SUMMARY:
            return context.accepted and context.final_iteration
        if kind is DiagnosticRecordKind.COMMITTED_EVENT_FINAL_BRACKET:
            return context.committed_event and context.final_bracket
        if self.level is DiagnosticLevel.COMPACT:
            return False
        if kind is DiagnosticRecordKind.ACCEPTED_FINAL_ITERATION:
            return context.accepted and context.final_iteration
        if kind in {DiagnosticRecordKind.EVENT_PROBE, DiagnosticRecordKind.EVENT_BRACKET}:
            return True
        if kind is DiagnosticRecordKind.REJECTED_RETRY_SUMMARY:
            return context.rejected_retry
        if kind is DiagnosticRecordKind.FINAL_FAILURE_TRACE:
            return context.terminal_failure
        if self.level is DiagnosticLevel.STANDARD:
            return False
        return True


def diagnostic_persistence_policy(
    level: DiagnosticLevel | str,
) -> DiagnosticPersistencePolicy:
    """Return an immutable persistence strategy for ``level``."""

    return DiagnosticPersistencePolicy(DiagnosticLevel(level))


def should_persist_diagnostic(
    level: DiagnosticLevel | str,
    kind: DiagnosticRecordKind,
    context: DiagnosticStorageContext = _EMPTY_DIAGNOSTIC_CONTEXT,
) -> bool:
    """Convenience form of the pure diagnostic retention decision."""

    return diagnostic_persistence_policy(level).should_store(kind, context)


_M02_SCHEMA_MATURITY = Maturity(
    theory_defined=MaturityEvidence(
        MaturityStatus.SPEC_DEFINED,
        "M02 frozen numerics result and plot-data contract",
        M02_EXTENSION_SCHEMA_VERSION,
    ),
    code_implemented=MaturityEvidence(
        MaturityStatus.PASSED_WITH_EVIDENCE,
        "M02 result extension and diagnostic isolation",
        M02_EXTENSION_SCHEMA_VERSION,
        ("tests/numerics/test_result_extension.py",),
    ),
    numerically_verified=MaturityEvidence(
        MaturityStatus.PASSED_WITH_EVIDENCE,
        "M02 schema registration and read-only recipe checks",
        M02_EXTENSION_SCHEMA_VERSION,
        (
            "tests/numerics/test_result_extension.py",
            "tests/numerics/test_plot_recipes.py",
        ),
    ),
    experimentally_validated=MaturityEvidence(
        MaturityStatus.BLOCKED_UNAVAILABLE,
        "no A/B physical implementation or experiment in M02 software validation",
    ),
)


_DATASET_CADENCE = {
    CONTINUATION_TARGETS_DATASET: "per_continuation_target",
    CONTINUATION_ATTEMPTS_DATASET: "per_trial_attempt",
    ACCEPTED_STEP_NUMERICS_DATASET: "per_receipt_backed_accepted_step",
    RESIDUAL_BLOCK_SUMMARIES_DATASET: "per_accepted_final_residual_block",
    ITERATION_TRACES_DATASET: "per_nonlinear_iteration",
    REJECTED_ITERATION_TRACES_DATASET: "per_rejected_nonlinear_iteration",
    EVENT_CHANNEL_REGISTRATIONS_DATASET: "per_event_channel_registration",
    EVENT_PROBES_DATASET: "per_equilibrated_event_probe",
    EVENT_BRACKETS_DATASET: "per_event_bracket_update",
    REJECTED_EVENT_BRACKETS_DATASET: "per_rejected_event_bracket_update",
    EVENT_EARLIESTNESS_CERTIFICATES_DATASET: "per_event_localization_attempt",
    SIMULTANEOUS_EVENT_GROUPS_DATASET: "per_committed_event_group_member",
    EVENT_DEPENDENCIES_DATASET: "per_committed_event_dependency",
    CASCADE_ROUNDS_DATASET: "per_committed_cascade_round",
    REJECTED_TRIAL_DIAGNOSTICS_DATASET: "per_rejected_trial",
    TRANSACTION_TRACE_DATASET: "per_transaction_phase",
    REPLAY_STEPS_DATASET: "per_semantic_replay_decision",
    FAILURE_DIAGNOSTICS_DATASET: "per_terminal_failure",
    REFINEMENT_STUDIES_DATASET: "per_refinement_level",
    M01_COMPATIBILITY_RESULTS_DATASET: "per_compatibility_path",
}

_DATASET_STORAGE = {
    CONTINUATION_TARGETS_DATASET: "all_levels_semantic_manifest",
    CONTINUATION_ATTEMPTS_DATASET: "standard_retry_rows_full_all_trials",
    ACCEPTED_STEP_NUMERICS_DATASET: "all_levels_receipt_backed",
    RESIDUAL_BLOCK_SUMMARIES_DATASET: "all_levels_accepted_final_blocks",
    ITERATION_TRACES_DATASET: "standard_accepted_final_full_all_accepted_iterations",
    REJECTED_ITERATION_TRACES_DATASET: "full_all_rejected_iterations",
    EVENT_CHANNEL_REGISTRATIONS_DATASET: "all_levels_semantic_manifest",
    EVENT_PROBES_DATASET: "standard_and_full",
    EVENT_BRACKETS_DATASET: "compact_committed_final_standard_all_committed_full_all",
    REJECTED_EVENT_BRACKETS_DATASET: "standard_and_full_rejected_trial_brackets",
    EVENT_EARLIESTNESS_CERTIFICATES_DATASET: "all_levels_semantic_decisions",
    SIMULTANEOUS_EVENT_GROUPS_DATASET: "all_levels_committed_events",
    EVENT_DEPENDENCIES_DATASET: "all_levels_committed_events",
    CASCADE_ROUNDS_DATASET: "all_levels_committed_events",
    REJECTED_TRIAL_DIAGNOSTICS_DATASET: "compact_counts_standard_rows_full_payloads",
    TRANSACTION_TRACE_DATASET: "compact_receipt_refs_full_transaction_details",
    REPLAY_STEPS_DATASET: "all_levels_semantic_decisions",
    FAILURE_DIAGNOSTICS_DATASET: "compact_counts_standard_terminal_trace",
    REFINEMENT_STUDIES_DATASET: "explicit_validation_campaign",
    M01_COMPATIBILITY_RESULTS_DATASET: "explicit_validation_campaign",
}

_UNIT_BY_FIELD = {
    "characteristic_length_mm": "mm",
    "start_coordinate": "declared_by_coordinate_unit",
    "target_coordinate": "declared_by_coordinate_unit",
    "attempted_coordinate": "declared_by_coordinate_unit",
    "accepted_coordinate": "declared_by_coordinate_unit",
    "requested_step": "declared_by_coordinate_unit",
    "accepted_step": "declared_by_coordinate_unit",
    "requested_path_target": "declared_by_coordinate_unit",
    "next_requested_step": "declared_by_coordinate_unit",
    "path_coordinate": "declared_by_coordinate_unit",
    "left_coordinate": "declared_by_coordinate_unit",
    "right_coordinate": "declared_by_coordinate_unit",
    "root_coordinate": "declared_by_coordinate_unit",
    "covered_start_coordinate": "declared_by_coordinate_unit",
    "covered_end_coordinate": "declared_by_coordinate_unit",
    "candidate_root_coordinate": "declared_by_coordinate_unit",
    "position_tolerance": "declared_by_coordinate_unit",
    "localization_error": "declared_by_coordinate_unit",
    "simultaneous_tolerance": "declared_by_coordinate_unit",
    "step_size": "declared_by_coordinate_unit",
    "event_tolerance": "declared_by_coordinate_unit",
    "event_position": "declared_by_coordinate_unit",
    "event_position_error": "declared_by_coordinate_unit",
    "raw_norm": "declared_by_raw_unit",
    "reference_norm": "declared_by_raw_unit",
    "absolute_tolerance": "declared_by_raw_unit",
    "tolerance": "declared_by_raw_unit",
    "raw_guard": "declared_by_raw_guard_unit",
    "left_raw_guard": "declared_by_raw_guard_unit",
    "right_raw_guard": "declared_by_raw_guard_unit",
    "zero_value": "declared_by_raw_guard_unit",
    "force_summary_n": "N",
    "work_summary_n_mm": "N*mm",
    "path_length_mm": "mm",
    "event_position_error_mm": "mm",
    "unique_support_error_mm": "mm",
    "normal_error_deg": "degree",
    "wall_time_s": "s",
    "peak_rss_bytes": "byte",
    "artifact_size_bytes": "byte",
}


def _dtype(annotation: Any) -> str:
    text = str(annotation)
    if text in {"float", "float | None"}:
        return "float64"
    if text in {"int", "int | None"}:
        return "int64"
    if text in {"bool", "bool | None"}:
        return "bool"
    return "utf8"


def _frame_and_reference(name: str, unit: str) -> tuple[str, str]:
    if unit in {"mm", "declared_by_coordinate_unit"} or "coordinate" in name:
        return "M02_CONTINUATION_COORDINATE", "M02_PATH_ORIGIN"
    if unit == "N":
        return "OWNER_DECLARED_FORCE_FRAME", "OWNER_DECLARED_APPLICATION_POINT"
    if unit in {"declared_by_raw_unit", "declared_by_raw_guard_unit"}:
        return "OWNER_DECLARED_FRAME", "OWNER_DECLARED_REFERENCE"
    return "NOT_APPLICABLE", "NOT_APPLICABLE"


def _fields(
    dataset_id: str,
    record_type: type[RecordBase],
    *,
    classification: DataClassification,
    source_identity: SourceIdentity,
    primary_keys: tuple[str, ...],
) -> tuple[FieldMetadata, ...]:
    result: list[FieldMetadata] = []
    indices = tuple(dict.fromkeys(("run_id", "case_id", *primary_keys)))
    for item in dataclasses.fields(record_type):
        name = item.name
        dtype = _dtype(item.type)
        unit = _UNIT_BY_FIELD.get(name, "1")
        frame, reference = _frame_and_reference(name, unit)
        result.append(
            FieldMetadata(
                field_id=f"{dataset_id}.{name}",
                namespace="m02",
                owner_module="M02",
                semantics=(
                    f"M02 {dataset_id.rsplit('.', 1)[-1]} {name.replace('_', ' ')}; "
                    "availability and interpretation are frozen by "
                    "M02_NUMERICS_REQUIREMENTS 1.0.0"
                ),
                classification=classification,
                dtype=dtype,
                shape=(),
                dimensions=(),
                raggedness="scalar_or_canonical_json",
                unit=unit,
                frame=frame,
                reference_point=reference,
                sign_semantics=(
                    "signed in the declared continuation/owner convention where numeric; "
                    "otherwise not applicable"
                ),
                action_semantics=(
                    "numerical orchestration evidence only; owner physical action semantics "
                    "remain opaque"
                ),
                indices=indices,
                sampling_cadence=_DATASET_CADENCE[dataset_id],
                storage_frequency=_DATASET_STORAGE[dataset_id],
                ownership=(
                    "M02 receipt-backed evidence"
                    if classification is DataClassification.CANONICAL_RAW
                    else "M02 isolated diagnostic or validation evidence"
                ),
                null_policy=(
                    "null only during M00 transaction staging; atomically patched before publication"
                    if name == "commit_receipt_id"
                    and dataset_id
                    in {
                        ACCEPTED_STEP_NUMERICS_DATASET,
                        CASCADE_ROUNDS_DATASET,
                        EVENT_BRACKETS_DATASET,
                        EVENT_DEPENDENCIES_DATASET,
                        ITERATION_TRACES_DATASET,
                        RESIDUAL_BLOCK_SUMMARIES_DATASET,
                        SIMULTANEOUS_EVENT_GROUPS_DATASET,
                    }
                    else "null only with explicit StatusTuple and unavailable/not-applicable meaning"
                    if "None" in str(item.type)
                    else "not_null"
                ),
                source_identity=source_identity,
                authority_refs=(
                    "M02_NUMERICS_REQUIREMENTS 1.0.0 §14.1-14.4",
                    "M02_NUMERICS_REQUIREMENTS 1.0.0 §17",
                    "M00_FOUNDATION_REQUIREMENTS 1.0.0 §9",
                ),
                maturity=_M02_SCHEMA_MATURITY,
                introduced_version=M02_EXTENSION_SCHEMA_VERSION,
                deprecated_version=None,
                storage_dataset=dataset_id,
                encoding="parquet_zstd_lossless",
                precision="float64" if dtype == "float64" else "exact",
                required="None" not in str(item.type),
            )
        )
    return tuple(result)


def _dataset(
    dataset_id: str,
    record_type: type[RecordBase],
    dataset_class: DatasetClass,
    primary_keys: tuple[str, ...],
    *,
    default_visible: bool,
    source_identity: SourceIdentity = SourceIdentity.DEV_POLICY,
) -> DatasetDescriptor:
    classification = {
        DatasetClass.ACCEPTED: DataClassification.CANONICAL_RAW,
        DatasetClass.EVENT: DataClassification.CANONICAL_RAW,
        DatasetClass.INDEX: DataClassification.CANONICAL_RAW,
        DatasetClass.TRANSACTION: DataClassification.CANONICAL_RAW,
        DatasetClass.REJECTED: DataClassification.DIAGNOSTIC,
        DatasetClass.SUMMARY: DataClassification.DERIVED,
    }[dataset_class]
    return DatasetDescriptor(
        dataset_id=dataset_id,
        namespace="m02",
        owner_module="M02",
        schema_version=M02_EXTENSION_SCHEMA_VERSION,
        dataset_class=dataset_class,
        record_type=record_type,
        fields=_fields(
            dataset_id,
            record_type,
            classification=classification,
            source_identity=source_identity,
            primary_keys=primary_keys,
        ),
        primary_keys=primary_keys,
        partition_keys=("case_id",),
        default_visible=default_visible,
        source_identity=source_identity,
    )


def _core_relation(
    suffix: str,
    left_dataset: str,
    left_key: str,
    right_dataset: str,
    right_key: str,
) -> RelationDescriptor:
    return RelationDescriptor(
        relation_id=f"m02.relation.{suffix}",
        left_dataset=left_dataset,
        right_dataset=right_dataset,
        left_keys=(left_key,),
        right_keys=(right_key,),
        cardinality="many-to-one",
    )


def m02_result_extension() -> ResultExtensionDescriptor:
    """Return the complete frozen M02 ``m02`` registry extension."""

    tables = (
        _dataset(
            CONTINUATION_TARGETS_DATASET,
            ContinuationTargetRecord,
            DatasetClass.INDEX,
            ("target_id",),
            default_visible=True,
        ),
        _dataset(
            CONTINUATION_ATTEMPTS_DATASET,
            ContinuationAttemptRecord,
            DatasetClass.REJECTED,
            ("attempt_id",),
            default_visible=False,
        ),
        _dataset(
            ACCEPTED_STEP_NUMERICS_DATASET,
            AcceptedStepNumericsRecord,
            DatasetClass.ACCEPTED,
            ("numerics_record_id",),
            default_visible=True,
        ),
        _dataset(
            RESIDUAL_BLOCK_SUMMARIES_DATASET,
            ResidualBlockSummaryRecord,
            DatasetClass.ACCEPTED,
            ("residual_summary_id",),
            default_visible=True,
        ),
        _dataset(
            ITERATION_TRACES_DATASET,
            IterationTraceRecord,
            DatasetClass.ACCEPTED,
            ("trace_id",),
            default_visible=True,
        ),
        _dataset(
            REJECTED_ITERATION_TRACES_DATASET,
            RejectedIterationTraceRecord,
            DatasetClass.REJECTED,
            ("trace_id",),
            default_visible=False,
        ),
        _dataset(
            EVENT_CHANNEL_REGISTRATIONS_DATASET,
            EventChannelRegistrationRecord,
            DatasetClass.INDEX,
            ("registration_id",),
            default_visible=True,
        ),
        _dataset(
            EVENT_PROBES_DATASET,
            EventProbeRecord,
            DatasetClass.REJECTED,
            ("probe_id",),
            default_visible=False,
        ),
        _dataset(
            EVENT_BRACKETS_DATASET,
            EventBracketRecord,
            DatasetClass.EVENT,
            ("bracket_id",),
            default_visible=True,
        ),
        _dataset(
            REJECTED_EVENT_BRACKETS_DATASET,
            RejectedEventBracketRecord,
            DatasetClass.REJECTED,
            ("bracket_id",),
            default_visible=False,
        ),
        _dataset(
            EVENT_EARLIESTNESS_CERTIFICATES_DATASET,
            EventEarliestnessCertificateRecord,
            DatasetClass.REJECTED,
            ("earliestness_certificate_id",),
            default_visible=False,
        ),
        _dataset(
            SIMULTANEOUS_EVENT_GROUPS_DATASET,
            SimultaneousEventGroupRecord,
            DatasetClass.EVENT,
            ("simultaneous_group_id", "event_id"),
            default_visible=True,
        ),
        _dataset(
            EVENT_DEPENDENCIES_DATASET,
            EventDependencyRecord,
            DatasetClass.EVENT,
            ("dependency_record_id",),
            default_visible=True,
        ),
        _dataset(
            CASCADE_ROUNDS_DATASET,
            CascadeRoundRecord,
            DatasetClass.EVENT,
            ("cascade_record_id",),
            default_visible=True,
        ),
        _dataset(
            REJECTED_TRIAL_DIAGNOSTICS_DATASET,
            RejectedTrialDiagnosticRecord,
            DatasetClass.REJECTED,
            ("diagnostic_id",),
            default_visible=False,
        ),
        _dataset(
            TRANSACTION_TRACE_DATASET,
            TransactionTraceRecord,
            DatasetClass.TRANSACTION,
            ("transaction_trace_id",),
            default_visible=False,
        ),
        _dataset(
            REPLAY_STEPS_DATASET,
            ReplayStepRecord,
            DatasetClass.TRANSACTION,
            ("replay_step_id", "decision_index"),
            default_visible=False,
        ),
        _dataset(
            FAILURE_DIAGNOSTICS_DATASET,
            FailureDiagnosticRecord,
            DatasetClass.REJECTED,
            ("failure_diagnostic_id",),
            default_visible=False,
        ),
        _dataset(
            REFINEMENT_STUDIES_DATASET,
            RefinementStudyRecord,
            DatasetClass.SUMMARY,
            ("study_id", "sample_id"),
            default_visible=False,
            source_identity=SourceIdentity.VALIDATION_ONLY,
        ),
        _dataset(
            M01_COMPATIBILITY_RESULTS_DATASET,
            M01CompatibilityResultRecord,
            DatasetClass.SUMMARY,
            ("compatibility_result_id",),
            default_visible=False,
            source_identity=SourceIdentity.VALIDATION_ONLY,
        ),
    )

    relations = (
        _core_relation(
            "target_parent_to_receipt",
            CONTINUATION_TARGETS_DATASET,
            "parent_commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "attempt_to_rejected_trial",
            CONTINUATION_ATTEMPTS_DATASET,
            "trial_id",
            CORE_REJECTED_TRIALS_DATASET,
            "trial_id",
        ),
        _core_relation(
            "accepted_step_to_point",
            ACCEPTED_STEP_NUMERICS_DATASET,
            "point_id",
            CORE_ACCEPTED_POINTS_DATASET,
            "point_id",
        ),
        _core_relation(
            "accepted_step_to_receipt",
            ACCEPTED_STEP_NUMERICS_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "accepted_step_to_event",
            ACCEPTED_STEP_NUMERICS_DATASET,
            "event_id",
            CORE_COMMITTED_EVENTS_DATASET,
            "event_id",
        ),
        _core_relation(
            "residual_to_point",
            RESIDUAL_BLOCK_SUMMARIES_DATASET,
            "point_id",
            CORE_ACCEPTED_POINTS_DATASET,
            "point_id",
        ),
        _core_relation(
            "residual_to_receipt",
            RESIDUAL_BLOCK_SUMMARIES_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "iteration_to_point",
            ITERATION_TRACES_DATASET,
            "point_id",
            CORE_ACCEPTED_POINTS_DATASET,
            "point_id",
        ),
        _core_relation(
            "iteration_to_rejected_trial",
            REJECTED_ITERATION_TRACES_DATASET,
            "trial_id",
            CORE_REJECTED_TRIALS_DATASET,
            "trial_id",
        ),
        _core_relation(
            "iteration_to_receipt",
            ITERATION_TRACES_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "probe_to_rejected_trial",
            EVENT_PROBES_DATASET,
            "trial_id",
            CORE_REJECTED_TRIALS_DATASET,
            "trial_id",
        ),
        _core_relation(
            "probe_to_event",
            EVENT_PROBES_DATASET,
            "event_id",
            CORE_COMMITTED_EVENTS_DATASET,
            "event_id",
        ),
        _core_relation(
            "probe_to_receipt",
            EVENT_PROBES_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "bracket_to_rejected_trial",
            REJECTED_EVENT_BRACKETS_DATASET,
            "trial_id",
            CORE_REJECTED_TRIALS_DATASET,
            "trial_id",
        ),
        _core_relation(
            "bracket_to_event",
            EVENT_BRACKETS_DATASET,
            "event_id",
            CORE_COMMITTED_EVENTS_DATASET,
            "event_id",
        ),
        _core_relation(
            "bracket_to_receipt",
            EVENT_BRACKETS_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "earliestness_to_rejected_trial",
            EVENT_EARLIESTNESS_CERTIFICATES_DATASET,
            "trial_id",
            CORE_REJECTED_TRIALS_DATASET,
            "trial_id",
        ),
        _core_relation(
            "earliestness_to_event",
            EVENT_EARLIESTNESS_CERTIFICATES_DATASET,
            "event_id",
            CORE_COMMITTED_EVENTS_DATASET,
            "event_id",
        ),
        _core_relation(
            "earliestness_to_receipt",
            EVENT_EARLIESTNESS_CERTIFICATES_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "simultaneous_member_to_event",
            SIMULTANEOUS_EVENT_GROUPS_DATASET,
            "event_id",
            CORE_COMMITTED_EVENTS_DATASET,
            "event_id",
        ),
        _core_relation(
            "dependency_to_receipt",
            EVENT_DEPENDENCIES_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "simultaneous_member_to_point",
            SIMULTANEOUS_EVENT_GROUPS_DATASET,
            "point_id",
            CORE_ACCEPTED_POINTS_DATASET,
            "point_id",
        ),
        _core_relation(
            "cascade_to_receipt",
            CASCADE_ROUNDS_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "simultaneous_member_to_receipt",
            SIMULTANEOUS_EVENT_GROUPS_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "dependency_event",
            EVENT_DEPENDENCIES_DATASET,
            "event_id",
            CORE_COMMITTED_EVENTS_DATASET,
            "event_id",
        ),
        _core_relation(
            "dependency_parent_event",
            EVENT_DEPENDENCIES_DATASET,
            "depends_on_event_id",
            CORE_COMMITTED_EVENTS_DATASET,
            "event_id",
        ),
        _core_relation(
            "cascade_to_event",
            CASCADE_ROUNDS_DATASET,
            "event_id",
            CORE_COMMITTED_EVENTS_DATASET,
            "event_id",
        ),
        _core_relation(
            "cascade_to_point",
            CASCADE_ROUNDS_DATASET,
            "point_id",
            CORE_ACCEPTED_POINTS_DATASET,
            "point_id",
        ),
        _core_relation(
            "rejected_diagnostic_to_trial",
            REJECTED_TRIAL_DIAGNOSTICS_DATASET,
            "trial_id",
            CORE_REJECTED_TRIALS_DATASET,
            "trial_id",
        ),
        _core_relation(
            "rejected_diagnostic_to_receipt",
            REJECTED_TRIAL_DIAGNOSTICS_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "transaction_to_point",
            TRANSACTION_TRACE_DATASET,
            "point_id",
            CORE_ACCEPTED_POINTS_DATASET,
            "point_id",
        ),
        _core_relation(
            "transaction_to_event",
            TRANSACTION_TRACE_DATASET,
            "event_id",
            CORE_COMMITTED_EVENTS_DATASET,
            "event_id",
        ),
        _core_relation(
            "transaction_to_trial",
            TRANSACTION_TRACE_DATASET,
            "trial_id",
            CORE_REJECTED_TRIALS_DATASET,
            "trial_id",
        ),
        _core_relation(
            "failure_to_receipt",
            FAILURE_DIAGNOSTICS_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "transaction_to_receipt",
            TRANSACTION_TRACE_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "replay_to_point",
            REPLAY_STEPS_DATASET,
            "point_id",
            CORE_ACCEPTED_POINTS_DATASET,
            "point_id",
        ),
        _core_relation(
            "replay_to_event",
            REPLAY_STEPS_DATASET,
            "event_id",
            CORE_COMMITTED_EVENTS_DATASET,
            "event_id",
        ),
        _core_relation(
            "replay_to_trial",
            REPLAY_STEPS_DATASET,
            "trial_id",
            CORE_REJECTED_TRIALS_DATASET,
            "trial_id",
        ),
        _core_relation(
            "replay_to_receipt",
            REPLAY_STEPS_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
        _core_relation(
            "failure_to_trial",
            FAILURE_DIAGNOSTICS_DATASET,
            "trial_id",
            CORE_REJECTED_TRIALS_DATASET,
            "trial_id",
        ),
        _core_relation(
            "refinement_to_point",
            REFINEMENT_STUDIES_DATASET,
            "point_id",
            CORE_ACCEPTED_POINTS_DATASET,
            "point_id",
        ),
        _core_relation(
            "refinement_to_event",
            REFINEMENT_STUDIES_DATASET,
            "event_id",
            CORE_COMMITTED_EVENTS_DATASET,
            "event_id",
        ),
    )
    return ResultExtensionDescriptor(
        namespace="m02",
        owner_module="M02",
        extension_schema_version=M02_EXTENSION_SCHEMA_VERSION,
        tables=tables,
        arrays=(),
        relations=relations,
        common_keys=("run_id", "case_id"),
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=_M02_SCHEMA_MATURITY,
        compatibility_class=CompatibilityClass.ADDITIVE_MINOR,
    )


def m02_dataset_ids() -> tuple[str, ...]:
    """Return the frozen IDs used by registry and future README checks."""

    return M02_REGISTERED_DATASET_IDS


def numerics_result_extension() -> ResultExtensionDescriptor:
    """M01-style public spelling for :func:`m02_result_extension`."""

    return m02_result_extension()


def m02_field_metadata(field_id: str) -> FieldMetadata:
    """Resolve a frozen M02 field ID for read-only consumer contracts."""

    for dataset in m02_result_extension().tables:
        for field in dataset.fields:
            if field.field_id == field_id:
                return field
    raise KeyError(field_id)
