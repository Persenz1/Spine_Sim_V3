from __future__ import annotations

import gc
import json
import weakref
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from scripts import run_m03_campaign as campaign_runner
from scripts.run_m03_campaign import (
    CampaignCaseEvaluation,
    CampaignCaseMetrics,
    RealStandaloneCaseEvaluator,
    _canonical_history_artifact,
    _InstrumentedKernel,
    build_plan_report,
    main,
    run_streaming_campaign,
)

from spine_sim.foundation.canonical import canonical_json_bytes, stable_content_id
from spine_sim.single_spine.campaigns import (
    CampaignStreamingCursor,
    StreamingCampaignCase,
    frozen_campaign_streaming_plan,
)
from spine_sim.single_spine.contracts import FailureAxis, StandaloneTerminalStatus
from spine_sim.single_spine.standalone import run_standalone_single_spine
from tests.single_spine.test_standalone import _AnalyticPlaneKernel, _request


class _FullHistory:
    pass


def test_instrumented_kernel_preserves_artifacts_and_counts_receipts_once() -> None:
    response = SimpleNamespace(
        geometry_contact=SimpleNamespace(query_receipt_ids=("query-1", "query-2"))
    )
    evaluation = SimpleNamespace(response=response, artifacts=object())

    class Kernel:
        def evaluate_trial(self, request: object) -> object:
            del request
            return response

        def evaluate_trial_with_artifacts(self, request: object) -> object:
            del request
            return evaluation

    class Tracker:
        def __init__(self) -> None:
            self.sample_count = 0

        def sample(self) -> int:
            self.sample_count += 1
            return 0

    tracker = Tracker()
    instrumented = _InstrumentedKernel.__new__(_InstrumentedKernel)
    instrumented._kernel = Kernel()  # type: ignore[assignment]
    instrumented._tracker = tracker  # type: ignore[assignment]
    instrumented.query_count = 0
    instrumented.final_receipt_id = None

    returned = instrumented.evaluate_trial_with_artifacts(object())  # type: ignore[arg-type]

    assert returned is evaluation
    assert instrumented.query_count == 2
    assert instrumented.final_receipt_id == "query-2"
    assert tracker.sample_count == 2


def _metrics(
    case: StreamingCampaignCase,
    *,
    terminal_status: str = StandaloneTerminalStatus.TRAVEL_COMPLETE.value,
    failure_axis: str = FailureAxis.NONE.value,
    final_receipt_id: str | None = None,
) -> CampaignCaseMetrics:
    return CampaignCaseMetrics(
        accepted_count=101 + case.ordinal,
        trial_count=202 + case.ordinal,
        committed_event_count=case.ordinal % 7,
        query_count=4 * (202 + case.ordinal),
        wall_time_seconds=0.25 + case.ordinal,
        peak_rss_bytes=1_000_000 + case.ordinal,
        cache_payload_bytes=0,
        cache_hit_count=0,
        cache_miss_count=0,
        cache_regeneration_count=0,
        artifact_size_bytes=20_000 + case.ordinal,
        terminal_status=terminal_status,
        failure_axis=failure_axis,
        reason_code=(
            "M03_TRAVEL_COMPLETE"
            if terminal_status == StandaloneTerminalStatus.TRAVEL_COMPLETE.value
            else "M03_TEST_NUMERICAL_FAILURE"
        ),
        replay_manifest_id=stable_content_id(
            "m03_test_replay", {"execution_case_id": case.execution_case_id}
        ),
        final_receipt_id=final_receipt_id,
    )


class _BoundedEvaluator:
    def __init__(self) -> None:
        self.references: list[weakref.ReferenceType[_FullHistory]] = []
        self.maximum_live_histories = 0

    def __call__(self, case: StreamingCampaignCase) -> CampaignCaseEvaluation:
        gc.collect()
        live_before = sum(reference() is not None for reference in self.references)
        history = _FullHistory()
        self.references.append(weakref.ref(history))
        self.maximum_live_histories = max(self.maximum_live_histories, live_before + 1)
        return CampaignCaseEvaluation(_metrics(case), history)


def _case_result_ids(report: dict[str, Any]) -> list[str]:
    return [item["semantic_case_result_id"] for item in report["case_results"]]


