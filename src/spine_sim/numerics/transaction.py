"""M02 transaction eligibility and the minimal M00 writer adapter.

M02 owns physical/numerical commit eligibility; M00 remains the sole owner of
canonical persistence, commit markers, and receipt identities.  This module
therefore validates a frozen :class:`PreparedCandidate`, delegates publication
to the public ``ResultWriter`` transaction API, and returns only a
``CommitReceiptRef`` to the M00 receipt.
"""

from __future__ import annotations

import os
import time
from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, TypeVar, cast

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import (
    ContractViolation,
    IdempotencyConflict,
    TransactionError,
)
from spine_sim.foundation.models import (
    AcceptedPointBase,
    CommitReceiptBase,
    CommittedEventBase,
    RecordBase,
)
from spine_sim.foundation.writer import ResultTransaction, ResultWriter

from .contracts import (
    M02_SCHEMA_VERSION,
    CommitReceiptRef,
    M02ReasonCode,
    PreparedCandidate,
    PrepareTokenRef,
    ProvisionalIntent,
    RollbackToken,
)

EvaluationResult = TypeVar("EvaluationResult")
SnapshotProvider = Callable[[], Any]
OwnerRollbackHandler = Callable[[RollbackToken], None]


class TransactionState(StrEnum):
    CREATED = "CREATED"
    PREPARED = "PREPARED"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"


class TransactionFaultStage(StrEnum):
    """Stable M02 fault points around the public M00 transaction call."""

    EVALUATE_BEFORE = "evaluate_before"
    EVALUATE_AFTER = "evaluate_after"
    PREPARE_BEFORE = "prepare_before"
    PREPARE_AFTER = "prepare_after"
    RECEIPT_BEFORE = "receipt_before"
    COMMIT_MARKER_BEFORE = "commit_marker_before"
    COMMIT_MARKER_AFTER = "commit_marker_after"
    RECEIPT_AFTER = "receipt_after"
    ROLLBACK_BEFORE = "rollback_before"
    ROLLBACK_AFTER = "rollback_after"


TransactionFaultInjector = Callable[[TransactionFaultStage], None]


def _noop_fault(_: TransactionFaultStage) -> None:
    return None


def _require_nonempty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{name} must be a nonempty string")


def _require_hash(value: str, name: str) -> None:
    _require_nonempty(value, name)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ContractViolation(f"{name} must be a canonical SHA-256 hash")


def _unique(values: Iterable[str], name: str) -> None:
    materialized = tuple(values)
    if len(set(materialized)) != len(materialized):
        raise ContractViolation(f"duplicate {name}")


@dataclass(frozen=True, slots=True)
class ResourceVersion:
    resource_id: str
    version: str

    def __post_init__(self) -> None:
        _require_nonempty(self.resource_id, "resource_id")
        _require_nonempty(self.version, "resource version")


@dataclass(frozen=True, slots=True)
class ResourceVersionExpectation:
    """Expected base version for one intent/resource access."""

    intent_id: str
    resource_id: str
    expected_version: str

    def __post_init__(self) -> None:
        _require_nonempty(self.intent_id, "intent_id")
        _require_nonempty(self.resource_id, "resource_id")
        _require_nonempty(self.expected_version, "expected_version")


@dataclass(frozen=True, slots=True)
class PrepareAccessPlan:
    """Versioned read/write expectations supplied by the physical owners."""

    expected_parent_state_version: str
    resource_expectations: tuple[ResourceVersionExpectation, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.expected_parent_state_version, "expected_parent_state_version")
        keys = tuple((item.intent_id, item.resource_id) for item in self.resource_expectations)
        if len(set(keys)) != len(keys):
            raise ContractViolation("duplicate intent/resource version expectation")


@dataclass(frozen=True, slots=True)
class TransactionAuthoritySnapshot:
    """Immutable accepted authority observed immediately before prepare."""

    run_id: str
    case_id: str
    parent_accepted_state_id: str
    parent_commit_receipt_id: str
    parent_state_version: str
    parent_state_hash: str
    accepted_snapshot_hash: str
    schema_version: str
    registry_hash: str
    config_hash: str
    owner_build_hashes: tuple[str, ...]
    owner_token_versions: tuple[tuple[str, str], ...]
    resource_versions: tuple[ResourceVersion, ...]
    damage_store_version: str | None
    external_read_locks: tuple[str, ...] = ()
    external_write_locks: tuple[str, ...] = ()
    persistence_available: bool = True

    def __post_init__(self) -> None:
        for name in (
            "run_id",
            "case_id",
            "parent_accepted_state_id",
            "parent_commit_receipt_id",
            "parent_state_version",
            "schema_version",
        ):
            _require_nonempty(str(getattr(self, name)), name)
        for name in (
            "parent_state_hash",
            "accepted_snapshot_hash",
            "registry_hash",
            "config_hash",
        ):
            _require_hash(str(getattr(self, name)), name)
        for value in self.owner_build_hashes:
            _require_hash(value, "owner_build_hash")
        _unique(self.owner_build_hashes, "owner build hashes")
        owner_ids = tuple(item[0] for item in self.owner_token_versions)
        _unique(owner_ids, "owner token version IDs")
        for owner_id, version in self.owner_token_versions:
            _require_nonempty(owner_id, "owner token version owner_id")
            _require_nonempty(version, "owner token version")
        resource_ids = tuple(item.resource_id for item in self.resource_versions)
        _unique(resource_ids, "authority resource versions")
        _unique(self.external_read_locks, "external read locks")
        _unique(self.external_write_locks, "external write locks")
        if self.damage_store_version is not None:
            _require_nonempty(self.damage_store_version, "damage_store_version")


