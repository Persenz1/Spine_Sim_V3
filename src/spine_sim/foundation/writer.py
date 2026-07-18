"""Strongly typed ResultWriter and commit-marker-gated transactions."""

from __future__ import annotations

import dataclasses
import json
import shutil
import time
import uuid
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

from .canonical import semantic_hash, stable_content_id, uuid7
from .config import ResolvedConfig
from .errors import ContractViolation, IdempotencyConflict, TransactionError
from .integrity import build_integrity_index, committed_markers
from .models import (
    AcceptedPointBase,
    CaseIndexBase,
    CommitReceiptBase,
    CommittedEventBase,
    RecordBase,
    RegisteredArrayPayload,
    RejectedTrialBase,
    RunEnvelope,
    SourceIdentity,
    SummaryBase,
    ValuePresence,
)
from .registry import BUNDLE_SCHEMA_VERSION, RESULT_API_VERSION, DatasetClass, SchemaRegistry
from .storage import (
    read_json,
    relative_entry,
    remove_owned_path,
    safe_component,
    write_json_atomic,
    write_parquet_records,
    write_zarr_array,
)

FaultInjector = Callable[[str], None]


def _noop_fault(_: str) -> None:
    return None


class ResultWriter:
    """M00 canonical bundle owner; no physical commit-eligibility logic lives here."""

    DIRECTORY_NAMES = (
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
        "output",
        "integrity",
    )

    def __init__(
        self,
        root: Path,
        registry: SchemaRegistry,
        run_envelope: RunEnvelope,
        *,
        parquet_compression: str = "zstd",
        zarr_compression_level: int = 3,
        zarr_chunk_shape: tuple[int, ...] = (512, 512),
        fault_injector: FaultInjector | None = None,
    ) -> None:
        self.root = root
        self.registry = registry
        self.run_envelope = run_envelope
        self.parquet_compression = parquet_compression
        self.zarr_compression_level = zarr_compression_level
        self.zarr_chunk_shape = zarr_chunk_shape
        self.fault_injector = fault_injector or _noop_fault
        self._case_drafts: set[str] = set()
        self._final_cases: set[str] = set()
        self._case_identities: dict[str, dict[str, str]] = {}
        self._record_identity_names: dict[type[RecordBase], tuple[str, ...]] = {}
        self._config_hash = run_envelope.resolved_run_config_hash
        self._committed_marker_cache = [marker for _, marker in committed_markers(root)]

    @classmethod
    def create_run_bundle(
        cls,
        destination: str | Path,
        *,
        registry: SchemaRegistry,
        run_envelope: RunEnvelope,
        parquet_compression: str = "zstd",
        zarr_compression_level: int = 3,
        zarr_chunk_shape: tuple[int, ...] = (512, 512),
        fault_injector: FaultInjector | None = None,
    ) -> ResultWriter:
        root = Path(destination)
        if root.exists():
            raise FileExistsError(root)
        registry_hash = registry.freeze()
        if run_envelope.registry_hash != registry_hash:
            raise ContractViolation("run envelope registry hash is stale")
        if (
            run_envelope.result_api_version != RESULT_API_VERSION
            or run_envelope.bundle_schema_version != BUNDLE_SCHEMA_VERSION
        ):
            raise ContractViolation("run envelope API/bundle schema version mismatch")
        root.mkdir(parents=True)
        for directory in cls.DIRECTORY_NAMES:
            (root / directory).mkdir()
        (root / "transactions" / "staging").mkdir()
        (root / "transactions" / "committed").mkdir()
        write_json_atomic(root / "schemas" / "registry.json", registry.snapshot())
        registry.validate_record(run_envelope)
        write_parquet_records(
            root / "indices" / "runs.parquet",
            [run_envelope.storage_dict()],
            compression=parquet_compression,
        )
        write_json_atomic(
            root / "provenance" / "run_envelope.json", dataclasses.asdict(run_envelope)
        )
        return cls(
            root,
            registry,
            run_envelope,
            parquet_compression=parquet_compression,
            zarr_compression_level=zarr_compression_level,
            zarr_chunk_shape=zarr_chunk_shape,
            fault_injector=fault_injector,
        )

    @staticmethod
    def register_extension_schema(registry: SchemaRegistry, descriptor: Any) -> None:
        registry.register_extension(descriptor)

    def write_resolved_config_and_provenance(
        self,
        resolved_run_config: ResolvedConfig,
        *,
        provenance: Mapping[str, Any],
        replay_manifest: Mapping[str, Any],
    ) -> None:
        if resolved_run_config.semantic_hash != self.run_envelope.resolved_run_config_hash:
            raise ContractViolation("resolved run config hash does not match run envelope")
        write_json_atomic(
            self.root / "config" / "resolved_run_config.json", resolved_run_config.as_manifest()
        )
        write_json_atomic(self.root / "provenance" / "provenance.json", dict(provenance))
        write_json_atomic(self.root / "replay" / "replay_manifest.json", dict(replay_manifest))

    def create_case_shard(
        self,
        case_id: str,
        *,
        design_id: str,
        seed_id: str,
        surface_realization_id: str,
        resolved_case_config: ResolvedConfig,
    ) -> None:
        safe_case = safe_component(case_id)
        index_path = self.root / "indices" / "cases" / f"{safe_case}.json"
        if index_path.exists() or case_id in self._case_drafts:
            raise ContractViolation(f"case shard already exists: {case_id}")
        for directory in (
            "accepted_points",
            "committed_events",
            "rejected_trials",
            "summaries",
            "arrays",
            "transactions/receipts",
        ):
            (self.root / directory / safe_case).mkdir(parents=True, exist_ok=True)
        case_config_path = self.root / "config" / "cases" / f"{safe_case}.json"
        write_json_atomic(case_config_path, resolved_case_config.as_manifest())
        draft = {
            "case_id": case_id,
            "run_id": self.run_envelope.run_id,
            "design_id": design_id,
            "seed_id": seed_id,
            "surface_realization_id": surface_realization_id,
            "resolved_case_config_hash": resolved_case_config.semantic_hash,
            "status": "DRAFT",
        }
        write_json_atomic(index_path, draft)
        self._case_drafts.add(case_id)
        self._case_identities[case_id] = {
            "run_id": self.run_envelope.run_id,
            "case_id": case_id,
            "design_id": design_id,
            "seed_id": seed_id,
            "surface_realization_id": surface_realization_id,
        }

    def begin_transaction(
        self, case_id: str, parent_state_id: str, idempotency_key: str
    ) -> ResultTransaction:
        if case_id not in self._case_drafts or case_id in self._final_cases:
            raise TransactionError(f"case is not open for transactions: {case_id}")
        existing = self._find_idempotency(case_id, idempotency_key)
        return ResultTransaction(self, case_id, parent_state_id, idempotency_key, existing)

    def record_rejected_trial(self, record: RejectedTrialBase) -> Path:
        descriptor = self.registry.validate_record(record)
        self._validate_case_identity(record)
        if descriptor.dataset_class is not DatasetClass.REJECTED:
            raise ContractViolation("record_rejected_trial accepts only rejected records")
        if (
            record.accepted_state_advanced
            or record.committed_event_id is not None
            or record.commit_receipt_id is not None
        ):
            raise ContractViolation("rejected trial cannot own accepted/event/receipt identity")
        path = (
            self.root
            / "rejected_trials"
            / safe_component(record.case_id)
            / f"{safe_component(record.trial_id)}.parquet"
        )
        if path.exists():
            raise ContractViolation(f"rejected trial already exists: {record.trial_id}")
        write_parquet_records(path, [record.storage_dict()], compression=self.parquet_compression)
        return path

    def write_versioned_summary(self, record: SummaryBase) -> Path:
        descriptor = self.registry.validate_record(record)
        self._validate_case_identity(record)
        if descriptor.dataset_class is not DatasetClass.SUMMARY:
            raise ContractViolation("write_versioned_summary accepts only summary records")
        included = set(record.included_dataset_classes)
        if "rejected" in included and "diagnostic" not in record.summary_kind.lower():
            raise ContractViolation("physical/design summaries cannot consume rejected trials")
        case_dir = (
            self.root
            / "summaries"
            / safe_component(record.case_id)
            / descriptor.dataset_id.replace(".", "__")
        )
        path = case_dir / f"{safe_component(record.summary_id)}.parquet"
        if path.exists():
            raise ContractViolation(f"summary already exists: {record.summary_id}")
        write_parquet_records(path, [record.storage_dict()], compression=self.parquet_compression)
        return path

    def finalize_case(self, case_id: str) -> CaseIndexBase:
        if case_id not in self._case_drafts:
            raise TransactionError(f"unknown case: {case_id}")
        index_path = self.root / "indices" / "cases" / f"{safe_component(case_id)}.json"
        draft = read_json(index_path)
        receipts = [
            marker for marker in self._committed_marker_cache if marker["case_id"] == case_id
        ]
        receipt_ids = sorted(marker["receipt_id"] for marker in receipts)
        record = CaseIndexBase(
            run_id=self.run_envelope.run_id,
            case_id=case_id,
            design_id=draft["design_id"],
            seed_id=draft["seed_id"],
            surface_realization_id=draft["surface_realization_id"],
            finalized=True,
            receipt_set_hash=semantic_hash(receipt_ids),
            source_identity=SourceIdentity.VALIDATION_ONLY
            if "VALIDATION_ONLY" in self.run_envelope.provenance_labels
            else SourceIdentity.DEV_POLICY,
        )
        self.registry.validate_record(record)
        write_parquet_records(
            self.root / "indices" / "cases" / f"{safe_component(case_id)}.parquet",
            [record.storage_dict()],
            compression=self.parquet_compression,
        )
        index_payload = {
            **draft,
            "status": "FINAL",
            "receipt_ids": receipt_ids,
            "record": record.semantic_dict(),
        }
        write_json_atomic(index_path, index_payload)
        self._final_cases.add(case_id)
        return record

    def publish_run_manifest(self) -> Path:
        if self._case_drafts - self._final_cases:
            raise TransactionError("all case shards must be finalized before run publication")
        integrity = build_integrity_index(self.root)
        write_json_atomic(self.root / "integrity" / "index.json", integrity)
        markers = list(self._committed_marker_cache)
        auxiliary_datasets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        auxiliary_sources = (
            ("core.indices.runs", (self.root / "indices").glob("runs.parquet")),
            ("core.indices.cases", (self.root / "indices" / "cases").glob("*.parquet")),
            (
                "core.rejected_trials.diagnostics",
                (self.root / "rejected_trials").rglob("*.parquet"),
            ),
            ("core.summaries.case", (self.root / "summaries").rglob("*.parquet")),
        )
        for default_dataset_id, paths in auxiliary_sources:
            for path in sorted(paths):
                dataset_id = default_dataset_id
                if default_dataset_id == "core.summaries.case":
                    for candidate in self.registry.datasets:
                        if candidate.replace(".", "__") in path.parent.name:
                            dataset_id = candidate
                            break
                rows = pq.read_table(path).to_pylist()
                from .canonical import source_file_hash

                auxiliary_datasets[dataset_id].append(
                    {
                        "path": path.relative_to(self.root).as_posix(),
                        "byte_sha256": source_file_hash(path),
                        "semantic_hash": semantic_hash(rows),
                        "row_count": len(rows),
                    }
                )
        bundle_semantic_hash = semantic_hash(
            {
                "run_fingerprint": self.run_envelope.run_fingerprint,
                "registry_hash": self.registry.snapshot_hash,
                "config_hash": self._config_hash,
                "receipt_candidates": sorted(
                    (item["candidate_hash"], item["semantic_content_hash"]) for item in markers
                ),
                "cases": sorted(self._final_cases),
            }
        )
        manifest = {
            "bundle_kind": "spine-result",
            "bundle_schema_version": BUNDLE_SCHEMA_VERSION,
            "result_api_version": RESULT_API_VERSION,
            "run_id": self.run_envelope.run_id,
            "run_fingerprint": self.run_envelope.run_fingerprint,
            "registry_hash": self.registry.snapshot_hash,
            "resolved_run_config_hash": self._config_hash,
            "case_ids": sorted(self._final_cases),
            "receipt_set_hash": integrity["receipt_set_hash"],
            "bundle_semantic_hash": bundle_semantic_hash,
            "auxiliary_datasets": dict(sorted(auxiliary_datasets.items())),
            "canonical_numeric_dtype": "float64",
            "parquet_compression": self.parquet_compression,
            "zarr_format": 3,
            "created_at_utc_ns": time.time_ns(),
        }
        path = self.root / "bundle_manifest.json"
        self.fault_injector("manifest_publish")
        write_json_atomic(path, manifest)
        return path

    def recover_crash_artifacts(self) -> dict[str, int]:
        staging_root = self.root / "transactions" / "staging"
        removed_staging = 0
        for child in list(staging_root.iterdir()):
            remove_owned_path(child, root=self.root)
            removed_staging += 1
        referenced = {
            entry["path"]
            for _, marker in committed_markers(self.root)
            for entry in list(marker.get("datasets", {}).values())
            + list(marker.get("arrays", {}).values())
        }
        removed_orphans = 0
        for base_name in ("accepted_points", "committed_events", "transactions/receipts"):
            for file_path in (self.root / base_name).rglob("*.parquet"):
                relative = file_path.relative_to(self.root).as_posix()
                if relative not in referenced:
                    remove_owned_path(file_path, root=self.root)
                    removed_orphans += 1
        for array_path in (self.root / "arrays").rglob("*.zarr"):
            relative = array_path.relative_to(self.root).as_posix()
            if relative not in referenced:
                remove_owned_path(array_path, root=self.root)
                removed_orphans += 1
        return {"removed_staging": removed_staging, "removed_orphans": removed_orphans}

    def _find_idempotency(self, case_id: str, key: str) -> dict[str, Any] | None:
        for marker in self._committed_marker_cache:
            if marker["case_id"] == case_id and marker["idempotency_key"] == key:
                return marker
        return None

    def _validate_case_identity(self, record: RecordBase) -> None:
        case_id = getattr(record, "case_id", None)
        if not isinstance(case_id, str):
            raise ContractViolation("case-partitioned record requires a string case_id")
        identity = self._case_identities.get(case_id)
        if identity is None:
            raise ContractViolation(f"record references unknown case shard: {case_id}")
        record_type = type(record)
        names = self._record_identity_names.get(record_type)
        if names is None:
            names = tuple(name for name in identity if hasattr(record, name))
            self._record_identity_names[record_type] = names
        for name in names:
            expected = identity[name]
            actual = getattr(record, name)
            if actual != expected:
                raise ContractViolation(
                    f"record {name} does not match case partition identity",
                    details={"case_id": case_id, "expected": expected, "actual": actual},
                )


