"""Manifest, marker, checksum, missing shard, and stale snapshot verification."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from .canonical import semantic_hash, source_file_hash
from .errors import IntegrityError
from .storage import read_json, tree_hash


class VerifyMode(StrEnum):
    NONE = "NONE"
    MANIFEST = "MANIFEST"
    FULL = "FULL"


@dataclass(frozen=True, slots=True)
class IntegrityIssue:
    code: str
    path: str
    message: str


@dataclass(frozen=True, slots=True)
class IntegrityReport:
    mode: VerifyMode
    files_checked: int
    markers_checked: int
    issues: tuple[IntegrityIssue, ...]

    @property
    def passed(self) -> bool:
        return not self.issues


def committed_markers(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    marker_root = root / "transactions" / "committed"
    if not marker_root.exists():
        return []
    return [(path, read_json(path)) for path in sorted(marker_root.glob("*.json"))]


def rejected_diagnostic_markers(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    marker_root = root / "rejected_trials" / "completed"
    if not marker_root.exists():
        return []
    return [(path, read_json(path)) for path in sorted(marker_root.glob("*.json"))]


def _marker_preimage(marker: dict[str, Any]) -> dict[str, Any]:
    return {
        "receipt_id": marker["receipt_id"],
        "case_id": marker["case_id"],
        "candidate_hash": marker["candidate_hash"],
        "paths": sorted(
            [entry["path"] for entry in marker.get("datasets", {}).values()]
            + [entry["path"] for entry in marker.get("arrays", {}).values()]
        ),
    }


def _rejected_diagnostic_marker_preimage(marker: dict[str, Any]) -> dict[str, Any]:
    return {
        "diagnostic_group_id": marker["diagnostic_group_id"],
        "case_id": marker["case_id"],
        "trial_id": marker["trial_id"],
        "paths": sorted(entry["path"] for entry in marker.get("datasets", {}).values()),
    }


def _marker_content_hash(marker: dict[str, Any]) -> str:
    """Recreate the frozen writer's marker content preimage."""

    return semantic_hash(
        {
            "datasets": {
                key: value["semantic_hash"]
                for key, value in sorted(marker.get("datasets", {}).items())
            },
            "arrays": {
                key: value["semantic_hash"]
                for key, value in sorted(marker.get("arrays", {}).items())
            },
        }
    )


def _diagnostic_content_hash(marker: dict[str, Any]) -> str:
    return semantic_hash(
        {key: value["semantic_hash"] for key, value in sorted(marker.get("datasets", {}).items())}
    )


def _issue(issues: list[IntegrityIssue], code: str, path: Path, message: str) -> None:
    issues.append(IntegrityIssue(code, path.as_posix(), message))


