from __future__ import annotations

import dataclasses
import math
from types import SimpleNamespace
from typing import Any

import pytest

from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import CapabilityStatus
from spine_sim.single_spine.contracts import (
    ContactMotionState,
    EmbeddedErrorClass,
    EmbeddedSingleSpineTrialRequest,
    FailureAxis,
    LODPurpose,
    MaterialSubstate,
    NeedleIdentity,
    NeedleStrengthSubstate,
    PrescribedBaseIncrement,
    PrimaryMechanicalState,
    TangentStatus,
    TrialIdentity,
    canonical_local_frame,
    make_baseline_parameter_bundle,
    make_embedded_request,
    make_initial_single_spine_state,
    make_rigid_pose,
)
from spine_sim.single_spine.events import (
    M03EventKind,
    M03EventProbeContext,
    bridge_residual_blocks_to_m02,
    bridge_response_to_m02_event_snapshot,
    raw_signed_guards_from_response,
)
from spine_sim.single_spine.geometry import engineering_initial_axis
from spine_sim.single_spine.kernel import (
    IntrinsicSingleSpineKernel,
    _classify_response,
    make_needle_identity,
)
from spine_sim.single_spine.persistence import (
    AcceptedRecordContext,
    accepted_records_from_evaluation,
    accepted_state_from_response,
    run_request_record_from_embedded,
)
from spine_sim.single_spine.surface_adapter import (
    BodyCollisionStatus,
    GeometryGateStatus,
    make_geometry_query_policy,
)
from spine_sim.surface import SurfaceFamily, SurfaceProvider, make_analytic_source_descriptor


def _plane_handle() -> Any:
    provider = SurfaceProvider()
    source = make_analytic_source_descriptor()
    spec = provider.create_surface_spec(source, SurfaceFamily.PLANE, {"offset_mm": 0.0}).spec
    assert spec is not None
    handle = provider.create_realization(source, spec).handle
    assert handle is not None
    return handle


def _request(
    *,
    center_height_mm: float,
    dx_mm: float = 0.0,
    dz_mm: float = 0.0,
    friction_coefficient: float = 0.40,
):
    bundle = make_baseline_parameter_bundle(friction_coefficient=friction_coefficient)
    frame = canonical_local_frame()
    axis = engineering_initial_axis(frame, bundle.needle.alpha_rad, bundle.needle.beta_rad)
    root = (
        75.0 - bundle.needle.exposed_length_mm * axis[0],
        75.0 - bundle.needle.exposed_length_mm * axis[1],
        center_height_mm - bundle.needle.exposed_length_mm * axis[2],
    )
    pose = make_rigid_pose(root)
    state = make_initial_single_spine_state(pose)
    request = make_embedded_request(
        needle_identity=make_needle_identity(bundle),
        surface_query_handle=_plane_handle(),
        base_pose_n=pose,
        prescribed_base_increment=PrescribedBaseIncrement(
            (dx_mm, 0.0, dz_mm),
            (0.0, 0.0, 0.0),
            "linear_translation_global",
            ("ux_global", "uy_global", "uz_global"),
            "GLOBAL",
            "M03_BASE_REFERENCE_O",
        ),
        immutable_single_spine_state_n=state,
        parameter_bundle=bundle,
        trial_identity=TrialIdentity("step-0", "trial-0", "newton-0", "caller-0"),
    )
    return bundle, state, request


