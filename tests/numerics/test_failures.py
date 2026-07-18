from __future__ import annotations

import pytest

from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    AttemptOutcome,
    CapabilityStatus,
    CertificationStatus,
    PhysicalFeasibility,
    StatusTuple,
    ValuePresence,
)
from spine_sim.numerics.contracts import FailureFamily, M02ReasonCode
from spine_sim.numerics.failures import classify_owner_failure, make_failure_diagnostic


def owner_status(
    reason: str,
    *,
    capability: CapabilityStatus = CapabilityStatus.SUPPORTED,
    attempt: AttemptOutcome = AttemptOutcome.REJECTED_TRIAL,
    physical: PhysicalFeasibility = PhysicalFeasibility.NOT_ASSESSED,
) -> StatusTuple:
    return StatusTuple(
        ValuePresence.NULL,
        capability,
        attempt,
        physical,
        CertificationStatus.CERTIFICATION_BLOCKED,
        reason,
        "synthetic owner status",
    )


def test_m01_reason_is_preserved_verbatim_and_mapped_to_domain_family() -> None:
    diagnostic = make_failure_diagnostic(
        reason_code="M01_ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN",
        stage="surface_coverage",
        parent_accepted_state_id="state-0",
        last_valid_state_id="state-0",
        retryable=False,
        details={"footprint_id": "wide-path"},
    )
    assert diagnostic.family is FailureFamily.DOMAIN_ERROR
    assert diagnostic.reason_code == "M01_ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN"
    assert diagnostic.original_reason_code == "M01_ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN"
    assert dict(diagnostic.structured_details)["footprint_id"] == "wide-path"


@pytest.mark.parametrize(
    ("reason", "family"),
    [
        (M02ReasonCode.NONLINEAR_NONCONVERGENCE, FailureFamily.NUMERICAL_FAILURE),
        (M02ReasonCode.EVENT_DEPENDENCY_CYCLE, FailureFamily.CONTRACT_REJECTION),
        (M02ReasonCode.PERSISTENCE_FAILURE, FailureFamily.TRANSACTION_FAILURE),
    ],
)
def test_m02_reason_maps_to_the_frozen_nonphysical_family(
    reason: M02ReasonCode, family: FailureFamily
) -> None:
    diagnostic = make_failure_diagnostic(
        reason_code=reason.value,
        stage="fixture",
        parent_accepted_state_id="state-0",
        last_valid_state_id="state-0",
        retryable=False,
    )
    assert diagnostic.family is family
    assert diagnostic.owner_proof_ref is None


def test_physical_infeasible_cannot_be_inferred_from_newton_failure() -> None:
    with pytest.raises(ContractViolation, match="owner proof"):
        make_failure_diagnostic(
            reason_code=M02ReasonCode.OWNER_PROVEN_PHYSICAL_INFEASIBLE.value,
            stage="owner_quality",
            parent_accepted_state_id="state-0",
            last_valid_state_id="state-0",
            retryable=False,
        )
    diagnostic = make_failure_diagnostic(
        reason_code=M02ReasonCode.OWNER_PROVEN_PHYSICAL_INFEASIBLE.value,
        stage="owner_quality",
        parent_accepted_state_id="state-0",
        last_valid_state_id="state-0",
        retryable=False,
        owner_proof_ref="owner-proof:v1",
    )
    assert diagnostic.family is FailureFamily.PHYSICAL_INFEASIBLE


def test_unknown_reason_requires_explicit_family_and_cannot_smuggle_proof() -> None:
    with pytest.raises(ContractViolation, match="explicit failure family"):
        make_failure_diagnostic(
            reason_code="OWNER_CUSTOM_REASON",
            stage="owner",
            parent_accepted_state_id="state-0",
            last_valid_state_id="state-0",
            retryable=False,
        )
    with pytest.raises(ContractViolation, match="nonphysical"):
        make_failure_diagnostic(
            reason_code="OWNER_CUSTOM_REASON",
            family=FailureFamily.DOMAIN_ERROR,
            stage="owner",
            parent_accepted_state_id="state-0",
            last_valid_state_id="state-0",
            retryable=False,
            owner_proof_ref="invalid-proof",
        )


def test_owner_failure_classifier_preserves_m01_reason_family() -> None:
    reason = "M01_ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN"
    assert (
        classify_owner_failure(reason_code=reason, status=owner_status(reason))
        is FailureFamily.DOMAIN_ERROR
    )


def test_owner_capability_status_is_not_remapped_to_numerical_or_transaction_failure() -> None:
    reason = "OWNER_DATA_UNAVAILABLE"
    status = owner_status(
        reason,
        capability=CapabilityStatus.UNAVAILABLE,
        attempt=AttemptOutcome.NOT_ATTEMPTED,
    )
    assert (
        classify_owner_failure(reason_code=reason, status=status)
        is FailureFamily.CONTRACT_REJECTION
    )
    with pytest.raises(ContractViolation, match="conflicts"):
        classify_owner_failure(
            reason_code=reason,
            status=status,
            explicit_family=FailureFamily.TRANSACTION_FAILURE,
        )


def test_owner_physical_family_requires_matching_status_and_proof() -> None:
    reason = "OWNER_MECHANISM_LIMIT_PROVEN"
    status = owner_status(reason, physical=PhysicalFeasibility.PHYSICAL_INFEASIBLE)
    with pytest.raises(ContractViolation, match="owner proof"):
        classify_owner_failure(reason_code=reason, status=status)
    assert (
        classify_owner_failure(
            reason_code=reason,
            status=status,
            owner_proof_ref="owner-proof:v1",
        )
        is FailureFamily.PHYSICAL_INFEASIBLE
    )
