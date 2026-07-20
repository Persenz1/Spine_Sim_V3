from __future__ import annotations

import dataclasses
from dataclasses import fields
from itertools import pairwise
from typing import Any, ClassVar

import pytest

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.numerics.contracts import ReturnPathCapability, ReturnPathMode
from spine_sim.single_spine.contracts import (
    ContactMotionState,
    ContactSupportResponse,
    EmbeddedErrorClass,
    EmbeddedSingleSpineTrialRequest,
    EventCandidateResponse,
    FailureAxis,
    OperationPhase,
    PrimaryMechanicalState,
    SingleSpineTrialResponse,
    SpringState,
    StandaloneTerminalStatus,
    make_baseline_parameter_bundle,
    make_standalone_request,
)
from spine_sim.single_spine.events import M03EventKind, m03_event_spec
from spine_sim.single_spine.geometry import engineering_initial_axis
from spine_sim.single_spine.kernel import IntrinsicSingleSpineKernel
from spine_sim.single_spine.standalone import StandaloneSingleSpineDriver
from spine_sim.surface import SurfaceFamily, SurfaceProvider, make_analytic_source_descriptor


def _plane_handle() -> Any:
    provider = SurfaceProvider()
    source = make_analytic_source_descriptor()
    result = provider.create_surface_spec(source, SurfaceFamily.PLANE, {"offset_mm": 0.0})
    assert result.spec is not None
    realization = provider.create_realization(source, result.spec)
    assert realization.handle is not None
    return realization.handle


