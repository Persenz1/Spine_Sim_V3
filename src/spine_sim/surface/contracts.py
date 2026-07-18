"""Strict public contracts for immutable M01 surface realizations and queries."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any

import numpy as np
from numpy.typing import NDArray

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    AttemptOutcome,
    AuthorityRef,
    CapabilityStatus,
    CertificationStatus,
    Maturity,
    MaturityEvidence,
    MaturityStatus,
    PhysicalFeasibility,
    SourceIdentity,
    StatusTuple,
    ValuePresence,
    ValueProvenance,
)

SOURCE_SCHEMA_VERSION = "1.0.0"
REALIZATION_SCHEMA_VERSION = "1.0.0"
QUERY_CONTRACT_VERSION = "1.0.0"
GENERATOR_ID = "M01_HIERARCHICAL_RANDOM_ACCESS_SPECTRAL"
GENERATOR_VERSION = "1.0.0"
RNG_PROFILE_ID = "M01_PHILOX4X64_10_KEYED_1"
NORMAL_TRANSFORM_ID = "M01_BOX_MULLER_PAIR_1"
LOGICAL_PARENT_SIZE_MM = 150.0
MAXIMUM_DRAG_PATH_MM = 100.0
SYNTHETIC_MATERIAL_LABEL = "synthetic_unidentified"


class SurfaceSourceKind(StrEnum):
    ANALYTIC = "analytic"
    SYNTHETIC = "synthetic"
    MEASURED = "measured"


class SurfaceFamily(StrEnum):
    PLANE = "plane"
    SLOPE_PLANE = "slope_plane"
    SINUSOID_1D = "sinusoid_1d"
    SINUSOID_2D = "sinusoid_2d"
    GAUSSIAN_BUMP = "gaussian_bump"
    GAUSSIAN_PIT = "gaussian_pit"
    MULTI_GAUSSIAN_FEATURE = "multi_gaussian_feature"
    GROOVE_COSINE = "groove_cosine"
    GROOVE_SMOOTH = "groove_smooth"
    GROOVE_CIRCULAR = "groove_circular"
    GROOVE_V = "groove_v"
    KNOWN_NEAREST_FEATURE_SWITCH = "known_nearest_feature_switch"
    SPHERICAL_CAP = "spherical_cap"
    SPHERICAL_BOWL = "spherical_bowl"
    SELF_AFFINE_GAUSSIAN = "self_affine_gaussian"


class BoundaryMode(StrEnum):
    ERROR = "ERROR"
    PERIODIC = "PERIODIC"


class DomainStatus(StrEnum):
    IN_DOMAIN = "IN_DOMAIN"
    ON_BOUNDARY = "ON_BOUNDARY"
    WRAPPED = "WRAPPED"
    OUT_OF_DOMAIN = "OUT_OF_DOMAIN"


class QualityStatus(StrEnum):
    TRUSTED_FOR_DECLARED_SCALE = "TRUSTED_FOR_DECLARED_SCALE"
    RESOLUTION_REFINEMENT_REQUIRED = "RESOLUTION_REFINEMENT_REQUIRED"
    MISSING_SOURCE_DATA = "MISSING_SOURCE_DATA"
    GEOMETRY_UNCERTAIN = "GEOMETRY_UNCERTAIN"
    NONSMOOTH_FEATURE_SET = "NONSMOOTH_FEATURE_SET"


class QueryCapability(StrEnum):
    EXACT = "EXACT"
    APPROXIMATE = "APPROXIMATE"
    UNAVAILABLE = "UNAVAILABLE"


class ConvergenceLevel(StrEnum):
    ANALYTIC = "ANALYTIC"
    CONVERGED = "CONVERGED"
    REFINEMENT_REQUIRED = "REFINEMENT_REQUIRED"
    FAILED = "FAILED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RoughnessTier(StrEnum):
    GENTLE = "gentle"
    MEDIUM = "medium"
    SHARP = "sharp"
    EXPLICIT = "explicit"


class StatisticsScope(StrEnum):
    TARGET_ANALYTIC = "TARGET_ANALYTIC"
    REALIZED_COEFFICIENT_FULL_PARENT = "REALIZED_COEFFICIENT_FULL_PARENT"
    AUDIT_SAMPLE = "AUDIT_SAMPLE"
    ACTIVE_FOOTPRINT_SAMPLE = "ACTIVE_FOOTPRINT_SAMPLE"
    VISUALIZATION_SAMPLE = "VISUALIZATION_SAMPLE"


class M01ReasonCode(StrEnum):
    OK = "M01_OK"
    INVALID_SURFACE_SPEC = "M01_INVALID_SURFACE_SPEC"
    MEASURED_IMPORT_DEFERRED = "M01_MEASURED_IMPORT_DEFERRED"
    EXTERNAL_MESH_IMPORT_DEFERRED = "M01_EXTERNAL_MESH_IMPORT_DEFERRED"
    QUERY_CAPABILITY_UNAVAILABLE = "M01_QUERY_CAPABILITY_UNAVAILABLE"
    OUT_OF_DOMAIN = "M01_OUT_OF_DOMAIN"
    ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN = "M01_ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN"
    TRUST_SCALE_INSUFFICIENT = "M01_TRUST_SCALE_INSUFFICIENT"
    RESOLUTION_REFINEMENT_REQUIRED = "M01_RESOLUTION_REFINEMENT_REQUIRED"
    GEOMETRY_UNCERTAIN = "M01_GEOMETRY_UNCERTAIN"
    QUERY_APPROXIMATION_FAILED = "M01_QUERY_APPROXIMATION_FAILED"
    REPLAY_MISMATCH = "M01_REPLAY_MISMATCH"
    CACHE_CORRUPTION_REGENERATED = "M01_CACHE_CORRUPTION_REGENERATED"


def m01_maturity(*, numerical_evidence: bool = True) -> Maturity:
    """M01 software evidence without upgrading experimental maturity."""

    return Maturity(
        MaturityEvidence(
            MaturityStatus.SPEC_DEFINED,
            "M01_SURFACE_REQUIREMENTS 1.0.0 and accepted A surface geometry",
            "M01_SURFACE_REQUIREMENTS 1.0.0",
        ),
        MaturityEvidence(
            MaturityStatus.PASSED_WITH_EVIDENCE,
            "M01 analytic/synthetic surface implementation",
            GENERATOR_VERSION,
            ("tests/surface",),
        ),
        MaturityEvidence(
            MaturityStatus.PASSED_WITH_EVIDENCE
            if numerical_evidence
            else MaturityStatus.NOT_ASSESSED,
            "M01 geometry and generator validation",
            GENERATOR_VERSION,
            ("reports/m01/M01_VALIDATION_REPORT.md",) if numerical_evidence else (),
        ),
        MaturityEvidence(
            MaturityStatus.BLOCKED_UNAVAILABLE,
            "no target-surface measurement or experiment is available",
            None,
        ),
    )


def supported_status(reason: str = M01ReasonCode.OK) -> StatusTuple:
    return StatusTuple(
        ValuePresence.PRESENT,
        CapabilityStatus.SUPPORTED,
        AttemptOutcome.ACCEPTED,
        PhysicalFeasibility.NOT_ASSESSED,
        CertificationStatus.NOT_CERTIFIABLE,
        reason.value if isinstance(reason, M01ReasonCode) else reason,
        "M01 geometry is available for its declared analytic or DEV synthetic scope",
        ("M01_SURFACE_REQUIREMENTS 1.0.0",),
    )


def unavailable_status(reason: M01ReasonCode, explanation: str) -> StatusTuple:
    return StatusTuple(
        ValuePresence.NULL,
        CapabilityStatus.UNAVAILABLE,
        AttemptOutcome.NOT_ATTEMPTED,
        PhysicalFeasibility.NOT_ASSESSED,
        CertificationStatus.CERTIFICATION_BLOCKED,
        reason.value,
        explanation,
        ("M01_SURFACE_REQUIREMENTS 1.0.0",),
    )


def not_applicable_status(explanation: str) -> StatusTuple:
    return StatusTuple(
        ValuePresence.NULL,
        CapabilityStatus.NOT_APPLICABLE,
        AttemptOutcome.NOT_ATTEMPTED,
        PhysicalFeasibility.NOT_ASSESSED,
        CertificationStatus.NOT_CERTIFIABLE,
        "M01_NOT_APPLICABLE",
        explanation,
        ("M01_SURFACE_REQUIREMENTS 1.0.0",),
    )


@dataclass(frozen=True, slots=True)
class Domain2D:
    x_min_mm: float = 0.0
    x_max_mm: float = LOGICAL_PARENT_SIZE_MM
    y_min_mm: float = 0.0
    y_max_mm: float = LOGICAL_PARENT_SIZE_MM

    def __post_init__(self) -> None:
        values = (self.x_min_mm, self.x_max_mm, self.y_min_mm, self.y_max_mm)
        if not all(math.isfinite(item) for item in values):
            raise ContractViolation("M01 logical domain must be finite")
        if self.x_max_mm <= self.x_min_mm or self.y_max_mm <= self.y_min_mm:
            raise ContractViolation("M01 logical domain extents must be positive")
        if not math.isclose(self.width_mm, LOGICAL_PARENT_SIZE_MM) or not math.isclose(
            self.height_mm, LOGICAL_PARENT_SIZE_MM
        ):
            raise ContractViolation("M01 logical parent domain must be 150 x 150 mm")

    @property
    def width_mm(self) -> float:
        return self.x_max_mm - self.x_min_mm

    @property
    def height_mm(self) -> float:
        return self.y_max_mm - self.y_min_mm

    def contains(self, x_mm: float, y_mm: float, *, tolerance_mm: float = 1.0e-12) -> bool:
        return (
            self.x_min_mm - tolerance_mm <= x_mm <= self.x_max_mm + tolerance_mm
            and self.y_min_mm - tolerance_mm <= y_mm <= self.y_max_mm + tolerance_mm
        )

    def map_periodic(self, x_mm: float, y_mm: float) -> tuple[float, float]:
        x = self.x_min_mm + (x_mm - self.x_min_mm) % self.width_mm
        y = self.y_min_mm + (y_mm - self.y_min_mm) % self.height_mm
        return x, y


@dataclass(frozen=True, slots=True)
class FrameTransformRef:
    transform_id: str
    from_frame_id: str
    to_frame_id: str
    version: str
    sha256: str


@dataclass(frozen=True, slots=True)
class ProcessingStep:
    step_id: str
    algorithm_id: str
    algorithm_version: str
    parameters_hash: str
    input_hashes: tuple[str, ...]
    output_hash: str
    source_identity: SourceIdentity


@dataclass(frozen=True, slots=True)
class TrustedScaleBand:
    band_id: str
    q_min_rad_per_mm: float
    q_max_rad_per_mm: float
    lambda_max_mm: float
    lambda_min_mm: float
    direction_rad: float | None
    uncertainty_bound_mm: float
    status: QualityStatus

    def __post_init__(self) -> None:
        if self.q_min_rad_per_mm < 0.0 or self.q_max_rad_per_mm <= self.q_min_rad_per_mm:
            raise ContractViolation("invalid trusted wavenumber band")
        if self.lambda_min_mm <= 0.0 or self.lambda_max_mm < self.lambda_min_mm:
            raise ContractViolation("invalid trusted wavelength band")
        if self.uncertainty_bound_mm < 0.0:
            raise ContractViolation("uncertainty bound cannot be negative")


@dataclass(frozen=True, slots=True)
class SurfaceSourceDescriptor:
    source_descriptor_id: str
    schema_version: str
    source_kind: SurfaceSourceKind
    source_identity: SourceIdentity
    source_artifact_identity: str | None
    raw_identity_sha256: str | None
    raw_artifact_status: StatusTuple
    source_frame_id: str
    surface_frame_id: str
    material_frame_id: str
    transforms: tuple[FrameTransformRef, ...]
    canonical_unit_system: str
    logical_domain: Domain2D
    source_native_domain: Domain2D | None
    material_label: str
    material_direction_rad: float | None
    direction_equivalence: str
    generator_or_acquisition_id: str
    generator_or_acquisition_version: str
    processing_chain: tuple[ProcessingStep, ...]
    boundary_mode: BoundaryMode
    trusted_bands: tuple[TrustedScaleBand, ...]
    missing_data_declared: bool
    capability_status: CapabilityStatus
    attempt_outcome: AttemptOutcome
    reason_code: str
    requirement_origin: str
    value_provenance: tuple[ValueProvenance, ...]
    authority_refs: tuple[AuthorityRef, ...]
    maturity: Maturity
    certification_status: CertificationStatus
    measured_reserved_fields: tuple[tuple[str, str | None], ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != SOURCE_SCHEMA_VERSION:
            raise ContractViolation("unsupported M01 source descriptor schema version")
        if self.canonical_unit_system != "N-mm-MPa":
            raise ContractViolation("M01 source must use the N-mm-MPa canonical unit system")
        if self.source_kind is SurfaceSourceKind.SYNTHETIC:
            if self.material_label != SYNTHETIC_MATERIAL_LABEL:
                raise ContractViolation(
                    "synthetic surfaces must use material_label=synthetic_unidentified"
                )
            if self.source_identity is not SourceIdentity.DEV_POLICY:
                raise ContractViolation("synthetic surfaces require DEV_POLICY source identity")
        if self.source_kind is SurfaceSourceKind.MEASURED:
            if self.capability_status is not CapabilityStatus.UNAVAILABLE:
                raise ContractViolation("measured import is schema-only in M01")
            if self.reason_code != M01ReasonCode.MEASURED_IMPORT_DEFERRED:
                raise ContractViolation("measured descriptor must carry the frozen deferred code")
        elif self.capability_status is not CapabilityStatus.SUPPORTED:
            raise ContractViolation("analytic/synthetic descriptors must be supported")
        if self.material_direction_rad is not None and not math.isfinite(
            self.material_direction_rad
        ):
            raise ContractViolation("material direction must be finite")
        expected = stable_content_id("surface_source", self.identity_preimage())
        if self.source_descriptor_id != expected:
            raise ContractViolation("source_descriptor_id does not match canonical content")

    def identity_preimage(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_kind": self.source_kind,
            "source_identity": self.source_identity,
            "source_artifact_identity": self.source_artifact_identity,
            "raw_identity_sha256": self.raw_identity_sha256,
            "source_frame_id": self.source_frame_id,
            "surface_frame_id": self.surface_frame_id,
            "material_frame_id": self.material_frame_id,
            "transforms": self.transforms,
            "canonical_unit_system": self.canonical_unit_system,
            "logical_domain": self.logical_domain,
            "source_native_domain": self.source_native_domain,
            "material_label": self.material_label,
            "material_direction_rad": self.material_direction_rad,
            "direction_equivalence": self.direction_equivalence,
            "generator_or_acquisition_id": self.generator_or_acquisition_id,
            "generator_or_acquisition_version": self.generator_or_acquisition_version,
            "processing_chain": self.processing_chain,
            "boundary_mode": self.boundary_mode,
            "trusted_bands": self.trusted_bands,
            "missing_data_declared": self.missing_data_declared,
            "capability_status": self.capability_status,
            "attempt_outcome": self.attempt_outcome,
            "reason_code": self.reason_code,
            "requirement_origin": self.requirement_origin,
            "certification_status": self.certification_status,
            "measured_reserved_fields": self.measured_reserved_fields,
        }


@dataclass(frozen=True, slots=True)
class SurfaceSpec:
    surface_spec_id: str
    source_descriptor_id: str
    source_kind: SurfaceSourceKind
    family: SurfaceFamily
    logical_domain: Domain2D
    parameters: tuple[tuple[str, Any], ...]
    generator_id: str
    generator_version: str
    query_contract_version: str
    boundary_mode: BoundaryMode
    material_label: str
    source_frame_id: str
    surface_frame_id: str
    material_frame_id: str
    requirement_origin: str
    source_identity: SourceIdentity
    certification_status: CertificationStatus

    def __post_init__(self) -> None:
        names = tuple(name for name, _ in self.parameters)
        if names != tuple(sorted(names)) or len(set(names)) != len(names):
            raise ContractViolation("surface parameters must have unique canonical sorted names")
        if self.query_contract_version != QUERY_CONTRACT_VERSION:
            raise ContractViolation("unsupported M01 query contract version")
        if self.source_kind is SurfaceSourceKind.SYNTHETIC:
            if self.family is not SurfaceFamily.SELF_AFFINE_GAUSSIAN:
                raise ContractViolation("M01 synthetic source only supports self_affine_gaussian")
            if self.material_label != SYNTHETIC_MATERIAL_LABEL:
                raise ContractViolation("synthetic spec cannot claim a real material identity")
        if (
            self.source_kind is SurfaceSourceKind.ANALYTIC
            and self.family is SurfaceFamily.SELF_AFFINE_GAUSSIAN
        ):
            raise ContractViolation("self_affine_gaussian requires a synthetic source")
        expected = stable_content_id("surface_spec", self.identity_preimage())
        if self.surface_spec_id != expected:
            raise ContractViolation("surface_spec_id does not match canonical spec content")

    def identity_preimage(self) -> dict[str, Any]:
        return {
            "source_descriptor_id": self.source_descriptor_id,
            "source_kind": self.source_kind,
            "family": self.family,
            "logical_domain": self.logical_domain,
            "parameters": self.parameters,
            "generator_id": self.generator_id,
            "generator_version": self.generator_version,
            "query_contract_version": self.query_contract_version,
            "boundary_mode": self.boundary_mode,
            "material_label": self.material_label,
            "source_frame_id": self.source_frame_id,
            "surface_frame_id": self.surface_frame_id,
            "material_frame_id": self.material_frame_id,
            "source_identity": self.source_identity,
        }

    def parameter_map(self) -> MappingProxyType[str, Any]:
        return MappingProxyType(dict(self.parameters))


@dataclass(frozen=True, slots=True)
class LatentNoiseIdentity:
    latent_noise_id: str
    seed_id: str
    root_seed: int
    surface_seed_index: int
    stream_namespace: str
    latent_noise_namespace: str
    rng_profile_id: str
    normal_transform_id: str

    def __post_init__(self) -> None:
        if not 0 <= self.root_seed < 1 << 128:
            raise ContractViolation("root_seed must be an unsigned 128-bit integer")
        if not 0 <= self.surface_seed_index < 1 << 64:
            raise ContractViolation("surface_seed_index must be an unsigned 64-bit integer")
        if self.stream_namespace != "m01.surface":
            raise ContractViolation("M01 RNG stream namespace must be m01.surface")
        if self.rng_profile_id != RNG_PROFILE_ID:
            raise ContractViolation("unsupported M01 RNG profile")
        if self.normal_transform_id != NORMAL_TRANSFORM_ID:
            raise ContractViolation("unsupported M01 normal transform")
        seed_expected = stable_content_id(
            "seed",
            {
                "rng_profile_id": self.rng_profile_id,
                "stream_namespace": self.stream_namespace,
                "root_seed": self.root_seed,
                "surface_seed_index": self.surface_seed_index,
            },
        )
        latent_expected = stable_content_id(
            "latent_noise",
            {
                "seed_id": seed_expected,
                "latent_noise_namespace": self.latent_noise_namespace,
                "normal_transform_id": self.normal_transform_id,
            },
        )
        if self.seed_id != seed_expected or self.latent_noise_id != latent_expected:
            raise ContractViolation("seed_id or latent_noise_id does not match canonical identity")


@dataclass(frozen=True, slots=True)
class CapabilityEntry:
    operation: str
    capability: QueryCapability
    method_id: str
    method_version: str
    parameter_domain: str
    smoothness: str
    nonsmooth_set: str
    boundary_compatibility: tuple[BoundaryMode, ...]
    field_capabilities: tuple[tuple[str, QueryCapability], ...]


@dataclass(frozen=True, slots=True)
class CapabilityManifest:
    manifest_id: str
    family: SurfaceFamily
    query_contract_version: str
    entries: tuple[CapabilityEntry, ...]
    source_identity: SourceIdentity

    def __post_init__(self) -> None:
        expected = stable_content_id(
            "surface_capability_manifest",
            {
                "family": self.family,
                "query_contract_version": self.query_contract_version,
                "entries": self.entries,
                "source_identity": self.source_identity,
            },
        )
        if self.manifest_id != expected:
            raise ContractViolation("capability manifest ID mismatch")

    def for_operation(self, operation: str) -> CapabilityEntry | None:
        return next((item for item in self.entries if item.operation == operation), None)


@dataclass(frozen=True, slots=True)
class SurfaceRealization:
    surface_realization_id: str
    surface_spec_id: str
    realization_schema_version: str
    source_descriptor_id: str
    source_kind: SurfaceSourceKind
    family: SurfaceFamily
    material_label: str
    seed_id: str | None
    latent_noise_id: str | None
    rng_profile_id: str | None
    generator_id: str
    generator_version: str
    query_contract_version: str
    logical_domain: Domain2D
    boundary_mode: BoundaryMode
    source_frame_id: str
    surface_frame_id: str
    material_frame_id: str
    definition_hash: str
    provenance_chain_hash: str
    capability_manifest: CapabilityManifest
    trusted_bands: tuple[TrustedScaleBand, ...]
    source_identity: SourceIdentity
    maturity: Maturity
    certification_status: CertificationStatus
    status: StatusTuple

    def __post_init__(self) -> None:
        if self.realization_schema_version != REALIZATION_SCHEMA_VERSION:
            raise ContractViolation("unsupported realization schema version")
        expected = stable_content_id(
            "surface_realization",
            {
                "surface_spec_id": self.surface_spec_id,
                "seed_id": self.seed_id,
                "latent_noise_id": self.latent_noise_id,
                "generator_id": self.generator_id,
                "generator_version": self.generator_version,
                "definition_hash": self.definition_hash,
            },
        )
        if self.surface_realization_id != expected:
            raise ContractViolation("surface_realization_id does not match its definition")
        if self.source_kind is SurfaceSourceKind.MEASURED:
            raise ContractViolation("M01 measured descriptors cannot create a realization")
        if self.source_kind is SurfaceSourceKind.SYNTHETIC:
            if self.seed_id is None or self.latent_noise_id is None:
                raise ContractViolation("synthetic realization requires seed and latent identities")
            if self.material_label != SYNTHETIC_MATERIAL_LABEL:
                raise ContractViolation("synthetic realization cannot claim a material identity")
        elif any(
            item is not None for item in (self.seed_id, self.latent_noise_id, self.rng_profile_id)
        ):
            raise ContractViolation("analytic realization must not invent RNG identity")


@dataclass(frozen=True, slots=True)
class QueryFootprint:
    footprint_id: str
    x_min_mm: float
    x_max_mm: float
    y_min_mm: float
    y_max_mm: float
    swept_geometry_hash: str
    guard_mm: float
    derivation_method: str

    def __post_init__(self) -> None:
        if self.x_max_mm <= self.x_min_mm or self.y_max_mm <= self.y_min_mm:
            raise ContractViolation("active footprint extent must be positive")
        if self.guard_mm < 0.0:
            raise ContractViolation("active footprint guard cannot be negative")
        expected = stable_content_id(
            "query_footprint",
            {
                "bounds": (self.x_min_mm, self.x_max_mm, self.y_min_mm, self.y_max_mm),
                "swept_geometry_hash": self.swept_geometry_hash,
                "guard_mm": self.guard_mm,
                "derivation_method": self.derivation_method,
            },
        )
        if self.footprint_id != expected:
            raise ContractViolation("query footprint ID mismatch")

    def inside(self, domain: Domain2D) -> bool:
        return domain.contains(self.x_min_mm, self.y_min_mm) and domain.contains(
            self.x_max_mm, self.y_max_mm
        )


@dataclass(frozen=True, slots=True)
class FieldQueryResult:
    field_id: str
    values: NDArray[Any] | None
    validity: NDArray[np.bool_]
    status: StatusTuple
    capability: QueryCapability
    unit: str
    frame_id: str
    reference_point: str
    quality_status: QualityStatus
    error_bound: float | None = None

    def __post_init__(self) -> None:
        validity = np.array(self.validity, dtype=np.bool_, copy=True)
        validity.setflags(write=False)
        object.__setattr__(self, "validity", validity)
        if self.values is None:
            if self.status.value_presence is not ValuePresence.NULL:
                raise ContractViolation("null query field must have NULL value presence")
        else:
            values = np.array(self.values, copy=True)
            if values.dtype.kind == "f" and not np.isfinite(values).all():
                raise ContractViolation("query values cannot use NaN/Inf as missing")
            values.setflags(write=False)
            object.__setattr__(self, "values", values)
            if self.status.value_presence is not ValuePresence.PRESENT:
                raise ContractViolation("present query field must have PRESENT value presence")


@dataclass(frozen=True, slots=True)
class QueryResponse:
    surface_realization_id: str
    surface_spec_id: str
    query_contract_version: str
    query_id: str
    operation: str
    requested_points_or_region_hash: str
    capability: QueryCapability
    reference_semantics: str
    method_id: str
    method_version: str
    status: StatusTuple
    domain_status: tuple[DomainStatus, ...]
    mapped_coordinates_mm: NDArray[np.float64] | None
    quality_status: tuple[QualityStatus, ...]
    quality_mask: NDArray[np.bool_]
    trusted_scale_status: QualityStatus
    requested_tolerance: float | None
    achieved_residual: float | None
    error_bound: float | None
    convergence_level: ConvergenceLevel
    units: str
    frame_id: str
    reference_point: str
    fields: tuple[FieldQueryResult, ...]
    feature_sets: tuple[tuple[ClosestFeature, ...], ...] = ()
    metadata: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        quality = np.array(self.quality_mask, dtype=np.bool_, copy=True)
        quality.setflags(write=False)
        object.__setattr__(self, "quality_mask", quality)
        if self.mapped_coordinates_mm is not None:
            mapped = np.array(self.mapped_coordinates_mm, dtype=np.float64, copy=True)
            if not np.isfinite(mapped).all():
                raise ContractViolation("mapped query coordinates must be finite")
            mapped.setflags(write=False)
            object.__setattr__(self, "mapped_coordinates_mm", mapped)
        if len(self.domain_status) != len(self.quality_status):
            raise ContractViolation("domain and quality statuses must preserve input cardinality")
        if quality.shape != (len(self.domain_status),):
            raise ContractViolation("quality mask must have one entry per input")
        if self.requested_tolerance is not None and self.requested_tolerance < 0.0:
            raise ContractViolation("requested tolerance cannot be negative")

    def field(self, field_id: str) -> FieldQueryResult:
        match = next((item for item in self.fields if item.field_id == field_id), None)
        if match is None:
            raise KeyError(field_id)
        return match


@dataclass(frozen=True, slots=True)
class ClosestFeature:
    feature_id: str
    feature_type: str
    point_mm: tuple[float, float, float]
    outward_normals: tuple[tuple[float, float, float], ...]
    signed_distance_mm: float
    domain_status: DomainStatus
    quality_status: QualityStatus
    residual_mm: float
    error_bound_mm: float


@dataclass(frozen=True, slots=True)
class SurfaceCreationResult:
    spec: SurfaceSpec | None
    realization: SurfaceRealization | None
    handle: Any | None
    status: StatusTuple

    def __post_init__(self) -> None:
        if self.status.capability_status is CapabilityStatus.UNAVAILABLE and (
            self.realization is not None or self.handle is not None
        ):
            raise ContractViolation("unavailable creation must not mint a realization or handle")


@dataclass(frozen=True, slots=True)
class MaterializationReceipt:
    receipt_id: str
    surface_realization_id: str
    footprint_id: str
    tile_coordinate: tuple[int, int]
    lod: int
    active_bands: tuple[int, ...]
    core_shape: tuple[int, int]
    halo_samples: int
    spacing_mm: float
    omitted_height_bound_mm: float
    omitted_slope_bound: float
    content_hash: str
    cache_status: str
    reason_code: str
    payload_bytes: int


@dataclass(frozen=True, slots=True)
class VisualizationSample:
    sample_id: str
    surface_realization_id: str
    window_mm: tuple[float, float, float, float]
    grid_shape: tuple[int, int]
    x_coordinates_mm: NDArray[np.float64]
    y_coordinates_mm: NDArray[np.float64]
    height_mm: NDArray[np.float64]
    validity: NDArray[np.bool_]
    visualization_q_max_rad_per_mm: float
    low_pass_method: str
    source_hash: str = field(init=False)

    def __post_init__(self) -> None:
        ny, nx = self.grid_shape
        x = np.array(self.x_coordinates_mm, dtype=np.float64, copy=True)
        y = np.array(self.y_coordinates_mm, dtype=np.float64, copy=True)
        height = np.array(self.height_mm, dtype=np.float64, copy=True)
        validity = np.array(self.validity, dtype=np.bool_, copy=True)
        if x.shape != (nx,) or y.shape != (ny,) or height.shape != (ny, nx):
            raise ContractViolation("visualization sample coordinate/height shape mismatch")
        if validity.shape != height.shape:
            raise ContractViolation("visualization validity must match height")
        if not np.isfinite(x).all() or not np.isfinite(y).all() or not np.isfinite(height).all():
            raise ContractViolation("visualization sample cannot encode missing as NaN/Inf")
        for array in (x, y, height, validity):
            array.setflags(write=False)
        object.__setattr__(self, "x_coordinates_mm", x)
        object.__setattr__(self, "y_coordinates_mm", y)
        object.__setattr__(self, "height_mm", height)
        object.__setattr__(self, "validity", validity)
        digest = semantic_hash(
            {
                "surface_realization_id": self.surface_realization_id,
                "window_mm": self.window_mm,
                "grid_shape": self.grid_shape,
                "x": x,
                "y": y,
                "height": height,
                "validity": validity,
                "visualization_q_max_rad_per_mm": self.visualization_q_max_rad_per_mm,
                "low_pass_method": self.low_pass_method,
            }
        )
        object.__setattr__(self, "source_hash", digest)
        expected = stable_content_id("visualization_sample", {"source_hash": digest})
        if self.sample_id != expected:
            raise ContractViolation("visualization sample ID mismatch")


def canonical_parameters(parameters: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    """Return a deterministic immutable parameter tree accepted by M00 hashing."""

    return tuple((name, _freeze_parameter(parameters[name])) for name in sorted(parameters))


def _freeze_parameter(value: Any) -> Any:
    if value is None or isinstance(value, str | int | bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractViolation("surface parameters cannot contain NaN/Inf")
        return value
    if isinstance(value, dict):
        return tuple((str(key), _freeze_parameter(value[key])) for key in sorted(value, key=str))
    if isinstance(value, tuple | list):
        return tuple(_freeze_parameter(item) for item in value)
    raise ContractViolation(f"unsupported surface parameter type: {type(value).__name__}")


def thaw_parameter(value: Any) -> Any:
    """Convert a canonical parameter tree to ordinary Python containers."""

    if isinstance(value, tuple):
        if all(
            isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str)
            for item in value
        ):
            return {item[0]: thaw_parameter(item[1]) for item in value}
        return [thaw_parameter(item) for item in value]
    return value


def make_latent_noise_identity(
    root_seed: int,
    surface_seed_index: int,
    *,
    latent_noise_namespace: str = "m01.surface.latent.default",
) -> LatentNoiseIdentity:
    seed_id = stable_content_id(
        "seed",
        {
            "rng_profile_id": RNG_PROFILE_ID,
            "stream_namespace": "m01.surface",
            "root_seed": root_seed,
            "surface_seed_index": surface_seed_index,
        },
    )
    latent_noise_id = stable_content_id(
        "latent_noise",
        {
            "seed_id": seed_id,
            "latent_noise_namespace": latent_noise_namespace,
            "normal_transform_id": NORMAL_TRANSFORM_ID,
        },
    )
    return LatentNoiseIdentity(
        latent_noise_id,
        seed_id,
        root_seed,
        surface_seed_index,
        "m01.surface",
        latent_noise_namespace,
        RNG_PROFILE_ID,
        NORMAL_TRANSFORM_ID,
    )


def make_visualization_sample(
    *,
    surface_realization_id: str,
    window_mm: tuple[float, float, float, float],
    x_coordinates_mm: NDArray[np.float64],
    y_coordinates_mm: NDArray[np.float64],
    height_mm: NDArray[np.float64],
    validity: NDArray[np.bool_],
    visualization_q_max_rad_per_mm: float,
    low_pass_method: str,
) -> VisualizationSample:
    x = np.asarray(x_coordinates_mm, dtype=np.float64)
    y = np.asarray(y_coordinates_mm, dtype=np.float64)
    height = np.asarray(height_mm, dtype=np.float64)
    mask = np.asarray(validity, dtype=np.bool_)
    digest = semantic_hash(
        {
            "surface_realization_id": surface_realization_id,
            "window_mm": window_mm,
            "grid_shape": height.shape,
            "x": x,
            "y": y,
            "height": height,
            "validity": mask,
            "visualization_q_max_rad_per_mm": visualization_q_max_rad_per_mm,
            "low_pass_method": low_pass_method,
        }
    )
    return VisualizationSample(
        stable_content_id("visualization_sample", {"source_hash": digest}),
        surface_realization_id,
        window_mm,
        (height.shape[0], height.shape[1]),
        x,
        y,
        height,
        mask,
        visualization_q_max_rad_per_mm,
        low_pass_method,
    )
