from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any, cast

import numpy as np
import pytest
from numpy.typing import NDArray

from spine_sim.foundation.errors import ContractViolation
from spine_sim.single_spine import surface_adapter
from spine_sim.single_spine.contracts import (
    SURFACE_SCALE_REFERENCE_RT_MM,
    LODPurpose,
    SingleSpineParameterBundle,
    canonical_local_frame,
    make_baseline_parameter_bundle,
)
from spine_sim.single_spine.geometry import (
    CollisionRole,
    ExplicitCenterlineProvider,
    NeedlePart,
    TipPose,
    build_composite_needle_geometry,
    engineering_initial_axis,
    finite_cap_legality_margin_mm,
    is_finite_cap_legal,
    make_swept_needle_geometry,
    resolve_tip_pose,
    rotation_matrix_from_global_vector,
    sample_centerline,
)
from spine_sim.single_spine.surface_adapter import (
    BodyCollisionStatus,
    CandidateOrigin,
    GeometryGateStatus,
    collect_support_candidates,
    derive_complete_query_footprint,
    evaluate_body_collision,
    make_geometry_query_policy,
    make_identity_surface_frame_transform,
)
from spine_sim.surface import (
    FootprintGuard,
    QueryResponse,
    SurfaceFamily,
    SurfaceProvider,
    SurfaceQueryHandle,
    make_analytic_source_descriptor,
    query_spherical_envelope_or_clearance,
)

FloatArray = NDArray[np.float64]
Vector3 = tuple[float, float, float]


def _vector3(value: FloatArray) -> Vector3:
    assert value.shape == (3,)
    return float(value[0]), float(value[1]), float(value[2])


def _surface_handle(
    family: SurfaceFamily,
    parameters: Mapping[str, object],
) -> SurfaceQueryHandle:
    provider = SurfaceProvider()
    descriptor = make_analytic_source_descriptor()
    spec_result = provider.create_surface_spec(descriptor, family, dict(parameters))
    assert spec_result.spec is not None, spec_result.status.explanation
    realization_result = provider.create_realization(descriptor, spec_result.spec)
    assert realization_result.handle is not None, realization_result.status.explanation
    return cast(SurfaceQueryHandle, realization_result.handle)


def _tip_pose_at(
    center_global_mm: Vector3,
    bundle: SingleSpineParameterBundle,
    *,
    translation_global_mm: Vector3 = (0.0, 0.0, 0.0),
    rotation_global_rad: Vector3 = (0.0, 0.0, 0.0),
) -> TipPose:
    frame = canonical_local_frame()
    axis = np.asarray(
        engineering_initial_axis(frame, bundle.needle.alpha_rad, bundle.needle.beta_rad),
        dtype=np.float64,
    )
    center = np.asarray(center_global_mm, dtype=np.float64)
    translation = np.asarray(translation_global_mm, dtype=np.float64)
    rigid_root = center - translation - bundle.needle.exposed_length_mm * axis
    return resolve_tip_pose(
        rigid_root_global_mm=_vector3(rigid_root),
        local_frame=frame,
        needle=bundle.needle,
        beam_tip_translation_global_mm=translation_global_mm,
        beam_tip_rotation_global_rad=rotation_global_rad,
    )


def test_engineering_axis_and_global_left_pose_are_unambiguous() -> None:
    bundle = make_baseline_parameter_bundle()
    frame = canonical_local_frame()
    axis = np.asarray(
        engineering_initial_axis(frame, bundle.needle.alpha_rad, bundle.needle.beta_rad)
    )
    np.testing.assert_allclose(axis, (0.5, 0.0, -math.sqrt(3.0) / 2.0), atol=1.0e-14)

    theta = (0.0, 0.0, math.pi / 2.0)
    pose = _tip_pose_at((75.0, 75.0, 1.0), bundle, rotation_global_rad=theta)
    expected = rotation_matrix_from_global_vector(theta) @ axis
    np.testing.assert_allclose(pose.current_axis_global, expected, atol=1.0e-14)
    stored_rotation = np.asarray(pose.current_rotation_global_from_needle)
    np.testing.assert_allclose(stored_rotation[:, 0], expected, atol=1.0e-14)
    assert pose.closure_id == "M03_GLOBAL_LEFT_MULTIPLY_P0_1"
    assert pose.source_identity == "PROPOSED_SUPPLEMENT"

    with pytest.raises(ContractViolation, match="production beta must be zero"):
        engineering_initial_axis(frame, bundle.needle.alpha_rad, 0.1)


