from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from spine_sim.foundation.canonical import semantic_hash
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    AttemptOutcome,
    CapabilityStatus,
    CertificationStatus,
    PhysicalFeasibility,
    StatusTuple,
    ValuePresence,
)
from spine_sim.numerics.continuation import ContinuationTrialEngine
from spine_sim.numerics.contracts import (
    AdvanceOutcome,
    ContinuationAdvanceRequest,
    ContinuationControlMode,
    ContinuationDirection,
    ContinuationSession,
    ContinuationTarget,
    DerivativeCapability,
    DerivativeKind,
    DiagnosticLevel,
    EventAdmissibleSide,
    EventCertificateKind,
    EventChannelRegistration,
    EventDetectionMode,
    EventTriggerDirection,
    FailureFamily,
    M02ReasonCode,
    OpaqueTrialStateRef,
    PhysicalEvaluationResponse,
    PreparedCandidate,
    ResidualBlock,
    ResidualKind,
    RollbackToken,
    TrialLifecycleState,
    TrialStep,
)
from spine_sim.numerics.events import (
    EquilibriumGuardSnapshot,
    EventCoverageDeclaration,
    EventSearchRequest,
    EventSearchResult,
)
from spine_sim.numerics.nonlinear import NonlinearEvaluation, NonlinearSolveResult
from spine_sim.numerics.service import (
    NumericsService,
    OwnerPublicationPlan,
    OwnerStepMapping,
    OwnerTrialRejection,
    OwnerTrialSetup,
)
from spine_sim.numerics.transaction import (
    M02TransactionCoordinator,
    TransactionFaultStage,
    transaction_staging_paths,
)
from tests.numerics.test_transaction import (
    DAMAGE_RESOURCE,
    OWNER_ID,
    OWNER_TOKEN_VERSION,
    PARENT_RECEIPT_ID,
    WORK_RESOURCE,
)
from tests.numerics.test_transaction import (
    _fixture as transaction_fixture,
)


def digest(value: object) -> str:
    return semantic_hash(value)


def make_target(
    *,
    mode: ContinuationControlMode = ContinuationControlMode.MONOTONE_SCALAR_TARGET,
    event_ids: tuple[str, ...] = (),
    coordinate_unit: str = "mm",
    target_value: float = 10.0,
) -> ContinuationTarget:
    return ContinuationTarget.create(
        target_id="target",
        parent_accepted_state_id="state-0",
        parent_commit_receipt_id="receipt-0",
        parent_state_hash=digest("state-0"),
        continuation_coordinate_id="drag",
        coordinate_unit=coordinate_unit,
        start_value=0.0,
        target_value=target_value,
        direction=ContinuationDirection.INCREASING,
        oriented_path_mapping_id="path",
        characteristic_length_mm=1.0,
        characteristic_length_source="owner-lref",
        control_mode=mode,
        physical_owner_ids=("owner",),
        required_event_channel_ids=event_ids,
        resolved_numerics_config_id="config",
        resolved_numerics_config_hash=digest("config"),
        external_dependency_refs=(),
        request_id="target-request",
        request_hash=digest("target-request"),
        idempotency_namespace="case",
        metadata_unit=coordinate_unit,
    )


def make_session(
    target: ContinuationTarget, *, current: float | None = None
) -> ContinuationSession:
    if target.control_mode is ContinuationControlMode.MONOTONE_SCALAR_TARGET:
        session = ContinuationTrialEngine().create_session(target)
        if current is None:
            return session
    else:
        session = ContinuationSession.create(
            session_handle="session",
            target_id=target.target_id,
            parent_accepted_state_id=target.parent_accepted_state_id,
            parent_commit_receipt_id=target.parent_commit_receipt_id,
            current_coordinate=target.start_value,
            next_regular_step_mm=0.5,
            easy_streak=0,
            retry_count_for_parent=0,
            accepted_step_count=0,
            last_failure_signature=None,
            lifecycle_state=TrialLifecycleState.COMMITTED,
            metadata_unit=target.coordinate_unit,
        )
        if current is None:
            return session
    return ContinuationSession.create(
        session_handle=session.session_handle,
        target_id=session.target_id,
        parent_accepted_state_id=session.parent_accepted_state_id,
        parent_commit_receipt_id=session.parent_commit_receipt_id,
        current_coordinate=current,
        next_regular_step_mm=session.next_regular_step_mm,
        easy_streak=session.easy_streak,
        retry_count_for_parent=session.retry_count_for_parent,
        accepted_step_count=session.accepted_step_count,
        last_failure_signature=session.last_failure_signature,
        lifecycle_state=session.lifecycle_state,
        metadata_unit=target.coordinate_unit,
    )


