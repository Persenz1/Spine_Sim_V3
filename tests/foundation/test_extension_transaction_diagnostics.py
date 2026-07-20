from __future__ import annotations

import dataclasses
import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import pytest

import spine_sim.foundation.writer as writer_module
from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.demo_validation_only import (
    DEMO_CASE_ID,
    DEMO_DESIGN_ID,
    DEMO_SEED_ID,
    DEMO_SURFACE_ID,
    _point,
    _resolved_config,
)
from spine_sim.foundation.errors import (
    ContractViolation,
    IntegrityError,
    QueryError,
    TransactionError,
)
from spine_sim.foundation.integrity import VerifyMode, committed_markers, verify_bundle
from spine_sim.foundation.models import (
    AttemptOutcome,
    CapabilityStatus,
    CertificationStatus,
    EventDependencyBase,
    Maturity,
    PhysicalFeasibility,
    RecordBase,
    RejectedTrialBase,
    SourceIdentity,
    StatusTuple,
    ValuePresence,
)
from spine_sim.foundation.reader import ResultReader
from spine_sim.foundation.registry import (
    CompatibilityClass,
    DataClassification,
    DatasetClass,
    DatasetDescriptor,
    FieldMetadata,
    RelationDescriptor,
    ResultExtensionDescriptor,
    SchemaRegistry,
)
from spine_sim.foundation.writer import ResultWriter, make_run_envelope

TRANSACTION_DATASET = "validation_ext.transaction_trace"
REJECTED_DATASET = "validation_ext.rejected_details"


@dataclass(frozen=True, slots=True)
class ExtensionTransactionRecord(RecordBase):
    __dataset_id__ = TRANSACTION_DATASET

    run_id: str
    case_id: str
    trace_id: str
    commit_receipt_id: str | None
    detail_hash: str
    vector_value: tuple[float, float, float]
    source_identity: SourceIdentity


@dataclass(frozen=True, slots=True)
class ExtensionRejectedRecord(RecordBase):
    __dataset_id__ = REJECTED_DATASET

    run_id: str
    case_id: str
    trial_id: str
    detail_id: str
    commit_receipt_id: str | None
    detail_hash: str
    source_identity: SourceIdentity


def _field(dataset_id: str, item: dataclasses.Field[Any]) -> FieldMetadata:
    annotation = str(item.type)
    is_numeric_vector = item.name == "vector_value"
    dtype = "float64" if is_numeric_vector else "bool" if annotation == "bool" else "utf8"
    return FieldMetadata(
        field_id=f"{dataset_id}.{item.name}",
        namespace="validation_ext",
        owner_module="VALIDATION_EXTENSION",
        semantics=f"validation-only {item.name}",
        classification=DataClassification.DIAGNOSTIC,
        dtype=dtype,
        shape=(3,) if is_numeric_vector else (),
        dimensions=("global_component",) if is_numeric_vector else (),
        raggedness="fixed" if is_numeric_vector else "scalar",
        unit="N" if is_numeric_vector else "1",
        frame="GLOBAL" if is_numeric_vector else "NOT_APPLICABLE",
        reference_point="GLOBAL_ORIGIN" if is_numeric_vector else "NOT_APPLICABLE",
        sign_semantics="NOT_APPLICABLE",
        action_semantics="NOT_APPLICABLE",
        indices=("run_id", "case_id"),
        sampling_cadence="per_record",
        storage_frequency="validation_only",
        ownership="transaction_or_rejected_diagnostic",
        null_policy="explicit_null_until_commit" if "None" in annotation else "not_null",
        source_identity=SourceIdentity.DEV_POLICY,
        authority_refs=("M00_FOUNDATION_REQUIREMENTS 1.0.0",),
        maturity=Maturity.validation_only_implemented(),
        introduced_version="1.0.0",
        deprecated_version=None,
        storage_dataset=dataset_id,
        encoding="parquet_zstd_lossless",
        precision="float64" if is_numeric_vector else "exact",
        required="None" not in annotation,
    )


