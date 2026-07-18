from __future__ import annotations

import pytest

from spine_sim.foundation.canonical import semantic_hash
from spine_sim.foundation.errors import ContractViolation
from spine_sim.numerics.config import NumericsConfig
from spine_sim.numerics.continuation import (
    ContinuationTrialEngine,
    NumericalTrialCache,
    PredictorRecord,
    StepDifficulty,
)
from spine_sim.numerics.contracts import (
    ContinuationControlMode,
    ContinuationDirection,
    ContinuationTarget,
    M02ReasonCode,
    TrialPhase,
)


def digest(value: object) -> str:
    return semantic_hash(value)


def target(**overrides: object) -> ContinuationTarget:
    values: dict[str, object] = {
        "target_id": "target",
        "parent_accepted_state_id": "state-0",
        "parent_commit_receipt_id": "receipt-0",
        "parent_state_hash": digest("state-0"),
        "continuation_coordinate_id": "drag",
        "coordinate_unit": "mm",
        "start_value": 0.0,
        "target_value": 100.0,
        "direction": ContinuationDirection.INCREASING,
        "oriented_path_mapping_id": "path",
        "characteristic_length_mm": 10.0,
        "characteristic_length_source": "owner-Rt",
        "control_mode": ContinuationControlMode.MONOTONE_SCALAR_TARGET,
        "physical_owner_ids": ("owner",),
        "required_event_channel_ids": ("event",),
        "resolved_numerics_config_id": "config",
        "resolved_numerics_config_hash": digest("config"),
        "external_dependency_refs": (),
        "request_id": "request",
        "request_hash": digest("request"),
        "idempotency_namespace": "case",
        "metadata_unit": "mm",
    }
    values.update(overrides)
    return ContinuationTarget.create(**values)


def test_resolved_config_contains_all_frozen_starting_values() -> None:
    config = NumericsConfig.resolved()
    assert config.initial_step_over_lref == 0.5
    assert config.maximum_step_over_lref == 1.0
    assert config.minimum_step_over_lref == 0.001
    assert config.growth_factor == 1.5
    assert config.shrink_factor == 0.5
    assert config.max_retries_per_parent == 12
    assert config.max_newton_iterations == 50
    assert config.max_bracket_iterations == 80
    assert config.config_id.startswith("m02_resolved_numerics_config:")
    assert len(config.config_hash) == 64


@pytest.mark.parametrize(
    "override",
    [
        {"minimum_step_over_lref": 0.6},
        {"growth_factor": 1.0},
        {"shrink_factor": 1.0},
        {"armijo_c1": float("nan")},
        {"max_retries_per_parent": 0},
    ],
)
def test_resolved_config_rejects_invalid_values(override: dict[str, object]) -> None:
    with pytest.raises(ContractViolation):
        NumericsConfig.resolved(**override)


def test_new_session_uses_half_lref_and_truncates_short_target() -> None:
    engine = ContinuationTrialEngine()
    session = engine.create_session(target())
    assert session.next_regular_step_mm == 5.0
    short = engine.create_session(target(target_id="short", target_value=2.0))
    assert short.next_regular_step_mm == 2.0


@pytest.mark.parametrize(
    "mode",
    [
        ContinuationControlMode.PSEUDO_ARCLENGTH,
        ContinuationControlMode.MULTIPARAMETER_FREE,
        ContinuationControlMode.DYNAMIC_INTEGRATION,
    ],
)
def test_v1_other_control_modes_are_explicitly_unsupported(
    mode: ContinuationControlMode,
) -> None:
    with pytest.raises(ContractViolation, match="unsupported"):
        ContinuationTrialEngine().create_session(target(control_mode=mode))


def test_regular_trial_is_separate_from_target_and_never_advances_state() -> None:
    engine = ContinuationTrialEngine()
    item = target()
    session = engine.create_session(item)
    trial = engine.propose_regular_trial(
        item,
        session,
        attempt_index=0,
        requested_coordinate=5.0,
        oriented_path_position_mm=5.0,
        predictor_refs=("predictor",),
        evaluation_cache_key="cache-key",
    )
    assert trial.phase is TrialPhase.TARGET_PROBE
    assert trial.trial_fraction == pytest.approx(0.05)
    assert trial.requested_step_mm == 5.0
    assert not trial.accepted_state_advanced
    assert trial.parent_accepted_state_id == item.parent_accepted_state_id


