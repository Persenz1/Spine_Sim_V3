from __future__ import annotations

from pathlib import Path

import pytest
from scripts.run_m00_performance import _rows, run_performance_fixture

from spine_sim.foundation.canonical import stable_content_id


def test_performance_point_identity_matches_canonical_profile() -> None:
    row = _rows("run", "case:IDENTITY", 1)[0]
    assert row.point_id == stable_content_id("point", {"case": "case:IDENTITY", "row": 0})


@pytest.mark.performance
def test_frozen_standard_io_performance_fixture(tmp_path: Path) -> None:
    report = run_performance_fixture(
        tmp_path / "M00_PERFORMANCE.spine-result",
        case_count=1000,
        rows_per_case=1000,
    )
    assert report["overall_pass"], report
