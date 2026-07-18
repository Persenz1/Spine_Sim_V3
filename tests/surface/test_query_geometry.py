from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pytest

from spine_sim.foundation.errors import ContractViolation
from spine_sim.surface.contracts import (
    BoundaryMode,
    ConvergenceLevel,
    Domain2D,
    DomainStatus,
    QualityStatus,
    QueryCapability,
    SurfaceFamily,
)
from spine_sim.surface.provider import SurfaceProvider, make_analytic_source_descriptor
from spine_sim.surface.query import SurfaceQueryHandle, classify_domain_coordinates


def _handle(
    family: SurfaceFamily,
    parameters: Mapping[str, object],
    *,
    boundary_mode: BoundaryMode = BoundaryMode.ERROR,
) -> SurfaceQueryHandle:
    provider = SurfaceProvider()
    descriptor = make_analytic_source_descriptor(boundary_mode=boundary_mode)
    spec_result = provider.create_surface_spec(descriptor, family, dict(parameters))
    assert spec_result.spec is not None, spec_result.status.explanation
    realization_result = provider.create_realization(descriptor, spec_result.spec)
    assert realization_result.handle is not None
    return SurfaceQueryHandle(realization_result.handle)


def test_error_boundary_preserves_cardinality_without_clamp_or_nan_missing() -> None:
    handle = _handle(SurfaceFamily.PLANE, {"offset_mm": 1.5})
    response = handle.query_height_differential(
        np.array([[20.0, 30.0], [-0.01, 30.0], [150.0, 150.0]]), derivative_order=2
    )
    assert response.domain_status == (
        DomainStatus.IN_DOMAIN,
        DomainStatus.OUT_OF_DOMAIN,
        DomainStatus.ON_BOUNDARY,
    )
    assert response.mapped_coordinates_mm is None
    assert response.quality_mask.tolist() == [True, False, True]
    height = response.field("height_mm")
    assert height.values is not None
    assert height.validity.tolist() == [True, False, True]
    assert np.isfinite(height.values).all()
    assert response.field("hessian_per_mm").validity.tolist() == [True, False, True]

    all_out = handle.query_height_differential([[-1.0, 50.0]], derivative_order=1)
    assert all_out.capability is QueryCapability.UNAVAILABLE
    assert all_out.field("height_mm").values is None
    assert all_out.status.reason_code == "M01_OUT_OF_DOMAIN"


def test_periodic_mapping_is_explicit_and_only_allowed_for_compatible_family() -> None:
    periodic_plane = _handle(
        SurfaceFamily.PLANE, {"offset_mm": 0.75}, boundary_mode=BoundaryMode.PERIODIC
    )
    response = periodic_plane.query_height_differential(
        [[151.0, -2.0], [150.0, 150.0]], derivative_order=0
    )
    assert response.domain_status == (DomainStatus.WRAPPED, DomainStatus.ON_BOUNDARY)
    assert response.mapped_coordinates_mm is not None
    np.testing.assert_allclose(response.mapped_coordinates_mm[0], [1.0, 148.0])
    np.testing.assert_allclose(response.field("height_mm").values, [0.75, 0.75])

    provider = SurfaceProvider()
    descriptor = make_analytic_source_descriptor(boundary_mode=BoundaryMode.PERIODIC)
    creation = provider.create_surface_spec(
        descriptor,
        SurfaceFamily.GAUSSIAN_BUMP,
        {"amplitude_mm": 1.0, "sigma_mm": 1.0},
    )
    assert creation.spec is not None
    with pytest.raises(ContractViolation, match="incompatible"):
        provider.create_realization(descriptor, creation.spec)

    with pytest.raises(ContractViolation, match="did not declare compatibility"):
        classify_domain_coordinates(
            Domain2D(),
            [[151.0, 20.0]],
            boundary_mode=BoundaryMode.PERIODIC,
            periodic_compatible=False,
        )


def test_typed_batch_rejects_broadcasting_and_nonfinite_coordinates() -> None:
    handle = _handle(SurfaceFamily.PLANE, {"offset_mm": 0.0})
    with pytest.raises(ContractViolation, match="broadcasting is forbidden"):
        handle.query_height_differential(np.array([1.0, 2.0]), np.array([3.0]))
    with pytest.raises(ContractViolation, match="finite"):
        handle.query_height_differential([[1.0, math.nan]])
    with pytest.raises(ContractViolation, match="shape"):
        handle.query_signed_distance([[1.0, 2.0]])


@pytest.mark.parametrize(
    ("family", "parameters", "query", "expected_point", "expected_distance"),
    (
        (
            SurfaceFamily.PLANE,
            {"offset_mm": 1.0},
            (70.0, 80.0, 3.0),
            (70.0, 80.0, 1.0),
            2.0,
        ),
        (
            SurfaceFamily.SLOPE_PLANE,
            {"offset_mm": 0.0, "slope_x": 0.2, "slope_y": -0.1},
            (70.0, 80.0, 9.0),
            None,
            None,
        ),
    ),
)
def test_affine_closest_and_sdf_are_exact_with_zero_residual_and_error(
    family: SurfaceFamily,
    parameters: Mapping[str, object],
    query: tuple[float, float, float],
    expected_point: tuple[float, float, float] | None,
    expected_distance: float | None,
) -> None:
    handle = _handle(family, parameters)
    closest = handle.query_closest_features([query])
    sdf = handle.query_signed_distance([query])
    assert closest.capability is QueryCapability.EXACT
    assert closest.convergence_level is ConvergenceLevel.ANALYTIC
    assert closest.achieved_residual == 0.0
    assert closest.error_bound == 0.0
    assert len(closest.feature_sets[0]) == 1
    feature = closest.feature_sets[0][0]
    assert feature.residual_mm <= 1.0e-12
    assert feature.error_bound_mm == 0.0

    if expected_point is not None and expected_distance is not None:
        np.testing.assert_allclose(feature.point_mm, expected_point, atol=1.0e-14)
        np.testing.assert_allclose(feature.signed_distance_mm, expected_distance, atol=1.0e-14)
    else:
        gradient = np.array([0.2, -0.1])
        intercept = 0.0
        normal = np.array([-gradient[0], -gradient[1], 1.0])
        normal /= np.linalg.norm(normal)
        signed_expected = (
            query[2] - intercept - np.dot(gradient, np.asarray(query[:2]))
        ) / math.sqrt(1.0 + np.dot(gradient, gradient))
        expected = np.asarray(query) - signed_expected * normal
        np.testing.assert_allclose(feature.point_mm, expected, atol=2.0e-13)
        np.testing.assert_allclose(feature.signed_distance_mm, signed_expected, atol=2.0e-13)
    assert sdf.field("signed_distance_mm").values is not None
    np.testing.assert_allclose(
        sdf.field("signed_distance_mm").values[0], feature.signed_distance_mm
    )


