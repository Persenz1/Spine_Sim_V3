from __future__ import annotations

import ast
import json
import subprocess
import sys
from importlib import import_module as standard_import_module
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from spine_sim.foundation.canonical import semantic_hash, source_file_hash
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import CapabilityStatus, CertificationStatus, SourceIdentity
from spine_sim.foundation.reader import ResultReader
from spine_sim.foundation.registry import BUNDLE_SCHEMA_VERSION, SchemaRegistry
from spine_sim.foundation.storage import write_json_atomic, write_parquet_records
from spine_sim.single_spine import validation_figures as validation_module
from spine_sim.single_spine.plot_recipes import M03_FROZEN_RECIPE_IDS, RecipeDataRole
from spine_sim.single_spine.result_extension import (
    ACCEPTED_STATE_HISTORY_DATASET,
    COMMITTED_EVENT_PAYLOADS_DATASET,
    CONTACT_CYCLE_RECORDS_DATASET,
    CONTACT_SUPPORT_HISTORY_DATASET,
    REJECTED_DIAGNOSTICS_DATASET,
    RELEASE_OPERATION_HISTORY_DATASET,
    RUN_REQUESTS_DATASET,
    SUPPORT_CANDIDATE_HISTORY_DATASET,
    WORK_LEDGER_DATASET,
    m03_result_extension,
)
from spine_sim.single_spine.validation_figures import (
    RAW_PEAK_ALGORITHM_ID,
    VALIDATION_FIGURE_MANIFEST,
    FigureRenderStatus,
    render_validation_figure_pack,
)

RUN_ID = "run:M03_VALIDATION_FIGURES"
SURFACE_ID = "surface:M03_PAIRED"


def _zero_shape(shape: tuple[int | None, ...]) -> Any:
    dimensions: list[int] = []
    for item in shape:
        assert item is not None
        dimensions.append(item)
    return np.zeros(tuple(dimensions), dtype=np.float64).tolist()


def _dataset_rows_base(registry: SchemaRegistry, dataset_id: str) -> dict[str, Any]:
    descriptor = registry.datasets[dataset_id]
    row: dict[str, Any] = {}
    for field in descriptor.fields:
        name = field.field_id.rsplit(".", 1)[-1]
        if field.shape:
            row[name] = _zero_shape(field.shape)
        elif field.dtype == "float64":
            row[name] = 0.0
        elif field.dtype == "int64":
            row[name] = 0
        elif field.dtype == "bool":
            row[name] = False
        else:
            row[name] = f"{name}:fixture"
    row.update(
        {
            "run_id": RUN_ID,
            "schema_version": "1.0.0",
            "source_identity": SourceIdentity.DEV_POLICY.value,
            "certification_status": CertificationStatus.NOT_CERTIFIABLE.value,
        }
    )
    return row


def _parameter_payload(case_index: int) -> dict[str, Any]:
    return {
        "parameter_bundle": {
            "needle": {
                "tip_radius_mm": 0.05 + 0.05 * case_index,
                "diameter_mm": 0.8 + 0.4 * case_index,
                "alpha_rad": 0.8 + 0.2 * case_index,
            },
            "contact": {"friction_coefficient": 0.2 + 0.4 * case_index},
            "mount": {"spring_stiffness_n_per_mm": 0.5 + 0.5 * case_index},
        }
    }


