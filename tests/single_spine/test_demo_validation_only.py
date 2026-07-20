from __future__ import annotations

from pathlib import Path

import pytest

from spine_sim.foundation.errors import QueryError
from spine_sim.foundation.integrity import VerifyMode
from spine_sim.foundation.reader import ResultReader
from spine_sim.single_spine.demo_validation_only import (
    catalog_overview,
    generate_validation_bundle,
)
from spine_sim.single_spine.result_extension import (
    ACCEPTED_STATE_HISTORY_DATASET,
    COMMITTED_EVENT_PAYLOADS_DATASET,
    REJECTED_DIAGNOSTICS_DATASET,
)


def test_canonical_analytic_plane_bundle_roundtrip_and_isolation(tmp_path: Path) -> None:
    bundle = generate_validation_bundle(tmp_path / "M03_VALIDATION_ONLY.spine-result")
    overview = catalog_overview(bundle)

    assert overview["manifest_integrity_passed"]
    assert overview["full_integrity_passed"]
    assert overview["registered_dataset_count"] == 26
    assert overview["m03_dataset_count"] == 12
    assert overview["accepted_rows"] == 1
    assert overview["committed_event_rows"] == 1
    assert overview["rejected_rows"] == 1
    assert overview["derived_summary_rows"] == 7
    assert overview["plot_recipe_rows"] == 8
    assert overview["material_model"] == "no_damage"
    assert overview["experimentally_validated"] == "NOT_ASSESSED"
    assert overview["certification"] == "NOT_CERTIFIABLE"

    reader = ResultReader.open(bundle, VerifyMode.FULL)
    accepted = (
        reader.query(
            ACCEPTED_STATE_HISTORY_DATASET,
            ("commit_receipt_id", "loaded_contact", "experimentally_validated"),
        )
        .read_all()
        .to_pylist()
    )
    assert accepted[0]["commit_receipt_id"]
    assert accepted[0]["loaded_contact"]
    assert accepted[0]["experimentally_validated"] == "NOT_ASSESSED"
    assert (
        reader.query(COMMITTED_EVENT_PAYLOADS_DATASET, ("event_kind",))
        .read_all()
        .to_pylist()[0]["event_kind"]
        == "TIP_CONTACT_ESTABLISH"
    )
    with pytest.raises(QueryError, match="explicit include_diagnostics opt-in"):
        reader.query(REJECTED_DIAGNOSTICS_DATASET, ("trial_id",))
