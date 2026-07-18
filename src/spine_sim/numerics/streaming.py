"""Bounded-memory streaming fixtures for the frozen M02 campaign contract.

This module is a VALIDATION_ONLY load-interface fixture.  It deliberately does
not schedule work, rank designs, or implement A/B physics.  A cheap deterministic
owner is used to prove that the frozen 64/256/256 and 4000/16000 case plans can
be generated lazily, paused, resumed, replayed, and merged.  Optional diagnostic
evidence is persisted through the public M00 ``ResultWriter``/``ResultReader``
boundary in bounded transaction batches.
"""

from __future__ import annotations

import json
import os
import platform
import resource
import sys
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from spine_sim.foundation import (
    ResultReader,
    ResultWriter,
    SchemaRegistry,
    VerifyMode,
    semantic_hash,
    stable_content_id,
)
from spine_sim.foundation.config import ResolvedConfig
from spine_sim.foundation.models import (
    AttemptOutcome,
    CapabilityStatus,
    CertificationStatus,
    PhysicalFeasibility,
    RejectedTrialBase,
    SourceIdentity,
    StatusTuple,
    ValuePresence,
)
from spine_sim.foundation.writer import make_run_envelope

from .contracts import FailureFamily, m02_maturity
from .result_extension import (
    REJECTED_TRIAL_DIAGNOSTICS_DATASET,
    REPLAY_STEPS_DATASET,
    DiagnosticLevel,
    RejectedTrialDiagnosticRecord,
    ReplayStepRecord,
    m02_result_extension,
)

STREAMING_SCHEMA_VERSION = "1.0.0"
STREAMING_REQUIREMENT_AUTHORITY = "M02_NUMERICS_REQUIREMENTS 1.0.0 §16,18.7,21"
PER_CASE_CACHE_LIMIT_BYTES = 256 * 1024 * 1024
DEFAULT_SYNTHETIC_CACHE_BYTES = 64 * 1024
DEFAULT_TRANSACTION_BATCH_SIZE = 256
DEFAULT_FAILURE_PERIOD = 257
_UINT256_MODULUS = 1 << 256


class StreamingStage(StrEnum):
    """Frozen M02 §16 load stages; these are not scheduler states."""

    SINGLE_SPINE_PRESCREEN = "SINGLE_SPINE_PRESCREEN"
    ARRAY_INITIAL_SCREEN = "ARRAY_INITIAL_SCREEN"
    ARRAY_FINE_SCREEN = "ARRAY_FINE_SCREEN"
    FINAL_COMPARE_1000 = "FINAL_COMPARE_1000"
    FINAL_EXTENSION_4000 = "FINAL_EXTENSION_4000"


_FINAL_STAGES = frozenset({StreamingStage.FINAL_COMPARE_1000, StreamingStage.FINAL_EXTENSION_4000})


@dataclass(frozen=True, slots=True)
class StreamingCasePlan:
    """A lazy Cartesian case-plan description supplied by an external caller."""

    stage: StreamingStage
    design_count: int
    scenario_count: int
    root_seed: int = 0x4D30325F53545245414D494E475F3130
    schema_version: str = STREAMING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != STREAMING_SCHEMA_VERSION:
            raise ValueError("unsupported M02 streaming schema version")
        if self.design_count <= 0 or self.scenario_count <= 0:
            raise ValueError("streaming plan dimensions must be positive")
        if not 0 <= self.root_seed < 1 << 128:
            raise ValueError("root_seed must be an unsigned 128-bit integer")

    @property
    def case_count(self) -> int:
        return self.design_count * self.scenario_count

    @property
    def final_paired_panel(self) -> bool:
        return self.stage in _FINAL_STAGES

    @property
    def semantic_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "stage": self.stage.value,
            "design_count": self.design_count,
            "scenario_count": self.scenario_count,
            "root_seed": self.root_seed,
            "pairing": "SCENARIO_MAJOR_COMMON_RANDOM_NUMBERS",
            "diagnostic_policy": (
                "COMPACT_WITH_FIXED_5_PERCENT_STANDARD_WITNESS_FAILURES_FULL"
                if self.final_paired_panel
                else "STANDARD"
            ),
        }

    @property
    def plan_hash(self) -> str:
        return semantic_hash(self.semantic_payload)

    @property
    def plan_id(self) -> str:
        return stable_content_id("m02-streaming-plan", self.semantic_payload)

    @property
    def checkpoint_scenario_counts(self) -> tuple[int, ...]:
        if not self.final_paired_panel:
            return ()
        candidates = (64, 128, 256, 512, 1000, 4000)
        return tuple(item for item in candidates if item <= self.scenario_count)

    @property
    def standard_witness_scenario_count(self) -> int:
        if not self.final_paired_panel:
            return self.scenario_count
        return sum(index % 20 == 0 for index in range(self.scenario_count))

    def case_at(self, ordinal: int) -> StreamingCase:
        if not 0 <= ordinal < self.case_count:
            raise IndexError("streaming case ordinal is outside the plan")
        scenario_index, design_index = divmod(ordinal, self.design_count)
        panel = "FINAL_PAIRED_TERRAIN_PANEL" if self.final_paired_panel else self.stage.value
        design_panel = "FINAL_FOUR_DESIGNS" if self.final_paired_panel else self.stage.value
        scenario_id = stable_content_id(
            "terrain-scenario",
            {
                "panel": panel,
                "root_seed": self.root_seed,
                "scenario_index": scenario_index,
            },
        )
        design_id = stable_content_id(
            "opaque-design",
            {"panel": design_panel, "design_index": design_index},
        )
        base_level = (
            DiagnosticLevel.STANDARD
            if not self.final_paired_panel or scenario_index % 20 == 0
            else DiagnosticLevel.COMPACT
        )
        case_id = stable_content_id(
            "case",
            {
                "campaign_panel": panel,
                "design_id": design_id,
                "terrain_scenario_id": scenario_id,
            },
        )
        return StreamingCase(
            ordinal=ordinal,
            case_id=case_id,
            design_index=design_index,
            design_id=design_id,
            scenario_index=scenario_index,
            terrain_scenario_id=scenario_id,
            requested_diagnostic_level=base_level,
        )

    def iter_cases(self, start: int = 0, stop: int | None = None) -> Iterable[StreamingCase]:
        resolved_stop = self.case_count if stop is None else stop
        if not 0 <= start <= resolved_stop <= self.case_count:
            raise ValueError("invalid streaming case slice")
        for ordinal in range(start, resolved_stop):
            yield self.case_at(ordinal)


