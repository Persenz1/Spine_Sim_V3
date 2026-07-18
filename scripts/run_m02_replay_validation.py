"""Run the deterministic VALIDATION_ONLY M02 replay acceptance fixture."""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path
from typing import Any

from spine_sim.foundation.canonical import semantic_hash
from spine_sim.foundation.replay import ReplayManifest, ReplayMode, make_replay_manifest
from spine_sim.foundation.storage import write_json_atomic
from spine_sim.numerics.contracts import DiagnosticLevel
from spine_sim.numerics.replay import (
    M02_CANONICAL_ORDER_POLICY,
    M02_CANONICAL_REDUCTION_ORDER,
    M02_FLOATING_POINT_PROFILE,
    M02_THREAD_POLICY,
    M02ReplayDecisionChain,
    M02ReplayManifest,
    ReplayDecisionDraft,
    ReplayDecisionKind,
    build_replay_decision_chain,
    make_m02_replay_manifest,
    verify_m02_replay,
)

DEFAULT_REPORT = Path("build/m02/M02_REPLAY_VALIDATION.json")
BACKEND = "numpy-lapack-float64"
CONFIG_HASH = semantic_hash("M02_VALIDATION_CONFIG_1.0.0")
OWNER_HASHES = {
    "owner:a": semantic_hash("M02_REPLAY_SYNTHETIC_OWNER_A_1.0.0"),
    "owner:b": semantic_hash("M02_REPLAY_SYNTHETIC_OWNER_B_1.0.0"),
}


def _profile(backend: str = BACKEND, operation_profile: str = "default") -> str:
    return semantic_hash(
        {
            "numerical_backend": backend,
            "operation_profile": operation_profile,
            "canonical_reduction_order": M02_CANONICAL_REDUCTION_ORDER,
            "thread_policy": M02_THREAD_POLICY,
            "floating_point_profile": M02_FLOATING_POINT_PROFILE,
        }
    )


def _draft(
    case_id: str,
    kind: ReplayDecisionKind,
    step: int,
    payload: dict[str, Any],
    *,
    owner_id: str = "",
    diagnostics: dict[str, Any] | None = None,
    profile: str | None = None,
) -> ReplayDecisionDraft:
    semantic_output = {
        key: value
        for key, value in payload.items()
        if key not in {"m01_cache_status", "m01_materialization_receipt_id"}
    }
    return ReplayDecisionDraft(
        case_id=case_id,
        target_id=f"target:{case_id}",
        trial_id=None if kind is ReplayDecisionKind.TARGET else f"trial:{case_id}:{step}",
        logical_step_index=step,
        decision_kind=kind,
        owner_id=owner_id,
        input_hash=semantic_hash((case_id, kind.value, step, "input")),
        output_hash=semantic_hash((case_id, kind.value, step, semantic_output)),
        backend_profile_hash=profile or _profile(),
        payload=payload,
        diagnostics=diagnostics or {},
    )


