"""Versioned, read-only M02 plot-data recipes for future M06 consumers.

This module contains field and filter contracts only.  It intentionally imports
neither a plotting library nor an M06 implementation, and it makes no visual
preset decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from spine_sim.foundation.plot_requirements import PlotDataRequirements, RequiredPlotField
from spine_sim.foundation.reader import FilterSpec
from spine_sim.foundation.registry import DatasetClass

from .result_extension import (
    ACCEPTED_STEP_NUMERICS_DATASET,
    CASCADE_ROUNDS_DATASET,
    CONTINUATION_ATTEMPTS_DATASET,
    EVENT_BRACKETS_DATASET,
    EVENT_PROBES_DATASET,
    FAILURE_DIAGNOSTICS_DATASET,
    ITERATION_TRACES_DATASET,
    REFINEMENT_STUDIES_DATASET,
    REJECTED_EVENT_BRACKETS_DATASET,
    REJECTED_ITERATION_TRACES_DATASET,
    REJECTED_TRIAL_DIAGNOSTICS_DATASET,
    RESIDUAL_BLOCK_SUMMARIES_DATASET,
    SIMULTANEOUS_EVENT_GROUPS_DATASET,
    m02_result_extension,
)

M02_PLOT_RECIPE_VERSION = "1.0.0"

RESIDUAL_ITERATIONS_RECIPE_ID = "m02.recipe.residual_iterations"
STEP_SIZE_RECIPE_ID = "m02.recipe.step_size"
EVENT_BRACKET_RECIPE_ID = "m02.recipe.event_bracket"
RELEASE_RECONTACT_CHAIN_RECIPE_ID = "m02.recipe.release_recontact_chain"
REFINEMENT_ERROR_RECIPE_ID = "m02.recipe.refinement_error"
FAILURE_STATISTICS_RECIPE_ID = "m02.recipe.failure_statistics"


class RecipeDataRole(StrEnum):
    """How a query may be used by a downstream read-only consumer."""

    PHYSICAL = "PHYSICAL"
    DIAGNOSTIC_OVERLAY = "DIAGNOSTIC_OVERLAY"
    VALIDATION = "VALIDATION"


_DESCRIPTOR = m02_result_extension()
_DATASETS = {item.dataset_id: item for item in _DESCRIPTOR.tables}
_FIELDS = {field.field_id: field for dataset in _DESCRIPTOR.tables for field in dataset.fields}


@dataclass(frozen=True, slots=True)
class M02RecipeQuery:
    """A projection/filter tuple accepted directly by ``ResultReader.query``."""

    dataset_id: str
    fields: tuple[str, ...]
    filters: tuple[FilterSpec, ...]
    role: RecipeDataRole
    include_non_default: bool
    include_diagnostics: bool

    def __post_init__(self) -> None:
        dataset = _DATASETS.get(self.dataset_id)
        if dataset is None:
            raise ValueError(f"unknown M02 recipe dataset: {self.dataset_id}")
        available = {item.field_id.rsplit(".", 1)[-1] for item in dataset.fields}
        missing = (set(self.fields) | {item.field for item in self.filters}) - available
        if missing:
            raise ValueError(
                f"recipe query references unknown fields in {self.dataset_id}: {sorted(missing)}"
            )
        if self.role is RecipeDataRole.PHYSICAL:
            if dataset.dataset_class is DatasetClass.REJECTED:
                raise ValueError("rejected diagnostics cannot be a physical plot-data source")
            if self.include_diagnostics:
                raise ValueError("physical query cannot enable diagnostic rows")
        if dataset.dataset_class is DatasetClass.REJECTED and not self.include_diagnostics:
            raise ValueError("rejected datasets require explicit diagnostic opt-in")


@dataclass(frozen=True, slots=True)
class M02PlotRecipe:
    """Frozen fields, filters, and accepted/rejected boundary for one recipe."""

    recipe_id: str
    recipe_version: str
    title: str
    requirements: PlotDataRequirements
    queries: tuple[M02RecipeQuery, ...]
    read_only: bool = True

    def __post_init__(self) -> None:
        if not self.recipe_id.startswith("m02.recipe."):
            raise ValueError("M02 recipe IDs must use the m02.recipe namespace")
        if self.recipe_version != M02_PLOT_RECIPE_VERSION:
            raise ValueError("unsupported M02 plot recipe version")
        if self.requirements.recipe_id != self.recipe_id:
            raise ValueError("plot requirements and recipe identity disagree")
        if not self.read_only:
            raise ValueError("M02 plot-data recipes are read-only")
        query_fields = {
            f"{query.dataset_id}.{field}" for query in self.queries for field in query.fields
        }
        required_fields = {item.field_id for item in self.requirements.fields}
        if query_fields != required_fields:
            raise ValueError("recipe requirements must exactly cover projected query fields")

    @property
    def physical_queries(self) -> tuple[M02RecipeQuery, ...]:
        return tuple(item for item in self.queries if item.role is RecipeDataRole.PHYSICAL)

    @property
    def diagnostic_queries(self) -> tuple[M02RecipeQuery, ...]:
        return tuple(
            item for item in self.queries if item.role is RecipeDataRole.DIAGNOSTIC_OVERLAY
        )

    @property
    def validation_queries(self) -> tuple[M02RecipeQuery, ...]:
        return tuple(item for item in self.queries if item.role is RecipeDataRole.VALIDATION)


def _query(
    dataset_id: str,
    fields: tuple[str, ...],
    *,
    filters: tuple[FilterSpec, ...] = (),
    role: RecipeDataRole,
) -> M02RecipeQuery:
    diagnostic = _DATASETS[dataset_id].dataset_class is DatasetClass.REJECTED
    return M02RecipeQuery(
        dataset_id=dataset_id,
        fields=fields,
        filters=filters,
        role=role,
        include_non_default=diagnostic or role is RecipeDataRole.VALIDATION,
        include_diagnostics=diagnostic,
    )


def _requirements(recipe_id: str, queries: tuple[M02RecipeQuery, ...]) -> PlotDataRequirements:
    ordered_ids = tuple(
        dict.fromkeys(f"{query.dataset_id}.{field}" for query in queries for field in query.fields)
    )
    fields = tuple(
        RequiredPlotField(
            field_id=field_id,
            minimum_sampling_cadence=_FIELDS[field_id].sampling_cadence,
            unit=_FIELDS[field_id].unit,
            frame=_FIELDS[field_id].frame,
            reference_point=_FIELDS[field_id].reference_point,
            allowed_source_identities=(_FIELDS[field_id].source_identity.value,),
        )
        for field_id in ordered_ids
    )
    return PlotDataRequirements(recipe_id, M02_PLOT_RECIPE_VERSION, fields)


def _recipe(
    recipe_id: str,
    title: str,
    queries: tuple[M02RecipeQuery, ...],
) -> M02PlotRecipe:
    return M02PlotRecipe(
        recipe_id=recipe_id,
        recipe_version=M02_PLOT_RECIPE_VERSION,
        title=title,
        requirements=_requirements(recipe_id, queries),
        queries=queries,
    )


_RESIDUAL_QUERIES = (
    _query(
        ITERATION_TRACES_DATASET,
        (
            "trial_id",
            "point_id",
            "iteration",
            "block_id",
            "raw_norm",
            "raw_unit",
            "tolerance",
            "normalized_norm",
            "merit",
            "linear_residual",
            "line_search_factor",
            "outcome",
        ),
        filters=(
            FilterSpec("iteration", ">=", 0),
            FilterSpec("commit_receipt_id", "!=", ""),
            FilterSpec("accepted_state_advanced", "==", True),
        ),
        role=RecipeDataRole.PHYSICAL,
    ),
    _query(
        REJECTED_ITERATION_TRACES_DATASET,
        (
            "trial_id",
            "point_id",
            "iteration",
            "block_id",
            "raw_norm",
            "raw_unit",
            "tolerance",
            "normalized_norm",
            "merit",
            "linear_residual",
            "line_search_factor",
            "outcome",
        ),
        filters=(
            FilterSpec("iteration", ">=", 0),
            FilterSpec("accepted_state_advanced", "==", False),
        ),
        role=RecipeDataRole.DIAGNOSTIC_OVERLAY,
    ),
    _query(
        RESIDUAL_BLOCK_SUMMARIES_DATASET,
        (
            "point_id",
            "commit_receipt_id",
            "iteration",
            "block_id",
            "raw_norm",
            "raw_unit",
            "tolerance",
            "normalized_norm",
            "merit",
            "hard",
            "passed",
        ),
        filters=(FilterSpec("commit_receipt_id", "!=", ""),),
        role=RecipeDataRole.PHYSICAL,
    ),
)

_STEP_SIZE_QUERIES = (
    _query(
        CONTINUATION_ATTEMPTS_DATASET,
        (
            "trial_id",
            "attempt_index",
            "retry_index",
            "attempted_coordinate",
            "coordinate_unit",
            "requested_step",
            "growth_shrink_reason",
            "event_marker_id",
            "outcome",
            "accepted_state_advanced",
        ),
        filters=(FilterSpec("accepted_state_advanced", "==", False),),
        role=RecipeDataRole.DIAGNOSTIC_OVERLAY,
    ),
    _query(
        ACCEPTED_STEP_NUMERICS_DATASET,
        (
            "point_id",
            "commit_receipt_id",
            "accepted_point_index",
            "attempted_coordinate",
            "accepted_coordinate",
            "coordinate_unit",
            "requested_step",
            "accepted_step",
            "step_reason",
            "retry_count",
            "event_id",
        ),
        filters=(FilterSpec("commit_receipt_id", "!=", ""),),
        role=RecipeDataRole.PHYSICAL,
    ),
)

_EVENT_BRACKET_QUERIES = (
    _query(
        EVENT_PROBES_DATASET,
        (
            "probe_id",
            "channel_id",
            "path_coordinate",
            "coordinate_unit",
            "raw_guard",
            "raw_guard_unit",
            "equilibrium_quality",
            "equilibrium_passed",
            "valid_bracket",
            "event_id",
            "accepted_state_advanced",
        ),
        filters=(
            FilterSpec("equilibrium_passed", "==", True),
            FilterSpec("accepted_state_advanced", "==", False),
        ),
        role=RecipeDataRole.DIAGNOSTIC_OVERLAY,
    ),
    _query(
        EVENT_BRACKETS_DATASET,
        (
            "bracket_id",
            "channel_id",
            "left_coordinate",
            "right_coordinate",
            "coordinate_unit",
            "left_raw_guard",
            "right_raw_guard",
            "raw_guard_unit",
            "root_coordinate",
            "root_method",
            "root_solver_level",
            "position_tolerance",
            "localization_error",
            "direction",
            "simultaneous_tolerance",
            "final_bracket",
            "event_id",
        ),
        filters=(
            FilterSpec("commit_receipt_id", "!=", ""),
            FilterSpec("accepted_state_advanced", "==", False),
        ),
        role=RecipeDataRole.PHYSICAL,
    ),
    _query(
        REJECTED_EVENT_BRACKETS_DATASET,
        (
            "bracket_id",
            "channel_id",
            "left_coordinate",
            "right_coordinate",
            "coordinate_unit",
            "left_raw_guard",
            "right_raw_guard",
            "raw_guard_unit",
            "root_coordinate",
            "root_method",
            "root_solver_level",
            "position_tolerance",
            "localization_error",
            "direction",
            "simultaneous_tolerance",
            "final_bracket",
            "event_id",
        ),
        filters=(FilterSpec("accepted_state_advanced", "==", False),),
        role=RecipeDataRole.DIAGNOSTIC_OVERLAY,
    ),
    _query(
        SIMULTANEOUS_EVENT_GROUPS_DATASET,
        (
            "simultaneous_group_id",
            "event_id",
            "point_id",
            "commit_receipt_id",
            "event_kind",
            "channel_id",
            "path_coordinate",
            "coordinate_unit",
            "simultaneous_tolerance",
        ),
        filters=(FilterSpec("commit_receipt_id", "!=", ""),),
        role=RecipeDataRole.PHYSICAL,
    ),
)

_RELEASE_RECONTACT_QUERIES = (
    _query(
        EVENT_PROBES_DATASET,
        (
            "probe_id",
            "channel_id",
            "path_coordinate",
            "coordinate_unit",
            "raw_guard",
            "raw_guard_unit",
            "release_pose_ref",
            "path_mode",
            "pre_accepted_state_id",
            "post_accepted_state_id",
            "event_id",
            "commit_receipt_id",
            "accepted_state_advanced",
        ),
        filters=(FilterSpec("accepted_state_advanced", "==", False),),
        role=RecipeDataRole.DIAGNOSTIC_OVERLAY,
    ),
    _query(
        SIMULTANEOUS_EVENT_GROUPS_DATASET,
        (
            "simultaneous_group_id",
            "event_id",
            "point_id",
            "commit_receipt_id",
            "event_kind",
            "channel_id",
            "path_coordinate",
            "coordinate_unit",
            "dependency_layer",
        ),
        filters=(
            FilterSpec(
                "event_kind",
                "in",
                ("RELEASE", "RECONTACT", "CONTACT_ESTABLISHED", "RELOAD"),
            ),
            FilterSpec("commit_receipt_id", "!=", ""),
        ),
        role=RecipeDataRole.PHYSICAL,
    ),
    _query(
        CASCADE_ROUNDS_DATASET,
        (
            "cascade_id",
            "event_id",
            "point_id",
            "commit_receipt_id",
            "round_index",
            "state_hash",
            "event_signature_hash",
            "zeno_candidate",
        ),
        filters=(FilterSpec("commit_receipt_id", "!=", ""),),
        role=RecipeDataRole.PHYSICAL,
    ),
)

_REFINEMENT_QUERIES = (
    _query(
        REFINEMENT_STUDIES_DATASET,
        (
            "study_id",
            "sample_id",
            "step_size",
            "event_tolerance",
            "coordinate_unit",
            "m01_lod",
            "root_solver_level",
            "event_position",
            "force_summary_n",
            "work_summary_n_mm",
            "event_position_error",
            "force_relative_error",
            "work_relative_error",
            "observed_order",
            "event_order_matched",
            "passed",
        ),
        role=RecipeDataRole.VALIDATION,
    ),
)

_FAILURE_QUERIES = (
    _query(
        FAILURE_DIAGNOSTICS_DATASET,
        (
            "failure_diagnostic_id",
            "trial_id",
            "failure_family",
            "reason_code",
            "failure_stage",
            "capability_status",
            "design_id",
            "surface_realization_id",
            "footprint_id",
            "last_valid_state_id",
            "path_coordinate",
            "coordinate_unit",
            "wall_time_s",
            "runtime_cost_units",
            "diagnostic_level",
            "denominator_scope",
            "includes_capability_unavailable",
            "accepted_state_advanced",
        ),
        filters=(FilterSpec("accepted_state_advanced", "==", False),),
        role=RecipeDataRole.DIAGNOSTIC_OVERLAY,
    ),
    _query(
        REJECTED_TRIAL_DIAGNOSTICS_DATASET,
        (
            "diagnostic_id",
            "trial_id",
            "failure_family",
            "reason_code",
            "failure_stage",
            "retry_index",
            "last_valid_state_id",
            "diagnostic_level",
            "retryable",
            "accepted_state_advanced",
        ),
        filters=(FilterSpec("accepted_state_advanced", "==", False),),
        role=RecipeDataRole.DIAGNOSTIC_OVERLAY,
    ),
)

RESIDUAL_ITERATIONS_RECIPE = _recipe(
    RESIDUAL_ITERATIONS_RECIPE_ID,
    "Residual iterations",
    _RESIDUAL_QUERIES,
)
STEP_SIZE_RECIPE = _recipe(STEP_SIZE_RECIPE_ID, "Continuation step size", _STEP_SIZE_QUERIES)
EVENT_BRACKET_RECIPE = _recipe(
    EVENT_BRACKET_RECIPE_ID,
    "Event probes and brackets",
    _EVENT_BRACKET_QUERIES,
)
RELEASE_RECONTACT_CHAIN_RECIPE = _recipe(
    RELEASE_RECONTACT_CHAIN_RECIPE_ID,
    "Release-return-recontact lineage",
    _RELEASE_RECONTACT_QUERIES,
)
REFINEMENT_ERROR_RECIPE = _recipe(
    REFINEMENT_ERROR_RECIPE_ID,
    "Refinement error",
    _REFINEMENT_QUERIES,
)
FAILURE_STATISTICS_RECIPE = _recipe(
    FAILURE_STATISTICS_RECIPE_ID,
    "Failure statistics",
    _FAILURE_QUERIES,
)

M02_PLOT_RECIPES = (
    RESIDUAL_ITERATIONS_RECIPE,
    STEP_SIZE_RECIPE,
    EVENT_BRACKET_RECIPE,
    RELEASE_RECONTACT_CHAIN_RECIPE,
    REFINEMENT_ERROR_RECIPE,
    FAILURE_STATISTICS_RECIPE,
)


def m02_plot_recipes() -> tuple[M02PlotRecipe, ...]:
    """Return all six frozen read-only recipe contracts."""

    return M02_PLOT_RECIPES


def m02_plot_recipe_registry() -> MappingProxyType[str, M02PlotRecipe]:
    """Return an immutable recipe lookup keyed by versioned recipe ID."""

    return MappingProxyType({item.recipe_id: item for item in M02_PLOT_RECIPES})


def get_m02_plot_recipe(recipe_id: str) -> M02PlotRecipe:
    """Resolve one recipe without importing plotting or M06 code."""

    try:
        return m02_plot_recipe_registry()[recipe_id]
    except KeyError as error:
        raise KeyError(f"unknown M02 plot-data recipe: {recipe_id}") from error
