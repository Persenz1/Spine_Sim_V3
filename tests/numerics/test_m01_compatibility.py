from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from spine_sim.numerics.m01_compatibility import (
    GEOMETRY_FIXTURES,
    PATH_LENGTH_MM,
    SURFACE_SCALE_REFERENCE_RT_MM,
    M01CompatibilityPanel,
    run_m01_compatibility_panel,
    write_m01_compatibility_report,
)


@pytest.fixture(scope="module")
def smoke_report() -> dict[str, Any]:
    return run_m01_compatibility_panel(M01CompatibilityPanel.SMOKE_4)


def test_smoke_panel_uses_four_independent_realizations_and_five_shared_paths(
    smoke_report: dict[str, Any],
) -> None:
    counts = smoke_report["counts"]
    assert isinstance(counts, dict)
    assert counts["scenario_count"] == 4
    assert counts["independent_surface_realization_count"] == 4
    assert counts["fixture_count"] == 5
    assert counts["full_path_count"] == 20
    assert counts["failure_count"] == 0
    assert smoke_report["overall_pass"] is True

    scenarios = smoke_report["scenarios"]
    paths = smoke_report["paths"]
    assert isinstance(scenarios, list) and isinstance(paths, list)
    assert len({item["scenario_id"] for item in scenarios}) == 4
    assert len({item["surface_realization_id"] for item in scenarios}) == 4
    by_scenario = Counter(item["scenario_id"] for item in paths)
    assert set(by_scenario.values()) == {len(GEOMETRY_FIXTURES)}
    for scenario in scenarios:
        assert (
            scenario["parameter_point"]["surface_scale_reference_Rt_mm"]
            == SURFACE_SCALE_REFERENCE_RT_MM
        )


def test_fixture_widths_come_from_complete_owner_geometry_and_m01_footprints(
    smoke_report: dict[str, Any],
) -> None:
    paths = smoke_report["paths"]
    assert isinstance(paths, list)
    first_scenario = paths[0]["scenario_id"]
    rows = {item["fixture_id"]: item for item in paths if item["scenario_id"] == first_scenario}
    assert set(rows) == {item.fixture_id for item in GEOMETRY_FIXTURES}
    for row in rows.values():
        geometry = row["geometry"]
        assert geometry["path_length_mm"] == pytest.approx(PATH_LENGTH_MM)
        assert geometry["full_100_mm_path_pass"] is True
        assert geometry["endpoint_guard_pass"] is True
        assert geometry["width_derived_by_m01"] is True
        assert geometry["geometry_component_counts_per_spine"] == {
            "body": 2,
            "installation": 2,
            "tip": 2,
        }
        bounds = geometry["footprint_bounds_mm"]
        assert 0.0 <= bounds[0] < bounds[1] <= 150.0
        assert 0.0 <= bounds[2] < bounds[3] <= 150.0

    assert (
        rows["ARRAY_2X6_S6"]["geometry"]["footprint_y_extent_mm"]
        > rows["ARRAY_2X2_S4"]["geometry"]["footprint_y_extent_mm"]
    )
    assert (
        rows["ARRAY_6X2_S6"]["geometry"]["footprint_x_extent_mm"]
        > rows["ARRAY_2X6_S6"]["geometry"]["footprint_x_extent_mm"]
    )
    assert (
        rows["ARRAY_6X6_S6"]["geometry"]["footprint_y_extent_mm"]
        == rows["ARRAY_2X6_S6"]["geometry"]["footprint_y_extent_mm"]
    )


