from __future__ import annotations

from pathlib import Path

import pytest
from scripts.run_m01_performance import run_m01_performance_fixture


@pytest.mark.performance
def test_bounded_performance_fixture_reports_resources_and_no_full_rt10_parent(
    tmp_path: Path,
) -> None:
    report = run_m01_performance_fixture(
        report_path=tmp_path / "report.json",
        preview_enabled=False,
        tile_core_size=32,
        visualization_grid_size=32,
        cache_budget_mib=8.0,
    )
    assert report["overall_pass"] is True
    assert report["memory"]["reported_peak_rss_bytes"] > 0
    assert report["cache"]["cache_hits"] > 0
    assert report["cache"]["cache_misses"] > 0
    assert report["cache"]["regenerated_tiles"] > 0
    assert report["cache"]["memory_payload_bytes"] <= report["cache"]["memory_budget_bytes"]
    assert report["safety_assertions"]["cache_budget_le_512_mib"] is True
    assert report["safety_assertions"]["full_domain_rt10_dense_created"] is False
    assert report["timings_seconds"]["total"] > 0.0
    assert len(report["lod_and_streaming"]["requests"]) == 6
    assert report["module"] == "M01_SURFACE_IMPLEMENTATION"
    assert report["environment"]["hardware_processor"]
    assert report["environment"]["os"]
    assert report["environment"]["python"]
    assert report["environment"]["dependencies"]
    assert report["fixture"]["family"] == "self_affine_gaussian"
    assert report["footprints"]["path_length_mm"] == 100.0
    assert report["safety_assertions"]["cache_payload_within_budget"] is True
