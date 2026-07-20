"""Read-only M03 VALIDATION_ONLY static figure renderer.

This module is an offline validation consumer.  Canonical simulation data is
read exclusively through :class:`spine_sim.foundation.reader.ResultReader`;
no solver, standalone runner, surface evaluator, or storage backend is
imported.  Matplotlib is imported lazily only when rendering is explicitly
requested, so the M03 runtime remains usable without the optional preview
dependency.

The figures are deliberately plain validation evidence.  They do not select
M06 publication styling, smooth raw curves, reset path/time at release, or
include rejected diagnostics unless the caller opts in.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from importlib import import_module
from pathlib import Path
from typing import Any

import numpy as np

from spine_sim.foundation.canonical import (
    canonical_json_bytes,
    semantic_hash,
    source_file_hash,
    stable_content_id,
)
from spine_sim.foundation.errors import ContractViolation, QueryError
from spine_sim.foundation.models import CapabilityStatus, CertificationStatus, SourceIdentity
from spine_sim.foundation.reader import FilterSpec, OrderSpec, ResultReader

from .plot_recipes import (
    EVENT_ZOOM_AND_MULTI_PEAK_RECIPE_ID,
    FIVE_STAGE_FUNNEL_BANDS_RECIPE_ID,
    LOCAL_GEOMETRY_RECIPE_ID,
    PARAMETER_TRENDS_RECIPE_ID,
    QUALITY_AND_WORK_RECIPE_ID,
    RESPONSE_OVERVIEW_RECIPE_ID,
    STATE_BANDS_RECIPE_ID,
    STRUCTURE_AND_SPRING_RECIPE_ID,
    M03PlotRecipe,
    m03_plot_recipes,
)
from .result_extension import (
    ACCEPTED_STATE_HISTORY_DATASET,
    COMMITTED_EVENT_PAYLOADS_DATASET,
    CONTACT_SUPPORT_HISTORY_DATASET,
    REJECTED_DIAGNOSTICS_DATASET,
    RUN_REQUESTS_DATASET,
    SUPPORT_CANDIDATE_HISTORY_DATASET,
    WORK_LEDGER_DATASET,
)

VALIDATION_FIGURE_PACK_VERSION = "1.0.0"
VALIDATION_FIGURE_MANIFEST = "M03_VALIDATION_ONLY_FIGURE_MANIFEST.json"
VALIDATION_RENDERER_ID = "M03_RESULT_READER_STATIC_VALIDATION_RENDERER_1"
RAW_PEAK_ALGORITHM_ID = "M03_STRICT_THREE_POINT_RAW_LOCAL_MAXIMUM_1"


class FigureRenderStatus(StrEnum):
    RENDERED = "RENDERED"
    RENDERED_WITH_DATA_GAPS = "RENDERED_WITH_DATA_GAPS"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class RendererCapability:
    capability_status: CapabilityStatus
    reason_code: str
    explanation: str
    backend: str | None
    backend_version: str | None

    @property
    def available(self) -> bool:
        return self.capability_status is CapabilityStatus.SUPPORTED


@dataclass(frozen=True, slots=True)
class FigureFile:
    relative_path: str
    media_type: str
    byte_size: int
    content_sha256: str


@dataclass(frozen=True, slots=True)
class QueryEvidence:
    dataset_id: str
    role: str
    fields: tuple[str, ...]
    row_count: int
    result_hash: str
    include_non_default: bool
    include_diagnostics: bool
    status: str
    reason_code: str


@dataclass(frozen=True, slots=True)
class RecipeFigureArtifact:
    recipe_id: str
    recipe_family: str
    status: FigureRenderStatus
    reason_code: str
    files: tuple[FigureFile, ...]
    query_evidence: tuple[QueryEvidence, ...]
    rejected_rows_included: int
    raw_curve_visible: bool
    smoothing: str
    algorithms: tuple[str, ...]
    data_gaps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ValidationFigurePackManifest:
    pack_id: str
    pack_version: str
    renderer_id: str
    capability: RendererCapability
    source_identity: SourceIdentity
    certification_status: CertificationStatus
    bundle_semantic_hash: str
    reader_compatibility_status: str
    include_rejected: bool
    include_non_default_sources: bool
    formats: tuple[str, ...]
    artifacts: tuple[RecipeFigureArtifact, ...]
    data_query_hash: str
    manifest_hash: str
    manifest_file: str = VALIDATION_FIGURE_MANIFEST

    def identity_payload(self) -> dict[str, Any]:
        return {
            "pack_version": self.pack_version,
            "renderer_id": self.renderer_id,
            "capability": self.capability,
            "source_identity": self.source_identity,
            "certification_status": self.certification_status,
            "bundle_semantic_hash": self.bundle_semantic_hash,
            "reader_compatibility_status": self.reader_compatibility_status,
            "include_rejected": self.include_rejected,
            "include_non_default_sources": self.include_non_default_sources,
            "formats": self.formats,
            "artifacts": self.artifacts,
            "data_query_hash": self.data_query_hash,
            "manifest_file": self.manifest_file,
        }

    def to_payload(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            **self.identity_payload(),
            "manifest_hash": self.manifest_hash,
        }


@dataclass(frozen=True, slots=True)
class _ReadQuery:
    evidence: QueryEvidence
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True, slots=True)
class _RecipeData:
    recipe: M03PlotRecipe
    queries: tuple[_ReadQuery, ...]
    data_gaps: tuple[str, ...]

    def rows(
        self, dataset_id: str, required_field: str | None = None
    ) -> tuple[dict[str, Any], ...]:
        for item in self.queries:
            if item.evidence.dataset_id != dataset_id:
                continue
            if required_field is not None and required_field not in item.evidence.fields:
                continue
            return item.rows
        return ()

    @property
    def rejected_row_count(self) -> int:
        return sum(
            item.evidence.row_count
            for item in self.queries
            if item.evidence.dataset_id == REJECTED_DIAGNOSTICS_DATASET
        )


@dataclass(frozen=True, slots=True)
class _RenderedFigure:
    figure: Any
    algorithms: tuple[str, ...] = ()
    data_gaps: tuple[str, ...] = ()


def _load_matplotlib() -> tuple[Any, Any]:
    matplotlib = import_module("matplotlib")
    matplotlib.use("Agg", force=True)
    pyplot = import_module("matplotlib.pyplot")
    return matplotlib, pyplot


def probe_validation_figure_capability() -> RendererCapability:
    """Probe the optional backend without changing any simulation runtime contract."""

    try:
        matplotlib, _ = _load_matplotlib()
    except ImportError as error:
        return RendererCapability(
            CapabilityStatus.UNAVAILABLE,
            "M03_VALIDATION_MATPLOTLIB_UNAVAILABLE",
            f"Optional matplotlib backend is unavailable: {type(error).__name__}",
            None,
            None,
        )
    return RendererCapability(
        CapabilityStatus.SUPPORTED,
        "M03_VALIDATION_RENDERER_AVAILABLE",
        "Optional matplotlib backend is available for offline validation rendering.",
        "matplotlib/Agg",
        str(getattr(matplotlib, "__version__", "UNKNOWN")),
    )


def _validated_formats(formats: Sequence[str]) -> tuple[str, ...]:
    result = tuple(dict.fromkeys(str(item).lower() for item in formats))
    if not result:
        raise ContractViolation("validation figure formats cannot be empty")
    unsupported = sorted(set(result) - {"png", "svg"})
    if unsupported:
        raise ContractViolation(
            "validation renderer supports only PNG and SVG",
            details={"formats": unsupported},
        )
    return result


def _decode_json_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped or stripped[0] not in "[{":
        return value
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return value


def _normalized_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {str(key): _decode_json_value(value) for key, value in row.items()} for row in rows
    )


def _ordering_for(fields: Sequence[str]) -> tuple[OrderSpec, ...]:
    available = set(fields)
    ordering: list[OrderSpec] = []
    for name in (
        "case_id",
        "accepted_point_index",
        "x_total_mm",
        "path_coordinate_mm",
        "accepted_interval_index",
        "event_sequence",
        "event_id",
        "point_id",
    ):
        if name in available:
            ordering.append(OrderSpec(name))
    return tuple(ordering)


def _query_rows(
    reader: ResultReader,
    *,
    dataset_id: str,
    fields: tuple[str, ...],
    filters: tuple[FilterSpec, ...],
    role: str,
    include_non_default: bool,
    include_diagnostics: bool,
) -> _ReadQuery:
    try:
        result = reader.query(
            dataset_id,
            fields,
            filters,
            ordering=_ordering_for(fields),
            include_non_default=include_non_default,
            include_diagnostics=include_diagnostics,
        )
        table = result.read_all()
    except QueryError as error:
        evidence = QueryEvidence(
            dataset_id,
            role,
            fields,
            0,
            "UNAVAILABLE",
            include_non_default,
            include_diagnostics,
            "UNAVAILABLE",
            str(error),
        )
        return _ReadQuery(evidence, ())
    evidence = QueryEvidence(
        dataset_id,
        role,
        fields,
        table.num_rows,
        result.manifest.result_hash,
        include_non_default,
        include_diagnostics,
        "READ",
        "M00_RESULT_READER_QUERY_OK",
    )
    return _ReadQuery(evidence, _normalized_rows(table.to_pylist()))


def _read_recipe(
    reader: ResultReader,
    recipe: M03PlotRecipe,
    *,
    include_rejected: bool,
    include_non_default_sources: bool,
) -> _RecipeData:
    requirements = reader.check_plot_requirements(recipe.requirements)
    gaps = tuple(f"{item.field_id}:{item.code}" for item in requirements.deficiencies)
    selected = list(recipe.default_queries)
    if include_rejected:
        selected.extend(recipe.diagnostic_queries)
    queries: list[_ReadQuery] = []
    for query in selected:
        queries.append(
            _query_rows(
                reader,
                dataset_id=query.dataset_id,
                fields=query.fields,
                filters=query.filters,
                role=query.role.value,
                include_non_default=(include_non_default_sources or query.include_non_default),
                include_diagnostics=query.include_diagnostics,
            )
        )
    if recipe.recipe_id == PARAMETER_TRENDS_RECIPE_ID:
        queries.append(
            _query_rows(
                reader,
                dataset_id=RUN_REQUESTS_DATASET,
                fields=(
                    "run_id",
                    "case_id",
                    "parameter_bundle_id",
                    "surface_realization_id",
                    "resolved_request_payload",
                    "commit_receipt_id",
                ),
                filters=(FilterSpec("commit_receipt_id", "!=", ""),),
                role="PARAMETER_PROVENANCE",
                include_non_default=include_non_default_sources,
                include_diagnostics=False,
            )
        )
    gaps += tuple(
        f"{item.evidence.dataset_id}:{item.evidence.reason_code}"
        for item in queries
        if item.evidence.status == "UNAVAILABLE"
    )
    return _RecipeData(recipe, tuple(queries), tuple(dict.fromkeys(gaps)))


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _float_or(row: Mapping[str, Any], field: str, fallback: float) -> float:
    value = _as_float(row.get(field))
    return fallback if value is None else value


def _as_vector(value: Any, length: int) -> np.ndarray[Any, np.dtype[np.float64]] | None:
    decoded = _decode_json_value(value)
    try:
        result = np.asarray(decoded, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if result.shape != (length,) or not np.isfinite(result).all():
        return None
    return result


def _grouped(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[tuple[str, tuple[Mapping[str, Any], ...]], ...]:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row.get("case_id", "case:UNKNOWN")), []).append(row)
    return tuple(
        (key, tuple(value)) for key, value in sorted(groups.items(), key=lambda item: item[0])
    )


def _xy(
    rows: Sequence[Mapping[str, Any]], x_field: str, y_field: str
) -> tuple[np.ndarray[Any, np.dtype[np.float64]], np.ndarray[Any, np.dtype[np.float64]]]:
    pairs: list[tuple[float, float]] = []
    for row in rows:
        x_value = _as_float(row.get(x_field))
        y_value = _as_float(row.get(y_field))
        if x_value is not None and y_value is not None:
            pairs.append((x_value, y_value))
    pairs.sort(key=lambda item: item[0])
    if not pairs:
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)
    values = np.asarray(pairs, dtype=np.float64)
    return values[:, 0], values[:, 1]


def _mark_unavailable(axis: Any, message: str = "data unavailable") -> None:
    axis.text(0.5, 0.5, message, ha="center", va="center", transform=axis.transAxes)


def _plot_scalar_groups(
    axis: Any,
    rows: Sequence[Mapping[str, Any]],
    x_field: str,
    y_field: str,
    *,
    label_prefix: str = "",
) -> bool:
    plotted = False
    for case_id, case_rows in _grouped(rows):
        x_values, y_values = _xy(case_rows, x_field, y_field)
        if len(x_values) == 0:
            continue
        label = f"{label_prefix}{case_id}"
        axis.plot(x_values, y_values, marker="o", markersize=2.5, linewidth=0.9, label=label)
        plotted = True
    if plotted and len(_grouped(rows)) > 1:
        axis.legend(fontsize="x-small")
    return plotted


def _plot_vector_groups(
    axis: Any,
    rows: Sequence[Mapping[str, Any]],
    x_field: str,
    vector_field: str,
    components: Sequence[int],
    labels: Sequence[str],
) -> bool:
    plotted = False
    for case_id, case_rows in _grouped(rows):
        ordered = sorted(case_rows, key=lambda row: _float_or(row, x_field, math.inf))
        x_values: list[float] = []
        vectors: list[np.ndarray[Any, np.dtype[np.float64]]] = []
        for row in ordered:
            x_value = _as_float(row.get(x_field))
            vector = _as_vector(row.get(vector_field), max(components) + 1)
            if x_value is not None and vector is not None:
                x_values.append(x_value)
                vectors.append(vector)
        if not vectors:
            continue
        matrix = np.vstack(vectors)
        for component, label in zip(components, labels, strict=True):
            axis.plot(
                x_values,
                matrix[:, component],
                marker=".",
                linewidth=0.8,
                label=f"{label} {case_id}",
            )
        plotted = True
    if plotted:
        axis.legend(fontsize="xx-small", ncols=2)
    return plotted


def _event_x(data: _RecipeData) -> tuple[tuple[float, str], ...]:
    result: list[tuple[float, str]] = []
    for row in data.rows(COMMITTED_EVENT_PAYLOADS_DATASET, "event_kind"):
        coordinate = _as_float(row.get("path_coordinate_mm"))
        if coordinate is not None:
            result.append((coordinate, str(row.get("event_kind", "EVENT"))))
    return tuple(sorted(result))


def _draw_event_markers(axis: Any, events: Sequence[tuple[float, str]]) -> None:
    for coordinate, kind in events:
        axis.axvline(coordinate, color="0.65", linewidth=0.7, linestyle="--")
        axis.text(
            coordinate,
            0.98,
            kind,
            rotation=90,
            va="top",
            fontsize="xx-small",
            transform=axis.get_xaxis_transform(),
        )


def _annotate_rejected(figure: Any, data: _RecipeData) -> None:
    if data.rejected_row_count:
        figure.text(
            0.995,
            0.005,
            f"rejected diagnostic overlay (explicit opt-in): {data.rejected_row_count} rows",
            ha="right",
            va="bottom",
            fontsize="xx-small",
        )


def _render_response_overview(plt: Any, data: _RecipeData) -> _RenderedFigure:
    rows = data.rows(ACCEPTED_STATE_HISTORY_DATASET, "grip_resistance_rx_n")
    figure, axes = plt.subplots(2, 3, figsize=(12, 6.5), layout="constrained")
    panels = axes.ravel()
    scalar_specs = (
        (panels[0], "x_total_mm", "grip_resistance_rx_n", "Rx-x", "x [mm]", "Rx [N]"),
        (
            panels[1],
            "drag_elapsed_time_s",
            "grip_resistance_rx_n",
            "Rx-t",
            "drag elapsed time [s]",
            "Rx [N]",
        ),
    )
    for axis, x_field, y_field, title, xlabel, ylabel in scalar_specs:
        if not _plot_scalar_groups(axis, rows, x_field, y_field):
            _mark_unavailable(axis)
        axis.set(title=title, xlabel=xlabel, ylabel=ylabel)
    if not _plot_vector_groups(
        panels[2], rows, "x_total_mm", "beam_tip_translation_global_mm", (2,), ("uz",)
    ):
        _mark_unavailable(panels[2])
    panels[2].set(title="uz-x", xlabel="x [mm]", ylabel="global tip uz [mm]")
    if not _plot_vector_groups(
        panels[3],
        rows,
        "x_total_mm",
        "wrench_a_on_b_global_at_o_n_n_mm",
        (0, 1, 2),
        ("Fx", "Fy", "Fz"),
    ):
        _mark_unavailable(panels[3])
    panels[3].set(title="Full force components", xlabel="x [mm]", ylabel="force [N]")
    if not _plot_vector_groups(
        panels[4],
        rows,
        "x_total_mm",
        "wrench_a_on_b_global_at_o_n_n_mm",
        (3, 4, 5),
        ("Mx", "My", "Mz"),
    ):
        _mark_unavailable(panels[4])
    panels[4].set(title="Full moment components", xlabel="x [mm]", ylabel="moment [N mm]")
    panels[5].axis("off")
    panels[5].text(
        0.0,
        1.0,
        "Raw accepted curves\nA-on-B wrench at declared O\nNo smoothing / no release reset",
        va="top",
    )
    events = _event_x(data)
    for axis in (panels[0], panels[2], panels[3], panels[4]):
        _draw_event_markers(axis, events)
    _annotate_rejected(figure, data)
    return _RenderedFigure(figure, ("RAW_ACCEPTED_POINT_LINES_1",))


def _categorical_panel(
    axis: Any,
    rows: Sequence[Mapping[str, Any]],
    field: str,
    title: str,
) -> bool:
    pairs: list[tuple[float, str]] = []
    for row in rows:
        coordinate = _as_float(row.get("x_total_mm"))
        value = row.get(field)
        if coordinate is None:
            continue
        if isinstance(value, list):
            label = "+".join(str(item) for item in value) or "NONE"
        else:
            label = str(value)
        pairs.append((coordinate, label))
    if not pairs:
        _mark_unavailable(axis)
        return False
    labels = sorted({item[1] for item in pairs})
    encoded = {label: index for index, label in enumerate(labels)}
    axis.scatter([item[0] for item in pairs], [encoded[item[1]] for item in pairs], s=13)
    axis.set_yticks(tuple(encoded.values()), tuple(encoded))
    axis.set(title=title, xlabel="x [mm]")
    return True


def _render_state_bands(plt: Any, data: _RecipeData) -> _RenderedFigure:
    rows = data.rows(ACCEPTED_STATE_HISTORY_DATASET, "primary_mechanical_state")
    figure, axes = plt.subplots(4, 1, figsize=(10, 7), sharex=True, layout="constrained")
    for axis, field, title in zip(
        axes,
        (
            "primary_mechanical_state",
            "operation_phase",
            "contact_motion_states",
            "spring_state",
        ),
        ("Primary state", "Operation phase", "Contact motion", "Spring state"),
        strict=True,
    ):
        _categorical_panel(axis, rows, field, title)
    _draw_event_markers(axes[-1], _event_x(data))
    _annotate_rejected(figure, data)
    return _RenderedFigure(figure, ("RAW_CATEGORICAL_ACCEPTED_STATE_SCATTER_1",))


def _render_five_stage(plt: Any, data: _RecipeData) -> _RenderedFigure:
    rows = data.rows(ACCEPTED_STATE_HISTORY_DATASET, "geometric_candidate")
    figure, axis = plt.subplots(figsize=(11, 4.5), layout="constrained")
    lanes = (
        ("geometric_candidate", "geometric candidate"),
        ("loaded_contact", "loaded contact"),
        ("frictionally_stable", "frictionally stable"),
        ("load_bearing", "load bearing"),
    )
    found = False
    for lane_index, (field, label) in enumerate(lanes):
        x_values: list[float] = []
        y_values: list[float] = []
        for row in rows:
            coordinate = _as_float(row.get("x_total_mm"))
            if coordinate is not None and isinstance(row.get(field), bool):
                x_values.append(coordinate)
                y_values.append(lane_index + (0.22 if row[field] else -0.22))
        if x_values:
            axis.scatter(x_values, y_values, s=18, label=label)
            found = True
    if not found:
        _mark_unavailable(axis)
    axis.set_yticks(range(len(lanes)), tuple(item[1] for item in lanes))
    axis.set(title="Five-stage evidence lanes + release lifecycle", xlabel="x [mm]")
    events = tuple(
        item for item in _event_x(data) if item[1] in {"RELEASE", "RECONTACT", "REENGAGEMENT"}
    )
    _draw_event_markers(axis, events)
    _annotate_rejected(figure, data)
    return _RenderedFigure(
        figure,
        ("M03_FIVE_STAGE_PROPOSED_SUPPLEMENT_LANES_1", "COMMITTED_RELEASE_CHAIN_MARKERS_1"),
    )


def _render_local_geometry(plt: Any, data: _RecipeData) -> _RenderedFigure:
    accepted = data.rows(ACCEPTED_STATE_HISTORY_DATASET, "tip_center_global_mm")
    figure, axis = plt.subplots(figsize=(8, 6), layout="constrained")
    if not accepted:
        _mark_unavailable(axis)
        return _RenderedFigure(figure, data_gaps=("NO_ACCEPTED_LOCAL_GEOMETRY",))
    selected = max(accepted, key=lambda row: _float_or(row, "x_total_mm", -math.inf))
    point_id = str(selected.get("point_id", ""))
    root = _as_vector(selected.get("root_position_global_mm"), 3)
    tip = _as_vector(selected.get("tip_center_global_mm"), 3)
    axis_vector = _as_vector(selected.get("a_t_global"), 3)
    task = _as_vector(selected.get("task_direction_global"), 3)
    if root is None or tip is None:
        _mark_unavailable(axis, "root/tip geometry unavailable")
    else:
        axis.plot((root[0], tip[0]), (root[2], tip[2]), marker="o", label="shaft/centerline")
        axis.scatter((root[0], tip[0]), (root[2], tip[2]), s=(45, 55))
        if axis_vector is not None:
            axis.quiver(
                tip[0],
                tip[2],
                axis_vector[0],
                axis_vector[2],
                angles="xy",
                scale_units="xy",
                scale=1.0,
                label="tip axis",
            )
        if task is not None:
            axis.quiver(
                root[0],
                root[2],
                task[0],
                task[2],
                angles="xy",
                scale_units="xy",
                scale=1.0,
                label="task direction",
            )
    candidates = tuple(
        row
        for row in data.rows(SUPPORT_CANDIDATE_HISTORY_DATASET, "candidate_point_global_mm")
        if str(row.get("point_id", "")) == point_id
    )
    for row in candidates:
        point = _as_vector(row.get("candidate_point_global_mm"), 3)
        normal = _as_vector(row.get("normal_global"), 3)
        tangent = _as_vector(row.get("tangent_1_global"), 3)
        if point is None:
            continue
        axis.scatter(point[0], point[2], marker="x", label="support candidate")
        if normal is not None:
            axis.quiver(
                point[0], point[2], normal[0], normal[2], angles="xy", scale_units="xy", scale=4.0
            )
        if tangent is not None:
            axis.quiver(
                point[0], point[2], tangent[0], tangent[2], angles="xy", scale_units="xy", scale=4.0
            )
    contacts = tuple(
        row
        for row in data.rows(CONTACT_SUPPORT_HISTORY_DATASET, "point_global_mm")
        if str(row.get("point_id", "")) == point_id and bool(row.get("active", False))
    )
    for row in contacts:
        point = _as_vector(row.get("point_global_mm"), 3)
        if point is not None:
            axis.scatter(
                point[0],
                point[2],
                facecolors="none",
                edgecolors="black",
                s=75,
                label="active contact",
            )
    clearances = (
        f"cone={selected.get('cone_clearance_mm')} mm\n"
        f"shaft={selected.get('shaft_clearance_mm')} mm\n"
        f"mount={selected.get('mount_clearance_mm')} mm"
    )
    axis.text(0.02, 0.98, clearances, transform=axis.transAxes, va="top", fontsize="small")
    axis.set(title=f"Local geometry at {point_id}", xlabel="global x [mm]", ylabel="global z [mm]")
    handles, labels = axis.get_legend_handles_labels()
    if handles:
        unique = dict(zip(labels, handles, strict=True))
        axis.legend(unique.values(), unique.keys(), fontsize="x-small")
    axis.set_aspect("equal", adjustable="datalim")
    _annotate_rejected(figure, data)
    gaps = () if candidates else ("NO_SUPPORT_CANDIDATES_AT_SELECTED_POINT",)
    return _RenderedFigure(figure, ("GLOBAL_XZ_RAW_GEOMETRY_PROJECTION_1",), gaps)


def _norm_series(
    rows: Sequence[Mapping[str, Any]], x_field: str, vector_field: str, length: int
) -> tuple[np.ndarray[Any, np.dtype[np.float64]], np.ndarray[Any, np.dtype[np.float64]]]:
    pairs: list[tuple[float, float]] = []
    for row in rows:
        coordinate = _as_float(row.get(x_field))
        vector = _as_vector(row.get(vector_field), length)
        if coordinate is not None and vector is not None:
            pairs.append((coordinate, float(np.linalg.norm(vector))))
    pairs.sort()
    if not pairs:
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)
    array = np.asarray(pairs, dtype=np.float64)
    return array[:, 0], array[:, 1]


def _render_structure_spring(plt: Any, data: _RecipeData) -> _RenderedFigure:
    rows = data.rows(ACCEPTED_STATE_HISTORY_DATASET, "spring_compression_mm")
    figure, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
    panels = axes.ravel()
    for field, label in (
        ("beam_tip_translation_global_mm", "|u_tip| [mm]"),
        ("beam_tip_rotation_global_rad", "|theta_tip| [rad]"),
    ):
        x_values, norms = _norm_series(rows, "x_total_mm", field, 3)
        if len(x_values):
            panels[0].plot(x_values, norms, marker="o", label=label)
    if panels[0].lines:
        panels[0].legend(fontsize="x-small")
    else:
        _mark_unavailable(panels[0])
    panels[0].set(title="Beam tip kinematics", xlabel="x [mm]")
    x_values, force_norm = _norm_series(rows, "x_total_mm", "beam_root_force_global_n", 3)
    if len(x_values):
        panels[1].plot(x_values, force_norm, marker="o", label="|root force|")
        panels[1].legend(fontsize="x-small")
    else:
        _mark_unavailable(panels[1])
    panels[1].set(title="Beam root resultant", xlabel="x [mm]", ylabel="N")
    for field in ("spring_compression_mm", "spring_remaining_travel_mm"):
        _plot_scalar_groups(panels[2], rows, "x_total_mm", field, label_prefix=f"{field} ")
    panels[2].set(title="Spring travel", xlabel="x [mm]", ylabel="mm")
    for field in ("spring_force_n", "spring_hard_stop_reaction_n"):
        _plot_scalar_groups(panels[3], rows, "x_total_mm", field, label_prefix=f"{field} ")
    panels[3].set(title="Spring forces", xlabel="x [mm]", ylabel="N")
    _draw_event_markers(panels[2], _event_x(data))
    _annotate_rejected(figure, data)
    return _RenderedFigure(figure, ("RAW_BEAM_SPRING_COMPONENT_AND_NORM_LINES_1",))


def _strict_raw_peak_indices(values: Sequence[float]) -> tuple[int, ...]:
    return tuple(
        index
        for index in range(1, len(values) - 1)
        if values[index] > values[index - 1] and values[index] >= values[index + 1]
    )


def _render_event_zoom(plt: Any, data: _RecipeData) -> _RenderedFigure:
    rows = data.rows(ACCEPTED_STATE_HISTORY_DATASET, "event_sequence")
    figure, axes = plt.subplots(2, 1, figsize=(10, 7), layout="constrained")
    events = _event_x(data)
    all_x: list[float] = []
    for case_id, case_rows in _grouped(rows):
        x_values, forces = _xy(case_rows, "x_total_mm", "grip_resistance_rx_n")
        if not len(x_values):
            continue
        all_x.extend(float(item) for item in x_values)
        axes[0].plot(x_values, forces, marker="o", linewidth=0.9, label=case_id)
        peaks = _strict_raw_peak_indices(tuple(float(item) for item in forces))
        if peaks:
            axes[0].scatter(
                x_values[list(peaks)],
                forces[list(peaks)],
                marker="^",
                s=38,
                label=f"raw peaks {case_id}",
            )
    if not axes[0].lines:
        _mark_unavailable(axes[0])
    else:
        axes[0].legend(fontsize="xx-small")
    axes[0].set(title="Raw multi-peak response", xlabel="unreset x [mm]", ylabel="Rx [N]")
    _draw_event_markers(axes[0], events)
    for case_id, case_rows in _grouped(rows):
        x_values, forces = _xy(case_rows, "x_total_mm", "grip_resistance_rx_n")
        if len(x_values):
            axes[1].plot(x_values, forces, marker="o", linewidth=0.9, label=case_id)
    if events and all_x:
        first_event = events[0][0]
        span = max(max(all_x) - min(all_x), 1.0)
        axes[1].set_xlim(first_event - 0.15 * span, first_event + 0.15 * span)
    elif not axes[1].lines:
        _mark_unavailable(axes[1])
    axes[1].set(title="Committed-event zoom", xlabel="unreset x [mm]", ylabel="Rx [N]")
    _draw_event_markers(axes[1], events)
    _annotate_rejected(figure, data)
    gaps = () if events else ("NO_COMMITTED_EVENT_FOR_ZOOM",)
    return _RenderedFigure(figure, (RAW_PEAK_ALGORITHM_ID, "RAW_PRE_EVENT_POST_MARKERS_1"), gaps)


def _residual_block_max(value: Any) -> float | None:
    decoded = _decode_json_value(value)
    if not isinstance(decoded, list):
        return None
    values: list[float] = []
    for item in decoded:
        if not isinstance(item, Mapping):
            continue
        for key in ("normalized_norm", "raw_norm", "residual"):
            candidate = _as_float(item.get(key))
            if candidate is not None:
                values.append(abs(candidate))
                break
    return max(values, default=None)


def _render_quality_work(plt: Any, data: _RecipeData) -> _RenderedFigure:
    accepted = data.rows(ACCEPTED_STATE_HISTORY_DATASET, "complementarity_residual")
    work = data.rows(WORK_LEDGER_DATASET, "closure_error_n_mm")
    figure, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
    panels = axes.ravel()
    for field in ("complementarity_residual", "contact_soc_residual", "graph_residual"):
        _plot_scalar_groups(panels[0], accepted, "x_total_mm", field, label_prefix=f"{field} ")
    panels[0].set_yscale("symlog", linthresh=1.0e-12)
    panels[0].set(title="Complementarity / SOC / graph", xlabel="x [mm]", ylabel="residual")
    residual_pairs: list[tuple[float, float]] = []
    for row in accepted:
        coordinate = _as_float(row.get("x_total_mm"))
        residual = _residual_block_max(row.get("residual_block_payloads"))
        if coordinate is not None and residual is not None:
            residual_pairs.append((coordinate, residual))
    if residual_pairs:
        residual_pairs.sort()
        panels[1].plot(
            [item[0] for item in residual_pairs],
            [item[1] for item in residual_pairs],
            marker="o",
        )
        panels[1].set_yscale("symlog", linthresh=1.0e-12)
    else:
        _mark_unavailable(panels[1], "residual blocks unavailable")
    panels[1].set(title="Raw residual block maximum", xlabel="x [mm]")
    for field in (
        "cumulative_input_work_n_mm",
        "cumulative_friction_dissipation_n_mm",
        "cumulative_returned_energy_n_mm",
    ):
        _plot_scalar_groups(
            panels[2], work, "accepted_interval_index", field, label_prefix=f"{field} "
        )
    panels[2].set(
        title="Work / dissipation / returned energy", xlabel="accepted interval", ylabel="N mm"
    )
    for field in ("closure_error_n_mm", "normalized_closure_error"):
        _plot_scalar_groups(
            panels[3], work, "accepted_interval_index", field, label_prefix=f"{field} "
        )
    panels[3].set(title="Work closure", xlabel="accepted interval")
    _annotate_rejected(figure, data)
    return _RenderedFigure(figure, ("RAW_RESIDUAL_AND_WORK_LEDGER_LINES_1",))


def _nested(payload: Any, path: Sequence[str]) -> Any:
    current = _decode_json_value(payload)
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return current


_PARAMETER_PATHS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Rt", ("parameter_bundle", "needle", "tip_radius_mm")),
    ("d", ("parameter_bundle", "needle", "diameter_mm")),
    ("alpha", ("parameter_bundle", "needle", "alpha_rad")),
    ("mu", ("parameter_bundle", "contact", "friction_coefficient")),
    ("ks", ("parameter_bundle", "mount", "spring_stiffness_n_per_mm")),
)


def _render_parameter_trends(plt: Any, data: _RecipeData) -> _RenderedFigure:
    accepted = data.rows(ACCEPTED_STATE_HISTORY_DATASET, "parameter_bundle_id")
    requests = data.rows(RUN_REQUESTS_DATASET, "resolved_request_payload")
    parameters: dict[str, dict[str, Any]] = {}
    for row in requests:
        case_id = str(row.get("case_id", ""))
        payload = row.get("resolved_request_payload")
        parameters[case_id] = {name: _nested(payload, path) for name, path in _PARAMETER_PATHS}
    figure, axes = plt.subplots(2, 3, figsize=(13, 7), layout="constrained")
    panels = axes.ravel()
    gaps: list[str] = []
    for axis, (name, _) in zip(panels, _PARAMETER_PATHS, strict=False):
        plotted = False
        for case_id, case_rows in _grouped(accepted):
            x_values, forces = _xy(case_rows, "x_total_mm", "grip_resistance_rx_n")
            value = parameters.get(case_id, {}).get(name)
            if not len(x_values) or value is None:
                continue
            axis.plot(x_values, forces, marker="o", linewidth=0.8, label=f"{name}={value}")
            plotted = True
        if plotted:
            axis.legend(fontsize="xx-small")
        else:
            _mark_unavailable(axis, f"paired {name} data unavailable")
            gaps.append(f"PARAMETER_{name}_PAIR_UNAVAILABLE")
        axis.set(title=f"Paired raw {name} trend", xlabel="common x [mm]", ylabel="Rx [N]")
    panels[-1].axis("off")
    panels[-1].text(
        0.0,
        1.0,
        "No aggregate ranking\nRaw curves remain visible\nPair by surface realization/path",
        va="top",
    )
    _annotate_rejected(figure, data)
    return _RenderedFigure(
        figure,
        ("PAIRED_RAW_COMMON_SURFACE_PATH_LINES_1",),
        tuple(gaps),
    )


_RENDERERS = {
    RESPONSE_OVERVIEW_RECIPE_ID: _render_response_overview,
    STATE_BANDS_RECIPE_ID: _render_state_bands,
    FIVE_STAGE_FUNNEL_BANDS_RECIPE_ID: _render_five_stage,
    LOCAL_GEOMETRY_RECIPE_ID: _render_local_geometry,
    STRUCTURE_AND_SPRING_RECIPE_ID: _render_structure_spring,
    EVENT_ZOOM_AND_MULTI_PEAK_RECIPE_ID: _render_event_zoom,
    QUALITY_AND_WORK_RECIPE_ID: _render_quality_work,
    PARAMETER_TRENDS_RECIPE_ID: _render_parameter_trends,
}


def _save_figure(
    figure: Any,
    output_directory: Path,
    recipe: M03PlotRecipe,
    formats: Sequence[str],
) -> tuple[FigureFile, ...]:
    result: list[FigureFile] = []
    stem = recipe.recipe_family.replace("_", "-")
    for output_format in formats:
        path = output_directory / f"{stem}.{output_format}"
        metadata = (
            {"Creator": VALIDATION_RENDERER_ID, "Date": None}
            if output_format == "svg"
            else {"Software": VALIDATION_RENDERER_ID}
        )
        figure.savefig(path, format=output_format, dpi=120, metadata=metadata)
        result.append(
            FigureFile(
                path.name,
                "image/png" if output_format == "png" else "image/svg+xml",
                path.stat().st_size,
                source_file_hash(path),
            )
        )
    return tuple(result)


def _manifest(
    *,
    capability: RendererCapability,
    reader: ResultReader,
    include_rejected: bool,
    include_non_default_sources: bool,
    formats: tuple[str, ...],
    artifacts: tuple[RecipeFigureArtifact, ...],
) -> ValidationFigurePackManifest:
    query_payload = tuple((artifact.recipe_id, artifact.query_evidence) for artifact in artifacts)
    data_query_hash = semantic_hash(query_payload)
    identity: dict[str, Any] = {
        "pack_version": VALIDATION_FIGURE_PACK_VERSION,
        "renderer_id": VALIDATION_RENDERER_ID,
        "capability": capability,
        "source_identity": SourceIdentity.VALIDATION_ONLY,
        "certification_status": CertificationStatus.NOT_CERTIFIABLE,
        "bundle_semantic_hash": str(
            reader.bundle_info().get("bundle_semantic_hash", "UNAVAILABLE")
        ),
        "reader_compatibility_status": reader.compatibility_status,
        "include_rejected": include_rejected,
        "include_non_default_sources": include_non_default_sources,
        "formats": formats,
        "artifacts": artifacts,
        "data_query_hash": data_query_hash,
        "manifest_file": VALIDATION_FIGURE_MANIFEST,
    }
    manifest_hash = semantic_hash(identity)
    return ValidationFigurePackManifest(
        stable_content_id("m03_validation_figure_pack", identity),
        VALIDATION_FIGURE_PACK_VERSION,
        VALIDATION_RENDERER_ID,
        capability,
        SourceIdentity.VALIDATION_ONLY,
        CertificationStatus.NOT_CERTIFIABLE,
        identity["bundle_semantic_hash"],
        reader.compatibility_status,
        include_rejected,
        include_non_default_sources,
        formats,
        artifacts,
        data_query_hash,
        manifest_hash,
    )


def _write_manifest(output_directory: Path, manifest: ValidationFigurePackManifest) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    path = output_directory / manifest.manifest_file
    temporary = path.with_suffix(".json.tmp")
    temporary.write_bytes(canonical_json_bytes(manifest.to_payload()) + b"\n")
    temporary.replace(path)


def render_validation_figure_pack(
    reader: ResultReader,
    output_directory: str | Path,
    *,
    formats: Sequence[str] = ("png", "svg"),
    include_rejected: bool = False,
    include_non_default_sources: bool = False,
) -> ValidationFigurePackManifest:
    """Render the eight frozen recipes from a read-only M00 ``ResultReader``.

    ``include_rejected`` is deliberately false by default.  Enabling it reads
    the isolated M03 rejected dataset with both M00 opt-in switches and records
    the diagnostic row counts in each artifact; it never changes a raw curve or
    advances accepted/event history.
    """

    if not isinstance(reader, ResultReader):
        raise ContractViolation("validation renderer requires an M00 ResultReader")
    resolved_formats = _validated_formats(formats)
    output = Path(output_directory)
    capability = probe_validation_figure_capability()
    if not capability.available:
        manifest = _manifest(
            capability=capability,
            reader=reader,
            include_rejected=include_rejected,
            include_non_default_sources=include_non_default_sources,
            formats=resolved_formats,
            artifacts=(),
        )
        _write_manifest(output, manifest)
        return manifest

    matplotlib, pyplot = _load_matplotlib()
    matplotlib.rcParams["svg.hashsalt"] = VALIDATION_RENDERER_ID
    output.mkdir(parents=True, exist_ok=True)
    artifacts: list[RecipeFigureArtifact] = []
    for recipe in m03_plot_recipes():
        data = _read_recipe(
            reader,
            recipe,
            include_rejected=include_rejected,
            include_non_default_sources=include_non_default_sources,
        )
        rendered = _RENDERERS[recipe.recipe_id](pyplot, data)
        rendered.figure.suptitle(f"{recipe.title} — VALIDATION_ONLY", fontsize="large")
        files = _save_figure(rendered.figure, output, recipe, resolved_formats)
        pyplot.close(rendered.figure)
        gaps = tuple(dict.fromkeys((*data.data_gaps, *rendered.data_gaps)))
        artifacts.append(
            RecipeFigureArtifact(
                recipe.recipe_id,
                recipe.recipe_family,
                FigureRenderStatus.RENDERED_WITH_DATA_GAPS if gaps else FigureRenderStatus.RENDERED,
                "M03_VALIDATION_FIGURE_DATA_GAP" if gaps else "M03_VALIDATION_FIGURE_RENDERED",
                files,
                tuple(item.evidence for item in data.queries),
                data.rejected_row_count,
                True,
                "NONE",
                rendered.algorithms,
                gaps,
            )
        )
    manifest = _manifest(
        capability=capability,
        reader=reader,
        include_rejected=include_rejected,
        include_non_default_sources=include_non_default_sources,
        formats=resolved_formats,
        artifacts=tuple(artifacts),
    )
    _write_manifest(output, manifest)
    return manifest


__all__ = [
    "RAW_PEAK_ALGORITHM_ID",
    "VALIDATION_FIGURE_MANIFEST",
    "VALIDATION_FIGURE_PACK_VERSION",
    "VALIDATION_RENDERER_ID",
    "FigureFile",
    "FigureRenderStatus",
    "QueryEvidence",
    "RecipeFigureArtifact",
    "RendererCapability",
    "ValidationFigurePackManifest",
    "probe_validation_figure_capability",
    "render_validation_figure_pack",
]