def advance_request(
    target: ContinuationTarget, session: ContinuationSession
) -> ContinuationAdvanceRequest:
    return ContinuationAdvanceRequest.create(
        request_id="advance",
        target=target,
        session=session,
        parent_accepted_state_id=session.parent_accepted_state_id,
        parent_commit_receipt_id=session.parent_commit_receipt_id,
        parent_state_hash=target.parent_state_hash,
        diagnostic_level=DiagnosticLevel.STANDARD,
        request_hash=digest((target.target_id, session.semantic_hash)),
        metadata_unit="mm",
    )


def derivative_capability() -> DerivativeCapability:
    return DerivativeCapability.create(
        capability_id="derivative",
        owner_id="owner",
        owner_version="1",
        kind=DerivativeKind.ANALYTIC_JACOBIAN,
        nonsmooth_supported=False,
        production_safe=True,
        derivative_hash=digest("derivative"),
        branch_scope="fixture",
        metadata_unit="1",
    )


@dataclass
class ScalarProblem:
    wrong_derivative: bool
    derivative_capability: DerivativeCapability

    def evaluate(self, iterate: np.ndarray[Any, np.dtype[np.float64]]) -> NonlinearEvaluation:
        residual = float(iterate[0]) - 1.0
        block = ResidualBlock.from_values(
            block_id="force",
            owner_id="owner",
            kind=ResidualKind.FORCE_EQUILIBRIUM,
            physical_semantics="synthetic scalar",
            raw_values=(residual,),
            raw_unit="N",
            reference_norm=0.0,
            absolute_tolerance=1.0e-10,
            relative_tolerance=0.0,
            scale_id="force-scale",
            scale_value=1.0,
        )
        return NonlinearEvaluation(
            residual_blocks=(block,),
            generalized_derivative=np.asarray(
                [[-1.0 if self.wrong_derivative else 1.0]], dtype=np.float64
            ),
            owner_response_hash=digest((float(iterate[0]), self.wrong_derivative)),
        )


class FakeCoordinator:
    def evaluate(self, evaluator: Any) -> Any:
        return evaluator()


@dataclass
class FailureOwner:
    wrong_derivative: bool = True
    event_request: EventSearchRequest | None = None
    rollback_count: int = 0

    def map_regular_step(
        self, request: ContinuationAdvanceRequest, requested_step_mm: float
    ) -> OwnerStepMapping:
        return OwnerStepMapping(requested_step_mm, requested_step_mm, requested_step_mm)

    def setup_trial(self, request: ContinuationAdvanceRequest, trial: TrialStep) -> OwnerTrialSetup:
        del request, trial
        probe = self._probe if self.event_request is not None else None
        return OwnerTrialSetup(
            initial_iterate=(0.0 if self.wrong_derivative else 1.0,),
            nonlinear_problem=ScalarProblem(
                self.wrong_derivative,
                derivative_capability(),
            ),
            event_search_request=self.event_request,
            event_probe=probe,
        )

    def freeze_candidate(
        self,
        request: ContinuationAdvanceRequest,
        trial: TrialStep,
        nonlinear_result: NonlinearSolveResult,
        event_result: EventSearchResult | None,
    ) -> OwnerPublicationPlan:
        del request, trial, nonlinear_result, event_result
        raise AssertionError("failure fixture must not freeze a candidate")

    def rollback_trial(self, trial: TrialStep) -> None:
        del trial
        self.rollback_count += 1

    @staticmethod
    def _probe(
        oriented_path_position_mm: float,
        channel_ids: tuple[str, ...],
    ) -> EquilibriumGuardSnapshot:
        return EquilibriumGuardSnapshot(
            oriented_path_position_mm,
            {key: oriented_path_position_mm - 0.25 for key in channel_ids},
            {key: "mm" for key in channel_ids},
            True,
            digest(("response", oriented_path_position_mm)),
            (digest(("quality", oriented_path_position_mm)),),
            None,
            False,
            (),
        )


