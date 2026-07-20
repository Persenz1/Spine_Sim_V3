from __future__ import annotations

import ast
import dataclasses
from pathlib import Path
from typing import Any

import pytest

from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    AttemptOutcome,
    CapabilityStatus,
    CertificationStatus,
    Maturity,
    PhysicalFeasibility,
    SourceIdentity,
    StatusTuple,
    ValuePresence,
)
from spine_sim.foundation.reader import ResultReader
from spine_sim.foundation.registry import DatasetClass, SchemaRegistry
from spine_sim.single_spine import plot_recipes as plot_recipe_module
from spine_sim.single_spine.contracts import M03_SCHEMA_VERSION
from spine_sim.single_spine.plot_recipes import (
    EVENT_ZOOM_AND_MULTI_PEAK_RECIPE_ID,
    FIVE_STAGE_FUNNEL_BANDS_RECIPE_ID,
    LOCAL_GEOMETRY_RECIPE_ID,
    M03_FILTER_CONTRACT,
    M03_FROZEN_RECIPE_IDS,
    M03_PLOT_RECIPE_VERSION,
    PARAMETER_TRENDS_RECIPE_ID,
    QUALITY_AND_WORK_RECIPE_ID,
    RESPONSE_OVERVIEW_RECIPE_ID,
    STATE_BANDS_RECIPE_ID,
    STRUCTURE_AND_SPRING_RECIPE_ID,
    RecipeDataRole,
    build_plot_recipe_manifest_records,
    get_m03_plot_recipe,
    m03_plot_recipe_registry,
    m03_plot_recipes,
)
from spine_sim.single_spine.result_extension import (
    ACCEPTED_STATE_HISTORY_DATASET,
    COMMITTED_EVENT_PAYLOADS_DATASET,
    REJECTED_DIAGNOSTICS_DATASET,
    AcceptedStateHistoryRecord,
    CommittedEventPayloadRecord,
    ContactCycleRecord,
    WorkLedgerRecord,
    m03_result_extension,
)
from spine_sim.single_spine.summaries import (
    CYCLE_PATH_FRACTION_DEFINITION_ID,
    FALSE_ENGAGEMENT_DEFINITION_ID,
    FIRST_LOAD_BEARING_DEFINITION_ID,
    FIRST_LOADED_CONTACT_DEFINITION_ID,
    M03_SUMMARY_DEFINITION_IDS,
    MULTI_PEAK_DEFINITION_ID,
    RELEASE_LIFECYCLE_DEFINITION_ID,
    WORK_ENERGY_DEFINITION_ID,
    build_m03_summaries,
    rebuild_m03_summaries,
)

RUN_ID = "run:M03_SUMMARY_FIXTURE"
CASE_ID = "case:M03_SUMMARY_FIXTURE"


def _status() -> StatusTuple:
    return StatusTuple(
        value_presence=ValuePresence.PRESENT,
        capability_status=CapabilityStatus.SUPPORTED,
        attempt_outcome=AttemptOutcome.ACCEPTED,
        physical_feasibility=PhysicalFeasibility.FEASIBLE,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        reason_code="M03_TEST_COMMITTED_RAW",
        explanation="Deterministic validation-only summary fixture.",
    )


def _generic_value(name: str, annotation: Any) -> Any:
    text = str(annotation)
    if "None" in text:
        return None
    if text == "str":
        return f"{name}:fixture"
    if text == "float":
        return 0.0
    if text == "int":
        return 0
    if text == "bool":
        return False
    if "tuple" in text.lower() or text.startswith(("Vector", "Matrix")):
        return ()
    if "dict" in text.lower():
        return {}
    return f"{name}:fixture"


def _record(record_type: type[Any], **overrides: Any) -> Any:
    values = {
        item.name: _generic_value(item.name, item.type) for item in dataclasses.fields(record_type)
    }
    values.update(
        {
            "run_id": RUN_ID,
            "case_id": CASE_ID,
            "schema_version": M03_SCHEMA_VERSION,
            "status": _status(),
            "source_identity": SourceIdentity.DEV_POLICY,
            "maturity": Maturity.validation_only_implemented(),
            "certification_status": CertificationStatus.NOT_CERTIFIABLE,
        }
    )
    values.update(overrides)
    return record_type(**values)


