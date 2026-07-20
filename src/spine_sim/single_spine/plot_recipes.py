"""Frozen, machine-readable M03 plot-data recipes for later M06 consumers.

This module defines read-only data contracts.  It deliberately has no plotting
dependency, styling policy, smoothing implementation, or interactive UI code.
Accepted raw rows and committed events are enabled by default; rejected trial
diagnostics are exposed only as an explicit opt-in overlay.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
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
from spine_sim.foundation.plot_requirements import PlotDataRequirements, RequiredPlotField
from spine_sim.foundation.reader import FilterSpec
from spine_sim.foundation.registry import DatasetClass

from .contracts import M03_SCHEMA_VERSION
from .result_extension import (
    ACCEPTED_STATE_HISTORY_DATASET,
    COMMITTED_EVENT_PAYLOADS_DATASET,
    CONTACT_CYCLE_RECORDS_DATASET,
    CONTACT_SUPPORT_HISTORY_DATASET,
    REJECTED_DIAGNOSTICS_DATASET,
    RELEASE_OPERATION_HISTORY_DATASET,
    SUPPORT_CANDIDATE_HISTORY_DATASET,
    WORK_LEDGER_DATASET,
    PlotRecipeManifestRecord,
    m03_result_extension,
)

M03_PLOT_RECIPE_VERSION = "1.0.0"

RESPONSE_OVERVIEW_RECIPE_ID = "m03.recipe.response_overview"
STATE_BANDS_RECIPE_ID = "m03.recipe.state_bands"
FIVE_STAGE_FUNNEL_BANDS_RECIPE_ID = "m03.recipe.five_stage_funnel_bands"
LOCAL_GEOMETRY_RECIPE_ID = "m03.recipe.local_geometry"
STRUCTURE_AND_SPRING_RECIPE_ID = "m03.recipe.structure_and_spring"
EVENT_ZOOM_AND_MULTI_PEAK_RECIPE_ID = "m03.recipe.event_zoom_and_multi_peak"
QUALITY_AND_WORK_RECIPE_ID = "m03.recipe.quality_and_work"
PARAMETER_TRENDS_RECIPE_ID = "m03.recipe.parameter_trends"

M03_FROZEN_RECIPE_IDS = (
    RESPONSE_OVERVIEW_RECIPE_ID,
    STATE_BANDS_RECIPE_ID,
    FIVE_STAGE_FUNNEL_BANDS_RECIPE_ID,
    LOCAL_GEOMETRY_RECIPE_ID,
    STRUCTURE_AND_SPRING_RECIPE_ID,
    EVENT_ZOOM_AND_MULTI_PEAK_RECIPE_ID,
    QUALITY_AND_WORK_RECIPE_ID,
    PARAMETER_TRENDS_RECIPE_ID,
)

M03_COMMITTED_EVENT_KINDS = (
    "CONTACT_LOAD_ONSET",
    "FRICTION_BOUNDARY",
    "CONFIRMED_SLIP",
    "SUPPORT_SWITCH",
    "CAP_LOSS",
    "SPRING_ZERO",
    "SPRING_HARD_STOP",
    "RELEASE",
    "SWEPT_COLLISION",
    "RECONTACT",
    "REENGAGEMENT",
    "TRAVEL_COMPLETE",
)

_DESCRIPTOR = m03_result_extension()
_DATASETS = {item.dataset_id: item for item in _DESCRIPTOR.tables}
_FIELDS = {field.field_id: field for dataset in _DESCRIPTOR.tables for field in dataset.fields}


class RecipeDataRole(StrEnum):
    """Isolation role of one recipe query."""

    ACCEPTED_RAW = "ACCEPTED_RAW"
    COMMITTED_EVENT = "COMMITTED_EVENT"
    REJECTED_DIAGNOSTIC = "REJECTED_DIAGNOSTIC"


class FilterStorageKind(StrEnum):
    """How an M06 consumer resolves one logical filter dimension."""

    DIRECT_FIELD = "DIRECT_FIELD"
    JSON_PATH = "JSON_PATH"
    FIELD_METADATA = "FIELD_METADATA"
    CONSUMER_VIEW = "CONSUMER_VIEW"
    DATASET_CLASS = "DATASET_CLASS"


@dataclass(frozen=True, slots=True)
class M03FilterDimension:
    """Machine-readable logical-to-storage mapping for one filter dimension."""

    filter_id: str
    storage_kind: FilterStorageKind
    source_field_id: str | None
    value_path: str | None
    unit: str
    operators: tuple[str, ...] = ("==", "in")
    allowed_values: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.filter_id:
            raise ValueError("filter IDs cannot be empty")
        if self.storage_kind in {FilterStorageKind.DIRECT_FIELD, FilterStorageKind.JSON_PATH}:
            if self.source_field_id not in _FIELDS:
                raise ValueError(f"filter source field is not registered: {self.source_field_id}")
        elif self.source_field_id is not None and self.source_field_id not in _FIELDS:
            raise ValueError(f"filter metadata field is not registered: {self.source_field_id}")
        if self.storage_kind is FilterStorageKind.JSON_PATH and not self.value_path:
            raise ValueError("JSON-path filters require a value path")
        if not self.operators:
            raise ValueError("filter dimensions require at least one operator")


_REQUEST_PAYLOAD = "m03.run_requests.resolved_request_payload"


def _direct(filter_id: str, field_id: str, unit: str = "1") -> M03FilterDimension:
    return M03FilterDimension(
        filter_id,
        FilterStorageKind.DIRECT_FIELD,
        field_id,
        None,
        unit,
    )


def _json(filter_id: str, value_path: str, unit: str = "1") -> M03FilterDimension:
    return M03FilterDimension(
        filter_id,
        FilterStorageKind.JSON_PATH,
        _REQUEST_PAYLOAD,
        value_path,
        unit,
    )


def _view(filter_id: str, allowed_values: tuple[str, ...]) -> M03FilterDimension:
    return M03FilterDimension(
        filter_id,
        FilterStorageKind.CONSUMER_VIEW,
        None,
        None,
        "1",
        allowed_values=allowed_values,
    )


M03_FILTER_CONTRACT = (
    _json("surface_family", "surface.family"),
    _direct("surface_realization_id", f"{ACCEPTED_STATE_HISTORY_DATASET}.surface_realization_id"),
    _json("surface_seed", "surface.seed"),
    _json("surface_scale", "surface.scale_mm", "mm"),
    _direct("case_id", f"{ACCEPTED_STATE_HISTORY_DATASET}.case_id"),
    _json("design_id", "design_id"),
    _json("Rt", "parameter_bundle.needle.tip_radius_mm", "mm"),
    _json("d", "parameter_bundle.needle.diameter_mm", "mm"),
    _json("L", "parameter_bundle.needle.exposed_length_mm", "mm"),
    _json("alpha", "parameter_bundle.needle.alpha_rad", "rad"),
    _json("beta", "parameter_bundle.needle.beta_rad", "rad"),
    _json("E", "parameter_bundle.beam.youngs_modulus_mpa", "MPa"),
    _json("nu", "parameter_bundle.beam.poisson_ratio"),
    _json("mu", "parameter_bundle.contact.friction_coefficient"),
    _json("bending", "parameter_bundle.beam.bending_enabled"),
    _json("mount", "parameter_bundle.mount.mode"),
    _json("ks", "parameter_bundle.mount.spring_stiffness_n_per_mm", "N/mm"),
    _direct("spring_state", f"{ACCEPTED_STATE_HISTORY_DATASET}.spring_state"),
    _direct(
        "primary_mechanical_state",
        f"{ACCEPTED_STATE_HISTORY_DATASET}.primary_mechanical_state",
    ),
    _direct("contact_motion_state", f"{CONTACT_SUPPORT_HISTORY_DATASET}.motion_state"),
    _direct("operation_phase", f"{ACCEPTED_STATE_HISTORY_DATASET}.operation_phase"),
    _direct("geometric_candidate", f"{ACCEPTED_STATE_HISTORY_DATASET}.geometric_candidate"),
    _direct("loaded_contact", f"{ACCEPTED_STATE_HISTORY_DATASET}.loaded_contact"),
    _direct("frictionally_stable", f"{ACCEPTED_STATE_HISTORY_DATASET}.frictionally_stable"),
    _direct("load_bearing", f"{ACCEPTED_STATE_HISTORY_DATASET}.load_bearing"),
    _direct("cycle_id", f"{ACCEPTED_STATE_HISTORY_DATASET}.cycle_id"),
    _direct("event_kind", f"{COMMITTED_EVENT_PAYLOADS_DATASET}.event_kind"),
    M03FilterDimension(
        "frame",
        FilterStorageKind.FIELD_METADATA,
        f"{ACCEPTED_STATE_HISTORY_DATASET}.wrench_a_on_b_global_at_o_n_n_mm",
        "frame",
        "1",
    ),
    M03FilterDimension(
        "reference_point",
        FilterStorageKind.FIELD_METADATA,
        f"{ACCEPTED_STATE_HISTORY_DATASET}.wrench_a_on_b_global_at_o_n_n_mm",
        "reference_point",
        "1",
    ),
    _direct("task_direction", f"{ACCEPTED_STATE_HISTORY_DATASET}.task_direction_global"),
    M03FilterDimension(
        "source_class",
        FilterStorageKind.DATASET_CLASS,
        None,
        None,
        "1",
        allowed_values=("accepted", "committed_event", "rejected"),
    ),
    _direct("maturity", f"{ACCEPTED_STATE_HISTORY_DATASET}.maturity"),
    _direct("source_identity", f"{ACCEPTED_STATE_HISTORY_DATASET}.source_identity"),
    _direct("certification_status", f"{ACCEPTED_STATE_HISTORY_DATASET}.certification_status"),
    _direct("capability_status", "m03.capability_status.capability_state"),
    _view("x_or_t_view", ("x_total_mm", "drag_elapsed_time_s")),
    _view("global_or_local_component_view", ("GLOBAL", "NEEDLE_LOCAL")),
)


@dataclass(frozen=True, slots=True)
class M03RecipeQuery:
    """One projection/filter request accepted directly by ``ResultReader.query``."""

    dataset_id: str
    fields: tuple[str, ...]
    filters: tuple[FilterSpec, ...]
    role: RecipeDataRole
    enabled_by_default: bool
    include_non_default: bool
    include_diagnostics: bool

    def __post_init__(self) -> None:
        dataset = _DATASETS.get(self.dataset_id)
        if dataset is None:
            raise ValueError(f"unknown M03 recipe dataset: {self.dataset_id}")
        local_fields = {item.field_id.rsplit(".", 1)[-1] for item in dataset.fields}
        missing = (set(self.fields) | {item.field for item in self.filters}) - local_fields
        if missing:
            raise ValueError(
                f"recipe query references unknown fields in {self.dataset_id}: {sorted(missing)}"
            )
        expected_class = {
            RecipeDataRole.ACCEPTED_RAW: DatasetClass.ACCEPTED,
            RecipeDataRole.COMMITTED_EVENT: DatasetClass.EVENT,
            RecipeDataRole.REJECTED_DIAGNOSTIC: DatasetClass.REJECTED,
        }[self.role]
        if dataset.dataset_class is not expected_class:
            raise ValueError("M03 recipe query role disagrees with dataset isolation class")
        if self.role is RecipeDataRole.REJECTED_DIAGNOSTIC:
            if self.enabled_by_default or not self.include_diagnostics:
                raise ValueError("rejected diagnostic queries must be disabled and opt-in")
        elif not self.enabled_by_default or self.include_diagnostics:
            raise ValueError("accepted/event queries must be enabled without diagnostics")


@dataclass(frozen=True, slots=True)
class M03PlotRecipe:
    """Complete frozen field, source, grouping, and filter contract for one family."""

    recipe_id: str
    recipe_family: str
    recipe_version: str
    title: str
    requirements: PlotDataRequirements
    queries: tuple[M03RecipeQuery, ...]
    grouping_fields: tuple[str, ...]
    filter_contract: tuple[M03FilterDimension, ...]
    event_kinds: tuple[str, ...]
    axis_contract: tuple[str, ...]
    semantic_contract: tuple[str, ...]
    smoothing: str = "NONE"
    read_only: bool = True
    rejected_opt_in: bool = True

    def __post_init__(self) -> None:
        if not self.recipe_id.startswith("m03.recipe."):
            raise ValueError("M03 recipe IDs must use the m03.recipe namespace")
        if self.recipe_version != M03_PLOT_RECIPE_VERSION:
            raise ValueError("unsupported M03 plot recipe version")
        if self.requirements.recipe_id != self.recipe_id:
            raise ValueError("plot requirements and recipe identity disagree")
        if not self.read_only or self.smoothing != "NONE":
            raise ValueError("M03 recipes are read-only and unsmoothed")
        query_fields = {
            f"{query.dataset_id}.{field}" for query in self.queries for field in query.fields
        }
        required_fields = {item.field_id for item in self.requirements.fields}
        if query_fields != required_fields:
            raise ValueError("recipe requirements must exactly cover projected query fields")
        defaults = self.default_queries
        if not defaults or not any(item.role is RecipeDataRole.ACCEPTED_RAW for item in defaults):
            raise ValueError("every M03 family requires accepted raw data")
        if not any(item.role is RecipeDataRole.COMMITTED_EVENT for item in defaults):
            raise ValueError("every M03 family requires committed-event markers")
        if not self.diagnostic_queries or not self.rejected_opt_in:
            raise ValueError("every M03 family must expose rejected rows only as opt-in")
        if {item.filter_id for item in self.filter_contract} != {
            item.filter_id for item in M03_FILTER_CONTRACT
        }:
            raise ValueError("M03 recipes must publish the complete frozen filter contract")

    @property
    def default_queries(self) -> tuple[M03RecipeQuery, ...]:
        return tuple(item for item in self.queries if item.enabled_by_default)

    @property
    def diagnostic_queries(self) -> tuple[M03RecipeQuery, ...]:
        return tuple(
            item for item in self.queries if item.role is RecipeDataRole.REJECTED_DIAGNOSTIC
        )

    @property
    def default_dataset_classes(self) -> tuple[str, ...]:
        return ("accepted", "event")

    @property
    def raw_dataset_links(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(item.dataset_id for item in self.default_queries))

    @property
    def definition_hash(self) -> str:
        return semantic_hash(
            {
                "recipe_id": self.recipe_id,
                "recipe_family": self.recipe_family,
                "recipe_version": self.recipe_version,
                "queries": tuple(
                    {
                        "dataset_id": item.dataset_id,
                        "fields": item.fields,
                        "filters": tuple(
                            (spec.field, spec.operator, spec.value) for spec in item.filters
                        ),
                        "role": item.role.value,
                        "enabled_by_default": item.enabled_by_default,
                    }
                    for item in self.queries
                ),
                "grouping_fields": self.grouping_fields,
                "filter_contract": tuple(
                    (
                        item.filter_id,
                        item.storage_kind.value,
                        item.source_field_id,
                        item.value_path,
                        item.unit,
                        item.operators,
                        item.allowed_values,
                    )
                    for item in self.filter_contract
                ),
                "field_contract": tuple(
                    (
                        item.field_id,
                        item.minimum_sampling_cadence,
                        item.unit,
                        item.frame,
                        item.reference_point,
                        item.allowed_source_identities,
                    )
                    for item in self.requirements.fields
                ),
                "event_kinds": self.event_kinds,
                "axis_contract": self.axis_contract,
                "semantic_contract": self.semantic_contract,
                "smoothing": self.smoothing,
                "rejected_opt_in": self.rejected_opt_in,
            }
        )

    def manifest_payload(self) -> dict[str, Any]:
        """Return a canonical JSON-compatible recipe payload."""

        return {
            "title": self.title,
            "default_dataset_classes": self.default_dataset_classes,
            "queries": tuple(
                {
                    "dataset_id": item.dataset_id,
                    "fields": item.fields,
                    "filters": tuple(
                        {"field": spec.field, "operator": spec.operator, "value": spec.value}
                        for spec in item.filters
                    ),
                    "role": item.role.value,
                    "enabled_by_default": item.enabled_by_default,
                    "include_non_default": item.include_non_default,
                    "include_diagnostics": item.include_diagnostics,
                }
                for item in self.queries
            ),
            "filter_contract": tuple(
                {
                    "filter_id": item.filter_id,
                    "storage_kind": item.storage_kind.value,
                    "source_field_id": item.source_field_id,
                    "value_path": item.value_path,
                    "unit": item.unit,
                    "operators": item.operators,
                    "allowed_values": item.allowed_values,
                }
                for item in self.filter_contract
            ),
            "field_contracts": tuple(
                {
                    "field_id": item.field_id,
                    "minimum_sampling_cadence": item.minimum_sampling_cadence,
                    "unit": item.unit,
                    "frame": item.frame,
                    "reference_point": item.reference_point,
                    "allowed_source_identities": item.allowed_source_identities,
                }
                for item in self.requirements.fields
            ),
            "axis_contract": self.axis_contract,
            "semantic_contract": self.semantic_contract,
            "recipe_definition_hash": self.definition_hash,
            "resolved_config_hash": "REQUIRED_AT_RENDER_TIME",
            "data_query_hash": "REQUIRED_AT_RENDER_TIME",
            "raw_curve_visible": True,
            "derived_curve_policy": "ALGORITHM_AND_PARAMETERS_REQUIRED; RAW_REMAINS_VISIBLE",
            "continuous_coordinate_policy": "NO_RESET_AFTER_RELEASE_RECONTACT_OR_NEW_CYCLE",
            "committed_event_markers_only": True,
            "failure_hold_unavailable_policy": "SHOW_STATUS; DO_NOT_INTERPOLATE",
        }


def _query(
    dataset_id: str,
    fields: tuple[str, ...],
    *,
    role: RecipeDataRole,
) -> M03RecipeQuery:
    diagnostic = role is RecipeDataRole.REJECTED_DIAGNOSTIC
    filters = (
        (FilterSpec("accepted_state_advanced", "==", False),)
        if diagnostic
        else (FilterSpec("commit_receipt_id", "!=", ""),)
    )
    return M03RecipeQuery(
        dataset_id=dataset_id,
        fields=fields,
        filters=filters,
        role=role,
        enabled_by_default=not diagnostic,
        include_non_default=diagnostic,
        include_diagnostics=diagnostic,
    )


def _requirements(recipe_id: str, queries: tuple[M03RecipeQuery, ...]) -> PlotDataRequirements:
    field_ids = tuple(
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
        for field_id in field_ids
    )
    return PlotDataRequirements(recipe_id, M03_PLOT_RECIPE_VERSION, fields)


_REJECTED_OVERLAY = _query(
    REJECTED_DIAGNOSTICS_DATASET,
    (
        "run_id",
        "case_id",
        "trial_id",
        "attempt_kind",
        "reason_family",
        "reason_code",
        "failure_axis",
        "raw_residual",
        "raw_residual_unit",
        "raw_guard",
        "raw_guard_unit",
        "surface_quality",
        "accepted_state_advanced",
        "path_advanced",
        "time_advanced",
        "work_advanced",
        "cycle_advanced",
        "event_history_advanced",
        "source_identity",
        "maturity",
        "certification_status",
    ),
    role=RecipeDataRole.REJECTED_DIAGNOSTIC,
)

_EVENT_MARKERS = _query(
    COMMITTED_EVENT_PAYLOADS_DATASET,
    (
        "run_id",
        "case_id",
        "event_id",
        "commit_receipt_id",
        "event_kind",
        "path_coordinate_mm",
        "cycle_id",
        "support_ids",
        "pre_beam_energy_n_mm",
        "post_beam_energy_n_mm",
        "pre_spring_energy_n_mm",
        "post_spring_energy_n_mm",
        "remaining_stored_energy_n_mm",
        "released_recoverable_energy_n_mm",
        "source_identity",
        "maturity",
        "certification_status",
    ),
    role=RecipeDataRole.COMMITTED_EVENT,
)


def _recipe(
    recipe_id: str,
    family: str,
    title: str,
    physical_queries: tuple[M03RecipeQuery, ...],
    *,
    grouping_fields: tuple[str, ...],
    axis_contract: tuple[str, ...],
    semantic_contract: tuple[str, ...],
    event_kinds: tuple[str, ...] = M03_COMMITTED_EVENT_KINDS,
) -> M03PlotRecipe:
    queries = (*physical_queries, _EVENT_MARKERS, _REJECTED_OVERLAY)
    return M03PlotRecipe(
        recipe_id=recipe_id,
        recipe_family=family,
        recipe_version=M03_PLOT_RECIPE_VERSION,
        title=title,
        requirements=_requirements(recipe_id, queries),
        queries=queries,
        grouping_fields=grouping_fields,
        filter_contract=M03_FILTER_CONTRACT,
        event_kinds=event_kinds,
        axis_contract=axis_contract,
        semantic_contract=semantic_contract,
    )


_RESPONSE_ACCEPTED = _query(
    ACCEPTED_STATE_HISTORY_DATASET,
    (
        "run_id",
        "case_id",
        "point_id",
        "commit_receipt_id",
        "accepted_point_index",
        "x_total_mm",
        "drag_elapsed_time_s",
        "operation_phase",
        "cycle_id",
        "wrench_a_on_b_global_at_o_n_n_mm",
        "grip_resistance_rx_n",
        "beam_tip_translation_global_mm",
        "beam_tip_translation_needle_mm",
        "task_direction_global",
        "reference_point_id",
        "source_identity",
        "maturity",
        "certification_status",
    ),
    role=RecipeDataRole.ACCEPTED_RAW,
)

_STATE_ACCEPTED = _query(
    ACCEPTED_STATE_HISTORY_DATASET,
    (
        "run_id",
        "case_id",
        "point_id",
        "commit_receipt_id",
        "x_total_mm",
        "drag_elapsed_time_s",
        "cycle_id",
        "primary_mechanical_state",
        "operation_phase",
        "contact_motion_states",
        "active_support_ids",
        "spring_state",
        "source_identity",
        "maturity",
        "certification_status",
    ),
    role=RecipeDataRole.ACCEPTED_RAW,
)

_FIVE_STAGE_ACCEPTED = _query(
    ACCEPTED_STATE_HISTORY_DATASET,
    (
        "run_id",
        "case_id",
        "point_id",
        "commit_receipt_id",
        "x_total_mm",
        "drag_elapsed_time_s",
        "cycle_id",
        "geometric_candidate",
        "loaded_contact",
        "frictionally_stable",
        "load_bearing",
        "five_stage_reason_codes",
        "five_stage_evidence_refs",
        "source_identity",
        "maturity",
        "certification_status",
    ),
    role=RecipeDataRole.ACCEPTED_RAW,
)

_LOCAL_GEOMETRY_ACCEPTED = _query(
    ACCEPTED_STATE_HISTORY_DATASET,
    (
        "run_id",
        "case_id",
        "point_id",
        "commit_receipt_id",
        "x_total_mm",
        "cycle_id",
        "parameter_bundle_id",
        "surface_realization_id",
        "query_receipt_id",
        "root_position_global_mm",
        "tip_center_global_mm",
        "a_t_global",
        "task_direction_global",
        "active_candidate_ids",
        "active_support_ids",
        "full_body_minimum_clearance_mm",
        "cone_clearance_mm",
        "shaft_clearance_mm",
        "mount_clearance_mm",
        "source_identity",
        "maturity",
        "certification_status",
    ),
    role=RecipeDataRole.ACCEPTED_RAW,
)

_LOCAL_CANDIDATES = _query(
    SUPPORT_CANDIDATE_HISTORY_DATASET,
    (
        "run_id",
        "case_id",
        "point_id",
        "commit_receipt_id",
        "candidate_id",
        "support_id",
        "candidate_point_global_mm",
        "normal_global",
        "tangent_1_global",
        "tangent_2_global",
        "cap_margin_mm",
        "finite_cap_legal",
        "coverage_certified",
        "nonsmooth",
        "nonunique",
        "rejection_reason",
    ),
    role=RecipeDataRole.ACCEPTED_RAW,
)

_LOCAL_CONTACTS = _query(
    CONTACT_SUPPORT_HISTORY_DATASET,
    (
        "run_id",
        "case_id",
        "point_id",
        "commit_receipt_id",
        "support_id",
        "active",
        "point_global_mm",
        "normal_global",
        "tangent_1_global",
        "tangent_2_global",
        "motion_state",
    ),
    role=RecipeDataRole.ACCEPTED_RAW,
)

_STRUCTURE_ACCEPTED = _query(
    ACCEPTED_STATE_HISTORY_DATASET,
    (
        "run_id",
        "case_id",
        "point_id",
        "commit_receipt_id",
        "x_total_mm",
        "drag_elapsed_time_s",
        "cycle_id",
        "beam_tip_translation_global_mm",
        "beam_tip_rotation_global_rad",
        "beam_tip_translation_needle_mm",
        "beam_tip_rotation_needle_rad",
        "beam_root_force_global_n",
        "beam_root_moment_global_n_mm",
        "section_resultants_needle_n_n_mm",
        "beam_energy_n_mm",
        "spring_state",
        "spring_compression_mm",
        "spring_remaining_travel_mm",
        "spring_force_n",
        "spring_hard_stop_reaction_n",
        "spring_energy_n_mm",
        "source_identity",
        "maturity",
        "certification_status",
    ),
    role=RecipeDataRole.ACCEPTED_RAW,
)

_EVENT_ZOOM_ACCEPTED = _query(
    ACCEPTED_STATE_HISTORY_DATASET,
    (
        "run_id",
        "case_id",
        "point_id",
        "commit_receipt_id",
        "accepted_point_index",
        "x_total_mm",
        "drag_elapsed_time_s",
        "cycle_id",
        "event_sequence",
        "grip_resistance_rx_n",
        "wrench_a_on_b_global_at_o_n_n_mm",
        "primary_mechanical_state",
        "contact_motion_states",
        "source_identity",
        "maturity",
        "certification_status",
    ),
    role=RecipeDataRole.ACCEPTED_RAW,
)

_EVENT_ZOOM_PAYLOAD = _query(
    COMMITTED_EVENT_PAYLOADS_DATASET,
    (
        "run_id",
        "case_id",
        "event_id",
        "commit_receipt_id",
        "event_kind",
        "raw_signed_guard",
        "raw_guard_unit",
        "bracket_ref",
        "probe_refs",
        "earliestness_ref",
        "path_coordinate_mm",
        "cycle_id",
        "pre_wrench_global_at_o_n_n_mm",
        "event_wrench_global_at_o_n_n_mm",
        "post_wrench_global_at_o_n_n_mm",
        "remaining_stored_energy_n_mm",
        "released_recoverable_energy_n_mm",
        "one_sided_consistency",
    ),
    role=RecipeDataRole.COMMITTED_EVENT,
)

_RELEASE_OPERATIONS = _query(
    RELEASE_OPERATION_HISTORY_DATASET,
    (
        "run_id",
        "case_id",
        "point_id",
        "commit_receipt_id",
        "event_id",
        "cycle_id",
        "operation_phase",
        "segment_id",
        "path_coordinate_mm",
        "x_total_mm",
        "signed_guard_payloads",
        "quality_gate_passed",
        "termination_kind",
        "lifecycle_kind",
        "remaining_stored_energy_n_mm",
    ),
    role=RecipeDataRole.COMMITTED_EVENT,
)

_CYCLES = _query(
    CONTACT_CYCLE_RECORDS_DATASET,
    (
        "run_id",
        "case_id",
        "cycle_id",
        "commit_receipt_id",
        "lifecycle_kind",
        "start_point_id",
        "end_point_id",
        "release_event_id",
        "recontact_event_id",
        "reengagement_event_id",
        "start_x_total_mm",
        "end_x_total_mm",
        "right_censored",
    ),
    role=RecipeDataRole.COMMITTED_EVENT,
)

_QUALITY_ACCEPTED = _query(
    ACCEPTED_STATE_HISTORY_DATASET,
    (
        "run_id",
        "case_id",
        "point_id",
        "commit_receipt_id",
        "x_total_mm",
        "drag_elapsed_time_s",
        "cycle_id",
        "query_lod_purpose",
        "query_error_bound_mm",
        "query_quality",
        "query_domain_status",
        "query_nonsmooth",
        "query_nonunique",
        "quality_solve_state",
        "residual_block_payloads",
        "complementarity_residual",
        "contact_soc_residual",
        "graph_residual",
        "jacobian_quality",
        "beam_energy_n_mm",
        "spring_energy_n_mm",
        "source_identity",
        "maturity",
        "certification_status",
    ),
    role=RecipeDataRole.ACCEPTED_RAW,
)

_WORK_ACCEPTED = _query(
    WORK_LEDGER_DATASET,
    (
        "run_id",
        "case_id",
        "start_point_id",
        "end_point_id",
        "commit_receipt_id",
        "accepted_interval_index",
        "base_or_actuator_input_work_n_mm",
        "delta_beam_energy_n_mm",
        "delta_spring_energy_n_mm",
        "friction_dissipation_n_mm",
        "returned_recoverable_energy_n_mm",
        "remaining_stored_energy_n_mm",
        "closure_error_n_mm",
        "normalized_closure_error",
        "cumulative_input_work_n_mm",
        "cumulative_friction_dissipation_n_mm",
        "cumulative_returned_energy_n_mm",
    ),
    role=RecipeDataRole.ACCEPTED_RAW,
)

_TRENDS_ACCEPTED = _query(
    ACCEPTED_STATE_HISTORY_DATASET,
    (
        "run_id",
        "case_id",
        "point_id",
        "commit_receipt_id",
        "parameter_bundle_id",
        "surface_realization_id",
        "x_total_mm",
        "drag_elapsed_time_s",
        "cycle_id",
        "grip_resistance_rx_n",
        "wrench_a_on_b_global_at_o_n_n_mm",
        "loaded_contact",
        "load_bearing",
        "spring_state",
        "source_identity",
        "maturity",
        "certification_status",
    ),
    role=RecipeDataRole.ACCEPTED_RAW,
)

RESPONSE_OVERVIEW_RECIPE = _recipe(
    RESPONSE_OVERVIEW_RECIPE_ID,
    "response_overview",
    "Response overview",
    (_RESPONSE_ACCEPTED,),
    grouping_fields=("case_id", "cycle_id"),
    axis_contract=("x_total_mm", "drag_elapsed_time_s", "Rx", "uz", "six_component_wrench"),
    semantic_contract=(
        "WRENCH_DIRECTION=A_ON_B",
        "WRENCH_REFERENCE=M03_BASE_REFERENCE_O",
        "FULL_FX_FY_FZ_MX_MY_MZ_REQUIRED",
    ),
)

STATE_BANDS_RECIPE = _recipe(
    STATE_BANDS_RECIPE_ID,
    "state_bands",
    "State bands",
    (_STATE_ACCEPTED,),
    grouping_fields=("case_id", "cycle_id"),
    axis_contract=("x_total_mm", "drag_elapsed_time_s"),
    semantic_contract=(
        "PRIMARY_OPERATION_CONTACT_AND_SPRING_STATES_REMAIN_ORTHOGONAL",
        "ACTIVE_SUPPORT_COUNT_DERIVED_FROM_ACTIVE_SUPPORT_IDS",
    ),
)

FIVE_STAGE_FUNNEL_BANDS_RECIPE = _recipe(
    FIVE_STAGE_FUNNEL_BANDS_RECIPE_ID,
    "five_stage_funnel_bands",
    "Five-stage funnel bands",
    (_FIVE_STAGE_ACCEPTED,),
    grouping_fields=("case_id", "cycle_id"),
    axis_contract=("x_total_mm", "drag_elapsed_time_s", "four_independent_binary_lanes"),
    semantic_contract=(
        "SOURCE_IDENTITY=PROPOSED_SUPPLEMENT",
        "NO_SYNTHETIC_ENGAGED_LANE",
        "RECONTACT_DOES_NOT_IMPLY_REENGAGEMENT",
    ),
)

LOCAL_GEOMETRY_RECIPE = _recipe(
    LOCAL_GEOMETRY_RECIPE_ID,
    "local_geometry",
    "Local geometry",
    (_LOCAL_GEOMETRY_ACCEPTED, _LOCAL_CANDIDATES, _LOCAL_CONTACTS),
    grouping_fields=("case_id", "cycle_id", "point_id"),
    axis_contract=("GLOBAL_3D_AT_SELECTED_ACCEPTED_POINT_OR_COMMITTED_EVENT",),
    semantic_contract=(
        "SHOW_SURFACE_SUPPORT_NORMAL_TANGENTS_NEEDLE_BODY_AND_TASK_DIRECTION",
        "SHOW_FINITE_CAP_AND_FULL_BODY_CLEARANCE",
        "M01_SLOPE_MUST_NOT_BE_LABELLED_ENGAGEMENT",
    ),
)

STRUCTURE_AND_SPRING_RECIPE = _recipe(
    STRUCTURE_AND_SPRING_RECIPE_ID,
    "structure_and_spring",
    "Structure and spring",
    (_STRUCTURE_ACCEPTED,),
    grouping_fields=("case_id", "cycle_id"),
    axis_contract=("x_total_mm", "drag_elapsed_time_s", "GLOBAL_AND_NEEDLE_LOCAL_COMPONENTS"),
    semantic_contract=(
        "TIP_TRANSLATION_ROTATION_COMPONENTS_AND_NORMS",
        "ROOT_RESULTANTS_WITHOUT_STRENGTH_INFERENCE",
        "RELEASE_REMAINING_STORED_ENERGY_MARKER",
    ),
)

EVENT_ZOOM_AND_MULTI_PEAK_RECIPE = _recipe(
    EVENT_ZOOM_AND_MULTI_PEAK_RECIPE_ID,
    "event_zoom_and_multi_peak",
    "Event zoom and multi-peak",
    (_EVENT_ZOOM_ACCEPTED, _EVENT_ZOOM_PAYLOAD, _RELEASE_OPERATIONS, _CYCLES),
    grouping_fields=("case_id", "cycle_id", "event_kind"),
    axis_contract=("UNRESET_X_TOTAL", "UNRESET_DRAG_ELAPSED_TIME", "RAW_PRE_EVENT_POST"),
    semantic_contract=(
        "NO_SMOOTHING",
        "PEAKS_KEEP_POINT_LEVEL_RAW_LINKS",
        "RELEASE_SWEEP_RECONTACT_REENGAGEMENT_LINEAGE",
    ),
)

QUALITY_AND_WORK_RECIPE = _recipe(
    QUALITY_AND_WORK_RECIPE_ID,
    "quality_and_work",
    "Quality and work",
    (_QUALITY_ACCEPTED, _WORK_ACCEPTED),
    grouping_fields=("case_id", "cycle_id"),
    axis_contract=("x_total_mm", "drag_elapsed_time_s", "accepted_interval_index"),
    semantic_contract=(
        "RAW_AND_NORMALIZED_RESIDUALS",
        "QUERY_AND_LOD_QUALITY",
        "WORK_CLOSURE_ENERGIES_DISSIPATION_AND_RETURNED_ENERGY",
    ),
)

PARAMETER_TRENDS_RECIPE = _recipe(
    PARAMETER_TRENDS_RECIPE_ID,
    "parameter_trends",
    "Parameter trends",
    (_TRENDS_ACCEPTED,),
    grouping_fields=("surface_realization_id", "Rt", "d", "alpha", "mu", "ks"),
    axis_contract=("PAIRED_RAW_COMPARISON_ON_COMMON_SURFACE_REALIZATION_AND_PATH",),
    semantic_contract=(
        "FACET_BY_PARAMETER_FAMILY",
        "NO_SINGLE_AGGREGATE_RANKING",
        "E_NU_BENDING_AND_MOUNT_ARE_TECHNICAL_FILTERS",
    ),
)

M03_PLOT_RECIPES = (
    RESPONSE_OVERVIEW_RECIPE,
    STATE_BANDS_RECIPE,
    FIVE_STAGE_FUNNEL_BANDS_RECIPE,
    LOCAL_GEOMETRY_RECIPE,
    STRUCTURE_AND_SPRING_RECIPE,
    EVENT_ZOOM_AND_MULTI_PEAK_RECIPE,
    QUALITY_AND_WORK_RECIPE,
    PARAMETER_TRENDS_RECIPE,
)


def m03_plot_recipes() -> tuple[M03PlotRecipe, ...]:
    """Return the exact eight frozen M03 recipe families."""

    return M03_PLOT_RECIPES


def m03_plot_recipe_registry() -> MappingProxyType[str, M03PlotRecipe]:
    """Return an immutable lookup by versioned recipe ID."""

    return MappingProxyType({item.recipe_id: item for item in M03_PLOT_RECIPES})


def get_m03_plot_recipe(recipe_id: str) -> M03PlotRecipe:
    """Resolve one recipe without importing an M06 or plotting implementation."""

    try:
        return m03_plot_recipe_registry()[recipe_id]
    except KeyError as error:
        raise KeyError(f"unknown M03 plot-data recipe: {recipe_id}") from error


def _manifest_status() -> StatusTuple:
    return StatusTuple(
        value_presence=ValuePresence.PRESENT,
        capability_status=CapabilityStatus.SUPPORTED,
        attempt_outcome=AttemptOutcome.ACCEPTED,
        physical_feasibility=PhysicalFeasibility.NOT_ASSESSED,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        reason_code="M03_MACHINE_READABLE_PLOT_RECIPE",
        explanation="Read-only recipe contract; no physical or certification claim.",
    )


def build_plot_recipe_manifest_records(
    *,
    run_id: str,
    case_id: str,
    source_identity: SourceIdentity = SourceIdentity.DEV_POLICY,
    maturity: Maturity | None = None,
) -> tuple[PlotRecipeManifestRecord, ...]:
    """Materialize all recipe contracts as versioned M00 summary records."""

    resolved_maturity = maturity or Maturity.validation_only_implemented()
    records: list[PlotRecipeManifestRecord] = []
    for recipe in M03_PLOT_RECIPES:
        payload = recipe.manifest_payload()
        recipe_source_identity = (
            SourceIdentity.PROPOSED_SUPPLEMENT
            if recipe.recipe_id == FIVE_STAGE_FUNNEL_BANDS_RECIPE_ID
            else source_identity
        )
        summary_id = stable_content_id(
            "m03-plot-recipe-manifest",
            {
                "run_id": run_id,
                "case_id": case_id,
                "recipe_id": recipe.recipe_id,
                "definition_hash": recipe.definition_hash,
            },
        )
        records.append(
            PlotRecipeManifestRecord(
                run_id=run_id,
                case_id=case_id,
                schema_version=M03_SCHEMA_VERSION,
                status=_manifest_status(),
                source_identity=recipe_source_identity,
                maturity=resolved_maturity,
                certification_status=CertificationStatus.NOT_CERTIFIABLE,
                summary_id=summary_id,
                summary_kind="M03_PLOT_RECIPE_MANIFEST",
                included_dataset_classes=("accepted", "event"),
                recipe_id=recipe.recipe_id,
                recipe_family=recipe.recipe_family,
                recipe_version=recipe.recipe_version,
                definition_hash=recipe.definition_hash,
                field_ids=tuple(item.field_id for item in recipe.requirements.fields),
                grouping_fields=recipe.grouping_fields,
                filter_fields=tuple(item.filter_id for item in recipe.filter_contract),
                event_kinds=recipe.event_kinds,
                raw_dataset_links=recipe.raw_dataset_links,
                rejected_opt_in=recipe.rejected_opt_in,
                smoothing=recipe.smoothing,
                missing_data_policy="SHOW_FAILURE_HOLD_UNAVAILABLE_STATUS; DO_NOT_INTERPOLATE",
                recipe_payload=payload,
            )
        )
    return tuple(records)
