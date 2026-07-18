"""Declarative core/extension schemas, fields, arrays, and registered relations."""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, cast

import numpy as np
from packaging.version import Version

from .canonical import semantic_hash
from .errors import ContractViolation, SchemaRegistrationError
from .models import (
    AcceptedPointBase,
    CascadeRoundBase,
    CaseIndexBase,
    CertificationStatus,
    CommitReceiptBase,
    CommittedEventBase,
    DesignSummaryBase,
    EventDependencyBase,
    FailureDiagnosticSummaryBase,
    Maturity,
    PerNeedleAcceptedPoint,
    PerSupportAcceptedPoint,
    PerUnitAcceptedPoint,
    RecordBase,
    RejectedTrialBase,
    RunEnvelope,
    SourceIdentity,
    StatusTuple,
    SummaryBase,
)

RESULT_API_VERSION = "1.0.0"
BUNDLE_SCHEMA_VERSION = "1.1.0"
CORE_SCHEMA_VERSION = "1.1.0"


class DataClassification(StrEnum):
    CANONICAL_RAW = "canonical_raw"
    DERIVED = "derived"
    DIAGNOSTIC = "diagnostic"


class DatasetClass(StrEnum):
    INDEX = "index"
    ACCEPTED = "accepted"
    EVENT = "event"
    REJECTED = "rejected"
    SUMMARY = "summary"
    TRANSACTION = "transaction"
    ARRAY = "array"


class CompatibilityClass(StrEnum):
    PATCH = "PATCH"
    ADDITIVE_MINOR = "ADDITIVE_MINOR"
    BREAKING_MAJOR = "BREAKING_MAJOR"


@dataclass(frozen=True, slots=True)
class FieldMetadata:
    field_id: str
    namespace: str
    owner_module: str
    semantics: str
    classification: DataClassification
    dtype: str
    shape: tuple[int | None, ...]
    dimensions: tuple[str, ...]
    raggedness: str
    unit: str
    frame: str
    reference_point: str
    sign_semantics: str
    action_semantics: str
    indices: tuple[str, ...]
    sampling_cadence: str
    storage_frequency: str
    ownership: str
    null_policy: str
    source_identity: SourceIdentity
    authority_refs: tuple[str, ...]
    maturity: Maturity
    introduced_version: str
    deprecated_version: str | None
    storage_dataset: str
    encoding: str
    precision: str
    required: bool

    def __post_init__(self) -> None:
        if not self.field_id.startswith(f"{self.namespace}."):
            raise SchemaRegistrationError(
                f"field {self.field_id} is outside namespace {self.namespace}"
            )
        Version(self.introduced_version)
        is_directed = bool(self.shape) or any(
            word in self.semantics.lower() for word in ("vector", "wrench", "pose", "direction")
        )
        if is_directed and (
            self.unit in {"", "UNSPECIFIED"}
            or self.frame in {"", "UNSPECIFIED"}
            or self.reference_point in {"", "UNSPECIFIED"}
        ):
            raise SchemaRegistrationError(
                f"directed field {self.field_id} requires unit, frame, and reference point"
            )
        if self.precision == "float32":
            raise SchemaRegistrationError(f"canonical field {self.field_id} cannot use float32")

    def snapshot(self) -> dict[str, Any]:
        return cast(dict[str, Any], _enum_values(dataclasses.asdict(self)))


