"""Generate the canonical M02 VALIDATION_ONLY result bundle.

The fixture exercises numerical orchestration, replay, M00 transactions, and
the M02 result extension with a cheap deterministic synthetic owner.  It has
no contact, friction, beam, spring, material, damage, needle, or array physics
and is explicitly not certifiable.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import platform
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from spine_sim.foundation.canonical import semantic_hash, source_file_hash, stable_content_id
from spine_sim.foundation.config import (
    ConfigField,
    ConfigLayer,
    ConfigLayerLevel,
    ConfigSchema,
    ParameterOwnership,
    ResolvedConfig,
    resolve_config,
)
from spine_sim.foundation.integrity import VerifyMode, verify_bundle
from spine_sim.foundation.models import (
    AcceptedPointBase,
    AttemptOutcome,
    AuthorityRef,
    CapabilityStatus,
    CertificationStatus,
    CommittedEventBase,
    Maturity,
    PhysicalFeasibility,
    RecordBase,
    RejectedTrialBase,
    SourceIdentity,
    StatusTuple,
    ValuePresence,
    ValueProvenance,
)
from spine_sim.foundation.reader import JoinSpec, ResultReader
from spine_sim.foundation.registry import (
    BUNDLE_SCHEMA_VERSION,
    RESULT_API_VERSION,
    SchemaRegistry,
)
from spine_sim.foundation.replay import ReplayManifest, ReplayMode, make_replay_manifest
from spine_sim.foundation.writer import ResultWriter, make_run_envelope

from .contracts import DiagnosticLevel, FailureFamily, M02ReasonCode
from .plot_recipes import m02_plot_recipes
from .replay import (
    M02_CANONICAL_REDUCTION_ORDER,
    M02_FLOATING_POINT_PROFILE,
    M02_THREAD_POLICY,
    M02ReplayDecisionChain,
    M02ReplayManifest,
    ReplayDecisionDraft,
    ReplayDecisionKind,
    build_replay_decision_chain,
    make_m02_replay_manifest,
)
from .result_extension import (
    ACCEPTED_STEP_NUMERICS_DATASET,
    CASCADE_ROUNDS_DATASET,
    EVENT_BRACKETS_DATASET,
    EVENT_DEPENDENCIES_DATASET,
    ITERATION_TRACES_DATASET,
    M01_COMPATIBILITY_RESULTS_DATASET,
    REFINEMENT_STUDIES_DATASET,
    REJECTED_EVENT_BRACKETS_DATASET,
    REJECTED_ITERATION_TRACES_DATASET,
    REJECTED_TRIAL_DIAGNOSTICS_DATASET,
    REPLAY_STEPS_DATASET,
    RESIDUAL_BLOCK_SUMMARIES_DATASET,
    SIMULTANEOUS_EVENT_GROUPS_DATASET,
    TRANSACTION_TRACE_DATASET,
    AcceptedStepNumericsRecord,
    CascadeRoundRecord,
    ContinuationAttemptRecord,
    EventBracketRecord,
    EventDependencyRecord,
    EventProbeRecord,
    FailureDiagnosticRecord,
    IterationTraceRecord,
    M01CompatibilityResultRecord,
    RefinementStudyRecord,
    RejectedEventBracketRecord,
    RejectedIterationTraceRecord,
    RejectedTrialDiagnosticRecord,
    ReplayStepRecord,
    ResidualBlockSummaryRecord,
    SimultaneousEventGroupRecord,
    TransactionTraceRecord,
    m02_result_extension,
)

DEFAULT_BUNDLE_PATH = Path("build/m02")
DEMO_BACKEND = "M02_DETERMINISTIC_SYNTHETIC_FLOAT64"
DEMO_OWNER_ID = "owner:m02-validation-linear-scalar"
DEMO_DESIGN_ID = stable_content_id("design", {"fixture": "M02_VALIDATION_ONLY"})
DEMO_SEED_ID = stable_content_id("seed", {"fixture": "M02_VALIDATION_ONLY", "rng": "NONE"})
DEMO_SURFACE_ID = stable_content_id(
    "surface", {"fixture": "M02_VALIDATION_ONLY", "surface": "NO_M01_QUERY_REQUIRED"}
)
DEMO_CASE_ID = stable_content_id(
    "case",
    {
        "design_id": DEMO_DESIGN_ID,
        "seed_id": DEMO_SEED_ID,
        "surface_realization_id": DEMO_SURFACE_ID,
    },
)
DEMO_TARGET_ID = stable_content_id("m02-target", {"case_id": DEMO_CASE_ID, "target": 1.0})
DEMO_POINT_ID = stable_content_id("point", {"case_id": DEMO_CASE_ID, "index": 0})
DEMO_EVENT_ID = stable_content_id(
    "event", {"case_id": DEMO_CASE_ID, "kind": "VALIDATION_ZERO_CROSSING"}
)
DEMO_PARENT_EVENT_ID = stable_content_id(
    "event", {"case_id": DEMO_CASE_ID, "kind": "VALIDATION_DEPENDENCY_PARENT"}
)
DEMO_GROUP_ID = stable_content_id("simultaneous-group", {"events": [DEMO_EVENT_ID]})
DEMO_REPLAY_STEP_ID = stable_content_id(
    "m02-replay-step", {"case_id": DEMO_CASE_ID, "point_id": DEMO_POINT_ID}
)
DEMO_TRIAL_ID = stable_content_id(
    "trial", {"case_id": DEMO_CASE_ID, "kind": "INTENTIONAL_NUMERICAL_REJECTION"}
)
DEMO_IDEMPOTENCY_KEY = "M02_VALIDATION_ONLY_ACCEPTED_EVENT_TX_1"


def _config_schema() -> ConfigSchema:
    return ConfigSchema(
        "M02_VALIDATION_ONLY_CONFIG",
        "1.0.0",
        (
            ConfigField(
                "foundation.canonical_numeric_dtype",
                str,
                ParameterOwnership.NUMERICAL_CONFIGURATION,
                "M00_FOUNDATION_REQUIREMENTS 1.0.0 §3.2",
                SourceIdentity.ACCEPTED_AUTHORITY,
                locked=True,
                enum_values=("float64",),
            ),
            ConfigField(
                "m02_validation.synthetic_owner_scale",
                float,
                ParameterOwnership.NUMERICAL_CONFIGURATION,
                "M02_NUMERICS_REQUIREMENTS 1.0.0 §18.7",
                SourceIdentity.VALIDATION_ONLY,
                dimension="dimensionless",
                minimum=0.0,
            ),
        ),
    )


def _resolved_config(kind: str) -> ResolvedConfig:
    authority = ConfigLayer(
        ConfigLayerLevel.L1_AUTHORITY,
        "M02_VALIDATION_ONLY:inline-authority",
        semantic_hash("float64"),
        {"foundation": {"canonical_numeric_dtype": "float64"}},
        SourceIdentity.ACCEPTED_AUTHORITY,
    )
    validation = ConfigLayer(
        ConfigLayerLevel.L2_ISOLATED,
        "M02_VALIDATION_ONLY:inline-synthetic-owner",
        semantic_hash({"synthetic_owner_scale": 1.0}),
        {"m02_validation": {"synthetic_owner_scale": {"value": 1.0, "unit": "1"}}},
        SourceIdentity.VALIDATION_ONLY,
        "m02_validation",
    )
    return resolve_config(
        _config_schema(),
        (authority, validation),
        config_kind=kind,
    )


def _status(
    *,
    outcome: AttemptOutcome = AttemptOutcome.ACCEPTED,
    value_presence: ValuePresence = ValuePresence.PRESENT,
    reason_code: str = "M02_VALIDATION_ONLY",
    explanation: str = "synthetic numerical protocol evidence; no physical interpretation",
    last_valid_state_id: str | None = None,
) -> StatusTuple:
    return StatusTuple(
        value_presence,
        CapabilityStatus.SUPPORTED,
        outcome,
        PhysicalFeasibility.NOT_ASSESSED,
        CertificationStatus.NOT_CERTIFIABLE,
        reason_code,
        explanation,
        ("M02_NUMERICS_REQUIREMENTS 1.0.0",),
        last_valid_state_id,
    )


def _record_common(run_id: str, status: StatusTuple | None = None) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "case_id": DEMO_CASE_ID,
        "schema_version": "1.0.0",
        "status": status or _status(),
        "source_identity": SourceIdentity.DEV_POLICY,
        "maturity": Maturity.validation_only_implemented(),
        "certification_status": CertificationStatus.NOT_CERTIFIABLE,
    }


def _source_hashes(repo_root: Path) -> dict[str, str]:
    paths = (
        repo_root / "docs/simulator_development/requirements/M00_FOUNDATION_REQUIREMENTS.md",
        repo_root / "docs/simulator_development/requirements/M02_NUMERICS_REQUIREMENTS.md",
        repo_root / "theory/system/SYSTEM_INTEGRATED_MODEL.md",
    )
    return {path.relative_to(repo_root).as_posix(): source_file_hash(path) for path in paths}


def _git_state(repo_root: Path) -> tuple[str, str]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
        ).strip()
        dirty = (
            "dirty"
            if subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=repo_root, text=True
            ).strip()
            else "clean"
        )
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE", "UNAVAILABLE"
    return commit, dirty


def _backend_profile_hash() -> str:
    return semantic_hash(
        {
            "numerical_backend": DEMO_BACKEND,
            "canonical_reduction_order": M02_CANONICAL_REDUCTION_ORDER,
            "thread_policy": M02_THREAD_POLICY,
            "floating_point_profile": M02_FLOATING_POINT_PROFILE,
        }
    )


def _decision_chain(parent_state_id: str) -> M02ReplayDecisionChain:
    profile = _backend_profile_hash()
    target_payload = {
        "target_id": DEMO_TARGET_ID,
        "parent_accepted_state_id": parent_state_id,
        "target_value": 1.0,
        "coordinate_unit": "1",
        "synthetic_owner_id": DEMO_OWNER_ID,
    }
    commit_payload = {
        "point_id": DEMO_POINT_ID,
        "event_order": [DEMO_EVENT_ID],
        "committed_state_id": stable_content_id(
            "state", {"case_id": DEMO_CASE_ID, "accepted_index": 0}
        ),
        "owner_response_hash": semantic_hash("linear-scalar-response:zero-crossing"),
        "ordered_intents_hash": semantic_hash((DEMO_OWNER_ID, "accept", "event")),
    }
    return build_replay_decision_chain(
        (
            ReplayDecisionDraft(
                case_id=DEMO_CASE_ID,
                target_id=DEMO_TARGET_ID,
                decision_kind=ReplayDecisionKind.TARGET,
                logical_step_index=0,
                input_hash=semantic_hash((parent_state_id, DEMO_TARGET_ID)),
                output_hash=semantic_hash(target_payload),
                backend_profile_hash=profile,
                payload=target_payload,
            ),
            ReplayDecisionDraft(
                case_id=DEMO_CASE_ID,
                target_id=DEMO_TARGET_ID,
                trial_id="trial:m02-validation-accepted",
                decision_kind=ReplayDecisionKind.COMMIT,
                logical_step_index=1,
                input_hash=semantic_hash((parent_state_id, "trial:m02-validation-accepted")),
                output_hash=semantic_hash(commit_payload),
                backend_profile_hash=profile,
                owner_id=DEMO_OWNER_ID,
                payload=commit_payload,
                diagnostics={"worker_id": "validation-main-thread", "m01_cache_status": "unused"},
            ),
        ),
        diagnostic_level=DiagnosticLevel.STANDARD,
    )


def _replay_manifest(
    envelope_run_id: str,
    run_fingerprint: str,
    resolved_run: ResolvedConfig,
    resolved_case: ResolvedConfig,
    registry_hash: str,
    source_hashes: dict[str, str],
    git_commit: str,
    dirty_status: str,
    chain: M02ReplayDecisionChain,
) -> M02ReplayManifest:
    base: ReplayManifest = make_replay_manifest(
        run_id=envelope_run_id,
        run_fingerprint=run_fingerprint,
        result_api_version=RESULT_API_VERSION,
        bundle_schema_version=BUNDLE_SCHEMA_VERSION,
        resolved_run_config_hash=resolved_run.semantic_hash,
        resolved_case_config_hashes={DEMO_CASE_ID: resolved_case.semantic_hash},
        source_hashes=source_hashes,
        registry_hash=registry_hash,
        git_commit=git_commit,
        dirty_status=dirty_status,
        case_execution_plan=(DEMO_CASE_ID,),
        idempotency_keys=(DEMO_IDEMPOTENCY_KEY,),
        surface_identities=(DEMO_SURFACE_ID,),
        field_tolerances={"final_merit": 1.0e-12, "path_coordinate": 1.0e-12},
    )
    base = dataclasses.replace(
        base,
        solver_build_id="M02_VALIDATION_ONLY_SYNTHETIC_OWNER",
        model_contract_versions=(
            *base.model_contract_versions,
            "M02_NUMERICS_REQUIREMENTS 1.0.0",
        ),
        numerical_backend=DEMO_BACKEND,
        thread_and_float_settings={
            "canonical_numeric_dtype": "float64",
            "canonical_reduction_order": M02_CANONICAL_REDUCTION_ORDER,
            "thread_policy": M02_THREAD_POLICY,
            "runtime_thread_count": 1,
            "floating_point_profile": M02_FLOATING_POINT_PROFILE,
        },
        diagnostic_level=DiagnosticLevel.STANDARD.value,
    )
    return make_m02_replay_manifest(
        base,
        chain,
        resolved_numerics_config_hash=resolved_run.semantic_hash,
        owner_contract_hashes={DEMO_OWNER_ID: semantic_hash("M02_SYNTHETIC_OWNER_CONTRACT_1.0.0")},
        backend_profile_hash=_backend_profile_hash(),
        diagnostic_level=DiagnosticLevel.STANDARD,
    )


def _authority_refs(source_hashes: dict[str, str]) -> tuple[AuthorityRef, ...]:
    return tuple(
        AuthorityRef(path, "frozen/current", digest, "whole-file")
        for path, digest in sorted(source_hashes.items())
    )


def _accepted_point(
    run_id: str,
    parent_state_id: str,
    accepted_state_id: str,
    source_hashes: dict[str, str],
    chain: M02ReplayDecisionChain,
) -> AcceptedPointBase:
    return AcceptedPointBase(
        run_id=run_id,
        case_id=DEMO_CASE_ID,
        design_id=DEMO_DESIGN_ID,
        seed_id=DEMO_SEED_ID,
        surface_realization_id=DEMO_SURFACE_ID,
        point_id=DEMO_POINT_ID,
        accepted_point_index=0,
        accepted_state_id=accepted_state_id,
        parent_state_id=parent_state_id,
        commit_receipt_id=None,
        operation_kind="M02_VALIDATION_ONLY",
        stage="SYNTHETIC_ZERO_CROSSING",
        path_kind="MONOTONE_SCALAR_TARGET",
        path_coordinate=1.0,
        path_unit="1",
        accepted_increment=1.0,
        physical_time_value=0.0,
        physical_time_status=StatusTuple(
            ValuePresence.PRESENT,
            CapabilityStatus.SUPPORTED,
            AttemptOutcome.ACCEPTED,
            PhysicalFeasibility.NOT_ASSESSED,
            CertificationStatus.NOT_CERTIFIABLE,
            "VALIDATION_ONLY_SYNTHETIC_CLOCK",
            "zero-valued protocol clock; it has no physical interpretation",
        ),
        event_sequence=1,
        simultaneous_group_ids=(DEMO_GROUP_ID,),
        cascade_ids=(),
        module_payload_refs=(f"{ACCEPTED_STEP_NUMERICS_DATASET}:{DEMO_POINT_ID}",),
        residual_refs=(),
        graph_refs=(),
        quality_refs=("m02-validation-hard-quality:passed",),
        work_ledger_refs=(),
        source_identity=SourceIdentity.VALIDATION_ONLY,
        requirement_origin="M02_NUMERICS_REQUIREMENTS 1.0.0 §13-14",
        value_provenance=(
            ValueProvenance(
                DEMO_OWNER_ID,
                semantic_hash("M02_SYNTHETIC_OWNER_CONTRACT_1.0.0"),
                "path_coordinate",
                SourceIdentity.VALIDATION_ONLY,
            ),
        ),
        authority_refs=_authority_refs(source_hashes),
        maturity=Maturity.validation_only_implemented(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        request_hash=semantic_hash((DEMO_TARGET_ID, parent_state_id)),
        response_hash=semantic_hash((DEMO_POINT_ID, accepted_state_id, DEMO_EVENT_ID)),
        replay_step_hash=chain.records[-1].metadata.semantic_hash,
    )


def _committed_event(
    run_id: str,
    parent_state_id: str,
    accepted_state_id: str,
) -> CommittedEventBase:
    return CommittedEventBase(
        event_id=DEMO_EVENT_ID,
        source_event_ids=("synthetic-owner:zero-crossing",),
        hierarchy="VALIDATION_ONLY",
        entity_ids=(DEMO_OWNER_ID,),
        run_id=run_id,
        case_id=DEMO_CASE_ID,
        design_id=DEMO_DESIGN_ID,
        seed_id=DEMO_SEED_ID,
        surface_realization_id=DEMO_SURFACE_ID,
        # The token exercises the future M6 release/recontact filter only.  No
        # release mechanics or physical return path is evaluated here.
        event_kind="RELEASE",
        raw_event_function=0.0,
        event_function_unit="1",
        numerical_scaling_id="M02_VALIDATION_UNIT_SCALE",
        path_coordinate=1.0,
        path_bracket=(0.5, 1.0),
        fraction_basis="MONOTONE_SCALAR_TARGET",
        localization_error=0.0,
        pre_event_accepted_state_id=parent_state_id,
        event_point_trial_id="trial:m02-validation-accepted",
        post_event_accepted_state_id=accepted_state_id,
        post_event_status=_status(),
        simultaneous_group_id=DEMO_GROUP_ID,
        dependency_edges=(),
        cascade_round=0,
        pre_payload_refs=("synthetic-owner:pre",),
        event_payload_refs=("synthetic-owner:event",),
        post_payload_refs=("synthetic-owner:post",),
        uncertainty_refs=(),
        recoverability="NOT_APPLICABLE_VALIDATION_ONLY",
        stability="NOT_ASSESSED_VALIDATION_ONLY",
        terminal_classification="NON_TERMINAL_VALIDATION_EVENT",
        status=_status(),
        source_identity=SourceIdentity.VALIDATION_ONLY,
        maturity=Maturity.validation_only_implemented(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        committed=True,
        commit_receipt_id=None,
    )


def _dependency_parent_event(event: CommittedEventBase) -> CommittedEventBase:
    return dataclasses.replace(
        event,
        event_id=DEMO_PARENT_EVENT_ID,
        source_event_ids=("synthetic-owner:dependency-parent",),
        event_kind="CONTACT_ESTABLISHED",
        raw_event_function=-0.0,
        event_point_trial_id="trial:m02-validation-dependency-parent",
        event_payload_refs=("synthetic-owner:dependency-parent",),
    )


def _accepted_extension_records(
    run_id: str,
    accepted_state_id: str,
    parent_state_id: str,
    event: CommittedEventBase,
    parent_event: CommittedEventBase,
    replay: M02ReplayManifest,
    chain: M02ReplayDecisionChain,
) -> tuple[
    AcceptedStepNumericsRecord,
    ResidualBlockSummaryRecord,
    IterationTraceRecord,
    EventBracketRecord,
    SimultaneousEventGroupRecord,
    EventDependencyRecord,
    CascadeRoundRecord,
    TransactionTraceRecord,
    ReplayStepRecord,
]:
    common = _record_common(run_id)
    accepted = AcceptedStepNumericsRecord(
        **common,
        numerics_record_id=stable_content_id("m02-accepted-numerics", DEMO_POINT_ID),
        point_id=DEMO_POINT_ID,
        accepted_state_id=accepted_state_id,
        commit_receipt_id=None,
        target_id=DEMO_TARGET_ID,
        trial_request_hash=semantic_hash("trial:m02-validation-accepted"),
        accepted_point_index=0,
        attempted_coordinate=1.0,
        accepted_coordinate=1.0,
        coordinate_unit="1",
        requested_step=1.0,
        accepted_step=1.0,
        step_reason="VALIDATION_ONLY_INITIAL_STEP",
        retry_count=0,
        newton_iterations=1,
        backtrack_count=0,
        difficulty="EASY_VALIDATION_ONLY",
        final_merit=0.0,
        event_id=event.event_id,
        replay_step_id=DEMO_REPLAY_STEP_ID,
        resolved_config_hash=replay.m02_extension.resolved_numerics_config_hash,
    )
    residual = ResidualBlockSummaryRecord(
        **common,
        residual_summary_id=stable_content_id("m02-residual-summary", DEMO_POINT_ID),
        point_id=DEMO_POINT_ID,
        commit_receipt_id=None,
        trial_request_hash=semantic_hash("trial:m02-validation-accepted"),
        iteration=0,
        block_id="synthetic_scalar_balance",
        owner_module_id=DEMO_OWNER_ID,
        block_semantics="VALIDATION_ONLY scalar residual",
        raw_norm=0.0,
        raw_unit="1",
        reference_norm=1.0,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        scale_id="M02_VALIDATION_UNIT_SCALE",
        tolerance=2.0e-12,
        normalized_norm=0.0,
        merit=0.0,
        hard=True,
        passed=True,
    )
    iteration = IterationTraceRecord(
        **common,
        trace_id=stable_content_id("m02-iteration-trace", DEMO_POINT_ID),
        trial_id=None,
        point_id=DEMO_POINT_ID,
        commit_receipt_id=None,
        trial_request_hash=semantic_hash("trial:m02-validation-accepted"),
        iteration=0,
        block_id="synthetic_scalar_balance",
        raw_norm=0.0,
        raw_unit="1",
        tolerance=2.0e-12,
        normalized_norm=0.0,
        merit=0.0,
        linear_residual=0.0,
        line_search_factor=1.0,
        algorithm_id="VALIDATION_ONLY_DAMPED_NEWTON",
        backtrack_count=0,
        owner_response_hash=semantic_hash((DEMO_POINT_ID, "accepted-owner-response")),
        outcome="ACCEPTED_FINAL",
        accepted_state_advanced=True,
    )
    bracket = EventBracketRecord(
        **common,
        bracket_id=stable_content_id("m02-event-bracket", event.event_id),
        trial_id=None,
        channel_id="synthetic-owner:zero-crossing",
        left_coordinate=0.5,
        right_coordinate=1.0,
        coordinate_unit="1",
        left_raw_guard=-0.5,
        right_raw_guard=0.0,
        raw_guard_unit="1",
        root_coordinate=1.0,
        root_method="BISECTION",
        root_solver_level=1,
        root_iterations=1,
        position_tolerance=0.01,
        localization_error=0.0,
        direction="RISING",
        simultaneous_tolerance=0.01,
        coverage_certificate_id="coverage:m02-validation-only",
        event_id=event.event_id,
        commit_receipt_id=None,
        final_bracket=True,
        accepted_state_advanced=False,
    )
    event_group = SimultaneousEventGroupRecord(
        **common,
        simultaneous_group_id=DEMO_GROUP_ID,
        event_id=event.event_id,
        point_id=DEMO_POINT_ID,
        commit_receipt_id=None,
        event_kind=event.event_kind,
        channel_id="synthetic-owner:zero-crossing",
        path_coordinate=1.0,
        coordinate_unit="1",
        simultaneous_tolerance=0.01,
        dependency_layer=0,
        group_hash=semantic_hash((DEMO_GROUP_ID, event.event_id)),
    )
    dependency = EventDependencyRecord(
        **common,
        dependency_record_id=stable_content_id(
            "m02-event-dependency", (event.event_id, parent_event.event_id)
        ),
        event_id=event.event_id,
        depends_on_event_id=parent_event.event_id,
        simultaneous_group_id=DEMO_GROUP_ID,
        dependency_kind="VALIDATION_ONLY_DAG_EDGE",
        topological_layer=1,
        commit_receipt_id=None,
    )
    cascade = CascadeRoundRecord(
        **common,
        cascade_record_id=stable_content_id("m02-cascade-round", (event.event_id, 0)),
        cascade_id="cascade:m02-validation-only",
        event_id=event.event_id,
        point_id=DEMO_POINT_ID,
        commit_receipt_id=None,
        round_index=0,
        state_hash=semantic_hash((accepted_state_id, "cascade-round-0")),
        event_signature_hash=semantic_hash((parent_event.event_id, event.event_id)),
        residual_margin=1.0,
        zero_progress_intent_count=0,
        zeno_candidate=False,
    )
    transaction = TransactionTraceRecord(
        **common,
        transaction_trace_id=stable_content_id("m02-transaction-trace", DEMO_POINT_ID),
        transaction_id="transaction:m02-validation-accepted",
        point_id=DEMO_POINT_ID,
        event_id=event.event_id,
        trial_id=None,
        parent_accepted_state_id=parent_state_id,
        candidate_hash=semantic_hash("m02-validation-frozen-candidate"),
        phase="PREPARED",
        ordered_intents_hash=semantic_hash((DEMO_OWNER_ID, "accept", "event")),
        prepare_token_ref="prepare:m02-validation",
        commit_receipt_id=None,
        rollback_token_ref="rollback:m02-validation",
        read_set_hash=semantic_hash((parent_state_id,)),
        write_set_hash=semantic_hash((accepted_state_id, event.event_id)),
        idempotency_key=DEMO_IDEMPOTENCY_KEY,
        outcome="PREPARED_FOR_M00_ATOMIC_COMMIT",
        fault_stage=None,
        accepted_state_advanced=False,
    )
    replay_step = ReplayStepRecord(
        **common,
        replay_step_id=DEMO_REPLAY_STEP_ID,
        target_id=DEMO_TARGET_ID,
        point_id=DEMO_POINT_ID,
        event_id=event.event_id,
        trial_id=None,
        commit_receipt_id=None,
        decision_index=chain.records[-1].sequence_index,
        decision_kind=chain.records[-1].decision_kind,
        decision_hash=chain.records[-1].metadata.semantic_hash,
        replay_mode=ReplayMode.BITWISE_REPLAY.value,
        backend_id=DEMO_BACKEND,
        operation_profile_id=replay.m02_extension.backend_profile_hash,
        resolved_config_hash=replay.m02_extension.resolved_numerics_config_hash,
        owner_contract_hash=dict(replay.m02_extension.owner_contract_hashes)[DEMO_OWNER_ID],
        canonical_reduction_hash=semantic_hash(M02_CANONICAL_REDUCTION_ORDER),
        thread_settings_hash=semantic_hash(M02_THREAD_POLICY),
        expected_semantic_hash=chain.semantic_hash,
        observed_semantic_hash=chain.semantic_hash,
        matched=True,
    )
    return (
        accepted,
        residual,
        iteration,
        bracket,
        event_group,
        dependency,
        cascade,
        transaction,
        replay_step,
    )


def _rejected_records(
    run_id: str,
    accepted_state_id: str,
) -> tuple[RejectedTrialBase, tuple[RecordBase, ...]]:
    request_hash = semantic_hash((DEMO_TRIAL_ID, accepted_state_id, "request"))
    candidate_hash = semantic_hash((DEMO_TRIAL_ID, "nonconverged-candidate"))
    status = _status(
        outcome=AttemptOutcome.NUMERICAL_FAILURE,
        value_presence=ValuePresence.NULL,
        reason_code=M02ReasonCode.NONLINEAR_NONCONVERGENCE.value,
        explanation="intentional synthetic numerical rejection; physical feasibility not assessed",
        last_valid_state_id=accepted_state_id,
    )
    core = RejectedTrialBase(
        trial_id=DEMO_TRIAL_ID,
        run_id=run_id,
        case_id=DEMO_CASE_ID,
        parent_accepted_state_id=accepted_state_id,
        request_hash=request_hash,
        candidate_hash=candidate_hash,
        requested_path_target=2.0,
        status=status,
        reason_codes=(M02ReasonCode.NONLINEAR_NONCONVERGENCE.value,),
        diagnostic_summary=(
            "VALIDATION_ONLY intentional nonlinear failure; no accepted state/event/receipt"
        ),
        optional_full_payload_ref=None,
        last_valid_state_id=accepted_state_id,
        source_identity=SourceIdentity.VALIDATION_ONLY,
    )
    detail = RejectedTrialDiagnosticRecord(
        **_record_common(run_id, status),
        diagnostic_id=stable_content_id("m02-rejected-diagnostic", DEMO_TRIAL_ID),
        trial_id=DEMO_TRIAL_ID,
        parent_accepted_state_id=accepted_state_id,
        request_hash=request_hash,
        candidate_hash=candidate_hash,
        failure_family=FailureFamily.NUMERICAL_FAILURE.value,
        reason_code=M02ReasonCode.NONLINEAR_NONCONVERGENCE.value,
        failure_stage="VALIDATION_ONLY_SYNTHETIC_NEWTON",
        attempt_index=1,
        retry_index=0,
        requested_path_target=2.0,
        coordinate_unit="1",
        last_valid_state_id=accepted_state_id,
        diagnostic_level=DiagnosticLevel.STANDARD.value,
        full_payload_ref=None,
        retryable=True,
        next_requested_step=0.5,
        accepted_state_advanced=False,
        commit_receipt_id=None,
    )
    attempt = ContinuationAttemptRecord(
        **_record_common(run_id, status),
        attempt_id=stable_content_id("m02-continuation-attempt", DEMO_TRIAL_ID),
        target_id=DEMO_TARGET_ID,
        trial_id=DEMO_TRIAL_ID,
        parent_accepted_state_id=accepted_state_id,
        attempt_index=1,
        retry_index=0,
        trial_phase="TARGET_PROBE",
        attempted_coordinate=2.0,
        coordinate_unit="1",
        requested_step=1.0,
        growth_shrink_reason="VALIDATION_ONLY_NUMERICAL_RETRY",
        event_marker_id=None,
        newton_iterations=50,
        backtrack_count=20,
        outcome="NUMERICAL_FAILURE",
        accepted_state_advanced=False,
        commit_receipt_id=None,
    )
    iteration = RejectedIterationTraceRecord(
        **_record_common(run_id, status),
        trace_id=stable_content_id("m02-rejected-iteration-trace", DEMO_TRIAL_ID),
        trial_id=DEMO_TRIAL_ID,
        point_id=None,
        commit_receipt_id=None,
        trial_request_hash=request_hash,
        iteration=49,
        block_id="synthetic_scalar_balance",
        raw_norm=1.0,
        raw_unit="1",
        tolerance=1.0e-12,
        normalized_norm=1.0,
        merit=1.0,
        linear_residual=1.0,
        line_search_factor=2.0**-20,
        algorithm_id="VALIDATION_ONLY_DAMPED_NEWTON",
        backtrack_count=20,
        owner_response_hash=semantic_hash((DEMO_TRIAL_ID, "owner-response")),
        outcome="NONCONVERGED",
        accepted_state_advanced=False,
    )
    probe = EventProbeRecord(
        **_record_common(run_id, status),
        probe_id=stable_content_id("m02-event-probe", DEMO_TRIAL_ID),
        trial_id=DEMO_TRIAL_ID,
        channel_id="synthetic-owner:release-recontact-channel",
        path_coordinate=1.5,
        coordinate_unit="1",
        raw_guard=0.5,
        raw_guard_unit="1",
        equilibrium_quality=0.0,
        equilibrium_passed=True,
        owner_response_hash=semantic_hash((DEMO_TRIAL_ID, "balanced-probe")),
        coverage_certificate_id="coverage:m02-validation-only",
        valid_bracket=True,
        release_pose_ref="pose:m02-validation-release",
        path_mode="HOLD_AT_RELEASE_POSE",
        pre_accepted_state_id=accepted_state_id,
        post_accepted_state_id=None,
        event_id=DEMO_EVENT_ID,
        commit_receipt_id=None,
        accepted_state_advanced=False,
    )
    bracket = RejectedEventBracketRecord(
        **_record_common(run_id, status),
        bracket_id=stable_content_id("m02-rejected-event-bracket", DEMO_TRIAL_ID),
        trial_id=DEMO_TRIAL_ID,
        channel_id="synthetic-owner:release-recontact-channel",
        left_coordinate=1.0,
        right_coordinate=1.5,
        coordinate_unit="1",
        left_raw_guard=-0.5,
        right_raw_guard=0.5,
        raw_guard_unit="1",
        root_coordinate=1.25,
        root_method="BISECTION",
        root_solver_level=1,
        root_iterations=1,
        position_tolerance=0.01,
        localization_error=0.0,
        direction="RISING",
        simultaneous_tolerance=0.01,
        coverage_certificate_id="coverage:m02-validation-only",
        event_id=None,
        commit_receipt_id=None,
        final_bracket=True,
        accepted_state_advanced=False,
    )
    failure = FailureDiagnosticRecord(
        **_record_common(run_id, status),
        failure_diagnostic_id=stable_content_id("m02-failure-diagnostic", DEMO_TRIAL_ID),
        trial_id=DEMO_TRIAL_ID,
        parent_accepted_state_id=accepted_state_id,
        last_valid_state_id=accepted_state_id,
        failure_family=FailureFamily.NUMERICAL_FAILURE.value,
        reason_code=M02ReasonCode.NONLINEAR_NONCONVERGENCE.value,
        failure_stage="VALIDATION_ONLY_SYNTHETIC_NEWTON",
        capability_status=CapabilityStatus.SUPPORTED.value,
        owner_proof_ref=None,
        design_id=DEMO_DESIGN_ID,
        surface_realization_id=DEMO_SURFACE_ID,
        footprint_id="footprint:NOT_APPLICABLE_NO_M01_QUERY",
        path_coordinate=2.0,
        coordinate_unit="1",
        wall_time_s=0.0,
        runtime_cost_units=1.0,
        diagnostic_level=DiagnosticLevel.STANDARD.value,
        denominator_scope="ONE_VALIDATION_ONLY_TRIAL",
        includes_capability_unavailable=False,
        full_trace_ref=None,
        accepted_state_advanced=False,
        commit_receipt_id=None,
    )
    return core, (detail, attempt, iteration, probe, bracket, failure)


def _refinement_record(run_id: str) -> RefinementStudyRecord:
    common = _record_common(run_id)
    common["source_identity"] = SourceIdentity.VALIDATION_ONLY
    return RefinementStudyRecord(
        **common,
        study_id="study:m02-validation-only-refinement",
        sample_id="sample:h-over-2",
        point_id=DEMO_POINT_ID,
        event_id=DEMO_EVENT_ID,
        step_size=0.5,
        event_tolerance=0.01,
        coordinate_unit="1",
        m01_lod=10,
        root_solver_level=1,
        event_position=1.0,
        force_summary_n=0.0,
        work_summary_n_mm=0.0,
        event_order_hash=semantic_hash((DEMO_EVENT_ID,)),
        event_position_error=0.0,
        force_relative_error=0.0,
        work_relative_error=0.0,
        observed_order=2.0,
        event_order_matched=True,
        passed=True,
    )


def _m01_compatibility_record(run_id: str) -> M01CompatibilityResultRecord:
    common = _record_common(run_id)
    common["source_identity"] = SourceIdentity.VALIDATION_ONLY
    return M01CompatibilityResultRecord(
        **common,
        compatibility_result_id="m01-compatibility:m02-validation-only",
        panel_id="M02_M01_SMOKE_4",
        scenario_id="scenario:m02-validation-only",
        design_id=DEMO_DESIGN_ID,
        geometry_fixture_id="NO_M01_QUERY_VALIDATION_FIXTURE",
        surface_realization_id=DEMO_SURFACE_ID,
        footprint_id="footprint:NOT_APPLICABLE_NO_M01_QUERY",
        path_length_mm=100.0,
        query_count=0,
        step_count=1,
        event_count=1,
        cache_mode="NOT_APPLICABLE_NO_M01_QUERY",
        diagnostic_level=DiagnosticLevel.STANDARD.value,
        m01_lod=10,
        witness_lod=10,
        event_position_error_mm=0.0,
        unique_support_error_mm=None,
        normal_error_deg=None,
        force_relative_error=None,
        work_relative_error=None,
        event_order_matched=True,
        reason_code="M02_VALIDATION_ONLY_NO_M01_QUERY",
        wall_time_s=0.0,
        peak_rss_bytes=0,
        artifact_size_bytes=0,
        passed=True,
    )


def _readback_validation(
    bundle: Path,
    *,
    receipt_id: str,
    accepted_state_id: str,
) -> dict[str, Any]:
    manifest_integrity = verify_bundle(bundle, VerifyMode.MANIFEST)
    full_integrity = verify_bundle(bundle, VerifyMode.FULL)
    manifest_reader = ResultReader.open(bundle, VerifyMode.MANIFEST)
    full_reader = ResultReader.open(bundle, VerifyMode.FULL)

    accepted_query = full_reader.query(
        ACCEPTED_STEP_NUMERICS_DATASET,
        ("numerics_record_id", "point_id", "accepted_state_id", "commit_receipt_id"),
        include_non_default=True,
    )
    accepted = accepted_query.read_all()
    if accepted.num_rows != 1 or accepted["commit_receipt_id"].to_pylist() != [receipt_id]:
        raise RuntimeError("M02 accepted-step readback lost its authoritative receipt")
    if accepted["accepted_state_id"].to_pylist() != [accepted_state_id]:
        raise RuntimeError("M02 accepted-step state lineage changed during storage")

    manifest_query = manifest_reader.query(
        ACCEPTED_STEP_NUMERICS_DATASET,
        ("numerics_record_id", "point_id", "accepted_state_id", "commit_receipt_id"),
        include_non_default=True,
    )
    manifest_rows = manifest_query.read_all()
    if manifest_rows.to_pylist() != accepted.to_pylist():
        raise RuntimeError("MANIFEST and FULL readers returned different accepted evidence")
    if manifest_query.manifest.result_hash != accepted_query.manifest.result_hash:
        raise RuntimeError("MANIFEST and FULL query semantic hashes differ")

    point_join = full_reader.query(
        ACCEPTED_STEP_NUMERICS_DATASET,
        ("numerics_record_id", "point_id"),
        joins=(JoinSpec("m02.relation.accepted_step_to_point"),),
        include_non_default=True,
    ).read_all()
    receipt_join = full_reader.query(
        ACCEPTED_STEP_NUMERICS_DATASET,
        ("numerics_record_id", "commit_receipt_id"),
        joins=(JoinSpec("m02.relation.accepted_step_to_receipt"),),
        include_non_default=True,
    ).read_all()
    if (
        point_join.num_rows != 1
        or point_join["accepted_state_id"].to_pylist() != [accepted_state_id]
        or receipt_join["idempotency_key"].to_pylist() != [DEMO_IDEMPOTENCY_KEY]
    ):
        raise RuntimeError("registered accepted-step relations did not resolve to M00 authorities")

    event_group = full_reader.query(
        SIMULTANEOUS_EVENT_GROUPS_DATASET,
        ("simultaneous_group_id", "event_id", "point_id", "commit_receipt_id"),
        joins=(JoinSpec("m02.relation.simultaneous_member_to_event"),),
        include_non_default=True,
    ).read_all()
    transaction = full_reader.query(
        TRANSACTION_TRACE_DATASET,
        ("transaction_trace_id", "commit_receipt_id", "accepted_state_advanced"),
        include_non_default=True,
    ).read_all()
    replay = full_reader.query(
        REPLAY_STEPS_DATASET,
        ("replay_step_id", "commit_receipt_id", "matched"),
        include_non_default=True,
    ).read_all()
    if event_group.num_rows != 1 or event_group["commit_receipt_id"].to_pylist() != [receipt_id]:
        raise RuntimeError("M02 event evidence was not atomically receipt-backed")
    if transaction["commit_receipt_id"].to_pylist() != [receipt_id]:
        raise RuntimeError("M02 transaction evidence was not atomically receipt-backed")
    if replay["commit_receipt_id"].to_pylist() != [receipt_id] or replay["matched"].to_pylist() != [
        True
    ]:
        raise RuntimeError("M02 replay evidence failed readback")

    for dataset_id in (
        RESIDUAL_BLOCK_SUMMARIES_DATASET,
        ITERATION_TRACES_DATASET,
        EVENT_BRACKETS_DATASET,
        EVENT_DEPENDENCIES_DATASET,
        CASCADE_ROUNDS_DATASET,
    ):
        receipt_rows = full_reader.query(
            dataset_id,
            ("commit_receipt_id",),
            include_non_default=True,
        ).read_all()
        if receipt_rows.num_rows != 1 or receipt_rows["commit_receipt_id"].to_pylist() != [
            receipt_id
        ]:
            raise RuntimeError(f"{dataset_id} was published without its M00 receipt")

    refinement = full_reader.query(
        REFINEMENT_STUDIES_DATASET,
        ("study_id", "sample_id", "passed"),
        include_non_default=True,
    ).read_all()
    compatibility = full_reader.query(
        M01_COMPATIBILITY_RESULTS_DATASET,
        ("compatibility_result_id", "panel_id", "passed"),
        include_non_default=True,
    ).read_all()
    if refinement.num_rows != 1 or refinement["passed"].to_pylist() != [True]:
        raise RuntimeError("M02 refinement summary failed direct writer/reader round trip")
    if compatibility.num_rows != 1 or compatibility["passed"].to_pylist() != [True]:
        raise RuntimeError("M02/M01 compatibility summary failed direct writer/reader round trip")

    rejected = full_reader.query(
        REJECTED_TRIAL_DIAGNOSTICS_DATASET,
        ("diagnostic_id", "trial_id", "accepted_state_advanced", "commit_receipt_id"),
        include_non_default=True,
        include_diagnostics=True,
    ).read_all()
    if (
        rejected.num_rows != 1
        or rejected["accepted_state_advanced"].to_pylist() != [False]
        or rejected["commit_receipt_id"].to_pylist() != [None]
    ):
        raise RuntimeError("rejected diagnostic escaped its atomic isolated namespace")
    for dataset_id in (
        REJECTED_ITERATION_TRACES_DATASET,
        REJECTED_EVENT_BRACKETS_DATASET,
    ):
        rejected_detail = full_reader.query(
            dataset_id,
            ("trial_id", "accepted_state_advanced", "commit_receipt_id"),
            include_non_default=True,
            include_diagnostics=True,
        ).read_all()
        if (
            rejected_detail.num_rows != 1
            or rejected_detail["trial_id"].to_pylist() != [DEMO_TRIAL_ID]
            or rejected_detail["accepted_state_advanced"].to_pylist() != [False]
            or rejected_detail["commit_receipt_id"].to_pylist() != [None]
        ):
            raise RuntimeError(f"{dataset_id} escaped the rejected diagnostic marker")

    relation_ids = {item["relation_id"] for item in full_reader.list_relations().relations}
    required_relations = {
        "m02.relation.accepted_step_to_point",
        "m02.relation.accepted_step_to_receipt",
        "m02.relation.simultaneous_member_to_event",
        "m02.relation.rejected_diagnostic_to_trial",
    }
    if not required_relations <= relation_ids:
        raise RuntimeError("M02 relation registry is incomplete after readback")
    if (
        manifest_reader.bundle_info()["bundle_semantic_hash"]
        != full_reader.bundle_info()["bundle_semantic_hash"]
    ):
        raise RuntimeError("bundle semantic identity changed across reader verification modes")
    recipe_rows: dict[str, dict[str, int]] = {}
    for recipe in m02_plot_recipes():
        query_rows: dict[str, int] = {}
        for query_index, query in enumerate(recipe.queries):
            table = full_reader.query(
                query.dataset_id,
                query.fields,
                filters=query.filters,
                include_non_default=query.include_non_default,
                include_diagnostics=query.include_diagnostics,
            ).read_all()
            if table.num_rows < 1:
                raise RuntimeError(
                    f"M6 recipe query returned no validation rows: "
                    f"{recipe.recipe_id}/{query.dataset_id}"
                )
            query_rows[f"{query_index}:{query.dataset_id}"] = table.num_rows
        recipe_rows[recipe.recipe_id] = query_rows
    return {
        "bundle_semantic_hash": full_reader.bundle_info()["bundle_semantic_hash"],
        "manifest_files_checked": manifest_integrity.files_checked,
        "full_files_checked": full_integrity.files_checked,
        "committed_markers_checked": full_integrity.markers_checked,
        "accepted_query_hash": accepted_query.manifest.result_hash,
        "accepted_rows": accepted.num_rows,
        "event_rows": event_group.num_rows,
        "transaction_rows": transaction.num_rows,
        "replay_rows": replay.num_rows,
        "rejected_rows": rejected.num_rows,
        "refinement_summary_rows": refinement.num_rows,
        "m01_compatibility_summary_rows": compatibility.num_rows,
        "m6_recipe_rows": recipe_rows,
    }


def generate_validation_bundle(destination: str | Path = DEFAULT_BUNDLE_PATH) -> Path:
    """Write, finalize, and read back the canonical no-physics M02 fixture."""

    output = Path(destination)
    repo_root = Path(__file__).resolve().parents[3]
    source_hashes = _source_hashes(repo_root)
    resolved_run = _resolved_config("resolved_run_config")
    resolved_case = _resolved_config("resolved_case_config")
    registry = SchemaRegistry()
    registry.register_extension(m02_result_extension())
    registry_hash = registry.freeze()
    git_commit, dirty_status = _git_state(repo_root)
    parent_state_id = stable_content_id("state", {"case_id": DEMO_CASE_ID, "index": -1})
    accepted_state_id = stable_content_id("state", {"case_id": DEMO_CASE_ID, "index": 0})
    chain = _decision_chain(parent_state_id)
    replay_seed = {
        "scope": "M02_VALIDATION_ONLY_SYNTHETIC_OWNER",
        "case_execution_plan": [DEMO_CASE_ID],
        "idempotency_keys": [DEMO_IDEMPOTENCY_KEY],
        "canonical_reduction_order": M02_CANONICAL_REDUCTION_ORDER,
        "thread_policy": M02_THREAD_POLICY,
    }
    envelope = make_run_envelope(
        registry_hash=registry_hash,
        resolved_run_config=resolved_run,
        operation_kind="M02_VALIDATION_ONLY",
        operation_profile="SYNTHETIC_OWNER_CANONICAL_BUNDLE",
        source_file_hashes=source_hashes,
        replay_manifest=replay_seed,
        git_commit=git_commit,
        dirty_status=dirty_status,
        provenance_labels=(
            "VALIDATION_ONLY",
            "synthetic_owner",
            "no_A_or_B_physics",
            "not_certifiable",
        ),
    )
    replay = _replay_manifest(
        envelope.run_id,
        envelope.run_fingerprint,
        resolved_run,
        resolved_case,
        registry_hash,
        source_hashes,
        git_commit,
        dirty_status,
        chain,
    )
    replay_payload = replay.as_dict()
    envelope = dataclasses.replace(
        envelope,
        engineering_model_contract_versions=(
            *envelope.engineering_model_contract_versions,
            "M02_NUMERICS_REQUIREMENTS 1.0.0 frozen",
        ),
        solver_build_id="M02_VALIDATION_ONLY_SYNTHETIC_OWNER",
        replay_manifest_id=replay.replay_manifest_id,
        replay_manifest_hash=semantic_hash(replay_payload),
    )
    writer = ResultWriter.create_run_bundle(output, registry=registry, run_envelope=envelope)
    writer.write_resolved_config_and_provenance(
        resolved_run,
        provenance={
            "source_identity": SourceIdentity.VALIDATION_ONLY.value,
            "owner_contract": "deterministic scalar zero-crossing protocol fixture",
            "authority_refs": source_hashes,
            "runtime": platform.python_version(),
            "interpretation_exclusions": (
                "no_A_or_B_physics",
                "no_surface_query",
                "no_contact_or_friction",
                "no_beam_spring_material_damage_or_array_physics",
                "not_experimentally_validated",
                "not_certifiable",
            ),
        },
        replay_manifest=replay_payload,
    )
    writer.create_case_shard(
        DEMO_CASE_ID,
        design_id=DEMO_DESIGN_ID,
        seed_id=DEMO_SEED_ID,
        surface_realization_id=DEMO_SURFACE_ID,
        resolved_case_config=resolved_case,
    )

    point = _accepted_point(
        envelope.run_id,
        parent_state_id,
        accepted_state_id,
        source_hashes,
        chain,
    )
    event = _committed_event(envelope.run_id, parent_state_id, accepted_state_id)
    parent_event = _dependency_parent_event(event)
    (
        accepted,
        residual,
        iteration,
        bracket,
        event_group,
        dependency,
        cascade,
        transaction,
        replay_step,
    ) = _accepted_extension_records(
        envelope.run_id,
        accepted_state_id,
        parent_state_id,
        event,
        parent_event,
        replay,
        chain,
    )
    commit = writer.begin_transaction(DEMO_CASE_ID, parent_state_id, DEMO_IDEMPOTENCY_KEY)
    commit.stage_accepted_point(point, accepted, residual, iteration)
    commit.stage_committed_events(
        parent_event,
        event,
        bracket,
        event_group,
        dependency,
        cascade,
    )
    commit.stage_transaction_records(transaction, replay_step)
    commit.stage_state_and_ledger_references(
        (
            semantic_hash((parent_state_id, accepted_state_id)),
            parent_event.event_id,
            event.event_id,
            chain.semantic_hash,
        )
    )
    commit.prepare()
    receipt = commit.commit()

    rejected, rejected_extensions = _rejected_records(envelope.run_id, accepted_state_id)
    writer.record_rejected_trial(rejected, extension_records=rejected_extensions)
    writer.write_versioned_summary(_refinement_record(envelope.run_id))
    writer.write_versioned_summary(_m01_compatibility_record(envelope.run_id))
    writer.finalize_case(DEMO_CASE_ID)
    writer.publish_run_manifest()
    _readback_validation(
        output,
        receipt_id=receipt.receipt_id,
        accepted_state_id=accepted_state_id,
    )
    return output


def catalog_overview(bundle: str | Path) -> dict[str, Any]:
    root = Path(bundle)
    reader = ResultReader.open(root, VerifyMode.MANIFEST)
    datasets = reader.list_datasets(include_non_default=True, include_diagnostics=True)
    lineage = reader.resolve_lineage()
    accepted = reader.query(
        ACCEPTED_STEP_NUMERICS_DATASET,
        ("point_id", "commit_receipt_id", "event_id", "replay_step_id"),
        include_non_default=True,
    ).read_all()
    rejected = reader.query(
        REJECTED_TRIAL_DIAGNOSTICS_DATASET,
        ("trial_id", "failure_family", "accepted_state_advanced", "commit_receipt_id"),
        include_non_default=True,
        include_diagnostics=True,
    ).read_all()
    return {
        "bundle": root.as_posix(),
        "label": "VALIDATION_ONLY / synthetic_owner / no_A_or_B_physics / not_certifiable",
        "bundle_semantic_hash": reader.bundle_info()["bundle_semantic_hash"],
        "dataset_count": len(datasets.entries),
        "receipt_count": len(lineage.receipts),
        "event_count": len(lineage.events),
        "accepted_step": accepted.to_pylist(),
        "rejected_diagnostic": rejected.to_pylist(),
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the M02 VALIDATION_ONLY synthetic-owner canonical bundle"
    )
    parser.add_argument(
        "destination",
        nargs="?",
        type=Path,
        default=DEFAULT_BUNDLE_PATH,
        help=f"bundle destination (default: {DEFAULT_BUNDLE_PATH.as_posix()})",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    path = generate_validation_bundle(args.destination)
    print(json.dumps(catalog_overview(path), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
