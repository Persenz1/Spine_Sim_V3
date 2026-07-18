"""Storage-independent, read-only ResultReader for downstream consumers."""

from __future__ import annotations

import fnmatch
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import zarr
from packaging.version import Version

from .canonical import canonical_array_manifest, semantic_hash
from .errors import CompatibilityError, QueryError
from .integrity import VerifyMode, committed_markers, verify_bundle
from .models import DEFAULT_READER_IDENTITIES
from .plot_requirements import (
    PlotDataGapRequest,
    PlotDataRequirements,
    PlotRequirementDeficiency,
    PlotRequirementsReport,
)
from .registry import BUNDLE_SCHEMA_VERSION, RESULT_API_VERSION, DatasetClass
from .storage import read_json


@dataclass(frozen=True, slots=True)
class DatasetCatalogEntry:
    dataset_id: str
    dataset_class: str
    schema_version: str
    owner_module: str
    default_visible: bool
    source_identity: str
    primary_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DatasetCatalog:
    entries: tuple[DatasetCatalogEntry, ...]
    bundle_schema_version: str
    registry_hash: str


@dataclass(frozen=True, slots=True)
class FieldMetadataView:
    field_id: str
    dataset_id: str
    metadata: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class RelationCatalog:
    relations: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True, slots=True)
class FilterSpec:
    field: str
    operator: str
    value: Any


@dataclass(frozen=True, slots=True)
class JoinSpec:
    relation_id: str


@dataclass(frozen=True, slots=True)
class OrderSpec:
    field: str
    direction: str = "ascending"


@dataclass(slots=True)
class QueryManifest:
    bundle_semantic_hash: str
    bundle_schema_version: str
    registry_hash: str
    dataset: str
    fields: tuple[str, ...]
    filters: tuple[FilterSpec, ...]
    joins: tuple[str, ...]
    ordering: tuple[OrderSpec, ...]
    unit_frame_reference_view: tuple[str, ...]
    source_identities: tuple[str, ...]
    result_hash: str = "DEFERRED_UNTIL_EXHAUSTED"
    rows_yielded: int = 0


class QueryResult:
    """One-shot read-only batch stream with a finalized result hash after exhaustion."""

    def __init__(self, batches: Iterable[pa.RecordBatch], manifest: QueryManifest) -> None:
        self._batches = iter(batches)
        self.manifest = manifest
        self._consumed = False

    def __iter__(self) -> Iterator[pa.RecordBatch]:
        if self._consumed:
            raise QueryError("QueryResult is a one-shot iterator")
        self._consumed = True
        batch_hashes: list[str] = []
        row_count = 0
        for batch in self._batches:
            immutable = pa.RecordBatch.from_arrays(batch.columns, schema=batch.schema)
            batch_hashes.append(_record_batch_semantic_hash(immutable))
            row_count += immutable.num_rows
            yield immutable
        self.manifest.rows_yielded = row_count
        self.manifest.result_hash = semantic_hash(batch_hashes)

    def read_all(self) -> pa.Table:
        return pa.Table.from_batches(list(self))


class ChunkedArrayView:
    """Read-only Zarr v3 view; consumers receive slices, never a mutable array handle."""

    def __init__(self, path: Path, metadata: Mapping[str, Any], slice_spec: Any = None) -> None:
        self._path = path
        self.metadata = dict(metadata)
        self._slice_spec = slice_spec
        self._group = zarr.open_group(path, mode="r")

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(cast(Any, self._group["values"]).shape)

    @property
    def chunks(self) -> tuple[int, ...]:
        return tuple(cast(Any, self._group["values"]).chunks)

    def read(self, slice_spec: Any = None) -> Any:
        selection = slice_spec if slice_spec is not None else self._slice_spec
        if selection is None:
            selection = (...,)
        values = self._group["values"][selection]
        validity = self._group["validity"][selection] if "validity" in self._group else None
        status = self._group["status"][selection] if "status" in self._group else None
        return {"values": values, "validity": validity, "status": status}