def _accepted(
    index: int,
    force_n: float,
    *,
    cycle_id: str,
    geometric: bool = False,
    loaded: bool = False,
    stable: bool = False,
    bearing: bool = False,
) -> AcceptedStateHistoryRecord:
    return _record(
        AcceptedStateHistoryRecord,
        state_record_id=f"state-record:{index}",
        point_id=f"point:{index}",
        commit_receipt_id=f"receipt:{index}",
        accepted_point_index=index,
        x_total_mm=float(index),
        drag_elapsed_time_s=float(index),
        operation_path_coordinate_mm=float(index),
        cycle_id=cycle_id,
        grip_resistance_rx_n=force_n,
        geometric_candidate=geometric,
        loaded_contact=loaded,
        frictionally_stable=stable,
        load_bearing=bearing,
    )


def _event(index: int, kind: str, cycle_id: str) -> CommittedEventPayloadRecord:
    return _record(
        CommittedEventPayloadRecord,
        event_payload_id=f"event-payload:{index}",
        event_id=f"event:{kind.lower()}",
        commit_receipt_id=f"event-receipt:{index}",
        event_kind=kind,
        path_coordinate_mm=float(index),
        cycle_id=cycle_id,
    )


def _summary_fixture() -> tuple[
    tuple[AcceptedStateHistoryRecord, ...],
    tuple[CommittedEventPayloadRecord, ...],
    tuple[ContactCycleRecord, ...],
    tuple[WorkLedgerRecord, ...],
]:
    forces = (0.0, 4.0, 1.0, 5.0, 1.0, 0.5, 0.0, 0.0, 0.0)
    accepted = tuple(
        _accepted(
            index,
            force,
            cycle_id="cycle:0" if index <= 6 else "cycle:1",
            geometric=index in {1, 2, 3},
            loaded=index in {2, 3, 4, 5},
            stable=index in {2, 3, 4, 5},
            bearing=index in {3, 4, 5},
        )
        for index, force in enumerate(forces)
    )
    events = (
        _event(6, "RELEASE", "cycle:0"),
        _event(7, "RECONTACT", "cycle:1"),
        _event(8, "REENGAGEMENT", "cycle:1"),
    )
    cycles = (
        _record(
            ContactCycleRecord,
            cycle_record_id="cycle-record:0",
            cycle_id="cycle:0",
            commit_receipt_id="cycle-receipt:0",
            release_event_id="event:release",
            recontact_event_id="event:recontact",
            reengagement_event_id="event:reengagement",
            start_x_total_mm=0.0,
            end_x_total_mm=6.0,
            start_drag_elapsed_time_s=0.0,
            end_drag_elapsed_time_s=6.0,
            right_censored=False,
        ),
        _record(
            ContactCycleRecord,
            cycle_record_id="cycle-record:1",
            cycle_id="cycle:1",
            commit_receipt_id="cycle-receipt:1",
            start_x_total_mm=7.0,
            end_x_total_mm=8.0,
            start_drag_elapsed_time_s=7.0,
            end_drag_elapsed_time_s=8.0,
            right_censored=False,
        ),
    )
    ledger = (
        _record(
            WorkLedgerRecord,
            work_ledger_id="work:0",
            start_point_id="point:0",
            end_point_id="point:1",
            commit_receipt_id="work-receipt:0",
            accepted_interval_index=0,
            friction_dissipation_n_mm=1.5,
            returned_recoverable_energy_n_mm=0.25,
            rigid_contact_energy_n_mm=0.0,
            material_dissipation_n_mm=0.0,
        ),
        _record(
            WorkLedgerRecord,
            work_ledger_id="work:1",
            start_point_id="point:1",
            end_point_id="point:2",
            commit_receipt_id="work-receipt:1",
            accepted_interval_index=1,
            friction_dissipation_n_mm=2.5,
            returned_recoverable_energy_n_mm=0.5,
            rigid_contact_energy_n_mm=0.0,
            material_dissipation_n_mm=0.0,
        ),
    )
    return accepted, events, cycles, ledger


