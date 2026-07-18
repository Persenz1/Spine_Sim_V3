from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from scripts.run_m00_performance import PerformanceRow, _rows, performance_extension

from spine_sim.foundation.canonical import semantic_hash
from spine_sim.foundation.config import ResolvedConfig
from spine_sim.foundation.demo_validation_only import _resolved_config
from spine_sim.foundation.reader import ResultReader
from spine_sim.foundation.registry import SchemaRegistry
from spine_sim.foundation.replay import ReplayMode, compare_replay
from spine_sim.foundation.writer import ResultWriter, make_run_envelope


def _build_case(writer: ResultWriter, case_id: str, config: ResolvedConfig) -> None:
    writer.create_case_shard(
        case_id,
        design_id="design:M00_PARALLEL_INVARIANCE",
        seed_id="seed:NO_RNG",
        surface_realization_id="surface:NO_SURFACE",
        resolved_case_config=config,
    )
    transaction = writer.begin_transaction(case_id, "state:ROOT", f"tx:{case_id}")
    records: list[PerformanceRow] = _rows(writer.run_envelope.run_id, case_id, 4)
    transaction.stage_accepted_point(*records)
    transaction.prepare()
    transaction.commit()
    writer.finalize_case(case_id)


def _build_bundle(destination: Path, *, parallel: bool) -> Path:
    registry = SchemaRegistry()
    registry.register_extension(performance_extension())
    registry_hash = registry.freeze()
    config = _resolved_config("parallel_invariance")
    cases = tuple(f"case:M00_INVARIANCE_{index:02d}" for index in range(8))
    envelope = make_run_envelope(
        registry_hash=registry_hash,
        resolved_run_config=config,
        operation_kind="M00_VALIDATION_ONLY",
        operation_profile="SERIAL_PARALLEL_INVARIANCE",
        source_file_hashes={"M00": semantic_hash("parallel-invariance")},
        replay_manifest={"cases": cases},
        git_commit="TEST",
        dirty_status="clean",
        provenance_labels=("VALIDATION_ONLY",),
    )
    writer = ResultWriter.create_run_bundle(destination, registry=registry, run_envelope=envelope)
    writer.write_resolved_config_and_provenance(
        config,
        provenance={"source_identity": "VALIDATION_ONLY"},
        replay_manifest={"cases": cases},
    )
    if parallel:
        with ThreadPoolExecutor(max_workers=4) as executor:
            tuple(executor.map(lambda case_id: _build_case(writer, case_id, config), cases))
    else:
        for case_id in cases:
            _build_case(writer, case_id, config)
    writer.publish_run_manifest()
    return destination


def test_serial_parallel_case_execution_is_semantically_invariant(tmp_path: Path) -> None:
    serial = _build_bundle(tmp_path / "serial.spine-result", parallel=False)
    parallel = _build_bundle(tmp_path / "parallel.spine-result", parallel=True)
    assert (
        ResultReader.open(serial).bundle_info()["bundle_semantic_hash"]
        == ResultReader.open(parallel).bundle_info()["bundle_semantic_hash"]
    )
    report = compare_replay(serial, parallel, mode=ReplayMode.BITWISE_REPLAY)
    assert report.equivalent, report.differences
