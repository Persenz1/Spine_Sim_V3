#!/usr/bin/env python3
"""Run the M03 analytic surface/geometry validation suite as JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from spine_sim.foundation.storage import write_json_atomic
from spine_sim.single_spine.analytic_validation import (
    AnalyticValidationStatus,
    run_analytic_surface_validation_suite,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional machine-readable JSON destination; stdout is always emitted.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    suite = run_analytic_surface_validation_suite()
    payload = suite.to_dict()
    if args.output is not None:
        write_json_atomic(args.output, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if suite.status is AnalyticValidationStatus.PASSED else 1


if __name__ == "__main__":
    raise SystemExit(main())