def test_embedded_open_is_exact_positive_zero_and_trial_is_side_effect_free() -> None:
    _, state, request = _request(center_height_mm=0.15)
    state_before = dataclasses.asdict(state)
    realization_id = request.surface_query_handle.realization.surface_realization_id

    response = IntrinsicSingleSpineKernel().evaluate_trial(request)

    assert response.diagnostics.error_class is EmbeddedErrorClass.OPEN_RESPONSE
    assert response.state_events.primary_mechanical_state is PrimaryMechanicalState.OPEN
    assert response.wrench.wrench_a_on_b == (0.0,) * 6
    assert response.wrench.opposite_wrench_b_on_a == (0.0,) * 6
    assert all(math.copysign(1.0, value) == 1.0 for value in response.wrench.wrench_a_on_b)
    assert response.linearization.tangent_or_secant_matrix == ((0.0,) * 6,) * 6
    assert not response.state_events.five_stage.geometric_candidate.value
    assert not response.state_events.five_stage.loaded_contact.value
    guards = {
        item.event_kind: item.raw_guard for item in response.state_events.all_event_candidates
    }
    assert guards[M03EventKind.CONTACT_LOAD_ONSET.value] == pytest.approx(
        -request.parameter_bundle.numerical.acceptance_force_resolution_n
    )
    assert M03EventKind.CONTACT_RELEASE.value not in guards
    assert M03EventKind.FRICTION_CONE_REACHED.value not in guards
    assert guards[M03EventKind.SPRING_ORIGINAL_LENGTH.value] == 0.0
    assert guards[M03EventKind.SPRING_HARD_STOP.value] == pytest.approx(4.0)
    assert dataclasses.asdict(state) == state_before
    assert request.surface_query_handle.realization.surface_realization_id == realization_id
    assert response.transaction.accepted_history_version_read == state.state_version
    assert not response.transaction.damage_intents
    assert not response.transaction.damage_write_set


def test_body_query_failure_reason_precedes_unrelated_candidate_ok_status() -> None:
    error, axis, reason_codes = _classify_response(
        SimpleNamespace(gate_status=GeometryGateStatus.PASSED, reason_code="M01_OK"),
        SimpleNamespace(
            status=BodyCollisionStatus.GEOMETRY_UNCERTAIN,
            reason_code="M01_QUERY_TOLERANCE_UNMET",
        ),
        SimpleNamespace(),
        SimpleNamespace(),
        False,
    )

    assert error is EmbeddedErrorClass.GEOMETRY_UNCERTAIN
    assert axis is FailureAxis.CAPABILITY_UNAVAILABLE
    assert reason_codes == ("M01_QUERY_TOLERANCE_UNMET",)


