"""Monotone scalar continuation and side-effect-free trial orchestration."""

from __future__ import annotations

import math
from collections import OrderedDict
from dataclasses import dataclass
from enum import StrEnum

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation

from .config import DEFAULT_NUMERICS_CONFIG, NumericsConfig
from .contracts import (
    ContinuationControlMode,
    ContinuationSession,
    ContinuationTarget,
    M02ReasonCode,
    TrialLifecycleState,
    TrialPhase,
    TrialStep,
    unsupported_status,
)


class StepDifficulty(StrEnum):
    EASY = "EASY"
    NORMAL = "NORMAL"
    HARD = "HARD"
    EVENT = "EVENT"


@dataclass(frozen=True, slots=True)
class PredictorRecord:
    predictor_id: str
    predictor_hash: str
    predictor_kind: str
    source_accepted_state_ids: tuple[str, ...]
    values: tuple[float, ...]
    units: tuple[str, ...]
    declared_branch_refs: tuple[str, ...]
    discarded: bool
    discard_reason: str | None
    accepted_state_advanced: bool = False

    @classmethod
    def create(
        cls,
        *,
        predictor_kind: str,
        source_accepted_state_ids: tuple[str, ...],
        values: tuple[float, ...],
        units: tuple[str, ...],
        declared_branch_refs: tuple[str, ...] = (),
        discarded: bool = False,
        discard_reason: str | None = None,
    ) -> PredictorRecord:
        if not predictor_kind.strip() or not source_accepted_state_ids:
            raise ContractViolation("predictor kind and accepted-state sources are required")
        if len(values) != len(units) or not values:
            raise ContractViolation("predictor values require one explicit unit each")
        if any(not math.isfinite(value) for value in values) or any(not unit for unit in units):
            raise ContractViolation("predictor values/units must be finite and nonempty")
        if discarded != (discard_reason is not None):
            raise ContractViolation("discarded predictor requires exactly one discard reason")
        payload = {
            "predictor_kind": predictor_kind,
            "source_accepted_state_ids": source_accepted_state_ids,
            "values": values,
            "units": units,
            "declared_branch_refs": declared_branch_refs,
            "discarded": discarded,
            "discard_reason": discard_reason,
            "accepted_state_advanced": False,
        }
        return cls(
            predictor_id=stable_content_id("m02_predictor", payload),
            predictor_hash=semantic_hash(payload),
            predictor_kind=predictor_kind,
            source_accepted_state_ids=source_accepted_state_ids,
            values=values,
            units=units,
            declared_branch_refs=declared_branch_refs,
            discarded=discarded,
            discard_reason=discard_reason,
        )


@dataclass(frozen=True, slots=True)
class StepUpdate:
    difficulty: StepDifficulty
    next_session: ContinuationSession
    step_reason: str
    terminal_reason: M02ReasonCode | None