@dataclass(frozen=True, slots=True)
class RollbackReport:
    transaction_id: str
    token_refs: tuple[str, ...]
    failed_token_refs: tuple[str, ...]
    accepted_snapshot_hash: str
    m00_staging_closed: bool
    complete: bool


class OwnerSideEffectDetected(ContractViolation):
    code = M02ReasonCode.OWNER_SIDE_EFFECT_DETECTED.value


class PrepareRejected(TransactionError):
    code = M02ReasonCode.PREPARE_REJECTED.value


class RollbackFailed(TransactionError):
    code = M02ReasonCode.ROLLBACK_FAILURE.value


class SideEffectSentinel:
    """Hash an accepted snapshot before/after trial-only operations."""

    def __init__(self, snapshot_provider: SnapshotProvider) -> None:
        self._snapshot_provider = snapshot_provider

    def capture_hash(self) -> str:
        return semantic_hash(self._snapshot_provider())

    def assert_unchanged(self, expected_hash: str, *, stage: str) -> str:
        actual_hash = self.capture_hash()
        if actual_hash != expected_hash:
            raise OwnerSideEffectDetected(
                "owner changed accepted state during a trial-only operation",
                details={
                    "reason_code": M02ReasonCode.OWNER_SIDE_EFFECT_DETECTED.value,
                    "stage": stage,
                    "expected_snapshot_hash": expected_hash,
                    "actual_snapshot_hash": actual_hash,
                },
            )
        return actual_hash


class M00ResultWriterAdapter:
    """Thin adapter over M00 public transaction calls and core receipt refs."""

    def __init__(self, writer: ResultWriter) -> None:
        self.writer = writer

    @property
    def run_id(self) -> str:
        return self.writer.run_envelope.run_id

    @property
    def registry_hash(self) -> str:
        return self.writer.registry.snapshot_hash

    @property
    def config_hash(self) -> str:
        return self.writer.run_envelope.resolved_run_config_hash

    def begin_transaction(
        self, case_id: str, parent_state_id: str, idempotency_key: str
    ) -> ResultTransaction:
        return self.writer.begin_transaction(case_id, parent_state_id, idempotency_key)

    def persistence_ready(self) -> bool:
        required = (
            self.writer.root,
            self.writer.root / "transactions" / "staging",
            self.writer.root / "transactions" / "committed",
            self.writer.root / "transactions" / "receipts",
        )
        return self.writer.registry.frozen and all(
            path.is_dir() and os.access(path, os.W_OK | os.X_OK) for path in required
        )

    def authority_snapshot(
        self,
        *,
        case_id: str,
        parent_accepted_state_id: str,
        parent_commit_receipt_id: str,
        parent_state_version: str,
        parent_state_hash: str,
        accepted_snapshot_hash: str,
        owner_build_hashes: tuple[str, ...],
        owner_token_versions: tuple[tuple[str, str], ...],
        resource_versions: tuple[ResourceVersion, ...],
        damage_store_version: str | None,
        external_read_locks: tuple[str, ...] = (),
        external_write_locks: tuple[str, ...] = (),
        persistence_available: bool = True,
    ) -> TransactionAuthoritySnapshot:
        return TransactionAuthoritySnapshot(
            run_id=self.run_id,
            case_id=case_id,
            parent_accepted_state_id=parent_accepted_state_id,
            parent_commit_receipt_id=parent_commit_receipt_id,
            parent_state_version=parent_state_version,
            parent_state_hash=parent_state_hash,
            accepted_snapshot_hash=accepted_snapshot_hash,
            schema_version=M02_SCHEMA_VERSION,
            registry_hash=self.registry_hash,
            config_hash=self.config_hash,
            owner_build_hashes=owner_build_hashes,
            owner_token_versions=owner_token_versions,
            resource_versions=resource_versions,
            damage_store_version=damage_store_version,
            external_read_locks=external_read_locks,
            external_write_locks=external_write_locks,
            persistence_available=persistence_available,
        )

    @staticmethod
    def receipt_ref(receipt: CommitReceiptBase) -> CommitReceiptRef:
        return CommitReceiptRef.create(
            receipt_id=receipt.receipt_id,
            committed_state_id=receipt.committed_state_id,
            candidate_hash=receipt.candidate_hash,
            commit_marker_hash=receipt.commit_marker_hash,
            core_receipt_dataset_id=CommitReceiptBase.__dataset_id__,
            metadata_unit="1",
        )