@dataclass(frozen=True, slots=True)
class LineageGraph:
    states: tuple[str, ...]
    events: tuple[str, ...]
    receipts: tuple[str, ...]
    edges: tuple[tuple[str, str, str], ...]


class ResultReader:
    """The only supported consumer boundary for canonical bundles."""

    def __init__(
        self,
        root: Path,
        manifest: dict[str, Any],
        registry: dict[str, Any],
        compatibility_status: str,
    ) -> None:
        self._root = root
        self._manifest = manifest
        self._registry = registry
        self.compatibility_status = compatibility_status
        self._datasets = {item["dataset_id"]: item for item in registry["datasets"]}
        self._fields = {
            field_item["field_id"]: {**field_item, "dataset_id": dataset_item["dataset_id"]}
            for dataset_item in registry["datasets"]
            for field_item in dataset_item["fields"]
        }
        self._arrays = {item["field"]["field_id"]: item for item in registry.get("arrays", [])}
        self._relations = {item["relation_id"]: item for item in registry["relations"]}
        self._markers = committed_markers(root)

    @classmethod
    def open(
        cls, bundle_uri: str | Path, verify_mode: VerifyMode = VerifyMode.MANIFEST
    ) -> ResultReader:
        root = Path(bundle_uri)
        verify_bundle(root, verify_mode)
        manifest = read_json(root / "bundle_manifest.json")
        registry = read_json(root / "schemas" / "registry.json")
        bundle_api = Version(manifest["result_api_version"])
        reader_api = Version(RESULT_API_VERSION)
        bundle_schema = Version(manifest["bundle_schema_version"])
        reader_schema = Version(BUNDLE_SCHEMA_VERSION)
        if bundle_api.major != reader_api.major or bundle_schema.major != reader_schema.major:
            raise CompatibilityError(
                "breaking schema unsupported",
                details={
                    "code": "BREAKING_SCHEMA_UNSUPPORTED",
                    "bundle_schema_version": str(bundle_schema),
                    "reader_schema_version": str(reader_schema),
                    "minimal_manifest": manifest,
                },
            )
        compatibility_status = "FULL_SCHEMA_SUPPORT"
        if bundle_schema.minor > reader_schema.minor:
            compatibility_status = "PARTIAL_SCHEMA_SUPPORT"
        elif bundle_schema.minor < reader_schema.minor:
            compatibility_status = "READ_TIME_ADAPTER_ACTIVE"
        return cls(root, manifest, registry, compatibility_status)

    def bundle_info(self) -> Mapping[str, Any]:
        return dict(self._manifest)

    def list_datasets(
        self, *, include_non_default: bool = False, include_diagnostics: bool = False
    ) -> DatasetCatalog:
        entries: list[DatasetCatalogEntry] = []
        allowed = {item.value for item in DEFAULT_READER_IDENTITIES}
        for item in self._datasets.values():
            is_rejected = item["dataset_class"] == DatasetClass.REJECTED.value
            if is_rejected:
                if not include_diagnostics:
                    continue
                if not include_non_default and item["source_identity"] not in allowed:
                    continue
            elif not include_non_default and (
                not item["default_visible"] or item["source_identity"] not in allowed
            ):
                continue
            entries.append(
                DatasetCatalogEntry(
                    dataset_id=item["dataset_id"],
                    dataset_class=item["dataset_class"],
                    schema_version=item["schema_version"],
                    owner_module=item["owner_module"],
                    default_visible=item["default_visible"],
                    source_identity=item["source_identity"],
                    primary_keys=tuple(item["primary_keys"]),
                )
            )
        return DatasetCatalog(
            tuple(sorted(entries, key=lambda value: value.dataset_id)),
            self._manifest["bundle_schema_version"],
            self._manifest["registry_hash"],
        )

    def list_fields(
        self,
        selector: str = "*",
        *,
        include_non_default: bool = False,
        include_diagnostics: bool = False,
    ) -> tuple[FieldMetadataView, ...]:
        allowed = {item.value for item in DEFAULT_READER_IDENTITIES}
        fields = []
        for field_id, metadata in self._fields.items():
            if not fnmatch.fnmatch(field_id, selector):
                continue
            descriptor = self._datasets[metadata["dataset_id"]]
            is_rejected = descriptor["dataset_class"] == DatasetClass.REJECTED.value
            if is_rejected and not include_diagnostics:
                continue
            if not include_non_default and metadata["source_identity"] not in allowed:
                continue
            if not is_rejected and not include_non_default and not descriptor["default_visible"]:
                continue
            fields.append(FieldMetadataView(field_id, metadata["dataset_id"], dict(metadata)))
        return tuple(sorted(fields, key=lambda value: value.field_id))

    def describe_fields(self, field_ids: Sequence[str]) -> tuple[FieldMetadataView, ...]:
        missing = [
            field_id
            for field_id in field_ids
            if field_id not in self._fields and field_id not in self._arrays
        ]
        if missing:
            raise QueryError("unknown field IDs", details={"field_ids": missing})
        result = []
        for field_id in field_ids:
            if field_id in self._fields:
                metadata = self._fields[field_id]
                result.append(FieldMetadataView(field_id, metadata["dataset_id"], dict(metadata)))
            else:
                metadata = self._arrays[field_id]["field"]
                result.append(FieldMetadataView(field_id, "arrays", dict(metadata)))
        return tuple(result)

    def list_relations(self) -> RelationCatalog:
        return RelationCatalog(tuple(dict(self._relations[key]) for key in sorted(self._relations)))

    def query(
        self,
        dataset: str,
        fields: Sequence[str] | None = None,
        filters: Sequence[FilterSpec] = (),
        joins: Sequence[JoinSpec] = (),
        ordering: Sequence[OrderSpec] = (),
        batch_size: int = 65536,
        *,
        include_non_default: bool = False,
        include_diagnostics: bool = False,
    ) -> QueryResult:
        descriptor = self._datasets.get(dataset)
        if descriptor is None:
            raise QueryError(f"unknown dataset: {dataset}")
        if descriptor["dataset_class"] == DatasetClass.REJECTED.value and not include_diagnostics:
            raise QueryError("rejected diagnostics require explicit include_diagnostics opt-in")
        if (
            not descriptor["default_visible"]
            and not include_non_default
            and descriptor["dataset_class"] != DatasetClass.REJECTED.value
        ):
            raise QueryError("non-default dataset requires explicit opt-in")
        local_names = {item["field_id"].rsplit(".", 1)[-1] for item in descriptor["fields"]}
        selected = tuple(fields or sorted(local_names))
        unknown = set(selected) - local_names
        if unknown:
            raise QueryError(
                "projection contains unknown fields", details={"fields": sorted(unknown)}
            )
        for item in filters:
            if item.field not in local_names:
                raise QueryError(f"filter field is not in dataset: {item.field}")
        source_filters = list(filters)
        allowed_identities = tuple(sorted(item.value for item in DEFAULT_READER_IDENTITIES))
        if "source_identity" in local_names and not include_non_default:
            source_filters.append(FilterSpec("source_identity", "in", allowed_identities))
        relation_ids = tuple(item.relation_id for item in joins)
        for relation_id in relation_ids:
            relation = self._relations.get(relation_id)
            if relation is None or relation["left_dataset"] != dataset:
                raise QueryError(f"join is not registered from {dataset}: {relation_id}")
        files = self._files_for_dataset(dataset, source_filters)
        if joins:
            batches = self._joined_batches(
                dataset,
                files,
                selected,
                source_filters,
                joins,
                ordering,
                batch_size,
                include_non_default,
                include_diagnostics,
            )
        else:
            batches = self._scan_batches(files, selected, source_filters, ordering, batch_size)
        manifest = QueryManifest(
            bundle_semantic_hash=self._manifest["bundle_semantic_hash"],
            bundle_schema_version=self._manifest["bundle_schema_version"],
            registry_hash=self._manifest["registry_hash"],
            dataset=dataset,
            fields=selected,
            filters=tuple(source_filters),
            joins=relation_ids,
            ordering=tuple(ordering),
            unit_frame_reference_view=tuple(
                f"{name}:{self._field_meta_for_local(dataset, name).get('unit')}/{self._field_meta_for_local(dataset, name).get('frame')}/{self._field_meta_for_local(dataset, name).get('reference_point')}"
                for name in selected
            ),
            source_identities=("ALL_EXPLICITLY_OPTED_IN",)
            if include_non_default
            else allowed_identities,
        )
        return QueryResult(batches, manifest)

    def series(
        self,
        x_field: str,
        y_fields: Sequence[str],
        *,
        dataset: str = "core.accepted_points.common",
        group_by: Sequence[str] = (),
        filters: Sequence[FilterSpec] = (),
        entity_scope: Sequence[str] = (),
        batch_size: int = 65536,
        include_non_default: bool = False,
    ) -> QueryResult:
        del entity_scope
        fields = (*group_by, x_field, *y_fields)
        ordering = tuple(OrderSpec(item) for item in (*group_by, x_field))
        return self.query(
            dataset,
            fields,
            filters,
            ordering=ordering,
            batch_size=batch_size,
            include_non_default=include_non_default,
        )

    def events(
        self,
        filters: Sequence[FilterSpec] = (),
        event_window: tuple[float, float] | None = None,
        include_sides: frozenset[str] = frozenset({"pre", "event", "post"}),
        *,
        include_non_default: bool = False,
    ) -> QueryResult:
        event_filters = list(filters)
        if event_window is not None:
            event_filters.extend(
                (
                    FilterSpec("path_coordinate", ">=", event_window[0]),
                    FilterSpec("path_coordinate", "<=", event_window[1]),
                )
            )
        all_fields = {
            item["field_id"].rsplit(".", 1)[-1]
            for item in self._datasets["core.committed_events.events"]["fields"]
        }
        excluded = {
            f"{side}_payload_refs" for side in {"pre", "event", "post"} - set(include_sides)
        }
        return self.query(
            "core.committed_events.events",
            sorted(all_fields - excluded),
            event_filters,
            ordering=(OrderSpec("path_coordinate"), OrderSpec("event_id")),
            include_non_default=include_non_default,
        )

    def open_array(
        self,
        field_id: str,
        case_selector: str,
        entity_selector: str | None = None,
        slice_spec: Any = None,
        *,
        include_non_default: bool = False,
    ) -> ChunkedArrayView:
        del entity_selector
        if field_id not in self._arrays:
            raise QueryError(f"unknown array field: {field_id}")
        for _, marker in self._markers:
            if marker["case_id"] != case_selector:
                continue
            entry = marker.get("arrays", {}).get(field_id)
            if entry is None:
                continue
            if (
                entry["source_identity"] not in {item.value for item in DEFAULT_READER_IDENTITIES}
                and not include_non_default
            ):
                raise QueryError("non-default array requires explicit opt-in")
            return ChunkedArrayView(self._root / entry["path"], entry, slice_spec)
        raise QueryError(f"array {field_id} not found for case {case_selector}")

    def resolve_lineage(
        self,
        *,
        state_ids: Sequence[str] = (),
        event_ids: Sequence[str] = (),
        receipt_ids: Sequence[str] = (),
    ) -> LineageGraph:
        wanted_states = set(state_ids)
        wanted_events = set(event_ids)
        wanted_receipts = set(receipt_ids)
        edges: set[tuple[str, str, str]] = set()
        for _, marker in self._markers:
            receipt = marker["receipt_id"]
            parent = marker["parent_state_id"]
            committed = marker["committed_state_id"]
            if (
                (not wanted_states and not wanted_events and not wanted_receipts)
                or receipt in wanted_receipts
                or parent in wanted_states
                or committed in wanted_states
            ):
                wanted_receipts.add(receipt)
                wanted_states.update((parent, committed))
                edges.add((parent, committed, receipt))
                event_entry = marker.get("datasets", {}).get("core.committed_events.events")
                if event_entry is not None:
                    for row in pq.read_table(
                        self._root / event_entry["path"], columns=["event_id"]
                    ).to_pylist():
                        wanted_events.add(row["event_id"])
                        edges.add((row["event_id"], receipt, "committed_by"))
        return LineageGraph(
            tuple(sorted(wanted_states)),
            tuple(sorted(wanted_events)),
            tuple(sorted(wanted_receipts)),
            tuple(sorted(edges)),
        )

    def check_plot_requirements(self, requirements: PlotDataRequirements) -> PlotRequirementsReport:
        deficiencies: list[PlotRequirementDeficiency] = []
        for required in requirements.fields:
            metadata = self._fields.get(required.field_id) or self._arrays.get(
                required.field_id, {}
            ).get("field")
            expected = {
                "unit": required.unit,
                "frame": required.frame,
                "reference_point": required.reference_point,
                "sampling_cadence": required.minimum_sampling_cadence,
                "allowed_source_identities": required.allowed_source_identities,
            }
            if metadata is None:
                deficiencies.append(
                    PlotRequirementDeficiency(
                        required.field_id,
                        "FIELD_NOT_PRESENT",
                        "field is not registered in this bundle",
                        expected,
                        None,
                    )
                )
                continue
            for key in ("unit", "frame", "reference_point"):
                if metadata[key] != expected[key]:
                    deficiencies.append(
                        PlotRequirementDeficiency(
                            required.field_id,
                            f"{key.upper()}_INCOMPATIBLE",
                            f"registered {key} is incompatible",
                            expected,
                            dict(metadata),
                        )
                    )
                    break
            else:
                if metadata["source_identity"] not in required.allowed_source_identities:
                    deficiencies.append(
                        PlotRequirementDeficiency(
                            required.field_id,
                            "SOURCE_IDENTITY_NOT_ALLOWED",
                            "recipe does not opt into the field source identity",
                            expected,
                            dict(metadata),
                        )
                    )
                elif metadata["sampling_cadence"] != required.minimum_sampling_cadence:
                    deficiencies.append(
                        PlotRequirementDeficiency(
                            required.field_id,
                            "SAMPLING_CADENCE_INSUFFICIENT",
                            "sampling cadence does not exactly satisfy the frozen requirement",
                            expected,
                            dict(metadata),
                        )
                    )
        return PlotRequirementsReport(requirements.recipe_id, not deficiencies, tuple(deficiencies))

    def build_plot_data_gap_request(
        self, report: PlotRequirementsReport, recipe_identity: str
    ) -> PlotDataGapRequest:
        if report.satisfied:
            raise QueryError("cannot build a gap request from a satisfied report")
        return PlotDataGapRequest.from_report(report, recipe_identity=recipe_identity)

    def _field_meta_for_local(self, dataset: str, local_name: str) -> Mapping[str, Any]:
        for item in self._datasets[dataset]["fields"]:
            if item["field_id"].rsplit(".", 1)[-1] == local_name:
                return cast(Mapping[str, Any], item)
        raise QueryError(f"field {local_name} not in {dataset}")

    def _files_for_dataset(self, dataset: str, filters: Sequence[FilterSpec]) -> list[Path]:
        selected_case = next(
            (item.value for item in filters if item.field == "case_id" and item.operator == "=="),
            None,
        )
        files: list[Path] = []
        for _, marker in self._markers:
            if selected_case is not None and marker["case_id"] != selected_case:
                continue
            entry = marker.get("datasets", {}).get(dataset)
            if entry is not None:
                files.append(self._root / entry["path"])
        if files:
            return files
        auxiliary = self._manifest.get("auxiliary_datasets", {}).get(dataset, [])
        return [self._root / entry["path"] for entry in auxiliary]

    def _scan_batches(
        self,
        files: Sequence[Path],
        fields: Sequence[str],
        filters: Sequence[FilterSpec],
        ordering: Sequence[OrderSpec],
        batch_size: int,
    ) -> Iterable[pa.RecordBatch]:
        if not files:
            schema = pa.schema([(name, pa.null()) for name in fields])
            return iter(
                (
                    pa.RecordBatch.from_arrays(
                        [pa.array([], type=pa.null()) for _ in fields], schema=schema
                    ),
                )
            )
        expression = _filter_expression(filters)
        scanner = ds.dataset([str(path) for path in files], format="parquet").scanner(
            columns=list(fields),
            filter=expression,
            batch_size=batch_size,
            batch_readahead=64,
            fragment_readahead=64,
            use_threads=True,
        )
        if ordering:
            table = scanner.to_table().sort_by([(item.field, item.direction) for item in ordering])
            return cast(list[pa.RecordBatch], table.to_batches(max_chunksize=batch_size))
        return cast(Iterable[pa.RecordBatch], scanner.to_batches())

    def _joined_batches(
        self,
        dataset: str,
        files: Sequence[Path],
        fields: Sequence[str],
        filters: Sequence[FilterSpec],
        joins: Sequence[JoinSpec],
        ordering: Sequence[OrderSpec],
        batch_size: int,
        include_non_default: bool,
        include_diagnostics: bool,
    ) -> Iterable[pa.RecordBatch]:
        left_fields = sorted(
            {item.field for item in filters}
            | set(fields)
            | {key for join in joins for key in self._relations[join.relation_id]["left_keys"]}
        )
        left = pa.Table.from_batches(
            list(self._scan_batches(files, left_fields, filters, (), batch_size))
        )
        for join in joins:
            relation = self._relations[join.relation_id]
            right_dataset = relation["right_dataset"]
            right_descriptor = self._datasets[right_dataset]
            right_names = [
                item["field_id"].rsplit(".", 1)[-1] for item in right_descriptor["fields"]
            ]
            right_result = self.query(
                right_dataset,
                right_names,
                include_non_default=include_non_default,
                include_diagnostics=include_diagnostics,
            )
            right = right_result.read_all()
            left = left.join(
                right,
                keys=relation["left_keys"],
                right_keys=relation["right_keys"],
                join_type="left outer",
                right_suffix=f"__{right_dataset.replace('.', '_')}",
            )
        if ordering:
            left = left.sort_by([(item.field, item.direction) for item in ordering])
        return cast(list[pa.RecordBatch], left.to_batches(max_chunksize=batch_size))