def _case_drafts(
    case_id: str,
    *,
    cache_status: str = "cold",
    materialization_receipt: str = "m01-materialization:cold",
    merit: float = 0.125,
    profile: str | None = None,
) -> list[ReplayDecisionDraft]:
    values: list[tuple[ReplayDecisionKind, dict[str, Any]]] = [
        (
            ReplayDecisionKind.TARGET,
            {
                "parent_accepted_state_id": f"state:{case_id}:parent",
                "parent_commit_receipt_id": f"receipt:{case_id}:parent",
                "target_value_mm": 100.0,
            },
        ),
        (
            ReplayDecisionKind.STEP_SIZE,
            {
                "proposed_step_mm": 0.5,
                "reason": "INITIAL",
                "retry_index": 0,
                "easy_streak": 0,
                "hard_streak": 0,
            },
        ),
        (
            ReplayDecisionKind.PREDICTOR,
            {
                "predictor_source_state_id": f"state:{case_id}:parent",
                "unknown_initial_hash": semantic_hash((case_id, "unknown")),
                "branch_request": "OWNER_BRANCH_REQUEST",
            },
        ),
        (
            ReplayDecisionKind.NONLINEAR_ITERATION,
            {
                "iteration": 0,
                "linear_solve_hash": semantic_hash((case_id, "linear")),
                "line_search_factor": 1.0,
                "merit": merit,
            },
        ),
        (
            ReplayDecisionKind.RESIDUAL_QUALITY,
            {
                "block_id": "force_x",
                "raw_norm": merit,
                "scaled_norm": merit,
                "hard": True,
                "passed": True,
            },
        ),
        (
            ReplayDecisionKind.EVENT_REGISTRATION,
            {
                "event_set": ["event:slip", "event:contact"],
                "applicable_event_ids": ["event:contact", "event:slip"],
                "registration_hash": semantic_hash((case_id, "registration")),
            },
        ),
        (
            ReplayDecisionKind.EVENT_PROBE,
            {
                "probe_coordinate_mm": 0.5,
                "balance_response_hash": semantic_hash((case_id, "balanced-probe")),
                "uz_recomputed": True,
                "surface_realization_id": "surface:stable",
                "m01_cache_status": cache_status,
                "m01_materialization_receipt_id": materialization_receipt,
            },
        ),
        (
            ReplayDecisionKind.EVENT_BRACKET,
            {
                "bracket_hash": semantic_hash((case_id, "bracket")),
                "root_method": "BRENT",
                "earliestness_certificate_hash": semantic_hash((case_id, "earliest")),
            },
        ),
        (
            ReplayDecisionKind.CASCADE_ROUND,
            {
                "simultaneous_group_hash": semantic_hash((case_id, "simultaneous")),
                "dependency_dag_hash": semantic_hash((case_id, "dag")),
                "cascade_round": 0,
                "state_hash": semantic_hash((case_id, "cascade-state")),
            },
        ),
        (
            ReplayDecisionKind.PREPARE,
            {
                "owner_response_hash": semantic_hash((case_id, "owners")),
                "intent_batch_hash": semantic_hash((case_id, "intents")),
                "read_set": ["owner:b", "owner:a"],
                "write_set": ["state:b", "state:a"],
                "rollback_hash": semantic_hash((case_id, "rollback")),
                "prepare_hash": semantic_hash((case_id, "prepare")),
            },
        ),
        (
            ReplayDecisionKind.COMMIT,
            {
                "commit_hash": semantic_hash((case_id, "commit")),
                "commit_receipt_id": f"receipt:{case_id}:accepted:0",
                "committed_state_id": f"state:{case_id}:accepted:0",
                "event_order": ["event:contact", "event:slip"],
            },
        ),
    ]
    drafts = [
        _draft(
            case_id,
            kind,
            0 if kind is ReplayDecisionKind.TARGET else 1,
            payload,
            profile=profile,
            diagnostics={"m01_tile_order": [2, 0, 1]}
            if kind is ReplayDecisionKind.EVENT_PROBE
            else None,
        )
        for kind, payload in values
    ]
    drafts.extend(
        [
            _draft(
                case_id,
                ReplayDecisionKind.OWNER_RESPONSE,
                1,
                {"response_hash": semantic_hash((case_id, owner_id))},
                owner_id=owner_id,
                diagnostics={"owner_call_order": call_index},
                profile=profile,
            )
            for call_index, owner_id in enumerate(("owner:b", "owner:a"))
        ]
    )
    return drafts