@dataclass
class TypedResponseOwner:
    status: StatusTuple
    physical_feasibility_proof_ref: str | None = None
    stale_lineage: bool = False
    rollback_count: int = 0

    def map_regular_step(
        self, request: ContinuationAdvanceRequest, requested_step_mm: float
    ) -> OwnerStepMapping:
        del request
        return OwnerStepMapping(requested_step_mm, requested_step_mm, requested_step_mm)

    def setup_trial(
        self, request: ContinuationAdvanceRequest, trial: TrialStep
    ) -> PhysicalEvaluationResponse:
        lineage_trial_id = "stale-trial" if self.stale_lineage else trial.trial_id
        lineage_parent = "stale-state" if self.stale_lineage else request.parent_accepted_state_id
        lineage_hash = digest("stale-state") if self.stale_lineage else request.parent_state_hash
        opaque = OpaqueTrialStateRef.create(
            state_ref=f"opaque:{trial.trial_id}",
            owner_id="owner",
            owner_version="1",
            parent_accepted_state_id=lineage_parent,
            parent_state_hash=lineage_hash,
            trial_id=lineage_trial_id,
            metadata_unit="1",
        )
        rollback = RollbackToken.create(
            token_ref=f"rollback:{trial.trial_id}",
            owner_id="owner",
            run_id="run",
            trial_id=lineage_trial_id,
            parent_accepted_state_id=lineage_parent,
            parent_state_hash=lineage_hash,
            token_version="1",
            metadata_unit="1",
        )
        return PhysicalEvaluationResponse.create(
            response_id=f"response:{trial.trial_id}",
            request_id=request.request_id,
            request_hash=request.request_hash,
            owner_id="owner",
            owner_version="1",
            opaque_trial_state_ref=opaque,
            rollback_token=rollback,
            unknown_vector=(0.0,),
            unknown_units=("1",),
            residual_blocks=(),
            derivative_capability=derivative_capability(),
            hard_inequalities=(),
            complementarity_qualities=(),
            graph_qualities=(),
            guard_samples=(),
            provisional_intents=(),
            surface_realization_refs=(),
            surface_coverage_refs=(),
            physical_feasibility_proof_ref=self.physical_feasibility_proof_ref,
            capability_status=self.status.capability_status,
            status=self.status,
            determinism_hash=digest((request.request_hash, trial.trial_id, self.status)),
            metadata_unit="1",
        )

    def freeze_candidate(
        self,
        request: ContinuationAdvanceRequest,
        trial: TrialStep,
        nonlinear_result: NonlinearSolveResult,
        event_result: EventSearchResult | None,
    ) -> OwnerPublicationPlan:
        del request, trial, nonlinear_result, event_result
        raise AssertionError("typed owner rejection must not freeze a candidate")

    def rollback_trial(self, trial: TrialStep) -> None:
        del trial
        self.rollback_count += 1


