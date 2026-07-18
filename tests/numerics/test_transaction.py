from __future__ import annotations

import dataclasses
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
)
from spine_sim.foundation.errors import (
    ContractViolation,
    IdempotencyConflict,
    TransactionError,
)
from spine_sim.foundation.integrity import committed_markers
from spine_sim.foundation.models import (
    CertificationStatus,
    CommittedEventBase,
    EventDependencyBase,
    Maturity,
    PerUnitAcceptedPoint,
    SourceIdentity,
)
from spine_sim.foundation.registry import SchemaRegistry
from spine_sim.foundation.writer import ResultWriter, make_run_envelope
from spine_sim.numerics.contracts import (
    M02ReasonCode,
    OrderedIntentBatch,
    PreparedCandidate,
    ProvisionalIntent,
    RollbackToken,
)
from spine_sim.numerics.transaction import (
    M00ResultWriterAdapter,
    M02PreparedTransaction,
    M02TransactionCoordinator,
    OwnerSideEffectDetected,
    PrepareAccessPlan,
    PrepareRejected,
    ResourceVersion,
    ResourceVersionExpectation,
    RollbackFailed,
    SideEffectSentinel,
    TransactionAuthoritySnapshot,
    TransactionFaultStage,
    TransactionState,
    transaction_staging_paths,
)

PARENT_RECEIPT_ID = "receipt:validation-root"
PARENT_VERSION = "accepted-state-v1"
OWNER_ID = "VALIDATION_OWNER"
OWNER_TOKEN_VERSION = "owner-token-v1"
OWNER_BUILD_HASH = semantic_hash("validation-owner-build")
STATE_RESOURCE = "owner/state"
DAMAGE_RESOURCE = "DamageStore/global"
WORK_RESOURCE = "work/ledger"
STATE_VERSION = "state-resource-v1"
DAMAGE_VERSION = "damage-resource-v1"
WORK_VERSION = "work-resource-v1"


class InjectOnce:
    def __init__(self, target: str) -> None:
        self.target = target
        self.triggered = False

    def __call__(self, stage: Any) -> None:
        value = stage.value if hasattr(stage, "value") else str(stage)
        if value == self.target and not self.triggered:
            self.triggered = True
            raise OSError(f"fault injected at {value}")


class FailRollbackOnce:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, _: RollbackToken) -> None:
        self.calls += 1
        if self.calls == 1:
            raise OSError("owner rollback fault")


@dataclass(slots=True)
class TransactionFixture:
    writer: ResultWriter
    adapter: M00ResultWriterAdapter
    coordinator: M02TransactionCoordinator
    candidate: PreparedCandidate
    authority: TransactionAuthoritySnapshot
    access_plan: PrepareAccessPlan
    point: Any
    accepted_snapshot: dict[str, Any]
    baseline_snapshot: dict[str, Any]
    rollback_calls: list[str]
    source_hashes: dict[str, str]
    parent_state_id: str
    committed_state_id: str

    def begin(self) -> M02PreparedTransaction:
        transaction = self.coordinator.begin(
            self.candidate,
            authority=self.authority,
            access_plan=self.access_plan,
        )
        transaction.stage_accepted_point(self.point)
        transaction.stage_state_and_ledger_references(
            (
                *self.candidate.final_opaque_state_refs,
                self.candidate.ordered_intent_batch.semantic_id,
                DAMAGE_RESOURCE,
                WORK_RESOURCE,
            )
        )
        return transaction


def _intent(
    intent_id: str,
    *,
    read_set: tuple[str, ...],
    write_set: tuple[str, ...],
    versions: tuple[str, ...],
) -> ProvisionalIntent:
    return ProvisionalIntent.create(
        intent_id=intent_id,
        owner_id=OWNER_ID,
        intent_kind="VALIDATION_ONLY_OPAQUE_UPDATE",
        payload_hash=semantic_hash({"intent": intent_id}),
        read_set=read_set,
        write_set=write_set,
        dependency_versions=versions,
        zero_progress=False,
        metadata_unit="1",
    )


def _rollback_token(
    *,
    run_id: str,
    trial_id: str,
    parent_state_id: str,
    parent_state_hash: str,
    token_version: str = OWNER_TOKEN_VERSION,
    owner_id: str = OWNER_ID,
) -> RollbackToken:
    return RollbackToken.create(
        token_ref=stable_content_id(
            "rollback-token",
            {
                "run": run_id,
                "trial": trial_id,
                "parent": parent_state_id,
                "owner": owner_id,
                "version": token_version,
            },
        ),
        owner_id=owner_id,
        run_id=run_id,
        trial_id=trial_id,
        parent_accepted_state_id=parent_state_id,
        parent_state_hash=parent_state_hash,
        token_version=token_version,
        metadata_unit="1",
    )