def test_plan_only_exposes_all_38_cases_and_exact_metric_schema() -> None:
    plan = frozen_campaign_streaming_plan()
    report = build_plan_report()

    assert report["mode"] == "PLAN_ONLY"
    assert report["frozen_case_count"] == 38
    assert report["selected_case_count"] == 38
    assert len(report["cases"]) == 38
    assert tuple(report["required_per_case_metrics"]) == plan.required_per_case_metrics
    assert all(
        tuple(item["metrics"]) == plan.required_per_case_metrics
        and set(item["metrics"].values()) == {None}
        for item in report["cases"]
    )
    assert [item["case"]["ordinal"] for item in report["cases"]] == list(range(38))
    assert [item["case"]["surface_role"] for item in report["cases"][-2:]] == [
        "GENTLE_SMOKE",
        "SHARP_SMOKE",
    ]
    assert report["streaming_policy"] == {
        "maximum_full_histories_in_memory": 1,
        "checkpoint_interval_cases": 1,
        "retain_completed_full_history": False,
        "pause_resume_supported": True,
        "semantic_replay_required": True,
    }


def test_pause_resume_matches_one_shot_semantic_replay() -> None:
    plan = frozen_campaign_streaming_plan()
    first = run_streaming_campaign(evaluator=_BoundedEvaluator(), start=0, stop=13)
    cursor = CampaignStreamingCursor.from_dict(first["next_cursor"])
    resumed = run_streaming_campaign(
        evaluator=_BoundedEvaluator(),
        cursor=cursor,
        stop=plan.case_count,
    )
    one_shot = run_streaming_campaign(
        evaluator=_BoundedEvaluator(),
        start=0,
        stop=plan.case_count,
    )
    replay = run_streaming_campaign(
        evaluator=_BoundedEvaluator(),
        start=0,
        stop=plan.case_count,
    )

    assert _case_result_ids(first) + _case_result_ids(resumed) == _case_result_ids(one_shot)
    assert _case_result_ids(replay) == _case_result_ids(one_shot)
    assert replay["campaign_replay_manifest_id"] == one_shot["campaign_replay_manifest_id"]
    assert resumed["next_cursor"] == {"plan_id": plan.plan_id, "next_ordinal": 38}


def test_runner_releases_each_full_history_before_next_case() -> None:
    evaluator = _BoundedEvaluator()
    report = run_streaming_campaign(evaluator=evaluator)
    gc.collect()

    assert evaluator.maximum_live_histories == 1
    assert all(reference() is None for reference in evaluator.references)
    assert report["streaming_evidence"] == {
        "maximum_full_histories_allowed": 1,
        "maximum_full_histories_observed": 1,
        "retained_completed_full_history_count": 0,
        "checkpoint_interval_cases": 1,
        "full_domain_dense_grid_created": False,
    }
    assert not any("full_history" in item for item in report["case_results"])


def test_numerical_termination_is_explicitly_excluded_from_trends() -> None:
    def numerical(case: StreamingCampaignCase) -> CampaignCaseEvaluation:
        return CampaignCaseEvaluation(
            _metrics(
                case,
                terminal_status=StandaloneTerminalStatus.NUMERICAL_TERMINATION.value,
                failure_axis=FailureAxis.NUMERICAL_FAILURE.value,
            ),
            _FullHistory(),
        )

    report = run_streaming_campaign(evaluator=numerical, start=0, stop=1)
    result = report["case_results"][0]

    assert result["metrics"]["terminal_status"] == "NUMERICAL_TERMINATION"
    assert result["metrics"]["failure_axis"] == "NUMERICAL_FAILURE"
    assert result["metrics"]["reason_code"] == "M03_TEST_NUMERICAL_FAILURE"
    assert result["trend_value"] is None
    assert result["trend_value_eligible"] is False
    assert result["numerical_failure_excluded_from_trends"] is True


def test_completed_status_without_canonical_commit_is_not_trend_eligible() -> None:
    report = run_streaming_campaign(evaluator=_BoundedEvaluator(), start=0, stop=1)
    result = report["case_results"][0]

    assert result["metrics"]["terminal_status"] == "TRAVEL_COMPLETE"
    assert result["trend_value_eligible"] is False
    assert result["trend_eligibility_evidence"] == {
        "completed_100_mm_response": False,
        "m00_canonical_bundle_committed": False,
        "final_receipt_matches_commit": False,
    }


