"""Deterministic M02 decision-chain replay built on the public M00 manifest.

M00 remains the authority for run-level replay metadata.  This module adds a
canonical, per-case M02 numerical decision chain and field-level verification.
Runtime scheduling and M01 cache/materialization observations are retained as
diagnostics, but cannot enter either bitwise or semantic numerical identity.
"""

from __future__ import annotations

import dataclasses
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from spine_sim.foundation.canonical import canonical_json_bytes, semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.replay import (
    ReplayDifference,
    ReplayManifest,
    ReplayMode,
)

from .contracts import DiagnosticLevel, ReplayDecisionRecord

M02_REPLAY_SCHEMA_VERSION = "1.0.0"
M02_CANONICAL_ORDER_POLICY = (
    "CASE_ID>LOGICAL_STEP_INDEX>DEPENDENCY_RANK>DECISION_STAGE>OWNER_ID>STABLE_CONTENT"
)
M02_CANONICAL_REDUCTION_ORDER = "OWNER_ID_BLOCK_ID_COMPONENT_INDEX"
M02_THREAD_POLICY = "EXPLICIT_CALLER_CONTROLLED_PER_CASE_NO_CROSS_CASE_REDUCTION"
M02_FLOATING_POINT_PROFILE = "IEEE754_BINARY64_ROUND_TO_NEAREST_TIES_TO_EVEN"
M02_FIELD_TOLERANCE_PROFILE_ID = "M02_REPLAY_FIELD_TOLERANCES"
M02_FIELD_TOLERANCE_PROFILE_VERSION = "1.0.0"
M02_NON_SEMANTIC_DIAGNOSTIC_POLICY = (
    "M01_CACHE_TILE_QUERY_MATERIALIZATION_AND_RUNTIME_SCHEDULING_EXCLUDED"
)


class ReplayDecisionKind(StrEnum):
    """Canonical stages required by frozen M02 section 13."""

    TARGET = "TARGET"
    ACCEPTED_PARENT = "ACCEPTED_PARENT"
    TRIAL_STEP = "TRIAL_STEP"
    STEP_SIZE = "STEP_SIZE"
    PREDICTOR = "PREDICTOR"
    NONLINEAR_ITERATION = "NONLINEAR_ITERATION"
    LINEAR_SOLVE = "LINEAR_SOLVE"
    LINE_SEARCH = "LINE_SEARCH"
    RESIDUAL_QUALITY = "RESIDUAL_QUALITY"
    EVENT_REGISTRATION = "EVENT_REGISTRATION"
    EVENT_APPLICABILITY = "EVENT_APPLICABILITY"
    EVENT_PROBE = "EVENT_PROBE"
    B_PROBE_BALANCE = "B_PROBE_BALANCE"
    EVENT_BRACKET = "EVENT_BRACKET"
    EVENT_ROOT = "EVENT_ROOT"
    EVENT_EARLIESTNESS = "EVENT_EARLIESTNESS"
    SIMULTANEOUS_GROUP = "SIMULTANEOUS_GROUP"
    EVENT_DEPENDENCY = "EVENT_DEPENDENCY"
    CASCADE_ROUND = "CASCADE_ROUND"
    OWNER_RESPONSE = "OWNER_RESPONSE"
    INTENT_BATCH = "INTENT_BATCH"
    ROLLBACK = "ROLLBACK"
    PREPARE = "PREPARE"
    COMMIT = "COMMIT"
    ACCEPTED_STEP = "ACCEPTED_STEP"
    FAILURE = "FAILURE"


_DECISION_STAGE_RANK = {kind.value: index for index, kind in enumerate(ReplayDecisionKind)}

_SET_LIKE_PAYLOAD_FIELDS = frozenset(
    {
        "applicable_event_ids",
        "event_set",
        "owner_ids",
        "physical_owner_ids",
        "read_set",
        "simultaneous_event_ids",
        "stream_namespaces",
        "write_set",
    }
)

_NON_SEMANTIC_DIAGNOSTIC_KEYS = frozenset(
    {
        "case_execution_order",
        "case_order",
        "cache_hit",
        "cache_miss",
        "cache_status",
        "elapsed_ns",
        "execution_order",
        "m01_cache_hit",
        "m01_cache_miss",
        "m01_cache_status",
        "m01_materialization_order",
        "m01_materialization_receipt_id",
        "m01_query_order",
        "m01_tile_order",
        "materialization_receipt_id",
        "materialization_request_order",
        "owner_call_order",
        "peak_rss_bytes",
        "runtime_thread_count",
        "thread_count",
        "thread_assignment",
        "thread_id",
        "wall_time_s",
        "worker_id",
        "worker_index",
        "query_order",
        "tile_materialization_order",
        "tile_query_order",
    }
)


