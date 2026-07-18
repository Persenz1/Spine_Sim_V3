"""Additive M01 result records and the frozen ``m01`` registry extension."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

from spine_sim.foundation.models import (
    CertificationStatus,
    Maturity,
    MaturityEvidence,
    MaturityStatus,
    RecordBase,
    SourceIdentity,
    StatusTuple,
)
from spine_sim.foundation.registry import (
    ArrayDescriptor,
    CompatibilityClass,
    DataClassification,
    DatasetClass,
    DatasetDescriptor,
    FieldMetadata,
    RelationDescriptor,
    ResultExtensionDescriptor,
)

M01_EXTENSION_SCHEMA_VERSION = "1.0.0"

SURFACE_REALIZATIONS_DATASET = "m01.surface_realizations"
SURFACE_PROVENANCE_DATASET = "m01.surface_provenance_steps"
SURFACE_QUALITY_BANDS_DATASET = "m01.surface_quality_bands"
SURFACE_STATISTICS_DATASET = "m01.surface_statistics"
MATERIALIZATION_RECEIPTS_DATASET = "m01.surface_materialization_receipts"
VALIDATION_RESULTS_DATASET = "m01.surface_validation_results"
SOURCE_AVAILABILITY_DATASET = "m01.source_availability"
VISUALIZATION_HEIGHT_FIELD = "m01.visualization_height"
VISUALIZATION_VALIDITY_FIELD = "m01.visualization_validity"
VISUALIZATION_COORDINATES_FIELD = "m01.visualization_coordinates"


@dataclass(frozen=True, slots=True)
class SurfaceRealizationRecord(RecordBase):
    __dataset_id__ = SURFACE_REALIZATIONS_DATASET

    run_id: str
    case_id: str
    surface_spec_id: str
    surface_realization_id: str
    realization_schema_version: str
    source_descriptor_id: str
    source_kind: str
    family: str
    material_label: str
    seed_id: str | None
    latent_noise_id: str | None
    rng_profile_id: str | None
    generator_id: str
    generator_version: str
    query_contract_version: str
    logical_domain_mm: tuple[float, float, float, float]
    boundary_mode: str
    source_frame_id: str
    surface_frame_id: str
    material_frame_id: str
    definition_hash: str
    provenance_chain_hash: str
    capability_manifest_hash: str
    quality_manifest_hash: str
    target_statistics_ref: str | None
    realized_statistics_ref: str | None
    statistic_scope: str
    requirement_origin: str
    value_provenance: tuple[str, ...]
    authority_refs: tuple[str, ...]
    status: StatusTuple
    source_identity: SourceIdentity
    maturity: Maturity
    certification_status: CertificationStatus


@dataclass(frozen=True, slots=True)
class SurfaceProvenanceStepRecord(RecordBase):
    __dataset_id__ = SURFACE_PROVENANCE_DATASET

    run_id: str
    case_id: str
    surface_realization_id: str
    step_index: int
    step_id: str
    algorithm_id: str
    algorithm_version: str
    parameters_hash: str
    input_hashes: tuple[str, ...]
    output_hash: str
    requirement_origin: str
    status: StatusTuple
    source_identity: SourceIdentity
    maturity: Maturity
    certification_status: CertificationStatus


@dataclass(frozen=True, slots=True)
class SurfaceQualityBandRecord(RecordBase):
    __dataset_id__ = SURFACE_QUALITY_BANDS_DATASET

    run_id: str
    case_id: str
    surface_realization_id: str
    band_id: str
    q_min_rad_per_mm: float
    q_max_rad_per_mm: float
    lambda_max_mm: float
    lambda_min_mm: float
    direction_rad: float | None
    uncertainty_bound_mm: float
    quality_status: str
    basis: str
    status: StatusTuple
    source_identity: SourceIdentity
    maturity: Maturity
    certification_status: CertificationStatus


@dataclass(frozen=True, slots=True)
class SurfaceStatisticRecord(RecordBase):
    __dataset_id__ = SURFACE_STATISTICS_DATASET

    run_id: str
    case_id: str
    surface_realization_id: str
    statistic_id: str
    statistic_scope: str
    metric: str
    target_value: float | None
    realized_value: float | None
    unit: str
    method_id: str
    method_version: str
    sample_count: int
    window: str
    detrend: str
    bin_manifest: str
    direction_rad: float | None
    error_or_uncertainty: float
    validity_coverage: float
    status: StatusTuple
    source_identity: SourceIdentity
    maturity: Maturity
    certification_status: CertificationStatus


@dataclass(frozen=True, slots=True)
class SurfaceMaterializationReceiptRecord(RecordBase):
    __dataset_id__ = MATERIALIZATION_RECEIPTS_DATASET

    run_id: str
    case_id: str
    surface_realization_id: str
    receipt_id: str
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
    status: StatusTuple
    source_identity: SourceIdentity
    maturity: Maturity
    certification_status: CertificationStatus


@dataclass(frozen=True, slots=True)
class SurfaceValidationResultRecord(RecordBase):
    __dataset_id__ = VALIDATION_RESULTS_DATASET

    run_id: str
    case_id: str
    surface_realization_id: str
    validation_id: str
    fixture_id: str
    metric: str
    tolerance: float
    observed_error: float
    passed: bool
    failure_class: str
    evidence_ref: str
    status: StatusTuple
    source_identity: SourceIdentity
    maturity: Maturity
    certification_status: CertificationStatus


@dataclass(frozen=True, slots=True)
class SourceAvailabilityRecord(RecordBase):
    __dataset_id__ = SOURCE_AVAILABILITY_DATASET

    run_id: str
    case_id: str
    request_id: str
    source_descriptor_id: str
    requested_source_kind: str
    requested_capability: str
    missing_fields: tuple[str, ...]
    reason_code: str
    explanation: str
    status: StatusTuple
    source_identity: SourceIdentity
    maturity: Maturity
    certification_status: CertificationStatus


_SHAPES: dict[str, tuple[int | None, ...]] = {
    "logical_domain_mm": (4,),
    "tile_coordinate": (2,),
    "core_shape": (2,),
}

_UNITS: dict[str, str] = {
    "logical_domain_mm": "mm",
    "q_min_rad_per_mm": "rad/mm",
    "q_max_rad_per_mm": "rad/mm",
    "lambda_max_mm": "mm",
    "lambda_min_mm": "mm",
    "direction_rad": "rad",
    "uncertainty_bound_mm": "mm",
    "spacing_mm": "mm",
    "omitted_height_bound_mm": "mm",
    "omitted_slope_bound": "1",
    "tolerance": "declared_by_metric",
    "observed_error": "declared_by_metric",
    "error_or_uncertainty": "declared_by_metric",
    "target_value": "declared_by_unit_field",
    "realized_value": "declared_by_unit_field",
    "validity_coverage": "1",
    "payload_bytes": "byte",
}


def _dtype(annotation: Any) -> str:
    text = str(annotation)
    if text in {"float", "float | None"}:
        return "float64"
    if text in {"int", "int | None"}:
        return "int64"
    if text in {"bool", "bool | None"}:
        return "bool"
    return "utf8"


def _fields(
    dataset_id: str,
    record_type: type[RecordBase],
    *,
    classification: DataClassification,
    source_identity: SourceIdentity,
) -> tuple[FieldMetadata, ...]:
    result: list[FieldMetadata] = []
    for item in dataclasses.fields(record_type):
        name = item.name
        shape = _SHAPES.get(name, ())
        unit = _UNITS.get(name, "1")
        frame = "M01_SURFACE_XY_HEIGHT_Z" if shape or unit in {"mm", "rad/mm"} else "NOT_APPLICABLE"
        reference = (
            "M01_LOGICAL_DOMAIN_ORIGIN" if shape or unit in {"mm", "rad/mm"} else "NOT_APPLICABLE"
        )
        result.append(
            FieldMetadata(
                field_id=f"{dataset_id}.{name}",
                namespace="m01",
                owner_module="M01",
                semantics=(
                    f"M01 {dataset_id.rsplit('.', 1)[-1]}: {name.replace('_', ' ')}; "
                    "meaning and availability are governed by M01_SURFACE_REQUIREMENTS 1.0.0"
                ),
                classification=classification,
                dtype=_dtype(item.type),
                shape=shape,
                dimensions=tuple(f"component_{index}" for index in range(len(shape))),
                raggedness="fixed" if shape else "scalar_or_canonical_json",
                unit=unit,
                frame=frame,
                reference_point=reference,
                sign_semantics="outward-positive where directed; otherwise not applicable",
                action_semantics="surface evidence only; no contact/load semantics",
                indices=("run_id", "case_id", "surface_realization_id")
                if "surface_realization_id"
                in {field.name for field in dataclasses.fields(record_type)}
                else ("run_id", "case_id", "source_descriptor_id"),
                sampling_cadence="per_realization_or_explicit_materialization",
                storage_frequency="compact_manifest_or_explicit_selected_sample",
                ownership="M01 immutable evidence or diagnostic",
                null_policy="explicit StatusTuple required"
                if "None" in str(item.type)
                else "not_null",
                source_identity=source_identity,
                authority_refs=(
                    "M01_SURFACE_REQUIREMENTS 1.0.0 §11",
                    "M00_FOUNDATION_REQUIREMENTS 1.0.0 §9",
                    "A_INTEGRATED_MODEL 1.0.0 §5.1",
                ),
                maturity=_M01_SCHEMA_MATURITY,
                introduced_version=M01_EXTENSION_SCHEMA_VERSION,
                deprecated_version=None,
                storage_dataset=dataset_id,
                encoding="parquet_zstd_lossless",
                precision="float64" if _dtype(item.type) == "float64" else "exact",
                required="None" not in str(item.type),
            )
        )
    return tuple(result)


def _dataset(
    dataset_id: str,
    record_type: type[RecordBase],
    *,
    classification: DataClassification,
    source_identity: SourceIdentity,
    default_visible: bool,
    primary_keys: tuple[str, ...],
) -> DatasetDescriptor:
    return DatasetDescriptor(
        dataset_id=dataset_id,
        namespace="m01",
        owner_module="M01",
        schema_version=M01_EXTENSION_SCHEMA_VERSION,
        dataset_class=DatasetClass.ACCEPTED,
        record_type=record_type,
        fields=_fields(
            dataset_id,
            record_type,
            classification=classification,
            source_identity=source_identity,
        ),
        primary_keys=primary_keys,
        partition_keys=("case_id",),
        default_visible=default_visible,
        source_identity=source_identity,
    )


def _array_field(
    field_id: str,
    *,
    dtype: str,
    shape: tuple[int | None, ...],
    unit: str,
    dimensions: tuple[str, ...],
    source_identity: SourceIdentity,
) -> FieldMetadata:
    return FieldMetadata(
        field_id=field_id,
        namespace="m01",
        owner_module="M01",
        semantics=(
            f"Explicit selected visualization {field_id.rsplit('.', 1)[-1]}; "
            "derived display sample and never solver geometry"
        ),
        classification=DataClassification.DERIVED,
        dtype=dtype,
        shape=shape,
        dimensions=dimensions,
        raggedness="fixed_per_selected_sample",
        unit=unit,
        frame="M01_SURFACE_XY_HEIGHT_Z",
        reference_point="M01_LOGICAL_DOMAIN_ORIGIN",
        sign_semantics="+Z height / validity / x-y coordinates as named",
        action_semantics="visualization only; no contact/load semantics",
        indices=("run_id", "case_id", "surface_realization_id", "visualization_sample_id"),
        sampling_cadence="explicit_selected_visualization_window",
        storage_frequency="only_when_explicitly_selected",
        ownership="M01 visualization derived array",
        null_policy="separate validity array; NaN missing forbidden",
        source_identity=source_identity,
        authority_refs=("M01_SURFACE_REQUIREMENTS 1.0.0 §11-12",),
        maturity=_M01_SCHEMA_MATURITY,
        introduced_version=M01_EXTENSION_SCHEMA_VERSION,
        deprecated_version=None,
        storage_dataset="m01.visualization_arrays",
        encoding="zarr_v3_lossless_content_addressed",
        precision="float64" if dtype == "float64" else "exact",
        required=True,
    )


def surface_result_extension() -> ResultExtensionDescriptor:
    """Return the frozen additive M01 registry descriptor."""

    tables = (
        _dataset(
            SURFACE_REALIZATIONS_DATASET,
            SurfaceRealizationRecord,
            classification=DataClassification.CANONICAL_RAW,
            source_identity=SourceIdentity.DEV_POLICY,
            default_visible=True,
            primary_keys=("surface_realization_id",),
        ),
        _dataset(
            SURFACE_PROVENANCE_DATASET,
            SurfaceProvenanceStepRecord,
            classification=DataClassification.CANONICAL_RAW,
            source_identity=SourceIdentity.DEV_POLICY,
            default_visible=True,
            primary_keys=("surface_realization_id", "step_index"),
        ),
        _dataset(
            SURFACE_QUALITY_BANDS_DATASET,
            SurfaceQualityBandRecord,
            classification=DataClassification.CANONICAL_RAW,
            source_identity=SourceIdentity.DEV_POLICY,
            default_visible=True,
            primary_keys=("surface_realization_id", "band_id"),
        ),
        _dataset(
            SURFACE_STATISTICS_DATASET,
            SurfaceStatisticRecord,
            classification=DataClassification.CANONICAL_RAW,
            source_identity=SourceIdentity.DEV_POLICY,
            default_visible=True,
            primary_keys=("surface_realization_id", "statistic_id"),
        ),
        _dataset(
            MATERIALIZATION_RECEIPTS_DATASET,
            SurfaceMaterializationReceiptRecord,
            classification=DataClassification.DIAGNOSTIC,
            source_identity=SourceIdentity.DEV_POLICY,
            default_visible=False,
            primary_keys=("receipt_id",),
        ),
        _dataset(
            VALIDATION_RESULTS_DATASET,
            SurfaceValidationResultRecord,
            classification=DataClassification.DIAGNOSTIC,
            source_identity=SourceIdentity.VALIDATION_ONLY,
            default_visible=False,
            primary_keys=("validation_id",),
        ),
        _dataset(
            SOURCE_AVAILABILITY_DATASET,
            SourceAvailabilityRecord,
            classification=DataClassification.DIAGNOSTIC,
            source_identity=SourceIdentity.PROPOSED_SUPPLEMENT,
            default_visible=False,
            primary_keys=("request_id",),
        ),
    )
    arrays = (
        ArrayDescriptor(
            _array_field(
                VISUALIZATION_HEIGHT_FIELD,
                dtype="float64",
                shape=(None, None),
                unit="mm",
                dimensions=("y", "x"),
                source_identity=SourceIdentity.DEV_POLICY,
            ),
            M01_EXTENSION_SCHEMA_VERSION,
            canonical_dtype="float64",
            nullable=True,
            default_chunk_shape=(512, 512),
        ),
        ArrayDescriptor(
            _array_field(
                VISUALIZATION_VALIDITY_FIELD,
                dtype="bool",
                shape=(None, None),
                unit="1",
                dimensions=("y", "x"),
                source_identity=SourceIdentity.DEV_POLICY,
            ),
            M01_EXTENSION_SCHEMA_VERSION,
            canonical_dtype="bool",
            nullable=False,
            default_chunk_shape=(512, 512),
        ),
        ArrayDescriptor(
            _array_field(
                VISUALIZATION_COORDINATES_FIELD,
                dtype="float64",
                shape=(2, None),
                unit="mm",
                dimensions=("axis", "coordinate"),
                source_identity=SourceIdentity.DEV_POLICY,
            ),
            M01_EXTENSION_SCHEMA_VERSION,
            canonical_dtype="float64",
            nullable=False,
            default_chunk_shape=(2, 1024),
        ),
    )
    relations = tuple(
        RelationDescriptor(
            f"m01.relation.realization_to_{dataset.dataset_id.rsplit('.', 1)[-1]}",
            SURFACE_REALIZATIONS_DATASET,
            dataset.dataset_id,
            ("surface_realization_id",),
            ("surface_realization_id",),
            "one-to-many",
        )
        for dataset in tables[1:-1]
    )
    return ResultExtensionDescriptor(
        namespace="m01",
        owner_module="M01",
        extension_schema_version=M01_EXTENSION_SCHEMA_VERSION,
        tables=tables,
        arrays=arrays,
        relations=relations,
        common_keys=("run_id", "case_id"),
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=_M01_SCHEMA_MATURITY,
        compatibility_class=CompatibilityClass.ADDITIVE_MINOR,
    )


_M01_SCHEMA_MATURITY = Maturity(
    # Kept local to avoid importing the evaluator/preview dependency graph.
    theory_defined=MaturityEvidence(
        MaturityStatus.SPEC_DEFINED,
        "M01 frozen result contract",
        "1.0.0",
    ),
    code_implemented=MaturityEvidence(
        MaturityStatus.PASSED_WITH_EVIDENCE,
        "M01 result extension",
        "1.0.0",
        ("tests/surface/test_result_extension.py",),
    ),
    numerically_verified=MaturityEvidence(
        MaturityStatus.PASSED_WITH_EVIDENCE,
        "M01 result round trip",
        "1.0.0",
        ("reports/m01/M01_VALIDATION_REPORT.md",),
    ),
    experimentally_validated=MaturityEvidence(
        MaturityStatus.BLOCKED_UNAVAILABLE,
        "no target-surface experiment",
    ),
)