def _dataset(
    dataset_id: str,
    record_type: type[RecordBase],
    dataset_class: DatasetClass,
    primary_keys: tuple[str, ...],
) -> DatasetDescriptor:
    return DatasetDescriptor(
        dataset_id=dataset_id,
        namespace="validation_ext",
        owner_module="VALIDATION_EXTENSION",
        schema_version="1.0.0",
        dataset_class=dataset_class,
        record_type=record_type,
        fields=tuple(_field(dataset_id, item) for item in dataclasses.fields(record_type)),
        primary_keys=primary_keys,
        partition_keys=("case_id",),
        default_visible=False,
        source_identity=SourceIdentity.DEV_POLICY,
    )


def _extension() -> ResultExtensionDescriptor:
    return ResultExtensionDescriptor(
        namespace="validation_ext",
        owner_module="VALIDATION_EXTENSION",
        extension_schema_version="1.0.0",
        tables=(
            _dataset(
                TRANSACTION_DATASET,
                ExtensionTransactionRecord,
                DatasetClass.TRANSACTION,
                ("trace_id",),
            ),
            _dataset(
                REJECTED_DATASET,
                ExtensionRejectedRecord,
                DatasetClass.REJECTED,
                ("trial_id", "detail_id"),
            ),
        ),
        arrays=(),
        relations=(
            RelationDescriptor(
                "validation_ext.relation.transaction_to_receipt",
                TRANSACTION_DATASET,
                "core.transactions.receipts",
                ("commit_receipt_id",),
                ("receipt_id",),
                "many-to-one",
            ),
            RelationDescriptor(
                "validation_ext.relation.rejected_base_to_detail",
                "core.rejected_trials.diagnostics",
                REJECTED_DATASET,
                ("trial_id",),
                ("trial_id",),
                "one-to-many",
            ),
        ),
        common_keys=("run_id", "case_id"),
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=Maturity.validation_only_implemented(),
        compatibility_class=CompatibilityClass.ADDITIVE_MINOR,
    )


class InjectOnce:
    def __init__(self, target: str) -> None:
        self.target = target
        self.triggered = False

    def __call__(self, stage: str) -> None:
        if stage == self.target and not self.triggered:
            self.triggered = True
            raise OSError(f"fault injected at {stage}")


def _writer(
    tmp_path: Path, injector: Callable[[str], None] | None = None
) -> tuple[ResultWriter, str, str, dict[str, str]]:
    resolved = _resolved_config("extension-run")
    registry = SchemaRegistry()
    registry.register_extension(_extension())
    registry_hash = registry.freeze()
    source_hashes = {"M00": semantic_hash("extension-authority")}
    envelope = make_run_envelope(
        registry_hash=registry_hash,
        resolved_run_config=resolved,
        operation_kind="M00_VALIDATION_ONLY",
        operation_profile="EXTENSION_TRANSACTION_DIAGNOSTICS",
        source_file_hashes=source_hashes,
        replay_manifest={"fixture": "extension-transaction-diagnostics"},
        git_commit="TEST",
        dirty_status="clean",
        provenance_labels=("VALIDATION_ONLY",),
    )
    writer = ResultWriter.create_run_bundle(
        tmp_path / "extension.spine-result",
        registry=registry,
        run_envelope=envelope,
        fault_injector=injector,
    )
    writer.write_resolved_config_and_provenance(
        resolved,
        provenance={"source_identity": "VALIDATION_ONLY"},
        replay_manifest={"fixture": "extension-transaction-diagnostics"},
    )
    writer.create_case_shard(
        DEMO_CASE_ID,
        design_id=DEMO_DESIGN_ID,
        seed_id=DEMO_SEED_ID,
        surface_realization_id=DEMO_SURFACE_ID,
        resolved_case_config=_resolved_config("extension-case"),
    )
    parent = stable_content_id("state", {"extension": "parent"})
    state = stable_content_id("state", {"extension": "accepted"})
    return writer, parent, state, source_hashes


