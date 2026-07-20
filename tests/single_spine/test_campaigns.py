from __future__ import annotations

import json

import pytest

from spine_sim.single_spine.campaigns import (
    ALPHA_GRID_DEG,
    DIAMETER_GRID_MM,
    FRICTION_GRID,
    POISSON_RATIO_GRID,
    RT_GRID_MM,
    SPRING_STIFFNESS_GRID_N_PER_MM,
    YOUNGS_MODULUS_GRID_MPA,
    CampaignRunKind,
    CampaignStreamingCursor,
    SurfaceCampaignRole,
    TrendPanel,
    TrendParameters,
    frozen_campaign_streaming_plan,
    frozen_synthetic_surface_specs,
    frozen_trend_campaign,
)
from spine_sim.single_spine.contracts import SURFACE_SCALE_REFERENCE_RT_MM, MountMode


def test_frozen_trend_plan_has_exact_distinct_count_and_panel_grids() -> None:
    plan = frozen_trend_campaign()

    assert len(plan.cases) == 36
    assert len({case.case_id for case in plan.cases}) == 36
    assert len({case.parameters for case in plan.cases}) == 36
    assert len({case.parameter_bundle.parameter_bundle_id for case in plan.cases}) == 36
    assert [case.ordinal for case in plan.cases] == list(range(36))

    expected_counts = {
        TrendPanel.GEOMETRY_MAIN_EFFECT: 16,
        TrendPanel.FRICTION_CONDITIONAL_OFAT: 5,
        TrendPanel.MOUNT_CONDITIONAL_OFAT: 6,
        TrendPanel.BENDING_CONDITIONAL_OFAT: 2,
        TrendPanel.YOUNGS_MODULUS_CONDITIONAL_OFAT: 3,
        TrendPanel.POISSON_RATIO_CONDITIONAL_OFAT: 3,
        TrendPanel.RT_FRICTION_INTERACTION: 4,
        TrendPanel.DIAMETER_SPRING_INTERACTION: 4,
        TrendPanel.ALPHA_MOUNT_INTERACTION: 4,
    }
    assert {panel: len(plan.cases_for_panel(panel)) for panel in TrendPanel} == expected_counts

    geometry = plan.cases_for_panel(TrendPanel.GEOMETRY_MAIN_EFFECT)
    assert {
        (case.parameters.tip_radius_mm, case.parameters.diameter_mm, case.parameters.alpha_deg)
        for case in geometry
    } == {
        (tip_radius_mm, diameter_mm, alpha_deg)
        for tip_radius_mm in RT_GRID_MM
        for diameter_mm in DIAMETER_GRID_MM
        for alpha_deg in ALPHA_GRID_DEG
    }
    assert all(case.parameters.friction_coefficient == 0.40 for case in geometry)
    assert all(case.parameters.spring_stiffness_n_per_mm == 0.5 for case in geometry)


def test_conditional_ofat_is_exact_and_excludes_meaningless_combinations() -> None:
    plan = frozen_trend_campaign()

    friction = plan.cases_for_panel(TrendPanel.FRICTION_CONDITIONAL_OFAT)
    assert {case.parameters.friction_coefficient for case in friction} == set(FRICTION_GRID)
    assert all(
        (
            case.parameters.tip_radius_mm,
            case.parameters.diameter_mm,
            case.parameters.alpha_deg,
        )
        == (0.05, 0.80, 60.0)
        for case in friction
    )

    mount = plan.cases_for_panel(TrendPanel.MOUNT_CONDITIONAL_OFAT)
    assert {
        (case.parameters.mount_mode, case.parameters.spring_stiffness_n_per_mm) for case in mount
    } == {
        (MountMode.RIGID_MOUNT, None),
        *{
            (MountMode.INDEPENDENT_AXIAL_SPRINGS, stiffness)
            for stiffness in SPRING_STIFFNESS_GRID_N_PER_MM
        },
    }

    bending = plan.cases_for_panel(TrendPanel.BENDING_CONDITIONAL_OFAT)
    assert {case.parameters.bending_enabled for case in bending} == {True, False}
    bending_off = next(case for case in bending if not case.parameters.bending_enabled)
    assert bending_off.parameters.youngs_modulus_mpa is None
    assert bending_off.parameters.poisson_ratio is None
    assert bending_off.parameter_bundle.beam.youngs_modulus_mpa is None
    assert bending_off.parameter_bundle.beam.poisson_ratio is None

    youngs_modulus = plan.cases_for_panel(TrendPanel.YOUNGS_MODULUS_CONDITIONAL_OFAT)
    poisson = plan.cases_for_panel(TrendPanel.POISSON_RATIO_CONDITIONAL_OFAT)
    assert {case.parameters.youngs_modulus_mpa for case in youngs_modulus} == set(
        YOUNGS_MODULUS_GRID_MPA
    )
    assert {case.parameters.poisson_ratio for case in poisson} == set(POISSON_RATIO_GRID)
    assert all(case.parameters.bending_enabled for case in youngs_modulus + poisson)
    assert all(
        case.parameters.mount_mode is MountMode.INDEPENDENT_AXIAL_SPRINGS
        for case in youngs_modulus + poisson
    )
    assert len(plan.cases) < (
        len(RT_GRID_MM)
        * len(DIAMETER_GRID_MM)
        * len(ALPHA_GRID_DEG)
        * len(YOUNGS_MODULUS_GRID_MPA)
        * len(POISSON_RATIO_GRID)
        * len(FRICTION_GRID)
        * 6
        * 2
    )