def verify_bundle(root: str | Path, mode: VerifyMode = VerifyMode.MANIFEST) -> IntegrityReport:
    bundle = Path(root)
    issues: list[IntegrityIssue] = []
    files_checked = 0
    manifest_path = bundle / "bundle_manifest.json"
    registry_path = bundle / "schemas" / "registry.json"
    if not manifest_path.exists():
        raise IntegrityError("missing bundle manifest", details={"code": "MISSING_BUNDLE_MANIFEST"})
    manifest = read_json(manifest_path)
    if mode is VerifyMode.NONE:
        return IntegrityReport(mode, 0, 0, ())
    if not registry_path.exists():
        issues.append(
            IntegrityIssue(
                "MISSING_REGISTRY_SNAPSHOT",
                registry_path.as_posix(),
                "registry snapshot is missing",
            )
        )
    else:
        registry = read_json(registry_path)
        registry_hash = registry.pop("registry_hash", None)
        computed = semantic_hash(registry)
        files_checked += 1
        if registry_hash != computed or manifest.get("registry_hash") != computed:
            issues.append(
                IntegrityIssue(
                    "STALE_MANIFEST",
                    registry_path.as_posix(),
                    "registry hash does not match bundle manifest",
                )
            )
    markers = committed_markers(bundle)
    receipt_ids: list[str] = []
    for marker_path, marker in markers:
        try:
            expected_marker_hash = semantic_hash(_marker_preimage(marker))
            receipt_ids.append(marker["receipt_id"])
        except (KeyError, TypeError) as error:
            _issue(
                issues,
                "MALFORMED_COMMIT_MARKER",
                marker_path,
                f"commit marker is missing its frozen preimage fields: {error}",
            )
            continue
        if marker.get("commit_marker_hash") != expected_marker_hash:
            issues.append(
                IntegrityIssue(
                    "COMMIT_MARKER_HASH_MISMATCH",
                    marker_path.as_posix(),
                    "commit marker semantic hash mismatch",
                )
            )
        try:
            expected_content_hash = _marker_content_hash(marker)
        except (KeyError, TypeError) as error:
            _issue(
                issues,
                "MALFORMED_COMMIT_MARKER",
                marker_path,
                f"commit marker has malformed semantic shard metadata: {error}",
            )
            expected_content_hash = None
        if (
            expected_content_hash is not None
            and marker.get("semantic_content_hash") != expected_content_hash
        ):
            _issue(
                issues,
                "COMMIT_MARKER_CONTENT_HASH_MISMATCH",
                marker_path,
                "commit marker semantic content hash mismatch",
            )

        receipt_entry = marker.get("datasets", {}).get("core.transactions.receipts")
        if receipt_entry is None:
            _issue(
                issues,
                "MISSING_RECEIPT_ENTRY",
                marker_path,
                "commit marker does not reference its authoritative receipt shard",
            )
        else:
            receipt_path = bundle / receipt_entry.get("path", "")
            if receipt_path.exists():
                try:
                    receipt_rows = pq.read_table(
                        receipt_path,
                        columns=[
                            "receipt_id",
                            "idempotency_key",
                            "parent_state_id",
                            "committed_state_id",
                            "candidate_hash",
                            "ordered_intents_hash",
                            "commit_marker_hash",
                        ],
                    ).to_pylist()
                    expected_receipt = {
                        "receipt_id": marker.get("receipt_id"),
                        "idempotency_key": marker.get("idempotency_key"),
                        "parent_state_id": marker.get("parent_state_id"),
                        "committed_state_id": marker.get("committed_state_id"),
                        "candidate_hash": marker.get("candidate_hash"),
                        "ordered_intents_hash": marker.get("ordered_intents_hash"),
                        "commit_marker_hash": marker.get("commit_marker_hash"),
                    }
                    if len(receipt_rows) != 1 or receipt_rows[0] != expected_receipt:
                        _issue(
                            issues,
                            "COMMIT_MARKER_RECEIPT_MISMATCH",
                            marker_path,
                            "commit marker identity does not match its authoritative receipt",
                        )
                except Exception as error:
                    _issue(
                        issues,
                        "MALFORMED_RECEIPT_SHARD",
                        receipt_path,
                        f"authoritative receipt shard cannot be read: {error}",
                    )
        for entry in list(marker.get("datasets", {}).values()) + list(
            marker.get("arrays", {}).values()
        ):
            target = bundle / entry["path"]
            if not target.exists():
                issues.append(
                    IntegrityIssue(
                        "MISSING_SHARD", target.as_posix(), "referenced immutable shard is missing"
                    )
                )
                continue
            files_checked += 1
            if mode is VerifyMode.FULL:
                if target.is_dir():
                    actual = tree_hash(target)
                    expected = entry.get("tree_sha256")
                else:
                    actual = source_file_hash(target)
                    expected = entry.get("byte_sha256")
                if actual != expected:
                    issues.append(
                        IntegrityIssue(
                            "CHECKSUM_MISMATCH",
                            target.as_posix(),
                            "stored checksum does not match content",
                        )
                    )
    for marker_path, marker in rejected_diagnostic_markers(bundle):
        expected_marker_hash = semantic_hash(_rejected_diagnostic_marker_preimage(marker))
        if marker.get("completion_marker_hash") != expected_marker_hash:
            issues.append(
                IntegrityIssue(
                    "REJECTED_COMPLETION_MARKER_HASH_MISMATCH",
                    marker_path.as_posix(),
                    "rejected diagnostic completion marker semantic hash mismatch",
                )
            )
        try:
            expected_content_hash = _diagnostic_content_hash(marker)
        except (KeyError, TypeError) as error:
            _issue(
                issues,
                "MALFORMED_REJECTED_DIAGNOSTIC_MARKER",
                marker_path,
                f"rejected diagnostic marker has malformed shard metadata: {error}",
            )
            expected_content_hash = None
        if (
            expected_content_hash is not None
            and marker.get("semantic_content_hash") != expected_content_hash
        ):
            _issue(
                issues,
                "REJECTED_DIAGNOSTIC_CONTENT_HASH_MISMATCH",
                marker_path,
                "rejected diagnostic semantic content hash mismatch",
            )
        if (
            marker.get("accepted_state_advanced") is not False
            or marker.get("committed_event_id") is not None
            or marker.get("commit_receipt_id") is not None
        ):
            issues.append(
                IntegrityIssue(
                    "REJECTED_DIAGNOSTIC_IDENTITY_VIOLATION",
                    marker_path.as_posix(),
                    "rejected diagnostic marker cannot advance or own accepted identities",
                )
            )
    for entries in manifest.get("auxiliary_datasets", {}).values():
        for entry in entries:
            target = bundle / entry["path"]
            if not target.exists():
                issues.append(
                    IntegrityIssue(
                        "MISSING_SHARD", target.as_posix(), "referenced auxiliary shard is missing"
                    )
                )
                continue
            files_checked += 1
            if mode is VerifyMode.FULL and source_file_hash(target) != entry.get("byte_sha256"):
                issues.append(
                    IntegrityIssue(
                        "CHECKSUM_MISMATCH",
                        target.as_posix(),
                        "auxiliary checksum does not match content",
                    )
                )

    computed_receipt_set_hash = semantic_hash(sorted(receipt_ids))
    manifest_receipt_set_hash = manifest.get("receipt_set_hash")
    if manifest_receipt_set_hash is None:
        _issue(
            issues,
            "MISSING_RECEIPT_SET_HASH",
            manifest_path,
            "bundle manifest is missing receipt_set_hash",
        )
    elif manifest_receipt_set_hash != computed_receipt_set_hash:
        _issue(
            issues,
            "RECEIPT_SET_HASH_MISMATCH",
            manifest_path,
            "bundle manifest receipt set does not match committed markers",
        )

    migration_path = bundle / "provenance" / "migration_lineage.json"
    try:
        if migration_path.exists():
            migration = read_json(migration_path)
            computed_bundle_hash = semantic_hash(
                {
                    "migrated_from": migration["source_bundle_semantic_hash"],
                    "registry_hash": manifest["registry_hash"],
                    "target_bundle_schema_version": manifest["bundle_schema_version"],
                    "adapter_id": migration["adapter_id"],
                    "adapter_version": migration["adapter_version"],
                }
            )
            if migration.get("target_bundle_schema_version") != manifest.get(
                "bundle_schema_version"
            ) or migration.get("target_bundle_semantic_hash") != manifest.get(
                "bundle_semantic_hash"
            ):
                _issue(
                    issues,
                    "MIGRATION_LINEAGE_MISMATCH",
                    migration_path,
                    "migration lineage does not match the migrated bundle manifest",
                )
        else:
            computed_bundle_hash = semantic_hash(
                {
                    "run_fingerprint": manifest["run_fingerprint"],
                    "registry_hash": manifest["registry_hash"],
                    "config_hash": manifest["resolved_run_config_hash"],
                    "receipt_candidates": sorted(
                        (marker["candidate_hash"], marker["semantic_content_hash"])
                        for _, marker in markers
                    ),
                    "cases": sorted(manifest["case_ids"]),
                }
            )
    except (KeyError, TypeError) as error:
        _issue(
            issues,
            "MALFORMED_BUNDLE_HASH_PREIMAGE",
            manifest_path,
            f"bundle manifest is missing frozen semantic preimage fields: {error}",
        )
    else:
        if manifest.get("bundle_semantic_hash") is None:
            _issue(
                issues,
                "MISSING_BUNDLE_SEMANTIC_HASH",
                manifest_path,
                "bundle manifest is missing bundle_semantic_hash",
            )
        elif manifest["bundle_semantic_hash"] != computed_bundle_hash:
            _issue(
                issues,
                "BUNDLE_SEMANTIC_HASH_MISMATCH",
                manifest_path,
                "bundle semantic hash does not match the frozen writer preimage",
            )

    integrity_path = bundle / "integrity" / "index.json"
    if not integrity_path.exists():
        _issue(
            issues,
            "MISSING_INTEGRITY_INDEX",
            integrity_path,
            "published bundle integrity index is missing",
        )
    else:
        try:
            stored_integrity = read_json(integrity_path)
            expected_integrity = build_integrity_index(bundle)
            frozen_fields = (
                "integrity_schema_version",
                "markers",
                "diagnostic_markers",
                "receipt_set_hash",
                "diagnostic_group_set_hash",
            )
            if any(
                stored_integrity.get(field) != expected_integrity[field] for field in frozen_fields
            ):
                _issue(
                    issues,
                    "INTEGRITY_INDEX_MISMATCH",
                    integrity_path,
                    "integrity index does not match published marker sets",
                )
            files_checked += 1
        except Exception as error:
            _issue(
                issues,
                "MALFORMED_INTEGRITY_INDEX",
                integrity_path,
                f"integrity index cannot be verified: {error}",
            )
    report = IntegrityReport(mode, files_checked, len(markers), tuple(issues))
    if issues:
        raise IntegrityError(
            "bundle integrity verification failed",
            details={"issues": [dataclasses.asdict(issue) for issue in issues]},
        )
    return report


def build_integrity_index(root: Path) -> dict[str, Any]:
    markers = committed_markers(root)
    diagnostic_markers = rejected_diagnostic_markers(root)
    return {
        "integrity_schema_version": "1.0.0",
        "markers": [
            {
                "path": path.relative_to(root).as_posix(),
                "receipt_id": marker["receipt_id"],
                "commit_marker_hash": marker["commit_marker_hash"],
            }
            for path, marker in markers
        ],
        "diagnostic_markers": [
            {
                "path": path.relative_to(root).as_posix(),
                "diagnostic_group_id": marker["diagnostic_group_id"],
                "completion_marker_hash": marker["completion_marker_hash"],
            }
            for path, marker in diagnostic_markers
        ],
        "receipt_set_hash": semantic_hash(sorted(marker["receipt_id"] for _, marker in markers)),
        "diagnostic_group_set_hash": semantic_hash(
            sorted(marker["diagnostic_group_id"] for _, marker in diagnostic_markers)
        ),
    }
