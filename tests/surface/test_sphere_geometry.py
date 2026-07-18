from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pytest

from spine_sim.foundation.errors import ContractViolation
from spine_sim.surface.contracts import ConvergenceLevel, QueryCapability, SurfaceFamily
from spine_sim.surface.provider import SurfaceProvider, make_analytic_source_descriptor
from spine_sim.surface.query import SurfaceQueryHandle
from spine_sim.surface.sphere import (
    generic_sphere_clearance,
    height_field_spherical_envelope,
    query_spherical_envelope_or_clearance,
    validate_sphere_path_consistency,
)


def _handle(family: SurfaceFamily, parameters: Mapping[str, object]) -> SurfaceQueryHandle:
    provider = SurfaceProvider()
    descriptor = make_analytic_source_descriptor()
    spec_result = provider.create_surface_spec(descriptor, family, dict(parameters))
    assert spec_result.spec is not None, spec_result.status.explanation
    realization_result = provider.create_realization(descriptor, spec_result.spec)
    assert realization_result.handle is not None
    return SurfaceQueryHandle(realization_result.handle)


@pytest.mark.parametrize("radius_mm", (0.05, 0.10))
def test_complete_sphere_plane_and_slope_have_closed_form_envelopes(radius_mm: float) -> None:
    plane = _handle(SurfaceFamily.PLANE, {"offset_mm": 0.3})
    plane_envelope = height_field_spherical_envelope(plane.evaluator, [[75.0, 75.0]], radius_mm)
    np.testing.assert_allclose(plane_envelope.envelope_height_mm, [0.3 + radius_mm])
    assert plane_envelope.capability is QueryCapability.EXACT
    assert plane_envelope.convergence_level is ConvergenceLevel.ANALYTIC
    assert plane_envelope.achieved_residual_mm == 0.0
    assert plane_envelope.error_bound_mm == 0.0

    gradient = np.array([0.2, -0.1])
    slope = _handle(
        SurfaceFamily.SLOPE_PLANE,
        {"offset_mm": 0.3, "slope_x": gradient[0], "slope_y": gradient[1]},
    )
    center = np.array([75.0, 75.0])
    slope_envelope = height_field_spherical_envelope(slope.evaluator, [center], radius_mm)
    expected_height = (
        0.3 + np.dot(gradient, center) + radius_mm * math.sqrt(1.0 + np.dot(gradient, gradient))
    )
    np.testing.assert_allclose(slope_envelope.envelope_height_mm, [expected_height])
    expected_support_xy = center + radius_mm * gradient / math.sqrt(
        1.0 + np.dot(gradient, gradient)
    )
    np.testing.assert_allclose(
        slope_envelope.supports[0][0].point_mm[:2], expected_support_xy, atol=2.0e-14
    )


@pytest.mark.parametrize(
    ("family", "parameters"),
    (
        (
            SurfaceFamily.GAUSSIAN_BUMP,
            {"amplitude_mm": 0.5, "sigma_mm": 0.7},
        ),
        (
            SurfaceFamily.GAUSSIAN_PIT,
            {"amplitude_mm": 0.5, "sigma_mm": 0.7},
        ),
        (
            SurfaceFamily.GROOVE_SMOOTH,
            {"depth_mm": 0.4, "sigma_mm": 0.6},
        ),
        (
            SurfaceFamily.MULTI_GAUSSIAN_FEATURE,
            {
                "features": (
                    {
                        "feature_id": "peak",
                        "amplitude_mm": 0.45,
                        "center_x_mm": 74.8,
                        "center_y_mm": 75.0,
                        "sigma_mm": 0.6,
                    },
                    {
                        "feature_id": "pit",
                        "amplitude_mm": -0.25,
                        "center_x_mm": 75.5,
                        "center_y_mm": 75.1,
                        "sigma_mm": 0.8,
                    },
                )
            },
        ),
    ),
)
@pytest.mark.parametrize("radius_mm", (0.05, 0.10))
def test_peak_pit_groove_and_multi_feature_sphere_fixtures_declare_quality(
    family: SurfaceFamily, parameters: Mapping[str, object], radius_mm: float
) -> None:
    handle = _handle(family, parameters)
    result = height_field_spherical_envelope(
        handle.evaluator,
        [[75.0, 75.0]],
        radius_mm,
        requested_tolerance_mm=1.0e-4,
        sample_count=33,
    )
    assert result.capability is QueryCapability.APPROXIMATE
    assert result.convergence_level in {
        ConvergenceLevel.CONVERGED,
        ConvergenceLevel.REFINEMENT_REQUIRED,
    }
    assert result.validity.tolist() == [True]
    assert np.isfinite(result.envelope_height_mm).all()
    assert result.supports[0]
    assert result.achieved_residual_mm >= 0.0
    assert result.error_bound_mm >= 0.0
    for support in result.supports[0]:
        assert support.outward_normals
        assert support.residual_mm >= 0.0
        assert support.error_bound_mm == result.error_bound_mm