class _AnalyticPlaneKernel:
    """Small deterministic constitutive double over a real M01 plane handle.

    It is intentionally injected through the public standalone kernel boundary:
    the test isolates driver scheduling/event ownership from the much richer
    intrinsic mechanics regression suite.
    """

    _shared_template: ClassVar[SingleSpineTrialResponse | None] = None

    def __init__(
        self,
        *,
        release_once: bool = False,
        fail_during_research: bool = False,
    ) -> None:
        self.release_once = release_once
        self.fail_during_research = fail_during_research
        self.calls: list[EmbeddedSingleSpineTrialRequest] = []
        self.embedded_field_names: list[set[str]] = []

    def evaluate_trial(
        self,
        request: EmbeddedSingleSpineTrialRequest,
    ) -> SingleSpineTrialResponse:
        self.calls.append(request)
        self.embedded_field_names.append({item.name for item in fields(request)})
        if self._shared_template is None:
            type(self)._shared_template = IntrinsicSingleSpineKernel().evaluate_trial(request)
        template = self._shared_template
        assert template is not None

        parent = request.immutable_single_spine_state_n
        increment = request.prescribed_base_increment.translation_global_mm
        if (
            self.fail_during_research
            and parent.primary_state is PrimaryMechanicalState.REVERSIBLE_RETURN
            and increment[2] < 0.0
        ):
            raise RuntimeError("injected research failure")
        target_root = tuple(
            parent.base_pose.position_mm[index] + increment[index] for index in range(3)
        )
        axis = engineering_initial_axis(
            request.local_frame,
            request.parameter_bundle.needle.alpha_rad,
            request.parameter_bundle.needle.beta_rad,
        )
        length = request.parameter_bundle.needle.exposed_length_mm
        radius = request.parameter_bundle.needle.tip_radius_mm
        tip_center = (
            target_root[0] + length * axis[0],
            target_root[1] + length * axis[1],
            target_root[2] + length * axis[2],
        )
        gap = tip_center[2] - radius
        penetration = max(0.0, -gap)

        local_x = request.local_frame.e_x_global
        drag_delta = sum(increment[index] * local_x[index] for index in range(3))
        target_x = parent.total_path_x_mm + drag_delta
        release_factor = 1.0
        release_active = self.release_once and parent.contact_cycle_id == 1 and target_x >= 9.0
        if release_active:
            release_factor = max(0.0, min(1.0, 10.0 - target_x))

        stiffness = 0.5
        normal_load = stiffness * penetration * release_factor
        returning = parent.primary_state in {
            PrimaryMechanicalState.RELEASE_TRANSITION,
            PrimaryMechanicalState.REVERSIBLE_RETURN,
        }
        if returning and increment[2] >= 0.0:
            compression = max(0.0, parent.spring_compression_mm - increment[2])
            normal_load = 0.0
        elif release_active:
            # Release removes support while the accepted state still owns the
            # recoverable deformation that the HOLD branch must preserve.
            compression = penetration
        else:
            compression = penetration
        energy = 0.5 * stiffness * compression * compression

        contact_tolerance = (
            radius * request.parameter_bundle.numerical.event_position_tolerance_over_rt
        )
        has_support = gap <= contact_tolerance and not (
            returning and increment[2] > penetration + contact_tolerance
        )
        motion = (
            ContactMotionState.TOUCH_ZERO_LOAD
            if normal_load <= request.parameter_bundle.numerical.acceptance_force_resolution_n
            else ContactMotionState.STICKING_INTERIOR
        )
        support: tuple[ContactSupportResponse, ...] = ()
        if has_support:
            support_id = stable_content_id(
                "test_plane_support",
                {"request_hash": request.request_hash, "gap": gap, "normal": normal_load},
            )
            support = (
                ContactSupportResponse(
                    support_id,
                    f"candidate:{support_id}",
                    (tip_center[0], tip_center[1], 0.0),
                    "SPHERICAL_TIP_CAP",
                    "analytic-plane-chart",
                    gap,
                    gap,
                    (0.0, 0.0, 1.0),
                    ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
                    (0.0, 0.0, normal_load),
                    normal_load,
                    (0.0, 0.0),
                    (0.0, 0.0, 0.0),
                    (0.0, 0.0),
                    parent.total_path_x_mm,
                    motion,
                    False,
                    10.0,
                ),
            )

        if gap > contact_tolerance:
            primary = PrimaryMechanicalState.OPEN
        elif normal_load <= request.parameter_bundle.numerical.acceptance_force_resolution_n:
            primary = (
                PrimaryMechanicalState.RELEASE_TRANSITION
                if release_active and penetration > contact_tolerance
                else PrimaryMechanicalState.TIP_ZERO_LOAD
            )
        else:
            primary = PrimaryMechanicalState.ATTACHED_STICK
        spring_state = (
            SpringState.COMPRESSING
            if compression > contact_tolerance
            else SpringState.AT_ORIGINAL_LENGTH
        )
        body_clearance = 5.0
        receipt_id = stable_content_id(
            "test_plane_query_receipt", {"request_hash": request.request_hash}
        )

        def event_candidate(kind: M03EventKind, value: float) -> EventCandidateResponse:
            spec = m03_event_spec(kind)
            return EventCandidateResponse(
                f"test-{kind.value.lower()}",
                kind.value,
                value,
                spec.raw_guard_unit,
                spec.zero_level,
                spec.admissible_side.value,
                spec.trigger_direction.value,
                None,
                None,
                receipt_id,
            )

        force_resolution = request.parameter_bundle.numerical.acceptance_force_resolution_n
        candidates = (
            event_candidate(M03EventKind.TIP_CONTACT_ESTABLISH, gap),
            event_candidate(M03EventKind.CONTACT_LOAD_ONSET, normal_load - force_resolution),
            event_candidate(M03EventKind.CONTACT_RELEASE, normal_load - force_resolution),
            event_candidate(M03EventKind.CAP_LEGALITY_LOSS, 10.0),
        )
        geometry = dataclasses.replace(
            template.geometry_contact,
            active_support_ids=tuple(item.support_id for item in support),
            near_contact_support_ids=tuple(item.support_id for item in support),
            supports=support,
            candidate_ids=tuple(item.candidate_id for item in support),
            tip_center_global_mm=tip_center,
            current_axis_global=axis,
            initial_axis_global=axis,
            cone_gap_mm=body_clearance,
            shaft_gap_mm=body_clearance,
            mount_gap_mm=body_clearance,
            minimum_full_body_clearance_mm=body_clearance,
            query_receipt_ids=(receipt_id,),
            geometry_uncertainty_mm=0.0,
            footprint_id="analytic-plane-footprint",
            candidate_any=has_support,
            candidate_robust=has_support,
        )
        structure = dataclasses.replace(
            template.structure,
            beam_energy_n_mm=0.0,
            spring_state=spring_state,
            spring_compression_mm=compression,
            spring_force_n=normal_load,
            remaining_spring_travel_mm=max(0.0, 4.0 - compression),
            spring_energy_n_mm=energy,
        )
        state_events = dataclasses.replace(
            template.state_events,
            primary_mechanical_state=primary,
            per_contact_motion_states=tuple(item.motion_state for item in support),
            spring_substate=spring_state,
            all_event_candidates=candidates,
            # This closed-form validation double has a unique analytic plane
            # branch on either side of every guard used by the driver.
            event_one_sided_consistency=True,
            operation_phase=None,
        )
        error_class = (
            EmbeddedErrorClass.OK if normal_load > 0.0 else EmbeddedErrorClass.OPEN_RESPONSE
        )
        diagnostics = dataclasses.replace(
            template.diagnostics,
            error_class=error_class,
            error_detail="analytic plane driver double",
            failure_axis=FailureAxis.NONE,
            original_reason_codes=("M03_OK",),
        )
        work = dataclasses.replace(
            template.work,
            base_or_actuator_input_work_n_mm=max(0.0, drag_delta) * normal_load * 0.01,
            friction_dissipation_n_mm=max(0.0, drag_delta) * normal_load * 0.01,
            remaining_stored_energy_n_mm=energy,
            closure_error_n_mm=0.0,
            normalized_closure_error=0.0,
        )
        response_payload = {
            "model": "test-analytic-plane-kernel-v1",
            "request_hash": request.request_hash,
            "gap_mm": gap,
            "normal_load_n": normal_load,
            "energy_n_mm": energy,
        }
        response_hash = semantic_hash(response_payload)
        transaction = dataclasses.replace(
            template.transaction,
            opaque_trial_state_handle=stable_content_id("test_trial_state", response_payload),
            rollback_token=stable_content_id("test_rollback", response_payload),
            provisional_commit_intent=stable_content_id("test_commit", response_payload),
            accepted_history_version_read=parent.state_version,
            request_hash=request.request_hash,
            response_hash=response_hash,
            idempotency_key=stable_content_id("test_idempotency", response_payload),
        )
        return dataclasses.replace(
            template,
            response_id=stable_content_id("test_plane_response", response_payload),
            response_hash=response_hash,
            geometry_contact=geometry,
            structure=structure,
            state_events=state_events,
            diagnostics=diagnostics,
            work=work,
            transaction=transaction,
        )


