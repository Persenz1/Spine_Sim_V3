#!/usr/bin/env python3
"""Plan or execute the frozen 38-case M03 campaign with bounded history.

The default mode is intentionally cheap and emits the exact frozen plan.  The
``--execute`` mode constructs each M01 synthetic realization and invokes the
real public M03 standalone driver one case at a time.  A completed FULL
standalone history is reduced to metrics before the next case is admitted.
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import platform
import resource
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Protocol

from spine_sim.foundation.canonical import (
    canonical_json_bytes,
    semantic_hash,
    stable_content_id,
)
from spine_sim.foundation.errors import ContractViolation, FoundationError, TransactionError
from spine_sim.foundation.storage import read_json, write_json_atomic
from spine_sim.single_spine.campaigns import (
    CampaignStreamingCursor,
    CampaignStreamingPlan,
    StreamingCampaignCase,
    SyntheticSurfaceCampaignSpec,
    frozen_campaign_streaming_plan,
)
from spine_sim.single_spine.contracts import (
    EmbeddedSingleSpineTrialRequest,
    FailureAxis,
    SingleSpineTrialResponse,
    StandaloneSingleSpineRunRequest,
    StandaloneTerminalStatus,
    make_standalone_request,
)
from spine_sim.single_spine.kernel import IntrinsicSingleSpineKernel, KernelEvaluation
from spine_sim.single_spine.standalone import (
    STANDALONE_DRIVER_VERSION,
    StandaloneDriverConfig,
    StandaloneTrialKernel,
    run_standalone_single_spine,
)
from spine_sim.single_spine.surface_adapter import make_geometry_query_policy
from spine_sim.surface import M01ReasonCode, SurfaceProvider, make_synthetic_source_descriptor

DEFAULT_OUTPUT = Path("build/m03/M03_CAMPAIGN_RUN.json")
CAMPAIGN_RUNNER_VERSION = "M03_CAMPAIGN_RUNNER_1.0.0"
NO_TILE_CACHE_MODE = "M01_RANDOM_ACCESS_SPECTRAL_NO_TILE_CACHE"


class _CampaignEvaluationFailure(RuntimeError):
    """A structured case failure whose physical axis must survive reduction."""

    def __init__(self, reason_code: str, failure_axis: FailureAxis, explanation: str) -> None:
        super().__init__(explanation)
        self.reason_code = reason_code
        self.failure_axis = failure_axis
        self.explanation = explanation


@dataclass(frozen=True, slots=True)
class CampaignCaseMetrics:
    """The exact per-case metric set frozen by the M03 campaign plan."""

    accepted_count: int
    trial_count: int
    committed_event_count: int
    query_count: int
    wall_time_seconds: float
    peak_rss_bytes: int
    cache_payload_bytes: int
    cache_hit_count: int
    cache_miss_count: int
    cache_regeneration_count: int
    artifact_size_bytes: int
    terminal_status: str
    failure_axis: str
    reason_code: str
    replay_manifest_id: str
    final_receipt_id: str | None

    def __post_init__(self) -> None:
        integer_metrics = (
            self.accepted_count,
            self.trial_count,
            self.committed_event_count,
            self.query_count,
            self.peak_rss_bytes,
            self.cache_payload_bytes,
            self.cache_hit_count,
            self.cache_miss_count,
            self.cache_regeneration_count,
            self.artifact_size_bytes,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in integer_metrics
        ):
            raise ValueError("M03 campaign count/size metrics must be nonnegative integers")
        if (
            isinstance(self.wall_time_seconds, bool)
            or not math.isfinite(self.wall_time_seconds)
            or self.wall_time_seconds < 0.0
        ):
            raise ValueError("M03 campaign wall time must be finite and nonnegative")

        if not all(
            isinstance(value, str) and value
            for value in (
                self.terminal_status,
                self.failure_axis,
                self.reason_code,
                self.replay_manifest_id,
            )
        ):
            raise ValueError("M03 campaign terminal/replay identities cannot be empty")
        if self.final_receipt_id is not None and not self.final_receipt_id:
            raise ValueError("final_receipt_id must be nonempty when available")

    def to_dict(self) -> dict[str, int | float | str | None]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class _ArtifactSurfaceHandleReference:
    """Serialization-safe identity for an immutable M01 query handle.

    The live handle owns evaluator state and read-only mapping proxies that are
    deliberately not result data.  A FULL campaign-history measurement keeps
    the exact public M01 identities while excluding those runtime internals.
    ``realization`` remains present so rebuilding an embedded request preserves
    its public-handle precondition during construction.
    """

    handle_id: str
    surface_realization_id: str
    realization: str


def _canonical_history_artifact(execution: Any) -> Any:
    """Return a canonicalizable FULL-history view without live M01 evaluators."""

    snapshots = getattr(execution, "trial_snapshots", None)
    if snapshots is None:
        return execution
    sanitized_snapshots = []
    for snapshot in snapshots:
        handle = snapshot.request.surface_query_handle
        realization = handle.realization
        realization_id = realization.surface_realization_id
        reference = _ArtifactSurfaceHandleReference(
            handle_id=handle.handle_id,
            surface_realization_id=realization_id,
            realization=realization_id,
        )
        sanitized_request = replace(snapshot.request, surface_query_handle=reference)
        sanitized_snapshots.append(replace(snapshot, request=sanitized_request))
    return replace(execution, trial_snapshots=tuple(sanitized_snapshots))


@dataclass(frozen=True, slots=True)
class CampaignCaseEvaluation:
    """One reduced metric row plus, transiently, at most one FULL history."""

    metrics: CampaignCaseMetrics
    full_history: object | None = None
    execution_profile: Mapping[str, Any] | None = None


class CampaignCaseEvaluator(Protocol):
    def __call__(self, case: StreamingCampaignCase) -> CampaignCaseEvaluation: ...


@dataclass(slots=True)
class _RssTracker:
    maximum_observed_bytes: int

    @classmethod
    def start(cls) -> _RssTracker:
        return cls(_current_rss_bytes())

    def sample(self) -> int:
        current = _current_rss_bytes()
        self.maximum_observed_bytes = max(self.maximum_observed_bytes, current)
        return current


class _InstrumentedKernel(StandaloneTrialKernel):
    """Count public M01 query receipts without retaining trial responses."""

    def __init__(self, tracker: _RssTracker, *, maximum_global_cells: int = 20_000) -> None:
        self._kernel = IntrinsicSingleSpineKernel(
            query_policy=make_geometry_query_policy(
                maximum_global_cells=maximum_global_cells,
            )
        )
        self._tracker = tracker
        self.query_count = 0
        self.final_receipt_id: str | None = None

    def evaluate_trial(
        self,
        request: EmbeddedSingleSpineTrialRequest,
    ) -> SingleSpineTrialResponse:
        self._tracker.sample()
        response = self._kernel.evaluate_trial(request)
        self._record_response(response)
        self._tracker.sample()
        return response

    def evaluate_trial_with_artifacts(
        self,
        request: EmbeddedSingleSpineTrialRequest,
    ) -> KernelEvaluation:
        self._tracker.sample()
        evaluation = self._kernel.evaluate_trial_with_artifacts(request)
        self._record_response(evaluation.response)
        self._tracker.sample()
        return evaluation

    def _record_response(self, response: SingleSpineTrialResponse) -> None:
        receipts = response.geometry_contact.query_receipt_ids
        self.query_count += len(receipts)
        if receipts:
            self.final_receipt_id = receipts[-1]


def _current_rss_bytes() -> int:
    try:
        import psutil  # type: ignore[import-untyped]

        return int(psutil.Process().memory_info().rss)
    except ImportError:
        peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return peak if platform.system() == "Darwin" else peak * 1024


def _case_description(case: StreamingCampaignCase) -> dict[str, Any]:
    bundle = case.parameter_bundle
    return {
        "ordinal": case.ordinal,
        "execution_case_id": case.execution_case_id,
        "run_kind": case.run_kind.value,
        "surface_role": case.surface_role.value,
        "surface_spec_id": case.surface_spec_id,
        "seed_id": case.seed_id,
        "latent_noise_id": case.latent_noise_id,
        "surface_realization_id": case.surface_realization_id,
        "trend_case_id": case.trend_case_id,
        "parameter_bundle_id": bundle.parameter_bundle_id,
        "parameters": {
            "tip_radius_mm": bundle.needle.tip_radius_mm,
            "diameter_mm": bundle.needle.diameter_mm,
            "alpha_rad": bundle.needle.alpha_rad,
            "youngs_modulus_mpa": bundle.beam.youngs_modulus_mpa,
            "poisson_ratio": bundle.beam.poisson_ratio,
            "friction_coefficient": bundle.contact.friction_coefficient,
            "bending_enabled": bundle.beam.bending_enabled,
            "mount_mode": bundle.mount.mode.value,
            "spring_stiffness_n_per_mm": bundle.mount.spring_stiffness_n_per_mm,
        },
        "path_policy_id": case.path_policy_id,
        "query_policy_id": case.query_policy_id,
        "requested_diagnostic_level": case.requested_diagnostic_level,
    }


def _validate_metrics(plan: CampaignStreamingPlan, metrics: CampaignCaseMetrics) -> None:
    if tuple(metrics.to_dict()) != plan.required_per_case_metrics:
        raise ContractViolation("case evaluator did not return the exact frozen M03 metric schema")


def _semantic_case_result_id(
    case: StreamingCampaignCase,
    metrics: CampaignCaseMetrics,
    trend_eligibility_evidence: Mapping[str, bool],
) -> str:
    return stable_content_id(
        "m03_campaign_case_result",
        {
            "runner_version": CAMPAIGN_RUNNER_VERSION,
            "execution_case_id": case.execution_case_id,
            "surface_realization_id": case.surface_realization_id,
            "parameter_bundle_id": case.parameter_bundle.parameter_bundle_id,
            "accepted_count": metrics.accepted_count,
            "trial_count": metrics.trial_count,
            "committed_event_count": metrics.committed_event_count,
            "query_count": metrics.query_count,
            "terminal_status": metrics.terminal_status,
            "failure_axis": metrics.failure_axis,
            "reason_code": metrics.reason_code,
            "replay_manifest_id": metrics.replay_manifest_id,
            "final_receipt_id": metrics.final_receipt_id,
            "trend_eligibility_evidence": trend_eligibility_evidence,
        },
    )


def _trend_eligibility(
    metrics: CampaignCaseMetrics,
    execution_profile: Mapping[str, Any] | None,
) -> tuple[bool, dict[str, bool]]:
    """Require completed 100 mm response evidence and a matching M00 commit."""

    profile = {} if execution_profile is None else execution_profile
    final_path = profile.get("final_state_total_path_x_mm")
    remaining = profile.get("remaining_travel_mm")
    requested = profile.get("total_drag_travel_mm")
    completed_100_mm = (
        metrics.terminal_status == StandaloneTerminalStatus.TRAVEL_COMPLETE.value
        and metrics.failure_axis == FailureAxis.NONE.value
        and profile.get("completed_travel") is True
        and isinstance(final_path, int | float)
        and not isinstance(final_path, bool)
        and math.isclose(float(final_path), 100.0, rel_tol=0.0, abs_tol=1.0e-9)
        and isinstance(remaining, int | float)
        and not isinstance(remaining, bool)
        and math.isclose(float(remaining), 0.0, rel_tol=0.0, abs_tol=1.0e-9)
        and isinstance(requested, int | float)
        and not isinstance(requested, bool)
        and math.isclose(float(requested), 100.0, rel_tol=0.0, abs_tol=1.0e-9)
    )
    receipt_matches_commit = (
        metrics.final_receipt_id is not None
        and profile.get("m00_campaign_bundle_committed") is True
        and profile.get("final_m00_commit_receipt_id") == metrics.final_receipt_id
    )
    evidence = {
        "completed_100_mm_response": completed_100_mm,
        "m00_canonical_bundle_committed": profile.get("m00_campaign_bundle_committed") is True,
        "final_receipt_matches_commit": receipt_matches_commit,
    }
    return completed_100_mm and receipt_matches_commit, evidence


def _case_result(
    case: StreamingCampaignCase,
    metrics: CampaignCaseMetrics,
    execution_profile: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    trend_eligible, trend_evidence = _trend_eligibility(metrics, execution_profile)
    numerical_failure = (
        metrics.terminal_status == StandaloneTerminalStatus.NUMERICAL_TERMINATION.value
        or metrics.failure_axis == FailureAxis.NUMERICAL_FAILURE.value
    )
    return {
        "case": _case_description(case),
        "metrics": metrics.to_dict(),
        "semantic_case_result_id": _semantic_case_result_id(case, metrics, trend_evidence),
        "trend_value_eligible": trend_eligible,
        "trend_eligibility_evidence": trend_evidence,
        "trend_value": None,
        "numerical_failure_excluded_from_trends": numerical_failure,
        "execution_profile": (
            dict(execution_profile)
            if execution_profile is not None
            else {"mode": "INJECTED_OR_UNDECLARED_EVALUATOR"}
        ),
        "metric_semantics": {
            "query_count": "sum of public M01 query receipt IDs returned by every trial call",
            "peak_rss_bytes": "maximum sampled process RSS during this active case",
            "artifact_size_bytes": "canonical JSON byte size of the transient FULL history",
            "cache_mode": NO_TILE_CACHE_MODE,
            "cache_metrics": "zero because the random-access spectral evaluator has no tile cache",
            "final_receipt_id": (
                "final canonical M00 commit receipt; required, with matching commit evidence, "
                "before a completed 100 mm case may enter trends"
            ),
        },
    }


def _reason_from_foundation_error(error: FoundationError) -> str | None:
    reason = error.details.get("reason_code")
    return reason if isinstance(reason, str) and reason else None


def _classified_exception(error: Exception) -> tuple[FailureAxis, str]:
    if isinstance(error, _CampaignEvaluationFailure):
        return error.failure_axis, error.reason_code

    structured_reason = (
        _reason_from_foundation_error(error) if isinstance(error, FoundationError) else None
    )
    domain_reasons = {
        M01ReasonCode.OUT_OF_DOMAIN.value,
        M01ReasonCode.ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN.value,
    }
    capability_reasons = {
        M01ReasonCode.MEASURED_IMPORT_DEFERRED.value,
        M01ReasonCode.EXTERNAL_MESH_IMPORT_DEFERRED.value,
        M01ReasonCode.QUERY_CAPABILITY_UNAVAILABLE.value,
        M01ReasonCode.TRUST_SCALE_INSUFFICIENT.value,
        M01ReasonCode.RESOLUTION_REFINEMENT_REQUIRED.value,
        M01ReasonCode.GEOMETRY_UNCERTAIN.value,
        M01ReasonCode.QUERY_APPROXIMATION_FAILED.value,
    }
    if structured_reason in domain_reasons:
        return FailureAxis.DOMAIN_ERROR, structured_reason
    if structured_reason in capability_reasons:
        return FailureAxis.CAPABILITY_UNAVAILABLE, structured_reason
    if isinstance(error, TransactionError):
        return FailureAxis.TRANSACTION_FAILURE, structured_reason or error.code
    if isinstance(error, ContractViolation):
        return FailureAxis.CONTRACT_REJECTION, structured_reason or error.code
    return (
        FailureAxis.NUMERICAL_FAILURE,
        f"M03_CAMPAIGN_EXECUTION_EXCEPTION_{type(error).__name__.upper()}",
    )


def _exception_metrics(
    case: StreamingCampaignCase,
    error: Exception,
    *,
    elapsed_seconds: float,
    peak_rss_bytes: int,
) -> CampaignCaseMetrics:
    failure_axis, reason = _classified_exception(error)
    terminal_status = {
        FailureAxis.PHYSICAL_INFEASIBLE: StandaloneTerminalStatus.PHYSICAL_TERMINATION,
        FailureAxis.DOMAIN_ERROR: StandaloneTerminalStatus.DOMAIN_TERMINATION,
        FailureAxis.CAPABILITY_UNAVAILABLE: StandaloneTerminalStatus.CAPABILITY_TERMINATION,
        FailureAxis.CONTRACT_REJECTION: StandaloneTerminalStatus.CAPABILITY_TERMINATION,
        FailureAxis.TRANSACTION_FAILURE: StandaloneTerminalStatus.TRANSACTION_TERMINATION,
        FailureAxis.NUMERICAL_FAILURE: StandaloneTerminalStatus.NUMERICAL_TERMINATION,
        FailureAxis.NONE: StandaloneTerminalStatus.NUMERICAL_TERMINATION,
    }[failure_axis]
    replay_id = stable_content_id(
        "m03_campaign_exception_replay",
        {
            "runner_version": CAMPAIGN_RUNNER_VERSION,
            "execution_case_id": case.execution_case_id,
            "exception_type": type(error).__name__,
            "reason_code": reason,
            "failure_axis": failure_axis,
        },
    )
    return CampaignCaseMetrics(
        accepted_count=0,
        trial_count=0,
        committed_event_count=0,
        query_count=0,
        wall_time_seconds=elapsed_seconds,
        peak_rss_bytes=peak_rss_bytes,
        cache_payload_bytes=0,
        cache_hit_count=0,
        cache_miss_count=0,
        cache_regeneration_count=0,
        artifact_size_bytes=0,
        terminal_status=terminal_status.value,
        failure_axis=failure_axis.value,
        reason_code=reason,
        replay_manifest_id=replay_id,
        final_receipt_id=None,
    )


def _selected_bounds(
    plan: CampaignStreamingPlan,
    *,
    cursor: CampaignStreamingCursor | None,
    start: int | None,
    stop: int | None,
) -> tuple[int, int]:
    if cursor is not None and start is not None:
        raise ValueError("cursor and explicit start are mutually exclusive")
    resolved_start = cursor.next_ordinal if cursor is not None else 0 if start is None else start
    resolved_stop = plan.case_count if stop is None else stop
    if not 0 <= resolved_start <= resolved_stop <= plan.case_count:
        raise ValueError("invalid M03 campaign start/stop bounds")
    return resolved_start, resolved_stop


def build_plan_report(
    *,
    cursor: CampaignStreamingCursor | None = None,
    start: int | None = None,
    stop: int | None = None,
) -> dict[str, Any]:
    """Return a fast, execution-free JSON-ready view of the frozen plan."""

    plan = frozen_campaign_streaming_plan()
    selected_start, selected_stop = _selected_bounds(
        plan,
        cursor=cursor,
        start=start,
        stop=stop,
    )
    metric_placeholders = {name: None for name in plan.required_per_case_metrics}
    cases = [
        {
            "case": _case_description(case),
            "metrics": dict(metric_placeholders),
            "planned_only": True,
        }
        for case in plan.iter_cases(selected_start, selected_stop)
    ]
    next_cursor = CampaignStreamingCursor(plan.plan_id, selected_stop)
    return {
        "schema_version": CAMPAIGN_RUNNER_VERSION,
        "mode": "PLAN_ONLY",
        "plan_id": plan.plan_id,
        "frozen_case_count": plan.case_count,
        "primary_case_count": plan.primary_case_count,
        "smoke_case_count": plan.smoke_case_count,
        "selected_start": selected_start,
        "selected_stop": selected_stop,
        "selected_case_count": len(cases),
        "required_per_case_metrics": list(plan.required_per_case_metrics),
        "streaming_policy": {
            "maximum_full_histories_in_memory": plan.maximum_full_histories_in_memory,
            "checkpoint_interval_cases": plan.checkpoint_interval_cases,
            "retain_completed_full_history": plan.retain_completed_full_history,
            "pause_resume_supported": plan.pause_resume_supported,
            "semantic_replay_required": plan.semantic_replay_required,
        },
        "cases": cases,
        "next_cursor": next_cursor.to_dict(),
    }


def run_streaming_campaign(
    *,
    evaluator: CampaignCaseEvaluator,
    cursor: CampaignStreamingCursor | None = None,
    start: int | None = None,
    stop: int | None = None,
    checkpoint: Callable[[Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Execute a selected slice, reducing and releasing each FULL history in order."""

    plan = frozen_campaign_streaming_plan()
    selected_start, selected_stop = _selected_bounds(
        plan,
        cursor=cursor,
        start=start,
        stop=stop,
    )
    started = time.perf_counter()
    case_results: list[dict[str, Any]] = []
    maximum_full_histories_observed = 0

    def report(next_ordinal: int) -> dict[str, Any]:
        semantic_ids = tuple(item["semantic_case_result_id"] for item in case_results)
        return {
            "schema_version": CAMPAIGN_RUNNER_VERSION,
            "mode": "EXECUTE",
            "plan_id": plan.plan_id,
            "frozen_case_count": plan.case_count,
            "primary_case_count": plan.primary_case_count,
            "smoke_case_count": plan.smoke_case_count,
            "selected_start": selected_start,
            "selected_stop": selected_stop,
            "selected_case_count": selected_stop - selected_start,
            "completed_case_count": len(case_results),
            "required_per_case_metrics": list(plan.required_per_case_metrics),
            "case_results": list(case_results),
            "next_cursor": CampaignStreamingCursor(plan.plan_id, next_ordinal).to_dict(),
            "streaming_evidence": {
                "maximum_full_histories_allowed": plan.maximum_full_histories_in_memory,
                "maximum_full_histories_observed": maximum_full_histories_observed,
                "retained_completed_full_history_count": 0,
                "checkpoint_interval_cases": plan.checkpoint_interval_cases,
                "full_domain_dense_grid_created": False,
            },
            "campaign_replay_manifest_id": stable_content_id(
                "m03_campaign_replay_manifest",
                {
                    "runner_version": CAMPAIGN_RUNNER_VERSION,
                    "plan_id": plan.plan_id,
                    "selected_start": selected_start,
                    "next_ordinal": next_ordinal,
                    "semantic_case_result_ids": semantic_ids,
                },
            ),
            "wall_time_seconds": time.perf_counter() - started,
        }

    for case in plan.iter_cases(selected_start, selected_stop):
        evaluation_started = time.perf_counter()
        tracker = _RssTracker.start()
        execution_profile: Mapping[str, Any] | None = None
        try:
            evaluation = evaluator(case)
            active_full_histories = 1 if evaluation.full_history is not None else 0
            if active_full_histories > plan.maximum_full_histories_in_memory:
                raise ContractViolation("M03 campaign admitted more than one FULL history")
            maximum_full_histories_observed = max(
                maximum_full_histories_observed,
                active_full_histories,
            )
            metrics = evaluation.metrics
            execution_profile = evaluation.execution_profile
            _validate_metrics(plan, metrics)
            del evaluation
        except Exception as error:  # A failed case remains explicit and cannot enter trends.
            tracker.sample()
            metrics = _exception_metrics(
                case,
                error,
                elapsed_seconds=time.perf_counter() - evaluation_started,
                peak_rss_bytes=tracker.maximum_observed_bytes,
            )
            execution_profile = {
                "mode": "CASE_EVALUATOR_EXCEPTION",
                "exception_type": type(error).__name__,
                "exception_message": str(error),
                "terminal_classification": f"{metrics.failure_axis}_EXCLUDED_FROM_TRENDS",
            }
        case_results.append(_case_result(case, metrics, execution_profile))
        next_ordinal = case.ordinal + 1
        gc.collect()
        if checkpoint is not None:
            checkpoint(report(next_ordinal))

    return report(selected_stop)