def test_finite_cap_rejects_the_rear_sphere() -> None:
    bundle = make_baseline_parameter_bundle()
    radius = bundle.needle.tip_radius_mm
    blend = bundle.needle.cap_blend_coordinate_mm
    apex = (radius, 0.0, 0.0)
    rear = (-radius, 0.0, 0.0)

    assert finite_cap_legality_margin_mm(apex, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), blend) > 0.0
    assert is_finite_cap_legal(apex, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), blend)
    assert not is_finite_cap_legal(rear, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), blend)


def test_beam_owned_centerline_builds_the_complete_composite_and_sweep() -> None:
    bundle = make_baseline_parameter_bundle()
    translation = (0.0, 0.12, 0.04)
    rotation = (0.0, 0.02, 0.0)
    pose = _tip_pose_at(
        (75.0, 75.0, 1.0),
        bundle,
        translation_global_mm=translation,
        rotation_global_rad=rotation,
    )
    root = np.asarray(pose.current_root_global_mm)
    tip = np.asarray(pose.current_tip_center_global_mm)
    controls = (
        _vector3(root),
        _vector3(0.5 * (root + tip) + np.array((0.0, 0.08, 0.03))),
        _vector3(tip),
    )
    provider = ExplicitCenterlineProvider(controls, "TEST_EB_CENTERLINE")
    centerline = sample_centerline(
        provider,
        expected_root_global_mm=_vector3(root),
        expected_tip_center_global_mm=_vector3(tip),
        sample_count=33,
    )
    geometry = build_composite_needle_geometry(
        tip_pose=pose,
        needle=bundle.needle,
        centerline=centerline,
        axial_sample_count=33,
        radial_sample_count=16,
    )

    assert tuple(part.part for part in geometry.parts) == tuple(NeedlePart)
    assert geometry.part(NeedlePart.TIP_CAP).collision_role is CollisionRole.LEGAL_TIP_CONTACT
    assert all(
        geometry.part(part).collision_role is CollisionRole.FORBIDDEN_BODY
        for part in (NeedlePart.CONE, NeedlePart.SHAFT, NeedlePart.MOUNT)
    )
    np.testing.assert_allclose(centerline.points_global_mm[0], root)
    np.testing.assert_allclose(centerline.points_global_mm[-1], tip)

    with pytest.raises(ContractViolation, match="explicit beam-owned CenterlineProvider"):
        build_composite_needle_geometry(tip_pose=pose, needle=bundle.needle)

    second_pose = _tip_pose_at((75.02, 75.0, 1.0), bundle)
    second_geometry = build_composite_needle_geometry(
        tip_pose=second_pose,
        needle=bundle.needle,
        axial_sample_count=33,
        radial_sample_count=16,
    )
    rigid_first = build_composite_needle_geometry(
        tip_pose=_tip_pose_at((75.0, 75.0, 1.0), bundle),
        needle=bundle.needle,
        axial_sample_count=33,
        radial_sample_count=16,
    )
    sweep = make_swept_needle_geometry((rigid_first, second_geometry))
    for part in NeedlePart:
        assert len(sweep.part(part).witness_points_global_mm) == 2 * len(
            rigid_first.part(part).surface_points_global_mm
        )
        assert (
            sweep.part(part).continuous_cover_radius_mm
            >= rigid_first.part(part).surface_cover_radius_mm
        )


def test_ring_cover_combines_axial_radial_and_circumferential_errors() -> None:
    bundle = make_baseline_parameter_bundle()
    axial_count = 33
    radial_count = 16
    geometry = build_composite_needle_geometry(
        tip_pose=_tip_pose_at((75.0, 75.0, 1.0), bundle),
        needle=bundle.needle,
        axial_sample_count=axial_count,
        radial_sample_count=radial_count,
    )

    blend_radius = math.sqrt(
        bundle.needle.tip_radius_mm**2 - bundle.needle.cap_blend_coordinate_mm**2
    )
    cone_components = (
        0.5 * bundle.needle.cone_length_mm / (axial_count - 1),
        0.5 * abs(bundle.needle.diameter_mm / 2.0 - blend_radius) / (axial_count - 1),
        bundle.needle.diameter_mm * math.pi / (2.0 * radial_count),
    )
    expected_cone_cover = math.hypot(*cone_components)
    assert geometry.part(NeedlePart.CONE).surface_cover_radius_mm == pytest.approx(
        expected_cone_cover,
        rel=1.0e-13,
    )
    assert expected_cone_cover < sum(cone_components)

    mount_components = (
        0.5 * bundle.needle.mount_length_mm / (axial_count - 1),
        0.0,
        bundle.needle.mount_radius_mm * math.pi / radial_count,
    )
    assert geometry.part(NeedlePart.MOUNT).surface_cover_radius_mm == pytest.approx(
        math.hypot(*mount_components),
        rel=1.0e-13,
    )