@dataclass
class ExplicitRejectionOwner:
    status: StatusTuple
    family: FailureFamily
    retryable: bool
    rollback_count: int = 0

    def map_regular_step(
        self, request: ContinuationAdvanceRequest, requested_step_mm: float
    ) -> OwnerStepMapping:
        del request
        return OwnerStepMapping(requested_step_mm, requested_step_mm, requested_step_mm)

    def setup_trial(
        self, request: ContinuationAdvanceRequest, trial: TrialStep
    ) -> OwnerTrialRejection:
        return OwnerTrialRejection(
            trial_id=trial.trial_id,
            parent_accepted_state_id=request.parent_accepted_state_id,
            parent_state_hash=request.parent_state_hash,
            status=self.status,
            family=self.family,
            retryable=self.retryable,
            structured_details=(("owner", "synthetic"),),
        )

    def freeze_candidate(
        self,
        request: ContinuationAdvanceRequest,
        trial: TrialStep,
        nonlinear_result: NonlinearSolveResult,
        event_result: EventSearchResult | None,
    ) -> OwnerPublicationPlan:
        del request, trial, nonlinear_result, event_result
        raise AssertionError("explicit owner rejection must not freeze a candidate")

    def rollback_trial(self, trial: TrialStep) -> None:
        del trial
        self.rollback_count += 1


def owner_rejection_status(
    reason_code: str,
    *,
    capability_status: CapabilityStatus = CapabilityStatus.SUPPORTED,
    attempt_outcome: AttemptOutcome = AttemptOutcome.REJECTED_TRIAL,
    physical_feasibility: PhysicalFeasibility = PhysicalFeasibility.NOT_ASSESSED,
) -> StatusTuple:
    return StatusTuple(
        ValuePresence.NULL,
        capability_status,
        attempt_outcome,
        physical_feasibility,
        CertificationStatus.CERTIFICATION_BLOCKED,
        reason_code,
        "synthetic typed owner rejection",
        authority_refs=("owner-contract:v1",),
    )


def fake_transaction() -> M02TransactionCoordinator:
    return cast(M02TransactionCoordinator, FakeCoordinator())


def test_target_complete_returns_without_owner_or_transaction_side_effect() -> None:
    target = make_target()
    session = make_session(target, current=10.0)
    owner = FailureOwner()
    response = NumericsService().advance(
        advance_request(target, session), owner, fake_transaction()
    )
    assert response.outcome is AdvanceOutcome.TARGET_COMPLETE
    assert response.commit_receipt_ref is None
    assert response.accepted_point_id is None
    assert owner.rollback_count == 0


def test_non_mm_target_completion_uses_exact_or_explicit_dimensionless_tolerance() -> None:
    exact_target = make_target(coordinate_unit="rad")
    exact_session = make_session(exact_target, current=exact_target.target_value)
    exact_owner = FailureOwner()
    exact_response = NumericsService().advance(
        advance_request(exact_target, exact_session),
        exact_owner,
        fake_transaction(),
    )
    assert exact_response.outcome is AdvanceOutcome.TARGET_COMPLETE
    assert exact_owner.rollback_count == 0

    dimensionless_target = make_target(coordinate_unit="1", target_value=1.0)
    near_session = make_session(dimensionless_target, current=1.0 - 5.0e-13)
    near_owner = FailureOwner()
    near_response = NumericsService(dimensionless_target_tolerance=1.0e-12).advance(
        advance_request(dimensionless_target, near_session),
        near_owner,
        fake_transaction(),
    )
    assert near_response.outcome is AdvanceOutcome.TARGET_COMPLETE
    assert near_owner.rollback_count == 0


def test_invalid_dimensionless_target_tolerance_is_rejected() -> None:
    for tolerance in (-1.0, float("nan"), float("inf")):
        with pytest.raises(ContractViolation, match="dimensionless target tolerance"):
            NumericsService(dimensionless_target_tolerance=tolerance)


def test_unsupported_control_mode_is_explicit_and_parent_preserving() -> None:
    target = make_target(mode=ContinuationControlMode.PSEUDO_ARCLENGTH)
    session = make_session(target)
    response = NumericsService().advance(
        advance_request(target, session), FailureOwner(), fake_transaction()
    )
    assert response.outcome is AdvanceOutcome.UNSUPPORTED
    assert response.failure is not None
    assert response.next_session.parent_accepted_state_id == "state-0"
    assert response.commit_receipt_ref is None


