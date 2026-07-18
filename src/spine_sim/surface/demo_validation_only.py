"""Generate the frozen M01 VALIDATION_ONLY surface demonstration.

The bundle contains immutable analytic/synthetic surface evidence only.  It
does not create contact, friction, load, material-failure, or engagement
semantics.  Preview rendering is an optional, read-only post-process over the
saved visualization arrays.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import platform
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from spine_sim.foundation.canonical import semantic_hash, source_file_hash, stable_content_id
from spine_sim.foundation.config import (
    ConfigField,
    ConfigLayer,
    ConfigLayerLevel,
    ConfigSchema,
    ParameterOwnership,
    ResolvedConfig,
    resolve_config,
)
from spine_sim.foundation.integrity import VerifyMode
from spine_sim.foundation.models import CertificationStatus, RegisteredArrayPayload, SourceIdentity
from spine_sim.foundation.reader import FilterSpec, ResultReader
from spine_sim.foundation.registry import BUNDLE_SCHEMA_VERSION, RESULT_API_VERSION, SchemaRegistry
from spine_sim.foundation.replay import make_replay_manifest
from spine_sim.foundation.storage import write_json_atomic
from spine_sim.foundation.writer import ResultWriter, make_run_envelope

from .contracts import (
    GENERATOR_VERSION,
    RNG_PROFILE_ID,
    ConvergenceLevel,
    M01ReasonCode,
    RoughnessTier,
    SurfaceFamily,
    VisualizationSample,
    m01_maturity,
    make_latent_noise_identity,
    supported_status,
)
from .materialization import (
    NORMAL_PATH_BUILDS_FULL_DOMAIN_RT10_DENSE,
    LODLevel,
    MaterializationConfig,
    TileMaterializer,
    derive_query_footprint,
)
from .mesh_regression import heightfield_triangulation_regression_adapter
from .provider import (
    SurfaceProvider,
    SurfaceQueryHandle,
    make_analytic_source_descriptor,
    make_measured_source_descriptor,
    make_synthetic_source_descriptor,
)
from .query import SurfaceQuery
from .result_extension import (
    MATERIALIZATION_RECEIPTS_DATASET,
    SOURCE_AVAILABILITY_DATASET,
    SURFACE_PROVENANCE_DATASET,
    SURFACE_QUALITY_BANDS_DATASET,
    SURFACE_REALIZATIONS_DATASET,
    SURFACE_STATISTICS_DATASET,
    VALIDATION_RESULTS_DATASET,
    VISUALIZATION_COORDINATES_FIELD,
    VISUALIZATION_HEIGHT_FIELD,
    VISUALIZATION_VALIDITY_FIELD,
    SourceAvailabilityRecord,
    SurfaceMaterializationReceiptRecord,
    SurfaceProvenanceStepRecord,
    SurfaceQualityBandRecord,
    SurfaceRealizationRecord,
    SurfaceStatisticRecord,
    SurfaceValidationResultRecord,
    surface_result_extension,
)
from .sphere import height_field_spherical_envelope, validate_sphere_path_consistency
from .synthetic import SyntheticEvaluator, synthetic_parameters_for_tier

DEMO_ROOT_SEED = 0x4D30315F535552464143455F44454D4F
DEMO_SEED_INDEX = 1
DEMO_LATENT_NAMESPACE = "m01.surface.latent.validation_demo.shared_crn"
DEMO_TIERS = (RoughnessTier.GENTLE, RoughnessTier.MEDIUM, RoughnessTier.SHARP)
DEMO_WINDOW_MM = (0.0, 150.0, 0.0, 150.0)
DEFAULT_DEMO_GRID_SHAPE = (1024, 1024)
DEMO_REQUIREMENT_ORIGIN = "M01_SURFACE_REQUIREMENTS 1.0.0 §14.6"


@dataclass(frozen=True, slots=True)
class DemoCase:
    tier: RoughnessTier
    case_id: str
    design_id: str
    handle: SurfaceQueryHandle
    resolved_config: ResolvedConfig


@dataclass(frozen=True, slots=True)
class DemoArtifacts:
    bundle_path: Path
    bundle_manifest_path: Path
    summary_path: Path
    case_ids: tuple[str, ...]
    surface_realization_ids: tuple[str, ...]
    preview_paths: tuple[Path, ...]
    elapsed_seconds: float


def _demo_schema() -> ConfigSchema:
    return ConfigSchema(
        "M01_VALIDATION_ONLY_CONFIG",
        "1.0.0",
        (
            ConfigField(
                "surface.generator_version",
                str,
                ParameterOwnership.NUMERICAL_CONFIGURATION,
                "M01_SURFACE_REQUIREMENTS 1.0.0 §5.3",
                SourceIdentity.ACCEPTED_AUTHORITY,
                locked=True,
                enum_values=(GENERATOR_VERSION,),
            ),
            ConfigField(
                "surface.roughness_tier",
                str,
                ParameterOwnership.DEV_PRIOR_UNCERTAINTY,
                "M01_SURFACE_REQUIREMENTS 1.0.0 §4.2",
                SourceIdentity.DEV_POLICY,
                enum_values=("multi_tier_demo", "gentle", "medium", "sharp"),
            ),
            ConfigField(
                "preview.grid_size",
                int,
                ParameterOwnership.RUN_AND_PLOT_CONFIGURATION,
                "M01_SURFACE_REQUIREMENTS 1.0.0 §4.1/§12.1",
                SourceIdentity.DEV_POLICY,
                minimum=2,
                maximum=4096,
            ),
        ),
    )


def _resolved_config(tier: str, grid_size: int, *, config_kind: str) -> ResolvedConfig:
    authority = ConfigLayer(
        ConfigLayerLevel.L1_AUTHORITY,
        "M01:inline-frozen-generator",
        semantic_hash({"generator_version": GENERATOR_VERSION}),
        {"surface": {"generator_version": GENERATOR_VERSION}},
        SourceIdentity.ACCEPTED_AUTHORITY,
    )
    policy = ConfigLayer(
        ConfigLayerLevel.L2_DEV_POLICY,
        "M01:inline-validation-demo-policy",
        semantic_hash({"tier": tier, "grid_size": grid_size}),
        {
            "surface": {"roughness_tier": tier},
            "preview": {"grid_size": grid_size},
        },
        SourceIdentity.DEV_POLICY,
    )
    return resolve_config(_demo_schema(), (authority, policy), config_kind=config_kind)


def _git_state(repo_root: Path) -> tuple[str, str]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
        ).strip()
        dirty = (
            "dirty"
            if subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=repo_root, text=True
            ).strip()
            else "clean"
        )
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE", "UNAVAILABLE"
    return commit, dirty


def _make_cases(grid_size: int) -> tuple[DemoCase, ...]:
    provider = SurfaceProvider()
    descriptor = make_synthetic_source_descriptor()
    latent = make_latent_noise_identity(
        DEMO_ROOT_SEED,
        DEMO_SEED_INDEX,
        latent_noise_namespace=DEMO_LATENT_NAMESPACE,
    )
    cases: list[DemoCase] = []
    for tier in DEMO_TIERS:
        creation = provider.create_surface_spec(
            descriptor,
            SurfaceFamily.SELF_AFFINE_GAUSSIAN,
            synthetic_parameters_for_tier(tier),
        )
        realization = provider.create_realization(
            descriptor,
            creation.spec,
            latent_identity=latent,
        )
        handle = provider.open_query_handle(realization)
        if handle is None:
            raise RuntimeError(f"failed to create supported synthetic tier: {tier.value}")
        design_id = stable_content_id(
            "design", {"fixture": "M01_VALIDATION_ONLY", "tier": tier.value}
        )
        case_id = stable_content_id(
            "case",
            {
                "design_id": design_id,
                "seed_id": latent.seed_id,
                "surface_realization_id": handle.realization.surface_realization_id,
            },
        )
        cases.append(
            DemoCase(
                tier,
                case_id,
                design_id,
                handle,
                _resolved_config(
                    tier.value,
                    grid_size,
                    config_kind=f"m01_case_{tier.value}",
                ),
            )
        )
    if len({item.handle.realization.latent_noise_id for item in cases}) != 1:
        raise RuntimeError("M01 demo tiers must share one latent-noise identity")
    if len({item.handle.realization.surface_realization_id for item in cases}) != len(cases):
        raise RuntimeError("M01 demo tiers must have distinct realization identities")
    return tuple(cases)


def _realization_record(run_id: str, case: DemoCase) -> SurfaceRealizationRecord:
    realization = case.handle.realization
    evaluator = case.handle.evaluator
    statistics_ref = stable_content_id(
        "m01_statistics_ref",
        {"realization": realization.surface_realization_id, "scope": "coefficient_parent"},
    )
    return SurfaceRealizationRecord(
        run_id=run_id,
        case_id=case.case_id,
        surface_spec_id=realization.surface_spec_id,
        surface_realization_id=realization.surface_realization_id,
        realization_schema_version=realization.realization_schema_version,
        source_descriptor_id=realization.source_descriptor_id,
        source_kind=realization.source_kind.value,
        family=realization.family.value,
        material_label=realization.material_label,
        seed_id=realization.seed_id,
        latent_noise_id=realization.latent_noise_id,
        rng_profile_id=realization.rng_profile_id,
        generator_id=realization.generator_id,
        generator_version=realization.generator_version,
        query_contract_version=realization.query_contract_version,
        logical_domain_mm=(
            realization.logical_domain.x_min_mm,
            realization.logical_domain.x_max_mm,
            realization.logical_domain.y_min_mm,
            realization.logical_domain.y_max_mm,
        ),
        boundary_mode=realization.boundary_mode.value,
        source_frame_id=realization.source_frame_id,
        surface_frame_id=realization.surface_frame_id,
        material_frame_id=realization.material_frame_id,
        definition_hash=realization.definition_hash,
        provenance_chain_hash=realization.provenance_chain_hash,
        capability_manifest_hash=semantic_hash(realization.capability_manifest),
        quality_manifest_hash=semantic_hash(
            getattr(evaluator, "band_manifests", realization.trusted_bands)
        ),
        target_statistics_ref=statistics_ref,
        realized_statistics_ref=statistics_ref,
        statistic_scope="TARGET_ANALYTIC + REALIZED_COEFFICIENT_FULL_PARENT",
        requirement_origin=DEMO_REQUIREMENT_ORIGIN,
        value_provenance=(
            "DEV_POLICY synthetic tier",
            "VALIDATION_ONLY demo selection",
            "shared latent CRN",
        ),
        authority_refs=(
            "M01_SURFACE_REQUIREMENTS 1.0.0",
            "A_INTEGRATED_MODEL 1.0.0 accepted §5.1",
        ),
        status=realization.status,
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=realization.maturity,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
    )


def _provenance_record(run_id: str, case: DemoCase) -> SurfaceProvenanceStepRecord:
    realization = case.handle.realization
    step_id = stable_content_id(
        "m01_provenance_step",
        {"realization": realization.surface_realization_id, "step": 0},
    )
    return SurfaceProvenanceStepRecord(
        run_id=run_id,
        case_id=case.case_id,
        surface_realization_id=realization.surface_realization_id,
        step_index=0,
        step_id=step_id,
        algorithm_id=realization.generator_id,
        algorithm_version=realization.generator_version,
        parameters_hash=semantic_hash(case.handle.spec.parameters),
        input_hashes=(realization.latent_noise_id or "NOT_APPLICABLE",),
        output_hash=realization.definition_hash,
        requirement_origin="M01_SURFACE_REQUIREMENTS 1.0.0 §5.3/§7",
        status=supported_status(),
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=realization.maturity,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
    )


def _quality_records(run_id: str, case: DemoCase) -> tuple[SurfaceQualityBandRecord, ...]:
    realization = case.handle.realization
    manifests = case.handle.evaluator.band_manifests
    return tuple(
        SurfaceQualityBandRecord(
            run_id=run_id,
            case_id=case.case_id,
            surface_realization_id=realization.surface_realization_id,
            band_id=f"band-{band.band_id:02d}",
            q_min_rad_per_mm=band.q_min_rad_per_mm,
            q_max_rad_per_mm=band.q_max_rad_per_mm,
            lambda_max_mm=band.lambda_max_mm,
            lambda_min_mm=band.lambda_min_mm,
            direction_rad=case.handle.evaluator.parameters.anisotropy_direction_rad,
            uncertainty_bound_mm=band.truncation_error_bound_mm,
            quality_status="TRUSTED_FOR_DECLARED_SCALE",
            basis=(
                f"{band.filter_rule}; {band.quadrature_rule}; "
                f"{band.hermitian_rule}; {band.real_construction_rule}"
            ),
            status=supported_status(),
            source_identity=SourceIdentity.DEV_POLICY,
            maturity=realization.maturity,
            certification_status=CertificationStatus.NOT_CERTIFIABLE,
        )
        for band in manifests
    )


def _statistic_record(
    run_id: str,
    case: DemoCase,
    *,
    metric: str,
    target: float | None,
    realized: float | None,
    unit: str,
    error: float,
    bin_manifest: str = "full represented parent coefficient definition",
    direction_rad: float | None = None,
) -> SurfaceStatisticRecord:
    realization_id = case.handle.realization.surface_realization_id
    statistic_id = stable_content_id(
        "m01_statistic",
        {
            "realization": realization_id,
            "metric": metric,
            "bin": bin_manifest,
            "direction_rad": direction_rad,
        },
    )
    return SurfaceStatisticRecord(
        run_id=run_id,
        case_id=case.case_id,
        surface_realization_id=realization_id,
        statistic_id=statistic_id,
        statistic_scope="TARGET_ANALYTIC + REALIZED_COEFFICIENT_FULL_PARENT",
        metric=metric,
        target_value=target,
        realized_value=realized,
        unit=unit,
        method_id="M01_PERIODIC_MODE_COEFFICIENT_AUDIT",
        method_version=GENERATOR_VERSION,
        sample_count=case.handle.evaluator.mode_count,
        window="150 x 150 mm periodic parent coefficient definition",
        detrend="zero DC by construction; no crop normalization",
        bin_manifest=bin_manifest,
        direction_rad=direction_rad,
        error_or_uncertainty=error,
        validity_coverage=1.0,
        status=supported_status(),
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=case.handle.realization.maturity,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
    )


def _statistic_records(run_id: str, case: DemoCase) -> tuple[SurfaceStatisticRecord, ...]:
    statistics = case.handle.evaluator.statistics
    records = [
        _statistic_record(
            run_id,
            case,
            metric="mean_height",
            target=statistics.target_mean_mm,
            realized=statistics.realized_mean_mm,
            unit="mm",
            error=0.0,
        ),
        _statistic_record(
            run_id,
            case,
            metric="Sq",
            target=statistics.target_Sq_mm,
            realized=statistics.realized_Sq_mm,
            unit="mm",
            error=abs(statistics.realized_Sq_mm - statistics.target_Sq_mm),
        ),
        _statistic_record(
            run_id,
            case,
            metric="variance",
            target=statistics.target_variance_mm2,
            realized=statistics.realized_variance_mm2,
            unit="mm^2",
            error=statistics.parseval_absolute_error_mm2,
        ),
        _statistic_record(
            run_id,
            case,
            metric="parseval_relative_error",
            target=0.0,
            realized=statistics.parseval_relative_error,
            unit="1",
            error=statistics.parseval_relative_error,
        ),
        _statistic_record(
            run_id,
            case,
            metric="hermitian_relative_residual",
            target=0.0,
            realized=statistics.hermitian_relative_residual,
            unit="1",
            error=statistics.hermitian_relative_residual,
        ),
        _statistic_record(
            run_id,
            case,
            metric="imaginary_relative_residual",
            target=0.0,
            realized=statistics.imaginary_relative_residual,
            unit="1",
            error=statistics.imaginary_relative_residual,
        ),
    ]
    for target, realized in zip(statistics.target_psd, statistics.realized_psd, strict=True):
        records.append(
            _statistic_record(
                run_id,
                case,
                metric=f"radial_psd_band_{target.band_id:02d}",
                target=target.psd_mm4,
                realized=realized.psd_mm4,
                unit="mm^4",
                error=abs(realized.psd_mm4 - target.psd_mm4),
                bin_manifest=(
                    f"q=[{target.q_min_rad_per_mm:.17g},"
                    f"{target.q_max_rad_per_mm:.17g}] rad/mm; "
                    f"modes={target.mode_count}"
                ),
            )
        )
    for index, (target, realized) in enumerate(
        zip(
            statistics.target_directional_spectrum,
            statistics.realized_directional_spectrum,
            strict=True,
        )
    ):
        direction = 0.5 * (target.direction_min_rad + target.direction_max_rad)
        records.append(
            _statistic_record(
                run_id,
                case,
                metric=f"directional_variance_bin_{index:02d}",
                target=target.integrated_variance_mm2,
                realized=realized.integrated_variance_mm2,
                unit="mm^2",
                error=abs(realized.integrated_variance_mm2 - target.integrated_variance_mm2),
                bin_manifest=(
                    f"theta=[{target.direction_min_rad:.17g},"
                    f"{target.direction_max_rad:.17g}] rad modulo pi; "
                    f"modes={target.mode_count}"
                ),
                direction_rad=direction,
            )
        )
    return tuple(records)


def _materialization_record(
    run_id: str,
    case: DemoCase,
    receipt: Any,
) -> SurfaceMaterializationReceiptRecord:
    return SurfaceMaterializationReceiptRecord(
        run_id=run_id,
        case_id=case.case_id,
        surface_realization_id=receipt.surface_realization_id,
        receipt_id=receipt.receipt_id,
        footprint_id=receipt.footprint_id,
        tile_coordinate=receipt.tile_coordinate,
        lod=receipt.lod,
        active_bands=receipt.active_bands,
        core_shape=receipt.core_shape,
        halo_samples=receipt.halo_samples,
        spacing_mm=receipt.spacing_mm,
        omitted_height_bound_mm=receipt.omitted_height_bound_mm,
        omitted_slope_bound=receipt.omitted_slope_bound,
        content_hash=receipt.content_hash,
        cache_status=receipt.cache_status,
        reason_code=receipt.reason_code,
        payload_bytes=receipt.payload_bytes,
        status=supported_status(receipt.reason_code),
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=case.handle.realization.maturity,
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
    )


def _validation_record(
    run_id: str,
    case: DemoCase,
    *,
    fixture: str,
    metric: str,
    tolerance: float,
    observed: float,
    passed: bool,
    evidence_ref: str,
) -> SurfaceValidationResultRecord:
    validation_id = stable_content_id(
        "m01_validation",
        {
            "realization": case.handle.realization.surface_realization_id,
            "fixture": fixture,
            "metric": metric,
        },
    )
    return SurfaceValidationResultRecord(
        run_id=run_id,
        case_id=case.case_id,
        surface_realization_id=case.handle.realization.surface_realization_id,
        validation_id=validation_id,
        fixture_id=fixture,
        metric=metric,
        tolerance=tolerance,
        observed_error=observed,
        passed=passed,
        failure_class="NONE" if passed else "NUMERICAL_VALIDATION_FAILURE",
        evidence_ref=evidence_ref,
        status=supported_status(
            "M01_VALIDATION_ONLY_PASS" if passed else "M01_VALIDATION_ONLY_FAIL"
        ),
        source_identity=SourceIdentity.VALIDATION_ONLY,
        maturity=m01_maturity(numerical_evidence=passed),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
    )


def _analytic_fixture_validation_records(
    run_id: str, case: DemoCase
) -> tuple[SurfaceValidationResultRecord, ...]:
    """Execute the analytic/sphere/mesh fixtures required by §14.6."""

    provider = SurfaceProvider()
    descriptor = make_analytic_source_descriptor()
    fixtures: tuple[tuple[str, SurfaceFamily, dict[str, Any], tuple[float, float]], ...] = (
        ("plane", SurfaceFamily.PLANE, {"offset_mm": 0.2}, (73.0, 74.0)),
        (
            "slope",
            SurfaceFamily.SLOPE_PLANE,
            {"offset_mm": 0.1, "slope_x": 0.02, "slope_y": -0.01},
            (73.0, 74.0),
        ),
        (
            "sinusoid_1d",
            SurfaceFamily.SINUSOID_1D,
            {"amplitude_mm": 0.2, "wavelength_mm": 10.0, "direction_rad": 0.3},
            (73.0, 74.0),
        ),
        (
            "sinusoid_2d",
            SurfaceFamily.SINUSOID_2D,
            {"amplitude_mm": 0.2, "wavelength_mm": 10.0},
            (73.0, 74.0),
        ),
        (
            "gaussian_bump",
            SurfaceFamily.GAUSSIAN_BUMP,
            {"amplitude_mm": 0.1, "sigma_mm": 0.2},
            (74.9, 75.0),
        ),
        (
            "gaussian_pit",
            SurfaceFamily.GAUSSIAN_PIT,
            {"amplitude_mm": 0.1, "sigma_mm": 0.2},
            (74.9, 75.0),
        ),
        (
            "multi_gaussian_feature",
            SurfaceFamily.MULTI_GAUSSIAN_FEATURE,
            {
                "features": [
                    {
                        "feature_id": "peak_a",
                        "amplitude_mm": 0.1,
                        "sigma_mm": 0.2,
                        "center_x_mm": 74.95,
                        "center_y_mm": 75.0,
                    },
                    {
                        "feature_id": "peak_b",
                        "amplitude_mm": 0.1,
                        "sigma_mm": 0.2,
                        "center_x_mm": 75.05,
                        "center_y_mm": 75.0,
                    },
                ]
            },
            (74.8, 75.0),
        ),
        (
            "groove_cosine",
            SurfaceFamily.GROOVE_COSINE,
            {"depth_mm": 0.1, "half_width_mm": 0.2},
            (75.0, 74.9),
        ),
        (
            "groove_smooth",
            SurfaceFamily.GROOVE_SMOOTH,
            {"depth_mm": 0.1, "sigma_mm": 0.1},
            (75.0, 74.9),
        ),
        (
            "groove_circular",
            SurfaceFamily.GROOVE_CIRCULAR,
            {"depth_mm": 0.1, "half_width_mm": 0.2},
            (75.0, 74.9),
        ),
        (
            "groove_v",
            SurfaceFamily.GROOVE_V,
            {"depth_mm": 0.1, "half_width_mm": 0.2},
            (75.0, 74.9),
        ),
        (
            "known_nearest_feature_switch",
            SurfaceFamily.KNOWN_NEAREST_FEATURE_SWITCH,
            {"ridge_slope": 0.1},
            (75.0, 74.9),
        ),
        (
            "spherical_cap",
            SurfaceFamily.SPHERICAL_CAP,
            {"radius_mm": 5.0, "aperture_radius_mm": 2.0},
            (74.5, 75.0),
        ),
        (
            "spherical_bowl",
            SurfaceFamily.SPHERICAL_BOWL,
            {"radius_mm": 5.0, "aperture_radius_mm": 2.0},
            (74.5, 75.0),
        ),
    )
    handles: dict[str, SurfaceQueryHandle] = {}
    records: list[SurfaceValidationResultRecord] = []
    for fixture_id, family, parameters, point in fixtures:
        creation = provider.create_surface_spec(descriptor, family, parameters)
        realized = provider.create_realization(descriptor, creation.spec)
        handle = provider.open_query_handle(realized)
        if handle is None:
            raise RuntimeError(f"analytic validation fixture unavailable: {fixture_id}")
        handles[fixture_id] = handle
        evaluator = handle.evaluator
        x, y = point
        step = 1.0e-5
        evaluated = evaluator.evaluate(x, y, derivative_order=2)
        finite_difference = np.array(
            (
                (
                    evaluator.evaluate(x + step, y, derivative_order=0).height[0]
                    - evaluator.evaluate(x - step, y, derivative_order=0).height[0]
                )
                / (2.0 * step),
                (
                    evaluator.evaluate(x, y + step, derivative_order=0).height[0]
                    - evaluator.evaluate(x, y - step, derivative_order=0).height[0]
                )
                / (2.0 * step),
            ),
            dtype=np.float64,
        )
        gradient_error = float(np.max(np.abs(finite_difference - evaluated.gradient[0])))
        normal_error = abs(float(np.linalg.norm(evaluated.normal[0])) - 1.0)
        curvature_failure = 0.0 if evaluated.curvature_validity[0] else 1.0
        observed = max(gradient_error, normal_error, curvature_failure)
        records.append(
            _validation_record(
                run_id,
                case,
                fixture=f"analytic_{fixture_id}",
                metric="height_gradient_normal_curvature_max_error",
                tolerance=5.0e-7,
                observed=observed,
                passed=observed <= 5.0e-7,
                evidence_ref="tests/surface/test_analytic.py",
            )
        )

    for fixture_id in ("groove_v", "known_nearest_feature_switch"):
        query = SurfaceQuery(handles[fixture_id])
        response = query.query_height_differential(75.0, 75.0, derivative_order=2)
        hessian = response.field("hessian_per_mm")
        passed = bool(response.feature_sets[0]) and not bool(hessian.validity[0])
        records.append(
            _validation_record(
                run_id,
                case,
                fixture=f"analytic_{fixture_id}_nonsmooth",
                metric="feature_set_retained_and_curvature_unavailable",
                tolerance=0.0,
                observed=0.0 if passed else 1.0,
                passed=passed,
                evidence_ref="tests/surface/test_query_geometry.py",
            )
        )

    sphere_fixtures = (
        "plane",
        "slope",
        "gaussian_bump",
        "gaussian_pit",
        "groove_v",
        "multi_gaussian_feature",
    )
    for fixture_id in sphere_fixtures:
        result = height_field_spherical_envelope(
            handles[fixture_id].evaluator,
            np.array(((75.0, 75.0),), dtype=np.float64),
            0.05,
            sample_count=21,
            requested_tolerance_mm=1.0e-5,
        )
        passed = (
            bool(result.validity[0])
            and bool(result.supports[0])
            and bool(np.isfinite(result.envelope_height_mm[0]))
        )
        records.append(
            _validation_record(
                run_id,
                case,
                fixture=f"complete_sphere_{fixture_id}",
                metric="finite_envelope_with_support_set",
                tolerance=0.0,
                observed=0.0 if passed else 1.0,
                passed=passed,
                evidence_ref="tests/surface/test_sphere_geometry.py",
            )
        )

    bump = handles["gaussian_bump"].evaluator
    for radius_mm in (0.05, 0.10):
        rt8 = height_field_spherical_envelope(
            bump,
            [[75.0, 75.0]],
            radius_mm,
            sample_count=17,
            requested_tolerance_mm=1.0e-5,
        )
        rt10 = height_field_spherical_envelope(
            bump,
            [[75.0, 75.0]],
            radius_mm,
            sample_count=21,
            requested_tolerance_mm=1.0e-5,
        )
        height_error = abs(float(rt10.envelope_height_mm[0] - rt8.envelope_height_mm[0]))
        support_8 = rt8.supports[0][0]
        support_10 = rt10.supports[0][0]
        position_error = math.dist(support_8.point_mm, support_10.point_mm)
        normal_8 = np.asarray(support_8.outward_normals[0], dtype=np.float64)
        normal_10 = np.asarray(support_10.outward_normals[0], dtype=np.float64)
        normal_angle_deg = math.degrees(
            math.acos(float(np.clip(np.dot(normal_8, normal_10), -1.0, 1.0)))
        )
        topology_error = 0.0 if support_8.feature_id == support_10.feature_id else 1.0
        prefix = f"complete_sphere_R{round(radius_mm * 1000)}um_Rt8_Rt10"
        for metric, tolerance, observed in (
            ("envelope_difference_mm", 0.01 * radius_mm, height_error),
            ("support_position_difference_mm", 0.02 * radius_mm, position_error),
            ("normal_angle_difference_deg", 1.0, normal_angle_deg),
            ("feature_topology_change_count", 0.0, topology_error),
        ):
            records.append(
                _validation_record(
                    run_id,
                    case,
                    fixture=prefix,
                    metric=metric,
                    tolerance=tolerance,
                    observed=observed,
                    passed=observed <= tolerance,
                    evidence_ref="tests/surface/test_sphere_geometry.py",
                )
            )
        refine_before_certify = (
            rt10.convergence_level is ConvergenceLevel.REFINEMENT_REQUIRED
            or rt10.error_bound_mm <= 0.01 * radius_mm
        )
        records.append(
            _validation_record(
                run_id,
                case,
                fixture=prefix,
                metric="refine_before_certify_gate",
                tolerance=0.0,
                observed=0.0 if refine_before_certify else 1.0,
                passed=refine_before_certify,
                evidence_ref="tests/surface/test_sphere_geometry.py",
            )
        )

    for radius_mm in (0.05, 0.10):
        consistency = validate_sphere_path_consistency(
            handles["plane"], [[75.0, 75.0]], radius_mm, tolerance_mm=1.0e-7
        )
        records.append(
            _validation_record(
                run_id,
                case,
                fixture=f"sphere_path_consistency_R{round(radius_mm * 1000)}um",
                metric="H_R_vs_phi_minus_R_inconsistency_count",
                tolerance=0.0,
                observed=float(np.count_nonzero(~consistency)),
                passed=bool(consistency.all()),
                evidence_ref="tests/surface/test_sphere_geometry.py",
            )
        )

    mesh_evaluator = handles["sinusoid_1d"].evaluator
    mesh_coarse = heightfield_triangulation_regression_adapter(mesh_evaluator, grid_shape=(17, 17))
    mesh_fine = heightfield_triangulation_regression_adapter(mesh_evaluator, grid_shape=(33, 33))
    mesh_reference = heightfield_triangulation_regression_adapter(
        mesh_evaluator, grid_shape=(65, 65)
    )
    mesh_query_points = [[74.2, 74.3, 0.5]]
    distance_fine = float(mesh_fine.signed_distance(mesh_query_points).signed_distance_mm[0])
    distance_reference = float(
        mesh_reference.signed_distance(mesh_query_points).signed_distance_mm[0]
    )
    declared_excess = max(
        0.0,
        abs(distance_fine - distance_reference)
        - (
            mesh_fine.analytic_discretization_bound_mm
            + mesh_reference.analytic_discretization_bound_mm
        ),
    )
    mesh_pass = (
        declared_excess == 0.0
        and mesh_reference.analytic_discretization_bound_mm
        < mesh_fine.analytic_discretization_bound_mm
        < mesh_coarse.analytic_discretization_bound_mm
        and not mesh_fine.accepts_external_mesh
        and not mesh_fine.is_default_query_provider
    )
    records.append(
        _validation_record(
            run_id,
            case,
            fixture="validation_only_heightfield_triangulation",
            metric="fine_reference_distance_delta_excess_over_declared_bounds_mm",
            tolerance=0.0,
            observed=declared_excess,
            passed=mesh_pass,
            evidence_ref="tests/surface/test_mesh_regression.py",
        )
    )

    forbidden = ("force", "friction", "contact", "engagement", "failure", "load")
    sphere_field_names = {
        field.name.lower()
        for field in dataclasses.fields(
            type(height_field_spherical_envelope(handles["plane"].evaluator, [[75.0, 75.0]], 0.05))
        )
    }
    forbidden_count = sum(
        token in field_name for field_name in sphere_field_names for token in forbidden
    )
    records.append(
        _validation_record(
            run_id,
            case,
            fixture="complete_sphere_pure_geometry_boundary",
            metric="forbidden_contact_force_field_count",
            tolerance=0.0,
            observed=float(forbidden_count),
            passed=forbidden_count == 0,
            evidence_ref="tests/surface/test_sphere_geometry.py",
        )
    )
    return tuple(records)


def _unavailable_records(run_id: str, case: DemoCase) -> tuple[SourceAvailabilityRecord, ...]:
    provider = SurfaceProvider()
    measured = make_measured_source_descriptor()
    measured_result = provider.create_surface_spec(
        measured,
        SurfaceFamily.PLANE,
        {"height_mm": 0.0},
    )
    mesh_result = provider.request_external_mesh_or_point_cloud_import()
    return (
        SourceAvailabilityRecord(
            run_id=run_id,
            case_id=case.case_id,
            request_id=stable_content_id(
                "m01_source_request", {"case": case.case_id, "kind": "measured"}
            ),
            source_descriptor_id=measured.source_descriptor_id,
            requested_source_kind="measured",
            requested_capability="create_realization_and_query",
            missing_fields=tuple(
                name for name, value in measured.measured_reserved_fields if value is None
            ),
            reason_code=M01ReasonCode.MEASURED_IMPORT_DEFERRED.value,
            explanation=measured_result.status.explanation,
            status=measured_result.status,
            source_identity=SourceIdentity.PROPOSED_SUPPLEMENT,
            maturity=m01_maturity(numerical_evidence=False),
            certification_status=CertificationStatus.CERTIFICATION_BLOCKED,
        ),
        SourceAvailabilityRecord(
            run_id=run_id,
            case_id=case.case_id,
            request_id=stable_content_id(
                "m01_source_request", {"case": case.case_id, "kind": "external_mesh"}
            ),
            source_descriptor_id=stable_content_id(
                "surface_source", {"deferred_kind": "external_mesh_or_point_cloud"}
            ),
            requested_source_kind="external_mesh_or_point_cloud",
            requested_capability="production_import_and_query",
            missing_fields=("raw_artifact", "registration", "quality_manifest"),
            reason_code=M01ReasonCode.EXTERNAL_MESH_IMPORT_DEFERRED.value,
            explanation=mesh_result.status.explanation,
            status=mesh_result.status,
            source_identity=SourceIdentity.PROPOSED_SUPPLEMENT,
            maturity=m01_maturity(numerical_evidence=False),
            certification_status=CertificationStatus.CERTIFICATION_BLOCKED,
        ),
    )


def _sample_and_materialize(
    run_id: str,
    case: DemoCase,
    grid_shape: tuple[int, int],
) -> tuple[
    VisualizationSample,
    tuple[SurfaceMaterializationReceiptRecord, ...],
    tuple[SurfaceValidationResultRecord, ...],
    dict[str, Any],
]:
    evaluator = case.handle.evaluator
    if not isinstance(evaluator, SyntheticEvaluator):
        raise TypeError("M01 demo cases must use SyntheticEvaluator")
    materializer = TileMaterializer(
        evaluator,
        case.handle.realization.surface_realization_id,
        logical_domain=case.handle.realization.logical_domain,
        generator_version=case.handle.realization.generator_version,
        config=MaterializationConfig(core_shape=(64, 64), halo_samples=8),
    )
    narrow = derive_query_footprint(
        path_points_mm=np.array(((25.0, 75.0), (125.0, 75.0)), dtype=np.float64),
        geometry_offsets_mm=np.array(((-0.2, -0.4), (0.2, 0.4)), dtype=np.float64),
        guard_mm=0.1,
        logical_domain=case.handle.realization.logical_domain,
    )
    wide = derive_query_footprint(
        path_points_mm=np.array(((25.0, 75.0), (125.0, 75.0)), dtype=np.float64),
        geometry_offsets_mm=np.array(((-0.2, -10.0), (0.2, 10.0)), dtype=np.float64),
        guard_mm=0.1,
        logical_domain=case.handle.realization.logical_domain,
    )
    common = sorted(
        set(
            materializer.tile_coordinates_for_footprint(
                narrow, reference_rt_mm=0.05, lod=LODLevel.RT_OVER_5
            )
        )
        & set(
            materializer.tile_coordinates_for_footprint(
                wide, reference_rt_mm=0.05, lod=LODLevel.RT_OVER_5
            )
        )
    )
    if not common:
        raise RuntimeError("narrow/wide footprints must have an overlapping tile")
    central = min(common, key=lambda value: abs(value[0] - 117) + abs(value[1] - 117))
    narrow_tile = materializer.sample_tile(
        narrow,
        central,
        reference_rt_mm=0.05,
        lod=LODLevel.RT_OVER_5,
    )
    wide_tile = materializer.sample_tile(
        wide,
        central,
        reference_rt_mm=0.05,
        lod=LODLevel.RT_OVER_5,
    )
    overlap_error = float(
        np.max(np.abs(narrow_tile.payload.height_mm - wide_tile.payload.height_mm))
    )
    receipts = (
        _materialization_record(run_id, case, narrow_tile.receipt),
        _materialization_record(run_id, case, wide_tile.receipt),
    )
    validation = (
        _validation_record(
            run_id,
            case,
            fixture="narrow_wide_100mm_footprint_overlap",
            metric="bitwise_height_overlap_max_abs_mm",
            tolerance=0.0,
            observed=overlap_error,
            passed=np.array_equal(narrow_tile.payload.height_mm, wide_tile.payload.height_mm),
            evidence_ref="tests/surface/test_materialization.py",
        ),
        _validation_record(
            run_id,
            case,
            fixture="hierarchical_real_construction",
            metric="imaginary_relative_residual",
            tolerance=1.0e-12,
            observed=evaluator.statistics.imaginary_relative_residual,
            passed=evaluator.statistics.imaginary_relative_residual <= 1.0e-12,
            evidence_ref="tests/surface/test_synthetic.py",
        ),
        _validation_record(
            run_id,
            case,
            fixture="coefficient_parseval",
            metric="relative_variance_error",
            tolerance=1.0e-12,
            observed=evaluator.statistics.parseval_relative_error,
            passed=evaluator.statistics.parseval_relative_error <= 1.0e-12,
            evidence_ref="tests/surface/test_synthetic.py",
        ),
    )
    sample = materializer.sample_visualization_window(DEMO_WINDOW_MM, grid_shape)
    stats = dataclasses.asdict(materializer.stats)
    stats["normal_path_builds_full_domain_rt10_dense"] = NORMAL_PATH_BUILDS_FULL_DOMAIN_RT10_DENSE
    stats["narrow_footprint_id"] = narrow.footprint_id
    stats["wide_footprint_id"] = wide.footprint_id
    stats["overlap_max_abs_error_mm"] = overlap_error
    return sample, receipts, validation, stats


def _array_payloads(
    case: DemoCase, sample: VisualizationSample
) -> tuple[RegisteredArrayPayload, ...]:
    return (
        RegisteredArrayPayload(
            field_id=VISUALIZATION_HEIGHT_FIELD,
            case_id=case.case_id,
            data=np.asarray(sample.height_mm, dtype=np.float64),
            validity=np.asarray(sample.validity, dtype=np.bool_),
            status=None,
            unit="mm",
            frame="M01_SURFACE_XY_HEIGHT_Z",
            reference_point="M01_LOGICAL_DOMAIN_ORIGIN",
            source_identity=SourceIdentity.DEV_POLICY,
        ),
        RegisteredArrayPayload(
            field_id=VISUALIZATION_VALIDITY_FIELD,
            case_id=case.case_id,
            data=np.asarray(sample.validity, dtype=np.bool_),
            validity=None,
            status=None,
            unit="1",
            frame="M01_SURFACE_XY_HEIGHT_Z",
            reference_point="M01_LOGICAL_DOMAIN_ORIGIN",
            source_identity=SourceIdentity.DEV_POLICY,
        ),
        RegisteredArrayPayload(
            field_id=VISUALIZATION_COORDINATES_FIELD,
            case_id=case.case_id,
            data=np.vstack((sample.x_coordinates_mm, sample.y_coordinates_mm)).astype(
                np.float64, copy=False
            ),
            validity=None,
            status=None,
            unit="mm",
            frame="M01_SURFACE_XY_HEIGHT_Z",
            reference_point="M01_LOGICAL_DOMAIN_ORIGIN",
            source_identity=SourceIdentity.DEV_POLICY,
        ),
    )


def _render_saved_previews(
    bundle_path: Path,
    cases: tuple[DemoCase, ...],
    preview_directory: Path,
) -> tuple[Path, ...]:
    from .preview.recipes import HEIGHT_MAP_2D, OBLIQUE_3D_SURFACE, render_preview

    reader = ResultReader.open(bundle_path, VerifyMode.MANIFEST)
    preview_directory.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for case in cases:
        from .preview.recipes import sample_from_result_reader

        sample = sample_from_result_reader(reader, case.case_id)
        for recipe, suffix in ((HEIGHT_MAP_2D, "2d"), (OBLIQUE_3D_SURFACE, "3d")):
            path = preview_directory / f"m01_{case.tier.value}_{suffix}.png"
            render_preview(
                sample,
                recipe,
                path,
                title_label=f"synthetic unidentified — {case.tier.value} tier",
                vertical_exaggeration=4.0 if recipe == OBLIQUE_3D_SURFACE else 1.0,
            )
            paths.append(path)
    return tuple(paths)


def generate_validation_demo(
    destination: str | Path,
    *,
    preview_directory: str | Path | None = None,
    grid_shape: tuple[int, int] = DEFAULT_DEMO_GRID_SHAPE,
    render_previews: bool = False,
) -> DemoArtifacts:
    """Create, publish, fully verify, and read back the §14.6 M01 demo."""

    started = time.perf_counter()
    output = Path(destination)
    if len(grid_shape) != 2 or grid_shape[0] != grid_shape[1] or grid_shape[0] < 2:
        raise ValueError("M01 full-domain demo grid must be square and at least 2 x 2")
    grid_size = int(grid_shape[0])
    cases = _make_cases(grid_size)
    repo_root = Path(__file__).resolve().parents[3]
    source_paths = (
        repo_root / "docs/simulator_development/requirements/M01_SURFACE_REQUIREMENTS.md",
        repo_root
        / "docs/simulator_development/implementation_prompts/M01_SURFACE_IMPLEMENTATION_WINDOW_PROMPT.md",
        repo_root / "theory/modules/A_INTEGRATED_MODEL.md",
        repo_root / "theory/evidence_reassessment/engineering_fixed_context.md",
    )
    source_hashes = {
        path.relative_to(repo_root).as_posix(): source_file_hash(path) for path in source_paths
    }
    registry = SchemaRegistry()
    registry.register_extension(surface_result_extension())
    registry_hash = registry.freeze()
    resolved_run = _resolved_config(
        "multi_tier_demo", grid_size, config_kind="m01_resolved_run_config"
    )
    case_configs = {case.case_id: case.resolved_config for case in cases}
    case_ids = tuple(case.case_id for case in cases)
    idempotency_keys = tuple(f"M01_VALIDATION_ONLY_{case.tier.value.upper()}_TX" for case in cases)
    realization_ids = tuple(case.handle.realization.surface_realization_id for case in cases)
    git_commit, dirty_status = _git_state(repo_root)
    replay_seed = {
        "case_execution_plan": case_ids,
        "idempotency_keys": idempotency_keys,
        "root_seed": DEMO_ROOT_SEED,
        "runtime": platform.python_version(),
    }
    envelope = make_run_envelope(
        registry_hash=registry_hash,
        resolved_run_config=resolved_run,
        operation_kind="M01_VALIDATION_ONLY",
        operation_profile="SURFACE_GEOMETRY_NO_CONTACT_NO_LOAD",
        source_file_hashes=source_hashes,
        replay_manifest=replay_seed,
        git_commit=git_commit,
        dirty_status=dirty_status,
        provenance_labels=(
            "VALIDATION_ONLY",
            "DEV_PRIOR",
            "synthetic_unidentified",
            "no_contact_or_force",
            "not_certifiable",
        ),
    )
    replay = make_replay_manifest(
        run_id=envelope.run_id,
        run_fingerprint=envelope.run_fingerprint,
        result_api_version=RESULT_API_VERSION,
        bundle_schema_version=BUNDLE_SCHEMA_VERSION,
        resolved_run_config_hash=resolved_run.semantic_hash,
        resolved_case_config_hashes={
            case_id: config.semantic_hash for case_id, config in case_configs.items()
        },
        source_hashes=source_hashes,
        registry_hash=registry_hash,
        git_commit=git_commit,
        dirty_status=dirty_status,
        case_execution_plan=case_ids,
        idempotency_keys=idempotency_keys,
        root_seeds=(DEMO_ROOT_SEED,),
        stream_namespaces=("m01.surface", DEMO_LATENT_NAMESPACE),
        surface_identities=realization_ids,
        field_tolerances={
            "imaginary_relative_residual": 1.0e-12,
            "Rt8_to_Rt10_envelope_over_Rt": 0.01,
            "Rt8_to_Rt10_support_position_over_Rt": 0.02,
            "Rt8_to_Rt10_normal_angle_deg": 1.0,
        },
    )
    replay = dataclasses.replace(
        replay,
        solver_build_id="M01_SURFACE_GEOMETRY_ONLY_1.0.0",
        model_contract_versions=(
            "M00_FOUNDATION_REQUIREMENTS 1.0.0 frozen",
            "M01_SURFACE_REQUIREMENTS 1.0.0 frozen",
            "A_INTEGRATED_MODEL 1.0.0 accepted surface geometry only",
        ),
        unit_frame_reference_transform_hash=semantic_hash(
            "N-mm-MPa/M01_SURFACE_XY_HEIGHT_Z/M01_LOGICAL_DOMAIN_ORIGIN"
        ),
        boundary_manifest_hash=semantic_hash("150mm parent; public ERROR; periodic latent"),
        rng_algorithm_version=RNG_PROFILE_ID,
        numerical_backend="numpy float64 random-access periodic Fourier mode sum",
        thread_and_float_settings={
            "canonical_numeric_dtype": "float64",
            "mode_reduction_order": "band_then_global_mode_coordinate",
            "full_domain_rt10_dense_normal_path": False,
            "memory_cache_budget_mib": 512,
        },
        determinism_profile="M01_COORDINATE_KEYED_RANDOM_ACCESS_1.0.0",
        diagnostic_level="full_validation_demo",
    )
    replay_payload = dataclasses.asdict(replay)
    envelope = dataclasses.replace(
        envelope,
        engineering_model_contract_versions=(
            *envelope.engineering_model_contract_versions,
            "M01_SURFACE_REQUIREMENTS 1.0.0 frozen",
        ),
        solver_build_id="M01_SURFACE_GEOMETRY_ONLY_1.0.0",
        frame_registry_id="M01_SURFACE_XY_HEIGHT_Z_1.0.0",
        reference_registry_id="M01_LOGICAL_DOMAIN_ORIGIN_1.0.0",
        transform_registry_id="M01_IDENTITY_SURFACE_TRANSFORM_1.0.0",
        replay_manifest_id=replay.replay_manifest_id,
        replay_manifest_hash=semantic_hash(replay_payload),
    )
    writer = ResultWriter.create_run_bundle(
        output,
        registry=registry,
        run_envelope=envelope,
        zarr_chunk_shape=(512, 512),
    )
    writer.write_resolved_config_and_provenance(
        resolved_run,
        provenance={
            "source_identity": "DEV_POLICY + VALIDATION_ONLY",
            "requirement_origin": DEMO_REQUIREMENT_ORIGIN,
            "authority_refs": source_hashes,
            "surface_realization_ids": realization_ids,
            "shared_latent_noise_id": cases[0].handle.realization.latent_noise_id,
            "interpretation_exclusions": [
                "no_measured_surface_truth",
                "no_contact_or_friction",
                "no_load_or_material_failure",
                "no_engagement_or_success_classification",
                "no_M02_M03_M06_semantics",
            ],
        },
        replay_manifest=replay_payload,
    )
    samples: dict[str, VisualizationSample] = {}
    materialization_stats: dict[str, dict[str, Any]] = {}
    for case, idempotency_key in zip(cases, idempotency_keys, strict=True):
        realization = case.handle.realization
        writer.create_case_shard(
            case.case_id,
            design_id=case.design_id,
            seed_id=realization.seed_id or "NOT_APPLICABLE",
            surface_realization_id=realization.surface_realization_id,
            resolved_case_config=case.resolved_config,
        )
        sample, materialization_records, validation_records, cache_stats = _sample_and_materialize(
            run_id=envelope.run_id, case=case, grid_shape=grid_shape
        )
        samples[case.case_id] = sample
        materialization_stats[case.tier.value] = cache_stats
        records: list[Any] = [
            _realization_record(envelope.run_id, case),
            _provenance_record(envelope.run_id, case),
            *_quality_records(envelope.run_id, case),
            *_statistic_records(envelope.run_id, case),
            *materialization_records,
            *validation_records,
        ]
        if case.tier is RoughnessTier.MEDIUM:
            records.extend(_analytic_fixture_validation_records(envelope.run_id, case))
            records.extend(_unavailable_records(envelope.run_id, case))
        parent_state_id = stable_content_id(
            "state", {"case": case.case_id, "kind": "M01_GEOMETRY_ONLY_PARENT"}
        )
        transaction = writer.begin_transaction(case.case_id, parent_state_id, idempotency_key)
        transaction.stage_accepted_point(*records)
        for payload in _array_payloads(case, sample):
            transaction.stage_chunked_array(payload)
        transaction.stage_state_and_ledger_references(
            ("M01_SURFACE_GEOMETRY_ONLY_NO_PHYSICAL_STATE_ADVANCE",)
        )
        transaction.prepare()
        transaction.commit()
        writer.finalize_case(case.case_id)
    manifest_path = writer.publish_run_manifest()

    reader = ResultReader.open(output, VerifyMode.FULL)
    realization_rows = reader.query(
        SURFACE_REALIZATIONS_DATASET,
        ("case_id", "surface_realization_id", "latent_noise_id", "material_label"),
    ).read_all()
    if realization_rows.num_rows != 3:
        raise RuntimeError("M01 demo ResultReader round trip lost realization records")
    for case in cases:
        height = reader.open_array(VISUALIZATION_HEIGHT_FIELD, case.case_id).read()["values"]
        if tuple(np.asarray(height).shape) != grid_shape:
            raise RuntimeError("M01 demo visualization array round trip changed shape")
    diagnostic_counts = {
        dataset: reader.query(
            dataset,
            filters=(FilterSpec("run_id", "==", envelope.run_id),),
            include_non_default=True,
        )
        .read_all()
        .num_rows
        for dataset in (
            MATERIALIZATION_RECEIPTS_DATASET,
            VALIDATION_RESULTS_DATASET,
            SOURCE_AVAILABILITY_DATASET,
        )
    }
    canonical_counts = {
        dataset: reader.query(dataset).read_all().num_rows
        for dataset in (
            SURFACE_REALIZATIONS_DATASET,
            SURFACE_PROVENANCE_DATASET,
            SURFACE_QUALITY_BANDS_DATASET,
            SURFACE_STATISTICS_DATASET,
        )
    }
    preview_paths: tuple[Path, ...] = ()
    if render_previews:
        target = (
            Path(preview_directory)
            if preview_directory is not None
            else repo_root / "reports/m01/demo"
        )
        preview_paths = _render_saved_previews(output, cases, target)
    elapsed = time.perf_counter() - started
    summary_path = output.parent / "M01_DEMO_SUMMARY.json"
    write_json_atomic(
        summary_path,
        {
            "bundle_path": output.as_posix(),
            "bundle_manifest": manifest_path.as_posix(),
            "run_id": envelope.run_id,
            "case_ids": case_ids,
            "surface_realization_ids": realization_ids,
            "shared_latent_noise_id": cases[0].handle.realization.latent_noise_id,
            "grid_shape": grid_shape,
            "window_mm": DEMO_WINDOW_MM,
            "canonical_dataset_row_counts": canonical_counts,
            "diagnostic_dataset_row_counts": diagnostic_counts,
            "materialization": materialization_stats,
            "preview_paths": tuple(path.as_posix() for path in preview_paths),
            "reader_compatibility_status": reader.compatibility_status,
            "full_integrity_verification": "PASS",
            "full_domain_rt10_dense_created": False,
            "experimentally_validated": "BLOCKED_UNAVAILABLE",
            "certification_status": "NOT_CERTIFIABLE",
            "elapsed_seconds": elapsed,
        },
    )
    return DemoArtifacts(
        output,
        manifest_path,
        summary_path,
        case_ids,
        realization_ids,
        preview_paths,
        elapsed,
    )


def catalog_overview(bundle: str | Path) -> dict[str, Any]:
    reader = ResultReader.open(bundle, VerifyMode.MANIFEST)
    return {
        "bundle": Path(bundle).as_posix(),
        "compatibility_status": reader.compatibility_status,
        "datasets": [
            item.dataset_id
            for item in reader.list_datasets(
                include_non_default=True, include_diagnostics=True
            ).entries
            if item.dataset_id.startswith("m01.")
        ],
        "surface_realizations": reader.query(
            SURFACE_REALIZATIONS_DATASET,
            ("case_id", "surface_realization_id", "material_label"),
        )
        .read_all()
        .to_pylist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the M01 VALIDATION_ONLY surface demo bundle and previews"
    )
    parser.add_argument(
        "destination",
        nargs="?",
        default="build/M01_VALIDATION_ONLY.spine-result",
    )
    parser.add_argument(
        "--preview-directory",
        default="reports/m01/demo",
        help="directory for the six optional PNG previews",
    )
    parser.add_argument("--grid-size", type=int, default=1024)
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="write the canonical bundle without importing the optional preview dependency",
    )
    args = parser.parse_args()
    artifacts = generate_validation_demo(
        args.destination,
        preview_directory=args.preview_directory,
        grid_shape=(args.grid_size, args.grid_size),
        render_previews=not args.no_render,
    )
    print(
        json.dumps(
            {
                **catalog_overview(artifacts.bundle_path),
                "summary": artifacts.summary_path.as_posix(),
                "preview_paths": tuple(path.as_posix() for path in artifacts.preview_paths),
                "elapsed_seconds": artifacts.elapsed_seconds,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