class ContinuationTrialEngine:
    """Frozen v1 continuation controller; it never publishes accepted state."""

    def __init__(self, config: NumericsConfig = DEFAULT_NUMERICS_CONFIG) -> None:
        self.config = config

    def create_session(self, target: ContinuationTarget) -> ContinuationSession:
        self.require_supported_target(target)
        initial = min(
            self.config.regular_initial_step_mm(target.characteristic_length_mm),
            self.config.regular_maximum_step_mm(target.characteristic_length_mm),
        )
        if target.coordinate_unit == "mm":
            initial = min(initial, abs(target.target_value - target.start_value))
        return ContinuationSession.create(
            session_handle=stable_content_id(
                "m02_continuation_session_handle",
                {"target_id": target.target_id, "parent": target.parent_accepted_state_id},
            ),
            target_id=target.target_id,
            parent_accepted_state_id=target.parent_accepted_state_id,
            parent_commit_receipt_id=target.parent_commit_receipt_id,
            current_coordinate=target.start_value,
            next_regular_step_mm=initial,
            easy_streak=0,
            retry_count_for_parent=0,
            accepted_step_count=0,
            last_failure_signature=None,
            lifecycle_state=TrialLifecycleState.COMMITTED,
            metadata_unit=target.coordinate_unit,
        )

    @staticmethod
    def require_supported_target(target: ContinuationTarget) -> None:
        if target.control_mode is not ContinuationControlMode.MONOTONE_SCALAR_TARGET:
            status = unsupported_status(
                M02ReasonCode.UNSUPPORTED_CONTROL_MODE.value,
                f"{target.control_mode.value} is frozen as unsupported in M02 v1",
            )
            raise ContractViolation(status.explanation, details={"reason": status.reason_code})

    def propose_regular_trial(
        self,
        target: ContinuationTarget,
        session: ContinuationSession,
        *,
        attempt_index: int,
        requested_coordinate: float,
        oriented_path_position_mm: float,
        requested_step_mm: float | None = None,
        predictor_refs: tuple[str, ...] = (),
        branch_request_refs: tuple[str, ...] = (),
        evaluation_cache_key: str,
    ) -> TrialStep:
        self._validate_session(target, session)
        step_mm = session.next_regular_step_mm if requested_step_mm is None else requested_step_mm
        minimum = self.config.regular_minimum_step_mm(target.characteristic_length_mm)
        maximum = self.config.regular_maximum_step_mm(target.characteristic_length_mm)
        target_fraction = self._trial_fraction(target, requested_coordinate)
        target_truncation = math.isclose(target_fraction, 1.0, rel_tol=0.0, abs_tol=1.0e-12)
        if (
            not math.isfinite(step_mm)
            or step_mm <= 0.0
            or step_mm > maximum
            or (step_mm < minimum and not target_truncation)
        ):
            raise ContractViolation(
                "regular trial step lies outside resolved bounds",
                details={"step_mm": step_mm, "minimum_mm": minimum, "maximum_mm": maximum},
            )
        self._require_forward_coordinate(
            target,
            session,
            requested_coordinate,
            allow_same=False,
            field_name="requested_coordinate",
        )
        fraction = target_fraction
        payload = {
            "target_id": target.target_id,
            "parent": session.parent_accepted_state_id,
            "attempt_index": attempt_index,
            "retry_index": session.retry_count_for_parent,
            "requested_coordinate": requested_coordinate,
            "oriented_path_position_mm": oriented_path_position_mm,
            "requested_step_mm": step_mm,
            "predictor_refs": predictor_refs,
            "branch_request_refs": branch_request_refs,
        }
        return TrialStep.create(
            trial_id=stable_content_id("m02_trial", payload),
            target_id=target.target_id,
            parent_accepted_state_id=session.parent_accepted_state_id,
            phase=TrialPhase.TARGET_PROBE,
            attempt_index=attempt_index,
            retry_index=session.retry_count_for_parent,
            cascade_round=0,
            requested_coordinate=requested_coordinate,
            oriented_path_position_mm=oriented_path_position_mm,
            trial_fraction=fraction,
            requested_step_mm=step_mm,
            predictor_refs=predictor_refs,
            branch_request_refs=branch_request_refs,
            event_channel_subset=(),
            bracket_ref=None,
            simultaneous_group_ref=None,
            evaluation_cache_key=evaluation_cache_key,
            request_hash=semantic_hash(payload),
            accepted_state_advanced=False,
            metadata_unit=target.coordinate_unit,
        )

    def propose_event_trial(
        self,
        target: ContinuationTarget,
        session: ContinuationSession,
        *,
        phase: TrialPhase,
        attempt_index: int,
        requested_coordinate: float,
        oriented_path_position_mm: float,
        requested_step_mm: float,
        channel_ids: tuple[str, ...],
        bracket_ref: str,
        evaluation_cache_key: str,
        cascade_round: int = 0,
    ) -> TrialStep:
        """Create an exact-event subtrial; regular hmin intentionally does not apply."""

        self._validate_session(target, session)
        if phase not in {
            TrialPhase.EVENT_PROBE,
            TrialPhase.EVENT_POINT,
            TrialPhase.POST_EVENT_SIDE,
            TrialPhase.CASCADE_ROUND,
        }:
            raise ContractViolation("event subtrial requires an event-related phase")
        if not channel_ids or requested_step_mm < 0.0:
            raise ContractViolation("event subtrial requires channels and a nonnegative substep")
        self._require_forward_coordinate(
            target,
            session,
            requested_coordinate,
            allow_same=True,
            field_name="requested_coordinate",
        )
        payload = {
            "target_id": target.target_id,
            "parent": session.parent_accepted_state_id,
            "phase": phase.value,
            "attempt_index": attempt_index,
            "retry_index": session.retry_count_for_parent,
            "cascade_round": cascade_round,
            "requested_coordinate": requested_coordinate,
            "oriented_path_position_mm": oriented_path_position_mm,
            "requested_step_mm": requested_step_mm,
            "channel_ids": channel_ids,
            "bracket_ref": bracket_ref,
        }
        return TrialStep.create(
            trial_id=stable_content_id("m02_event_trial", payload),
            target_id=target.target_id,
            parent_accepted_state_id=session.parent_accepted_state_id,
            phase=phase,
            attempt_index=attempt_index,
            retry_index=session.retry_count_for_parent,
            cascade_round=cascade_round,
            requested_coordinate=requested_coordinate,
            oriented_path_position_mm=oriented_path_position_mm,
            trial_fraction=self._trial_fraction(target, requested_coordinate),
            requested_step_mm=requested_step_mm,
            predictor_refs=(),
            branch_request_refs=(),
            event_channel_subset=channel_ids,
            bracket_ref=bracket_ref,
            simultaneous_group_ref=None,
            evaluation_cache_key=evaluation_cache_key,
            request_hash=semantic_hash(payload),
            accepted_state_advanced=False,
            metadata_unit=target.coordinate_unit,
        )

    def accepted_update(
        self,
        target: ContinuationTarget,
        session: ContinuationSession,
        *,
        new_parent_accepted_state_id: str,
        new_parent_commit_receipt_id: str,
        accepted_coordinate: float,
        newton_iterations: int,
        backtracks: int,
        event_step: bool,
        quality_warning_ids: tuple[str, ...] = (),
    ) -> StepUpdate:
        self._validate_session(target, session)
        if not new_parent_accepted_state_id or not new_parent_commit_receipt_id:
            raise ContractViolation("accepted update requires M00 state and receipt identities")
        if newton_iterations < 0 or backtracks < 0:
            raise ContractViolation("iteration and backtrack counts cannot be negative")
        self._require_forward_coordinate(
            target,
            session,
            accepted_coordinate,
            allow_same=event_step,
            field_name="accepted_coordinate",
        )
        current_step = session.next_regular_step_mm
        easy_streak = session.easy_streak
        if event_step:
            difficulty = StepDifficulty.EVENT
            easy_streak = 0
            next_step = current_step
            reason = "EVENT_STEP_RESETS_EASY_STREAK"
        elif newton_iterations >= self.config.hard_newton_min or (
            backtracks >= self.config.hard_backtrack_min
        ):
            difficulty = StepDifficulty.HARD
            easy_streak = 0
            next_step = current_step * self.config.shrink_factor
            reason = "HARD_ACCEPTED_STEP_SHRINK"
        elif (
            newton_iterations <= self.config.easy_newton_max
            and backtracks == 0
            and not quality_warning_ids
        ):
            difficulty = StepDifficulty.EASY
            easy_streak += 1
            if easy_streak >= 2:
                next_step = current_step * self.config.growth_factor
                easy_streak = 0
                reason = "TWO_EASY_ACCEPTED_STEPS_GROW"
            else:
                next_step = current_step
                reason = "FIRST_EASY_ACCEPTED_STEP_HOLD"
        else:
            difficulty = StepDifficulty.NORMAL
            easy_streak = 0
            next_step = current_step
            reason = "NORMAL_ACCEPTED_STEP_HOLD"
        next_step = min(
            next_step,
            self.config.regular_maximum_step_mm(target.characteristic_length_mm),
        )
        next_session = self._new_session(
            session,
            parent_accepted_state_id=new_parent_accepted_state_id,
            parent_commit_receipt_id=new_parent_commit_receipt_id,
            current_coordinate=accepted_coordinate,
            next_regular_step_mm=next_step,
            easy_streak=easy_streak,
            retry_count_for_parent=0,
            accepted_step_count=session.accepted_step_count + 1,
            last_failure_signature=None,
            lifecycle_state=TrialLifecycleState.COMMITTED,
            metadata_unit=target.coordinate_unit,
        )
        return StepUpdate(difficulty, next_session, reason, None)

    def numerical_retry(
        self,
        target: ContinuationTarget,
        session: ContinuationSession,
        *,
        failure_signature: str,
    ) -> StepUpdate:
        self._validate_session(target, session)
        if not failure_signature.strip():
            raise ContractViolation("retry requires a structured failure signature")
        retry_count = session.retry_count_for_parent + 1
        next_step = session.next_regular_step_mm * self.config.shrink_factor
        minimum = self.config.regular_minimum_step_mm(target.characteristic_length_mm)
        repeated_without_progress = session.last_failure_signature == failure_signature
        exhausted = (
            retry_count >= self.config.max_retries_per_parent
            or next_step < minimum
            or (repeated_without_progress and session.retry_count_for_parent > 0)
        )
        reason = M02ReasonCode.STEP_RETRY_EXHAUSTED if exhausted else None
        next_session = self._new_session(
            session,
            parent_accepted_state_id=session.parent_accepted_state_id,
            parent_commit_receipt_id=session.parent_commit_receipt_id,
            current_coordinate=session.current_coordinate,
            next_regular_step_mm=max(next_step, minimum),
            easy_streak=session.easy_streak,
            retry_count_for_parent=retry_count,
            accepted_step_count=session.accepted_step_count,
            last_failure_signature=failure_signature,
            lifecycle_state=(
                TrialLifecycleState.REJECTED if exhausted else TrialLifecycleState.COMMITTED
            ),
            metadata_unit=target.coordinate_unit,
        )
        return StepUpdate(
            StepDifficulty.HARD,
            next_session,
            "NUMERICAL_RETRY_EXHAUSTED" if exhausted else "NUMERICAL_RETRY_SHRINK",
            reason,
        )

    @staticmethod
    def _trial_fraction(target: ContinuationTarget, coordinate: float) -> float:
        if not math.isfinite(coordinate):
            raise ContractViolation("trial coordinate must be finite")
        fraction = (coordinate - target.start_value) / (target.target_value - target.start_value)
        if fraction < -1.0e-12 or fraction > 1.0 + 1.0e-12:
            raise ContractViolation("trial coordinate lies outside the continuation target")
        return min(max(fraction, 0.0), 1.0)

    @staticmethod
    def _validate_session(target: ContinuationTarget, session: ContinuationSession) -> None:
        if session.target_id != target.target_id:
            raise ContractViolation("continuation session does not belong to target")
        if session.metadata.unit != target.coordinate_unit:
            raise ContractViolation("continuation session coordinate unit does not match target")
        if session.lifecycle_state is not TrialLifecycleState.COMMITTED:
            raise ContractViolation("continuation session is not open for another trial")
        ContinuationTrialEngine._trial_fraction(target, session.current_coordinate)

    @staticmethod
    def _require_forward_coordinate(
        target: ContinuationTarget,
        session: ContinuationSession,
        coordinate: float,
        *,
        allow_same: bool,
        field_name: str,
    ) -> None:
        current_fraction = ContinuationTrialEngine._trial_fraction(
            target, session.current_coordinate
        )
        candidate_fraction = ContinuationTrialEngine._trial_fraction(target, coordinate)
        tolerance = 1.0e-12
        behind = candidate_fraction < current_fraction - tolerance
        no_progress = candidate_fraction <= current_fraction + tolerance
        if behind or (no_progress and not allow_same):
            raise ContractViolation(
                f"{field_name} does not advance monotonically from the current parent",
                details={
                    "current_coordinate": session.current_coordinate,
                    field_name: coordinate,
                    "direction": target.direction.value,
                },
            )

    @staticmethod
    def _new_session(
        session: ContinuationSession,
        **updates: object,
    ) -> ContinuationSession:
        values: dict[str, object] = {
            "session_handle": session.session_handle,
            "target_id": session.target_id,
            "parent_accepted_state_id": session.parent_accepted_state_id,
            "parent_commit_receipt_id": session.parent_commit_receipt_id,
            "current_coordinate": session.current_coordinate,
            "next_regular_step_mm": session.next_regular_step_mm,
            "easy_streak": session.easy_streak,
            "retry_count_for_parent": session.retry_count_for_parent,
            "accepted_step_count": session.accepted_step_count,
            "last_failure_signature": session.last_failure_signature,
            "lifecycle_state": session.lifecycle_state,
        }
        metadata_unit = str(updates.pop("metadata_unit", session.metadata.unit))
        values.update(updates)
        return ContinuationSession.create(**values, metadata_unit=metadata_unit)


class NumericalTrialCache[CacheValue]:
    """Bounded, discardable LRU cache that is excluded from semantic history."""

    def __init__(self, max_entries: int) -> None:
        if max_entries <= 0:
            raise ContractViolation("trial cache max_entries must be positive")
        self.max_entries = max_entries
        self._values: OrderedDict[str, CacheValue] = OrderedDict()

    def get(self, key: str) -> CacheValue | None:
        value = self._values.get(key)
        if value is not None:
            self._values.move_to_end(key)
        return value

    def put(self, key: str, value: CacheValue) -> None:
        if not key:
            raise ContractViolation("trial cache key cannot be empty")
        self._values[key] = value
        self._values.move_to_end(key)
        while len(self._values) > self.max_entries:
            self._values.popitem(last=False)

    def clear(self) -> None:
        self._values.clear()

    def __len__(self) -> int:
        return len(self._values)
