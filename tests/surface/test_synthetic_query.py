from __future__ import annotations

import dataclasses

import numpy as np

from spine_sim.surface import (
    BoundaryMode,
    ConvergenceLevel,
    DomainStatus,
    QualityStatus,
    QueryCapability,
    SurfaceFamily,
    SurfaceProvider,
    SurfaceQuery,
    make_latent_noise_identity,
    make_synthetic_source_descriptor,
    synthetic_parameters_for_tier,
)


def _query(*, boundary: BoundaryMode = BoundaryMode.ERROR) -> SurfaceQuery:
    provider = SurfaceProvider()
    descriptor = make_synthetic_source_descriptor(boundary_mode=boundary)
    creation = provider.create_surface_spec(
        descriptor,
        SurfaceFamily.SELF_AFFINE_GAUSSIAN,
        synthetic_parameters_for_tier("medium", modes_per_band=8),
    )
    realization = provider.create_realization(
        descriptor,
        creation.spec,
        latent_identity=make_latent_noise_identity(0x123456789ABCDEF, 4),
    )
    assert realization.handle is not None
    return SurfaceQuery(realization.handle)


def test_synthetic_query_has_typed_differential_fields_and_refinement_axis() -> None:
    query = _query()
    full = query.query_height_differential([[74.0, 75.0], [76.0, 75.0]])
    assert full.capability is QueryCapability.EXACT
    assert full.convergence_level is ConvergenceLevel.CONVERGED
    assert full.field("height_mm").values is not None
    assert full.field("gradient").values.shape == (2, 2)
    assert full.field("outward_normal").values.shape == (2, 3)
    assert full.field("hessian_per_mm").values.shape == (2, 2, 2)

    coarse = query.query_height_differential([[74.0, 75.0]], q_max_rad_per_mm=0.1)
    assert coarse.capability is QueryCapability.EXACT
    assert coarse.convergence_level is ConvergenceLevel.REFINEMENT_REQUIRED
    assert coarse.trusted_scale_status is QualityStatus.RESOLUTION_REFINEMENT_REQUIRED
    assert coarse.error_bound is not None and coarse.error_bound > 0.0


def test_synthetic_query_domain_policy_closest_sdf_and_sphere_are_geometry_only() -> None:
    error_query = _query()
    rejected = error_query.query_height_differential([[-1.0, 75.0]])
    assert rejected.domain_status == (DomainStatus.OUT_OF_DOMAIN,)
    assert rejected.capability is QueryCapability.UNAVAILABLE

    periodic_query = _query(boundary=BoundaryMode.PERIODIC)
    wrapped = periodic_query.query_height_differential([[-1.0, 75.0]])
    reference = periodic_query.query_height_differential([[149.0, 75.0]])
    assert wrapped.domain_status == (DomainStatus.WRAPPED,)
    np.testing.assert_array_equal(
        wrapped.field("height_mm").values,
        reference.field("height_mm").values,
    )

    closest = error_query.query_closest_features(
        [[75.0, 75.0, 0.1]],
        requested_tolerance_mm=0.2,
        maximum_global_cells=200,
    )
    distance = error_query.query_signed_distance(
        [[75.0, 75.0, 0.1]],
        requested_tolerance_mm=0.2,
        maximum_global_cells=200,
    )
    sphere = error_query.query_spherical_envelope_or_clearance(
        [[75.0, 75.0]],
        0.05,
        requested_tolerance_mm=0.1,
        sample_count=9,
    )
    assert closest.capability is QueryCapability.APPROXIMATE
    assert distance.field("signed_distance_mm").values is not None
    assert sphere.field("sphere_envelope_height_mm").values is not None
    forbidden = ("force", "friction", "contact", "engagement", "failure", "load")
    field_names = {
        item.name.lower()
        for record in (closest, distance, sphere)
        for item in dataclasses.fields(record)
    }
    assert not any(token in name for name in field_names for token in forbidden)