class M02TransactionCoordinator:
    """Create M02-eligible transactions without owning M00 core identity."""

    def __init__(
        self,
        adapter: M00ResultWriterAdapter,
        *,
        sentinel: SideEffectSentinel,
        rollback_handlers: Mapping[str, OwnerRollbackHandler],
        fault_injector: TransactionFaultInjector | None = None,
        prepare_token_ttl_ns: int | None = None,
        monotonic_ns: Callable[[], int] = time.monotonic_ns,
    ) -> None:
        if prepare_token_ttl_ns is not None and prepare_token_ttl_ns <= 0:
            raise ContractViolation("prepare token TTL must be positive")
        self.adapter = adapter
        self.sentinel = sentinel
        self.rollback_handlers = dict(rollback_handlers)
        self.fault_injector = fault_injector or _noop_fault
        self.prepare_token_ttl_ns = prepare_token_ttl_ns
        self.monotonic_ns = monotonic_ns
        self._candidate_by_key: dict[tuple[str, str], str] = {}
        self._active_by_key: dict[tuple[str, str], M02PreparedTransaction] = {}

    def evaluate(self, evaluator: Callable[[], EvaluationResult]) -> EvaluationResult:
        """Run one owner evaluation and reject any accepted-state side effect."""

        baseline = self.sentinel.capture_hash()
        self.fault_injector(TransactionFaultStage.EVALUATE_BEFORE)
        try:
            result = evaluator()
        except Exception as error:
            try:
                self.sentinel.assert_unchanged(baseline, stage="evaluate_exception")
            except OwnerSideEffectDetected as side_effect:
                raise side_effect from error
            raise
        self.sentinel.assert_unchanged(baseline, stage="evaluate")
        self.fault_injector(TransactionFaultStage.EVALUATE_AFTER)
        return result

    def begin(
        self,
        candidate: PreparedCandidate,
        *,
        authority: TransactionAuthoritySnapshot,
        access_plan: PrepareAccessPlan,
    ) -> M02PreparedTransaction:
        key = (authority.case_id, candidate.idempotency_key)
        prior_hash = self._candidate_by_key.get(key)
        if prior_hash is not None and prior_hash != candidate.semantic_hash:
            raise IdempotencyConflict(
                "same M02 idempotency key was bound to a different frozen candidate",
                details={
                    "reason_code": M02ReasonCode.COMMIT_CONFLICT.value,
                    "idempotency_key": candidate.idempotency_key,
                    "existing_candidate_hash": prior_hash,
                    "incoming_candidate_hash": candidate.semantic_hash,
                },
            )
        active = self._active_by_key.get(key)
        if active is not None and active.state in {
            TransactionState.CREATED,
            TransactionState.PREPARED,
            TransactionState.ROLLBACK_FAILED,
        }:
            raise TransactionError("an equivalent M02 transaction is already active")
        self._candidate_by_key[key] = candidate.semantic_hash
        transaction = M02PreparedTransaction(
            coordinator=self,
            candidate=candidate,
            authority=authority,
            access_plan=access_plan,
            m00_transaction=self.adapter.begin_transaction(
                authority.case_id,
                candidate.parent_accepted_state_id,
                candidate.idempotency_key,
            ),
            baseline_snapshot_hash=self.sentinel.capture_hash(),
        )
        self._active_by_key[key] = transaction
        return transaction


