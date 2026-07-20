"""Pure adapters from an intrinsic M03 evaluation to M00 extension records.

The functions in this module do not open a writer and do not commit state.  A
caller (standalone or an embedded M02 transaction owner) supplies the accepted
point identity and stages the returned rows in the same M00 transaction as the
core accepted point.  This keeps evaluation, persistence, and commit ownership
separate.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from typing import Any

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation, IdempotencyConflict
from spine_sim.foundation.integrity import rejected_diagnostic_markers
from spine_sim.foundation.models import (
    AcceptedPointBase,
    AttemptOutcome,
    CapabilityStatus,
    CertificationStatus,
    CommitReceiptBase,
    CommittedEventBase,
    PhysicalFeasibility,
    RejectedTrialBase,
    SourceIdentity,
    StatusTuple,
)
from spine_sim.foundation.writer import ResultWriter

from .contact import deterministic_tangent_basis
from .contracts import (
    M03_REQUIREMENTS_ID,
    M03_SCHEMA_VERSION,
    AcceptedSupportState,
    EmbeddedErrorClass,
    EmbeddedSingleSpineTrialRequest,
    FailureAxis,
    ImmutableSingleSpineState,
    OperationPhase,
    SingleSpineTrialResponse,
    StandaloneSingleSpineRunRequest,
    m03_maturity,
    m03_status,
    make_metadata,
    make_rigid_pose,
)
from .events import M03EventKind, m03_event_spec
from .geometry import engineering_initial_axis, resolve_tip_pose
from .kernel import KernelEvaluation
from .result_extension import (
    AcceptedStateHistoryRecord,
    CapabilityStatusRecord,
    CommittedEventPayloadRecord,
    ContactCycleRecord,
    ContactSupportHistoryRecord,
    RejectedDiagnosticRecord,
    ReleaseOperationHistoryRecord,
    RunRequestRecord,
    SupportCandidateHistoryRecord,
    WorkLedgerRecord,
)
from .standalone import (
    OperationSegmentRecord,
    StandaloneAcceptedPointRecord,
    StandaloneCommittedEventRecord,
    StandaloneExecution,
    StandaloneRejectedTrialRecord,
    StandaloneTrialSnapshot,
)
from .surface_adapter import CandidateOrigin


@dataclass(frozen=True, slots=True)
class AcceptedRecordContext:
    """M00 identities and cumulative coordinates owned by the accepting caller."""

    run_id: str
    case_id: str
    point_id: str
    parent_point_id: str | None
    accepted_state_id: str
    parent_accepted_state_id: str
    config_hash: str
    accepted_point_index: int
    x_total_mm: float
    drag_elapsed_time_s: float
    operation_phase: str
    operation_path_coordinate_mm: float
    cycle_id: str
    event_sequence: int
    start_point_id_for_work: str

    def __post_init__(self) -> None:
        identifiers = (
            self.run_id,
            self.case_id,
            self.point_id,
            self.accepted_state_id,
            self.parent_accepted_state_id,
            self.config_hash,
            self.operation_phase,
            self.cycle_id,
            self.start_point_id_for_work,
        )
        if any(not item for item in identifiers):
            raise ContractViolation("accepted M03 persistence context has an empty identity")
        if self.accepted_point_index < 0 or self.event_sequence < 0:
            raise ContractViolation("accepted point/event indices cannot be negative")
        if self.x_total_mm < 0.0 or self.drag_elapsed_time_s < 0.0:
            raise ContractViolation("accepted cumulative path/time cannot be negative")


@dataclass(frozen=True, slots=True)
class AcceptedResultRecords:
    """Rows that must be staged atomically with one M00 accepted point."""

    accepted_state: AcceptedStateHistoryRecord
    support_candidates: tuple[SupportCandidateHistoryRecord, ...]
    contact_supports: tuple[ContactSupportHistoryRecord, ...]
    work: WorkLedgerRecord
    capability: CapabilityStatusRecord

    @property
    def transaction_records(self) -> tuple[Any, ...]:
        return (
            self.accepted_state,
            *self.support_candidates,
            *self.contact_supports,
            self.work,
            self.capability,
        )


@dataclass(frozen=True, slots=True)
class StandalonePersistenceContext:
    """M00 case identity supplied by the owner of an open case shard."""

    design_id: str
    seed_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        if not self.design_id or not self.seed_id or not self.idempotency_key:
            raise ContractViolation("standalone persistence context has an empty identity")


@dataclass(frozen=True, slots=True)
class StandalonePersistenceResult:
    """Authoritative publication evidence returned by M00 public APIs."""

    receipt: CommitReceiptBase
    accepted_point_count: int
    committed_event_count: int
    operation_segment_count: int
    contact_cycle_count: int
    rejected_diagnostic_paths: tuple[str, ...]
    artifact_backed_accepted_point_count: int
    response_only_accepted_point_count: int
    unrepresentable_candidate_count: int

    @property
    def receipt_id(self) -> str:
        return self.receipt.receipt_id


def accepted_state_from_response(
    *,
    request: EmbeddedSingleSpineTrialRequest,
    response: SingleSpineTrialResponse,
    total_path_x_mm: float,
    drag_elapsed_time_s: float,
    contact_cycle_id: int,
    event_sequence_number: int,
    numerically_verified: bool = False,
) -> ImmutableSingleSpineState:
    """Materialize accepted history only after an external transaction is armed.

    This helper is pure. It neither mutates the request snapshot nor publishes
    a transaction; the caller must publish the matching M00 records atomically.
    """

    _assert_response_matches_request(request, response)
    _assert_response_acceptance_quality(response)
    if total_path_x_mm < 0.0 or drag_elapsed_time_s < 0.0:
        raise ContractViolation("accepted cumulative path/time cannot be negative")
    if contact_cycle_id < 0 or event_sequence_number < 0:
        raise ContractViolation("accepted cycle/event identities cannot be negative")
    previous = request.immutable_single_spine_state_n
    base_position = tuple(
        left + right
        for left, right in zip(
            request.base_pose_n.position_mm,
            request.prescribed_base_increment.translation_global_mm,
            strict=True,
        )
    )
    base_pose = make_rigid_pose(
        base_position,  # type: ignore[arg-type]
        rotation_global_from_local=request.base_pose_n.rotation_global_from_local,
        expressed_frame_id=request.base_pose_n.expressed_frame_id,
        reference_point_id=request.base_pose_n.reference_point_id,
    )
    supports = tuple(
        AcceptedSupportState(
            support_id=item.support_id,
            candidate_id=item.candidate_id,
            point_global_mm=item.point_global_mm,
            normal_global=item.normal_global,
            tangent_basis_global=item.tangent_basis_global,
            normal_multiplier_n=item.normal_multiplier_n,
            tangential_multiplier_n=item.tangential_multiplier_n,
            accumulated_slip_mm=item.accumulated_slip_if_committed_preview_mm,
            motion_state=item.motion_state,
        )
        for item in response.geometry_contact.supports
    )
    payload = {
        "parent_state_id": previous.state_id,
        "state_version": previous.state_version + 1,
        "base_pose_id": base_pose.pose_id,
        "primary_state": response.state_events.primary_mechanical_state,
        "active_supports": supports,
        "beam_tip_translation_global_mm": response.structure.beam_tip_translation_global_mm,
        "beam_tip_rotation_global_rad": response.structure.beam_tip_rotation_global_rad,
        "spring_state": response.structure.spring_state,
        "spring_compression_mm": response.structure.spring_compression_mm,
        "total_path_x_mm": total_path_x_mm,
        "drag_elapsed_time_s": drag_elapsed_time_s,
        "contact_cycle_id": contact_cycle_id,
        "event_sequence_number": event_sequence_number,
        "cumulative_friction_dissipation_n_mm": (
            previous.cumulative_friction_dissipation_n_mm + response.work.friction_dissipation_n_mm
        ),
        "cumulative_input_work_n_mm": (
            previous.cumulative_input_work_n_mm + response.work.base_or_actuator_input_work_n_mm
        ),
        "accepted_response_hash": response.response_hash,
    }
    return ImmutableSingleSpineState(
        state_id=stable_content_id("m03_single_spine_state", payload),
        state_version=previous.state_version + 1,
        base_pose=base_pose,
        primary_state=response.state_events.primary_mechanical_state,
        active_supports=supports,
        beam_tip_translation_global_mm=response.structure.beam_tip_translation_global_mm,
        beam_tip_rotation_global_rad=response.structure.beam_tip_rotation_global_rad,
        spring_state=response.structure.spring_state,
        spring_compression_mm=response.structure.spring_compression_mm,
        total_path_x_mm=total_path_x_mm,
        drag_elapsed_time_s=drag_elapsed_time_s,
        contact_cycle_id=contact_cycle_id,
        event_sequence_number=event_sequence_number,
        cumulative_friction_dissipation_n_mm=(
            previous.cumulative_friction_dissipation_n_mm + response.work.friction_dissipation_n_mm
        ),
        cumulative_input_work_n_mm=(
            previous.cumulative_input_work_n_mm + response.work.base_or_actuator_input_work_n_mm
        ),
        accepted_response_hash=response.response_hash,
        metadata=make_metadata(
            "m03_accepted_single_spine_state",
            payload,
            source_identity=SourceIdentity.DEV_POLICY,
            numerically_verified=numerically_verified,
        ),
    )


def run_request_record_from_embedded(
    *,
    run_id: str,
    case_id: str,
    request: EmbeddedSingleSpineTrialRequest,
    config_hash: str,
    numerically_verified: bool = False,
) -> RunRequestRecord:
    """Create the immutable request audit row staged with the first acceptance."""

    status = m03_status(feasibility=PhysicalFeasibility.NOT_ASSESSED)
    payload = {
        **request.identity_payload(),
        "surface_query_handle_id": request.surface_query_handle.handle_id,
        "surface_realization_id": (request.surface_query_handle.realization.surface_realization_id),
        "parameter_bundle_hash": request.parameter_bundle.parameter_bundle_hash,
        "parameter_bundle": request.parameter_bundle.identity_payload(),
    }
    return RunRequestRecord(
        run_id=run_id,
        case_id=case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=m03_maturity(numerically_verified=numerically_verified),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        request_id=request.request_id,
        request_kind="EMBEDDED_SINGLE_SPINE_TRIAL",
        contract_id=request.contract_id,
        contract_version=request.contract_version,
        call_mode=request.call_mode.value,
        request_hash=request.request_hash,
        resolved_config_hash=config_hash,
        parameter_bundle_id=request.parameter_bundle.parameter_bundle_id,
        parameter_bundle_hash=request.parameter_bundle.parameter_bundle_hash,
        surface_query_handle_id=request.surface_query_handle.handle_id,
        surface_realization_id=request.surface_query_handle.realization.surface_realization_id,
        resolved_request_payload=payload,
        diagnostic_level=request.quality_request.diagnostic_level,
        output_policy="STANDARD_ACCEPTED_RAW_AND_COMMITTED_EVENTS",
        commit_receipt_id=None,
    )


def accepted_records_from_evaluation(
    *,
    context: AcceptedRecordContext,
    request: EmbeddedSingleSpineTrialRequest,
    evaluation: KernelEvaluation,
    numerically_verified: bool = False,
) -> AcceptedResultRecords:
    """Map a fresh side-effect-free trial to rows for an armed accept transaction."""

    response = evaluation.response
    _assert_response_matches_request(request, response)
    _assert_response_acceptance_quality(response)
    geometry = response.geometry_contact
    if not geometry.query_receipt_ids:
        raise ContractViolation("an accepted M03 point requires an M01 query receipt")
    clearances = (
        geometry.minimum_full_body_clearance_mm,
        geometry.cone_gap_mm,
        geometry.shaft_gap_mm,
        geometry.mount_gap_mm,
    )
    if any(value is None for value in clearances):
        raise ContractViolation("accepted M03 raw history requires resolved full-body clearances")

    status = m03_status(feasibility=PhysicalFeasibility.FEASIBLE)
    maturity = m03_maturity(numerically_verified=numerically_verified)
    frame = request.local_frame
    global_from_local = (
        (frame.e_x_global[0], frame.e_y_global[0], frame.e_z_global[0]),
        (frame.e_x_global[1], frame.e_y_global[1], frame.e_z_global[1]),
        (frame.e_x_global[2], frame.e_y_global[2], frame.e_z_global[2]),
    )
    local_from_global = tuple(zip(*global_from_local, strict=True))
    trial_base = tuple(
        left + right
        for left, right in zip(
            request.base_pose_n.position_mm,
            request.prescribed_base_increment.translation_global_mm,
            strict=True,
        )
    )
    five_stage = response.state_events.five_stage
    stages = (
        five_stage.geometric_candidate,
        five_stage.loaded_contact,
        five_stage.frictionally_stable,
        five_stage.load_bearing,
        five_stage.released,
        five_stage.recontacted_zero_load,
        five_stage.reengaged,
    )
    work_id = stable_content_id(
        "m03_work_ledger",
        {"point_id": context.point_id, "response_hash": response.response_hash},
    )
    accepted = AcceptedStateHistoryRecord(
        run_id=context.run_id,
        case_id=context.case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=maturity,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        state_record_id=stable_content_id(
            "m03_accepted_state_record",
            {"point_id": context.point_id, "state_id": context.accepted_state_id},
        ),
        point_id=context.point_id,
        parent_point_id=context.parent_point_id,
        accepted_state_id=context.accepted_state_id,
        parent_accepted_state_id=context.parent_accepted_state_id,
        commit_receipt_id=None,
        config_hash=context.config_hash,
        parameter_bundle_id=request.parameter_bundle.parameter_bundle_id,
        surface_realization_id=request.surface_query_handle.realization.surface_realization_id,
        accepted_point_index=context.accepted_point_index,
        x_total_mm=context.x_total_mm,
        drag_elapsed_time_s=context.drag_elapsed_time_s,
        operation_phase=context.operation_phase,
        operation_path_coordinate_mm=context.operation_path_coordinate_mm,
        cycle_id=context.cycle_id,
        event_sequence=context.event_sequence,
        base_position_global_mm=trial_base,  # type: ignore[arg-type]
        base_rotation_global_from_base=request.base_pose_n.rotation_global_from_local,
        root_position_global_mm=(
            evaluation.artifacts.trial_geometry.tip_pose.current_root_global_mm
        ),
        tip_center_global_mm=geometry.tip_center_global_mm,
        a0_global=engineering_initial_axis(
            frame,
            request.parameter_bundle.needle.alpha_rad,
            request.parameter_bundle.needle.beta_rad,
        ),
        a_t_global=geometry.current_axis_global,
        global_from_local=global_from_local,
        local_from_global=local_from_global,  # type: ignore[arg-type]
        reference_point_id=request.base_pose_n.reference_point_id,
        query_receipt_id=geometry.query_receipt_ids[0],
        query_lod_purpose=geometry.lod_purpose.value,
        query_error_bound_mm=geometry.geometry_uncertainty_mm or 0.0,
        query_quality=geometry.query_quality,
        query_domain_status=evaluation.artifacts.candidate_evaluation.gate_status.value,
        query_nonsmooth=geometry.nonsmooth,
        query_nonunique=geometry.nonsmooth,
        active_candidate_ids=tuple(item.candidate_id for item in geometry.supports),
        active_support_ids=geometry.active_support_ids,
        full_body_minimum_clearance_mm=_required(clearances[0]),
        cone_clearance_mm=_required(clearances[1]),
        shaft_clearance_mm=_required(clearances[2]),
        mount_clearance_mm=_required(clearances[3]),
        wrench_a_on_b_global_at_o_n_n_mm=response.wrench.wrench_a_on_b,
        opposite_wrench_b_on_a_global_at_o_n_n_mm=response.wrench.opposite_wrench_b_on_a,
        grip_resistance_rx_n=response.wrench.grip_resistance_rx_n,
        task_resistance_n=response.wrench.task_resistance_n,
        task_direction_global=response.wrench.task_direction_global,
        force_resolution_n=request.parameter_bundle.numerical.acceptance_force_resolution_n,
        beam_tip_translation_global_mm=response.structure.beam_tip_translation_global_mm,
        beam_tip_rotation_global_rad=response.structure.beam_tip_rotation_global_rad,
        beam_tip_translation_needle_mm=response.structure.beam_tip_translation_needle_mm,
        beam_tip_rotation_needle_rad=response.structure.beam_tip_rotation_needle_rad,
        beam_root_force_global_n=response.structure.beam_root_reaction_force_global_n,
        beam_root_moment_global_n_mm=response.structure.beam_root_reaction_moment_global_n_mm,
        section_resultants_needle_n_n_mm=response.structure.section_resultants_needle,
        beam_energy_n_mm=response.structure.beam_energy_n_mm,
        beam_model_state=response.structure.beam_model_state.value,
        spring_state=response.structure.spring_state.value,
        spring_compression_mm=response.structure.spring_compression_mm,
        spring_remaining_travel_mm=response.structure.remaining_spring_travel_mm,
        spring_force_n=response.structure.spring_force_n,
        spring_hard_stop_reaction_n=response.structure.hard_stop_reaction_n,
        spring_energy_n_mm=response.structure.spring_energy_n_mm,
        primary_mechanical_state=response.state_events.primary_mechanical_state.value,
        contact_motion_states=tuple(
            item.value for item in response.state_events.per_contact_motion_states
        ),
        quality_solve_state=response.state_events.quality_solve_state,
        geometric_candidate=five_stage.geometric_candidate.value,
        loaded_contact=five_stage.loaded_contact.value,
        frictionally_stable=five_stage.frictionally_stable.value,
        load_bearing=five_stage.load_bearing.value,
        five_stage_reason_codes=tuple(item.reason_code for item in stages),
        five_stage_evidence_refs=tuple(ref for item in stages for ref in item.evidence_references),
        residual_block_payloads=tuple(
            dataclasses.asdict(item) for item in response.diagnostics.residual_blocks
        ),
        complementarity_residual=response.diagnostics.complementarity_residual,
        contact_soc_residual=response.diagnostics.contact_soc_residual,
        graph_residual=response.diagnostics.graph_residual,
        jacobian_quality=response.diagnostics.jacobian_quality,
        work_ledger_id=work_id,
        damage_status=response.material_damage.material_substate.value,
        strength_status=response.structure.needle_strength_status.value,
        failure_prediction_allowed=response.material_damage.failure_prediction_allowed,
        experimentally_validated="NOT_ASSESSED",
        not_certifiable=True,
    )

    response_support = {item.candidate_id: item for item in geometry.supports}
    support_by_candidate = {
        item.candidate_id: item for item in evaluation.artifacts.contact_graph.supports
    }
    candidate_records: list[SupportCandidateHistoryRecord] = []
    for candidate in evaluation.artifacts.candidate_evaluation.candidates:
        normal = candidate.radial_normal_global
        if normal is None:
            continue
        response_item = response_support.get(candidate.candidate_id)
        tangents = (
            response_item.tangent_basis_global
            if response_item is not None
            else deterministic_tangent_basis(normal, request.task_direction_global)
        )
        support_id = (
            response_item.support_id
            if response_item is not None
            else stable_content_id(
                "m03_contact_support",
                {
                    "surface_realization_id": candidate.surface_realization_id,
                    "candidate_id": candidate.candidate_id,
                },
            )
        )
        candidate_records.append(
            SupportCandidateHistoryRecord(
                run_id=context.run_id,
                case_id=context.case_id,
                schema_version=M03_SCHEMA_VERSION,
                status=status,
                source_identity=SourceIdentity.DEV_POLICY,
                maturity=maturity,
                certification_status=CertificationStatus.NOT_CERTIFIABLE,
                candidate_record_id=stable_content_id(
                    "m03_candidate_record",
                    {"point_id": context.point_id, "candidate_id": candidate.candidate_id},
                ),
                point_id=context.point_id,
                commit_receipt_id=None,
                candidate_id=candidate.candidate_id,
                support_id=support_id,
                candidate_origin="|".join(item.value for item in candidate.origins),
                candidate_point_global_mm=candidate.point_global_mm,
                feature_id=candidate.feature_id,
                chart_id=candidate.chart_id,
                legal_gap_mm=candidate.sphere_gap_mm,
                effective_gap_mm=(
                    response_item.effective_gap_mm
                    if response_item is not None
                    else candidate.sphere_gap_mm
                ),
                cap_margin_mm=candidate.cap_legality_margin_mm,
                normal_global=normal,
                tangent_1_global=tangents[0],
                tangent_2_global=tangents[1],
                is_current_cominimal=CandidateOrigin.CURRENT_CO_MINIMAL in candidate.origins,
                is_previous_active=CandidateOrigin.PREVIOUS_ACTIVE in candidate.origins,
                is_nearby_switch_candidate=(
                    CandidateOrigin.NEARBY_SWITCH_PROBE in candidate.origins
                ),
                local_minimum_verified=candidate.local_minimum_verified,
                empty_ball_verified=candidate.empty_ball_verified,
                full_candidate_comparison_verified=candidate.query_quality_passed,
                finite_cap_legal=candidate.finite_cap_legal,
                query_receipt_id=(
                    candidate.query_receipt_ids[0]
                    if candidate.query_receipt_ids
                    else geometry.query_receipt_ids[0]
                ),
                lod_purpose=geometry.lod_purpose.value,
                error_bound_mm=candidate.error_bound_mm,
                coverage_certified=candidate.query_quality_passed,
                nonsmooth=geometry.nonsmooth,
                nonunique=geometry.nonsmooth,
                rejection_reason=("|".join(candidate.rejection_reasons) or None),
            )
        )

    contact_records = tuple(
        ContactSupportHistoryRecord(
            run_id=context.run_id,
            case_id=context.case_id,
            schema_version=M03_SCHEMA_VERSION,
            status=status,
            source_identity=SourceIdentity.DEV_POLICY,
            maturity=maturity,
            certification_status=CertificationStatus.NOT_CERTIFIABLE,
            contact_record_id=stable_content_id(
                "m03_contact_record",
                {"point_id": context.point_id, "support_id": item.support_id},
            ),
            point_id=context.point_id,
            commit_receipt_id=None,
            support_id=item.support_id,
            candidate_id=item.candidate_id,
            active=True,
            near_support=item.support_id in geometry.near_contact_support_ids,
            point_global_mm=item.point_global_mm,
            normal_global=item.normal_global,
            tangent_1_global=item.tangent_basis_global[0],
            tangent_2_global=item.tangent_basis_global[1],
            legal_gap_mm=item.legal_cap_gap_mm,
            effective_gap_mm=item.effective_gap_mm,
            normal_multiplier_n=item.normal_multiplier_n,
            tangential_multiplier_n=item.tangential_multiplier_n,
            contact_force_global_n=item.contact_force_global_n,
            objective_slip_increment_global_mm=item.objective_slip_increment_global_mm,
            objective_slip_increment_local_mm=item.objective_slip_increment_local_mm,
            motion_state=item.motion_state.value,
            support_migrated=False,
            friction_margin_n=support_by_candidate[item.candidate_id].friction_margin_n,
        )
        for item in geometry.supports
    )
    previous = request.immutable_single_spine_state_n
    work = WorkLedgerRecord(
        run_id=context.run_id,
        case_id=context.case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=maturity,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        work_ledger_id=work_id,
        start_point_id=context.start_point_id_for_work,
        end_point_id=context.point_id,
        commit_receipt_id=None,
        accepted_interval_index=context.accepted_point_index,
        base_or_actuator_input_work_n_mm=response.work.base_or_actuator_input_work_n_mm,
        delta_beam_energy_n_mm=response.work.delta_beam_energy_n_mm,
        delta_spring_energy_n_mm=response.work.delta_spring_energy_n_mm,
        rigid_contact_energy_n_mm=0.0,
        friction_dissipation_n_mm=response.work.friction_dissipation_n_mm,
        material_dissipation_n_mm=response.work.material_dissipation_n_mm,
        returned_recoverable_energy_n_mm=response.work.returned_recoverable_energy_n_mm,
        remaining_stored_energy_n_mm=response.work.remaining_stored_energy_n_mm,
        closure_error_n_mm=response.work.closure_error_n_mm,
        normalized_closure_error=response.work.normalized_closure_error,
        cumulative_input_work_n_mm=(
            previous.cumulative_input_work_n_mm + response.work.base_or_actuator_input_work_n_mm
        ),
        cumulative_friction_dissipation_n_mm=(
            previous.cumulative_friction_dissipation_n_mm + response.work.friction_dissipation_n_mm
        ),
        cumulative_material_dissipation_n_mm=0.0,
        cumulative_returned_energy_n_mm=response.work.returned_recoverable_energy_n_mm,
    )
    capability = CapabilityStatusRecord(
        run_id=context.run_id,
        case_id=context.case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=maturity,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        capability_record_id=stable_content_id(
            "m03_capability_record",
            {"point_id": context.point_id, "branch_id": response.linearization.branch_id},
        ),
        branch_id=response.linearization.branch_id,
        capability_id="M03_A_M0_NO_DAMAGE_STRENGTH_UNAVAILABLE",
        capability_state="SUPPORTED_WITH_EXPLICIT_UNAVAILABLE_FIELDS",
        reason_code="NO_DAMAGE_AND_NEEDLE_STRENGTH_UNAVAILABLE",
        material_model_id=response.material_damage.material_model_id,
        material_substate=response.material_damage.material_substate.value,
        strength_substate=response.structure.needle_strength_status.value,
        return_path_status="INTRINSIC_KERNEL_NOT_STANDALONE_OWNER",
        structural_model_status=response.structure.beam_model_state.value,
        failure_prediction_allowed=False,
        damage_intents=response.material_damage.trial_damage_intents,
        damage_write_set=response.material_damage.damage_write_set,
        initiation_utilization=None,
        current_capacity_scale=None,
        fracture_energy_n_per_mm=None,
        yield_margin=None,
        fracture_margin=None,
        experimentally_validated="NOT_ASSESSED",
        not_certifiable=True,
        commit_receipt_id=None,
    )
    return AcceptedResultRecords(
        accepted,
        tuple(candidate_records),
        contact_records,
        work,
        capability,
    )


def persist_standalone_execution(
    *,
    writer: ResultWriter,
    request: StandaloneSingleSpineRunRequest,
    execution: StandaloneExecution,
    context: StandalonePersistenceContext,
) -> StandalonePersistenceResult:
    """Publish one completed standalone history through the public M00 APIs.

    Accepted points, committed events, operation segments, work ledgers,
    contact cycles, capabilities, and the resolved request are staged in one
    M00 transaction and consequently share one real commit receipt.  Rejected
    attempts use M00's separate atomic rejected-diagnostic API; by contract
    they never receive a commit receipt and never advance accepted history.

    Standalone numerical maturity remains ``NOT_ASSESSED``.  This generic path
    cannot uplift itself merely because a trial returned successfully.
    """

    _assert_standalone_execution_matches_request(request, execution, writer)
    point_trials = _accepted_trial_snapshots(execution)
    response_by_hash = {
        item.response.response_hash: item.response
        for item in execution.trial_snapshots
        if item.response is not None
    }
    point_by_id = {item.accepted_point_id: item for item in execution.accepted_points}
    point_by_state = {item.state.state_id: item for item in execution.accepted_points}

    accepted_core: list[AcceptedPointBase] = []
    accepted_extensions: list[Any] = []
    cumulative_returned = 0.0
    artifact_backed_point_count = 0
    unrepresentable_candidate_count = 0
    for index, point in enumerate(execution.accepted_points):
        snapshot = point_trials[point.accepted_point_id]
        response = _required_trial_response(snapshot)
        _assert_response_acceptance_quality(response)
        previous_point = execution.accepted_points[index - 1] if index else None
        parent_state_id = (
            previous_point.state.state_id
            if previous_point is not None
            else snapshot.request.immutable_single_spine_state_n.state_id
        )
        if snapshot.request.immutable_single_spine_state_n.state_id != parent_state_id:
            raise ContractViolation(
                "standalone accepted history cannot be represented as one M00 lineage"
            )
        rows = _standalone_accepted_rows(
            request=request,
            point=point,
            snapshot=snapshot,
            parent_point=previous_point,
            parent_state_id=parent_state_id,
            config_hash=execution.resolved_driver_config.config_hash,
            cumulative_returned_before=cumulative_returned,
        )
        if snapshot.kernel_evaluation is not None:
            artifact_backed_point_count += 1
            artifact_context = AcceptedRecordContext(
                run_id=request.run_id,
                case_id=request.case_id,
                point_id=point.accepted_point_id,
                parent_point_id=(
                    previous_point.accepted_point_id if previous_point is not None else None
                ),
                accepted_state_id=point.state.state_id,
                parent_accepted_state_id=parent_state_id,
                config_hash=execution.resolved_driver_config.config_hash,
                accepted_point_index=point.sequence_index,
                x_total_mm=point.drag_path_x_mm,
                drag_elapsed_time_s=point.drag_elapsed_time_s,
                operation_phase=point.operation_phase.value,
                operation_path_coordinate_mm=point.operation_coordinate,
                cycle_id=f"cycle:{point.state.contact_cycle_id}",
                event_sequence=point.state.event_sequence_number,
                start_point_id_for_work=(
                    previous_point.accepted_point_id
                    if previous_point is not None
                    else point.accepted_point_id
                ),
            )
            artifact_rows = accepted_records_from_evaluation(
                context=artifact_context,
                request=snapshot.request,
                evaluation=snapshot.kernel_evaluation,
            )
            rows = dataclasses.replace(
                rows,
                support_candidates=artifact_rows.support_candidates,
            )
            unrepresentable_candidate_count += sum(
                item.radial_normal_global is None
                for item in snapshot.kernel_evaluation.artifacts.candidate_evaluation.candidates
            )
        cumulative_returned += response.work.returned_recoverable_energy_n_mm
        accepted_core.append(
            _standalone_core_point(
                request=request,
                point=point,
                snapshot=snapshot,
                parent_state_id=parent_state_id,
                previous_point=previous_point,
                design_id=context.design_id,
                seed_id=context.seed_id,
                events=execution.committed_events,
            )
        )
        accepted_extensions.extend(rows.transaction_records)

    event_core: list[CommittedEventBase] = []
    event_extensions: list[Any] = []
    for event in execution.committed_events:
        event_point = point_by_id.get(event.accepted_point_id)
        if event_point is None:
            raise ContractViolation("standalone committed event references an unknown point")
        event_response = response_by_hash.get(event.response_hash)
        pre_response = response_by_hash.get(event.pre_event_response_hash or "")
        post_response = response_by_hash.get(event.post_event_response_hash or "")
        if event_response is None or pre_response is None or post_response is None:
            raise ContractViolation(
                "standalone event persistence requires retained pre/event/post responses"
            )
        _assert_event_reassembly_responses(
            event=event,
            pre_response=pre_response,
            event_response=event_response,
            post_response=post_response,
        )
        point_index = event_point.sequence_index
        pre_state_id = (
            execution.accepted_points[point_index - 1].state.state_id
            if point_index > 0
            else point_trials[
                event_point.accepted_point_id
            ].request.immutable_single_spine_state_n.state_id
        )
        core, payload = _standalone_event_rows(
            request=request,
            event=event,
            point=event_point,
            snapshot=point_trials[event_point.accepted_point_id],
            pre_state_id=pre_state_id,
            pre_response=pre_response,
            event_response=event_response,
            post_response=post_response,
            design_id=context.design_id,
            seed_id=context.seed_id,
        )
        event_core.append(core)
        event_extensions.append(payload)

    operation_rows = tuple(
        _standalone_operation_row(
            request=request,
            execution=execution,
            segment=segment,
            point_by_id=point_by_id,
            point_trials=point_trials,
        )
        for segment in execution.operation_segments
    )
    cycle_rows = _standalone_cycle_rows(request, execution)
    request_row = _standalone_run_request_row(request, execution)

    parent_state_id = (
        point_trials[
            execution.accepted_points[0].accepted_point_id
        ].request.immutable_single_spine_state_n.state_id
        if execution.accepted_points
        else execution.response.final_state.state_id
    )
    transaction = writer.begin_transaction(
        request.case_id,
        parent_state_id,
        context.idempotency_key,
    )
    if accepted_core:
        transaction.stage_accepted_point(*accepted_core, *accepted_extensions)
    if event_core or event_extensions or operation_rows or cycle_rows:
        transaction.stage_committed_events(
            *event_core,
            *event_extensions,
            *operation_rows,
            *cycle_rows,
        )
    transaction.stage_transaction_records(request_row)
    transaction.stage_state_and_ledger_references(
        (
            *(item.event_id for item in event_core),
            *(
                item.work_ledger_id
                for item in accepted_extensions
                if isinstance(item, WorkLedgerRecord)
            ),
            *(item.operation_record_id for item in operation_rows),
            *(item.cycle_record_id for item in cycle_rows),
        )
    )
    transaction.prepare()
    receipt = transaction.commit()

    rejected_paths = tuple(
        _publish_standalone_rejected(
            writer=writer,
            request=request,
            record=record,
            execution=execution,
            point_by_state=point_by_state,
        )
        for record in execution.rejected_trials
    )
    return StandalonePersistenceResult(
        receipt=receipt,
        accepted_point_count=len(accepted_core),
        committed_event_count=len(event_core),
        operation_segment_count=len(operation_rows),
        contact_cycle_count=len(cycle_rows),
        rejected_diagnostic_paths=rejected_paths,
        artifact_backed_accepted_point_count=artifact_backed_point_count,
        response_only_accepted_point_count=len(accepted_core) - artifact_backed_point_count,
        unrepresentable_candidate_count=unrepresentable_candidate_count,
    )


def _assert_standalone_execution_matches_request(
    request: StandaloneSingleSpineRunRequest,
    execution: StandaloneExecution,
    writer: ResultWriter,
) -> None:
    response = execution.response
    if (
        response.request_hash != request.request_hash
        or response.run_id != request.run_id
        or response.case_id != request.case_id
    ):
        raise ContractViolation("standalone execution does not belong to the request")
    if writer.run_envelope.run_id != request.run_id:
        raise ContractViolation("standalone request does not belong to the M00 run")
    surface_id = request.surface_query_handle.realization.surface_realization_id
    if response.surface_realization_id != surface_id:
        raise ContractViolation("standalone response surface realization is inconsistent")
    if any(
        item.run_id != request.run_id or item.case_id != request.case_id
        for collection in (
            execution.accepted_points,
            execution.committed_events,
            execution.rejected_trials,
            execution.operation_segments,
        )
        for item in collection
    ):
        raise ContractViolation("standalone execution contains cross-run/case records")


def _accepted_trial_snapshots(
    execution: StandaloneExecution,
) -> dict[str, StandaloneTrialSnapshot]:
    result: dict[str, StandaloneTrialSnapshot] = {}
    for point in execution.accepted_points:
        matches = tuple(
            item
            for item in execution.trial_snapshots
            if item.response is not None
            and item.response.response_id == point.response_id
            and item.response.response_hash == point.response_hash
            and item.target_pose_id == point.pose_id
        )
        if len(matches) != 1:
            raise ContractViolation(
                "accepted standalone point requires one retained request/response snapshot"
            )
        result[point.accepted_point_id] = matches[0]
    return result


def _required_trial_response(snapshot: StandaloneTrialSnapshot) -> SingleSpineTrialResponse:
    if snapshot.response is None:
        raise ContractViolation("accepted standalone trial cannot have an exception snapshot")
    return snapshot.response


def _standalone_run_request_row(
    request: StandaloneSingleSpineRunRequest,
    execution: StandaloneExecution,
) -> RunRequestRecord:
    payload = {
        "operation_id": request.operation_id,
        "request_hash": request.request_hash,
        "resolved_config_hash": request.resolved_config_hash,
        "standalone_driver_config": dataclasses.asdict(execution.resolved_driver_config),
        "parameter_bundle": request.parameter_bundle.identity_payload(),
        "surface_query_handle_id": request.surface_query_handle.handle_id,
        "surface_realization_id": (request.surface_query_handle.realization.surface_realization_id),
        "policies": {
            "initial_pose": dataclasses.asdict(request.initial_pose_policy),
            "search": dataclasses.asdict(request.search_policy),
            "preload": dataclasses.asdict(request.preload_policy),
            "drag": dataclasses.asdict(request.drag_policy),
            "release": dataclasses.asdict(request.release_policy),
        },
        "material_model_id": request.material_model_id,
    }
    return RunRequestRecord(
        run_id=request.run_id,
        case_id=request.case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=m03_status(feasibility=PhysicalFeasibility.NOT_ASSESSED),
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=m03_maturity(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        request_id=request.request_id,
        request_kind="STANDALONE_SINGLE_SPINE_OPERATION",
        contract_id="M03_STANDALONE_SINGLE_SPINE",
        contract_version=M03_SCHEMA_VERSION,
        call_mode="STANDALONE_OUTER_OPERATION",
        request_hash=request.request_hash,
        resolved_config_hash=execution.resolved_driver_config.config_hash,
        parameter_bundle_id=request.parameter_bundle.parameter_bundle_id,
        parameter_bundle_hash=request.parameter_bundle.parameter_bundle_hash,
        surface_query_handle_id=request.surface_query_handle.handle_id,
        surface_realization_id=request.surface_query_handle.realization.surface_realization_id,
        resolved_request_payload=payload,
        diagnostic_level=request.diagnostic_level,
        output_policy=request.output_policy,
        commit_receipt_id=None,
    )


def _standalone_accepted_rows(
    *,
    request: StandaloneSingleSpineRunRequest,
    point: StandaloneAcceptedPointRecord,
    snapshot: StandaloneTrialSnapshot,
    parent_point: StandaloneAcceptedPointRecord | None,
    parent_state_id: str,
    config_hash: str,
    cumulative_returned_before: float,
) -> AcceptedResultRecords:
    response = _required_trial_response(snapshot)
    geometry = response.geometry_contact
    if not geometry.query_receipt_ids:
        raise ContractViolation("accepted standalone point requires an M01 query receipt")
    clearances = (
        geometry.minimum_full_body_clearance_mm,
        geometry.cone_gap_mm,
        geometry.shaft_gap_mm,
        geometry.mount_gap_mm,
    )
    if any(item is None for item in clearances):
        raise ContractViolation(
            "accepted standalone persistence requires resolved full-body clearances"
        )
    status = m03_status(feasibility=PhysicalFeasibility.FEASIBLE)
    maturity = m03_maturity()
    frame = request.local_frame
    global_from_local = (
        (frame.e_x_global[0], frame.e_y_global[0], frame.e_z_global[0]),
        (frame.e_x_global[1], frame.e_y_global[1], frame.e_z_global[1]),
        (frame.e_x_global[2], frame.e_y_global[2], frame.e_z_global[2]),
    )
    local_from_global = tuple(zip(*global_from_local, strict=True))
    tip_pose = resolve_tip_pose(
        rigid_root_global_mm=point.state.base_pose.position_mm,
        local_frame=request.local_frame,
        needle=request.parameter_bundle.needle,
        spring_compression_mm=response.structure.spring_compression_mm,
        beam_tip_translation_global_mm=response.structure.beam_tip_translation_global_mm,
        beam_tip_rotation_global_rad=response.structure.beam_tip_rotation_global_rad,
    )
    five_stage = response.state_events.five_stage
    stages = (
        five_stage.geometric_candidate,
        five_stage.loaded_contact,
        five_stage.frictionally_stable,
        five_stage.load_bearing,
        five_stage.released,
        five_stage.recontacted_zero_load,
        five_stage.reengaged,
    )
    work_id = stable_content_id(
        "m03_work_ledger",
        {"point_id": point.accepted_point_id, "response_hash": response.response_hash},
    )
    accepted = AcceptedStateHistoryRecord(
        run_id=request.run_id,
        case_id=request.case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=maturity,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        state_record_id=stable_content_id(
            "m03_accepted_state_record",
            {"point_id": point.accepted_point_id, "state_id": point.state.state_id},
        ),
        point_id=point.accepted_point_id,
        parent_point_id=(parent_point.accepted_point_id if parent_point is not None else None),
        accepted_state_id=point.state.state_id,
        parent_accepted_state_id=parent_state_id,
        commit_receipt_id=None,
        config_hash=config_hash,
        parameter_bundle_id=request.parameter_bundle.parameter_bundle_id,
        surface_realization_id=request.surface_query_handle.realization.surface_realization_id,
        accepted_point_index=point.sequence_index,
        x_total_mm=point.drag_path_x_mm,
        drag_elapsed_time_s=point.drag_elapsed_time_s,
        operation_phase=point.operation_phase.value,
        operation_path_coordinate_mm=point.operation_coordinate,
        cycle_id=f"cycle:{point.state.contact_cycle_id}",
        event_sequence=point.state.event_sequence_number,
        base_position_global_mm=point.state.base_pose.position_mm,
        base_rotation_global_from_base=point.state.base_pose.rotation_global_from_local,
        root_position_global_mm=tip_pose.current_root_global_mm,
        tip_center_global_mm=geometry.tip_center_global_mm,
        a0_global=engineering_initial_axis(
            frame,
            request.parameter_bundle.needle.alpha_rad,
            request.parameter_bundle.needle.beta_rad,
        ),
        a_t_global=geometry.current_axis_global,
        global_from_local=global_from_local,
        local_from_global=local_from_global,  # type: ignore[arg-type]
        reference_point_id=request.reference_point_id,
        query_receipt_id=geometry.query_receipt_ids[0],
        query_lod_purpose=geometry.lod_purpose.value,
        query_error_bound_mm=geometry.geometry_uncertainty_mm or 0.0,
        query_quality=geometry.query_quality,
        query_domain_status=response.diagnostics.surface_data_quality,
        query_nonsmooth=geometry.nonsmooth,
        query_nonunique=geometry.nonsmooth,
        active_candidate_ids=tuple(item.candidate_id for item in geometry.supports),
        active_support_ids=geometry.active_support_ids,
        full_body_minimum_clearance_mm=_required(clearances[0]),
        cone_clearance_mm=_required(clearances[1]),
        shaft_clearance_mm=_required(clearances[2]),
        mount_clearance_mm=_required(clearances[3]),
        wrench_a_on_b_global_at_o_n_n_mm=response.wrench.wrench_a_on_b,
        opposite_wrench_b_on_a_global_at_o_n_n_mm=response.wrench.opposite_wrench_b_on_a,
        grip_resistance_rx_n=response.wrench.grip_resistance_rx_n,
        task_resistance_n=response.wrench.task_resistance_n,
        task_direction_global=response.wrench.task_direction_global,
        force_resolution_n=request.parameter_bundle.numerical.acceptance_force_resolution_n,
        beam_tip_translation_global_mm=response.structure.beam_tip_translation_global_mm,
        beam_tip_rotation_global_rad=response.structure.beam_tip_rotation_global_rad,
        beam_tip_translation_needle_mm=response.structure.beam_tip_translation_needle_mm,
        beam_tip_rotation_needle_rad=response.structure.beam_tip_rotation_needle_rad,
        beam_root_force_global_n=response.structure.beam_root_reaction_force_global_n,
        beam_root_moment_global_n_mm=response.structure.beam_root_reaction_moment_global_n_mm,
        section_resultants_needle_n_n_mm=response.structure.section_resultants_needle,
        beam_energy_n_mm=response.structure.beam_energy_n_mm,
        beam_model_state=response.structure.beam_model_state.value,
        spring_state=response.structure.spring_state.value,
        spring_compression_mm=response.structure.spring_compression_mm,
        spring_remaining_travel_mm=response.structure.remaining_spring_travel_mm,
        spring_force_n=response.structure.spring_force_n,
        spring_hard_stop_reaction_n=response.structure.hard_stop_reaction_n,
        spring_energy_n_mm=response.structure.spring_energy_n_mm,
        primary_mechanical_state=point.state.primary_state.value,
        contact_motion_states=tuple(
            item.motion_state.value for item in point.state.active_supports
        ),
        quality_solve_state=response.state_events.quality_solve_state,
        geometric_candidate=five_stage.geometric_candidate.value,
        loaded_contact=five_stage.loaded_contact.value,
        frictionally_stable=five_stage.frictionally_stable.value,
        load_bearing=five_stage.load_bearing.value,
        five_stage_reason_codes=tuple(item.reason_code for item in stages),
        five_stage_evidence_refs=tuple(ref for item in stages for ref in item.evidence_references),
        residual_block_payloads=tuple(
            dataclasses.asdict(item) for item in response.diagnostics.residual_blocks
        ),
        complementarity_residual=response.diagnostics.complementarity_residual,
        contact_soc_residual=response.diagnostics.contact_soc_residual,
        graph_residual=response.diagnostics.graph_residual,
        jacobian_quality=response.diagnostics.jacobian_quality,
        work_ledger_id=work_id,
        damage_status=response.material_damage.material_substate.value,
        strength_status=response.structure.needle_strength_status.value,
        failure_prediction_allowed=response.material_damage.failure_prediction_allowed,
        experimentally_validated="NOT_ASSESSED",
        not_certifiable=True,
    )

    candidates = tuple(
        _support_candidate_from_response(request, point, response, item, status, maturity)
        for item in geometry.supports
    )
    mu = request.parameter_bundle.contact.friction_coefficient
    contacts = tuple(
        ContactSupportHistoryRecord(
            run_id=request.run_id,
            case_id=request.case_id,
            schema_version=M03_SCHEMA_VERSION,
            status=status,
            source_identity=SourceIdentity.DEV_POLICY,
            maturity=maturity,
            certification_status=CertificationStatus.NOT_CERTIFIABLE,
            contact_record_id=stable_content_id(
                "m03_contact_record",
                {"point_id": point.accepted_point_id, "support_id": item.support_id},
            ),
            point_id=point.accepted_point_id,
            commit_receipt_id=None,
            support_id=item.support_id,
            candidate_id=item.candidate_id,
            active=True,
            near_support=item.support_id in geometry.near_contact_support_ids,
            point_global_mm=item.point_global_mm,
            normal_global=item.normal_global,
            tangent_1_global=item.tangent_basis_global[0],
            tangent_2_global=item.tangent_basis_global[1],
            legal_gap_mm=item.legal_cap_gap_mm,
            effective_gap_mm=item.effective_gap_mm,
            normal_multiplier_n=item.normal_multiplier_n,
            tangential_multiplier_n=item.tangential_multiplier_n,
            contact_force_global_n=item.contact_force_global_n,
            objective_slip_increment_global_mm=item.objective_slip_increment_global_mm,
            objective_slip_increment_local_mm=item.objective_slip_increment_local_mm,
            motion_state=item.motion_state.value,
            support_migrated=False,
            friction_margin_n=max(
                0.0,
                mu * item.normal_multiplier_n - math.hypot(*item.tangential_multiplier_n),
            ),
        )
        for item in geometry.supports
    )
    work = WorkLedgerRecord(
        run_id=request.run_id,
        case_id=request.case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=maturity,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        work_ledger_id=work_id,
        start_point_id=(
            parent_point.accepted_point_id if parent_point is not None else point.accepted_point_id
        ),
        end_point_id=point.accepted_point_id,
        commit_receipt_id=None,
        accepted_interval_index=point.sequence_index,
        base_or_actuator_input_work_n_mm=response.work.base_or_actuator_input_work_n_mm,
        delta_beam_energy_n_mm=response.work.delta_beam_energy_n_mm,
        delta_spring_energy_n_mm=response.work.delta_spring_energy_n_mm,
        rigid_contact_energy_n_mm=0.0,
        friction_dissipation_n_mm=response.work.friction_dissipation_n_mm,
        material_dissipation_n_mm=0.0,
        returned_recoverable_energy_n_mm=response.work.returned_recoverable_energy_n_mm,
        remaining_stored_energy_n_mm=response.work.remaining_stored_energy_n_mm,
        closure_error_n_mm=response.work.closure_error_n_mm,
        normalized_closure_error=response.work.normalized_closure_error,
        cumulative_input_work_n_mm=point.state.cumulative_input_work_n_mm,
        cumulative_friction_dissipation_n_mm=(point.state.cumulative_friction_dissipation_n_mm),
        cumulative_material_dissipation_n_mm=0.0,
        cumulative_returned_energy_n_mm=(
            cumulative_returned_before + response.work.returned_recoverable_energy_n_mm
        ),
    )
    capability = CapabilityStatusRecord(
        run_id=request.run_id,
        case_id=request.case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=maturity,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        capability_record_id=stable_content_id(
            "m03_capability_record",
            {"point_id": point.accepted_point_id, "branch_id": response.linearization.branch_id},
        ),
        branch_id=response.linearization.branch_id,
        capability_id="M03_A_M0_NO_DAMAGE_STRENGTH_UNAVAILABLE",
        capability_state="SUPPORTED_WITH_EXPLICIT_UNAVAILABLE_FIELDS",
        reason_code="NO_DAMAGE_AND_NEEDLE_STRENGTH_UNAVAILABLE",
        material_model_id=response.material_damage.material_model_id,
        material_substate=response.material_damage.material_substate.value,
        strength_substate=response.structure.needle_strength_status.value,
        return_path_status="STANDALONE_OPERATION_OWNER",
        structural_model_status=response.structure.beam_model_state.value,
        failure_prediction_allowed=False,
        damage_intents=response.material_damage.trial_damage_intents,
        damage_write_set=response.material_damage.damage_write_set,
        initiation_utilization=None,
        current_capacity_scale=None,
        fracture_energy_n_per_mm=None,
        yield_margin=None,
        fracture_margin=None,
        experimentally_validated="NOT_ASSESSED",
        not_certifiable=True,
        commit_receipt_id=None,
    )
    return AcceptedResultRecords(accepted, candidates, contacts, work, capability)


def _support_candidate_from_response(
    request: StandaloneSingleSpineRunRequest,
    point: StandaloneAcceptedPointRecord,
    response: SingleSpineTrialResponse,
    item: Any,
    status: StatusTuple,
    maturity: Any,
) -> SupportCandidateHistoryRecord:
    """Persist only response-exposed active candidates without inventing witnesses."""

    return SupportCandidateHistoryRecord(
        run_id=request.run_id,
        case_id=request.case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=maturity,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        candidate_record_id=stable_content_id(
            "m03_candidate_record",
            {"point_id": point.accepted_point_id, "candidate_id": item.candidate_id},
        ),
        point_id=point.accepted_point_id,
        commit_receipt_id=None,
        candidate_id=item.candidate_id,
        support_id=item.support_id,
        candidate_origin="ACCEPTED_ACTIVE_RESPONSE_ONLY",
        candidate_point_global_mm=item.point_global_mm,
        feature_id=stable_content_id(
            "m03_response_feature",
            {
                "candidate_id": item.candidate_id,
                "feature_type": item.feature_type,
                "chart_id": item.chart_id,
            },
        ),
        chart_id=item.chart_id,
        legal_gap_mm=item.legal_cap_gap_mm,
        effective_gap_mm=item.effective_gap_mm,
        cap_margin_mm=item.cap_legality_margin_mm,
        normal_global=item.normal_global,
        tangent_1_global=item.tangent_basis_global[0],
        tangent_2_global=item.tangent_basis_global[1],
        is_current_cominimal=False,
        is_previous_active=False,
        is_nearby_switch_candidate=False,
        local_minimum_verified=False,
        empty_ball_verified=False,
        full_candidate_comparison_verified=False,
        finite_cap_legal=item.cap_legality_margin_mm >= 0.0,
        query_receipt_id=response.geometry_contact.query_receipt_ids[0],
        lod_purpose=response.geometry_contact.lod_purpose.value,
        error_bound_mm=response.geometry_contact.geometry_uncertainty_mm or 0.0,
        coverage_certified=False,
        nonsmooth=response.geometry_contact.nonsmooth,
        nonunique=response.geometry_contact.nonsmooth,
        rejection_reason=None,
    )


def _standalone_core_point(
    *,
    request: StandaloneSingleSpineRunRequest,
    point: StandaloneAcceptedPointRecord,
    snapshot: StandaloneTrialSnapshot,
    parent_state_id: str,
    previous_point: StandaloneAcceptedPointRecord | None,
    design_id: str,
    seed_id: str,
    events: tuple[StandaloneCommittedEventRecord, ...],
) -> AcceptedPointBase:
    response = _required_trial_response(snapshot)
    point_events = tuple(
        item for item in events if item.accepted_point_id == point.accepted_point_id
    )
    simultaneous = tuple(
        sorted(
            {
                item.simultaneous_group_id
                for item in point_events
                if item.simultaneous_group_id is not None
            }
        )
    )
    if point.operation_phase is OperationPhase.DRAG:
        time_status = m03_status(feasibility=PhysicalFeasibility.FEASIBLE)
        physical_time = point.drag_elapsed_time_s
    else:
        time_status = m03_status(
            "PHYSICAL_OPERATION_TIME_NOT_DEFINED_FOR_PHASE",
            capability=CapabilityStatus.NOT_APPLICABLE,
            outcome=AttemptOutcome.NOT_ATTEMPTED,
            explanation="Only the frozen drag speed defines physical operation time.",
        )
        physical_time = None
    accepted_increment = 0.0
    if (
        previous_point is not None
        and previous_point.operation_phase is point.operation_phase
        and previous_point.operation_coordinate_unit == point.operation_coordinate_unit
    ):
        accepted_increment = point.operation_coordinate - previous_point.operation_coordinate
    work_id = stable_content_id(
        "m03_work_ledger",
        {"point_id": point.accepted_point_id, "response_hash": response.response_hash},
    )
    return AcceptedPointBase(
        run_id=request.run_id,
        case_id=request.case_id,
        design_id=design_id,
        seed_id=seed_id,
        surface_realization_id=request.surface_query_handle.realization.surface_realization_id,
        point_id=point.accepted_point_id,
        accepted_point_index=point.sequence_index,
        accepted_state_id=point.state.state_id,
        parent_state_id=parent_state_id,
        commit_receipt_id=None,
        operation_kind="M03_STANDALONE_SINGLE_SPINE",
        stage=point.operation_phase.value,
        path_kind=f"M03_{point.operation_phase.value}_COORDINATE",
        path_coordinate=point.operation_coordinate,
        path_unit=point.operation_coordinate_unit,
        accepted_increment=accepted_increment,
        physical_time_value=physical_time,
        physical_time_status=time_status,
        event_sequence=point.state.event_sequence_number,
        simultaneous_group_ids=simultaneous,
        cascade_ids=tuple(
            f"m03:standalone:cascade:{item.event_sequence_number}"
            for item in point_events
            if item.dependency_layer > 0
        ),
        module_payload_refs=(f"m03.accepted_state_history#{point.accepted_point_id}",),
        residual_refs=tuple(item.block_id for item in response.diagnostics.residual_blocks),
        graph_refs=(response.linearization.branch_id,),
        quality_refs=response.geometry_contact.query_receipt_ids,
        work_ledger_refs=(work_id,),
        source_identity=SourceIdentity.DEV_POLICY,
        requirement_origin=M03_REQUIREMENTS_ID,
        value_provenance=snapshot.request.metadata.value_provenance,
        authority_refs=snapshot.request.metadata.authority_refs,
        maturity=m03_maturity(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        request_hash=snapshot.request.request_hash,
        response_hash=response.response_hash,
        replay_step_hash=semantic_hash(
            {
                "kind": "m03_standalone_replay_step",
                "parent_state_id": parent_state_id,
                "accepted_state_id": point.state.state_id,
                "request_hash": snapshot.request.request_hash,
                "response_hash": response.response_hash,
            }
        ),
    )


def _standalone_event_rows(
    *,
    request: StandaloneSingleSpineRunRequest,
    event: StandaloneCommittedEventRecord,
    point: StandaloneAcceptedPointRecord,
    snapshot: StandaloneTrialSnapshot,
    pre_state_id: str,
    pre_response: SingleSpineTrialResponse,
    event_response: SingleSpineTrialResponse,
    post_response: SingleSpineTrialResponse,
    design_id: str,
    seed_id: str,
) -> tuple[CommittedEventBase, CommittedEventPayloadRecord]:
    try:
        spec = m03_event_spec(M03EventKind(event.event_kind))
    except ValueError as exc:
        raise ContractViolation(
            f"standalone event kind is outside the frozen M03 registry: {event.event_kind}"
        ) from exc
    matching_candidates = tuple(
        item
        for item in event_response.state_events.all_event_candidates
        if item.event_kind == event.event_kind
    )
    source_event_ids = (
        tuple(item.event_id for item in matching_candidates)
        if matching_candidates
        else (
            stable_content_id(
                "m03_standalone_discrete_source_event",
                {
                    "event_id": event.committed_event_id,
                    "event_kind": event.event_kind,
                    "coordinate": event.operation_coordinate,
                },
            ),
        )
    )
    status = m03_status(feasibility=PhysicalFeasibility.FEASIBLE)
    event_path_mm = (
        event.operation_coordinate if event.coordinate_unit == "mm" else point.drag_path_x_mm
    )
    bracket_ref = stable_content_id(
        "m03_standalone_event_bracket",
        {
            "event_id": event.committed_event_id,
            "path_bracket": event.path_bracket,
            "probe_refs": event.probe_refs,
        },
    )
    core = CommittedEventBase(
        event_id=event.committed_event_id,
        source_event_ids=source_event_ids,
        hierarchy="M03_STANDALONE_SINGLE_SPINE",
        entity_ids=(snapshot.request.needle_identity.needle_id,),
        run_id=request.run_id,
        case_id=request.case_id,
        design_id=design_id,
        seed_id=seed_id,
        surface_realization_id=request.surface_query_handle.realization.surface_realization_id,
        event_kind=event.event_kind,
        raw_event_function=event.raw_guard,
        event_function_unit=event.raw_guard_unit,
        numerical_scaling_id=spec.channel_id,
        path_coordinate=event.operation_coordinate,
        path_bracket=event.path_bracket,
        fraction_basis=f"{event.operation_phase.value}:{event.coordinate_unit}",
        localization_error=event.localization_error_mm,
        pre_event_accepted_state_id=pre_state_id,
        event_point_trial_id=snapshot.request.trial_identity.global_trial_id,
        post_event_accepted_state_id=point.state.state_id,
        post_event_status=status,
        simultaneous_group_id=event.simultaneous_group_id,
        dependency_edges=(),
        cascade_round=event.dependency_layer,
        pre_payload_refs=(pre_response.response_id,),
        event_payload_refs=(f"m03.committed_event_payloads#{event.committed_event_id}",),
        post_payload_refs=(f"m03.accepted_state_history#{point.accepted_point_id}",),
        uncertainty_refs=event_response.geometry_contact.query_receipt_ids,
        recoverability=(
            "RETURN_PATH_OPERATION"
            if event.operation_phase
            in {
                OperationPhase.UNLOAD,
                OperationPhase.DRIVE_OFF_UNLOCK,
                OperationPhase.REVERSE_SEARCH,
                OperationPhase.LIFT_OFF,
                OperationPhase.RESEARCH,
                OperationPhase.RELOAD,
            }
            else "FORWARD_OPERATION"
        ),
        stability=(
            "ONE_SIDED_CONSISTENT"
            if post_response.state_events.event_one_sided_consistency
            else "ONE_SIDED_INCONSISTENT"
        ),
        terminal_classification=(
            "TERMINAL_TRAVEL_COMPLETE"
            if event.event_kind == M03EventKind.TRAVEL_COMPLETE.value
            else "NON_TERMINAL"
        ),
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=m03_maturity(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        committed=True,
        commit_receipt_id=None,
    )
    transition_hash = semantic_hash(
        {
            "kind": "m03_standalone_event_transition",
            "event_id": event.committed_event_id,
            "pre_response_hash": pre_response.response_hash,
            "event_response_hash": event_response.response_hash,
            "post_response_hash": post_response.response_hash,
            "pre_state": pre_response.state_events.primary_mechanical_state,
            "post_state": point.state.primary_state,
        },
    )
    payload = CommittedEventPayloadRecord(
        run_id=request.run_id,
        case_id=request.case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=m03_maturity(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        event_payload_id=stable_content_id(
            "m03_event_payload", {"event_id": event.committed_event_id}
        ),
        event_id=event.committed_event_id,
        commit_receipt_id=None,
        event_kind=event.event_kind,
        raw_signed_guard=event.raw_guard,
        raw_guard_unit=event.raw_guard_unit,
        zero_value=spec.zero_level,
        admissible_side=spec.admissible_side.value,
        crossing_direction=spec.trigger_direction.value,
        bracket_ref=bracket_ref,
        probe_refs=event.probe_refs,
        earliestness_ref=(
            event.earliestness_certificate_id or "NOT_REQUIRED_DISCRETE_OPERATION_EVENT"
        ),
        simultaneous_group_ids=(
            (event.simultaneous_group_id,) if event.simultaneous_group_id is not None else ()
        ),
        cascade_ids=(
            (f"m03:standalone:cascade:{event.event_sequence_number}",)
            if event.dependency_layer > 0
            else ()
        ),
        pre_response_hash=pre_response.response_hash,
        event_response_hash=event_response.response_hash,
        transition_response_hash=transition_hash,
        post_response_hash=post_response.response_hash,
        old_primary_state=pre_response.state_events.primary_mechanical_state.value,
        new_primary_state=point.state.primary_state.value,
        old_orthogonal_states=tuple(pre_response.state_events.quality_solve_state.split("|")),
        new_orthogonal_states=tuple(post_response.state_events.quality_solve_state.split("|")),
        support_ids=post_response.geometry_contact.active_support_ids,
        branch_id=post_response.linearization.branch_id,
        path_coordinate_mm=event_path_mm,
        cycle_id=f"cycle:{point.state.contact_cycle_id}",
        pre_wrench_global_at_o_n_n_mm=pre_response.wrench.wrench_a_on_b,
        event_wrench_global_at_o_n_n_mm=event_response.wrench.wrench_a_on_b,
        post_wrench_global_at_o_n_n_mm=post_response.wrench.wrench_a_on_b,
        pre_beam_energy_n_mm=pre_response.structure.beam_energy_n_mm,
        post_beam_energy_n_mm=post_response.structure.beam_energy_n_mm,
        pre_spring_energy_n_mm=pre_response.structure.spring_energy_n_mm,
        post_spring_energy_n_mm=post_response.structure.spring_energy_n_mm,
        remaining_stored_energy_n_mm=post_response.work.remaining_stored_energy_n_mm,
        released_recoverable_energy_n_mm=(post_response.work.returned_recoverable_energy_n_mm),
        one_sided_consistency=post_response.state_events.event_one_sided_consistency,
    )
    return core, payload


def _standalone_operation_row(
    *,
    request: StandaloneSingleSpineRunRequest,
    execution: StandaloneExecution,
    segment: OperationSegmentRecord,
    point_by_id: dict[str, StandaloneAcceptedPointRecord],
    point_trials: dict[str, StandaloneTrialSnapshot],
) -> ReleaseOperationHistoryRecord:
    if not segment.accepted_point_ids:
        raise ContractViolation(
            "canonical standalone operation segment requires an accepted endpoint"
        )
    point_id = segment.accepted_point_ids[-1]
    point = point_by_id.get(point_id)
    if point is None:
        raise ContractViolation("operation segment references an unknown accepted endpoint")
    response = _required_trial_response(point_trials[point_id])
    if segment.physical_operation_time_available:
        time_status = m03_status(feasibility=PhysicalFeasibility.FEASIBLE)
    else:
        time_status = m03_status(
            "PHYSICAL_OPERATION_TIME_UNAVAILABLE",
            capability=CapabilityStatus.NOT_APPLICABLE,
            outcome=AttemptOutcome.NOT_ATTEMPTED,
            explanation="The segment has no declared speed/time mapping.",
        )
    hard_passed = all(item.passed for item in response.diagnostics.residual_blocks if item.hard)
    return ReleaseOperationHistoryRecord(
        run_id=request.run_id,
        case_id=request.case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=m03_status(feasibility=PhysicalFeasibility.FEASIBLE),
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=m03_maturity(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        operation_record_id=segment.operation_segment_id,
        point_id=point_id,
        commit_receipt_id=None,
        event_id=(segment.committed_event_ids[-1] if segment.committed_event_ids else None),
        cycle_id=f"cycle:{point.state.contact_cycle_id}",
        operation_phase=segment.phase.value,
        segment_id=segment.operation_segment_id,
        interpolation=segment.interpolation,
        path_coordinate_kind=segment.path_coordinate_id,
        path_coordinate_mm=segment.end_coordinate,
        x_total_mm=point.drag_path_x_mm,
        physical_operation_time_s=segment.operation_elapsed_time_s,
        physical_operation_time_status=time_status,
        swept_envelope_id=segment.swept_envelope_ref,
        signed_guard_payloads=tuple(
            {
                "channel_id": channel_id,
                "raw_guard": None,
                "evidence_status": "VALUE_RETAINED_IN_EVENT_OR_TRIAL_RESPONSE",
            }
            for channel_id in segment.signed_guard_channel_ids
        ),
        quality_gate_passed=hard_passed,
        termination_kind=segment.termination_condition,
        lifecycle_kind=segment.termination_reason,
        remaining_travel_mm=max(0.0, request.drag_policy.travel_mm - point.drag_path_x_mm),
        remaining_stored_energy_n_mm=response.work.remaining_stored_energy_n_mm,
    )


def _standalone_cycle_rows(
    request: StandaloneSingleSpineRunRequest,
    execution: StandaloneExecution,
) -> tuple[ContactCycleRecord, ...]:
    groups: dict[int, list[StandaloneAcceptedPointRecord]] = {}
    for point in execution.accepted_points:
        groups.setdefault(point.state.contact_cycle_id, []).append(point)
    event_by_point: dict[str, list[StandaloneCommittedEventRecord]] = {}
    for event in execution.committed_events:
        event_by_point.setdefault(event.accepted_point_id, []).append(event)
    rows: list[ContactCycleRecord] = []
    for cycle_number, points in sorted(groups.items()):
        contact_points = tuple(item for item in points if item.state.active_supports)
        if not contact_points:
            continue
        cycle_events = tuple(
            event for point in points for event in event_by_point.get(point.accepted_point_id, ())
        )
        release = next(
            (
                item
                for item in cycle_events
                if item.event_kind == M03EventKind.CONTACT_RELEASE.value
            ),
            None,
        )
        recontact = next(
            (
                item
                for item in cycle_events
                if item.event_kind == M03EventKind.RECONTACT_ZERO_LOAD.value
            ),
            None,
        )
        reengagement = next(
            (item for item in cycle_events if item.event_kind == M03EventKind.REENGAGEMENT.value),
            None,
        )
        right_censored = release is None
        lifecycle = (
            "RELEASE_RECONTACT_REENGAGED"
            if release is not None and recontact is not None and reengagement is not None
            else "RELEASED"
            if release is not None
            else "CONTACT_ACTIVE_RIGHT_CENSORED"
        )
        first = contact_points[0]
        last = points[-1]
        rows.append(
            ContactCycleRecord(
                run_id=request.run_id,
                case_id=request.case_id,
                schema_version=M03_SCHEMA_VERSION,
                status=m03_status(feasibility=PhysicalFeasibility.FEASIBLE),
                source_identity=SourceIdentity.DEV_POLICY,
                maturity=m03_maturity(),
                certification_status=CertificationStatus.NOT_CERTIFIABLE,
                cycle_record_id=stable_content_id(
                    "m03_cycle_record",
                    {"case_id": request.case_id, "cycle": cycle_number},
                ),
                cycle_id=f"cycle:{cycle_number}",
                lifecycle_kind=lifecycle,
                start_point_id=first.accepted_point_id,
                end_point_id=last.accepted_point_id,
                commit_receipt_id=None,
                support_ids=tuple(
                    sorted(
                        {
                            support.support_id
                            for item in contact_points
                            for support in item.state.active_supports
                        }
                    )
                ),
                release_event_id=(release.committed_event_id if release is not None else None),
                recontact_event_id=(
                    recontact.committed_event_id if recontact is not None else None
                ),
                reengagement_event_id=(
                    reengagement.committed_event_id if reengagement is not None else None
                ),
                start_x_total_mm=first.drag_path_x_mm,
                end_x_total_mm=last.drag_path_x_mm,
                start_drag_elapsed_time_s=first.drag_elapsed_time_s,
                end_drag_elapsed_time_s=last.drag_elapsed_time_s,
                right_censored=right_censored,
            )
        )
    return tuple(rows)


def _publish_standalone_rejected(
    *,
    writer: ResultWriter,
    request: StandaloneSingleSpineRunRequest,
    record: StandaloneRejectedTrialRecord,
    execution: StandaloneExecution,
    point_by_state: dict[str, StandaloneAcceptedPointRecord],
) -> str:
    snapshot = next(
        (
            item
            for item in execution.trial_snapshots
            if item.request.request_id == record.trial_request_id
            and (
                record.trial_response_hash is None
                or (
                    item.response is not None
                    and item.response.response_hash == record.trial_response_hash
                )
            )
        ),
        None,
    )
    response = snapshot.response if snapshot is not None else None
    feasibility = (
        PhysicalFeasibility.PHYSICAL_INFEASIBLE
        if record.failure_axis is FailureAxis.PHYSICAL_INFEASIBLE
        else PhysicalFeasibility.NOT_ASSESSED
    )
    status = dataclasses.replace(
        m03_status(
            record.reason_code,
            outcome=AttemptOutcome.REJECTED_TRIAL,
            feasibility=feasibility,
            explanation="Standalone trial was rejected without advancing accepted history.",
        ),
        last_valid_state_id=record.parent_state_id,
    )
    request_hash = (
        snapshot.request.request_hash
        if snapshot is not None
        else semantic_hash(
            {
                "kind": "m03_unavailable_rejected_request",
                "rejected_trial_id": record.rejected_trial_id,
            }
        )
    )
    candidate_hash = (
        response.response_hash
        if response is not None
        else semantic_hash(
            {
                "kind": "m03_rejected_kernel_exception",
                "request_hash": request_hash,
                "exception": snapshot.exception_detail if snapshot is not None else "UNAVAILABLE",
            },
        )
    )
    parent_point = point_by_state.get(record.parent_state_id)
    parent_point_id = (
        parent_point.accepted_point_id
        if parent_point is not None
        else f"UNAVAILABLE_NO_ACCEPTED_POINT:{record.parent_state_id}"
    )
    if response is not None and response.diagnostics.residual_blocks:
        controlling = max(
            response.diagnostics.residual_blocks,
            key=lambda item: item.normalized_norm,
        )
        raw_residual = controlling.raw_norm
        raw_residual_unit = controlling.raw_unit
    else:
        raw_residual = 1.0
        raw_residual_unit = "kernel_exception_indicator"
    guard = None
    guard_unit = None
    if response is not None and response.state_events.all_event_candidates:
        candidate = min(
            response.state_events.all_event_candidates,
            key=lambda item: abs(item.raw_guard),
        )
        guard = candidate.raw_guard
        guard_unit = candidate.raw_guard_unit
    rollback_token = (
        response.transaction.rollback_token
        if response is not None
        else stable_content_id(
            "m03_side_effect_free_exception_rollback",
            {"request_hash": request_hash, "parent_state_id": record.parent_state_id},
        )
    )
    core = RejectedTrialBase(
        trial_id=record.rejected_trial_id,
        run_id=request.run_id,
        case_id=request.case_id,
        parent_accepted_state_id=record.parent_state_id,
        request_hash=request_hash,
        candidate_hash=candidate_hash,
        requested_path_target=None,
        status=status,
        reason_codes=(record.reason_code,),
        diagnostic_summary=(
            snapshot.exception_detail
            if snapshot is not None and snapshot.exception_detail is not None
            else f"{record.operation_phase.value}: {record.reason_code}"
        ),
        optional_full_payload_ref=f"m03.rejected_diagnostics#{record.rejected_trial_id}",
        last_valid_state_id=record.parent_state_id,
        source_identity=SourceIdentity.DEV_POLICY,
    )
    diagnostic = RejectedDiagnosticRecord(
        run_id=request.run_id,
        case_id=request.case_id,
        schema_version=M03_SCHEMA_VERSION,
        status=status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=m03_maturity(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        diagnostic_id=stable_content_id(
            "m03_rejected_diagnostic", {"trial_id": record.rejected_trial_id}
        ),
        trial_id=record.rejected_trial_id,
        attempt_kind=f"STANDALONE_{record.operation_phase.value}",
        parent_point_id=parent_point_id,
        parent_accepted_state_id=record.parent_state_id,
        reason_family=record.failure_axis.value,
        reason_code=record.reason_code,
        failure_axis=record.failure_axis.value,
        raw_residual=raw_residual,
        raw_residual_unit=raw_residual_unit,
        raw_guard=guard,
        raw_guard_unit=guard_unit,
        solver_trace_ref=(response.response_id if response is not None else None),
        surface_quality=(
            response.diagnostics.surface_data_quality
            if response is not None
            else "UNAVAILABLE_KERNEL_EXCEPTION"
        ),
        rollback_token=rollback_token,
        accepted_state_advanced=False,
        path_advanced=False,
        time_advanced=False,
        slip_advanced=False,
        work_advanced=False,
        cycle_advanced=False,
        event_history_advanced=False,
    )
    dataset_hashes = {
        RejectedTrialBase.__dataset_id__: semantic_hash([writer.registry.storage_dict(core)]),
        RejectedDiagnosticRecord.__dataset_id__: semantic_hash(
            [writer.registry.storage_dict(diagnostic)]
        ),
    }
    expected_content_hash = semantic_hash(
        {key: value for key, value in sorted(dataset_hashes.items())}
    )
    for _, marker in rejected_diagnostic_markers(writer.root):
        if marker.get("trial_id") != core.trial_id:
            continue
        if marker.get("semantic_content_hash") != expected_content_hash:
            raise IdempotencyConflict(
                "standalone rejected-trial identity was reused for different diagnostics",
                details={"trial_id": core.trial_id},
            )
        entry = marker.get("datasets", {}).get(RejectedTrialBase.__dataset_id__)
        existing_path = entry.get("path") if isinstance(entry, dict) else None
        if not isinstance(existing_path, str):
            raise ContractViolation("existing rejected diagnostic marker is malformed")
        return (writer.root / existing_path).as_posix()
    return writer.record_rejected_trial(core, extension_records=(diagnostic,)).as_posix()


def _assert_response_matches_request(
    request: EmbeddedSingleSpineTrialRequest,
    response: SingleSpineTrialResponse,
) -> None:
    if response.transaction.request_hash != request.request_hash:
        raise ContractViolation("cannot persist a response for a different M03 request")
    if response.contract_id != request.contract_id or response.contract_version != (
        request.contract_version
    ):
        raise ContractViolation("cannot persist an incompatible A-to-B response")


def _assert_response_acceptance_quality(response: SingleSpineTrialResponse) -> None:
    """Reject probe/retry/failed-quality responses at every accepted adapter."""

    diagnostics = response.diagnostics
    if diagnostics.failure_axis is not FailureAxis.NONE:
        raise ContractViolation("failed M03 response cannot become accepted history")
    if diagnostics.error_class not in {
        EmbeddedErrorClass.OK,
        EmbeddedErrorClass.OPEN_RESPONSE,
        EmbeddedErrorClass.EQUILIBRIUM_DEGENERATE,
    }:
        raise ContractViolation(
            "M03 response class is not eligible for accepted history",
            details={"error_class": diagnostics.error_class.value},
        )
    if not diagnostics.residual_blocks:
        raise ContractViolation("accepted M03 response requires explicit residual blocks")
    failed_hard = tuple(
        item.block_id for item in diagnostics.residual_blocks if item.hard and not item.passed
    )
    if failed_hard:
        raise ContractViolation(
            "M03 response failed hard residual acceptance quality",
            details={"residual_blocks": failed_hard},
        )
    if response.state_events.quality_solve_state == "QUALITY_REJECTED":
        raise ContractViolation("QUALITY_REJECTED M03 response cannot become accepted history")


def _assert_event_reassembly_responses(
    *,
    event: StandaloneCommittedEventRecord,
    pre_response: SingleSpineTrialResponse,
    event_response: SingleSpineTrialResponse,
    post_response: SingleSpineTrialResponse,
) -> None:
    """Defend publication against replayed or incomplete event-side evidence."""

    for response in (pre_response, event_response, post_response):
        _assert_response_acceptance_quality(response)
    if (
        pre_response.response_hash != event.pre_event_response_hash
        or event_response.response_hash != event.response_hash
        or post_response.response_hash != event.post_event_response_hash
    ):
        raise ContractViolation("standalone event response hashes do not match retained evidence")
    if (
        len(
            {
                pre_response.response_hash,
                event_response.response_hash,
                post_response.response_hash,
            }
        )
        != 3
    ):
        raise ContractViolation(
            "standalone event persistence forbids pre/event/post response reuse"
        )
    accepted_versions = {
        pre_response.transaction.accepted_history_version_read,
        event_response.transaction.accepted_history_version_read,
        post_response.transaction.accepted_history_version_read,
    }
    damage_versions = {
        pre_response.transaction.damage_snapshot_version_read,
        event_response.transaction.damage_snapshot_version_read,
        post_response.transaction.damage_snapshot_version_read,
    }
    if len(accepted_versions) != 1 or len(damage_versions) != 1:
        raise ContractViolation("standalone event sides did not read the same parent versions")
    if not post_response.state_events.event_one_sided_consistency:
        raise ContractViolation("standalone event post-side failed one-sided consistency")


def _required(value: float | None) -> float:
    if value is None:
        raise ContractViolation("required accepted M03 numeric field is unavailable")
    return value


__all__ = [
    "AcceptedRecordContext",
    "AcceptedResultRecords",
    "StandalonePersistenceContext",
    "StandalonePersistenceResult",
    "accepted_records_from_evaluation",
    "accepted_state_from_response",
    "persist_standalone_execution",
    "run_request_record_from_embedded",
]
