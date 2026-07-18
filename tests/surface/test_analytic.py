from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pytest

from spine_sim.foundation.errors import ContractViolation
from spine_sim.surface.analytic import AnalyticEvaluator, validate_analytic_parameters
from spine_sim.surface.contracts import SurfaceFamily
from spine_sim.surface.provider import SurfaceProvider, make_analytic_source_descriptor

FAMILY_FIXTURES: tuple[tuple[SurfaceFamily, Mapping[str, object], tuple[float, float]], ...] = (
    (SurfaceFamily.PLANE, {"offset_mm": 0.4}, (73.2, 76.1)),
    (
        SurfaceFamily.SLOPE_PLANE,
        {"offset_mm": 0.4, "slope_x": 0.12, "slope_y": -0.07},
        (73.2, 76.1),
    ),
    (
        SurfaceFamily.SINUSOID_1D,
        {
            "amplitude_mm": 0.3,
            "wavelength_mm": 4.5,
            "direction_rad": 0.37,
            "phase_rad": 0.2,
        },
        (73.2, 76.1),
    ),
    (
        SurfaceFamily.SINUSOID_2D,
        {
            "amplitude_x_mm": 0.22,
            "amplitude_y_mm": 0.13,
            "wavelength_x_mm": 5.1,
            "wavelength_y_mm": 3.8,
            "direction_rad": 0.23,
            "phase_x_rad": 0.1,
            "phase_y_rad": -0.4,
        },
        (73.2, 76.1),
    ),
    (
        SurfaceFamily.GAUSSIAN_BUMP,
        {"amplitude_mm": 0.8, "sigma_x_mm": 1.4, "sigma_y_mm": 0.9},
        (75.4, 75.3),
    ),
    (
        SurfaceFamily.GAUSSIAN_PIT,
        {"amplitude_mm": 0.8, "sigma_x_mm": 1.4, "sigma_y_mm": 0.9},
        (75.4, 75.3),
    ),
    (
        SurfaceFamily.MULTI_GAUSSIAN_FEATURE,
        {
            "features": (
                {
                    "feature_id": "peak",
                    "amplitude_mm": 0.7,
                    "center_x_mm": 74.4,
                    "center_y_mm": 75.2,
                    "sigma_mm": 1.1,
                },
                {
                    "feature_id": "pit",
                    "amplitude_mm": -0.35,
                    "center_x_mm": 76.3,
                    "center_y_mm": 74.7,
                    "sigma_x_mm": 0.8,
                    "sigma_y_mm": 1.3,
                },
            )
        },
        (75.1, 75.6),
    ),
    (
        SurfaceFamily.GROOVE_COSINE,
        {"depth_mm": 0.7, "half_width_mm": 1.8, "direction_rad": 0.2},
        (74.7, 75.6),
    ),
    (
        SurfaceFamily.GROOVE_SMOOTH,
        {"depth_mm": 0.7, "sigma_mm": 0.8, "direction_rad": 0.2},
        (74.7, 75.6),
    ),
    (
        SurfaceFamily.GROOVE_CIRCULAR,
        {"depth_mm": 0.6, "half_width_mm": 1.4, "direction_rad": 0.2},
        (74.7, 75.6),
    ),
    (
        SurfaceFamily.GROOVE_V,
        {"depth_mm": 0.6, "half_width_mm": 1.4, "direction_rad": 0.2},
        (74.7, 75.6),
    ),
    (
        SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH,
        {"ridge_slope": 0.25, "direction_rad": 0.2},
        (74.7, 75.6),
    ),
    (
        SurfaceFamily.SPHERICAL_CAP,
        {"radius_mm": 3.0, "aperture_radius_mm": 1.5},
        (75.4, 75.3),
    ),
    (
        SurfaceFamily.SPHERICAL_BOWL,
        {"radius_mm": 3.0, "aperture_radius_mm": 1.5},
        (75.4, 75.3),
    ),
)


def _evaluator(family: SurfaceFamily, parameters: Mapping[str, object]) -> AnalyticEvaluator:
    provider = SurfaceProvider()
    descriptor = make_analytic_source_descriptor()
    creation = provider.create_surface_spec(descriptor, family, dict(parameters))
    assert creation.spec is not None, creation.status.explanation
    return AnalyticEvaluator(creation.spec)


