from __future__ import annotations

import math

import numpy as np
import pytest

from spine_sim.single_spine.beam import (
    circular_section,
    corotational_validation_reference,
    solve_euler_bernoulli,
    timoshenko_validation_reference,
)
from spine_sim.single_spine.contact import (
    ContactKinematics,
    deterministic_tangent_basis,
    objective_slip_increment,
    project_lorentz_cone,
    solve_rigid_contact_graph,
)
from spine_sim.single_spine.contracts import (
    BeamModelState,
    ContactMotionState,
    MountMode,
    SpringState,
    WrenchUniqueness,
    make_baseline_parameter_bundle,
)
from spine_sim.single_spine.mount import solve_mount_graph


def test_euler_bernoulli_analytic_axial_bending_energy_and_centerline() -> None:
    bundle = make_baseline_parameter_bundle()
    needle = bundle.needle
    beam = bundle.beam
    section = circular_section(needle, beam)
    assert beam.youngs_modulus_mpa is not None
    response = solve_euler_bernoulli(
        needle=needle,
        beam=beam,
        root_position_global_mm=(1.0, 2.0, 3.0),
        initial_axis_global=(1.0, 0.0, 0.0),
        contact_force_global_n=(1.0, 2.0, 0.0),
    )
    length = needle.exposed_length_mm
    expected_axial = length / (beam.youngs_modulus_mpa * section.area_mm2)
    expected_bending = 2.0 * length**3 / (3.0 * beam.youngs_modulus_mpa * section.second_moment_mm4)
    assert response.tip_translation_global_mm[0] == pytest.approx(expected_axial)
    assert response.tip_translation_global_mm[1] == pytest.approx(expected_bending)
    assert response.tip_rotation_global_rad[2] == pytest.approx(
        2.0 * length**2 / (2.0 * beam.youngs_modulus_mpa * section.second_moment_mm4)
    )
    generalized_work = np.dot(
        np.array((1.0, 2.0, 0.0)), np.array(response.tip_translation_global_mm)
    )
    assert response.energy_n_mm == pytest.approx(0.5 * generalized_work)
    assert response.root_reaction_force_global_n == (-1.0, -2.0, -0.0)
    assert response.centerline[0].position_global_mm == (1.0, 2.0, 3.0)
    assert response.centerline[-1].translation_global_mm == pytest.approx(
        response.tip_translation_global_mm
    )


def test_bending_off_keeps_root_resultants_but_zeroes_deformation_and_energy() -> None:
    bundle = make_baseline_parameter_bundle(bending_enabled=False)
    response = solve_euler_bernoulli(
        needle=bundle.needle,
        beam=bundle.beam,
        root_position_global_mm=(0.0, 0.0, 0.0),
        initial_axis_global=(1.0, 0.0, 0.0),
        contact_force_global_n=(0.0, 1.0, 0.0),
    )
    assert response.model_state is BeamModelState.BENDING_OFF
    assert response.tip_translation_global_mm == (0.0, 0.0, 0.0)
    assert response.tip_rotation_global_rad == (0.0, 0.0, 0.0)
    assert response.energy_n_mm == 0.0
    assert response.root_reaction_force_global_n == (-0.0, -1.0, -0.0)
    assert response.section_resultants_needle != (0.0,) * 6


def test_validation_only_beam_references_converge_from_accepted_eb() -> None:
    bundle = make_baseline_parameter_bundle()
    response = solve_euler_bernoulli(
        needle=bundle.needle,
        beam=bundle.beam,
        root_position_global_mm=(0.0, 0.0, 0.0),
        initial_axis_global=(1.0, 0.0, 0.0),
        contact_force_global_n=(0.0, 0.01, 0.0),
    )
    timoshenko = timoshenko_validation_reference(
        response,
        needle=bundle.needle,
        beam=bundle.beam,
        contact_force_global_n=(0.0, 0.01, 0.0),
        initial_axis_global=(1.0, 0.0, 0.0),
    )
    corotational = corotational_validation_reference(response)
    assert timoshenko[1] > response.tip_translation_global_mm[1]
    assert np.linalg.norm(np.asarray(corotational) - response.tip_translation_global_mm) < 1e-5