def test_only_receipt_backed_completed_100_mm_case_enters_trends() -> None:
    receipt_id = "receipt:m00-canonical"

    def completed(case: StreamingCampaignCase) -> CampaignCaseEvaluation:
        return CampaignCaseEvaluation(
            _metrics(case, final_receipt_id=receipt_id),
            _FullHistory(),
            {
                "completed_travel": True,
                "final_state_total_path_x_mm": 100.0,
                "remaining_travel_mm": 0.0,
                "total_drag_travel_mm": 100.0,
                "m00_campaign_bundle_committed": True,
                "final_m00_commit_receipt_id": receipt_id,
            },
        )

    result = run_streaming_campaign(evaluator=completed, start=0, stop=1)["case_results"][0]

    assert result["trend_value_eligible"] is True
    assert all(result["trend_eligibility_evidence"].values())


def test_receipt_backed_incomplete_path_still_cannot_enter_trends() -> None:
    receipt_id = "receipt:m00-incomplete"

    def incomplete(case: StreamingCampaignCase) -> CampaignCaseEvaluation:
        return CampaignCaseEvaluation(
            _metrics(case, final_receipt_id=receipt_id),
            _FullHistory(),
            {
                "completed_travel": True,
                "final_state_total_path_x_mm": 99.0,
                "remaining_travel_mm": 1.0,
                "total_drag_travel_mm": 100.0,
                "m00_campaign_bundle_committed": True,
                "final_m00_commit_receipt_id": receipt_id,
            },
        )

    result = run_streaming_campaign(evaluator=incomplete, start=0, stop=1)["case_results"][0]

    assert result["trend_value_eligible"] is False
    assert result["trend_eligibility_evidence"] == {
        "completed_100_mm_response": False,
        "m00_canonical_bundle_committed": True,
        "final_receipt_matches_commit": True,
    }


@pytest.mark.parametrize(
    ("error", "terminal_status", "failure_axis", "reason_code"),
    (
        (
            campaign_runner.ContractViolation("bad campaign contract"),
            "CAPABILITY_TERMINATION",
            "CONTRACT_REJECTION",
            "CONTRACT_VIOLATION",
        ),
        (
            campaign_runner.ContractViolation(
                "outside M01 domain",
                details={"reason_code": "M01_OUT_OF_DOMAIN"},
            ),
            "DOMAIN_TERMINATION",
            "DOMAIN_ERROR",
            "M01_OUT_OF_DOMAIN",
        ),
        (
            campaign_runner.ContractViolation(
                "M01 operation unavailable",
                details={"reason_code": "M01_QUERY_CAPABILITY_UNAVAILABLE"},
            ),
            "CAPABILITY_TERMINATION",
            "CAPABILITY_UNAVAILABLE",
            "M01_QUERY_CAPABILITY_UNAVAILABLE",
        ),
        (
            campaign_runner._CampaignEvaluationFailure(
                "M03_M01_REALIZATION_IDENTITY_MISMATCH",
                FailureAxis.CONTRACT_REJECTION,
                "identity mismatch",
            ),
            "CAPABILITY_TERMINATION",
            "CONTRACT_REJECTION",
            "M03_M01_REALIZATION_IDENTITY_MISMATCH",
        ),
    ),
)
def test_campaign_exceptions_preserve_structured_axis_and_reason(
    error: Exception,
    terminal_status: str,
    failure_axis: str,
    reason_code: str,
) -> None:
    def failing(_case: StreamingCampaignCase) -> CampaignCaseEvaluation:
        raise error

    result = run_streaming_campaign(evaluator=failing, start=0, stop=1)["case_results"][0]

    assert result["metrics"]["terminal_status"] == terminal_status
    assert result["metrics"]["failure_axis"] == failure_axis
    assert result["metrics"]["reason_code"] == reason_code
    assert result["trend_value_eligible"] is False
    assert result["numerical_failure_excluded_from_trends"] is False


