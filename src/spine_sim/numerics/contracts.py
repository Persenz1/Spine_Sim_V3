"""Typed public contracts for M02 numerical orchestration.

The contracts in this module deliberately contain no A/B constitutive data.
They reference M00 state, event, rejected-trial, and receipt identities and keep
physical-owner state opaque.  Every public value has a canonical semantic
identity and is validated at construction time.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import MISSING, dataclass
from enum import StrEnum
from typing import Any, ClassVar, Self

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    AttemptOutcome,
    AuthorityRef,
    CapabilityStatus,
    CertificationStatus,
    Maturity,
    MaturityEvidence,
    MaturityStatus,
    PhysicalFeasibility,
    SourceIdentity,
    StatusTuple,
    ValuePresence,
)

M02_SCHEMA_VERSION = "1.0.0"
M02_REQUIREMENT_AUTHORITY = "M02_NUMERICS_REQUIREMENTS 1.0.0"


class ContinuationControlMode(StrEnum):
    MONOTONE_SCALAR_TARGET = "MONOTONE_SCALAR_TARGET"
    PSEUDO_ARCLENGTH = "PSEUDO_ARCLENGTH"
    MULTIPARAMETER_FREE = "MULTIPARAMETER_FREE"
    DYNAMIC_INTEGRATION = "DYNAMIC_INTEGRATION"


class ContinuationDirection(StrEnum):
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"


class TrialPhase(StrEnum):
    TARGET_PROBE = "TARGET_PROBE"
    EVENT_PROBE = "EVENT_PROBE"
    EVENT_POINT = "EVENT_POINT"
    POST_EVENT_SIDE = "POST_EVENT_SIDE"
    CASCADE_ROUND = "CASCADE_ROUND"
    FINAL_CANDIDATE = "FINAL_CANDIDATE"


class TrialLifecycleState(StrEnum):
    TRIAL_CREATED = "TRIAL_CREATED"
    OWNER_EVALUATED = "OWNER_EVALUATED"
    NUMERICALLY_ELIGIBLE = "NUMERICALLY_ELIGIBLE"
    EVENT_COMPLETE = "EVENT_COMPLETE"
    CANDIDATE_FROZEN = "CANDIDATE_FROZEN"
    PREPARED = "PREPARED"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"
    REJECTED = "REJECTED"


class DiagnosticLevel(StrEnum):
    COMPACT = "COMPACT"
    STANDARD = "STANDARD"
    FULL = "FULL"


class ResidualKind(StrEnum):
    FORCE_EQUILIBRIUM = "FORCE_EQUILIBRIUM"
    MOMENT_EQUILIBRIUM = "MOMENT_EQUILIBRIUM"
    KINEMATIC_COMPATIBILITY = "KINEMATIC_COMPATIBILITY"
    LOAD_CONTROL = "LOAD_CONTROL"
    COMPLEMENTARITY_KKT = "COMPLEMENTARITY_KKT"
    GRAPH_DISTANCE = "GRAPH_DISTANCE"
    ACTIVE_BRANCH = "ACTIVE_BRANCH"
    ENERGY_WORK = "ENERGY_WORK"
    OWNER_DEFINED_HARD_QUALITY = "OWNER_DEFINED_HARD_QUALITY"


class ReductionNorm(StrEnum):
    L1 = "L1"
    L2 = "L2"
    LINF = "LINF"


class DerivativeKind(StrEnum):
    ANALYTIC_JACOBIAN = "ANALYTIC_JACOBIAN"
    GENERALIZED_JACOBIAN = "GENERALIZED_JACOBIAN"
    JACOBIAN_VECTOR_PRODUCT = "JACOBIAN_VECTOR_PRODUCT"
    VERSIONED_TANGENT = "VERSIONED_TANGENT"
    FINITE_DIFFERENCE_VALIDATION_ONLY = "FINITE_DIFFERENCE_VALIDATION_ONLY"
    UNAVAILABLE = "UNAVAILABLE"


class NonlinearMethod(StrEnum):
    DAMPED_NEWTON = "DAMPED_NEWTON"
    SEMISMOOTH_GENERALIZED_NEWTON = "SEMISMOOTH_GENERALIZED_NEWTON"
    TRUST_REGION = "TRUST_REGION"


class EventAdmissibleSide(StrEnum):
    NONNEGATIVE = "NONNEGATIVE"
    NONPOSITIVE = "NONPOSITIVE"
    BOTH_WITH_GRAPH_RULE = "BOTH_WITH_GRAPH_RULE"


class EventTriggerDirection(StrEnum):
    RISING = "RISING"
    FALLING = "FALLING"
    EITHER = "EITHER"
    TOUCH = "TOUCH"


class EventDetectionMode(StrEnum):
    SIGN_CHANGE = "SIGN_CHANGE"
    SIGN_CHANGE_AND_TOUCH = "SIGN_CHANGE_AND_TOUCH"
    SWEPT_COLLISION = "SWEPT_COLLISION"
    OWNER_ENCLOSURE = "OWNER_ENCLOSURE"


class EventCertificateKind(StrEnum):
    SIGN_CHANGE_BRACKETS = "SIGN_CHANGE_BRACKETS"
    STATIONARY_TOUCH_ENCLOSURE = "STATIONARY_TOUCH_ENCLOSURE"
    SWEPT_NO_EVENT = "SWEPT_NO_EVENT"
    LIPSCHITZ_ENCLOSURE = "LIPSCHITZ_ENCLOSURE"
    ADAPTIVE_PROBE_SPACING = "ADAPTIVE_PROBE_SPACING"


class EventRootMethod(StrEnum):
    BRENT = "BRENT"
    BISECTION = "BISECTION"
    TOUCH_ENCLOSURE = "TOUCH_ENCLOSURE"


class ReturnPathMode(StrEnum):
    EXPLICIT_RETURN_PATH = "EXPLICIT_RETURN_PATH"
    HOLD_AT_RELEASE_POSE = "HOLD_AT_RELEASE_POSE"
    UNSUPPORTED = "UNSUPPORTED"
    UNAVAILABLE = "UNAVAILABLE"


class FailureFamily(StrEnum):
    NUMERICAL_FAILURE = "NUMERICAL_FAILURE"
    PHYSICAL_INFEASIBLE = "PHYSICAL_INFEASIBLE"
    CONTRACT_REJECTION = "CONTRACT_REJECTION"
    DOMAIN_ERROR = "DOMAIN_ERROR"
    TRANSACTION_FAILURE = "TRANSACTION_FAILURE"


class M02ReasonCode(StrEnum):
    OK = "M02_OK"
    UNSUPPORTED_CONTROL_MODE = "M02_UNSUPPORTED_CONTROL_MODE"
    NONLINEAR_NONCONVERGENCE = "M02_NONLINEAR_NONCONVERGENCE"
    LINE_SEARCH_EXHAUSTED = "M02_LINE_SEARCH_EXHAUSTED"
    LINEAR_SOLVE_FAILURE = "M02_LINEAR_SOLVE_FAILURE"
    STEP_RETRY_EXHAUSTED = "M02_STEP_RETRY_EXHAUSTED"
    EVENT_ROOT_NONCONVERGENCE = "M02_EVENT_ROOT_NONCONVERGENCE"
    EVENT_EARLIESTNESS_UNPROVEN = "M02_EVENT_EARLIESTNESS_UNPROVEN"
    EVENT_COVERAGE_UNAVAILABLE = "M02_EVENT_COVERAGE_UNAVAILABLE"
    ZENO_CANDIDATE = "M02_ZENO_CANDIDATE"
    REPLAY_MISMATCH = "M02_REPLAY_MISMATCH"
    RESIDUAL_SCALE_MISSING = "M02_RESIDUAL_SCALE_MISSING"
    EVENT_CHANNEL_CONTRACT_INVALID = "M02_EVENT_CHANNEL_CONTRACT_INVALID"
    EVENT_DEPENDENCY_CYCLE = "M02_EVENT_DEPENDENCY_CYCLE"
    STALE_PARENT = "M02_STALE_PARENT"
    OWNER_SIDE_EFFECT_DETECTED = "M02_OWNER_SIDE_EFFECT_DETECTED"
    OWNER_PROVEN_PHYSICAL_INFEASIBLE = "M02_OWNER_PROVEN_PHYSICAL_INFEASIBLE"
    PREPARE_REJECTED = "M02_PREPARE_REJECTED"
    COMMIT_CONFLICT = "M02_COMMIT_CONFLICT"
    PERSISTENCE_FAILURE = "M02_PERSISTENCE_FAILURE"
    ROLLBACK_FAILURE = "M02_ROLLBACK_FAILURE"


class AdvanceOutcome(StrEnum):
    ACCEPTED_STEP = "ACCEPTED_STEP"
    COMMITTED_EVENT_STEP = "COMMITTED_EVENT_STEP"
    TARGET_COMPLETE = "TARGET_COMPLETE"
    REJECTED_RETRYABLE = "REJECTED_RETRYABLE"
    TERMINAL_FAILURE = "TERMINAL_FAILURE"
    UNAVAILABLE = "UNAVAILABLE"
    UNSUPPORTED = "UNSUPPORTED"


def m02_maturity(*, numerically_verified: bool = False) -> Maturity:
    """Return the frozen four-column maturity for M02 software artifacts."""

    return Maturity(
        MaturityEvidence(MaturityStatus.SPEC_DEFINED, M02_REQUIREMENT_AUTHORITY),
        MaturityEvidence(
            MaturityStatus.PASSED_WITH_EVIDENCE,
            "M02 typed software contract",
            M02_SCHEMA_VERSION,
        ),
        MaturityEvidence(
            MaturityStatus.PASSED_WITH_EVIDENCE
            if numerically_verified
            else MaturityStatus.NOT_ASSESSED,
            "analytic/VALIDATION_ONLY numerical fixtures",
        ),
        MaturityEvidence(
            MaturityStatus.BLOCKED_UNAVAILABLE,
            "no target-wall or mechanism experiment is part of M02",
        ),
    )


def supported_status(reason: str = M02ReasonCode.OK.value) -> StatusTuple:
    return StatusTuple(
        ValuePresence.PRESENT,
        CapabilityStatus.SUPPORTED,
        AttemptOutcome.NOT_ATTEMPTED,
        PhysicalFeasibility.NOT_ASSESSED,
        CertificationStatus.NOT_CERTIFIABLE,
        reason,
        "M02 software capability is available for the declared scope",
        authority_refs=(M02_REQUIREMENT_AUTHORITY,),
    )


def unavailable_status(reason: str, explanation: str) -> StatusTuple:
    return StatusTuple(
        ValuePresence.NULL,
        CapabilityStatus.UNAVAILABLE,
        AttemptOutcome.NOT_ATTEMPTED,
        PhysicalFeasibility.NOT_ASSESSED,
        CertificationStatus.CERTIFICATION_BLOCKED,
        reason,
        explanation,
        authority_refs=(M02_REQUIREMENT_AUTHORITY,),
    )


def unsupported_status(reason: str, explanation: str) -> StatusTuple:
    return StatusTuple(
        ValuePresence.NULL,
        CapabilityStatus.UNSUPPORTED,
        AttemptOutcome.NOT_ATTEMPTED,
        PhysicalFeasibility.NOT_ASSESSED,
        CertificationStatus.CERTIFICATION_BLOCKED,
        reason,
        explanation,
        authority_refs=(M02_REQUIREMENT_AUTHORITY,),
    )


@dataclass(frozen=True, slots=True)
class ContractMetadata:
    """Canonical metadata shared by every M02 public contract."""

    schema_version: str
    semantic_id: str
    semantic_hash: str
    unit: str
    status: StatusTuple
    source_identity: SourceIdentity
    maturity: Maturity
    certification_status: CertificationStatus
    authority_refs: tuple[AuthorityRef, ...] = ()

    @classmethod
    def build(
        cls,
        kind: str,
        payload: dict[str, Any],
        *,
        unit: str = "1",
        status: StatusTuple | None = None,
        source_identity: SourceIdentity = SourceIdentity.ACCEPTED_AUTHORITY,
        maturity: Maturity | None = None,
        certification_status: CertificationStatus = CertificationStatus.NOT_CERTIFIABLE,
        authority_refs: tuple[AuthorityRef, ...] = (),
    ) -> ContractMetadata:
        digest = semantic_hash(payload)
        return cls(
            schema_version=M02_SCHEMA_VERSION,
            semantic_id=stable_content_id(f"m02_{kind}", payload),
            semantic_hash=digest,
            unit=unit,
            status=status or supported_status(),
            source_identity=source_identity,
            maturity=maturity or m02_maturity(),
            certification_status=certification_status,
            authority_refs=authority_refs,
        )

    def __post_init__(self) -> None:
        if self.schema_version != M02_SCHEMA_VERSION:
            raise ContractViolation(
                "M02 schema major/version mismatch",
                details={"expected": M02_SCHEMA_VERSION, "actual": self.schema_version},
            )
        _nonempty(self.semantic_id, "semantic_id")
        _hash(self.semantic_hash, "semantic_hash")
        _nonempty(self.unit, "unit")
        if not isinstance(self.status, StatusTuple):
            raise ContractViolation("M02 metadata requires StatusTuple")
        if not isinstance(self.source_identity, SourceIdentity):
            raise ContractViolation("M02 metadata requires SourceIdentity")
        if not isinstance(self.maturity, Maturity):
            raise ContractViolation("M02 metadata requires four-column Maturity")
        if not isinstance(self.certification_status, CertificationStatus):
            raise ContractViolation("M02 metadata requires CertificationStatus")


class SemanticContract:
    """Mixin providing a canonical ``create`` constructor and metadata views."""

    __semantic_kind__: ClassVar[str]
    metadata: ContractMetadata

    @classmethod
    def create(cls, **values: Any) -> Self:
        if "metadata_unit" not in values:
            raise ContractViolation("M02 public contracts require an explicit metadata unit")
        metadata_unit = values.pop("metadata_unit")
        _nonempty(metadata_unit, "metadata_unit")
        metadata_status = values.pop("metadata_status", None)
        source_identity = values.pop("source_identity", SourceIdentity.ACCEPTED_AUTHORITY)
        maturity = values.pop("maturity", None)
        certification_status = values.pop(
            "certification_status", CertificationStatus.NOT_CERTIFIABLE
        )
        authority_refs = values.pop("authority_refs", ())
        if "metadata" in values:
            raise ContractViolation("create() owns M02 contract metadata")
        payload = _resolved_payload(cls, values)
        metadata = ContractMetadata.build(
            cls.__semantic_kind__,
            payload,
            unit=metadata_unit,
            status=metadata_status,
            source_identity=source_identity,
            maturity=maturity,
            certification_status=certification_status,
            authority_refs=authority_refs,
        )
        return cls(**values, metadata=metadata)  # type: ignore[call-arg]

    @property
    def schema_version(self) -> str:
        return self.metadata.schema_version

    @property
    def semantic_id(self) -> str:
        return self.metadata.semantic_id

    @property
    def semantic_hash(self) -> str:
        return self.metadata.semantic_hash

    def semantic_payload(self) -> dict[str, Any]:
        return {
            field.name: getattr(self, field.name)
            for field in dataclasses.fields(self)  # type: ignore[arg-type]
            if field.name != "metadata"
        }

    def _validate_metadata(self) -> None:
        payload = self.semantic_payload()
        expected_hash = semantic_hash(payload)
        expected_id = stable_content_id(f"m02_{self.__semantic_kind__}", payload)
        if self.metadata.semantic_hash != expected_hash or self.metadata.semantic_id != expected_id:
            raise ContractViolation(
                "M02 semantic ID/hash does not match contract content",
                details={
                    "kind": self.__semantic_kind__,
                    "expected_id": expected_id,
                    "actual_id": self.metadata.semantic_id,
                    "expected_hash": expected_hash,
                    "actual_hash": self.metadata.semantic_hash,
                },
            )


@dataclass(frozen=True, slots=True)
class ContinuationTarget(SemanticContract):
    __semantic_kind__ = "continuation_target"

    target_id: str
    parent_accepted_state_id: str
    parent_commit_receipt_id: str
    parent_state_hash: str
    continuation_coordinate_id: str
    coordinate_unit: str
    start_value: float
    target_value: float
    direction: ContinuationDirection
    oriented_path_mapping_id: str
    characteristic_length_mm: float
    characteristic_length_source: str
    control_mode: ContinuationControlMode
    physical_owner_ids: tuple[str, ...]
    required_event_channel_ids: tuple[str, ...]
    resolved_numerics_config_id: str
    resolved_numerics_config_hash: str
    external_dependency_refs: tuple[str, ...]
    request_id: str
    request_hash: str
    idempotency_namespace: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in (
            "target_id",
            "parent_accepted_state_id",
            "parent_commit_receipt_id",
            "continuation_coordinate_id",
            "coordinate_unit",
            "oriented_path_mapping_id",
            "characteristic_length_source",
            "resolved_numerics_config_id",
            "request_id",
            "idempotency_namespace",
        ):
            _nonempty(getattr(self, name), name)
        _hash(self.parent_state_hash, "parent_state_hash")
        _hash(self.resolved_numerics_config_hash, "resolved_numerics_config_hash")
        _hash(self.request_hash, "request_hash")
        _finite(self.start_value, "start_value")
        _finite(self.target_value, "target_value")
        _positive(self.characteristic_length_mm, "characteristic_length_mm")
        _enum(self.direction, ContinuationDirection, "direction")
        _enum(self.control_mode, ContinuationControlMode, "control_mode")
        if self.start_value == self.target_value:
            raise ContractViolation("continuation target must have nonzero oriented extent")
        expected = (
            ContinuationDirection.INCREASING
            if self.target_value > self.start_value
            else ContinuationDirection.DECREASING
        )
        if self.direction is not expected:
            raise ContractViolation("continuation direction conflicts with start/target values")
        _unique_nonempty(self.physical_owner_ids, "physical_owner_ids")
        _unique(self.required_event_channel_ids, "required_event_channel_ids")
        _unique(self.external_dependency_refs, "external_dependency_refs")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class ContinuationSession(SemanticContract):
    __semantic_kind__ = "continuation_session"

    session_handle: str
    target_id: str
    parent_accepted_state_id: str
    parent_commit_receipt_id: str
    current_coordinate: float
    next_regular_step_mm: float
    easy_streak: int
    retry_count_for_parent: int
    accepted_step_count: int
    last_failure_signature: str | None
    lifecycle_state: TrialLifecycleState
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in (
            "session_handle",
            "target_id",
            "parent_accepted_state_id",
            "parent_commit_receipt_id",
        ):
            _nonempty(getattr(self, name), name)
        _finite(self.current_coordinate, "current_coordinate")
        _positive(self.next_regular_step_mm, "next_regular_step_mm")
        for name in ("easy_streak", "retry_count_for_parent", "accepted_step_count"):
            _nonnegative_int(getattr(self, name), name)
        _enum(self.lifecycle_state, TrialLifecycleState, "lifecycle_state")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class TrialStep(SemanticContract):
    __semantic_kind__ = "trial_step"

    trial_id: str
    target_id: str
    parent_accepted_state_id: str
    phase: TrialPhase
    attempt_index: int
    retry_index: int
    cascade_round: int
    requested_coordinate: float
    oriented_path_position_mm: float
    trial_fraction: float
    requested_step_mm: float
    predictor_refs: tuple[str, ...]
    branch_request_refs: tuple[str, ...]
    event_channel_subset: tuple[str, ...]
    bracket_ref: str | None
    simultaneous_group_ref: str | None
    evaluation_cache_key: str
    request_hash: str
    accepted_state_advanced: bool
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in (
            "trial_id",
            "target_id",
            "parent_accepted_state_id",
            "evaluation_cache_key",
        ):
            _nonempty(getattr(self, name), name)
        for name in ("attempt_index", "retry_index", "cascade_round"):
            _nonnegative_int(getattr(self, name), name)
        _enum(self.phase, TrialPhase, "phase")
        _finite(self.requested_coordinate, "requested_coordinate")
        _finite(self.oriented_path_position_mm, "oriented_path_position_mm")
        _bounded(self.trial_fraction, 0.0, 1.0, "trial_fraction")
        _nonnegative(self.requested_step_mm, "requested_step_mm")
        _hash(self.request_hash, "request_hash")
        _unique(self.event_channel_subset, "event_channel_subset")
        if self.accepted_state_advanced:
            raise ContractViolation("trial objects can never advance accepted state")
        if self.phase in {TrialPhase.EVENT_PROBE, TrialPhase.EVENT_POINT} and not (
            self.bracket_ref or self.event_channel_subset
        ):
            raise ContractViolation("event trial requires a bracket or event channel subset")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class OpaqueTrialStateRef(SemanticContract):
    __semantic_kind__ = "opaque_trial_state_ref"

    state_ref: str
    owner_id: str
    owner_version: str
    parent_accepted_state_id: str
    parent_state_hash: str
    trial_id: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in (
            "state_ref",
            "owner_id",
            "owner_version",
            "parent_accepted_state_id",
            "trial_id",
        ):
            _nonempty(getattr(self, name), name)
        _hash(self.parent_state_hash, "parent_state_hash")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class RollbackToken(SemanticContract):
    __semantic_kind__ = "rollback_token"

    token_ref: str
    owner_id: str
    run_id: str
    trial_id: str
    parent_accepted_state_id: str
    parent_state_hash: str
    token_version: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in (
            "token_ref",
            "owner_id",
            "run_id",
            "trial_id",
            "parent_accepted_state_id",
            "token_version",
        ):
            _nonempty(getattr(self, name), name)
        _hash(self.parent_state_hash, "parent_state_hash")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class ResidualBlock(SemanticContract):
    __semantic_kind__ = "residual_block"

    block_id: str
    owner_id: str
    kind: ResidualKind
    physical_semantics: str
    raw_values: tuple[float, ...]
    raw_unit: str
    reduction_norm: ReductionNorm
    raw_norm: float
    reference_norm: float
    absolute_tolerance: float
    relative_tolerance: float
    scale_id: str
    scale_value: float
    normalized_norm: float
    hard_acceptance: bool
    branch_ref: str
    entity_refs: tuple[str, ...]
    metadata: ContractMetadata

    @classmethod
    def from_values(
        cls,
        *,
        block_id: str,
        owner_id: str,
        kind: ResidualKind,
        physical_semantics: str,
        raw_values: tuple[float, ...],
        raw_unit: str,
        reduction_norm: ReductionNorm = ReductionNorm.L2,
        reference_norm: float,
        absolute_tolerance: float,
        relative_tolerance: float,
        scale_id: str,
        scale_value: float,
        hard_acceptance: bool = True,
        branch_ref: str = "OWNER_DECLARED",
        entity_refs: tuple[str, ...] = (),
        **metadata_values: Any,
    ) -> ResidualBlock:
        _positive(scale_value, "scale_value")
        norm = _norm(raw_values, reduction_norm)
        return cls.create(
            block_id=block_id,
            owner_id=owner_id,
            kind=kind,
            physical_semantics=physical_semantics,
            raw_values=raw_values,
            raw_unit=raw_unit,
            reduction_norm=reduction_norm,
            raw_norm=norm,
            reference_norm=reference_norm,
            absolute_tolerance=absolute_tolerance,
            relative_tolerance=relative_tolerance,
            scale_id=scale_id,
            scale_value=scale_value,
            normalized_norm=norm / scale_value,
            hard_acceptance=hard_acceptance,
            branch_ref=branch_ref,
            entity_refs=entity_refs,
            metadata_unit=raw_unit,
            **metadata_values,
        )

    @property
    def accepted(self) -> bool:
        return (
            self.raw_norm <= self.absolute_tolerance + self.relative_tolerance * self.reference_norm
        )

    def __post_init__(self) -> None:
        _nonempty(self.block_id, "block_id")
        _nonempty(self.owner_id, "owner_id")
        _nonempty(self.physical_semantics, "physical_semantics")
        _nonempty(self.raw_unit, "raw_unit")
        _enum(self.kind, ResidualKind, "kind")
        _enum(self.reduction_norm, ReductionNorm, "reduction_norm")
        if not self.raw_values:
            raise ContractViolation("ResidualBlock.raw_values cannot be empty")
        for index, value in enumerate(self.raw_values):
            _finite(value, f"raw_values[{index}]")
        expected_norm = _norm(self.raw_values, self.reduction_norm)
        _close(self.raw_norm, expected_norm, "raw_norm")
        _nonnegative(self.reference_norm, "reference_norm")
        _nonnegative(self.absolute_tolerance, "absolute_tolerance")
        _nonnegative(self.relative_tolerance, "relative_tolerance")
        _nonempty(self.scale_id, "scale_id")
        _positive(self.scale_value, "scale_value")
        _close(self.normalized_norm, expected_norm / self.scale_value, "normalized_norm")
        _unique(self.entity_refs, "entity_refs")
        _nonempty(self.branch_ref, "branch_ref")
        if self.kind is ResidualKind.MOMENT_EQUILIBRIUM and self.raw_unit != "N*mm":
            raise ContractViolation("moment residual blocks require raw unit N*mm")
        if self.kind is ResidualKind.FORCE_EQUILIBRIUM and self.raw_unit != "N":
            raise ContractViolation("force residual blocks require raw unit N")
        if self.kind is ResidualKind.KINEMATIC_COMPATIBILITY and self.raw_unit not in {
            "mm",
            "rad",
        }:
            raise ContractViolation("kinematic residual requires mm or rad")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class HardInequalityQuality(SemanticContract):
    __semantic_kind__ = "hard_inequality_quality"

    quality_id: str
    owner_id: str
    semantics: str
    raw_margin: float
    raw_unit: str
    absolute_tolerance: float
    scale_id: str
    scale_value: float
    normalized_violation: float
    passed: bool
    entity_refs: tuple[str, ...]
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        _nonempty(self.quality_id, "quality_id")
        _nonempty(self.owner_id, "owner_id")
        _nonempty(self.semantics, "semantics")
        _finite(self.raw_margin, "raw_margin")
        _nonempty(self.raw_unit, "raw_unit")
        _nonnegative(self.absolute_tolerance, "absolute_tolerance")
        _nonempty(self.scale_id, "scale_id")
        _positive(self.scale_value, "scale_value")
        expected = max(-(self.raw_margin + self.absolute_tolerance), 0.0) / self.scale_value
        _close(self.normalized_violation, expected, "normalized_violation")
        if self.passed != (self.raw_margin >= -self.absolute_tolerance):
            raise ContractViolation("hard inequality pass flag conflicts with raw margin")
        _unique(self.entity_refs, "entity_refs")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class ComplementarityQuality(SemanticContract):
    __semantic_kind__ = "complementarity_quality"

    quality_id: str
    owner_id: str
    primal_violation: float
    dual_violation: float
    complementarity_residual: float
    primal_unit: str
    dual_unit: str
    complementarity_unit: str
    scale_id: str
    scale_value: float
    normalized_norm: float
    absolute_tolerance: float
    relative_tolerance: float
    reference_norm: float
    hard_acceptance: bool
    active_branch: str
    metadata: ContractMetadata

    @property
    def accepted(self) -> bool:
        return (
            self.normalized_norm
            <= self.absolute_tolerance + self.relative_tolerance * self.reference_norm
        )

    def __post_init__(self) -> None:
        _nonempty(self.quality_id, "quality_id")
        _nonempty(self.owner_id, "owner_id")
        for name in ("primal_violation", "dual_violation", "complementarity_residual"):
            _nonnegative(getattr(self, name), name)
        for name in ("primal_unit", "dual_unit", "complementarity_unit", "scale_id"):
            _nonempty(getattr(self, name), name)
        _positive(self.scale_value, "scale_value")
        expected = (
            max(
                self.primal_violation,
                self.dual_violation,
                self.complementarity_residual,
            )
            / self.scale_value
        )
        _close(self.normalized_norm, expected, "normalized_norm")
        _nonnegative(self.absolute_tolerance, "absolute_tolerance")
        _nonnegative(self.relative_tolerance, "relative_tolerance")
        _nonnegative(self.reference_norm, "reference_norm")
        _nonempty(self.active_branch, "active_branch")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class GraphQuality(SemanticContract):
    __semantic_kind__ = "graph_quality"

    quality_id: str
    owner_id: str
    graph_id: str
    raw_distance: float
    raw_unit: str
    scale_id: str
    scale_value: float
    normalized_distance: float
    absolute_tolerance: float
    relative_tolerance: float
    reference_norm: float
    hard_acceptance: bool
    active_branch: str
    set_valued: bool
    degenerate: bool
    rank: int | None
    nullspace_dimension: int | None
    metadata: ContractMetadata

    @property
    def accepted(self) -> bool:
        return (
            self.normalized_distance
            <= self.absolute_tolerance + self.relative_tolerance * self.reference_norm
        )

    def __post_init__(self) -> None:
        for name in ("quality_id", "owner_id", "graph_id", "raw_unit", "scale_id", "active_branch"):
            _nonempty(getattr(self, name), name)
        _nonnegative(self.raw_distance, "raw_distance")
        _positive(self.scale_value, "scale_value")
        _close(
            self.normalized_distance, self.raw_distance / self.scale_value, "normalized_distance"
        )
        for name in ("absolute_tolerance", "relative_tolerance", "reference_norm"):
            _nonnegative(getattr(self, name), name)
        if self.rank is not None:
            _nonnegative_int(self.rank, "rank")
        if self.nullspace_dimension is not None:
            _nonnegative_int(self.nullspace_dimension, "nullspace_dimension")
        if self.degenerate and not (self.set_valued or (self.nullspace_dimension or 0) > 0):
            raise ContractViolation("degenerate graph requires set-valued or nullspace evidence")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class DerivativeCapability(SemanticContract):
    __semantic_kind__ = "derivative_capability"

    capability_id: str
    owner_id: str
    owner_version: str
    kind: DerivativeKind
    nonsmooth_supported: bool
    production_safe: bool
    derivative_hash: str
    branch_scope: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in ("capability_id", "owner_id", "owner_version", "branch_scope"):
            _nonempty(getattr(self, name), name)
        _enum(self.kind, DerivativeKind, "kind")
        _hash(self.derivative_hash, "derivative_hash")
        if self.kind is DerivativeKind.FINITE_DIFFERENCE_VALIDATION_ONLY and self.production_safe:
            raise ContractViolation("finite differences cannot be declared production-safe")
        if self.nonsmooth_supported and self.kind not in {
            DerivativeKind.GENERALIZED_JACOBIAN,
            DerivativeKind.JACOBIAN_VECTOR_PRODUCT,
            DerivativeKind.VERSIONED_TANGENT,
        }:
            raise ContractViolation(
                "nonsmooth production needs a generalized derivative capability"
            )
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class PhysicalEvaluationRequest(SemanticContract):
    __semantic_kind__ = "physical_evaluation_request"

    request_id: str
    trial_step: TrialStep
    immutable_parent_snapshot_refs: tuple[str, ...]
    evaluation_purpose: str
    requested_continuation_coordinate: float
    unknown_iterate: tuple[float, ...]
    unknown_units: tuple[str, ...]
    active_branch_request_refs: tuple[str, ...]
    required_residual_block_ids: tuple[str, ...]
    required_event_channel_ids: tuple[str, ...]
    required_quality_ids: tuple[str, ...]
    dependency_coverage_refs: tuple[str, ...]
    diagnostic_level: DiagnosticLevel
    replay_decision_context_hash: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        _nonempty(self.request_id, "request_id")
        _unique_nonempty(self.immutable_parent_snapshot_refs, "immutable_parent_snapshot_refs")
        _nonempty(self.evaluation_purpose, "evaluation_purpose")
        _enum(self.diagnostic_level, DiagnosticLevel, "diagnostic_level")
        _finite(self.requested_continuation_coordinate, "requested_continuation_coordinate")
        if len(self.unknown_iterate) != len(self.unknown_units):
            raise ContractViolation("unknown iterate and unit metadata lengths differ")
        for index, value in enumerate(self.unknown_iterate):
            _finite(value, f"unknown_iterate[{index}]")
        for index, unit in enumerate(self.unknown_units):
            _nonempty(unit, f"unknown_units[{index}]")
        for name in (
            "active_branch_request_refs",
            "required_residual_block_ids",
            "required_event_channel_ids",
            "required_quality_ids",
            "dependency_coverage_refs",
        ):
            _unique(getattr(self, name), name)
        _hash(self.replay_decision_context_hash, "replay_decision_context_hash")
        if self.trial_step.parent_accepted_state_id not in self.immutable_parent_snapshot_refs:
            raise ContractViolation(
                "evaluation request does not reference the trial parent snapshot"
            )
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class GuardSample(SemanticContract):
    __semantic_kind__ = "guard_sample"

    sample_id: str
    channel_id: str
    trial_id: str
    oriented_path_position_mm: float
    trial_fraction: float
    raw_guard_value: float
    raw_guard_unit: str
    equilibrium_quality_passed: bool
    quality_hashes: tuple[str, ...]
    owner_response_hash: str
    balance_response_hash: str | None
    balance_recomputed: bool
    coverage_refs: tuple[str, ...]
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in ("sample_id", "channel_id", "trial_id", "raw_guard_unit"):
            _nonempty(getattr(self, name), name)
        _finite(self.oriented_path_position_mm, "oriented_path_position_mm")
        _bounded(self.trial_fraction, 0.0, 1.0, "trial_fraction")
        _finite(self.raw_guard_value, "raw_guard_value")
        _hash(self.owner_response_hash, "owner_response_hash")
        if self.balance_response_hash is not None:
            _hash(self.balance_response_hash, "balance_response_hash")
        for item in self.quality_hashes:
            _hash(item, "quality_hash")
        _unique(self.coverage_refs, "coverage_refs")
        if not self.equilibrium_quality_passed:
            raise ContractViolation(
                "an unconverged equilibrium cannot be a legal event guard sample"
            )
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class ProvisionalIntent(SemanticContract):
    __semantic_kind__ = "provisional_intent"

    intent_id: str
    owner_id: str
    intent_kind: str
    payload_hash: str
    read_set: tuple[str, ...]
    write_set: tuple[str, ...]
    dependency_versions: tuple[str, ...]
    zero_progress: bool
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in ("intent_id", "owner_id", "intent_kind"):
            _nonempty(getattr(self, name), name)
        _hash(self.payload_hash, "payload_hash")
        _unique(self.read_set, "read_set")
        _unique(self.write_set, "write_set")
        _unique(self.dependency_versions, "dependency_versions")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class PhysicalEvaluationResponse(SemanticContract):
    __semantic_kind__ = "physical_evaluation_response"

    response_id: str
    request_id: str
    request_hash: str
    owner_id: str
    owner_version: str
    opaque_trial_state_ref: OpaqueTrialStateRef
    rollback_token: RollbackToken
    unknown_vector: tuple[float, ...]
    unknown_units: tuple[str, ...]
    residual_blocks: tuple[ResidualBlock, ...]
    derivative_capability: DerivativeCapability
    hard_inequalities: tuple[HardInequalityQuality, ...]
    complementarity_qualities: tuple[ComplementarityQuality, ...]
    graph_qualities: tuple[GraphQuality, ...]
    guard_samples: tuple[GuardSample, ...]
    provisional_intents: tuple[ProvisionalIntent, ...]
    surface_realization_refs: tuple[str, ...]
    surface_coverage_refs: tuple[str, ...]
    physical_feasibility_proof_ref: str | None
    capability_status: CapabilityStatus
    status: StatusTuple
    determinism_hash: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in ("response_id", "request_id", "owner_id", "owner_version"):
            _nonempty(getattr(self, name), name)
        _hash(self.request_hash, "request_hash")
        _hash(self.determinism_hash, "determinism_hash")
        _enum(self.capability_status, CapabilityStatus, "capability_status")
        if len(self.unknown_vector) != len(self.unknown_units):
            raise ContractViolation("response unknown vector/unit lengths differ")
        for index, value in enumerate(self.unknown_vector):
            _finite(value, f"unknown_vector[{index}]")
        _unique_by(self.residual_blocks, lambda item: item.block_id, "residual block IDs")
        _unique_by(self.hard_inequalities, lambda item: item.quality_id, "inequality IDs")
        _unique_by(
            self.complementarity_qualities,
            lambda item: item.quality_id,
            "complementarity IDs",
        )
        _unique_by(self.graph_qualities, lambda item: item.quality_id, "graph IDs")
        _unique_by(self.guard_samples, lambda item: item.channel_id, "guard channel IDs")
        _unique_by(self.provisional_intents, lambda item: item.intent_id, "intent IDs")
        _unique(self.surface_realization_refs, "surface_realization_refs")
        _unique(self.surface_coverage_refs, "surface_coverage_refs")
        if self.opaque_trial_state_ref.owner_id != self.owner_id:
            raise ContractViolation("opaque state owner does not match evaluation response")
        if self.rollback_token.owner_id != self.owner_id:
            raise ContractViolation("rollback token owner does not match evaluation response")
        if (
            self.status.physical_feasibility is PhysicalFeasibility.PHYSICAL_INFEASIBLE
            and not self.physical_feasibility_proof_ref
        ):
            raise ContractViolation("physical infeasibility requires an owner proof reference")
        if self.status.capability_status is not self.capability_status:
            raise ContractViolation("owner response capability axis conflicts with its status")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class EventChannelRegistration(SemanticContract):
    __semantic_kind__ = "event_channel_registration"

    channel_id: str
    owner_id: str
    entity_ids: tuple[str, ...]
    event_kind: str
    guard_id: str
    guard_version: str
    raw_guard_unit: str
    zero_level: float
    admissible_side: EventAdmissibleSide
    trigger_direction: EventTriggerDirection
    applicability_predicate_id: str
    branch_state_scope: tuple[str, ...]
    detection_mode: EventDetectionMode
    no_event_certificate_capabilities: tuple[EventCertificateKind, ...]
    dependency_predecessors: tuple[str, ...]
    transition_owner: str
    post_event_side_request_id: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in (
            "channel_id",
            "owner_id",
            "event_kind",
            "guard_id",
            "guard_version",
            "raw_guard_unit",
            "applicability_predicate_id",
            "transition_owner",
            "post_event_side_request_id",
        ):
            _nonempty(getattr(self, name), name)
        _finite(self.zero_level, "zero_level")
        _enum(self.admissible_side, EventAdmissibleSide, "admissible_side")
        _enum(self.trigger_direction, EventTriggerDirection, "trigger_direction")
        _enum(self.detection_mode, EventDetectionMode, "detection_mode")
        _unique_nonempty(self.entity_ids, "entity_ids")
        _unique(self.branch_state_scope, "branch_state_scope")
        _unique(self.no_event_certificate_capabilities, "certificate capabilities")
        for capability in self.no_event_certificate_capabilities:
            _enum(capability, EventCertificateKind, "certificate capability")
        _unique(self.dependency_predecessors, "dependency_predecessors")
        if self.channel_id in self.dependency_predecessors:
            raise ContractViolation("event channel dependency cannot be a self-loop")
        if (
            self.trigger_direction is EventTriggerDirection.TOUCH
            and EventCertificateKind.STATIONARY_TOUCH_ENCLOSURE
            not in self.no_event_certificate_capabilities
        ):
            raise ContractViolation("TOUCH channel requires stationary/enclosure capability")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class EventProbeRequest(SemanticContract):
    __semantic_kind__ = "event_probe_request"

    probe_id: str
    trial_step: TrialStep
    parent_accepted_state_id: str
    branch_ref: str
    channel_ids: tuple[str, ...]
    required_equilibrium_quality_ids: tuple[str, ...]
    coverage_request_refs: tuple[str, ...]
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        _nonempty(self.probe_id, "probe_id")
        _nonempty(self.parent_accepted_state_id, "parent_accepted_state_id")
        _nonempty(self.branch_ref, "branch_ref")
        _unique_nonempty(self.channel_ids, "channel_ids")
        _unique(self.required_equilibrium_quality_ids, "required_equilibrium_quality_ids")
        if self.trial_step.phase not in {
            TrialPhase.EVENT_PROBE,
            TrialPhase.EVENT_POINT,
            TrialPhase.POST_EVENT_SIDE,
            TrialPhase.CASCADE_ROUND,
        }:
            raise ContractViolation("EventProbeRequest requires an event-related TrialPhase")
        if self.trial_step.parent_accepted_state_id != self.parent_accepted_state_id:
            raise ContractViolation("event probe parent does not match trial parent")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class EventProbeResult(SemanticContract):
    __semantic_kind__ = "event_probe_result"

    probe_id: str
    request_hash: str
    trial_id: str
    oriented_path_position_mm: float
    trial_fraction: float
    equilibrium_response_hash: str
    equilibrium_quality_passed: bool
    guard_samples: tuple[GuardSample, ...]
    coverage_certificate_refs: tuple[str, ...]
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        _nonempty(self.probe_id, "probe_id")
        _hash(self.request_hash, "request_hash")
        _nonempty(self.trial_id, "trial_id")
        _finite(self.oriented_path_position_mm, "oriented_path_position_mm")
        _bounded(self.trial_fraction, 0.0, 1.0, "trial_fraction")
        _hash(self.equilibrium_response_hash, "equilibrium_response_hash")
        if not self.equilibrium_quality_passed:
            raise ContractViolation(
                "event probe result is illegal until equilibrium quality passes"
            )
        _unique_by(self.guard_samples, lambda item: item.channel_id, "guard channel IDs")
        for sample in self.guard_samples:
            _close(
                sample.oriented_path_position_mm, self.oriented_path_position_mm, "sample position"
            )
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class EventBracket(SemanticContract):
    __semantic_kind__ = "event_bracket"

    bracket_id: str
    channel_id: str
    left_position_mm: float
    right_position_mm: float
    left_guard_value: float
    right_guard_value: float
    guard_unit: str
    root_method: EventRootMethod
    touch_enclosure: bool
    coverage_certificate_ref: str
    probe_ids: tuple[str, ...]
    iterations: int
    localization_error_mm: float
    converged: bool
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in ("bracket_id", "channel_id", "guard_unit", "coverage_certificate_ref"):
            _nonempty(getattr(self, name), name)
        _finite(self.left_position_mm, "left_position_mm")
        _finite(self.right_position_mm, "right_position_mm")
        if self.right_position_mm < self.left_position_mm:
            raise ContractViolation("event bracket endpoints are reversed")
        _finite(self.left_guard_value, "left_guard_value")
        _finite(self.right_guard_value, "right_guard_value")
        _enum(self.root_method, EventRootMethod, "root_method")
        _nonnegative_int(self.iterations, "iterations")
        _nonnegative(self.localization_error_mm, "localization_error_mm")
        _unique_nonempty(self.probe_ids, "probe_ids")
        if not self.touch_enclosure and self.left_guard_value * self.right_guard_value > 0.0:
            raise ContractViolation(
                "non-touch event bracket must preserve a sign change or endpoint root"
            )
        if self.touch_enclosure and self.root_method is not EventRootMethod.TOUCH_ENCLOSURE:
            raise ContractViolation("touch enclosure requires TOUCH_ENCLOSURE root method")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class EventEarliestnessCertificate(SemanticContract):
    __semantic_kind__ = "event_earliestness_certificate"

    certificate_id: str
    interval_start_mm: float
    candidate_left_mm: float
    applicable_channel_ids: tuple[str, ...]
    covered_channel_ids: tuple[str, ...]
    coverage_certificate_refs: tuple[str, ...]
    no_earlier_event_proven: bool
    proof_hash: str
    explanation: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        _nonempty(self.certificate_id, "certificate_id")
        _finite(self.interval_start_mm, "interval_start_mm")
        _finite(self.candidate_left_mm, "candidate_left_mm")
        if self.candidate_left_mm < self.interval_start_mm:
            raise ContractViolation("earliest candidate lies before certificate interval")
        _unique(self.applicable_channel_ids, "applicable_channel_ids")
        _unique(self.covered_channel_ids, "covered_channel_ids")
        _unique(self.coverage_certificate_refs, "coverage_certificate_refs")
        _hash(self.proof_hash, "proof_hash")
        _nonempty(self.explanation, "explanation")
        if self.no_earlier_event_proven and set(self.applicable_channel_ids) != set(
            self.covered_channel_ids
        ):
            raise ContractViolation(
                "earliestness cannot be proven with incomplete channel coverage"
            )
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class LocatedEventGroup(SemanticContract):
    __semantic_kind__ = "located_event_group"

    located_group_id: str
    oriented_path_position_mm: float
    localization_tolerance_mm: float
    channel_ids: tuple[str, ...]
    bracket_ids: tuple[str, ...]
    event_probe_ids: tuple[str, ...]
    earliestness_certificate: EventEarliestnessCertificate
    pre_event_response_hash: str
    event_point_response_hash: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        _nonempty(self.located_group_id, "located_group_id")
        _finite(self.oriented_path_position_mm, "oriented_path_position_mm")
        _positive(self.localization_tolerance_mm, "localization_tolerance_mm")
        _unique_nonempty(self.channel_ids, "channel_ids")
        _unique_nonempty(self.bracket_ids, "bracket_ids")
        _unique_nonempty(self.event_probe_ids, "event_probe_ids")
        _hash(self.pre_event_response_hash, "pre_event_response_hash")
        _hash(self.event_point_response_hash, "event_point_response_hash")
        if not self.earliestness_certificate.no_earlier_event_proven:
            raise ContractViolation("located event group requires a closed earliestness proof")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class EventDependencyEdge(SemanticContract):
    __semantic_kind__ = "event_dependency_edge"

    edge_id: str
    predecessor_channel_id: str
    successor_channel_id: str
    dependency_kind: str
    owner_id: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in (
            "edge_id",
            "predecessor_channel_id",
            "successor_channel_id",
            "dependency_kind",
            "owner_id",
        ):
            _nonempty(getattr(self, name), name)
        if self.predecessor_channel_id == self.successor_channel_id:
            raise ContractViolation("event dependency cannot be a self-loop")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class SimultaneousEventGroup(SemanticContract):
    __semantic_kind__ = "simultaneous_event_group"

    simultaneous_group_id: str
    oriented_path_position_mm: float
    simultaneous_tolerance_mm: float
    located_group_ids: tuple[str, ...]
    channel_ids: tuple[str, ...]
    dependency_edges: tuple[EventDependencyEdge, ...]
    canonical_independent_order: tuple[str, ...]
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        _nonempty(self.simultaneous_group_id, "simultaneous_group_id")
        _finite(self.oriented_path_position_mm, "oriented_path_position_mm")
        _positive(self.simultaneous_tolerance_mm, "simultaneous_tolerance_mm")
        _unique_nonempty(self.located_group_ids, "located_group_ids")
        _unique_nonempty(self.channel_ids, "channel_ids")
        _unique_by(self.dependency_edges, lambda item: item.edge_id, "dependency edge IDs")
        if set(self.canonical_independent_order) != set(self.channel_ids):
            raise ContractViolation("canonical simultaneous order must contain every channel once")
        order = {
            channel_id: index for index, channel_id in enumerate(self.canonical_independent_order)
        }
        for edge in self.dependency_edges:
            if edge.predecessor_channel_id not in order or edge.successor_channel_id not in order:
                raise ContractViolation(
                    "event dependency endpoint is outside its simultaneous group"
                )
            if order[edge.predecessor_channel_id] >= order[edge.successor_channel_id]:
                raise ContractViolation(
                    "simultaneous event dependency order contains a cycle/conflict"
                )
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class CascadeRound(SemanticContract):
    __semantic_kind__ = "cascade_round"

    cascade_id: str
    round_index: int
    event_coordinate_mm: float
    state_hash: str
    event_signature_hash: str
    event_channel_ids: tuple[str, ...]
    transition_intent_ids: tuple[str, ...]
    guard_margin_improvement: float
    equilibrium_response_hash: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        _nonempty(self.cascade_id, "cascade_id")
        _nonnegative_int(self.round_index, "round_index")
        _finite(self.event_coordinate_mm, "event_coordinate_mm")
        for name in ("state_hash", "event_signature_hash", "equilibrium_response_hash"):
            _hash(getattr(self, name), name)
        _unique(self.event_channel_ids, "event_channel_ids")
        _unique(self.transition_intent_ids, "transition_intent_ids")
        _finite(self.guard_margin_improvement, "guard_margin_improvement")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class ReturnPathCapability(SemanticContract):
    __semantic_kind__ = "return_path_capability"

    owner_id: str
    release_event_id: str
    mode: ReturnPathMode
    path_mapping_id: str | None
    pose_path_ref: str | None
    swept_geometry_ref: str | None
    reason_code: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        _nonempty(self.owner_id, "owner_id")
        _nonempty(self.release_event_id, "release_event_id")
        _nonempty(self.reason_code, "reason_code")
        _enum(self.mode, ReturnPathMode, "mode")
        refs = (self.path_mapping_id, self.pose_path_ref, self.swept_geometry_ref)
        if self.mode is ReturnPathMode.EXPLICIT_RETURN_PATH:
            if not all(refs):
                raise ContractViolation(
                    "explicit return path requires mapping, pose path, and sweep refs"
                )
        elif any(refs):
            raise ContractViolation("non-explicit return path cannot carry an implicit trajectory")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class OrderedIntentBatch(SemanticContract):
    __semantic_kind__ = "ordered_intent_batch"

    batch_id: str
    intents: tuple[ProvisionalIntent, ...]
    dependency_order: tuple[str, ...]
    conflicts_resolved: bool
    damage_store_parent_version: str | None
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        _nonempty(self.batch_id, "batch_id")
        _unique_by(self.intents, lambda item: item.intent_id, "intent IDs")
        if tuple(item.intent_id for item in self.intents) != self.dependency_order:
            raise ContractViolation("ordered intent batch order does not match its intents")
        if not self.conflicts_resolved:
            raise ContractViolation("unresolved intent conflicts cannot enter a prepared candidate")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class PreparedCandidate(SemanticContract):
    __semantic_kind__ = "prepared_candidate"

    candidate_id: str
    target_id: str
    trial_id: str
    parent_accepted_state_id: str
    parent_commit_receipt_id: str
    parent_state_hash: str
    final_opaque_state_refs: tuple[str, ...]
    final_state_hash: str
    ordered_intent_batch: OrderedIntentBatch
    rollback_tokens: tuple[RollbackToken, ...]
    located_event_group_refs: tuple[str, ...]
    numerical_quality_hashes: tuple[str, ...]
    registry_hash: str
    config_hash: str
    owner_build_hashes: tuple[str, ...]
    event_coverage_complete: bool
    earliestness_complete: bool
    post_event_side_complete: bool
    quality_complete: bool
    persistence_ready: bool
    idempotency_key: str
    proposed_accepted_point_id: str
    proposed_committed_event_ids: tuple[str, ...]
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in (
            "candidate_id",
            "target_id",
            "trial_id",
            "parent_accepted_state_id",
            "parent_commit_receipt_id",
            "idempotency_key",
            "proposed_accepted_point_id",
        ):
            _nonempty(getattr(self, name), name)
        for name in ("parent_state_hash", "final_state_hash", "registry_hash", "config_hash"):
            _hash(getattr(self, name), name)
        _unique_nonempty(self.final_opaque_state_refs, "final_opaque_state_refs")
        _unique_by(self.rollback_tokens, lambda item: item.token_ref, "rollback token refs")
        _unique(self.located_event_group_refs, "located_event_group_refs")
        _unique(self.proposed_committed_event_ids, "proposed_committed_event_ids")
        for value in (*self.numerical_quality_hashes, *self.owner_build_hashes):
            _hash(value, "candidate dependency hash")
        gates = {
            "event_coverage_complete": self.event_coverage_complete,
            "earliestness_complete": self.earliestness_complete,
            "post_event_side_complete": self.post_event_side_complete,
            "quality_complete": self.quality_complete,
            "persistence_ready": self.persistence_ready,
        }
        if not all(gates.values()):
            raise ContractViolation(
                "candidate cannot be frozen before every prepare gate passes",
                details={key: value for key, value in gates.items() if not value},
            )
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class PrepareTokenRef(SemanticContract):
    __semantic_kind__ = "prepare_token_ref"

    token_ref: str
    candidate_id: str
    candidate_hash: str
    parent_accepted_state_id: str
    idempotency_key: str
    expires_at_monotonic_ns: int | None
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in ("token_ref", "candidate_id", "parent_accepted_state_id", "idempotency_key"):
            _nonempty(getattr(self, name), name)
        _hash(self.candidate_hash, "candidate_hash")
        if self.expires_at_monotonic_ns is not None:
            _positive_int(self.expires_at_monotonic_ns, "expires_at_monotonic_ns")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class CommitReceiptRef(SemanticContract):
    """A reference to, never a competing copy of, ``CommitReceiptBase``."""

    __semantic_kind__ = "commit_receipt_ref"

    receipt_id: str
    committed_state_id: str
    candidate_hash: str
    commit_marker_hash: str
    core_receipt_dataset_id: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        _nonempty(self.receipt_id, "receipt_id")
        _nonempty(self.committed_state_id, "committed_state_id")
        _hash(self.candidate_hash, "candidate_hash")
        _hash(self.commit_marker_hash, "commit_marker_hash")
        if self.core_receipt_dataset_id != "core.transactions.receipts":
            raise ContractViolation("M02 receipt refs must point to the M00 core receipt dataset")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class FailureDiagnostic(SemanticContract):
    __semantic_kind__ = "failure_diagnostic"

    failure_id: str
    family: FailureFamily
    reason_code: str
    stage: str
    parent_accepted_state_id: str
    last_valid_state_id: str
    owner_proof_ref: str | None
    original_reason_code: str | None
    structured_details: tuple[tuple[str, str], ...]
    retryable: bool
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in (
            "failure_id",
            "reason_code",
            "stage",
            "parent_accepted_state_id",
            "last_valid_state_id",
        ):
            _nonempty(getattr(self, name), name)
        _enum(self.family, FailureFamily, "family")
        keys = tuple(item[0] for item in self.structured_details)
        _unique(keys, "structured detail keys")
        if self.family is FailureFamily.PHYSICAL_INFEASIBLE and not self.owner_proof_ref:
            raise ContractViolation("M02 cannot emit PHYSICAL_INFEASIBLE without owner proof")
        if self.family is not FailureFamily.PHYSICAL_INFEASIBLE and self.owner_proof_ref:
            raise ContractViolation("owner physical proof is only valid for PHYSICAL_INFEASIBLE")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class ReplayDecisionRecord(SemanticContract):
    __semantic_kind__ = "replay_decision_record"

    decision_id: str
    case_id: str
    target_id: str
    trial_id: str | None
    sequence_index: int
    decision_kind: str
    input_hash: str
    output_hash: str
    parent_decision_hash: str | None
    payload: tuple[tuple[str, str], ...]
    backend_profile_hash: str
    diagnostic_level: DiagnosticLevel
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in ("decision_id", "case_id", "target_id", "decision_kind"):
            _nonempty(getattr(self, name), name)
        _nonnegative_int(self.sequence_index, "sequence_index")
        _enum(self.diagnostic_level, DiagnosticLevel, "diagnostic_level")
        for name in ("input_hash", "output_hash", "backend_profile_hash"):
            _hash(getattr(self, name), name)
        if self.parent_decision_hash is not None:
            _hash(self.parent_decision_hash, "parent_decision_hash")
        _unique(tuple(item[0] for item in self.payload), "replay payload keys")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class ContinuationAdvanceRequest(SemanticContract):
    __semantic_kind__ = "continuation_advance_request"

    request_id: str
    target: ContinuationTarget
    session: ContinuationSession
    parent_accepted_state_id: str
    parent_commit_receipt_id: str
    parent_state_hash: str
    diagnostic_level: DiagnosticLevel
    request_hash: str
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        _nonempty(self.request_id, "request_id")
        _enum(self.diagnostic_level, DiagnosticLevel, "diagnostic_level")
        _hash(self.parent_state_hash, "parent_state_hash")
        _hash(self.request_hash, "request_hash")
        if self.target.target_id != self.session.target_id:
            raise ContractViolation("advance session does not belong to target")
        identities = {self.session.parent_accepted_state_id, self.parent_accepted_state_id}
        receipts = {self.session.parent_commit_receipt_id, self.parent_commit_receipt_id}
        if len(identities) != 1 or len(receipts) != 1:
            raise ContractViolation("advance request contains a stale/conflicting parent")
        if self.session.accepted_step_count == 0 and (
            self.target.parent_accepted_state_id != self.parent_accepted_state_id
            or self.target.parent_commit_receipt_id != self.parent_commit_receipt_id
            or self.target.parent_state_hash != self.parent_state_hash
        ):
            raise ContractViolation("first target advance does not use the immutable target parent")
        self._validate_metadata()


@dataclass(frozen=True, slots=True)
class ContinuationAdvanceResponse(SemanticContract):
    __semantic_kind__ = "continuation_advance_response"

    response_id: str
    request_id: str
    outcome: AdvanceOutcome
    target_id: str
    parent_accepted_state_id: str
    accepted_point_id: str | None
    committed_event_ids: tuple[str, ...]
    commit_receipt_ref: CommitReceiptRef | None
    next_session: ContinuationSession
    suggested_next_step_mm: float | None
    failure: FailureDiagnostic | None
    status: StatusTuple
    metadata: ContractMetadata

    def __post_init__(self) -> None:
        for name in ("response_id", "request_id", "target_id", "parent_accepted_state_id"):
            _nonempty(getattr(self, name), name)
        _enum(self.outcome, AdvanceOutcome, "outcome")
        if self.suggested_next_step_mm is not None:
            _positive(self.suggested_next_step_mm, "suggested_next_step_mm")
        committed = self.outcome in {
            AdvanceOutcome.ACCEPTED_STEP,
            AdvanceOutcome.COMMITTED_EVENT_STEP,
        }
        if committed != (
            self.accepted_point_id is not None and self.commit_receipt_ref is not None
        ):
            raise ContractViolation(
                "accepted advance requires both core point and receipt references"
            )
        if self.outcome is AdvanceOutcome.COMMITTED_EVENT_STEP and not self.committed_event_ids:
            raise ContractViolation("committed event advance requires core committed event IDs")
        if self.outcome is not AdvanceOutcome.COMMITTED_EVENT_STEP and self.committed_event_ids:
            raise ContractViolation("non-event advance cannot own committed event IDs")
        failure_outcome = self.outcome in {
            AdvanceOutcome.REJECTED_RETRYABLE,
            AdvanceOutcome.TERMINAL_FAILURE,
            AdvanceOutcome.UNAVAILABLE,
            AdvanceOutcome.UNSUPPORTED,
        }
        if failure_outcome != (self.failure is not None):
            raise ContractViolation("advance failure variants require a structured diagnostic")
        self._validate_metadata()


def validate_trial_transition(before: TrialLifecycleState, after: TrialLifecycleState) -> None:
    """Reject lifecycle transitions that could publish or resurrect a trial illegally."""

    allowed: dict[TrialLifecycleState, frozenset[TrialLifecycleState]] = {
        TrialLifecycleState.TRIAL_CREATED: frozenset(
            {
                TrialLifecycleState.OWNER_EVALUATED,
                TrialLifecycleState.ROLLED_BACK,
                TrialLifecycleState.REJECTED,
            }
        ),
        TrialLifecycleState.OWNER_EVALUATED: frozenset(
            {
                TrialLifecycleState.NUMERICALLY_ELIGIBLE,
                TrialLifecycleState.ROLLED_BACK,
                TrialLifecycleState.REJECTED,
            }
        ),
        TrialLifecycleState.NUMERICALLY_ELIGIBLE: frozenset(
            {
                TrialLifecycleState.EVENT_COMPLETE,
                TrialLifecycleState.ROLLED_BACK,
                TrialLifecycleState.REJECTED,
            }
        ),
        TrialLifecycleState.EVENT_COMPLETE: frozenset(
            {
                TrialLifecycleState.CANDIDATE_FROZEN,
                TrialLifecycleState.ROLLED_BACK,
                TrialLifecycleState.REJECTED,
            }
        ),
        TrialLifecycleState.CANDIDATE_FROZEN: frozenset(
            {
                TrialLifecycleState.PREPARED,
                TrialLifecycleState.ROLLED_BACK,
                TrialLifecycleState.REJECTED,
            }
        ),
        TrialLifecycleState.PREPARED: frozenset(
            {TrialLifecycleState.COMMITTED, TrialLifecycleState.ROLLED_BACK}
        ),
        TrialLifecycleState.COMMITTED: frozenset(),
        TrialLifecycleState.ROLLED_BACK: frozenset(),
        TrialLifecycleState.REJECTED: frozenset(),
    }
    if after not in allowed[before]:
        raise ContractViolation(
            "illegal M02 trial lifecycle transition",
            details={"before": before.value, "after": after.value},
        )


def _resolved_payload(cls: type[Any], supplied: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    fields = {item.name: item for item in dataclasses.fields(cls)}
    unknown = set(supplied) - (set(fields) - {"metadata"})
    if unknown:
        raise ContractViolation(
            f"unknown {cls.__name__} field(s)", details={"fields": sorted(unknown)}
        )
    for name, field in fields.items():
        if name == "metadata":
            continue
        if name in supplied:
            payload[name] = supplied[name]
        elif field.default is not MISSING:
            payload[name] = field.default
        elif field.default_factory is not MISSING:
            payload[name] = field.default_factory()
        else:
            raise ContractViolation(f"missing required {cls.__name__} field: {name}")
    return payload


def _nonempty(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{name} must be a non-empty string")


def _enum(value: Any, expected: type[Any], name: str) -> None:
    if not isinstance(value, expected):
        raise ContractViolation(f"{name} must be a {expected.__name__} value")


def _hash(value: Any, name: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ContractViolation(f"{name} must be a full SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise ContractViolation(f"{name} must be hexadecimal") from error


def _finite(value: Any, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ContractViolation(f"{name} must be finite")


def _positive(value: Any, name: str) -> None:
    _finite(value, name)
    if value <= 0.0:
        raise ContractViolation(f"{name} must be positive")


def _nonnegative(value: Any, name: str) -> None:
    _finite(value, name)
    if value < 0.0:
        raise ContractViolation(f"{name} cannot be negative")


def _bounded(value: Any, lower: float, upper: float, name: str) -> None:
    _finite(value, name)
    if not lower <= value <= upper:
        raise ContractViolation(f"{name} must be in [{lower}, {upper}]")


def _nonnegative_int(value: Any, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContractViolation(f"{name} must be a non-negative integer")


def _positive_int(value: Any, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ContractViolation(f"{name} must be a positive integer")


def _unique(values: tuple[Any, ...], name: str) -> None:
    if len(set(values)) != len(values):
        raise ContractViolation(f"{name} must be unique")


def _unique_nonempty(values: tuple[str, ...], name: str) -> None:
    if not values:
        raise ContractViolation(f"{name} cannot be empty")
    for index, value in enumerate(values):
        _nonempty(value, f"{name}[{index}]")
    _unique(values, name)


def _unique_by(values: tuple[Any, ...], key: Any, name: str) -> None:
    keys = tuple(key(item) for item in values)
    _unique(keys, name)


def _norm(values: tuple[float, ...], reduction: ReductionNorm) -> float:
    absolute = tuple(abs(value) for value in values)
    if reduction is ReductionNorm.L1:
        return float(sum(absolute))
    if reduction is ReductionNorm.LINF:
        return float(max(absolute))
    return math.sqrt(sum(value * value for value in values))


def _close(actual: float, expected: float, name: str) -> None:
    _finite(actual, name)
    if not math.isclose(actual, expected, rel_tol=1.0e-12, abs_tol=1.0e-15):
        raise ContractViolation(
            f"{name} conflicts with canonical derived value",
            details={"actual": actual, "expected": expected},
        )
