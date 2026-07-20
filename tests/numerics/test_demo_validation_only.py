from __future__ import annotations

import json
from pathlib import Path

import pytest

from spine_sim.foundation.canonical import semantic_hash
from spine_sim.foundation.integrity import (
    VerifyMode,
    committed_markers,
    rejected_diagnostic_markers,
    verify_bundle,
)
from spine_sim.foundation.reader import JoinSpec, ResultReader
from spine_sim.numerics.demo_validation_only import (
    DEFAULT_BUNDLE_PATH,
    DEMO_CASE_ID,
    DEMO_IDEMPOTENCY_KEY,
    generate_validation_bundle,
    parse_args,
)
from spine_sim.numerics.plot_recipes import m02_plot_recipes
from spine_sim.numerics.result_extension import (
    ACCEPTED_STEP_NUMERICS_DATASET,
    CASCADE_ROUNDS_DATASET,
    CONTINUATION_ATTEMPTS_DATASET,
    EVENT_BRACKETS_DATASET,
    EVENT_DEPENDENCIES_DATASET,
    EVENT_PROBES_DATASET,
    FAILURE_DIAGNOSTICS_DATASET,
    ITERATION_TRACES_DATASET,
    M01_COMPATIBILITY_RESULTS_DATASET,
    REFINEMENT_STUDIES_DATASET,
    REJECTED_EVENT_BRACKETS_DATASET,
    REJECTED_ITERATION_TRACES_DATASET,
    REJECTED_TRIAL_DIAGNOSTICS_DATASET,
    REPLAY_STEPS_DATASET,
    RESIDUAL_BLOCK_SUMMARIES_DATASET,
    SIMULTANEOUS_EVENT_GROUPS_DATASET,
    TRANSACTION_TRACE_DATASET,
)


@pytest.fixture(scope="module")
def m02_demo_bundle(tmp_path_factory: pytest.TempPathFactory) -> Path:
    destination = tmp_path_factory.mktemp("m02-demo") / "canonical-bundle"
    return generate_validation_bundle(destination)


def test_cli_default_and_project_release_metadata_are_m02_scoped() -> None:
    assert parse_args([]).destination == DEFAULT_BUNDLE_PATH == Path("build/m02")
    project = Path(__file__).parents[2] / "pyproject.toml"
    text = project.read_text(encoding="utf-8")
    assert 'version = "0.4.0"' in text
    assert "numerical orchestration" in text
    assert 'spine-sim-m02-validation-demo = "spine_sim.numerics.demo_validation_only:main"' in text


def test_bundle_passes_manifest_and_full_integrity_with_atomic_namespaces(
    m02_demo_bundle: Path,
) -> None:
    manifest_report = verify_bundle(m02_demo_bundle, VerifyMode.MANIFEST)
    full_report = verify_bundle(m02_demo_bundle, VerifyMode.FULL)
    assert manifest_report.passed
    assert full_report.passed
    assert full_report.markers_checked == 1
    assert full_report.files_checked >= manifest_report.files_checked

    committed = committed_markers(m02_demo_bundle)
    rejected = rejected_diagnostic_markers(m02_demo_bundle)
    assert len(committed) == 1
    assert len(rejected) == 1
    commit = committed[0][1]
    rejected_group = rejected[0][1]
    assert commit["idempotency_key"] == DEMO_IDEMPOTENCY_KEY
    assert commit["case_id"] == DEMO_CASE_ID
    assert rejected_group["accepted_state_advanced"] is False
    assert rejected_group["committed_event_id"] is None
    assert rejected_group["commit_receipt_id"] is None
    assert REJECTED_TRIAL_DIAGNOSTICS_DATASET not in commit["datasets"]
    assert REJECTED_TRIAL_DIAGNOSTICS_DATASET in rejected_group["datasets"]
    assert ITERATION_TRACES_DATASET in commit["datasets"]
    assert EVENT_BRACKETS_DATASET in commit["datasets"]
    assert ITERATION_TRACES_DATASET not in rejected_group["datasets"]
    assert EVENT_BRACKETS_DATASET not in rejected_group["datasets"]
    assert REJECTED_ITERATION_TRACES_DATASET in rejected_group["datasets"]
    assert REJECTED_EVENT_BRACKETS_DATASET in rejected_group["datasets"]
    assert REJECTED_ITERATION_TRACES_DATASET not in commit["datasets"]
    assert REJECTED_EVENT_BRACKETS_DATASET not in commit["datasets"]