def _candidate(
    *,
    run_id: str,
    parent_state_id: str,
    parent_state_hash: str,
    point_id: str,
    registry_hash: str,
    config_hash: str,
    idempotency_key: str = "m02:transaction",
    final_state_hash: str | None = None,
    intents: tuple[ProvisionalIntent, ...] | None = None,
    damage_store_parent_version: str | None = DAMAGE_VERSION,
    rollback_tokens: tuple[RollbackToken, ...] | None = None,
    quality_hashes: tuple[str, ...] = (semantic_hash("quality-pass"),),
    event_ids: tuple[str, ...] = (),
    located_event_refs: tuple[str, ...] = (),
) -> PreparedCandidate:
    trial_id = "trial:m02-transaction-validation"
    chosen_intents = intents or (
        _intent(
            "intent:owner-state",
            read_set=(STATE_RESOURCE,),
            write_set=(STATE_RESOURCE,),
            versions=(STATE_VERSION,),
        ),
        _intent(
            "intent:shared-ledgers",
            read_set=(DAMAGE_RESOURCE, WORK_RESOURCE),
            write_set=(DAMAGE_RESOURCE, WORK_RESOURCE),
            versions=(DAMAGE_VERSION, WORK_VERSION),
        ),
    )
    batch = OrderedIntentBatch.create(
        batch_id=stable_content_id(
            "ordered-intent-batch", tuple(item.intent_id for item in chosen_intents)
        ),
        intents=chosen_intents,
        dependency_order=tuple(item.intent_id for item in chosen_intents),
        conflicts_resolved=True,
        damage_store_parent_version=damage_store_parent_version,
        metadata_unit="1",
    )
    chosen_tokens = rollback_tokens or (
        _rollback_token(
            run_id=run_id,
            trial_id=trial_id,
            parent_state_id=parent_state_id,
            parent_state_hash=parent_state_hash,
        ),
    )
    payload = {
        "point_id": point_id,
        "parent": parent_state_id,
        "final": final_state_hash or semantic_hash("accepted-final-state"),
        "events": event_ids,
        "batch": batch.semantic_hash,
    }
    return PreparedCandidate.create(
        candidate_id=stable_content_id("prepared-candidate", payload),
        target_id="target:m02-transaction-validation",
        trial_id=trial_id,
        parent_accepted_state_id=parent_state_id,
        parent_commit_receipt_id=PARENT_RECEIPT_ID,
        parent_state_hash=parent_state_hash,
        final_opaque_state_refs=("opaque-state:validation-owner",),
        final_state_hash=payload["final"],
        ordered_intent_batch=batch,
        rollback_tokens=chosen_tokens,
        located_event_group_refs=located_event_refs,
        numerical_quality_hashes=quality_hashes,
        registry_hash=registry_hash,
        config_hash=config_hash,
        owner_build_hashes=(OWNER_BUILD_HASH,),
        event_coverage_complete=True,
        earliestness_complete=True,
        post_event_side_complete=True,
        quality_complete=True,
        persistence_ready=True,
        idempotency_key=idempotency_key,
        proposed_accepted_point_id=point_id,
        proposed_committed_event_ids=event_ids,
        metadata_unit="1",
    )


def _access_plan(intents: tuple[ProvisionalIntent, ...]) -> PrepareAccessPlan:
    current = {
        STATE_RESOURCE: STATE_VERSION,
        DAMAGE_RESOURCE: DAMAGE_VERSION,
        WORK_RESOURCE: WORK_VERSION,
    }
    return PrepareAccessPlan(
        expected_parent_state_version=PARENT_VERSION,
        resource_expectations=tuple(
            ResourceVersionExpectation(intent.intent_id, resource, current[resource])
            for intent in intents
            for resource in dict.fromkeys((*intent.read_set, *intent.write_set))
        ),
    )


