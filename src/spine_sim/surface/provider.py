"""M01 source validation, immutable realization creation, and capability gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    AttemptOutcome,
    AuthorityRef,
    CapabilityStatus,
    CertificationStatus,
    SourceIdentity,
    StatusTuple,
)

from .contracts import (
    GENERATOR_ID,
    GENERATOR_VERSION,
    NORMAL_TRANSFORM_ID,
    QUERY_CONTRACT_VERSION,
    REALIZATION_SCHEMA_VERSION,
    RNG_PROFILE_ID,
    SOURCE_SCHEMA_VERSION,
    SYNTHETIC_MATERIAL_LABEL,
    BoundaryMode,
    CapabilityEntry,
    CapabilityManifest,
    Domain2D,
    LatentNoiseIdentity,
    M01ReasonCode,
    QueryCapability,
    SurfaceCreationResult,
    SurfaceFamily,
    SurfaceRealization,
    SurfaceSourceDescriptor,
    SurfaceSourceKind,
    SurfaceSpec,
    canonical_parameters,
    m01_maturity,
    not_applicable_status,
    supported_status,
    unavailable_status,
)

ANALYTIC_GENERATOR_ID = "M01_ANALYTIC_SURFACE_LIBRARY"
ANALYTIC_GENERATOR_VERSION = "1.0.0"

MEASURED_RESERVED_FIELDS = (
    "instrument_make_model",
    "acquisition_principle",
    "calibration_id",
    "probe_geometry_or_tip_radius",
    "MTF",
    "SNR",
    "native_point_spacing_x_y",
    "native_sampling_layout",
    "trusted_cutoff_by_direction",
    "registration_error",
    "detrend",
    "interpolation",
    "filtering",
    "windowing_steps",
    "missing_data_mask",
    "contamination_or_defect_labels",
    "steep_slope_dropout",
    "narrow_valley_access_limitation",
    "height_normal_position_uncertainty_bands",
    "batch",
    "location",
    "track",
    "material_direction",
    "holdout_identity",
    "raw_grid_point_cloud_mesh_artifact_identities",
)


@dataclass(frozen=True, slots=True)
class SurfaceQueryHandle:
    """Logical read-only handle; evaluator caches never enter realization identity."""

    handle_id: str
    realization: SurfaceRealization
    spec: SurfaceSpec
    evaluator: Any

    def __post_init__(self) -> None:
        expected = stable_content_id(
            "surface_query_handle",
            {
                "surface_realization_id": self.realization.surface_realization_id,
                "query_contract_version": self.realization.query_contract_version,
            },
        )
        if self.handle_id != expected:
            raise ContractViolation("surface query handle ID mismatch")


def _authority_refs() -> tuple[AuthorityRef, ...]:
    refs = (
        (
            "docs/simulator_development/requirements/M01_SURFACE_REQUIREMENTS.md",
            "1.0.0",
        ),
        ("theory/modules/A_INTEGRATED_MODEL.md", "1.0.0 accepted"),
        ("theory/evidence_reassessment/engineering_fixed_context.md", "1.0.0"),
    )
    return tuple(
        AuthorityRef(path, version, semantic_hash({"path": path, "version": version}), "M01 scope")
        for path, version in refs
    )


def _source_preimage(values: dict[str, Any]) -> dict[str, Any]:
    excluded = {
        "source_descriptor_id",
        "raw_artifact_status",
        "value_provenance",
        "authority_refs",
        "maturity",
    }
    return {key: values[key] for key in values if key not in excluded}


def _source_descriptor(
    *,
    source_kind: SurfaceSourceKind,
    material_label: str,
    boundary_mode: BoundaryMode,
    material_direction_rad: float | None,
    measured_fields: dict[str, str | None] | None = None,
) -> SurfaceSourceDescriptor:
    measured = measured_fields or {}
    unknown_measured = set(measured) - set(MEASURED_RESERVED_FIELDS)
    if unknown_measured:
        raise ContractViolation(
            "unknown measured source descriptor fields",
            details={"fields": sorted(unknown_measured)},
        )
    is_measured = source_kind is SurfaceSourceKind.MEASURED
    is_synthetic = source_kind is SurfaceSourceKind.SYNTHETIC
    source_identity = (
        SourceIdentity.PROPOSED_SUPPLEMENT
        if is_measured
        else SourceIdentity.DEV_POLICY
        if is_synthetic
        else SourceIdentity.VALIDATION_ONLY
    )
    capability = CapabilityStatus.UNAVAILABLE if is_measured else CapabilityStatus.SUPPORTED
    outcome = AttemptOutcome.NOT_ATTEMPTED if is_measured else AttemptOutcome.ACCEPTED
    reason = M01ReasonCode.MEASURED_IMPORT_DEFERRED.value if is_measured else M01ReasonCode.OK.value
    generator_id = (
        "M01_MEASURED_ACQUISITION_DEFERRED"
        if is_measured
        else GENERATOR_ID
        if is_synthetic
        else ANALYTIC_GENERATOR_ID
    )
    generator_version = (
        "0.0.0-deferred"
        if is_measured
        else GENERATOR_VERSION
        if is_synthetic
        else ANALYTIC_GENERATOR_VERSION
    )
    values: dict[str, Any] = {
        "source_descriptor_id": "deferred",
        "schema_version": SOURCE_SCHEMA_VERSION,
        "source_kind": source_kind,
        "source_identity": source_identity,
        "source_artifact_identity": None,
        "raw_identity_sha256": None,
        "raw_artifact_status": unavailable_status(
            M01ReasonCode.MEASURED_IMPORT_DEFERRED,
            "no measured raw artifact was imported in M01",
        )
        if is_measured
        else not_applicable_status("analytic/synthetic definitions have no measured raw artifact"),
        "source_frame_id": "M01_GLOBAL_WALL_XY_PLUS_Z",
        "surface_frame_id": "M01_SURFACE_XY_HEIGHT_Z",
        "material_frame_id": "M01_SYNTHETIC_DIRECTION_FRAME"
        if is_synthetic
        else "M01_ANALYTIC_DIRECTION_FRAME"
        if not is_measured
        else "M01_MEASURED_MATERIAL_FRAME_UNAVAILABLE",
        "transforms": (),
        "canonical_unit_system": "N-mm-MPa",
        "logical_domain": Domain2D(),
        "source_native_domain": None if is_measured else Domain2D(),
        "material_label": material_label,
        "material_direction_rad": material_direction_rad,
        "direction_equivalence": "theta modulo pi; NOT_APPLICABLE when isotropic",
        "generator_or_acquisition_id": generator_id,
        "generator_or_acquisition_version": generator_version,
        "processing_chain": (),
        "boundary_mode": boundary_mode,
        "trusted_bands": (),
        "missing_data_declared": is_measured,
        "capability_status": capability,
        "attempt_outcome": outcome,
        "reason_code": reason,
        "requirement_origin": "M01_SURFACE_REQUIREMENTS 1.0.0 §5",
        "value_provenance": (),
        "authority_refs": _authority_refs(),
        "maturity": m01_maturity(numerical_evidence=not is_measured),
        "certification_status": CertificationStatus.CERTIFICATION_BLOCKED
        if is_measured
        else CertificationStatus.NOT_CERTIFIABLE,
        "measured_reserved_fields": tuple(
            (name, measured.get(name)) for name in MEASURED_RESERVED_FIELDS
        )
        if is_measured
        else (),
    }
    values["source_descriptor_id"] = stable_content_id("surface_source", _source_preimage(values))
    return SurfaceSourceDescriptor(**values)


def make_analytic_source_descriptor(
    *,
    boundary_mode: BoundaryMode = BoundaryMode.ERROR,
    material_direction_rad: float | None = None,
) -> SurfaceSourceDescriptor:
    return _source_descriptor(
        source_kind=SurfaceSourceKind.ANALYTIC,
        material_label="analytic_validation_fixture",
        boundary_mode=boundary_mode,
        material_direction_rad=material_direction_rad,
    )


def make_synthetic_source_descriptor(
    *,
    boundary_mode: BoundaryMode = BoundaryMode.ERROR,
    material_direction_rad: float | None = None,
) -> SurfaceSourceDescriptor:
    return _source_descriptor(
        source_kind=SurfaceSourceKind.SYNTHETIC,
        material_label=SYNTHETIC_MATERIAL_LABEL,
        boundary_mode=boundary_mode,
        material_direction_rad=material_direction_rad,
    )


def make_measured_source_descriptor(
    *,
    material_label: str = "measured_unidentified",
    reserved_fields: dict[str, str | None] | None = None,
) -> SurfaceSourceDescriptor:
    return _source_descriptor(
        source_kind=SurfaceSourceKind.MEASURED,
        material_label=material_label,
        boundary_mode=BoundaryMode.ERROR,
        material_direction_rad=None,
        measured_fields=reserved_fields,
    )


def validate_source_descriptor(descriptor: SurfaceSourceDescriptor) -> StatusTuple:
    """Return a typed capability result after dataclass construction enforced strict schema."""

    if descriptor.source_kind is SurfaceSourceKind.MEASURED:
        return unavailable_status(
            M01ReasonCode.MEASURED_IMPORT_DEFERRED,
            "measured descriptors are parse/validate-only in M01",
        )
    return supported_status()


def _spec_preimage(
    descriptor: SurfaceSourceDescriptor,
    family: SurfaceFamily,
    parameters: tuple[tuple[str, Any], ...],
    generator_id: str,
    generator_version: str,
) -> dict[str, Any]:
    return {
        "source_descriptor_id": descriptor.source_descriptor_id,
        "source_kind": descriptor.source_kind,
        "family": family,
        "logical_domain": descriptor.logical_domain,
        "parameters": parameters,
        "generator_id": generator_id,
        "generator_version": generator_version,
        "query_contract_version": QUERY_CONTRACT_VERSION,
        "boundary_mode": descriptor.boundary_mode,
        "material_label": descriptor.material_label,
        "source_frame_id": descriptor.source_frame_id,
        "surface_frame_id": descriptor.surface_frame_id,
        "material_frame_id": descriptor.material_frame_id,
        "source_identity": descriptor.source_identity,
    }


def _synthetic_capability_manifest(spec: SurfaceSpec) -> CapabilityManifest:
    entries = (
        CapabilityEntry(
            "height_differential",
            QueryCapability.EXACT,
            "M01_RANDOM_ACCESS_BAND_LIMITED_EVALUATOR",
            GENERATOR_VERSION,
            "declared trusted bands",
            "C-infinity for represented finite spectral sum",
            "none in represented field",
            (BoundaryMode.ERROR, BoundaryMode.PERIODIC),
            (
                ("height", QueryCapability.EXACT),
                ("gradient", QueryCapability.EXACT),
                ("normal", QueryCapability.EXACT),
                ("curvature", QueryCapability.EXACT),
            ),
        ),
        CapabilityEntry(
            "signed_distance",
            QueryCapability.APPROXIMATE,
            "M01_GLOBAL_CANDIDATE_CLOSEST_SEARCH",
            "1.0.0",
            "logical domain and declared search coverage",
            "smooth represented field",
            "co-minimal candidates retained",
            (BoundaryMode.ERROR, BoundaryMode.PERIODIC),
            (("signed_distance", QueryCapability.APPROXIMATE),),
        ),
        CapabilityEntry(
            "closest_features",
            QueryCapability.APPROXIMATE,
            "M01_GLOBAL_CANDIDATE_CLOSEST_SEARCH",
            "1.0.0",
            "logical domain and declared search coverage",
            "smooth represented field",
            "co-minimal candidates retained",
            (BoundaryMode.ERROR, BoundaryMode.PERIODIC),
            (("closest_features", QueryCapability.APPROXIMATE),),
        ),
        CapabilityEntry(
            "neighborhood",
            QueryCapability.APPROXIMATE,
            "M01_SYNTHETIC_LIPSCHITZ_NEIGHBORHOOD",
            "1.0.0",
            "logical domain and represented band",
            "smooth represented field",
            "none in represented field",
            (BoundaryMode.ERROR, BoundaryMode.PERIODIC),
            (
                ("height_bounds", QueryCapability.APPROXIMATE),
                ("slope_bound", QueryCapability.EXACT),
            ),
        ),
        CapabilityEntry(
            "spherical_envelope_or_clearance",
            QueryCapability.APPROXIMATE,
            "M01_COMPLETE_SPHERE_HEIGHT_ENVELOPE",
            "1.0.0",
            "probe disk inside query domain",
            "smooth represented field",
            "co-maximal supports retained",
            (BoundaryMode.ERROR, BoundaryMode.PERIODIC),
            (("spherical_envelope", QueryCapability.APPROXIMATE),),
        ),
    )
    manifest_id = stable_content_id(
        "surface_capability_manifest",
        {
            "family": spec.family,
            "query_contract_version": QUERY_CONTRACT_VERSION,
            "entries": entries,
            "source_identity": spec.source_identity,
        },
    )
    return CapabilityManifest(
        manifest_id,
        spec.family,
        QUERY_CONTRACT_VERSION,
        entries,
        spec.source_identity,
    )


class SurfaceProvider:
    """Stateless realization factory; measured/production mesh capabilities stay unavailable."""

    def create_surface_spec(
        self,
        descriptor: SurfaceSourceDescriptor,
        family: SurfaceFamily,
        parameters: dict[str, Any],
        *,
        generator_version: str | None = None,
    ) -> SurfaceCreationResult:
        if descriptor.source_kind is SurfaceSourceKind.MEASURED:
            return SurfaceCreationResult(
                None,
                None,
                None,
                unavailable_status(
                    M01ReasonCode.MEASURED_IMPORT_DEFERRED,
                    "measured descriptors cannot create an M01 surface spec/realization",
                ),
            )
        if (
            descriptor.source_kind is SurfaceSourceKind.ANALYTIC
            and family is SurfaceFamily.SELF_AFFINE_GAUSSIAN
        ):
            raise ContractViolation("self_affine_gaussian requires a synthetic source")
        if (
            descriptor.source_kind is SurfaceSourceKind.SYNTHETIC
            and family is not SurfaceFamily.SELF_AFFINE_GAUSSIAN
        ):
            raise ContractViolation("M01 synthetic source only supports self_affine_gaussian")
        generator_id = (
            GENERATOR_ID
            if descriptor.source_kind is SurfaceSourceKind.SYNTHETIC
            else ANALYTIC_GENERATOR_ID
        )
        version = generator_version or (
            GENERATOR_VERSION
            if descriptor.source_kind is SurfaceSourceKind.SYNTHETIC
            else ANALYTIC_GENERATOR_VERSION
        )
        try:
            if descriptor.source_kind is SurfaceSourceKind.SYNTHETIC:
                from .synthetic import validate_synthetic_parameters

                validate_synthetic_parameters(parameters)
            else:
                from .analytic import validate_analytic_parameters

                validate_analytic_parameters(family, parameters)
            canonical = canonical_parameters(parameters)
            preimage = _spec_preimage(descriptor, family, canonical, generator_id, version)
            spec = SurfaceSpec(
                stable_content_id("surface_spec", preimage),
                descriptor.source_descriptor_id,
                descriptor.source_kind,
                family,
                descriptor.logical_domain,
                canonical,
                generator_id,
                version,
                QUERY_CONTRACT_VERSION,
                descriptor.boundary_mode,
                descriptor.material_label,
                descriptor.source_frame_id,
                descriptor.surface_frame_id,
                descriptor.material_frame_id,
                "M01_SURFACE_REQUIREMENTS 1.0.0 §4/§6",
                descriptor.source_identity,
                CertificationStatus.NOT_CERTIFIABLE,
            )
        except (ContractViolation, TypeError, ValueError) as error:
            return SurfaceCreationResult(
                None,
                None,
                None,
                unavailable_status(
                    M01ReasonCode.INVALID_SURFACE_SPEC,
                    f"strict M01 surface parameter validation failed: {error}",
                ),
            )
        return SurfaceCreationResult(spec, None, None, supported_status())

    def create_realization(
        self,
        descriptor: SurfaceSourceDescriptor,
        spec: SurfaceSpec | None,
        *,
        latent_identity: LatentNoiseIdentity | None = None,
    ) -> SurfaceCreationResult:
        if descriptor.source_kind is SurfaceSourceKind.MEASURED or spec is None:
            return SurfaceCreationResult(
                None,
                None,
                None,
                unavailable_status(
                    M01ReasonCode.MEASURED_IMPORT_DEFERRED,
                    "measured creation/query is deferred and cannot mint an ID or handle",
                ),
            )
        if spec.source_descriptor_id != descriptor.source_descriptor_id:
            raise ContractViolation("surface spec belongs to a different source descriptor")
        evaluator: Any
        if spec.source_kind is SurfaceSourceKind.SYNTHETIC:
            if latent_identity is None:
                raise ContractViolation("synthetic realization requires explicit latent identity")
            from .synthetic import SyntheticEvaluator

            evaluator = SyntheticEvaluator(spec, latent_identity)
            capability = _synthetic_capability_manifest(spec)
            seed_id = latent_identity.seed_id
            latent_noise_id = latent_identity.latent_noise_id
            rng_profile_id = RNG_PROFILE_ID
            trusted_bands = tuple(getattr(evaluator, "trusted_bands", ()))
        else:
            if latent_identity is not None:
                raise ContractViolation("analytic realization must not receive latent noise")
            from .analytic import AnalyticEvaluator, capability_manifest

            evaluator = AnalyticEvaluator(spec)
            capability = capability_manifest(spec)
            seed_id = None
            latent_noise_id = None
            rng_profile_id = None
            trusted_bands = ()
        definition_hash = semantic_hash(
            {
                "spec": spec.identity_preimage(),
                "latent_noise_id": latent_noise_id,
                "rng_profile_id": rng_profile_id,
                "normal_transform_id": NORMAL_TRANSFORM_ID if latent_noise_id is not None else None,
                "generator_version": spec.generator_version,
                "evaluator_definition": getattr(evaluator, "definition_manifest", None),
            }
        )
        realization_id = stable_content_id(
            "surface_realization",
            {
                "surface_spec_id": spec.surface_spec_id,
                "seed_id": seed_id,
                "latent_noise_id": latent_noise_id,
                "generator_id": spec.generator_id,
                "generator_version": spec.generator_version,
                "definition_hash": definition_hash,
            },
        )
        realization = SurfaceRealization(
            realization_id,
            spec.surface_spec_id,
            REALIZATION_SCHEMA_VERSION,
            descriptor.source_descriptor_id,
            descriptor.source_kind,
            spec.family,
            descriptor.material_label,
            seed_id,
            latent_noise_id,
            rng_profile_id,
            spec.generator_id,
            spec.generator_version,
            QUERY_CONTRACT_VERSION,
            spec.logical_domain,
            spec.boundary_mode,
            spec.source_frame_id,
            spec.surface_frame_id,
            spec.material_frame_id,
            definition_hash,
            semantic_hash(descriptor.processing_chain),
            capability,
            trusted_bands,
            spec.source_identity,
            m01_maturity(),
            CertificationStatus.NOT_CERTIFIABLE,
            supported_status(),
        )
        handle_id = stable_content_id(
            "surface_query_handle",
            {
                "surface_realization_id": realization_id,
                "query_contract_version": QUERY_CONTRACT_VERSION,
            },
        )
        handle = SurfaceQueryHandle(handle_id, realization, spec, evaluator)
        return SurfaceCreationResult(spec, realization, handle, supported_status())

    @staticmethod
    def describe_realization(handle: SurfaceQueryHandle) -> SurfaceRealization:
        return handle.realization

    @staticmethod
    def get_capability_manifest(handle: SurfaceQueryHandle) -> CapabilityManifest:
        return handle.realization.capability_manifest

    @staticmethod
    def open_query_handle(result: SurfaceCreationResult) -> SurfaceQueryHandle | None:
        return result.handle if isinstance(result.handle, SurfaceQueryHandle) else None

    @staticmethod
    def request_external_mesh_or_point_cloud_import() -> SurfaceCreationResult:
        return SurfaceCreationResult(
            None,
            None,
            None,
            unavailable_status(
                M01ReasonCode.EXTERNAL_MESH_IMPORT_DEFERRED,
                "production point-cloud and arbitrary-mesh import is unavailable in M01",
            ),
        )