@pytest.mark.parametrize(("family", "parameters", "point"), FAMILY_FIXTURES)
def test_all_analytic_families_have_consistent_height_differentials(
    family: SurfaceFamily,
    parameters: Mapping[str, object],
    point: tuple[float, float],
) -> None:
    evaluator = _evaluator(family, parameters)
    x_mm, y_mm = point
    step = 1.0e-5
    result = evaluator.evaluate(x_mm, y_mm, derivative_order=2)

    def height(x_value: float, y_value: float) -> float:
        return float(evaluator.evaluate(x_value, y_value, derivative_order=0).height[0])

    gradient_fd = np.array(
        [
            (height(x_mm + step, y_mm) - height(x_mm - step, y_mm)) / (2.0 * step),
            (height(x_mm, y_mm + step) - height(x_mm, y_mm - step)) / (2.0 * step),
        ]
    )
    gradient_x_plus = evaluator.evaluate(x_mm + step, y_mm, derivative_order=1).gradient[0]
    gradient_x_minus = evaluator.evaluate(x_mm - step, y_mm, derivative_order=1).gradient[0]
    gradient_y_plus = evaluator.evaluate(x_mm, y_mm + step, derivative_order=1).gradient[0]
    gradient_y_minus = evaluator.evaluate(x_mm, y_mm - step, derivative_order=1).gradient[0]
    hessian_fd = np.column_stack(
        (
            (gradient_x_plus - gradient_x_minus) / (2.0 * step),
            (gradient_y_plus - gradient_y_minus) / (2.0 * step),
        )
    )

    assert result.height.shape == (1,)
    assert result.points.shape == (1, 3)
    assert result.gradient.shape == (1, 2)
    assert result.hessian is not None
    np.testing.assert_allclose(result.points[0], (x_mm, y_mm, result.height[0]))
    np.testing.assert_allclose(result.gradient[0], gradient_fd, rtol=2.0e-5, atol=2.0e-7)
    np.testing.assert_allclose(result.hessian[0], hessian_fd, rtol=3.0e-4, atol=3.0e-6)
    expected_normal = np.array([-result.gradient[0, 0], -result.gradient[0, 1], 1.0])
    expected_normal /= np.linalg.norm(expected_normal)
    np.testing.assert_allclose(result.normal[0], expected_normal, atol=2.0e-15)
    assert result.normal[0, 2] > 0.0
    assert result.hessian_validity.tolist() == [True]
    assert result.curvature_validity.tolist() == [True]
    assert not result.nonsmooth_mask[0]

    assert result.mean_curvature is not None
    assert result.gaussian_curvature is not None
    assert result.principal_curvatures is not None
    np.testing.assert_allclose(
        result.principal_curvatures[0].sum(), 2.0 * result.mean_curvature[0], atol=2.0e-12
    )
    np.testing.assert_allclose(
        result.principal_curvatures[0].prod(), result.gaussian_curvature[0], atol=2.0e-12
    )
    assert not result.height.flags.writeable
    assert not result.gradient.flags.writeable


def test_plane_slope_and_gaussian_center_have_known_values_and_curvature() -> None:
    plane = _evaluator(SurfaceFamily.PLANE, {"height_mm": 1.25})
    plane_value = plane.evaluate([1.0, 2.0], [3.0, 4.0], derivative_order=2)
    np.testing.assert_array_equal(plane_value.height, [1.25, 1.25])
    np.testing.assert_array_equal(plane_value.gradient, np.zeros((2, 2)))
    np.testing.assert_array_equal(plane_value.principal_curvatures, np.zeros((2, 2)))

    slope = _evaluator(
        SurfaceFamily.SLOPE_PLANE,
        {"offset_mm": 0.5, "slope_x": 0.2, "slope_y": -0.1},
    )
    slope_value = slope.evaluate(3.0, 4.0, derivative_order=2)
    np.testing.assert_allclose(slope_value.height, [0.7])
    np.testing.assert_allclose(slope_value.gradient, [[0.2, -0.1]])
    np.testing.assert_array_equal(slope_value.principal_curvatures, np.zeros((1, 2)))

    bump = _evaluator(
        SurfaceFamily.GAUSSIAN_BUMP,
        {"offset_mm": 0.2, "amplitude_mm": 0.8, "sigma_mm": 2.0},
    )
    bump_center = bump.evaluate(75.0, 75.0, derivative_order=2)
    np.testing.assert_allclose(bump_center.height, [1.0])
    np.testing.assert_array_equal(bump_center.gradient, [[0.0, 0.0]])
    np.testing.assert_allclose(bump_center.hessian, [[[-0.2, 0.0], [0.0, -0.2]]])
    np.testing.assert_allclose(bump_center.principal_curvatures, [[-0.2, -0.2]])