@dataclass(frozen=True, slots=True)
class StreamingCase:
    """One opaque design/scenario pair, generated only when requested."""

    ordinal: int
    case_id: str
    design_index: int
    design_id: str
    scenario_index: int
    terrain_scenario_id: str
    requested_diagnostic_level: DiagnosticLevel

    @property
    def semantic_payload(self) -> dict[str, Any]:
        return {
            "ordinal": self.ordinal,
            "case_id": self.case_id,
            "design_index": self.design_index,
            "design_id": self.design_id,
            "scenario_index": self.scenario_index,
            "terrain_scenario_id": self.terrain_scenario_id,
        }


def frozen_streaming_plans() -> tuple[StreamingCasePlan, ...]:
    """Return the exact five §16 load descriptions without materializing their cases."""

    return (
        StreamingCasePlan(StreamingStage.SINGLE_SPINE_PRESCREEN, 16, 4),
        StreamingCasePlan(StreamingStage.ARRAY_INITIAL_SCREEN, 64, 4),
        StreamingCasePlan(StreamingStage.ARRAY_FINE_SCREEN, 16, 16),
        StreamingCasePlan(StreamingStage.FINAL_COMPARE_1000, 4, 1000),
        StreamingCasePlan(StreamingStage.FINAL_EXTENSION_4000, 4, 4000),
    )


@dataclass(frozen=True, slots=True)
class SyntheticOutcome:
    """Deterministic, non-physical response from the cheap scalability owner."""

    outcome_kind: str
    failure_family: str | None
    reason_code: str
    step_count: int
    event_count: int
    raw_response_metric_micro: int | None
    raw_secondary_metric_micro: int | None
    runtime_cost_units: int
    semantic_result_hash: str

    @property
    def semantic_payload(self) -> dict[str, Any]:
        return {
            "outcome_kind": self.outcome_kind,
            "failure_family": self.failure_family,
            "reason_code": self.reason_code,
            "step_count": self.step_count,
            "event_count": self.event_count,
            "raw_response_metric_micro": self.raw_response_metric_micro,
            "raw_secondary_metric_micro": self.raw_secondary_metric_micro,
            "runtime_cost_units": self.runtime_cost_units,
        }

    @property
    def failed(self) -> bool:
        return self.failure_family is not None


class DeterministicSyntheticOwner:
    """Stateless case evaluator with a fixed, reusable scratch allocation."""

    backend_id = "M02_CHEAP_DETERMINISTIC_SYNTHETIC_OWNER"
    operation_profile_id = "VALIDATION_ONLY_STREAMING_1.0.0"

    def __init__(
        self,
        *,
        failure_period: int = DEFAULT_FAILURE_PERIOD,
        cache_bytes: int = DEFAULT_SYNTHETIC_CACHE_BYTES,
    ) -> None:
        if failure_period < 0:
            raise ValueError("failure_period cannot be negative")
        if not 0 <= cache_bytes <= PER_CASE_CACHE_LIMIT_BYTES:
            raise ValueError("synthetic owner cache exceeds the per-case 256 MiB limit")
        self.failure_period = failure_period
        self.cache_bytes = cache_bytes
        self._scratch = bytearray(cache_bytes)
        self.evaluation_count = 0
        self.owner_contract_hash = semantic_hash(
            {
                "backend_id": self.backend_id,
                "operation_profile_id": self.operation_profile_id,
                "failure_period": failure_period,
                "algorithm": "hash_derived_integer_metrics_without_A_or_B_physics",
            }
        )

    @property
    def retained_case_count(self) -> int:
        return 0

    def evaluate(self, case: StreamingCase) -> SyntheticOutcome:
        digest = semantic_hash(
            {
                "owner_contract_hash": self.owner_contract_hash,
                "case": case.semantic_payload,
            }
        )
        word_a = int(digest[:16], 16)
        word_b = int(digest[16:32], 16)
        if self._scratch:
            index = word_a % len(self._scratch)
            self._scratch[index] = word_b & 0xFF
        self.evaluation_count += 1
        failed = self.failure_period > 0 and word_a % self.failure_period == 0
        step_count = 2 + word_b % 7
        event_count = (word_a >> 8) % 4
        runtime_cost_units = step_count * 10 + event_count * 3 + 1
        if failed:
            payload: dict[str, Any] = {
                "outcome_kind": "NUMERICAL_FAILURE",
                "failure_family": FailureFamily.NUMERICAL_FAILURE.value,
                "reason_code": "M02_VALIDATION_SYNTHETIC_NUMERICAL_FAILURE",
                "step_count": step_count,
                "event_count": event_count,
                "raw_response_metric_micro": None,
                "raw_secondary_metric_micro": None,
                "runtime_cost_units": runtime_cost_units,
            }
        else:
            payload = {
                "outcome_kind": "SYNTHETIC_ACCEPTED_DECISION",
                "failure_family": None,
                "reason_code": "M02_VALIDATION_SYNTHETIC_ACCEPTED",
                "step_count": step_count,
                "event_count": event_count,
                "raw_response_metric_micro": word_a % 1_000_003,
                "raw_secondary_metric_micro": word_b % 1_000_033,
                "runtime_cost_units": runtime_cost_units,
            }
        return SyntheticOutcome(**payload, semantic_result_hash=semantic_hash(payload))


def effective_diagnostic_level(case: StreamingCase, outcome: SyntheticOutcome) -> DiagnosticLevel:
    """Upgrade every failure to FULL without feeding retention back into evaluation."""

    return DiagnosticLevel.FULL if outcome.failed else case.requested_diagnostic_level


