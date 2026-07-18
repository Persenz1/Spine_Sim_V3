from __future__ import annotations

import math
from concurrent.futures import ThreadPoolExecutor
from itertools import pairwise

import numpy as np
import pytest

from spine_sim.surface import (
    SurfaceFamily,
    SurfaceProvider,
    make_latent_noise_identity,
    make_synthetic_source_descriptor,
)
from spine_sim.surface.rng import Philox4x64
from spine_sim.surface.synthetic import (
    SyntheticEvaluator,
    synthetic_parameters_for_tier,
)

_ROOT_SEED = 0x0123456789ABCDEF
_LATENT_NAMESPACE = "m01.surface.latent.synthetic-tests"
_TEST_LAMBDA_MIN_MM = 4.6875
_TEST_MODES_PER_BAND = 24
_COEFFICIENT_ROLE = "real_fourier_cos_sin_pair_v1"


def _make_spec(tier: str = "medium", **overrides: object):
    parameters = synthetic_parameters_for_tier(
        tier,
        lambda_min_declared_trust_mm=_TEST_LAMBDA_MIN_MM,
        modes_per_band=_TEST_MODES_PER_BAND,
    )
    parameters.update(overrides)
    result = SurfaceProvider().create_surface_spec(
        make_synthetic_source_descriptor(),
        SurfaceFamily.SELF_AFFINE_GAUSSIAN,
        parameters,
    )
    assert result.spec is not None
    return result.spec


def _make_evaluator(tier: str = "medium", *, seed_index: int = 7) -> SyntheticEvaluator:
    return SyntheticEvaluator(
        _make_spec(tier),
        make_latent_noise_identity(
            _ROOT_SEED,
            seed_index,
            latent_noise_namespace=_LATENT_NAMESPACE,
        ),
    )


def _mode_q(evaluator: SyntheticEvaluator) -> np.ndarray:
    return np.hypot(
        evaluator.mode_coordinates[:, 0],
        evaluator.mode_coordinates[:, 1],
    ) * (math.tau / 150.0)


def test_query_order_crop_and_periodic_parent_are_bitwise_invariant() -> None:
    evaluator = _make_evaluator()
    x = np.array([0.125, 17.25, 44.75, 88.125, 149.875, 37.5])
    y = np.array([149.5, 39.5, 91.25, 0.75, 71.125, 112.0])
    whole = evaluator.evaluate(x, y, derivative_order=2)
    permutation = np.array([4, 1, 5, 0, 3, 2])
    shuffled = evaluator.evaluate(x[permutation], y[permutation], derivative_order=2)

    np.testing.assert_array_equal(shuffled.height, whole.height[permutation])
    np.testing.assert_array_equal(shuffled.gradient, whole.gradient[permutation])
    np.testing.assert_array_equal(shuffled.hessian, whole.hessian[permutation])
    cropped = evaluator.evaluate(x[1:5], y[1:5], derivative_order=2)
    np.testing.assert_array_equal(cropped.height, whole.height[1:5])
    np.testing.assert_array_equal(cropped.gradient, whole.gradient[1:5])
    np.testing.assert_array_equal(cropped.hessian, whole.hessian[1:5])
    scalar = evaluator.evaluate(float(x[2]), float(y[2]), derivative_order=2)
    np.testing.assert_array_equal(scalar.height, whole.height[2:3])
    np.testing.assert_array_equal(scalar.gradient, whole.gradient[2:3])
    np.testing.assert_array_equal(scalar.hessian, whole.hessian[2:3])

    periodic = evaluator.evaluate(x + 150.0, y - 300.0, derivative_order=2)
    np.testing.assert_allclose(periodic.height, whole.height, rtol=0.0, atol=3.0e-15)
    np.testing.assert_allclose(periodic.gradient, whole.gradient, rtol=0.0, atol=3.0e-15)
    np.testing.assert_allclose(periodic.hessian, whole.hessian, rtol=0.0, atol=3.0e-15)