def _base_manifest(
    case_plan: tuple[str, ...],
    *,
    backend: str = BACKEND,
    config_hash: str = CONFIG_HASH,
) -> ReplayManifest:
    base = make_replay_manifest(
        run_id="run:m02-replay-validation",
        run_fingerprint=semantic_hash("M02_REPLAY_VALIDATION_RUN"),
        result_api_version="1.0.0",
        bundle_schema_version="1.0.0",
        resolved_run_config_hash=config_hash,
        resolved_case_config_hashes={case_id: config_hash for case_id in case_plan},
        source_hashes={"M02_NUMERICS_REQUIREMENTS": semantic_hash("1.0.0")},
        registry_hash=semantic_hash("M02_REPLAY_VALIDATION_REGISTRY"),
        git_commit="VALIDATION_ONLY",
        dirty_status="VALIDATION_ONLY",
        case_execution_plan=case_plan,
        idempotency_keys=tuple(f"idempotency:{case_id}" for case_id in case_plan),
        surface_identities=("surface:stable",),
        field_tolerances={"merit": 1.0e-8, "raw_norm": 1.0e-8, "scaled_norm": 1.0e-8},
    )
    return dataclasses.replace(
        base,
        numerical_backend=backend,
        diagnostic_level=DiagnosticLevel.STANDARD.value,
        thread_and_float_settings={
            "canonical_numeric_dtype": "float64",
            "case_reduction_order": "sorted",
            "runtime_thread_count": 1,
        },
    )


def _manifest(
    chain: M02ReplayDecisionChain,
    *,
    case_plan: tuple[str, ...] = ("case:a", "case:b"),
    backend: str = BACKEND,
    config_hash: str = CONFIG_HASH,
    owners: dict[str, str] | None = None,
    profile: str | None = None,
) -> M02ReplayManifest:
    return make_m02_replay_manifest(
        _base_manifest(case_plan, backend=backend, config_hash=config_hash),
        chain,
        resolved_numerics_config_hash=config_hash,
        owner_contract_hashes=owners or OWNER_HASHES,
        backend_profile_hash=profile or _profile(backend),
    )


def _report_summary(report: Any) -> dict[str, Any]:
    return {
        "equivalent": report.equivalent,
        "difference_count": len(report.differences),
        "ignored_difference_count": len(report.ignored_differences),
        "difference_fields": sorted({item.scope for item in report.differences}),
    }