def test_each_path_is_lazy_and_cache_or_request_order_never_changes_semantics(
    smoke_report: dict[str, Any],
) -> None:
    paths = smoke_report["paths"]
    assert isinstance(paths, list)
    for path in paths:
        probes = path["canonical_probes"]
        assert [item["lod"] for item in probes] == ["Rt/5", "Rt/8", "Rt/8", "Rt/10"]
        assert [item["purpose"] for item in probes] == [
            "ahead",
            "event_probe",
            "acceptance_witness_baseline",
            "acceptance_witness_refined",
        ]
        assert all(item["narrow_wide_overlap_equal"] for item in probes)
        assert all(item["cold_warm_equal"] for item in probes)
        assert all(item["prewide_dynamic_equal"] for item in probes)
        assert all(item["query_order_equal"] for item in probes)
        assert path["probe_radius_identity_invariant"] is True
        assert path["refinement"]["passed"] is True
        assert path["cache_audit"]["payload_within_budget"] is True
        assert path["cache_audit"]["full_domain_rt10_dense_created"] is False
        assert path["overall_pass"] is True

    cache = smoke_report["cache"]
    assert cache["cache_receipts_are_diagnostic"] is True
    assert cache["receipt_ids_excluded_from_semantic_comparisons"] is True
    assert cache["normal_path_builds_full_domain_rt10_dense"] is False


def test_raw_m01_domain_reason_is_preserved_without_wrap_crop_or_shortening(
    smoke_report: dict[str, Any],
) -> None:
    checks = smoke_report["domain_error_checks"]
    assert isinstance(checks, list) and len(checks) == 4
    assert {item["reason_code"] for item in checks} == {"M01_ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN"}
    assert all(item["raw_reason_preserved"] for item in checks)
    assert all(item["no_wrap_clamp_crop_or_shortening"] for item in checks)
    assert all(item["passed"] for item in checks)


def test_replay_hash_ignores_receipt_diagnostics_and_report_round_trips(
    smoke_report: dict[str, Any],
    tmp_path: Path,
) -> None:
    replay = run_m01_compatibility_panel("smoke")
    assert replay["semantic_result_hash"] == smoke_report["semantic_result_hash"]
    assert [item["semantic_result_hash"] for item in replay["paths"]] == [
        item["semantic_result_hash"] for item in smoke_report["paths"]
    ]

    output = write_m01_compatibility_report(tmp_path / "m02-m01-smoke.json", smoke_report)
    decoded = json.loads(output.read_text(encoding="utf-8"))
    assert decoded["semantic_result_hash"] == smoke_report["semantic_result_hash"]
    assert decoded["overall_pass"] is True


@pytest.mark.performance
@pytest.mark.parametrize(
    ("panel", "scenario_count", "path_count"),
    (
        (M01CompatibilityPanel.STANDARD_64, 64, 320),
        (M01CompatibilityPanel.STRESS_256, 256, 1280),
    ),
)
def test_full_standard_and_stress_panels_are_bounded_and_complete(
    panel: M01CompatibilityPanel,
    scenario_count: int,
    path_count: int,
) -> None:
    report = run_m01_compatibility_panel(panel)
    assert report["overall_pass"] is True
    assert report["counts"]["scenario_count"] == scenario_count
    assert report["counts"]["independent_surface_realization_count"] == scenario_count
    assert report["counts"]["full_path_count"] == path_count
    assert report["counts"]["failure_count"] == 0
    assert report["cache"]["normal_path_builds_full_domain_rt10_dense"] is False
    assert report["cache"]["max_resident_payload_bytes"] < 128 * 1024

    balance = report["panel_design"]["parameter_balance"]
    assert set(balance["H"]) == {"0.5", "0.7", "0.9"}
    assert set(balance["Sq_over_reference_Rt"]) == {"0.25", "1.0", "4.0"}
    assert set(balance["lc_over_reference_Rt"]) == {"5.0", "20.0", "80.0"}
    assert set(balance["anisotropy_ratio"]) == {"1.0", "2.0"}

    diagnostic_counts = Counter(item["diagnostic_level"] for item in report["paths"])
    if panel is M01CompatibilityPanel.STANDARD_64:
        assert diagnostic_counts == {"STANDARD": 320}
    else:
        assert diagnostic_counts == {"STANDARD": 160, "COMPACT": 1120}