@dataclass(frozen=True, slots=True)
class DatasetDescriptor:
    dataset_id: str
    namespace: str
    owner_module: str
    schema_version: str
    dataset_class: DatasetClass
    record_type: type[RecordBase] | None
    fields: tuple[FieldMetadata, ...]
    primary_keys: tuple[str, ...]
    partition_keys: tuple[str, ...]
    default_visible: bool
    source_identity: SourceIdentity

    def __post_init__(self) -> None:
        Version(self.schema_version)
        if not self.dataset_id.startswith(f"{self.namespace}."):
            raise SchemaRegistrationError(
                f"dataset {self.dataset_id} is outside namespace {self.namespace}"
            )
        if len({item.field_id for item in self.fields}) != len(self.fields):
            raise SchemaRegistrationError(f"duplicate fields in {self.dataset_id}")
        local_names = {item.field_id.rsplit(".", 1)[-1] for item in self.fields}
        if not set(self.primary_keys).issubset(local_names):
            raise SchemaRegistrationError(f"unknown primary key in {self.dataset_id}")

    def snapshot(self) -> dict[str, Any]:
        record_name = None
        if self.record_type is not None:
            record_name = f"{self.record_type.__module__}.{self.record_type.__qualname__}"
        return {
            "dataset_id": self.dataset_id,
            "namespace": self.namespace,
            "owner_module": self.owner_module,
            "schema_version": self.schema_version,
            "dataset_class": self.dataset_class.value,
            "record_type": record_name,
            "fields": [item.snapshot() for item in self.fields],
            "primary_keys": list(self.primary_keys),
            "partition_keys": list(self.partition_keys),
            "default_visible": self.default_visible,
            "source_identity": self.source_identity.value,
        }


@dataclass(frozen=True, slots=True)
class ArrayDescriptor:
    field: FieldMetadata
    schema_version: str
    canonical_dtype: str = "float64"
    nullable: bool = True
    default_chunk_shape: tuple[int, ...] = (512, 512)
    lossless_only: bool = True

    def snapshot(self) -> dict[str, Any]:
        return {
            "field": self.field.snapshot(),
            "schema_version": self.schema_version,
            "canonical_dtype": self.canonical_dtype,
            "nullable": self.nullable,
            "default_chunk_shape": list(self.default_chunk_shape),
            "lossless_only": self.lossless_only,
        }


@dataclass(frozen=True, slots=True)
class RelationDescriptor:
    relation_id: str
    left_dataset: str
    right_dataset: str
    left_keys: tuple[str, ...]
    right_keys: tuple[str, ...]
    cardinality: str
    allow_many_to_many: bool = False

    def __post_init__(self) -> None:
        if len(self.left_keys) != len(self.right_keys) or not self.left_keys:
            raise SchemaRegistrationError(f"invalid relation keys for {self.relation_id}")
        if self.cardinality == "many-to-many" and not self.allow_many_to_many:
            raise SchemaRegistrationError(
                f"relation {self.relation_id} must explicitly allow many-to-many"
            )

    def snapshot(self) -> dict[str, Any]:
        return cast(dict[str, Any], _enum_values(dataclasses.asdict(self)))


@dataclass(frozen=True, slots=True)
class ResultExtensionDescriptor:
    namespace: str
    owner_module: str
    extension_schema_version: str
    tables: tuple[DatasetDescriptor, ...]
    arrays: tuple[ArrayDescriptor, ...]
    relations: tuple[RelationDescriptor, ...]
    common_keys: tuple[str, ...]
    source_identity: SourceIdentity
    maturity: Maturity
    compatibility_class: CompatibilityClass

    def __post_init__(self) -> None:
        Version(self.extension_schema_version)
        if self.namespace == "core" or not self.namespace:
            raise SchemaRegistrationError("extension namespace cannot be core or empty")
        for table in self.tables:
            if table.namespace != self.namespace or table.owner_module != self.owner_module:
                raise SchemaRegistrationError("extension table namespace/owner mismatch")
            local_names = {item.field_id.rsplit(".", 1)[-1] for item in table.fields}
            if not set(self.common_keys).issubset(local_names):
                raise SchemaRegistrationError(
                    f"extension table {table.dataset_id} is missing declared common keys"
                )
        for array in self.arrays:
            if (
                array.field.namespace != self.namespace
                or array.field.owner_module != self.owner_module
            ):
                raise SchemaRegistrationError("extension array namespace/owner mismatch")


