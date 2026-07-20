"""Side-effect-free intrinsic A-M0 single-spine constitutive trial kernel."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import CapabilityStatus, SourceIdentity

from .beam import BeamResponse, beam_compliance_matrix, solve_euler_bernoulli
from .contact import (
    ContactGraphSolution,
    ContactKinematics,
    deterministic_tangent_basis,
    objective_slip_increment,
    solve_rigid_contact_graph,
)
from .contracts import (
    A_TO_B_CONTRACT_ID,
    A_TO_B_CONTRACT_VERSION,
    BeamModelState,
    ContactMotionState,
    ContactSupportResponse,
    DiagnosticsResponse,
    EmbeddedErrorClass,
    EmbeddedSingleSpineTrialRequest,
    EventCandidateResponse,
    FailureAxis,
    FiveStageFunnel,
    GeometryContactResponse,
    LinearizationResponse,
    M03ReasonCode,
    MaterialDamageResponse,
    MaterialSubstate,
    MountMode,
    NeedleIdentity,
    NeedleStrengthSubstate,
    PrimaryMechanicalState,
    RequestedTangentMode,
    ResidualBlockReport,
    SingleSpineParameterBundle,
    SingleSpineTrialResponse,
    StageEvidence,
    StateEventsResponse,
    StructureResponse,
    TangentStatus,
    TransactionResponse,
    Vector3,
    Vector6,
    WorkIncrementResponse,
    WrenchResponse,
    WrenchUniqueness,
    m03_status,
    make_metadata,
)
from .events import M03EventKind, m03_event_spec
from .geometry import (
    CompositeNeedleGeometry,
    ExplicitCenterlineProvider,
    NeedlePart,
    SweptNeedleGeometry,
    TipPose,
    build_composite_needle_geometry,
    engineering_initial_axis,
    make_swept_needle_geometry,
    resolve_tip_pose,
    sample_centerline,
)
from .mount import MountResponse, solve_mount_graph
from .surface_adapter import (
    BodyCollisionEvaluation,
    BodyCollisionStatus,
    CandidateSetEvaluation,
    GeometryGateStatus,
    GeometryQueryPolicy,
    SupportCandidate,
    collect_support_candidates,
    derive_complete_query_footprint,
    evaluate_body_collision,
    make_geometry_query_policy,
    make_identity_surface_frame_transform,
)


@dataclass(frozen=True, slots=True)
class KernelEvaluationArtifacts:
    """Read-only evidence useful to M02/M00 adapters; never accepted state."""

    previous_geometry: CompositeNeedleGeometry
    trial_geometry: CompositeNeedleGeometry
    swept_geometry: SweptNeedleGeometry
    candidate_evaluation: CandidateSetEvaluation
    body_collision: BodyCollisionEvaluation
    contact_graph: ContactGraphSolution
    beam_response: BeamResponse
    mount_response: MountResponse


@dataclass(frozen=True, slots=True)
class KernelEvaluation:
    response: SingleSpineTrialResponse
    artifacts: KernelEvaluationArtifacts


class IntrinsicSingleSpineKernel:
    """Evaluate one immutable A→B trial without committing any history.

    Contact graph closure is analytic for the frozen linear EB/interior-spring
    branches.  Continuation, retries, event brackets, nonlinear iteration, and
    transactions remain outside this class and are delegated through M02.
    """

    owner_id = "M03_INTRINSIC_SINGLE_SPINE_A_M0"
    owner_version = "1.0.0"

    def __init__(self, *, query_policy: GeometryQueryPolicy | None = None) -> None:
        self.query_policy = query_policy or make_geometry_query_policy()

    def evaluate_trial(self, request: EmbeddedSingleSpineTrialRequest) -> SingleSpineTrialResponse:
        return self.evaluate_trial_with_artifacts(request).response

    def evaluate_trial_with_artifacts(
        self, request: EmbeddedSingleSpineTrialRequest
    ) -> KernelEvaluation:
        self._preflight(request)
        bundle = request.parameter_bundle
        needle = bundle.needle
        history = request.immutable_single_spine_state_n
        axis = engineering_initial_axis(
            request.local_frame,
            needle.alpha_rad,
            needle.beta_rad,
        )
        rigid_root_old = history.base_pose.position_mm
        rigid_root_trial = _add3(
            request.base_pose_n.position_mm,
            request.prescribed_base_increment.translation_global_mm,
        )

        previous_pose = resolve_tip_pose(
            rigid_root_global_mm=rigid_root_old,
            local_frame=request.local_frame,
            needle=needle,
            spring_compression_mm=history.spring_compression_mm,
            beam_tip_translation_global_mm=history.beam_tip_translation_global_mm,
            beam_tip_rotation_global_rad=history.beam_tip_rotation_global_rad,
        )
        previous_geometry = _geometry_for_pose(previous_pose, needle)

        # The contact graph is formulated in total (not incremental) force.
        # Its free geometry must therefore be the undeformed beam/original
        # spring at the prescribed rigid-base pose.  Accepted deformation is
        # used only for the swept path and objective history; carrying it into
        # the free gap would count structural compliance twice.
        predictor_pose = resolve_tip_pose(
            rigid_root_global_mm=rigid_root_trial,
            local_frame=request.local_frame,
            needle=needle,
            spring_compression_mm=0.0,
            beam_tip_translation_global_mm=(0.0, 0.0, 0.0),
            beam_tip_rotation_global_rad=(0.0, 0.0, 0.0),
        )
        predictor_geometry = _geometry_for_pose(predictor_pose, needle)
        predictor_sweep = make_swept_needle_geometry((previous_geometry, predictor_geometry))
        transform = make_identity_surface_frame_transform(request.surface_query_handle)
        footprint = derive_complete_query_footprint(
            request.surface_query_handle,
            predictor_sweep,
            transform,
            self.query_policy,
        )
        candidates = collect_support_candidates(
            request.surface_query_handle,
            tip_pose=predictor_pose,
            tip_radius_mm=needle.tip_radius_mm,
            cap_blend_coordinate_mm=needle.cap_blend_coordinate_mm,
            footprint=footprint,
            transform=transform,
            policy=self.query_policy,
        )

        compliance = np.asarray(
            beam_compliance_matrix(needle, bundle.beam, axis), dtype=np.float64
        )[:3, :3]
        if (
            bundle.mount.mode is MountMode.INDEPENDENT_AXIAL_SPRINGS
            and bundle.mount.spring_stiffness_n_per_mm is not None
            and history.spring_compression_mm < bundle.mount.maximum_compression_mm
        ):
            direction = np.asarray(axis, dtype=np.float64)
            compliance += np.outer(direction, direction) / bundle.mount.spring_stiffness_n_per_mm

        support_candidates = tuple(
            item for item in candidates.candidates if item.admissible_support_candidate
        )
        kinematics = tuple(
            self._contact_kinematics(request, candidate, predictor_pose)
            for candidate in support_candidates
        )
        gap_tolerance = needle.tip_radius_mm * bundle.numerical.event_position_tolerance_over_rt
        contact = solve_rigid_contact_graph(
            supports=kinematics,
            point_compliance_global_mm_per_n=_matrix3_tuple(compliance),
            free_tip_increment_global_mm=(0.0, 0.0, 0.0),
            friction_coefficient=bundle.contact.friction_coefficient,
            gap_tolerance_mm=gap_tolerance,
            force_tolerance_n=bundle.numerical.force_absolute_tolerance_n,
            slip_tolerance_mm=gap_tolerance,
            soc_projection_scale=bundle.contact.numerical_soc_projection_scale,
        )

        force_b_on_a = contact.resultant_force_global_n
        support_by_id = {_support_id(item): item for item in support_candidates}
        moment_b_on_a_tip = np.zeros(3, dtype=np.float64)
        for solution in contact.supports:
            candidate = support_by_id[solution.support_id]
            lever = np.asarray(candidate.point_global_mm) - np.asarray(
                predictor_pose.current_tip_center_global_mm
            )
            moment_b_on_a_tip += np.cross(lever, np.asarray(solution.contact_force_global_n))
        beam = solve_euler_bernoulli(
            needle=needle,
            beam=bundle.beam,
            root_position_global_mm=rigid_root_trial,
            initial_axis_global=axis,
            contact_force_global_n=force_b_on_a,
            contact_moment_at_tip_global_n_mm=_tuple3(moment_b_on_a_tip),
        )
        mount = solve_mount_graph(
            parameters=bundle.mount,
            initial_axis_global=axis,
            contact_force_global_n=force_b_on_a,
            force_tolerance_n=bundle.numerical.force_absolute_tolerance_n,
        )

        final_pose = resolve_tip_pose(
            rigid_root_global_mm=rigid_root_trial,
            local_frame=request.local_frame,
            needle=needle,
            spring_compression_mm=mount.compression_mm,
            beam_tip_translation_global_mm=beam.tip_translation_global_mm,
            beam_tip_rotation_global_rad=beam.tip_rotation_global_rad,
        )
        final_geometry = _geometry_for_pose(final_pose, needle, beam=beam)
        sweep = make_swept_needle_geometry((previous_geometry, final_geometry))
        final_footprint = derive_complete_query_footprint(
            request.surface_query_handle,
            sweep,
            transform,
            self.query_policy,
        )
        body = evaluate_body_collision(
            request.surface_query_handle,
            swept_geometry=sweep,
            footprint=final_footprint,
            transform=transform,
            policy=self.query_policy,
        )

        response = self._assemble_response(
            request=request,
            axis=axis,
            tip_pose=final_pose,
            candidates=candidates,
            support_candidates=support_candidates,
            contact=contact,
            beam=beam,
            mount=mount,
            body=body,
            footprint_id=final_footprint.footprint_id,
        )
        return KernelEvaluation(
            response,
            KernelEvaluationArtifacts(
                previous_geometry,
                final_geometry,
                sweep,
                candidates,
                body,
                contact,
                beam,
                mount,
            ),
        )

    @staticmethod
    def _preflight(request: EmbeddedSingleSpineTrialRequest) -> None:
        if not isinstance(request, EmbeddedSingleSpineTrialRequest):
            raise ContractViolation("M03 kernel requires EmbeddedSingleSpineTrialRequest")
        if (
            request.contract_id != A_TO_B_CONTRACT_ID
            or request.contract_version != A_TO_B_CONTRACT_VERSION
        ):
            raise ContractViolation("M03 kernel only accepts A_TO_B 1.0.0")
        bundle = request.parameter_bundle
        expected = (
            bundle.needle.metadata.semantic_id,
            bundle.beam.metadata.semantic_id,
            bundle.material.metadata.semantic_id,
        )
        actual = (
            request.needle_identity.geometry_id,
            request.needle_identity.structure_parameter_id,
            request.needle_identity.material_parameter_id,
        )
        if actual != expected:
            raise ContractViolation(
                "needle identity does not match immutable parameter bundle",
                details={"expected": expected, "actual": actual},
            )
        if request.needle_identity.needle_strength_parameter_id != "NEEDLE_STRENGTH_UNAVAILABLE":
            raise ContractViolation("M03 needle strength identity must be explicitly unavailable")
        if request.shared_damage_store_snapshot.version != 0:
            raise ContractViolation("no_damage snapshot version must remain zero")
        if request.base_pose_n.expressed_frame_id != "GLOBAL":
            raise ContractViolation("M03 embedded base pose must be expressed in GLOBAL")
        if (
            request.prescribed_base_increment.expressed_frame_id != "GLOBAL"
            or request.prescribed_base_increment.reference_point_id
            != request.base_pose_n.reference_point_id
        ):
            raise ContractViolation("prescribed increment frame/reference mismatch")

    @staticmethod
    def _contact_kinematics(
        request: EmbeddedSingleSpineTrialRequest,
        candidate: SupportCandidate,
        tip_pose: TipPose,
    ) -> ContactKinematics:
        assert candidate.radial_normal_global is not None
        tangent = deterministic_tangent_basis(
            candidate.radial_normal_global,
            request.task_direction_global,
        )
        slip = objective_slip_increment(
            tip_translation_increment_global_mm=request.prescribed_base_increment.translation_global_mm,
            tip_rotation_increment_global_rad=request.prescribed_base_increment.rotation_global_rad,
            support_point_mid_global_mm=candidate.point_global_mm,
            tip_center_mid_global_mm=tip_pose.current_tip_center_global_mm,
            normal_mid_global=candidate.radial_normal_global,
        )
        previous = next(
            (
                item
                for item in request.immutable_single_spine_state_n.active_supports
                if item.candidate_id == candidate.candidate_id
                or item.support_id == _support_id(candidate)
            ),
            None,
        )
        return ContactKinematics(
            support_id=_support_id(candidate),
            candidate_id=candidate.candidate_id,
            point_global_mm=candidate.point_global_mm,
            normal_global=candidate.radial_normal_global,
            tangent_basis_global=tangent,
            free_gap_mm=candidate.sphere_gap_mm,
            objective_slip_increment_global_mm=slip,
            previous_normal_multiplier_n=(
                previous.normal_multiplier_n if previous is not None else 0.0
            ),
            previous_tangential_multiplier_n=(
                previous.tangential_multiplier_n if previous is not None else (0.0, 0.0)
            ),
            support_migrated=(
                bool(request.immutable_single_spine_state_n.active_supports) and previous is None
            ),
        )

    def _assemble_response(
        self,
        *,
        request: EmbeddedSingleSpineTrialRequest,
        axis: Vector3,
        tip_pose: TipPose,
        candidates: CandidateSetEvaluation,
        support_candidates: tuple[SupportCandidate, ...],
        contact: ContactGraphSolution,
        beam: BeamResponse,
        mount: MountResponse,
        body: BodyCollisionEvaluation,
        footprint_id: str,
    ) -> SingleSpineTrialResponse:
        bundle = request.parameter_bundle
        numerical = bundle.numerical
        force_resolution = numerical.acceptance_force_resolution_n
        candidate_by_support = {_support_id(item): item for item in support_candidates}
        loaded = any(item.normal_multiplier_n > force_resolution for item in contact.supports)

        # Accepted A→B 1.0.0 defines the public wrench as the wall-on-spine
        # contact resultant transported to the declared backing reference.
        # The internal contact graph already uses exactly that convention.
        force_a_on_b = (
            np.asarray(contact.resultant_force_global_n, dtype=np.float64)
            if loaded
            else np.zeros(3, dtype=np.float64)
        )
        force_a_on_b[np.abs(force_a_on_b) == 0.0] = 0.0
        moment_a_on_b = np.zeros(3, dtype=np.float64)
        trial_reference_position = _add3(
            request.base_pose_n.position_mm,
            request.prescribed_base_increment.translation_global_mm,
        )
        contact_support_responses: list[ContactSupportResponse] = []
        for solution in contact.supports:
            candidate = candidate_by_support[solution.support_id]
            support_loaded = solution.normal_multiplier_n > force_resolution
            force = (
                np.asarray(solution.contact_force_global_n, dtype=np.float64)
                if support_loaded
                else np.zeros(3, dtype=np.float64)
            )
            lever = np.asarray(candidate.point_global_mm) - np.asarray(trial_reference_position)
            moment_a_on_b += np.cross(lever, force)
            normal = candidate.radial_normal_global
            assert normal is not None
            tangents = deterministic_tangent_basis(normal, request.task_direction_global)
            previous_slip = next(
                (
                    item.accumulated_slip_mm
                    for item in request.immutable_single_spine_state_n.active_supports
                    if item.candidate_id == candidate.candidate_id
                ),
                0.0,
            )
            slip_preview = previous_slip + (
                math.hypot(*solution.objective_slip_increment_local_mm) if support_loaded else 0.0
            )
            contact_support_responses.append(
                ContactSupportResponse(
                    solution.support_id,
                    solution.candidate_id,
                    candidate.point_global_mm,
                    candidate.feature_type,
                    candidate.chart_id,
                    candidate.sphere_gap_mm,
                    solution.final_gap_mm,
                    normal,
                    tangents,
                    _tuple3(force),
                    solution.normal_multiplier_n if support_loaded else 0.0,
                    (
                        solution.tangential_multiplier_n[0] if support_loaded else 0.0,
                        solution.tangential_multiplier_n[1] if support_loaded else 0.0,
                    ),
                    solution.objective_slip_increment_global_mm,
                    solution.objective_slip_increment_local_mm,
                    slip_preview,
                    solution.motion_state if support_loaded else ContactMotionState.TOUCH_ZERO_LOAD,
                    support_loaded and solution.motion_state is ContactMotionState.ROLLING_NO_SLIP,
                    candidate.cap_legality_margin_mm,
                )
            )
        moment_a_on_b[np.abs(moment_a_on_b) == 0.0] = 0.0

        wrench_vector: Vector6 = (*_tuple3(force_a_on_b), *_tuple3(moment_a_on_b))
        task = np.asarray(request.task_direction_global, dtype=np.float64)
        rx = -float(np.dot(np.asarray(request.local_frame.e_x_global), force_a_on_b))
        task_resistance = -float(np.dot(task, force_a_on_b))
        geometric = any(
            item.admissible_support_candidate
            and item.sphere_gap_mm
            <= request.parameter_bundle.needle.tip_radius_mm
            * request.parameter_bundle.numerical.event_position_tolerance_over_rt
            for item in candidates.candidates
        )
        stable = loaded and contact.branch_feasible and contact.graph_quality_passed
        load_bearing = stable and task_resistance > force_resolution
        was_loaded = any(
            item.normal_multiplier_n > force_resolution
            for item in request.immutable_single_spine_state_n.active_supports
        )
        released = was_loaded and not loaded

        primary = _primary_state(contact, geometric, loaded, released)
        five_stage = FiveStageFunnel(
            _stage(geometric, "M03_GEOMETRIC_CANDIDATE", candidates.evaluation_id),
            _stage(loaded, "M03_POSITIVE_NORMAL_LOAD", contact.branch_id),
            _stage(stable, "M03_FRICTION_GRAPH_ADMISSIBLE", contact.branch_id),
            _stage(load_bearing, "M03_POSITIVE_TASK_RESISTANCE", request.request_id),
            _stage(released, "M03_RELEASE_LIFECYCLE", request.request_id),
            _stage(False, "M03_STANDALONE_RECONTACT_NOT_COMMITTED", request.request_id),
            _stage(False, "M03_STANDALONE_REENGAGEMENT_NOT_COMMITTED", request.request_id),
        )

        graph_nullspace = _wrench_nullspace(contact.nullspace_basis)
        uniqueness = contact.wrench_uniqueness
        opposite_wrench: Vector6 = tuple(0.0 if item == 0.0 else -item for item in wrench_vector)  # type: ignore[assignment]
        wrench = WrenchResponse(
            "A_on_B",
            _tuple3(force_a_on_b),
            _tuple3(moment_a_on_b),
            "GLOBAL",
            request.base_pose_n.reference_point_id,
            trial_reference_position,
            "N",
            "N*mm",
            opposite_wrench,
            rx,
            task_resistance,
            request.task_direction_global,
            uniqueness,
            contact.admissible_graph_handle,
            min(contact.rank, 6),
            graph_nullspace,
            True,
        )

        part_clearance = {item.part: item for item in body.part_clearances}
        minimum = body.minimum_forbidden_body_clearance_lower_bound_mm
        geometry_contact = GeometryContactResponse(
            tuple(item.support_id for item in contact.supports),
            tuple(
                _support_id(item)
                for item in support_candidates
                if _support_id(item) not in {value.support_id for value in contact.supports}
            ),
            tuple(contact_support_responses),
            tuple(item.candidate_id for item in candidates.candidates),
            tip_pose.current_tip_center_global_mm,
            tip_pose.current_axis_global,
            axis,
            _part_clearance(part_clearance, NeedlePart.CONE),
            _part_clearance(part_clearance, NeedlePart.SHAFT),
            _part_clearance(part_clearance, NeedlePart.MOUNT),
            minimum,
            tuple(dict.fromkeys((*candidates.all_query_receipt_ids, *body.query_receipt_ids))),
            f"{candidates.gate_status.value}|{body.status.value}",
            max(
                value
                for value in (
                    candidates.error_bound_mm or 0.0,
                    *(item.surface_error_bound_mm or 0.0 for item in body.part_clearances),
                )
            ),
            candidates.nonsmooth_or_nonunique,
            footprint_id,
            self.query_policy.lod_purpose,
            bool(candidates.candidates),
            geometric,
        )

        structure = StructureResponse(
            bundle.beam.bending_enabled,
            beam.model_id,
            beam.model_state,
            beam.tip_translation_global_mm,
            beam.tip_rotation_global_rad,
            _global_to_needle(beam.tip_translation_global_mm, axis),
            _global_to_needle(beam.tip_rotation_global_rad, axis),
            beam.root_reaction_force_global_n,
            beam.root_reaction_moment_global_n_mm,
            beam.section_resultants_needle,
            beam.energy_n_mm,
            bundle.mount.mode,
            mount.state,
            mount.compression_mm,
            mount.spring_force_n,
            mount.remaining_travel_mm,
            mount.hard_stop_reaction_n,
            mount.energy_n_mm,
            None,
            0.0,
            None,
            None,
            NeedleStrengthSubstate.NEEDLE_STRENGTH_UNAVAILABLE,
        )

        friction_dissipation = max(
            0.0,
            sum(
                -float(
                    np.dot(
                        np.asarray(item.contact_force_global_n),
                        np.asarray(item.objective_slip_increment_global_mm),
                    )
                )
                for item in contact.supports
                if item.motion_state is ContactMotionState.SLIDING_COMMITTED
            ),
        )
        previous_beam_energy = _previous_beam_energy(request, axis)
        previous_spring_energy = _previous_spring_energy(request.parameter_bundle, request)
        delta_beam = beam.energy_n_mm - previous_beam_energy
        delta_spring = mount.energy_n_mm - previous_spring_energy
        input_work = _trapezoidal_actuator_input_work(
            request,
            current_force_a_on_b_global_n=force_a_on_b,
            current_moment_a_on_b_at_base_n_mm=moment_a_on_b,
        )
        closure = input_work - delta_beam - delta_spring - friction_dissipation
        work_reference = max(
            abs(input_work),
            abs(delta_beam) + abs(delta_spring) + friction_dissipation,
            numerical.work_absolute_tolerance_n_mm,
        )
        work = WorkIncrementResponse(
            input_work,
            delta_beam,
            delta_spring,
            friction_dissipation,
            0.0,
            0.0,
            beam.energy_n_mm + mount.energy_n_mm,
            closure,
            abs(closure) / work_reference,
        )
        material = MaterialDamageResponse(
            "no_damage",
            "NOT_APPLICABLE_NO_DAMAGE_MODEL",
            (),
            (),
            (),
            (),
            None,
            None,
            (),
            MaterialSubstate.NO_DAMAGE_MODEL,
            friction_dissipation,
            0.0,
            0.0,
            None,
            False,
            None,
            m03_status(
                M03ReasonCode.MATERIAL_DAMAGE_UNAVAILABLE,
                capability=CapabilityStatus.NOT_APPLICABLE,
                explanation="no_damage exposes no damage state, capacity, or write intent",
            ),
        )

        error_class, failure_axis, reason_codes = _classify_response(
            candidates, body, contact, beam, loaded
        )
        residuals = _residual_reports(
            contact=contact,
            beam=beam,
            mount=mount,
            candidates=candidates,
            body=body,
            work_error=closure,
            work_reference=work_reference,
            bundle=bundle,
        )
        failed_hard_residuals = tuple(
            item.block_id for item in residuals if item.hard and not item.passed
        )
        hard_gate_applied = failure_axis is FailureAxis.NONE and bool(failed_hard_residuals)
        if hard_gate_applied:
            # An accepted A→B ``OK`` response must satisfy every hard quality
            # block before B may assemble it.  Preserve the raw blocks and
            # classify the unclosed trial as numerical nonconvergence instead
            # of exposing a misleading continuable response.
            error_class = EmbeddedErrorClass.NUMERICAL_NONCONVERGENCE
            failure_axis = FailureAxis.NUMERICAL_FAILURE
            reason_codes = (M03ReasonCode.HARD_RESIDUAL_QUALITY_FAILED.value,)
        geometric_residual = max((abs(item.final_gap_mm) for item in contact.supports), default=0.0)
        diagnostics = DiagnosticsResponse(
            residuals,
            contact.complementarity_residual,
            contact.soc_residual,
            contact.graph_residual,
            geometric_residual,
            0.0,
            0.0,
            closure,
            min(contact.rank, 6),
            None if uniqueness is WrenchUniqueness.SET_VALUED_CONSTRAINT else 1.0,
            "SET_VALUED"
            if uniqueness is WrenchUniqueness.SET_VALUED_CONSTRAINT
            else "ANALYTIC_BRANCH",
            uniqueness is not WrenchUniqueness.UNIQUE,
            "FULLY_RESOLVED_DEV_PRIOR",
            geometry_contact.query_quality,
            geometry_contact.geometry_uncertainty_mm,
            error_class,
            (
                "hard residual quality gate failed: " + ",".join(failed_hard_residuals)
                if hard_gate_applied
                else "side-effect-free intrinsic trial; commit eligibility is owned by M02/M00"
            ),
            failure_axis,
            reason_codes,
        )

        events = _event_candidates(
            request,
            contact,
            candidates,
            body,
            mount,
            beam,
            task_resistance,
        )
        state_events = StateEventsResponse(
            primary,
            tuple(item.motion_state for item in contact.supports),
            mount.state,
            MaterialSubstate.NO_DAMAGE_MODEL,
            NeedleStrengthSubstate.NEEDLE_STRENGTH_UNAVAILABLE,
            "QUALITY_PASSED"
            if all(item.passed for item in residuals if item.hard)
            else "QUALITY_REJECTED",
            events,
            (),
            None,
            None,
            1.0,
            False,
            "CONTINUABLE" if failure_axis is FailureAxis.NONE else "REJECTED_TRIAL",
            five_stage,
            None,
        )
        linearization = _linearization(request, contact)

        core_payload: dict[str, Any] = {
            "request_hash": request.request_hash,
            "wrench": wrench,
            "geometry_contact": geometry_contact,
            "structure": structure,
            "material_damage": material,
            "state_events": state_events,
            "linearization": linearization,
            "diagnostics": diagnostics,
            "work": work,
        }
        response_hash = semantic_hash(core_payload)
        response_id = stable_content_id("m03_single_spine_trial_response", core_payload)
        transaction = TransactionResponse(
            stable_content_id(
                "m03_opaque_trial_state",
                {"request_hash": request.request_hash, "response_hash": response_hash},
            ),
            stable_content_id(
                "m03_rollback_token",
                {
                    "request_hash": request.request_hash,
                    "parent_state_id": request.immutable_single_spine_state_n.state_id,
                },
            ),
            stable_content_id(
                "m03_provisional_commit_intent",
                {"response_hash": response_hash, "no_damage": True},
            ),
            request.immutable_single_spine_state_n.state_version,
            request.shared_damage_store_snapshot.version,
            request.request_hash,
            response_hash,
            stable_content_id(
                "m03_trial_idempotency",
                {
                    "request_hash": request.request_hash,
                    "trial_identity": request.trial_identity,
                },
            ),
        )
        metadata_status = m03_status(
            reason_codes[0] if reason_codes else M03ReasonCode.OK,
            explanation="M03 intrinsic response is DEV_PRIOR analytic/synthetic and not certifiable",
        )
        return SingleSpineTrialResponse(
            A_TO_B_CONTRACT_ID,
            A_TO_B_CONTRACT_VERSION,
            response_id,
            response_hash,
            wrench,
            geometry_contact,
            structure,
            material,
            state_events,
            linearization,
            diagnostics,
            work,
            transaction,
            make_metadata(
                "m03_single_spine_trial_response_metadata",
                {"response_id": response_id, "response_hash": response_hash},
                source_identity=SourceIdentity.ACCEPTED_AUTHORITY,
                status=metadata_status,
            ),
        )


def make_needle_identity(
    bundle: SingleSpineParameterBundle,
    *,
    needle_id: str = "M03_SINGLE_SPINE_0",
    unit_id: str = "M03_UNIT_0",
) -> NeedleIdentity:
    """Create the strict identity expected by :class:`IntrinsicSingleSpineKernel`."""

    return NeedleIdentity(
        needle_id,
        unit_id,
        bundle.needle.metadata.semantic_id,
        bundle.beam.metadata.semantic_id,
        bundle.material.metadata.semantic_id,
        "NEEDLE_STRENGTH_UNAVAILABLE",
    )


def _geometry_for_pose(
    pose: TipPose,
    needle: Any,
    *,
    beam: BeamResponse | None = None,
) -> CompositeNeedleGeometry:
    if beam is not None:
        beam_root = np.asarray(beam.centerline[0].position_global_mm, dtype=np.float64)
        resolved_root = np.asarray(pose.current_root_global_mm, dtype=np.float64)
        mount_shift = resolved_root - beam_root
        points = tuple(
            _tuple3(np.asarray(item.position_global_mm, dtype=np.float64) + mount_shift)
            for item in beam.centerline
        )
        provider = ExplicitCenterlineProvider(
            points,
            stable_content_id("m03_eb_centerline_provider", {"points": points}),
        )
        centerline = sample_centerline(
            provider,
            expected_root_global_mm=pose.current_root_global_mm,
            expected_tip_center_global_mm=pose.current_tip_center_global_mm,
            sample_count=len(points),
        )
        return build_composite_needle_geometry(
            tip_pose=pose,
            needle=needle,
            centerline=centerline,
            axial_sample_count=65,
            radial_sample_count=72,
        )
    if any(
        abs(value) > 0.0
        for value in (*pose.beam_tip_translation_global_mm, *pose.beam_tip_rotation_global_rad)
    ):
        root = np.asarray(pose.current_root_global_mm, dtype=np.float64)
        axis = np.asarray(pose.initial_axis_global, dtype=np.float64)
        translation = np.asarray(pose.beam_tip_translation_global_mm, dtype=np.float64)
        fractions = np.linspace(0.0, 1.0, 17)
        shape = fractions**2 * (3.0 - 2.0 * fractions)
        points_array = (
            root[None, :]
            + fractions[:, None] * needle.exposed_length_mm * axis[None, :]
            + shape[:, None] * translation[None, :]
        )
        points = tuple(_tuple3(item) for item in points_array)
        provider = ExplicitCenterlineProvider(
            points,
            stable_content_id("m03_history_centerline_provider", {"points": points}),
        )
        centerline = sample_centerline(
            provider,
            expected_root_global_mm=pose.current_root_global_mm,
            expected_tip_center_global_mm=pose.current_tip_center_global_mm,
            sample_count=len(points),
        )
        return build_composite_needle_geometry(
            tip_pose=pose,
            needle=needle,
            centerline=centerline,
            axial_sample_count=65,
            radial_sample_count=72,
        )
    return build_composite_needle_geometry(
        tip_pose=pose,
        needle=needle,
        axial_sample_count=65,
        radial_sample_count=72,
    )


def _primary_state(
    contact: ContactGraphSolution,
    geometric: bool,
    loaded: bool,
    released: bool,
) -> PrimaryMechanicalState:
    if released:
        return PrimaryMechanicalState.RELEASE_TRANSITION
    if not loaded:
        return PrimaryMechanicalState.TIP_ZERO_LOAD if geometric else PrimaryMechanicalState.OPEN
    if any(item.motion_state is ContactMotionState.SLIDING_COMMITTED for item in contact.supports):
        return PrimaryMechanicalState.ATTACHED_SLIDE
    return PrimaryMechanicalState.ATTACHED_STICK


def _classify_response(
    candidates: CandidateSetEvaluation,
    body: BodyCollisionEvaluation,
    contact: ContactGraphSolution,
    beam: BeamResponse,
    loaded: bool,
) -> tuple[EmbeddedErrorClass, FailureAxis, tuple[str, ...]]:
    if (
        candidates.gate_status is GeometryGateStatus.OUT_OF_DOMAIN
        or body.status is BodyCollisionStatus.OUT_OF_DOMAIN
    ):
        reason_codes = tuple(
            dict.fromkeys(
                (
                    *(
                        (candidates.reason_code,)
                        if candidates.gate_status is GeometryGateStatus.OUT_OF_DOMAIN
                        else ()
                    ),
                    *(
                        (body.reason_code,)
                        if body.status is BodyCollisionStatus.OUT_OF_DOMAIN
                        else ()
                    ),
                )
            )
        )
        return (
            EmbeddedErrorClass.OUT_OF_DOMAIN,
            FailureAxis.DOMAIN_ERROR,
            reason_codes,
        )
    if body.status is BodyCollisionStatus.BODY_COLLISION_INVALID:
        return (
            EmbeddedErrorClass.BODY_COLLISION_INVALID,
            FailureAxis.PHYSICAL_INFEASIBLE,
            (M03ReasonCode.BODY_COLLISION_INVALID.value,),
        )
    if (
        candidates.gate_status is GeometryGateStatus.GEOMETRY_UNCERTAIN
        or body.status is BodyCollisionStatus.GEOMETRY_UNCERTAIN
    ):
        reason_codes = tuple(
            dict.fromkeys(
                (
                    *(
                        (candidates.reason_code,)
                        if candidates.gate_status is GeometryGateStatus.GEOMETRY_UNCERTAIN
                        else ()
                    ),
                    *(
                        (body.reason_code,)
                        if body.status is BodyCollisionStatus.GEOMETRY_UNCERTAIN
                        else ()
                    ),
                )
            )
        )
        return (
            EmbeddedErrorClass.GEOMETRY_UNCERTAIN,
            FailureAxis.CAPABILITY_UNAVAILABLE,
            reason_codes,
        )
    if beam.model_state is BeamModelState.STRUCTURAL_MODEL_OUT_OF_RANGE:
        return (
            EmbeddedErrorClass.MODEL_UNAVAILABLE,
            FailureAxis.CAPABILITY_UNAVAILABLE,
            (M03ReasonCode.STRUCTURAL_MODEL_OUT_OF_RANGE.value,),
        )
    if not contact.branch_feasible or not contact.graph_quality_passed:
        error = (
            EmbeddedErrorClass.EQUILIBRIUM_DEGENERATE
            if contact.wrench_uniqueness is WrenchUniqueness.SET_VALUED_CONSTRAINT
            else EmbeddedErrorClass.NUMERICAL_NONCONVERGENCE
        )
        return error, FailureAxis.NUMERICAL_FAILURE, ("M03_CONTACT_GRAPH_QUALITY_FAILED",)
    if not loaded:
        return EmbeddedErrorClass.OPEN_RESPONSE, FailureAxis.NONE, ("M03_OPEN_RESPONSE",)
    return EmbeddedErrorClass.OK, FailureAxis.NONE, (M03ReasonCode.OK.value,)


def _residual_reports(
    *,
    contact: ContactGraphSolution,
    beam: BeamResponse,
    mount: MountResponse,
    candidates: CandidateSetEvaluation,
    body: BodyCollisionEvaluation,
    work_error: float,
    work_reference: float,
    bundle: SingleSpineParameterBundle,
) -> tuple[ResidualBlockReport, ...]:
    force_tol = bundle.numerical.force_absolute_tolerance_n
    gap_tol = bundle.needle.tip_radius_mm * bundle.numerical.event_position_tolerance_over_rt
    work_tol = bundle.numerical.work_absolute_tolerance_n_mm
    geometry_raw = 0.0
    if candidates.gate_status is GeometryGateStatus.GEOMETRY_UNCERTAIN:
        geometry_raw = max(candidates.error_bound_mm or gap_tol * 2.0, gap_tol * 2.0)
    if body.status is BodyCollisionStatus.GEOMETRY_UNCERTAIN:
        geometry_raw = max(geometry_raw, gap_tol * 2.0)
    values = (
        (
            "complementarity",
            "Signorini complementarity",
            contact.complementarity_residual,
            "1",
            max(force_tol, gap_tol),
        ),
        (
            "coulomb_soc",
            "Coulomb second-order-cone admissibility",
            contact.soc_residual,
            "N",
            force_tol,
        ),
        (
            "contact_graph",
            "rigid contact graph distance",
            contact.graph_residual,
            "1",
            max(force_tol, gap_tol),
        ),
        ("geometric_closure", "M01 geometry/coverage closure", geometry_raw, "mm", gap_tol),
        ("beam_equilibrium", "analytic Euler-Bernoulli equilibrium", 0.0, "mm", gap_tol),
        ("spring_graph", f"A-authoritative mount branch {mount.state.value}", 0.0, "N", force_tol),
        (
            "work_closure",
            "input/energy/dissipation work closure",
            abs(work_error),
            "N*mm",
            work_tol,
        ),
        (
            "jacobian_quality",
            f"branch rank {contact.rank}",
            0.0 if contact.branch_feasible else 2.0,
            "1",
            1.0,
        ),
    )
    return tuple(
        _residual(
            block_id,
            semantics,
            raw,
            unit,
            tolerance,
            reference_norm=work_reference if block_id == "work_closure" else None,
            relative_tolerance=(
                bundle.numerical.work_relative_tolerance if block_id == "work_closure" else 0.0
            ),
        )
        for block_id, semantics, raw, unit, tolerance in values
    )


def _residual(
    block_id: str,
    semantics: str,
    raw: float,
    unit: str,
    tolerance: float,
    *,
    reference_norm: float | None = None,
    relative_tolerance: float = 0.0,
) -> ResidualBlockReport:
    reference = max(abs(raw), tolerance) if reference_norm is None else reference_norm
    threshold = tolerance + relative_tolerance * reference
    normalized = abs(raw) / max(threshold, np.finfo(float).tiny)
    passed = abs(raw) <= threshold
    return ResidualBlockReport(
        block_id,
        semantics,
        abs(raw),
        unit,
        reference,
        tolerance,
        relative_tolerance,
        f"M03_{block_id.upper()}_SCALE",
        normalized,
        True,
        passed,
    )


def _event_candidates(
    request: EmbeddedSingleSpineTrialRequest,
    contact: ContactGraphSolution,
    candidates: CandidateSetEvaluation,
    body: BodyCollisionEvaluation,
    mount: MountResponse,
    beam: BeamResponse,
    task_resistance_n: float,
) -> tuple[EventCandidateResponse, ...]:
    del task_resistance_n  # Kept in the private signature for call-site stability.
    output: list[EventCandidateResponse] = []
    geometry_coverage = next(iter(candidates.all_query_receipt_ids), None)

    def append(kind: M03EventKind, value: float, coverage_id: str | None = None) -> None:
        if not math.isfinite(value):
            raise ContractViolation(
                "M03 runtime event guard must be finite",
                details={"event_kind": kind.value, "raw_guard": value},
            )
        spec = m03_event_spec(kind)
        output.append(
            EventCandidateResponse(
                stable_content_id(
                    "m03_event_candidate",
                    {"request_hash": request.request_hash, "kind": kind.value},
                ),
                kind.value,
                float(value),
                spec.raw_guard_unit,
                spec.zero_level,
                spec.admissible_side.value,
                spec.trigger_direction.value,
                None,
                None,
                coverage_id
                or geometry_coverage
                or stable_content_id(
                    "m03_event_coverage",
                    {"request_hash": request.request_hash, "kind": kind.value},
                ),
            )
        )

    # Only candidates with independent closest-point, empty-ball and quality
    # evidence may own a physical tip/cap guard.  An uncertain query must not
    # mint a zero-valued event in place of a missing signed margin.
    witnessed = tuple(
        item
        for item in candidates.candidates
        if item.local_minimum_verified
        and item.empty_ball_verified
        and item.query_quality_passed
        and item.radial_normal_global is not None
    )
    legal = tuple(item for item in witnessed if item.finite_cap_legal)
    if legal:
        minimum_gap = min(item.sphere_gap_mm for item in legal)
        append(M03EventKind.TIP_CONTACT_ESTABLISH, minimum_gap)
        append(M03EventKind.TIP_CONTACT_TANGENCY, minimum_gap)

    force_resolution = request.parameter_bundle.numerical.acceptance_force_resolution_n
    maximum_normal = max((item.normal_multiplier_n for item in contact.supports), default=0.0)
    append(M03EventKind.CONTACT_LOAD_ONSET, maximum_normal - force_resolution)
    if contact.supports or request.immutable_single_spine_state_n.active_supports:
        minimum_normal = min(
            (item.normal_multiplier_n for item in contact.supports),
            default=0.0,
        )
        append(M03EventKind.CONTACT_RELEASE, minimum_normal - force_resolution)

    if contact.supports:
        append(
            M03EventKind.FRICTION_CONE_REACHED,
            min(item.friction_margin_n for item in contact.supports),
        )
        append(
            M03EventKind.ALL_STICK_BRANCH_LOSS,
            min(item.all_stick_friction_margin_n for item in contact.supports),
        )
        slip_resolution = (
            request.parameter_bundle.needle.tip_radius_mm
            * request.parameter_bundle.numerical.event_position_tolerance_over_rt
        )
        confirmed_sliding_supports = tuple(
            item
            for item in contact.supports
            if item.motion_state is ContactMotionState.SLIDING_COMMITTED
            and not item.all_stick_feasible
            and item.maximum_dissipation_closed
        )
        if confirmed_sliding_supports:
            maximum_objective_slip = max(
                math.hypot(*item.objective_slip_increment_local_mm)
                for item in confirmed_sliding_supports
            )
            append(
                M03EventKind.SLIP_ONSET_CONFIRMED,
                maximum_objective_slip - slip_resolution,
            )

    if witnessed:
        append(
            M03EventKind.CAP_LEGALITY_LOSS,
            min(item.cap_legality_margin_mm for item in witnessed),
        )

    if request.parameter_bundle.mount.mode is MountMode.INDEPENDENT_AXIAL_SPRINGS:
        append(M03EventKind.SPRING_ORIGINAL_LENGTH, mount.compression_mm)
        append(M03EventKind.SPRING_HARD_STOP, mount.remaining_travel_mm)

    body_by_part = {item.part: item for item in body.part_clearances}

    def certified_part_clearance(part: NeedlePart) -> float | None:
        clearance = body_by_part.get(part)
        if clearance is None or clearance.certified_euclidean_clearance_lower_bound_mm is None:
            return None
        return clearance.certified_euclidean_clearance_lower_bound_mm

    for kind, part in (
        (M03EventKind.CONE_COLLISION, NeedlePart.CONE),
        (M03EventKind.SHAFT_COLLISION, NeedlePart.SHAFT),
        (M03EventKind.MOUNT_COLLISION, NeedlePart.MOUNT),
    ):
        clearance = certified_part_clearance(part)
        if clearance is not None:
            append(kind, clearance, next(iter(body.query_receipt_ids), None))

    if request.parameter_bundle.beam.bending_enabled:
        beam_parameters = request.parameter_bundle.beam
        structural_margin = min(
            beam.slenderness_ratio / beam_parameters.minimum_slenderness_ratio - 1.0,
            1.0
            - beam.tip_deflection_over_length / beam_parameters.maximum_tip_deflection_over_length,
            1.0 - beam.rotation_norm_rad / beam_parameters.maximum_rotation_rad,
        )
        append(M03EventKind.STRUCTURAL_MODEL_LIMIT, structural_margin)

    return tuple(output)


def _linearization(
    request: EmbeddedSingleSpineTrialRequest,
    contact: ContactGraphSolution,
) -> LinearizationResponse:
    if request.requested_tangent_mode is RequestedTangentMode.NONE:
        matrix = None
        status = TangentStatus.UNAVAILABLE
    elif contact.branch_id == "OPEN_GRAPH":
        matrix = tuple(tuple(0.0 for _ in range(6)) for _ in range(6))
        status = TangentStatus.SMOOTH_CONSISTENT
    else:
        matrix = None
        # A branch label is not itself a consistent tangent.  Preserve the
        # informative graph status for nonsmooth/set-valued branches, but do
        # not advertise a smooth matrix that this first implementation does
        # not actually assemble.
        status = (
            TangentStatus.UNAVAILABLE
            if contact.tangent_status is TangentStatus.SMOOTH_CONSISTENT
            else contact.tangent_status
        )
    return LinearizationResponse(
        matrix,  # type: ignore[arg-type]
        "GLOBAL wrench A_on_B at M03_BASE_REFERENCE_O",
        request.prescribed_base_increment.increment_basis,
        request.request_hash,
        status,
        contact.branch_id,
        None,
    )


def _stage(value: bool, reason: str, evidence: str) -> StageEvidence:
    return StageEvidence(value, reason, (evidence,))


def _support_id(candidate: SupportCandidate) -> str:
    return stable_content_id(
        "m03_contact_support",
        {
            "surface_realization_id": candidate.surface_realization_id,
            "candidate_id": candidate.candidate_id,
        },
    )


def _trapezoidal_actuator_input_work(
    request: EmbeddedSingleSpineTrialRequest,
    *,
    current_force_a_on_b_global_n: np.ndarray[Any, Any],
    current_moment_a_on_b_at_base_n_mm: np.ndarray[Any, Any],
) -> float:
    """Independently integrate base-actuator work over one trial increment.

    Quasistatic action/reaction makes the external base force on the spine
    equal to the reported ``A_on_B`` contact resultant.  The immutable
    accepted supports retain the previous endpoint multipliers and bases, so
    the prior resultant can be reconstructed without using beam/spring energy
    or friction dissipation.  M03 currently rejects nonzero base rotations;
    the moment term remains explicit so the conjugate convention is auditable.
    """

    previous_force = np.zeros(3, dtype=np.float64)
    previous_moment = np.zeros(3, dtype=np.float64)
    previous_reference = np.asarray(request.base_pose_n.position_mm, dtype=np.float64)
    for support in request.immutable_single_spine_state_n.active_supports:
        normal = np.asarray(support.normal_global, dtype=np.float64)
        tangent_1 = np.asarray(support.tangent_basis_global[0], dtype=np.float64)
        tangent_2 = np.asarray(support.tangent_basis_global[1], dtype=np.float64)
        # Accepted multipliers and bases reconstruct the canonical A_on_B
        # (wall-on-spine) contact resultant directly.
        force = (
            support.normal_multiplier_n * normal
            + support.tangential_multiplier_n[0] * tangent_1
            + support.tangential_multiplier_n[1] * tangent_2
        )
        previous_force += force
        lever = np.asarray(support.point_global_mm, dtype=np.float64) - previous_reference
        previous_moment += np.cross(lever, force)

    translation = np.asarray(
        request.prescribed_base_increment.translation_global_mm,
        dtype=np.float64,
    )
    rotation = np.asarray(
        request.prescribed_base_increment.rotation_global_rad,
        dtype=np.float64,
    )
    # Backing input to A is the negative of the public A-on-B wrench power.
    force_work = -0.5 * float(np.dot(previous_force + current_force_a_on_b_global_n, translation))
    moment_work = -0.5 * float(
        np.dot(previous_moment + current_moment_a_on_b_at_base_n_mm, rotation)
    )
    result = force_work + moment_work
    if not math.isfinite(result):
        raise ContractViolation("actuator work quadrature produced a non-finite value")
    return 0.0 if result == 0.0 else result


def _previous_beam_energy(
    request: EmbeddedSingleSpineTrialRequest,
    axis: Vector3,
) -> float:
    compliance = np.asarray(
        beam_compliance_matrix(
            request.parameter_bundle.needle,
            request.parameter_bundle.beam,
            axis,
        ),
        dtype=np.float64,
    )
    displacement = np.asarray(
        (
            *request.immutable_single_spine_state_n.beam_tip_translation_global_mm,
            *request.immutable_single_spine_state_n.beam_tip_rotation_global_rad,
        ),
        dtype=np.float64,
    )
    if not np.any(compliance) or not np.any(displacement):
        return 0.0
    generalized_force = np.linalg.pinv(compliance, rcond=1.0e-12) @ displacement
    return max(0.0, 0.5 * float(np.dot(displacement, generalized_force)))


def _previous_spring_energy(
    bundle: SingleSpineParameterBundle,
    request: EmbeddedSingleSpineTrialRequest,
) -> float:
    stiffness = bundle.mount.spring_stiffness_n_per_mm
    if stiffness is None:
        return 0.0
    compression = request.immutable_single_spine_state_n.spring_compression_mm
    return 0.5 * stiffness * compression**2


def _part_clearance(values: dict[NeedlePart, Any], part: NeedlePart) -> float | None:
    value = values.get(part)
    return None if value is None else value.certified_euclidean_clearance_lower_bound_mm


def _wrench_nullspace(
    values: tuple[tuple[float, ...], ...],
) -> tuple[Vector6, ...]:
    result: list[Vector6] = []
    for value in values:
        padded = tuple((*value, *([0.0] * 6))[:6])
        result.append(padded)  # type: ignore[arg-type]
    return tuple(result)


def _global_to_needle(value: Vector3, axis: Vector3) -> Vector3:
    from .beam import needle_basis

    result = needle_basis(axis).T @ np.asarray(value, dtype=np.float64)
    return _tuple3(result)


def _matrix3_tuple(value: np.ndarray[Any, Any]) -> tuple[Vector3, Vector3, Vector3]:
    return tuple(_tuple3(row) for row in value)  # type: ignore[return-value]


def _tuple3(value: Any) -> Vector3:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (3,) or not np.isfinite(array).all():
        raise ContractViolation("expected a finite three-vector")
    return tuple(float(item) for item in array)  # type: ignore[return-value]


def _add3(left: Vector3, right: Vector3) -> Vector3:
    return _tuple3(np.asarray(left, dtype=np.float64) + np.asarray(right, dtype=np.float64))


__all__ = [
    "IntrinsicSingleSpineKernel",
    "KernelEvaluation",
    "KernelEvaluationArtifacts",
    "make_needle_identity",
]