def _is_non_semantic_diagnostic(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_").replace(".", "_")
    if normalized in _NON_SEMANTIC_DIAGNOSTIC_KEYS:
        return True
    return normalized.startswith(
        (
            "m01_cache_",
            "m01_materialization_",
            "m01_query_order_",
            "m01_tile_order_",
            "runtime_worker_",
            "scheduler_",
            "thread_assignment_",
        )
    )


def _nonempty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{name} must be a nonempty string")


def _hash(value: str, name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ContractViolation(f"{name} must be a lowercase SHA-256 hex digest")


def _kind_value(kind: ReplayDecisionKind | str) -> str:
    value = kind.value if isinstance(kind, ReplayDecisionKind) else kind
    _nonempty(value, "decision_kind")
    return value


def _normalize_payload_value(key: str, value: Any) -> str:
    if (
        key in _SET_LIKE_PAYLOAD_FIELDS
        and isinstance(value, Sequence)
        and not isinstance(value, str | bytes | bytearray)
    ):
        value = sorted(value, key=canonical_json_bytes)
    return canonical_json_bytes(value).decode("utf-8")


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplayDecisionDraft:
    """Unordered ingestion value used to construct a canonical decision chain."""

    case_id: str
    target_id: str
    decision_kind: ReplayDecisionKind | str
    logical_step_index: int
    input_hash: str
    output_hash: str
    backend_profile_hash: str
    trial_id: str | None = None
    dependency_rank: int = 0
    owner_id: str = ""
    payload: Mapping[str, Any] = field(default_factory=dict)
    diagnostics: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _nonempty(self.case_id, "case_id")
        _nonempty(self.target_id, "target_id")
        _kind_value(self.decision_kind)
        if self.trial_id is not None:
            _nonempty(self.trial_id, "trial_id")
        if (
            isinstance(self.logical_step_index, bool)
            or not isinstance(self.logical_step_index, int)
            or self.logical_step_index < 0
        ):
            raise ContractViolation("logical_step_index must be a nonnegative integer")
        if (
            isinstance(self.dependency_rank, bool)
            or not isinstance(self.dependency_rank, int)
            or self.dependency_rank < 0
        ):
            raise ContractViolation("dependency_rank must be a nonnegative integer")
        _hash(self.input_hash, "input_hash")
        _hash(self.output_hash, "output_hash")
        _hash(self.backend_profile_hash, "backend_profile_hash")
        reserved = {"logical_step_index", "dependency_rank", "owner_id"}
        collision = reserved & set(self.payload)
        if collision:
            raise ContractViolation(
                "replay payload uses builder-owned keys",
                details={"keys": sorted(collision)},
            )
        for name, values in (("payload", self.payload), ("diagnostics", self.diagnostics)):
            for key, value in values.items():
                _nonempty(key, f"{name} key")
                canonical_json_bytes(value)


def _draft_payload_and_diagnostics(
    draft: ReplayDecisionDraft,
) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    payload_values = dict(draft.payload)
    diagnostic_values = dict(draft.diagnostics)
    for key in tuple(payload_values):
        if _is_non_semantic_diagnostic(key):
            diagnostic_values[key] = payload_values.pop(key)
    payload_values["logical_step_index"] = draft.logical_step_index
    payload_values["dependency_rank"] = draft.dependency_rank
    if draft.owner_id:
        payload_values["owner_id"] = draft.owner_id
    payload = tuple(
        (key, _normalize_payload_value(key, value)) for key, value in sorted(payload_values.items())
    )
    diagnostics = tuple(
        (key, canonical_json_bytes(value).decode("utf-8"))
        for key, value in sorted(diagnostic_values.items())
    )
    return payload, diagnostics


def _draft_sort_key(draft: ReplayDecisionDraft) -> tuple[Any, ...]:
    payload, _ = _draft_payload_and_diagnostics(draft)
    kind = _kind_value(draft.decision_kind)
    return (
        draft.case_id,
        draft.logical_step_index,
        draft.dependency_rank,
        _DECISION_STAGE_RANK.get(kind, len(_DECISION_STAGE_RANK)),
        draft.owner_id,
        kind,
        draft.target_id,
        draft.trial_id or "",
        semantic_hash(payload),
        draft.input_hash,
        draft.output_hash,
    )


@dataclass(frozen=True, slots=True)
class M02ReplayDecisionChain:
    """Validated, canonical per-case chain of frozen M02 replay records."""

    records: tuple[ReplayDecisionRecord, ...]
    diagnostics: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = ()
    canonical_order_policy: str = M02_CANONICAL_ORDER_POLICY
    canonical_reduction_order: str = M02_CANONICAL_REDUCTION_ORDER
    thread_policy: str = M02_THREAD_POLICY

    def __post_init__(self) -> None:
        if self.canonical_order_policy != M02_CANONICAL_ORDER_POLICY:
            raise ContractViolation("unsupported M02 canonical decision-order policy")
        if not self.canonical_reduction_order.strip() or not self.thread_policy.strip():
            raise ContractViolation("canonical reduction and thread policy must be explicit")
        record_ids = [record.decision_id for record in self.records]
        if len(record_ids) != len(set(record_ids)):
            raise ContractViolation("M02 replay decision IDs must be unique")
        diagnostic_ids = [decision_id for decision_id, _ in self.diagnostics]
        if len(diagnostic_ids) != len(set(diagnostic_ids)):
            raise ContractViolation("M02 replay diagnostics must have unique decision IDs")
        if not set(diagnostic_ids) <= set(record_ids):
            raise ContractViolation("M02 replay diagnostics reference an unknown decision")

        previous_case = ""
        expected_index: dict[str, int] = {}
        previous_hash: dict[str, str] = {}
        for record in self.records:
            if previous_case and record.case_id < previous_case:
                raise ContractViolation("M02 replay records are not in canonical case order")
            expected = expected_index.get(record.case_id, 0)
            if record.sequence_index != expected:
                raise ContractViolation("M02 replay sequence indexes must be contiguous per case")
            expected_parent = previous_hash.get(record.case_id)
            if record.parent_decision_hash != expected_parent:
                raise ContractViolation("M02 replay parent-decision chain is inconsistent")
            previous_case = record.case_id
            expected_index[record.case_id] = expected + 1
            previous_hash[record.case_id] = record.metadata.semantic_hash
        if tuple(_record_sort_key(record) for record in self.records) != tuple(
            sorted(_record_sort_key(record) for record in self.records)
        ):
            raise ContractViolation(
                "M02 replay records violate the canonical decision-order policy"
            )

    @classmethod
    def from_drafts(
        cls,
        drafts: Sequence[ReplayDecisionDraft],
        *,
        diagnostic_level: DiagnosticLevel = DiagnosticLevel.STANDARD,
        canonical_reduction_order: str = M02_CANONICAL_REDUCTION_ORDER,
        thread_policy: str = M02_THREAD_POLICY,
    ) -> M02ReplayDecisionChain:
        ordered = sorted(drafts, key=_draft_sort_key)
        records: list[ReplayDecisionRecord] = []
        diagnostics: list[tuple[str, tuple[tuple[str, str], ...]]] = []
        case_indexes: dict[str, int] = {}
        parent_hashes: dict[str, str] = {}
        for draft in ordered:
            payload, diagnostic_payload = _draft_payload_and_diagnostics(draft)
            kind = _kind_value(draft.decision_kind)
            sequence_index = case_indexes.get(draft.case_id, 0)
            identity = {
                "case_id": draft.case_id,
                "target_id": draft.target_id,
                "trial_id": draft.trial_id,
                "sequence_index": sequence_index,
                "decision_kind": kind,
                "input_hash": draft.input_hash,
                "output_hash": draft.output_hash,
                "payload": payload,
                "backend_profile_hash": draft.backend_profile_hash,
            }
            decision_id = stable_content_id("m02_replay_decision", identity)
            record = ReplayDecisionRecord.create(
                decision_id=decision_id,
                case_id=draft.case_id,
                target_id=draft.target_id,
                trial_id=draft.trial_id,
                sequence_index=sequence_index,
                decision_kind=kind,
                input_hash=draft.input_hash,
                output_hash=draft.output_hash,
                parent_decision_hash=parent_hashes.get(draft.case_id),
                payload=payload,
                backend_profile_hash=draft.backend_profile_hash,
                diagnostic_level=diagnostic_level,
                metadata_unit="1",
            )
            records.append(record)
            if diagnostic_payload:
                diagnostics.append((decision_id, diagnostic_payload))
            case_indexes[draft.case_id] = sequence_index + 1
            parent_hashes[draft.case_id] = record.metadata.semantic_hash
        return cls(
            tuple(records),
            tuple(diagnostics),
            canonical_reduction_order=canonical_reduction_order,
            thread_policy=thread_policy,
        )

    @property
    def case_ids(self) -> tuple[str, ...]:
        return tuple(sorted({record.case_id for record in self.records}))

    @property
    def bitwise_hash(self) -> str:
        return semantic_hash(
            {
                "schema_version": M02_REPLAY_SCHEMA_VERSION,
                "records": [dataclasses.asdict(record) for record in self.records],
                "canonical_order_policy": self.canonical_order_policy,
                "canonical_reduction_order": self.canonical_reduction_order,
                "thread_policy": self.thread_policy,
            }
        )

    @property
    def semantic_hash(self) -> str:
        return semantic_hash(
            {
                "schema_version": M02_REPLAY_SCHEMA_VERSION,
                "records": [_semantic_record_payload(record) for record in self.records],
                "canonical_order_policy": self.canonical_order_policy,
                "canonical_reduction_order": self.canonical_reduction_order,
                "thread_policy": self.thread_policy,
            }
        )

    @property
    def case_bitwise_hashes(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (case_id, semantic_hash([dataclasses.asdict(item) for item in self.for_case(case_id)]))
            for case_id in self.case_ids
        )

    @property
    def case_semantic_hashes(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (
                case_id,
                semantic_hash([_semantic_record_payload(item) for item in self.for_case(case_id)]),
            )
            for case_id in self.case_ids
        )

    def for_case(self, case_id: str) -> tuple[ReplayDecisionRecord, ...]:
        return tuple(record for record in self.records if record.case_id == case_id)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": M02_REPLAY_SCHEMA_VERSION,
            "records": [dataclasses.asdict(record) for record in self.records],
            "diagnostics": {key: dict(value) for key, value in self.diagnostics},
            "canonical_order_policy": self.canonical_order_policy,
            "canonical_reduction_order": self.canonical_reduction_order,
            "thread_policy": self.thread_policy,
            "bitwise_hash": self.bitwise_hash,
            "semantic_hash": self.semantic_hash,
            "case_bitwise_hashes": dict(self.case_bitwise_hashes),
            "case_semantic_hashes": dict(self.case_semantic_hashes),
        }


def _semantic_record_payload(record: ReplayDecisionRecord) -> dict[str, Any]:
    return {
        "case_id": record.case_id,
        "target_id": record.target_id,
        "trial_id": record.trial_id,
        "sequence_index": record.sequence_index,
        "decision_kind": record.decision_kind,
        "payload": record.payload,
        "backend_profile_hash": record.backend_profile_hash,
    }


def _record_sort_key(record: ReplayDecisionRecord) -> tuple[Any, ...]:
    payload = dict(record.payload)
    logical_step_index = json.loads(payload.get("logical_step_index", "0"))
    dependency_rank = json.loads(payload.get("dependency_rank", "0"))
    owner_id = json.loads(payload.get("owner_id", '""'))
    return (
        record.case_id,
        logical_step_index,
        dependency_rank,
        _DECISION_STAGE_RANK.get(record.decision_kind, len(_DECISION_STAGE_RANK)),
        owner_id,
        record.decision_kind,
        record.target_id,
        record.trial_id or "",
        semantic_hash(record.payload),
        record.input_hash,
        record.output_hash,
    )


def build_replay_decision_chain(
    drafts: Sequence[ReplayDecisionDraft],
    *,
    diagnostic_level: DiagnosticLevel = DiagnosticLevel.STANDARD,
    canonical_reduction_order: str = M02_CANONICAL_REDUCTION_ORDER,
    thread_policy: str = M02_THREAD_POLICY,
) -> M02ReplayDecisionChain:
    """Public functional constructor for a canonical M02 decision chain."""

    return M02ReplayDecisionChain.from_drafts(
        drafts,
        diagnostic_level=diagnostic_level,
        canonical_reduction_order=canonical_reduction_order,
        thread_policy=thread_policy,
    )


@dataclass(frozen=True, slots=True)
class M02ReplayManifestExtension:
    """Additive M02 fields embedded alongside every M00 ReplayManifest field."""

    schema_version: str
    decision_chain_bitwise_hash: str
    decision_chain_semantic_hash: str
    decision_count: int
    case_ids: tuple[str, ...]
    case_bitwise_hashes: tuple[tuple[str, str], ...]
    case_semantic_hashes: tuple[tuple[str, str], ...]
    resolved_numerics_config_hash: str
    owner_contract_hashes: tuple[tuple[str, str], ...]
    numerical_backend: str
    backend_profile_hash: str
    canonical_order_policy: str
    canonical_reduction_order: str
    thread_policy: str
    floating_point_profile: str
    field_tolerance_profile_id: str
    field_tolerance_profile_version: str
    diagnostic_level: DiagnosticLevel
    non_semantic_diagnostic_policy: str

    def __post_init__(self) -> None:
        if self.schema_version != M02_REPLAY_SCHEMA_VERSION:
            raise ContractViolation("unsupported M02 replay manifest schema version")
        for name in (
            "decision_chain_bitwise_hash",
            "decision_chain_semantic_hash",
            "resolved_numerics_config_hash",
            "backend_profile_hash",
        ):
            _hash(getattr(self, name), name)
        if isinstance(self.decision_count, bool) or self.decision_count < 0:
            raise ContractViolation("decision_count must be a nonnegative integer")
        if tuple(sorted(self.case_ids)) != self.case_ids or len(set(self.case_ids)) != len(
            self.case_ids
        ):
            raise ContractViolation("M02 replay case IDs must be unique and sorted")
        owner_ids = tuple(key for key, _ in self.owner_contract_hashes)
        if tuple(sorted(owner_ids)) != owner_ids or len(set(owner_ids)) != len(owner_ids):
            raise ContractViolation("owner contract hashes must have unique sorted owner IDs")
        for owner_id, owner_hash in self.owner_contract_hashes:
            _nonempty(owner_id, "owner_id")
            _hash(owner_hash, f"owner_contract_hashes[{owner_id}]")
        for collection_name, values in (
            ("case_bitwise_hashes", self.case_bitwise_hashes),
            ("case_semantic_hashes", self.case_semantic_hashes),
        ):
            if tuple(key for key, _ in values) != self.case_ids:
                raise ContractViolation(f"{collection_name} must cover the canonical case IDs")
            for case_id, digest in values:
                _hash(digest, f"{collection_name}[{case_id}]")
        for name in (
            "numerical_backend",
            "canonical_order_policy",
            "canonical_reduction_order",
            "thread_policy",
            "floating_point_profile",
            "field_tolerance_profile_id",
            "field_tolerance_profile_version",
            "non_semantic_diagnostic_policy",
        ):
            _nonempty(getattr(self, name), name)
        if not isinstance(self.diagnostic_level, DiagnosticLevel):
            raise ContractViolation("M02 replay diagnostic level must use DiagnosticLevel")

    @property
    def extension_id(self) -> str:
        return stable_content_id("m02_replay_extension", dataclasses.asdict(self))

    def as_dict(self) -> dict[str, Any]:
        value = dataclasses.asdict(self)
        value["extension_id"] = self.extension_id
        return value


@dataclass(frozen=True, slots=True)
class M02ReplayManifest:
    """Composition-based extension that preserves the complete public M00 schema."""

    base_manifest: ReplayManifest
    m02_extension: M02ReplayManifestExtension

    @property
    def replay_manifest_id(self) -> str:
        return stable_content_id(
            "m02_replay_manifest",
            {
                "base_replay_manifest_id": self.base_manifest.replay_manifest_id,
                "extension_id": self.m02_extension.extension_id,
            },
        )

    @property
    def base_replay_manifest_id(self) -> str:
        return self.base_manifest.replay_manifest_id

    def as_dict(self) -> dict[str, Any]:
        output = self.base_manifest.as_dict()
        output["m02_replay_manifest_id"] = self.replay_manifest_id
        output["m02_extension"] = self.m02_extension.as_dict()
        return output


def make_m02_replay_manifest(
    base_manifest: ReplayManifest,
    decision_chain: M02ReplayDecisionChain,
    *,
    resolved_numerics_config_hash: str,
    owner_contract_hashes: Mapping[str, str],
    backend_profile_hash: str | None = None,
    numerical_backend: str | None = None,
    canonical_reduction_order: str | None = None,
    thread_policy: str | None = None,
    floating_point_profile: str = M02_FLOATING_POINT_PROFILE,
    field_tolerance_profile_id: str = M02_FIELD_TOLERANCE_PROFILE_ID,
    field_tolerance_profile_version: str = M02_FIELD_TOLERANCE_PROFILE_VERSION,
    diagnostic_level: DiagnosticLevel = DiagnosticLevel.STANDARD,
) -> M02ReplayManifest:
    """Extend an existing M00 manifest without duplicating or changing its schema."""

    _hash(resolved_numerics_config_hash, "resolved_numerics_config_hash")
    for field_id, tolerance in base_manifest.field_tolerances.items():
        _nonempty(field_id, "field tolerance ID")
        if not math.isfinite(tolerance) or tolerance < 0.0:
            raise ContractViolation("replay field tolerances must be finite and nonnegative")
    backend = numerical_backend or base_manifest.numerical_backend
    reduction = canonical_reduction_order or decision_chain.canonical_reduction_order
    threads = thread_policy or decision_chain.thread_policy
    if reduction != decision_chain.canonical_reduction_order:
        raise ContractViolation("manifest and decision-chain canonical reduction order disagree")
    if threads != decision_chain.thread_policy:
        raise ContractViolation("manifest and decision-chain thread policy disagree")
    profile_hash = backend_profile_hash or semantic_hash(
        {
            "numerical_backend": backend,
            "canonical_reduction_order": reduction,
            "thread_policy": threads,
            "floating_point_profile": floating_point_profile,
        }
    )
    _hash(profile_hash, "backend_profile_hash")
    record_profiles = {record.backend_profile_hash for record in decision_chain.records}
    if record_profiles and record_profiles != {profile_hash}:
        raise ContractViolation(
            "decision records and replay manifest use different backend profiles"
        )
    owners = tuple(sorted(owner_contract_hashes.items()))
    extension = M02ReplayManifestExtension(
        schema_version=M02_REPLAY_SCHEMA_VERSION,
        decision_chain_bitwise_hash=decision_chain.bitwise_hash,
        decision_chain_semantic_hash=decision_chain.semantic_hash,
        decision_count=len(decision_chain.records),
        case_ids=decision_chain.case_ids,
        case_bitwise_hashes=decision_chain.case_bitwise_hashes,
        case_semantic_hashes=decision_chain.case_semantic_hashes,
        resolved_numerics_config_hash=resolved_numerics_config_hash,
        owner_contract_hashes=owners,
        numerical_backend=backend,
        backend_profile_hash=profile_hash,
        canonical_order_policy=decision_chain.canonical_order_policy,
        canonical_reduction_order=reduction,
        thread_policy=threads,
        floating_point_profile=floating_point_profile,
        field_tolerance_profile_id=field_tolerance_profile_id,
        field_tolerance_profile_version=field_tolerance_profile_version,
        diagnostic_level=diagnostic_level,
        non_semantic_diagnostic_policy=M02_NON_SEMANTIC_DIAGNOSTIC_POLICY,
    )
    return M02ReplayManifest(base_manifest, extension)


@dataclass(frozen=True, slots=True)
class M02ReplayVerificationReport:
    """Structured, field-level BITWISE or SEMANTIC M02 replay comparison."""

    mode: ReplayMode
    expected_manifest_id: str
    observed_manifest_id: str
    expected_chain_hash: str
    observed_chain_hash: str
    compared_cases: int
    compared_decisions: int
    differences: tuple[ReplayDifference, ...]
    ignored_differences: tuple[ReplayDifference, ...]
    canonical_order_policy: str
    thread_policy: str

    @property
    def equivalent(self) -> bool:
        return not self.differences

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "equivalent": self.equivalent,
            "expected_manifest_id": self.expected_manifest_id,
            "observed_manifest_id": self.observed_manifest_id,
            "expected_chain_hash": self.expected_chain_hash,
            "observed_chain_hash": self.observed_chain_hash,
            "compared_cases": self.compared_cases,
            "compared_decisions": self.compared_decisions,
            "differences": [dataclasses.asdict(item) for item in self.differences],
            "ignored_differences": [dataclasses.asdict(item) for item in self.ignored_differences],
            "canonical_order_policy": self.canonical_order_policy,
            "thread_policy": self.thread_policy,
        }