def test_complete_footprint_and_candidate_merge_keep_all_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = make_baseline_parameter_bundle()
    handle = _surface_handle(SurfaceFamily.PLANE, {"offset_mm": 0.0})
    transform = make_identity_surface_frame_transform(handle)
    policy = make_geometry_query_policy()
    pose = _tip_pose_at((75.0, 75.0, bundle.needle.tip_radius_mm), bundle)
    geometry = build_composite_needle_geometry(
        tip_pose=pose,
        needle=bundle.needle,
        axial_sample_count=33,
        radial_sample_count=16,
    )
    sweep = make_swept_needle_geometry((geometry,))
    footprint = derive_complete_query_footprint(handle, sweep, transform, policy)

    points = transform.global_to_surface_points(sweep.all_witness_points_global_mm)
    guard = FootprintGuard(
        probe_radius_mm=sweep.maximum_cover_radius_mm,
        trusted_scale_halo_mm=policy.trusted_scale_halo_mm,
        derivative_search_halo_mm=policy.derivative_search_halo_mm,
        tile_halo_mm=policy.tile_halo_mm,
        declared_clearance_guard_mm=policy.declared_clearance_guard_mm,
    ).effective_mm
    assert footprint.x_min_mm == pytest.approx(float(np.min(points[:, 0])) - guard)
    assert footprint.x_max_mm == pytest.approx(float(np.max(points[:, 0])) + guard)
    assert footprint.y_min_mm == pytest.approx(float(np.min(points[:, 1])) - guard)
    assert footprint.y_max_mm == pytest.approx(float(np.max(points[:, 1])) + guard)
    assert footprint.x_max_mm - footprint.x_min_mm < 10.0

    spherical_responses: list[QueryResponse] = []
    spherical_probe_shapes: list[tuple[int, ...]] = []
    spherical_paths: list[object] = []
    original_spherical_query = query_spherical_envelope_or_clearance

    def spherical_query_spy(*args: Any, **kwargs: Any) -> QueryResponse:
        response = original_spherical_query(*args, **kwargs)
        spherical_responses.append(response)
        spherical_probe_shapes.append(np.asarray(args[1]).shape)
        spherical_paths.append(kwargs.get("path"))
        return response

    monkeypatch.setattr(
        surface_adapter,
        "query_spherical_envelope_or_clearance",
        spherical_query_spy,
    )

    first = collect_support_candidates(
        handle,
        tip_pose=pose,
        tip_radius_mm=bundle.needle.tip_radius_mm,
        cap_blend_coordinate_mm=bundle.needle.cap_blend_coordinate_mm,
        footprint=footprint,
        transform=transform,
        policy=policy,
    )
    assert first.gate_status is GeometryGateStatus.PASSED
    assert spherical_probe_shapes == [(5, 3)]
    assert spherical_paths == ["phi_minus_radius"]
    assert spherical_responses[0].query_id in first.all_query_receipt_ids
    assert len(first.candidates) == 5
    active = [item for item in first.candidates if item.admissible_support_candidate]
    assert len(active) == 1
    assert active[0].origins == (CandidateOrigin.CURRENT_NEAREST,)
    assert active[0].finite_cap_legal
    assert active[0].local_minimum_verified
    assert active[0].empty_ball_verified
    assert (
        sum(CandidateOrigin.NEARBY_SWITCH_PROBE in item.origins for item in first.candidates) == 4
    )

    shifted_pose = _tip_pose_at((75.02, 75.0, bundle.needle.tip_radius_mm), bundle)
    shifted_geometry = build_composite_needle_geometry(
        tip_pose=shifted_pose,
        needle=bundle.needle,
        axial_sample_count=33,
        radial_sample_count=16,
    )
    shifted_sweep = make_swept_needle_geometry((geometry, shifted_geometry))
    shifted_footprint = derive_complete_query_footprint(handle, shifted_sweep, transform, policy)
    second = collect_support_candidates(
        handle,
        tip_pose=shifted_pose,
        tip_radius_mm=bundle.needle.tip_radius_mm,
        cap_blend_coordinate_mm=bundle.needle.cap_blend_coordinate_mm,
        footprint=shifted_footprint,
        transform=transform,
        policy=policy,
        previous_active_candidates=active,
    )
    retained = [
        item for item in second.candidates if CandidateOrigin.PREVIOUS_ACTIVE in item.origins
    ]
    assert len(retained) == 1
    assert spherical_probe_shapes == [(5, 3), (5, 3)]
    assert spherical_responses[1].query_id in second.all_query_receipt_ids
    assert not retained[0].local_minimum_verified
    assert first.current_query_receipt_id in second.all_query_receipt_ids
    assert second.current_query_receipt_id in second.all_query_receipt_ids
    assert all(
        CandidateOrigin.CURRENT_NEAREST in item.origins
        or CandidateOrigin.CURRENT_CO_MINIMAL in item.origins
        for item in second.candidates
        if item.candidate_id in second.active_graph_candidate_ids
    )