def _trace(run_id: str, *, receipt_id: str | None = None) -> ExtensionTransactionRecord:
    return ExtensionTransactionRecord(
        run_id=run_id,
        case_id=DEMO_CASE_ID,
        trace_id="trace:validation-extension",
        commit_receipt_id=receipt_id,
        detail_hash=semantic_hash("transaction-detail"),
        vector_value=(1.0, 2.0, 3.0),
        source_identity=SourceIdentity.DEV_POLICY,
    )


def _rejected(run_id: str, parent: str) -> RejectedTrialBase:
    return RejectedTrialBase(
        trial_id="trial:validation-extension-rejected",
        run_id=run_id,
        case_id=DEMO_CASE_ID,
        parent_accepted_state_id=parent,
        request_hash=semantic_hash("rejected-request"),
        candidate_hash=semantic_hash("rejected-candidate"),
        requested_path_target=1.0,
        status=StatusTuple(
            ValuePresence.NULL,
            CapabilityStatus.SUPPORTED,
            AttemptOutcome.REJECTED_TRIAL,
            PhysicalFeasibility.NOT_ASSESSED,
            CertificationStatus.NOT_CERTIFIABLE,
            "VALIDATION_ONLY_REJECTION",
            "intentional extension diagnostic",
            last_valid_state_id=parent,
        ),
        reason_codes=("VALIDATION_ONLY_REJECTION",),
        diagnostic_summary="intentional rejected extension fixture",
        optional_full_payload_ref=None,
        last_valid_state_id=parent,
        source_identity=SourceIdentity.DEV_POLICY,
    )


def _rejected_extension(run_id: str, trial_id: str) -> ExtensionRejectedRecord:
    return ExtensionRejectedRecord(
        run_id=run_id,
        case_id=DEMO_CASE_ID,
        trial_id=trial_id,
        detail_id="detail:validation-extension",
        commit_receipt_id=None,
        detail_hash=semantic_hash("rejected-detail"),
        source_identity=SourceIdentity.DEV_POLICY,
    )


def test_transaction_extension_is_marker_gated_and_receipt_linked(tmp_path: Path) -> None:
    writer, parent, state, source_hashes = _writer(tmp_path)
    transaction = writer.begin_transaction(DEMO_CASE_ID, parent, "extension-transaction")
    transaction.stage_accepted_point(
        _point(writer.run_envelope.run_id, 0, parent, state, source_hashes)
    )
    event_dependency = EventDependencyBase(
        run_id=writer.run_envelope.run_id,
        case_id=DEMO_CASE_ID,
        event_id="event:validation-extension",
        depends_on_event_id="event:validation-parent",
        dependency_kind="VALIDATION_ONLY",
        source_identity=SourceIdentity.VALIDATION_ONLY,
    )
    transaction.stage_committed_events(event_dependency)
    transaction.stage_transaction_records(_trace(writer.run_envelope.run_id))
    transaction.prepare()
    assert not committed_markers(writer.root)
    assert not list((writer.root / "transactions" / "extensions").rglob("*.parquet"))

    receipt = transaction.commit()
    marker = committed_markers(writer.root)[0][1]
    assert TRANSACTION_DATASET in marker["datasets"]
    assert EventDependencyBase.__dataset_id__ in marker["datasets"]
    trace_path = writer.root / marker["datasets"][TRANSACTION_DATASET]["path"]
    row = pq.read_table(trace_path).to_pylist()[0]
    assert row["commit_receipt_id"] == receipt.receipt_id
    assert row["vector_value"] == [1.0, 2.0, 3.0]
    assert marker["committed_state_id"] == state

    retry = writer.begin_transaction(DEMO_CASE_ID, parent, "extension-transaction")
    retry.stage_accepted_point(_point(writer.run_envelope.run_id, 0, parent, state, source_hashes))
    retry.stage_committed_events(event_dependency)
    retry.stage_transaction_records(_trace(writer.run_envelope.run_id))
    retry.prepare()
    assert retry.commit().receipt_id == receipt.receipt_id
    assert len(committed_markers(writer.root)) == 1

    writer.finalize_case(DEMO_CASE_ID)
    writer.publish_run_manifest()
    reader = ResultReader.open(writer.root)
    trace = reader.query(
        TRANSACTION_DATASET,
        ("trace_id", "commit_receipt_id", "vector_value"),
        include_non_default=True,
    ).read_all()
    assert trace["commit_receipt_id"].to_pylist() == [receipt.receipt_id]
    assert trace["vector_value"].to_pylist() == [[1.0, 2.0, 3.0]]


