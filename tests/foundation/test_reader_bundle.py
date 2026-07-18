from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from spine_sim.foundation.demo_validation_only import (
    DEMO_ARRAY_FIELD_ID,
    DEMO_CASE_ID,
    DEMO_DATASET_ID,
)
from spine_sim.foundation.errors import IntegrityError, QueryError
from spine_sim.foundation.integrity import VerifyMode, committed_markers, verify_bundle
from spine_sim.foundation.plot_requirements import PlotDataRequirements, RequiredPlotField
from spine_sim.foundation.reader import FilterSpec, JoinSpec, OrderSpec, ResultReader


def test_full_integrity_and_bundle_layout(demo_bundle: Path) -> None:
    report = verify_bundle(demo_bundle, VerifyMode.FULL)
    assert report.passed
    assert report.markers_checked == 2
    expected = {
        "bundle_manifest.json",
        "schemas",
        "config",
        "provenance",
        "replay",
        "indices",
        "accepted_points",
        "committed_events",
        "rejected_trials",
        "summaries",
        "arrays",
        "transactions",
        "integrity",
    }
    assert expected <= {item.name for item in demo_bundle.iterdir()}
    run_envelope = json.loads((demo_bundle / "provenance" / "run_envelope.json").read_text())
    replay_manifest = json.loads((demo_bundle / "replay" / "replay_manifest.json").read_text())
    assert run_envelope["run_id"] == replay_manifest["run_id"]


def test_default_query_excludes_validation_and_diagnostics(demo_bundle: Path) -> None:
    reader = ResultReader.open(demo_bundle)
    default_points = reader.query(
        "core.accepted_points.common",
        ("point_id", "source_identity"),
    ).read_all()
    assert default_points.num_rows == 0
    with pytest.raises(QueryError):
        reader.query("core.rejected_trials.diagnostics", ("trial_id",))
    validation_points = reader.query(
        "core.accepted_points.common",
        ("accepted_point_index", "source_identity"),
        ordering=(OrderSpec("accepted_point_index"),),
        include_non_default=True,
    ).read_all()
    assert validation_points["accepted_point_index"].to_pylist() == [0, 1]
    rejected = reader.query(
        "core.rejected_trials.diagnostics",
        ("trial_id", "accepted_state_advanced", "committed_event_id", "commit_receipt_id"),
        include_non_default=True,
        include_diagnostics=True,
    ).read_all()
    assert rejected.num_rows == 1
    assert rejected["accepted_state_advanced"].to_pylist() == [False]
    assert rejected["committed_event_id"].to_pylist() == [None]
    assert rejected["commit_receipt_id"].to_pylist() == [None]


def test_projection_filter_registered_join_and_query_manifest(demo_bundle: Path) -> None:
    reader = ResultReader.open(demo_bundle)
    result = reader.query(
        "core.accepted_points.common",
        ("point_id", "accepted_point_index", "source_identity"),
        filters=(FilterSpec("accepted_point_index", ">=", 1),),
        joins=(JoinSpec("validation_m00.relation.core_point_to_sample"),),
        ordering=(OrderSpec("accepted_point_index"),),
        include_non_default=True,
        batch_size=1,
    )
    table = result.read_all()
    assert table.num_rows == 1
    assert table["sample_value"].to_pylist() == [2.0]
    assert result.manifest.result_hash != "DEFERRED_UNTIL_EXHAUSTED"
    assert result.manifest.rows_yielded == 1
    with pytest.raises(QueryError):
        reader.query(
            "core.accepted_points.common",
            ("point_id",),
            joins=(JoinSpec("not.registered"),),
            include_non_default=True,
        )


def test_series_events_array_and_lineage(demo_bundle: Path) -> None:
    reader = ResultReader.open(demo_bundle)
    series = reader.series(
        "accepted_point_index",
        ("path_coordinate",),
        include_non_default=True,
    ).read_all()
    assert series["accepted_point_index"].to_pylist() == [0, 1]
    events = reader.events(include_sides=frozenset({"event"}), include_non_default=True).read_all()
    assert events.num_rows == 1
    assert "pre_payload_refs" not in events.schema.names
    view = reader.open_array(
        DEMO_ARRAY_FIELD_ID, DEMO_CASE_ID, slice_spec=np.s_[1:3, 1:3], include_non_default=True
    )
    values = view.read()
    assert values["values"].tolist() == [[5.0, 6.0], [9.0, 10.0]]
    assert values["validity"].all()
    lineage = reader.resolve_lineage()
    assert len(lineage.receipts) == 2
    assert len(lineage.events) == 1
    assert len(lineage.states) == 3