def test_loaded_plane_response_reports_independent_work_mismatch_without_false_closure() -> None:
    bundle, state, request = _request(
        center_height_mm=bundle_tip_height(),
        dz_mm=-0.01,
    )
    kernel = IntrinsicSingleSpineKernel()
    evaluation = kernel.evaluate_trial_with_artifacts(request)
    response = evaluation.response

    assert response.diagnostics.error_class is EmbeddedErrorClass.NUMERICAL_NONCONVERGENCE
    assert response.diagnostics.failure_axis is FailureAxis.NUMERICAL_FAILURE
    assert response.diagnostics.original_reason_codes == ("M03_HARD_RESIDUAL_QUALITY_FAILED",)
    assert response.state_events.primary_mechanical_state is PrimaryMechanicalState.ATTACHED_SLIDE
    assert response.state_events.per_contact_motion_states == (
        ContactMotionState.SLIDING_COMMITTED,
    )
    assert response.wrench.opposite_wrench_b_on_a == tuple(
        -value for value in response.wrench.wrench_a_on_b
    )
    assert response.wrench.grip_resistance_rx_n == pytest.approx(-response.wrench.force_global_n[0])
    assert response.wrench.task_resistance_n == pytest.approx(response.wrench.grip_resistance_rx_n)
    assert response.wrench.reference_transport_work_invariant
    assert response.wrench.force_global_n == pytest.approx(
        evaluation.artifacts.contact_graph.resultant_force_global_n
    )
    assert response.structure.optional_contact_compression_mm is None
    assert response.structure.optional_contact_energy_n_mm == 0.0
    assert response.material_damage.material_substate is MaterialSubstate.NO_DAMAGE_MODEL
    assert response.material_damage.status.capability_status is CapabilityStatus.NOT_APPLICABLE
    assert response.material_damage.initiation_utilization is None
    assert response.material_damage.current_capacity_scale is None
    assert response.material_damage.fracture_energy_n_per_mm is None
    assert not response.material_damage.failure_prediction_allowed
    assert not response.material_damage.trial_damage_intents
    assert not response.material_damage.damage_write_set
    assert response.structure.yield_margin is None
    assert response.structure.fracture_margin is None
    assert (
        response.structure.needle_strength_status
        is NeedleStrengthSubstate.NEEDLE_STRENGTH_UNAVAILABLE
    )
    assert response.work.material_dissipation_n_mm == 0.0
    independent_trapezoid = -0.5 * sum(
        force * increment
        for force, increment in zip(
            response.wrench.force_global_n,
            request.prescribed_base_increment.translation_global_mm,
            strict=True,
        )
    )
    energy_identity = (
        response.work.delta_beam_energy_n_mm
        + response.work.delta_spring_energy_n_mm
        + response.work.friction_dissipation_n_mm
    )
    assert response.work.base_or_actuator_input_work_n_mm == pytest.approx(independent_trapezoid)
    assert response.work.base_or_actuator_input_work_n_mm != pytest.approx(energy_identity)
    assert response.work.closure_error_n_mm == pytest.approx(
        independent_trapezoid - energy_identity
    )
    assert response.work.normalized_closure_error > 0.01
    work_residual = next(
        item for item in response.diagnostics.residual_blocks if item.block_id == "work_closure"
    )
    assert not work_residual.passed
    assert response.state_events.quality_solve_state == "QUALITY_REJECTED"
    assert response.state_events.terminal_or_continuable == "REJECTED_TRIAL"
    assert not response.state_events.event_one_sided_consistency
    assert response.linearization.tangent_or_secant_matrix is None
    assert response.linearization.tangent_status is TangentStatus.BRANCH_DEPENDENT
    assert not all(item.passed for item in response.diagnostics.residual_blocks if item.hard)
    assert state.total_path_x_mm == 0.0
    assert state.drag_elapsed_time_s == 0.0
    assert evaluation.artifacts.body_collision.status.value == "CLEAR"
    assert request.parameter_bundle == bundle

    guards = raw_signed_guards_from_response(response)
    assert {item.event_kind for item in guards} == {
        M03EventKind.TIP_CONTACT_ESTABLISH,
        M03EventKind.TIP_CONTACT_TANGENCY,
        M03EventKind.CONTACT_LOAD_ONSET,
        M03EventKind.CONTACT_RELEASE,
        M03EventKind.FRICTION_CONE_REACHED,
        M03EventKind.ALL_STICK_BRANCH_LOSS,
        M03EventKind.SLIP_ONSET_CONFIRMED,
        M03EventKind.CAP_LEGALITY_LOSS,
        M03EventKind.SPRING_ORIGINAL_LENGTH,
        M03EventKind.SPRING_HARD_STOP,
        M03EventKind.CONE_COLLISION,
        M03EventKind.SHAFT_COLLISION,
        M03EventKind.MOUNT_COLLISION,
        M03EventKind.STRUCTURAL_MODEL_LIMIT,
    }
    by_kind = {item.event_kind: item for item in guards}
    assert by_kind[M03EventKind.CONTACT_LOAD_ONSET].raw_value > 0.0
    assert by_kind[M03EventKind.ALL_STICK_BRANCH_LOSS].raw_value < 0.0
    assert by_kind[M03EventKind.SLIP_ONSET_CONFIRMED].raw_value > 0.0

    _, _, open_request = _request(center_height_mm=0.15)
    open_response = kernel.evaluate_trial(open_request)
    open_guards = raw_signed_guards_from_response(open_response)
    snapshot = bridge_response_to_m02_event_snapshot(
        open_response,
        M03EventProbeContext("trial-0", 0.01, 1.0),
    )
    assert set(snapshot.raw_guard_values) == {item.channel_id for item in open_guards}
    assert len(bridge_residual_blocks_to_m02(response)) == len(response.diagnostics.residual_blocks)

    context = AcceptedRecordContext(
        run_id="run:m03-kernel-test",
        case_id="case:m03-kernel-test",
        point_id="point:m03-kernel-test",
        parent_point_id=None,
        accepted_state_id="state:m03-kernel-test",
        parent_accepted_state_id=state.state_id,
        config_hash=request.parameter_bundle.parameter_bundle_hash,
        accepted_point_index=0,
        x_total_mm=0.0,
        drag_elapsed_time_s=0.0,
        operation_phase="EMBEDDED_TRIAL_ACCEPT",
        operation_path_coordinate_mm=0.0,
        cycle_id="cycle:0",
        event_sequence=0,
        start_point_id_for_work="point:m03-initial",
    )
    with pytest.raises(ContractViolation, match=r"accepted|quality"):
        accepted_records_from_evaluation(
            context=context,
            request=request,
            evaluation=evaluation,
        )
    request_record = run_request_record_from_embedded(
        run_id=context.run_id,
        case_id=context.case_id,
        request=request,
        config_hash=context.config_hash,
    )
    assert request_record.request_hash == request.request_hash
    assert request_record.commit_receipt_id is None
    with pytest.raises(ContractViolation, match=r"accepted|quality"):
        accepted_state_from_response(
            request=request,
            response=response,
            total_path_x_mm=0.0,
            drag_elapsed_time_s=0.0,
            contact_cycle_id=0,
            event_sequence_number=0,
        )
    assert state.state_version == 0