@pytest.mark.parametrize(
    ("vector_value", "message"),
    (
        ((1.0, 2.0), "shape does not match"),
        ((1.0, 2, 3.0), "runtime float64 components"),
        ((1.0, float("inf"), 3.0), "non-finite canonical value"),
    ),
)
def test_shaped_numeric_extension_rejects_invalid_values(
    tmp_path: Path,
    vector_value: tuple[object, ...],
    message: str,
) -> None:
    writer, parent, _, _ = _writer(tmp_path)
    transaction = writer.begin_transaction(DEMO_CASE_ID, parent, "invalid-shaped-numeric")
    invalid = dataclasses.replace(
        _trace(writer.run_envelope.run_id),
        vector_value=vector_value,  # type: ignore[arg-type]
    )
    with pytest.raises(ContractViolation, match=message):
        transaction.stage_transaction_records(invalid)
    transaction.rollback()


def test_transaction_extension_rejects_a_competing_receipt(tmp_path: Path) -> None:
    writer, parent, _, _ = _writer(tmp_path)
    transaction = writer.begin_transaction(DEMO_CASE_ID, parent, "forged-receipt")
    with pytest.raises(ContractViolation):
        transaction.stage_transaction_records(
            _trace(writer.run_envelope.run_id, receipt_id="receipt:FORGED")
        )
    transaction.rollback()


def test_staged_extension_primary_keys_must_be_unique(tmp_path: Path) -> None:
    writer, parent, state, source_hashes = _writer(tmp_path)
    transaction = writer.begin_transaction(DEMO_CASE_ID, parent, "duplicate-extension-key")
    transaction.stage_accepted_point(
        _point(writer.run_envelope.run_id, 0, parent, state, source_hashes)
    )
    trace = _trace(writer.run_envelope.run_id)
    transaction.stage_transaction_records(trace, trace)
    with pytest.raises(ContractViolation, match="duplicate primary key"):
        transaction.prepare()
    transaction.rollback()


def test_rejected_diagnostic_extension_primary_keys_must_be_unique(tmp_path: Path) -> None:
    writer, parent, _, _ = _writer(tmp_path)
    rejected = _rejected(writer.run_envelope.run_id, parent)
    detail = _rejected_extension(writer.run_envelope.run_id, rejected.trial_id)
    with pytest.raises(ContractViolation, match="duplicate primary key"):
        writer.record_rejected_trial(
            rejected,
            extension_records=(detail, detail),
        )
    assert not list((writer.root / "rejected_trials" / "completed").glob("*.json"))


def test_published_commit_survives_staging_cleanup_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    writer, parent, state, source_hashes = _writer(tmp_path)
    transaction = writer.begin_transaction(DEMO_CASE_ID, parent, "cleanup-failure")
    transaction.stage_accepted_point(
        _point(writer.run_envelope.run_id, 0, parent, state, source_hashes)
    )
    transaction.prepare()
    original_remove = writer_module.remove_owned_path

    def fail_staging_cleanup(path: Path, *, root: Path) -> None:
        if path == transaction.staging_root:
            raise OSError("staging cleanup acknowledgement failed")
        original_remove(path, root=root)

    monkeypatch.setattr(writer_module, "remove_owned_path", fail_staging_cleanup)
    receipt = transaction.commit()
    assert transaction.commit_marker_published
    assert transaction.committed_receipt == receipt
    assert committed_markers(writer.root)[0][1]["receipt_id"] == receipt.receipt_id
    with pytest.raises(TransactionError, match="published transaction"):
        transaction.rollback()