class SchemaRegistry:
    """Mutable registration phase followed by an immutable run snapshot."""

    def __init__(self, *, include_core: bool = True) -> None:
        self._datasets: dict[str, DatasetDescriptor] = {}
        self._arrays: dict[str, ArrayDescriptor] = {}
        self._relations: dict[str, RelationDescriptor] = {}
        self._namespaces: dict[str, str] = {}
        self._extensions: list[ResultExtensionDescriptor] = []
        self._validation_plans: dict[
            type[RecordBase], tuple[tuple[FieldMetadata, str, str], ...]
        ] = {}
        self._frozen = False
        self._snapshot_hash: str | None = None
        if include_core:
            for dataset in core_dataset_descriptors():
                self._add_dataset(dataset)
            for relation in core_relation_descriptors():
                self._add_relation(relation)
            self._namespaces["core"] = "M00"

    @property
    def frozen(self) -> bool:
        return self._frozen

    @property
    def snapshot_hash(self) -> str:
        if not self._frozen or self._snapshot_hash is None:
            raise SchemaRegistrationError("registry is not frozen")
        return self._snapshot_hash

    @property
    def datasets(self) -> MappingProxyType[str, DatasetDescriptor]:
        return MappingProxyType(self._datasets)

    @property
    def arrays(self) -> MappingProxyType[str, ArrayDescriptor]:
        return MappingProxyType(self._arrays)

    @property
    def relations(self) -> MappingProxyType[str, RelationDescriptor]:
        return MappingProxyType(self._relations)

    def register_extension(self, descriptor: ResultExtensionDescriptor) -> None:
        if self._frozen:
            raise SchemaRegistrationError("cannot register after registry freeze")
        existing_owner = self._namespaces.get(descriptor.namespace)
        if existing_owner is not None and existing_owner != descriptor.owner_module:
            raise SchemaRegistrationError(
                f"namespace {descriptor.namespace} is owned by {existing_owner}"
            )
        if existing_owner is not None:
            raise SchemaRegistrationError(f"namespace {descriptor.namespace} is already registered")
        self._namespaces[descriptor.namespace] = descriptor.owner_module
        for dataset in descriptor.tables:
            self._add_dataset(dataset)
        for array in descriptor.arrays:
            self._add_array(array)
        for relation in descriptor.relations:
            self._add_relation(relation)
        self._extensions.append(descriptor)

    def freeze(self) -> str:
        if not self._frozen:
            snapshot = self.snapshot(include_hash=False)
            self._snapshot_hash = semantic_hash(snapshot)
            self._frozen = True
        assert self._snapshot_hash is not None
        return self._snapshot_hash

    def snapshot(self, *, include_hash: bool = True) -> dict[str, Any]:
        snapshot: dict[str, Any] = {
            "registry_schema_version": CORE_SCHEMA_VERSION,
            "result_api_version": RESULT_API_VERSION,
            "bundle_schema_version": BUNDLE_SCHEMA_VERSION,
            "datasets": [self._datasets[key].snapshot() for key in sorted(self._datasets)],
            "arrays": [self._arrays[key].snapshot() for key in sorted(self._arrays)],
            "relations": [self._relations[key].snapshot() for key in sorted(self._relations)],
            "namespaces": dict(sorted(self._namespaces.items())),
            "extensions": [
                {
                    "namespace": item.namespace,
                    "owner_module": item.owner_module,
                    "extension_schema_version": item.extension_schema_version,
                    "common_keys": list(item.common_keys),
                    "source_identity": item.source_identity.value,
                    "compatibility_class": item.compatibility_class.value,
                }
                for item in sorted(self._extensions, key=lambda value: value.namespace)
            ],
        }
        if include_hash and self._snapshot_hash is not None:
            snapshot["registry_hash"] = self._snapshot_hash
        return snapshot

    def validate_record(self, record: RecordBase) -> DatasetDescriptor:
        if not self._frozen:
            raise SchemaRegistrationError("registry must be frozen before writing")
        if not dataclasses.is_dataclass(record) or not isinstance(record, RecordBase):
            raise ContractViolation("writer accepts only typed RecordBase dataclasses")
        dataset_id = record.__dataset_id__
        descriptor = self._datasets.get(dataset_id)
        if descriptor is None:
            raise ContractViolation(f"record dataset is not registered: {dataset_id}")
        if descriptor.record_type is None or not isinstance(record, descriptor.record_type):
            raise ContractViolation(
                f"record type {type(record).__name__} does not match {descriptor.record_type}"
            )
        record_type = type(record)
        plan = self._validation_plans.get(record_type)
        if plan is None:
            fields = dataclasses.fields(record)
            field_names = {item.name for item in fields}
            annotations = {item.name: str(item.type) for item in fields}
            metadata_names = {item.field_id.rsplit(".", 1)[-1] for item in descriptor.fields}
            if field_names != metadata_names:
                raise ContractViolation(
                    "record fields do not match registered schema",
                    details={
                        "missing": sorted(metadata_names - field_names),
                        "extra": sorted(field_names - metadata_names),
                    },
                )
            plan = tuple(
                (metadata, name, annotations[name])
                for metadata in descriptor.fields
                for name in (metadata.field_id.rsplit(".", 1)[-1],)
            )
            self._validation_plans[record_type] = plan
        for metadata, name, annotation in plan:
            value = getattr(record, name)
            if metadata.required and value is None:
                raise ContractViolation(f"required field is null: {metadata.field_id}")
            if value is None:
                continue
            if metadata.dtype == "float64" and (
                isinstance(value, bool) or not isinstance(value, float)
            ):
                raise ContractViolation(
                    f"field requires runtime float64 value: {metadata.field_id}"
                )
            if metadata.dtype == "int64" and (
                isinstance(value, bool) or not isinstance(value, int)
            ):
                raise ContractViolation(f"field requires runtime int64 value: {metadata.field_id}")
            if metadata.dtype == "bool" and not isinstance(value, bool):
                raise ContractViolation(f"field requires runtime bool value: {metadata.field_id}")
            if annotation in {"str", "str | None"} and not isinstance(value, str):
                raise ContractViolation(f"field requires runtime string value: {metadata.field_id}")
            if "SourceIdentity" in annotation and not isinstance(value, SourceIdentity):
                raise ContractViolation(f"field requires SourceIdentity: {metadata.field_id}")
            if "Maturity" in annotation and not isinstance(value, Maturity):
                raise ContractViolation(f"field requires four-column Maturity: {metadata.field_id}")
            if "StatusTuple" in annotation and not isinstance(value, StatusTuple):
                raise ContractViolation(
                    f"field requires multidimensional StatusTuple: {metadata.field_id}"
                )
            if "CertificationStatus" in annotation and not isinstance(value, CertificationStatus):
                raise ContractViolation(f"field requires CertificationStatus: {metadata.field_id}")
            if metadata.shape:
                actual_shape = np.asarray(value).shape
                if len(actual_shape) != len(metadata.shape) or any(
                    expected is not None and actual != expected
                    for actual, expected in zip(actual_shape, metadata.shape, strict=True)
                ):
                    raise ContractViolation(
                        f"field shape does not match schema: {metadata.field_id}"
                    )
            if isinstance(value, float) and not math.isfinite(value):
                if descriptor.dataset_class is not DatasetClass.REJECTED:
                    raise ContractViolation(f"non-finite canonical value: {metadata.field_id}")
        return descriptor

    def _add_dataset(self, descriptor: DatasetDescriptor) -> None:
        if descriptor.dataset_id in self._datasets:
            raise SchemaRegistrationError(f"dataset conflict: {descriptor.dataset_id}")
        for field_meta in descriptor.fields:
            if any(
                field_meta.field_id == existing.field_id
                for dataset in self._datasets.values()
                for existing in dataset.fields
            ):
                raise SchemaRegistrationError(f"field conflict: {field_meta.field_id}")
        self._datasets[descriptor.dataset_id] = descriptor

    def _add_array(self, descriptor: ArrayDescriptor) -> None:
        field_id = descriptor.field.field_id
        if field_id in self._arrays:
            raise SchemaRegistrationError(f"array conflict: {field_id}")
        if descriptor.canonical_dtype == "float32" or not descriptor.lossless_only:
            raise SchemaRegistrationError("canonical arrays require float64/lossless storage")
        self._arrays[field_id] = descriptor

    def _add_relation(self, descriptor: RelationDescriptor) -> None:
        if descriptor.relation_id in self._relations:
            raise SchemaRegistrationError(f"relation conflict: {descriptor.relation_id}")
        if (
            descriptor.left_dataset not in self._datasets
            or descriptor.right_dataset not in self._datasets
        ):
            raise SchemaRegistrationError(
                f"relation references unknown dataset: {descriptor.relation_id}"
            )
        self._relations[descriptor.relation_id] = descriptor


