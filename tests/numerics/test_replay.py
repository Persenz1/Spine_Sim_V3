from __future__ import annotations

import dataclasses
from collections.abc import Sequence

import pytest

from spine_sim.foundation.canonical import semantic_hash
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.replay import ReplayManifest, ReplayMode, make_replay_manifest
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


def _profile(backend: str = "numpy-lapack-float64") -> str:
    return semantic_hash(
        {
            "numerical_backend": backend,
            "canonical_reduction_order": M02_CANONICAL_REDUCTION_ORDER,
            "thread_policy": M02_THREAD_POLICY,
            "floating_point_profile": M02_FLOATING_POINT_PROFILE,
        }
    )


def _draft(
    *,
    case_id: str,
    kind: ReplayDecisionKind,
    step: int,
    payload: dict[str, object],
    owner_id: str = "",
    diagnostics: dict[str, object] | None = None,
    backend_profile_hash: str | None = None,
) -> ReplayDecisionDraft:
    semantic_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"m01_cache_status", "m01_materialization_receipt_id"}
    }
    input_value = {"case_id": case_id, "kind": kind.value, "step": step, "side": "input"}
    output_value = {
        "case_id": case_id,
        "kind": kind.value,
        "step": step,
        "side": "output",
        "payload": semantic_payload,
    }
    return ReplayDecisionDraft(
        case_id=case_id,
        target_id=f"target:{case_id}",
        trial_id=None if kind is ReplayDecisionKind.TARGET else f"trial:{case_id}:{step}",
        logical_step_index=step,
        dependency_rank=0,
        owner_id=owner_id,
        decision_kind=kind,
        input_hash=semantic_hash(input_value),
        output_hash=semantic_hash(output_value),
        backend_profile_hash=backend_profile_hash or _profile(),
        payload=payload,
        diagnostics=diagnostics or {},
    )


def _case_drafts(
    case_id: str,
    *,
    merit: float = 0.125,
    event_order: Sequence[str] = ("event:contact", "event:slip"),
    commit_receipt_id: str | None = None,
    cache_status: str = "cold",
    materialization_receipt_id: str = "m01-materialization:cold",
    backend_profile_hash: str | None = None,
) -> list[ReplayDecisionDraft]:
    receipt = commit_receipt_id or f"receipt:{case_id}:0"
    return [
        _draft(
            case_id=case_id,
            kind=ReplayDecisionKind.TARGET,
            step=0,
            payload={
                "parent_accepted_state_id": f"state:{case_id}:parent",
                "parent_commit_receipt_id": f"receipt:{case_id}:parent",
                "target_value_mm": 100.0,
            },
            backend_profile_hash=backend_profile_hash,
        ),
        _draft(
            case_id=case_id,
            kind=ReplayDecisionKind.STEP_SIZE,
            step=1,
            payload={
                "proposed_step_mm": 0.5,
                "reason": "INITIAL",
                "retry_index": 0,
                "easy_streak": 0,
                "hard_streak": 0,
            },
            backend_profile_hash=backend_profile_hash,
        ),
        _draft(
            case_id=case_id,
            kind=ReplayDecisionKind.OWNER_RESPONSE,
            step=1,
            owner_id="owner:z",
            payload={"response_hash": semantic_hash((case_id, "z")), "read_set": ["b", "a"]},
            diagnostics={"owner_call_order": 0},
            backend_profile_hash=backend_profile_hash,
        ),
        _draft(
            case_id=case_id,
            kind=ReplayDecisionKind.OWNER_RESPONSE,
            step=1,
            owner_id="owner:a",
            payload={"response_hash": semantic_hash((case_id, "a")), "write_set": ["y", "x"]},
            diagnostics={"owner_call_order": 1},
            backend_profile_hash=backend_profile_hash,
        ),
        _draft(
            case_id=case_id,
            kind=ReplayDecisionKind.NONLINEAR_ITERATION,
            step=1,
            payload={
                "iteration": 0,
                "unknown_initial_hash": semantic_hash((case_id, "unknown")),
                "branch_request": "ACTIVE_BRANCH_A",
                "linear_solve_hash": semantic_hash((case_id, "linear")),
                "line_search_factor": 1.0,
                "merit": merit,
            },
            backend_profile_hash=backend_profile_hash,
        ),
        _draft(
            case_id=case_id,
            kind=ReplayDecisionKind.RESIDUAL_QUALITY,
            step=1,
            payload={
                "block_id": "force_x",
                "raw_norm": merit,
                "scaled_norm": merit,
                "hard": True,
                "passed": True,
            },
            backend_profile_hash=backend_profile_hash,
        ),
        _draft(
            case_id=case_id,
            kind=ReplayDecisionKind.EVENT_PROBE,
            step=1,
            payload={
                "event_set": list(reversed(event_order)),
                "event_order": list(event_order),
                "probe_coordinate_mm": 0.5,
                "balance_response_hash": semantic_hash((case_id, "balance")),
                "uz_recomputed": True,
                "surface_realization_id": "surface:stable",
                "m01_materialization_receipt_id": materialization_receipt_id,
                "m01_cache_status": cache_status,
            },
            diagnostics={"m01_tile_order": [3, 1, 2]},
            backend_profile_hash=backend_profile_hash,
        ),
        _draft(
            case_id=case_id,
            kind=ReplayDecisionKind.EVENT_EARLIESTNESS,
            step=1,
            payload={
                "event_order": list(event_order),
                "certificate_hash": semantic_hash((case_id, "earliest")),
                "dependency_dag_hash": semantic_hash((case_id, "dag")),
                "cascade_state_hash": semantic_hash((case_id, "cascade")),
            },
            backend_profile_hash=backend_profile_hash,
        ),
        _draft(
            case_id=case_id,
            kind=ReplayDecisionKind.PREPARE,
            step=1,
            payload={
                "intent_batch_hash": semantic_hash((case_id, "intents")),
                "rollback_token_hash": semantic_hash((case_id, "rollback")),
                "prepare_token_hash": semantic_hash((case_id, "prepare")),
                "read_set": ["owner:z", "owner:a"],
                "write_set": ["state:z", "state:a"],
            },
            backend_profile_hash=backend_profile_hash,
        ),
        _draft(
            case_id=case_id,
            kind=ReplayDecisionKind.COMMIT,
            step=1,
            payload={
                "commit_hash": semantic_hash((case_id, "commit")),
                "commit_receipt_id": receipt,
                "committed_state_id": f"state:{case_id}:accepted:0",
                "event_order": list(event_order),
            },
            backend_profile_hash=backend_profile_hash,
        ),
    ]


