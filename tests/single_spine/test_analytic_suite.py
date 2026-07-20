from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.run_m03_analytic_suite import main

from spine_sim.single_spine.analytic_validation import (
    ANALYTIC_VALIDATION_SUITE_ID,
    AnalyticValidationStatus,
    AnalyticValidationSuiteResult,
    run_analytic_surface_validation_suite,
)


@pytest.fixture(scope="module")
def suite() -> AnalyticValidationSuiteResult:
    return run_analytic_surface_validation_suite()


def test_suite_covers_all_frozen_analytic_geometry_fixtures(
    suite: AnalyticValidationSuiteResult,
) -> None:
    assert suite.status is AnalyticValidationStatus.PASSED
    assert suite.failed_count == 0
    assert suite.passed_count == 6
    assert tuple(item.surface_family for item in suite.cases) == (
        "plane",
        "slope_plane",
        "spherical_cap",
        "spherical_bowl",
        "multi_gaussian_feature",
        "known_nearest_feature_switch",
    )
    assert all(item.checks and all(check.passed for check in item.checks) for item in suite.cases)


def test_each_case_retains_public_receipts_and_composite_geometry_evidence(
    suite: AnalyticValidationSuiteResult,
) -> None:
    for case in suite.cases:
        receipt_ids = {item.query_id for item in case.query_receipts}
        assert len(receipt_ids) == 2
        assert case.adapter_current_query_receipt_id in receipt_ids
        assert receipt_ids <= set(case.adapter_all_query_receipt_ids)
        assert case.geometry_evidence["composite_geometry_id"]
        assert case.geometry_evidence["sweep_id"]
        assert case.geometry_evidence["footprint_id"]
        assert case.geometry_evidence["part_order"] == (
            "tip_cap",
            "cone",
            "shaft",
            "mount",
        )
        current = [
            item
            for item in case.candidates
            if {"CURRENT_NEAREST", "CURRENT_CO_MINIMAL"}.intersection(item.origins)
        ]
        assert current
        assert all(item.finite_cap_legal for item in current)
        assert all(item.local_minimum_verified for item in current)
        assert all(item.empty_ball_verified for item in current)
        assert all(item.query_quality_passed for item in current)


def test_closed_form_observables_and_known_switch_are_preserved(
    suite: AnalyticValidationSuiteResult,
) -> None:
    by_id = {item.case_id: item for item in suite.cases}
    plane = by_id["analytic_plane"]
    assert plane.observables["public_sphere_gap_mm"] == pytest.approx(0.05, abs=1.0e-12)
    assert plane.observables["public_nearest_points_global_mm"] == ((75.0, 75.0, 0.0),)

    cap = by_id["analytic_convex_spherical_cap"]
    bowl = by_id["analytic_concave_spherical_bowl"]
    assert cap.observables["public_outward_normals_global"] == (((0.0, 0.0, 1.0),),)
    assert bowl.observables["public_outward_normals_global"] == (((0.0, 0.0, 1.0),),)

    switch = by_id["analytic_known_nearest_switch"]
    current = [item for item in switch.candidates if "CURRENT_CO_MINIMAL" in item.origins]
    assert {item.feature_id for item in current} == {
        "switch_face_negative",
        "switch_face_positive",
    }
    assert len(switch.active_graph_candidate_ids) == 2
    assert switch.adapter_gate_status == "PASSED_NONSMOOTH_GRAPH"


def test_multi_peak_uses_approximate_global_coverage_without_hiding_quality(
    suite: AnalyticValidationSuiteResult,
) -> None:
    case = next(item for item in suite.cases if item.case_id == "analytic_constructed_multi_peak")
    closest, sphere = case.query_receipts
    assert closest.capability == "APPROXIMATE"
    assert sphere.capability == "APPROXIMATE"
    assert closest.convergence_level == "CONVERGED"
    assert sphere.convergence_level == "CONVERGED"
    assert closest.metadata["global_candidate_coverage"] is True
    assert closest.error_bound_mm is not None
    assert closest.error_bound_mm <= 0.0005


def test_serialization_is_explicit_about_validation_only_scope_and_is_stable(
    suite: AnalyticValidationSuiteResult,
) -> None:
    payload = suite.to_dict()
    assert payload["suite_definition_id"] == ANALYTIC_VALIDATION_SUITE_ID
    assert payload["status"] == "PASSED"
    scope = payload["scope"]
    assert isinstance(scope, dict)
    assert scope["mechanics_solver"] == "NOT_INVOKED"
    assert scope["measured_target_surface"] == "NOT_USED"
    assert scope["target_brick_claim"] == "NOT_MADE"
    assert scope["experimental_validation"] == "NOT_ASSESSED"
    assert run_analytic_surface_validation_suite().suite_id == suite.suite_id
    json.dumps(payload, allow_nan=False)


def test_cli_writes_the_same_machine_readable_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    suite: AnalyticValidationSuiteResult,
) -> None:
    # Reuse the already executed suite here; the production CLI itself is run
    # separately by the validation command in this task.
    monkeypatch.setattr(
        "scripts.run_m03_analytic_suite.run_analytic_surface_validation_suite",
        lambda: suite,
    )
    output = tmp_path / "m03-analytic-suite.json"
    assert main(["--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["suite_id"] == suite.suite_id
    assert payload["case_count"] == 6
    assert payload["failed_count"] == 0