class _OneSidedUnavailableKernel(_AnalyticPlaneKernel):
    def evaluate_trial(
        self,
        request: EmbeddedSingleSpineTrialRequest,
    ) -> SingleSpineTrialResponse:
        response = super().evaluate_trial(request)
        return dataclasses.replace(
            response,
            state_events=dataclasses.replace(
                response.state_events,
                event_one_sided_consistency=False,
            ),
        )


class _InitialGeometryUncertainKernel(_AnalyticPlaneKernel):
    """Return an honest M01 capability failure without a physical tip guard."""

    def evaluate_trial(
        self,
        request: EmbeddedSingleSpineTrialRequest,
    ) -> SingleSpineTrialResponse:
        response = super().evaluate_trial(request)
        candidates = tuple(
            item
            for item in response.state_events.all_event_candidates
            if item.event_kind != M03EventKind.TIP_CONTACT_ESTABLISH.value
        )
        return dataclasses.replace(
            response,
            state_events=dataclasses.replace(
                response.state_events,
                all_event_candidates=candidates,
                quality_solve_state="QUALITY_REJECTED",
                event_one_sided_consistency=False,
            ),
            diagnostics=dataclasses.replace(
                response.diagnostics,
                error_class=EmbeddedErrorClass.GEOMETRY_UNCERTAIN,
                error_detail="M01 closest query requires resolution refinement",
                failure_axis=FailureAxis.CAPABILITY_UNAVAILABLE,
                original_reason_codes=(
                    "M01_RESOLUTION_REFINEMENT_REQUIRED",
                    "M03_GEOMETRY_UNCERTAIN",
                ),
            ),
        )