def _accepted_rows(registry: SchemaRegistry, case_id: str, case_index: int) -> list[dict[str, Any]]:
    force_profiles = (
        (0.0, 1.0, 3.0, 1.0, 4.0, 0.5, 0.0),
        (0.0, 1.4, 3.8, 1.3, 4.7, 0.7, 0.0),
    )
    rows: list[dict[str, Any]] = []
    for index, force in enumerate(force_profiles[case_index]):
        row = _dataset_rows_base(registry, ACCEPTED_STATE_HISTORY_DATASET)
        point_id = f"point:{case_index}:{index}"
        row.update(
            {
                "case_id": case_id,
                "state_record_id": f"state-record:{case_index}:{index}",
                "point_id": point_id,
                "parent_point_id": None if index == 0 else f"point:{case_index}:{index - 1}",
                "accepted_state_id": f"state:{case_index}:{index}",
                "parent_accepted_state_id": f"state:{case_index}:{index - 1}",
                "commit_receipt_id": f"receipt:{case_index}:{index}",
                "parameter_bundle_id": f"bundle:{case_index}",
                "surface_realization_id": SURFACE_ID,
                "accepted_point_index": index,
                "x_total_mm": float(index),
                "drag_elapsed_time_s": 0.5 * index,
                "operation_phase": "DRAG" if index != 2 else "RELEASE_RETURN",
                "operation_path_coordinate_mm": float(index),
                "cycle_id": "cycle:0" if index < 3 else "cycle:1",
                "event_sequence": index,
                "root_position_global_mm": [72.0 + index, 75.0, 3.5],
                "tip_center_global_mm": [75.0 + index, 75.0, 0.05],
                "a0_global": [0.5, 0.0, -0.8660254037844386],
                "a_t_global": [0.5, 0.0, -0.8660254037844386],
                "task_direction_global": [1.0, 0.0, 0.0],
                "active_candidate_ids": json.dumps([f"candidate:{case_index}:{index}"]),
                "active_support_ids": json.dumps([f"support:{case_index}:{index}"]),
                "query_receipt_id": f"query:{case_index}:{index}",
                "query_lod_purpose": "event_support",
                "query_error_bound_mm": 1.0e-5 * (index + 1),
                "query_quality": "TRUSTED_FOR_DECLARED_SCALE",
                "query_domain_status": "IN_DOMAIN",
                "query_nonsmooth": index == 4,
                "query_nonunique": False,
                "full_body_minimum_clearance_mm": 0.2,
                "cone_clearance_mm": 0.12,
                "shaft_clearance_mm": 0.18,
                "mount_clearance_mm": 0.25,
                "wrench_a_on_b_global_at_o_n_n_mm": [
                    force,
                    0.15 * force,
                    0.3 * force,
                    0.02 * force,
                    0.03 * force,
                    0.04 * force,
                ],
                "opposite_wrench_b_on_a_global_at_o_n_n_mm": [
                    -force,
                    -0.15 * force,
                    -0.3 * force,
                    -0.02 * force,
                    -0.03 * force,
                    -0.04 * force,
                ],
                "grip_resistance_rx_n": force,
                "task_resistance_n": force,
                "beam_tip_translation_global_mm": [
                    0.01 * index,
                    0.005 * index,
                    -0.02 * index,
                ],
                "beam_tip_rotation_global_rad": [0.001 * index, 0.0, 0.002 * index],
                "beam_tip_translation_needle_mm": [0.01 * index, 0.0, -0.02 * index],
                "beam_tip_rotation_needle_rad": [0.001 * index, 0.0, 0.002 * index],
                "beam_root_force_global_n": [force, 0.1 * force, 0.2 * force],
                "beam_root_moment_global_n_mm": [0.01 * force, 0.02 * force, 0.03 * force],
                "section_resultants_needle_n_n_mm": [
                    force,
                    0.0,
                    0.0,
                    0.01 * force,
                    0.02 * force,
                    0.03 * force,
                ],
                "beam_energy_n_mm": 0.05 * index,
                "beam_model_state": "EB_ACTIVE",
                "spring_state": "INTERIOR" if index < 5 else "ZERO_LOAD",
                "spring_compression_mm": max(0.0, 0.04 * (5 - index)),
                "spring_remaining_travel_mm": 4.0 - 0.04 * (5 - index),
                "spring_force_n": max(0.0, 0.02 * (5 - index)),
                "spring_hard_stop_reaction_n": 0.0,
                "spring_energy_n_mm": 0.01 * index,
                "primary_mechanical_state": "ATTACHED_STICK" if 1 <= index <= 4 else "OPEN",
                "contact_motion_states": json.dumps(["STICK"] if 1 <= index <= 4 else []),
                "quality_solve_state": "SOLVED",
                "geometric_candidate": index >= 1,
                "loaded_contact": 2 <= index <= 4,
                "frictionally_stable": 2 <= index <= 4,
                "load_bearing": 3 <= index <= 4,
                "five_stage_reason_codes": json.dumps(["M03_OK"]),
                "five_stage_evidence_refs": json.dumps([point_id]),
                "residual_block_payloads": json.dumps(
                    [
                        {
                            "block_id": "equilibrium",
                            "raw_norm": 1.0e-6 * (index + 1),
                            "normalized_norm": 1.0e-5 * (index + 1),
                        }
                    ]
                ),
                "complementarity_residual": 1.0e-7 * (index + 1),
                "contact_soc_residual": 2.0e-7 * (index + 1),
                "graph_residual": 3.0e-7 * (index + 1),
                "jacobian_quality": "REGULAR",
                "work_ledger_id": f"work:{case_index}:{max(index - 1, 0)}",
                "damage_status": "UNAVAILABLE_NO_DAMAGE",
                "strength_status": "UNAVAILABLE",
                "failure_prediction_allowed": False,
                "experimentally_validated": "NOT_ASSESSED",
                "not_certifiable": True,
            }
        )
        rows.append(row)
    return rows