@pytest.mark.parametrize(
    ("family", "parameters"),
    (
        (SurfaceFamily.PLANE, {"offset_mm": 0.0, "mystery": 1.0}),
        (SurfaceFamily.PLANE, {"height_mm": 0.0, "offset_mm": 0.0}),
        (SurfaceFamily.SINUSOID_1D, {"amplitude_mm": 1.0, "wavelength_mm": 0.0}),
        (
            SurfaceFamily.SINUSOID_2D,
            {"amplitude_mm": 1.0, "amplitude_x_mm": 1.0, "wavelength_mm": 2.0},
        ),
        (SurfaceFamily.GAUSSIAN_BUMP, {"amplitude_mm": -1.0, "sigma_mm": 1.0}),
        (SurfaceFamily.GAUSSIAN_PIT, {"amplitude_mm": 1.0, "sigma_x_mm": 1.0}),
        (SurfaceFamily.MULTI_GAUSSIAN_FEATURE, {"features": ()}),
        (SurfaceFamily.GROOVE_CIRCULAR, {"depth_mm": 2.0, "half_width_mm": 1.0}),
        (SurfaceFamily.GROOVE_SMOOTH, {"depth_mm": 1.0, "sigma_mm": math.inf}),
        (SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH, {"ridge_slope": 0.0}),
        (SurfaceFamily.SPHERICAL_CAP, {"radius_mm": 1.0, "aperture_radius_mm": 1.0}),
    ),
)
def test_strict_parameter_contract_rejects_unknown_ambiguous_or_invalid_values(
    family: SurfaceFamily, parameters: Mapping[str, object]
) -> None:
    with pytest.raises(ContractViolation):
        validate_analytic_parameters(family, parameters)


def test_nonsmooth_families_return_feature_sets_and_one_sided_normals() -> None:
    switch = _evaluator(
        SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH,
        {"ridge_slope": 0.4, "switch_tolerance_mm": 1.0e-12},
    )
    value = switch.evaluate([75.0, 75.0], [75.0, 75.25], derivative_order=2)
    assert value.nonsmooth_mask.tolist() == [True, False]
    assert set(value.feature_sets[0]) == {
        "switch_face_negative",
        "switch_face_positive",
        "switch_edge",
    }
    assert len(value.one_sided_gradients[0]) == 2
    assert len(value.one_sided_normals[0]) == 2
    assert value.hessian_validity.tolist() == [False, True]
    assert value.curvature_validity.tolist() == [False, True]

    v_groove = _evaluator(
        SurfaceFamily.GROOVE_V,
        {"depth_mm": 0.5, "half_width_mm": 1.0},
    )
    groove_value = v_groove.evaluate([75.0, 75.0, 75.0], [74.0, 75.0, 76.0], derivative_order=2)
    assert groove_value.nonsmooth_mask.tolist() == [True, True, True]
    assert "v_bottom_edge" in groove_value.feature_sets[1]
    assert groove_value.hessian_validity.tolist() == [False, False, False]


def test_spherical_patch_aperture_is_a_declared_nonsmooth_feature_not_missing_data() -> None:
    evaluator = _evaluator(
        SurfaceFamily.SPHERICAL_CAP,
        {"radius_mm": 4.0, "aperture_radius_mm": 2.0},
    )
    value = evaluator.evaluate([75.0, 77.0, 78.0], [75.0, 75.0, 75.0], derivative_order=2)
    assert value.validity.tolist() == [True, True, True]
    assert value.nonsmooth_mask.tolist() == [False, True, False]
    assert set(value.feature_sets[1]) == {"spherical_patch", "outside_plane", "aperture_ring"}
    np.testing.assert_allclose(value.height[2], 0.0)