@dataclass(frozen=True, slots=True)
class StreamingAggregate:
    """Constant-size, order-independent summary that can be merged across shards."""

    case_count: int = 0
    accepted_decision_count: int = 0
    numerical_failure_count: int = 0
    step_count: int = 0
    event_count: int = 0
    compact_diagnostic_count: int = 0
    standard_diagnostic_count: int = 0
    full_diagnostic_count: int = 0
    runtime_cost_units: int = 0
    diagnostic_cost_units: int = 0
    raw_response_metric_micro_sum: int = 0
    raw_secondary_metric_micro_sum: int = 0
    ordinal_sum: int = 0
    ordinal_square_sum: int = 0
    outcome_hash_sum: int = 0
    outcome_hash_xor: int = 0

    @property
    def semantic_result_hash(self) -> str:
        return semantic_hash(
            {
                "case_count": self.case_count,
                "accepted_decision_count": self.accepted_decision_count,
                "numerical_failure_count": self.numerical_failure_count,
                "step_count": self.step_count,
                "event_count": self.event_count,
                "runtime_cost_units": self.runtime_cost_units,
                "raw_response_metric_micro_sum": self.raw_response_metric_micro_sum,
                "raw_secondary_metric_micro_sum": self.raw_secondary_metric_micro_sum,
                "ordinal_sum": self.ordinal_sum,
                "ordinal_square_sum": self.ordinal_square_sum,
                "outcome_hash_sum_hex": f"{self.outcome_hash_sum:064x}",
                "outcome_hash_xor_hex": f"{self.outcome_hash_xor:064x}",
            }
        )

    @property
    def diagnostic_level_counts(self) -> dict[str, int]:
        return {
            DiagnosticLevel.COMPACT.value: self.compact_diagnostic_count,
            DiagnosticLevel.STANDARD.value: self.standard_diagnostic_count,
            DiagnosticLevel.FULL.value: self.full_diagnostic_count,
        }

    def merge(self, other: StreamingAggregate) -> StreamingAggregate:
        return StreamingAggregate(
            case_count=self.case_count + other.case_count,
            accepted_decision_count=(self.accepted_decision_count + other.accepted_decision_count),
            numerical_failure_count=(self.numerical_failure_count + other.numerical_failure_count),
            step_count=self.step_count + other.step_count,
            event_count=self.event_count + other.event_count,
            compact_diagnostic_count=(
                self.compact_diagnostic_count + other.compact_diagnostic_count
            ),
            standard_diagnostic_count=(
                self.standard_diagnostic_count + other.standard_diagnostic_count
            ),
            full_diagnostic_count=self.full_diagnostic_count + other.full_diagnostic_count,
            runtime_cost_units=self.runtime_cost_units + other.runtime_cost_units,
            diagnostic_cost_units=self.diagnostic_cost_units + other.diagnostic_cost_units,
            raw_response_metric_micro_sum=(
                self.raw_response_metric_micro_sum + other.raw_response_metric_micro_sum
            ),
            raw_secondary_metric_micro_sum=(
                self.raw_secondary_metric_micro_sum + other.raw_secondary_metric_micro_sum
            ),
            ordinal_sum=self.ordinal_sum + other.ordinal_sum,
            ordinal_square_sum=self.ordinal_square_sum + other.ordinal_square_sum,
            outcome_hash_sum=(self.outcome_hash_sum + other.outcome_hash_sum) % _UINT256_MODULUS,
            outcome_hash_xor=self.outcome_hash_xor ^ other.outcome_hash_xor,
        )

    def to_dict(self) -> dict[str, int | str | dict[str, int]]:
        return {
            "case_count": self.case_count,
            "accepted_decision_count": self.accepted_decision_count,
            "numerical_failure_count": self.numerical_failure_count,
            "step_count": self.step_count,
            "event_count": self.event_count,
            "diagnostic_level_counts": self.diagnostic_level_counts,
            "runtime_cost_units": self.runtime_cost_units,
            "diagnostic_cost_units": self.diagnostic_cost_units,
            "raw_response_metric_micro_sum": self.raw_response_metric_micro_sum,
            "raw_secondary_metric_micro_sum": self.raw_secondary_metric_micro_sum,
            "ordinal_sum": self.ordinal_sum,
            "ordinal_square_sum": self.ordinal_square_sum,
            "outcome_hash_sum_hex": f"{self.outcome_hash_sum:064x}",
            "outcome_hash_xor_hex": f"{self.outcome_hash_xor:064x}",
        }


class _MutableAggregate:
    def __init__(self, initial: StreamingAggregate | None = None) -> None:
        value = initial or StreamingAggregate()
        self.case_count = value.case_count
        self.accepted_decision_count = value.accepted_decision_count
        self.numerical_failure_count = value.numerical_failure_count
        self.step_count = value.step_count
        self.event_count = value.event_count
        self.compact_diagnostic_count = value.compact_diagnostic_count
        self.standard_diagnostic_count = value.standard_diagnostic_count
        self.full_diagnostic_count = value.full_diagnostic_count
        self.runtime_cost_units = value.runtime_cost_units
        self.diagnostic_cost_units = value.diagnostic_cost_units
        self.raw_response_metric_micro_sum = value.raw_response_metric_micro_sum
        self.raw_secondary_metric_micro_sum = value.raw_secondary_metric_micro_sum
        self.ordinal_sum = value.ordinal_sum
        self.ordinal_square_sum = value.ordinal_square_sum
        self.outcome_hash_sum = value.outcome_hash_sum
        self.outcome_hash_xor = value.outcome_hash_xor

    def add(
        self,
        case: StreamingCase,
        outcome: SyntheticOutcome,
        level: DiagnosticLevel,
    ) -> None:
        self.case_count += 1
        self.accepted_decision_count += int(not outcome.failed)
        self.numerical_failure_count += int(outcome.failed)
        self.step_count += outcome.step_count
        self.event_count += outcome.event_count
        if level is DiagnosticLevel.COMPACT:
            self.compact_diagnostic_count += 1
            self.diagnostic_cost_units += 1
        elif level is DiagnosticLevel.STANDARD:
            self.standard_diagnostic_count += 1
            self.diagnostic_cost_units += 3
        else:
            self.full_diagnostic_count += 1
            self.diagnostic_cost_units += 8
        self.runtime_cost_units += outcome.runtime_cost_units
        self.raw_response_metric_micro_sum += outcome.raw_response_metric_micro or 0
        self.raw_secondary_metric_micro_sum += outcome.raw_secondary_metric_micro or 0
        self.ordinal_sum += case.ordinal
        self.ordinal_square_sum += case.ordinal * case.ordinal
        digest = int(outcome.semantic_result_hash, 16)
        self.outcome_hash_sum = (self.outcome_hash_sum + digest) % _UINT256_MODULUS
        self.outcome_hash_xor ^= digest

    def freeze(self) -> StreamingAggregate:
        return StreamingAggregate(
            case_count=self.case_count,
            accepted_decision_count=self.accepted_decision_count,
            numerical_failure_count=self.numerical_failure_count,
            step_count=self.step_count,
            event_count=self.event_count,
            compact_diagnostic_count=self.compact_diagnostic_count,
            standard_diagnostic_count=self.standard_diagnostic_count,
            full_diagnostic_count=self.full_diagnostic_count,
            runtime_cost_units=self.runtime_cost_units,
            diagnostic_cost_units=self.diagnostic_cost_units,
            raw_response_metric_micro_sum=self.raw_response_metric_micro_sum,
            raw_secondary_metric_micro_sum=self.raw_secondary_metric_micro_sum,
            ordinal_sum=self.ordinal_sum,
            ordinal_square_sum=self.ordinal_square_sum,
            outcome_hash_sum=self.outcome_hash_sum,
            outcome_hash_xor=self.outcome_hash_xor,
        )