def test_serial_and_parallel_queries_are_bitwise_identical() -> None:
    evaluator = _make_evaluator()
    x = np.linspace(0.125, 149.875, 96, dtype=np.float64)
    y = np.remainder(x * 0.731 + 17.0, 150.0)
    serial = evaluator.evaluate(x, y, derivative_order=2)
    chunks = tuple(np.array_split(np.arange(x.size), 4))

    def evaluate_chunk(indices: np.ndarray):
        return evaluator.evaluate(x[indices], y[indices], derivative_order=2)

    with ThreadPoolExecutor(max_workers=4) as executor:
        parallel_chunks = tuple(executor.map(evaluate_chunk, chunks))

    np.testing.assert_array_equal(
        np.concatenate([item.height for item in parallel_chunks]), serial.height
    )
    np.testing.assert_array_equal(
        np.concatenate([item.gradient for item in parallel_chunks]), serial.gradient
    )
    np.testing.assert_array_equal(
        np.concatenate([item.hessian for item in parallel_chunks]), serial.hessian
    )


def test_gentle_medium_sharp_share_exact_latent_innovations_for_crn() -> None:
    evaluators = [_make_evaluator(tier) for tier in ("gentle", "medium", "sharp")]
    reference = evaluators[0]
    assert all(
        np.array_equal(item.mode_coordinates, reference.mode_coordinates) for item in evaluators[1:]
    )
    assert [item.parameters.Sq_mm for item in evaluators] == [0.0125, 0.05, 0.2]
    assert [item.parameters.H for item in evaluators] == [0.9, 0.7, 0.5]
    assert tuple(b.global_mode_coordinate_hash for b in reference.band_manifests) == tuple(
        b.global_mode_coordinate_hash for b in evaluators[1].band_manifests
    )

    for evaluator in evaluators:
        expected_cos = np.empty(evaluator.mode_count)
        expected_sin = np.empty(evaluator.mode_count)
        for band in evaluator.band_manifests:
            rng = Philox4x64.from_latent_identity(
                evaluator.latent_identity,
                band.band_id,
                _COEFFICIENT_ROLE,
            )
            for index in range(
                band.first_mode_ordinal,
                band.last_mode_ordinal_exclusive,
            ):
                mode_x, mode_y = evaluator.mode_coordinates[index]
                expected_cos[index], expected_sin[index] = rng.normal_pair(
                    int(mode_x),
                    int(mode_y),
                )
        scale = np.sqrt(evaluator.target_mode_variance_mm2)
        np.testing.assert_allclose(
            evaluator.coefficient_cos_mm / scale,
            expected_cos,
            rtol=2.0e-16,
            atol=2.0e-16,
        )
        np.testing.assert_allclose(
            evaluator.coefficient_sin_mm / scale,
            expected_sin,
            rtol=2.0e-16,
            atol=2.0e-16,
        )

    innovations = [
        item.coefficient_cos_mm / np.sqrt(item.target_mode_variance_mm2) for item in evaluators
    ]
    np.testing.assert_allclose(innovations[0], innovations[1], rtol=3.0e-16, atol=3.0e-16)
    np.testing.assert_allclose(innovations[0], innovations[2], rtol=3.0e-16, atol=3.0e-16)


def test_octave_bands_and_q_cutoff_form_nested_lods() -> None:
    evaluator = _make_evaluator()
    manifests = evaluator.band_manifests
    assert len(manifests) >= 4
    assert tuple(item.band_id for item in manifests) == tuple(range(len(manifests)))
    assert all(
        math.isclose(left.q_max_rad_per_mm, right.q_min_rad_per_mm)
        for left, right in pairwise(manifests)
    )
    assert all(
        item.first_mode_ordinal
        == (0 if index == 0 else manifests[index - 1].last_mode_ordinal_exclusive)
        for index, item in enumerate(manifests)
    )

    x = np.array([4.0, 19.5, 72.25, 141.0])
    y = np.array([11.0, 83.5, 38.75, 121.0])
    low_cutoff = manifests[1].q_max_rad_per_mm * (1.0 - 1.0e-12)
    medium_cutoff = manifests[3].q_max_rad_per_mm * (1.0 - 1.0e-12)
    low = evaluator.evaluate(x, y, q_max_rad_per_mm=low_cutoff)
    medium = evaluator.evaluate(x, y, q_max_rad_per_mm=medium_cutoff)
    full = evaluator.evaluate(x, y)

    assert set(low.active_band_ids) < set(medium.active_band_ids) < set(full.active_band_ids)
    assert (
        low.omitted_bounds.omitted_mode_count
        > medium.omitted_bounds.omitted_mode_count
        > full.omitted_bounds.omitted_mode_count
        == 0
    )
    assert low.omitted_bounds.height_bound_mm >= medium.omitted_bounds.height_bound_mm
    np.testing.assert_array_equal(
        low.height,
        evaluator.evaluate(x, y, q_max_rad_per_mm=low_cutoff).height,
    )

    none = evaluator.evaluate(x, y, q_max_rad_per_mm=0.0)
    np.testing.assert_array_equal(none.height, np.zeros(x.size))
    np.testing.assert_array_equal(none.gradient, np.zeros((x.size, 2)))
    np.testing.assert_array_equal(none.hessian, np.zeros((x.size, 2, 2)))
    assert none.active_band_ids == ()
    assert none.omitted_bounds.omitted_mode_count == evaluator.mode_count


