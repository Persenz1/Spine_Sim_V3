"""Accepted 3D Euler--Bernoulli beam implementation for M03 A-M0."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from spine_sim.foundation.errors import ContractViolation

from .contracts import (
    BeamModelState,
    BeamParameterBundle,
    Matrix6,
    NeedleParameterBundle,
    Vector3,
    Vector6,
)

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class CircularSection:
    area_mm2: float
    second_moment_mm4: float
    polar_moment_mm4: float
    shear_modulus_mpa: float | None


@dataclass(frozen=True, slots=True)
class BeamCenterlinePoint:
    arc_coordinate_mm: float
    position_global_mm: Vector3
    translation_global_mm: Vector3
    rotation_global_rad: Vector3


@dataclass(frozen=True, slots=True)
class BeamResponse:
    model_id: str
    model_state: BeamModelState
    tip_translation_global_mm: Vector3
    tip_rotation_global_rad: Vector3
    root_reaction_force_global_n: Vector3
    root_reaction_moment_global_n_mm: Vector3
    section_resultants_needle: Vector6
    energy_n_mm: float
    compliance_global: Matrix6
    centerline: tuple[BeamCenterlinePoint, ...]
    slenderness_ratio: float
    tip_deflection_over_length: float
    rotation_norm_rad: float
    validity_reasons: tuple[str, ...]


def circular_section(
    needle: NeedleParameterBundle,
    beam: BeamParameterBundle,
) -> CircularSection:
    diameter = needle.diameter_mm
    area = math.pi * diameter**2 / 4.0
    second = math.pi * diameter**4 / 64.0
    polar = math.pi * diameter**4 / 32.0
    shear = None
    if beam.bending_enabled:
        assert beam.youngs_modulus_mpa is not None
        assert beam.poisson_ratio is not None
        shear = beam.youngs_modulus_mpa / (2.0 * (1.0 + beam.poisson_ratio))
    return CircularSection(area, second, polar, shear)


def _unit(vector: Vector3, name: str) -> FloatArray:
    result = np.asarray(vector, dtype=np.float64)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ContractViolation(f"{name} must be a finite 3-vector")
    norm = float(np.linalg.norm(result))
    if not math.isclose(norm, 1.0, abs_tol=1.0e-9):
        raise ContractViolation(f"{name} must be unit length")
    return result


def _cross_matrix(vector: FloatArray) -> FloatArray:
    x, y, z = vector
    return np.array(((0.0, -z, y), (z, 0.0, -x), (-y, x, 0.0)), dtype=np.float64)


def needle_basis(initial_axis_global: Vector3) -> FloatArray:
    """Return a deterministic right-handed needle basis with axis in column 0."""

    axis = _unit(initial_axis_global, "initial_axis_global")
    candidates = np.eye(3, dtype=np.float64)
    seed = candidates[int(np.argmin(np.abs(candidates @ axis)))]
    second = seed - float(np.dot(seed, axis)) * axis
    second /= np.linalg.norm(second)
    third = np.cross(axis, second)
    basis = np.column_stack((axis, second, third))
    if float(np.linalg.det(basis)) < 0.0:
        basis[:, 2] *= -1.0
    return basis


def _beam_kinematics(
    *,
    s_mm: float,
    length_mm: float,
    force: FloatArray,
    moment: FloatArray,
    axis: FloatArray,
    section: CircularSection,
    youngs_modulus_mpa: float,
) -> tuple[FloatArray, FloatArray]:
    assert section.shear_modulus_mpa is not None
    parallel = np.outer(axis, axis)
    transverse = np.eye(3) - parallel
    skew = _cross_matrix(axis)
    axial = s_mm / (youngs_modulus_mpa * section.area_mm2) * (parallel @ force)
    bending_force = (
        s_mm**2
        * (3.0 * length_mm - s_mm)
        / (6.0 * youngs_modulus_mpa * section.second_moment_mm4)
        * (transverse @ force)
    )
    bending_moment = (
        -(s_mm**2) / (2.0 * youngs_modulus_mpa * section.second_moment_mm4) * (skew @ moment)
    )
    translation = axial + bending_force + bending_moment
    rotation = (
        s_mm
        * (2.0 * length_mm - s_mm)
        / (2.0 * youngs_modulus_mpa * section.second_moment_mm4)
        * (skew @ force)
        + s_mm / (youngs_modulus_mpa * section.second_moment_mm4) * (transverse @ moment)
        + s_mm / (section.shear_modulus_mpa * section.polar_moment_mm4) * (parallel @ moment)
    )
    return translation, rotation


def beam_compliance_matrix(
    needle: NeedleParameterBundle,
    beam: BeamParameterBundle,
    initial_axis_global: Vector3,
) -> Matrix6:
    if not beam.bending_enabled:
        return tuple(tuple(0.0 for _ in range(6)) for _ in range(6))  # type: ignore[return-value]
    assert beam.youngs_modulus_mpa is not None
    section = circular_section(needle, beam)
    axis = _unit(initial_axis_global, "initial_axis_global")
    matrix = np.zeros((6, 6), dtype=np.float64)
    for column in range(6):
        force = np.zeros(3, dtype=np.float64)
        moment = np.zeros(3, dtype=np.float64)
        if column < 3:
            force[column] = 1.0
        else:
            moment[column - 3] = 1.0
        translation, rotation = _beam_kinematics(
            s_mm=needle.exposed_length_mm,
            length_mm=needle.exposed_length_mm,
            force=force,
            moment=moment,
            axis=axis,
            section=section,
            youngs_modulus_mpa=beam.youngs_modulus_mpa,
        )
        matrix[:, column] = np.concatenate((translation, rotation))
    matrix = 0.5 * (matrix + matrix.T)
    return tuple(tuple(float(value) for value in row) for row in matrix)  # type: ignore[return-value]


def solve_euler_bernoulli(
    *,
    needle: NeedleParameterBundle,
    beam: BeamParameterBundle,
    root_position_global_mm: Vector3,
    initial_axis_global: Vector3,
    contact_force_global_n: Vector3,
    contact_moment_at_tip_global_n_mm: Vector3 = (0.0, 0.0, 0.0),
    centerline_sample_count: int = 17,
) -> BeamResponse:
    """Evaluate the accepted EB response and an endpoint-consistent centerline."""

    if centerline_sample_count < 2:
        raise ContractViolation("beam centerline requires at least two samples")
    root = np.asarray(root_position_global_mm, dtype=np.float64)
    force = np.asarray(contact_force_global_n, dtype=np.float64)
    moment = np.asarray(contact_moment_at_tip_global_n_mm, dtype=np.float64)
    if any(value.shape != (3,) or not np.isfinite(value).all() for value in (root, force, moment)):
        raise ContractViolation("beam inputs must be finite global 3-vectors")
    axis = _unit(initial_axis_global, "initial_axis_global")
    section = circular_section(needle, beam)
    length = needle.exposed_length_mm
    compliance = beam_compliance_matrix(needle, beam, initial_axis_global)

    if beam.bending_enabled:
        assert beam.youngs_modulus_mpa is not None
        tip_translation, tip_rotation = _beam_kinematics(
            s_mm=length,
            length_mm=length,
            force=force,
            moment=moment,
            axis=axis,
            section=section,
            youngs_modulus_mpa=beam.youngs_modulus_mpa,
        )
        centerline_values: list[BeamCenterlinePoint] = []
        for coordinate in np.linspace(0.0, length, centerline_sample_count):
            translation, rotation = _beam_kinematics(
                s_mm=float(coordinate),
                length_mm=length,
                force=force,
                moment=moment,
                axis=axis,
                section=section,
                youngs_modulus_mpa=beam.youngs_modulus_mpa,
            )
            position = root + coordinate * axis + translation
            centerline_values.append(
                BeamCenterlinePoint(
                    float(coordinate),
                    tuple(float(value) for value in position),  # type: ignore[arg-type]
                    tuple(float(value) for value in translation),  # type: ignore[arg-type]
                    tuple(float(value) for value in rotation),  # type: ignore[arg-type]
                )
            )
        wrench = np.concatenate((force, moment))
        generalized = np.concatenate((tip_translation, tip_rotation))
        energy = max(0.0, 0.5 * float(np.dot(wrench, generalized)))
        state = BeamModelState.EB_ELASTIC
    else:
        tip_translation = np.zeros(3, dtype=np.float64)
        tip_rotation = np.zeros(3, dtype=np.float64)
        energy = 0.0
        centerline_values = [
            BeamCenterlinePoint(
                float(coordinate),
                tuple(float(value) for value in root + coordinate * axis),  # type: ignore[arg-type]
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
            )
            for coordinate in np.linspace(0.0, length, centerline_sample_count)
        ]
        state = BeamModelState.BENDING_OFF

    tip_position = root + length * axis + tip_translation
    section_moment = moment + np.cross(tip_position - root, force)
    basis = needle_basis(initial_axis_global)
    local_force = basis.T @ force
    local_moment = basis.T @ section_moment
    section_resultants: Vector6 = tuple(
        float(value) for value in np.concatenate((local_force, local_moment))
    )  # type: ignore[assignment]

    slenderness = length / needle.diameter_mm
    deflection_ratio = float(np.linalg.norm(tip_translation)) / length
    rotation_norm = float(np.linalg.norm(tip_rotation))
    validity: list[str] = []
    if beam.bending_enabled and slenderness < beam.minimum_slenderness_ratio:
        validity.append("SLENDERNESS_BELOW_VALIDATED_RANGE")
    if beam.bending_enabled and deflection_ratio > beam.maximum_tip_deflection_over_length:
        validity.append("TIP_DEFLECTION_OUT_OF_SMALL_DEFORMATION_RANGE")
    if beam.bending_enabled and rotation_norm > beam.maximum_rotation_rad:
        validity.append("ROTATION_OUT_OF_SMALL_ANGLE_RANGE")
    if validity:
        state = BeamModelState.STRUCTURAL_MODEL_OUT_OF_RANGE

    root_reaction_force = -force
    root_reaction_moment = -section_moment
    return BeamResponse(
        "euler_bernoulli",
        state,
        tuple(float(value) for value in tip_translation),  # type: ignore[arg-type]
        tuple(float(value) for value in tip_rotation),  # type: ignore[arg-type]
        tuple(float(value) for value in root_reaction_force),  # type: ignore[arg-type]
        tuple(float(value) for value in root_reaction_moment),  # type: ignore[arg-type]
        section_resultants,
        energy,
        compliance,
        tuple(centerline_values),
        slenderness,
        deflection_ratio,
        rotation_norm,
        tuple(validity),
    )


def timoshenko_validation_reference(
    response: BeamResponse,
    *,
    needle: NeedleParameterBundle,
    beam: BeamParameterBundle,
    contact_force_global_n: Vector3,
    initial_axis_global: Vector3,
    shear_correction: float = 5.0 / 6.0,
) -> Vector3:
    """VALIDATION_ONLY Timoshenko tip translation; never a production registry model."""

    if not beam.bending_enabled:
        return response.tip_translation_global_mm
    if not 0.0 < shear_correction <= 1.0:
        raise ContractViolation("invalid validation shear correction")
    section = circular_section(needle, beam)
    assert section.shear_modulus_mpa is not None
    axis = _unit(initial_axis_global, "initial_axis_global")
    force = np.asarray(contact_force_global_n, dtype=np.float64)
    transverse = (np.eye(3) - np.outer(axis, axis)) @ force
    shear = (
        needle.exposed_length_mm
        / (shear_correction * section.shear_modulus_mpa * section.area_mm2)
        * transverse
    )
    value = np.asarray(response.tip_translation_global_mm) + shear
    return tuple(float(component) for component in value)  # type: ignore[return-value]


def corotational_validation_reference(response: BeamResponse) -> Vector3:
    """VALIDATION_ONLY finite-rotation endpoint correction for small-angle convergence."""

    rotation = np.asarray(response.tip_rotation_global_rad, dtype=np.float64)
    angle = float(np.linalg.norm(rotation))
    if angle == 0.0:
        return response.tip_translation_global_mm
    axis = rotation / angle
    skew = _cross_matrix(axis)
    rotation_matrix = np.eye(3) + math.sin(angle) * skew + (1.0 - math.cos(angle)) * (skew @ skew)
    correction = (rotation_matrix - np.eye(3)) @ np.asarray(response.tip_translation_global_mm)
    result = np.asarray(response.tip_translation_global_mm) + correction
    return tuple(float(component) for component in result)  # type: ignore[return-value]


__all__ = [
    "BeamCenterlinePoint",
    "BeamResponse",
    "CircularSection",
    "beam_compliance_matrix",
    "circular_section",
    "corotational_validation_reference",
    "needle_basis",
    "solve_euler_bernoulli",
    "timoshenko_validation_reference",
]