def test_rt_refinement_sequence_tightens_bound_or_explicitly_requests_more_resolution() -> None:
    """Exercise the Rt/5 -> Rt/8 -> Rt/10 geometry-gate refinement sequence."""

    rt_mm = 0.5
    radius_mm = 0.10
    handle = _handle(
        SurfaceFamily.GAUSSIAN_BUMP,
        {"amplitude_mm": rt_mm, "sigma_mm": 0.65},
    )
    # Odd global disk covers representing successively tighter Rt-based local LODs.
    sample_count_by_gate = {"Rt/5": 17, "Rt/8": 33, "Rt/10": 65}
    results = [
        height_field_spherical_envelope(
            handle.evaluator,
            [[75.08, 75.03]],
            radius_mm,
            requested_tolerance_mm=0.01 * rt_mm,
            sample_count=sample_count,
        )
        for sample_count in sample_count_by_gate.values()
    ]
    bounds = [result.error_bound_mm for result in results]
    assert bounds[2] < bounds[1] < bounds[0]
    np.testing.assert_allclose(
        results[-2].envelope_height_mm,
        results[-1].envelope_height_mm,
        atol=max(bounds[-2], bounds[-1]),
    )
    for result in results:
        if max(result.achieved_residual_mm, result.error_bound_mm) > 0.01 * rt_mm:
            assert result.convergence_level is ConvergenceLevel.REFINEMENT_REQUIRED
        else:
            assert result.convergence_level is ConvergenceLevel.CONVERGED


@pytest.mark.parametrize(
    ("family", "parameters"),
    (
        (SurfaceFamily.PLANE, {"offset_mm": 0.3}),
        (
            SurfaceFamily.SLOPE_PLANE,
            {"offset_mm": 0.3, "slope_x": 0.2, "slope_y": -0.1},
        ),
    ),
)
@pytest.mark.parametrize("radius_mm", (0.05, 0.10))
def test_height_envelope_zero_set_matches_generic_phi_minus_radius_path(
    family: SurfaceFamily, parameters: Mapping[str, object], radius_mm: float
) -> None:
    handle = _handle(family, parameters)
    consistent = validate_sphere_path_consistency(
        handle, [[75.0, 75.0]], radius_mm, tolerance_mm=1.0e-9
    )
    assert consistent.tolist() == [True]

    height_response = query_spherical_envelope_or_clearance(
        handle, [[75.0, 75.0]], radius_mm, path="height_envelope"
    )
    envelope_height = height_response.field("sphere_envelope_height_mm").values
    assert envelope_height is not None
    generic_response = generic_sphere_clearance(
        handle, [[75.0, 75.0, float(envelope_height[0])]], radius_mm
    )
    clearance = generic_response.field("sphere_clearance_mm").values
    assert clearance is not None
    np.testing.assert_allclose(clearance, [0.0], atol=1.0e-12)
    assert dict(height_response.metadata)["radius_is_query_probe"] is True
    assert dict(generic_response.metadata)["radius_is_query_probe"] is True
    assert height_response.surface_realization_id == generic_response.surface_realization_id
    assert height_response.surface_spec_id == generic_response.surface_spec_id


def test_sphere_domain_requires_complete_disk_and_never_clamps() -> None:
    handle = _handle(SurfaceFamily.PLANE, {"offset_mm": 0.0})
    result = height_field_spherical_envelope(handle.evaluator, [[0.04, 75.0], [0.05, 75.0]], 0.05)
    assert result.validity.tolist() == [False, True]
    assert result.supports[0] == ()


@pytest.mark.parametrize("bad_radius", (0.0, -0.1, math.inf, math.nan))
def test_sphere_probe_radius_is_strictly_positive_and_finite(bad_radius: float) -> None:
    handle = _handle(SurfaceFamily.PLANE, {"offset_mm": 0.0})
    with pytest.raises(ContractViolation, match="radius_mm"):
        height_field_spherical_envelope(handle.evaluator, [[75.0, 75.0]], bad_radius)


def test_complete_sphere_queries_remain_pure_geometry() -> None:
    handle = _handle(SurfaceFamily.PLANE, {"offset_mm": 0.0})
    responses = (
        query_spherical_envelope_or_clearance(handle, [[75.0, 75.0]], 0.1, path="height_envelope"),
        query_spherical_envelope_or_clearance(
            handle, [[75.0, 75.0, 0.1]], 0.1, path="phi_minus_radius"
        ),
    )
    forbidden = ("force", "contact", "friction", "legal_cap", "engaged", "success")
    for response in responses:
        schema = " ".join(
            (
                response.operation,
                response.reference_semantics,
                *(field.field_id for field in response.fields),
                *(name for name, _ in response.metadata),
            )
        ).lower()
        assert not any(token in schema for token in forbidden)
