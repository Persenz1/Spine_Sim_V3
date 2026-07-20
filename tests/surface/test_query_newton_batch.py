from __future__ import annotations

import heapq
import math
from typing import Any

import numpy as np
import pytest

from spine_sim.foundation.canonical import semantic_hash
from spine_sim.surface import (
    SurfaceFamily,
    SurfaceProvider,
    SurfaceQuery,
    make_latent_noise_identity,
    make_synthetic_source_descriptor,
    query_spherical_envelope_or_clearance,
    synthetic_parameters_for_tier,
)
from spine_sim.surface import query as query_module
from spine_sim.surface.query import (
    _adaptive_global_lower_bound,
    _adaptive_global_lower_bounds,
    _interval_distance,
    _project_graph_newton,
    _project_graph_newton_many,
    _project_graph_newton_pairs,
)


class _CountingEvaluator:
    def __init__(self, delegate: Any) -> None:
        self.delegate = delegate
        self.spec = delegate.spec
        self.family = delegate.family
        self.calls = 0

    def evaluate(self, *args: Any, **kwargs: Any) -> Any:
        self.calls += 1
        return self.delegate.evaluate(*args, **kwargs)

    def global_slope_bound(self) -> float:
        return float(self.delegate.global_slope_bound())


def _synthetic_query() -> SurfaceQuery:
    provider = SurfaceProvider()
    descriptor = make_synthetic_source_descriptor()
    creation = provider.create_surface_spec(
        descriptor,
        SurfaceFamily.SELF_AFFINE_GAUSSIAN,
        synthetic_parameters_for_tier("medium", modes_per_band=4),
    )
    realization = provider.create_realization(
        descriptor,
        creation.spec,
        latent_identity=make_latent_noise_identity(0xA17E, 3),
    )
    assert realization.handle is not None
    return SurfaceQuery(realization.handle)


def test_batched_newton_is_bitwise_equivalent_and_reduces_evaluator_calls() -> None:
    evaluator = _synthetic_query().evaluator
    query = np.array([25.0, 75.0, 0.3], dtype=np.float64)
    starts = np.array(
        [[x, y] for x in (0.0, 25.0, 50.0, 75.0) for y in (25.0, 75.0)],
        dtype=np.float64,
    )

    scalar_evaluator = _CountingEvaluator(evaluator)
    scalar = [
        _project_graph_newton(scalar_evaluator, query, start)  # type: ignore[arg-type]
        for start in starts
    ]
    scalar_points = np.asarray([item[0] for item in scalar])
    scalar_residuals = np.asarray([item[1] for item in scalar])

    batched_evaluator = _CountingEvaluator(evaluator)
    batched_points, batched_residuals = _project_graph_newton_many(
        batched_evaluator,  # type: ignore[arg-type]
        query,
        starts,
    )

    np.testing.assert_array_equal(batched_points, scalar_points)
    np.testing.assert_array_equal(batched_residuals, scalar_residuals)
    assert batched_evaluator.calls <= scalar_evaluator.calls // 2


