"""VALIDATION_ONLY height-field triangulation regression adapter.

The adapter is intentionally not a production surface provider and does not
accept arbitrary meshes or point clouds.  Its sole purpose is convergence
comparison against an already-defined analytic M01 height field.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from spine_sim.foundation.errors import ContractViolation

from .analytic import AnalyticEvaluator
from .contracts import DomainStatus, QualityStatus
from .query import _xyz_points

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]
IntArray = NDArray[np.int64]


@dataclass(frozen=True, slots=True)
class MeshRegressionClosestResult:
    """Exact triangle result with a discretization bound to the analytic field."""

    query_points_mm: FloatArray
    closest_points_mm: FloatArray
    signed_distance_mm: FloatArray
    triangle_indices: IntArray
    co_minimal_triangle_sets: tuple[tuple[int, ...], ...]
    outward_normal_sets: tuple[tuple[tuple[float, float, float], ...], ...]
    validity: BoolArray
    domain_status: tuple[DomainStatus, ...]
    quality_status: tuple[QualityStatus, ...]
    triangle_residual_mm: float
    analytic_discretization_bound_mm: float

    def __post_init__(self) -> None:
        for array in (
            self.query_points_mm,
            self.closest_points_mm,
            self.signed_distance_mm,
            self.triangle_indices,
            self.validity,
        ):
            array.setflags(write=False)


class HeightfieldTriangulationRegressionAdapter:
    """Immutable regular triangulation of an analytic evaluator."""

    __slots__ = (
        "evaluator",
        "grid_shape",
        "triangles",
        "vertices",
        "window_mm",
        "x_coordinates_mm",
        "y_coordinates_mm",
    )

    provider_role = "VALIDATION_ONLY_REGRESSION_ADAPTER"
    accepts_external_mesh = False
    is_default_query_provider = False

    def __init__(
        self,
        evaluator: AnalyticEvaluator,
        *,
        window_mm: tuple[float, float, float, float] | None = None,
        grid_shape: tuple[int, int] = (65, 65),
    ) -> None:
        domain = evaluator.spec.logical_domain
        window = window_mm or (
            domain.x_min_mm,
            domain.x_max_mm,
            domain.y_min_mm,
            domain.y_max_mm,
        )
        if len(window) != 4 or not all(math.isfinite(value) for value in window):
            raise ContractViolation("mesh-regression window must contain four finite bounds")
        x_min, x_max, y_min, y_max = window
        if x_max <= x_min or y_max <= y_min:
            raise ContractViolation("mesh-regression window must have positive extent")
        if not domain.contains(x_min, y_min) or not domain.contains(x_max, y_max):
            raise ContractViolation("mesh-regression window must stay inside the logical domain")
        if (
            len(grid_shape) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) for value in grid_shape)
            or min(grid_shape) < 2
            or max(grid_shape) > 4097
        ):
            raise ContractViolation(
                "mesh-regression grid_shape entries must be integers in [2, 4097]"
            )
        ny, nx = grid_shape
        x = np.linspace(x_min, x_max, nx, dtype=np.float64)
        y = np.linspace(y_min, y_max, ny, dtype=np.float64)
        xx, yy = np.meshgrid(x, y)
        height = evaluator.evaluate(xx.ravel(), yy.ravel(), derivative_order=0).height
        vertices = np.column_stack((xx.ravel(), yy.ravel(), height))
        triangles = np.empty((2 * (ny - 1) * (nx - 1), 3), dtype=np.int64)
        cursor = 0
        for row in range(ny - 1):
            for column in range(nx - 1):
                lower_left = row * nx + column
                lower_right = lower_left + 1
                upper_left = lower_left + nx
                upper_right = upper_left + 1
                triangles[cursor] = (lower_left, lower_right, upper_right)
                triangles[cursor + 1] = (lower_left, upper_right, upper_left)
                cursor += 2
        for array in (x, y, vertices, triangles):
            array.setflags(write=False)
        self.evaluator = evaluator
        self.window_mm = tuple(float(value) for value in window)
        self.grid_shape = grid_shape
        self.x_coordinates_mm = x
        self.y_coordinates_mm = y
        self.vertices = vertices
        self.triangles = triangles

    @property
    def maximum_spacing_mm(self) -> float:
        return max(
            float(np.max(np.diff(self.x_coordinates_mm))),
            float(np.max(np.diff(self.y_coordinates_mm))),
        )

    @property
    def analytic_discretization_bound_mm(self) -> float:
        return self.evaluator.global_slope_bound() * self.maximum_spacing_mm / math.sqrt(2.0)

    def closest_features(
        self,
        points_mm: ArrayLike,
        *,
        co_minimal_tolerance_mm: float = 1.0e-10,
    ) -> MeshRegressionClosestResult:
        if not math.isfinite(co_minimal_tolerance_mm) or co_minimal_tolerance_mm < 0.0:
            raise ContractViolation("co_minimal_tolerance_mm must be finite and non-negative")
        queries = _xyz_points(points_mm)
        closest = np.zeros_like(queries)
        signed = np.zeros(len(queries), dtype=np.float64)
        representative = np.full(len(queries), -1, dtype=np.int64)
        validity = np.zeros(len(queries), dtype=np.bool_)
        triangle_sets: list[tuple[int, ...]] = [() for _ in queries]
        normal_sets: list[tuple[tuple[float, float, float], ...]] = [() for _ in queries]
        statuses: list[DomainStatus] = []
        qualities: list[QualityStatus] = []
        x_min, x_max, y_min, y_max = self.window_mm
        triangle_vertices = self.vertices[self.triangles]
        raw_normals = np.cross(
            triangle_vertices[:, 1] - triangle_vertices[:, 0],
            triangle_vertices[:, 2] - triangle_vertices[:, 0],
        )
        raw_norms = np.linalg.norm(raw_normals, axis=1)
        normals = raw_normals / raw_norms[:, None]
        for query_index, query in enumerate(queries):
            x_value, y_value = query[:2]
            inside = x_min <= x_value <= x_max and y_min <= y_value <= y_max
            if not inside:
                statuses.append(DomainStatus.OUT_OF_DOMAIN)
                qualities.append(QualityStatus.GEOMETRY_UNCERTAIN)
                continue
            on_boundary = x_value in (x_min, x_max) or y_value in (y_min, y_max)
            statuses.append(DomainStatus.ON_BOUNDARY if on_boundary else DomainStatus.IN_DOMAIN)
            candidates = np.empty_like(triangle_vertices[:, 0])
            distances = np.empty(len(self.triangles), dtype=np.float64)
            for triangle_index, triangle in enumerate(triangle_vertices):
                point = _closest_point_triangle(query, triangle[0], triangle[1], triangle[2])
                candidates[triangle_index] = point
                distances[triangle_index] = np.linalg.norm(point - query)
            minimum = float(np.min(distances))
            selected = np.flatnonzero(distances <= minimum + co_minimal_tolerance_mm)
            first = int(selected[0])
            closest[query_index] = candidates[first]
            height = float(
                self.evaluator.evaluate(query[0], query[1], derivative_order=0).height[0]
            )
            signed[query_index] = minimum if query[2] >= height else -minimum
            representative[query_index] = first
            triangle_sets[query_index] = tuple(int(value) for value in selected)
            unique_normals: list[tuple[float, float, float]] = sorted(
                {
                    (
                        float(normals[value, 0]),
                        float(normals[value, 1]),
                        float(normals[value, 2]),
                    )
                    for value in selected
                }
            )
            normal_sets[query_index] = tuple(unique_normals)
            validity[query_index] = True
            qualities.append(
                QualityStatus.NONSMOOTH_FEATURE_SET
                if len(unique_normals) > 1
                else QualityStatus.TRUSTED_FOR_DECLARED_SCALE
            )
        return MeshRegressionClosestResult(
            np.array(queries, copy=True),
            closest,
            signed,
            representative,
            tuple(triangle_sets),
            tuple(normal_sets),
            validity,
            tuple(statuses),
            tuple(qualities),
            0.0,
            self.analytic_discretization_bound_mm,
        )

    def signed_distance(self, points_mm: ArrayLike) -> MeshRegressionClosestResult:
        return self.closest_features(points_mm)


def _closest_point_triangle(
    point: FloatArray, first: FloatArray, second: FloatArray, third: FloatArray
) -> FloatArray:
    """Ericson region-test closest point, including edges and vertices."""

    ab = second - first
    ac = third - first
    ap = point - first
    d1 = float(np.dot(ab, ap))
    d2 = float(np.dot(ac, ap))
    if d1 <= 0.0 and d2 <= 0.0:
        return first.copy()
    bp = point - second
    d3 = float(np.dot(ab, bp))
    d4 = float(np.dot(ac, bp))
    if d3 >= 0.0 and d4 <= d3:
        return second.copy()
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        fraction = d1 / (d1 - d3)
        return first + fraction * ab
    cp = point - third
    d5 = float(np.dot(ab, cp))
    d6 = float(np.dot(ac, cp))
    if d6 >= 0.0 and d5 <= d6:
        return third.copy()
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        fraction = d2 / (d2 - d6)
        return first + fraction * ac
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and d4 - d3 >= 0.0 and d5 - d6 >= 0.0:
        fraction = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return second + fraction * (third - second)
    denominator = 1.0 / (va + vb + vc)
    v_value = vb * denominator
    w_value = vc * denominator
    return first + ab * v_value + ac * w_value


def heightfield_triangulation_regression_adapter(
    evaluator: AnalyticEvaluator,
    *,
    window_mm: tuple[float, float, float, float] | None = None,
    grid_shape: tuple[int, int] | None = None,
    spacing_mm: float | None = None,
) -> HeightfieldTriangulationRegressionAdapter:
    """Create the frozen validation-only adapter from an analytic definition."""

    if grid_shape is not None and spacing_mm is not None:
        raise ContractViolation("specify grid_shape or spacing_mm, not both")
    domain = evaluator.spec.logical_domain
    window = window_mm or (
        domain.x_min_mm,
        domain.x_max_mm,
        domain.y_min_mm,
        domain.y_max_mm,
    )
    if spacing_mm is not None:
        if not math.isfinite(spacing_mm) or spacing_mm <= 0.0:
            raise ContractViolation("spacing_mm must be finite and positive")
        nx = math.ceil((window[1] - window[0]) / spacing_mm) + 1
        ny = math.ceil((window[3] - window[2]) / spacing_mm) + 1
        grid_shape = (ny, nx)
    return HeightfieldTriangulationRegressionAdapter(
        evaluator,
        window_mm=window,
        grid_shape=(65, 65) if grid_shape is None else grid_shape,
    )


__all__ = [
    "HeightfieldTriangulationRegressionAdapter",
    "MeshRegressionClosestResult",
    "heightfield_triangulation_regression_adapter",
]