def _difference(
    code: str,
    scope: str,
    left: Any,
    right: Any,
    explanation: str,
    tolerance: float | None = None,
) -> ReplayDifference:
    return ReplayDifference(code, scope, left, right, tolerance, explanation)


_SEMANTIC_BASE_IGNORED_FIELDS = frozenset(
    {
        "replay_manifest_id",
        "run_id",
        "semantic_input_hashes",
        "python_runtime",
        "os_architecture",
        "dependency_versions",
        "diagnostic_level",
    }
)


def _semantic_thread_settings(value: Mapping[str, Any]) -> dict[str, Any]:
    ignored_tokens = ("count", "worker", "assignment", "executor", "omp_", "mkl_")
    return {
        key: item
        for key, item in value.items()
        if not any(token in key.lower() for token in ignored_tokens)
    }


def _compare_manifest_fields(
    expected: M02ReplayManifest,
    observed: M02ReplayManifest,
    mode: ReplayMode,
    differences: list[ReplayDifference],
    ignored: list[ReplayDifference],
) -> None:
    for item in dataclasses.fields(ReplayManifest):
        name = item.name
        left = getattr(expected.base_manifest, name)
        right = getattr(observed.base_manifest, name)
        scope = f"manifest.{name}"
        if mode is ReplayMode.BITWISE_REPLAY:
            if left != right:
                differences.append(
                    _difference(
                        "MANIFEST_FIELD_MISMATCH",
                        scope,
                        left,
                        right,
                        "bitwise replay requires the M00 manifest field to match exactly",
                    )
                )
            continue
        if name in _SEMANTIC_BASE_IGNORED_FIELDS:
            if left != right:
                ignored.append(
                    _difference(
                        "COMPATIBLE_PLATFORM_OR_DIAGNOSTIC_DIFFERENCE",
                        scope,
                        left,
                        right,
                        "field is intentionally outside cross-platform semantic equivalence",
                    )
                )
            continue
        if name in {"case_execution_plan", "idempotency_keys", "surface_identities"}:
            original_left, original_right = left, right
            left, right = tuple(sorted(left)), tuple(sorted(right))
            if left == right and original_left != original_right:
                ignored.append(
                    _difference(
                        "CANONICAL_EXECUTION_ORDER_DIFFERENCE",
                        scope,
                        original_left,
                        original_right,
                        "execution order is normalized before per-case semantic replay",
                    )
                )
        elif name == "thread_and_float_settings":
            original_left, original_right = left, right
            left = _semantic_thread_settings(left)
            right = _semantic_thread_settings(right)
            if left == right and original_left != original_right:
                ignored.append(
                    _difference(
                        "RUNTIME_THREAD_SCHEDULING_DIFFERENCE",
                        scope,
                        original_left,
                        original_right,
                        "runtime worker count/assignment is outside per-case semantic identity",
                    )
                )
        if left != right:
            differences.append(
                _difference(
                    "MANIFEST_FIELD_MISMATCH",
                    scope,
                    left,
                    right,
                    "semantic replay requires this canonical M00 field to match",
                )
            )

    ignored_extension_fields = {
        "decision_chain_bitwise_hash",
        "decision_chain_semantic_hash",
        "case_bitwise_hashes",
        "case_semantic_hashes",
        "diagnostic_level",
    }
    for item in dataclasses.fields(M02ReplayManifestExtension):
        name = item.name
        left = getattr(expected.m02_extension, name)
        right = getattr(observed.m02_extension, name)
        scope = f"manifest.m02_extension.{name}"
        if mode is ReplayMode.SEMANTIC_REPLAY and name in ignored_extension_fields:
            if name == "diagnostic_level" and left != right:
                ignored.append(
                    _difference(
                        "NON_SEMANTIC_DIAGNOSTIC_DIFFERENCE",
                        scope,
                        left,
                        right,
                        "diagnostic retention cannot change numerical semantic replay",
                    )
                )
            continue
        if left != right:
            differences.append(
                _difference(
                    "MANIFEST_FIELD_MISMATCH",
                    scope,
                    left,
                    right,
                    "replay manifest extension field differs",
                )
            )