def test_signed_distance_uses_outside_positive_solid_semantics() -> None:
    handle = _handle(SurfaceFamily.PLANE, {"offset_mm": 2.0})
    response = handle.query_signed_distance([[75.0, 75.0, 2.7], [75.0, 75.0, 1.3]])
    values = response.field("signed_distance_mm").values
    assert values is not None
    np.testing.assert_allclose(values, [0.7, -0.7])
    assert response.reference_semantics == "signed distance to Omega_h={z<=h}; outside positive"


def test_known_switch_returns_all_noncoincident_co_minimal_features() -> None:
    handle = _handle(
        SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH,
        {"offset_mm": 0.0, "ridge_slope": 0.5},
    )
    response = handle.query_closest_features([[75.0, 75.0, 1.0]], co_minimal_tolerance_mm=1.0e-10)
    assert response.capability is QueryCapability.EXACT
    assert response.quality_status == (QualityStatus.NONSMOOTH_FEATURE_SET,)
    assert len(response.feature_sets[0]) == 2
    assert {feature.feature_id for feature in response.feature_sets[0]} == {
        "switch_face_negative",
        "switch_face_positive",
    }
    points = sorted(tuple(feature.point_mm) for feature in response.feature_sets[0])
    np.testing.assert_allclose(points, [[75.0, 74.6, 0.2], [75.0, 75.4, 0.2]], atol=1.0e-12)
    for feature in response.feature_sets[0]:
        assert len(feature.outward_normals) == 1
        np.testing.assert_allclose(feature.signed_distance_mm, math.sqrt(0.8), atol=1.0e-12)


def test_gaussian_closest_declares_approximation_residual_bound_and_refinement() -> None:
    handle = _handle(
        SurfaceFamily.GAUSSIAN_BUMP,
        {"amplitude_mm": 0.8, "sigma_mm": 1.2},
    )
    response = handle.query_closest_features(
        [[75.35, 75.1, 1.4]],
        requested_tolerance_mm=2.0e-3,
        maximum_global_cells=800,
    )
    assert response.capability is QueryCapability.APPROXIMATE
    assert response.achieved_residual is not None
    assert response.error_bound is not None
    assert response.achieved_residual >= 0.0
    assert response.error_bound >= 0.0
    assert response.convergence_level in {
        ConvergenceLevel.CONVERGED,
        ConvergenceLevel.REFINEMENT_REQUIRED,
    }
    assert response.feature_sets[0]
    metadata = dict(response.metadata)
    assert metadata["global_candidate_coverage"] is True
    assert metadata["global_bound_cells_by_point"][0] <= 800


def test_exact_primitive_fixtures_expose_feature_identity_and_normals() -> None:
    fixtures = (
        (
            SurfaceFamily.GROOVE_CIRCULAR,
            {"depth_mm": 0.5, "half_width_mm": 1.0},
            [75.0, 75.0, 0.4],
            "circular_groove_arc",
        ),
        (
            SurfaceFamily.SPHERICAL_CAP,
            {"radius_mm": 3.0, "aperture_radius_mm": 1.5},
            [75.0, 75.0, 2.0],
            "spherical_patch",
        ),
        (
            SurfaceFamily.SPHERICAL_BOWL,
            {"radius_mm": 3.0, "aperture_radius_mm": 1.5},
            [75.0, 75.0, 1.0],
            "spherical_patch",
        ),
    )
    for family, parameters, query, expected_feature in fixtures:
        response = _handle(family, parameters).query_closest_features([query])
        assert response.capability is QueryCapability.EXACT
        assert any(expected_feature in item.feature_id for item in response.feature_sets[0])
        assert all(item.outward_normals for item in response.feature_sets[0])


def test_geometry_query_schema_never_returns_contact_force_or_material_semantics() -> None:
    handle = _handle(
        SurfaceFamily.GROOVE_V,
        {"depth_mm": 0.4, "half_width_mm": 0.8},
    )
    responses = (
        handle.query_height_differential([[75.0, 75.0]]),
        handle.query_closest_features([[75.0, 75.0, 1.0]]),
        handle.query_signed_distance([[75.0, 75.0, 1.0]]),
        handle.query_neighborhood((74.0, 76.0, 74.0, 76.0), grid_size=9),
    )
    forbidden = ("force", "contact", "friction", "engaged", "success", "material_failure")
    for response in responses:
        schema_text = " ".join(
            (
                response.operation,
                response.reference_semantics,
                *(field.field_id for field in response.fields),
                *(name for name, _ in response.metadata),
            )
        ).lower()
        assert not any(token in schema_text for token in forbidden)
