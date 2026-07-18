"""Low-level lossless JSON, Parquet, Zarr v3, and checksum helpers."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import zarr

from .canonical import (
    canonical_array_manifest,
    canonical_json_bytes,
    semantic_hash,
    sha256_bytes,
    source_file_hash,
)
from .errors import ContractViolation


def safe_component(value: str) -> str:
    if not value or value in {".", ".."} or any(char in value for char in "/\\\x00"):
        raise ContractViolation("unsafe path component", details={"value": value})
    return value


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_bytes(canonical_json_bytes(value) + b"\n")
    os.replace(temporary, path)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractViolation(f"expected JSON object: {path}")
    return value


def records_semantic_hash(records: list[dict[str, Any]]) -> str:
    return semantic_hash(records)


def write_parquet_records(
    path: Path,
    records: list[dict[str, Any]],
    *,
    compression: str = "zstd",
    row_group_size: int | None = None,
) -> dict[str, Any]:
    if not records:
        raise ValueError("cannot write an empty parquet shard")
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(records)
    pq.write_table(
        table,
        path,
        compression=compression,
        use_dictionary=True,
        write_statistics=True,
        row_group_size=row_group_size,
        data_page_version="2.0",
    )
    return {
        "path": path.as_posix(),
        "byte_sha256": source_file_hash(path),
        "semantic_hash": records_semantic_hash(records),
        "row_count": len(records),
        "storage_format": "parquet",
        "compression": compression,
    }


def _zarr_codecs(compression_level: int) -> tuple[list[Any], list[Any]]:
    """Return Zarr v3 serializers/compressors using lossless shuffle+zstd+CRC32C."""

    try:
        from zarr.codecs import BloscCodec, BloscShuffle, Crc32cCodec

        compressors = [
            BloscCodec(cname="zstd", clevel=compression_level, shuffle=BloscShuffle.shuffle),
            Crc32cCodec(),
        ]
        return [], compressors
    except (ImportError, AttributeError):
        return [], []


def write_zarr_array(
    path: Path,
    data: np.ndarray[Any, Any],
    *,
    validity: np.ndarray[Any, Any] | None,
    status: np.ndarray[Any, Any] | None,
    chunks: tuple[int, ...],
    compression_level: int,
) -> dict[str, Any]:
    materialized = np.asarray(data)
    if materialized.dtype.kind == "f":
        materialized = materialized.astype(np.float64, copy=False)
        if not np.isfinite(materialized).all():
            raise ContractViolation("canonical arrays cannot contain NaN/Inf")
    if validity is not None and np.asarray(validity).shape != materialized.shape:
        raise ContractViolation("validity array shape mismatch")
    if status is not None and np.asarray(status).shape != materialized.shape:
        raise ContractViolation("status array shape mismatch")
    path.parent.mkdir(parents=True, exist_ok=True)
    serializers, compressors = _zarr_codecs(compression_level)
    group = zarr.open_group(path, mode="w", zarr_format=3)
    kwargs: dict[str, Any] = {"chunks": chunks, "overwrite": True}
    if serializers:
        kwargs["serializers"] = serializers
    if compressors:
        kwargs["compressors"] = compressors
    group.create_array("values", data=materialized, **kwargs)
    if validity is not None:
        group.create_array(
            "validity", data=np.asarray(validity, dtype=np.bool_), chunks=chunks, overwrite=True
        )
    if status is not None:
        group.create_array("status", data=np.asarray(status), chunks=chunks, overwrite=True)
    group.attrs["canonical_numeric_dtype"] = str(materialized.dtype)
    group.attrs["zarr_format"] = 3
    manifest = canonical_array_manifest(materialized)
    return {
        "path": path.as_posix(),
        "tree_sha256": tree_hash(path),
        "semantic_hash": semantic_hash(
            {
                "values": manifest,
                "validity": canonical_array_manifest(np.asarray(validity, dtype=np.bool_))
                if validity is not None
                else None,
                "status": canonical_array_manifest(np.asarray(status))
                if status is not None
                else None,
            }
        ),
        "shape": list(materialized.shape),
        "dtype": str(materialized.dtype),
        "chunks": list(chunks),
        "storage_format": "zarr-v3",
        "compression": "blosc-zstd-shuffle-crc32c" if compressors else "zarr-v3-default-lossless",
    }


def tree_hash(path: Path) -> str:
    entries: list[dict[str, str]] = []
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        entries.append(
            {"path": child.relative_to(path).as_posix(), "sha256": source_file_hash(child)}
        )
    return sha256_bytes(canonical_json_bytes(entries))


def remove_owned_path(path: Path, *, root: Path) -> None:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if root_resolved not in resolved.parents:
        raise ContractViolation(
            "refusing to remove path outside bundle", details={"path": str(path)}
        )
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def relative_entry(entry: dict[str, Any], root: Path) -> dict[str, Any]:
    output = dict(entry)
    output["path"] = Path(entry["path"]).relative_to(root).as_posix()
    return output
