"""Manifest, marker, checksum, missing shard, and stale snapshot verification."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

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
    for marker_path, marker in markers:
        expected_marker_hash = semantic_hash(_marker_preimage(marker))
        if marker.get("commit_marker_hash") != expected_marker_hash:
            issues.append(
                IntegrityIssue(
                    "COMMIT_MARKER_HASH_MISMATCH",
                    marker_path.as_posix(),
                    "commit marker semantic hash mismatch",
                )
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
    report = IntegrityReport(mode, files_checked, len(markers), tuple(issues))
    if issues:
        raise IntegrityError(
            "bundle integrity verification failed",
            details={"issues": [dataclasses.asdict(issue) for issue in issues]},
        )
    return report


def build_integrity_index(root: Path) -> dict[str, Any]:
    markers = committed_markers(root)
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
        "receipt_set_hash": semantic_hash(sorted(marker["receipt_id"] for _, marker in markers)),
    }