def _base_manifest(
    *,
    case_plan: tuple[str, ...] = ("case:a", "case:b"),
    backend: str = "numpy-lapack-float64",
    config_hash: str | None = None,
    diagnostic_level: str = "STANDARD",
) -> ReplayManifest:
    resolved_hash = config_hash or semantic_hash("m02-config:v1")
    manifest = make_replay_manifest(
        run_id="run:m02-replay-test",
        run_fingerprint=semantic_hash("run-fingerprint"),
        result_api_version="1.0.0",
        bundle_schema_version="1.0.0",
        resolved_run_config_hash=resolved_hash,
        resolved_case_config_hashes={case_id: resolved_hash for case_id in case_plan},
        source_hashes={"M02_NUMERICS_REQUIREMENTS": semantic_hash("1.0.0")},
        registry_hash=semantic_hash("registry"),
        git_commit="test-commit",
        dirty_status="clean",
        case_execution_plan=case_plan,
        idempotency_keys=tuple(f"idempotency:{case_id}" for case_id in case_plan),
        surface_identities=("surface:stable",),
        field_tolerances={"merit": 1.0e-8, "raw_norm": 1.0e-8, "scaled_norm": 1.0e-8},
    )
    return dataclasses.replace(
        manifest,
        numerical_backend=backend,
        diagnostic_level=diagnostic_level,
        thread_and_float_settings={
            "canonical_numeric_dtype": "float64",
            "case_reduction_order": "sorted",
            "runtime_thread_count": 1,
        },
    )