class _SignedReturnWorkKernel(_AnalyticPlaneKernel):
    def evaluate_trial(
        self,
        request: EmbeddedSingleSpineTrialRequest,
    ) -> SingleSpineTrialResponse:
        response = super().evaluate_trial(request)
        parent = request.immutable_single_spine_state_n
        dz = request.prescribed_base_increment.translation_global_mm[2]
        if dz <= 0.0 or parent.primary_state not in {
            PrimaryMechanicalState.RELEASE_TRANSITION,
            PrimaryMechanicalState.REVERSIBLE_RETURN,
        }:
            return response
        signed_work = -0.05
        response_hash = semantic_hash(
            {
                "base_response_hash": response.response_hash,
                "signed_return_work_n_mm": signed_work,
            }
        )
        return dataclasses.replace(
            response,
            response_id=stable_content_id(
                "test_signed_return_response",
                {"response_hash": response_hash},
            ),
            response_hash=response_hash,
            work=dataclasses.replace(
                response.work,
                base_or_actuator_input_work_n_mm=signed_work,
            ),
            transaction=dataclasses.replace(
                response.transaction,
                response_hash=response_hash,
            ),
        )


def _request(run_id: str) -> Any:
    return make_standalone_request(
        run_id=run_id,
        case_id="analytic-plane",
        parameter_bundle=make_baseline_parameter_bundle(),
        surface_query_handle=_plane_handle(),
    )


def test_initial_geometry_failure_is_not_masked_by_missing_contact_guard() -> None:
    execution = StandaloneSingleSpineDriver(kernel=_InitialGeometryUncertainKernel()).execute(
        _request("initial-geometry-uncertain")
    )

    assert execution.response.terminal_status is StandaloneTerminalStatus.CAPABILITY_TERMINATION
    assert execution.response.failure_axis is FailureAxis.CAPABILITY_UNAVAILABLE
    assert execution.response.terminal_reason_code == "M01_RESOLUTION_REFINEMENT_REQUIRED"
    assert (
        execution.response.unavailable_protocol_reason
        == "M01 closest query requires resolution refinement"
    )
    assert execution.accepted_points == ()
    assert execution.rejected_trials[-1].reason_code == "M01_RESOLUTION_REFINEMENT_REQUIRED"


def _hold_path(
    request: object,
    state: object,
    response: object,
) -> ReturnPathCapability:
    del request, state, response
    return ReturnPathCapability.create(
        owner_id="test-owner",
        release_event_id="test-release-event",
        mode=ReturnPathMode.HOLD_AT_RELEASE_POSE,
        path_mapping_id=None,
        pose_path_ref=None,
        swept_geometry_ref=None,
        reason_code="TEST_EXPLICIT_RETURN_PATH_UNAVAILABLE",
        metadata_unit="1",
    )