@dataclass(frozen=True, slots=True)
class StreamingCursor:
    """Serializable pause token bound to one semantic plan."""

    plan_hash: str
    next_ordinal: int
    aggregate: StreamingAggregate
    schema_version: str = STREAMING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != STREAMING_SCHEMA_VERSION:
            raise ValueError("unsupported streaming cursor schema version")
        if self.next_ordinal < 0 or self.aggregate.case_count != self.next_ordinal:
            raise ValueError("cursor ordinal and aggregate count disagree")

    @classmethod
    def initial(cls, plan: StreamingCasePlan) -> StreamingCursor:
        return cls(plan.plan_hash, 0, StreamingAggregate())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "plan_hash": self.plan_hash,
            "next_ordinal": self.next_ordinal,
            "aggregate": {
                name: getattr(self.aggregate, name)
                for name in StreamingAggregate.__dataclass_fields__
            },
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> StreamingCursor:
        schema_version = _required_str(payload, "schema_version")
        plan_hash = _required_str(payload, "plan_hash")
        next_ordinal = _required_int(payload, "next_ordinal")
        raw_aggregate = payload.get("aggregate")
        if not isinstance(raw_aggregate, Mapping):
            raise ValueError("cursor aggregate must be an object")
        values = {
            name: _required_int(raw_aggregate, name)
            for name in StreamingAggregate.__dataclass_fields__
        }
        return cls(
            plan_hash=plan_hash,
            next_ordinal=next_ordinal,
            aggregate=StreamingAggregate(**values),
            schema_version=schema_version,
        )