def test_q_cutoff_matches_direct_sum_over_global_modes() -> None:
    evaluator = _make_evaluator()
    cutoff = evaluator.band_manifests[2].q_max_rad_per_mm * 0.87
    x, y = 37.125, 91.75
    result = evaluator.evaluate(x, y, derivative_order=2, q_max_rad_per_mm=cutoff)
    mode_q = _mode_q(evaluator)
    selected = mode_q <= cutoff
    qx = evaluator.mode_coordinates[:, 0] * (math.tau / 150.0)
    qy = evaluator.mode_coordinates[:, 1] * (math.tau / 150.0)
    phase = qx * x + qy * y
    in_phase = evaluator.coefficient_cos_mm * np.cos(phase) + evaluator.coefficient_sin_mm * np.sin(
        phase
    )
    quadrature = -evaluator.coefficient_cos_mm * np.sin(
        phase
    ) + evaluator.coefficient_sin_mm * np.cos(phase)
    expected_height = float(np.sum(in_phase[selected]))
    expected_gradient = np.array(
        [np.sum(qx[selected] * quadrature[selected]), np.sum(qy[selected] * quadrature[selected])]
    )
    expected_hessian = -np.array(
        [
            [
                np.sum(qx[selected] ** 2 * in_phase[selected]),
                np.sum(qx[selected] * qy[selected] * in_phase[selected]),
            ],
            [
                np.sum(qx[selected] * qy[selected] * in_phase[selected]),
                np.sum(qy[selected] ** 2 * in_phase[selected]),
            ],
        ]
    )
    np.testing.assert_allclose(result.height[0], expected_height, rtol=0.0, atol=2.0e-17)
    np.testing.assert_allclose(result.gradient[0], expected_gradient, rtol=0.0, atol=2.0e-17)
    np.testing.assert_allclose(result.hessian[0], expected_hessian, rtol=0.0, atol=2.0e-17)


def test_analytic_derivatives_match_centered_finite_differences() -> None:
    evaluator = _make_evaluator()
    x, y = 47.125, 81.375
    step = 1.0e-4
    exact = evaluator.evaluate(x, y, derivative_order=2)
    x_plus = evaluator.evaluate(x + step, y, derivative_order=1)
    x_minus = evaluator.evaluate(x - step, y, derivative_order=1)
    y_plus = evaluator.evaluate(x, y + step, derivative_order=1)
    y_minus = evaluator.evaluate(x, y - step, derivative_order=1)
    finite_gradient = np.array(
        [
            (x_plus.height[0] - x_minus.height[0]) / (2.0 * step),
            (y_plus.height[0] - y_minus.height[0]) / (2.0 * step),
        ]
    )
    finite_hessian = np.column_stack(
        (
            (x_plus.gradient[0] - x_minus.gradient[0]) / (2.0 * step),
            (y_plus.gradient[0] - y_minus.gradient[0]) / (2.0 * step),
        )
    )
    np.testing.assert_allclose(exact.gradient[0], finite_gradient, rtol=0.0, atol=1.0e-9)
    np.testing.assert_allclose(exact.hessian[0], finite_hessian, rtol=0.0, atol=1.0e-9)
    assert exact.hessian[0, 0, 1] == exact.hessian[0, 1, 0]