def test_real_analytic_plane_search_preload_and_100_mm_drag_complete() -> None:
    kernel = _AnalyticPlaneKernel()
    execution = StandaloneSingleSpineDriver(kernel=kernel).execute(_request("complete"))

    assert execution.response.terminal_status is StandaloneTerminalStatus.TRAVEL_COMPLETE
    assert execution.response.final_state.total_path_x_mm == pytest.approx(100.0)
    assert execution.response.final_state.drag_elapsed_time_s == pytest.approx(100.0)
    assert execution.resolved_initial_pose.actual_minimum_clearance_mm >= (
        execution.resolved_initial_pose.required_start_gap_mm
    )
    preload_etas = [
        item.preload_eta
        for item in execution.accepted_points
        if item.operation_phase is OperationPhase.INITIAL_PRELOAD
    ]
    assert preload_etas[0] == pytest.approx(2.0e-6)
    assert preload_etas[1:] == pytest.approx([0.2, 0.4, 0.6, 0.8, 1.0])
    assert {item.event_kind for item in execution.committed_events} >= {
        M03EventKind.TIP_CONTACT_ESTABLISH.value,
        M03EventKind.PRELOAD_TARGET_REACHED.value,
        M03EventKind.TRAVEL_COMPLETE.value,
    }
    assert all(
        len(
            {
                item.pre_event_response_hash,
                item.response_hash,
                item.post_event_response_hash,
            }
        )
        == 3
        for item in execution.committed_events
    )
    with pytest.raises(ContractViolation, match="cannot reuse"):
        dataclasses.replace(
            execution.committed_events[0],
            pre_event_response_hash=execution.committed_events[0].response_hash,
        )
    assert execution.trial_call_count == len(kernel.calls)
    assert execution.event_probe_count > len(execution.accepted_points)
    assert all(
        not names.intersection({"Pz", "pz", "per_spine_normal_force", "normal_force_target"})
        for names in kernel.embedded_field_names
    )
    assert all(
        point.drag_elapsed_time_s == pytest.approx(point.drag_path_x_mm)
        for point in execution.accepted_points
    )
    assert len({point.accepted_point_id for point in execution.accepted_points}) == len(
        execution.accepted_points
    )
    assert [point.state.state_version for point in execution.accepted_points] == list(
        range(1, len(execution.accepted_points) + 1)
    )
    assert all(
        segment.physical_operation_time_available == (segment.phase is OperationPhase.DRAG)
        for segment in execution.operation_segments
    )


def test_failed_one_sided_event_post_terminates_before_event_commit() -> None:
    execution = StandaloneSingleSpineDriver(kernel=_OneSidedUnavailableKernel()).execute(
        _request("one-sided-unavailable")
    )

    assert execution.response.terminal_status is StandaloneTerminalStatus.CAPABILITY_TERMINATION
    assert execution.response.terminal_reason_code == "M03_EVENT_POST_REASSEMBLY_UNAVAILABLE"
    assert execution.committed_events == ()
    assert len(execution.accepted_points) == 1


def test_unavailable_release_path_holds_without_resetting_history_or_energy() -> None:
    kernel = _AnalyticPlaneKernel(release_once=True)
    execution = StandaloneSingleSpineDriver(
        kernel=kernel,
        return_path_provider=_hold_path,
    ).execute(_request("hold"))

    response = execution.response
    assert response.terminal_status is StandaloneTerminalStatus.HOLD_AT_RELEASE_POSE
    assert response.remaining_travel_mm > 0.0
    assert response.remaining_stored_energy_n_mm > 0.0
    assert response.final_state.total_path_x_mm == pytest.approx(
        response.final_state.drag_elapsed_time_s
    )
    assert response.final_state.total_path_x_mm == pytest.approx(10.0, abs=2.0e-3)
    assert response.final_state.spring_compression_mm > 0.0
    assert response.final_state.contact_cycle_id == 1
    assert response.final_state.cumulative_input_work_n_mm > 0.0
    release = next(
        item
        for item in execution.committed_events
        if item.event_kind == M03EventKind.CONTACT_RELEASE.value
    )
    assert release.accepted_state_id == response.final_state.state_id
    assert execution.operation_segments[-1].phase is OperationPhase.HOLD_RELEASE_POSE
    assert not execution.operation_segments[-1].physical_operation_time_available
    assert all(not item.accepted_history_advanced for item in execution.rejected_trials)


