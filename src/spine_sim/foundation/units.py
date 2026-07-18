"""One-time conversion into the canonical N-mm-MPa unit system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import AggregateValidationError, ContractViolation, ValidationIssue


@dataclass(frozen=True, slots=True)
class UnitDefinition:
    dimension: str
    canonical_unit: str
    scale: float


UNIT_DEFINITIONS: dict[str, UnitDefinition] = {
    "1": UnitDefinition("dimensionless", "1", 1.0),
    "mm": UnitDefinition("length", "mm", 1.0),
    "um": UnitDefinition("length", "mm", 1.0e-3),
    "µm": UnitDefinition("length", "mm", 1.0e-3),
    "m": UnitDefinition("length", "mm", 1.0e3),
    "N": UnitDefinition("force", "N", 1.0),
    "MPa": UnitDefinition("stress", "MPa", 1.0),
    "GPa": UnitDefinition("stress", "MPa", 1.0e3),
    "Pa": UnitDefinition("stress", "MPa", 1.0e-6),
    "N/mm": UnitDefinition("stiffness", "N/mm", 1.0),
    "N/m": UnitDefinition("stiffness", "N/mm", 1.0e-3),
    "N*mm": UnitDefinition("moment_energy", "N*mm", 1.0),
    "N·mm": UnitDefinition("moment_energy", "N*mm", 1.0),
    "s": UnitDefinition("time", "s", 1.0),
    "mm/s": UnitDefinition("speed", "mm/s", 1.0),
    "m/s": UnitDefinition("speed", "mm/s", 1.0e3),
    "rad": UnitDefinition("angle", "rad", 1.0),
    "deg": UnitDefinition("angle", "rad", 0.017453292519943295),
    "N/mm^2": UnitDefinition("stress", "MPa", 1.0),
}

SUFFIX_UNITS: tuple[tuple[str, str], ...] = (
    ("_mm_per_s", "mm/s"),
    ("_N_per_mm", "N/mm"),
    ("_N_per_m", "N/m"),
    ("_N_mm", "N*mm"),
    ("_MPa", "MPa"),
    ("_GPa", "GPa"),
    ("_deg", "deg"),
    ("_rad", "rad"),
    ("_mm", "mm"),
    ("_um", "um"),
    ("_N", "N"),
    ("_s", "s"),
)

CONVERTER_ID = "spine-sim-unit-normalizer"
CONVERTER_VERSION = "1.0.0"
SUFFIX_ADAPTER_ID = "dev-profile-suffix-adapter"
SUFFIX_ADAPTER_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class Quantity:
    value: float
    unit: str


@dataclass(frozen=True, slots=True)
class NormalizedQuantity:
    canonical_value: float
    canonical_unit: str
    dimension: str
    original_value: float
    original_unit: str
    converter_id: str = CONVERTER_ID
    converter_version: str = CONVERTER_VERSION
    suffix_adapter_id: str | None = None
    suffix_adapter_version: str | None = None
    normalized_once: bool = True

    def semantic_value(self) -> dict[str, Any]:
        return {"value": self.canonical_value, "unit": self.canonical_unit}


def normalize_quantity(
    quantity: Quantity | dict[str, Any] | NormalizedQuantity,
    *,
    expected_dimension: str,
    suffix_adapter: bool = False,
) -> NormalizedQuantity:
    if isinstance(quantity, NormalizedQuantity):
        raise ContractViolation(
            "quantity has already been normalized", details={"code": "REPEATED_UNIT_CONVERSION"}
        )
    if isinstance(quantity, dict):
        if set(quantity) != {"value", "unit"}:
            raise AggregateValidationError(
                [
                    ValidationIssue(
                        "INVALID_QUANTITY_OBJECT",
                        "",
                        "quantity must contain exactly value and unit",
                        original_value=quantity,
                    )
                ]
            )
        raw_value, raw_unit = quantity["value"], quantity["unit"]
    else:
        raw_value, raw_unit = quantity.value, quantity.unit
    if isinstance(raw_value, bool) or not isinstance(raw_value, int | float):
        raise ContractViolation("quantity value must be numeric")
    if not isinstance(raw_unit, str) or raw_unit not in UNIT_DEFINITIONS:
        raise ContractViolation("unknown unit", details={"unit": raw_unit})
    definition = UNIT_DEFINITIONS[raw_unit]
    if definition.dimension != expected_dimension:
        raise ContractViolation(
            "quantity dimension mismatch",
            details={
                "expected": expected_dimension,
                "actual": definition.dimension,
                "unit": raw_unit,
            },
        )
    return NormalizedQuantity(
        canonical_value=float(raw_value) * definition.scale,
        canonical_unit=definition.canonical_unit,
        dimension=definition.dimension,
        original_value=float(raw_value),
        original_unit=raw_unit,
        suffix_adapter_id=SUFFIX_ADAPTER_ID if suffix_adapter else None,
        suffix_adapter_version=SUFFIX_ADAPTER_VERSION if suffix_adapter else None,
    )


def split_suffix_field(field_name: str) -> tuple[str, str] | None:
    for suffix, unit in SUFFIX_UNITS:
        if field_name.endswith(suffix) and len(field_name) > len(suffix):
            return field_name[: -len(suffix)], unit
    return None
