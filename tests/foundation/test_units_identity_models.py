from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest

from spine_sim.foundation.canonical import (
    ShortIdRegistry,
    canonical_array_manifest,
    semantic_hash,
    stable_content_id,
    uuid7,
)
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    AttemptOutcome,
    CapabilityStatus,
    CertificationStatus,
    Maturity,
    PhysicalFeasibility,
    RecordBase,
    StatusTuple,
    ValuePresence,
)
from spine_sim.foundation.units import Quantity, normalize_quantity


@pytest.mark.parametrize(
    ("value", "unit", "dimension", "expected", "canonical_unit"),
    [
        (50, "um", "length", 0.05, "mm"),
        (2, "N/m", "stiffness", 0.002, "N/mm"),
        (210, "GPa", "stress", 210000.0, "MPa"),
        (180, "deg", "angle", math.pi, "rad"),
        (1, "m/s", "speed", 1000.0, "mm/s"),
    ],
)
def test_unit_conversion(
    value: float, unit: str, dimension: str, expected: float, canonical_unit: str
) -> None:
    result = normalize_quantity(Quantity(value, unit), expected_dimension=dimension)
    assert result.canonical_value == pytest.approx(expected)
    assert result.canonical_unit == canonical_unit


def test_repeated_conversion_and_dimension_mismatch_rejected() -> None:
    normalized = normalize_quantity(Quantity(1, "mm"), expected_dimension="length")
    with pytest.raises(ContractViolation):
        normalize_quantity(normalized, expected_dimension="length")
    with pytest.raises(ContractViolation):
        normalize_quantity(Quantity(1, "N"), expected_dimension="length")


def test_uuid7_and_stable_content_identity() -> None:
    identifier = uuid7(timestamp_ms=1234, randomness=1)
    assert identifier.version == 7
    assert identifier.variant == "specified in RFC 4122"
    assert stable_content_id("case", {"b": 2, "a": 1}) == stable_content_id(
        "case", {"a": 1, "b": 2}
    )


def test_semantic_hash_rejects_nonfinite_and_array_layout_is_nonsemantic() -> None:
    with pytest.raises(ContractViolation):
        semantic_hash({"bad": float("nan")})
    contiguous = np.arange(12, dtype=np.float64).reshape(3, 4)
    fortran = np.asfortranarray(contiguous)
    assert canonical_array_manifest(contiguous) == canonical_array_manifest(fortran)


def test_short_id_collision_is_detected() -> None:
    registry = ShortIdRegistry(prefix_length=4)
    registry.register("abcd" + "0" * 60)
    with pytest.raises(ContractViolation):
        registry.register("abcd" + "1" * 60)


@dataclasses.dataclass(frozen=True, slots=True)
class _TimedRecord(RecordBase):
    __dataset_id__ = "test.records"
    run_id: str
    value: int
    created_at: int = dataclasses.field(metadata={"semantic": False})


def test_run_and_nonsemantic_fields_are_excluded_from_record_semantics() -> None:
    first = _TimedRecord("run-1", 5, 1)
    second = _TimedRecord("run-2", 5, 999)
    assert first.semantic_hash() == second.semantic_hash()
    assert first.storage_dict() != second.storage_dict()


def test_status_axes_reject_invalid_inference() -> None:
    with pytest.raises(ContractViolation):
        StatusTuple(
            ValuePresence.PRESENT,
            CapabilityStatus.UNAVAILABLE,
            AttemptOutcome.NOT_ATTEMPTED,
            PhysicalFeasibility.NOT_ASSESSED,
            CertificationStatus.NOT_CERTIFIABLE,
            "BAD",
            "bad",
        )
    with pytest.raises(ContractViolation):
        StatusTuple(
            ValuePresence.NULL,
            CapabilityStatus.SUPPORTED,
            AttemptOutcome.NUMERICAL_FAILURE,
            PhysicalFeasibility.PHYSICAL_INFEASIBLE,
            CertificationStatus.NOT_CERTIFIABLE,
            "BAD",
            "bad",
        )


def test_maturity_has_four_independent_columns() -> None:
    maturity = Maturity.validation_only_implemented()
    assert maturity.theory_defined.status != maturity.numerically_verified.status
    assert maturity.code_implemented.status != maturity.experimentally_validated.status