def _records_by_key(
    chain: M02ReplayDecisionChain,
) -> dict[tuple[str, int], ReplayDecisionRecord]:
    return {(record.case_id, record.sequence_index): record for record in chain.records}


def _compare_bitwise_record(
    left: ReplayDecisionRecord,
    right: ReplayDecisionRecord,
    scope: str,
    differences: list[ReplayDifference],
) -> None:
    fields = (
        "decision_id",
        "case_id",
        "target_id",
        "trial_id",
        "sequence_index",
        "decision_kind",
        "input_hash",
        "output_hash",
        "parent_decision_hash",
        "backend_profile_hash",
        "diagnostic_level",
    )
    for name in fields:
        left_value = getattr(left, name)
        right_value = getattr(right, name)
        if left_value != right_value:
            differences.append(
                _difference(
                    "DECISION_FIELD_MISMATCH",
                    f"{scope}.{name}",
                    left_value,
                    right_value,
                    "bitwise replay requires the decision field to match exactly",
                )
            )
    left_payload, right_payload = dict(left.payload), dict(right.payload)
    for key in sorted(set(left_payload) | set(right_payload)):
        if left_payload.get(key) != right_payload.get(key):
            differences.append(
                _difference(
                    "DECISION_PAYLOAD_MISMATCH",
                    f"{scope}.payload.{key}",
                    left_payload.get(key),
                    right_payload.get(key),
                    "bitwise replay requires canonical payload bytes to match",
                )
            )
    for metadata_field in dataclasses.fields(type(left.metadata)):
        name = metadata_field.name
        left_value = getattr(left.metadata, name)
        right_value = getattr(right.metadata, name)
        if left_value != right_value:
            differences.append(
                _difference(
                    "DECISION_IDENTITY_MISMATCH",
                    f"{scope}.metadata.{name}",
                    left_value,
                    right_value,
                    "bitwise replay requires identical decision semantic identity",
                )
            )


