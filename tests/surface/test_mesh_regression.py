from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pytest

from spine_sim.foundation.errors import ContractViolation
from spine_sim.surface.analytic import AnalyticEvaluator
from spine_sim.surface.contracts import DomainStatus, QualityStatus, SurfaceFamily
from spine_sim.surface.mesh_regression import (
    HeightfieldTriangulationRegressionAdapter,
    heightfield_triangulation_regression_adapter,
)
from spine_sim.surface.provider import SurfaceProvider, make_analytic_source_descriptor


def _evaluator(family: SurfaceFamily, parameters: Mapping[str, object]) -> AnalyticEvaluator:
    provider = SurfaceProvider()
    descriptor = make_analytic_source_descriptor()
    creation = provider.create_surface_spec(descriptor, family, dict(parameters))
    assert creation.spec is not None, creation.status.explanation
    return AnalyticEvaluator(creation.spec)


def test_adapter_is_explicitly_validation_only_and_not_an_external_mesh_provider() -> None:
    adapter = HeightfieldTriangulationRegressionAdapter(
        _evaluator(SurfaceFamily.PLANE, {"offset_mm": 0.0}),
        window_mm=(70.0, 80.0, 70.0, 80.0),
        grid_shape=(5, 7),
    )
    assert adapter.provider_role == "VALIDATION_ONLY_REGRESSION_ADAPTER"
    assert adapter.accepts_external_mesh is False
    assert adapter.is_default_query_provider is False
    assert adapter.vertices.shape == (35, 3)
    assert adapter.triangles.shape == (48, 3)
    assert not adapter.vertices.flags.writeable
    assert not adapter.triangles.flags.writeable


def test_planar_mesh_closest_matches_exact_geometry_and_reports_co_minimal_facets() -> None:
    adapter = HeightfieldTriangulationRegressionAdapter(
        _evaluator(
            SurfaceFamily.SLOPE_PLANE,
            {"offset_mm": 0.5, "slope_x": 0.1, "slope_y": -0.05},
        ),
        window_mm=(70.0, 80.0, 70.0, 80.0),
        grid_shape=(11, 11),
    )
    query = np.array([75.0, 75.0, 4.5])
    result = adapter.closest_features([query], co_minimal_tolerance_mm=1.0e-10)
    normal = np.array([-0.1, 0.05, 1.0])
    normal /= np.linalg.norm(normal)
    signed = (query[2] - 0.5 - 0.1 * query[0] + 0.05 * query[1]) / math.sqrt(1.0 + 0.1**2 + 0.05**2)
    expected = query - signed * normal

    assert result.validity.tolist() == [True]
    assert result.domain_status == (DomainStatus.IN_DOMAIN,)
    np.testing.assert_allclose(result.closest_points_mm[0], expected, atol=2.0e-13)
    np.testing.assert_allclose(result.signed_distance_mm, [signed], atol=2.0e-13)
    assert result.triangle_residual_mm == 0.0
    assert result.analytic_discretization_bound_mm >= 0.0
    assert result.triangle_indices[0] in result.co_minimal_triangle_sets[0]
    assert result.outward_normal_sets[0]
    assert result.quality_status[0] in {
        QualityStatus.TRUSTED_FOR_DECLARED_SCALE,
        QualityStatus.NONSMOOTH_FEATURE_SET,
    }


def test_nonlinear_mesh_regression_converges_and_bound_tightens_with_spacing() -> None:
    evaluator = _evaluator(
        SurfaceFamily.GAUSSIAN_BUMP,
        {"amplitude_mm": 0.8, "sigma_x_mm": 1.2, "sigma_y_mm": 0.9},
    )
    window = (72.0, 78.0, 72.0, 78.0)
    query = [[75.31, 75.17, 1.4]]
    adapters = [
        HeightfieldTriangulationRegressionAdapter(
            evaluator, window_mm=window, grid_shape=(size, size)
        )
        for size in (9, 17, 33)
    ]
    results = [adapter.signed_distance(query) for adapter in adapters]
    bounds = [adapter.analytic_discretization_bound_mm for adapter in adapters]
    assert bounds[2] < bounds[1] < bounds[0]
    assert all(result.validity.tolist() == [True] for result in results)
    # The two finest validation meshes must agree within their declared analytic bounds.
    distance_delta = abs(
        float(results[-1].signed_distance_mm[0]) - float(results[-2].signed_distance_mm[0])
    )
    position_delta = np.linalg.norm(
        results[-1].closest_points_mm[0] - results[-2].closest_points_mm[0]
    )
    assert distance_delta <= bounds[-2] + bounds[-1]
    assert position_delta <= 2.0 * (bounds[-2] + bounds[-1])


def test_mesh_boundary_status_and_missing_values_are_explicit() -> None:
    adapter = HeightfieldTriangulationRegressionAdapter(
        _evaluator(SurfaceFamily.PLANE, {"offset_mm": 0.0}),
        window_mm=(70.0, 80.0, 70.0, 80.0),
        grid_shape=(9, 9),
    )
    result = adapter.closest_features([[75.0, 75.0, 1.0], [70.0, 75.0, 1.0], [69.99, 75.0, 1.0]])
    assert result.domain_status == (
        DomainStatus.IN_DOMAIN,
        DomainStatus.ON_BOUNDARY,
        DomainStatus.OUT_OF_DOMAIN,
    )
    assert result.validity.tolist() == [True, True, False]
    assert result.triangle_indices.tolist()[2] == -1
    assert result.co_minimal_triangle_sets[2] == ()
    assert result.outward_normal_sets[2] == ()
    assert result.quality_status[2] is QualityStatus.GEOMETRY_UNCERTAIN


def test_spacing_factory_is_deterministic_and_validates_configuration() -> None:
    evaluator = _evaluator(SurfaceFamily.PLANE, {"offset_mm": 0.0})
    first = heightfield_triangulation_regression_adapter(
        evaluator,
        window_mm=(70.0, 72.0, 70.0, 73.0),
        spacing_mm=0.5,
    )
    replay = heightfield_triangulation_regression_adapter(
        evaluator,
        window_mm=(70.0, 72.0, 70.0, 73.0),
        spacing_mm=0.5,
    )
    assert first.grid_shape == (7, 5)
    np.testing.assert_array_equal(first.vertices, replay.vertices)
    np.testing.assert_array_equal(first.triangles, replay.triangles)

    with pytest.raises(ContractViolation, match="grid_shape or spacing_mm"):
        heightfield_triangulation_regression_adapter(
            evaluator,
            grid_shape=(5, 5),
            spacing_mm=0.5,
        )
    with pytest.raises(ContractViolation, match="positive"):
        heightfield_triangulation_regression_adapter(evaluator, spacing_mm=0.0)
    with pytest.raises(ContractViolation, match="inside"):
        HeightfieldTriangulationRegressionAdapter(
            evaluator,
            window_mm=(-1.0, 2.0, 0.0, 2.0),
        )
    with pytest.raises(ContractViolation, match=r"\[2, 4097\]"):
        HeightfieldTriangulationRegressionAdapter(evaluator, grid_shape=(1, 3))