def test_explicit_release_runs_frozen_return_chain_then_resumes_same_clock() -> None:
    kernel = _AnalyticPlaneKernel(release_once=True)
    execution = StandaloneSingleSpineDriver(kernel=kernel).execute(_request("return"))

    assert execution.response.terminal_status is StandaloneTerminalStatus.TRAVEL_COMPLETE
    phases = [item.phase for item in execution.operation_segments]
    release_start = phases.index(OperationPhase.UNLOAD)
    assert phases[release_start : release_start + 5] == [
        OperationPhase.UNLOAD,
        OperationPhase.DRIVE_OFF_UNLOCK,
        OperationPhase.LIFT_OFF,
        OperationPhase.RESEARCH,
        OperationPhase.RELOAD,
    ]
    kinds = [item.event_kind for item in execution.committed_events]
    assert kinds.index(M03EventKind.RECONTACT_ZERO_LOAD.value) < kinds.index(
        M03EventKind.REENGAGEMENT.value
    )
    assert execution.response.final_state.contact_cycle_id == 2
    assert execution.response.final_state.total_path_x_mm == pytest.approx(100.0)
    assert execution.response.final_state.drag_elapsed_time_s == pytest.approx(100.0)
    drag_clock_pairs = [
        (item.drag_clock_start_s, item.drag_clock_end_s) for item in execution.operation_segments
    ]
    assert all(end >= start for start, end in drag_clock_pairs)
    assert all(later[0] >= earlier[1] - 1.0e-12 for earlier, later in pairwise(drag_clock_pairs))
    assert all(
        not item.physical_operation_time_available
        for item in execution.operation_segments
        if item.phase
        in {
            OperationPhase.UNLOAD,
            OperationPhase.DRIVE_OFF_UNLOCK,
            OperationPhase.LIFT_OFF,
            OperationPhase.RESEARCH,
            OperationPhase.RELOAD,
        }
    )


def test_signed_return_work_cumulative_equals_sum_of_accepted_intervals() -> None:
    execution = StandaloneSingleSpineDriver(
        kernel=_SignedReturnWorkKernel(release_once=True)
    ).execute(_request("signed-return-work"))
    responses = {
        item.response.response_id: item.response
        for item in execution.trial_snapshots
        if item.response is not None
    }
    interval_work = [
        responses[point.response_id].work.base_or_actuator_input_work_n_mm
        for point in execution.accepted_points
    ]
    cumulative = [point.state.cumulative_input_work_n_mm for point in execution.accepted_points]

    assert any(value < 0.0 for value in interval_work)
    assert any(later < earlier for earlier, later in pairwise(cumulative))
    assert cumulative[-1] == pytest.approx(sum(interval_work))


def test_failed_research_holds_at_last_committed_operation_pose() -> None:
    kernel = _AnalyticPlaneKernel(release_once=True, fail_during_research=True)
    execution = StandaloneSingleSpineDriver(kernel=kernel).execute(_request("research-fault"))

    assert execution.response.terminal_status is StandaloneTerminalStatus.HOLD_AT_RELEASE_POSE
    assert execution.response.final_state.state_id == execution.accepted_points[-1].state.state_id
    assert execution.response.final_state.primary_state is PrimaryMechanicalState.REVERSIBLE_RETURN
    assert execution.response.final_state.total_path_x_mm == pytest.approx(10.0, abs=2.0e-3)
    assert execution.response.final_state.drag_elapsed_time_s == pytest.approx(
        execution.response.final_state.total_path_x_mm
    )
    assert execution.rejected_trials[-1].accepted_history_advanced is False
    assert execution.operation_segments[-1].phase is OperationPhase.HOLD_RELEASE_POSE
