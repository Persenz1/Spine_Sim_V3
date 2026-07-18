from __future__ import annotations

import re
from pathlib import Path

from spine_sim.foundation.models import MaturityStatus, SourceIdentity
from spine_sim.foundation.registry import DataClassification, SchemaRegistry
from spine_sim.surface.result_extension import (
    MATERIALIZATION_RECEIPTS_DATASET,
    SOURCE_AVAILABILITY_DATASET,
    SURFACE_PROVENANCE_DATASET,
    SURFACE_QUALITY_BANDS_DATASET,
    SURFACE_REALIZATIONS_DATASET,
    SURFACE_STATISTICS_DATASET,
    VALIDATION_RESULTS_DATASET,
    VISUALIZATION_COORDINATES_FIELD,
    VISUALIZATION_HEIGHT_FIELD,
    VISUALIZATION_VALIDITY_FIELD,
    surface_result_extension,
)


def test_m01_extension_registers_frozen_owner_namespace_and_all_required_ids() -> None:
    registry = SchemaRegistry()
    descriptor = surface_result_extension()
    registry.register_extension(descriptor)
    digest = registry.freeze()
    required_datasets = {
        SURFACE_REALIZATIONS_DATASET,
        SURFACE_PROVENANCE_DATASET,
        SURFACE_QUALITY_BANDS_DATASET,
        SURFACE_STATISTICS_DATASET,
        MATERIALIZATION_RECEIPTS_DATASET,
        VALIDATION_RESULTS_DATASET,
        SOURCE_AVAILABILITY_DATASET,
    }
    assert descriptor.owner_module == "M01"
    assert descriptor.namespace == "m01"
    assert required_datasets <= set(registry.datasets)
    assert {
        VISUALIZATION_HEIGHT_FIELD,
        VISUALIZATION_VALIDITY_FIELD,
        VISUALIZATION_COORDINATES_FIELD,
    } <= set(registry.arrays)
    assert digest == registry.snapshot_hash


def test_every_m01_field_has_complete_metadata_and_experimental_maturity_blocked() -> None:
    descriptor = surface_result_extension()
    for dataset in descriptor.tables:
        for field in dataset.fields:
            assert field.owner_module == "M01"
            assert field.semantics
            assert field.dtype
            assert field.unit
            assert field.frame
            assert field.reference_point
            assert field.indices
            assert field.null_policy
            assert field.authority_refs
            assert (
                field.maturity.experimentally_validated.status is MaturityStatus.BLOCKED_UNAVAILABLE
            )
    assert (
        next(
            item for item in descriptor.tables if item.dataset_id == VALIDATION_RESULTS_DATASET
        ).source_identity
        is SourceIdentity.VALIDATION_ONLY
    )
    availability = next(
        item for item in descriptor.tables if item.dataset_id == SOURCE_AVAILABILITY_DATASET
    )
    assert availability.source_identity is SourceIdentity.PROPOSED_SUPPLEMENT
    receipts = next(
        item for item in descriptor.tables if item.dataset_id == MATERIALIZATION_RECEIPTS_DATASET
    )
    assert not receipts.default_visible
    assert all(field.classification is DataClassification.DIAGNOSTIC for field in receipts.fields)


def test_surface_readme_output_overview_lists_only_registered_m01_ids() -> None:
    readme = Path(__file__).parents[2] / "src" / "spine_sim" / "surface" / "README.md"
    output_overview = readme.read_text(encoding="utf-8").split("## 输出概览", maxsplit=1)[1]
    documented_ids = set(re.findall(r"`(m01\.[a-z0-9_]+)`", output_overview))

    descriptor = surface_result_extension()
    registered_ids = {
        *(table.dataset_id for table in descriptor.tables),
        *(array.field.field_id for array in descriptor.arrays),
    }
    assert documented_ids == registered_ids