class RealStandaloneCaseEvaluator:
    """Production evaluator: real M01 realization plus real M03 standalone driver."""

    def __init__(
        self,
        plan: CampaignStreamingPlan | None = None,
        *,
        coarse_validation: bool = False,
        maximum_global_cells: int = 20_000,
    ) -> None:
        resolved = frozen_campaign_streaming_plan() if plan is None else plan
        self._surface_specs = {surface.role: surface for surface in resolved.surfaces}
        self._coarse_validation = coarse_validation
        if maximum_global_cells < 16:
            raise ValueError("maximum_global_cells must be at least 16")
        self._maximum_global_cells = maximum_global_cells

    def __call__(self, case: StreamingCampaignCase) -> CampaignCaseEvaluation:
        started = time.perf_counter()
        tracker = _RssTracker.start()
        surface = self._surface_specs[case.surface_role]
        handle = _open_frozen_surface(surface)
        kernel = _InstrumentedKernel(
            tracker,
            maximum_global_cells=self._maximum_global_cells,
        )
        request = make_standalone_request(
            run_id=stable_content_id(
                "m03_campaign_run",
                {
                    "runner_version": CAMPAIGN_RUNNER_VERSION,
                    "execution_case_id": case.execution_case_id,
                },
            ),
            case_id=case.execution_case_id,
            parameter_bundle=case.parameter_bundle,
            surface_query_handle=handle,
        )
        config = _resolved_execution_config(request, coarse=self._coarse_validation)
        execution = run_standalone_single_spine(request, kernel=kernel, config=config)
        tracker.sample()
        artifact_size = len(canonical_json_bytes(_canonical_history_artifact(execution)))
        response = execution.response
        replay_id = stable_content_id(
            "m03_campaign_case_replay",
            {
                "runner_version": CAMPAIGN_RUNNER_VERSION,
                "execution_case_id": case.execution_case_id,
                "request_hash": request.request_hash,
                "response_hash": response.metadata.semantic_hash,
                "terminal_status": response.terminal_status,
                "final_state_id": response.final_state.state_id,
                "final_query_receipt_id": kernel.final_receipt_id,
            },
        )
        metrics = CampaignCaseMetrics(
            accepted_count=len(execution.accepted_points),
            trial_count=execution.trial_call_count,
            committed_event_count=len(execution.committed_events),
            query_count=kernel.query_count,
            wall_time_seconds=time.perf_counter() - started,
            peak_rss_bytes=tracker.maximum_observed_bytes,
            cache_payload_bytes=0,
            cache_hit_count=0,
            cache_miss_count=0,
            cache_regeneration_count=0,
            artifact_size_bytes=artifact_size,
            terminal_status=response.terminal_status.value,
            failure_axis=response.failure_axis.value,
            reason_code=response.terminal_reason_code,
            replay_manifest_id=replay_id,
            final_receipt_id=None,
        )
        return CampaignCaseEvaluation(
            metrics,
            execution,
            {
                "mode": (
                    "COARSE_VALIDATION" if self._coarse_validation else "FROZEN_DEFAULT_STANDALONE"
                ),
                "real_intrinsic_kernel": True,
                "test_double": False,
                "driver_config_id": config.config_id,
                "driver_config_hash": config.config_hash,
                "drag_step_mm": config.drag_step_mm,
                "event_scan_subdivisions": config.event_scan_subdivisions,
                "maximum_global_cells": self._maximum_global_cells,
                "global_candidate_quality_tolerance_unchanged": True,
                "bounded_query_budget_may_return_capability_termination": (
                    self._maximum_global_cells < 20_000
                ),
                "total_drag_travel_mm": request.drag_policy.travel_mm,
                "quality_request_unchanged": True,
                "completed_travel": response.completed_travel,
                "final_state_total_path_x_mm": response.final_state.total_path_x_mm,
                "remaining_travel_mm": response.remaining_travel_mm,
                "unavailable_protocol_reason": response.unavailable_protocol_reason,
                "final_query_receipt_id": kernel.final_receipt_id,
                "m00_campaign_bundle_committed": False,
                "final_m00_commit_receipt_id": None,
            },
        )