def test_twelve_interactions_keep_exactly_six_shared_case_references() -> None:
    plan = frozen_trend_campaign()

    assert len(plan.interaction_records) == 12
    assert len({record.record_id for record in plan.interaction_records}) == 12
    assert len({record.case_id for record in plan.interaction_records}) == 12
    assert len(plan.shared_case_references) == 6
    assert sum(record.reuses_existing_case for record in plan.interaction_records) == 6
    assert {reference.interaction_record_id for reference in plan.shared_case_references} == {
        record.record_id for record in plan.interaction_records if record.reuses_existing_case
    }
    assert {
        panel: sum(reference.existing_panel is panel for reference in plan.shared_case_references)
        for panel in (
            TrendPanel.FRICTION_CONDITIONAL_OFAT,
            TrendPanel.MOUNT_CONDITIONAL_OFAT,
            TrendPanel.GEOMETRY_MAIN_EFFECT,
        )
    } == {
        TrendPanel.FRICTION_CONDITIONAL_OFAT: 2,
        TrendPanel.MOUNT_CONDITIONAL_OFAT: 2,
        TrendPanel.GEOMETRY_MAIN_EFFECT: 2,
    }

    shared = [record for record in plan.interaction_records if record.reuses_existing_case]
    assert {
        (record.first_value, record.second_value)
        for record in shared
        if record.panel is TrendPanel.RT_FRICTION_INTERACTION
    } == {(0.05, 0.15), (0.05, 0.80)}
    assert {
        (record.first_value, record.second_value)
        for record in shared
        if record.panel is TrendPanel.DIAMETER_SPRING_INTERACTION
    } == {(0.80, 0.1), (0.80, 2.0)}
    assert {
        (record.first_value, record.second_value)
        for record in shared
        if record.panel is TrendPanel.ALPHA_MOUNT_INTERACTION
    } == {
        (50.0, MountMode.INDEPENDENT_AXIAL_SPRINGS.value),
        (80.0, MountMode.INDEPENDENT_AXIAL_SPRINGS.value),
    }
    new_records = [record for record in plan.interaction_records if not record.reuses_existing_case]
    assert {
        (record.first_value, record.second_value)
        for record in new_records
        if record.panel is TrendPanel.RT_FRICTION_INTERACTION
    } == {(0.10, 0.15), (0.10, 0.80)}
    assert {
        (record.first_value, record.second_value)
        for record in new_records
        if record.panel is TrendPanel.DIAMETER_SPRING_INTERACTION
    } == {(0.60, 0.1), (0.60, 2.0)}
    assert {
        (record.first_value, record.second_value)
        for record in new_records
        if record.panel is TrendPanel.ALPHA_MOUNT_INTERACTION
    } == {
        (50.0, MountMode.RIGID_MOUNT.value),
        (80.0, MountMode.RIGID_MOUNT.value),
    }
    assert (
        sum(len(case.panels) == 1 and "INTERACTION" in case.panels[0].value for case in plan.cases)
        == 6
    )


def test_trend_parameter_normalization_rejects_inapplicable_values() -> None:
    with pytest.raises(ValueError, match="bending-off"):
        TrendParameters(bending_enabled=False)
    with pytest.raises(ValueError, match="rigid-mount"):
        TrendParameters(mount_mode=MountMode.RIGID_MOUNT)
    assert frozen_trend_campaign() == frozen_trend_campaign()