def test_regular_and_accepted_coordinates_must_advance_from_current_parent() -> None:
    engine = ContinuationTrialEngine()
    item = target()
    session = engine.create_session(item)
    advanced = engine.accepted_update(
        item,
        session,
        new_parent_accepted_state_id="state-1",
        new_parent_commit_receipt_id="receipt-1",
        accepted_coordinate=10.0,
        newton_iterations=9,
        backtracks=0,
        event_step=False,
    ).next_session

    with pytest.raises(ContractViolation, match="monotonically"):
        engine.propose_regular_trial(
            item,
            advanced,
            attempt_index=1,
            requested_coordinate=5.0,
            oriented_path_position_mm=5.0,
            requested_step_mm=2.5,
            evaluation_cache_key="backward",
        )
    with pytest.raises(ContractViolation, match="monotonically"):
        engine.accepted_update(
            item,
            advanced,
            new_parent_accepted_state_id="state-2",
            new_parent_commit_receipt_id="receipt-2",
            accepted_coordinate=5.0,
            newton_iterations=9,
            backtracks=0,
            event_step=False,
        )


def test_decreasing_target_uses_oriented_monotone_progress() -> None:
    engine = ContinuationTrialEngine()
    item = target(
        start_value=100.0,
        target_value=0.0,
        direction=ContinuationDirection.DECREASING,
    )
    session = engine.create_session(item)
    trial = engine.propose_regular_trial(
        item,
        session,
        attempt_index=0,
        requested_coordinate=95.0,
        oriented_path_position_mm=5.0,
        evaluation_cache_key="decreasing",
    )
    assert trial.trial_fraction == pytest.approx(0.05)
    advanced = engine.accepted_update(
        item,
        session,
        new_parent_accepted_state_id="state-1",
        new_parent_commit_receipt_id="receipt-1",
        accepted_coordinate=95.0,
        newton_iterations=9,
        backtracks=0,
        event_step=False,
    ).next_session
    with pytest.raises(ContractViolation, match="monotonically"):
        engine.propose_regular_trial(
            item,
            advanced,
            attempt_index=1,
            requested_coordinate=96.0,
            oriented_path_position_mm=4.0,
            requested_step_mm=2.5,
            evaluation_cache_key="decreasing-backward",
        )


def test_target_truncation_may_be_smaller_than_regular_hmin() -> None:
    engine = ContinuationTrialEngine()
    item = target(target_value=0.005)
    session = engine.create_session(item)
    trial = engine.propose_regular_trial(
        item,
        session,
        attempt_index=0,
        requested_coordinate=item.target_value,
        oriented_path_position_mm=0.005,
        evaluation_cache_key="target-truncation",
    )
    assert trial.requested_step_mm == pytest.approx(0.005)


def test_regular_trial_enforces_hmin_and_hmax() -> None:
    engine = ContinuationTrialEngine()
    item = target()
    session = engine.create_session(item)
    with pytest.raises(ContractViolation, match="bounds"):
        engine.propose_regular_trial(
            item,
            session,
            attempt_index=0,
            requested_coordinate=0.001,
            oriented_path_position_mm=0.001,
            requested_step_mm=0.001,
            evaluation_cache_key="cache",
        )
    with pytest.raises(ContractViolation, match="bounds"):
        engine.propose_regular_trial(
            item,
            session,
            attempt_index=0,
            requested_coordinate=20.0,
            oriented_path_position_mm=20.0,
            requested_step_mm=20.0,
            evaluation_cache_key="cache",
        )


def test_event_localization_can_go_below_regular_hmin() -> None:
    engine = ContinuationTrialEngine()
    item = target()
    session = engine.create_session(item)
    trial = engine.propose_event_trial(
        item,
        session,
        phase=TrialPhase.EVENT_POINT,
        attempt_index=1,
        requested_coordinate=0.0001,
        oriented_path_position_mm=0.0001,
        requested_step_mm=0.0001,
        channel_ids=("event",),
        bracket_ref="bracket",
        evaluation_cache_key="event-cache",
    )
    assert trial.requested_step_mm < 0.001 * item.characteristic_length_mm
    assert not trial.accepted_state_advanced


def test_two_easy_steps_grow_then_reset_streak() -> None:
    engine = ContinuationTrialEngine()
    item = target()
    session = engine.create_session(item)
    first = engine.accepted_update(
        item,
        session,
        new_parent_accepted_state_id="state-1",
        new_parent_commit_receipt_id="receipt-1",
        accepted_coordinate=5.0,
        newton_iterations=8,
        backtracks=0,
        event_step=False,
    )
    assert first.difficulty is StepDifficulty.EASY
    assert first.next_session.easy_streak == 1
    assert first.next_session.next_regular_step_mm == 5.0
    second = engine.accepted_update(
        item,
        first.next_session,
        new_parent_accepted_state_id="state-2",
        new_parent_commit_receipt_id="receipt-2",
        accepted_coordinate=10.0,
        newton_iterations=2,
        backtracks=0,
        event_step=False,
    )
    assert second.difficulty is StepDifficulty.EASY
    assert second.next_session.easy_streak == 0
    assert second.next_session.next_regular_step_mm == 7.5


