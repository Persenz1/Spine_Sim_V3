from __future__ import annotations

import ast
import inspect
import re
import tomllib
from pathlib import Path

from spine_sim.foundation.demo_validation_only import validation_extension
from spine_sim.foundation.reader import ResultReader
from spine_sim.foundation.registry import SchemaRegistry
from spine_sim.foundation.writer import ResultWriter

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "src/spine_sim/foundation"


def test_readme_dataset_and_field_ids_exist_in_registry() -> None:
    registry = SchemaRegistry()
    registry.register_extension(validation_extension())
    registry.freeze()
    readme = (PACKAGE_ROOT / "README.md").read_text()
    identifiers = set(re.findall(r"`((?:core|validation_m00)\.[a-zA-Z0-9_.]+)`", readme))
    known = set(registry.datasets) | set(registry.arrays)
    assert identifiers
    assert identifiers <= known


def test_readme_has_output_overview_and_validation_labels() -> None:
    text = (PACKAGE_ROOT / "README.md").read_text()
    assert "## 输出概览" in text
    assert "VALIDATION_ONLY" in text
    assert "not_certifiable" in text
    assert "ResultReader" in text


def test_readme_local_links_resolve() -> None:
    readme_path = PACKAGE_ROOT / "README.md"
    links = re.findall(r"\[[^]]+\]\(([^)]+)\)", readme_path.read_text())
    local_links = [item for item in links if "://" not in item and not item.startswith("#")]
    assert local_links
    assert all(
        (readme_path.parent / item.split("#", 1)[0]).resolve().exists() for item in local_links
    )


def test_foundation_has_no_future_physics_or_plotting_imports() -> None:
    forbidden_prefixes = (
        "spine_sim.surface",
        "spine_sim.numerics",
        "spine_sim.single_spine",
        "spine_sim.array",
        "spine_sim.plotting",
        "matplotlib",
        "plotly",
    )
    for path in PACKAGE_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(
                name.startswith(prefix) for name in names for prefix in forbidden_prefixes
            ), (path, names)


def test_reader_does_not_import_writer_or_solver_boundaries() -> None:
    tree = ast.parse((PACKAGE_ROOT / "reader.py").read_text())
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert "writer" not in imports
    assert not any("solver" in name or "surface" in name or "plotting" in name for name in imports)


def test_public_consumer_can_use_reader_without_storage_dependencies(demo_bundle: Path) -> None:
    from spine_sim.foundation import ChunkedArrayView, DatasetCatalog, QueryResult, ResultReader

    reader = ResultReader.open(demo_bundle)
    assert reader.bundle_info()["bundle_kind"] == "spine-result"
    assert DatasetCatalog and QueryResult and ChunkedArrayView


def test_frozen_public_api_signatures_and_strong_writer_boundary() -> None:
    writer_methods = {
        "create_run_bundle",
        "register_extension_schema",
        "write_resolved_config_and_provenance",
        "create_case_shard",
        "begin_transaction",
        "record_rejected_trial",
        "write_versioned_summary",
        "finalize_case",
        "publish_run_manifest",
        "recover_crash_artifacts",
    }
    reader_methods = {
        "open",
        "bundle_info",
        "list_datasets",
        "list_fields",
        "describe_fields",
        "list_relations",
        "query",
        "series",
        "events",
        "open_array",
        "resolve_lineage",
        "check_plot_requirements",
        "build_plot_data_gap_request",
    }
    assert writer_methods <= set(dir(ResultWriter))
    assert reader_methods <= set(dir(ResultReader))
    assert "write_dict" not in dir(ResultWriter)
    assert tuple(inspect.signature(ResultReader.open).parameters) == ("bundle_uri", "verify_mode")
    assert "include_diagnostics" in inspect.signature(ResultReader.query).parameters


def test_foundation_base_runtime_has_no_plotting_dependency() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    base_dependencies = tuple(item.lower() for item in project["project"]["dependencies"])
    assert not any("matplotlib" in item or "plotly" in item for item in base_dependencies)
    preview_dependencies = tuple(
        item.lower() for item in project["project"]["optional-dependencies"]["preview"]
    )
    assert any("matplotlib" in item for item in preview_dependencies)
