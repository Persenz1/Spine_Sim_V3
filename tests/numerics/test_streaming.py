from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from spine_sim.numerics.result_extension import DiagnosticLevel
from spine_sim.numerics.streaming import (
    PER_CASE_CACHE_LIMIT_BYTES,
    CountingDiagnosticSink,
    DeterministicSyntheticOwner,
    M00StreamingDiagnosticWriter,
    StreamingAggregate,
    StreamingCasePlan,
    StreamingCursor,
    StreamingStage,
    effective_diagnostic_level,
    execute_plan_shard,
    frozen_streaming_plans,
    run_streaming_validation,
    stream_plan,
    verify_streaming_bundle,
    write_streaming_validation_report,
)


def test_frozen_stage_dimensions_and_lazy_case_counts_are_exact() -> None:
    plans = frozen_streaming_plans()
    assert [(plan.design_count, plan.scenario_count, plan.case_count) for plan in plans] == [
        (16, 4, 64),
        (64, 4, 256),
        (16, 16, 256),
        (4, 1000, 4000),
        (4, 4000, 16000),
    ]
    assert not hasattr(plans[-1], "cases")
    assert sum(1 for _ in plans[0].iter_cases()) == 64
    with pytest.raises(ValueError):
        StreamingCasePlan(StreamingStage.SINGLE_SPINE_PRESCREEN, 0, 4)


def test_final_designs_share_scenario_ids_and_extension_preserves_first_1000() -> None:
    compare, extension = frozen_streaming_plans()[-2:]
    for scenario_index in (0, 19, 20, 999):
        compare_cases = [
            compare.case_at(scenario_index * compare.design_count + design_index)
            for design_index in range(compare.design_count)
        ]
        extension_cases = [
            extension.case_at(scenario_index * extension.design_count + design_index)
            for design_index in range(extension.design_count)
        ]
        assert len({item.terrain_scenario_id for item in compare_cases}) == 1
        assert [item.terrain_scenario_id for item in compare_cases] == [
            item.terrain_scenario_id for item in extension_cases
        ]
        assert [item.design_id for item in compare_cases] == [
            item.design_id for item in extension_cases
        ]
        assert [item.case_id for item in compare_cases] == [
            item.case_id for item in extension_cases
        ]
        compare_outcomes = [
            DeterministicSyntheticOwner(failure_period=257).evaluate(item) for item in compare_cases
        ]
        extension_outcomes = [
            DeterministicSyntheticOwner(failure_period=257).evaluate(item)
            for item in extension_cases
        ]
        assert [item.semantic_result_hash for item in compare_outcomes] == [
            item.semantic_result_hash for item in extension_outcomes
        ]

    assert compare.standard_witness_scenario_count == 50
    assert extension.standard_witness_scenario_count == 200
    for plan in (compare, extension):
        for scenario_index in (0, 1, 20, 21):
            levels = {
                plan.case_at(scenario_index * 4 + design_index).requested_diagnostic_level
                for design_index in range(4)
            }
            expected = (
                DiagnosticLevel.STANDARD if scenario_index % 20 == 0 else DiagnosticLevel.COMPACT
            )
            assert levels == {expected}


def test_diagnostic_level_does_not_change_owner_result_and_failure_is_full() -> None:
    case = frozen_streaming_plans()[-1].case_at(1)
    standard_case = replace(case, requested_diagnostic_level=DiagnosticLevel.STANDARD)
    compact_case = replace(case, requested_diagnostic_level=DiagnosticLevel.COMPACT)
    first = DeterministicSyntheticOwner(failure_period=1).evaluate(standard_case)
    second = DeterministicSyntheticOwner(failure_period=1).evaluate(compact_case)
    assert first.semantic_result_hash == second.semantic_result_hash
    assert effective_diagnostic_level(standard_case, first) is DiagnosticLevel.FULL
    assert effective_diagnostic_level(compact_case, second) is DiagnosticLevel.FULL
    assert first.failure_family == "NUMERICAL_FAILURE"