class M02PreparedTransaction:
    """One frozen candidate progressing through M02 prepare and M00 commit."""

    def __init__(
        self,
        *,
        coordinator: M02TransactionCoordinator,
        candidate: PreparedCandidate,
        authority: TransactionAuthoritySnapshot,
        access_plan: PrepareAccessPlan,
        m00_transaction: ResultTransaction,
        baseline_snapshot_hash: str,
    ) -> None:
        self.coordinator = coordinator
        self.candidate = candidate
        self.authority = authority
        self.access_plan = access_plan
        self._m00_transaction = m00_transaction
        self._baseline_snapshot_hash = baseline_snapshot_hash
        self._accepted_records: list[RecordBase] = []
        self._event_records: list[RecordBase] = []
        self._transaction_records: list[RecordBase] = []
        self._prepare_token: PrepareTokenRef | None = None
        self._m00_candidate_hash: str | None = None
        self._core_receipt: CommitReceiptBase | None = None
        self._receipt_ref: CommitReceiptRef | None = None
        self._rollback_report: RollbackReport | None = None
        self._rolled_back_tokens: set[str] = set()
        self._caller_state_and_ledger_refs: tuple[str, ...] = ()
        self.state = TransactionState.CREATED

    @property
    def transaction_id(self) -> str:
        return self._m00_transaction.transaction_id

    @property
    def prepare_token(self) -> PrepareTokenRef | None:
        return self._prepare_token

    @property
    def receipt_ref(self) -> CommitReceiptRef | None:
        return self._receipt_ref

    @property
    def core_receipt(self) -> CommitReceiptBase | None:
        return self._core_receipt

    def recover_receipt_ref(self) -> CommitReceiptRef:
        """Recover the M02 view of an already-authoritative M00 receipt."""

        if self._receipt_ref is not None:
            return self._receipt_ref
        core_receipt = self._core_receipt or self._m00_transaction.committed_receipt
        if core_receipt is None:
            raise TransactionError("committed transaction has no recoverable M00 receipt")
        self._core_receipt = core_receipt
        # Bypass an adapter instance override/fault during recovery.  This is a
        # pure view conversion over the immutable, registry-validated receipt.
        self._receipt_ref = M00ResultWriterAdapter.receipt_ref(core_receipt)
        return self._receipt_ref

    @property
    def last_rollback_report(self) -> RollbackReport | None:
        return self._rollback_report

    def stage_accepted_point(self, *records: RecordBase) -> None:
        self._require_created()
        self._m00_transaction.stage_accepted_point(*records)
        self._accepted_records.extend(records)

    def stage_committed_events(self, *records: RecordBase) -> None:
        self._require_created()
        self._m00_transaction.stage_committed_events(*records)
        self._event_records.extend(records)

    def stage_transaction_records(self, *records: RecordBase) -> None:
        self._require_created()
        self._m00_transaction.stage_transaction_records(*records)
        self._transaction_records.extend(records)

    def stage_state_and_ledger_references(self, refs: Iterable[str]) -> None:
        self._require_created()
        materialized = tuple(refs)
        _unique(materialized, "state/ledger references")
        if any(not item for item in materialized):
            raise ContractViolation("state/ledger references must be nonempty")
        self._caller_state_and_ledger_refs = materialized

    def prepare(self) -> PrepareTokenRef:
        if self.state is TransactionState.PREPARED and self._prepare_token is not None:
            return self._prepare_token
        self._require_created()
        self.coordinator.fault_injector(TransactionFaultStage.PREPARE_BEFORE)
        self.coordinator.sentinel.assert_unchanged(self._baseline_snapshot_hash, stage="prepare")
        self._validate_prepare_preconditions()
        self._validate_staged_core_identity()
        self._m00_transaction.stage_state_and_ledger_references(
            self._semantic_state_and_ledger_refs()
        )
        m00_candidate_hash = self._m00_transaction.prepare()
        _require_hash(m00_candidate_hash, "M00 prepared candidate hash")
        expires_at = (
            self.coordinator.monotonic_ns() + self.coordinator.prepare_token_ttl_ns
            if self.coordinator.prepare_token_ttl_ns is not None
            else None
        )
        token_ref = stable_content_id(
            "m02_prepare_token",
            {
                "candidate_id": self.candidate.candidate_id,
                "m00_candidate_hash": m00_candidate_hash,
                "parent": self.candidate.parent_accepted_state_id,
                "idempotency_key": self.candidate.idempotency_key,
            },
        )
        self._prepare_token = PrepareTokenRef.create(
            token_ref=token_ref,
            candidate_id=self.candidate.candidate_id,
            candidate_hash=m00_candidate_hash,
            parent_accepted_state_id=self.candidate.parent_accepted_state_id,
            idempotency_key=self.candidate.idempotency_key,
            expires_at_monotonic_ns=expires_at,
            metadata_unit="1",
        )
        self._m00_candidate_hash = m00_candidate_hash
        self.state = TransactionState.PREPARED
        self.coordinator.fault_injector(TransactionFaultStage.PREPARE_AFTER)
        return self._prepare_token

    def commit(self, token: PrepareTokenRef | None = None) -> CommitReceiptRef:
        if self.state is TransactionState.COMMITTED and self._receipt_ref is not None:
            return self._receipt_ref
        if self.state is not TransactionState.PREPARED or self._prepare_token is None:
            raise TransactionError("M02 prepare must succeed before commit")
        supplied = token or self._prepare_token
        self._validate_prepare_token(supplied)
        self.coordinator.sentinel.assert_unchanged(
            self._baseline_snapshot_hash, stage="commit_before_publication"
        )
        try:
            self.coordinator.fault_injector(TransactionFaultStage.RECEIPT_BEFORE)
            self.coordinator.fault_injector(TransactionFaultStage.COMMIT_MARKER_BEFORE)
            core_receipt = self._m00_transaction.commit()
        except Exception as error:
            published_receipt = self._m00_transaction.committed_receipt
            if published_receipt is not None:
                self._capture_committed_receipt(published_receipt)
                raise
            try:
                self.rollback()
            except Exception as rollback_error:
                raise RollbackFailed(
                    "commit failed and rollback did not complete",
                    details={
                        "reason_code": M02ReasonCode.ROLLBACK_FAILURE.value,
                        "commit_error": repr(error),
                        "rollback_error": repr(rollback_error),
                    },
                ) from error
            raise
        # M00 returning means its final marker/receipt is authoritative.  Mark
        # the local state committed before any M02 receipt-view validation so
        # even a downstream adapter defect can never make rollback legal.
        self._capture_committed_receipt(core_receipt)
        self._validate_core_receipt(core_receipt)
        self.coordinator.fault_injector(TransactionFaultStage.COMMIT_MARKER_AFTER)
        self.coordinator.fault_injector(TransactionFaultStage.RECEIPT_AFTER)
        return self.recover_receipt_ref()

    def _capture_committed_receipt(self, receipt: CommitReceiptBase) -> None:
        """Make publication irreversible before validation or view conversion."""

        self._core_receipt = receipt
        self.state = TransactionState.COMMITTED
        try:
            self._receipt_ref = self.coordinator.adapter.receipt_ref(receipt)
        except Exception:
            # A local adapter acknowledgement failure cannot change the M00
            # marker's authority.  The static conversion remains recoverable.
            self._receipt_ref = M00ResultWriterAdapter.receipt_ref(receipt)

    def rollback(self) -> RollbackReport:
        if self.state is TransactionState.COMMITTED:
            raise TransactionError(
                "a committed M00 receipt cannot be rolled back",
                details={"reason_code": M02ReasonCode.COMMIT_CONFLICT.value},
            )
        if self.state is TransactionState.ROLLED_BACK and self._rollback_report is not None:
            return self._rollback_report

        failures: dict[str, str] = {}
        try:
            self.coordinator.fault_injector(TransactionFaultStage.ROLLBACK_BEFORE)
        except Exception as error:
            failures["M02_COORDINATOR"] = repr(error)

        for token in self.candidate.rollback_tokens:
            if token.token_ref in self._rolled_back_tokens:
                continue
            scope_errors = self._rollback_token_scope_errors(token)
            if scope_errors:
                failures[token.token_ref] = repr(scope_errors)
                continue
            handler = self.coordinator.rollback_handlers.get(token.owner_id)
            if handler is None:
                failures[token.token_ref] = "unknown rollback owner"
                continue
            try:
                handler(token)
            except Exception as error:
                failures[token.token_ref] = repr(error)
            else:
                self._rolled_back_tokens.add(token.token_ref)

        m00_closed = True
        try:
            self._m00_transaction.rollback()
        except Exception as error:
            m00_closed = False
            failures["M00_STAGING"] = repr(error)

        try:
            snapshot_hash = self.coordinator.sentinel.assert_unchanged(
                self._baseline_snapshot_hash, stage="rollback"
            )
        except OwnerSideEffectDetected as error:
            snapshot_hash = self.coordinator.sentinel.capture_hash()
            failures["ACCEPTED_SNAPSHOT"] = repr(error)

        complete = not failures and len(self._rolled_back_tokens) == len(
            self.candidate.rollback_tokens
        )
        self._rollback_report = RollbackReport(
            transaction_id=self.transaction_id,
            token_refs=tuple(item.token_ref for item in self.candidate.rollback_tokens),
            failed_token_refs=tuple(sorted(failures)),
            accepted_snapshot_hash=snapshot_hash,
            m00_staging_closed=m00_closed,
            complete=complete,
        )
        self.state = TransactionState.ROLLED_BACK if complete else TransactionState.ROLLBACK_FAILED
        if failures:
            raise RollbackFailed(
                "one or more rollback participants failed",
                details={
                    "reason_code": M02ReasonCode.ROLLBACK_FAILURE.value,
                    "failures": failures,
                    "last_valid_state_id": self.candidate.parent_accepted_state_id,
                    "report": self._rollback_report,
                },
            )
        self.coordinator.fault_injector(TransactionFaultStage.ROLLBACK_AFTER)
        return self._rollback_report

    def _validate_prepare_preconditions(self) -> None:
        candidate = self.candidate
        authority = self.authority
        mismatches: dict[str, Any] = {}
        comparisons = {
            "run_id": (authority.run_id, self.coordinator.adapter.run_id),
            "parent_accepted_state_id": (
                candidate.parent_accepted_state_id,
                authority.parent_accepted_state_id,
            ),
            "parent_commit_receipt_id": (
                candidate.parent_commit_receipt_id,
                authority.parent_commit_receipt_id,
            ),
            "parent_state_hash": (candidate.parent_state_hash, authority.parent_state_hash),
            "schema_version": (candidate.schema_version, authority.schema_version),
            "registry_hash": (candidate.registry_hash, authority.registry_hash),
            "config_hash": (candidate.config_hash, authority.config_hash),
            "adapter_registry_hash": (
                authority.registry_hash,
                self.coordinator.adapter.registry_hash,
            ),
            "adapter_config_hash": (
                authority.config_hash,
                self.coordinator.adapter.config_hash,
            ),
            "parent_state_version": (
                self.access_plan.expected_parent_state_version,
                authority.parent_state_version,
            ),
            "accepted_snapshot_hash": (
                self._baseline_snapshot_hash,
                authority.accepted_snapshot_hash,
            ),
        }
        for name, (actual, expected) in comparisons.items():
            if actual != expected:
                mismatches[name] = {"expected": expected, "actual": actual}
        if set(candidate.owner_build_hashes) != set(authority.owner_build_hashes):
            mismatches["owner_build_hashes"] = {
                "expected": sorted(authority.owner_build_hashes),
                "actual": sorted(candidate.owner_build_hashes),
            }
        if len(set(candidate.owner_build_hashes)) != len(candidate.owner_build_hashes):
            mismatches["duplicate_owner_build_hashes"] = list(candidate.owner_build_hashes)
        if len(set(candidate.numerical_quality_hashes)) != len(candidate.numerical_quality_hashes):
            mismatches["duplicate_numerical_quality_hashes"] = list(
                candidate.numerical_quality_hashes
            )
        if candidate.metadata.schema_version != M02_SCHEMA_VERSION:
            mismatches["m02_schema_version"] = {
                "expected": M02_SCHEMA_VERSION,
                "actual": candidate.metadata.schema_version,
            }
        if mismatches:
            self._raise_prepare("stale parent/version/hash precondition", mismatches)

        if not authority.persistence_available or not self.coordinator.adapter.persistence_ready():
            self._raise_prepare("M00 persistence staging is unavailable", {})
        if not candidate.persistence_ready:
            self._raise_prepare("candidate persistence gate is not complete", {})
        if not candidate.numerical_quality_hashes:
            self._raise_prepare("candidate has no numerical quality evidence", {})
        if candidate.proposed_committed_event_ids and not candidate.located_event_group_refs:
            self._raise_prepare("committed event candidate lacks located-event evidence", {})

        self._validate_rollback_tokens()
        self._validate_resource_accesses(candidate.ordered_intent_batch.intents)

    def _validate_rollback_tokens(self) -> None:
        for token in self.candidate.rollback_tokens:
            mismatches = self._rollback_token_scope_errors(token)
            if mismatches:
                self._raise_prepare(
                    "rollback token is unknown or crosses run/parent/trial/version",
                    {"token_ref": token.token_ref, **mismatches},
                )

    def _rollback_token_scope_errors(self, token: RollbackToken) -> dict[str, Any]:
        owner_versions = dict(self.authority.owner_token_versions)
        expected_version = owner_versions.get(token.owner_id)
        mismatches: dict[str, Any] = {}
        checks = {
            "run_id": (token.run_id, self.authority.run_id),
            "trial_id": (token.trial_id, self.candidate.trial_id),
            "parent_accepted_state_id": (
                token.parent_accepted_state_id,
                self.candidate.parent_accepted_state_id,
            ),
            "parent_state_hash": (
                token.parent_state_hash,
                self.candidate.parent_state_hash,
            ),
            "token_version": (token.token_version, expected_version),
        }
        for name, (actual, expected) in checks.items():
            if expected is None or actual != expected:
                mismatches[name] = {"expected": expected, "actual": actual}
        if token.owner_id not in self.coordinator.rollback_handlers:
            mismatches["rollback_handler"] = {
                "expected": token.owner_id,
                "actual": None,
            }
        return mismatches

    def _validate_resource_accesses(self, intents: tuple[ProvisionalIntent, ...]) -> None:
        current_versions = {
            item.resource_id: item.version for item in self.authority.resource_versions
        }
        expectations = {
            (item.intent_id, item.resource_id): item.expected_version
            for item in self.access_plan.resource_expectations
        }
        declared_pairs = {
            (intent.intent_id, resource)
            for intent in intents
            for resource in (*intent.read_set, *intent.write_set)
        }
        if set(expectations) != declared_pairs:
            self._raise_prepare(
                "read/write version expectations do not exactly cover intent access sets",
                {
                    "missing": sorted(declared_pairs - set(expectations)),
                    "extra": sorted(set(expectations) - declared_pairs),
                },
            )

        stale: list[dict[str, str | None]] = []
        intent_by_id = {item.intent_id: item for item in intents}
        for (intent_id, resource_id), expected in expectations.items():
            current = current_versions.get(resource_id)
            if current != expected:
                stale.append(
                    {
                        "intent_id": intent_id,
                        "resource_id": resource_id,
                        "expected": expected,
                        "current": current,
                    }
                )
            if expected not in intent_by_id[intent_id].dependency_versions:
                stale.append(
                    {
                        "intent_id": intent_id,
                        "resource_id": resource_id,
                        "expected": expected,
                        "current": "missing_from_intent_dependency_versions",
                    }
                )
        if stale:
            self._raise_prepare("stale or incomplete resource version dependency", {"stale": stale})

        read_resources = {resource for intent in intents for resource in intent.read_set}
        write_resources = [resource for intent in intents for resource in intent.write_set]
        multiple_writers = sorted(
            resource for resource, count in Counter(write_resources).items() if count > 1
        )
        external_conflicts = {
            "read_vs_external_write": sorted(
                read_resources & set(self.authority.external_write_locks)
            ),
            "write_vs_external_read": sorted(
                set(write_resources) & set(self.authority.external_read_locks)
            ),
            "write_vs_external_write": sorted(
                set(write_resources) & set(self.authority.external_write_locks)
            ),
            "multiple_internal_writers": multiple_writers,
        }
        if any(external_conflicts.values()):
            self._raise_prepare("read/write set conflict", external_conflicts)

        damage_resources = {
            resource
            for resource in (*read_resources, *write_resources)
            if "damagestore" in resource.lower().replace("_", "")
        }
        if damage_resources:
            batch_version = self.candidate.ordered_intent_batch.damage_store_parent_version
            if (
                batch_version is None
                or self.authority.damage_store_version is None
                or batch_version != self.authority.damage_store_version
            ):
                self._raise_prepare(
                    "DamageStore parent version conflict",
                    {
                        "resources": sorted(damage_resources),
                        "candidate_version": batch_version,
                        "authority_version": self.authority.damage_store_version,
                    },
                )

    def _validate_staged_core_identity(self) -> None:
        core_points = [
            item for item in self._accepted_records if isinstance(item, AcceptedPointBase)
        ]
        if len(core_points) != 1:
            self._raise_prepare(
                "candidate requires exactly one M00 AcceptedPointBase",
                {"count": len(core_points)},
            )
        point = core_points[0]
        if (
            point.point_id != self.candidate.proposed_accepted_point_id
            or point.parent_state_id != self.candidate.parent_accepted_state_id
            or point.commit_receipt_id is not None
        ):
            self._raise_prepare(
                "staged M00 accepted point identity/parent/receipt does not match candidate",
                {
                    "candidate_point_id": self.candidate.proposed_accepted_point_id,
                    "staged_point_id": point.point_id,
                    "candidate_parent": self.candidate.parent_accepted_state_id,
                    "staged_parent": point.parent_state_id,
                    "staged_receipt": point.commit_receipt_id,
                },
            )

        core_events = [item for item in self._event_records if isinstance(item, CommittedEventBase)]
        staged_event_ids = {item.event_id for item in core_events}
        proposed_event_ids = set(self.candidate.proposed_committed_event_ids)
        if staged_event_ids != proposed_event_ids:
            self._raise_prepare(
                "staged M00 committed-event identities do not match candidate",
                {
                    "proposed": sorted(proposed_event_ids),
                    "staged": sorted(staged_event_ids),
                },
            )
        for event in core_events:
            if not event.committed or event.commit_receipt_id is not None:
                self._raise_prepare(
                    "staged event must be committed candidate without a competing receipt",
                    {"event_id": event.event_id},
                )
        self._validate_extension_lineage(
            point.point_id,
            point.accepted_state_id,
            proposed_event_ids,
        )

    def _validate_extension_lineage(
        self,
        point_id: str,
        accepted_state_id: str,
        proposed_event_ids: set[str],
    ) -> None:
        """Require extension rows to reference, never replace, M00 core IDs."""

        mismatches: list[dict[str, Any]] = []
        records = (
            *self._accepted_records,
            *self._event_records,
            *self._transaction_records,
        )
        scalar_references: dict[str, set[str]] = {
            "point_id": {point_id},
            "accepted_state_id": {accepted_state_id},
            "parent_state_id": {self.candidate.parent_accepted_state_id},
            "parent_accepted_state_id": {self.candidate.parent_accepted_state_id},
            "pre_event_accepted_state_id": {self.candidate.parent_accepted_state_id},
            "post_event_accepted_state_id": {accepted_state_id},
            "last_valid_state_id": {self.candidate.parent_accepted_state_id},
            "event_id": proposed_event_ids,
            "depends_on_event_id": proposed_event_ids,
            "trial_id": {self.candidate.trial_id},
            "event_point_trial_id": {self.candidate.trial_id},
        }
        for record in records:
            for field, allowed in scalar_references.items():
                if not hasattr(record, field):
                    continue
                actual = getattr(record, field)
                if actual is not None and actual not in allowed:
                    mismatches.append(
                        {
                            "dataset": record.__dataset_id__,
                            "field": field,
                            "expected": sorted(allowed),
                            "actual": actual,
                        }
                    )
            if hasattr(record, "event_ids"):
                unknown_events = set(cast(Any, record).event_ids) - proposed_event_ids
                if unknown_events:
                    mismatches.append(
                        {
                            "dataset": record.__dataset_id__,
                            "field": "event_ids",
                            "expected": sorted(proposed_event_ids),
                            "actual": sorted(unknown_events),
                        }
                    )
        if mismatches:
            self._raise_prepare(
                "M02 extension lineage does not reference the staged M00 core identity",
                {"mismatches": mismatches},
            )

    def _semantic_state_and_ledger_refs(self) -> tuple[str, ...]:
        """Bind M00's ordered-intents hash to the complete frozen M02 decision."""

        mandatory = (
            f"m02:candidate:{self.candidate.semantic_hash}",
            f"m02:intent-batch:{self.candidate.ordered_intent_batch.semantic_hash}",
            *(
                f"m02:intent:{item.semantic_hash}"
                for item in self.candidate.ordered_intent_batch.intents
            ),
            *(
                f"m02:rollback-token:{item.semantic_hash}"
                for item in self.candidate.rollback_tokens
            ),
            *(f"m02:quality:{item}" for item in self.candidate.numerical_quality_hashes),
            *(f"m02:owner-build:{item}" for item in self.candidate.owner_build_hashes),
            *self.candidate.final_opaque_state_refs,
            *self.candidate.located_event_group_refs,
            *self._caller_state_and_ledger_refs,
        )
        return tuple(dict.fromkeys(mandatory))

    def _validate_prepare_token(self, token: PrepareTokenRef) -> None:
        assert self._prepare_token is not None
        if token != self._prepare_token:
            raise TransactionError("prepare token does not belong to this transaction")
        expires_at = token.expires_at_monotonic_ns
        if expires_at is not None and self.coordinator.monotonic_ns() >= expires_at:
            self.rollback()
            raise TransactionError("prepare token expired before commit")

    def _validate_core_receipt(self, receipt: CommitReceiptBase) -> None:
        assert self._m00_candidate_hash is not None
        mismatches: dict[str, Any] = {}
        expected = {
            "idempotency_key": self.candidate.idempotency_key,
            "parent_state_id": self.candidate.parent_accepted_state_id,
            "candidate_hash": self._m00_candidate_hash,
            "registry_hash": self.authority.registry_hash,
            "config_hash": self.authority.config_hash,
        }
        for name, expected_value in expected.items():
            actual = getattr(receipt, name)
            if actual != expected_value:
                mismatches[name] = {"expected": expected_value, "actual": actual}
        if mismatches:
            raise TransactionError(
                "M00 receipt does not match the prepared M02 transaction",
                details={
                    "reason_code": M02ReasonCode.COMMIT_CONFLICT.value,
                    "mismatches": mismatches,
                },
            )

    def _raise_prepare(self, message: str, details: dict[str, Any]) -> None:
        raise PrepareRejected(
            message,
            details={
                "reason_code": M02ReasonCode.PREPARE_REJECTED.value,
                "candidate_id": self.candidate.candidate_id,
                **details,
            },
        )

    def _require_created(self) -> None:
        if self.state is not TransactionState.CREATED:
            raise TransactionError(
                f"transaction staging requires CREATED state, got {self.state.value}"
            )


def transaction_staging_paths(root: Path) -> tuple[Path, ...]:
    """Read-only diagnostic helper used by atomicity tests and reports."""

    staging = root / "transactions" / "staging"
    return tuple(sorted(staging.iterdir())) if staging.is_dir() else ()