def test_penetrating_trial_keeps_m01_outward_normal_and_signed_gap() -> None:
    bundle = make_baseline_parameter_bundle()
    handle = _surface_handle(SurfaceFamily.PLANE, {"offset_mm": 0.0})
    transform = make_identity_surface_frame_transform(handle)
    policy = make_geometry_query_policy()
    pose = _tip_pose_at((75.0, 75.0, -0.01), bundle)
    geometry = build_composite_needle_geometry(
        tip_pose=pose,
        needle=bundle.needle,
        axial_sample_count=33,
        radial_sample_count=16,
    )
    sweep = make_swept_needle_geometry((geometry,))
    footprint = derive_complete_query_footprint(handle, sweep, transform, policy)
    result = collect_support_candidates(
        handle,
        tip_pose=pose,
        tip_radius_mm=bundle.needle.tip_radius_mm,
        cap_blend_coordinate_mm=bundle.needle.cap_blend_coordinate_mm,
        footprint=footprint,
        transform=transform,
        policy=policy,
    )

    current = next(
        item for item in result.candidates if CandidateOrigin.CURRENT_NEAREST in item.origins
    )
    assert current.signed_distance_from_current_center_mm == pytest.approx(-0.01)
    assert current.sphere_gap_mm == pytest.approx(-0.06)
    assert current.outward_normals_global == ((0.0, 0.0, 1.0),)
    assert current.radial_normal_global == pytest.approx((0.0, 0.0, 1.0))
    assert current.local_minimum_verified
    assert current.empty_ball_verified
    assert current.admissible_support_candidate


def test_candidate_identity_binds_chart_and_complete_query_receipts() -> None:
    bundle = make_baseline_parameter_bundle()
    handle = _surface_handle(SurfaceFamily.PLANE, {"offset_mm": 0.0})
    transform = make_identity_surface_frame_transform(handle)
    policy = make_geometry_query_policy()
    radius = bundle.needle.tip_radius_mm
    pose = _tip_pose_at((75.0, 75.0, radius), bundle)
    geometry = build_composite_needle_geometry(
        tip_pose=pose,
        needle=bundle.needle,
        axial_sample_count=17,
        radial_sample_count=8,
    )
    footprint = derive_complete_query_footprint(
        handle,
        make_swept_needle_geometry((geometry,)),
        transform,
        policy,
    )

    first = collect_support_candidates(
        handle,
        tip_pose=pose,
        tip_radius_mm=radius,
        cap_blend_coordinate_mm=bundle.needle.cap_blend_coordinate_mm,
        footprint=footprint,
        transform=transform,
        policy=policy,
    )
    alternate_switch_probes = (
        (74.975, 75.0, radius),
        (75.025, 75.0, radius),
        (75.0, 74.975, radius),
        (75.0, 75.025, radius),
    )
    second = collect_support_candidates(
        handle,
        tip_pose=pose,
        tip_radius_mm=radius,
        cap_blend_coordinate_mm=bundle.needle.cap_blend_coordinate_mm,
        footprint=footprint,
        transform=transform,
        policy=policy,
        nearby_probe_centers_global_mm=alternate_switch_probes,
    )
    deterministic_replay = collect_support_candidates(
        handle,
        tip_pose=pose,
        tip_radius_mm=radius,
        cap_blend_coordinate_mm=bundle.needle.cap_blend_coordinate_mm,
        footprint=footprint,
        transform=transform,
        policy=policy,
        nearby_probe_centers_global_mm=alternate_switch_probes,
    )
    first_current = next(
        item for item in first.candidates if CandidateOrigin.CURRENT_NEAREST in item.origins
    )
    second_current = next(
        item for item in second.candidates if CandidateOrigin.CURRENT_NEAREST in item.origins
    )

    assert first_current.feature_id == second_current.feature_id
    assert first_current.chart_id == second_current.chart_id == first_current.feature_id
    assert first_current.point_global_mm == second_current.point_global_mm
    assert first_current.query_receipt_ids != second_current.query_receipt_ids
    assert first_current.candidate_id != second_current.candidate_id
    replay_current = next(
        item
        for item in deterministic_replay.candidates
        if CandidateOrigin.CURRENT_NEAREST in item.origins
    )
    assert replay_current.query_receipt_ids == second_current.query_receipt_ids
    assert replay_current.candidate_id == second_current.candidate_id


