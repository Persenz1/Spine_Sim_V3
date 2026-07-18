from __future__ import annotations

import ast
from pathlib import Path

import pytest

from spine_sim.foundation.reader import ResultReader
from spine_sim.foundation.registry import DatasetClass, SchemaRegistry
from spine_sim.numerics import plot_recipes as plot_recipe_module
from spine_sim.numerics.plot_recipes import (
    EVENT_BRACKET_RECIPE_ID,
    FAILURE_STATISTICS_RECIPE_ID,
    M02_PLOT_RECIPE_VERSION,
    REFINEMENT_ERROR_RECIPE_ID,
    RELEASE_RECONTACT_CHAIN_RECIPE_ID,
    RESIDUAL_ITERATIONS_RECIPE_ID,
    STEP_SIZE_RECIPE_ID,
    RecipeDataRole,
    get_m02_plot_recipe,
    m02_plot_recipe_registry,
    m02_plot_recipes,
)
from spine_sim.numerics.result_extension import m02_result_extension

FROZEN_RECIPE_IDS = {
    RESIDUAL_ITERATIONS_RECIPE_ID,
    STEP_SIZE_RECIPE_ID,
    EVENT_BRACKET_RECIPE_ID,
    RELEASE_RECONTACT_CHAIN_RECIPE_ID,
    REFINEMENT_ERROR_RECIPE_ID,
    FAILURE_STATISTICS_RECIPE_ID,
}


def _local_fields(recipe_id: str) -> set[str]:
    return {field for query in get_m02_plot_recipe(recipe_id).queries for field in query.fields}


def test_exactly_six_versioned_read_only_recipe_contracts_are_registered() -> None:
    recipes = m02_plot_recipes()
    registry = m02_plot_recipe_registry()
    assert len(recipes) == 6
    assert {item.recipe_id for item in recipes} == FROZEN_RECIPE_IDS
    assert set(registry) == FROZEN_RECIPE_IDS
    assert all(item.recipe_version == M02_PLOT_RECIPE_VERSION for item in recipes)
    assert all(item.requirements.recipe_version == M02_PLOT_RECIPE_VERSION for item in recipes)
    assert all(item.read_only for item in recipes)
    with pytest.raises(TypeError):
        registry["m02.recipe.forbidden_mutation"] = recipes[0]  # type: ignore[index]


