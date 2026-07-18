from __future__ import annotations

import ast
from pathlib import Path

import spine_sim.numerics as numerics

NUMERICS_ROOT = Path(__file__).parents[2] / "src" / "spine_sim" / "numerics"
VALIDATION_ONLY_MODULES = {
    "demo_validation_only.py",
    "m01_compatibility.py",
}


def imported_modules(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(item.name for item in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
    return tuple(modules)


def test_production_numerics_has_only_foundation_dependency_direction() -> None:
    forbidden = (
        "spine_sim.surface",
        "spine_sim.a",
        "spine_sim.b",
        "spine_sim.m03",
        "spine_sim.m04",
        "spine_sim.m05",
        "spine_sim.m06",
    )
    violations: list[str] = []
    for path in sorted(NUMERICS_ROOT.glob("*.py")):
        if path.name in VALIDATION_ONLY_MODULES:
            continue
        for module in imported_modules(path):
            if module.startswith(forbidden):
                violations.append(f"{path.name}: {module}")
    assert violations == []


def test_base_runtime_has_no_plotting_dependency() -> None:
    plotting = ("matplotlib", "seaborn", "plotly", "bokeh", "altair")
    violations: list[str] = []
    for path in sorted(NUMERICS_ROOT.glob("*.py")):
        for module in imported_modules(path):
            if module.startswith(plotting):
                violations.append(f"{path.name}: {module}")
    assert violations == []


def test_public_package_import_does_not_eagerly_import_surface_validation_harness() -> None:
    assert "NumericsService" in numerics.__all__
    assert "m01_compatibility" not in numerics.__all__
    assert "demo_validation_only" not in numerics.__all__


def test_m01_compatibility_module_is_explicit_validation_only_mock_owner() -> None:
    text = (NUMERICS_ROOT / "m01_compatibility.py").read_text(encoding="utf-8")
    assert text.startswith('"""VALIDATION_ONLY')
    assert "mock physical" in text
    assert "receipt IDs are\nnever part of a semantic comparison" in text
