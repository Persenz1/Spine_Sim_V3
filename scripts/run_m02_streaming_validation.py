"""Run the frozen M02 bounded-memory streaming scalability fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from spine_sim.numerics.streaming import (
    DEFAULT_FAILURE_PERIOD,
    DEFAULT_TRANSACTION_BATCH_SIZE,
    run_streaming_validation,
    write_streaming_validation_report,
)

DEFAULT_REPORT = Path("build/m02/M02_STREAMING_VALIDATION.json")
DEFAULT_BUNDLE = Path("build/m02/M02_STREAMING_VALIDATION.spine-result")


def _positive_int(value: str) -> int:
    converted = int(value)
    if converted <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return converted


def _available_bundle_path(requested: Path) -> Path:
    """Choose a non-existing generated path without deleting prior evidence."""

    if not requested.exists():
        return requested
    for index in range(1, 10_000):
        candidate = requested.with_name(f"{requested.name}.{index}")
        if not candidate.exists():
            return candidate
    raise FileExistsError("could not allocate a non-existing generated bundle path")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate lazy 64/256/256 and paired 4000/16000 M02 case plans with a "
            "cheap deterministic owner; no A/B physics or M05 ranking is run"
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT,
        help="Machine-readable report (default: build/m02/M02_STREAMING_VALIDATION.json)",
    )
    parser.add_argument(
        "--bundle-output",
        type=Path,
        default=DEFAULT_BUNDLE,
        help="M00 round-trip bundle; an unused suffix is chosen if it exists",
    )
    parser.add_argument(
        "--no-m00-bundle",
        action="store_true",
        help="Run scalability checks without writing the optional M00 evidence bundle",
    )
    parser.add_argument(
        "--failure-period",
        type=_positive_int,
        default=DEFAULT_FAILURE_PERIOD,
        help="Deterministic synthetic numerical-failure injection period",
    )
    parser.add_argument(
        "--batch-size",
        type=_positive_int,
        default=DEFAULT_TRANSACTION_BATCH_SIZE,
        help="Maximum ReplayStep rows retained before each M00 transaction flush",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    bundle = None if args.no_m00_bundle else _available_bundle_path(args.bundle_output)
    report = run_streaming_validation(
        failure_period=args.failure_period,
        bundle_destination=bundle,
        bundle_batch_size=args.batch_size,
    )
    destination = write_streaming_validation_report(args.output, report)
    summary = {
        "validation_status": report["validation_status"],
        "plan_case_counts": [item["case_count"] for item in report["plans"]],
        "wall_time_seconds": report["wall_time_seconds"],
        "peak_rss_bytes": max(item["performance"]["peak_rss_bytes"] for item in report["plans"]),
        "m02_cache_bytes": report["bounded_memory"]["observed_m02_cache_bytes_max"],
        "report_json": destination.as_posix(),
        "report_json_bytes": destination.stat().st_size,
        "m00_bundle": None if bundle is None else bundle.as_posix(),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["validation_status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