def run_validation() -> dict[str, Any]:
    cases = [*_case_drafts("case:a"), *_case_drafts("case:b")]
    expected_chain = build_replay_decision_chain(cases)
    expected_manifest = _manifest(expected_chain)

    exact_chain = build_replay_decision_chain(list(cases))
    exact = verify_m02_replay(
        expected_manifest,
        expected_chain,
        _manifest(exact_chain),
        exact_chain,
        mode=ReplayMode.BITWISE_REPLAY,
    )

    reordered_chain = build_replay_decision_chain(list(reversed(cases)))
    reordered = verify_m02_replay(
        expected_manifest,
        expected_chain,
        _manifest(reordered_chain, case_plan=("case:b", "case:a")),
        reordered_chain,
        mode=ReplayMode.SEMANTIC_REPLAY,
    )

    warm_cases = [
        *_case_drafts(
            "case:a",
            cache_status="warm",
            materialization_receipt="m01-materialization:warm:a",
        ),
        *_case_drafts(
            "case:b",
            cache_status="warm",
            materialization_receipt="m01-materialization:warm:b",
        ),
    ]
    warm_chain = build_replay_decision_chain(warm_cases)
    cache = verify_m02_replay(
        expected_manifest,
        expected_chain,
        _manifest(warm_chain),
        warm_chain,
        mode=ReplayMode.BITWISE_REPLAY,
    )

    close_chain = build_replay_decision_chain(
        [*_case_drafts("case:a", merit=0.125 + 5.0e-10), *_case_drafts("case:b")]
    )
    tolerance = verify_m02_replay(
        expected_manifest,
        expected_chain,
        _manifest(close_chain),
        close_chain,
        mode=ReplayMode.SEMANTIC_REPLAY,
    )
    tolerance_bitwise = verify_m02_replay(
        expected_manifest,
        expected_chain,
        _manifest(close_chain),
        close_chain,
        mode=ReplayMode.BITWISE_REPLAY,
    )

    changed_backend = "scipy-lapack-float64"
    changed_backend_profile = _profile(changed_backend)
    backend_chain = build_replay_decision_chain(
        [
            *_case_drafts("case:a", profile=changed_backend_profile),
            *_case_drafts("case:b", profile=changed_backend_profile),
        ]
    )
    backend = verify_m02_replay(
        expected_manifest,
        expected_chain,
        _manifest(
            backend_chain,
            backend=changed_backend,
            profile=changed_backend_profile,
        ),
        backend_chain,
        mode=ReplayMode.SEMANTIC_REPLAY,
    )

    changed_config = semantic_hash("M02_VALIDATION_CONFIG_1.0.0_MODIFIED")
    config = verify_m02_replay(
        expected_manifest,
        expected_chain,
        _manifest(expected_chain, config_hash=changed_config),
        expected_chain,
        mode=ReplayMode.SEMANTIC_REPLAY,
    )
    owner = verify_m02_replay(
        expected_manifest,
        expected_chain,
        _manifest(
            expected_chain,
            owners={**OWNER_HASHES, "owner:a": semantic_hash("MODIFIED_OWNER_CONTRACT")},
        ),
        expected_chain,
        mode=ReplayMode.SEMANTIC_REPLAY,
    )

    checks = {
        "exact_repeat_bitwise": _report_summary(exact),
        "serial_parallel_case_owner_order_semantic": _report_summary(reordered),
        "m01_cold_warm_materialization_bitwise": _report_summary(cache),
        "within_tolerance_semantic": _report_summary(tolerance),
        "within_tolerance_bitwise_negative": _report_summary(tolerance_bitwise),
        "backend_profile_negative": _report_summary(backend),
        "config_hash_negative": _report_summary(config),
        "owner_hash_negative": _report_summary(owner),
    }
    expected_outcomes = {
        "exact_repeat_bitwise": True,
        "serial_parallel_case_owner_order_semantic": True,
        "m01_cold_warm_materialization_bitwise": True,
        "within_tolerance_semantic": True,
        "within_tolerance_bitwise_negative": False,
        "backend_profile_negative": False,
        "config_hash_negative": False,
        "owner_hash_negative": False,
    }
    overall_pass = all(
        checks[name]["equivalent"] is expected for name, expected in expected_outcomes.items()
    )
    negative_fields_present = all(
        checks[name]["difference_fields"]
        for name in (
            "within_tolerance_bitwise_negative",
            "backend_profile_negative",
            "config_hash_negative",
            "owner_hash_negative",
        )
    )
    return {
        "schema_version": "1.0.0",
        "scope": "VALIDATION_ONLY_SYNTHETIC_OWNER_NOT_CERTIFIABLE",
        "overall_pass": overall_pass and negative_fields_present,
        "decision_count": len(expected_chain.records),
        "case_count": len(expected_chain.case_ids),
        "bitwise_chain_hash": expected_chain.bitwise_hash,
        "semantic_chain_hash": expected_chain.semantic_hash,
        "canonical_order_policy": M02_CANONICAL_ORDER_POLICY,
        "canonical_reduction_order": M02_CANONICAL_REDUCTION_ORDER,
        "thread_policy": M02_THREAD_POLICY,
        "floating_point_profile": M02_FLOATING_POINT_PROFILE,
        "checks": checks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run frozen M02 deterministic replay validation")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT,
        help=f"Audit JSON destination (default: {DEFAULT_REPORT.as_posix()})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_validation()
    write_json_atomic(args.output, report)
    summary = {
        "overall_pass": report["overall_pass"],
        "decision_count": report["decision_count"],
        "case_count": report["case_count"],
        "bitwise_chain_hash": report["bitwise_chain_hash"],
        "semantic_chain_hash": report["semantic_chain_hash"],
        "audit_json": args.output.as_posix(),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