def _field_tolerance(
    tolerances: Mapping[str, float],
    case_id: str,
    decision_kind: str,
    payload_path: str,
) -> float:
    root = payload_path.split(".", 1)[0].split("[", 1)[0]
    candidates = (
        f"{case_id}.{decision_kind}.{payload_path}",
        f"{decision_kind}.{payload_path}",
        payload_path,
        f"{decision_kind}.{root}",
        root,
        "*",
    )
    for candidate in candidates:
        if candidate in tolerances:
            tolerance = tolerances[candidate]
            if not math.isfinite(tolerance) or tolerance < 0.0:
                raise ContractViolation("replay field tolerances must be finite and nonnegative")
            return tolerance
    return 0.0


def _compare_semantic_value(
    left: Any,
    right: Any,
    *,
    scope: str,
    payload_path: str,
    case_id: str,
    decision_kind: str,
    tolerances: Mapping[str, float],
    differences: list[ReplayDifference],
) -> None:
    if (
        isinstance(left, int | float)
        and not isinstance(left, bool)
        and isinstance(right, int | float)
        and not isinstance(right, bool)
    ):
        tolerance = _field_tolerance(tolerances, case_id, decision_kind, payload_path)
        if not math.isclose(float(left), float(right), abs_tol=tolerance, rel_tol=tolerance):
            differences.append(
                _difference(
                    "NUMERIC_FIELD_OUTSIDE_TOLERANCE",
                    scope,
                    left,
                    right,
                    "numeric replay value differs outside its versioned field tolerance",
                    tolerance,
                )
            )
        return
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            child_scope = f"{scope}.{key}"
            child_path = f"{payload_path}.{key}"
            if key not in left or key not in right:
                differences.append(
                    _difference(
                        "DECISION_PAYLOAD_FIELD_PRESENCE_MISMATCH",
                        child_scope,
                        left.get(key),
                        right.get(key),
                        "semantic replay payload structure differs",
                    )
                )
            else:
                _compare_semantic_value(
                    left[key],
                    right[key],
                    scope=child_scope,
                    payload_path=child_path,
                    case_id=case_id,
                    decision_kind=decision_kind,
                    tolerances=tolerances,
                    differences=differences,
                )
        return
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            differences.append(
                _difference(
                    "DECISION_PAYLOAD_LENGTH_MISMATCH",
                    scope,
                    len(left),
                    len(right),
                    "semantic replay ordered payload length differs",
                )
            )
            return
        for index, (left_item, right_item) in enumerate(zip(left, right, strict=True)):
            _compare_semantic_value(
                left_item,
                right_item,
                scope=f"{scope}[{index}]",
                payload_path=f"{payload_path}[{index}]",
                case_id=case_id,
                decision_kind=decision_kind,
                tolerances=tolerances,
                differences=differences,
            )
        return
    if left != right:
        differences.append(
            _difference(
                "DECISION_PAYLOAD_MISMATCH",
                scope,
                left,
                right,
                "semantic branch/state/event/receipt payload differs",
            )
        )