def _enum_values(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {key: _enum_values(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_enum_values(item) for item in value]
    return value


_CORE_MATURITY = Maturity.validation_only_implemented()


def _dtype_for(annotation: Any) -> str:
    text = str(annotation)
    if text in {"float", "float | None"}:
        return "float64"
    if text in {"int", "int | None"}:
        return "int64"
    if text in {"bool", "bool | None"}:
        return "bool"
    return "utf8"


def _core_fields(
    dataset_id: str,
    record_type: type[RecordBase],
    *,
    classification: DataClassification,
    source_identity: SourceIdentity = SourceIdentity.ACCEPTED_AUTHORITY,
) -> tuple[FieldMetadata, ...]:
    fields: list[FieldMetadata] = []
    for item in dataclasses.fields(record_type):
        name = item.name
        dtype = _dtype_for(item.type)
        is_numeric = dtype in {"float64", "int64"}
        unit = "1"
        if name in {
            "path_coordinate",
            "accepted_increment",
            "requested_path_target",
            "localization_error",
        }:
            unit = "declared_by_companion_field"
        elif name in {"physical_time_value"}:
            unit = "s"
        semantics = f"M00 core {name.replace('_', ' ')}"
        fields.append(
            FieldMetadata(
                field_id=f"{dataset_id}.{name}",
                namespace="core",
                owner_module="M00",
                semantics=semantics,
                classification=classification,
                dtype=dtype,
                shape=(),
                dimensions=(),
                raggedness="scalar_or_canonical_json",
                unit=unit,
                frame="NOT_APPLICABLE",
                reference_point="NOT_APPLICABLE",
                sign_semantics="declared_by_field_or_not_applicable",
                action_semantics="declared_by_field_or_not_applicable",
                indices=("run_id", "case_id")
                if "case_id" in {f.name for f in dataclasses.fields(record_type)}
                else ("run_id",),
                sampling_cadence="per_record",
                storage_frequency="every_committed_record"
                if classification is DataClassification.CANONICAL_RAW
                else "versioned",
                ownership=dataset_id.split(".")[1],
                null_policy="explicit_status_required" if "None" in str(item.type) else "not_null",
                source_identity=source_identity,
                authority_refs=(
                    "M00_FOUNDATION_REQUIREMENTS 1.0.0",
                    "SYSTEM_INTEGRATED_MODEL 1.0.0 sections 25-30,40-45",
                ),
                maturity=_CORE_MATURITY,
                introduced_version="1.0.0" if name != "source_identity" else "1.1.0",
                deprecated_version=None,
                storage_dataset=dataset_id,
                encoding="parquet_zstd_lossless",
                precision="float64" if is_numeric and dtype == "float64" else "exact",
                required="None" not in str(item.type) and item.default is dataclasses.MISSING,
            )
        )
    return tuple(fields)


def _dataset(
    dataset_id: str,
    record_type: type[RecordBase],
    dataset_class: DatasetClass,
    primary_keys: tuple[str, ...],
    *,
    default_visible: bool,
    source_identity: SourceIdentity = SourceIdentity.ACCEPTED_AUTHORITY,
) -> DatasetDescriptor:
    classification = {
        DatasetClass.ACCEPTED: DataClassification.CANONICAL_RAW,
        DatasetClass.EVENT: DataClassification.CANONICAL_RAW,
        DatasetClass.REJECTED: DataClassification.DIAGNOSTIC,
        DatasetClass.SUMMARY: DataClassification.DERIVED,
        DatasetClass.TRANSACTION: DataClassification.CANONICAL_RAW,
        DatasetClass.INDEX: DataClassification.CANONICAL_RAW,
        DatasetClass.ARRAY: DataClassification.CANONICAL_RAW,
    }[dataset_class]
    return DatasetDescriptor(
        dataset_id=dataset_id,
        namespace="core",
        owner_module="M00",
        schema_version=CORE_SCHEMA_VERSION,
        dataset_class=dataset_class,
        record_type=record_type,
        fields=_core_fields(
            dataset_id, record_type, classification=classification, source_identity=source_identity
        ),
        primary_keys=primary_keys,
        partition_keys=("case_id",)
        if "case_id" in {item.name for item in dataclasses.fields(record_type)}
        else ("run_id",),
        default_visible=default_visible,
        source_identity=source_identity,
    )


def core_dataset_descriptors() -> tuple[DatasetDescriptor, ...]:
    return (
        _dataset(
            "core.indices.runs", RunEnvelope, DatasetClass.INDEX, ("run_id",), default_visible=True
        ),
        _dataset(
            "core.indices.cases",
            CaseIndexBase,
            DatasetClass.INDEX,
            ("case_id",),
            default_visible=True,
        ),
        _dataset(
            "core.accepted_points.common",
            AcceptedPointBase,
            DatasetClass.ACCEPTED,
            ("point_id",),
            default_visible=True,
        ),
        _dataset(
            "core.accepted_points.per_unit",
            PerUnitAcceptedPoint,
            DatasetClass.ACCEPTED,
            ("point_id", "entity_id"),
            default_visible=True,
        ),
        _dataset(
            "core.accepted_points.per_needle",
            PerNeedleAcceptedPoint,
            DatasetClass.ACCEPTED,
            ("point_id", "entity_id"),
            default_visible=True,
        ),
        _dataset(
            "core.accepted_points.per_support",
            PerSupportAcceptedPoint,
            DatasetClass.ACCEPTED,
            ("point_id", "entity_id"),
            default_visible=True,
        ),
        _dataset(
            "core.committed_events.events",
            CommittedEventBase,
            DatasetClass.EVENT,
            ("event_id",),
            default_visible=True,
        ),
        _dataset(
            "core.committed_events.dependencies",
            EventDependencyBase,
            DatasetClass.EVENT,
            ("event_id", "depends_on_event_id"),
            default_visible=True,
        ),
        _dataset(
            "core.committed_events.cascade_rounds",
            CascadeRoundBase,
            DatasetClass.EVENT,
            ("cascade_id", "round_index"),
            default_visible=True,
        ),
        _dataset(
            "core.rejected_trials.diagnostics",
            RejectedTrialBase,
            DatasetClass.REJECTED,
            ("trial_id",),
            default_visible=False,
        ),
        _dataset(
            "core.summaries.case",
            SummaryBase,
            DatasetClass.SUMMARY,
            ("summary_id",),
            default_visible=True,
        ),
        _dataset(
            "core.summaries.design",
            DesignSummaryBase,
            DatasetClass.SUMMARY,
            ("summary_id",),
            default_visible=True,
        ),
        _dataset(
            "core.summaries.failure_diagnostics",
            FailureDiagnosticSummaryBase,
            DatasetClass.SUMMARY,
            ("summary_id",),
            default_visible=False,
        ),
        _dataset(
            "core.transactions.receipts",
            CommitReceiptBase,
            DatasetClass.TRANSACTION,
            ("receipt_id",),
            default_visible=True,
        ),
    )


def core_relation_descriptors() -> tuple[RelationDescriptor, ...]:
    return (
        RelationDescriptor(
            "core.relation.point_to_receipt",
            "core.accepted_points.common",
            "core.transactions.receipts",
            ("commit_receipt_id",),
            ("receipt_id",),
            "many-to-one",
        ),
        RelationDescriptor(
            "core.relation.event_to_receipt",
            "core.committed_events.events",
            "core.transactions.receipts",
            ("commit_receipt_id",),
            ("receipt_id",),
            "many-to-one",
        ),
        RelationDescriptor(
            "core.relation.point_to_unit",
            "core.accepted_points.common",
            "core.accepted_points.per_unit",
            ("point_id",),
            ("point_id",),
            "one-to-many",
        ),
    )