def test_recipes_import_no_plotting_or_m06_implementation() -> None:
    source = Path(plot_recipe_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not any("matplotlib" in item or "plotly" in item for item in imported_modules)
    assert not any(item.startswith("spine_sim.m06") for item in imported_modules)


def test_all_recipe_field_requirements_exactly_match_registered_metadata(
    tmp_path: Path,
) -> None:
    registry = SchemaRegistry()
    extension = m02_result_extension()
    registry.register_extension(extension)
    registry.freeze()
    reader = ResultReader(tmp_path, {}, registry.snapshot(), "FULL_SCHEMA_SUPPORT")
    fields = {field.field_id: field for dataset in extension.tables for field in dataset.fields}

    for recipe in m02_plot_recipes():
        report = reader.check_plot_requirements(recipe.requirements)
        assert report.satisfied, report.deficiencies
        assert not report.deficiencies
        for required in recipe.requirements.fields:
            metadata = fields[required.field_id]
            assert required.minimum_sampling_cadence == metadata.sampling_cadence
            assert required.unit == metadata.unit
            assert required.frame == metadata.frame
            assert required.reference_point == metadata.reference_point
            assert required.allowed_source_identities == (metadata.source_identity.value,)


def test_recipe_queries_use_reader_supported_fields_filters_and_strict_data_roles() -> None:
    descriptor = m02_result_extension()
    datasets = {item.dataset_id: item for item in descriptor.tables}
    supported_operators = {"==", "!=", ">", ">=", "<", "<=", "in"}

    for recipe in m02_plot_recipes():
        for query in recipe.queries:
            dataset = datasets[query.dataset_id]
            local_fields = {item.field_id.rsplit(".", 1)[-1] for item in dataset.fields}
            assert set(query.fields) <= local_fields
            assert {item.field for item in query.filters} <= local_fields
            assert {item.operator for item in query.filters} <= supported_operators
            if query.role is RecipeDataRole.PHYSICAL:
                assert dataset.dataset_class is not DatasetClass.REJECTED
                assert not query.include_diagnostics
                assert any(
                    item.field == "commit_receipt_id" and item.operator == "!=" and item.value == ""
                    for item in query.filters
                )
            if dataset.dataset_class is DatasetClass.REJECTED:
                assert query.role is RecipeDataRole.DIAGNOSTIC_OVERLAY
                assert query.include_diagnostics
                assert query.include_non_default
            if query.role is RecipeDataRole.VALIDATION:
                assert dataset.dataset_class is DatasetClass.SUMMARY
                assert query.include_non_default


def test_physical_queries_never_consume_rejected_trial_or_probe_rows() -> None:
    datasets = {item.dataset_id: item.dataset_class for item in m02_result_extension().tables}
    for recipe in m02_plot_recipes():
        assert all(
            datasets[query.dataset_id] is not DatasetClass.REJECTED
            for query in recipe.physical_queries
        )
        assert all(
            datasets[query.dataset_id] is DatasetClass.REJECTED
            for query in recipe.diagnostic_queries
        )

    for recipe_id in {
        STEP_SIZE_RECIPE_ID,
        EVENT_BRACKET_RECIPE_ID,
        RELEASE_RECONTACT_CHAIN_RECIPE_ID,
        FAILURE_STATISTICS_RECIPE_ID,
    }:
        for query in get_m02_plot_recipe(recipe_id).diagnostic_queries:
            if "accepted_state_advanced" in {
                item.field_id.rsplit(".", 1)[-1]
                for item in next(
                    dataset
                    for dataset in m02_result_extension().tables
                    if dataset.dataset_id == query.dataset_id
                ).fields
            }:
                assert any(
                    item.field == "accepted_state_advanced"
                    and item.operator == "=="
                    and item.value is False
                    for item in query.filters
                )


@pytest.mark.parametrize(
    ("recipe_id", "required_fields"),
    [
        (
            RESIDUAL_ITERATIONS_RECIPE_ID,
            {
                "iteration",
                "block_id",
                "raw_norm",
                "raw_unit",
                "tolerance",
                "normalized_norm",
                "merit",
                "linear_residual",
                "line_search_factor",
            },
        ),
        (
            STEP_SIZE_RECIPE_ID,
            {
                "attempted_coordinate",
                "accepted_coordinate",
                "requested_step",
                "accepted_step",
                "retry_index",
                "growth_shrink_reason",
                "event_marker_id",
            },
        ),
        (
            EVENT_BRACKET_RECIPE_ID,
            {
                "raw_guard",
                "raw_guard_unit",
                "path_coordinate",
                "left_coordinate",
                "right_coordinate",
                "root_coordinate",
                "direction",
                "simultaneous_tolerance",
                "equilibrium_quality",
            },
        ),
        (
            RELEASE_RECONTACT_CHAIN_RECIPE_ID,
            {
                "release_pose_ref",
                "path_mode",
                "path_coordinate",
                "event_kind",
                "pre_accepted_state_id",
                "post_accepted_state_id",
                "event_id",
                "commit_receipt_id",
            },
        ),
        (
            REFINEMENT_ERROR_RECIPE_ID,
            {
                "step_size",
                "event_tolerance",
                "m01_lod",
                "root_solver_level",
                "event_position",
                "force_summary_n",
                "work_summary_n_mm",
                "observed_order",
                "event_order_matched",
            },
        ),
        (
            FAILURE_STATISTICS_RECIPE_ID,
            {
                "failure_family",
                "reason_code",
                "failure_stage",
                "design_id",
                "surface_realization_id",
                "footprint_id",
                "last_valid_state_id",
                "wall_time_s",
                "runtime_cost_units",
                "denominator_scope",
                "includes_capability_unavailable",
            },
        ),
    ],
)
def test_frozen_recipe_semantics_have_all_required_fields(
    recipe_id: str, required_fields: set[str]
) -> None:
    assert required_fields <= _local_fields(recipe_id)