def _replay(
    drafts: Sequence[ReplayDecisionDraft],
    *,
    case_plan: tuple[str, ...] = ("case:a", "case:b"),
    backend: str = "numpy-lapack-float64",
    config_hash: str | None = None,
    owners: dict[str, str] | None = None,
    diagnostic_level: DiagnosticLevel = DiagnosticLevel.STANDARD,
) -> tuple[M02ReplayManifest, M02ReplayDecisionChain]:
    chain = build_replay_decision_chain(drafts, diagnostic_level=diagnostic_level)
    base = _base_manifest(
        case_plan=case_plan,
        backend=backend,
        config_hash=config_hash,
        diagnostic_level=diagnostic_level.value,
    )
    manifest = make_m02_replay_manifest(
        base,
        chain,
        resolved_numerics_config_hash=config_hash or semantic_hash("m02-config:v1"),
        owner_contract_hashes=owners
        or {"owner:a": semantic_hash("owner:a:v1"), "owner:z": semantic_hash("owner:z:v1")},
        backend_profile_hash=_profile(backend),
        diagnostic_level=diagnostic_level,
    )
    return manifest, chain


def _standard_drafts(
    *,
    merit: float = 0.125,
    event_order: Sequence[str] = ("event:contact", "event:slip"),
    commit_receipt_id: str | None = None,
    cache_status: str = "cold",
    materialization_receipt_id: str = "m01-materialization:cold",
    backend_profile_hash: str | None = None,
) -> list[ReplayDecisionDraft]:
    return [
        *_case_drafts(
            "case:a",
            merit=merit,
            event_order=event_order,
            commit_receipt_id=commit_receipt_id,
            cache_status=cache_status,
            materialization_receipt_id=materialization_receipt_id,
            backend_profile_hash=backend_profile_hash,
        ),
        *_case_drafts("case:b", backend_profile_hash=backend_profile_hash),
    ]


def test_decision_chain_canonicalizes_case_owner_and_set_order() -> None:
    drafts = _standard_drafts()
    forward = build_replay_decision_chain(drafts)
    reverse = build_replay_decision_chain(list(reversed(drafts)))

    assert forward.bitwise_hash == reverse.bitwise_hash
    assert forward.semantic_hash == reverse.semantic_hash
    assert forward.case_ids == ("case:a", "case:b")
    assert forward.canonical_order_policy == M02_CANONICAL_ORDER_POLICY
    owner_records = [
        item
        for item in forward.for_case("case:a")
        if item.decision_kind == ReplayDecisionKind.OWNER_RESPONSE.value
    ]
    assert [dict(item.payload)["owner_id"] for item in owner_records] == ['"owner:a"', '"owner:z"']
    assert [item.sequence_index for item in forward.for_case("case:a")] == list(
        range(len(forward.for_case("case:a")))
    )
    for previous, current in zip(
        forward.for_case("case:a"), forward.for_case("case:a")[1:], strict=False
    ):
        assert current.parent_decision_hash == previous.metadata.semantic_hash


def test_m01_cache_materialization_and_scheduler_data_are_nonsemantic() -> None:
    cold = build_replay_decision_chain(_standard_drafts())
    warm = build_replay_decision_chain(
        _standard_drafts(
            cache_status="warm",
            materialization_receipt_id="m01-materialization:warm-and-different",
        )
    )

    assert cold.bitwise_hash == warm.bitwise_hash
    assert cold.semantic_hash == warm.semantic_hash
    probe = next(
        item for item in cold.records if item.decision_kind == ReplayDecisionKind.EVENT_PROBE.value
    )
    probe_payload = dict(probe.payload)
    assert "m01_cache_status" not in probe_payload
    assert "m01_materialization_receipt_id" not in probe_payload
    commit = next(
        item for item in cold.records if item.decision_kind == ReplayDecisionKind.COMMIT.value
    )
    assert "commit_receipt_id" in dict(commit.payload)

    cold_manifest, _ = _replay(_standard_drafts())
    warm_manifest, _ = _replay(
        _standard_drafts(
            cache_status="warm",
            materialization_receipt_id="m01-materialization:warm-and-different",
        )
    )
    report = verify_m02_replay(
        cold_manifest,
        cold,
        warm_manifest,
        warm,
        mode=ReplayMode.BITWISE_REPLAY,
    )
    assert report.equivalent
    assert report.ignored_differences
    assert all(
        item.code == "NON_SEMANTIC_DIAGNOSTIC_DIFFERENCE" for item in report.ignored_differences
    )