def test_real_evaluator_separates_m01_query_from_absent_m00_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = frozen_campaign_streaming_plan().case_at(0)
    request = SimpleNamespace(
        request_hash="request-hash",
        drag_policy=SimpleNamespace(travel_mm=100.0),
    )
    config = SimpleNamespace(
        config_id="config-id",
        config_hash="0" * 64,
        drag_step_mm=1.0,
        event_scan_subdivisions=4,
    )
    response = SimpleNamespace(
        metadata=SimpleNamespace(semantic_hash="response-hash"),
        terminal_status=StandaloneTerminalStatus.PHYSICAL_TERMINATION,
        final_state=SimpleNamespace(state_id="final-state", total_path_x_mm=0.0),
        failure_axis=FailureAxis.PHYSICAL_INFEASIBLE,
        terminal_reason_code="M03_BODY_COLLISION_INVALID",
        completed_travel=False,
        remaining_travel_mm=100.0,
        unavailable_protocol_reason="body collision gate",
    )
    execution = SimpleNamespace(
        accepted_points=(object(),),
        trial_call_count=7,
        committed_events=(),
        response=response,
    )
    calls: list[tuple[object, object, object]] = []

    class InstrumentedKernel:
        def __init__(
            self,
            tracker: object,
            *,
            maximum_global_cells: int = 20_000,
        ) -> None:
            del tracker
            assert maximum_global_cells == 20_000
            self.query_count = 28
            self.final_receipt_id = "m01-final-query-receipt"

    def fake_standalone(
        observed_request: object,
        *,
        kernel: object,
        config: object,
    ) -> object:
        calls.append((observed_request, kernel, config))
        return execution

    monkeypatch.setattr(campaign_runner, "_open_frozen_surface", lambda surface: object())
    monkeypatch.setattr(campaign_runner, "_InstrumentedKernel", InstrumentedKernel)
    monkeypatch.setattr(campaign_runner, "make_standalone_request", lambda **kwargs: request)
    monkeypatch.setattr(
        campaign_runner,
        "_resolved_execution_config",
        lambda observed_request, coarse: config,
    )
    monkeypatch.setattr(campaign_runner, "run_standalone_single_spine", fake_standalone)
    monkeypatch.setattr(campaign_runner, "canonical_json_bytes", lambda value: b"history")

    evaluated = RealStandaloneCaseEvaluator()(case)

    assert len(calls) == 1
    assert calls[0][0] is request
    assert evaluated.metrics.final_receipt_id is None
    assert evaluated.execution_profile is not None
    assert evaluated.execution_profile["final_query_receipt_id"] == ("m01-final-query-receipt")
    assert evaluated.execution_profile["m00_campaign_bundle_committed"] is False
    assert evaluated.execution_profile["final_m00_commit_receipt_id"] is None
    assert evaluated.execution_profile["remaining_travel_mm"] == 100.0
    assert evaluated.execution_profile["maximum_global_cells"] == 20_000
    assert not evaluated.execution_profile["bounded_query_budget_may_return_capability_termination"]


def test_full_history_artifact_replaces_only_live_m01_handle_internals() -> None:
    request = _request("campaign-artifact")
    execution = run_standalone_single_spine(request, kernel=_AnalyticPlaneKernel())

    artifact = _canonical_history_artifact(execution)
    payload = canonical_json_bytes(artifact)

    assert len(payload) > 0
    assert artifact.response == execution.response
    assert artifact.trial_snapshots[0].request.request_hash == (
        execution.trial_snapshots[0].request.request_hash
    )
    artifact_handle = artifact.trial_snapshots[0].request.surface_query_handle
    live_handle = execution.trial_snapshots[0].request.surface_query_handle
    assert artifact_handle.handle_id == live_handle.handle_id
    assert artifact_handle.surface_realization_id == (
        live_handle.realization.surface_realization_id
    )
    assert isinstance(artifact_handle.realization, str)


def test_real_evaluator_rejects_invalid_global_candidate_budget() -> None:
    with pytest.raises(ValueError, match="at least 16"):
        RealStandaloneCaseEvaluator(maximum_global_cells=15)


def test_cli_writes_plan_and_cursor_json(tmp_path: Path) -> None:
    output = tmp_path / "plan.json"
    cursor_output = tmp_path / "cursor.json"

    exit_code = main(
        [
            "--plan-only",
            "--start",
            "5",
            "--stop",
            "9",
            "--output",
            str(output),
            "--cursor-output",
            str(cursor_output),
        ]
    )
    report = json.loads(output.read_text(encoding="utf-8"))
    cursor = json.loads(cursor_output.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert report["selected_start"] == 5
    assert report["selected_stop"] == 9
    assert cursor == {"plan_id": report["plan_id"], "next_ordinal": 9}
