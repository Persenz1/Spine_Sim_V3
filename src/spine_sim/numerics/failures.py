"""Structured M02 failure taxonomy without inferring physical infeasibility."""

from __future__ import annotations

from collections.abc import Mapping

from spine_sim.foundation.canonical import stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    AttemptOutcome,
    CapabilityStatus,
    PhysicalFeasibility,
    StatusTuple,
)

from .contracts import FailureDiagnostic, FailureFamily, M02ReasonCode


def classify_owner_failure(
    *,
    reason_code: str,
    status: StatusTuple,
    explicit_family: FailureFamily | None = None,
    owner_proof_ref: str | None = None,
) -> FailureFamily:
    """Classify an owner-declared rejection without collapsing status axes.

    M01 reason identity and an owner physical proof take precedence.  Capability
    unavailability remains represented by ``StatusTuple.capability_status``;
    the diagnostic family is only the required rejected-trial envelope.
    """

    if not reason_code.strip():
        raise ContractViolation("owner rejection requires a reason code")
    if status.reason_code != reason_code:
        raise ContractViolation("owner rejection reason conflicts with its StatusTuple")

    if reason_code.startswith("M01_"):
        inferred = FailureFamily.DOMAIN_ERROR
    elif status.physical_feasibility is PhysicalFeasibility.PHYSICAL_INFEASIBLE:
        inferred = FailureFamily.PHYSICAL_INFEASIBLE
    elif status.capability_status in {
        CapabilityStatus.UNAVAILABLE,
        CapabilityStatus.UNSUPPORTED,
        CapabilityStatus.NOT_APPLICABLE,
    }:
        # FailureDiagnostic has no capability family.  Keep the distinction on
        # the independent capability axis and use the nonphysical envelope.
        inferred = FailureFamily.CONTRACT_REJECTION
    elif status.attempt_outcome is AttemptOutcome.NUMERICAL_FAILURE:
        inferred = FailureFamily.NUMERICAL_FAILURE
    elif status.attempt_outcome is AttemptOutcome.TRANSACTION_FAILURE:
        inferred = FailureFamily.TRANSACTION_FAILURE
    else:
        inferred = FailureFamily.CONTRACT_REJECTION

    family = inferred if explicit_family is None else explicit_family
    if family is not inferred:
        raise ContractViolation(
            "explicit owner failure family conflicts with status/reason evidence"
        )
    if family is FailureFamily.PHYSICAL_INFEASIBLE and not owner_proof_ref:
        raise ContractViolation("only an owner proof can classify PHYSICAL_INFEASIBLE")
    if family is not FailureFamily.PHYSICAL_INFEASIBLE and owner_proof_ref is not None:
        raise ContractViolation("nonphysical owner rejection cannot carry a physical proof")
    return family


def make_failure_diagnostic(
    *,
    reason_code: str,
    stage: str,
    parent_accepted_state_id: str,
    last_valid_state_id: str,
    retryable: bool,
    family: FailureFamily | None = None,
    owner_proof_ref: str | None = None,
    original_reason_code: str | None = None,
    details: Mapping[str, object] | None = None,
) -> FailureDiagnostic:
    """Normalize software failures while preserving owner/M01 reason identity."""

    if reason_code.startswith("M01_"):
        if family not in {None, FailureFamily.DOMAIN_ERROR}:
            raise ContractViolation(
                "M01 domain reason cannot be remapped to another failure family"
            )
        family = FailureFamily.DOMAIN_ERROR
        original_reason_code = original_reason_code or reason_code
    if family is None:
        family = _M02_FAMILY_BY_REASON.get(reason_code)
    if family is None:
        raise ContractViolation(
            "unknown reason requires an explicit failure family",
            details={"reason_code": reason_code},
        )
    if family is FailureFamily.PHYSICAL_INFEASIBLE and not owner_proof_ref:
        raise ContractViolation("only an owner proof can classify PHYSICAL_INFEASIBLE")
    if family is not FailureFamily.PHYSICAL_INFEASIBLE and owner_proof_ref is not None:
        raise ContractViolation("nonphysical failures cannot carry a physical infeasibility proof")
    structured = tuple(sorted((str(key), str(value)) for key, value in (details or {}).items()))
    payload = {
        "reason_code": reason_code,
        "stage": stage,
        "parent": parent_accepted_state_id,
        "last_valid": last_valid_state_id,
        "family": family.value,
        "owner_proof_ref": owner_proof_ref,
        "original_reason_code": original_reason_code,
        "details": structured,
        "retryable": retryable,
    }
    return FailureDiagnostic.create(
        failure_id=stable_content_id("m02_failure", payload),
        family=family,
        reason_code=reason_code,
        stage=stage,
        parent_accepted_state_id=parent_accepted_state_id,
        last_valid_state_id=last_valid_state_id,
        owner_proof_ref=owner_proof_ref,
        original_reason_code=original_reason_code,
        structured_details=structured,
        retryable=retryable,
        metadata_unit="1",
    )


_M02_FAMILY_BY_REASON: dict[str, FailureFamily] = {
    M02ReasonCode.NONLINEAR_NONCONVERGENCE.value: FailureFamily.NUMERICAL_FAILURE,
    M02ReasonCode.LINE_SEARCH_EXHAUSTED.value: FailureFamily.NUMERICAL_FAILURE,
    M02ReasonCode.LINEAR_SOLVE_FAILURE.value: FailureFamily.NUMERICAL_FAILURE,
    M02ReasonCode.STEP_RETRY_EXHAUSTED.value: FailureFamily.NUMERICAL_FAILURE,
    M02ReasonCode.EVENT_ROOT_NONCONVERGENCE.value: FailureFamily.NUMERICAL_FAILURE,
    M02ReasonCode.EVENT_EARLIESTNESS_UNPROVEN.value: FailureFamily.NUMERICAL_FAILURE,
    M02ReasonCode.EVENT_COVERAGE_UNAVAILABLE.value: FailureFamily.NUMERICAL_FAILURE,
    M02ReasonCode.ZENO_CANDIDATE.value: FailureFamily.NUMERICAL_FAILURE,
    M02ReasonCode.REPLAY_MISMATCH.value: FailureFamily.NUMERICAL_FAILURE,
    M02ReasonCode.RESIDUAL_SCALE_MISSING.value: FailureFamily.CONTRACT_REJECTION,
    M02ReasonCode.EVENT_CHANNEL_CONTRACT_INVALID.value: FailureFamily.CONTRACT_REJECTION,
    M02ReasonCode.EVENT_DEPENDENCY_CYCLE.value: FailureFamily.CONTRACT_REJECTION,
    M02ReasonCode.STALE_PARENT.value: FailureFamily.CONTRACT_REJECTION,
    M02ReasonCode.OWNER_SIDE_EFFECT_DETECTED.value: FailureFamily.CONTRACT_REJECTION,
    M02ReasonCode.OWNER_PROVEN_PHYSICAL_INFEASIBLE.value: FailureFamily.PHYSICAL_INFEASIBLE,
    M02ReasonCode.PREPARE_REJECTED.value: FailureFamily.TRANSACTION_FAILURE,
    M02ReasonCode.COMMIT_CONFLICT.value: FailureFamily.TRANSACTION_FAILURE,
    M02ReasonCode.PERSISTENCE_FAILURE.value: FailureFamily.TRANSACTION_FAILURE,
    M02ReasonCode.ROLLBACK_FAILURE.value: FailureFamily.TRANSACTION_FAILURE,
}