def test_summary_is_versioned_and_explicit_validation_only(demo_bundle: Path) -> None:
    reader = ResultReader.open(demo_bundle)
    summary = reader.query(
        "core.summaries.case",
        ("summary_id", "included_dataset_classes", "source_identity"),
        include_non_default=True,
    ).read_all()
    assert summary.num_rows == 1
    assert summary["source_identity"].to_pylist() == ["VALIDATION_ONLY"]
    assert "rejected" not in summary["included_dataset_classes"].to_pylist()[0]


def test_plot_requirements_and_complete_gap_request(demo_bundle: Path) -> None:
    reader = ResultReader.open(demo_bundle)
    requirements = PlotDataRequirements(
        "validation-recipe",
        "1.0.0",
        (
            RequiredPlotField(
                DEMO_ARRAY_FIELD_ID,
                "per_accepted_validation_point",
                "N",
                "WRONG_FRAME",
                "WRONG_REFERENCE",
                ("VALIDATION_ONLY",),
            ),
            RequiredPlotField(
                "future.missing.field",
                "per_point",
                "1",
                "NONE",
                "NONE",
                ("ACCEPTED_AUTHORITY",),
            ),
        ),
    )
    report = reader.check_plot_requirements(requirements)
    assert not report.satisfied
    request = reader.build_plot_data_gap_request(report, "validation-recipe@1.0.0")
    assert request.request_id.startswith("PLOT_DATA_GAP_REQUEST:")
    assert request.missing_field_semantics
    assert request.required_sampling_cadence
    assert request.backward_compatibility_expectation
    assert request.validation_plot_or_test


def test_checksum_missing_shard_and_stale_manifest_detection(
    demo_bundle: Path, tmp_path: Path
) -> None:
    corrupt = tmp_path / "corrupt.spine-result"
    shutil.copytree(demo_bundle, corrupt)
    _, marker = committed_markers(corrupt)[0]
    shard = corrupt / next(iter(marker["datasets"].values()))["path"]
    shard.write_bytes(shard.read_bytes() + b"corruption")
    with pytest.raises(IntegrityError) as checksum:
        verify_bundle(corrupt, VerifyMode.FULL)
    assert "CHECKSUM_MISMATCH" in str(checksum.value.details)

    missing = tmp_path / "missing.spine-result"
    shutil.copytree(demo_bundle, missing)
    _, marker = committed_markers(missing)[0]
    missing_shard = missing / next(iter(marker["datasets"].values()))["path"]
    missing_shard.rename(missing_shard.with_suffix(".missing"))
    with pytest.raises(IntegrityError) as missing_error:
        verify_bundle(missing, VerifyMode.MANIFEST)
    assert "MISSING_SHARD" in str(missing_error.value.details)

    stale = tmp_path / "stale.spine-result"
    shutil.copytree(demo_bundle, stale)
    registry = stale / "schemas" / "registry.json"
    registry.write_text(registry.read_text().replace('"M00"', '"M00_STALE"', 1))
    with pytest.raises(IntegrityError) as stale_error:
        verify_bundle(stale, VerifyMode.MANIFEST)
    assert "STALE_MANIFEST" in str(stale_error.value.details)


def test_auxiliary_rejected_checksum_is_verified(demo_bundle: Path, tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt-auxiliary.spine-result"
    shutil.copytree(demo_bundle, corrupt)
    manifest = json.loads((corrupt / "bundle_manifest.json").read_text())
    entry = manifest["auxiliary_datasets"]["core.rejected_trials.diagnostics"][0]
    shard = corrupt / entry["path"]
    shard.write_bytes(shard.read_bytes() + b"corruption")
    with pytest.raises(IntegrityError) as captured:
        verify_bundle(corrupt, VerifyMode.FULL)
    assert "CHECKSUM_MISMATCH" in str(captured.value.details)


def test_catalog_and_field_discovery(demo_bundle: Path) -> None:
    reader = ResultReader.open(demo_bundle)
    catalog = reader.list_datasets(include_non_default=True, include_diagnostics=True)
    ids = {item.dataset_id for item in catalog.entries}
    assert DEMO_DATASET_ID in ids
    fields = reader.list_fields("validation_m00.*", include_non_default=True)
    assert {item.field_id for item in fields} >= {
        f"{DEMO_DATASET_ID}.sample_value",
    }
    relations = reader.list_relations()
    assert any(
        item["relation_id"] == "validation_m00.relation.core_point_to_sample"
        for item in relations.relations
    )


def test_run_and_case_indices_are_canonical_parquet_tables(demo_bundle: Path) -> None:
    reader = ResultReader.open(demo_bundle)
    runs = reader.query(
        "core.indices.runs",
        ("run_id", "case_index_id", "design_index_id", "seed_index_id"),
    ).read_all()
    cases = reader.query(
        "core.indices.cases",
        ("case_id", "finalized", "receipt_set_hash"),
        include_non_default=True,
    ).read_all()
    assert runs.num_rows == 1
    assert cases.num_rows == 1
    assert cases["case_id"].to_pylist() == [DEMO_CASE_ID]