def _event_rows(registry: SchemaRegistry, case_id: str, case_index: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event_index, (kind, coordinate) in enumerate(
        (("RELEASE", 2.0), ("RECONTACT", 3.0), ("REENGAGEMENT", 4.0))
    ):
        row = _dataset_rows_base(registry, COMMITTED_EVENT_PAYLOADS_DATASET)
        force = float(event_index + 1)
        row.update(
            {
                "case_id": case_id,
                "event_payload_id": f"event-payload:{case_index}:{event_index}",
                "event_id": f"event:{case_index}:{event_index}",
                "commit_receipt_id": f"event-receipt:{case_index}:{event_index}",
                "event_kind": kind,
                "raw_signed_guard": 0.0,
                "raw_guard_unit": "N",
                "admissible_side": "POST",
                "crossing_direction": "POSITIVE",
                "bracket_ref": f"bracket:{case_index}:{event_index}",
                "probe_refs": json.dumps([f"probe:{case_index}:{event_index}"]),
                "earliestness_ref": f"earliest:{case_index}:{event_index}",
                "path_coordinate_mm": coordinate,
                "cycle_id": "cycle:0" if event_index == 0 else "cycle:1",
                "pre_wrench_global_at_o_n_n_mm": [force, 0.0, 0.0, 0.0, 0.0, 0.0],
                "event_wrench_global_at_o_n_n_mm": [force + 0.1, 0.0, 0.0, 0.0, 0.0, 0.0],
                "post_wrench_global_at_o_n_n_mm": [force + 0.2, 0.0, 0.0, 0.0, 0.0, 0.0],
                "pre_beam_energy_n_mm": 0.2,
                "post_beam_energy_n_mm": 0.1,
                "pre_spring_energy_n_mm": 0.1,
                "post_spring_energy_n_mm": 0.05,
                "remaining_stored_energy_n_mm": 0.15,
                "released_recoverable_energy_n_mm": 0.05,
                "one_sided_consistency": True,
            }
        )
        rows.append(row)
    return rows


def _other_rows(
    registry: SchemaRegistry, case_id: str, case_index: int
) -> dict[str, list[dict[str, Any]]]:
    request = _dataset_rows_base(registry, RUN_REQUESTS_DATASET)
    request.update(
        {
            "case_id": case_id,
            "request_id": f"request:{case_index}",
            "parameter_bundle_id": f"bundle:{case_index}",
            "surface_realization_id": SURFACE_ID,
            "resolved_request_payload": json.dumps(_parameter_payload(case_index)),
            "commit_receipt_id": f"request-receipt:{case_index}",
        }
    )

    candidate = _dataset_rows_base(registry, SUPPORT_CANDIDATE_HISTORY_DATASET)
    candidate.update(
        {
            "case_id": case_id,
            "candidate_record_id": f"candidate-record:{case_index}",
            "point_id": f"point:{case_index}:6",
            "commit_receipt_id": f"candidate-receipt:{case_index}",
            "candidate_id": f"candidate:{case_index}:6",
            "support_id": f"support:{case_index}:6",
            "candidate_point_global_mm": [81.0, 75.0, 0.0],
            "normal_global": [0.0, 0.0, 1.0],
            "tangent_1_global": [1.0, 0.0, 0.0],
            "tangent_2_global": [0.0, 1.0, 0.0],
            "cap_margin_mm": 0.02,
            "finite_cap_legal": True,
            "coverage_certified": True,
            "nonsmooth": False,
            "nonunique": False,
            "rejection_reason": None,
        }
    )
    contact = _dataset_rows_base(registry, CONTACT_SUPPORT_HISTORY_DATASET)
    contact.update(
        {
            "case_id": case_id,
            "contact_record_id": f"contact-record:{case_index}",
            "point_id": f"point:{case_index}:6",
            "commit_receipt_id": f"contact-receipt:{case_index}",
            "support_id": f"support:{case_index}:6",
            "candidate_id": f"candidate:{case_index}:6",
            "active": True,
            "point_global_mm": [81.0, 75.0, 0.0],
            "normal_global": [0.0, 0.0, 1.0],
            "tangent_1_global": [1.0, 0.0, 0.0],
            "tangent_2_global": [0.0, 1.0, 0.0],
            "motion_state": "STICK",
        }
    )
    releases: list[dict[str, Any]] = []
    for index, coordinate in enumerate((2.0, 3.0)):
        release = _dataset_rows_base(registry, RELEASE_OPERATION_HISTORY_DATASET)
        release.update(
            {
                "case_id": case_id,
                "operation_record_id": f"release-operation:{case_index}:{index}",
                "point_id": f"point:{case_index}:{index + 2}",
                "commit_receipt_id": f"release-receipt:{case_index}:{index}",
                "event_id": f"event:{case_index}:{index}",
                "cycle_id": "cycle:1",
                "operation_phase": "RELEASE_RETURN",
                "segment_id": f"return-segment:{case_index}",
                "path_coordinate_mm": coordinate,
                "x_total_mm": coordinate,
                "signed_guard_payloads": json.dumps([{"guard": coordinate - 2.5}]),
                "quality_gate_passed": True,
                "termination_kind": "RECONTACT" if index else "CONTINUE",
                "lifecycle_kind": "SWEPT_RETURN",
                "remaining_stored_energy_n_mm": 0.1 - 0.04 * index,
            }
        )
        releases.append(release)
    work_rows: list[dict[str, Any]] = []
    for index in range(6):
        work = _dataset_rows_base(registry, WORK_LEDGER_DATASET)
        work.update(
            {
                "case_id": case_id,
                "work_ledger_id": f"work:{case_index}:{index}",
                "start_point_id": f"point:{case_index}:{index}",
                "end_point_id": f"point:{case_index}:{index + 1}",
                "commit_receipt_id": f"work-receipt:{case_index}:{index}",
                "accepted_interval_index": index,
                "base_or_actuator_input_work_n_mm": 0.2 * (index + 1),
                "delta_beam_energy_n_mm": 0.02,
                "delta_spring_energy_n_mm": 0.01,
                "rigid_contact_energy_n_mm": 0.0,
                "friction_dissipation_n_mm": 0.1 * index,
                "material_dissipation_n_mm": 0.0,
                "returned_recoverable_energy_n_mm": 0.03 * index,
                "remaining_stored_energy_n_mm": 0.05,
                "closure_error_n_mm": 1.0e-8 * (index + 1),
                "normalized_closure_error": 1.0e-7 * (index + 1),
                "cumulative_input_work_n_mm": 0.2 * (index + 1),
                "cumulative_friction_dissipation_n_mm": 0.1 * index,
                "cumulative_material_dissipation_n_mm": 0.0,
                "cumulative_returned_energy_n_mm": 0.03 * index,
            }
        )
        work_rows.append(work)
    cycle = _dataset_rows_base(registry, CONTACT_CYCLE_RECORDS_DATASET)
    cycle.update(
        {
            "case_id": case_id,
            "cycle_record_id": f"cycle-record:{case_index}",
            "cycle_id": "cycle:1",
            "commit_receipt_id": f"cycle-receipt:{case_index}",
            "lifecycle_kind": "RELEASE_RECONTACT_REENGAGEMENT",
            "start_point_id": f"point:{case_index}:0",
            "end_point_id": f"point:{case_index}:6",
            "release_event_id": f"event:{case_index}:0",
            "recontact_event_id": f"event:{case_index}:1",
            "reengagement_event_id": f"event:{case_index}:2",
            "start_x_total_mm": 0.0,
            "end_x_total_mm": 6.0,
            "start_drag_elapsed_time_s": 0.0,
            "end_drag_elapsed_time_s": 3.0,
            "right_censored": False,
        }
    )
    return {
        RUN_REQUESTS_DATASET: [request],
        SUPPORT_CANDIDATE_HISTORY_DATASET: [candidate],
        CONTACT_SUPPORT_HISTORY_DATASET: [contact],
        RELEASE_OPERATION_HISTORY_DATASET: releases,
        WORK_LEDGER_DATASET: work_rows,
        CONTACT_CYCLE_RECORDS_DATASET: [cycle],
    }


def _rejected_row(registry: SchemaRegistry, case_id: str, case_index: int) -> dict[str, Any]:
    row = _dataset_rows_base(registry, REJECTED_DIAGNOSTICS_DATASET)
    row.update(
        {
            "case_id": case_id,
            "diagnostic_id": f"diagnostic:{case_index}",
            "trial_id": f"trial:rejected:{case_index}",
            "attempt_kind": "EVENT_PROBE",
            "parent_point_id": f"point:{case_index}:2",
            "parent_accepted_state_id": f"state:{case_index}:2",
            "reason_family": "NUMERICAL",
            "reason_code": "M03_TEST_REJECTED",
            "failure_axis": "graph_residual",
            "raw_residual": 2.0,
            "raw_residual_unit": "1",
            "raw_guard": -0.1,
            "raw_guard_unit": "N",
            "surface_quality": "TRUSTED_FOR_DECLARED_SCALE",
            "accepted_state_advanced": False,
            "path_advanced": False,
            "time_advanced": False,
            "slip_advanced": False,
            "work_advanced": False,
            "cycle_advanced": False,
            "event_history_advanced": False,
        }
    )
    return row


@pytest.fixture
def canonical_reader(tmp_path: Path) -> tuple[ResultReader, Path]:
    root = tmp_path / "M03_VALIDATION_ONLY.spine-result"
    (root / "transactions" / "committed").mkdir(parents=True)
    (root / "schemas").mkdir()
    registry = SchemaRegistry()
    registry.register_extension(m03_result_extension())
    registry_hash = registry.freeze()
    snapshot = registry.snapshot()
    write_json_atomic(root / "schemas" / "registry.json", snapshot)

    auxiliary_rejected: list[dict[str, Any]] = []
    for case_index in range(2):
        case_id = f"case:M03_FIGURE:{case_index}"
        records = _other_rows(registry, case_id, case_index)
        records[ACCEPTED_STATE_HISTORY_DATASET] = _accepted_rows(registry, case_id, case_index)
        records[COMMITTED_EVENT_PAYLOADS_DATASET] = _event_rows(registry, case_id, case_index)
        datasets: dict[str, dict[str, Any]] = {}
        for dataset_id, rows in sorted(records.items()):
            path = root / "data" / f"case-{case_index}" / f"{dataset_id}.parquet"
            entry = write_parquet_records(path, rows)
            entry["path"] = path.relative_to(root).as_posix()
            datasets[dataset_id] = entry
        write_json_atomic(
            root / "transactions" / "committed" / f"receipt-{case_index}.json",
            {
                "receipt_id": f"receipt:fixture:{case_index}",
                "case_id": case_id,
                "datasets": datasets,
            },
        )
        rejected_path = root / "rejected_trials" / f"case-{case_index}.parquet"
        rejected_entry = write_parquet_records(
            rejected_path, [_rejected_row(registry, case_id, case_index)]
        )
        rejected_entry["path"] = rejected_path.relative_to(root).as_posix()
        auxiliary_rejected.append(rejected_entry)

    manifest = {
        "bundle_kind": "spine-result",
        "bundle_schema_version": BUNDLE_SCHEMA_VERSION,
        "bundle_semantic_hash": semantic_hash("M03_VALIDATION_FIGURE_READER_FIXTURE"),
        "registry_hash": registry_hash,
        "source_identity": SourceIdentity.VALIDATION_ONLY.value,
        "auxiliary_datasets": {REJECTED_DIAGNOSTICS_DATASET: auxiliary_rejected},
    }
    write_json_atomic(root / "bundle_manifest.json", manifest)
    return ResultReader(root, manifest, snapshot, "FULL_SCHEMA_SUPPORT"), root


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): source_file_hash(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_optional_matplotlib_unavailable_returns_machine_readable_manifest(
    canonical_reader: tuple[ResultReader, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reader, _ = canonical_reader

    def missing_matplotlib(name: str, package: str | None = None) -> Any:
        if name.startswith("matplotlib"):
            raise ModuleNotFoundError("intentional optional dependency fixture")
        return standard_import_module(name, package)

    monkeypatch.setattr(validation_module, "import_module", missing_matplotlib)
    output = tmp_path / "unavailable-pack"
    manifest = render_validation_figure_pack(reader, output)

    assert manifest.capability.capability_status is CapabilityStatus.UNAVAILABLE
    assert manifest.capability.reason_code == "M03_VALIDATION_MATPLOTLIB_UNAVAILABLE"
    assert manifest.source_identity is SourceIdentity.VALIDATION_ONLY
    assert manifest.certification_status is CertificationStatus.NOT_CERTIFIABLE
    assert manifest.artifacts == ()
    payload = json.loads((output / VALIDATION_FIGURE_MANIFEST).read_text(encoding="utf-8"))
    assert payload["capability"]["capability_status"] == "UNAVAILABLE"
    assert not tuple(output.glob("*.png"))
    assert not tuple(output.glob("*.svg"))


def test_available_pack_covers_all_recipes_and_leaves_bundle_read_only(
    canonical_reader: tuple[ResultReader, Path],
    tmp_path: Path,
) -> None:
    pytest.importorskip("matplotlib")
    reader, bundle = canonical_reader
    before = _tree_hashes(bundle)
    output = tmp_path / "figure-pack"
    manifest = render_validation_figure_pack(reader, output)
    after = _tree_hashes(bundle)

    assert before == after
    assert manifest.capability.capability_status is CapabilityStatus.SUPPORTED
    assert tuple(item.recipe_id for item in manifest.artifacts) == M03_FROZEN_RECIPE_IDS
    assert len(manifest.artifacts) == 8
    assert all(item.status is FigureRenderStatus.RENDERED for item in manifest.artifacts)
    assert all(item.raw_curve_visible and item.smoothing == "NONE" for item in manifest.artifacts)
    assert all(item.rejected_rows_included == 0 for item in manifest.artifacts)
    assert all(
        REJECTED_DIAGNOSTICS_DATASET
        not in {evidence.dataset_id for evidence in item.query_evidence}
        for item in manifest.artifacts
    )
    assert sum(len(item.files) for item in manifest.artifacts) == 16
    for artifact in manifest.artifacts:
        assert {
            RecipeDataRole.ACCEPTED_RAW.value,
            RecipeDataRole.COMMITTED_EVENT.value,
        } <= {item.role for item in artifact.query_evidence}
        for output_file in artifact.files:
            path = output / output_file.relative_path
            assert path.stat().st_size == output_file.byte_size > 0
            assert source_file_hash(path) == output_file.content_sha256

    by_id = {item.recipe_id: item for item in manifest.artifacts}
    assert RAW_PEAK_ALGORITHM_ID in by_id["m03.recipe.event_zoom_and_multi_peak"].algorithms
    assert (
        "PAIRED_RAW_COMMON_SURFACE_PATH_LINES_1" in by_id["m03.recipe.parameter_trends"].algorithms
    )
    manifest_payload = json.loads((output / VALIDATION_FIGURE_MANIFEST).read_text(encoding="utf-8"))
    identity = {
        key: value
        for key, value in manifest_payload.items()
        if key not in {"pack_id", "manifest_hash"}
    }
    assert semantic_hash(identity) == manifest_payload["manifest_hash"]
    assert manifest_payload["source_identity"] == "VALIDATION_ONLY"
    assert manifest_payload["certification_status"] == "NOT_CERTIFIABLE"


def test_rejected_overlay_requires_explicit_opt_in(
    canonical_reader: tuple[ResultReader, Path],
    tmp_path: Path,
) -> None:
    pytest.importorskip("matplotlib")
    reader, _ = canonical_reader
    manifest = render_validation_figure_pack(
        reader,
        tmp_path / "diagnostic-pack",
        formats=("png",),
        include_rejected=True,
    )

    assert manifest.include_rejected
    assert all(item.rejected_rows_included == 2 for item in manifest.artifacts)
    for artifact in manifest.artifacts:
        rejected = tuple(
            item
            for item in artifact.query_evidence
            if item.dataset_id == REJECTED_DIAGNOSTICS_DATASET
        )
        assert len(rejected) == 1
        assert rejected[0].role == RecipeDataRole.REJECTED_DIAGNOSTIC.value
        assert rejected[0].include_non_default
        assert rejected[0].include_diagnostics


def test_import_boundaries_keep_plotting_out_of_solver_runtime() -> None:
    source = Path(validation_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)} | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not any(name.endswith((".kernel", ".standalone")) for name in imports)
    assert not any(name.startswith(("pyarrow", "zarr")) for name in imports)
    assert "._root" not in source

    package = Path(validation_module.__file__).parent
    for runtime_name in ("kernel.py", "events.py", "contact.py", "beam.py", "mount.py"):
        runtime_source = (package / runtime_name).read_text(encoding="utf-8")
        assert "validation_figures" not in runtime_source
        assert "matplotlib" not in runtime_source

    repo_root = package.parents[2]
    command = (
        "import sys;"
        f"sys.path.insert(0, {str(repo_root / 'src')!r});"
        "import spine_sim.single_spine.validation_figures;"
        "assert 'matplotlib' not in sys.modules;"
        "assert 'matplotlib.pyplot' not in sys.modules"
    )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize("bad_formats", [(), ("pdf",), ("png", "PDF")])
def test_output_formats_are_explicitly_bounded(
    canonical_reader: tuple[ResultReader, Path],
    tmp_path: Path,
    bad_formats: tuple[str, ...],
) -> None:
    reader, _ = canonical_reader
    with pytest.raises(ContractViolation, match=r"formats|PNG and SVG"):
        render_validation_figure_pack(reader, tmp_path / "bad-format", formats=bad_formats)