def test_manifest_marker_and_integrity_index_are_recomputed(
    tmp_path: Path,
) -> None:
    writer, parent, state, source_hashes = _writer(tmp_path / "source")
    transaction = writer.begin_transaction(DEMO_CASE_ID, parent, "integrity-recompute")
    transaction.stage_accepted_point(
        _point(writer.run_envelope.run_id, 0, parent, state, source_hashes)
    )
    transaction.prepare()
    transaction.commit()
    writer.finalize_case(DEMO_CASE_ID)
    writer.publish_run_manifest()
    assert verify_bundle(writer.root, VerifyMode.MANIFEST).passed

    mutations: tuple[tuple[str, Callable[[Path], None], str], ...] = (
        (
            "marker-tamper",
            lambda root: _mutate_json(
                next((root / "transactions" / "committed").glob("*.json")),
                "candidate_hash",
                semantic_hash("forged-candidate"),
            ),
            "COMMIT_MARKER_HASH_MISMATCH",
        ),
        (
            "marker-delete",
            lambda root: next((root / "transactions" / "committed").glob("*.json")).unlink(),
            "RECEIPT_SET_HASH_MISMATCH",
        ),
        (
            "receipt-set",
            lambda root: _mutate_json(
                root / "bundle_manifest.json",
                "receipt_set_hash",
                semantic_hash([]),
            ),
            "RECEIPT_SET_HASH_MISMATCH",
        ),
        (
            "bundle-hash",
            lambda root: _mutate_json(
                root / "bundle_manifest.json",
                "bundle_semantic_hash",
                semantic_hash("forged-bundle"),
            ),
            "BUNDLE_SEMANTIC_HASH_MISMATCH",
        ),
        (
            "integrity-index",
            lambda root: _mutate_json(
                root / "integrity" / "index.json",
                "receipt_set_hash",
                semantic_hash([]),
            ),
            "INTEGRITY_INDEX_MISMATCH",
        ),
    )
    for name, mutate, expected_code in mutations:
        target = tmp_path / f"{name}.spine-result"
        shutil.copytree(writer.root, target)
        mutate(target)
        with pytest.raises(IntegrityError) as captured:
            verify_bundle(target, VerifyMode.MANIFEST)
        assert expected_code in str(captured.value.details)


def _mutate_json(path: Path, key: str, value: Any) -> None:
    payload = json.loads(path.read_text())
    payload[key] = value
    path.write_text(json.dumps(payload))


@pytest.mark.parametrize("stage", ["data_write", "receipt", "manifest_publish"])
def test_transaction_extension_fault_has_no_partial_visibility(tmp_path: Path, stage: str) -> None:
    writer, parent, state, source_hashes = _writer(tmp_path, InjectOnce(stage))
    transaction = writer.begin_transaction(DEMO_CASE_ID, parent, f"fault:{stage}")
    transaction.stage_accepted_point(
        _point(writer.run_envelope.run_id, 0, parent, state, source_hashes)
    )
    transaction.stage_transaction_records(_trace(writer.run_envelope.run_id))
    transaction.prepare()
    with pytest.raises(OSError):
        transaction.commit()
    assert not committed_markers(writer.root)
    assert not list((writer.root / "transactions" / "extensions").rglob("*.parquet"))


