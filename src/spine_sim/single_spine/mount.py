"""A-authoritative one-sided independent-spring and rigid mount graph."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from spine_sim.foundation.canonical import stable_content_id
from spine_sim.foundation.errors import ContractViolation

from .contracts import MountMode, MountParameterBundle, SpringState, Vector3


@dataclass(frozen=True, slots=True)
class MountResponse:
    mode: MountMode
    state: SpringState
    generalized_compressive_force_n: float
    compression_mm: float
    remaining_travel_mm: float
    spring_force_n: float
    hard_stop_reaction_n: float
    rigid_constraint_reaction_n: float
    energy_n_mm: float
    incremental_axial_compliance_mm_per_n: float
    requires_contact_release: bool
    set_valued_constraint: bool
    admissible_graph_handle: str | None


def solve_mount_graph(
    *,
    parameters: MountParameterBundle,
    initial_axis_global: Vector3,
    contact_force_global_n: Vector3,
    force_tolerance_n: float = 1.0e-12,
) -> MountResponse:
    """Evaluate the frozen four-branch mount graph without any penalty surrogate."""

    axis = np.asarray(initial_axis_global, dtype=np.float64)
    force = np.asarray(contact_force_global_n, dtype=np.float64)
    if (
        axis.shape != (3,)
        or force.shape != (3,)
        or not np.isfinite(axis).all()
        or not np.isfinite(force).all()
    ):
        raise ContractViolation("mount graph requires finite global 3-vectors")
    if not math.isclose(float(np.linalg.norm(axis)), 1.0, abs_tol=1.0e-9):
        raise ContractViolation("mount axis must be unit length")
    if not math.isfinite(force_tolerance_n) or force_tolerance_n < 0.0:
        raise ContractViolation("mount force tolerance must be finite and non-negative")
    generalized = -float(np.dot(axis, force))

    if parameters.mode is MountMode.RIGID_MOUNT:
        graph = stable_content_id(
            "m03_rigid_mount_graph",
            {"mode": parameters.mode, "axis": tuple(axis), "generalized_force": generalized},
        )
        return MountResponse(
            parameters.mode,
            SpringState.RIGID_LOCKED,
            generalized,
            0.0,
            0.0,
            0.0,
            0.0,
            generalized,
            0.0,
            0.0,
            False,
            True,
            graph,
        )

    assert parameters.spring_stiffness_n_per_mm is not None
    stiffness = parameters.spring_stiffness_n_per_mm
    maximum = parameters.maximum_compression_mm
    if generalized <= force_tolerance_n:
        return MountResponse(
            parameters.mode,
            SpringState.AT_ORIGINAL_LENGTH,
            generalized,
            0.0,
            maximum,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0 / stiffness,
            generalized < -force_tolerance_n,
            False,
            None,
        )

    unconstrained = generalized / stiffness
    if unconstrained < maximum - force_tolerance_n / stiffness:
        energy = 0.5 * stiffness * unconstrained**2
        return MountResponse(
            parameters.mode,
            SpringState.COMPRESSING,
            generalized,
            unconstrained,
            maximum - unconstrained,
            generalized,
            0.0,
            0.0,
            energy,
            1.0 / stiffness,
            False,
            False,
            None,
        )

    spring_force = stiffness * maximum
    reaction = max(0.0, generalized - spring_force)
    return MountResponse(
        parameters.mode,
        SpringState.HARD_STOP,
        generalized,
        maximum,
        0.0,
        spring_force,
        reaction,
        0.0,
        0.5 * stiffness * maximum**2,
        0.0,
        False,
        False,
        None,
    )


__all__ = ["MountResponse", "solve_mount_graph"]