def _resolved_execution_config(
    request: StandaloneSingleSpineRunRequest,
    *,
    coarse: bool,
) -> StandaloneDriverConfig:
    config = StandaloneDriverConfig.resolved(request)
    if not coarse:
        return config
    values = {
        "driver_version": STANDALONE_DRIVER_VERSION,
        "request_resolved_config_hash": request.resolved_config_hash,
        "initial_retreat_step_mm": config.initial_retreat_step_mm,
        "maximum_initial_retreat_mm": config.maximum_initial_retreat_mm,
        "drag_step_mm": 100.0,
        "event_scan_subdivisions": 2,
        "minimum_z_bracket_mm": config.minimum_z_bracket_mm,
        "maximum_preload_z_travel_mm": config.maximum_preload_z_travel_mm,
        "maximum_lift_z_travel_mm": config.maximum_lift_z_travel_mm,
        "bracket_expansion_factor": config.bracket_expansion_factor,
        "event_side_offset_mm": config.event_side_offset_mm,
        "maximum_release_cycles": config.maximum_release_cycles,
    }
    digest = semantic_hash(values)
    return replace(
        config,
        drag_step_mm=100.0,
        event_scan_subdivisions=2,
        config_id=stable_content_id("m03_standalone_driver_config", values),
        config_hash=digest,
    )


