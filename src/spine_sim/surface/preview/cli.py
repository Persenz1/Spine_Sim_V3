"""Command-line rendering of already-saved M01 visualization fields."""

from __future__ import annotations

import argparse
from pathlib import Path

from spine_sim.foundation import ResultReader

from .recipes import HEIGHT_MAP_2D, OBLIQUE_3D_SURFACE, render_preview, sample_from_result_reader


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("case_id")
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--recipe", choices=(HEIGHT_MAP_2D, OBLIQUE_3D_SURFACE), default=HEIGHT_MAP_2D
    )
    parser.add_argument("--title-label", default="synthetic unidentified")
    parser.add_argument("--vertical-exaggeration", type=float, default=1.0)
    args = parser.parse_args(argv)
    reader = ResultReader.open(args.bundle)
    sample = sample_from_result_reader(reader, args.case_id)
    render_preview(
        sample,
        args.recipe,
        args.output,
        title_label=args.title_label,
        vertical_exaggeration=args.vertical_exaggeration,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