def test_physical_response_preserves_m01_domain_reason_and_parent() -> None:
    target = make_target()
    session = make_session(target)
    status = owner_rejection_status("M01_ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN")
    owner = TypedResponseOwner(status)
    response = NumericsService().advance(
        advance_request(target, session), owner, fake_transaction()
    )
    assert response.outcome is AdvanceOutcome.TERMINAL_FAILURE
    assert response.failure is not None
    assert response.failure.family is FailureFamily.DOMAIN_ERROR
    assert response.failure.reason_code == "M01_ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN"
    assert response.failure.original_reason_code == response.failure.reason_code
    assert response.next_session.semantic_hash == session.semantic_hash
    assert response.commit_receipt_ref is None
    assert owner.rollback_count == 1


def test_physical_response_requires_owner_proof_for_physical_infeasibility() -> None:
    target = make_target()
    session = make_session(target)
    status = owner_rejection_status(
        "OWNER_MECHANISM_LIMIT_PROVEN",
        physical_feasibility=PhysicalFeasibility.PHYSICAL_INFEASIBLE,
    )
    owner = TypedResponseOwner(status, physical_feasibility_proof_ref="owner-proof:v1")
    response = NumericsService().advance(
        advance_request(target, session), owner, fake_transaction()
    )
    assert response.outcome is AdvanceOutcome.TERMINAL_FAILURE
    assert response.failure is not None
    assert response.failure.family is FailureFamily.PHYSICAL_INFEASIBLE
    assert response.failure.owner_proof_ref == "owner-proof:v1"
    assert response.status.physical_feasibility is PhysicalFeasibility.PHYSICAL_INFEASIBLE
    assert response.next_session.semantic_hash == session.semantic_hash
    assert owner.rollback_count == 1


@pytest.mark.parametrize(
    ("capability", "outcome"),
    [
        (CapabilityStatus.UNAVAILABLE, AdvanceOutcome.UNAVAILABLE),
        (CapabilityStatus.UNSUPPORTED, AdvanceOutcome.UNSUPPORTED),
    ],
)
def test_physical_response_keeps_capability_axis_distinct(
    capability: CapabilityStatus, outcome: AdvanceOutcome
) -> None:
    target = make_target()
    session = make_session(target)
    status = owner_rejection_status(
        f"OWNER_{capability.value}",
        capability_status=capability,
        attempt_outcome=AttemptOutcome.NOT_ATTEMPTED,
    )
    owner = TypedResponseOwner(status)
    response = NumericsService().advance(
        advance_request(target, session), owner, fake_transaction()
    )
    assert response.outcome is outcome
    assert response.failure is not None
    assert response.failure.reason_code == f"OWNER_{capability.value}"
    assert response.failure.reason_code not in {
        "M02_PREPARE_REJECTED",
        "M02_PERSISTENCE_FAILURE",
    }
    assert response.status.capability_status is capability
    assert response.next_session.semantic_hash == session.semantic_hash
    assert owner.rollback_count == 1


def test_physical_response_lineage_mismatch_is_stale_parent_rejection() -> None:
    target = make_target()
    session = make_session(target)
    owner = TypedResponseOwner(owner_rejection_status("OWNER_DOMAIN_REJECTION"), stale_lineage=True)
    response = NumericsService().advance(
        advance_request(target, session), owner, fake_transaction()
    )
    assert response.outcome is AdvanceOutcome.TERMINAL_FAILURE
    assert response.failure is not None
    assert response.failure.family is FailureFamily.CONTRACT_REJECTION
    assert response.failure.reason_code == M02ReasonCode.STALE_PARENT.value
    assert response.next_session.semantic_hash == session.semantic_hash
    assert owner.rollback_count == 1


def test_successful_physical_response_requires_owner_trial_setup() -> None:
    target = make_target()
    session = make_session(target)
    success = StatusTuple(
        ValuePresence.PRESENT,
        CapabilityStatus.SUPPORTED,
        AttemptOutcome.ACCEPTED,
        PhysicalFeasibility.FEASIBLE,
        CertificationStatus.NOT_CERTIFIABLE,
        "OWNER_EVALUATION_ACCEPTED",
        "response has values but no derivative matrix",
    )
    owner = TypedResponseOwner(success)
    response = NumericsService().advance(
        advance_request(target, session), owner, fake_transaction()
    )
    assert response.outcome is AdvanceOutcome.TERMINAL_FAILURE
    assert response.failure is not None
    assert response.failure.family is FailureFamily.CONTRACT_REJECTION
    assert response.failure.reason_code == "M02_OWNER_RESPONSE_REQUIRES_TRIAL_SETUP"
    assert response.next_session.semantic_hash == session.semantic_hash
    assert owner.rollback_count == 1