@pytest.mark.parametrize(
    ("iterations", "backtracks"),
    [(21, 0), (9, 3)],
)
def test_hard_accepted_step_shrinks_next_regular_step(iterations: int, backtracks: int) -> None:
    engine = ContinuationTrialEngine()
    item = target()
    update = engine.accepted_update(
        item,
        engine.create_session(item),
        new_parent_accepted_state_id="state-1",
        new_parent_commit_receipt_id="receipt-1",
        accepted_coordinate=5.0,
        newton_iterations=iterations,
        backtracks=backtracks,
        event_step=False,
    )
    assert update.difficulty is StepDifficulty.HARD
    assert update.next_session.next_regular_step_mm == 2.5


def test_normal_step_holds_and_event_resets_easy_streak() -> None:
    engine = ContinuationTrialEngine()
    item = target()
    normal = engine.accepted_update(
        item,
        engine.create_session(item),
        new_parent_accepted_state_id="state-1",
        new_parent_commit_receipt_id="receipt-1",
        accepted_coordinate=5.0,
        newton_iterations=10,
        backtracks=1,
        event_step=False,
    )
    assert normal.difficulty is StepDifficulty.NORMAL
    assert normal.next_session.next_regular_step_mm == 5.0
    event = engine.accepted_update(
        item,
        normal.next_session,
        new_parent_accepted_state_id="state-2",
        new_parent_commit_receipt_id="receipt-2",
        accepted_coordinate=6.0,
        newton_iterations=2,
        backtracks=0,
        event_step=True,
    )
    assert event.difficulty is StepDifficulty.EVENT
    assert event.next_session.easy_streak == 0
    assert event.next_session.next_regular_step_mm == 5.0


def test_numerical_retry_shrinks_from_same_parent_without_advancing_history() -> None:
    engine = ContinuationTrialEngine()
    item = target()
    session = engine.create_session(item)
    retry = engine.numerical_retry(item, session, failure_signature="nonconvergence:1")
    assert retry.terminal_reason is None
    assert retry.next_session.parent_accepted_state_id == session.parent_accepted_state_id
    assert retry.next_session.parent_commit_receipt_id == session.parent_commit_receipt_id
    assert retry.next_session.current_coordinate == session.current_coordinate
    assert retry.next_session.accepted_step_count == 0
    assert retry.next_session.easy_streak == session.easy_streak
    assert retry.next_session.next_regular_step_mm == 2.5


def test_twelfth_retry_is_the_frozen_terminal_boundary() -> None:
    config = NumericsConfig.resolved(minimum_step_over_lref=1.0e-12)
    engine = ContinuationTrialEngine(config)
    item = target()
    session = engine.create_session(item)
    update = None
    for retry_index in range(1, 13):
        update = engine.numerical_retry(
            item,
            session,
            failure_signature=f"nonconvergence:{retry_index}",
        )
        if retry_index < 12:
            assert update.terminal_reason is None
        session = update.next_session
    assert update is not None
    assert update.terminal_reason is M02ReasonCode.STEP_RETRY_EXHAUSTED
    assert session.retry_count_for_parent == 12


def test_repeated_failure_signature_without_progress_is_terminal() -> None:
    engine = ContinuationTrialEngine()
    item = target()
    first = engine.numerical_retry(
        item,
        engine.create_session(item),
        failure_signature="same",
    )
    second = engine.numerical_retry(item, first.next_session, failure_signature="same")
    assert second.terminal_reason is M02ReasonCode.STEP_RETRY_EXHAUSTED
    assert second.next_session.parent_accepted_state_id == "state-0"


def test_predictor_is_hash_recorded_but_cannot_advance_state() -> None:
    predictor = PredictorRecord.create(
        predictor_kind="A_EVENT_FRACTION_FOR_B_INITIAL_GUESS",
        source_accepted_state_ids=("state-0",),
        values=(0.4, -0.1),
        units=("1", "mm"),
        declared_branch_refs=("branch",),
    )
    assert len(predictor.predictor_hash) == 64
    assert not predictor.accepted_state_advanced


def test_trial_cache_is_bounded_discardable_and_noncanonical() -> None:
    cache = NumericalTrialCache[int](2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    cache.put("c", 3)
    assert cache.get("b") is None
    assert len(cache) == 2
    cache.clear()
    assert len(cache) == 0