def _open_frozen_surface(surface: SyntheticSurfaceCampaignSpec) -> Any:
    provider = SurfaceProvider()
    source = make_synthetic_source_descriptor()
    realized = provider.create_realization(
        source,
        surface.surface_spec,
        latent_identity=surface.latent_noise_identity,
    )
    handle = realized.handle
    if handle is None:
        reason = realized.status.reason_code
        failure_axis = (
            FailureAxis.DOMAIN_ERROR
            if reason
            in {
                M01ReasonCode.OUT_OF_DOMAIN.value,
                M01ReasonCode.ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN.value,
            }
            else FailureAxis.CAPABILITY_UNAVAILABLE
        )
        raise _CampaignEvaluationFailure(
            reason,
            failure_axis,
            f"M01 could not open frozen surface: {reason}",
        )
    if handle.realization.surface_realization_id != surface.surface_realization_id:
        raise _CampaignEvaluationFailure(
            "M03_M01_REALIZATION_IDENTITY_MISMATCH",
            FailureAxis.CONTRACT_REJECTION,
            "reopened M01 realization identity differs from the frozen plan",
        )
    return handle


def _nonnegative_int(value: str) -> int:
    converted = int(value)
    if converted < 0:
        raise argparse.ArgumentTypeError("value must be nonnegative")
    return converted