def test_known_switch_retains_both_co_minimal_supports() -> None:
    bundle = make_baseline_parameter_bundle()
    handle = _surface_handle(
        SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH,
        {"offset_mm": 0.0, "ridge_slope": 0.5},
    )
    transform = make_identity_surface_frame_transform(handle)
    policy = make_geometry_query_policy()
    pose = _tip_pose_at((75.0, 75.0, 1.0), bundle)
    geometry = build_composite_needle_geometry(
        tip_pose=pose,
        needle=bundle.needle,
        axial_sample_count=33,
        radial_sample_count=16,
    )
    sweep = make_swept_needle_geometry((geometry,))
    footprint = derive_complete_query_footprint(handle, sweep, transform, policy)
    result = collect_support_candidates(
        handle,
        tip_pose=pose,
        tip_radius_mm=bundle.needle.tip_radius_mm,
        cap_blend_coordinate_mm=bundle.needle.cap_blend_coordinate_mm,
        footprint=footprint,
        transform=transform,
        policy=policy,
    )

    current = [
        item for item in result.candidates if CandidateOrigin.CURRENT_CO_MINIMAL in item.origins
    ]
    assert result.gate_status is GeometryGateStatus.PASSED_NONSMOOTH_GRAPH
    assert result.nonsmooth_or_nonunique
    assert {item.feature_id for item in current} == {
        "switch_face_negative",
        "switch_face_positive",
    }
    assert len(result.active_graph_candidate_ids) == 2
    assert all(item.local_minimum_verified and item.empty_ball_verified for item in current)


def test_body_collision_distinguishes_clear_and_forbidden_contact() -> None:
    bundle = make_baseline_parameter_bundle()
    pose = _tip_pose_at((75.0, 75.0, 1.0), bundle)
    geometry = build_composite_needle_geometry(
        tip_pose=pose,
        needle=bundle.needle,
        axial_sample_count=33,
        radial_sample_count=16,
    )
    sweep = make_swept_needle_geometry((geometry,))
    policy = make_geometry_query_policy()

    clear_handle = _surface_handle(SurfaceFamily.PLANE, {"offset_mm": 0.0})
    clear_transform = make_identity_surface_frame_transform(clear_handle)
    clear_footprint = derive_complete_query_footprint(clear_handle, sweep, clear_transform, policy)
    clear = evaluate_body_collision(
        clear_handle,
        swept_geometry=sweep,
        footprint=clear_footprint,
        transform=clear_transform,
        policy=policy,
    )
    assert clear.status is BodyCollisionStatus.CLEAR
    assert all(
        item.continuously_certified_clear
        for item in clear.part_clearances
        if item.collision_role is CollisionRole.FORBIDDEN_BODY
    )

    collision_handle = _surface_handle(SurfaceFamily.PLANE, {"offset_mm": 2.0})
    collision_transform = make_identity_surface_frame_transform(collision_handle)
    collision_footprint = derive_complete_query_footprint(
        collision_handle, sweep, collision_transform, policy
    )
    collision = evaluate_body_collision(
        collision_handle,
        swept_geometry=sweep,
        footprint=collision_footprint,
        transform=collision_transform,
        policy=policy,
    )
    assert collision.status is BodyCollisionStatus.BODY_COLLISION_INVALID
    assert collision.controlling_part in {
        NeedlePart.CONE,
        NeedlePart.SHAFT,
        NeedlePart.MOUNT,
    }
    controlling = next(
        item for item in collision.part_clearances if item.part is collision.controlling_part
    )
    assert controlling.collided_at_witness
    assert controlling.collision_role is CollisionRole.FORBIDDEN_BODY


