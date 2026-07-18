"""Unit-isolated residual merit and hard numerical quality gates."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation

from .contracts import (
    ComplementarityQuality,
    GraphQuality,
    HardInequalityQuality,
    ResidualBlock,
    ResidualKind,
)


@dataclass(frozen=True, slots=True)
class QualityGateReport:
    """Structured result of the acceptance gate; merit cannot mask failures."""

    report_id: str
    report_hash: str
    accepted: bool
    dimensionless_merit: float
    hard_block_failures: tuple[str, ...]
    hard_inequality_failures: tuple[str, ...]
    complementarity_failures: tuple[str, ...]
    graph_failures: tuple[str, ...]
    warning_ids: tuple[str, ...]
    assessed_ids: tuple[str, ...]


def assess_numerical_quality(
    residual_blocks: Iterable[ResidualBlock],
    hard_inequalities: Iterable[HardInequalityQuality] = (),
    complementarity_qualities: Iterable[ComplementarityQuality] = (),
    graph_qualities: Iterable[GraphQuality] = (),
    *,
    warning_ids: Iterable[str] = (),
) -> QualityGateReport:
    """Apply each raw-unit hard gate and separately compute scaled merit."""

    blocks = tuple(sorted(residual_blocks, key=lambda item: (item.owner_id, item.block_id)))
    inequalities = tuple(sorted(hard_inequalities, key=lambda item: item.quality_id))
    complementarity = tuple(sorted(complementarity_qualities, key=lambda item: item.quality_id))
    graphs = tuple(sorted(graph_qualities, key=lambda item: item.quality_id))
    warnings = tuple(sorted(set(warning_ids)))
    _ensure_unique_ids(
        (
            *(item.block_id for item in blocks),
            *(item.quality_id for item in inequalities),
            *(item.quality_id for item in complementarity),
            *(item.quality_id for item in graphs),
        )
    )
    for block in blocks:
        validate_residual_block_policy(block)
    block_failures = tuple(
        item.block_id for item in blocks if item.hard_acceptance and not item.accepted
    )
    inequality_failures = tuple(item.quality_id for item in inequalities if not item.passed)
    complementarity_failures = tuple(
        item.quality_id for item in complementarity if item.hard_acceptance and not item.accepted
    )
    graph_failures = tuple(
        item.quality_id for item in graphs if item.hard_acceptance and not item.accepted
    )
    scaled_terms = (
        *(item.normalized_norm for item in blocks),
        *(item.normalized_violation for item in inequalities),
        *(item.normalized_norm for item in complementarity),
        *(item.normalized_distance for item in graphs),
    )
    merit = math.sqrt(math.fsum(value * value for value in scaled_terms))
    accepted = not (
        block_failures or inequality_failures or complementarity_failures or graph_failures
    )
    assessed_ids = (
        *(item.block_id for item in blocks),
        *(item.quality_id for item in inequalities),
        *(item.quality_id for item in complementarity),
        *(item.quality_id for item in graphs),
    )
    payload = {
        "accepted": accepted,
        "dimensionless_merit": merit,
        "hard_block_failures": block_failures,
        "hard_inequality_failures": inequality_failures,
        "complementarity_failures": complementarity_failures,
        "graph_failures": graph_failures,
        "warning_ids": warnings,
        "assessed_ids": assessed_ids,
    }
    return QualityGateReport(
        report_id=stable_content_id("m02_quality_gate", payload),
        report_hash=semantic_hash(payload),
        accepted=accepted,
        dimensionless_merit=merit,
        hard_block_failures=block_failures,
        hard_inequality_failures=inequality_failures,
        complementarity_failures=complementarity_failures,
        graph_failures=graph_failures,
        warning_ids=warnings,
        assessed_ids=assessed_ids,
    )


def validate_residual_block_policy(block: ResidualBlock) -> None:
    """Enforce the frozen unit/tolerance rules not expressible by the schema alone."""

    expected_units = {
        ResidualKind.FORCE_EQUILIBRIUM: {"N"},
        ResidualKind.MOMENT_EQUILIBRIUM: {"N*mm"},
        ResidualKind.KINEMATIC_COMPATIBILITY: {"mm", "rad"},
        ResidualKind.LOAD_CONTROL: {"N", "N*mm", "mm", "rad", "1"},
        ResidualKind.COMPLEMENTARITY_KKT: {"1"},
        ResidualKind.GRAPH_DISTANCE: {"1"},
        ResidualKind.ACTIVE_BRANCH: {"1"},
        ResidualKind.ENERGY_WORK: {"N*mm"},
        ResidualKind.OWNER_DEFINED_HARD_QUALITY: {block.raw_unit},
    }
    if block.raw_unit not in expected_units[block.kind]:
        raise ContractViolation(
            "residual kind/unit mismatch",
            details={"block_id": block.block_id, "kind": block.kind.value, "unit": block.raw_unit},
        )
    if block.kind is ResidualKind.MOMENT_EQUILIBRIUM and block.absolute_tolerance <= 0.0:
        raise ContractViolation(
            "moment residual requires an explicit positive N*mm tolerance",
            details={"block_id": block.block_id},
        )
    if not block.scale_id.strip() or block.scale_value <= 0.0:
        raise ContractViolation(
            "residual block lacks an explicit scale",
            details={"block_id": block.block_id},
        )


def validate_strict_rigid_graph(
    graph: GraphQuality,
    *,
    penalty_stiffness: float | None = None,
) -> None:
    """Reject a large-penalty surrogate for a declared strictly rigid graph."""

    if penalty_stiffness is not None:
        raise ContractViolation(
            "strict rigid behavior must use graph/set-valued semantics, not a penalty stiffness",
            details={"graph_id": graph.graph_id, "penalty_stiffness": penalty_stiffness},
        )
    if not graph.set_valued:
        raise ContractViolation(
            "strict rigid graph must preserve set-valued semantics",
            details={"graph_id": graph.graph_id},
        )
    if graph.degenerate and graph.nullspace_dimension is None:
        raise ContractViolation(
            "degenerate strict graph requires nullspace diagnostics",
            details={"graph_id": graph.graph_id},
        )


def _ensure_unique_ids(values: tuple[str, ...]) -> None:
    if len(values) != len(set(values)):
        raise ContractViolation("quality object IDs must be unique across all numerical gates")