def _global_cell_budget(value: str) -> int:
    converted = int(value)
    if converted < 16 or converted > 1_000_000:
        raise argparse.ArgumentTypeError("global cell budget must lie in [16, 1000000]")
    return converted


def _load_cursor(value: str) -> CampaignStreamingCursor:
    candidate = Path(value)
    try:
        payload = read_json(candidate) if candidate.is_file() else json.loads(value)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError("cursor must be a JSON object or JSON file") from error
    if not isinstance(payload, dict):
        raise argparse.ArgumentTypeError("cursor JSON must be an object")
    try:
        return CampaignStreamingCursor.from_dict(payload)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--plan-only",
        action="store_true",
        help="Emit the exact plan without constructing surfaces or running physics (default)",
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Run the real public standalone driver one case at a time",
    )
    bounds = parser.add_mutually_exclusive_group()
    bounds.add_argument("--start", type=_nonnegative_int, help="First ordinal (inclusive)")
    bounds.add_argument(
        "--cursor",
        type=_load_cursor,
        help="Resume from a cursor JSON object or file",
    )
    parser.add_argument("--stop", type=_nonnegative_int, help="Stop ordinal (exclusive)")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Atomic JSON report/checkpoint destination",
    )
    parser.add_argument(
        "--cursor-output",
        type=Path,
        help="Optional separate cursor checkpoint updated after every executed case",
    )
    parser.add_argument(
        "--coarse-validation",
        action="store_true",
        help=(
            "With --execute, use a 100 mm drag step and two event scan subdivisions; "
            "total travel, preload, physics kernel, and quality gates remain unchanged"
        ),
    )
    parser.add_argument(
        "--maximum-global-cells",
        type=_global_cell_budget,
        default=20_000,
        help=(
            "Per-query global candidate bound budget. Quality tolerances are never relaxed; "
            "an insufficient budget produces an explicit capability termination."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.coarse_validation and not args.execute:
        raise SystemExit("--coarse-validation requires --execute")
    cursor = args.cursor
    if args.execute:

        def checkpoint(payload: Mapping[str, Any]) -> None:
            report = dict(payload)
            write_json_atomic(args.output, report)
            if args.cursor_output is not None:
                write_json_atomic(args.cursor_output, report["next_cursor"])

        report = run_streaming_campaign(
            evaluator=RealStandaloneCaseEvaluator(
                coarse_validation=args.coarse_validation,
                maximum_global_cells=args.maximum_global_cells,
            ),
            cursor=cursor,
            start=args.start,
            stop=args.stop,
            checkpoint=checkpoint,
        )
    else:
        report = build_plan_report(cursor=cursor, start=args.start, stop=args.stop)
    write_json_atomic(args.output, report)
    if args.cursor_output is not None:
        write_json_atomic(args.cursor_output, report["next_cursor"])
    summary = {
        "mode": report["mode"],
        "plan_id": report["plan_id"],
        "selected_case_count": report["selected_case_count"],
        "completed_case_count": report.get("completed_case_count", 0),
        "next_cursor": report["next_cursor"],
        "output": args.output.as_posix(),
        "output_bytes": args.output.stat().st_size,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
