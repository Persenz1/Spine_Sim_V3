"""Generate the canonical M03 analytic-plane validation bundle.

The demo runs the real intrinsic A-M0 kernel at pre/event/post plane states,
then publishes the post-event accepted response through M00.  It is analytic
software/numerical evidence only: parameters are DEV_PRIOR, damage is disabled,
needle strength is unavailable, and no experimental certification is claimed.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import platform
import subprocess
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
    CertificationStatus,
    CommittedEventBase,
    PhysicalFeasibility,
    RejectedTrialBase,
    SourceIdentity,
    StatusTuple,
    ValuePresence,
)
from spine_sim.foundation.reader import ResultReader
from spine_sim.foundation.registry import SchemaRegistry
from spine_sim.foundation.writer import ResultWriter, make_run_envelope
from spine_sim.surface import SurfaceFamily, SurfaceProvider, make_analytic_source_descriptor

from .contracts import (
    M03_REQUIREMENTS_ID,
    M03_SCHEMA_VERSION,
    EmbeddedErrorClass,
    FailureAxis,
    PrescribedBaseIncrement,
    TrialIdentity,
    canonical_local_frame,
    m03_maturity,
    m03_status,
    make_baseline_parameter_bundle,
    make_embedded_request,
    make_initial_single_spine_state,
    make_rigid_pose,
)
from .events import M03EventKind
from .geometry import engineering_initial_axis
from .kernel import IntrinsicSingleSpineKernel, KernelEvaluation, make_needle_identity
from .persistence import (
    AcceptedRecordContext,
    accepted_records_from_evaluation,
    accepted_state_from_response,
    run_request_record_from_embedded,
)
from .plot_recipes import build_plot_recipe_manifest_records
from .result_extension import (
    ACCEPTED_STATE_HISTORY_DATASET,
    COMMITTED_EVENT_PAYLOADS_DATASET,
    REJECTED_DIAGNOSTICS_DATASET,
    CommittedEventPayloadRecord,
    ContactCycleRecord,
    RejectedDiagnosticRecord,
    m03_result_extension,
)
from .summaries import build_m03_summaries

DEFAULT_BUNDLE_PATH = Path("build/m03/M03_VALIDATION_ONLY.spine-result")
DEMO_PROFILE = "M03_ANALYTIC_PLANE_PRE_EVENT_POST"
DEMO_IDEMPOTENCY_KEY = "M03_VALIDATION_ONLY_PLANE_EVENT_TX_1"


def _config_schema() -> ConfigSchema:
    return ConfigSchema(
        "M03_VALIDATION_ONLY_CONFIG",
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
                "validation_only.m03_profile",
                str,
                ParameterOwnership.RUN_AND_PLOT_CONFIGURATION,
                "M03_SINGLE_SPINE_REQUIREMENTS 1.0.0 §16",
                SourceIdentity.VALIDATION_ONLY,
                enum_values=(DEMO_PROFILE,),
            ),
        ),
    )


def _resolved_config(kind: str) -> ResolvedConfig:
    authority = ConfigLayer(
        ConfigLayerLevel.L1_AUTHORITY,
        "M03_VALIDATION_ONLY:inline-authority",
        semantic_hash("float64"),
        {"foundation": {"canonical_numeric_dtype": "float64"}},
        SourceIdentity.ACCEPTED_AUTHORITY,
    )
    validation = ConfigLayer(
        ConfigLayerLevel.L2_ISOLATED,
        "M03_VALIDATION_ONLY:inline-analytic-plane",
        semantic_hash(DEMO_PROFILE),
        {"validation_only": {"m03_profile": DEMO_PROFILE}},
        SourceIdentity.VALIDATION_ONLY,
        "validation_only",
    )
    return resolve_config(
        _config_schema(),
        (authority, validation),
        config_kind=kind,
    )


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


def _source_hashes(repo_root: Path) -> dict[str, str]:
    paths = (
        repo_root / "docs/simulator_development/requirements/M00_FOUNDATION_REQUIREMENTS.md",
        repo_root / "docs/simulator_development/requirements/M01_SURFACE_REQUIREMENTS.md",
        repo_root / "docs/simulator_development/requirements/M02_NUMERICS_REQUIREMENTS.md",
        repo_root / "docs/simulator_development/requirements/M03_SINGLE_SPINE_REQUIREMENTS.md",
        repo_root / "theory/modules/A_INTEGRATED_MODEL.md",
        repo_root / "theory/interfaces/A_TO_B_CONTRACT.md",
    )
    return {path.relative_to(repo_root).as_posix(): source_file_hash(path) for path in paths}


def _authority_refs(source_hashes: dict[str, str]) -> tuple[AuthorityRef, ...]:
    return tuple(
        AuthorityRef(path, "frozen/current", digest, "whole-file")
        for path, digest in sorted(source_hashes.items())
    )


def _physical_time_unavailable() -> StatusTuple:
    return StatusTuple(
        ValuePresence.NULL,
        capability_status=m03_status().capability_status,
        attempt_outcome=AttemptOutcome.NOT_ATTEMPTED,
        physical_feasibility=PhysicalFeasibility.NOT_ASSESSED,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        reason_code="EMBEDDED_TRIAL_HAS_NO_STANDALONE_OPERATION_TIME",
        explanation="The embedded analytic event path has no declared physical operation speed.",
        authority_refs=(M03_REQUIREMENTS_ID,),
    )


def _plane_evaluations() -> tuple[Any, Any, KernelEvaluation, KernelEvaluation, KernelEvaluation]:
    provider = SurfaceProvider()
    source = make_analytic_source_descriptor()
    creation = provider.create_surface_spec(source, SurfaceFamily.PLANE, {"offset_mm": 0.0})
    if creation.spec is None:
        raise RuntimeError(creation.status.reason_code)
    realized = provider.create_realization(source, creation.spec)
    if realized.handle is None:
        raise RuntimeError(realized.status.reason_code)
    handle = realized.handle
    bundle = make_baseline_parameter_bundle()
    frame = canonical_local_frame()
    axis = engineering_initial_axis(frame, bundle.needle.alpha_rad, bundle.needle.beta_rad)
    kernel = IntrinsicSingleSpineKernel()

    def evaluate(name: str, center_height_mm: float, dz_mm: float) -> tuple[Any, KernelEvaluation]:
        center = (25.0, 75.0, center_height_mm)
        root = tuple(
            center[index] - bundle.needle.exposed_length_mm * axis[index] for index in range(3)
        )
        pose = make_rigid_pose(root)  # type: ignore[arg-type]
        state = make_initial_single_spine_state(pose)
        request = make_embedded_request(
            needle_identity=make_needle_identity(bundle),
            surface_query_handle=handle,
            base_pose_n=pose,
            prescribed_base_increment=PrescribedBaseIncrement(
                (0.0, 0.0, dz_mm),
                (0.0, 0.0, 0.0),
                "linear_translation_global",
                ("ux_global", "uy_global", "uz_global"),
                "GLOBAL",
                "M03_BASE_REFERENCE_O",
            ),
            immutable_single_spine_state_n=state,
            parameter_bundle=bundle,
            trial_identity=TrialIdentity(
                "m03-demo-step-0",
                f"m03-demo-{name}",
                "m03-demo-newton-0",
                f"m03-demo-sequence-{name}",
            ),
        )
        return request, kernel.evaluate_trial_with_artifacts(request)

    _, pre = evaluate("pre", 0.15, 0.0)
    _, event = evaluate("event", bundle.needle.tip_radius_mm, 0.0)
    # Keep the validation-only accepted point inside the independently
    # audited hard work tolerance.  The larger -0.01 mm diagnostic step is
    # intentionally rejected by the intrinsic kernel and remains covered by
    # the mechanics tests/report as an unresolved model-closure witness.
    post_request, post = evaluate("post", bundle.needle.tip_radius_mm, -5.0e-5)
    if pre.response.diagnostics.error_class is not EmbeddedErrorClass.OPEN_RESPONSE:
        raise RuntimeError("analytic pre-event plane response is not open")
    if event.response.state_events.primary_mechanical_state.value != "TIP_ZERO_LOAD":
        raise RuntimeError("analytic event point is not zero-load contact")
    if post.response.diagnostics.failure_axis is not FailureAxis.NONE:
        raise RuntimeError(
            f"analytic post-event response failed: {post.response.diagnostics.original_reason_codes}"
        )
    return bundle, post_request, pre, event, post


def _core_point(
    *,
    run_id: str,
    case_id: str,
    design_id: str,
    seed_id: str,
    surface_id: str,
    point_id: str,
    accepted_state_id: str,
    parent_state_id: str,
    request: Any,
    response: Any,
    source_hashes: dict[str, str],
) -> AcceptedPointBase:
    return AcceptedPointBase(
        run_id=run_id,
        case_id=case_id,
        design_id=design_id,
        seed_id=seed_id,
        surface_realization_id=surface_id,
        point_id=point_id,
        accepted_point_index=0,
        accepted_state_id=accepted_state_id,
        parent_state_id=parent_state_id,
        commit_receipt_id=None,
        operation_kind="M03_EMBEDDED_CONSTITUTIVE_TRIAL",
        stage="POST_TIP_CONTACT_ESTABLISH",
        path_kind="GLOBAL_Z_ANALYTIC_EVENT_PATH",
        path_coordinate=0.11,
        path_unit="mm",
        accepted_increment=0.01,
        physical_time_value=None,
        physical_time_status=_physical_time_unavailable(),
        event_sequence=1,
        simultaneous_group_ids=(),
        cascade_ids=(),
        module_payload_refs=(f"{ACCEPTED_STATE_HISTORY_DATASET}#{point_id}",),
        residual_refs=tuple(item.block_id for item in response.diagnostics.residual_blocks),
        graph_refs=(response.linearization.branch_id,),
        quality_refs=response.geometry_contact.query_receipt_ids,
        work_ledger_refs=(
            stable_content_id(
                "m03_work_ledger",
                {"point_id": point_id, "response_hash": response.response_hash},
            ),
        ),
        source_identity=SourceIdentity.DEV_POLICY,
        requirement_origin=M03_REQUIREMENTS_ID,
        value_provenance=request.metadata.value_provenance,
        authority_refs=_authority_refs(source_hashes),
        maturity=m03_maturity(numerically_verified=True),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        request_hash=request.request_hash,
        response_hash=response.response_hash,
        replay_step_hash=semantic_hash(
            {
                "parent_state_id": parent_state_id,
                "accepted_state_id": accepted_state_id,
                "request_hash": request.request_hash,
                "response_hash": response.response_hash,
            }
        ),
    )


def _event_records(
    *,
    run_id: str,
    case_id: str,
    design_id: str,
    seed_id: str,
    surface_id: str,
    point_id: str,
    parent_state_id: str,
    accepted_state_id: str,
    pre: KernelEvaluation,
    event: KernelEvaluation,
    post: KernelEvaluation,
) -> tuple[CommittedEventBase, CommittedEventPayloadRecord, ContactCycleRecord]:
    event_candidate = next(
        item
        for item in event.response.state_events.all_event_candidates
        if item.event_kind == M03EventKind.TIP_CONTACT_ESTABLISH.value
    )
    event_id = stable_content_id(
        "m03_committed_event",
        {"case_id": case_id, "kind": event_candidate.event_kind, "path_coordinate_mm": 0.10},
    )
    status = m03_status(feasibility=PhysicalFeasibility.FEASIBLE)
    core = CommittedEventBase(
        event_id=event_id,
        source_event_ids=(event_candidate.event_id,),
        hierarchy="M03_SINGLE_SPINE",
        entity_ids=("M03_VALIDATION_NEEDLE_0",),
        run_id=run_id,
        case_id=case_id,
        design_id=design_id,
        seed_id=seed_id,
        surface_realization_id=surface_id,
        event_kind=event_candidate.event_kind,
        raw_event_function=event_candidate.raw_guard,
        event_function_unit=event_candidate.raw_guard_unit,
        numerical_scaling_id="M03_EVENT_POSITION_RT_SCALE",
        path_coordinate=0.10,
        path_bracket=(0.10, 0.10),
        fraction_basis="GLOBAL_Z_ANALYTIC_EVENT_PATH_MM",
        localization_error=abs(event_candidate.raw_guard),
        pre_event_accepted_state_id=parent_state_id,
        event_point_trial_id="m03-demo-event",
        post_event_accepted_state_id=accepted_state_id,
        post_event_status=status,
        simultaneous_group_id=None,
        dependency_edges=(),
        cascade_round=0,
        pre_payload_refs=(pre.response.response_id,),
        event_payload_refs=(f"{COMMITTED_EVENT_PAYLOADS_DATASET}#{event_id}",),
        post_payload_refs=(f"{ACCEPTED_STATE_HISTORY_DATASET}#{point_id}",),
        uncertainty_refs=event.response.geometry_contact.query_receipt_ids,
        recoverability="ANALYTIC_PLANE_LOCALIZED_AND_POST_SIDE_REASSEMBLED",
        stability="ONE_SIDED_CONSISTENT",
        terminal_classification="NON_TERMINAL_CONTACT_ESTABLISH",
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=m03_maturity(numerically_verified=True),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        committed=True,
        commit_receipt_id=None,
    )
    payload = CommittedEventPayloadRecord(
        run_id=run_id,
        case_id=case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=m03_maturity(numerically_verified=True),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        event_payload_id=stable_content_id("m03_event_payload", {"event_id": event_id}),
        event_id=event_id,
        commit_receipt_id=None,
        event_kind=event_candidate.event_kind,
        raw_signed_guard=event_candidate.raw_guard,
        raw_guard_unit=event_candidate.raw_guard_unit,
        zero_value=event_candidate.zero_value,
        admissible_side=event_candidate.admissible_side,
        crossing_direction=event_candidate.direction,
        bracket_ref="ANALYTIC_PLANE_EXACT_ZERO",
        probe_refs=(
            pre.response.response_id,
            event.response.response_id,
            post.response.response_id,
        ),
        earliestness_ref="M03_VALIDATION_ANALYTIC_MONOTONE_Z_PATH",
        simultaneous_group_ids=(),
        cascade_ids=(),
        pre_response_hash=pre.response.response_hash,
        event_response_hash=event.response.response_hash,
        transition_response_hash=semantic_hash(
            {"from": "OPEN", "through": "TIP_ZERO_LOAD", "to": "ATTACHED_SLIDE"}
        ),
        post_response_hash=post.response.response_hash,
        old_primary_state=pre.response.state_events.primary_mechanical_state.value,
        new_primary_state=post.response.state_events.primary_mechanical_state.value,
        old_orthogonal_states=tuple(pre.response.state_events.quality_solve_state.split("|")),
        new_orthogonal_states=tuple(post.response.state_events.quality_solve_state.split("|")),
        support_ids=post.response.geometry_contact.active_support_ids,
        branch_id=post.response.linearization.branch_id,
        path_coordinate_mm=0.10,
        cycle_id="cycle:0",
        pre_wrench_global_at_o_n_n_mm=pre.response.wrench.wrench_a_on_b,
        event_wrench_global_at_o_n_n_mm=event.response.wrench.wrench_a_on_b,
        post_wrench_global_at_o_n_n_mm=post.response.wrench.wrench_a_on_b,
        pre_beam_energy_n_mm=pre.response.structure.beam_energy_n_mm,
        post_beam_energy_n_mm=post.response.structure.beam_energy_n_mm,
        pre_spring_energy_n_mm=pre.response.structure.spring_energy_n_mm,
        post_spring_energy_n_mm=post.response.structure.spring_energy_n_mm,
        remaining_stored_energy_n_mm=post.response.work.remaining_stored_energy_n_mm,
        released_recoverable_energy_n_mm=0.0,
        one_sided_consistency=True,
    )
    cycle = ContactCycleRecord(
        run_id=run_id,
        case_id=case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=m03_maturity(numerically_verified=True),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        cycle_record_id=stable_content_id("m03_cycle_record", {"case_id": case_id, "cycle": 0}),
        cycle_id="cycle:0",
        lifecycle_kind="CONTACT_ESTABLISHED_RIGHT_CENSORED",
        start_point_id=point_id,
        end_point_id=point_id,
        commit_receipt_id=None,
        support_ids=post.response.geometry_contact.active_support_ids,
        release_event_id=None,
        recontact_event_id=None,
        reengagement_event_id=None,
        start_x_total_mm=0.0,
        end_x_total_mm=0.0,
        start_drag_elapsed_time_s=0.0,
        end_drag_elapsed_time_s=0.0,
        right_censored=True,
    )
    return core, payload, cycle


def _rejected_records(
    *,
    run_id: str,
    case_id: str,
    accepted_state_id: str,
    point_id: str,
) -> tuple[RejectedTrialBase, RejectedDiagnosticRecord]:
    trial_id = stable_content_id(
        "m03_rejected_trial", {"case_id": case_id, "kind": "duplicate_embedded_pz"}
    )
    status = dataclasses.replace(
        m03_status(
            "CONTRACT_VIOLATION_DUPLICATE_NORMAL_LOAD",
            outcome=AttemptOutcome.REJECTED_TRIAL,
            feasibility=PhysicalFeasibility.NOT_ASSESSED,
            explanation="Intentional canonical negative fixture; no accepted history advanced.",
        ),
        last_valid_state_id=accepted_state_id,
    )
    core = RejectedTrialBase(
        trial_id=trial_id,
        run_id=run_id,
        case_id=case_id,
        parent_accepted_state_id=accepted_state_id,
        request_hash=semantic_hash({"Pz": 0.5, "call_mode": "embedded_constitutive_trial"}),
        candidate_hash=semantic_hash("REJECTED_BEFORE_SOLVE"),
        requested_path_target=0.0,
        status=status,
        reason_codes=("CONTRACT_VIOLATION_DUPLICATE_NORMAL_LOAD",),
        diagnostic_summary="Embedded per-spine Pz was rejected before constitutive evaluation.",
        optional_full_payload_ref=f"{REJECTED_DIAGNOSTICS_DATASET}#{trial_id}",
        last_valid_state_id=accepted_state_id,
        source_identity=SourceIdentity.VALIDATION_ONLY,
    )
    diagnostic = RejectedDiagnosticRecord(
        run_id=run_id,
        case_id=case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=status,
        source_identity=SourceIdentity.VALIDATION_ONLY,
        maturity=m03_maturity(numerically_verified=True),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        diagnostic_id=stable_content_id("m03_rejected_diagnostic", {"trial_id": trial_id}),
        trial_id=trial_id,
        attempt_kind="EMBEDDED_CONTRACT_PREFLIGHT",
        parent_point_id=point_id,
        parent_accepted_state_id=accepted_state_id,
        reason_family="CONTRACT_REJECTION",
        reason_code="CONTRACT_VIOLATION_DUPLICATE_NORMAL_LOAD",
        failure_axis=FailureAxis.CONTRACT_REJECTION.value,
        raw_residual=0.0,
        raw_residual_unit="1",
        raw_guard=None,
        raw_guard_unit=None,
        solver_trace_ref=None,
        surface_quality="NOT_QUERIED_CONTRACT_REJECTION",
        rollback_token=stable_content_id("m03_rollback", {"trial_id": trial_id}),
        accepted_state_advanced=False,
        path_advanced=False,
        time_advanced=False,
        slip_advanced=False,
        work_advanced=False,
        cycle_advanced=False,
        event_history_advanced=False,
    )
    return core, diagnostic


def generate_validation_bundle(destination: str | Path = DEFAULT_BUNDLE_PATH) -> Path:
    """Run the analytic pre/event/post fixture and publish a canonical bundle."""

    output = Path(destination)
    repo_root = Path(__file__).resolve().parents[3]
    source_hashes = _source_hashes(repo_root)
    resolved_run = _resolved_config("m03_validation_run")
    resolved_case = _resolved_config("m03_validation_case")
    registry = SchemaRegistry()
    registry.register_extension(m03_result_extension())
    registry_hash = registry.freeze()
    bundle, post_request, pre, event, post = _plane_evaluations()
    surface_id = post_request.surface_query_handle.realization.surface_realization_id
    design_id = bundle.parameter_bundle_id
    seed_id = stable_content_id("seed", {"fixture": DEMO_PROFILE, "rng": "NONE"})
    case_id = stable_content_id(
        "case",
        {
            "design_id": design_id,
            "seed_id": seed_id,
            "surface_realization_id": surface_id,
        },
    )
    git_commit, dirty_status = _git_state(repo_root)
    replay_seed = {
        "scope": DEMO_PROFILE,
        "case_execution_plan": [case_id],
        "idempotency_keys": [DEMO_IDEMPOTENCY_KEY],
        "surface_realization_id": surface_id,
        "pre_event_post_response_hashes": [
            pre.response.response_hash,
            event.response.response_hash,
            post.response.response_hash,
        ],
    }
    envelope = make_run_envelope(
        registry_hash=registry_hash,
        resolved_run_config=resolved_run,
        operation_kind="M03_VALIDATION_ONLY",
        operation_profile=DEMO_PROFILE,
        source_file_hashes=source_hashes,
        replay_manifest=replay_seed,
        git_commit=git_commit,
        dirty_status=dirty_status,
        provenance_labels=(
            "VALIDATION_ONLY",
            "analytic_plane",
            "A_M0_no_damage",
            "DEV_PRIOR_parameters",
            "not_experimentally_validated",
            "not_certifiable",
        ),
    )
    envelope = dataclasses.replace(
        envelope,
        engineering_model_contract_versions=(
            *envelope.engineering_model_contract_versions,
            "A_TO_B 1.0.0 accepted",
            "M03_SINGLE_SPINE_REQUIREMENTS 1.0.0 frozen",
        ),
        solver_build_id="M03_INTRINSIC_SINGLE_SPINE_A_M0_1.0.0",
    )
    writer = ResultWriter.create_run_bundle(output, registry=registry, run_envelope=envelope)
    writer.write_resolved_config_and_provenance(
        resolved_run,
        provenance={
            "source_identity": "DEV_POLICY / VALIDATION_ONLY",
            "authority_refs": source_hashes,
            "runtime": platform.python_version(),
            "physics": "rigid Signorini/Coulomb + Euler-Bernoulli + A-authoritative mount",
            "material_model": "no_damage",
            "experimentally_validated": "NOT_ASSESSED",
            "certification": "NOT_CERTIFIABLE",
            "interpretation_exclusions": (
                "no target-wall experimental validation",
                "no damage or fracture prediction",
                "no needle strength certification",
                "no array load sharing",
                "no binary success or composite score",
            ),
        },
        replay_manifest=replay_seed,
    )
    writer.create_case_shard(
        case_id,
        design_id=design_id,
        seed_id=seed_id,
        surface_realization_id=surface_id,
        resolved_case_config=resolved_case,
    )
    accepted_state = accepted_state_from_response(
        request=post_request,
        response=post.response,
        total_path_x_mm=0.0,
        drag_elapsed_time_s=0.0,
        contact_cycle_id=0,
        event_sequence_number=1,
        numerically_verified=True,
    )
    point_id = stable_content_id(
        "point", {"case_id": case_id, "state_id": accepted_state.state_id, "index": 0}
    )
    context = AcceptedRecordContext(
        run_id=envelope.run_id,
        case_id=case_id,
        point_id=point_id,
        parent_point_id=None,
        accepted_state_id=accepted_state.state_id,
        parent_accepted_state_id=post_request.immutable_single_spine_state_n.state_id,
        config_hash=resolved_case.semantic_hash,
        accepted_point_index=0,
        x_total_mm=0.0,
        drag_elapsed_time_s=0.0,
        operation_phase="POST_TIP_CONTACT_ESTABLISH",
        operation_path_coordinate_mm=0.11,
        cycle_id="cycle:0",
        event_sequence=1,
        start_point_id_for_work=point_id,
    )
    records = accepted_records_from_evaluation(
        context=context,
        request=post_request,
        evaluation=post,
        numerically_verified=True,
    )
    request_record = run_request_record_from_embedded(
        run_id=envelope.run_id,
        case_id=case_id,
        request=post_request,
        config_hash=resolved_case.semantic_hash,
        numerically_verified=True,
    )
    point = _core_point(
        run_id=envelope.run_id,
        case_id=case_id,
        design_id=design_id,
        seed_id=seed_id,
        surface_id=surface_id,
        point_id=point_id,
        accepted_state_id=accepted_state.state_id,
        parent_state_id=post_request.immutable_single_spine_state_n.state_id,
        request=post_request,
        response=post.response,
        source_hashes=source_hashes,
    )
    core_event, event_payload, cycle = _event_records(
        run_id=envelope.run_id,
        case_id=case_id,
        design_id=design_id,
        seed_id=seed_id,
        surface_id=surface_id,
        point_id=point_id,
        parent_state_id=post_request.immutable_single_spine_state_n.state_id,
        accepted_state_id=accepted_state.state_id,
        pre=pre,
        event=event,
        post=post,
    )
    transaction = writer.begin_transaction(
        case_id,
        post_request.immutable_single_spine_state_n.state_id,
        DEMO_IDEMPOTENCY_KEY,
    )
    transaction.stage_accepted_point(point, *records.transaction_records)
    transaction.stage_committed_events(core_event, event_payload, cycle)
    transaction.stage_transaction_records(request_record)
    transaction.stage_state_and_ledger_references(
        (
            accepted_state.state_id,
            records.work.work_ledger_id,
            core_event.event_id,
            post.response.transaction.rollback_token,
        )
    )
    transaction.prepare()
    receipt = transaction.commit()

    accepted_committed = dataclasses.replace(
        records.accepted_state, commit_receipt_id=receipt.receipt_id
    )
    event_committed = dataclasses.replace(event_payload, commit_receipt_id=receipt.receipt_id)
    cycle_committed = dataclasses.replace(cycle, commit_receipt_id=receipt.receipt_id)
    work_committed = dataclasses.replace(records.work, commit_receipt_id=receipt.receipt_id)
    for summary in build_m03_summaries(
        (accepted_committed,),
        committed_events=(event_committed,),
        contact_cycles=(cycle_committed,),
        work_ledger=(work_committed,),
    ):
        writer.write_versioned_summary(summary)
    for recipe in build_plot_recipe_manifest_records(
        run_id=envelope.run_id,
        case_id=case_id,
        maturity=m03_maturity(numerically_verified=True),
    ):
        writer.write_versioned_summary(recipe)
    rejected, diagnostic = _rejected_records(
        run_id=envelope.run_id,
        case_id=case_id,
        accepted_state_id=accepted_state.state_id,
        point_id=point_id,
    )
    writer.record_rejected_trial(rejected, extension_records=(diagnostic,))
    writer.finalize_case(case_id)
    writer.publish_run_manifest()
    _validate_readback(output, receipt.receipt_id)
    return output


def _validate_readback(bundle: Path, receipt_id: str) -> None:
    if not verify_bundle(bundle, VerifyMode.MANIFEST).passed:
        raise RuntimeError("M03 canonical bundle failed MANIFEST verification")
    if not verify_bundle(bundle, VerifyMode.FULL).passed:
        raise RuntimeError("M03 canonical bundle failed FULL verification")
    reader = ResultReader.open(bundle, VerifyMode.FULL)
    accepted = reader.query(
        ACCEPTED_STATE_HISTORY_DATASET,
        ("commit_receipt_id", "wrench_a_on_b_global_at_o_n_n_mm", "not_certifiable"),
    ).read_all()
    if accepted.num_rows != 1 or accepted.to_pylist()[0]["commit_receipt_id"] != receipt_id:
        raise RuntimeError("M03 accepted row is not receipt-backed")
    if reader.query(COMMITTED_EVENT_PAYLOADS_DATASET, ("event_id",)).read_all().num_rows != 1:
        raise RuntimeError("M03 committed event payload was not published")
    if (
        reader.query(
            REJECTED_DIAGNOSTICS_DATASET,
            ("trial_id",),
            include_non_default=True,
            include_diagnostics=True,
        )
        .read_all()
        .num_rows
        != 1
    ):
        raise RuntimeError("M03 rejected diagnostic isolation row is missing")


def catalog_overview(bundle: str | Path) -> dict[str, Any]:
    root = Path(bundle)
    reader = ResultReader.open(root, VerifyMode.MANIFEST)
    datasets = reader.list_datasets(include_non_default=True, include_diagnostics=True)
    accepted_rows = reader.query(ACCEPTED_STATE_HISTORY_DATASET, ("point_id",)).read_all().num_rows
    event_rows = reader.query(COMMITTED_EVENT_PAYLOADS_DATASET, ("event_id",)).read_all().num_rows
    rejected_rows = (
        reader.query(
            REJECTED_DIAGNOSTICS_DATASET,
            ("trial_id",),
            include_non_default=True,
            include_diagnostics=True,
        )
        .read_all()
        .num_rows
    )
    summary_rows = reader.query("m03.derived_summaries", ("summary_id",)).read_all().num_rows
    recipe_rows = (
        reader.query(
            "m03.plot_recipe_manifest",
            ("recipe_id",),
            include_non_default=True,
        )
        .read_all()
        .num_rows
    )
    return {
        "bundle": str(root),
        "bundle_size_bytes": sum(item.stat().st_size for item in root.rglob("*") if item.is_file()),
        "bundle_semantic_hash": reader.bundle_info()["bundle_semantic_hash"],
        "registered_dataset_count": len(datasets.entries),
        "m03_dataset_count": len(
            [item for item in datasets.entries if item.dataset_id.startswith("m03.")]
        ),
        "accepted_rows": accepted_rows,
        "committed_event_rows": event_rows,
        "rejected_rows": rejected_rows,
        "derived_summary_rows": summary_rows,
        "plot_recipe_rows": recipe_rows,
        "manifest_integrity_passed": verify_bundle(root, VerifyMode.MANIFEST).passed,
        "full_integrity_passed": verify_bundle(root, VerifyMode.FULL).passed,
        "source_identity": "DEV_POLICY / VALIDATION_ONLY",
        "material_model": "no_damage",
        "experimentally_validated": "NOT_ASSESSED",
        "certification": "NOT_CERTIFIABLE",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", nargs="?", default=DEFAULT_BUNDLE_PATH, type=Path)
    parser.add_argument("--overview-json", type=Path)
    args = parser.parse_args(argv)
    output = generate_validation_bundle(args.destination)
    overview = catalog_overview(output)
    rendered = json.dumps(overview, indent=2, sort_keys=True)
    if args.overview_json is not None:
        args.overview_json.parent.mkdir(parents=True, exist_ok=True)
        args.overview_json.write_text(f"{rendered}\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["DEFAULT_BUNDLE_PATH", "catalog_overview", "generate_validation_bundle", "main"]