class ResultTransaction:
    """Side-effect-free candidate staging followed by marker-gated publication."""

    def __init__(
        self,
        writer: ResultWriter,
        case_id: str,
        parent_state_id: str,
        idempotency_key: str,
        existing_marker: dict[str, Any] | None,
    ) -> None:
        self.writer = writer
        self.case_id = case_id
        self.parent_state_id = parent_state_id
        self.idempotency_key = idempotency_key
        self.existing_marker = existing_marker
        self.transaction_id = uuid.uuid4().hex
        self.staging_root = writer.root / "transactions" / "staging" / self.transaction_id
        self.staging_root.mkdir(parents=True)
        self._records: dict[str, list[RecordBase]] = defaultdict(list)
        self._arrays: list[RegisteredArrayPayload] = []
        self._ledger_refs: tuple[str, ...] = ()
        self._semantic_records: dict[str, list[dict[str, Any]]] = {}
        self._semantic_dataset_hashes: dict[str, str] = {}
        self._prepared = False
        self._candidate_hash: str | None = None
        self._ordered_intents_hash: str | None = None
        self._closed = False

    def stage_accepted_point(self, *records: RecordBase) -> None:
        self._stage_records(records, DatasetClass.ACCEPTED)

    def stage_committed_events(self, *records: RecordBase) -> None:
        self._stage_records(records, DatasetClass.EVENT)

    def stage_state_and_ledger_references(self, refs: Iterable[str]) -> None:
        self._ensure_open()
        self._ledger_refs = tuple(refs)

    def stage_chunked_array(self, payload: RegisteredArrayPayload) -> None:
        self._ensure_open()
        descriptor = self.writer.registry.arrays.get(payload.field_id)
        if descriptor is None:
            raise ContractViolation(f"array field is not registered: {payload.field_id}")
        if payload.case_id != self.case_id:
            raise ContractViolation("array partition does not belong to transaction case")
        if (
            payload.unit != descriptor.field.unit
            or payload.frame != descriptor.field.frame
            or payload.reference_point != descriptor.field.reference_point
        ):
            raise ContractViolation("array unit/frame/reference point mismatch")
        materialized = np.asarray(payload.data)
        if str(materialized.dtype) != descriptor.canonical_dtype:
            raise ContractViolation(
                f"array dtype must exactly match {descriptor.canonical_dtype}; implicit conversion is forbidden"
            )
        expected_shape = descriptor.field.shape
        if expected_shape and (
            len(materialized.shape) != len(expected_shape)
            or any(
                expected is not None and actual != expected
                for actual, expected in zip(materialized.shape, expected_shape, strict=True)
            )
        ):
            raise ContractViolation("array shape does not match registered descriptor")
        self._arrays.append(payload)

    def prepare(self) -> str:
        self._ensure_open()
        self.writer.fault_injector("prepare")
        if not self._records:
            raise TransactionError("transaction has no staged records")
        accepted = [
            record
            for records in self._records.values()
            for record in records
            if isinstance(record, AcceptedPointBase)
        ]
        if accepted:
            ordered = sorted(accepted, key=lambda value: value.accepted_point_index)
            if ordered[0].parent_state_id != self.parent_state_id:
                raise TransactionError(
                    "first accepted point parent does not match transaction parent"
                )
            for previous, current in pairwise(ordered):
                if current.parent_state_id != previous.accepted_state_id:
                    raise TransactionError("accepted point lineage is not continuous")
        event_records = [
            record
            for records in self._records.values()
            for record in records
            if isinstance(record, CommittedEventBase)
        ]
        for event in event_records:
            if not event.committed:
                raise ContractViolation(
                    "stage_committed_events requires committed=true candidate records"
                )
            if event.commit_receipt_id is not None:
                raise ContractViolation("staged event cannot already own a receipt")
            if (
                event.post_event_accepted_state_id is None
                and event.post_event_status.value_presence is not ValuePresence.NULL
            ) or (
                event.post_event_accepted_state_id is not None
                and event.post_event_status.value_presence is ValuePresence.NULL
            ):
                raise ContractViolation(
                    "post-event accepted state and explicit value-presence status disagree"
                )
        self._semantic_records = {
            key: [record.semantic_dict() for record in values]
            for key, values in sorted(self._records.items())
        }
        self._semantic_dataset_hashes = {
            key: semantic_hash(values) for key, values in self._semantic_records.items()
        }
        candidate = {
            "case_id": self.case_id,
            "parent_state_id": self.parent_state_id,
            "datasets": {
                key: {"row_count": len(self._semantic_records[key]), "semantic_hash": digest}
                for key, digest in sorted(self._semantic_dataset_hashes.items())
            },
            "arrays": [
                {
                    "field_id": item.field_id,
                    "data_hash": semantic_hash(np.asarray(item.data)),
                    "validity_hash": semantic_hash(np.asarray(item.validity))
                    if item.validity is not None
                    else None,
                    "status_hash": semantic_hash(np.asarray(item.status))
                    if item.status is not None
                    else None,
                }
                for item in self._arrays
            ],
            "ledger_refs": self._ledger_refs,
        }
        self._candidate_hash = semantic_hash(candidate)
        self._ordered_intents_hash = semantic_hash(
            [*sorted(self._records), *(item.field_id for item in self._arrays), *self._ledger_refs]
        )
        if self.existing_marker is not None:
            if self.existing_marker["candidate_hash"] != self._candidate_hash:
                raise IdempotencyConflict(
                    "same idempotency key was used for different candidate content",
                    details={"idempotency_key": self.idempotency_key},
                )
        self._prepared = True
        return self._candidate_hash

    def commit(self) -> CommitReceiptBase:
        self._ensure_open()
        if not self._prepared or self._candidate_hash is None or self._ordered_intents_hash is None:
            raise TransactionError("prepare must succeed before commit")
        if self.existing_marker is not None:
            receipt = self._read_existing_receipt(self.existing_marker)
            self.rollback()
            return receipt
        receipt_id = stable_content_id(
            "receipt",
            {
                "parent_state_id": self.parent_state_id,
                "candidate_hash": self._candidate_hash,
                "idempotency_key": self.idempotency_key,
                "ordered_intents_hash": self._ordered_intents_hash,
            },
        )
        safe_receipt = safe_component(receipt_id.replace(":", "_"))
        accepted = [
            record
            for records in self._records.values()
            for record in records
            if isinstance(record, AcceptedPointBase)
        ]
        committed_state_id = (
            max(accepted, key=lambda value: value.accepted_point_index).accepted_state_id
            if accepted
            else self.parent_state_id
        )
        final_paths = self._planned_paths(safe_receipt)
        marker_preimage = {
            "receipt_id": receipt_id,
            "case_id": self.case_id,
            "candidate_hash": self._candidate_hash,
            "paths": sorted(final_paths.values()),
        }
        commit_marker_hash = semantic_hash(marker_preimage)
        receipt = CommitReceiptBase(
            receipt_id=receipt_id,
            idempotency_key=self.idempotency_key,
            parent_state_id=self.parent_state_id,
            committed_state_id=committed_state_id,
            candidate_hash=self._candidate_hash,
            ordered_intents_hash=self._ordered_intents_hash,
            schema_hash=semantic_hash({"bundle_schema_version": BUNDLE_SCHEMA_VERSION}),
            registry_hash=self.writer.registry.snapshot_hash,
            config_hash=self.writer._config_hash,
            published_shard_hashes={},
            ledger_hashes={"refs": semantic_hash(self._ledger_refs)},
            commit_sequence=len(
                [
                    marker
                    for marker in self.writer._committed_marker_cache
                    if marker["case_id"] == self.case_id
                ]
            )
            + 1,
            commit_marker_hash=commit_marker_hash,
        )
        datasets: dict[str, dict[str, Any]] = {}
        arrays: dict[str, dict[str, Any]] = {}
        moved: list[Path] = []
        try:
            for dataset_id, records in sorted(self._records.items()):
                patched: list[RecordBase] = []
                for record in records:
                    changes: dict[str, Any] = {}
                    if isinstance(record, AcceptedPointBase):
                        changes["commit_receipt_id"] = receipt_id
                    if isinstance(record, CommittedEventBase):
                        changes["commit_receipt_id"] = receipt_id
                    patched.append(dataclasses.replace(record, **changes) if changes else record)
                staging_path = self.staging_root / f"{dataset_id.replace('.', '__')}.parquet"
                entry = write_parquet_records(
                    staging_path,
                    [record.storage_dict() for record in patched],
                    compression=self.writer.parquet_compression,
                )
                entry["semantic_hash"] = (
                    semantic_hash([record.semantic_dict() for record in patched])
                    if any(
                        isinstance(record, AcceptedPointBase | CommittedEventBase)
                        for record in records
                    )
                    else self._semantic_dataset_hashes[dataset_id]
                )
                self.writer.fault_injector(
                    "event_write"
                    if self.writer.registry.datasets[dataset_id].dataset_class is DatasetClass.EVENT
                    else "data_write"
                )
                final_path = self.writer.root / final_paths[f"dataset:{dataset_id}"]
                final_path.parent.mkdir(parents=True, exist_ok=True)
                staging_path.replace(final_path)
                moved.append(final_path)
                entry["path"] = final_path.as_posix()
                datasets[dataset_id] = relative_entry(entry, self.writer.root)
            for payload in self._arrays:
                staging_path = self.staging_root / f"{payload.field_id.replace('.', '__')}.zarr"
                shape = np.asarray(payload.data).shape
                chunks = tuple(
                    min(size, default)
                    for size, default in zip(shape, self.writer.zarr_chunk_shape, strict=False)
                )
                if len(chunks) < len(shape):
                    chunks += tuple(shape[len(chunks) :])
                entry = write_zarr_array(
                    staging_path,
                    np.asarray(payload.data),
                    validity=np.asarray(payload.validity) if payload.validity is not None else None,
                    status=np.asarray(payload.status) if payload.status is not None else None,
                    chunks=chunks,
                    compression_level=self.writer.zarr_compression_level,
                )
                self.writer.fault_injector("data_write")
                final_path = self.writer.root / final_paths[f"array:{payload.field_id}"]
                final_path.parent.mkdir(parents=True, exist_ok=True)
                staging_path.replace(final_path)
                moved.append(final_path)
                entry["path"] = final_path.as_posix()
                entry.update(
                    {
                        "field_id": payload.field_id,
                        "unit": payload.unit,
                        "frame": payload.frame,
                        "reference_point": payload.reference_point,
                        "source_identity": payload.source_identity.value,
                    }
                )
                arrays[payload.field_id] = relative_entry(entry, self.writer.root)
            receipt = dataclasses.replace(
                receipt,
                published_shard_hashes={
                    **{key: value["semantic_hash"] for key, value in datasets.items()},
                    **{key: value["semantic_hash"] for key, value in arrays.items()},
                },
            )
            self.writer.registry.validate_record(receipt)
            receipt_staging = self.staging_root / "receipt.parquet"
            receipt_entry = write_parquet_records(
                receipt_staging,
                [receipt.storage_dict()],
                compression=self.writer.parquet_compression,
            )
            self.writer.fault_injector("receipt")
            receipt_final = self.writer.root / final_paths["receipt"]
            receipt_final.parent.mkdir(parents=True, exist_ok=True)
            receipt_staging.replace(receipt_final)
            moved.append(receipt_final)
            receipt_entry["path"] = receipt_final.as_posix()
            datasets[CommitReceiptBase.__dataset_id__] = relative_entry(
                receipt_entry, self.writer.root
            )
            marker = {
                "marker_schema_version": "1.0.0",
                "receipt_id": receipt_id,
                "idempotency_key": self.idempotency_key,
                "case_id": self.case_id,
                "parent_state_id": self.parent_state_id,
                "committed_state_id": committed_state_id,
                "candidate_hash": self._candidate_hash,
                "ordered_intents_hash": self._ordered_intents_hash,
                "commit_marker_hash": commit_marker_hash,
                "semantic_content_hash": semantic_hash(
                    {
                        "datasets": {
                            key: value["semantic_hash"] for key, value in datasets.items()
                        },
                        "arrays": {key: value["semantic_hash"] for key, value in arrays.items()},
                    }
                ),
                "datasets": datasets,
                "arrays": arrays,
            }
            marker_path = self.writer.root / "transactions" / "committed" / f"{safe_receipt}.json"
            self.writer.fault_injector("manifest_publish")
            write_json_atomic(marker_path, marker)
            self.writer._committed_marker_cache.append(marker)
        except Exception:
            for path in moved:
                if path.exists():
                    remove_owned_path(path, root=self.writer.root)
            self.rollback()
            raise
        self._closed = True
        if self.staging_root.exists():
            shutil.rmtree(self.staging_root)
        return receipt

    def rollback(self) -> None:
        if self.staging_root.exists():
            remove_owned_path(self.staging_root, root=self.writer.root)
        self._closed = True

    def _stage_records(self, records: Iterable[RecordBase], expected: DatasetClass) -> None:
        self._ensure_open()
        for record in records:
            descriptor = self.writer.registry.validate_record(record)
            if descriptor.dataset_class is not expected:
                raise ContractViolation(
                    f"{record.__dataset_id__} is not a {expected.value} dataset"
                )
            case_id = getattr(record, "case_id", self.case_id)
            if case_id != self.case_id:
                raise ContractViolation("record partition does not belong to transaction case")
            self.writer._validate_case_identity(record)
            self._records[descriptor.dataset_id].append(record)

    def _ensure_open(self) -> None:
        if self._closed:
            raise TransactionError("transaction is closed")

    def _planned_paths(self, safe_receipt: str) -> dict[str, str]:
        paths: dict[str, str] = {}
        for dataset_id in self._records:
            dataset_class = self.writer.registry.datasets[dataset_id].dataset_class
            base = {
                DatasetClass.ACCEPTED: "accepted_points",
                DatasetClass.EVENT: "committed_events",
            }[dataset_class]
            paths[f"dataset:{dataset_id}"] = (
                Path(base)
                / safe_component(self.case_id)
                / dataset_id.replace(".", "__")
                / f"{safe_receipt}.parquet"
            ).as_posix()
        for payload in self._arrays:
            paths[f"array:{payload.field_id}"] = (
                Path("arrays")
                / safe_component(self.case_id)
                / payload.field_id.replace(".", "__")
                / f"{safe_receipt}.zarr"
            ).as_posix()
        paths["receipt"] = (
            Path("transactions")
            / "receipts"
            / safe_component(self.case_id)
            / f"{safe_receipt}.parquet"
        ).as_posix()
        return paths

    def _read_existing_receipt(self, marker: Mapping[str, Any]) -> CommitReceiptBase:
        import pyarrow.parquet as pq

        entry = marker["datasets"][CommitReceiptBase.__dataset_id__]
        row = pq.read_table(self.writer.root / entry["path"]).to_pylist()[0]
        row["published_shard_hashes"] = json.loads(row["published_shard_hashes"])
        row["ledger_hashes"] = json.loads(row["ledger_hashes"])
        return CommitReceiptBase(**row)


