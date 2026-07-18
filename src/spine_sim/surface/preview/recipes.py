"""The two frozen M01 preview recipes; matplotlib is loaded only on render."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from spine_sim.foundation.canonical import source_file_hash, stable_content_id
from spine_sim.foundation.reader import FilterSpec, ResultReader

from ..contracts import VisualizationSample, make_visualization_sample
from ..result_extension import (
    SURFACE_REALIZATIONS_DATASET,
    VISUALIZATION_COORDINATES_FIELD,
    VISUALIZATION_HEIGHT_FIELD,
    VISUALIZATION_VALIDITY_FIELD,
)

OBLIQUE_3D_SURFACE = "oblique_3d_surface"
HEIGHT_MAP_2D = "height_map_2d"
PREVIEW_RECIPE_VERSION = "1.0.0"


class PreviewDependencyUnavailable(RuntimeError):
    """Raised only when a preview is requested without the optional extra."""


@dataclass(frozen=True, slots=True)
class PlotManifest:
    plot_id: str
    recipe: str
    recipe_version: str
    surface_realization_id: str
    visualization_sample_id: str
    window_mm: tuple[float, float, float, float]
    source_grid_shape: tuple[int, int]
    rendered_grid_shape: tuple[int, int]
    coordinate_unit: str
    height_unit: str
    visualization_q_max_rad_per_mm: float
    low_pass_method: str
    vertical_exaggeration: float
    colormap: str
    source_data_hash: str
    figure_path: str
    figure_sha256: str
    source_identity: str
    certification_status: str


def _load_pyplot() -> Any:
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised in a subprocess test
        raise PreviewDependencyUnavailable(
            "M01 preview requires the optional extra: pip install 'spine-sim[preview]'"
        ) from exc
    return plt


def _safe_title_label(label: str) -> str:
    normalized = label.strip().lower()
    forbidden = ("brick", "concrete", "sandpaper", "红砖", "混凝土", "砂纸")
    if any(item in normalized for item in forbidden):
        raise ValueError("M01 preview titles may not claim a real material identity")
    return label


def render_preview(
    sample: VisualizationSample,
    recipe: str,
    output_path: str | Path,
    *,
    title_label: str = "synthetic unidentified",
    vertical_exaggeration: float = 1.0,
    colormap: str = "viridis",
    dpi: int = 180,
    maximum_3d_grid: int = 320,
) -> PlotManifest:
    """Render one public visualization sample and write an adjacent manifest."""

    if recipe not in {OBLIQUE_3D_SURFACE, HEIGHT_MAP_2D}:
        raise ValueError(f"unsupported M01 preview recipe: {recipe}")
    if vertical_exaggeration <= 0.0:
        raise ValueError("vertical exaggeration must be positive")
    label = _safe_title_label(title_label)
    path = Path(output_path)
    if path.suffix.lower() != ".png":
        raise ValueError("M01 minimal preview output must be PNG")
    path.parent.mkdir(parents=True, exist_ok=True)
    plt = _load_pyplot()
    rendered_shape = sample.grid_shape
    if recipe == HEIGHT_MAP_2D:
        figure, axis = plt.subplots(figsize=(9.2, 7.4), constrained_layout=True)
        image = axis.imshow(
            np.where(sample.validity, sample.height_mm, 0.0),
            origin="lower",
            extent=sample.window_mm,
            interpolation="nearest",
            aspect="equal",
            cmap=colormap,
        )
        axis.set_xlabel("x [mm]")
        axis.set_ylabel("y [mm]")
        axis.set_title(f"{label} — M01 height map (visualization band)")
        colorbar = figure.colorbar(image, ax=axis)
        colorbar.set_label("height h [mm]")
    else:
        ny, nx = sample.grid_shape
        stride = max(1, int(np.ceil(max(nx, ny) / maximum_3d_grid)))
        x = sample.x_coordinates_mm[::stride]
        y = sample.y_coordinates_mm[::stride]
        z = sample.height_mm[::stride, ::stride] * vertical_exaggeration
        valid = sample.validity[::stride, ::stride]
        rendered_shape = z.shape
        x_grid, y_grid = np.meshgrid(x, y, indexing="xy", copy=False)
        figure = plt.figure(figsize=(10.2, 7.8), constrained_layout=True)
        axis = figure.add_subplot(111, projection="3d")
        surface = axis.plot_surface(
            x_grid,
            y_grid,
            np.where(valid, z, 0.0),
            cmap=colormap,
            linewidth=0.0,
            antialiased=True,
            rcount=min(220, z.shape[0]),
            ccount=min(220, z.shape[1]),
        )
        axis.view_init(elev=34.0, azim=-128.0)
        axis.set_xlabel("x [mm]")
        axis.set_ylabel("y [mm]")
        axis.set_zlabel(f"h x {vertical_exaggeration:g} [mm]")
        axis.set_title(f"{label} — M01 oblique surface (visualization band)")
        figure.colorbar(surface, ax=axis, shrink=0.68, pad=0.08, label="displayed height [mm]")
    figure.savefig(path, dpi=dpi, format="png", metadata={"Software": "spine-sim M01"})
    plt.close(figure)
    figure_hash = source_file_hash(path)
    preimage = {
        "recipe": recipe,
        "recipe_version": PREVIEW_RECIPE_VERSION,
        "surface_realization_id": sample.surface_realization_id,
        "visualization_sample_id": sample.sample_id,
        "window_mm": sample.window_mm,
        "source_grid_shape": sample.grid_shape,
        "rendered_grid_shape": rendered_shape,
        "vertical_exaggeration": vertical_exaggeration,
        "colormap": colormap,
        "source_data_hash": sample.source_hash,
        "figure_sha256": figure_hash,
    }
    manifest = PlotManifest(
        stable_content_id("m01_plot", preimage),
        recipe,
        PREVIEW_RECIPE_VERSION,
        sample.surface_realization_id,
        sample.sample_id,
        sample.window_mm,
        sample.grid_shape,
        rendered_shape,
        "mm",
        "mm",
        sample.visualization_q_max_rad_per_mm,
        sample.low_pass_method,
        vertical_exaggeration,
        colormap,
        sample.source_hash,
        path.as_posix(),
        figure_hash,
        "DEV_POLICY synthetic_unidentified or VALIDATION_ONLY analytic",
        "NOT_CERTIFIABLE",
    )
    manifest_path = path.with_suffix(".plot_manifest.json")
    manifest_path.write_text(
        json.dumps(asdict(manifest), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def sample_from_result_reader(reader: ResultReader, case_id: str) -> VisualizationSample:
    """Build a public sample exclusively from saved M01 fields through ResultReader."""

    table = reader.query(
        SURFACE_REALIZATIONS_DATASET,
        fields=("surface_realization_id", "logical_domain_mm"),
        filters=(FilterSpec("case_id", "==", case_id),),
    ).read_all()
    if table.num_rows != 1:
        raise ValueError(f"expected one M01 realization for case {case_id}")
    row = table.to_pylist()[0]
    logical_domain = row["logical_domain_mm"]
    if isinstance(logical_domain, str):
        logical_domain = json.loads(logical_domain)
    height_payload = reader.open_array(VISUALIZATION_HEIGHT_FIELD, case_id).read()
    validity_payload = reader.open_array(VISUALIZATION_VALIDITY_FIELD, case_id).read()
    coordinate_payload = reader.open_array(VISUALIZATION_COORDINATES_FIELD, case_id).read()
    height = np.asarray(height_payload["values"], dtype=np.float64)
    validity = np.asarray(validity_payload["values"], dtype=np.bool_)
    coordinates = np.asarray(coordinate_payload["values"], dtype=np.float64)
    if coordinates.ndim != 2 or coordinates.shape[0] != 2:
        raise ValueError("saved M01 visualization_coordinates must have shape (2, N)")
    x, y = coordinates[0], coordinates[1]
    if height.shape != (y.size, x.size):
        raise ValueError("saved coordinates are incompatible with visualization height")
    spacing = max(
        float(np.max(np.diff(x))) if x.size > 1 else float("inf"),
        float(np.max(np.diff(y))) if y.size > 1 else float("inf"),
    )
    q_max = 0.0 if not np.isfinite(spacing) else float(np.pi / spacing)
    window_values = tuple(float(item) for item in logical_domain)
    if len(window_values) != 4:
        raise ValueError("saved M01 logical_domain_mm must contain four bounds")
    window_mm = (
        window_values[0],
        window_values[1],
        window_values[2],
        window_values[3],
    )
    return make_visualization_sample(
        surface_realization_id=row["surface_realization_id"],
        window_mm=window_mm,
        x_coordinates_mm=x,
        y_coordinates_mm=y,
        height_mm=height,
        validity=validity,
        visualization_q_max_rad_per_mm=q_max,
        low_pass_method="saved_M01_visualization_band_v1",
    )