def test_loaded_smooth_branch_does_not_advertise_an_unassembled_tangent() -> None:
    _, _, request = _request(
        center_height_mm=bundle_tip_height(),
        dz_mm=-0.01,
        friction_coefficient=10.0,
    )

    response = IntrinsicSingleSpineKernel().evaluate_trial(request)

    assert response.linearization.branch_id == "ONE_SIDED_ALL_STICK"
    assert response.linearization.tangent_or_secant_matrix is None
    assert response.linearization.tangent_status is TangentStatus.UNAVAILABLE


def test_accepted_adapters_reject_reduction_failure_and_hard_quality_responses() -> None:
    _, parent_state, request = _request(center_height_mm=0.15)
    evaluation = IntrinsicSingleSpineKernel().evaluate_trial_with_artifacts(request)
    response = evaluation.response
    context = AcceptedRecordContext(
        run_id="run:m03-acceptance-gate",
        case_id="case:m03-acceptance-gate",
        point_id="point:m03-acceptance-gate",
        parent_point_id=None,
        accepted_state_id="state:m03-acceptance-gate",
        parent_accepted_state_id=parent_state.state_id,
        config_hash=request.parameter_bundle.parameter_bundle_hash,
        accepted_point_index=0,
        x_total_mm=0.0,
        drag_elapsed_time_s=0.0,
        operation_phase="EMBEDDED_TRIAL_ACCEPT",
        operation_path_coordinate_mm=0.0,
        cycle_id="cycle:0",
        event_sequence=0,
        start_point_id_for_work="point:m03-initial",
    )
    failed_residual = dataclasses.replace(
        response.diagnostics.residual_blocks[0],
        raw_norm=1.0,
        reference_norm=1.0,
        normalized_norm=2.0,
        passed=False,
    )
    bad_responses = (
        dataclasses.replace(
            response,
            diagnostics=dataclasses.replace(
                response.diagnostics,
                error_class=EmbeddedErrorClass.EVENT_REDUCTION_REQUIRED,
            ),
        ),
        dataclasses.replace(
            response,
            diagnostics=dataclasses.replace(
                response.diagnostics,
                error_class=EmbeddedErrorClass.NUMERICAL_NONCONVERGENCE,
                failure_axis=FailureAxis.NUMERICAL_FAILURE,
            ),
        ),
        dataclasses.replace(
            response,
            diagnostics=dataclasses.replace(
                response.diagnostics,
                residual_blocks=(
                    failed_residual,
                    *response.diagnostics.residual_blocks[1:],
                ),
            ),
        ),
    )

    for bad_response in bad_responses:
        with pytest.raises(ContractViolation, match=r"accepted|acceptance quality"):
            accepted_state_from_response(
                request=request,
                response=bad_response,
                total_path_x_mm=0.0,
                drag_elapsed_time_s=0.0,
                contact_cycle_id=0,
                event_sequence_number=0,
            )
        with pytest.raises(ContractViolation, match=r"accepted|acceptance quality"):
            accepted_records_from_evaluation(
                context=context,
                request=request,
                evaluation=dataclasses.replace(evaluation, response=bad_response),
            )


