from __future__ import annotations

import dataclasses
from collections.abc import Callable
from pathlib import Path

import pytest

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.demo_validation_only import (
    DEMO_CASE_ID,
    DEMO_DESIGN_ID,
    DEMO_SEED_ID,
    DEMO_SURFACE_ID,
    _point,
    _resolved_config,
    _status,
    validation_extension,
)
from spine_sim.foundation.errors import ContractViolation, IdempotencyConflict
from spine_sim.foundation.integrity import committed_markers
from spine_sim.foundation.models import (
    CertificationStatus,
    CommittedEventBase,
    Maturity,
    SourceIdentity,
)
from spine_sim.foundation.registry import SchemaRegistry
from spine_sim.foundation.writer import ResultWriter, make_run_envelope


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
    resolved = _resolved_config("run")
    registry = SchemaRegistry()
    registry.register_extension(validation_extension())
    digest = registry.freeze()
    source_hashes = {"M00": semantic_hash("authority")}
    envelope = make_run_envelope(
        registry_hash=digest,
        resolved_run_config=resolved,
        operation_kind="M00_VALIDATION_ONLY",
        operation_profile="FAULT_INJECTION",
        source_file_hashes=source_hashes,
        replay_manifest={"fixture": "fault"},
        git_commit="TEST",
        dirty_status="clean",
        provenance_labels=("VALIDATION_ONLY",),
    )
    writer = ResultWriter.create_run_bundle(
        tmp_path / "fault.spine-result",
        registry=registry,
        run_envelope=envelope,
        fault_injector=injector,
    )
    writer.write_resolved_config_and_provenance(
        resolved,
        provenance={"source_identity": "VALIDATION_ONLY"},
        replay_manifest={"fixture": "fault"},
    )
    case_config = _resolved_config("case")
    writer.create_case_shard(
        DEMO_CASE_ID,
        design_id=DEMO_DESIGN_ID,
        seed_id=DEMO_SEED_ID,
        surface_realization_id=DEMO_SURFACE_ID,
        resolved_case_config=case_config,
    )
    initial = stable_content_id("state", {"case": DEMO_CASE_ID, "index": -1})
    state = stable_content_id("state", {"case": DEMO_CASE_ID, "index": 0})
    return writer, initial, state, source_hashes