@pytest.mark.parametrize("mode", tuple(ReplayMode))
def test_exact_repeat_is_equivalent_in_both_public_m00_modes(mode: ReplayMode) -> None:
    drafts = _standard_drafts()
    expected_manifest, expected_chain = _replay(drafts)
    observed_manifest, observed_chain = _replay(list(drafts))
    report = verify_m02_replay(
        expected_manifest,
        expected_chain,
        observed_manifest,
        observed_chain,
        mode=mode,
    )

    assert report.equivalent
    assert not report.differences
    assert report.compared_cases == 2
    assert report.compared_decisions == len(drafts)
    assert report.as_dict()["mode"] == mode.value


def test_serial_parallel_case_and_owner_order_are_semantically_invariant() -> None:
    drafts = _standard_drafts()
    expected_manifest, expected_chain = _replay(drafts)
    observed_manifest, observed_chain = _replay(
        list(reversed(drafts)),
        case_plan=("case:b", "case:a"),
    )
    semantic = verify_m02_replay(
        expected_manifest,
        expected_chain,
        observed_manifest,
        observed_chain,
        mode=ReplayMode.SEMANTIC_REPLAY,
    )
    bitwise = verify_m02_replay(
        expected_manifest,
        expected_chain,
        observed_manifest,
        observed_chain,
        mode=ReplayMode.BITWISE_REPLAY,
    )

    assert semantic.equivalent
    assert not bitwise.equivalent
    assert any(item.scope == "manifest.case_execution_plan" for item in bitwise.differences)


def test_semantic_numeric_tolerance_is_field_versioned_and_bitwise_stays_exact() -> None:
    expected_manifest, expected_chain = _replay(_standard_drafts(merit=0.125))
    close_manifest, close_chain = _replay(_standard_drafts(merit=0.125 + 5.0e-10))
    far_manifest, far_chain = _replay(_standard_drafts(merit=0.125 + 5.0e-5))

    close_semantic = verify_m02_replay(
        expected_manifest,
        expected_chain,
        close_manifest,
        close_chain,
        mode=ReplayMode.SEMANTIC_REPLAY,
    )
    close_bitwise = verify_m02_replay(
        expected_manifest,
        expected_chain,
        close_manifest,
        close_chain,
        mode=ReplayMode.BITWISE_REPLAY,
    )
    far_semantic = verify_m02_replay(
        expected_manifest,
        expected_chain,
        far_manifest,
        far_chain,
        mode=ReplayMode.SEMANTIC_REPLAY,
    )

    assert close_semantic.equivalent
    assert not close_bitwise.equivalent
    assert any(item.code == "DECISION_PAYLOAD_MISMATCH" for item in close_bitwise.differences)
    assert not far_semantic.equivalent
    numeric = [
        item for item in far_semantic.differences if item.code == "NUMERIC_FIELD_OUTSIDE_TOLERANCE"
    ]
    assert numeric
    assert all(item.tolerance == pytest.approx(1.0e-8) for item in numeric)


@pytest.mark.parametrize(
    ("mutation", "required_scope"),
    [
        ("backend", "manifest.numerical_backend"),
        ("profile", "manifest.m02_extension.backend_profile_hash"),
        ("config", "manifest.m02_extension.resolved_numerics_config_hash"),
        ("owner", "manifest.m02_extension.owner_contract_hashes"),
    ],
)
def test_backend_profile_config_and_owner_changes_are_structured_mismatches(
    mutation: str, required_scope: str
) -> None:
    expected_manifest, expected_chain = _replay(_standard_drafts())
    backend = (
        "scipy-lapack-float64" if mutation in {"backend", "profile"} else "numpy-lapack-float64"
    )
    profile = _profile(backend)
    drafts = (
        _standard_drafts(backend_profile_hash=profile)
        if mutation in {"backend", "profile"}
        else _standard_drafts()
    )
    if mutation == "profile":
        # A changed operation profile is represented independently of backend naming.
        profile = semantic_hash("operation-profile:v2")
        drafts = _standard_drafts(backend_profile_hash=profile)
    config_hash = semantic_hash("m02-config:v2") if mutation == "config" else None
    owners = (
        {"owner:a": semantic_hash("owner:a:v2"), "owner:z": semantic_hash("owner:z:v1")}
        if mutation == "owner"
        else None
    )
    observed_chain = build_replay_decision_chain(drafts)
    observed_base = _base_manifest(backend=backend, config_hash=config_hash)
    observed_manifest = make_m02_replay_manifest(
        observed_base,
        observed_chain,
        resolved_numerics_config_hash=config_hash or semantic_hash("m02-config:v1"),
        owner_contract_hashes=owners
        or {"owner:a": semantic_hash("owner:a:v1"), "owner:z": semantic_hash("owner:z:v1")},
        backend_profile_hash=profile,
    )

    report = verify_m02_replay(
        expected_manifest,
        expected_chain,
        observed_manifest,
        observed_chain,
        mode=ReplayMode.SEMANTIC_REPLAY,
    )

    assert not report.equivalent
    assert any(item.scope == required_scope for item in report.differences)
    assert all(item.code != "BOOLEAN_REPLAY_MISMATCH" for item in report.differences)


