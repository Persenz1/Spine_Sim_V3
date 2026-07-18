"""BITWISE/SEMANTIC replay manifests and structured difference reports."""

from __future__ import annotations

import dataclasses
import platform
import sys
from dataclasses import dataclass
from enum import StrEnum
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

from .canonical import HASH_PROFILE_ID, HASH_PROFILE_VERSION, semantic_hash
from .integrity import committed_markers
from .storage import read_json

NON_SEMANTIC_REPLAY_FIELDS = frozenset({"run_id", "created_at_utc_ns"})


class ReplayMode(StrEnum):
    BITWISE_REPLAY = "BITWISE_REPLAY"
    SEMANTIC_REPLAY = "SEMANTIC_REPLAY"


@dataclass(frozen=True, slots=True)
class ReplayManifest:
    replay_manifest_id: str
    run_id: str
    run_fingerprint: str
    result_api_version: str
    bundle_schema_version: str
    hash_profile_id: str
    hash_profile_version: str
    resolved_run_config_hash: str
    resolved_case_config_hashes: dict[str, str]
    source_hashes: dict[str, str]
    semantic_input_hashes: dict[str, str]
    git_commit: str
    dirty_status: str
    solver_build_id: str
    model_contract_versions: tuple[str, ...]
    registry_hash: str
    unit_frame_reference_transform_hash: str
    boundary_manifest_hash: str
    rng_algorithm_version: str
    root_seeds: tuple[int, ...]
    stream_namespaces: tuple[str, ...]
    reduction_order: str
    surface_identities: tuple[str, ...]
    python_runtime: str
    os_architecture: str
    dependency_versions: dict[str, str]
    numerical_backend: str
    thread_and_float_settings: dict[str, Any]
    parent_receipt_chain_hash: str
    idempotency_keys: tuple[str, ...]
    case_execution_plan: tuple[str, ...]
    determinism_profile: str
    field_tolerances: dict[str, float]
    diagnostic_level: str

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def runtime_dependency_versions(
    names: tuple[str, ...] = ("numpy", "pyarrow", "zarr"),
) -> dict[str, str]:
    output: dict[str, str] = {}
    for name in names:
        try:
            output[name] = version(name)
        except PackageNotFoundError:
            output[name] = "UNAVAILABLE"
    return output


def make_replay_manifest(
    *,
    run_id: str,
    run_fingerprint: str,
    result_api_version: str,
    bundle_schema_version: str,
    resolved_run_config_hash: str,
    resolved_case_config_hashes: dict[str, str],
    source_hashes: dict[str, str],
    registry_hash: str,
    git_commit: str,
    dirty_status: str,
    case_execution_plan: tuple[str, ...],
    idempotency_keys: tuple[str, ...],
    root_seeds: tuple[int, ...] = (),
    stream_namespaces: tuple[str, ...] = (),
    surface_identities: tuple[str, ...] = (),
    field_tolerances: dict[str, float] | None = None,
) -> ReplayManifest:
    content = {
        "run_fingerprint": run_fingerprint,
        "config": resolved_run_config_hash,
        "cases": resolved_case_config_hashes,
        "source": source_hashes,
        "registry": registry_hash,
        "plan": case_execution_plan,
        "idempotency": idempotency_keys,
    }
    replay_id = f"replay:{semantic_hash(content)}"
    return ReplayManifest(
        replay_manifest_id=replay_id,
        run_id=run_id,
        run_fingerprint=run_fingerprint,
        result_api_version=result_api_version,
        bundle_schema_version=bundle_schema_version,
        hash_profile_id=HASH_PROFILE_ID,
        hash_profile_version=HASH_PROFILE_VERSION,
        resolved_run_config_hash=resolved_run_config_hash,
        resolved_case_config_hashes=resolved_case_config_hashes,
        source_hashes=source_hashes,
        semantic_input_hashes={"inputs": semantic_hash(content)},
        git_commit=git_commit,
        dirty_status=dirty_status,
        solver_build_id="M00_FOUNDATION_NO_SOLVER",
        model_contract_versions=("M00_FOUNDATION_REQUIREMENTS 1.0.0",),
        registry_hash=registry_hash,
        unit_frame_reference_transform_hash=semantic_hash("N-mm-MPa/no-physical-frame"),
        boundary_manifest_hash=semantic_hash("M00_VALIDATION_ONLY_NO_PHYSICAL_BOUNDARY"),
        rng_algorithm_version="NO_RNG" if not root_seeds else "caller-declared",
        root_seeds=root_seeds,
        stream_namespaces=stream_namespaces,
        reduction_order="case_id_then_record_primary_key",
        surface_identities=surface_identities,
        python_runtime=sys.version,
        os_architecture=f"{platform.system()}-{platform.release()}-{platform.machine()}",
        dependency_versions=runtime_dependency_versions(),
        numerical_backend="NONE_M00_FOUNDATION",
        thread_and_float_settings={
            "canonical_numeric_dtype": "float64",
            "case_reduction_order": "sorted",
        },
        parent_receipt_chain_hash=semantic_hash(()),
        idempotency_keys=idempotency_keys,
        case_execution_plan=case_execution_plan,
        determinism_profile="M00_DETERMINISTIC_IO_1.0.0",
        field_tolerances=field_tolerances or {},
        diagnostic_level="summary",
    )


@dataclass(frozen=True, slots=True)
class ReplayDifference:
    code: str
    scope: str
    left: Any
    right: Any
    tolerance: float | None
    explanation: str