def test_zero_mode_hermitian_parseval_psd_and_spatial_statistics() -> None:
    evaluator = _make_evaluator()
    statistics = evaluator.statistics
    assert not np.any(np.all(evaluator.mode_coordinates == 0, axis=1))
    assert statistics.target_mean_mm == statistics.realized_mean_mm == 0.0
    assert statistics.zero_mode_coefficient_mm == 0.0
    assert statistics.hermitian_relative_residual == 0.0
    assert statistics.imaginary_relative_residual == 0.0
    assert statistics.parseval_relative_error == 0.0
    assert statistics.target_normalization_relative_error <= 3.0e-16
    assert math.isclose(
        sum(item.integrated_variance_mm2 for item in statistics.target_psd),
        statistics.target_variance_mm2,
        rel_tol=3.0e-16,
    )
    assert math.isclose(
        sum(item.integrated_variance_mm2 for item in statistics.realized_psd),
        statistics.realized_variance_mm2,
        rel_tol=3.0e-16,
    )
    assert all(left.psd_mm4 >= right.psd_mm4 for left, right in pairwise(statistics.target_psd))
    assert math.isclose(
        sum(item.fraction_of_variance for item in statistics.target_directional_spectrum),
        1.0,
        rel_tol=3.0e-16,
    )

    positive = (evaluator.coefficient_cos_mm - 1j * evaluator.coefficient_sin_mm) / 2.0
    negative = np.conjugate(positive)
    assert np.array_equal(negative, np.conjugate(positive))
    complex_parseval = float(np.sum(np.abs(positive) ** 2 + np.abs(negative) ** 2))
    assert math.isclose(
        complex_parseval,
        statistics.parseval_variance_mm2,
        rel_tol=3.0e-16,
    )

    coordinates = np.arange(128, dtype=np.float64) * (150.0 / 128.0)
    grid = evaluator.evaluate_grid(coordinates, coordinates, derivative_order=0)
    height = grid.height_in_query_shape()
    assert abs(float(np.mean(height))) <= 2.0e-17
    assert math.isclose(
        float(np.mean(height * height)),
        statistics.realized_variance_mm2,
        rel_tol=2.0e-14,
    )


@pytest.mark.parametrize("tier", ["gentle", "medium", "sharp"])
def test_target_statistics_track_frozen_tier_scale(tier: str) -> None:
    evaluator = _make_evaluator(tier)
    assert evaluator.statistics.target_Sq_mm == evaluator.parameters.Sq_mm
    assert evaluator.statistics.target_variance_mm2 == evaluator.parameters.Sq_mm**2
    assert evaluator.statistics.represented_target_variance_mm2 == pytest.approx(
        evaluator.parameters.Sq_mm**2,
        rel=3.0e-16,
    )
    assert sum(item.target_variance_mm2 for item in evaluator.band_manifests) == pytest.approx(
        evaluator.parameters.Sq_mm**2,
        rel=3.0e-16,
    )


def test_seed_ensemble_has_gaussian_marginal_with_stable_moment_bounds() -> None:
    spec = _make_spec()
    normalized_height = np.empty(512)
    for seed_index in range(normalized_height.size):
        evaluator = SyntheticEvaluator(
            spec,
            make_latent_noise_identity(
                _ROOT_SEED,
                seed_index,
                latent_noise_namespace=_LATENT_NAMESPACE,
            ),
        )
        normalized_height[seed_index] = (
            evaluator.evaluate(17.25, 39.5, derivative_order=0).height[0]
            / evaluator.parameters.Sq_mm
        )
    centered = normalized_height - np.mean(normalized_height)
    variance = float(np.mean(centered**2))
    skewness = float(np.mean(centered**3) / variance**1.5)
    kurtosis = float(np.mean(centered**4) / variance**2)

    assert abs(float(np.mean(normalized_height))) < 0.15
    assert 0.8 < variance < 1.25
    assert abs(skewness) < 0.25
    assert 2.5 < kurtosis < 3.5


def test_invalid_derivative_order_coordinates_and_cutoff_fail_closed() -> None:
    evaluator = _make_evaluator()
    with pytest.raises(ValueError, match="derivative_order"):
        evaluator.evaluate(1.0, 2.0, derivative_order=3)
    with pytest.raises(ValueError, match="finite"):
        evaluator.evaluate(np.nan, 2.0)
    with pytest.raises(ValueError, match="cannot be negative"):
        evaluator.evaluate(1.0, 2.0, q_max_rad_per_mm=-1.0)
    with pytest.raises(ValueError, match="one-dimensional"):
        evaluator.evaluate_grid(np.zeros((2, 2)), np.zeros(2))