def _compare_semantic_record(
    left: ReplayDecisionRecord,
    right: ReplayDecisionRecord,
    scope: str,
    tolerances: Mapping[str, float],
    differences: list[ReplayDifference],
) -> None:
    for name in (
        "case_id",
        "target_id",
        "trial_id",
        "sequence_index",
        "decision_kind",
        "backend_profile_hash",
    ):
        left_value = getattr(left, name)
        right_value = getattr(right, name)
        if left_value != right_value:
            differences.append(
                _difference(
                    "DECISION_FIELD_MISMATCH",
                    f"{scope}.{name}",
                    left_value,
                    right_value,
                    "semantic replay decision structure differs",
                )
            )
    if left.input_hash != right.input_hash:
        differences.append(
            _difference(
                "DECISION_INPUT_HASH_MISMATCH",
                f"{scope}.input_hash",
                left.input_hash,
                right.input_hash,
                "semantic replay requires the canonical decision input/context hash to match",
            )
        )
    left_payload, right_payload = dict(left.payload), dict(right.payload)
    payload_changed = left_payload != right_payload
    for key in sorted(set(left_payload) | set(right_payload)):
        payload_scope = f"{scope}.payload.{key}"
        if key not in left_payload or key not in right_payload:
            differences.append(
                _difference(
                    "DECISION_PAYLOAD_FIELD_PRESENCE_MISMATCH",
                    payload_scope,
                    left_payload.get(key),
                    right_payload.get(key),
                    "semantic replay payload field is present on only one side",
                )
            )
            continue
        _compare_semantic_value(
            json.loads(left_payload[key]),
            json.loads(right_payload[key]),
            scope=payload_scope,
            payload_path=key,
            case_id=left.case_id,
            decision_kind=left.decision_kind,
            tolerances=tolerances,
            differences=differences,
        )
    if left.output_hash != right.output_hash and not payload_changed:
        differences.append(
            _difference(
                "UNEXPLAINED_DECISION_OUTPUT_HASH_MISMATCH",
                f"{scope}.output_hash",
                left.output_hash,
                right.output_hash,
                "output identity changed without a field-level numeric difference to compare",
            )
        )


