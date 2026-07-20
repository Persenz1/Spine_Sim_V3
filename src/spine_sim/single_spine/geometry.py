"""M03 composite-needle geometry and swept-envelope primitives.

This module owns geometry only.  In particular, it does not solve an
Euler--Bernoulli constitutive equation or a contact problem.  A beam owner may
provide a sampled centreline through :class:`CenterlineProvider`; this module
then builds the finite cap, cone, shaft and mount envelopes used by M01 query
footprints and collision witnesses.

The tip orientation deliberately uses the frozen M03 global-left-multiply P0
closure.  ``initial_axis_global`` is already a global vector and is therefore
never rotated a second time as though it were local coordinates.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from itertools import pairwise
from typing import Any, Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray

from spine_sim.foundation.canonical import (
    canonical_json_bytes,
    semantic_hash,
    sha256_bytes,
)
from spine_sim.foundation.errors import ContractViolation

from .contracts import LocalFrame, NeedleParameterBundle, Vector3

FloatArray = NDArray[np.float64]

POSE_CLOSURE_ID = "M03_GLOBAL_LEFT_MULTIPLY_P0_1"
CENTERLINE_INTERFACE_ID = "M03_EB_CENTERLINE_GEOMETRY_INTERFACE_1"
COMPOSITE_GEOMETRY_ID = "M03_FINITE_CAP_COMPOSITE_NEEDLE_1"


def _identity_pair(kind: str, payload: Any) -> tuple[str, str]:
    """Return the existing stable ID and semantic hash from one canonical walk."""

    payload_bytes = canonical_json_bytes(payload)
    content_hash = sha256_bytes(payload_bytes)
    stable_bytes = b'{"content":' + payload_bytes + b',"kind":' + canonical_json_bytes(kind) + b"}"
    return f"{kind}:{sha256_bytes(stable_bytes)}", content_hash


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ContractViolation(f"{name} must be a finite number")
    return float(value)


def _positive(value: float, name: str) -> float:
    result = _finite(value, name)
    if result <= 0.0:
        raise ContractViolation(f"{name} must be positive")
    return result


def _vector(value: Sequence[float] | FloatArray, name: str) -> FloatArray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ContractViolation(f"{name} must be a finite three-vector")
    return np.array(result, dtype=np.float64, copy=True)


def _points(value: Sequence[Sequence[float]] | FloatArray, name: str) -> FloatArray:
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 2 or result.shape[1] != 3 or len(result) < 2:
        raise ContractViolation(f"{name} must have shape (N, 3) with N >= 2")
    if not np.isfinite(result).all():
        raise ContractViolation(f"{name} must contain only finite values")
    return np.array(result, dtype=np.float64, copy=True)


def _tuple3(value: Sequence[float] | FloatArray) -> Vector3:
    array = _vector(value, "vector")
    return float(array[0]), float(array[1]), float(array[2])


def _point_tuples(value: FloatArray) -> tuple[Vector3, ...]:
    """Convert a known ``(N, 3)`` construction array without scalar revalidation."""

    return tuple((float(x), float(y), float(z)) for x, y, z in value)


def _unit(value: Sequence[float] | FloatArray, name: str) -> FloatArray:
    result = _vector(value, name)
    norm = float(np.linalg.norm(result))
    if norm <= np.finfo(np.float64).eps:
        raise ContractViolation(f"{name} cannot be the zero vector")
    return result / norm


def rotation_matrix_from_global_vector(rotation_global_rad: Vector3) -> FloatArray:
    """Return ``Exp([theta^G]x)`` using a stable Rodrigues evaluation."""

    theta = _vector(rotation_global_rad, "rotation_global_rad")
    angle = float(np.linalg.norm(theta))
    skew = np.array(
        (
            (0.0, -theta[2], theta[1]),
            (theta[2], 0.0, -theta[0]),
            (-theta[1], theta[0], 0.0),
        ),
        dtype=np.float64,
    )
    if angle < 1.0e-8:
        # Exp(K) = I + K + K^2/2 is both stable and amply accurate in this range.
        return np.eye(3, dtype=np.float64) + skew + 0.5 * (skew @ skew)
    sine_over_angle = math.sin(angle) / angle
    one_minus_cos_over_angle2 = (1.0 - math.cos(angle)) / (angle * angle)
    return (
        np.eye(3, dtype=np.float64)
        + sine_over_angle * skew
        + one_minus_cos_over_angle2 * (skew @ skew)
    )


def engineering_initial_axis(
    local_frame: LocalFrame,
    alpha_rad: float,
    beta_rad: float,
    *,
    require_m03_beta_zero: bool = True,
) -> Vector3:
    """Compute the engineering root-to-tip axis in global coordinates."""

    alpha = _finite(alpha_rad, "alpha_rad")
    beta = _finite(beta_rad, "beta_rad")
    if not 0.0 < alpha < math.pi / 2.0:
        raise ContractViolation("alpha_rad must lie strictly between zero and pi/2")
    if require_m03_beta_zero and not math.isclose(beta, 0.0, abs_tol=1.0e-15, rel_tol=0.0):
        raise ContractViolation("M03_KINEMATIC_MODE_UNSUPPORTED: production beta must be zero")
    ex = _vector(local_frame.e_x_global, "local_frame.e_x_global")
    ey = _vector(local_frame.e_y_global, "local_frame.e_y_global")
    ez = _vector(local_frame.e_z_global, "local_frame.e_z_global")
    axis = (
        math.cos(alpha) * math.cos(beta) * ex
        + math.cos(alpha) * math.sin(beta) * ey
        - math.sin(alpha) * ez
    )
    return _tuple3(_unit(axis, "initial_axis_global"))


def initial_needle_rotation(
    local_frame: LocalFrame,
    alpha_rad: float,
    beta_rad: float,
    *,
    require_m03_beta_zero: bool = True,
) -> FloatArray:
    """Construct a deterministic right-handed ``R0`` with ``R0 e1 = a0``."""

    axis = np.asarray(
        engineering_initial_axis(
            local_frame,
            alpha_rad,
            beta_rad,
            require_m03_beta_zero=require_m03_beta_zero,
        )
    )
    ex = _vector(local_frame.e_x_global, "local_frame.e_x_global")
    ey = _vector(local_frame.e_y_global, "local_frame.e_y_global")
    beta = _finite(beta_rad, "beta_rad")
    transverse = -math.sin(beta) * ex + math.cos(beta) * ey
    transverse -= float(np.dot(transverse, axis)) * axis
    transverse = _unit(transverse, "needle_transverse_axis_global")
    third = _unit(np.cross(axis, transverse), "needle_third_axis_global")
    rotation = np.column_stack((axis, transverse, third))
    if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1.0e-12, rtol=1.0e-12):
        raise ContractViolation("initial needle rotation is not orthonormal")
    if not math.isclose(float(np.linalg.det(rotation)), 1.0, abs_tol=1.0e-12):
        raise ContractViolation("initial needle rotation is not right handed")
    return rotation


@dataclass(frozen=True, slots=True)
class TipPose:
    """Resolved root/tip kinematics with explicit global coordinate types."""

    rigid_root_global_mm: Vector3
    current_root_global_mm: Vector3
    undeformed_tip_center_global_mm: Vector3
    current_tip_center_global_mm: Vector3
    initial_axis_global: Vector3
    current_axis_global: Vector3
    initial_rotation_global_from_needle: tuple[Vector3, Vector3, Vector3]
    current_rotation_global_from_needle: tuple[Vector3, Vector3, Vector3]
    beam_tip_translation_global_mm: Vector3
    beam_tip_rotation_global_rad: Vector3
    spring_compression_mm: float
    closure_id: str
    source_identity: str
    pose_hash: str

    def __post_init__(self) -> None:
        for name in (
            "rigid_root_global_mm",
            "current_root_global_mm",
            "undeformed_tip_center_global_mm",
            "current_tip_center_global_mm",
            "initial_axis_global",
            "current_axis_global",
            "beam_tip_translation_global_mm",
            "beam_tip_rotation_global_rad",
        ):
            _vector(getattr(self, name), name)
        for name in (
            "initial_rotation_global_from_needle",
            "current_rotation_global_from_needle",
        ):
            rotation = np.asarray(getattr(self, name), dtype=np.float64)
            if rotation.shape != (3, 3) or not np.isfinite(rotation).all():
                raise ContractViolation(f"{name} must be a finite 3x3 rotation")
            if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1.0e-10, rtol=1.0e-10):
                raise ContractViolation(f"{name} must be orthonormal")
        if _finite(self.spring_compression_mm, "spring_compression_mm") < 0.0:
            raise ContractViolation("spring_compression_mm cannot be negative")
        if self.closure_id != POSE_CLOSURE_ID or self.source_identity != "PROPOSED_SUPPLEMENT":
            raise ContractViolation("M03 tip pose must identify the frozen P0 supplement")
        expected = semantic_hash(self.identity_payload())
        if self.pose_hash != expected:
            raise ContractViolation("tip pose hash does not match its resolved kinematics")

    def identity_payload(self) -> dict[str, object]:
        return {
            "rigid_root_global_mm": self.rigid_root_global_mm,
            "current_root_global_mm": self.current_root_global_mm,
            "undeformed_tip_center_global_mm": self.undeformed_tip_center_global_mm,
            "current_tip_center_global_mm": self.current_tip_center_global_mm,
            "initial_axis_global": self.initial_axis_global,
            "current_axis_global": self.current_axis_global,
            "initial_rotation_global_from_needle": self.initial_rotation_global_from_needle,
            "current_rotation_global_from_needle": self.current_rotation_global_from_needle,
            "beam_tip_translation_global_mm": self.beam_tip_translation_global_mm,
            "beam_tip_rotation_global_rad": self.beam_tip_rotation_global_rad,
            "spring_compression_mm": self.spring_compression_mm,
            "closure_id": self.closure_id,
            "source_identity": self.source_identity,
        }


def resolve_tip_pose(
    *,
    rigid_root_global_mm: Vector3,
    local_frame: LocalFrame,
    needle: NeedleParameterBundle,
    spring_compression_mm: float = 0.0,
    beam_tip_translation_global_mm: Vector3 = (0.0, 0.0, 0.0),
    beam_tip_rotation_global_rad: Vector3 = (0.0, 0.0, 0.0),
    require_m03_beta_zero: bool = True,
) -> TipPose:
    """Resolve ``r0``, ``c_t``, ``R_t`` and ``a_t`` without beam/contact solving."""

    rigid_root = _vector(rigid_root_global_mm, "rigid_root_global_mm")
    spring = _finite(spring_compression_mm, "spring_compression_mm")
    if spring < 0.0 or spring > 4.0:
        raise ContractViolation("spring_compression_mm must lie in [0, 4]")
    translation = _vector(beam_tip_translation_global_mm, "beam_tip_translation_global_mm")
    rotation_vector = _vector(beam_tip_rotation_global_rad, "beam_tip_rotation_global_rad")
    initial_rotation = initial_needle_rotation(
        local_frame,
        needle.alpha_rad,
        needle.beta_rad,
        require_m03_beta_zero=require_m03_beta_zero,
    )
    initial_axis = initial_rotation[:, 0]
    current_root = rigid_root - spring * initial_axis
    undeformed_center = current_root + needle.exposed_length_mm * initial_axis
    current_center = undeformed_center + translation
    delta_rotation = rotation_matrix_from_global_vector(_tuple3(rotation_vector))
    # Frozen P0 correction: global rotation acts on the left.
    current_rotation = delta_rotation @ initial_rotation
    current_axis = delta_rotation @ initial_axis
    payload: dict[str, object] = {
        "rigid_root_global_mm": _tuple3(rigid_root),
        "current_root_global_mm": _tuple3(current_root),
        "undeformed_tip_center_global_mm": _tuple3(undeformed_center),
        "current_tip_center_global_mm": _tuple3(current_center),
        "initial_axis_global": _tuple3(initial_axis),
        "current_axis_global": _tuple3(current_axis),
        "initial_rotation_global_from_needle": tuple(
            _tuple3(initial_rotation[index, :]) for index in range(3)
        ),
        "current_rotation_global_from_needle": tuple(
            _tuple3(current_rotation[index, :]) for index in range(3)
        ),
        "beam_tip_translation_global_mm": _tuple3(translation),
        "beam_tip_rotation_global_rad": _tuple3(rotation_vector),
        "spring_compression_mm": spring,
        "closure_id": POSE_CLOSURE_ID,
        "source_identity": "PROPOSED_SUPPLEMENT",
    }
    return TipPose(**payload, pose_hash=semantic_hash(payload))  # type: ignore[arg-type]


@runtime_checkable
class CenterlineProvider(Protocol):
    """Geometry-only interface implemented by a future EB structural owner."""

    @property
    def centerline_provider_id(self) -> str:
        """Stable identity of the beam-owned centerline source."""

    def sample_centerline_global_mm(self, normalized_s: FloatArray) -> FloatArray:
        """Return points from root (0) to tip centre (1), shape ``(N, 3)``."""


@dataclass(frozen=True, slots=True)
class RigidCenterlineProvider:
    """Bending-off/reference provider; it is not an EB constitutive model."""

    root_global_mm: Vector3
    tip_center_global_mm: Vector3
    centerline_provider_id: str = "M03_RIGID_CENTERLINE_1"

    def sample_centerline_global_mm(self, normalized_s: FloatArray) -> FloatArray:
        fractions = np.asarray(normalized_s, dtype=np.float64)
        if fractions.ndim != 1 or not np.isfinite(fractions).all():
            raise ContractViolation("normalized_s must be a finite one-dimensional array")
        root = _vector(self.root_global_mm, "root_global_mm")
        tip = _vector(self.tip_center_global_mm, "tip_center_global_mm")
        return root[None, :] + fractions[:, None] * (tip - root)[None, :]


@dataclass(frozen=True, slots=True)
class ExplicitCenterlineProvider:
    """Adapter for centreline samples produced by a beam implementation."""

    control_points_global_mm: tuple[Vector3, ...]
    centerline_provider_id: str

    def __post_init__(self) -> None:
        _points(self.control_points_global_mm, "control_points_global_mm")
        if not self.centerline_provider_id:
            raise ContractViolation("centerline_provider_id must be non-empty")

    def sample_centerline_global_mm(self, normalized_s: FloatArray) -> FloatArray:
        fractions = np.asarray(normalized_s, dtype=np.float64)
        if fractions.ndim != 1 or not np.isfinite(fractions).all():
            raise ContractViolation("normalized_s must be a finite one-dimensional array")
        controls = _points(self.control_points_global_mm, "control_points_global_mm")
        chord_lengths = np.linalg.norm(np.diff(controls, axis=0), axis=1)
        cumulative = np.concatenate((np.array([0.0]), np.cumsum(chord_lengths)))
        if cumulative[-1] <= np.finfo(np.float64).eps:
            raise ContractViolation("explicit centerline cannot have zero total length")
        cumulative /= cumulative[-1]
        result = np.column_stack(
            tuple(np.interp(fractions, cumulative, controls[:, axis]) for axis in range(3))
        )
        return np.asarray(result, dtype=np.float64)


@dataclass(frozen=True, slots=True)
class CenterlineGeometry:
    normalized_s: tuple[float, ...]
    points_global_mm: tuple[Vector3, ...]
    provider_id: str
    interface_id: str
    maximum_sample_chord_mm: float
    centerline_hash: str

    def __post_init__(self) -> None:
        fractions = np.asarray(self.normalized_s, dtype=np.float64)
        points = _points(self.points_global_mm, "points_global_mm")
        if fractions.shape != (len(points),) or not np.isfinite(fractions).all():
            raise ContractViolation("centerline normalized coordinates do not match its points")
        if not np.all(np.diff(fractions) > 0.0) or fractions[0] != 0.0 or fractions[-1] != 1.0:
            raise ContractViolation("centerline samples must increase exactly from zero to one")
        maximum = float(np.max(np.linalg.norm(np.diff(points, axis=0), axis=1)))
        if not math.isclose(
            maximum,
            self.maximum_sample_chord_mm,
            abs_tol=1.0e-12,
            rel_tol=1.0e-12,
        ):
            raise ContractViolation("maximum_sample_chord_mm does not match the samples")
        if self.interface_id != CENTERLINE_INTERFACE_ID:
            raise ContractViolation("unsupported M03 centerline interface")
        expected = semantic_hash(self.identity_payload())
        if self.centerline_hash != expected:
            raise ContractViolation("centerline hash mismatch")

    def identity_payload(self) -> dict[str, object]:
        return {
            "normalized_s": self.normalized_s,
            "points_global_mm": self.points_global_mm,
            "provider_id": self.provider_id,
            "interface_id": self.interface_id,
            "maximum_sample_chord_mm": self.maximum_sample_chord_mm,
        }

    def point_at(self, normalized_s: float) -> FloatArray:
        fraction = _finite(normalized_s, "normalized_s")
        if not 0.0 <= fraction <= 1.0:
            raise ContractViolation("normalized_s must lie in [0, 1]")
        coordinates = np.asarray(self.normalized_s, dtype=np.float64)
        points = np.asarray(self.points_global_mm, dtype=np.float64)
        return np.array(
            [np.interp(fraction, coordinates, points[:, axis]) for axis in range(3)],
            dtype=np.float64,
        )


def sample_centerline(
    provider: CenterlineProvider,
    *,
    expected_root_global_mm: Vector3,
    expected_tip_center_global_mm: Vector3,
    sample_count: int = 65,
    endpoint_tolerance_mm: float = 1.0e-9,
) -> CenterlineGeometry:
    """Sample and validate a beam-owned centreline without solving its mechanics."""

    if not isinstance(sample_count, int) or isinstance(sample_count, bool) or sample_count < 3:
        raise ContractViolation("sample_count must be an integer >= 3")
    tolerance = _positive(endpoint_tolerance_mm, "endpoint_tolerance_mm")
    normalized = np.linspace(0.0, 1.0, sample_count, dtype=np.float64)
    points = _points(provider.sample_centerline_global_mm(normalized), "centerline samples")
    if len(points) != sample_count:
        raise ContractViolation("centerline provider changed requested cardinality")
    if not np.allclose(
        points[0],
        _vector(expected_root_global_mm, "expected_root_global_mm"),
        atol=tolerance,
        rtol=0,
    ):
        raise ContractViolation("centerline root does not match current beam root")
    if not np.allclose(
        points[-1],
        _vector(expected_tip_center_global_mm, "expected_tip_center_global_mm"),
        atol=tolerance,
        rtol=0,
    ):
        raise ContractViolation("centerline tip does not match current tip center")
    maximum_chord = float(np.max(np.linalg.norm(np.diff(points, axis=0), axis=1)))
    payload: dict[str, object] = {
        "normalized_s": tuple(float(item) for item in normalized),
        "points_global_mm": tuple(_tuple3(item) for item in points),
        "provider_id": provider.centerline_provider_id,
        "interface_id": CENTERLINE_INTERFACE_ID,
        "maximum_sample_chord_mm": maximum_chord,
    }
    return CenterlineGeometry(**payload, centerline_hash=semantic_hash(payload))  # type: ignore[arg-type]


class NeedlePart(StrEnum):
    TIP_CAP = "tip_cap"
    CONE = "cone"
    SHAFT = "shaft"
    MOUNT = "mount"


class CollisionRole(StrEnum):
    LEGAL_TIP_CONTACT = "LEGAL_TIP_CONTACT"
    FORBIDDEN_BODY = "FORBIDDEN_BODY"


@dataclass(frozen=True, slots=True)
class PartSurfaceEnvelope:
    part: NeedlePart
    collision_role: CollisionRole
    surface_points_global_mm: tuple[Vector3, ...]
    surface_cover_radius_mm: float
    sampling_method: str

    def __post_init__(self) -> None:
        _points(self.surface_points_global_mm, "surface_points_global_mm")
        if _finite(self.surface_cover_radius_mm, "surface_cover_radius_mm") < 0.0:
            raise ContractViolation("surface cover radius cannot be negative")
        if not self.sampling_method:
            raise ContractViolation("sampling_method must be non-empty")


def _part_identity_payload(part: PartSurfaceEnvelope) -> dict[str, object]:
    # This is byte-equivalent to canonicalizing ``dataclasses.asdict(part)``
    # but avoids recursively copying every immutable witness coordinate first.
    return {
        "part": part.part,
        "collision_role": part.collision_role,
        "surface_points_global_mm": part.surface_points_global_mm,
        "surface_cover_radius_mm": part.surface_cover_radius_mm,
        "sampling_method": part.sampling_method,
    }


@lru_cache(maxsize=4)
def _composite_identity_pair(
    model_id: str,
    tip_pose_hash: str,
    centerline_hash: str,
    cap_blend_coordinate_mm: float,
    parts: tuple[PartSurfaceEnvelope, ...],
) -> tuple[str, str]:
    return _identity_pair(
        "m03_composite_needle_geometry",
        {
            "model_id": model_id,
            "tip_pose_hash": tip_pose_hash,
            "centerline_hash": centerline_hash,
            "cap_blend_coordinate_mm": cap_blend_coordinate_mm,
            "parts": tuple(_part_identity_payload(part) for part in parts),
        },
    )


@dataclass(frozen=True, slots=True)
class CompositeNeedleGeometry:
    geometry_id: str
    geometry_hash: str
    model_id: str
    tip_pose: TipPose
    centerline: CenterlineGeometry
    cap_blend_coordinate_mm: float
    parts: tuple[PartSurfaceEnvelope, ...]

    def __post_init__(self) -> None:
        if self.model_id != COMPOSITE_GEOMETRY_ID:
            raise ContractViolation("unsupported composite needle model")
        expected_parts = tuple(NeedlePart)
        if tuple(part.part for part in self.parts) != expected_parts:
            raise ContractViolation("composite parts must be tip, cone, shaft, mount in order")
        expected_id, expected_hash = _composite_identity_pair(
            self.model_id,
            self.tip_pose.pose_hash,
            self.centerline.centerline_hash,
            self.cap_blend_coordinate_mm,
            self.parts,
        )
        if self.geometry_hash != expected_hash or self.geometry_id != expected_id:
            raise ContractViolation("composite needle identity mismatch")

    def identity_payload(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "tip_pose_hash": self.tip_pose.pose_hash,
            "centerline_hash": self.centerline.centerline_hash,
            "cap_blend_coordinate_mm": self.cap_blend_coordinate_mm,
            "parts": self.parts,
        }

    def part(self, name: NeedlePart) -> PartSurfaceEnvelope:
        return next(item for item in self.parts if item.part is name)

    @property
    def all_surface_points_global_mm(self) -> FloatArray:
        return np.concatenate(
            tuple(
                np.asarray(item.surface_points_global_mm, dtype=np.float64) for item in self.parts
            ),
            axis=0,
        )


def finite_cap_legality_margin_mm(
    support_point_global_mm: Vector3,
    tip_center_global_mm: Vector3,
    current_axis_global: Vector3,
    cap_blend_coordinate_mm: float,
) -> float:
    point = _vector(support_point_global_mm, "support_point_global_mm")
    center = _vector(tip_center_global_mm, "tip_center_global_mm")
    axis = _unit(current_axis_global, "current_axis_global")
    blend = _finite(cap_blend_coordinate_mm, "cap_blend_coordinate_mm")
    return float(np.dot(point - center, axis) - blend)


def is_finite_cap_legal(
    support_point_global_mm: Vector3,
    tip_center_global_mm: Vector3,
    current_axis_global: Vector3,
    cap_blend_coordinate_mm: float,
    *,
    tolerance_mm: float = 0.0,
) -> bool:
    tolerance = _finite(tolerance_mm, "tolerance_mm")
    if tolerance < 0.0:
        raise ContractViolation("tolerance_mm cannot be negative")
    return (
        finite_cap_legality_margin_mm(
            support_point_global_mm,
            tip_center_global_mm,
            current_axis_global,
            cap_blend_coordinate_mm,
        )
        >= -tolerance
    )


def _transverse_basis(
    axis: FloatArray, preferred: FloatArray | None = None
) -> tuple[FloatArray, FloatArray]:
    unit_axis = _unit(axis, "axis")
    if preferred is not None:
        first = np.asarray(preferred, dtype=np.float64)
        first = first - float(np.dot(first, unit_axis)) * unit_axis
        if np.linalg.norm(first) > 1.0e-10:
            first = _unit(first, "preferred transverse")
            return first, _unit(np.cross(unit_axis, first), "second transverse")
    basis = np.eye(3, dtype=np.float64)
    choice = basis[int(np.argmin(np.abs(basis @ unit_axis)))]
    first = _unit(choice - float(np.dot(choice, unit_axis)) * unit_axis, "transverse")
    return first, _unit(np.cross(unit_axis, first), "second transverse")


def _ring_points(
    centers: FloatArray,
    axes: FloatArray,
    radii: FloatArray,
    radial_sample_count: int,
    *,
    initial_preferred: FloatArray,
) -> tuple[FloatArray, float]:
    angles = np.linspace(0.0, math.tau, radial_sample_count, endpoint=False, dtype=np.float64)
    rings: list[FloatArray] = []
    previous = np.array(initial_preferred, dtype=np.float64, copy=True)
    for center, axis, radius in zip(centers, axes, radii, strict=True):
        first, second = _transverse_basis(axis, previous)
        previous = first
        ring = center[None, :] + radius * (
            np.cos(angles)[:, None] * first[None, :] + np.sin(angles)[:, None] * second[None, :]
        )
        rings.append(ring)
    points = np.concatenate(rings, axis=0)
    axial_cover = 0.0
    radial_change = 0.0
    if len(centers) > 1:
        axial_cover = 0.5 * float(np.max(np.linalg.norm(np.diff(centers, axis=0), axis=1)))
        radial_change = 0.5 * float(np.max(np.abs(np.diff(radii))))
    circumferential_cover = float(np.max(radii)) * math.pi / radial_sample_count
    return points, math.hypot(axial_cover, radial_change, circumferential_cover)


def _centerline_axes(
    centerline: CenterlineGeometry, fractions: FloatArray
) -> tuple[FloatArray, FloatArray]:
    centers = np.vstack(tuple(centerline.point_at(float(item)) for item in fractions))
    if len(centers) == 1:
        raise ContractViolation("at least two centerline fractions are required")
    differences = np.asarray(np.gradient(centers, fractions, axis=0), dtype=np.float64)
    axes = np.vstack(tuple(_unit(item, "centerline tangent") for item in differences))
    return centers, axes


@lru_cache(maxsize=4)
def build_composite_needle_geometry(
    *,
    tip_pose: TipPose,
    needle: NeedleParameterBundle,
    centerline: CenterlineGeometry | None = None,
    axial_sample_count: int = 65,
    radial_sample_count: int = 32,
    endpoint_tolerance_mm: float = 1.0e-8,
) -> CompositeNeedleGeometry:
    """Build finite-cap/cone/shaft/mount surfaces from resolved kinematics."""

    if not isinstance(axial_sample_count, int) or axial_sample_count < 5:
        raise ContractViolation("axial_sample_count must be an integer >= 5")
    if not isinstance(radial_sample_count, int) or radial_sample_count < 8:
        raise ContractViolation("radial_sample_count must be an integer >= 8")
    root = np.asarray(tip_pose.current_root_global_mm, dtype=np.float64)
    tip_center = np.asarray(tip_pose.current_tip_center_global_mm, dtype=np.float64)
    if centerline is None:
        if not np.allclose(
            np.asarray(tip_pose.beam_tip_translation_global_mm),
            0.0,
            atol=endpoint_tolerance_mm,
            rtol=0.0,
        ) or not np.allclose(
            np.asarray(tip_pose.beam_tip_rotation_global_rad),
            0.0,
            atol=endpoint_tolerance_mm,
            rtol=0.0,
        ):
            raise ContractViolation(
                "bending-on geometry requires an explicit beam-owned CenterlineProvider"
            )
        provider = RigidCenterlineProvider(_tuple3(root), _tuple3(tip_center))
        centerline = sample_centerline(
            provider,
            expected_root_global_mm=_tuple3(root),
            expected_tip_center_global_mm=_tuple3(tip_center),
            sample_count=axial_sample_count,
            endpoint_tolerance_mm=endpoint_tolerance_mm,
        )
    elif not np.allclose(
        np.asarray(centerline.points_global_mm[0]), root, atol=endpoint_tolerance_mm, rtol=0.0
    ) or not np.allclose(
        np.asarray(centerline.points_global_mm[-1]),
        tip_center,
        atol=endpoint_tolerance_mm,
        rtol=0.0,
    ):
        raise ContractViolation("provided centerline endpoints do not match the resolved tip pose")

    initial_rotation = np.asarray(tip_pose.initial_rotation_global_from_needle, dtype=np.float64)
    current_rotation = np.asarray(tip_pose.current_rotation_global_from_needle, dtype=np.float64)
    current_axis = current_rotation[:, 0]
    current_b = current_rotation[:, 1]
    current_c = current_rotation[:, 2]
    initial_axis = initial_rotation[:, 0]
    initial_b = initial_rotation[:, 1]

    radius = needle.tip_radius_mm
    blend = needle.cap_blend_coordinate_mm
    blend_radius = math.sqrt(max(radius * radius - blend * blend, 0.0))
    polar_start = math.acos(max(-1.0, min(1.0, blend / radius)))
    polar = np.linspace(polar_start, 0.0, max(9, axial_sample_count // 2), dtype=np.float64)
    azimuth = np.linspace(0.0, math.tau, radial_sample_count, endpoint=False)
    cap_rings: list[FloatArray] = []
    for polar_angle in polar:
        axial = radius * math.cos(float(polar_angle))
        ring_radius = radius * math.sin(float(polar_angle))
        cap_rings.append(
            tip_center[None, :]
            + axial * current_axis[None, :]
            + ring_radius
            * (
                np.cos(azimuth)[:, None] * current_b[None, :]
                + np.sin(azimuth)[:, None] * current_c[None, :]
            )
        )
    cap_points = np.concatenate(cap_rings, axis=0)
    polar_step = max((polar_start / max(len(polar) - 1, 1)), 0.0)
    cap_cover = radius * (0.5 * polar_step + math.pi / radial_sample_count)

    cone_back = blend - needle.cone_length_mm
    cone_axial = np.linspace(cone_back, blend, axial_sample_count, dtype=np.float64)
    cone_centers = tip_center[None, :] + cone_axial[:, None] * current_axis[None, :]
    cone_radii = np.linspace(needle.diameter_mm / 2.0, blend_radius, axial_sample_count)
    cone_axes = np.repeat(current_axis[None, :], axial_sample_count, axis=0)
    cone_points, cone_cover = _ring_points(
        cone_centers,
        cone_axes,
        cone_radii,
        radial_sample_count,
        initial_preferred=current_b,
    )

    shaft_join_distance = needle.exposed_length_mm + cone_back
    if not 0.0 < shaft_join_distance < needle.exposed_length_mm:
        raise ContractViolation("cone/shaft transition lies outside the exposed needle length")
    shaft_fraction = shaft_join_distance / needle.exposed_length_mm
    shaft_fractions = np.linspace(0.0, shaft_fraction, axial_sample_count, dtype=np.float64)
    shaft_centers, shaft_axes = _centerline_axes(centerline, shaft_fractions)
    shaft_radii = np.full(axial_sample_count, needle.diameter_mm / 2.0)
    shaft_points, shaft_cover = _ring_points(
        shaft_centers,
        shaft_axes,
        shaft_radii,
        radial_sample_count,
        initial_preferred=initial_b,
    )

    mount_centers = np.linspace(
        root - needle.mount_length_mm * initial_axis,
        root,
        axial_sample_count,
        dtype=np.float64,
    )
    mount_axes = np.repeat(initial_axis[None, :], axial_sample_count, axis=0)
    mount_radii = np.full(axial_sample_count, needle.mount_radius_mm)
    mount_points, mount_cover = _ring_points(
        mount_centers,
        mount_axes,
        mount_radii,
        radial_sample_count,
        initial_preferred=initial_b,
    )

    parts = (
        PartSurfaceEnvelope(
            NeedlePart.TIP_CAP,
            CollisionRole.LEGAL_TIP_CONTACT,
            _point_tuples(cap_points),
            cap_cover,
            "M03_FINITE_SPHERICAL_CAP_POLAR_RINGS_1",
        ),
        PartSurfaceEnvelope(
            NeedlePart.CONE,
            CollisionRole.FORBIDDEN_BODY,
            _point_tuples(cone_points),
            cone_cover,
            "M03_TANGENT_CONE_SURFACE_RINGS_1",
        ),
        PartSurfaceEnvelope(
            NeedlePart.SHAFT,
            CollisionRole.FORBIDDEN_BODY,
            _point_tuples(shaft_points),
            shaft_cover,
            "M03_CENTERLINE_SHAFT_SURFACE_RINGS_1",
        ),
        PartSurfaceEnvelope(
            NeedlePart.MOUNT,
            CollisionRole.FORBIDDEN_BODY,
            _point_tuples(mount_points),
            mount_cover,
            "M03_MOUNT_CYLINDER_SURFACE_RINGS_1",
        ),
    )
    geometry_id, geometry_hash = _composite_identity_pair(
        COMPOSITE_GEOMETRY_ID,
        tip_pose.pose_hash,
        centerline.centerline_hash,
        blend,
        parts,
    )
    return CompositeNeedleGeometry(
        geometry_id,
        geometry_hash,
        COMPOSITE_GEOMETRY_ID,
        tip_pose,
        centerline,
        blend,
        parts,
    )


@dataclass(frozen=True, slots=True)
class SweptPartEnvelope:
    part: NeedlePart
    collision_role: CollisionRole
    witness_points_global_mm: tuple[Vector3, ...]
    continuous_cover_radius_mm: float
    interpolation: str

    def __post_init__(self) -> None:
        _points(self.witness_points_global_mm, "witness_points_global_mm")
        if _finite(self.continuous_cover_radius_mm, "continuous_cover_radius_mm") < 0.0:
            raise ContractViolation("continuous cover radius cannot be negative")


def _swept_part_identity_payload(part: SweptPartEnvelope) -> dict[str, object]:
    return {
        "part": part.part,
        "collision_role": part.collision_role,
        "witness_points_global_mm": part.witness_points_global_mm,
        "continuous_cover_radius_mm": part.continuous_cover_radius_mm,
        "interpolation": part.interpolation,
    }


@lru_cache(maxsize=4)
def _sweep_identity_pair(
    state_geometry_ids: tuple[str, ...],
    parts: tuple[SweptPartEnvelope, ...],
    interpolation: str,
) -> tuple[str, str]:
    return _identity_pair(
        "m03_swept_needle_geometry",
        {
            "state_geometry_ids": state_geometry_ids,
            "parts": tuple(_swept_part_identity_payload(part) for part in parts),
            "interpolation": interpolation,
        },
    )


@dataclass(frozen=True, slots=True)
class SweptNeedleGeometry:
    sweep_id: str
    sweep_hash: str
    state_geometry_ids: tuple[str, ...]
    parts: tuple[SweptPartEnvelope, ...]
    interpolation: str

    def __post_init__(self) -> None:
        if not self.state_geometry_ids:
            raise ContractViolation("a sweep requires at least one geometry state")
        if tuple(item.part for item in self.parts) != tuple(NeedlePart):
            raise ContractViolation("swept geometry part ordering mismatch")
        expected_id, expected_hash = _sweep_identity_pair(
            self.state_geometry_ids,
            self.parts,
            self.interpolation,
        )
        if self.sweep_hash != expected_hash or self.sweep_id != expected_id:
            raise ContractViolation("swept geometry identity mismatch")

    def identity_payload(self) -> dict[str, object]:
        return {
            "state_geometry_ids": self.state_geometry_ids,
            "parts": self.parts,
            "interpolation": self.interpolation,
        }

    def part(self, name: NeedlePart) -> SweptPartEnvelope:
        return next(item for item in self.parts if item.part is name)

    @property
    def all_witness_points_global_mm(self) -> FloatArray:
        return np.concatenate(
            tuple(
                np.asarray(item.witness_points_global_mm, dtype=np.float64) for item in self.parts
            ),
            axis=0,
        )

    @property
    def maximum_cover_radius_mm(self) -> float:
        return max(item.continuous_cover_radius_mm for item in self.parts)


def make_swept_needle_geometry(
    geometries: Sequence[CompositeNeedleGeometry],
    *,
    interpolation: str = "linear_corresponding_surface_points",
) -> SweptNeedleGeometry:
    """Build a conservative witness cover across explicitly supplied path states."""

    return _make_swept_needle_geometry_cached(tuple(geometries), interpolation)


@lru_cache(maxsize=4)
def _make_swept_needle_geometry_cached(
    geometries: tuple[CompositeNeedleGeometry, ...],
    interpolation: str,
) -> SweptNeedleGeometry:
    if not geometries:
        raise ContractViolation("at least one composite geometry is required")
    if interpolation != "linear_corresponding_surface_points":
        raise ContractViolation("unsupported swept-geometry interpolation")
    swept_parts: list[SweptPartEnvelope] = []
    for part_name in NeedlePart:
        states = [item.part(part_name) for item in geometries]
        cardinalities = {len(item.surface_points_global_mm) for item in states}
        if len(cardinalities) != 1:
            raise ContractViolation("swept states require corresponding part sample cardinality")
        state_points = [
            np.asarray(item.surface_points_global_mm, dtype=np.float64) for item in states
        ]
        interstate_cover = 0.0
        for left, right in pairwise(state_points):
            interstate_cover = max(
                interstate_cover,
                0.5 * float(np.max(np.linalg.norm(right - left, axis=1))),
            )
        continuous_cover = max(item.surface_cover_radius_mm for item in states) + interstate_cover
        witnesses = tuple(point for state in states for point in state.surface_points_global_mm)
        swept_parts.append(
            SweptPartEnvelope(
                part_name,
                states[0].collision_role,
                witnesses,
                continuous_cover,
                interpolation,
            )
        )
    state_geometry_ids = tuple(item.geometry_id for item in geometries)
    resolved_parts = tuple(swept_parts)
    sweep_id, sweep_hash = _sweep_identity_pair(
        state_geometry_ids,
        resolved_parts,
        interpolation,
    )
    return SweptNeedleGeometry(
        sweep_id,
        sweep_hash,
        state_geometry_ids,
        resolved_parts,
        interpolation,
    )


__all__ = [
    "CENTERLINE_INTERFACE_ID",
    "COMPOSITE_GEOMETRY_ID",
    "POSE_CLOSURE_ID",
    "CenterlineGeometry",
    "CenterlineProvider",
    "CollisionRole",
    "CompositeNeedleGeometry",
    "ExplicitCenterlineProvider",
    "NeedlePart",
    "PartSurfaceEnvelope",
    "RigidCenterlineProvider",
    "SweptNeedleGeometry",
    "SweptPartEnvelope",
    "TipPose",
    "build_composite_needle_geometry",
    "engineering_initial_axis",
    "finite_cap_legality_margin_mm",
    "initial_needle_rotation",
    "is_finite_cap_legal",
    "make_swept_needle_geometry",
    "resolve_tip_pose",
    "rotation_matrix_from_global_vector",
    "sample_centerline",
]