def test_rejected_base_and_extension_publish_as_one_diagnostic_group(tmp_path: Path) -> None:
    writer, parent, _, _ = _writer(tmp_path)
    base = _rejected(writer.run_envelope.run_id, parent)
    detail = _rejected_extension(writer.run_envelope.run_id, base.trial_id)
    base_path = writer.record_rejected_trial(base, extension_records=(detail,))
    assert base_path.exists()
    assert not committed_markers(writer.root)
    completion_markers = list((writer.root / "rejected_trials" / "completed").glob("*.json"))
    assert len(completion_markers) == 1

    writer.finalize_case(DEMO_CASE_ID)
    writer.publish_run_manifest()
    reader = ResultReader.open(writer.root)
    assert REJECTED_DATASET not in {item.dataset_id for item in reader.list_datasets().entries}
    assert REJECTED_DATASET in {
        item.dataset_id for item in reader.list_datasets(include_diagnostics=True).entries
    }
    assert not reader.list_fields("validation_ext.rejected_details.*")
    assert reader.list_fields("validation_ext.rejected_details.*", include_diagnostics=True)
    with pytest.raises(QueryError):
        reader.query(REJECTED_DATASET, ("trial_id",))
    rows = reader.query(
        REJECTED_DATASET,
        ("trial_id", "detail_id"),
        include_diagnostics=True,
    ).read_all()
    assert rows.to_pylist() == [{"trial_id": base.trial_id, "detail_id": detail.detail_id}]
    manifest = reader.bundle_info()
    assert REJECTED_DATASET in manifest["auxiliary_datasets"]
    assert "core.rejected_trials.diagnostics" in manifest["auxiliary_datasets"]
    assert manifest["receipt_set_hash"] == semantic_hash([])
    assert verify_bundle(writer.root, VerifyMode.FULL).passed

    marker_payload = json.loads(completion_markers[0].read_text())
    marker_payload["commit_receipt_id"] = "receipt:FORGED"
    completion_markers[0].write_text(json.dumps(marker_payload))
    with pytest.raises(IntegrityError):
        verify_bundle(writer.root, VerifyMode.MANIFEST)


@pytest.mark.parametrize(
    "stage", ["rejected_write", "rejected_extension_write", "rejected_marker_publish"]
)
def test_rejected_diagnostic_fault_has_no_completed_or_visible_group(
    tmp_path: Path, stage: str
) -> None:
    writer, parent, _, _ = _writer(tmp_path, InjectOnce(stage))
    base = _rejected(writer.run_envelope.run_id, parent)
    detail = _rejected_extension(writer.run_envelope.run_id, base.trial_id)
    with pytest.raises(OSError):
        writer.record_rejected_trial(base, extension_records=(detail,))
    assert not list((writer.root / "rejected_trials" / "completed").glob("*.json"))
    assert not list((writer.root / "rejected_trials" / DEMO_CASE_ID).rglob("*.parquet"))
    assert not committed_markers(writer.root)


def test_rejected_extension_must_match_core_trial_and_cannot_own_receipt(tmp_path: Path) -> None:
    writer, parent, _, _ = _writer(tmp_path)
    base = _rejected(writer.run_envelope.run_id, parent)
    wrong_trial = dataclasses.replace(
        _rejected_extension(writer.run_envelope.run_id, base.trial_id),
        trial_id="trial:OTHER",
    )
    with pytest.raises(ContractViolation):
        writer.record_rejected_trial(base, extension_records=(wrong_trial,))
    forged_receipt = dataclasses.replace(
        _rejected_extension(writer.run_envelope.run_id, base.trial_id),
        commit_receipt_id="receipt:FORGED",
    )
    with pytest.raises(ContractViolation):
        writer.record_rejected_trial(base, extension_records=(forged_receipt,))


def test_unmarked_rejected_orphan_is_not_cataloged_and_recovery_removes_it(
    tmp_path: Path,
) -> None:
    writer, _, _, _ = _writer(tmp_path)
    orphan = (
        writer.root
        / "rejected_trials"
        / DEMO_CASE_ID
        / REJECTED_DATASET.replace(".", "__")
        / "orphan.parquet"
    )
    orphan.parent.mkdir(parents=True)
    orphan.write_bytes(b"incomplete diagnostic shard")
    writer.finalize_case(DEMO_CASE_ID)
    writer.publish_run_manifest()
    assert REJECTED_DATASET not in ResultReader.open(writer.root).bundle_info().get(
        "auxiliary_datasets", {}
    )
    assert writer.recover_crash_artifacts()["removed_orphans"] == 1
    assert not orphan.exists()
