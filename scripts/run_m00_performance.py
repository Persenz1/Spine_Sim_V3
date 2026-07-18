#!/usr/bin/env python3
"""Build and measure the frozen 1,000-case / 1,000,000-row M00 I/O fixture."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import platform
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import psutil  # type: ignore[import-untyped]
import zarr

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.demo_validation_only import _resolved_config
from spine_sim.foundation.integrity import VerifyMode
from spine_sim.foundation.models import (
    AttemptOutcome,
    CapabilityStatus,
    CertificationStatus,
    CommittedEventBase,
    Maturity,
    PhysicalFeasibility,
    RecordBase,
    RegisteredArrayPayload,
    RejectedTrialBase,
    SourceIdentity,
    StatusTuple,
    ValuePresence,
)
from spine_sim.foundation.reader import FilterSpec, ResultReader
from spine_sim.foundation.registry import (
    BUNDLE_SCHEMA_VERSION,
    RESULT_API_VERSION,
    ArrayDescriptor,
    CompatibilityClass,
    DataClassification,
    DatasetClass,
    DatasetDescriptor,
    FieldMetadata,
    ResultExtensionDescriptor,
    SchemaRegistry,
)
from spine_sim.foundation.replay import make_replay_manifest, runtime_dependency_versions
from spine_sim.foundation.writer import ResultWriter, make_run_envelope

PERFORMANCE_DATASET_ID = "validation_perf.accepted_points.per_entity"
PERFORMANCE_ARRAY_ID = "validation_perf.arrays.chunk_probe"


@dataclass(frozen=True, slots=True)
class PerformanceRow(RecordBase):
    __dataset_id__ = PERFORMANCE_DATASET_ID

    run_id: str
    case_id: str
    point_id: str
    row_index: int
    value_0: float
    value_1: float
    value_2: float
    value_3: float
    value_4: float
    value_5: float
    value_6: float
    value_7: float
    source_identity: SourceIdentity

    def semantic_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "point_id": self.point_id,
            "row_index": self.row_index,
            "value_0": self.value_0,
            "value_1": self.value_1,
            "value_2": self.value_2,
            "value_3": self.value_3,
            "value_4": self.value_4,
            "value_5": self.value_5,
            "value_6": self.value_6,
            "value_7": self.value_7,
            "source_identity": self.source_identity.value,
        }

    def storage_dict(self) -> dict[str, Any]:
        return {"run_id": self.run_id, **self.semantic_dict()}


def _field(
    dataset_id: str,
    name: str,
    dtype: str,
    *,
    shape: tuple[int | None, ...] = (),
) -> FieldMetadata:
    return FieldMetadata(
        field_id=f"{dataset_id}.{name}",
        namespace="validation_perf",
        owner_module="M00_PERFORMANCE_FIXTURE",
        semantics=f"VALIDATION_ONLY performance field {name}; no physical meaning",
        classification=DataClassification.CANONICAL_RAW,
        dtype=dtype,
        shape=shape,
        dimensions=("logical_index",) if shape else (),
        raggedness="fixed",
        unit="1",
        frame="M00_VALIDATION_FRAME" if shape else "NOT_APPLICABLE",
        reference_point="M00_VALIDATION_ORIGIN" if shape else "NOT_APPLICABLE",
        sign_semantics="VALIDATION_ONLY",
        action_semantics="NOT_APPLICABLE_NO_PHYSICS",
        indices=("case_id", "row_index"),
        sampling_cadence="per_validation_row",
        storage_frequency="every_validation_row",
        ownership="accepted",
        null_policy="not_null",
        source_identity=SourceIdentity.VALIDATION_ONLY,
        authority_refs=("M00_FOUNDATION_REQUIREMENTS 1.0.0 section 14",),
        maturity=Maturity.validation_only_implemented(),
        introduced_version="1.0.0",
        deprecated_version=None,
        storage_dataset=dataset_id,
        encoding="zarr_v3_lossless" if shape else "parquet_zstd_lossless",
        precision="float64" if dtype == "float64" else "exact",
        required=True,
    )


def performance_extension() -> ResultExtensionDescriptor:
    fields = (
        _field(PERFORMANCE_DATASET_ID, "run_id", "utf8"),
        _field(PERFORMANCE_DATASET_ID, "case_id", "utf8"),
        _field(PERFORMANCE_DATASET_ID, "point_id", "utf8"),
        _field(PERFORMANCE_DATASET_ID, "row_index", "int64"),
        *(_field(PERFORMANCE_DATASET_ID, f"value_{index}", "float64") for index in range(8)),
        _field(PERFORMANCE_DATASET_ID, "source_identity", "utf8"),
    )
    dataset = DatasetDescriptor(
        PERFORMANCE_DATASET_ID,
        "validation_perf",
        "M00_PERFORMANCE_FIXTURE",
        "1.0.0",
        DatasetClass.ACCEPTED,
        PerformanceRow,
        fields,
        ("point_id",),
        ("case_id",),
        False,
        SourceIdentity.VALIDATION_ONLY,
    )
    array = ArrayDescriptor(
        _field("validation_perf.arrays", "chunk_probe", "float64", shape=(None,)),
        "1.0.0",
        default_chunk_shape=(524288,),
    )
    return ResultExtensionDescriptor(
        "validation_perf",
        "M00_PERFORMANCE_FIXTURE",
        "1.0.0",
        (dataset,),
        (array,),
        (),
        ("run_id", "case_id", "point_id"),
        SourceIdentity.VALIDATION_ONLY,
        Maturity.validation_only_implemented(),
        CompatibilityClass.ADDITIVE_MINOR,
    )


def _rows(run_id: str, case_id: str, count: int) -> list[PerformanceRow]:
    output: list[PerformanceRow] = []
    encoded_case = json.dumps(case_id, ensure_ascii=False, separators=(",", ":")).encode()
    point_prefix = b'{"content":{"case":' + encoded_case + b',"row":'
    point_suffix = b'},"kind":"point"}'
    for index in range(count):
        base = float(index)
        point_id = (
            f"point:{hashlib.sha256(point_prefix + str(index).encode() + point_suffix).hexdigest()}"
        )
        output.append(
            PerformanceRow(
                run_id,
                case_id,
                point_id,
                index,
                base,
                base + 1.0,
                base + 2.0,
                base + 3.0,
                base + 4.0,
                base + 5.0,
                base + 6.0,
                base + 7.0,
                SourceIdentity.VALIDATION_ONLY,
            )
        )
    return output


def _validation_status(outcome: AttemptOutcome, reason: str) -> StatusTuple:
    return StatusTuple(
        ValuePresence.PRESENT if outcome is AttemptOutcome.ACCEPTED else ValuePresence.NULL,
        CapabilityStatus.SUPPORTED,
        outcome,
        PhysicalFeasibility.NOT_ASSESSED,
        CertificationStatus.NOT_CERTIFIABLE,
        reason,
        "M00 I/O performance validation only; no physical interpretation",
        ("M00_FOUNDATION_REQUIREMENTS 1.0.0 section 14",),
    )


def _performance_event(run_id: str, case_id: str) -> CommittedEventBase:
    return CommittedEventBase(
        event_id=stable_content_id("event", {"case": case_id, "kind": "PERFORMANCE_MARKER"}),
        source_event_ids=("M00_PERFORMANCE_SOURCE_EVENT",),
        hierarchy="VALIDATION_ONLY",
        entity_ids=("M00_PERFORMANCE_ENTITY",),
        run_id=run_id,
        case_id=case_id,
        design_id="design:M00_PERFORMANCE",
        seed_id="seed:NO_RNG_PERFORMANCE",
        surface_realization_id="surface:NO_SURFACE_PERFORMANCE",
        event_kind="PERFORMANCE_MARKER",
        raw_event_function=0.0,
        event_function_unit="1",
        numerical_scaling_id="NONE_VALIDATION_ONLY",
        path_coordinate=0.0,
        path_bracket=(0.0, 0.0),
        fraction_basis="VALIDATION_INDEX",
        localization_error=0.0,
        pre_event_accepted_state_id="state:M00_PERFORMANCE_ROOT",
        event_point_trial_id="trial:M00_PERFORMANCE_EVENT_POINT",
        post_event_accepted_state_id=None,
        post_event_status=StatusTuple(
            ValuePresence.NULL,
            CapabilityStatus.NOT_APPLICABLE,
            AttemptOutcome.NOT_ATTEMPTED,
            PhysicalFeasibility.NOT_ASSESSED,
            CertificationStatus.NOT_CERTIFIABLE,
            "NO_POST_EVENT_STATE",
            "performance marker does not advance a physical state",
        ),
        simultaneous_group_id=None,
        dependency_edges=(),
        cascade_round=0,
        pre_payload_refs=(),
        event_payload_refs=("validation_perf:event",),
        post_payload_refs=(),
        uncertainty_refs=(),
        recoverability="NOT_APPLICABLE_NO_PHYSICS",
        stability="NOT_APPLICABLE_NO_PHYSICS",
        terminal_classification="NON_TERMINAL_VALIDATION_MARKER",
        status=_validation_status(AttemptOutcome.ACCEPTED, "PERFORMANCE_EVENT"),
        source_identity=SourceIdentity.VALIDATION_ONLY,
        maturity=Maturity.validation_only_implemented(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        committed=True,
        commit_receipt_id=None,
    )


def _logical_ten_gib_probe(path: Path) -> dict[str, Any]:
    logical_bytes = 10 * 1024**3
    element_count = logical_bytes // np.dtype(np.float64).itemsize
    chunk_elements = 524288
    group = zarr.open_group(path, mode="w", zarr_format=3)
    array = group.create_array(
        "values",
        shape=(element_count,),
        dtype=np.float64,
        chunks=(chunk_elements,),
        fill_value=0.0,
        overwrite=True,
    )
    process = psutil.Process()
    baseline = process.memory_info().rss
    peak = baseline
    checksum = 0.0
    started = time.perf_counter()
    for start in range(0, element_count, chunk_elements):
        block = np.asarray(
            array[start : min(start + chunk_elements, element_count)],
            dtype=np.float64,
        ).reshape(-1)
        checksum += float(block[0]) if block.size else 0.0
        peak = max(peak, process.memory_info().rss)
    elapsed = time.perf_counter() - started
    return {
        "logical_bytes": logical_bytes,
        "chunk_bytes": chunk_elements * 8,
        "elapsed_seconds": elapsed,
        "peak_extra_rss_bytes": max(0, peak - baseline),
        "checksum": checksum,
    }


def run_performance_fixture(
    destination: Path,
    *,
    case_count: int = 1000,
    rows_per_case: int = 1000,
) -> dict[str, Any]:
    registry = SchemaRegistry()
    registry.register_extension(performance_extension())
    registry_hash = registry.freeze()
    config = _resolved_config("performance_run")
    case_ids = tuple(f"case:M00_PERF_{index:04d}" for index in range(case_count))
    source_hashes = {"M00": semantic_hash("performance")}
    replay_seed = {"case_count": case_count, "rows_per_case": rows_per_case}
    envelope = make_run_envelope(
        registry_hash=registry_hash,
        resolved_run_config=config,
        operation_kind="M00_VALIDATION_ONLY_PERFORMANCE",
        operation_profile="STANDARD_IO_FIXTURE",
        source_file_hashes=source_hashes,
        replay_manifest=replay_seed,
        git_commit="PERFORMANCE_FIXTURE",
        dirty_status="recorded-in-report",
        provenance_labels=("VALIDATION_ONLY", "not_certifiable"),
    )
    replay = make_replay_manifest(
        run_id=envelope.run_id,
        run_fingerprint=envelope.run_fingerprint,
        result_api_version=RESULT_API_VERSION,
        bundle_schema_version=BUNDLE_SCHEMA_VERSION,
        resolved_run_config_hash=config.semantic_hash,
        resolved_case_config_hashes={case_id: config.semantic_hash for case_id in case_ids},
        source_hashes=source_hashes,
        registry_hash=registry_hash,
        git_commit="PERFORMANCE_FIXTURE",
        dirty_status="recorded-in-report",
        case_execution_plan=case_ids,
        idempotency_keys=tuple(f"M00_PERFORMANCE_TX_{index:04d}" for index in range(case_count)),
        surface_identities=("surface:NO_SURFACE_PERFORMANCE",),
    )
    replay_payload = dataclasses.asdict(replay)
    envelope = dataclasses.replace(
        envelope,
        replay_manifest_id=replay.replay_manifest_id,
        replay_manifest_hash=semantic_hash(replay_payload),
    )
    writer_started = time.perf_counter()
    writer = ResultWriter.create_run_bundle(destination, registry=registry, run_envelope=envelope)
    writer.write_resolved_config_and_provenance(
        config,
        provenance={"source_identity": "VALIDATION_ONLY", "physical_interpretation": "none"},
        replay_manifest=replay_payload,
    )
    total_rows = case_count * rows_per_case + (10_000 - rows_per_case)

    def write_case(case_index: int) -> None:
        case_id = f"case:M00_PERF_{case_index:04d}"
        case_rows = 10_000 if case_index == 0 else rows_per_case
        writer.create_case_shard(
            case_id,
            design_id="design:M00_PERFORMANCE",
            seed_id="seed:NO_RNG_PERFORMANCE",
            surface_realization_id="surface:NO_SURFACE_PERFORMANCE",
            resolved_case_config=config,
        )
        transaction = writer.begin_transaction(
            case_id,
            "state:M00_PERFORMANCE_ROOT",
            f"M00_PERFORMANCE_TX_{case_index:04d}",
        )
        transaction.stage_accepted_point(*_rows(envelope.run_id, case_id, case_rows))
        if case_index == 0:
            transaction.stage_committed_events(_performance_event(envelope.run_id, case_id))
            transaction.stage_chunked_array(
                RegisteredArrayPayload(
                    PERFORMANCE_ARRAY_ID,
                    case_id,
                    np.arange(4096, dtype=np.float64),
                    np.ones(4096, dtype=np.bool_),
                    np.zeros(4096, dtype=np.uint8),
                    "1",
                    "M00_VALIDATION_FRAME",
                    "M00_VALIDATION_ORIGIN",
                    SourceIdentity.VALIDATION_ONLY,
                )
            )
        transaction.prepare()
        transaction.commit()
        if case_index == 0:
            writer.record_rejected_trial(
                RejectedTrialBase(
                    trial_id="trial:M00_PERFORMANCE_REJECTED",
                    run_id=envelope.run_id,
                    case_id=case_id,
                    parent_accepted_state_id="state:M00_PERFORMANCE_ROOT",
                    request_hash=semantic_hash("performance-rejected-request"),
                    candidate_hash=semantic_hash("performance-rejected-candidate"),
                    requested_path_target=None,
                    status=_validation_status(
                        AttemptOutcome.REJECTED_TRIAL, "PERFORMANCE_REJECTED"
                    ),
                    reason_codes=("VALIDATION_ONLY_INTENTIONAL_REJECTION",),
                    diagnostic_summary="Intentional performance fixture diagnostic; no physical meaning.",
                    optional_full_payload_ref=None,
                    last_valid_state_id="state:M00_PERFORMANCE_ROOT",
                    source_identity=SourceIdentity.VALIDATION_ONLY,
                )
            )
        writer.finalize_case(case_id)

    writer_workers = min(8, case_count)
    with ThreadPoolExecutor(max_workers=writer_workers) as executor:
        tuple(executor.map(write_case, range(case_count)))
    writer.publish_run_manifest()
    writer_seconds = time.perf_counter() - writer_started

    open_started = time.perf_counter()
    reader = ResultReader.open(destination, VerifyMode.MANIFEST)
    open_seconds = time.perf_counter() - open_started
    catalog_started = time.perf_counter()
    fields = reader.list_fields("validation_perf.*", include_non_default=True)
    catalog_seconds = time.perf_counter() - catalog_started
    single_case_started = time.perf_counter()
    single_case = reader.query(
        PERFORMANCE_DATASET_ID,
        ("row_index", "value_0"),
        filters=(FilterSpec("case_id", "==", "case:M00_PERF_0000"),),
        batch_size=10000,
        include_non_default=True,
    ).read_all()
    single_case_seconds = time.perf_counter() - single_case_started
    scan_started = time.perf_counter()
    scan = reader.query(
        PERFORMANCE_DATASET_ID,
        tuple(f"value_{index}" for index in range(8)),
        batch_size=65536,
        include_non_default=True,
    ).read_all()
    scan_seconds = time.perf_counter() - scan_started
    logical_probe = _logical_ten_gib_probe(destination.parent / "M00_LOGICAL_10_GIB.zarr")
    metrics = {
        "writer_seconds": writer_seconds,
        "open_and_catalog_manifest_seconds": open_seconds,
        "field_catalog_seconds": catalog_seconds,
        "single_case_10000_point_first_result_seconds": single_case_seconds,
        "eight_column_million_row_scan_seconds": scan_seconds,
        "single_case_rows": single_case.num_rows,
        "scan_rows": scan.num_rows,
        "field_count": len(fields),
        "logical_10_gib_batch_probe": logical_probe,
    }
    limits = {
        "writer_seconds": 30.0,
        "open_and_catalog_manifest_seconds": 2.0,
        "field_catalog_seconds": 0.5,
        "single_case_10000_point_first_result_seconds": 1.0,
        "eight_column_million_row_scan_seconds": 5.0,
        "logical_10_gib_peak_extra_rss_bytes": 512 * 1024**2,
    }
    checks = {
        "writer": writer_seconds <= limits["writer_seconds"],
        "open": open_seconds <= limits["open_and_catalog_manifest_seconds"],
        "field_catalog": catalog_seconds <= limits["field_catalog_seconds"],
        "single_case": single_case_seconds
        <= limits["single_case_10000_point_first_result_seconds"],
        "scan": scan_seconds <= limits["eight_column_million_row_scan_seconds"],
        "bounded_memory": logical_probe["peak_extra_rss_bytes"]
        <= limits["logical_10_gib_peak_extra_rss_bytes"],
        "fixture_shape": case_count == 1000
        and total_rows >= 1_000_000
        and single_case.num_rows == 10_000,
    }
    disk = shutil.disk_usage(destination)
    report = {
        "report_schema_version": "1.0.0",
        "fixture": {
            "source_identity": "VALIDATION_ONLY",
            "case_count": case_count,
            "rows_per_case": rows_per_case,
            "accepted_rows": total_rows,
            "writer_workers": writer_workers,
            "canonical_numeric_dtype": "float64",
            "bundle": destination.as_posix(),
        },
        "environment": {
            "hardware": platform.processor() or "UNAVAILABLE",
            "machine": platform.machine(),
            "cpu_logical_count": os.cpu_count(),
            "physical_memory_bytes": psutil.virtual_memory().total,
            "disk_total_bytes": disk.total,
            "disk_free_bytes_after": disk.free,
            "os": platform.platform(),
            "python": sys.version,
            "dependencies": runtime_dependency_versions(("numpy", "pyarrow", "zarr", "psutil")),
        },
        "metrics": metrics,
        "limits": limits,
        "checks": checks,
        "overall_pass": all(checks.values()),
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = run_performance_fixture(args.destination)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["overall_pass"] else 1)


if __name__ == "__main__":
    main()