def test_a_authoritative_mount_zero_interior_stop_unload_and_rigid_graph() -> None:
    spring = make_baseline_parameter_bundle().mount
    original = solve_mount_graph(
        parameters=spring,
        initial_axis_global=(0.0, 0.0, -1.0),
        contact_force_global_n=(0.0, 0.0, 0.0),
    )
    interior = solve_mount_graph(
        parameters=spring,
        initial_axis_global=(0.0, 0.0, -1.0),
        contact_force_global_n=(0.0, 0.0, 0.5),
    )
    stop = solve_mount_graph(
        parameters=spring,
        initial_axis_global=(0.0, 0.0, -1.0),
        contact_force_global_n=(0.0, 0.0, 3.0),
    )
    unload = solve_mount_graph(
        parameters=spring,
        initial_axis_global=(0.0, 0.0, -1.0),
        contact_force_global_n=(0.0, 0.0, -0.1),
    )
    assert original.state is SpringState.AT_ORIGINAL_LENGTH
    assert interior.state is SpringState.COMPRESSING
    assert interior.compression_mm == pytest.approx(1.0)
    assert interior.energy_n_mm == pytest.approx(0.25)
    assert stop.state is SpringState.HARD_STOP
    assert stop.compression_mm == 4.0
    assert stop.spring_force_n == 2.0
    assert stop.hard_stop_reaction_n == 1.0
    assert unload.state is SpringState.AT_ORIGINAL_LENGTH
    assert unload.requires_contact_release

    rigid = make_baseline_parameter_bundle(
        mount_mode=MountMode.RIGID_MOUNT,
        spring_stiffness_n_per_mm=None,
    ).mount
    locked = solve_mount_graph(
        parameters=rigid,
        initial_axis_global=(0.0, 0.0, -1.0),
        contact_force_global_n=(0.0, 0.0, 0.5),
    )
    assert locked.state is SpringState.RIGID_LOCKED
    assert locked.incremental_axial_compliance_mm_per_n == 0.0
    assert locked.set_valued_constraint
    assert locked.admissible_graph_handle is not None


def _support(
    *,
    support_id: str = "support",
    gap: float,
    slip: tuple[float, float, float] = (0.0, 0.0, 0.0),
    migrated: bool = False,
) -> ContactKinematics:
    normal = (0.0, 0.0, 1.0)
    return ContactKinematics(
        support_id,
        f"candidate-{support_id}",
        (0.0, 0.0, 0.0),
        normal,
        deterministic_tangent_basis(normal, (1.0, 0.0, 0.0)),
        gap,
        slip,
        support_migrated=migrated,
    )


def _solve(
    supports: tuple[ContactKinematics, ...],
    *,
    free: tuple[float, float, float] = (0.0, 0.0, 0.0),
    mu: float = 0.4,
    slip_tolerance_mm: float = 1e-9,
):
    return solve_rigid_contact_graph(
        supports=supports,
        point_compliance_global_mm_per_n=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        free_tip_increment_global_mm=free,
        friction_coefficient=mu,
        gap_tolerance_mm=1e-9,
        force_tolerance_n=1e-9,
        slip_tolerance_mm=slip_tolerance_mm,
    )


def test_signorini_open_zero_loaded_mu_zero_stick_boundary_and_true_slide() -> None:
    assert _solve((_support(gap=0.1),)).branch_id == "OPEN_GRAPH"

    zero = _solve((_support(gap=0.0),))
    assert zero.supports[0].normal_multiplier_n == 0.0
    assert zero.supports[0].motion_state is ContactMotionState.TOUCH_ZERO_LOAD

    loaded = _solve((_support(gap=-0.1),))
    assert loaded.supports[0].normal_multiplier_n == pytest.approx(0.1)
    assert loaded.supports[0].motion_state is ContactMotionState.STICKING_INTERIOR
    assert loaded.graph_quality_passed

    boundary = _solve((_support(gap=-0.1, slip=(0.04, 0.0, 0.0)),))
    assert boundary.supports[0].motion_state is ContactMotionState.STICKING_AT_CONE_BOUNDARY
    assert boundary.supports[0].tangential_multiplier_n == pytest.approx((-0.04, 0.0))
    assert boundary.supports[0].objective_slip_increment_local_mm == pytest.approx((0.0, 0.0))

    frictionless = _solve(
        (_support(gap=-0.1, slip=(0.1, 0.0, 0.0)),),
        mu=0.0,
    )
    assert frictionless.supports[0].tangential_multiplier_n == pytest.approx((0.0, 0.0))
    assert frictionless.supports[0].motion_state is ContactMotionState.SLIDING_COMMITTED

    slide = _solve(
        (_support(gap=-0.1, slip=(0.2, 0.1, 0.0)),),
    )
    assert slide.branch_id == "MAXIMUM_DISSIPATION_SLIDE"
    assert slide.supports[0].maximum_dissipation_closed
    assert slide.supports[0].all_stick_friction_margin_n < 0.0
    assert not slide.supports[0].all_stick_feasible
    assert math.hypot(*slide.supports[0].tangential_multiplier_n) == pytest.approx(
        0.4 * slide.supports[0].normal_multiplier_n
    )
    traction = np.asarray(slide.supports[0].tangential_multiplier_n)
    final_slip = np.asarray(slide.supports[0].objective_slip_increment_local_mm)
    assert np.dot(traction, final_slip) / (
        np.linalg.norm(traction) * np.linalg.norm(final_slip)
    ) == pytest.approx(-1.0)
    assert slide.supports[0].graph_residual <= 1.0e-9


