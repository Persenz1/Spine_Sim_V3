"""Canonical semantic forms, stable identities, and byte hashes."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import secrets
import time
import uuid
from collections.abc import Mapping, Sequence
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from .errors import ContractViolation

HASH_ALGORITHM = "SHA-256"
HASH_PROFILE_ID = "spine-sim-canonical-json"
HASH_PROFILE_VERSION = "1.0.0"


def _canonical_value(value: Any) -> Any:
    if value is None or isinstance(value, str | int | bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractViolation("NaN/Inf cannot enter canonical semantic content")
        if value == 0.0:
            return 0.0
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, np.generic):
        return _canonical_value(value.item())
    if isinstance(value, np.ndarray):
        return canonical_array_manifest(value)
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, tuple | list):
        return [_canonical_value(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if dataclasses.is_dataclass(value):
        return _canonical_value(dataclasses.asdict(value))  # type: ignore[arg-type]
    raise ContractViolation(
        f"unsupported canonical value type: {type(value).__name__}",
        details={"type": type(value).__name__},
    )


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON for semantic hashing."""

    return json.dumps(
        _canonical_value(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def semantic_hash(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def source_file_hash(path: str | Path, *, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def stable_content_id(kind: str, value: Any) -> str:
    return f"{kind}:{semantic_hash({'kind': kind, 'content': value})}"


def canonical_array_bytes(array: np.ndarray[Any, Any]) -> bytes:
    """Canonical little-endian, C-order array bytes without storage layout metadata."""

    materialized = np.asarray(array)
    if materialized.dtype.kind == "f" and not np.isfinite(materialized).all():
        raise ContractViolation("canonical arrays cannot contain NaN/Inf")
    little_dtype = materialized.dtype.newbyteorder("<")
    return np.ascontiguousarray(materialized.astype(little_dtype, copy=False)).tobytes(order="C")


def canonical_array_manifest(array: np.ndarray[Any, Any]) -> dict[str, Any]:
    materialized = np.asarray(array)
    little_dtype = materialized.dtype.newbyteorder("<")
    return {
        "dtype": little_dtype.str,
        "shape": list(materialized.shape),
        "endianness": "little",
        "content_sha256": sha256_bytes(canonical_array_bytes(materialized)),
    }


def uuid7(*, timestamp_ms: int | None = None, randomness: int | None = None) -> uuid.UUID:
    """Generate an RFC 9562 UUIDv7 without depending on Python 3.14."""

    ts = int(time.time_ns() // 1_000_000 if timestamp_ms is None else timestamp_ms)
    if not 0 <= ts < 1 << 48:
        raise ValueError("UUIDv7 timestamp must fit in 48 bits")
    random_bits = secrets.randbits(74) if randomness is None else randomness
    if not 0 <= random_bits < 1 << 74:
        raise ValueError("UUIDv7 randomness must fit in 74 bits")
    rand_a = random_bits >> 62
    rand_b = random_bits & ((1 << 62) - 1)
    value = (ts << 80) | (0x7 << 76) | (rand_a << 64) | (0b10 << 62) | rand_b
    return uuid.UUID(int=value)


class ShortIdRegistry:
    """Collision-check display prefixes while preserving full hashes."""

    def __init__(self, prefix_length: int = 12) -> None:
        if prefix_length < 4:
            raise ValueError("prefix_length must be at least 4")
        self.prefix_length = prefix_length
        self._prefixes: dict[str, str] = {}

    def register(self, full_hash: str) -> str:
        prefix = full_hash[: self.prefix_length]
        existing = self._prefixes.get(prefix)
        if existing is not None and existing != full_hash:
            raise ContractViolation(
                "short ID collision",
                details={"prefix": prefix, "existing": existing, "incoming": full_hash},
            )
        self._prefixes[prefix] = full_hash
        return prefix


def semantic_manifest_hash(items: Sequence[Mapping[str, Any]]) -> str:
    return semantic_hash(
        sorted((_canonical_value(item) for item in items), key=canonical_json_bytes)
    )