def _fixture(
    tmp_path: Path,
    *,
    m00_fault: str | None = None,
    m02_fault: TransactionFaultStage | None = None,
    rollback_handler: Callable[[RollbackToken], None] | None = None,
    prepare_token_ttl_ns: int | None = None,
    monotonic_ns: Callable[[], int] | None = None,
) -> TransactionFixture:
    resolved = _resolved_config("m02-transaction-run")
    registry = SchemaRegistry()
    registry_hash = registry.freeze()
    source_hashes = {"M00": semantic_hash("m02-transaction-authority")}
    envelope = make_run_envelope(
        registry_hash=registry_hash,
        resolved_run_config=resolved,
        operation_kind="M02_VALIDATION_ONLY",
        operation_profile="TRANSACTION",
        source_file_hashes=source_hashes,
        replay_manifest={"fixture": "m02-transaction"},
        git_commit="TEST",
        dirty_status="clean",
        provenance_labels=("VALIDATION_ONLY",),
    )
    writer = ResultWriter.create_run_bundle(
        tmp_path / "m02-transaction.spine-result",
        registry=registry,
        run_envelope=envelope,
        fault_injector=InjectOnce(m00_fault) if m00_fault else None,
    )
    writer.write_resolved_config_and_provenance(
        resolved,
        provenance={"source_identity": "VALIDATION_ONLY"},
        replay_manifest={"fixture": "m02-transaction"},
    )
    writer.create_case_shard(
        DEMO_CASE_ID,
        design_id=DEMO_DESIGN_ID,
        seed_id=DEMO_SEED_ID,
        surface_realization_id=DEMO_SURFACE_ID,
        resolved_case_config=_resolved_config("m02-transaction-case"),
    )
    parent = stable_content_id("state", {"m02": "parent"})
    committed = stable_content_id("state", {"m02": "committed"})
    point = _point(writer.run_envelope.run_id, 0, parent, committed, source_hashes)
    accepted_snapshot: dict[str, Any] = {
        "accepted_state_id": parent,
        "path_coordinate": 0.0,
        "physical_time": 0.0,
        "slip": 0.0,
        "damage_store_version": DAMAGE_VERSION,
        "work": 0.0,
        "event_ids": (),
        "peak": 0.0,
        "cycle": 0,
        "receipt_sequence": 0,
    }
    sentinel = SideEffectSentinel(lambda: accepted_snapshot)
    adapter = M00ResultWriterAdapter(writer)
    parent_hash = semantic_hash(accepted_snapshot)
    candidate = _candidate(
        run_id=writer.run_envelope.run_id,
        parent_state_id=parent,
        parent_state_hash=parent_hash,
        point_id=point.point_id,
        registry_hash=adapter.registry_hash,
        config_hash=adapter.config_hash,
    )
    authority = adapter.authority_snapshot(
        case_id=DEMO_CASE_ID,
        parent_accepted_state_id=parent,
        parent_commit_receipt_id=PARENT_RECEIPT_ID,
        parent_state_version=PARENT_VERSION,
        parent_state_hash=parent_hash,
        accepted_snapshot_hash=sentinel.capture_hash(),
        owner_build_hashes=(OWNER_BUILD_HASH,),
        owner_token_versions=((OWNER_ID, OWNER_TOKEN_VERSION),),
        resource_versions=(
            ResourceVersion(STATE_RESOURCE, STATE_VERSION),
            ResourceVersion(DAMAGE_RESOURCE, DAMAGE_VERSION),
            ResourceVersion(WORK_RESOURCE, WORK_VERSION),
        ),
        damage_store_version=DAMAGE_VERSION,
    )
    rollback_calls: list[str] = []

    def default_rollback(token: RollbackToken) -> None:
        rollback_calls.append(token.token_ref)

    coordinator = M02TransactionCoordinator(
        adapter,
        sentinel=sentinel,
        rollback_handlers={OWNER_ID: rollback_handler or default_rollback},
        fault_injector=InjectOnce(m02_fault.value) if m02_fault else None,
        prepare_token_ttl_ns=prepare_token_ttl_ns,
        monotonic_ns=monotonic_ns or (lambda: 100),
    )
    return TransactionFixture(
        writer,
        adapter,
        coordinator,
        candidate,
        authority,
        _access_plan(candidate.ordered_intent_batch.intents),
        point,
        accepted_snapshot,
        dict(accepted_snapshot),
        rollback_calls,
        source_hashes,
        parent,
        committed,
    )