def make_run_envelope(
    *,
    registry_hash: str,
    resolved_run_config: ResolvedConfig,
    operation_kind: str,
    operation_profile: str,
    source_file_hashes: Mapping[str, str],
    replay_manifest: Mapping[str, Any],
    git_commit: str,
    dirty_status: str,
    provenance_labels: tuple[str, ...],
) -> RunEnvelope:
    run_id = str(uuid7())
    fingerprint_content = {
        "resolved_config_hash": resolved_run_config.semantic_hash,
        "registry_hash": registry_hash,
        "operation_kind": operation_kind,
        "operation_profile": operation_profile,
        "source_file_hashes": dict(source_file_hashes),
        "git_commit": git_commit,
        "replay_manifest": replay_manifest,
    }
    run_fingerprint = semantic_hash(fingerprint_content)
    replay_hash = semantic_hash(replay_manifest)
    from .models import CertificationStatus

    return RunEnvelope(
        run_id=run_id,
        run_fingerprint=run_fingerprint,
        operation_kind=operation_kind,
        operation_profile=operation_profile,
        result_api_version=RESULT_API_VERSION,
        bundle_schema_version=BUNDLE_SCHEMA_VERSION,
        registry_hash=registry_hash,
        engineering_model_contract_versions=(
            "engineering_fixed_context 1.0.0",
            "SYSTEM_INTEGRATED_MODEL 1.0.0 accepted",
            "M00_FOUNDATION_REQUIREMENTS 1.0.0 frozen",
        ),
        solver_build_id="M00_FOUNDATION_NO_SOLVER",
        git_commit=git_commit,
        dirty_status=dirty_status,
        resolved_run_config_id=resolved_run_config.config_id,
        resolved_run_config_hash=resolved_run_config.semantic_hash,
        source_file_hashes=dict(source_file_hashes),
        case_index_id=stable_content_id("index", {"kind": "case", "run": run_fingerprint}),
        design_index_id=stable_content_id("index", {"kind": "design", "run": run_fingerprint}),
        seed_index_id=stable_content_id("index", {"kind": "seed", "run": run_fingerprint}),
        surface_realization_index_id=stable_content_id(
            "index", {"kind": "surface_realization", "run": run_fingerprint}
        ),
        unit_registry_id="N-mm-MPa-1.0.0",
        frame_registry_id="M00-NO-PHYSICAL-FRAME-1.0.0",
        reference_registry_id="M00-NO-PHYSICAL-REFERENCE-1.0.0",
        transform_registry_id="M00-NO-TRANSFORM-1.0.0",
        provenance_labels=provenance_labels,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        replay_manifest_id=f"replay:{replay_hash}",
        replay_manifest_hash=replay_hash,
        created_at_utc_ns=time.time_ns(),
    )