@dataclass(frozen=True, slots=True)
class ReplayDifferenceReport:
    mode: ReplayMode
    left_bundle: str
    right_bundle: str
    left_bundle_semantic_hash: str
    right_bundle_semantic_hash: str
    compared_receipts: int
    compared_datasets: int
    differences: tuple[ReplayDifference, ...]

    @property
    def equivalent(self) -> bool:
        return not self.differences


def compare_replay(
    left_bundle: str | Path,
    right_bundle: str | Path,
    *,
    mode: ReplayMode,
    field_tolerances: dict[str, float] | None = None,
) -> ReplayDifferenceReport:
    left_root, right_root = Path(left_bundle), Path(right_bundle)
    left_manifest = read_json(left_root / "bundle_manifest.json")
    right_manifest = read_json(right_root / "bundle_manifest.json")
    differences: list[ReplayDifference] = []
    left_markers = {item["receipt_id"]: item for _, item in committed_markers(left_root)}
    right_markers = {item["receipt_id"]: item for _, item in committed_markers(right_root)}
    if set(left_markers) != set(right_markers):
        differences.append(
            ReplayDifference(
                "RECEIPT_SET_MISMATCH",
                "receipts",
                sorted(left_markers),
                sorted(right_markers),
                None,
                "semantic receipt identities differ",
            )
        )
    compared_datasets = 0
    tolerances = field_tolerances or {}
    for receipt_id in sorted(set(left_markers) & set(right_markers)):
        left_marker, right_marker = left_markers[receipt_id], right_markers[receipt_id]
        if mode is ReplayMode.BITWISE_REPLAY:
            for key in (
                "candidate_hash",
                "semantic_content_hash",
                "committed_state_id",
                "commit_marker_hash",
            ):
                if left_marker[key] != right_marker[key]:
                    differences.append(
                        ReplayDifference(
                            "BITWISE_IDENTITY_MISMATCH",
                            f"{receipt_id}.{key}",
                            left_marker[key],
                            right_marker[key],
                            None,
                            "bitwise replay requires identical semantic identity",
                        )
                    )
        dataset_ids = set(left_marker["datasets"]) | set(right_marker["datasets"])
        for dataset_id in sorted(dataset_ids):
            compared_datasets += 1
            left_entry = left_marker["datasets"].get(dataset_id)
            right_entry = right_marker["datasets"].get(dataset_id)
            if left_entry is None or right_entry is None:
                differences.append(
                    ReplayDifference(
                        "DATASET_PRESENCE_MISMATCH",
                        dataset_id,
                        left_entry is not None,
                        right_entry is not None,
                        None,
                        "dataset is present on only one side",
                    )
                )
                continue
            if mode is ReplayMode.BITWISE_REPLAY:
                if left_entry["semantic_hash"] != right_entry["semantic_hash"]:
                    differences.append(
                        ReplayDifference(
                            "DATASET_SEMANTIC_HASH_MISMATCH",
                            dataset_id,
                            left_entry["semantic_hash"],
                            right_entry["semantic_hash"],
                            None,
                            "canonical rows differ",
                        )
                    )
            else:
                _compare_tables(
                    left_root / left_entry["path"],
                    right_root / right_entry["path"],
                    dataset_id,
                    tolerances,
                    differences,
                )
        for field_id in sorted(
            set(left_marker.get("arrays", {})) | set(right_marker.get("arrays", {}))
        ):
            left_entry = left_marker.get("arrays", {}).get(field_id)
            right_entry = right_marker.get("arrays", {}).get(field_id)
            if (
                left_entry is None
                or right_entry is None
                or left_entry["semantic_hash"] != right_entry["semantic_hash"]
            ):
                differences.append(
                    ReplayDifference(
                        "ARRAY_SEMANTIC_MISMATCH",
                        field_id,
                        left_entry,
                        right_entry,
                        tolerances.get(field_id),
                        "array canonical values/validity/status differ",
                    )
                )
    return ReplayDifferenceReport(
        mode,
        left_root.as_posix(),
        right_root.as_posix(),
        left_manifest["bundle_semantic_hash"],
        right_manifest["bundle_semantic_hash"],
        len(set(left_markers) & set(right_markers)),
        compared_datasets,
        tuple(differences),
    )


def _compare_tables(
    left_path: Path,
    right_path: Path,
    dataset_id: str,
    tolerances: dict[str, float],
    differences: list[ReplayDifference],
) -> None:
    left = pq.read_table(left_path)
    right = pq.read_table(right_path)
    if left.schema.names != right.schema.names or left.num_rows != right.num_rows:
        differences.append(
            ReplayDifference(
                "TABLE_SHAPE_OR_SCHEMA_MISMATCH",
                dataset_id,
                {"schema": left.schema.names, "rows": left.num_rows},
                {"schema": right.schema.names, "rows": right.num_rows},
                None,
                "semantic replay requires compatible columns and row count",
            )
        )
        return
    for name in left.schema.names:
        if name in NON_SEMANTIC_REPLAY_FIELDS:
            continue
        left_values = left[name].to_pylist()
        right_values = right[name].to_pylist()
        tolerance = tolerances.get(f"{dataset_id}.{name}", 0.0)
        for index, (left_value, right_value) in enumerate(
            zip(left_values, right_values, strict=True)
        ):
            if isinstance(left_value, float) and isinstance(right_value, float):
                equal = bool(np.isclose(left_value, right_value, atol=tolerance, rtol=tolerance))
            else:
                equal = left_value == right_value
            if not equal:
                differences.append(
                    ReplayDifference(
                        "FIELD_VALUE_MISMATCH",
                        f"{dataset_id}.{name}[{index}]",
                        left_value,
                        right_value,
                        tolerance,
                        "value differs outside the versioned field tolerance",
                    )
                )
                break