def _event(run_id: str, parent: str, state: str) -> CommittedEventBase:
    return CommittedEventBase(
        event_id=stable_content_id("event", {"fault": "event"}),
        source_event_ids=("source",),
        hierarchy="VALIDATION_ONLY",
        entity_ids=("validation",),
        run_id=run_id,
        case_id=DEMO_CASE_ID,
        design_id=DEMO_DESIGN_ID,
        seed_id=DEMO_SEED_ID,
        surface_realization_id=DEMO_SURFACE_ID,
        event_kind="VALIDATION_MARKER",
        raw_event_function=0.0,
        event_function_unit="1",
        numerical_scaling_id="NONE",
        path_coordinate=0.0,
        path_bracket=(0.0, 0.0),
        fraction_basis="VALIDATION_INDEX",
        localization_error=0.0,
        pre_event_accepted_state_id=parent,
        event_point_trial_id="trial:event",
        post_event_accepted_state_id=state,
        post_event_status=_status(),
        simultaneous_group_id=None,
        dependency_edges=(),
        cascade_round=0,
        pre_payload_refs=(),
        event_payload_refs=(),
        post_payload_refs=(),
        uncertainty_refs=(),
        recoverability="NOT_APPLICABLE",
        stability="NOT_APPLICABLE",
        terminal_classification="NON_TERMINAL",
        status=_status(),
        source_identity=SourceIdentity.VALIDATION_ONLY,
        maturity=Maturity.validation_only_implemented(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        committed=True,
        commit_receipt_id=None,
    )


@pytest.mark.parametrize(
    "stage", ["prepare", "data_write", "event_write", "receipt", "manifest_publish"]
)
def test_fault_injection_has_no_partial_accepted_visibility(tmp_path: Path, stage: str) -> None:
    injector = InjectOnce(stage)
    writer, initial, state, hashes = _writer(tmp_path, injector)
    point = _point(writer.run_envelope.run_id, 0, initial, state, hashes)
    transaction = writer.begin_transaction(DEMO_CASE_ID, initial, "fault-key")
    transaction.stage_accepted_point(point)
    transaction.stage_committed_events(_event(writer.run_envelope.run_id, initial, state))
    if stage == "prepare":
        with pytest.raises(OSError):
            transaction.prepare()
        transaction.rollback()
    else:
        transaction.prepare()
        with pytest.raises(OSError):
            transaction.commit()
    assert not committed_markers(writer.root)
    assert not list((writer.root / "accepted_points").rglob("*.parquet"))
    assert not list((writer.root / "committed_events").rglob("*.parquet"))
    assert not list((writer.root / "transactions" / "receipts").rglob("*.parquet"))


def test_staged_candidate_is_invisible_until_commit(tmp_path: Path) -> None:
    writer, initial, state, hashes = _writer(tmp_path)
    point = _point(writer.run_envelope.run_id, 0, initial, state, hashes)
    transaction = writer.begin_transaction(DEMO_CASE_ID, initial, "visibility-key")
    transaction.stage_accepted_point(point)
    transaction.prepare()
    assert not committed_markers(writer.root)
    assert not list((writer.root / "accepted_points").rglob("*.parquet"))
    receipt = transaction.commit()
    markers = committed_markers(writer.root)
    assert len(markers) == 1
    assert markers[0][1]["receipt_id"] == receipt.receipt_id


def test_record_identity_must_match_case_partition(tmp_path: Path) -> None:
    writer, initial, state, hashes = _writer(tmp_path)
    point = dataclasses.replace(
        _point(writer.run_envelope.run_id, 0, initial, state, hashes),
        design_id="design:WRONG_PARTITION",
    )
    transaction = writer.begin_transaction(DEMO_CASE_ID, initial, "identity-key")
    with pytest.raises(ContractViolation):
        transaction.stage_accepted_point(point)
    transaction.rollback()


def test_idempotent_retry_returns_original_receipt_and_conflict_rejects(tmp_path: Path) -> None:
    writer, initial, state, hashes = _writer(tmp_path)
    point = _point(writer.run_envelope.run_id, 0, initial, state, hashes)
    first = writer.begin_transaction(DEMO_CASE_ID, initial, "same-key")
    first.stage_accepted_point(point)
    first.prepare()
    receipt = first.commit()
    retry = writer.begin_transaction(DEMO_CASE_ID, initial, "same-key")
    retry.stage_accepted_point(point)
    retry.prepare()
    assert retry.commit().receipt_id == receipt.receipt_id
    assert len(committed_markers(writer.root)) == 1

    changed_state = stable_content_id("state", {"different": True})
    changed = _point(writer.run_envelope.run_id, 0, initial, changed_state, hashes)
    conflict = writer.begin_transaction(DEMO_CASE_ID, initial, "same-key")
    conflict.stage_accepted_point(changed)
    with pytest.raises(IdempotencyConflict):
        conflict.prepare()
    conflict.rollback()


def test_crash_recovery_removes_only_owned_staging_and_orphans(tmp_path: Path) -> None:
    writer, _, _, _ = _writer(tmp_path)
    stale = writer.root / "transactions" / "staging" / "stale"
    stale.mkdir()
    (stale / "candidate.tmp").write_text("stale")
    orphan = writer.root / "accepted_points" / DEMO_CASE_ID / "orphan.parquet"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_text("orphan")
    orphan_array = writer.root / "arrays" / DEMO_CASE_ID / "orphan.zarr"
    orphan_array.mkdir(parents=True)
    (orphan_array / "zarr.json").write_text("orphan")
    outside = tmp_path / "outside.txt"
    outside.write_text("preserve")
    report = writer.recover_crash_artifacts()
    assert report == {"removed_staging": 1, "removed_orphans": 2}
    assert outside.read_text() == "preserve"