def test_explicit_owner_rejection_can_retry_without_advancing_parent() -> None:
    target = make_target()
    session = make_session(target)
    status = owner_rejection_status(
        "OWNER_LOCAL_NUMERICAL_FAILURE",
        attempt_outcome=AttemptOutcome.NUMERICAL_FAILURE,
    )
    owner = ExplicitRejectionOwner(status, FailureFamily.NUMERICAL_FAILURE, True)
    response = NumericsService().advance(
        advance_request(target, session), owner, fake_transaction()
    )
    assert response.outcome is AdvanceOutcome.REJECTED_RETRYABLE
    assert response.failure is not None
    assert response.failure.family is FailureFamily.NUMERICAL_FAILURE
    assert response.failure.reason_code == "OWNER_LOCAL_NUMERICAL_FAILURE"
    assert response.next_session.semantic_hash == session.semantic_hash
    assert response.next_session.retry_count_for_parent == 0
    assert response.commit_receipt_ref is None
    assert owner.rollback_count == 1


def test_nonlinear_failure_rolls_back_and_returns_retry_from_same_parent() -> None:
    target = make_target()
    owner = FailureOwner(wrong_derivative=True)
    response = NumericsService().advance(
        advance_request(target, make_session(target)), owner, fake_transaction()
    )
    assert response.outcome is AdvanceOutcome.REJECTED_RETRYABLE
    assert response.failure is not None
    assert response.failure.family.value == "NUMERICAL_FAILURE"
    assert response.next_session.parent_accepted_state_id == "state-0"
    assert response.next_session.current_coordinate == 0.0
    assert response.next_session.next_regular_step_mm == 0.25
    assert owner.rollback_count == 1


def test_event_coverage_failure_rolls_back_without_receipt() -> None:
    registration = EventChannelRegistration.create(
        channel_id="event",
        owner_id="owner",
        entity_ids=("entity",),
        event_kind="OWNER_EVENT",
        guard_id="guard",
        guard_version="1",
        raw_guard_unit="mm",
        zero_level=0.0,
        admissible_side=EventAdmissibleSide.NONNEGATIVE,
        trigger_direction=EventTriggerDirection.RISING,
        applicability_predicate_id="applicable",
        branch_state_scope=(),
        detection_mode=EventDetectionMode.SIGN_CHANGE,
        no_event_certificate_capabilities=(EventCertificateKind.ADAPTIVE_PROBE_SPACING,),
        dependency_predecessors=(),
        transition_owner="owner",
        post_event_side_request_id="post",
        metadata_unit="mm",
    )
    coverage = EventCoverageDeclaration(
        certificate_id="coverage-event",
        channel_id="event",
        kind=EventCertificateKind.ADAPTIVE_PROBE_SPACING,
        certificate_hash=digest("coverage"),
        complete=False,
        certifies_no_event=False,
        maximum_probe_spacing_mm=0.1,
        raw_guard_zero_tolerance=1.0e-10,
    )
    event_request = EventSearchRequest(
        search_id="search",
        target_id="target",
        trial_id="trial-probe",
        parent_accepted_state_id="state-0",
        interval_start_mm=0.0,
        interval_end_mm=0.5,
        characteristic_length_mm=1.0,
        channels=(registration,),
        coverage=(coverage,),
    )
    target = make_target(event_ids=("event",))
    owner = FailureOwner(wrong_derivative=False, event_request=event_request)
    response = NumericsService().advance(
        advance_request(target, make_session(target)), owner, fake_transaction()
    )
    assert response.outcome is AdvanceOutcome.REJECTED_RETRYABLE
    assert response.failure is not None
    assert response.failure.reason_code == "M02_EVENT_COVERAGE_UNAVAILABLE"
    assert response.commit_receipt_ref is None
    assert owner.rollback_count == 1