def _by_definition() -> dict[str, Any]:
    accepted, events, cycles, ledger = _summary_fixture()
    summaries = build_m03_summaries(
        accepted,
        committed_events=events,
        contact_cycles=cycles,
        work_ledger=ledger,
    )
    return {item.definition_id: item for item in summaries}


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, (list, tuple)):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def test_all_versioned_summary_families_are_rebuildable_and_raw_linked() -> None:
    accepted, events, cycles, ledger = _summary_fixture()
    summaries = build_m03_summaries(
        accepted,
        committed_events=events,
        contact_cycles=cycles,
        work_ledger=ledger,
    )
    rebuilt = rebuild_m03_summaries(
        accepted,
        committed_events=events,
        contact_cycles=cycles,
        work_ledger=ledger,
    )
    assert len(summaries) == 7
    assert {item.definition_id for item in summaries} == set(M03_SUMMARY_DEFINITION_IDS)
    assert tuple(item.summary_id for item in summaries) == tuple(
        item.summary_id for item in rebuilt
    )
    assert all(item.definition_version == "1.0.0" for item in summaries)
    assert all(item.definition_hash and item.input_raw_links for item in summaries)
    assert all(
        item.input_accepted_point_ids == tuple(row.point_id for row in accepted)
        for item in summaries
    )
    assert all("rejected" not in item.included_dataset_classes for item in summaries)
    forbidden = {"success", "composite_score", "score", "confidence_interval", "ci"}
    assert all(not (_all_keys(item.summary_payload) & forbidden) for item in summaries)


def test_first_stage_right_censor_and_false_engagement_episode_semantics() -> None:
    by_definition = _by_definition()
    first_loaded = by_definition[FIRST_LOADED_CONTACT_DEFINITION_ID]
    first_bearing = by_definition[FIRST_LOAD_BEARING_DEFINITION_ID]
    false_engagement = by_definition[FALSE_ENGAGEMENT_DEFINITION_ID]

    assert first_loaded.summary_payload["first_distance_mm"] == 2.0
    assert not first_loaded.right_censored
    assert first_bearing.summary_payload["first_distance_mm"] == 3.0
    assert not first_bearing.right_censored
    assert false_engagement.summary_payload["episode_count"] == 1
    episode = false_engagement.summary_payload["episodes"][0]
    assert (episode["start_point_id"], episode["end_point_id"]) == ("point:1", "point:2")
    assert not episode["right_censored"]

    censored_rows = (
        _accepted(0, 0.0, cycle_id="cycle:0", geometric=True),
        _accepted(1, 1.0, cycle_id="cycle:0", geometric=True, loaded=True),
    )
    censored = {item.definition_id: item for item in build_m03_summaries(censored_rows)}
    assert censored[FIRST_LOAD_BEARING_DEFINITION_ID].right_censored
    assert censored[FIRST_LOAD_BEARING_DEFINITION_ID].summary_payload["first_distance_mm"] is None
    assert censored[FALSE_ENGAGEMENT_DEFINITION_ID].right_censored


def test_release_cycle_peak_and_work_summaries_preserve_descriptive_evidence() -> None:
    by_definition = _by_definition()
    lifecycle = by_definition[RELEASE_LIFECYCLE_DEFINITION_ID]
    cycle = by_definition[CYCLE_PATH_FRACTION_DEFINITION_ID]
    peaks = by_definition[MULTI_PEAK_DEFINITION_ID]
    work = by_definition[WORK_ENERGY_DEFINITION_ID]

    chain = lifecycle.summary_payload["chains"][0]
    assert chain["release_to_recontact_distance_mm"] == 1.0
    assert chain["release_to_recontact_drag_elapsed_time_s"] == 1.0
    assert chain["release_to_reengagement_distance_mm"] == 2.0
    assert chain["physical_operation_time_s"] is None
    assert not lifecycle.right_censored

    assert cycle.summary_payload["contact_cycle_count"] == 2
    assert cycle.summary_payload["loaded_path_fraction"] == pytest.approx(0.5)
    assert cycle.summary_payload["load_bearing_path_fraction"] == pytest.approx(0.375)

    assert peaks.summary_payload["smoothing"] == "NONE"
    assert peaks.summary_payload["total_peak_count"] == 2
    raw_peak_links = tuple(
        peak["raw_record_link"]
        for cycle_payload in peaks.summary_payload["cycles"]
        for peak in cycle_payload["peaks"]
    )
    assert raw_peak_links == (
        f"{ACCEPTED_STATE_HISTORY_DATASET}#state-record:1",
        f"{ACCEPTED_STATE_HISTORY_DATASET}#state-record:3",
    )

    assert work.summary_payload["positive_resisting_work_n_mm"] == pytest.approx(11.5)
    assert work.summary_payload["friction_dissipation_n_mm"] == 4.0
    assert work.summary_payload["returned_recoverable_energy_n_mm"] == 0.75


def test_summary_builder_rejects_mixed_cases_and_coordinate_resets() -> None:
    good = _accepted(0, 0.0, cycle_id="cycle:0")
    wrong_case = dataclasses.replace(_accepted(1, 0.0, cycle_id="cycle:0"), case_id="case:WRONG")
    with pytest.raises(ContractViolation, match="one run and case"):
        build_m03_summaries((good, wrong_case))

    reset = dataclasses.replace(_accepted(1, 0.0, cycle_id="cycle:0"), x_total_mm=-1.0)
    with pytest.raises(ContractViolation, match="cannot decrease"):
        build_m03_summaries((good, reset))