def test_lod_policy_and_refinement_failure_are_explicit() -> None:
    expected_spacing = {
        LODPurpose.AHEAD: SURFACE_SCALE_REFERENCE_RT_MM / 5.0,
        LODPurpose.EVENT_SUPPORT: SURFACE_SCALE_REFERENCE_RT_MM / 8.0,
        LODPurpose.ACCEPTANCE_WITNESS: SURFACE_SCALE_REFERENCE_RT_MM / 10.0,
    }
    for purpose, spacing in expected_spacing.items():
        policy = make_geometry_query_policy(purpose)
        assert policy.surface_scale_reference_rt_mm == SURFACE_SCALE_REFERENCE_RT_MM
        assert policy.declared_spacing_mm == pytest.approx(spacing)

    bundle = make_baseline_parameter_bundle()
    handle = _surface_handle(
        SurfaceFamily.GAUSSIAN_BUMP,
        {"amplitude_mm": 0.8, "sigma_mm": 1.2},
    )
    transform = make_identity_surface_frame_transform(handle)
    policy = make_geometry_query_policy(maximum_global_cells=16)
    pose = _tip_pose_at((75.35, 75.1, 1.4), bundle)
    geometry = build_composite_needle_geometry(
        tip_pose=pose,
        needle=bundle.needle,
        axial_sample_count=17,
        radial_sample_count=8,
    )
    sweep = make_swept_needle_geometry((geometry,))
    footprint = derive_complete_query_footprint(handle, sweep, transform, policy)
    result = collect_support_candidates(
        handle,
        tip_pose=pose,
        tip_radius_mm=bundle.needle.tip_radius_mm,
        cap_blend_coordinate_mm=bundle.needle.cap_blend_coordinate_mm,
        footprint=footprint,
        transform=transform,
        policy=policy,
    )
    assert result.gate_status is GeometryGateStatus.GEOMETRY_UNCERTAIN
    assert result.reason_code == "M01_RESOLUTION_REFINEMENT_REQUIRED"
    assert result.active_graph_candidate_ids == ()
    assert all(not item.query_quality_passed for item in result.candidates)


def test_actual_m01_stationary_distance_maximum_and_saddle_are_not_active_supports() -> None:
    """A Newton stationary point is not sufficient M03 support evidence."""

    bundle = make_baseline_parameter_bundle()
    cases = (
        (
            SurfaceFamily.GAUSSIAN_BUMP,
            {"amplitude_mm": 0.8, "sigma_mm": 0.5},
            (75.0, 75.0, -1.0),
            (75.0, 75.0, 0.8),
        ),
        (
            SurfaceFamily.SINUSOID_2D,
            {
                "amplitude_mm": 0.2,
                "wavelength_mm": 1.0,
                "origin_x_mm": 75.0,
                "origin_y_mm": 75.0,
                "phase_x_rad": math.pi / 2.0,
                "phase_y_rad": -math.pi / 2.0,
            },
            (75.0, 75.0, 1.0),
            (75.0, 75.0, 0.0),
        ),
    )
    for family, parameters, center, stationary_point in cases:
        handle = _surface_handle(family, parameters)
        transform = make_identity_surface_frame_transform(handle)
        policy = make_geometry_query_policy()
        pose = _tip_pose_at(center, bundle)
        geometry = build_composite_needle_geometry(
            tip_pose=pose,
            needle=bundle.needle,
            axial_sample_count=17,
            radial_sample_count=8,
        )
        sweep = make_swept_needle_geometry((geometry,))
        footprint = derive_complete_query_footprint(handle, sweep, transform, policy)
        result = collect_support_candidates(
            handle,
            tip_pose=pose,
            tip_radius_mm=bundle.needle.tip_radius_mm,
            cap_blend_coordinate_mm=bundle.needle.cap_blend_coordinate_mm,
            footprint=footprint,
            transform=transform,
            policy=policy,
        )

        current = next(
            item for item in result.candidates if CandidateOrigin.CURRENT_NEAREST in item.origins
        )
        assert current.point_global_mm == pytest.approx(stationary_point)
        assert result.gate_status is GeometryGateStatus.GEOMETRY_UNCERTAIN
        assert result.reason_code == "M01_RESOLUTION_REFINEMENT_REQUIRED"
        assert result.active_graph_candidate_ids == ()
        assert not current.admissible_support_candidate
        assert "QUERY_QUALITY_UNCERTAIN" in current.rejection_reasons
