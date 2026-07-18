#!/usr/bin/env python3
"""Measure a bounded, deterministic M01 synthetic-surface fixture.

This is a geometry/materialization performance probe only.  It deliberately
does not construct a full-parent Rt/10 dense field and carries no contact,
force, friction, or real-material interpretation.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import platform
import resource
import sys
import time
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np

from spine_sim.foundation.storage import write_json_atomic
from spine_sim.surface.contracts import (
    GENERATOR_VERSION,
    QUERY_CONTRACT_VERSION,
    RNG_PROFILE_ID,
    RoughnessTier,
    SurfaceFamily,
    make_latent_noise_identity,
)
from spine_sim.surface.materialization import (
    NORMAL_PATH_BUILDS_FULL_DOMAIN_RT10_DENSE,
    LODLevel,
    MaterializationConfig,
    TileMaterializer,
    derive_query_footprint,
)
from spine_sim.surface.provider import SurfaceProvider, make_synthetic_source_descriptor
from spine_sim.surface.query import SurfaceQueryHandle
from spine_sim.surface.synthetic import synthetic_parameters_for_tier

DEFAULT_REPORT = Path("reports/m01/M01_PERFORMANCE_REPORT.json")
DEFAULT_PREVIEW_NAME = "M01_PERFORMANCE_HEIGHT_MAP.png"
REFERENCE_RT_MM = 0.05
ROOT_SEED = 0x4D30315F50455246
SURFACE_SEED_INDEX = 17
LATENT_NAMESPACE = "m01.surface.latent.performance_fixture"
MAXIMUM_CACHE_MIB = 512.0


@dataclass(slots=True)
class _RssTracker:
    baseline_bytes: int
    maximum_observed_bytes: int

    @classmethod
    def start(cls) -> _RssTracker:
        current = _current_rss_bytes()
        return cls(current, current)

    def sample(self) -> int:
        current = _current_rss_bytes()
        self.maximum_observed_bytes = max(self.maximum_observed_bytes, current)
        return current


def _current_rss_bytes() -> int:
    try:
        import psutil  # type: ignore[import-untyped]

        return int(psutil.Process().memory_info().rss)
    except ImportError:
        return _resource_peak_rss_bytes()


def _resource_peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _physical_memory_bytes() -> int | None:
    try:
        import psutil

        return int(psutil.virtual_memory().total)
    except ImportError:
        try:
            return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
        except (OSError, TypeError, ValueError):
            return None


def _physical_cpu_count() -> int | None:
    try:
        import psutil

        result = psutil.cpu_count(logical=False)
        return None if result is None else int(result)
    except ImportError:
        return None


def _dependency_versions() -> dict[str, str]:
    names = ("spine-sim", "numpy", "pyarrow", "zarr", "psutil", "matplotlib")
    output: dict[str, str] = {}
    for name in names:
        try:
            output[name] = version(name)
        except PackageNotFoundError:
            output[name] = "UNAVAILABLE"
    return output


def _thread_settings() -> dict[str, Any]:
    names = (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    )
    return {
        "logical_cpu_count": os.cpu_count(),
        "environment": {name: os.environ.get(name, "UNSET") for name in names},
    }


def _float_settings() -> dict[str, Any]:
    details = np.finfo(np.float64)
    return {
        "canonical_dtype": "float64",
        "byteorder": sys.byteorder,
        "numpy_error_policy": dict(np.geterr()),
        "epsilon": float(details.eps),
        "smallest_normal": float(details.smallest_normal),
        "maximum": float(details.max),
        "mantissa_bits": int(details.nmant),
        "rounding": "IEEE-754 round-to-nearest assumed by the locked runtime",
    }


def _bounds(footprint: Any) -> list[float]:
    return [
        float(footprint.x_min_mm),
        float(footprint.x_max_mm),
        float(footprint.y_min_mm),
        float(footprint.y_max_mm),
    ]


def _directory_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if not path.is_dir():
        return 0
    return sum(
        item.stat().st_size for item in path.rglob("*") if item.is_file() and not item.is_symlink()
    )


def _known_artifact_sizes(preview_path: Path | None) -> dict[str, int]:
    candidates = (
        Path("build/M01_VALIDATION_ONLY.spine-result"),
        Path("reports/m01/demo"),
        *((preview_path,) if preview_path is not None else ()),
        *((preview_path.with_suffix(".plot_manifest.json"),) if preview_path is not None else ()),
    )
    output: dict[str, int] = {}
    for path in candidates:
        if path.exists():
            output[path.as_posix()] = _directory_size(path)
    return output


def _render_optional_preview(sample: Any, output_path: Path, enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"attempted": False, "status": "DISABLED", "elapsed_seconds": 0.0}
    if importlib.util.find_spec("matplotlib") is None:
        return {
            "attempted": False,
            "status": "OPTIONAL_DEPENDENCY_UNAVAILABLE",
            "elapsed_seconds": 0.0,
        }
    started = time.perf_counter()
    try:
        from spine_sim.surface.preview.recipes import HEIGHT_MAP_2D, render_preview

        manifest = render_preview(
            sample,
            HEIGHT_MAP_2D,
            output_path,
            title_label="synthetic unidentified performance fixture",
            dpi=100,
        )
    except Exception as error:  # optional evidence must not invalidate geometry timings
        return {
            "attempted": True,
            "status": "FAILED",
            "elapsed_seconds": time.perf_counter() - started,
            "error_type": type(error).__name__,
            "error": str(error),
        }
    return {
        "attempted": True,
        "status": "CREATED",
        "elapsed_seconds": time.perf_counter() - started,
        "path": output_path.as_posix(),
        "plot_id": manifest.plot_id,
        "recipe": manifest.recipe,
    }


def run_m01_performance_fixture(
    *,
    report_path: Path = DEFAULT_REPORT,
    preview_path: Path | None = None,
    preview_enabled: bool = True,
    tile_core_size: int = 64,
    visualization_grid_size: int = 128,
    cache_budget_mib: float = 64.0,
) -> dict[str, Any]:
    """Run the representative bounded fixture and return its JSON report."""

    if tile_core_size < 16:
        raise ValueError("tile_core_size must be at least 16")
    if visualization_grid_size < 16:
        raise ValueError("visualization_grid_size must be at least 16")
    if not 0.0 < cache_budget_mib <= MAXIMUM_CACHE_MIB:
        raise ValueError("cache_budget_mib must be positive and no greater than 512 MiB")

    output_preview = preview_path or report_path.parent / DEFAULT_PREVIEW_NAME
    rss = _RssTracker.start()
    total_started = time.perf_counter()

    fixture_started = time.perf_counter()
    provider = SurfaceProvider()
    descriptor = make_synthetic_source_descriptor()
    parameters = synthetic_parameters_for_tier(
        RoughnessTier.MEDIUM,
        surface_scale_reference_Rt_mm=REFERENCE_RT_MM,
        modes_per_band=8,
    )
    spec_result = provider.create_surface_spec(
        descriptor,
        SurfaceFamily.SELF_AFFINE_GAUSSIAN,
        parameters,
    )
    if spec_result.spec is None:
        raise RuntimeError(f"M01 performance spec unavailable: {spec_result.status.reason_code}")
    latent = make_latent_noise_identity(
        ROOT_SEED,
        SURFACE_SEED_INDEX,
        latent_noise_namespace=LATENT_NAMESPACE,
    )
    realization_result = provider.create_realization(
        descriptor,
        spec_result.spec,
        latent_identity=latent,
    )
    handle = provider.open_query_handle(realization_result)
    if handle is None:
        raise RuntimeError(
            f"M01 performance realization unavailable: {realization_result.status.reason_code}"
        )
    evaluator = handle.evaluator
    fixture_seconds = time.perf_counter() - fixture_started
    rss.sample()

    path = np.asarray(((25.0, 75.0), (125.0, 75.0)), dtype=np.float64)
    narrow = derive_query_footprint(
        path_points_mm=path,
        guard_mm=0.5,
        maximum_path_length_mm=100.0,
        derivation_method="M01_PERFORMANCE_100MM_NARROW",
    )
    wide = derive_query_footprint(
        path_points_mm=path,
        geometry_offsets_mm=np.asarray(((-4.0, -10.0), (4.0, 10.0)), dtype=np.float64),
        guard_mm=0.5,
        maximum_path_length_mm=100.0,
        derivation_method="M01_PERFORMANCE_100MM_WIDE",
    )

    config = MaterializationConfig(
        core_shape=(tile_core_size, tile_core_size),
        halo_samples=4,
        memory_cache_budget_mib=cache_budget_mib,
        disk_cache_enabled=False,
    )
    materializer = TileMaterializer(
        evaluator,
        handle.realization.surface_realization_id,
        logical_domain=handle.realization.logical_domain,
        generator_version=handle.realization.generator_version,
        query_contract_version=handle.realization.query_contract_version,
        config=config,
    )

    generation_seconds = 0.0
    hit_seconds = 0.0
    streamed: list[dict[str, Any]] = []
    first_request: tuple[Any, LODLevel, tuple[int, int], Any] | None = None
    for footprint_name, footprint in (("narrow", narrow), ("wide", wide)):
        for lod in (LODLevel.RT_OVER_5, LODLevel.RT_OVER_8, LODLevel.RT_OVER_10):
            coordinates = materializer.tile_coordinates_for_footprint(
                footprint,
                reference_rt_mm=REFERENCE_RT_MM,
                lod=lod,
            )
            started = time.perf_counter()
            tile = next(
                materializer.iter_footprint_tiles(
                    footprint,
                    reference_rt_mm=REFERENCE_RT_MM,
                    lod=lod,
                )
            )
            miss_elapsed = time.perf_counter() - started
            generation_seconds += miss_elapsed
            rss.sample()
            started = time.perf_counter()
            hit = materializer.sample_tile(
                footprint,
                tile.payload.key.tile_coordinate,
                reference_rt_mm=REFERENCE_RT_MM,
                lod=lod,
            )
            hit_elapsed = time.perf_counter() - started
            hit_seconds += hit_elapsed
            streamed.append(
                {
                    "footprint": footprint_name,
                    "lod": lod.label,
                    "spacing_mm": lod.spacing_mm(REFERENCE_RT_MM),
                    "active_bands": list(lod.active_bands),
                    "available_tile_count": len(coordinates),
                    "streamed_tile_count": 1,
                    "tile_coordinate": list(tile.payload.key.tile_coordinate),
                    "first_request_status": tile.receipt.cache_status,
                    "repeat_request_status": hit.receipt.cache_status,
                    "first_request_seconds": miss_elapsed,
                    "repeat_request_seconds": hit_elapsed,
                    "payload_bytes": tile.payload.payload_bytes,
                }
            )
            if first_request is None:
                first_request = (footprint, lod, tile.payload.key.tile_coordinate, tile.payload.key)

    if first_request is None:  # pragma: no cover - the validated footprints always yield tiles
        raise RuntimeError("M01 performance footprints produced no tiles")
    first_footprint, first_lod, first_coordinate, first_key = first_request
    materializer.cache.corrupt_memory_entry_for_testing(first_key)
    regeneration_started = time.perf_counter()
    regenerated = materializer.sample_tile(
        first_footprint,
        first_coordinate,
        reference_rt_mm=REFERENCE_RT_MM,
        lod=first_lod,
    )
    regeneration_seconds = time.perf_counter() - regeneration_started
    rss.sample()

    query = SurfaceQueryHandle(handle)
    scalar_started = time.perf_counter()
    scalar_response = query.query_height_differential(
        np.asarray((75.0, 75.0), dtype=np.float64),
        derivative_order=2,
    )
    scalar_query_seconds = time.perf_counter() - scalar_started
    batch_points = np.column_stack(
        (
            np.linspace(25.0, 125.0, 256, dtype=np.float64),
            np.linspace(65.0, 85.0, 256, dtype=np.float64),
        )
    )
    batch_started = time.perf_counter()
    batch_response = query.query_height_differential(batch_points, derivative_order=2)
    batch_query_seconds = time.perf_counter() - batch_started
    rss.sample()

    visualization_started = time.perf_counter()
    sample = materializer.sample_visualization_window(
        (25.0, 125.0, 55.0, 95.0),
        (visualization_grid_size, visualization_grid_size),
    )
    visualization_seconds = time.perf_counter() - visualization_started
    rss.sample()

    preview = _render_optional_preview(sample, output_preview, preview_enabled)
    rss.sample()
    cache = materializer.stats
    scalar_height = scalar_response.field("height_mm")
    batch_height = batch_response.field("height_mm")
    checks = {
        "deterministic_fixture_created": handle.realization.latent_noise_id
        == latent.latent_noise_id,
        "path_length_exactly_100_mm": bool(
            np.isclose(np.linalg.norm(path[1] - path[0]), 100.0, rtol=0.0, atol=0.0)
        ),
        "narrow_and_wide_footprints_distinct": narrow.footprint_id != wide.footprint_id,
        "all_lods_streamed_for_both_footprints": len(streamed) == 6,
        "cache_miss_exercised": cache.cache_misses > 0,
        "cache_hit_exercised": cache.cache_hits > 0,
        "cache_corruption_regenerated": (
            cache.regenerated_tiles > 0
            and regenerated.receipt.cache_status == "CORRUPTION_REGENERATED"
        ),
        "cache_payload_within_configured_budget": cache.payload_within_budget,
        "cache_budget_at_most_512_mib": cache.memory_budget_bytes
        <= int(MAXIMUM_CACHE_MIB * 1024**2),
        "scalar_query_valid": bool(scalar_height.validity.all()),
        "batch_query_cardinality_and_validity": bool(
            batch_height.validity.shape == (256,) and batch_height.validity.all()
        ),
        "visualization_valid": bool(sample.validity.all()),
        "full_domain_rt10_dense_created_is_false": (
            not NORMAL_PATH_BUILDS_FULL_DOMAIN_RT10_DENSE
            and not cache.full_domain_rt10_dense_created
        ),
    }
    resource_peak = _resource_peak_rss_bytes()
    observed_peak = max(rss.maximum_observed_bytes, resource_peak)
    total_seconds = time.perf_counter() - total_started
    report: dict[str, Any] = {
        "report_schema_version": "1.0.0",
        "module": "M01_SURFACE_IMPLEMENTATION",
        "source_identity": "VALIDATION_ONLY performance evidence over DEV_POLICY synthetic geometry",
        "certification_status": "NOT_CERTIFIABLE",
        "physical_interpretation": "none; geometry/materialization performance only",
        "environment": {
            "hardware_processor": platform.processor() or "UNAVAILABLE",
            "machine": platform.machine(),
            "cpu_logical_count": os.cpu_count(),
            "cpu_physical_count": _physical_cpu_count(),
            "physical_memory_bytes": _physical_memory_bytes(),
            "os": platform.platform(),
            "python": sys.version,
            "dependencies": _dependency_versions(),
            "thread_settings": _thread_settings(),
            "float_settings": _float_settings(),
        },
        "fixture": {
            "family": handle.realization.family.value,
            "tier": RoughnessTier.MEDIUM.value,
            "generator_version": GENERATOR_VERSION,
            "query_contract_version": QUERY_CONTRACT_VERSION,
            "rng_profile_id": RNG_PROFILE_ID,
            "source_descriptor_id": descriptor.source_descriptor_id,
            "surface_spec_id": handle.spec.surface_spec_id,
            "surface_realization_id": handle.realization.surface_realization_id,
            "seed_id": latent.seed_id,
            "latent_noise_id": latent.latent_noise_id,
            "root_seed": ROOT_SEED,
            "surface_seed_index": SURFACE_SEED_INDEX,
            "logical_domain_mm": [0.0, 150.0, 0.0, 150.0],
            "reference_rt_mm": REFERENCE_RT_MM,
            "mode_count": int(evaluator.mode_count),
            "band_count": len(evaluator.band_manifests),
            "parameters": parameters,
        },
        "footprints": {
            "path_points_mm": path.tolist(),
            "path_length_mm": float(np.linalg.norm(path[1] - path[0])),
            "narrow": {
                "footprint_id": narrow.footprint_id,
                "bounds_mm": _bounds(narrow),
                "guard_mm": narrow.guard_mm,
            },
            "wide": {
                "footprint_id": wide.footprint_id,
                "bounds_mm": _bounds(wide),
                "guard_mm": wide.guard_mm,
                "geometry_offsets_mm": [[-4.0, -10.0], [4.0, 10.0]],
            },
        },
        "lod_and_streaming": {
            "tile_core_shape": list(config.core_shape),
            "halo_samples": config.halo_samples,
            "bounded_tiles_per_footprint_lod": 1,
            "requests": streamed,
        },
        "cache": {
            **asdict(cache),
            "cache_hits": cache.cache_hits,
            "cache_budget_mib": cache.memory_budget_bytes / 1024**2,
            "memory_payload_mib": cache.memory_payload_bytes / 1024**2,
            "payload_within_budget": cache.payload_within_budget,
            "regeneration_probe_status": regenerated.receipt.cache_status,
        },
        "timings_seconds": {
            "fixture_spec_realization_generate": fixture_seconds,
            "tile_first_requests_total": generation_seconds,
            "tile_repeat_hits_total": hit_seconds,
            "corruption_regeneration": regeneration_seconds,
            "scalar_query": scalar_query_seconds,
            "batch_query_256_points": batch_query_seconds,
            "visualization_sample_generate": visualization_seconds,
            "optional_plot": preview["elapsed_seconds"],
            "total": total_seconds,
        },
        "query": {
            "scalar_query_id": scalar_response.query_id,
            "scalar_capability": scalar_response.capability.value,
            "scalar_height_mm": None
            if scalar_height.values is None
            else float(scalar_height.values[0]),
            "batch_query_id": batch_response.query_id,
            "batch_capability": batch_response.capability.value,
            "batch_point_count": int(batch_height.validity.size),
        },
        "visualization": {
            "sample_id": sample.sample_id,
            "window_mm": list(sample.window_mm),
            "grid_shape": list(sample.grid_shape),
            "q_max_rad_per_mm": sample.visualization_q_max_rad_per_mm,
            "low_pass_method": sample.low_pass_method,
            "source_hash": sample.source_hash,
            "preview": preview,
        },
        "memory": {
            "baseline_rss_bytes": rss.baseline_bytes,
            "maximum_sampled_rss_bytes": rss.maximum_observed_bytes,
            "resource_peak_rss_bytes": resource_peak,
            "reported_peak_rss_bytes": observed_peak,
            "peak_extra_over_baseline_bytes": max(0, observed_peak - rss.baseline_bytes),
        },
        "artifact_sizes_bytes": _known_artifact_sizes(
            output_preview if preview.get("status") == "CREATED" else None
        ),
        "safety_assertions": {
            "full_domain_rt10_dense_created": False,
            "normal_path_constant": NORMAL_PATH_BUILDS_FULL_DOMAIN_RT10_DENSE,
            "cache_budget_mib": cache.memory_budget_bytes / 1024**2,
            "cache_budget_maximum_mib": MAXIMUM_CACHE_MIB,
            "cache_budget_le_512_mib": cache.memory_budget_bytes
            <= int(MAXIMUM_CACHE_MIB * 1024**2),
            "cache_payload_within_budget": cache.payload_within_budget,
        },
        "checks": checks,
        "overall_pass": all(checks.values()),
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--preview-output", type=Path)
    parser.add_argument("--no-preview", action="store_true")
    parser.add_argument("--tile-core-size", type=int, default=64)
    parser.add_argument("--visualization-grid-size", type=int, default=128)
    parser.add_argument("--cache-budget-mib", type=float, default=64.0)
    args = parser.parse_args()
    report = run_m01_performance_fixture(
        report_path=args.report,
        preview_path=args.preview_output,
        preview_enabled=not args.no_preview,
        tile_core_size=args.tile_core_size,
        visualization_grid_size=args.visualization_grid_size,
        cache_budget_mib=args.cache_budget_mib,
    )
    write_json_atomic(args.report, report)
    print(f"M01 performance report: {args.report}")
    print(f"overall_pass={report['overall_pass']}")
    raise SystemExit(0 if report["overall_pass"] else 1)


if __name__ == "__main__":
    main()