def test_all_receipt_backed_m02_rows_are_patched_before_full_readback(
    m02_demo_bundle: Path,
) -> None:
    reader = ResultReader.open(m02_demo_bundle, VerifyMode.FULL)
    receipt_datasets = (
        ACCEPTED_STEP_NUMERICS_DATASET,
        RESIDUAL_BLOCK_SUMMARIES_DATASET,
        ITERATION_TRACES_DATASET,
        EVENT_BRACKETS_DATASET,
        SIMULTANEOUS_EVENT_GROUPS_DATASET,
        EVENT_DEPENDENCIES_DATASET,
        CASCADE_ROUNDS_DATASET,
        TRANSACTION_TRACE_DATASET,
        REPLAY_STEPS_DATASET,
    )
    receipts: set[str] = set()
    for dataset_id in receipt_datasets:
        table = reader.query(
            dataset_id,
            ("commit_receipt_id",),
            include_non_default=True,
        ).read_all()
        assert table.num_rows == 1
        value = table["commit_receipt_id"].to_pylist()[0]
        assert isinstance(value, str) and value.startswith("receipt:")
        receipts.add(value)
    assert len(receipts) == 1

    rejected_datasets = (
        CONTINUATION_ATTEMPTS_DATASET,
        EVENT_PROBES_DATASET,
        FAILURE_DIAGNOSTICS_DATASET,
        REJECTED_ITERATION_TRACES_DATASET,
        REJECTED_EVENT_BRACKETS_DATASET,
        REJECTED_TRIAL_DIAGNOSTICS_DATASET,
    )
    for dataset_id in rejected_datasets:
        fields = ("accepted_state_advanced",)
        table = reader.query(
            dataset_id,
            fields,
            include_non_default=True,
            include_diagnostics=True,
        ).read_all()
        assert table.num_rows == 1
        assert table["accepted_state_advanced"].to_pylist() == [False]

    iteration = reader.query(
        ITERATION_TRACES_DATASET,
        ("point_id", "commit_receipt_id", "accepted_state_advanced", "outcome"),
    ).read_all()
    bracket = reader.query(
        EVENT_BRACKETS_DATASET,
        ("event_id", "commit_receipt_id", "final_bracket", "accepted_state_advanced"),
    ).read_all()
    assert iteration["accepted_state_advanced"].to_pylist() == [True]
    assert iteration["outcome"].to_pylist() == ["ACCEPTED_FINAL"]
    assert bracket["final_bracket"].to_pylist() == [True]
    assert bracket["accepted_state_advanced"].to_pylist() == [False]


def test_manifest_and_full_reader_hashes_relations_and_lineage_match(
    m02_demo_bundle: Path,
) -> None:
    manifest_reader = ResultReader.open(m02_demo_bundle, VerifyMode.MANIFEST)
    full_reader = ResultReader.open(m02_demo_bundle, VerifyMode.FULL)
    assert (
        manifest_reader.bundle_info()["bundle_semantic_hash"]
        == full_reader.bundle_info()["bundle_semantic_hash"]
    )

    fields = ("numerics_record_id", "point_id", "commit_receipt_id")
    manifest_query = manifest_reader.query(
        ACCEPTED_STEP_NUMERICS_DATASET,
        fields,
        include_non_default=True,
    )
    full_query = full_reader.query(
        ACCEPTED_STEP_NUMERICS_DATASET,
        fields,
        include_non_default=True,
    )
    assert manifest_query.read_all().to_pylist() == full_query.read_all().to_pylist()
    assert manifest_query.manifest.result_hash == full_query.manifest.result_hash

    point_join = full_reader.query(
        ACCEPTED_STEP_NUMERICS_DATASET,
        ("numerics_record_id", "point_id"),
        joins=(JoinSpec("m02.relation.accepted_step_to_point"),),
        include_non_default=True,
    ).read_all()
    receipt_join = full_reader.query(
        ACCEPTED_STEP_NUMERICS_DATASET,
        ("numerics_record_id", "commit_receipt_id"),
        joins=(JoinSpec("m02.relation.accepted_step_to_receipt"),),
        include_non_default=True,
    ).read_all()
    event_join = full_reader.query(
        SIMULTANEOUS_EVENT_GROUPS_DATASET,
        ("simultaneous_group_id", "event_id"),
        joins=(JoinSpec("m02.relation.simultaneous_member_to_event"),),
        include_non_default=True,
    ).read_all()
    dependency_event_join = full_reader.query(
        EVENT_DEPENDENCIES_DATASET,
        ("dependency_record_id", "event_id"),
        joins=(JoinSpec("m02.relation.dependency_event"),),
        include_non_default=True,
    ).read_all()
    dependency_parent_join = full_reader.query(
        EVENT_DEPENDENCIES_DATASET,
        ("dependency_record_id", "depends_on_event_id"),
        joins=(JoinSpec("m02.relation.dependency_parent_event"),),
        include_non_default=True,
    ).read_all()
    assert point_join["accepted_point_index"].to_pylist() == [0]
    assert receipt_join["idempotency_key"].to_pylist() == [DEMO_IDEMPOTENCY_KEY]
    assert event_join["event_kind"].to_pylist() == ["RELEASE"]
    assert dependency_event_join["event_kind"].to_pylist() == ["RELEASE"]
    assert dependency_parent_join["event_kind"].to_pylist() == ["CONTACT_ESTABLISHED"]

    lineage = full_reader.resolve_lineage()
    assert len(lineage.receipts) == 1
    assert len(lineage.events) == 2
    assert len(lineage.states) == 2