def test_primary_gentle_and_sharp_specs_preserve_frozen_m01_identity_inputs() -> None:
    surfaces = frozen_synthetic_surface_specs()

    assert [surface.role for surface in surfaces] == list(SurfaceCampaignRole)
    assert [surface.root_seed for surface in surfaces] == [30301, 30302, 30303]
    assert [surface.intended_case_count for surface in surfaces] == [36, 1, 1]
    assert len({surface.surface_spec_id for surface in surfaces}) == 3
    assert len({surface.latent_noise_id for surface in surfaces}) == 3
    assert all(surface.surface_seed_index == 0 for surface in surfaces)
    assert all(not surface.statistical_sample for surface in surfaces)
    assert [surface.surface_spec_id for surface in surfaces] == [
        surface.surface_spec_id for surface in frozen_synthetic_surface_specs()
    ]
    assert [surface.surface_realization_id for surface in surfaces] == [
        surface.surface_realization_id for surface in frozen_synthetic_surface_specs()
    ]

    expected = {
        SurfaceCampaignRole.PRIMARY_MEDIUM: (0.7, 1.0, 20.0, 0.05, 1.0),
        SurfaceCampaignRole.GENTLE_SMOKE: (0.9, 0.25, 80.0, 0.0125, 4.0),
        SurfaceCampaignRole.SHARP_SMOKE: (0.5, 4.0, 5.0, 0.20, 0.25),
    }
    for surface in surfaces:
        parameters = surface.surface_spec.parameter_map()
        h, sq_ratio, lc_ratio, sq_mm, lc_mm = expected[surface.role]
        assert parameters["H"] == h
        assert parameters["Sq_over_reference_Rt"] == sq_ratio
        assert parameters["lc_over_reference_Rt"] == lc_ratio
        assert parameters["Sq_mm"] == sq_mm
        assert parameters["lc_mm"] == lc_mm
        assert parameters["surface_scale_reference_Rt_mm"] == SURFACE_SCALE_REFERENCE_RT_MM
        assert parameters["anisotropy_ratio"] == 1.0
        expected_direction = 0.0 if surface.role is SurfaceCampaignRole.PRIMARY_MEDIUM else None
        assert parameters["anisotropy_direction_rad"] == expected_direction
        assert surface.surface_spec.logical_domain.width_mm == 150.0
        assert surface.surface_spec.logical_domain.height_mm == 150.0
        assert surface.surface_realization.surface_spec_id == surface.surface_spec_id
        assert surface.surface_realization.seed_id == surface.seed_id
        assert surface.surface_realization.latent_noise_id == surface.latent_noise_id


def test_streaming_plan_pairs_primary_cases_and_bounds_full_history() -> None:
    plan = frozen_campaign_streaming_plan()
    cases = tuple(plan.iter_cases())

    assert plan.case_count == 38
    assert plan.primary_case_count == 36
    assert plan.smoke_case_count == 2
    assert len(cases) == 38
    assert len({case.execution_case_id for case in cases}) == 38
    assert [case.ordinal for case in cases] == list(range(38))
    assert all(case.run_kind is CampaignRunKind.PRIMARY_TREND for case in cases[:36])
    assert [case.surface_role for case in cases[36:]] == [
        SurfaceCampaignRole.GENTLE_SMOKE,
        SurfaceCampaignRole.SHARP_SMOKE,
    ]

    primary_identity = {
        (
            case.surface_spec_id,
            case.seed_id,
            case.latent_noise_id,
            case.surface_realization_id,
            case.path_policy_id,
            case.query_policy_id,
        )
        for case in cases[:36]
    }
    assert len(primary_identity) == 1
    assert {case.parameter_bundle.needle.tip_radius_mm for case in cases[:36]} == {0.05, 0.10}
    assert len({case.surface_spec_id for case in cases[:36]}) == 1
    baseline_bundle_id = plan.trend_campaign.baseline_case.parameter_bundle.parameter_bundle_id
    assert {case.parameter_bundle.parameter_bundle_id for case in cases[36:]} == {
        baseline_bundle_id
    }

    assert plan.maximum_full_histories_in_memory == 1
    assert not plan.retain_completed_full_history
    assert plan.checkpoint_interval_cases == 1
    assert plan.pause_resume_supported
    assert plan.semantic_replay_required
    assert plan.path_query_policy.lazy_active_footprint_only
    assert not plan.path_query_policy.full_domain_dense_grid_allowed
    assert plan.path_query_policy.travel_mm == 100.0
    assert set(plan.required_per_case_metrics) == {
        "accepted_count",
        "trial_count",
        "committed_event_count",
        "query_count",
        "wall_time_seconds",
        "peak_rss_bytes",
        "cache_payload_bytes",
        "cache_hit_count",
        "cache_miss_count",
        "cache_regeneration_count",
        "artifact_size_bytes",
        "terminal_status",
        "failure_axis",
        "reason_code",
        "replay_manifest_id",
        "final_receipt_id",
    }


def test_streaming_cursor_round_trip_pause_resume_and_bounds() -> None:
    plan = frozen_campaign_streaming_plan()
    initial = plan.initial_cursor()
    first, paused = plan.iter_from_cursor(initial, maximum_cases=7)
    encoded = json.dumps(paused.to_dict(), sort_keys=True)
    restored = CampaignStreamingCursor.from_dict(json.loads(encoded))
    remainder, completed = plan.iter_from_cursor(restored)

    assert tuple(first) + tuple(remainder) == tuple(plan.iter_cases())
    assert completed.next_ordinal == plan.case_count
    assert plan.iter_from_cursor(completed, maximum_cases=1)[0] == ()
    with pytest.raises(ValueError, match="maximum_cases"):
        plan.iter_from_cursor(initial, maximum_cases=-1)
    with pytest.raises(ValueError, match="cursor"):
        CampaignStreamingCursor.from_dict({"plan_id": plan.plan_id, "next_ordinal": True})
    with pytest.raises(IndexError):
        plan.case_at(plan.case_count)
    with pytest.raises(ValueError, match="slice"):
        tuple(plan.iter_cases(4, 3))
