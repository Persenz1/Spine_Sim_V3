"""SemVer compatibility decisions, read-time adapters, and explicit migration lineage."""

from __future__ import annotations

import dataclasses
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging.version import Version

from .canonical import semantic_hash
from .errors import CompatibilityError
from .storage import read_json, write_json_atomic


@dataclass(frozen=True, slots=True)
class CompatibilityDecision:
    status: str
    readable: bool
    partial: bool
    migration_required: bool
    explanation: str


def assess_compatibility(reader_version: str, bundle_version: str) -> CompatibilityDecision:
    reader = Version(reader_version)
    bundle = Version(bundle_version)
    if reader.major != bundle.major:
        return CompatibilityDecision(
            "BREAKING_SCHEMA_UNSUPPORTED",
            False,
            False,
            True,
            "major versions differ; only minimal manifest metadata is safe to read",
        )
    if bundle.minor > reader.minor:
        return CompatibilityDecision(
            "PARTIAL_SCHEMA_SUPPORT",
            True,
            True,
            False,
            "older reader may expose only fields it knows",
        )
    if bundle.minor < reader.minor:
        return CompatibilityDecision(
            "READ_TIME_ADAPTER_ACTIVE",
            True,
            False,
            False,
            "new optional fields remain NULL+UNAVAILABLE when absent from the old bundle",
        )
    return CompatibilityDecision(
        "FULL_SCHEMA_SUPPORT", True, False, False, "same major/minor schema"
    )


@dataclass(frozen=True, slots=True)
class MissingFieldAdapter:
    field_id: str
    introduced_version: str
    reason_code: str = "FIELD_NOT_PRESENT_IN_SCHEMA_VERSION"

    def adapt_row(self, row: dict[str, Any], *, bundle_version: str) -> dict[str, Any]:
        if Version(bundle_version) < Version(self.introduced_version):
            name = self.field_id.rsplit(".", 1)[-1]
            row = dict(row)
            row[name] = None
            row[f"{name}__status"] = {
                "value_presence": "NULL",
                "capability_status": "UNAVAILABLE",
                "reason_code": self.reason_code,
            }
        return row


@dataclass(frozen=True, slots=True)
class MigrationLineage:
    adapter_id: str
    adapter_version: str
    source_bundle_uri: str
    source_bundle_semantic_hash: str
    source_bundle_schema_version: str
    target_bundle_schema_version: str
    target_bundle_semantic_hash: str
    migrated_at_utc_ns: int
    in_place: bool = False


def migrate_manifest_only(
    source: str | Path,
    destination: str | Path,
    *,
    target_bundle_schema_version: str,
    adapter_id: str,
    adapter_version: str,
) -> MigrationLineage:
    """Copy an additive-compatible bundle and record lineage; never modify the source."""

    source_path = Path(source)
    target_path = Path(destination)
    if source_path.resolve() == target_path.resolve():
        raise CompatibilityError("in-place migration is forbidden")
    if target_path.exists():
        raise FileExistsError(target_path)
    manifest = read_json(source_path / "bundle_manifest.json")
    decision = assess_compatibility(target_bundle_schema_version, manifest["bundle_schema_version"])
    if (
        not decision.readable
        or Version(target_bundle_schema_version).major
        != Version(manifest["bundle_schema_version"]).major
    ):
        raise CompatibilityError("manifest-only adapter cannot cross a breaking major version")
    shutil.copytree(source_path, target_path)
    registry_path = target_path / "schemas" / "registry.json"
    registry = read_json(registry_path)
    registry.pop("registry_hash", None)
    registry["bundle_schema_version"] = target_bundle_schema_version
    registry_hash = semantic_hash(registry)
    registry["registry_hash"] = registry_hash
    write_json_atomic(registry_path, registry)
    old_hash = manifest["bundle_semantic_hash"]
    manifest["bundle_schema_version"] = target_bundle_schema_version
    manifest["registry_hash"] = registry_hash
    manifest["bundle_semantic_hash"] = semantic_hash(
        {
            "migrated_from": old_hash,
            "registry_hash": registry_hash,
            "target_bundle_schema_version": target_bundle_schema_version,
            "adapter_id": adapter_id,
            "adapter_version": adapter_version,
        }
    )
    lineage = MigrationLineage(
        adapter_id=adapter_id,
        adapter_version=adapter_version,
        source_bundle_uri=source_path.as_posix(),
        source_bundle_semantic_hash=old_hash,
        source_bundle_schema_version=read_json(source_path / "bundle_manifest.json")[
            "bundle_schema_version"
        ],
        target_bundle_schema_version=target_bundle_schema_version,
        target_bundle_semantic_hash=manifest["bundle_semantic_hash"],
        migrated_at_utc_ns=time.time_ns(),
    )
    write_json_atomic(target_path / "bundle_manifest.json", manifest)
    write_json_atomic(
        target_path / "provenance" / "migration_lineage.json", dataclasses.asdict(lineage)
    )
    return lineage
