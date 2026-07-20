"""Run the canonical M03 analytic bundle and read-only validation figure pack."""

from __future__ import annotations

import argparse
import json
import platform
import resource
import time
from pathlib import Path
from typing import Any

from spine_sim.foundation.integrity import VerifyMode
from spine_sim.foundation.reader import ResultReader
from spine_sim.single_spine.demo_validation_only import (
    DEFAULT_BUNDLE_PATH,
    catalog_overview,
    generate_validation_bundle,
)
from spine_sim.single_spine.validation_figures import render_validation_figure_pack

DEFAULT_OUTPUT = Path("build/m03/M03_VALIDATION_RUN.json")
DEFAULT_FIGURE_DIRECTORY = Path("build/m03/validation_figures")


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Linux reports KiB; macOS reports bytes.
    return value if platform.system() == "Darwin" else value * 1024


def run_validation(
    *,
    bundle_output: Path,
    figure_output: Path,
    render_figures: bool,
    formats: tuple[str, ...],
) -> dict[str, Any]:
    started = time.perf_counter()
    bundle_started = time.perf_counter()
    bundle = generate_validation_bundle(bundle_output)
    bundle_seconds = time.perf_counter() - bundle_started
    overview = catalog_overview(bundle)
    figure_payload: dict[str, Any]
    if render_figures:
        figure_started = time.perf_counter()
        reader = ResultReader.open(bundle, VerifyMode.FULL)
        manifest = render_validation_figure_pack(
            reader,
            figure_output,
            formats=formats,
        )
        figure_seconds = time.perf_counter() - figure_started
        figure_payload = {
            "capability": manifest.capability.capability_status.value,
            "reason_code": manifest.capability.reason_code,
            "manifest_file": str(figure_output / manifest.manifest_file),
            "manifest_hash": manifest.manifest_hash,
            "artifact_count": len(manifest.artifacts),
            "file_count": sum(len(item.files) for item in manifest.artifacts),
            "rendered_with_data_gaps": sum(
                item.status.value == "RENDERED_WITH_DATA_GAPS" for item in manifest.artifacts
            ),
            "data_gaps": {
                item.recipe_id: list(item.data_gaps)
                for item in manifest.artifacts
                if item.data_gaps
            },
            "wall_time_seconds": figure_seconds,
        }
    else:
        figure_payload = {
            "capability": "NOT_ATTEMPTED",
            "reason_code": "M03_VALIDATION_FIGURES_SKIPPED_BY_CALLER",
            "artifact_count": 0,
            "file_count": 0,
            "rendered_with_data_gaps": 0,
            "data_gaps": {},
            "wall_time_seconds": 0.0,
        }
    return {
        "schema_version": "1.0.0",
        "task_id": "M03_SINGLE_SPINE_IMPLEMENTATION",
        "source_identity": "DEV_POLICY / VALIDATION_ONLY",
        "physics_scope": "no_damage + rigid Signorini/Coulomb + Euler-Bernoulli + A-authoritative mount",
        "experimentally_validated": "NOT_ASSESSED",
        "certification": "NOT_CERTIFIABLE",
        "bundle": overview,
        "figures": figure_payload,
        "performance": {
            "bundle_wall_time_seconds": bundle_seconds,
            "total_wall_time_seconds": time.perf_counter() - started,
            "process_peak_rss_bytes": _peak_rss_bytes(),
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-output", type=Path, default=DEFAULT_BUNDLE_PATH)
    parser.add_argument("--figure-output", type=Path, default=DEFAULT_FIGURE_DIRECTORY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--formats", nargs="+", default=("png", "svg"), choices=("png", "svg"))
    parser.add_argument("--skip-figures", action="store_true")
    args = parser.parse_args(argv)
    payload = run_validation(
        bundle_output=args.bundle_output,
        figure_output=args.figure_output,
        render_figures=not args.skip_figures,
        formats=tuple(args.formats),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    args.output.write_text(f"{rendered}\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
