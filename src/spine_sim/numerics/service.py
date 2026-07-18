"""Public one-attempt M02 continuation service.

The service composes the continuation, nonlinear, event, and transaction
engines.  Physical equations and branch meaning remain behind the owner port;
M00 remains the only publisher of accepted identities and receipts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Protocol, cast

from spine_sim.foundation.canonical import stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    AttemptOutcome,
    CapabilityStatus,
    CertificationStatus,
    PhysicalFeasibility,
    RecordBase,
    StatusTuple,
    ValuePresence,
)

from .config import DEFAULT_NUMERICS_CONFIG, NumericsConfig
from .continuation import ContinuationTrialEngine
from .contracts import (
    AdvanceOutcome,
    CommitReceiptRef,
    ContinuationAdvanceRequest,
    ContinuationAdvanceResponse,
    FailureFamily,
    M02ReasonCode,
    PhysicalEvaluationResponse,
    PreparedCandidate,
    TrialStep,
    supported_status,
)
from .events import (
    EquilibriumEventProbe,
    EventEngine,
    EventSearchRequest,
    EventSearchResult,
)
from .failures import classify_owner_failure, make_failure_diagnostic
from .nonlinear import NonlinearOwnerProblem, NonlinearSolver, NonlinearSolveResult
from .transaction import (
    M02PreparedTransaction,
    M02TransactionCoordinator,
    PrepareAccessPlan,
    TransactionAuthoritySnapshot,
    TransactionState,
)


@dataclass(frozen=True, slots=True)
class OwnerStepMapping:
    requested_coordinate: float
    oriented_path_position_mm: float
    requested_step_mm: float


@dataclass(frozen=True, slots=True)
class OwnerTrialSetup:
    initial_iterate: tuple[float, ...]
    nonlinear_problem: NonlinearOwnerProblem
    event_search_request: EventSearchRequest | None
    event_probe: EquilibriumEventProbe | None


@dataclass(frozen=True, slots=True)
class OwnerTrialRejection:
    """Explicit owner rejection returned before M02 starts its nonlinear solve."""

    trial_id: str
    parent_accepted_state_id: str
    parent_state_hash: str
    status: StatusTuple
    retryable: bool
    family: FailureFamily | None = None
    owner_proof_ref: str | None = None
    stage: str = "owner_trial_setup"
    structured_details: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for name in ("trial_id", "parent_accepted_state_id", "parent_state_hash", "stage"):
            if not getattr(self, name).strip():
                raise ContractViolation(f"{name} cannot be empty")
        keys = tuple(key for key, _ in self.structured_details)
        if len(keys) != len(set(keys)):
            raise ContractViolation("owner rejection detail keys must be unique")


@dataclass(frozen=True, slots=True)
class OwnerPublicationPlan:
    candidate: PreparedCandidate
    authority: TransactionAuthoritySnapshot
    access_plan: PrepareAccessPlan
    accepted_state_id: str
    accepted_coordinate: float
    accepted_records: tuple[RecordBase, ...]
    committed_event_records: tuple[RecordBase, ...]
    transaction_records: tuple[RecordBase, ...]
    state_and_ledger_refs: tuple[str, ...]


class PhysicalNumericsOwner(Protocol):
    """Physical-owner boundary; no A/B schema or meaning enters M02."""

    def map_regular_step(
        self,
        request: ContinuationAdvanceRequest,
        requested_step_mm: float,
    ) -> OwnerStepMapping: ...

    def setup_trial(
        self,
        request: ContinuationAdvanceRequest,
        trial: TrialStep,
    ) -> OwnerTrialSetup | PhysicalEvaluationResponse | OwnerTrialRejection: ...

    def freeze_candidate(
        self,
        request: ContinuationAdvanceRequest,
        trial: TrialStep,
        nonlinear_result: NonlinearSolveResult,
        event_result: EventSearchResult | None,
    ) -> OwnerPublicationPlan: ...

    def rollback_trial(self, trial: TrialStep) -> None: ...


class NumericsService:
    """Execute exactly one receipt-gated continuation advancement attempt."""

    def __init__(
        self,
        config: NumericsConfig = DEFAULT_NUMERICS_CONFIG,
        *,
        nonlinear_solver: NonlinearSolver | None = None,
        event_engine: EventEngine | None = None,
        continuation_engine: ContinuationTrialEngine | None = None,
        dimensionless_target_tolerance: float = 1.0e-12,
    ) -> None:
        if (
            not math.isfinite(dimensionless_target_tolerance)
            or dimensionless_target_tolerance < 0.0
        ):
            raise ContractViolation("dimensionless target tolerance must be finite and nonnegative")
        self.config = config
        self.nonlinear_solver = nonlinear_solver or NonlinearSolver(config)
        self.event_engine = event_engine or EventEngine(config)
        self.continuation_engine = continuation_engine or ContinuationTrialEngine(config)
        self.dimensionless_target_tolerance = dimensionless_target_tolerance

    def advance(
        self,
        request: ContinuationAdvanceRequest,
        owner_port: PhysicalNumericsOwner,
        transaction_port: M02TransactionCoordinator,
    ) -> ContinuationAdvanceResponse:
        """Advance once; failure and event probes leave the accepted parent unchanged."""

        target = request.target
        session = request.session
        prepared_transaction: M02PreparedTransaction | None = None
        trial: TrialStep | None = None
        publication: OwnerPublicationPlan | None = None
        nonlinear_result: NonlinearSolveResult | None = None
        receipt: CommitReceiptRef | None = None
        try:
            self.continuation_engine.require_supported_target(target)
        except ContractViolation as error:
            return self._failure_response(
                request,
                session,
                outcome=AdvanceOutcome.UNSUPPORTED,
                family=FailureFamily.CONTRACT_REJECTION,
                reason=M02ReasonCode.UNSUPPORTED_CONTROL_MODE,
                stage="control_mode",
                retryable=False,
                details=(("error", str(error)),),
            )
        if self._target_is_complete(request):
            return ContinuationAdvanceResponse.create(
                response_id=stable_content_id(
                    "m02_advance_response",
                    {"request_id": request.request_id, "outcome": "TARGET_COMPLETE"},
                ),
                request_id=request.request_id,
                outcome=AdvanceOutcome.TARGET_COMPLETE,
                target_id=target.target_id,
                parent_accepted_state_id=request.parent_accepted_state_id,
                accepted_point_id=None,
                committed_event_ids=(),
                commit_receipt_ref=None,
                next_session=session,
                suggested_next_step_mm=None,
                failure=None,
                status=supported_status(),
                metadata_unit=target.coordinate_unit,
            )

        try:
            mapping = transaction_port.evaluate(
                lambda: owner_port.map_regular_step(
                    request,
                    session.next_regular_step_mm,
                )
            )
            trial = self.continuation_engine.propose_regular_trial(
                target,
                session,
                attempt_index=session.accepted_step_count + session.retry_count_for_parent,
                requested_coordinate=mapping.requested_coordinate,
                oriented_path_position_mm=mapping.oriented_path_position_mm,
                requested_step_mm=mapping.requested_step_mm,
                evaluation_cache_key=stable_content_id(
                    "m02_trial_cache",
                    {
                        "request": request.request_hash,
                        "coordinate": mapping.requested_coordinate,
                        "retry": session.retry_count_for_parent,
                    },
                ),
            )
            setup_or_rejection = transaction_port.evaluate(
                lambda: owner_port.setup_trial(request, trial)
            )
            if isinstance(setup_or_rejection, PhysicalEvaluationResponse):
                lineage_error = self._owner_response_lineage_error(
                    request,
                    trial,
                    setup_or_rejection,
                )
                if lineage_error is not None:
                    owner_port.rollback_trial(trial)
                    return self._failure_response(
                        request,
                        session,
                        outcome=AdvanceOutcome.TERMINAL_FAILURE,
                        family=FailureFamily.CONTRACT_REJECTION,
                        reason=M02ReasonCode.STALE_PARENT,
                        stage="owner_trial_response_lineage",
                        retryable=False,
                        details=(("error", lineage_error),),
                    )
                if self._owner_response_is_success(setup_or_rejection):
                    owner_port.rollback_trial(trial)
                    return self._failure_response(
                        request,
                        session,
                        outcome=AdvanceOutcome.TERMINAL_FAILURE,
                        family=FailureFamily.CONTRACT_REJECTION,
                        reason="M02_OWNER_RESPONSE_REQUIRES_TRIAL_SETUP",
                        stage="owner_trial_setup",
                        retryable=False,
                        details=(
                            (
                                "error",
                                "successful PhysicalEvaluationResponse has no derivative matrix; "
                                "return OwnerTrialSetup for nonlinear solve",
                            ),
                        ),
                    )
                owner_port.rollback_trial(trial)
                return self._owner_status_rejection(
                    request,
                    session,
                    status=setup_or_rejection.status,
                    owner_proof_ref=setup_or_rejection.physical_feasibility_proof_ref,
                    explicit_family=None,
                    retryable=False,
                    stage="owner_physical_evaluation",
                    details=(
                        ("trial_id", trial.trial_id),
                        ("owner_id", setup_or_rejection.owner_id),
                        ("owner_response_id", setup_or_rejection.response_id),
                    ),
                )
            if isinstance(setup_or_rejection, OwnerTrialRejection):
                lineage_error = self._owner_rejection_lineage_error(
                    request,
                    trial,
                    setup_or_rejection,
                )
                if lineage_error is not None:
                    owner_port.rollback_trial(trial)
                    return self._failure_response(
                        request,
                        session,
                        outcome=AdvanceOutcome.TERMINAL_FAILURE,
                        family=FailureFamily.CONTRACT_REJECTION,
                        reason=M02ReasonCode.STALE_PARENT,
                        stage="owner_trial_rejection_lineage",
                        retryable=False,
                        details=(("error", lineage_error),),
                    )
                owner_port.rollback_trial(trial)
                return self._owner_status_rejection(
                    request,
                    session,
                    status=setup_or_rejection.status,
                    owner_proof_ref=setup_or_rejection.owner_proof_ref,
                    explicit_family=setup_or_rejection.family,
                    retryable=setup_or_rejection.retryable,
                    stage=setup_or_rejection.stage,
                    details=(
                        ("trial_id", trial.trial_id),
                        *setup_or_rejection.structured_details,
                    ),
                )
            if not isinstance(setup_or_rejection, OwnerTrialSetup):
                raise ContractViolation("owner setup returned an unsupported response type")
            setup = setup_or_rejection
            nonlinear_result = self.nonlinear_solver.solve(
                setup.nonlinear_problem,
                setup.initial_iterate,
            )
            if not nonlinear_result.converged:
                owner_port.rollback_trial(trial)
                return self._numerical_rejection(request, nonlinear_result, trial)
            event_result: EventSearchResult | None = None
            if setup.event_search_request is not None or setup.event_probe is not None:
                if setup.event_search_request is None or setup.event_probe is None:
                    raise ContractViolation(
                        "owner event search request and probe must be supplied together"
                    )
                event_result = self.event_engine.search(
                    setup.event_search_request,
                    setup.event_probe,
                )
                if not event_result.success:
                    owner_port.rollback_trial(trial)
                    reason = (
                        event_result.failure.reason_code
                        if event_result.failure is not None
                        else M02ReasonCode.EVENT_EARLIESTNESS_UNPROVEN
                    )
                    return self._event_rejection(request, trial, reason, event_result)
            elif target.required_event_channel_ids:
                raise ContractViolation("owner omitted required event coverage")
            publication = transaction_port.evaluate(
                lambda: owner_port.freeze_candidate(
                    request,
                    trial,
                    nonlinear_result,
                    event_result,
                )
            )
            self._validate_publication(request, trial, publication)
            prepared_transaction = transaction_port.begin(
                publication.candidate,
                authority=publication.authority,
                access_plan=publication.access_plan,
            )
            prepared_transaction.stage_accepted_point(*publication.accepted_records)
            if publication.committed_event_records:
                prepared_transaction.stage_committed_events(*publication.committed_event_records)
            if publication.transaction_records:
                prepared_transaction.stage_transaction_records(*publication.transaction_records)
            prepared_transaction.stage_state_and_ledger_references(
                publication.state_and_ledger_refs
            )
            token = prepared_transaction.prepare()
            receipt = prepared_transaction.commit(token)
        except Exception as error:
            if prepared_transaction is not None and (
                prepared_transaction.state is TransactionState.COMMITTED
            ):
                # Publication is authoritative even if a post-marker local ACK
                # or receipt-view fault was raised.  Never rollback a marker-
                # backed commit, even when the cached M02 view was temporarily
                # unavailable.
                receipt = prepared_transaction.recover_receipt_ref()
            else:
                rollback_details: list[tuple[str, str]] = []
                if prepared_transaction is not None:
                    try:
                        prepared_transaction.rollback()
                    except Exception as transaction_rollback_error:
                        rollback_details.append(
                            ("transaction_rollback_error", repr(transaction_rollback_error))
                        )
                if trial is not None:
                    try:
                        owner_port.rollback_trial(trial)
                    except Exception as rollback_error:
                        rollback_details.append(("owner_rollback_error", repr(rollback_error)))
                if rollback_details:
                    return self._failure_response(
                        request,
                        session,
                        outcome=AdvanceOutcome.TERMINAL_FAILURE,
                        family=FailureFamily.TRANSACTION_FAILURE,
                        reason=M02ReasonCode.ROLLBACK_FAILURE,
                        stage="rollback",
                        retryable=False,
                        details=(("error", repr(error)), *rollback_details),
                    )
                return self._failure_response(
                    request,
                    session,
                    outcome=AdvanceOutcome.TERMINAL_FAILURE,
                    family=(
                        FailureFamily.CONTRACT_REJECTION
                        if isinstance(error, ContractViolation)
                        else FailureFamily.TRANSACTION_FAILURE
                    ),
                    reason=(
                        M02ReasonCode.PREPARE_REJECTED
                        if isinstance(error, ContractViolation)
                        else M02ReasonCode.PERSISTENCE_FAILURE
                    ),
                    stage="prepare_commit",
                    retryable=False,
                    details=(("error", repr(error)),),
                )

        if publication is None or nonlinear_result is None or receipt is None:
            raise RuntimeError("committed advancement is missing its authoritative result")
        event_committed = bool(publication.candidate.proposed_committed_event_ids)
        update = self.continuation_engine.accepted_update(
            target,
            session,
            new_parent_accepted_state_id=publication.accepted_state_id,
            new_parent_commit_receipt_id=receipt.receipt_id,
            accepted_coordinate=publication.accepted_coordinate,
            newton_iterations=nonlinear_result.iterations,
            backtracks=nonlinear_result.total_backtracks,
            event_step=event_committed,
            quality_warning_ids=tuple(
                warning for record in nonlinear_result.records for warning in record.warning_ids
            ),
        )
        outcome = (
            AdvanceOutcome.COMMITTED_EVENT_STEP if event_committed else AdvanceOutcome.ACCEPTED_STEP
        )
        return ContinuationAdvanceResponse.create(
            response_id=stable_content_id(
                "m02_advance_response",
                {"request_id": request.request_id, "receipt_id": receipt.receipt_id},
            ),
            request_id=request.request_id,
            outcome=outcome,
            target_id=target.target_id,
            parent_accepted_state_id=request.parent_accepted_state_id,
            accepted_point_id=publication.candidate.proposed_accepted_point_id,
            committed_event_ids=publication.candidate.proposed_committed_event_ids,
            commit_receipt_ref=receipt,
            next_session=update.next_session,
            suggested_next_step_mm=update.next_session.next_regular_step_mm,
            failure=None,
            status=supported_status(),
            metadata_unit=target.coordinate_unit,
        )

    def _target_is_complete(self, request: ContinuationAdvanceRequest) -> bool:
        target = request.target
        current = request.session.current_coordinate
        if target.coordinate_unit == "mm":
            tolerance = self.config.event_position_tolerance_mm(target.characteristic_length_mm)
            return math.isclose(current, target.target_value, rel_tol=0.0, abs_tol=tolerance)
        if target.coordinate_unit == "1":
            return math.isclose(
                current,
                target.target_value,
                rel_tol=0.0,
                abs_tol=self.dimensionless_target_tolerance,
            )
        # No dimensional conversion or guessed tolerance is legal for an
        # arbitrary owner unit.  Exact completion is nevertheless well-defined.
        return current == target.target_value

    @staticmethod
    def _owner_response_is_success(response: PhysicalEvaluationResponse) -> bool:
        return (
            response.capability_status is CapabilityStatus.SUPPORTED
            and response.status.value_presence is ValuePresence.PRESENT
            and response.status.attempt_outcome is AttemptOutcome.ACCEPTED
            and response.status.physical_feasibility is not PhysicalFeasibility.PHYSICAL_INFEASIBLE
        )

    @staticmethod
    def _owner_response_lineage_error(
        request: ContinuationAdvanceRequest,
        trial: TrialStep,
        response: PhysicalEvaluationResponse,
    ) -> str | None:
        expected = (
            trial.trial_id,
            request.parent_accepted_state_id,
            request.parent_state_hash,
        )
        opaque = response.opaque_trial_state_ref
        rollback = response.rollback_token
        actuals = {
            "opaque_trial_state_ref": (
                opaque.trial_id,
                opaque.parent_accepted_state_id,
                opaque.parent_state_hash,
            ),
            "rollback_token": (
                rollback.trial_id,
                rollback.parent_accepted_state_id,
                rollback.parent_state_hash,
            ),
        }
        mismatches = tuple(name for name, actual in actuals.items() if actual != expected)
        return None if not mismatches else f"lineage mismatch in {', '.join(mismatches)}"

    @staticmethod
    def _owner_rejection_lineage_error(
        request: ContinuationAdvanceRequest,
        trial: TrialStep,
        rejection: OwnerTrialRejection,
    ) -> str | None:
        expected = (
            trial.trial_id,
            request.parent_accepted_state_id,
            request.parent_state_hash,
        )
        actual = (
            rejection.trial_id,
            rejection.parent_accepted_state_id,
            rejection.parent_state_hash,
        )
        return None if actual == expected else "explicit owner rejection lineage mismatch"

    def _owner_status_rejection(
        self,
        request: ContinuationAdvanceRequest,
        session: object,
        *,
        status: StatusTuple,
        owner_proof_ref: str | None,
        explicit_family: FailureFamily | None,
        retryable: bool,
        stage: str,
        details: tuple[tuple[str, str], ...],
    ) -> ContinuationAdvanceResponse:
        family = classify_owner_failure(
            reason_code=status.reason_code,
            status=status,
            explicit_family=explicit_family,
            owner_proof_ref=owner_proof_ref,
        )
        if status.capability_status is CapabilityStatus.UNAVAILABLE:
            outcome = AdvanceOutcome.UNAVAILABLE
            retryable = False
        elif status.capability_status in {
            CapabilityStatus.UNSUPPORTED,
            CapabilityStatus.NOT_APPLICABLE,
        }:
            outcome = AdvanceOutcome.UNSUPPORTED
            retryable = False
        else:
            outcome = (
                AdvanceOutcome.REJECTED_RETRYABLE if retryable else AdvanceOutcome.TERMINAL_FAILURE
            )
        response_status = StatusTuple(
            ValuePresence.NULL,
            status.capability_status,
            status.attempt_outcome,
            status.physical_feasibility,
            status.certification_status,
            status.reason_code,
            status.explanation,
            authority_refs=status.authority_refs,
            last_valid_state_id=request.parent_accepted_state_id,
        )
        return self._failure_response(
            request,
            session,
            outcome=outcome,
            family=family,
            reason=status.reason_code,
            stage=stage,
            retryable=retryable,
            details=details,
            owner_proof_ref=owner_proof_ref,
            original_reason_code=(
                status.reason_code if status.reason_code.startswith("M01_") else None
            ),
            status=response_status,
        )

    @staticmethod
    def _validate_publication(
        request: ContinuationAdvanceRequest,
        trial: TrialStep,
        publication: OwnerPublicationPlan,
    ) -> None:
        candidate = publication.candidate
        mismatches: dict[str, object] = {}
        expected = {
            "target_id": request.target.target_id,
            "trial_id": trial.trial_id,
            "parent_accepted_state_id": request.parent_accepted_state_id,
            "parent_commit_receipt_id": request.parent_commit_receipt_id,
            "parent_state_hash": request.parent_state_hash,
        }
        for name, value in expected.items():
            actual = getattr(candidate, name)
            if actual != value:
                mismatches[name] = {"expected": value, "actual": actual}
        if not publication.accepted_state_id or not math.isfinite(publication.accepted_coordinate):
            mismatches["accepted_publication"] = "missing state or finite coordinate"
        point_matches = tuple(
            record
            for record in publication.accepted_records
            if getattr(record, "point_id", None) == candidate.proposed_accepted_point_id
            and getattr(record, "accepted_state_id", None) == publication.accepted_state_id
        )
        if not point_matches:
            mismatches["core_accepted_point"] = candidate.proposed_accepted_point_id
        staged_event_ids = {
            str(cast(Any, record).event_id)
            for record in publication.committed_event_records
            if hasattr(record, "event_id") and cast(Any, record).event_id is not None
        }
        if staged_event_ids != set(candidate.proposed_committed_event_ids):
            mismatches["committed_event_ids"] = {
                "expected": sorted(candidate.proposed_committed_event_ids),
                "actual": sorted(staged_event_ids),
            }
        if mismatches:
            raise ContractViolation(
                "owner publication plan conflicts with the final M02 trial",
                details=mismatches,
            )

    def _numerical_rejection(
        self,
        request: ContinuationAdvanceRequest,
        result: NonlinearSolveResult,
        trial: TrialStep,
    ) -> ContinuationAdvanceResponse:
        update = self.continuation_engine.numerical_retry(
            request.target,
            request.session,
            failure_signature=result.result_hash,
        )
        terminal = update.terminal_reason is not None
        return self._failure_response(
            request,
            update.next_session,
            outcome=(
                AdvanceOutcome.TERMINAL_FAILURE if terminal else AdvanceOutcome.REJECTED_RETRYABLE
            ),
            family=FailureFamily.NUMERICAL_FAILURE,
            reason=update.terminal_reason or result.reason_code,
            stage="nonlinear_solve",
            retryable=not terminal,
            details=(("trial_id", trial.trial_id), ("solve_result_hash", result.result_hash)),
        )

    def _event_rejection(
        self,
        request: ContinuationAdvanceRequest,
        trial: TrialStep,
        reason: M02ReasonCode,
        result: EventSearchResult,
    ) -> ContinuationAdvanceResponse:
        update = self.continuation_engine.numerical_retry(
            request.target,
            request.session,
            failure_signature=result.result_hash,
        )
        terminal = update.terminal_reason is not None
        return self._failure_response(
            request,
            update.next_session,
            outcome=(
                AdvanceOutcome.TERMINAL_FAILURE if terminal else AdvanceOutcome.REJECTED_RETRYABLE
            ),
            family=FailureFamily.NUMERICAL_FAILURE,
            reason=reason,
            stage="event_coverage_and_earliestness",
            retryable=not terminal,
            details=(("trial_id", trial.trial_id), ("event_result_hash", result.result_hash)),
        )

    @staticmethod
    def _failure_response(
        request: ContinuationAdvanceRequest,
        next_session: object,
        *,
        outcome: AdvanceOutcome,
        family: FailureFamily,
        reason: M02ReasonCode | str,
        stage: str,
        retryable: bool,
        details: tuple[tuple[str, str], ...],
        owner_proof_ref: str | None = None,
        original_reason_code: str | None = None,
        status: StatusTuple | None = None,
    ) -> ContinuationAdvanceResponse:
        # Kept local to avoid letting a diagnostic alter any solver decision.
        from .contracts import ContinuationSession

        if not isinstance(next_session, ContinuationSession):
            raise ContractViolation("failure response requires a continuation session")
        reason_code = reason.value if isinstance(reason, M02ReasonCode) else reason
        failure = make_failure_diagnostic(
            family=family,
            reason_code=reason_code,
            stage=stage,
            parent_accepted_state_id=request.parent_accepted_state_id,
            last_valid_state_id=request.parent_accepted_state_id,
            owner_proof_ref=owner_proof_ref,
            original_reason_code=original_reason_code,
            details=dict(details),
            retryable=retryable,
        )
        attempt_outcome = {
            FailureFamily.NUMERICAL_FAILURE: AttemptOutcome.NUMERICAL_FAILURE,
            FailureFamily.TRANSACTION_FAILURE: AttemptOutcome.TRANSACTION_FAILURE,
            FailureFamily.CONTRACT_REJECTION: AttemptOutcome.REJECTED_TRIAL,
            FailureFamily.DOMAIN_ERROR: AttemptOutcome.REJECTED_TRIAL,
            FailureFamily.PHYSICAL_INFEASIBLE: AttemptOutcome.REJECTED_TRIAL,
        }[family]
        if outcome in {AdvanceOutcome.UNSUPPORTED, AdvanceOutcome.UNAVAILABLE}:
            attempt_outcome = AttemptOutcome.NOT_ATTEMPTED
        if status is None:
            capability_status = CapabilityStatus.SUPPORTED
            if outcome is AdvanceOutcome.UNSUPPORTED:
                capability_status = CapabilityStatus.UNSUPPORTED
            elif outcome is AdvanceOutcome.UNAVAILABLE:
                capability_status = CapabilityStatus.UNAVAILABLE
            status = StatusTuple(
                ValuePresence.NULL,
                capability_status,
                attempt_outcome,
                (
                    PhysicalFeasibility.PHYSICAL_INFEASIBLE
                    if family is FailureFamily.PHYSICAL_INFEASIBLE
                    else PhysicalFeasibility.NOT_ASSESSED
                ),
                CertificationStatus.CERTIFICATION_BLOCKED,
                reason_code,
                f"M02 advance stopped at {stage}",
                last_valid_state_id=request.parent_accepted_state_id,
            )
        return ContinuationAdvanceResponse.create(
            response_id=stable_content_id(
                "m02_advance_response_failure",
                {"request": request.request_id, "failure": failure.semantic_hash},
            ),
            request_id=request.request_id,
            outcome=outcome,
            target_id=request.target.target_id,
            parent_accepted_state_id=request.parent_accepted_state_id,
            accepted_point_id=None,
            committed_event_ids=(),
            commit_receipt_ref=None,
            next_session=next_session,
            suggested_next_step_mm=(
                next_session.next_regular_step_mm
                if outcome is AdvanceOutcome.REJECTED_RETRYABLE
                else None
            ),
            failure=failure,
            status=status,
            metadata_unit=request.target.coordinate_unit,
        )