def _required_str(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _required_int(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    return value


class StreamingDiagnosticSink(Protocol):
    """Minimal ordered sink contract; implementations may retain only a small batch."""

    @property
    def next_ordinal(self) -> int: ...

    @property
    def max_buffered_case_count(self) -> int: ...

    @property
    def max_buffered_bytes(self) -> int: ...

    def write(
        self,
        case: StreamingCase,
        outcome: SyntheticOutcome,
        level: DiagnosticLevel,
    ) -> None: ...

    def flush(self) -> None: ...


class CountingDiagnosticSink:
    """Constant-memory sink used for replay and scalability measurements."""

    def __init__(self) -> None:
        self._next_ordinal = 0

    @property
    def next_ordinal(self) -> int:
        return self._next_ordinal

    @property
    def max_buffered_case_count(self) -> int:
        return min(self._next_ordinal, 1)

    @property
    def max_buffered_bytes(self) -> int:
        return 0

    def write(
        self,
        case: StreamingCase,
        outcome: SyntheticOutcome,
        level: DiagnosticLevel,
    ) -> None:
        del outcome, level
        if case.ordinal != self._next_ordinal:
            raise ValueError("diagnostic sink received a non-contiguous case")
        self._next_ordinal += 1

    def flush(self) -> None:
        return None


@dataclass(frozen=True, slots=True)
class StreamingPassResult:
    cursor: StreamingCursor
    plan_case_count: int
    processed_case_count: int
    wall_time_seconds: float
    peak_rss_bytes: int
    owner_cache_bytes: int
    sink_max_buffered_case_count: int
    sink_max_buffered_bytes: int

    @property
    def complete(self) -> bool:
        return self.cursor.next_ordinal == self.plan_case_count


def stream_plan(
    plan: StreamingCasePlan,
    owner: DeterministicSyntheticOwner,
    sink: StreamingDiagnosticSink,
    *,
    cursor: StreamingCursor | None = None,
    max_cases: int | None = None,
) -> StreamingPassResult:
    """Execute a contiguous slice, flushing diagnostics before returning a pause token."""

    active = cursor or StreamingCursor.initial(plan)
    if active.plan_hash != plan.plan_hash:
        raise ValueError("cursor belongs to a different streaming plan")
    if active.next_ordinal > plan.case_count:
        raise ValueError("cursor is beyond the end of the plan")
    if sink.next_ordinal != active.next_ordinal:
        raise ValueError("diagnostic sink position and cursor position disagree")
    if max_cases is not None and max_cases < 0:
        raise ValueError("max_cases cannot be negative")
    stop = plan.case_count
    if max_cases is not None:
        stop = min(stop, active.next_ordinal + max_cases)
    accumulator = _MutableAggregate(active.aggregate)
    started = time.perf_counter()
    for case in plan.iter_cases(active.next_ordinal, stop):
        outcome = owner.evaluate(case)
        level = effective_diagnostic_level(case, outcome)
        sink.write(case, outcome, level)
        accumulator.add(case, outcome, level)
    sink.flush()
    wall_time = time.perf_counter() - started
    next_cursor = StreamingCursor(plan.plan_hash, stop, accumulator.freeze())
    return StreamingPassResult(
        cursor=next_cursor,
        plan_case_count=plan.case_count,
        processed_case_count=stop - active.next_ordinal,
        wall_time_seconds=wall_time,
        peak_rss_bytes=_peak_rss_bytes(),
        owner_cache_bytes=owner.cache_bytes,
        sink_max_buffered_case_count=sink.max_buffered_case_count,
        sink_max_buffered_bytes=sink.max_buffered_bytes,
    )


def execute_plan_shard(
    plan: StreamingCasePlan,
    *,
    shard_index: int,
    shard_count: int,
    failure_period: int = DEFAULT_FAILURE_PERIOD,
) -> StreamingAggregate:
    """Execute one strided shard for an order-independent merge check."""

    if shard_count <= 0 or not 0 <= shard_index < shard_count:
        raise ValueError("invalid shard index/count")
    owner = DeterministicSyntheticOwner(failure_period=failure_period)
    accumulator = _MutableAggregate()
    for ordinal in range(shard_index, plan.case_count, shard_count):
        case = plan.case_at(ordinal)
        outcome = owner.evaluate(case)
        accumulator.add(case, outcome, effective_diagnostic_level(case, outcome))
    return accumulator.freeze()


class M00StreamingDiagnosticWriter:
    """Bounded-batch M02 replay diagnostic writer backed by M00 transactions."""

    def __init__(
        self,
        writer: ResultWriter,
        plan: StreamingCasePlan,
        resolved_config: ResolvedConfig,
        *,
        batch_size: int,
        campaign_case_id: str,
        parent_state_id: str,
        owner_contract_hash: str,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self.writer = writer
        self.plan = plan
        self.resolved_config = resolved_config
        self.batch_size = batch_size
        self.campaign_case_id = campaign_case_id
        self.parent_state_id = parent_state_id
        self.owner_contract_hash = owner_contract_hash
        self._pending: list[
            tuple[StreamingCase, SyntheticOutcome, DiagnosticLevel, ReplayStepRecord]
        ] = []
        self._next_ordinal = 0
        self._max_buffered_case_count = 0
        self._max_buffered_bytes = 0
        self._pending_bytes = 0
        self._published = False

    @classmethod
    def create(
        cls,
        destination: str | Path,
        plan: StreamingCasePlan,
        *,
        batch_size: int = DEFAULT_TRANSACTION_BATCH_SIZE,
        failure_period: int = DEFAULT_FAILURE_PERIOD,
    ) -> M00StreamingDiagnosticWriter:
        registry = SchemaRegistry()
        ResultWriter.register_extension_schema(registry, m02_result_extension())
        registry_hash = registry.freeze()
        config_values = {
            "artifact_kind": "M02_STREAMING_VALIDATION_ONLY",
            "streaming_plan": plan.semantic_payload,
            "per_case_cache_limit_bytes": PER_CASE_CACHE_LIMIT_BYTES,
            "synthetic_failure_period": failure_period,
            "scheduler_ranker": "NOT_IMPLEMENTED",
            "physical_owner": "CHEAP_DETERMINISTIC_SYNTHETIC_OWNER",
        }
        resolved_config = ResolvedConfig(
            config_id=f"m02-streaming:{plan.plan_hash}",
            schema_id="m02.streaming.validation.config",
            schema_version=STREAMING_SCHEMA_VERSION,
            values=config_values,
            leaves=(),
            semantic_hash=semantic_hash(config_values),
        )
        replay_manifest = {
            "artifact_kind": "M02_STREAMING_REPLAY_MANIFEST",
            "schema_version": STREAMING_SCHEMA_VERSION,
            "plan": plan.semantic_payload,
            "canonical_reduction": "UINT256_SUM_XOR_AND_INTEGER_COUNTERS",
            "thread_count": 1,
        }
        envelope = make_run_envelope(
            registry_hash=registry_hash,
            resolved_run_config=resolved_config,
            operation_kind="M02_VALIDATION_ONLY",
            operation_profile="STREAMING_SCALABILITY",
            source_file_hashes={
                "M02_NUMERICS_REQUIREMENTS": semantic_hash(STREAMING_REQUIREMENT_AUTHORITY)
            },
            replay_manifest=replay_manifest,
            git_commit="VALIDATION_ONLY",
            dirty_status="RECORDED_BY_CALLER_OUTSIDE_SEMANTIC_FIXTURE",
            provenance_labels=("VALIDATION_ONLY", "SYNTHETIC_OWNER", "NOT_CERTIFIABLE"),
        )
        writer = ResultWriter.create_run_bundle(
            destination,
            registry=registry,
            run_envelope=envelope,
        )
        writer.write_resolved_config_and_provenance(
            resolved_config,
            provenance={
                "source_identity": SourceIdentity.VALIDATION_ONLY.value,
                "experimentally_validated": "BLOCKED_UNAVAILABLE",
                "physical_scope": "NO_A_OR_B_PHYSICS",
            },
            replay_manifest=replay_manifest,
        )
        campaign_case_id = stable_content_id(
            "case", {"plan_hash": plan.plan_hash, "role": "streaming-validation-campaign"}
        )
        writer.create_case_shard(
            campaign_case_id,
            design_id="design:M02_STREAMING_VALIDATION_CAMPAIGN",
            seed_id=f"seed:{plan.root_seed:032x}",
            surface_realization_id="surface:SYNTHETIC_OWNER_NO_M01",
            resolved_case_config=resolved_config,
        )
        parent_state_id = stable_content_id(
            "state", {"plan_hash": plan.plan_hash, "role": "diagnostic-root"}
        )
        owner_contract_hash = DeterministicSyntheticOwner(
            failure_period=failure_period,
            cache_bytes=0,
        ).owner_contract_hash
        return cls(
            writer,
            plan,
            resolved_config,
            batch_size=batch_size,
            campaign_case_id=campaign_case_id,
            parent_state_id=parent_state_id,
            owner_contract_hash=owner_contract_hash,
        )

    @property
    def next_ordinal(self) -> int:
        return self._next_ordinal

    @property
    def max_buffered_case_count(self) -> int:
        return self._max_buffered_case_count

    @property
    def max_buffered_bytes(self) -> int:
        return self._max_buffered_bytes

    @property
    def root(self) -> Path:
        return self.writer.root

    def write(
        self,
        case: StreamingCase,
        outcome: SyntheticOutcome,
        level: DiagnosticLevel,
    ) -> None:
        if self._published:
            raise ValueError("cannot append to a published M00 bundle")
        if case.ordinal != self._next_ordinal:
            raise ValueError("M00 streaming writer received a non-contiguous case")
        status = _outcome_status(outcome, self.parent_state_id)
        trial_id = (
            stable_content_id("trial", {"plan_hash": self.plan.plan_hash, "case": case.case_id})
            if outcome.failed
            else None
        )
        record = ReplayStepRecord(
            run_id=self.writer.run_envelope.run_id,
            case_id=self.campaign_case_id,
            schema_version=STREAMING_SCHEMA_VERSION,
            status=status,
            source_identity=SourceIdentity.VALIDATION_ONLY,
            maturity=m02_maturity(numerically_verified=True),
            certification_status=CertificationStatus.NOT_CERTIFIABLE,
            replay_step_id=stable_content_id(
                "replay-step", {"plan_hash": self.plan.plan_hash, "ordinal": case.ordinal}
            ),
            target_id=case.case_id,
            point_id=None,
            event_id=None,
            trial_id=trial_id,
            commit_receipt_id=None,
            decision_index=case.ordinal,
            decision_kind=f"SYNTHETIC_OWNER_CASE_{level.value}",
            decision_hash=outcome.semantic_result_hash,
            replay_mode="SEMANTIC_REPLAY",
            backend_id=DeterministicSyntheticOwner.backend_id,
            operation_profile_id=DeterministicSyntheticOwner.operation_profile_id,
            resolved_config_hash=self.resolved_config.semantic_hash,
            owner_contract_hash=self.owner_contract_hash,
            canonical_reduction_hash=semantic_hash("UINT256_SUM_XOR_AND_INTEGER_COUNTERS"),
            thread_settings_hash=semantic_hash({"synthetic_owner_threads": 1}),
            expected_semantic_hash=outcome.semantic_result_hash,
            observed_semantic_hash=outcome.semantic_result_hash,
            matched=True,
        )
        self._pending.append((case, outcome, level, record))
        self._pending_bytes += len(
            json.dumps(record.storage_dict(), ensure_ascii=False, sort_keys=True)
        )
        self._next_ordinal += 1
        self._max_buffered_case_count = max(self._max_buffered_case_count, len(self._pending))
        self._max_buffered_bytes = max(self._max_buffered_bytes, self._pending_bytes)
        if len(self._pending) >= self.batch_size:
            self.flush()

    def flush(self) -> None:
        if not self._pending:
            return
        first = self._pending[0][0].ordinal
        last = self._pending[-1][0].ordinal
        transaction = self.writer.begin_transaction(
            self.campaign_case_id,
            self.parent_state_id,
            f"m02-stream:{self.plan.plan_hash}:{first}:{last}",
        )
        transaction.stage_transaction_records(*(item[3] for item in self._pending))
        transaction.prepare()
        transaction.commit()
        for case, outcome, level, _ in self._pending:
            if outcome.failed:
                self._write_rejected_diagnostic(case, outcome, level)
        self._pending.clear()
        self._pending_bytes = 0

    def finish(self) -> Path:
        if self._published:
            return self.root
        if self._next_ordinal != self.plan.case_count:
            raise ValueError("cannot publish a partial streaming validation bundle")
        self.flush()
        self.writer.finalize_case(self.campaign_case_id)
        self.writer.publish_run_manifest()
        self._published = True
        return self.root

    def output_size_bytes(self) -> int:
        return sum(path.stat().st_size for path in self.root.rglob("*") if path.is_file())

    def _write_rejected_diagnostic(
        self,
        case: StreamingCase,
        outcome: SyntheticOutcome,
        level: DiagnosticLevel,
    ) -> None:
        if level is not DiagnosticLevel.FULL:
            raise ValueError("synthetic failures must retain FULL diagnostics")
        trial_id = stable_content_id(
            "trial", {"plan_hash": self.plan.plan_hash, "case": case.case_id}
        )
        status = _outcome_status(outcome, self.parent_state_id)
        payload_ref = f"validation-only:m02-stream:{case.case_id}"
        base = RejectedTrialBase(
            trial_id=trial_id,
            run_id=self.writer.run_envelope.run_id,
            case_id=self.campaign_case_id,
            parent_accepted_state_id=self.parent_state_id,
            request_hash=semantic_hash(case.semantic_payload),
            candidate_hash=outcome.semantic_result_hash,
            requested_path_target=float(case.ordinal),
            status=status,
            reason_codes=(outcome.reason_code,),
            diagnostic_summary="deterministic synthetic numerical-failure fixture",
            optional_full_payload_ref=payload_ref,
            last_valid_state_id=self.parent_state_id,
            source_identity=SourceIdentity.VALIDATION_ONLY,
        )
        extension = RejectedTrialDiagnosticRecord(
            run_id=self.writer.run_envelope.run_id,
            case_id=self.campaign_case_id,
            schema_version=STREAMING_SCHEMA_VERSION,
            status=status,
            source_identity=SourceIdentity.VALIDATION_ONLY,
            maturity=m02_maturity(numerically_verified=True),
            certification_status=CertificationStatus.NOT_CERTIFIABLE,
            diagnostic_id=stable_content_id("m02-rejected-diagnostic", {"trial_id": trial_id}),
            trial_id=trial_id,
            parent_accepted_state_id=self.parent_state_id,
            request_hash=semantic_hash(case.semantic_payload),
            candidate_hash=outcome.semantic_result_hash,
            failure_family=FailureFamily.NUMERICAL_FAILURE.value,
            reason_code=outcome.reason_code,
            failure_stage="VALIDATION_ONLY_SYNTHETIC_OWNER",
            attempt_index=case.ordinal,
            retry_index=0,
            requested_path_target=float(case.ordinal),
            coordinate_unit="case_index",
            last_valid_state_id=self.parent_state_id,
            diagnostic_level=DiagnosticLevel.FULL.value,
            full_payload_ref=payload_ref,
            retryable=False,
            next_requested_step=None,
            accepted_state_advanced=False,
            commit_receipt_id=None,
        )
        self.writer.record_rejected_trial(base, extension_records=(extension,))


def _outcome_status(outcome: SyntheticOutcome, parent_state_id: str) -> StatusTuple:
    return StatusTuple(
        ValuePresence.NULL if outcome.failed else ValuePresence.PRESENT,
        CapabilityStatus.SUPPORTED,
        AttemptOutcome.NUMERICAL_FAILURE if outcome.failed else AttemptOutcome.ACCEPTED,
        PhysicalFeasibility.NOT_ASSESSED,
        CertificationStatus.NOT_CERTIFIABLE,
        outcome.reason_code,
        (
            "VALIDATION_ONLY injected numerical failure; no physical inference"
            if outcome.failed
            else "VALIDATION_ONLY deterministic synthetic decision; no A/B physics"
        ),
        authority_refs=(STREAMING_REQUIREMENT_AUTHORITY,),
        last_valid_state_id=parent_state_id,
    )


def verify_streaming_bundle(
    bundle: str | Path,
    plan: StreamingCasePlan,
    expected: StreamingAggregate,
) -> dict[str, Any]:
    """Read an M00 bundle in streaming batches and compare its replay digest."""

    reader = ResultReader.open(bundle, VerifyMode.FULL)
    result = reader.query(
        REPLAY_STEPS_DATASET,
        (
            "decision_index",
            "decision_hash",
            "decision_kind",
            "matched",
        ),
        batch_size=DEFAULT_TRANSACTION_BATCH_SIZE,
        include_non_default=True,
    )
    count = 0
    ordinal_sum = 0
    ordinal_square_sum = 0
    outcome_hash_sum = 0
    outcome_hash_xor = 0
    replay_mismatch_count = 0
    failure_count = 0
    level_counts = {item.value: 0 for item in DiagnosticLevel}
    for batch in result:
        columns = batch.to_pydict()
        for ordinal, digest, kind, matched in zip(
            columns["decision_index"],
            columns["decision_hash"],
            columns["decision_kind"],
            columns["matched"],
            strict=True,
        ):
            if not isinstance(ordinal, int) or not isinstance(digest, str):
                raise ValueError("M00 replay row has an invalid ordinal/hash")
            if not isinstance(kind, str) or not isinstance(matched, bool):
                raise ValueError("M00 replay row has invalid decision metadata")
            count += 1
            ordinal_sum += ordinal
            ordinal_square_sum += ordinal * ordinal
            numeric_digest = int(digest, 16)
            outcome_hash_sum = (outcome_hash_sum + numeric_digest) % _UINT256_MODULUS
            outcome_hash_xor ^= numeric_digest
            replay_mismatch_count += int(not matched)
            level = kind.rsplit("_", 1)[-1]
            if level not in level_counts:
                raise ValueError("M00 replay row has an unknown diagnostic level")
            level_counts[level] += 1
            failure_count += int(level == DiagnosticLevel.FULL.value)

    diagnostic_count = 0
    non_full_failure_count = 0
    accepted_state_advanced_count = 0
    diagnostics = reader.query(
        REJECTED_TRIAL_DIAGNOSTICS_DATASET,
        ("diagnostic_level", "accepted_state_advanced", "commit_receipt_id"),
        batch_size=DEFAULT_TRANSACTION_BATCH_SIZE,
        include_non_default=True,
        include_diagnostics=True,
    )
    for batch in diagnostics:
        columns = batch.to_pydict()
        for level, advanced, receipt in zip(
            columns["diagnostic_level"],
            columns["accepted_state_advanced"],
            columns["commit_receipt_id"],
            strict=True,
        ):
            diagnostic_count += 1
            non_full_failure_count += int(level != DiagnosticLevel.FULL.value)
            accepted_state_advanced_count += int(bool(advanced) or receipt is not None)

    checks = {
        "case_count_matched": count == expected.case_count == plan.case_count,
        "ordinal_coverage_matched": (
            ordinal_sum == expected.ordinal_sum
            and ordinal_square_sum == expected.ordinal_square_sum
        ),
        "semantic_digest_matched": (
            outcome_hash_sum == expected.outcome_hash_sum
            and outcome_hash_xor == expected.outcome_hash_xor
        ),
        "diagnostic_levels_matched": level_counts == expected.diagnostic_level_counts,
        "replay_rows_matched": replay_mismatch_count == 0,
        "failure_count_matched": (
            failure_count == diagnostic_count == expected.numerical_failure_count
        ),
        "all_failures_full": non_full_failure_count == 0,
        "rejected_state_isolated": accepted_state_advanced_count == 0,
    }
    return {
        "status": "PASSED" if all(checks.values()) else "FAILED",
        "checks": checks,
        "replay_row_count": count,
        "rejected_diagnostic_count": diagnostic_count,
        "query_result_hash": result.manifest.result_hash,
        "bundle_semantic_hash": reader.bundle_info()["bundle_semantic_hash"],
    }


def validate_streaming_plan(
    plan: StreamingCasePlan,
    *,
    failure_period: int = DEFAULT_FAILURE_PERIOD,
    shard_count: int = 4,
) -> dict[str, Any]:
    """Exercise pause/resume, replay, and merge for one frozen plan."""

    pause_after = max(1, plan.case_count // 3)
    owner = DeterministicSyntheticOwner(failure_period=failure_period)
    sink = CountingDiagnosticSink()
    first = stream_plan(plan, owner, sink, max_cases=pause_after)
    serialized_cursor = json.dumps(first.cursor.to_dict(), sort_keys=True)
    restored = StreamingCursor.from_dict(json.loads(serialized_cursor))
    second = stream_plan(plan, owner, sink, cursor=restored)
    primary = second.cursor.aggregate

    replay_owner = DeterministicSyntheticOwner(failure_period=failure_period)
    replay_sink = CountingDiagnosticSink()
    replay = stream_plan(plan, replay_owner, replay_sink)

    merged = StreamingAggregate()
    for shard_index in reversed(range(shard_count)):
        merged = merged.merge(
            execute_plan_shard(
                plan,
                shard_index=shard_index,
                shard_count=shard_count,
                failure_period=failure_period,
            )
        )

    checks = {
        "case_count_matched": primary.case_count == plan.case_count,
        "pause_resume_matched": restored.next_ordinal == pause_after,
        "replay_matched": replay.cursor.aggregate == primary,
        "merge_matched": merged == primary,
        "owner_retains_no_cases": owner.retained_case_count == 0,
        "cache_within_per_case_limit": owner.cache_bytes <= PER_CASE_CACHE_LIMIT_BYTES,
        "all_failures_full": (primary.full_diagnostic_count == primary.numerical_failure_count),
    }
    return {
        "stage": plan.stage.value,
        "plan_id": plan.plan_id,
        "plan_hash": plan.plan_hash,
        "design_count": plan.design_count,
        "terrain_scenario_count": plan.scenario_count,
        "case_count": plan.case_count,
        "shared_terrain_scenario_ids_across_designs": True,
        "checkpoint_scenario_counts": list(plan.checkpoint_scenario_counts),
        "requested_standard_witness_scenario_count": (plan.standard_witness_scenario_count),
        "requested_standard_witness_case_count": (
            plan.standard_witness_scenario_count * plan.design_count
        ),
        "failure_axis": {
            "numerical_failure_count": primary.numerical_failure_count,
            "physical_feasibility": PhysicalFeasibility.NOT_ASSESSED.value,
            "replacement_seed_count": 0,
        },
        "raw_metric_axes": {
            "raw_response_metric_micro_sum": primary.raw_response_metric_micro_sum,
            "raw_secondary_metric_micro_sum": primary.raw_secondary_metric_micro_sum,
        },
        "cost_axis": {
            "runtime_cost_units": primary.runtime_cost_units,
            "diagnostic_cost_units": primary.diagnostic_cost_units,
            "diagnostic_level_counts": primary.diagnostic_level_counts,
        },
        "counts": {
            "case_count": primary.case_count,
            "step_count": primary.step_count,
            "event_count": primary.event_count,
        },
        "semantic_result_hash": primary.semantic_result_hash,
        "pause_resume": {
            "pause_after_case_count": pause_after,
            "serialized_cursor_bytes": len(serialized_cursor.encode("utf-8")),
            "status": "MATCHED" if checks["pause_resume_matched"] else "MISMATCH",
        },
        "replay_status": "MATCHED" if checks["replay_matched"] else "MISMATCH",
        "merge_status": "MATCHED" if checks["merge_matched"] else "MISMATCH",
        "performance": {
            "wall_time_seconds": first.wall_time_seconds + second.wall_time_seconds,
            "replay_wall_time_seconds": replay.wall_time_seconds,
            "peak_rss_bytes": max(first.peak_rss_bytes, second.peak_rss_bytes),
            "m01_cache_bytes": 0,
            "m02_cache_bytes": owner.cache_bytes,
            "per_case_cache_limit_bytes": PER_CASE_CACHE_LIMIT_BYTES,
            "max_buffered_case_count": sink.max_buffered_case_count,
            "max_buffered_bytes": sink.max_buffered_bytes,
            "output_size_bytes": 0,
        },
        "checks": checks,
        "validation_status": "PASSED" if all(checks.values()) else "FAILED",
    }


def run_streaming_validation(
    *,
    plans: Iterable[StreamingCasePlan] | None = None,
    failure_period: int = DEFAULT_FAILURE_PERIOD,
    bundle_destination: str | Path | None = None,
    bundle_batch_size: int = DEFAULT_TRANSACTION_BATCH_SIZE,
) -> dict[str, Any]:
    """Run all frozen scalability fixtures and optionally write/read an M00 bundle."""

    selected = tuple(plans or frozen_streaming_plans())
    if not selected:
        raise ValueError("at least one streaming plan is required")
    started = time.perf_counter()
    plan_reports = [
        validate_streaming_plan(plan, failure_period=failure_period) for plan in selected
    ]
    bundle_report: dict[str, Any] = {"status": "NOT_REQUESTED"}
    bundle_output_size = 0
    if bundle_destination is not None:
        bundle_plan = max(selected, key=lambda item: item.case_count)
        owner = DeterministicSyntheticOwner(failure_period=failure_period)
        writer = M00StreamingDiagnosticWriter.create(
            bundle_destination,
            bundle_plan,
            batch_size=bundle_batch_size,
            failure_period=failure_period,
        )
        pause_after = max(1, bundle_plan.case_count // 3)
        first = stream_plan(bundle_plan, owner, writer, max_cases=pause_after)
        restored = StreamingCursor.from_dict(
            json.loads(json.dumps(first.cursor.to_dict(), sort_keys=True))
        )
        second = stream_plan(bundle_plan, owner, writer, cursor=restored)
        writer.finish()
        bundle_output_size = writer.output_size_bytes()
        bundle_report = verify_streaming_bundle(writer.root, bundle_plan, second.cursor.aggregate)
        bundle_report.update(
            {
                "path": writer.root.as_posix(),
                "output_size_bytes": bundle_output_size,
                "transaction_batch_size": bundle_batch_size,
                "max_buffered_case_count": writer.max_buffered_case_count,
                "max_buffered_bytes": writer.max_buffered_bytes,
            }
        )

    plan_statuses = [item["validation_status"] for item in plan_reports]
    status = (
        "PASSED"
        if all(item == "PASSED" for item in plan_statuses)
        and bundle_report["status"] in {"PASSED", "NOT_REQUESTED"}
        else "FAILED"
    )
    cache_sizes = [int(item["performance"]["m02_cache_bytes"]) for item in plan_reports]
    return {
        "artifact_kind": "M02_STREAMING_SCALABILITY_VALIDATION",
        "schema_version": STREAMING_SCHEMA_VERSION,
        "requirement_authority": STREAMING_REQUIREMENT_AUTHORITY,
        "scope": {
            "source_identity": SourceIdentity.VALIDATION_ONLY.value,
            "owner": DeterministicSyntheticOwner.backend_id,
            "a_b_physics": "NOT_IMPLEMENTED",
            "production_scheduler_ranker": "NOT_IMPLEMENTED",
            "binary_success_or_composite_score": "NOT_PRODUCED",
            "experimentally_validated": "BLOCKED_UNAVAILABLE",
            "certification_status": CertificationStatus.NOT_CERTIFIABLE.value,
        },
        "frozen_campaign_totals": {
            "base_case_count": 4576,
            "expanded_case_count": 16576,
            "final_compare_and_extension_are_alternative_campaign_totals": True,
        },
        "environment": _environment_report(),
        "plans": plan_reports,
        "bounded_memory": {
            "per_case_cache_limit_bytes": PER_CASE_CACHE_LIMIT_BYTES,
            "observed_m02_cache_bytes_min": min(cache_sizes),
            "observed_m02_cache_bytes_max": max(cache_sizes),
            "cache_growth_across_campaign_sizes_bytes": max(cache_sizes) - min(cache_sizes),
            "campaign_cases_retained": 0,
        },
        "m00_writer_reader_round_trip": bundle_report,
        "artifact_output_size_bytes": bundle_output_size,
        "wall_time_seconds": time.perf_counter() - started,
        "validation_status": status,
    }


def write_streaming_validation_report(destination: str | Path, report: Mapping[str, Any]) -> Path:
    """Write a machine-readable JSON report and record its converged byte size."""

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.loads(json.dumps(report, ensure_ascii=False, sort_keys=True))
    payload.setdefault("report_artifact", {})
    for _ in range(4):
        encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        size = len(encoded.encode("utf-8"))
        payload["report_artifact"] = {"path": path.as_posix(), "size_bytes": size}
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _environment_report() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor() or "UNAVAILABLE",
        "logical_cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "backend_id": DeterministicSyntheticOwner.backend_id,
        "thread_settings": {"synthetic_owner_threads": 1},
        "canonical_reduction": "UINT256_SUM_XOR_AND_INTEGER_COUNTERS",
    }


__all__ = [
    "DEFAULT_FAILURE_PERIOD",
    "DEFAULT_SYNTHETIC_CACHE_BYTES",
    "DEFAULT_TRANSACTION_BATCH_SIZE",
    "PER_CASE_CACHE_LIMIT_BYTES",
    "CountingDiagnosticSink",
    "DeterministicSyntheticOwner",
    "M00StreamingDiagnosticWriter",
    "StreamingAggregate",
    "StreamingCase",
    "StreamingCasePlan",
    "StreamingCursor",
    "StreamingPassResult",
    "StreamingStage",
    "effective_diagnostic_level",
    "execute_plan_shard",
    "frozen_streaming_plans",
    "run_streaming_validation",
    "stream_plan",
    "validate_streaming_plan",
    "verify_streaming_bundle",
    "write_streaming_validation_report",
]
