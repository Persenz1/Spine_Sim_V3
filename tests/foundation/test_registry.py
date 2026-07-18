from __future__ import annotations

import dataclasses

import pytest

from spine_sim.foundation.demo_validation_only import (
    DEMO_DATASET_ID,
    ValidationOnlySample,
    validation_extension,
)
from spine_sim.foundation.errors import ContractViolation, SchemaRegistrationError
from spine_sim.foundation.models import Maturity, SourceIdentity
from spine_sim.foundation.registry import (
    DataClassification,
    FieldMetadata,
    SchemaRegistry,
)


def _metadata(**updates: object) -> FieldMetadata:
    values = {
        "field_id": "example.vector",
        "namespace": "example",
        "owner_module": "M01",
        "semantics": "directed vector",
        "classification": DataClassification.CANONICAL_RAW,
        "dtype": "float64",
        "shape": (3,),
        "dimensions": ("component",),
        "raggedness": "fixed",
        "unit": "N",
        "frame": "GLOBAL",
        "reference_point": "ORIGIN",
        "sign_semantics": "declared",
        "action_semantics": "wall_on_object",
        "indices": ("case_id",),
        "sampling_cadence": "per_point",
        "storage_frequency": "every_point",
        "ownership": "accepted",
        "null_policy": "not_null",
        "source_identity": SourceIdentity.ACCEPTED_AUTHORITY,
        "authority_refs": ("contract",),
        "maturity": Maturity.validation_only_implemented(),
        "introduced_version": "1.0.0",
        "deprecated_version": None,
        "storage_dataset": "example.table",
        "encoding": "parquet",
        "precision": "float64",
        "required": True,
    }
    values.update(updates)
    return FieldMetadata(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("missing", ["unit", "frame", "reference_point"])
def test_directed_field_requires_unit_frame_reference(missing: str) -> None:
    with pytest.raises(SchemaRegistrationError):
        _metadata(**{missing: "UNSPECIFIED"})


def test_float32_and_namespace_mismatch_rejected() -> None:
    with pytest.raises(SchemaRegistrationError):
        _metadata(precision="float32")
    with pytest.raises(SchemaRegistrationError):
        _metadata(field_id="other.vector")


def test_core_and_extension_registry_freeze_snapshot() -> None:
    registry = SchemaRegistry()
    registry.register_extension(validation_extension())
    digest = registry.freeze()
    assert digest == registry.snapshot_hash
    assert DEMO_DATASET_ID in registry.datasets
    assert registry.snapshot()["registry_hash"] == digest
    with pytest.raises(SchemaRegistrationError):
        registry.register_extension(validation_extension())


def test_extension_namespace_conflict() -> None:
    registry = SchemaRegistry()
    extension = validation_extension()
    registry.register_extension(extension)
    with pytest.raises(SchemaRegistrationError):
        registry.register_extension(dataclasses.replace(extension, owner_module="OTHER"))


def test_every_core_field_has_complete_metadata() -> None:
    registry = SchemaRegistry()
    for dataset in registry.datasets.values():
        for item in dataset.fields:
            assert item.semantics
            assert item.dtype
            assert item.unit
            assert item.frame
            assert item.reference_point
            assert item.indices
            assert item.authority_refs
            assert item.null_policy
            assert item.introduced_version


def test_writer_registry_rejects_runtime_dtype_and_source_identity_spoofing() -> None:
    registry = SchemaRegistry()
    registry.register_extension(validation_extension())
    registry.freeze()
    wrong_dtype = ValidationOnlySample(
        "run",
        "case",
        "point",
        "not-a-float",
        SourceIdentity.VALIDATION_ONLY,  # type: ignore[arg-type]
    )
    with pytest.raises(ContractViolation):
        registry.validate_record(wrong_dtype)
    wrong_source = ValidationOnlySample(
        "run",
        "case",
        "point",
        1.0,
        "VALIDATION_ONLY",  # type: ignore[arg-type]
    )
    with pytest.raises(ContractViolation):
        registry.validate_record(wrong_source)
