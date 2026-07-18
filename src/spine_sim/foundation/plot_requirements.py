"""Read-only plot-data requirement checks and complete gap request records."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

from .canonical import semantic_hash


@dataclass(frozen=True, slots=True)
class RequiredPlotField:
    field_id: str
    minimum_sampling_cadence: str
    unit: str
    frame: str
    reference_point: str
    allowed_source_identities: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PlotDataRequirements:
    recipe_id: str
    recipe_version: str
    fields: tuple[RequiredPlotField, ...]


@dataclass(frozen=True, slots=True)
class PlotRequirementDeficiency:
    field_id: str
    code: str
    explanation: str
    expected: dict[str, Any]
    actual: dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class PlotRequirementsReport:
    recipe_id: str
    satisfied: bool
    deficiencies: tuple[PlotRequirementDeficiency, ...]


@dataclass(frozen=True, slots=True)
class PlotDataGapRequest:
    request_id: str
    requesting_recipe: str
    owning_source_module: str
    missing_field_semantics: tuple[dict[str, Any], ...]
    why_existing_fields_are_insufficient: tuple[str, ...]
    entity_path_event_indexing: tuple[str, ...]
    data_type_and_shape: tuple[str, ...]
    unit_frame_reference_point: tuple[str, ...]
    required_sampling_cadence: tuple[str, ...]
    raw_or_derived_classification: str
    estimated_storage_cost: str
    additive_or_breaking_schema_change: str
    backward_compatibility_expectation: str
    validation_plot_or_test: str

    @classmethod
    def from_report(
        cls,
        report: PlotRequirementsReport,
        *,
        recipe_identity: str,
        owning_source_module: str = "UNRESOLVED_SOURCE_MODULE",
    ) -> PlotDataGapRequest:
        content = {
            "recipe": recipe_identity,
            "deficiencies": [dataclasses.asdict(item) for item in report.deficiencies],
        }
        return cls(
            request_id=f"PLOT_DATA_GAP_REQUEST:{semantic_hash(content)}",
            requesting_recipe=recipe_identity,
            owning_source_module=owning_source_module,
            missing_field_semantics=tuple(
                {"field_id": item.field_id, "code": item.code, "expected": item.expected}
                for item in report.deficiencies
            ),
            why_existing_fields_are_insufficient=tuple(
                item.explanation for item in report.deficiencies
            ),
            entity_path_event_indexing=tuple(
                str(item.expected.get("indexing", "must be supplied by owning source module"))
                for item in report.deficiencies
            ),
            data_type_and_shape=tuple(
                str(
                    item.expected.get(
                        "data_type_and_shape", "must be supplied by owning source module"
                    )
                )
                for item in report.deficiencies
            ),
            unit_frame_reference_point=tuple(
                f"{item.expected.get('unit')} / {item.expected.get('frame')} / {item.expected.get('reference_point')}"
                for item in report.deficiencies
            ),
            required_sampling_cadence=tuple(
                str(item.expected.get("sampling_cadence")) for item in report.deficiencies
            ),
            raw_or_derived_classification="canonical_raw_if_new_physical_state_else_versioned_derived",
            estimated_storage_cost="OWNING_MODULE_MUST_ESTIMATE",
            additive_or_breaking_schema_change="ADDITIVE_IF_SEMANTICS_AND_INDICES_ARE_NEW; OTHERWISE_MAJOR_REVIEW",
            backward_compatibility_expectation="old bundles remain readable; missing fields return NULL+UNAVAILABLE",
            validation_plot_or_test=f"{recipe_identity}: missing/present/cadence/frame/reference regression",
        )