def test_exactly_eight_frozen_machine_readable_recipe_families() -> None:
    recipes = m03_plot_recipes()
    registry = m03_plot_recipe_registry()
    assert len(recipes) == 8
    assert tuple(item.recipe_id for item in recipes) == M03_FROZEN_RECIPE_IDS
    assert set(registry) == set(M03_FROZEN_RECIPE_IDS)
    assert all(item.recipe_version == M03_PLOT_RECIPE_VERSION for item in recipes)
    assert all(item.smoothing == "NONE" and item.read_only for item in recipes)
    assert all(item.default_dataset_classes == ("accepted", "event") for item in recipes)
    with pytest.raises(TypeError):
        registry["m03.recipe.forbidden_mutation"] = recipes[0]  # type: ignore[index]


def test_recipes_import_no_plotting_or_m06_runtime() -> None:
    source = Path(plot_recipe_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not any("matplotlib" in item or "plotly" in item for item in imported)
    assert not any(item.startswith("spine_sim.m06") for item in imported)


def test_recipe_queries_enforce_default_raw_event_and_rejected_opt_in_boundary() -> None:
    datasets = {item.dataset_id: item.dataset_class for item in m03_result_extension().tables}
    for recipe in m03_plot_recipes():
        assert all(query.enabled_by_default for query in recipe.default_queries)
        assert {datasets[query.dataset_id] for query in recipe.default_queries} <= {
            DatasetClass.ACCEPTED,
            DatasetClass.EVENT,
        }
        assert any(query.role is RecipeDataRole.ACCEPTED_RAW for query in recipe.default_queries)
        assert any(query.role is RecipeDataRole.COMMITTED_EVENT for query in recipe.default_queries)
        assert all(not query.include_diagnostics for query in recipe.default_queries)
        assert all(
            any(
                item.field == "commit_receipt_id" and item.operator == "!=" and item.value == ""
                for item in query.filters
            )
            for query in recipe.default_queries
        )
        assert all(
            query.dataset_id == REJECTED_DIAGNOSTICS_DATASET
            and not query.enabled_by_default
            and query.include_diagnostics
            and query.include_non_default
            for query in recipe.diagnostic_queries
        )


def test_recipe_requirements_exactly_match_registered_m03_metadata(tmp_path: Path) -> None:
    registry = SchemaRegistry()
    extension = m03_result_extension()
    registry.register_extension(extension)
    registry.freeze()
    reader = ResultReader(tmp_path, {}, registry.snapshot(), "FULL_SCHEMA_SUPPORT")
    metadata = {field.field_id: field for table in extension.tables for field in table.fields}

    for recipe in m03_plot_recipes():
        report = reader.check_plot_requirements(recipe.requirements)
        assert report.satisfied, report.deficiencies
        for field in recipe.requirements.fields:
            registered = metadata[field.field_id]
            assert field.minimum_sampling_cadence == registered.sampling_cadence
            assert field.unit == registered.unit
            assert field.frame == registered.frame
            assert field.reference_point == registered.reference_point


def test_filter_contract_covers_every_frozen_interactive_dimension() -> None:
    required = {
        "surface_family",
        "surface_realization_id",
        "surface_seed",
        "surface_scale",
        "case_id",
        "design_id",
        "Rt",
        "d",
        "L",
        "alpha",
        "beta",
        "E",
        "nu",
        "mu",
        "bending",
        "mount",
        "ks",
        "spring_state",
        "primary_mechanical_state",
        "contact_motion_state",
        "operation_phase",
        "geometric_candidate",
        "loaded_contact",
        "frictionally_stable",
        "load_bearing",
        "cycle_id",
        "event_kind",
        "frame",
        "reference_point",
        "task_direction",
        "source_class",
        "maturity",
        "source_identity",
        "certification_status",
        "capability_status",
        "x_or_t_view",
        "global_or_local_component_view",
    }
    assert {item.filter_id for item in M03_FILTER_CONTRACT} == required
    assert all(
        {item.filter_id for item in recipe.filter_contract} == required
        for recipe in m03_plot_recipes()
    )
    by_id = {item.filter_id: item for item in M03_FILTER_CONTRACT}
    assert by_id["source_class"].allowed_values == (
        "accepted",
        "committed_event",
        "rejected",
    )
    assert by_id["x_or_t_view"].allowed_values == (
        "x_total_mm",
        "drag_elapsed_time_s",
    )
    assert by_id["global_or_local_component_view"].allowed_values == (
        "GLOBAL",
        "NEEDLE_LOCAL",
    )


@pytest.mark.parametrize(
    ("recipe_id", "required_local_fields"),
    [
        (
            RESPONSE_OVERVIEW_RECIPE_ID,
            {"x_total_mm", "drag_elapsed_time_s", "wrench_a_on_b_global_at_o_n_n_mm"},
        ),
        (
            STATE_BANDS_RECIPE_ID,
            {
                "primary_mechanical_state",
                "operation_phase",
                "contact_motion_states",
                "active_support_ids",
                "spring_state",
            },
        ),
        (
            FIVE_STAGE_FUNNEL_BANDS_RECIPE_ID,
            {
                "geometric_candidate",
                "loaded_contact",
                "frictionally_stable",
                "load_bearing",
                "five_stage_reason_codes",
            },
        ),
        (
            LOCAL_GEOMETRY_RECIPE_ID,
            {
                "candidate_point_global_mm",
                "normal_global",
                "tangent_1_global",
                "finite_cap_legal",
                "rejection_reason",
                "full_body_minimum_clearance_mm",
            },
        ),
        (
            STRUCTURE_AND_SPRING_RECIPE_ID,
            {
                "beam_tip_translation_global_mm",
                "beam_tip_rotation_global_rad",
                "beam_root_force_global_n",
                "section_resultants_needle_n_n_mm",
                "spring_compression_mm",
                "spring_hard_stop_reaction_n",
            },
        ),
        (
            EVENT_ZOOM_AND_MULTI_PEAK_RECIPE_ID,
            {
                "raw_signed_guard",
                "bracket_ref",
                "probe_refs",
                "pre_wrench_global_at_o_n_n_mm",
                "event_wrench_global_at_o_n_n_mm",
                "post_wrench_global_at_o_n_n_mm",
                "release_event_id",
                "recontact_event_id",
                "reengagement_event_id",
            },
        ),
        (
            QUALITY_AND_WORK_RECIPE_ID,
            {
                "residual_block_payloads",
                "complementarity_residual",
                "contact_soc_residual",
                "graph_residual",
                "query_quality",
                "closure_error_n_mm",
                "friction_dissipation_n_mm",
                "returned_recoverable_energy_n_mm",
            },
        ),
        (
            PARAMETER_TRENDS_RECIPE_ID,
            {
                "parameter_bundle_id",
                "surface_realization_id",
                "grip_resistance_rx_n",
                "loaded_contact",
                "load_bearing",
            },
        ),
    ],
)
def test_frozen_recipe_semantics_project_required_raw_fields(
    recipe_id: str, required_local_fields: set[str]
) -> None:
    recipe = get_m03_plot_recipe(recipe_id)
    projected = {field for query in recipe.default_queries for field in query.fields}
    assert required_local_fields <= projected


def test_manifest_records_are_deterministic_complete_and_keep_rejected_out_of_defaults() -> None:
    first = build_plot_recipe_manifest_records(run_id=RUN_ID, case_id=CASE_ID)
    second = build_plot_recipe_manifest_records(run_id=RUN_ID, case_id=CASE_ID)
    assert len(first) == 8
    assert tuple(item.recipe_id for item in first) == M03_FROZEN_RECIPE_IDS
    assert tuple(item.summary_id for item in first) == tuple(item.summary_id for item in second)
    assert all(item.included_dataset_classes == ("accepted", "event") for item in first)
    assert all(item.rejected_opt_in and item.smoothing == "NONE" for item in first)
    assert all(REJECTED_DIAGNOSTICS_DATASET not in item.raw_dataset_links for item in first)
    assert all(ACCEPTED_STATE_HISTORY_DATASET in item.raw_dataset_links for item in first)
    assert all(COMMITTED_EVENT_PAYLOADS_DATASET in item.raw_dataset_links for item in first)
    assert all(item.recipe_payload["raw_curve_visible"] for item in first)
    assert all(item.recipe_payload["field_contracts"] for item in first)
    assert all(
        item.recipe_payload["recipe_definition_hash"] == item.definition_hash for item in first
    )
    five_stage = next(item for item in first if item.recipe_id == FIVE_STAGE_FUNNEL_BANDS_RECIPE_ID)
    assert five_stage.source_identity is SourceIdentity.PROPOSED_SUPPLEMENT
