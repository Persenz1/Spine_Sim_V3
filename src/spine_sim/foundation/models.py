"""Frozen source, maturity, status, and core record value objects."""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, ClassVar

from .canonical import canonical_json_bytes, semantic_hash
from .errors import ContractViolation


class SourceIdentity(StrEnum):
    FIXED_ENGINEERING = "FIXED_ENGINEERING"
    ACCEPTED_AUTHORITY = "ACCEPTED_AUTHORITY"
    PROPOSED_SUPPLEMENT = "PROPOSED_SUPPLEMENT"
    DEV_POLICY = "DEV_POLICY"
    VALIDATION_ONLY = "VALIDATION_ONLY"


DEFAULT_READER_IDENTITIES = frozenset(
    {SourceIdentity.FIXED_ENGINEERING, SourceIdentity.ACCEPTED_AUTHORITY, SourceIdentity.DEV_POLICY}
)


class MaturityStatus(StrEnum):
    NOT_ASSESSED = "NOT_ASSESSED"
    SPEC_DEFINED = "SPEC_DEFINED"
    IMPLEMENTED_NOT_RUN = "IMPLEMENTED_NOT_RUN"
    PASSED_WITH_EVIDENCE = "PASSED_WITH_EVIDENCE"
    FAILED = "FAILED"
    BLOCKED_UNAVAILABLE = "BLOCKED_UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ValuePresence(StrEnum):
    PRESENT = "PRESENT"
    NULL = "NULL"


class CapabilityStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    UNAVAILABLE = "UNAVAILABLE"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AttemptOutcome(StrEnum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    ACCEPTED = "ACCEPTED"
    REJECTED_TRIAL = "REJECTED_TRIAL"
    CERTIFICATION_REJECTED = "CERTIFICATION_REJECTED"
    NUMERICAL_FAILURE = "NUMERICAL_FAILURE"
    TRANSACTION_FAILURE = "TRANSACTION_FAILURE"


class PhysicalFeasibility(StrEnum):
    NOT_ASSESSED = "NOT_ASSESSED"
    FEASIBLE = "FEASIBLE"
    PHYSICAL_INFEASIBLE = "PHYSICAL_INFEASIBLE"


class CertificationStatus(StrEnum):
    NOT_ASSESSED = "NOT_ASSESSED"
    NOT_CERTIFIABLE = "NOT_CERTIFIABLE"
    CERTIFICATION_BLOCKED = "CERTIFICATION_BLOCKED"
    CERTIFIED_FOR_DECLARED_SCOPE = "CERTIFIED_FOR_DECLARED_SCOPE"


@dataclass(frozen=True, slots=True)
class AuthorityRef:
    path_or_id: str
    version: str
    sha256: str
    locator: str


@dataclass(frozen=True, slots=True)
class ValueProvenance:
    source_id: str
    source_hash: str
    field_path: str
    source_identity: SourceIdentity


@dataclass(frozen=True, slots=True)
class MaturityEvidence:
    status: MaturityStatus
    scope: str
    version_or_hash: str | None = None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Maturity:
    theory_defined: MaturityEvidence
    code_implemented: MaturityEvidence
    numerically_verified: MaturityEvidence
    experimentally_validated: MaturityEvidence

    @classmethod
    def validation_only_implemented(cls) -> Maturity:
        return cls(
            MaturityEvidence(MaturityStatus.SPEC_DEFINED, "M00 software contract"),
            MaturityEvidence(MaturityStatus.PASSED_WITH_EVIDENCE, "M00 validation fixture"),
            MaturityEvidence(MaturityStatus.NOT_APPLICABLE, "no physics"),
            MaturityEvidence(MaturityStatus.NOT_APPLICABLE, "no experiment"),
        )


@dataclass(frozen=True, slots=True)
class StatusTuple:
    value_presence: ValuePresence
    capability_status: CapabilityStatus
    attempt_outcome: AttemptOutcome
    physical_feasibility: PhysicalFeasibility
    certification_status: CertificationStatus
    reason_code: str
    explanation: str
    authority_refs: tuple[str, ...] = ()
    last_valid_state_id: str | None = None

    def __post_init__(self) -> None:
        if (
            self.value_presence is ValuePresence.PRESENT
            and self.capability_status is CapabilityStatus.UNAVAILABLE
        ):
            raise ContractViolation("unavailable values cannot be marked PRESENT")
        if (
            self.physical_feasibility is PhysicalFeasibility.PHYSICAL_INFEASIBLE
            and self.attempt_outcome
            in {AttemptOutcome.NUMERICAL_FAILURE, AttemptOutcome.TRANSACTION_FAILURE}
        ):
            raise ContractViolation(
                "numerical/transaction failure cannot imply physical infeasibility"
            )


@dataclass(frozen=True, slots=True)
class RecordBase:
    """Marker for records accepted by ResultWriter."""

    __dataset_id__: ClassVar[str]

    def semantic_dict(self) -> dict[str, Any]:
        return {
            item.name: _serialize(getattr(self, item.name))
            for item in dataclasses.fields(self)
            if item.metadata.get("semantic", True) and item.name != "run_id"
        }

    def semantic_hash(self) -> str:
        return semantic_hash(self.semantic_dict())

    def storage_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for item in dataclasses.fields(self):
            value = getattr(self, item.name)
            result[item.name] = _storage_value(value)
        return result


def _serialize(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return _serialize(dataclasses.asdict(value))  # type: ignore[arg-type]
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_serialize(item) for item in value]
    return value


def _storage_value(value: Any) -> Any:
    if dataclasses.is_dataclass(value) or isinstance(value, dict | tuple | list):
        return canonical_json_bytes(_serialize(value)).decode("utf-8")
    if isinstance(value, StrEnum):
        return value.value
    return value


def decode_json_storage(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


@dataclass(frozen=True, slots=True)
class RunEnvelope(RecordBase):
    __dataset_id__ = "core.indices.runs"

    run_id: str
    run_fingerprint: str
    operation_kind: str
    operation_profile: str
    result_api_version: str
    bundle_schema_version: str
    registry_hash: str
    engineering_model_contract_versions: tuple[str, ...]
    solver_build_id: str
    git_commit: str
    dirty_status: str
    resolved_run_config_id: str
    resolved_run_config_hash: str
    source_file_hashes: dict[str, str]
    case_index_id: str
    design_index_id: str
    seed_index_id: str
    surface_realization_index_id: str
    unit_registry_id: str
    frame_registry_id: str
    reference_registry_id: str
    transform_registry_id: str
    provenance_labels: tuple[str, ...]
    certification_status: CertificationStatus
    replay_manifest_id: str
    replay_manifest_hash: str
    created_at_utc_ns: int = field(metadata={"semantic": False})


@dataclass(frozen=True, slots=True)
class AcceptedPointBase(RecordBase):
    __dataset_id__ = "core.accepted_points.common"

    run_id: str
    case_id: str
    design_id: str
    seed_id: str
    surface_realization_id: str
    point_id: str
    accepted_point_index: int
    accepted_state_id: str
    parent_state_id: str
    commit_receipt_id: str | None
    operation_kind: str
    stage: str
    path_kind: str
    path_coordinate: float
    path_unit: str
    accepted_increment: float
    physical_time_value: float | None
    physical_time_status: StatusTuple
    event_sequence: int
    simultaneous_group_ids: tuple[str, ...]
    cascade_ids: tuple[str, ...]
    module_payload_refs: tuple[str, ...]
    residual_refs: tuple[str, ...]
    graph_refs: tuple[str, ...]
    quality_refs: tuple[str, ...]
    work_ledger_refs: tuple[str, ...]
    source_identity: SourceIdentity
    requirement_origin: str
    value_provenance: tuple[ValueProvenance, ...]
    authority_refs: tuple[AuthorityRef, ...]
    maturity: Maturity
    certification_status: CertificationStatus
    request_hash: str
    response_hash: str
    replay_step_hash: str


@dataclass(frozen=True, slots=True)
class EntityAcceptedPointBase(RecordBase):
    run_id: str
    case_id: str
    point_id: str
    accepted_state_id: str
    entity_id: str
    entity_kind: str
    module_payload_refs: tuple[str, ...]
    source_identity: SourceIdentity


@dataclass(frozen=True, slots=True)
class PerUnitAcceptedPoint(EntityAcceptedPointBase):
    __dataset_id__ = "core.accepted_points.per_unit"


@dataclass(frozen=True, slots=True)
class PerNeedleAcceptedPoint(EntityAcceptedPointBase):
    __dataset_id__ = "core.accepted_points.per_needle"


@dataclass(frozen=True, slots=True)
class PerSupportAcceptedPoint(EntityAcceptedPointBase):
    __dataset_id__ = "core.accepted_points.per_support"


@dataclass(frozen=True, slots=True)
class CommittedEventBase(RecordBase):
    __dataset_id__ = "core.committed_events.events"

    event_id: str
    source_event_ids: tuple[str, ...]
    hierarchy: str
    entity_ids: tuple[str, ...]
    run_id: str
    case_id: str
    design_id: str
    seed_id: str
    surface_realization_id: str
    event_kind: str
    raw_event_function: float
    event_function_unit: str
    numerical_scaling_id: str
    path_coordinate: float
    path_bracket: tuple[float, float]
    fraction_basis: str
    localization_error: float
    pre_event_accepted_state_id: str
    event_point_trial_id: str
    post_event_accepted_state_id: str | None
    post_event_status: StatusTuple
    simultaneous_group_id: str | None
    dependency_edges: tuple[str, ...]
    cascade_round: int
    pre_payload_refs: tuple[str, ...]
    event_payload_refs: tuple[str, ...]
    post_payload_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    recoverability: str
    stability: str
    terminal_classification: str
    status: StatusTuple
    source_identity: SourceIdentity
    maturity: Maturity
    certification_status: CertificationStatus
    committed: bool
    commit_receipt_id: str | None


@dataclass(frozen=True, slots=True)
class EventDependencyBase(RecordBase):
    __dataset_id__ = "core.committed_events.dependencies"

    run_id: str
    case_id: str
    event_id: str
    depends_on_event_id: str
    dependency_kind: str
    source_identity: SourceIdentity


@dataclass(frozen=True, slots=True)
class CascadeRoundBase(RecordBase):
    __dataset_id__ = "core.committed_events.cascade_rounds"

    run_id: str
    case_id: str
    cascade_id: str
    round_index: int
    state_hash: str
    event_ids: tuple[str, ...]
    source_identity: SourceIdentity


@dataclass(frozen=True, slots=True)
class RejectedTrialBase(RecordBase):
    __dataset_id__ = "core.rejected_trials.diagnostics"

    trial_id: str
    run_id: str
    case_id: str
    parent_accepted_state_id: str
    request_hash: str
    candidate_hash: str
    requested_path_target: float | None
    status: StatusTuple
    reason_codes: tuple[str, ...]
    diagnostic_summary: str
    optional_full_payload_ref: str | None
    last_valid_state_id: str
    source_identity: SourceIdentity
    accepted_state_advanced: bool = False
    committed_event_id: str | None = None
    commit_receipt_id: str | None = None


@dataclass(frozen=True, slots=True)
class SummaryBase(RecordBase):
    __dataset_id__ = "core.summaries.case"

    summary_id: str
    summary_kind: str
    schema_version: str
    algorithm_id: str
    algorithm_version: str
    algorithm_hash: str
    source_bundle_hash: str
    source_receipt_set_hash: str
    included_dataset_classes: tuple[str, ...]
    status_filters: tuple[str, ...]
    case_id: str
    design_id: str
    seed_id: str
    entity_scope: tuple[str, ...]
    output_field_ids: tuple[str, ...]
    source_identity: SourceIdentity
    maturity: Maturity
    certification_status: CertificationStatus
    created_at_utc_ns: int = field(metadata={"semantic": False})


@dataclass(frozen=True, slots=True)
class DesignSummaryBase(SummaryBase):
    __dataset_id__ = "core.summaries.design"


@dataclass(frozen=True, slots=True)
class FailureDiagnosticSummaryBase(SummaryBase):
    __dataset_id__ = "core.summaries.failure_diagnostics"


@dataclass(frozen=True, slots=True)
class CommitReceiptBase(RecordBase):
    __dataset_id__ = "core.transactions.receipts"

    receipt_id: str
    idempotency_key: str
    parent_state_id: str
    committed_state_id: str
    candidate_hash: str
    ordered_intents_hash: str
    schema_hash: str
    registry_hash: str
    config_hash: str
    published_shard_hashes: dict[str, str]
    ledger_hashes: dict[str, str]
    commit_sequence: int
    commit_marker_hash: str


@dataclass(frozen=True, slots=True)
class CaseIndexBase(RecordBase):
    __dataset_id__ = "core.indices.cases"

    run_id: str
    case_id: str
    design_id: str
    seed_id: str
    surface_realization_id: str
    finalized: bool
    receipt_set_hash: str
    source_identity: SourceIdentity


@dataclass(frozen=True, slots=True)
class RegisteredArrayPayload:
    field_id: str
    case_id: str
    data: Any
    validity: Any | None
    status: Any | None
    unit: str
    frame: str
    reference_point: str
    source_identity: SourceIdentity