class InvalidMappingOwner(FailureOwner):
    def __init__(self, requested_coordinate: float) -> None:
        super().__init__(wrong_derivative=False)
        self.requested_coordinate = requested_coordinate

    def map_regular_step(
        self, request: ContinuationAdvanceRequest, requested_step_mm: float
    ) -> OwnerStepMapping:
        del request
        return OwnerStepMapping(
            self.requested_coordinate,
            self.requested_coordinate,
            requested_step_mm,
        )


def test_invalid_owner_mapping_returns_structured_contract_rejection() -> None:
    target = make_target()
    for requested_coordinate in (float("nan"), -0.5):
        owner = InvalidMappingOwner(requested_coordinate)
        response = NumericsService().advance(
            advance_request(target, make_session(target)),
            owner,
            fake_transaction(),
        )
        assert response.outcome is AdvanceOutcome.TERMINAL_FAILURE
        assert response.failure is not None
        assert response.failure.family.value == "CONTRACT_REJECTION"
        assert response.failure.reason_code == "M02_PREPARE_REJECTED"
        assert response.commit_receipt_ref is None
        assert owner.rollback_count == 0


class AcceptedOwner(FailureOwner):
    def __init__(self, fixture: Any) -> None:
        super().__init__(wrong_derivative=False)
        self.fixture = fixture
        self.last_trial: TrialStep | None = None

    def setup_trial(self, request: ContinuationAdvanceRequest, trial: TrialStep) -> OwnerTrialSetup:
        self.last_trial = trial
        return super().setup_trial(request, trial)

    def freeze_candidate(
        self,
        request: ContinuationAdvanceRequest,
        trial: TrialStep,
        nonlinear_result: NonlinearSolveResult,
        event_result: EventSearchResult | None,
    ) -> OwnerPublicationPlan:
        del nonlinear_result, event_result
        base = self.fixture.candidate
        token = RollbackToken.create(
            token_ref=f"rollback:{trial.trial_id}",
            owner_id=OWNER_ID,
            run_id=self.fixture.writer.run_envelope.run_id,
            trial_id=trial.trial_id,
            parent_accepted_state_id=request.parent_accepted_state_id,
            parent_state_hash=request.parent_state_hash,
            token_version=OWNER_TOKEN_VERSION,
            metadata_unit="1",
        )
        candidate = PreparedCandidate.create(
            candidate_id=f"candidate:{trial.trial_id}",
            target_id=request.target.target_id,
            trial_id=trial.trial_id,
            parent_accepted_state_id=request.parent_accepted_state_id,
            parent_commit_receipt_id=request.parent_commit_receipt_id,
            parent_state_hash=request.parent_state_hash,
            final_opaque_state_refs=base.final_opaque_state_refs,
            final_state_hash=base.final_state_hash,
            ordered_intent_batch=base.ordered_intent_batch,
            rollback_tokens=(token,),
            located_event_group_refs=(),
            numerical_quality_hashes=base.numerical_quality_hashes,
            registry_hash=base.registry_hash,
            config_hash=base.config_hash,
            owner_build_hashes=base.owner_build_hashes,
            event_coverage_complete=True,
            earliestness_complete=True,
            post_event_side_complete=True,
            quality_complete=True,
            persistence_ready=True,
            idempotency_key="service-accepted",
            proposed_accepted_point_id=self.fixture.point.point_id,
            proposed_committed_event_ids=(),
            metadata_unit="1",
        )
        return OwnerPublicationPlan(
            candidate=candidate,
            authority=self.fixture.authority,
            access_plan=self.fixture.access_plan,
            accepted_state_id=self.fixture.committed_state_id,
            accepted_coordinate=0.5,
            accepted_records=(self.fixture.point,),
            committed_event_records=(),
            transaction_records=(),
            state_and_ledger_refs=(
                *candidate.final_opaque_state_refs,
                candidate.ordered_intent_batch.semantic_id,
                DAMAGE_RESOURCE,
                WORK_RESOURCE,
            ),
        )