def test_public_closest_response_matches_scalar_newton_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query = _synthetic_query()
    points = [
        [25.0, 75.0, 0.3],
        [25.2, 75.0, 0.3],
        [24.8, 75.0, 0.3],
        [25.0, 75.2, 0.3],
        [25.0, 74.8, 0.3],
    ]
    optimized = query.query_closest_features(
        points,
        requested_tolerance_mm=0.2,
        maximum_global_cells=16,
    )

    def scalar_many(
        evaluator: Any,
        target: np.ndarray,
        starts: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        results = [_project_graph_newton(evaluator, target, start) for start in starts]
        return (
            np.asarray([item[0] for item in results]),
            np.asarray([item[1] for item in results]),
        )

    def scalar_bounds(
        evaluator: Any,
        targets: np.ndarray,
        upper_distances: np.ndarray,
        tolerance: float,
        maximum_cells: int,
    ) -> tuple[tuple[float, int], ...]:
        return tuple(
            _scalar_global_lower_bound(
                evaluator,
                target,
                upper_distance=float(upper_distance),
                tolerance=tolerance,
                maximum_cells=maximum_cells,
            )
            for target, upper_distance in zip(targets, upper_distances, strict=True)
        )

    def independent_local_candidates(
        evaluator: Any,
        targets: np.ndarray,
        *,
        co_minimal_tolerance_mm: float,
    ) -> tuple[Any, ...]:
        return tuple(
            query_module._approximate_local_candidates(
                evaluator,
                target,
                co_minimal_tolerance_mm=co_minimal_tolerance_mm,
            )
            for target in targets
        )

    monkeypatch.setattr(query_module, "_project_graph_newton_many", scalar_many)
    monkeypatch.setattr(query_module, "_adaptive_global_lower_bounds", scalar_bounds)
    monkeypatch.setattr(
        query_module,
        "_approximate_local_candidates_many",
        independent_local_candidates,
    )
    reference = query.query_closest_features(
        points,
        requested_tolerance_mm=0.2,
        maximum_global_cells=16,
    )

    assert semantic_hash(optimized) == semantic_hash(reference)


def test_batched_distinct_query_newton_matches_independent_scalar_solves() -> None:
    evaluator = _synthetic_query().evaluator
    targets = np.array(
        [
            [25.0, 75.0, 0.3],
            [25.2, 75.0, 0.3],
            [24.8, 75.0, 0.3],
            [25.0, 75.2, 0.3],
        ],
        dtype=np.float64,
    )
    starts = np.array(
        [[20.0, 70.0], [30.0, 70.0], [20.0, 80.0], [30.0, 80.0]],
        dtype=np.float64,
    )
    scalar_evaluator = _CountingEvaluator(evaluator)
    scalar = [
        _project_graph_newton(scalar_evaluator, target, start)  # type: ignore[arg-type]
        for target, start in zip(targets, starts, strict=True)
    ]
    batched_evaluator = _CountingEvaluator(evaluator)
    points, residuals = _project_graph_newton_pairs(
        batched_evaluator,  # type: ignore[arg-type]
        targets,
        starts,
    )

    np.testing.assert_array_equal(points, np.asarray([item[0] for item in scalar]))
    np.testing.assert_array_equal(residuals, np.asarray([item[1] for item in scalar]))
    assert batched_evaluator.calls < scalar_evaluator.calls


def test_global_cell_bounds_batch_siblings_without_changing_result() -> None:
    evaluator = _synthetic_query().evaluator
    query = np.array([25.0, 75.0, 0.3], dtype=np.float64)

    scalar_evaluator = _CountingEvaluator(evaluator)
    scalar = _scalar_global_lower_bound(
        scalar_evaluator,
        query,
        upper_distance=0.4,
        tolerance=1.0e-8,
        maximum_cells=64,
    )
    batched_evaluator = _CountingEvaluator(evaluator)
    batched = _adaptive_global_lower_bound(
        batched_evaluator,  # type: ignore[arg-type]
        query,
        upper_distance=0.4,
        tolerance=1.0e-8,
        maximum_cells=64,
    )

    assert batched == scalar
    assert batched_evaluator.calls * 3 < scalar_evaluator.calls


def test_global_cell_bounds_batch_queries_without_changing_each_heap() -> None:
    evaluator = _synthetic_query().evaluator
    queries = np.array(
        [
            [25.0, 75.0, 0.3],
            [25.2, 75.0, 0.3],
            [24.8, 75.0, 0.3],
            [25.0, 75.2, 0.3],
            [25.0, 74.8, 0.3],
        ],
        dtype=np.float64,
    )
    upper_distances = np.full(len(queries), 0.4, dtype=np.float64)

    scalar_evaluator = _CountingEvaluator(evaluator)
    scalar = tuple(
        _scalar_global_lower_bound(
            scalar_evaluator,
            query,
            upper_distance=float(upper_distance),
            tolerance=1.0e-8,
            maximum_cells=64,
        )
        for query, upper_distance in zip(queries, upper_distances, strict=True)
    )
    batched_evaluator = _CountingEvaluator(evaluator)
    batched = _adaptive_global_lower_bounds(
        batched_evaluator,  # type: ignore[arg-type]
        queries,
        upper_distances,
        tolerance=1.0e-8,
        maximum_cells=64,
    )

    assert batched == scalar
    assert batched_evaluator.calls * 4 <= scalar_evaluator.calls


def test_signed_distance_can_reuse_identical_closest_receipt_without_semantic_change() -> None:
    query = _synthetic_query()
    points = np.array(
        [[25.0, 75.0, 0.3], [25.2, 75.0, 0.3]],
        dtype=np.float64,
    )
    options = {
        "requested_tolerance_mm": 0.2,
        "co_minimal_tolerance_mm": 1.0e-9,
        "maximum_global_cells": 16,
    }
    closest = query.query_closest_features(points, **options)

    signed_reference = query.query_signed_distance(points, **options)
    signed_reused = query.query_signed_distance(
        points,
        **options,
        _precomputed_closest_response=closest,
    )
    sphere_reference = query_spherical_envelope_or_clearance(
        query,
        points,
        0.2,
        path="phi_minus_radius",
        **options,
    )
    sphere_reused = query_spherical_envelope_or_clearance(
        query,
        points,
        0.2,
        path="phi_minus_radius",
        **options,
        _precomputed_closest_response=closest,
    )

    assert semantic_hash(signed_reused) == semantic_hash(signed_reference)
    assert semantic_hash(sphere_reused) == semantic_hash(sphere_reference)


def _scalar_global_lower_bound(
    evaluator: Any,
    query: np.ndarray,
    upper_distance: float,
    tolerance: float,
    maximum_cells: int,
) -> tuple[float, int]:
    domain = evaluator.spec.logical_domain
    slope_bound = evaluator.global_slope_bound()
    serial = 0
    heap: list[tuple[float, int, tuple[float, float, float, float]]] = []

    def bound(cell: tuple[float, float, float, float]) -> float:
        x0, x1, y0, y1 = cell
        xc = 0.5 * (x0 + x1)
        yc = 0.5 * (y0 + y1)
        height = float(evaluator.evaluate(xc, yc, derivative_order=0).height[0])
        radius = 0.5 * math.hypot(x1 - x0, y1 - y0)
        z0 = height - slope_bound * radius
        z1 = height + slope_bound * radius
        dx = _interval_distance(float(query[0]), x0, x1)
        dy = _interval_distance(float(query[1]), y0, y1)
        dz = _interval_distance(float(query[2]), z0, z1)
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    initial = (domain.x_min_mm, domain.x_max_mm, domain.y_min_mm, domain.y_max_mm)
    heapq.heappush(heap, (bound(initial), serial, initial))
    created = 1
    while heap and created < maximum_cells:
        lower_bound, _, cell = heap[0]
        if upper_distance - lower_bound <= tolerance:
            break
        heapq.heappop(heap)
        x0, x1, y0, y1 = cell
        if max(x1 - x0, y1 - y0) <= np.finfo(np.float64).eps * 1024:
            heapq.heappush(heap, (lower_bound, serial, cell))
            break
        xm = 0.5 * (x0 + x1)
        ym = 0.5 * (y0 + y1)
        for child in (
            (x0, xm, y0, ym),
            (xm, x1, y0, ym),
            (x0, xm, ym, y1),
            (xm, x1, ym, y1),
        ):
            child_bound = bound(child)
            created += 1
            serial += 1
            if child_bound <= upper_distance:
                heapq.heappush(heap, (child_bound, serial, child))
    return min((item[0] for item in heap), default=upper_distance), created