def test_pause_cursor_round_trip_replay_and_shard_merge_are_identical() -> None:
    plan = frozen_streaming_plans()[1]
    owner = DeterministicSyntheticOwner(failure_period=13)
    sink = CountingDiagnosticSink()
    paused = stream_plan(plan, owner, sink, max_cases=77)
    encoded = json.dumps(paused.cursor.to_dict(), sort_keys=True)
    cursor = StreamingCursor.from_dict(json.loads(encoded))
    resumed = stream_plan(plan, owner, sink, cursor=cursor)

    replay = stream_plan(
        plan,
        DeterministicSyntheticOwner(failure_period=13),
        CountingDiagnosticSink(),
    )
    assert resumed.cursor.aggregate == replay.cursor.aggregate
    assert resumed.cursor.next_ordinal == plan.case_count

    merged = StreamingAggregate()
    for shard_index in (3, 1, 0, 2):
        merged = merged.merge(
            execute_plan_shard(
                plan,
                shard_index=shard_index,
                shard_count=4,
                failure_period=13,
            )
        )
    assert merged == resumed.cursor.aggregate
    assert owner.retained_case_count == 0
    assert owner.cache_bytes < PER_CASE_CACHE_LIMIT_BYTES

    wrong_plan = frozen_streaming_plans()[0]
    with pytest.raises(ValueError, match="different streaming plan"):
        stream_plan(
            wrong_plan,
            DeterministicSyntheticOwner(),
            sink,
            cursor=resumed.cursor,
        )


def test_m00_writer_reader_round_trip_streams_replay_and_rejected_diagnostics(
    tmp_path: Path,
) -> None:
    plan = frozen_streaming_plans()[0]
    owner = DeterministicSyntheticOwner(failure_period=5)
    writer = M00StreamingDiagnosticWriter.create(
        tmp_path / "m02-streaming.spine-result",
        plan,
        batch_size=11,
        failure_period=5,
    )
    paused = stream_plan(plan, owner, writer, max_cases=19)
    cursor = StreamingCursor.from_dict(
        json.loads(json.dumps(paused.cursor.to_dict(), sort_keys=True))
    )
    completed = stream_plan(plan, owner, writer, cursor=cursor)
    writer.finish()

    evidence = verify_streaming_bundle(writer.root, plan, completed.cursor.aggregate)
    assert evidence["status"] == "PASSED"
    assert evidence["replay_row_count"] == 64
    assert (
        evidence["rejected_diagnostic_count"] == completed.cursor.aggregate.numerical_failure_count
    )
    assert completed.cursor.aggregate.numerical_failure_count > 0
    assert writer.max_buffered_case_count <= 11
    assert writer.max_buffered_bytes < PER_CASE_CACHE_LIMIT_BYTES
    assert writer.output_size_bytes() > 0


def test_machine_readable_report_records_scope_environment_and_its_size(
    tmp_path: Path,
) -> None:
    plans = (
        StreamingCasePlan(StreamingStage.SINGLE_SPINE_PRESCREEN, 2, 3),
        StreamingCasePlan(StreamingStage.FINAL_COMPARE_1000, 4, 20),
    )
    report = run_streaming_validation(plans=plans, failure_period=7)
    path = write_streaming_validation_report(tmp_path / "streaming-report.json", report)
    decoded = json.loads(path.read_text(encoding="utf-8"))
    assert decoded["validation_status"] == "PASSED"
    assert decoded["scope"]["binary_success_or_composite_score"] == "NOT_PRODUCED"
    assert decoded["scope"]["production_scheduler_ranker"] == "NOT_IMPLEMENTED"
    assert decoded["scope"]["experimentally_validated"] == "BLOCKED_UNAVAILABLE"
    assert decoded["environment"]["thread_settings"] == {"synthetic_owner_threads": 1}
    assert decoded["report_artifact"]["size_bytes"] == path.stat().st_size


@pytest.mark.performance
@pytest.mark.parametrize(
    ("plan_index", "expected_cases", "expected_witness_scenarios"),
    ((3, 4000, 50), (4, 16000, 200)),
)
def test_4000_and_16000_case_scalability_is_bounded_pauseable_and_replayable(
    plan_index: int,
    expected_cases: int,
    expected_witness_scenarios: int,
) -> None:
    plan = frozen_streaming_plans()[plan_index]
    report = run_streaming_validation(plans=(plan,), failure_period=257)
    item = report["plans"][0]
    assert report["validation_status"] == "PASSED"
    assert item["case_count"] == expected_cases
    assert item["requested_standard_witness_scenario_count"] == expected_witness_scenarios
    assert item["pause_resume"]["status"] == "MATCHED"
    assert item["replay_status"] == "MATCHED"
    assert item["merge_status"] == "MATCHED"
    assert item["performance"]["m01_cache_bytes"] == 0
    assert item["performance"]["m02_cache_bytes"] < PER_CASE_CACHE_LIMIT_BYTES
    assert item["performance"]["max_buffered_case_count"] <= 1
    assert item["checks"]["owner_retains_no_cases"] is True
    assert item["checks"]["all_failures_full"] is True
    assert item["failure_axis"]["replacement_seed_count"] == 0