def fixture_target(fixture: Any) -> ContinuationTarget:
    return ContinuationTarget.create(
        target_id="target:m02-service-validation",
        parent_accepted_state_id=fixture.parent_state_id,
        parent_commit_receipt_id=PARENT_RECEIPT_ID,
        parent_state_hash=fixture.authority.parent_state_hash,
        continuation_coordinate_id="drag",
        coordinate_unit="mm",
        start_value=0.0,
        target_value=10.0,
        direction=ContinuationDirection.INCREASING,
        oriented_path_mapping_id="path",
        characteristic_length_mm=1.0,
        characteristic_length_source="owner-lref",
        control_mode=ContinuationControlMode.MONOTONE_SCALAR_TARGET,
        physical_owner_ids=(OWNER_ID,),
        required_event_channel_ids=(),
        resolved_numerics_config_id="config",
        resolved_numerics_config_hash=fixture.adapter.config_hash,
        external_dependency_refs=(),
        request_id="target-request",
        request_hash=digest("target-request"),
        idempotency_namespace="case",
        metadata_unit="mm",
    )


def test_successful_service_advance_exists_only_with_m00_receipt(tmp_path: Path) -> None:
    fixture = transaction_fixture(tmp_path)
    target = fixture_target(fixture)
    session = ContinuationTrialEngine().create_session(target)
    request = advance_request(target, session)
    owner = AcceptedOwner(fixture)
    response = NumericsService().advance(request, owner, fixture.coordinator)
    assert response.outcome is AdvanceOutcome.ACCEPTED_STEP
    assert response.commit_receipt_ref is not None
    assert response.accepted_point_id == fixture.point.point_id
    assert response.next_session.parent_accepted_state_id == fixture.committed_state_id
    assert response.next_session.parent_commit_receipt_id == response.commit_receipt_ref.receipt_id
    assert owner.rollback_count == 0


def test_service_prepare_fault_rolls_back_m00_staging_and_owner_trial(tmp_path: Path) -> None:
    fixture = transaction_fixture(tmp_path, m02_fault=TransactionFaultStage.PREPARE_AFTER)
    target = fixture_target(fixture)
    owner = AcceptedOwner(fixture)
    response = NumericsService().advance(
        advance_request(target, ContinuationTrialEngine().create_session(target)),
        owner,
        fixture.coordinator,
    )
    assert response.outcome is AdvanceOutcome.TERMINAL_FAILURE
    assert response.commit_receipt_ref is None
    assert transaction_staging_paths(fixture.writer.root) == ()
    assert owner.rollback_count == 1


def test_service_postpublication_ack_fault_recovers_receipt_instead_of_rollback(
    tmp_path: Path,
) -> None:
    fixture = transaction_fixture(
        tmp_path,
        m02_fault=TransactionFaultStage.COMMIT_MARKER_AFTER,
    )
    target = fixture_target(fixture)
    owner = AcceptedOwner(fixture)
    response = NumericsService().advance(
        advance_request(target, ContinuationTrialEngine().create_session(target)),
        owner,
        fixture.coordinator,
    )
    assert response.outcome is AdvanceOutcome.ACCEPTED_STEP
    assert response.commit_receipt_ref is not None
    assert owner.rollback_count == 0


def test_service_receipt_view_fault_still_returns_committed_response(
    tmp_path: Path,
) -> None:
    fixture = transaction_fixture(tmp_path)

    def fail_receipt_view(_: Any) -> Any:
        raise OSError("local receipt view failed")

    fixture.adapter.receipt_ref = fail_receipt_view
    target = fixture_target(fixture)
    owner = AcceptedOwner(fixture)
    response = NumericsService().advance(
        advance_request(target, ContinuationTrialEngine().create_session(target)),
        owner,
        fixture.coordinator,
    )
    assert response.outcome is AdvanceOutcome.ACCEPTED_STEP
    assert response.commit_receipt_ref is not None
    assert owner.rollback_count == 0