def _event(fixture: TransactionFixture) -> CommittedEventBase:
    return CommittedEventBase(
        event_id=stable_content_id("event", {"m02": "transaction-event"}),
        source_event_ids=("source:m02-validation",),
        hierarchy="VALIDATION_ONLY",
        entity_ids=("entity:m02-validation",),
        run_id=fixture.writer.run_envelope.run_id,
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
        pre_event_accepted_state_id=fixture.parent_state_id,
        event_point_trial_id=fixture.candidate.trial_id,
        post_event_accepted_state_id=fixture.committed_state_id,
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


def _with_event(fixture: TransactionFixture) -> tuple[M02PreparedTransaction, CommittedEventBase]:
    event = _event(fixture)
    fixture.candidate = _candidate(
        run_id=fixture.writer.run_envelope.run_id,
        parent_state_id=fixture.parent_state_id,
        parent_state_hash=fixture.authority.parent_state_hash,
        point_id=fixture.point.point_id,
        registry_hash=fixture.adapter.registry_hash,
        config_hash=fixture.adapter.config_hash,
        event_ids=(event.event_id,),
        located_event_refs=("located-event-group:validation",),
    )
    fixture.access_plan = _access_plan(fixture.candidate.ordered_intent_batch.intents)
    transaction = fixture.begin()
    transaction.stage_committed_events(event)
    return transaction, event


def _assert_no_partial_publication(fixture: TransactionFixture) -> None:
    assert not committed_markers(fixture.writer.root)
    assert not list((fixture.writer.root / "accepted_points").rglob("*.parquet"))
    assert not list((fixture.writer.root / "committed_events").rglob("*.parquet"))
    assert not list((fixture.writer.root / "transactions" / "receipts").rglob("*.parquet"))
    assert fixture.accepted_snapshot == fixture.baseline_snapshot


def test_prepare_is_invisible_and_commit_returns_only_m00_receipt_reference(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    transaction = fixture.begin()
    token = transaction.prepare()
    assert transaction.prepare() is token
    _assert_no_partial_publication(fixture)

    receipt = transaction.commit(token)
    assert receipt.core_receipt_dataset_id == "core.transactions.receipts"
    assert receipt.candidate_hash == token.candidate_hash
    assert receipt.committed_state_id == fixture.committed_state_id
    assert transaction.state is TransactionState.COMMITTED
    assert len(committed_markers(fixture.writer.root)) == 1
    with pytest.raises(TransactionError):
        transaction.rollback()


@pytest.mark.parametrize(
    "mutation",
    [
        "parent_hash",
        "parent_receipt",
        "parent_version",
        "schema_version",
        "registry_hash",
        "config_hash",
        "owner_build",
        "snapshot_hash",
        "persistence",
    ],
)
def test_prepare_rejects_parent_version_hash_registry_config_and_persistence_gates(
    tmp_path: Path, mutation: str
) -> None:
    fixture = _fixture(tmp_path)
    if mutation == "parent_hash":
        fixture.authority = dataclasses.replace(
            fixture.authority, parent_state_hash=semantic_hash("stale-parent")
        )
    elif mutation == "parent_receipt":
        fixture.authority = dataclasses.replace(
            fixture.authority, parent_commit_receipt_id="receipt:stale-parent"
        )
    elif mutation == "parent_version":
        fixture.access_plan = dataclasses.replace(
            fixture.access_plan, expected_parent_state_version="stale-version"
        )
    elif mutation == "schema_version":
        fixture.authority = dataclasses.replace(fixture.authority, schema_version="2.0.0")
    elif mutation == "registry_hash":
        fixture.authority = dataclasses.replace(
            fixture.authority, registry_hash=semantic_hash("stale-registry")
        )
    elif mutation == "config_hash":
        fixture.authority = dataclasses.replace(
            fixture.authority, config_hash=semantic_hash("stale-config")
        )
    elif mutation == "owner_build":
        fixture.authority = dataclasses.replace(
            fixture.authority, owner_build_hashes=(semantic_hash("stale-owner"),)
        )
    elif mutation == "snapshot_hash":
        fixture.authority = dataclasses.replace(
            fixture.authority, accepted_snapshot_hash=semantic_hash("stale-snapshot")
        )
    elif mutation == "persistence":
        fixture.authority = dataclasses.replace(fixture.authority, persistence_available=False)

    transaction = fixture.begin()
    with pytest.raises(PrepareRejected) as captured:
        transaction.prepare()
    assert captured.value.details["reason_code"] == M02ReasonCode.PREPARE_REJECTED.value
    transaction.rollback()
    _assert_no_partial_publication(fixture)


@pytest.mark.parametrize(
    "conflict",
    ["missing_expectation", "stale_resource", "external_writer", "damage_version"],
)
def test_prepare_checks_complete_read_write_versions_locks_and_damagestore(
    tmp_path: Path, conflict: str
) -> None:
    fixture = _fixture(tmp_path)
    if conflict == "missing_expectation":
        fixture.access_plan = dataclasses.replace(
            fixture.access_plan,
            resource_expectations=fixture.access_plan.resource_expectations[:-1],
        )
    elif conflict == "stale_resource":
        resources = tuple(
            ResourceVersion(item.resource_id, "concurrent-version")
            if item.resource_id == STATE_RESOURCE
            else item
            for item in fixture.authority.resource_versions
        )
        fixture.authority = dataclasses.replace(fixture.authority, resource_versions=resources)
    elif conflict == "external_writer":
        fixture.authority = dataclasses.replace(
            fixture.authority, external_write_locks=(STATE_RESOURCE,)
        )
    elif conflict == "damage_version":
        fixture.authority = dataclasses.replace(
            fixture.authority, damage_store_version="concurrent-damage-version"
        )

    transaction = fixture.begin()
    with pytest.raises(PrepareRejected):
        transaction.prepare()
    transaction.rollback()
    _assert_no_partial_publication(fixture)


def test_prepare_rejects_multiple_internal_writers_even_when_owner_claims_resolved(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    intents = (
        _intent(
            "intent:writer-one",
            read_set=(STATE_RESOURCE,),
            write_set=(STATE_RESOURCE,),
            versions=(STATE_VERSION,),
        ),
        _intent(
            "intent:writer-two",
            read_set=(),
            write_set=(STATE_RESOURCE,),
            versions=(STATE_VERSION,),
        ),
    )
    fixture.candidate = _candidate(
        run_id=fixture.writer.run_envelope.run_id,
        parent_state_id=fixture.parent_state_id,
        parent_state_hash=fixture.authority.parent_state_hash,
        point_id=fixture.point.point_id,
        registry_hash=fixture.adapter.registry_hash,
        config_hash=fixture.adapter.config_hash,
        intents=intents,
        damage_store_parent_version=None,
    )
    fixture.access_plan = _access_plan(intents)
    transaction = fixture.begin()
    with pytest.raises(PrepareRejected, match="read/write set conflict"):
        transaction.prepare()
    transaction.rollback()


def test_prepare_requires_quality_event_evidence_and_exact_core_ids(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture.candidate = _candidate(
        run_id=fixture.writer.run_envelope.run_id,
        parent_state_id=fixture.parent_state_id,
        parent_state_hash=fixture.authority.parent_state_hash,
        point_id=fixture.point.point_id,
        registry_hash=fixture.adapter.registry_hash,
        config_hash=fixture.adapter.config_hash,
        quality_hashes=(),
    )
    fixture.access_plan = _access_plan(fixture.candidate.ordered_intent_batch.intents)
    transaction = fixture.begin()
    with pytest.raises(PrepareRejected, match="quality"):
        transaction.prepare()
    transaction.rollback()

    second = _fixture(tmp_path / "event")
    event = _event(second)
    second.candidate = _candidate(
        run_id=second.writer.run_envelope.run_id,
        parent_state_id=second.parent_state_id,
        parent_state_hash=second.authority.parent_state_hash,
        point_id=second.point.point_id,
        registry_hash=second.adapter.registry_hash,
        config_hash=second.adapter.config_hash,
        event_ids=(event.event_id,),
        located_event_refs=(),
    )
    second.access_plan = _access_plan(second.candidate.ordered_intent_batch.intents)
    event_tx = second.begin()
    event_tx.stage_committed_events(event)
    with pytest.raises(PrepareRejected, match="located-event"):
        event_tx.prepare()
    event_tx.rollback()

    third = _fixture(tmp_path / "point")
    third.candidate = _candidate(
        run_id=third.writer.run_envelope.run_id,
        parent_state_id=third.parent_state_id,
        parent_state_hash=third.authority.parent_state_hash,
        point_id="point:wrong-core-identity",
        registry_hash=third.adapter.registry_hash,
        config_hash=third.adapter.config_hash,
    )
    third.access_plan = _access_plan(third.candidate.ordered_intent_batch.intents)
    point_tx = third.begin()
    with pytest.raises(PrepareRejected, match="accepted point identity"):
        point_tx.prepare()
    point_tx.rollback()


@pytest.mark.parametrize("token_fault", ["run", "parent", "version", "owner"])
def test_prepare_rejects_unknown_cross_run_parent_or_version_rollback_tokens(
    tmp_path: Path, token_fault: str
) -> None:
    fixture = _fixture(tmp_path)
    values = {
        "run_id": fixture.writer.run_envelope.run_id,
        "trial_id": fixture.candidate.trial_id,
        "parent_state_id": fixture.parent_state_id,
        "parent_state_hash": fixture.authority.parent_state_hash,
        "token_version": OWNER_TOKEN_VERSION,
        "owner_id": OWNER_ID,
    }
    if token_fault == "run":
        values["run_id"] = "run:wrong"
    elif token_fault == "parent":
        values["parent_state_id"] = "state:wrong"
    elif token_fault == "version":
        values["token_version"] = "owner-token-wrong"
    elif token_fault == "owner":
        values["owner_id"] = "UNKNOWN_OWNER"
    token = _rollback_token(**values)
    fixture.candidate = _candidate(
        run_id=fixture.writer.run_envelope.run_id,
        parent_state_id=fixture.parent_state_id,
        parent_state_hash=fixture.authority.parent_state_hash,
        point_id=fixture.point.point_id,
        registry_hash=fixture.adapter.registry_hash,
        config_hash=fixture.adapter.config_hash,
        rollback_tokens=(token,),
    )
    fixture.access_plan = _access_plan(fixture.candidate.ordered_intent_batch.intents)
    transaction = fixture.begin()
    with pytest.raises(PrepareRejected, match="rollback token"):
        transaction.prepare()
    with pytest.raises(RollbackFailed):
        # Cross-scope tokens are deliberately not dispatched to a different owner.
        transaction.rollback()


def test_idempotency_same_candidate_returns_original_receipt_and_different_conflicts(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    first = fixture.begin()
    first.prepare()
    receipt = first.commit()

    retry = fixture.begin()
    retry.prepare()
    assert retry.commit().receipt_id == receipt.receipt_id
    assert len(committed_markers(fixture.writer.root)) == 1

    changed = _candidate(
        run_id=fixture.writer.run_envelope.run_id,
        parent_state_id=fixture.parent_state_id,
        parent_state_hash=fixture.authority.parent_state_hash,
        point_id=fixture.point.point_id,
        registry_hash=fixture.adapter.registry_hash,
        config_hash=fixture.adapter.config_hash,
        idempotency_key=fixture.candidate.idempotency_key,
        final_state_hash=semantic_hash("different-final-state"),
    )
    with pytest.raises(IdempotencyConflict):
        fixture.coordinator.begin(
            changed,
            authority=fixture.authority,
            access_plan=_access_plan(changed.ordered_intent_batch.intents),
        )


def test_rollback_is_idempotent_and_committed_receipt_cannot_be_rolled_back(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    transaction = fixture.begin()
    transaction.prepare()
    first = transaction.rollback()
    second = transaction.rollback()
    assert first is second
    assert first.complete
    assert fixture.rollback_calls == [fixture.candidate.rollback_tokens[0].token_ref]
    assert not transaction_staging_paths(fixture.writer.root)

    committed_fixture = _fixture(tmp_path / "committed")
    committed = committed_fixture.begin()
    committed.prepare()
    committed.commit()
    with pytest.raises(TransactionError, match="cannot be rolled back"):
        committed.rollback()


def test_owner_rollback_failure_keeps_last_valid_state_and_retry_finishes_cleanup(
    tmp_path: Path,
) -> None:
    failing = FailRollbackOnce()
    fixture = _fixture(tmp_path, rollback_handler=failing)
    transaction = fixture.begin()
    transaction.prepare()
    with pytest.raises(RollbackFailed) as captured:
        transaction.rollback()
    assert captured.value.details["last_valid_state_id"] == fixture.parent_state_id
    assert transaction.state is TransactionState.ROLLBACK_FAILED
    assert not transaction_staging_paths(fixture.writer.root)
    report = transaction.rollback()
    assert report.complete
    assert failing.calls == 2
    _assert_no_partial_publication(fixture)


def test_side_effect_sentinel_guards_repeated_evaluate_and_prepare(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    baseline = semantic_hash(fixture.accepted_snapshot)
    assert fixture.coordinator.evaluate(lambda: "owner-response") == "owner-response"
    assert fixture.coordinator.evaluate(lambda: "owner-response") == "owner-response"
    assert semantic_hash(fixture.accepted_snapshot) == baseline

    def illegal_owner() -> str:
        fixture.accepted_snapshot["work"] = 1.0
        return "illegal"

    with pytest.raises(OwnerSideEffectDetected):
        fixture.coordinator.evaluate(illegal_owner)
    assert fixture.accepted_snapshot["work"] == 1.0

    clean = _fixture(tmp_path / "prepare")
    transaction = clean.begin()
    clean.accepted_snapshot["event_ids"] = ("illegal:event",)
    with pytest.raises(OwnerSideEffectDetected):
        transaction.prepare()
    assert not committed_markers(clean.writer.root)
    assert clean.accepted_snapshot["event_ids"] == ("illegal:event",)


def test_expired_prepare_token_rolls_back_without_publication(tmp_path: Path) -> None:
    clock = iter((100, 200))
    fixture = _fixture(
        tmp_path,
        prepare_token_ttl_ns=50,
        monotonic_ns=lambda: next(clock),
    )
    transaction = fixture.begin()
    token = transaction.prepare()
    assert token.expires_at_monotonic_ns == 150
    with pytest.raises(TransactionError, match="expired"):
        transaction.commit(token)
    assert transaction.state is TransactionState.ROLLED_BACK
    _assert_no_partial_publication(fixture)


@pytest.mark.parametrize(
    "stage",
    [
        TransactionFaultStage.PREPARE_BEFORE,
        TransactionFaultStage.PREPARE_AFTER,
        TransactionFaultStage.RECEIPT_BEFORE,
        TransactionFaultStage.COMMIT_MARKER_BEFORE,
    ],
)
def test_m02_prepublication_faults_leave_no_partial_accepted_state(
    tmp_path: Path, stage: TransactionFaultStage
) -> None:
    fixture = _fixture(tmp_path, m02_fault=stage)
    transaction, _ = _with_event(fixture)
    if stage in {TransactionFaultStage.PREPARE_BEFORE, TransactionFaultStage.PREPARE_AFTER}:
        with pytest.raises(OSError):
            transaction.prepare()
        transaction.rollback()
    else:
        transaction.prepare()
        with pytest.raises(OSError):
            transaction.commit()
    _assert_no_partial_publication(fixture)


@pytest.mark.parametrize("m00_stage", ["data_write", "event_write", "receipt", "manifest_publish"])
def test_m00_state_event_receipt_and_commit_marker_faults_are_all_or_none(
    tmp_path: Path, m00_stage: str
) -> None:
    fixture = _fixture(tmp_path, m00_fault=m00_stage)
    transaction, _ = _with_event(fixture)
    transaction.prepare()
    with pytest.raises(OSError):
        transaction.commit()
    assert transaction.state is TransactionState.ROLLED_BACK
    _assert_no_partial_publication(fixture)


@pytest.mark.parametrize(
    "stage",
    [TransactionFaultStage.COMMIT_MARKER_AFTER, TransactionFaultStage.RECEIPT_AFTER],
)
def test_postpublication_ack_fault_recovers_original_complete_receipt(
    tmp_path: Path, stage: TransactionFaultStage
) -> None:
    fixture = _fixture(tmp_path, m02_fault=stage)
    transaction, event = _with_event(fixture)
    token = transaction.prepare()
    with pytest.raises(OSError):
        transaction.commit(token)
    assert transaction.state is TransactionState.COMMITTED
    marker = committed_markers(fixture.writer.root)[0][1]
    assert "core.accepted_points.common" in marker["datasets"]
    assert "core.committed_events.events" in marker["datasets"]
    assert "core.transactions.receipts" in marker["datasets"]
    assert marker["committed_state_id"] == fixture.committed_state_id
    assert event.event_id in fixture.candidate.proposed_committed_event_ids
    recovered = transaction.commit(token)
    assert recovered is transaction.receipt_ref
    assert recovered.receipt_id == marker["receipt_id"]


@pytest.mark.parametrize(
    "stage", [TransactionFaultStage.ROLLBACK_BEFORE, TransactionFaultStage.ROLLBACK_AFTER]
)
def test_rollback_fault_is_retryable_and_never_publishes_staging(
    tmp_path: Path, stage: TransactionFaultStage
) -> None:
    fixture = _fixture(tmp_path, m02_fault=stage)
    transaction = fixture.begin()
    transaction.prepare()
    expected_error = RollbackFailed if stage is TransactionFaultStage.ROLLBACK_BEFORE else OSError
    with pytest.raises(expected_error):
        transaction.rollback()
    assert not transaction_staging_paths(fixture.writer.root)
    report = transaction.rollback()
    assert report.complete
    _assert_no_partial_publication(fixture)


@pytest.mark.parametrize(
    "stage", [TransactionFaultStage.EVALUATE_BEFORE, TransactionFaultStage.EVALUATE_AFTER]
)
def test_evaluate_fault_injection_never_changes_accepted_snapshot(
    tmp_path: Path, stage: TransactionFaultStage
) -> None:
    fixture = _fixture(tmp_path, m02_fault=stage)
    baseline = semantic_hash(fixture.accepted_snapshot)
    with pytest.raises(OSError):
        fixture.coordinator.evaluate(lambda: "side-effect-free-response")
    assert semantic_hash(fixture.accepted_snapshot) == baseline
    _assert_no_partial_publication(fixture)


def test_duplicate_core_event_primary_key_is_rejected(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    transaction, event = _with_event(fixture)
    transaction.stage_committed_events(event)
    with pytest.raises(ContractViolation, match="duplicate primary key"):
        transaction.prepare()
    transaction.rollback()


@pytest.mark.parametrize(
    ("field", "forged"),
    [
        ("pre_event_accepted_state_id", "state:forged-parent"),
        ("post_event_accepted_state_id", "state:forged-post"),
        ("event_point_trial_id", "trial:forged"),
    ],
)
def test_forged_core_event_state_and_trial_lineage_is_rejected(
    tmp_path: Path, field: str, forged: str
) -> None:
    fixture = _fixture(tmp_path)
    event = dataclasses.replace(_event(fixture), **{field: forged})
    fixture.candidate = _candidate(
        run_id=fixture.writer.run_envelope.run_id,
        parent_state_id=fixture.parent_state_id,
        parent_state_hash=fixture.authority.parent_state_hash,
        point_id=fixture.point.point_id,
        registry_hash=fixture.adapter.registry_hash,
        config_hash=fixture.adapter.config_hash,
        event_ids=(event.event_id,),
        located_event_refs=("located-event-group:validation",),
    )
    fixture.access_plan = _access_plan(fixture.candidate.ordered_intent_batch.intents)
    transaction = fixture.begin()
    transaction.stage_committed_events(event)
    with pytest.raises(PrepareRejected, match="extension lineage"):
        transaction.prepare()
    transaction.rollback()


def test_forged_point_state_and_event_dependency_lineage_is_rejected(
    tmp_path: Path,
) -> None:
    point_fixture = _fixture(tmp_path / "point")
    forged_point_extension = PerUnitAcceptedPoint(
        run_id=point_fixture.writer.run_envelope.run_id,
        case_id=DEMO_CASE_ID,
        point_id=point_fixture.point.point_id,
        accepted_state_id="state:forged-accepted",
        entity_id="entity:validation",
        entity_kind="VALIDATION_ONLY",
        module_payload_refs=(),
        source_identity=SourceIdentity.VALIDATION_ONLY,
    )
    point_transaction = point_fixture.begin()
    point_transaction.stage_accepted_point(forged_point_extension)
    with pytest.raises(PrepareRejected, match="extension lineage"):
        point_transaction.prepare()
    point_transaction.rollback()

    dependency_fixture = _fixture(tmp_path / "dependency")
    event = _event(dependency_fixture)
    dependency_fixture.candidate = _candidate(
        run_id=dependency_fixture.writer.run_envelope.run_id,
        parent_state_id=dependency_fixture.parent_state_id,
        parent_state_hash=dependency_fixture.authority.parent_state_hash,
        point_id=dependency_fixture.point.point_id,
        registry_hash=dependency_fixture.adapter.registry_hash,
        config_hash=dependency_fixture.adapter.config_hash,
        event_ids=(event.event_id,),
        located_event_refs=("located-event-group:validation",),
    )
    dependency_fixture.access_plan = _access_plan(
        dependency_fixture.candidate.ordered_intent_batch.intents
    )
    dependency_transaction = dependency_fixture.begin()
    dependency_transaction.stage_committed_events(
        event,
        EventDependencyBase(
            run_id=dependency_fixture.writer.run_envelope.run_id,
            case_id=DEMO_CASE_ID,
            event_id=event.event_id,
            depends_on_event_id="event:forged-dependency",
            dependency_kind="VALIDATION_ONLY",
            source_identity=SourceIdentity.VALIDATION_ONLY,
        ),
    )
    with pytest.raises(PrepareRejected, match="extension lineage"):
        dependency_transaction.prepare()
    dependency_transaction.rollback()


def test_receipt_view_and_validation_faults_preserve_committed_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conversion_fixture = _fixture(tmp_path / "conversion")
    conversion = conversion_fixture.begin()
    conversion.prepare()

    def fail_conversion(_: Any) -> Any:
        raise OSError("local receipt view conversion failed")

    monkeypatch.setattr(conversion_fixture.adapter, "receipt_ref", fail_conversion)
    receipt = conversion.commit()
    assert conversion.state is TransactionState.COMMITTED
    assert conversion.core_receipt is not None
    assert conversion.recover_receipt_ref() == receipt
    with pytest.raises(TransactionError, match="cannot be rolled back"):
        conversion.rollback()

    validation_fixture = _fixture(tmp_path / "validation")
    validation = validation_fixture.begin()
    token = validation.prepare()

    def fail_validation(_: Any) -> None:
        raise TransactionError("local receipt validation failed")

    monkeypatch.setattr(validation, "_validate_core_receipt", fail_validation)
    with pytest.raises(TransactionError, match="local receipt validation"):
        validation.commit(token)
    assert validation.state is TransactionState.COMMITTED
    assert validation.core_receipt is not None
    assert validation.commit(token) == validation.recover_receipt_ref()
    with pytest.raises(TransactionError, match="cannot be rolled back"):
        validation.rollback()