def test_signed_input_work_is_preserved_in_state_and_ledger_cumulative_sum() -> None:
    _, parent_state, request = _request(center_height_mm=0.15)
    evaluation = IntrinsicSingleSpineKernel().evaluate_trial_with_artifacts(request)
    signed_response = dataclasses.replace(
        evaluation.response,
        work=dataclasses.replace(
            evaluation.response.work,
            base_or_actuator_input_work_n_mm=-0.25,
        ),
    )
    state = accepted_state_from_response(
        request=request,
        response=signed_response,
        total_path_x_mm=0.0,
        drag_elapsed_time_s=0.0,
        contact_cycle_id=0,
        event_sequence_number=0,
    )
    context = AcceptedRecordContext(
        run_id="run:m03-signed-work",
        case_id="case:m03-signed-work",
        point_id="point:m03-signed-work",
        parent_point_id=None,
        accepted_state_id=state.state_id,
        parent_accepted_state_id=parent_state.state_id,
        config_hash=request.parameter_bundle.parameter_bundle_hash,
        accepted_point_index=0,
        x_total_mm=0.0,
        drag_elapsed_time_s=0.0,
        operation_phase="EMBEDDED_TRIAL_ACCEPT",
        operation_path_coordinate_mm=0.0,
        cycle_id="cycle:0",
        event_sequence=0,
        start_point_id_for_work="point:m03-initial",
    )
    records = accepted_records_from_evaluation(
        context=context,
        request=request,
        evaluation=dataclasses.replace(evaluation, response=signed_response),
    )

    assert state.cumulative_input_work_n_mm == pytest.approx(-0.25)
    assert records.work.base_or_actuator_input_work_n_mm == pytest.approx(-0.25)
    assert records.work.cumulative_input_work_n_mm == pytest.approx(-0.25)


def test_kernel_loaded_contact_uses_pure_tangential_objective_increment() -> None:
    kernel = IntrinsicSingleSpineKernel()
    _, _, stationary_request = _request(
        center_height_mm=bundle_tip_height() - 0.01,
        friction_coefficient=100.0,
    )
    _, _, tangential_request = _request(
        center_height_mm=bundle_tip_height() - 0.01,
        dx_mm=0.001,
        friction_coefficient=100.0,
    )

    stationary = kernel.evaluate_trial_with_artifacts(stationary_request).artifacts.contact_graph
    tangential = kernel.evaluate_trial_with_artifacts(tangential_request).artifacts.contact_graph
    stationary_support = stationary.supports[0]
    tangential_support = tangential.supports[0]

    assert stationary.branch_id == tangential.branch_id == "ONE_SIDED_ALL_STICK"
    assert stationary.graph_quality_passed and tangential.graph_quality_passed
    assert tangential_support.tangential_multiplier_n != pytest.approx(
        stationary_support.tangential_multiplier_n
    )
    assert math.hypot(*tangential_support.objective_slip_increment_local_mm) <= 1.0e-12


def test_kernel_cone_boundary_without_objective_slip_is_not_committed_slide() -> None:
    _, _, interior_request = _request(
        center_height_mm=bundle_tip_height(),
        dz_mm=-0.01,
        friction_coefficient=10.0,
    )
    kernel = IntrinsicSingleSpineKernel()
    interior = kernel.evaluate_trial_with_artifacts(interior_request)
    interior_support = interior.artifacts.contact_graph.supports[0]
    boundary_mu = math.hypot(*interior_support.tangential_multiplier_n) / (
        interior_support.normal_multiplier_n
    )
    _, _, boundary_request = _request(
        center_height_mm=bundle_tip_height(),
        dz_mm=-0.01,
        friction_coefficient=boundary_mu,
    )

    evaluation = kernel.evaluate_trial_with_artifacts(boundary_request)
    response = evaluation.response

    assert response.diagnostics.error_class is EmbeddedErrorClass.NUMERICAL_NONCONVERGENCE
    assert response.linearization.branch_id == "ONE_SIDED_ALL_STICK"
    assert evaluation.artifacts.contact_graph.branch_feasible
    assert evaluation.artifacts.contact_graph.graph_quality_passed
    assert response.state_events.per_contact_motion_states == (
        ContactMotionState.STICKING_AT_CONE_BOUNDARY,
    )
    assert ContactMotionState.SLIDING_COMMITTED not in (
        response.state_events.per_contact_motion_states
    )
    guards = {
        item.event_kind: item.raw_guard for item in response.state_events.all_event_candidates
    }
    assert guards[M03EventKind.FRICTION_CONE_REACHED.value] == pytest.approx(0.0)
    assert guards[M03EventKind.ALL_STICK_BRANCH_LOSS.value] == pytest.approx(0.0)
    assert M03EventKind.SLIP_ONSET_CONFIRMED.value not in guards


