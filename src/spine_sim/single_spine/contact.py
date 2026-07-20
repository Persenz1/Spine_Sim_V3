"""Rigid Signorini/Coulomb graph and objective-slip utilities for M03."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from spine_sim.foundation.canonical import stable_content_id
from spine_sim.foundation.errors import ContractViolation

from .contracts import (
    ContactMotionState,
    TangentStatus,
    Vector2,
    Vector3,
    WrenchUniqueness,
)

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class ContactKinematics:
    support_id: str
    candidate_id: str
    point_global_mm: Vector3
    normal_global: Vector3
    tangent_basis_global: tuple[Vector3, Vector3]
    free_gap_mm: float
    objective_slip_increment_global_mm: Vector3
    previous_normal_multiplier_n: float = 0.0
    previous_tangential_multiplier_n: Vector2 = (0.0, 0.0)
    support_migrated: bool = False


@dataclass(frozen=True, slots=True)
class ContactSupportSolution:
    support_id: str
    candidate_id: str
    normal_multiplier_n: float
    tangential_multiplier_n: Vector2
    contact_force_global_n: Vector3
    final_gap_mm: float
    friction_margin_n: float
    objective_slip_increment_global_mm: Vector3
    objective_slip_increment_local_mm: Vector2
    motion_state: ContactMotionState
    all_stick_friction_margin_n: float
    all_stick_feasible: bool
    maximum_dissipation_closed: bool
    complementarity_residual: float
    soc_residual: float
    graph_residual: float


@dataclass(frozen=True, slots=True)
class ContactGraphSolution:
    supports: tuple[ContactSupportSolution, ...]
    resultant_force_global_n: Vector3
    branch_id: str
    branch_feasible: bool
    graph_quality_passed: bool
    complementarity_residual: float
    soc_residual: float
    graph_residual: float
    wrench_uniqueness: WrenchUniqueness
    rank: int
    nullspace_basis: tuple[tuple[float, ...], ...]
    admissible_graph_handle: str | None
    tangent_status: TangentStatus
    numerical_regularization_used_as_physics: bool = False


def deterministic_tangent_basis(
    normal_global: Vector3, task_direction_global: Vector3
) -> tuple[Vector3, Vector3]:
    normal = _unit(normal_global, "normal_global")
    task = _unit(task_direction_global, "task_direction_global")
    tangent = task - float(np.dot(task, normal)) * normal
    if float(np.linalg.norm(tangent)) <= 1.0e-12:
        axes = np.eye(3)
        seed = axes[int(np.argmin(np.abs(axes @ normal)))]
        tangent = seed - float(np.dot(seed, normal)) * normal
    tangent /= np.linalg.norm(tangent)
    second = np.cross(normal, tangent)
    return (
        tuple(float(value) for value in tangent),  # type: ignore[return-value]
        tuple(float(value) for value in second),
    )


def objective_slip_increment(
    *,
    tip_translation_increment_global_mm: Vector3,
    tip_rotation_increment_global_rad: Vector3,
    support_point_mid_global_mm: Vector3,
    tip_center_mid_global_mm: Vector3,
    normal_mid_global: Vector3,
) -> Vector3:
    """Compute the frozen midpoint/current-tangent-plane objective slip increment."""

    translation = _vector(tip_translation_increment_global_mm, "tip translation")
    rotation = _vector(tip_rotation_increment_global_rad, "tip rotation")
    point = _vector(support_point_mid_global_mm, "support point")
    center = _vector(tip_center_mid_global_mm, "tip center")
    normal = _unit(normal_mid_global, "normal")
    projector = np.eye(3) - np.outer(normal, normal)
    slip = projector @ (translation + np.cross(rotation, point - center))
    return tuple(float(value) for value in slip)  # type: ignore[return-value]


def project_lorentz_cone(value: tuple[float, float, float]) -> tuple[float, float, float]:
    scalar = float(value[0])
    vector = np.asarray(value[1:], dtype=np.float64)
    norm = float(np.linalg.norm(vector))
    if norm <= scalar:
        return value
    if norm <= -scalar:
        return (0.0, 0.0, 0.0)
    projected_scalar = 0.5 * (norm + scalar)
    projected_vector = projected_scalar * vector / norm
    return (
        projected_scalar,
        float(projected_vector[0]),
        float(projected_vector[1]),
    )


def soc_projection_residual(
    *,
    normal_multiplier_n: float,
    tangential_multiplier_n: Vector2,
    effective_gap_mm: float,
    slip_increment_local_mm: Vector2,
    friction_coefficient: float,
    projection_scale: float = 1.0,
) -> float:
    if friction_coefficient < 0.0 or not math.isfinite(friction_coefficient):
        raise ContractViolation("friction coefficient must be finite and non-negative")
    if friction_coefficient == 0.0:
        return max(
            abs(tangential_multiplier_n[0]),
            abs(tangential_multiplier_n[1]),
            max(-normal_multiplier_n, 0.0),
            max(-effective_gap_mm, 0.0),
            abs(normal_multiplier_n * effective_gap_mm),
        )
    chi = np.array(
        (
            friction_coefficient * normal_multiplier_n,
            tangential_multiplier_n[0],
            tangential_multiplier_n[1],
        ),
        dtype=np.float64,
    )
    slip_norm = math.hypot(*slip_increment_local_mm)
    psi = np.array(
        (
            effective_gap_mm / friction_coefficient + slip_norm,
            slip_increment_local_mm[0],
            slip_increment_local_mm[1],
        ),
        dtype=np.float64,
    )
    projected = np.asarray(project_lorentz_cone(tuple(chi - projection_scale * psi)))
    return float(np.linalg.norm(chi - projected))


def _assemble_branch_system(
    *,
    candidate_data: list[tuple[ContactKinematics, FloatArray, FloatArray]],
    active_indices: list[int],
    compliance: FloatArray,
    free: FloatArray,
    friction_coefficient: float,
    sliding_directions: dict[int, FloatArray],
) -> tuple[FloatArray, FloatArray]:
    """Assemble compatibility rows and force columns for one contact branch."""

    compatibility_rows: list[FloatArray] = []
    force_columns: list[FloatArray] = []
    right_hand: list[float] = []
    for local_index, support_index in enumerate(active_indices):
        item, normal, tangent = candidate_data[support_index]
        compatibility_rows.append(normal)
        right_hand.append(-(item.free_gap_mm + float(np.dot(normal, free))))
        direction = sliding_directions.get(local_index)
        if direction is not None:
            force_columns.append(normal - friction_coefficient * (tangent @ direction))
            continue

        force_columns.extend((normal, tangent[:, 0], tangent[:, 1]))
        compatibility_rows.extend((tangent[:, 0], tangent[:, 1]))
        objective_slip_local = tangent.T @ np.asarray(
            item.objective_slip_increment_global_mm,
            dtype=np.float64,
        )
        right_hand.extend((-float(objective_slip_local[0]), -float(objective_slip_local[1])))

    row_matrix = np.column_stack(compatibility_rows)
    force_matrix = np.column_stack(force_columns)
    return (
        row_matrix.T @ compliance @ force_matrix,
        np.asarray(right_hand, dtype=np.float64),
    )


def _decode_branch_coefficients(
    coefficients: FloatArray,
    *,
    support_count: int,
    friction_coefficient: float,
    sliding_directions: dict[int, FloatArray],
) -> tuple[FloatArray, FloatArray]:
    normals = np.zeros(support_count, dtype=np.float64)
    tangents = np.zeros((support_count, 2), dtype=np.float64)
    cursor = 0
    for local_index in range(support_count):
        direction = sliding_directions.get(local_index)
        normal_force = max(0.0, float(coefficients[cursor]))
        normals[local_index] = normal_force
        if direction is None:
            tangents[local_index] = coefficients[cursor + 1 : cursor + 3]
            cursor += 3
        else:
            tangents[local_index] = -friction_coefficient * normal_force * direction
            cursor += 1
    return normals, tangents


def _raw_normal_multipliers_feasible(
    coefficients: FloatArray,
    *,
    support_count: int,
    sliding_indices: set[int],
    force_tolerance_n: float,
) -> bool:
    cursor = 0
    for local_index in range(support_count):
        if float(coefficients[cursor]) < -force_tolerance_n:
            return False
        cursor += 1 if local_index in sliding_indices else 3
    return True


def _support_forces(
    candidate_data: list[tuple[ContactKinematics, FloatArray, FloatArray]],
    active_indices: list[int],
    normal_multipliers: FloatArray,
    tangential_multipliers: FloatArray,
) -> list[FloatArray]:
    return [
        normal_multipliers[local_index] * candidate_data[support_index][1]
        + candidate_data[support_index][2] @ tangential_multipliers[local_index]
        for local_index, support_index in enumerate(active_indices)
    ]


def _final_objective_slips_local(
    candidate_data: list[tuple[ContactKinematics, FloatArray, FloatArray]],
    active_indices: list[int],
    elastic_displacement: FloatArray,
) -> tuple[FloatArray, ...]:
    return tuple(
        tangent.T
        @ (
            np.asarray(item.objective_slip_increment_global_mm, dtype=np.float64)
            + elastic_displacement
        )
        for support_index in active_indices
        for item, _, tangent in (candidate_data[support_index],)
    )


def _initial_sliding_direction(
    *,
    candidate_data: list[tuple[ContactKinematics, FloatArray, FloatArray]],
    active_indices: list[int],
    local_index: int,
    all_stick_coefficients: FloatArray,
    force_tolerance_n: float,
) -> FloatArray | None:
    item, _, tangent = candidate_data[active_indices[local_index]]
    objective_slip = tangent.T @ np.asarray(
        item.objective_slip_increment_global_mm,
        dtype=np.float64,
    )
    slip_norm = float(np.linalg.norm(objective_slip))
    if slip_norm > np.finfo(np.float64).eps:
        return objective_slip / slip_norm
    all_stick_traction = all_stick_coefficients[3 * local_index + 1 : 3 * local_index + 3]
    traction_norm = float(np.linalg.norm(all_stick_traction))
    if traction_norm > force_tolerance_n:
        # This is only an iteration seed.  A support is committed as sliding
        # only after the re-equilibrated objective slip closes the vector
        # maximum-dissipation law below.
        return -all_stick_traction / traction_norm
    return None


def _solve_maximum_dissipation_branch(
    *,
    candidate_data: list[tuple[ContactKinematics, FloatArray, FloatArray]],
    active_indices: list[int],
    compliance: FloatArray,
    free: FloatArray,
    friction_coefficient: float,
    all_stick_coefficients: FloatArray,
    initially_sliding: set[int],
    force_tolerance_n: float,
) -> tuple[FloatArray, FloatArray, FloatArray, set[int], bool]:
    """Re-equilibrate a coupled stick/maximum-dissipation candidate branch."""

    support_count = len(active_indices)
    sliding_indices = set(initially_sliding)
    directions: dict[int, FloatArray] = {}
    for local_index in sorted(sliding_indices):
        direction = _initial_sliding_direction(
            candidate_data=candidate_data,
            active_indices=active_indices,
            local_index=local_index,
            all_stick_coefficients=all_stick_coefficients,
            force_tolerance_n=force_tolerance_n,
        )
        if direction is None:
            normals, tangents = _decode_branch_coefficients(
                all_stick_coefficients,
                support_count=support_count,
                friction_coefficient=friction_coefficient,
                sliding_directions={},
            )
            system, _ = _assemble_branch_system(
                candidate_data=candidate_data,
                active_indices=active_indices,
                compliance=compliance,
                free=free,
                friction_coefficient=friction_coefficient,
                sliding_directions={},
            )
            return normals, tangents, system, sliding_indices, False
        directions[local_index] = direction

    normals = np.zeros(support_count, dtype=np.float64)
    tangents = np.zeros((support_count, 2), dtype=np.float64)
    system = np.empty((0, 0), dtype=np.float64)
    for _ in range(support_count + 1):
        converged = False
        raw_normals_feasible = False
        for _ in range(64):
            system, rhs = _assemble_branch_system(
                candidate_data=candidate_data,
                active_indices=active_indices,
                compliance=compliance,
                free=free,
                friction_coefficient=friction_coefficient,
                sliding_directions=directions,
            )
            coefficients = np.linalg.pinv(system, rcond=1.0e-12) @ rhs
            raw_normals_feasible = _raw_normal_multipliers_feasible(
                coefficients,
                support_count=support_count,
                sliding_indices=sliding_indices,
                force_tolerance_n=force_tolerance_n,
            )
            normals, tangents = _decode_branch_coefficients(
                coefficients,
                support_count=support_count,
                friction_coefficient=friction_coefficient,
                sliding_directions=directions,
            )
            forces = _support_forces(
                candidate_data,
                active_indices,
                normals,
                tangents,
            )
            elastic_displacement = compliance @ np.sum(forces, axis=0)
            slips = _final_objective_slips_local(
                candidate_data,
                active_indices,
                elastic_displacement,
            )
            updated: dict[int, FloatArray] = {}
            maximum_law_residual = 0.0
            direction_resolved = True
            for local_index in sorted(sliding_indices):
                slip_norm = float(np.linalg.norm(slips[local_index]))
                if slip_norm <= np.finfo(np.float64).eps:
                    direction_resolved = False
                    continue
                updated[local_index] = slips[local_index] / slip_norm
                maximum_law_residual = max(
                    maximum_law_residual,
                    float(
                        np.linalg.norm(
                            tangents[local_index]
                            + friction_coefficient * normals[local_index] * updated[local_index]
                        )
                    ),
                )
            if (
                direction_resolved
                and raw_normals_feasible
                and maximum_law_residual <= force_tolerance_n
            ):
                converged = True
                break
            directions.update(updated)

        newly_sliding = {
            local_index
            for local_index in range(support_count)
            if local_index not in sliding_indices
            and float(np.linalg.norm(tangents[local_index]))
            > friction_coefficient * normals[local_index] + force_tolerance_n
        }
        if not newly_sliding:
            return normals, tangents, system, sliding_indices, converged
        for local_index in sorted(newly_sliding):
            slip_norm = float(np.linalg.norm(slips[local_index]))
            if slip_norm > np.finfo(np.float64).eps:
                directions[local_index] = slips[local_index] / slip_norm
            else:
                traction_norm = float(np.linalg.norm(tangents[local_index]))
                if traction_norm <= force_tolerance_n:
                    return normals, tangents, system, sliding_indices, False
                directions[local_index] = -tangents[local_index] / traction_norm
        sliding_indices.update(newly_sliding)

    return normals, tangents, system, sliding_indices, False


def solve_rigid_contact_graph(
    *,
    supports: tuple[ContactKinematics, ...],
    point_compliance_global_mm_per_n: tuple[Vector3, Vector3, Vector3],
    free_tip_increment_global_mm: Vector3,
    friction_coefficient: float,
    gap_tolerance_mm: float,
    force_tolerance_n: float,
    slip_tolerance_mm: float,
    soc_projection_scale: float = 1.0,
) -> ContactGraphSolution:
    """Solve a fixed candidate graph, trying one-sided all-stick before true sliding.

    The compliance matrix contains only explicitly enabled beam/mount physics.
    No penalty or normal contact compliance is introduced.
    """

    compliance = np.asarray(point_compliance_global_mm_per_n, dtype=np.float64)
    free = _vector(free_tip_increment_global_mm, "free tip increment")
    if compliance.shape != (3, 3) or not np.isfinite(compliance).all():
        raise ContractViolation("point compliance must be a finite 3x3 matrix")
    if not np.allclose(compliance, compliance.T, atol=1.0e-12, rtol=1.0e-12):
        raise ContractViolation("reversible point compliance must be symmetric")
    eigenvalues = np.linalg.eigvalsh(compliance)
    if float(np.min(eigenvalues)) < -1.0e-12:
        raise ContractViolation("point compliance cannot contain a negative-energy direction")
    for name, value in (
        ("friction_coefficient", friction_coefficient),
        ("gap_tolerance_mm", gap_tolerance_mm),
        ("force_tolerance_n", force_tolerance_n),
        ("slip_tolerance_mm", slip_tolerance_mm),
    ):
        if not math.isfinite(value) or value < 0.0:
            raise ContractViolation(f"{name} must be finite and non-negative")

    candidate_data = [_basis_and_validate(item) for item in supports]
    active_indices = [
        index
        for index, (item, _, _) in enumerate(candidate_data)
        if item.free_gap_mm <= gap_tolerance_mm
        and (
            item.free_gap_mm + float(np.dot(item.normal_global, free)) < gap_tolerance_mm
            or item.previous_normal_multiplier_n > force_tolerance_n
            or abs(item.free_gap_mm) <= gap_tolerance_mm
        )
    ]
    if not active_indices:
        return _open_solution()

    # ``free_tip_increment_global_mm`` closes the normal gap predictor.  The
    # tangential compatibility datum is support-local objective slip: unlike a
    # single global translation it also contains rotation and the current
    # tangent plane.  Keeping these two inputs distinct is essential when the
    # kernel has already folded prescribed translation into each support's
    # objective-slip increment and therefore passes ``free=(0, 0, 0)``.
    all_stick_system, all_stick_rhs = _assemble_branch_system(
        candidate_data=candidate_data,
        active_indices=active_indices,
        compliance=compliance,
        free=free,
        friction_coefficient=friction_coefficient,
        sliding_directions={},
    )
    all_stick_coefficients = np.linalg.pinv(all_stick_system, rcond=1.0e-12) @ all_stick_rhs

    # Eliminate supports whose all-stick representative violates lambda_n >= 0.
    kept = [
        local_index
        for local_index in range(len(active_indices))
        if all_stick_coefficients[3 * local_index] >= -force_tolerance_n
    ]
    if len(kept) != len(active_indices):
        active_indices = [active_indices[index] for index in kept]
        if not active_indices:
            return _open_solution()
        return solve_rigid_contact_graph(
            supports=tuple(supports[index] for index in active_indices),
            point_compliance_global_mm_per_n=point_compliance_global_mm_per_n,
            free_tip_increment_global_mm=free_tip_increment_global_mm,
            friction_coefficient=friction_coefficient,
            gap_tolerance_mm=gap_tolerance_mm,
            force_tolerance_n=force_tolerance_n,
            slip_tolerance_mm=slip_tolerance_mm,
            soc_projection_scale=soc_projection_scale,
        )

    all_stick_margins: list[float] = []
    violating: list[int] = []
    for local_index in range(len(active_indices)):
        normal_force = max(0.0, float(all_stick_coefficients[3 * local_index]))
        tangent_force = all_stick_coefficients[3 * local_index + 1 : 3 * local_index + 3]
        magnitude = float(np.linalg.norm(tangent_force))
        limit = friction_coefficient * normal_force
        all_stick_margins.append(limit - magnitude)
        if magnitude > limit + force_tolerance_n:
            violating.append(local_index)

    normal_multipliers, tangential_multipliers = _decode_branch_coefficients(
        all_stick_coefficients,
        support_count=len(active_indices),
        friction_coefficient=friction_coefficient,
        sliding_directions={},
    )
    system = all_stick_system
    branch_iteration_closed = True
    sliding_indices: set[int] = set()
    if violating:
        (
            normal_multipliers,
            tangential_multipliers,
            system,
            sliding_indices,
            branch_iteration_closed,
        ) = _solve_maximum_dissipation_branch(
            candidate_data=candidate_data,
            active_indices=active_indices,
            compliance=compliance,
            free=free,
            friction_coefficient=friction_coefficient,
            all_stick_coefficients=all_stick_coefficients,
            initially_sliding=set(violating),
            force_tolerance_n=force_tolerance_n,
        )

    # Elastic displacement is driven by the resultant of the complete graph.
    # Evaluating each gap against a running partial sum would make the answer
    # depend on support enumeration order.
    support_forces = _support_forces(
        candidate_data,
        active_indices,
        normal_multipliers,
        tangential_multipliers,
    )
    total_force = np.sum(support_forces, axis=0)
    elastic_displacement = compliance @ total_force
    final_displacement = free + elastic_displacement
    final_slips_local = _final_objective_slips_local(
        candidate_data,
        active_indices,
        elastic_displacement,
    )
    rank = int(np.linalg.matrix_rank(system, tol=1.0e-12))
    rank_deficient = rank < system.shape[1]
    subresolution_boundary_indices = {
        local_index
        for local_index in sliding_indices
        if np.finfo(np.float64).eps
        < float(np.linalg.norm(final_slips_local[local_index]))
        <= slip_tolerance_mm
        and abs(
            float(np.linalg.norm(tangential_multipliers[local_index]))
            - friction_coefficient * normal_multipliers[local_index]
        )
        <= force_tolerance_n
        and float(
            np.linalg.norm(
                tangential_multipliers[local_index]
                + friction_coefficient
                * normal_multipliers[local_index]
                * final_slips_local[local_index]
                / float(np.linalg.norm(final_slips_local[local_index]))
            )
        )
        <= force_tolerance_n
    }
    solutions: list[ContactSupportSolution] = []
    maximum_complementarity = 0.0
    maximum_soc = 0.0
    maximum_graph = 0.0
    for local_index, support_index in enumerate(active_indices):
        item, normal, tangent = candidate_data[support_index]
        normal_force = float(normal_multipliers[local_index])
        tangent_force = tangential_multipliers[local_index]
        force = support_forces[local_index]
        final_gap = item.free_gap_mm + float(np.dot(normal, final_displacement))
        slip_local = final_slips_local[local_index]
        slip_global = tangent @ slip_local
        slip_norm = float(np.linalg.norm(slip_local))
        friction_margin = friction_coefficient * normal_force - float(np.linalg.norm(tangent_force))
        maximum_dissipation_residual = 0.0
        if local_index in sliding_indices and slip_norm > np.finfo(np.float64).eps:
            maximum_dissipation_residual = float(
                np.linalg.norm(
                    tangent_force + friction_coefficient * normal_force * slip_local / slip_norm
                )
            )
        maximum_dissipation = (
            local_index in sliding_indices
            and branch_iteration_closed
            and slip_norm > slip_tolerance_mm
            and maximum_dissipation_residual <= force_tolerance_n
            and abs(float(np.linalg.norm(tangent_force)) - friction_coefficient * normal_force)
            <= force_tolerance_n
        )
        complementarity = max(
            max(-final_gap, 0.0),
            max(-normal_force, 0.0),
            abs(final_gap * normal_force),
        )
        soc = max(0.0, -friction_margin)
        graph = max(
            soc_projection_residual(
                normal_multiplier_n=normal_force,
                tangential_multiplier_n=(float(tangent_force[0]), float(tangent_force[1])),
                effective_gap_mm=final_gap,
                slip_increment_local_mm=(float(slip_local[0]), float(slip_local[1])),
                friction_coefficient=friction_coefficient,
                projection_scale=soc_projection_scale,
            ),
            maximum_dissipation_residual,
        )
        if normal_force <= force_tolerance_n:
            motion = ContactMotionState.TOUCH_ZERO_LOAD
        elif maximum_dissipation:
            motion = ContactMotionState.SLIDING_COMMITTED
        elif item.support_migrated and slip_norm <= slip_tolerance_mm:
            motion = ContactMotionState.ROLLING_NO_SLIP
        elif abs(friction_margin) <= force_tolerance_n:
            motion = ContactMotionState.STICKING_AT_CONE_BOUNDARY
        else:
            motion = ContactMotionState.STICKING_INTERIOR
        maximum_complementarity = max(maximum_complementarity, complementarity)
        maximum_soc = max(maximum_soc, soc)
        maximum_graph = max(maximum_graph, graph)
        solutions.append(
            ContactSupportSolution(
                item.support_id,
                item.candidate_id,
                normal_force,
                (float(tangent_force[0]), float(tangent_force[1])),
                tuple(float(value) for value in force),  # type: ignore[arg-type]
                final_gap,
                friction_margin,
                tuple(float(value) for value in slip_global),  # type: ignore[arg-type]
                (float(slip_local[0]), float(slip_local[1])),
                motion,
                all_stick_margins[local_index],
                all_stick_margins[local_index] >= -force_tolerance_n,
                maximum_dissipation,
                complementarity,
                soc,
                graph,
            )
        )

    confirmed_sliding = {
        index for index, item in enumerate(solutions) if item.maximum_dissipation_closed
    }
    final_cone_violations = {
        index for index, item in enumerate(solutions) if item.friction_margin_n < -force_tolerance_n
    }
    unresolved_violation = bool(
        (sliding_indices - confirmed_sliding - subresolution_boundary_indices)
        | final_cone_violations
    )
    branch_feasible = branch_iteration_closed and not unresolved_violation
    quality = (
        branch_feasible
        and maximum_complementarity <= max(gap_tolerance_mm, force_tolerance_n)
        and maximum_soc <= force_tolerance_n
        and maximum_graph <= max(gap_tolerance_mm, force_tolerance_n, slip_tolerance_mm)
    )
    uniqueness = (
        WrenchUniqueness.SET_VALUED_CONSTRAINT if rank_deficient else WrenchUniqueness.UNIQUE
    )
    graph_handle = None
    nullspace: tuple[tuple[float, ...], ...] = ()
    tangent_status = TangentStatus.GENERALIZED_ONE_SIDED
    if rank_deficient:
        _, _, vh = np.linalg.svd(system)
        null_vectors = vh[rank:]
        nullspace = tuple(tuple(float(value) for value in row) for row in null_vectors)
        graph_handle = stable_content_id(
            "m03_contact_admissible_graph",
            {
                "support_ids": tuple(item.support_id for item in solutions),
                "rank": rank,
                "nullspace": nullspace,
                "mu": friction_coefficient,
            },
        )
        tangent_status = TangentStatus.CONSTRAINT_SET_VALUED
    elif confirmed_sliding:
        tangent_status = TangentStatus.BRANCH_DEPENDENT
    elif not violating:
        tangent_status = TangentStatus.SMOOTH_CONSISTENT

    if confirmed_sliding and branch_feasible:
        branch = "MAXIMUM_DISSIPATION_SLIDE"
    elif subresolution_boundary_indices and branch_feasible:
        branch = "ONE_SIDED_CONE_BOUNDARY"
    elif sliding_indices:
        branch = "MAXIMUM_DISSIPATION_UNRESOLVED"
    else:
        branch = "ONE_SIDED_ALL_STICK"
    return ContactGraphSolution(
        tuple(solutions),
        tuple(float(value) for value in total_force),  # type: ignore[arg-type]
        branch,
        branch_feasible,
        quality,
        maximum_complementarity,
        maximum_soc,
        maximum_graph,
        uniqueness,
        rank,
        nullspace,
        graph_handle,
        tangent_status,
    )


def _open_solution() -> ContactGraphSolution:
    return ContactGraphSolution(
        (),
        (0.0, 0.0, 0.0),
        "OPEN_GRAPH",
        True,
        True,
        0.0,
        0.0,
        0.0,
        WrenchUniqueness.UNIQUE,
        0,
        (),
        None,
        TangentStatus.SMOOTH_CONSISTENT,
    )


def _vector(value: Vector3, name: str) -> FloatArray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ContractViolation(f"{name} must be a finite 3-vector")
    return result


def _unit(value: Vector3, name: str) -> FloatArray:
    result = _vector(value, name)
    if not math.isclose(float(np.linalg.norm(result)), 1.0, abs_tol=1.0e-9):
        raise ContractViolation(f"{name} must be unit length")
    return result


def _basis_and_validate(
    item: ContactKinematics,
) -> tuple[ContactKinematics, FloatArray, FloatArray]:
    normal = _unit(item.normal_global, "contact normal")
    tangent = np.column_stack(
        (
            _unit(item.tangent_basis_global[0], "first tangent"),
            _unit(item.tangent_basis_global[1], "second tangent"),
        )
    )
    if not np.allclose(tangent.T @ tangent, np.eye(2), atol=1.0e-9, rtol=1.0e-9):
        raise ContractViolation("contact tangent basis must be orthonormal")
    if not np.allclose(normal @ tangent, np.zeros(2), atol=1.0e-9, rtol=1.0e-9):
        raise ContractViolation("contact tangent basis must lie in the tangent plane")
    if not math.isfinite(item.free_gap_mm):
        raise ContractViolation("contact free gap must be finite")
    _vector(item.point_global_mm, "contact point")
    _vector(item.objective_slip_increment_global_mm, "objective slip")
    return item, normal, tangent


__all__ = [
    "ContactGraphSolution",
    "ContactKinematics",
    "ContactSupportSolution",
    "deterministic_tangent_basis",
    "objective_slip_increment",
    "project_lorentz_cone",
    "soc_projection_residual",
    "solve_rigid_contact_graph",
]
