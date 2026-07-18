from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SURFACE_ROOT = REPO_ROOT / "src/spine_sim/surface"


def test_surface_evaluator_does_not_reverse_import_preview_or_future_modules() -> None:
    forbidden = (
        "matplotlib",
        "plotly",
        "spine_sim.surface.preview",
        "spine_sim.numerics",
        "spine_sim.single_spine",
        "spine_sim.array",
        "spine_sim.plotting",
    )
    for path in SURFACE_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names = (node.module or "",)
            else:
                continue
            assert not any(name.startswith(prefix) for name in names for prefix in forbidden), (
                path,
                names,
            )


def test_base_surface_import_does_not_load_matplotlib() -> None:
    command = (
        "import sys; import spine_sim.foundation; import spine_sim.surface; "
        "assert not any(k == 'matplotlib' or k.startswith('matplotlib.') for k in sys.modules)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