def test_intrinsic_plane_rt8_to_rt10_witness_preserves_guards_support_force_and_work() -> None:
    bundle, _, request = _request(
        center_height_mm=bundle_tip_height(),
        dz_mm=-0.01,
    )
    event = IntrinsicSingleSpineKernel(
        query_policy=make_geometry_query_policy(LODPurpose.EVENT_SUPPORT)
    ).evaluate_trial(request)
    acceptance = IntrinsicSingleSpineKernel(
        query_policy=make_geometry_query_policy(LODPurpose.ACCEPTANCE_WITNESS)
    ).evaluate_trial(request)

    assert event.geometry_contact.lod_purpose is LODPurpose.EVENT_SUPPORT
    assert acceptance.geometry_contact.lod_purpose is LODPurpose.ACCEPTANCE_WITNESS
    event_support = event.geometry_contact.supports[0]
    acceptance_support = acceptance.geometry_contact.supports[0]
    assert math.dist(event_support.point_global_mm, acceptance_support.point_global_mm) <= (
        0.02 * bundle.needle.tip_radius_mm
    )
    normal_dot = sum(
        left * right
        for left, right in zip(
            event_support.normal_global,
            acceptance_support.normal_global,
            strict=True,
        )
    )
    normal_angle_deg = math.degrees(math.acos(max(-1.0, min(1.0, normal_dot))))
    assert normal_angle_deg <= 1.0
    assert event.wrench.force_global_n == pytest.approx(
        acceptance.wrench.force_global_n,
        rel=0.01,
        abs=1.0e-12,
    )
    assert event.work.base_or_actuator_input_work_n_mm == pytest.approx(
        acceptance.work.base_or_actuator_input_work_n_mm,
        rel=0.01,
        abs=1.0e-12,
    )
    event_guards = event.state_events.all_event_candidates
    acceptance_guards = acceptance.state_events.all_event_candidates
    assert tuple(item.event_kind for item in event_guards) == tuple(
        item.event_kind for item in acceptance_guards
    )
    assert tuple(item.raw_guard for item in event_guards) == pytest.approx(
        tuple(item.raw_guard for item in acceptance_guards),
        rel=0.01,
        abs=1.0e-12,
    )


def bundle_tip_height() -> float:
    return make_baseline_parameter_bundle().needle.tip_radius_mm


def test_same_trial_is_semantically_deterministic_and_does_not_mint_history() -> None:
    _, state, request = _request(center_height_mm=0.15)
    kernel = IntrinsicSingleSpineKernel()
    first = kernel.evaluate_trial(request)
    second = kernel.evaluate_trial(request)
    assert first == second
    assert first.response_hash == second.response_hash
    assert first.response_id == second.response_id
    assert first.transaction.idempotency_key == second.transaction.idempotency_key
    assert state.state_version == 0
    assert state.accepted_response_hash != first.response_hash


def test_embedded_mapping_rejects_per_spine_pz_before_any_solve() -> None:
    with pytest.raises(ContractViolation, match="DUPLICATE_NORMAL_LOAD"):
        EmbeddedSingleSpineTrialRequest.from_mapping({"Pz": 0.5})
    with pytest.raises(TypeError):
        EmbeddedSingleSpineTrialRequest(Pz=0.5)  # type: ignore[call-arg]


def test_preflight_rejects_parameter_identity_aliasing() -> None:
    _, _, request = _request(center_height_mm=0.15)
    bad_identity = NeedleIdentity(
        request.needle_identity.needle_id,
        request.needle_identity.unit_id,
        "wrong-geometry",
        request.needle_identity.structure_parameter_id,
        request.needle_identity.material_parameter_id,
        request.needle_identity.needle_strength_parameter_id,
    )
    with pytest.raises(ContractViolation, match="identity"):
        dataclasses.replace(request, needle_identity=bad_identity)
