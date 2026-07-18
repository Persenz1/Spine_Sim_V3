from __future__ import annotations

import dataclasses

import pytest

from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import CapabilityStatus, CertificationStatus, SourceIdentity
from spine_sim.surface import (
    M01ReasonCode,
    SurfaceFamily,
    SurfaceProvider,
    make_analytic_source_descriptor,
    make_latent_noise_identity,
    make_measured_source_descriptor,
    make_synthetic_source_descriptor,
    validate_source_descriptor,
)


def test_source_descriptors_are_strict_and_synthetic_cannot_spoof_material() -> None:
    analytic = make_analytic_source_descriptor()
    synthetic = make_synthetic_source_descriptor(material_direction_rad=0.25)
    assert validate_source_descriptor(analytic).capability_status is CapabilityStatus.SUPPORTED
    assert synthetic.material_label == "synthetic_unidentified"
    assert synthetic.source_identity is SourceIdentity.DEV_POLICY
    assert synthetic.certification_status is CertificationStatus.NOT_CERTIFIABLE
    with pytest.raises(ContractViolation):
        dataclasses.replace(synthetic, material_label="concrete")
    with pytest.raises(ContractViolation):
        make_measured_source_descriptor(reserved_fields={"unknown_instrument_field": "x"})


def test_measured_and_external_mesh_are_safe_unavailable_without_identity() -> None:
    provider = SurfaceProvider()
    measured = make_measured_source_descriptor(
        reserved_fields={"instrument_make_model": None, "native_point_spacing_x_y": None}
    )
    status = validate_source_descriptor(measured)
    assert status.capability_status is CapabilityStatus.UNAVAILABLE
    assert status.reason_code == M01ReasonCode.MEASURED_IMPORT_DEFERRED
    creation = provider.create_surface_spec(measured, SurfaceFamily.PLANE, {"z0_mm": 0.0})
    assert creation.spec is None
    assert creation.realization is None
    assert creation.handle is None
    assert creation.status.reason_code == M01ReasonCode.MEASURED_IMPORT_DEFERRED
    mesh = provider.request_external_mesh_or_point_cloud_import()
    assert mesh.realization is None and mesh.handle is None
    assert mesh.status.reason_code == M01ReasonCode.EXTERNAL_MESH_IMPORT_DEFERRED


def test_spec_seed_latent_and_generator_version_have_content_identity() -> None:
    provider = SurfaceProvider()
    source = make_synthetic_source_descriptor()
    parameters = {
        "roughness_tier": "medium",
        "H": 0.7,
        "Sq_mm": 0.05,
        "lc_mm": 1.0,
        "anisotropy_ratio": 1.0,
        "anisotropy_direction_rad": 0.0,
        "lambda_min_declared_trust_mm": 0.025,
    }
    first = provider.create_surface_spec(source, SurfaceFamily.SELF_AFFINE_GAUSSIAN, parameters)
    replay = provider.create_surface_spec(source, SurfaceFamily.SELF_AFFINE_GAUSSIAN, parameters)
    changed = provider.create_surface_spec(
        source,
        SurfaceFamily.SELF_AFFINE_GAUSSIAN,
        parameters,
        generator_version="1.0.1",
    )
    assert first.spec is not None and replay.spec is not None and changed.spec is not None
    assert first.spec.surface_spec_id == replay.spec.surface_spec_id
    assert first.spec.surface_spec_id != changed.spec.surface_spec_id
    latent = make_latent_noise_identity(123456789, 7)
    latent_replay = make_latent_noise_identity(123456789, 7)
    other = make_latent_noise_identity(123456789, 8)
    assert latent == latent_replay
    assert latent.seed_id != other.seed_id
    assert latent.latent_noise_id != other.latent_noise_id


def test_analytic_spec_rejects_synthetic_family_and_parameter_order_is_canonical() -> None:
    provider = SurfaceProvider()
    source = make_analytic_source_descriptor()
    first = provider.create_surface_spec(
        source, SurfaceFamily.SLOPE_PLANE, {"slope_y": 0.2, "z0_mm": 1.0, "slope_x": 0.1}
    )
    second = provider.create_surface_spec(
        source, SurfaceFamily.SLOPE_PLANE, {"z0_mm": 1.0, "slope_x": 0.1, "slope_y": 0.2}
    )
    assert first.spec is not None and second.spec is not None
    assert first.spec.surface_spec_id == second.spec.surface_spec_id
    with pytest.raises(ContractViolation):
        provider.create_surface_spec(source, SurfaceFamily.SELF_AFFINE_GAUSSIAN, {})