def test_event_order_state_and_commit_receipt_lineage_are_semantic() -> None:
    expected_manifest, expected_chain = _replay(_standard_drafts())
    observed_manifest, observed_chain = _replay(
        _standard_drafts(
            event_order=("event:slip", "event:contact"),
            commit_receipt_id="receipt:case:a:DIFFERENT",
        )
    )
    report = verify_m02_replay(
        expected_manifest,
        expected_chain,
        observed_manifest,
        observed_chain,
        mode=ReplayMode.SEMANTIC_REPLAY,
    )

    assert not report.equivalent
    scopes = {item.scope for item in report.differences}
    assert any("payload.event_order" in scope for scope in scopes)
    assert any(scope.endswith("payload.commit_receipt_id") for scope in scopes)


def test_diagnostic_retention_level_cannot_change_semantic_result() -> None:
    expected_manifest, expected_chain = _replay(
        _standard_drafts(), diagnostic_level=DiagnosticLevel.COMPACT
    )
    observed_manifest, observed_chain = _replay(
        _standard_drafts(), diagnostic_level=DiagnosticLevel.FULL
    )
    semantic = verify_m02_replay(
        expected_manifest,
        expected_chain,
        observed_manifest,
        observed_chain,
        mode=ReplayMode.SEMANTIC_REPLAY,
    )
    bitwise = verify_m02_replay(
        expected_manifest,
        expected_chain,
        observed_manifest,
        observed_chain,
        mode=ReplayMode.BITWISE_REPLAY,
    )

    assert semantic.equivalent
    assert semantic.ignored_differences
    assert not bitwise.equivalent
    assert any(item.scope.endswith("diagnostic_level") for item in bitwise.differences)


def test_manifest_rejects_backend_profile_not_used_by_decision_records() -> None:
    chain = build_replay_decision_chain(_standard_drafts())
    with pytest.raises(ContractViolation, match="different backend profiles"):
        make_m02_replay_manifest(
            _base_manifest(),
            chain,
            resolved_numerics_config_hash=semantic_hash("m02-config:v1"),
            owner_contract_hashes={"owner:a": semantic_hash("owner:a:v1")},
            backend_profile_hash=semantic_hash("incompatible-profile"),
        )


def test_unexplained_input_or_output_hash_change_is_a_semantic_mismatch() -> None:
    drafts = _standard_drafts()
    expected_manifest, expected_chain = _replay(drafts)
    changed = dataclasses.replace(
        drafts[0],
        input_hash=semantic_hash("changed-input-with-identical-fields"),
        output_hash=semantic_hash("changed-output-with-identical-fields"),
    )
    observed_drafts = [changed, *drafts[1:]]
    observed_manifest, observed_chain = _replay(observed_drafts)

    report = verify_m02_replay(
        expected_manifest,
        expected_chain,
        observed_manifest,
        observed_chain,
        mode=ReplayMode.SEMANTIC_REPLAY,
    )

    assert not report.equivalent
    codes = {item.code for item in report.differences}
    assert "DECISION_INPUT_HASH_MISMATCH" in codes
    assert "UNEXPLAINED_DECISION_OUTPUT_HASH_MISMATCH" in codes


def test_draft_rejects_non_integer_logical_order() -> None:
    draft = _standard_drafts()[0]
    with pytest.raises(ContractViolation, match="logical_step_index"):
        dataclasses.replace(draft, logical_step_index=0.5)  # type: ignore[arg-type]
