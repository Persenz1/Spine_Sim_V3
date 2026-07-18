"""Run the frozen VALIDATION_ONLY M02/M01 compatibility panels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from spine_sim.numerics.m01_compatibility import (
    M01CompatibilityPanel,
    run_m01_compatibility_panel,
    write_m01_compatibility_report,
)


def _unsigned_128(value: str) -> int:
    converted = int(value, 0)
    if not 0 <= converted < 1 << 128:
        raise argparse.ArgumentTypeError("root seed must be an unsigned 128-bit integer")
    return converted


def _default_report(panel: str) -> Path:
    normalized = panel.upper().replace("-", "_")
    return Path("build/m02") / f"{normalized}_COMPATIBILITY_REPORT.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run real M01 SurfaceRealization compatibility paths without A/B production physics"
        )
    )
    parser.add_argument(
        "--panel",
        default=M01CompatibilityPanel.SMOKE_4.value,
        choices=(
            "smoke",
            "standard",
            "stress",
            *(item.value for item in M01CompatibilityPanel),
        ),
        help="Frozen 20-, 320-, or 1280-path panel",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Audit JSON destination (default: build/m02/<panel>_COMPATIBILITY_REPORT.json)",
    )
    parser.add_argument(
        "--root-seed",
        type=_unsigned_128,
        default=None,
        help="Optional unsigned 128-bit root seed, accepted in decimal or 0x form",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    kwargs = {} if args.root_seed is None else {"root_seed": args.root_seed}
    report = run_m01_compatibility_panel(args.panel, **kwargs)
    destination = args.output if args.output is not None else _default_report(report["panel_id"])
    write_m01_compatibility_report(destination, report)
    summary = {
        "panel_id": report["panel_id"],
        "overall_pass": report["overall_pass"],
        "counts": report["counts"],
        "semantic_result_hash": report["semantic_result_hash"],
        "wall_time_seconds": report["performance"]["wall_time_seconds"],
        "peak_rss_after_bytes": report["performance"]["peak_rss_after_bytes"],
        "audit_json": destination.as_posix(),
        "audit_json_bytes": destination.stat().st_size,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