def test_all_six_m6_recipe_queries_parse_and_filter_without_plotting(
    m02_demo_bundle: Path,
) -> None:
    reader = ResultReader.open(m02_demo_bundle, VerifyMode.FULL)
    recipes = m02_plot_recipes()
    assert len(recipes) == 6

    seen_datasets: set[str] = set()
    for recipe in recipes:
        for query in recipe.queries:
            result = reader.query(
                query.dataset_id,
                query.fields,
                filters=query.filters,
                include_non_default=query.include_non_default,
                include_diagnostics=query.include_diagnostics,
            )
            table = result.read_all()
            assert table.num_rows == 1, (recipe.recipe_id, query.dataset_id)
            assert table.schema.names == list(query.fields)
            assert result.manifest.result_hash != "DEFERRED_UNTIL_EXHAUSTED"
            seen_datasets.add(query.dataset_id)

    assert seen_datasets == {
        ACCEPTED_STEP_NUMERICS_DATASET,
        CASCADE_ROUNDS_DATASET,
        CONTINUATION_ATTEMPTS_DATASET,
        EVENT_BRACKETS_DATASET,
        EVENT_PROBES_DATASET,
        FAILURE_DIAGNOSTICS_DATASET,
        ITERATION_TRACES_DATASET,
        REJECTED_ITERATION_TRACES_DATASET,
        REJECTED_EVENT_BRACKETS_DATASET,
        REJECTED_TRIAL_DIAGNOSTICS_DATASET,
        REFINEMENT_STUDIES_DATASET,
        RESIDUAL_BLOCK_SUMMARIES_DATASET,
        SIMULTANEOUS_EVENT_GROUPS_DATASET,
    }


def test_both_validation_summary_types_round_trip_through_public_writer_reader_path(
    m02_demo_bundle: Path,
) -> None:
    reader = ResultReader.open(m02_demo_bundle, VerifyMode.FULL)
    refinement = reader.query(
        REFINEMENT_STUDIES_DATASET,
        ("study_id", "sample_id", "passed"),
        include_non_default=True,
    ).read_all()
    compatibility = reader.query(
        M01_COMPATIBILITY_RESULTS_DATASET,
        ("compatibility_result_id", "panel_id", "passed"),
        include_non_default=True,
    ).read_all()

    assert refinement.to_pylist() == [
        {
            "study_id": "study:m02-validation-only-refinement",
            "sample_id": "sample:h-over-2",
            "passed": True,
        }
    ]
    assert compatibility.to_pylist() == [
        {
            "compatibility_result_id": "m01-compatibility:m02-validation-only",
            "panel_id": "M02_M01_SMOKE_4",
            "passed": True,
        }
    ]


def test_replay_and_provenance_remain_explicitly_validation_only(
    m02_demo_bundle: Path,
) -> None:
    replay = json.loads(
        (m02_demo_bundle / "replay" / "replay_manifest.json").read_text(encoding="utf-8")
    )
    envelope = json.loads(
        (m02_demo_bundle / "provenance" / "run_envelope.json").read_text(encoding="utf-8")
    )
    provenance = json.loads(
        (m02_demo_bundle / "provenance" / "provenance.json").read_text(encoding="utf-8")
    )

    assert envelope["replay_manifest_id"] == replay["m02_replay_manifest_id"]
    assert envelope["replay_manifest_hash"] == semantic_hash(replay)
    extension = replay["m02_extension"]
    assert extension["decision_count"] == 2
    assert extension["canonical_reduction_order"]
    assert extension["thread_policy"]
    assert extension["floating_point_profile"]
    exclusions = set(provenance["interpretation_exclusions"])
    assert "no_A_or_B_physics" in exclusions
    assert "not_experimentally_validated" in exclusions
    assert "not_certifiable" in exclusions
