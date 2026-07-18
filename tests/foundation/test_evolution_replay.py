from __future__ import annotations

import json
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from spine_sim.foundation.demo_validation_only import generate_validation_bundle
from spine_sim.foundation.errors import CompatibilityError
from spine_sim.foundation.evolution import (
    MissingFieldAdapter,
    assess_compatibility,
    migrate_manifest_only,
)
from spine_sim.foundation.reader import ResultReader
from spine_sim.foundation.replay import ReplayMode, compare_replay

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_semver_patch_minor_major_rules() -> None:
    assert assess_compatibility("1.1.2", "1.1.0").status == "FULL_SCHEMA_SUPPORT"
    assert assess_compatibility("1.0.0", "1.1.0").status == "PARTIAL_SCHEMA_SUPPORT"
    assert assess_compatibility("1.1.0", "1.0.0").status == "READ_TIME_ADAPTER_ACTIVE"
    decision = assess_compatibility("1.1.0", "2.0.0")
    assert decision.status == "BREAKING_SCHEMA_UNSUPPORTED"
    assert decision.migration_required


def test_missing_field_adapter_uses_null_unavailable() -> None:
    adapter = MissingFieldAdapter("core.accepted_points.common.future_optional", "1.1.0")
    adapted = adapter.adapt_row({"point_id": "p"}, bundle_version="1.0.0")
    assert adapted["future_optional"] is None
    assert adapted["future_optional__status"]["capability_status"] == "UNAVAILABLE"


def test_versioned_legacy_fixture_and_compatibility_matrix() -> None:
    fixture = json.loads((REPO_ROOT / "tests/fixtures/M00_LEGACY_BUNDLE_1_0_0.json").read_text())
    matrix = json.loads(
        (REPO_ROOT / "src/spine_sim/foundation/schemas/compatibility_matrix.json").read_text()
    )
    adapter = MissingFieldAdapter(
        fixture["field_absent_in_old_schema"],
        "1.1.0",
    )
    adapted = adapter.adapt_row(fixture["row"], bundle_version=fixture["bundle_schema_version"])
    assert adapted["future_optional"] is fixture["expected_adapted_value"]
    assert adapted["future_optional__status"]["reason_code"] == fixture["expected_reason_code"]
    assert matrix["bundle_schema"]["current"] == "1.1.0"
    assert matrix["migration_policy"]["in_place"] is False


def test_explicit_migration_is_not_in_place(demo_bundle: Path, tmp_path: Path) -> None:
    source_manifest = (demo_bundle / "bundle_manifest.json").read_bytes()
    target = tmp_path / "migrated.spine-result"
    lineage = migrate_manifest_only(
        demo_bundle,
        target,
        target_bundle_schema_version="1.2.0",
        adapter_id="M00_TEST_ADDITIVE_ADAPTER",
        adapter_version="1.0.0",
    )
    assert not lineage.in_place
    assert (demo_bundle / "bundle_manifest.json").read_bytes() == source_manifest
    assert (target / "provenance" / "migration_lineage.json").exists()
    assert ResultReader.open(target).compatibility_status == "PARTIAL_SCHEMA_SUPPORT"


def test_major_bundle_rejection_retains_minimal_manifest(demo_bundle: Path, tmp_path: Path) -> None:
    target = tmp_path / "major.spine-result"
    shutil.copytree(demo_bundle, target)
    path = target / "bundle_manifest.json"
    manifest = json.loads(path.read_text())
    manifest["bundle_schema_version"] = "2.0.0"
    path.write_text(json.dumps(manifest))
    with pytest.raises(CompatibilityError) as captured:
        ResultReader.open(target)
    assert captured.value.details["code"] == "BREAKING_SCHEMA_UNSUPPORTED"
    assert captured.value.details["minimal_manifest"]["run_id"]


def test_bitwise_replay_and_codec_chunk_invariance(tmp_path: Path) -> None:
    left = generate_validation_bundle(
        tmp_path / "left.spine-result",
        parquet_compression="zstd",
        zarr_compression_level=1,
        zarr_chunk_shape=(1, 4),
    )
    right = generate_validation_bundle(
        tmp_path / "right.spine-result",
        parquet_compression="none",
        zarr_compression_level=8,
        zarr_chunk_shape=(4, 1),
    )
    left_info = ResultReader.open(left).bundle_info()
    right_info = ResultReader.open(right).bundle_info()
    assert left_info["bundle_semantic_hash"] == right_info["bundle_semantic_hash"]
    report = compare_replay(left, right, mode=ReplayMode.BITWISE_REPLAY)
    assert report.equivalent, report.differences
    semantic = compare_replay(left, right, mode=ReplayMode.SEMANTIC_REPLAY)
    assert semantic.equivalent, semantic.differences


def test_bitwise_replay_negative_report_is_structured(tmp_path: Path) -> None:
    left = generate_validation_bundle(tmp_path / "semantic-left.spine-result")
    right = generate_validation_bundle(tmp_path / "semantic-right.spine-result")
    marker_path = next((right / "transactions" / "committed").glob("*.json"))
    marker = json.loads(marker_path.read_text())
    marker["semantic_content_hash"] = "0" * 64
    marker_path.write_text(json.dumps(marker))
    report = compare_replay(left, right, mode=ReplayMode.BITWISE_REPLAY)
    assert not report.equivalent
    assert report.differences[0].code
    assert report.differences[0].scope


def test_semantic_replay_negative_report_is_structured(tmp_path: Path) -> None:
    left = generate_validation_bundle(tmp_path / "semantic-value-left.spine-result")
    right = generate_validation_bundle(tmp_path / "semantic-value-right.spine-result")
    marker_path = next((right / "transactions" / "committed").glob("*.json"))
    marker = json.loads(marker_path.read_text())
    entry = marker["datasets"]["core.accepted_points.common"]
    parquet_path = right / entry["path"]
    table = pq.read_table(parquet_path)
    column_index = table.schema.get_field_index("path_coordinate")
    changed = pa.array([999.0] * table.num_rows, type=pa.float64())
    pq.write_table(table.set_column(column_index, "path_coordinate", changed), parquet_path)
    report = compare_replay(left, right, mode=ReplayMode.SEMANTIC_REPLAY)
    assert not report.equivalent
    assert any(item.code == "FIELD_VALUE_MISMATCH" for item in report.differences)