def _filter_expression(filters: Sequence[FilterSpec]) -> ds.Expression | None:
    expression: ds.Expression | None = None
    for item in filters:
        field_expr = ds.field(item.field)
        if item.operator == "==":
            built = field_expr == item.value
        elif item.operator == "!=":
            built = field_expr != item.value
        elif item.operator == ">":
            built = field_expr > item.value
        elif item.operator == ">=":
            built = field_expr >= item.value
        elif item.operator == "<":
            built = field_expr < item.value
        elif item.operator == "<=":
            built = field_expr <= item.value
        elif item.operator == "in":
            built = field_expr.isin(list(item.value))
        else:
            raise QueryError(f"unsupported filter operator: {item.operator}")
        expression = built if expression is None else expression & built
    return expression


def _record_batch_semantic_hash(batch: pa.RecordBatch) -> str:
    columns: list[dict[str, Any]] = []
    for name, column in zip(batch.schema.names, batch.columns, strict=True):
        if column.null_count == 0 and (
            pa.types.is_floating(column.type)
            or pa.types.is_integer(column.type)
            or pa.types.is_boolean(column.type)
        ):
            values: Any = canonical_array_manifest(column.to_numpy(zero_copy_only=False))
        else:
            values = {"content_hash": semantic_hash(column.to_pylist()), "length": len(column)}
        columns.append({"name": name, "type": str(column.type), "values": values})
    return semantic_hash({"row_count": batch.num_rows, "columns": columns})