def _compare_diagnostics(
    expected: M02ReplayDecisionChain,
    observed: M02ReplayDecisionChain,
) -> list[ReplayDifference]:
    left = {key: dict(value) for key, value in expected.diagnostics}
    right = {key: dict(value) for key, value in observed.diagnostics}
    output: list[ReplayDifference] = []
    for decision_id in sorted(set(left) | set(right)):
        left_values, right_values = left.get(decision_id, {}), right.get(decision_id, {})
        for key in sorted(set(left_values) | set(right_values)):
            if left_values.get(key) != right_values.get(key):
                output.append(
                    _difference(
                        "NON_SEMANTIC_DIAGNOSTIC_DIFFERENCE",
                        f"diagnostics.{decision_id}.{key}",
                        left_values.get(key),
                        right_values.get(key),
                        "cache/materialization/runtime observation is excluded from replay identity",
                    )
                )
    return output


def verify_m02_replay(
    expected_manifest: M02ReplayManifest,
    expected_chain: M02ReplayDecisionChain,
    observed_manifest: M02ReplayManifest,
    observed_chain: M02ReplayDecisionChain,
    *,
    mode: ReplayMode,
    field_tolerances: Mapping[str, float] | None = None,
) -> M02ReplayVerificationReport:
    """Compare two M02 replays and return all structured field differences."""

    if not isinstance(mode, ReplayMode):
        raise ContractViolation("M02 replay mode must use the public M00 ReplayMode")
    differences: list[ReplayDifference] = []
    ignored: list[ReplayDifference] = []
    _compare_manifest_fields(expected_manifest, observed_manifest, mode, differences, ignored)

    left_records, right_records = _records_by_key(expected_chain), _records_by_key(observed_chain)
    compared_keys = sorted(set(left_records) & set(right_records))
    for key in sorted(set(left_records) | set(right_records)):
        scope = f"decisions.{key[0]}[{key[1]}]"
        left, right = left_records.get(key), right_records.get(key)
        if left is None or right is None:
            differences.append(
                _difference(
                    "DECISION_PRESENCE_MISMATCH",
                    scope,
                    left is not None,
                    right is not None,
                    "canonical decision is present on only one side",
                )
            )
            continue
        if mode is ReplayMode.BITWISE_REPLAY:
            _compare_bitwise_record(left, right, scope, differences)
        else:
            tolerances = dict(expected_manifest.base_manifest.field_tolerances)
            if field_tolerances:
                tolerances.update(field_tolerances)
            _compare_semantic_record(left, right, scope, tolerances, differences)
    ignored.extend(_compare_diagnostics(expected_chain, observed_chain))

    expected_hash = (
        expected_chain.bitwise_hash
        if mode is ReplayMode.BITWISE_REPLAY
        else expected_chain.semantic_hash
    )
    observed_hash = (
        observed_chain.bitwise_hash
        if mode is ReplayMode.BITWISE_REPLAY
        else observed_chain.semantic_hash
    )
    compared_cases = len({key[0] for key in compared_keys})
    return M02ReplayVerificationReport(
        mode=mode,
        expected_manifest_id=expected_manifest.replay_manifest_id,
        observed_manifest_id=observed_manifest.replay_manifest_id,
        expected_chain_hash=expected_hash,
        observed_chain_hash=observed_hash,
        compared_cases=compared_cases,
        compared_decisions=len(compared_keys),
        differences=tuple(differences),
        ignored_differences=tuple(ignored),
        canonical_order_policy=expected_chain.canonical_order_policy,
        thread_policy=expected_chain.thread_policy,
    )


compare_m02_replay = verify_m02_replay


__all__ = [
    "M02_CANONICAL_ORDER_POLICY",
    "M02_CANONICAL_REDUCTION_ORDER",
    "M02_FIELD_TOLERANCE_PROFILE_ID",
    "M02_FIELD_TOLERANCE_PROFILE_VERSION",
    "M02_FLOATING_POINT_PROFILE",
    "M02_NON_SEMANTIC_DIAGNOSTIC_POLICY",
    "M02_REPLAY_SCHEMA_VERSION",
    "M02_THREAD_POLICY",
    "M02ReplayDecisionChain",
    "M02ReplayManifest",
    "M02ReplayManifestExtension",
    "M02ReplayVerificationReport",
    "ReplayDecisionDraft",
    "ReplayDecisionKind",
    "ReplayMode",
    "build_replay_decision_chain",
    "compare_m02_replay",
    "make_m02_replay_manifest",
    "verify_m02_replay",
]