def test_contact_uses_per_support_objective_slip_when_global_free_is_zero() -> None:
    no_tangential_predictor = _solve((_support(gap=-0.1),), free=(0.0, 0.0, 0.0))
    pure_tangential_step = _solve(
        (_support(gap=-0.1, slip=(0.02, 0.0, 0.0)),),
        free=(0.0, 0.0, 0.0),
    )

    assert no_tangential_predictor.supports[0].tangential_multiplier_n == (0.0, 0.0)
    assert pure_tangential_step.supports[0].tangential_multiplier_n == pytest.approx((-0.02, 0.0))
    assert pure_tangential_step.supports[0].objective_slip_increment_local_mm == pytest.approx(
        (0.0, 0.0)
    )
    assert pure_tangential_step.supports[0].motion_state is ContactMotionState.STICKING_INTERIOR


def test_subresolution_cone_return_is_feasible_but_not_committed_as_slip() -> None:
    result = _solve(
        (_support(gap=-0.1, slip=(0.05, 0.0, 0.0)),),
        slip_tolerance_mm=0.02,
    )
    support = result.supports[0]

    assert result.branch_id == "ONE_SIDED_CONE_BOUNDARY"
    assert result.branch_feasible and result.graph_quality_passed
    assert support.motion_state is ContactMotionState.STICKING_AT_CONE_BOUNDARY
    assert not support.all_stick_feasible
    assert not support.maximum_dissipation_closed
    assert 0.0 < math.hypot(*support.objective_slip_increment_local_mm) <= 0.02
    traction = np.asarray(support.tangential_multiplier_n)
    slip = np.asarray(support.objective_slip_increment_local_mm)
    assert np.dot(traction, slip) / (np.linalg.norm(traction) * np.linalg.norm(slip)) == (
        pytest.approx(-1.0)
    )


def test_multi_support_set_valued_and_solution_is_order_independent() -> None:
    first = _support(support_id="a", gap=-0.1)
    second = _support(support_id="b", gap=-0.1)
    forward = _solve((first, second))
    reverse = _solve((second, first))
    assert forward.wrench_uniqueness is WrenchUniqueness.SET_VALUED_CONSTRAINT
    assert forward.admissible_graph_handle is not None
    assert forward.nullspace_basis
    assert forward.resultant_force_global_n == pytest.approx(reverse.resultant_force_global_n)
    assert {item.support_id: item.final_gap_mm for item in forward.supports} == pytest.approx(
        {item.support_id: item.final_gap_mm for item in reverse.supports}
    )

    sliding_first = _support(support_id="a", gap=-0.1, slip=(0.2, 0.1, 0.0))
    sliding_second = _support(support_id="b", gap=-0.1, slip=(0.2, 0.1, 0.0))
    sliding_forward = _solve((sliding_first, sliding_second))
    sliding_reverse = _solve((sliding_second, sliding_first))
    assert sliding_forward.branch_id == "MAXIMUM_DISSIPATION_SLIDE"
    assert sliding_forward.branch_feasible and sliding_forward.graph_quality_passed
    assert all(item.maximum_dissipation_closed for item in sliding_forward.supports)
    assert sliding_forward.resultant_force_global_n == pytest.approx(
        sliding_reverse.resultant_force_global_n
    )


def test_objective_midpoint_slip_and_rolling_are_not_historical_slip_tests() -> None:
    slip = objective_slip_increment(
        tip_translation_increment_global_mm=(1.0, 2.0, 3.0),
        tip_rotation_increment_global_rad=(0.0, 0.0, 1.0),
        support_point_mid_global_mm=(1.0, 0.0, 0.0),
        tip_center_mid_global_mm=(0.0, 0.0, 0.0),
        normal_mid_global=(0.0, 0.0, 1.0),
    )
    assert slip == pytest.approx((1.0, 3.0, 0.0))
    sticking = _solve((_support(gap=-0.1),))
    rolling = _solve((_support(gap=-0.1, migrated=True),))
    assert sticking.supports[0].motion_state is ContactMotionState.STICKING_INTERIOR
    assert rolling.supports[0].motion_state is ContactMotionState.ROLLING_NO_SLIP
    assert rolling.supports[0].objective_slip_increment_local_mm == (0.0, 0.0)
    assert rolling.resultant_force_global_n == pytest.approx(sticking.resultant_force_global_n)

    assert project_lorentz_cone((2.0, 0.2, 0.3)) == (2.0, 0.2, 0.3)
    assert project_lorentz_cone((-2.0, 0.2, 0.3)) == (0.0, 0.0, 0.0)
