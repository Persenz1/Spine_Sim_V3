"""Lazy, coordinate-anchored materialization for M01 surfaces.

This module deliberately has no plotting dependency.  A materialized tile is a
deletable view of a :class:`~spine_sim.surface.contracts.SurfaceRealization`; it
is never part of that realization's semantic identity.  Tile coordinates are
anchored to the logical parent domain so enlarging an active footprint cannot
change values in its overlap with an earlier footprint.
"""

from __future__ import annotations

import inspect
import json
import math
import os
import tempfile
import threading
from collections import OrderedDict
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import numpy as np
from numpy.typing import ArrayLike, NDArray

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation

from .contracts import (
    MAXIMUM_DRAG_PATH_MM,
    QUERY_CONTRACT_VERSION,
    Domain2D,
    M01ReasonCode,
    MaterializationReceipt,
    QueryFootprint,
    VisualizationSample,
    make_visualization_sample,
)

MATERIALIZATION_METHOD_ID = "M01_COORDINATE_ANCHORED_TILE"
MATERIALIZATION_METHOD_VERSION = "1.0.0"
VISUALIZATION_LOW_PASS_METHOD = "M01_DISPLAY_NYQUIST_BANDLIMIT_1"

DEFAULT_TILE_CORE_SHAPE = (256, 256)
DEFAULT_TILE_HALO_SAMPLES = 16
DEFAULT_MEMORY_CACHE_BUDGET_MIB = 512.0
DEFAULT_DISK_CACHE_BUDGET_MIB = 2048.0
MIB = 1024 * 1024

# This public audit marker is intentionally a constant, rather than an
# inference from current cache contents.  Neither TileMaterializer nor the
# visualization sampler has an API that constructs a full-parent Rt/10 array.
NORMAL_PATH_BUILDS_FULL_DOMAIN_RT10_DENSE = False


class ActiveFootprintDomainError(ContractViolation):
    """A swept footprint would leave the 150 x 150 mm logical parent."""

    code = M01ReasonCode.ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN.value


class LODLevel(IntEnum):
    """Frozen tip-local spacing levels; the integer is the Rt divisor."""

    RT_OVER_5 = 5
    RT_OVER_8 = 8
    RT_OVER_10 = 10

    @property
    def label(self) -> str:
        return f"Rt/{int(self)}"

    @property
    def active_bands(self) -> tuple[int, ...]:
        if self is LODLevel.RT_OVER_5:
            return (0,)
        if self is LODLevel.RT_OVER_8:
            return (0, 1)
        return (0, 1, 2)

    def spacing_mm(self, reference_rt_mm: float) -> float:
        reference = _positive_finite(reference_rt_mm, "reference_rt_mm")
        return reference / int(self)


# Readable aliases for callers that use the requirement terminology.
MaterializationLOD = LODLevel
LOD_RT_OVER_5 = LODLevel.RT_OVER_5
LOD_RT_OVER_8 = LODLevel.RT_OVER_8
LOD_RT_OVER_10 = LODLevel.RT_OVER_10


@dataclass(frozen=True, slots=True)
class FootprintGuard:
    """Components of the frozen max-envelope guard rule, in millimetres."""

    probe_radius_mm: float = 0.0
    trusted_scale_halo_mm: float = 0.0
    derivative_search_halo_mm: float = 0.0
    tile_halo_mm: float = 0.0
    declared_clearance_guard_mm: float = 0.0

    def __post_init__(self) -> None:
        for name in (
            "probe_radius_mm",
            "trusted_scale_halo_mm",
            "derivative_search_halo_mm",
            "tile_halo_mm",
            "declared_clearance_guard_mm",
        ):
            _nonnegative_finite(getattr(self, name), name)

    @property
    def effective_mm(self) -> float:
        return max(
            self.probe_radius_mm,
            self.trusted_scale_halo_mm,
            self.derivative_search_halo_mm,
            self.tile_halo_mm,
            self.declared_clearance_guard_mm,
        )


def derive_query_footprint(
    swept_points_mm: ArrayLike | None = None,
    guard_mm: float | FootprintGuard = 0.0,
    logical_domain: Domain2D | None = None,
    *,
    path_points_mm: ArrayLike | None = None,
    geometry_offsets_mm: ArrayLike | None = None,
    maximum_path_length_mm: float | None = MAXIMUM_DRAG_PATH_MM,
    derivation_method: str = "M01_SWEPT_GEOMETRY_AABB_MAX_GUARD_1",
) -> QueryFootprint:
    """Derive an active AABB from swept points or a path and geometry offsets.

    ``swept_points_mm`` represents an already swept point set.  Alternatively,
    ``path_points_mm`` may be combined with one or more local
    ``geometry_offsets_mm``; the envelope of their Minkowski sum is used without
    allocating the Cartesian product.  The guard is applied on every side, so
    both path endpoints receive it.

    A footprint outside ``logical_domain`` is rejected.  It is never wrapped,
    clamped, cropped, or shortened.
    """

    domain = logical_domain if logical_domain is not None else Domain2D()
    if swept_points_mm is not None and path_points_mm is not None:
        raise ContractViolation(
            "provide either swept_points_mm or path_points_mm, not both",
            details={"reason_code": M01ReasonCode.INVALID_SURFACE_SPEC.value},
        )
    if swept_points_mm is None and path_points_mm is None:
        raise ContractViolation("a swept point set or path is required")
    if not isinstance(derivation_method, str) or not derivation_method.strip():
        raise ContractViolation("derivation_method must be a non-empty string")

    guard = guard_mm.effective_mm if isinstance(guard_mm, FootprintGuard) else guard_mm
    guard = _nonnegative_finite(guard, "guard_mm")

    if swept_points_mm is not None:
        if geometry_offsets_mm is not None:
            raise ContractViolation("geometry_offsets_mm is only valid with path_points_mm")
        swept = _points_2d(swept_points_mm, "swept_points_mm")
        x_min = float(np.min(swept[:, 0]))
        x_max = float(np.max(swept[:, 0]))
        y_min = float(np.min(swept[:, 1]))
        y_max = float(np.max(swept[:, 1]))
        swept_hash_payload: dict[str, Any] = {"swept_points_mm": swept}
    else:
        path = _points_2d(path_points_mm, "path_points_mm")
        if maximum_path_length_mm is not None:
            maximum_length = _positive_finite(maximum_path_length_mm, "maximum_path_length_mm")
            path_length = _polyline_length(path)
            tolerance = max(1.0e-12, maximum_length * 1.0e-12)
            if path_length > maximum_length + tolerance:
                raise ContractViolation(
                    "swept path exceeds the frozen maximum drag path",
                    details={
                        "reason_code": M01ReasonCode.INVALID_SURFACE_SPEC.value,
                        "path_length_mm": path_length,
                        "maximum_path_length_mm": maximum_length,
                    },
                )
        offsets = (
            np.zeros((1, 2), dtype=np.float64)
            if geometry_offsets_mm is None
            else _points_2d(geometry_offsets_mm, "geometry_offsets_mm")
        )
        x_min = float(np.min(path[:, 0]) + np.min(offsets[:, 0]))
        x_max = float(np.max(path[:, 0]) + np.max(offsets[:, 0]))
        y_min = float(np.min(path[:, 1]) + np.min(offsets[:, 1]))
        y_max = float(np.max(path[:, 1]) + np.max(offsets[:, 1]))
        swept_hash_payload = {
            "path_points_mm": path,
            "geometry_offsets_mm": offsets,
        }

    bounds = (x_min - guard, x_max + guard, y_min - guard, y_max + guard)
    if bounds[1] <= bounds[0] or bounds[3] <= bounds[2]:
        raise ContractViolation("the swept envelope plus guard must have positive x and y extents")

    swept_geometry_hash = semantic_hash(swept_hash_payload)
    preimage = {
        "bounds": bounds,
        "swept_geometry_hash": swept_geometry_hash,
        "guard_mm": guard,
        "derivation_method": derivation_method,
    }
    footprint = QueryFootprint(
        footprint_id=stable_content_id("query_footprint", preimage),
        x_min_mm=bounds[0],
        x_max_mm=bounds[1],
        y_min_mm=bounds[2],
        y_max_mm=bounds[3],
        swept_geometry_hash=swept_geometry_hash,
        guard_mm=guard,
        derivation_method=derivation_method,
    )
    if not footprint.inside(domain):
        raise ActiveFootprintDomainError(
            "active query footprint exceeds the logical parent domain",
            details={
                "reason_code": M01ReasonCode.ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN.value,
                "requested_bounds_mm": bounds,
                "logical_domain_mm": (
                    domain.x_min_mm,
                    domain.x_max_mm,
                    domain.y_min_mm,
                    domain.y_max_mm,
                ),
                "policy": "reject_without_wrap_clamp_crop_or_path_shortening",
            },
        )
    return footprint


@runtime_checkable
class SurfaceEvaluator(Protocol):
    """Minimal evaluator used by tile and visualization materialization.

    Implementations should accept same-shaped coordinate arrays.  ``q_max`` is
    an angular spatial-frequency cutoff in rad/mm.  The optional low-pass method
    is passed when the implementation declares that argument (or ``**kwargs``).
    A plain height array, ``(height, validity)`` pair, mapping, or object with a
    ``height_mm`` attribute is accepted as the return value.
    """

    surface_realization_id: str

    def evaluate(
        self,
        x_mm: NDArray[np.float64],
        y_mm: NDArray[np.float64],
        derivative_order: int = 0,
        q_max_rad_per_mm: float | None = None,
        low_pass_method: str | None = None,
    ) -> Any: ...


@dataclass(frozen=True, slots=True)
class MaterializationConfig:
    """Numerical/cache policy; none of these fields changes surface identity."""

    core_shape: tuple[int, int] = DEFAULT_TILE_CORE_SHAPE
    halo_samples: int = DEFAULT_TILE_HALO_SAMPLES
    memory_cache_budget_mib: float = DEFAULT_MEMORY_CACHE_BUDGET_MIB
    disk_cache_enabled: bool = False
    disk_cache_directory: Path | str | None = None
    disk_cache_budget_mib: float = DEFAULT_DISK_CACHE_BUDGET_MIB

    def __post_init__(self) -> None:
        _shape_2d(self.core_shape, "core_shape")
        if isinstance(self.halo_samples, bool) or not isinstance(self.halo_samples, int):
            raise ContractViolation("halo_samples must be an integer")
        if self.halo_samples < 0:
            raise ContractViolation("halo_samples cannot be negative")
        _positive_finite(self.memory_cache_budget_mib, "memory_cache_budget_mib")
        _positive_finite(self.disk_cache_budget_mib, "disk_cache_budget_mib")
        if self.disk_cache_enabled and self.disk_cache_directory is None:
            raise ContractViolation(
                "disk_cache_directory is required when persistent tile cache is enabled"
            )

    @property
    def memory_cache_budget_bytes(self) -> int:
        return int(self.memory_cache_budget_mib * MIB)

    @property
    def disk_cache_budget_bytes(self) -> int:
        return int(self.disk_cache_budget_mib * MIB)


@dataclass(frozen=True, slots=True)
class TileCacheKey:
    """Content-addressed identity of one coordinate-anchored tile request."""

    surface_realization_id: str
    generator_version: str
    query_contract_version: str
    materialization_method_version: str
    lod: int
    active_bands: tuple[int, ...]
    tile_coordinate: tuple[int, int]
    core_shape: tuple[int, int]
    halo_samples: int
    spacing_mm: float
    q_max_rad_per_mm: float
    fields: tuple[str, ...] = ("height_mm", "validity")
    dtype: str = "<f8"
    cache_key_id: str = field(init=False)

    def __post_init__(self) -> None:
        for name in (
            "surface_realization_id",
            "generator_version",
            "query_contract_version",
            "materialization_method_version",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ContractViolation(f"{name} must be a non-empty string")
        lod = _coerce_lod(self.lod)
        object.__setattr__(self, "lod", int(lod))
        _tile_coordinate(self.tile_coordinate)
        _shape_2d(self.core_shape, "core_shape")
        if isinstance(self.halo_samples, bool) or not isinstance(self.halo_samples, int):
            raise ContractViolation("halo_samples must be an integer")
        if self.halo_samples < 0:
            raise ContractViolation("halo_samples cannot be negative")
        _positive_finite(self.spacing_mm, "spacing_mm")
        _positive_finite(self.q_max_rad_per_mm, "q_max_rad_per_mm")
        if self.active_bands != tuple(sorted(set(self.active_bands))):
            raise ContractViolation("active_bands must be unique and sorted")
        if any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in self.active_bands
        ):
            raise ContractViolation("active_bands must contain non-negative integers")
        if not self.fields or self.fields != tuple(sorted(set(self.fields))):
            raise ContractViolation("fields must be non-empty, unique, and sorted")
        dtype = np.dtype(self.dtype)
        if dtype != np.dtype("<f8"):
            raise ContractViolation("M01 canonical tile height dtype must be little-endian float64")
        object.__setattr__(self, "dtype", "<f8")
        object.__setattr__(
            self,
            "cache_key_id",
            stable_content_id("surface_tile_cache_key", self.identity_preimage()),
        )

    def identity_preimage(self) -> dict[str, Any]:
        return {
            "surface_realization_id": self.surface_realization_id,
            "generator_version": self.generator_version,
            "query_contract_version": self.query_contract_version,
            "materialization_method_version": self.materialization_method_version,
            "lod": self.lod,
            "active_bands": self.active_bands,
            "tile_coordinate": self.tile_coordinate,
            "core_shape": self.core_shape,
            "halo_samples": self.halo_samples,
            "spacing_mm": self.spacing_mm,
            "q_max_rad_per_mm": self.q_max_rad_per_mm,
            "fields": self.fields,
            "dtype": self.dtype,
        }


# A shorter public spelling is convenient without multiplying implementations.
TileKey = TileCacheKey


@dataclass(frozen=True, slots=True)
class TilePayload:
    """Immutable tile payload including halo and an integrity digest."""

    key: TileCacheKey
    x_coordinates_mm: NDArray[np.float64]
    y_coordinates_mm: NDArray[np.float64]
    height_mm: NDArray[np.float64]
    validity: NDArray[np.bool_]
    content_hash: str = field(init=False)
    payload_bytes: int = field(init=False)

    def __post_init__(self) -> None:
        x = np.array(self.x_coordinates_mm, dtype="<f8", order="C", copy=True)
        y = np.array(self.y_coordinates_mm, dtype="<f8", order="C", copy=True)
        height = np.array(self.height_mm, dtype="<f8", order="C", copy=True)
        validity = np.array(self.validity, dtype=np.bool_, order="C", copy=True)
        ny, nx = self.key.core_shape
        expected_shape = (
            ny + 2 * self.key.halo_samples,
            nx + 2 * self.key.halo_samples,
        )
        if x.shape != (expected_shape[1],) or y.shape != (expected_shape[0],):
            raise ContractViolation("tile coordinate vector shape does not match core plus halo")
        if height.shape != expected_shape or validity.shape != expected_shape:
            raise ContractViolation("tile height/validity shape does not match core plus halo")
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ContractViolation("tile coordinates must be finite")
        if not np.isfinite(height).all():
            raise ContractViolation("tile payload cannot encode invalid values as NaN/Inf")
        for array in (x, y, height, validity):
            array.setflags(write=False)
        object.__setattr__(self, "x_coordinates_mm", x)
        object.__setattr__(self, "y_coordinates_mm", y)
        object.__setattr__(self, "height_mm", height)
        object.__setattr__(self, "validity", validity)
        object.__setattr__(self, "content_hash", self._calculate_content_hash())
        object.__setattr__(
            self,
            "payload_bytes",
            int(x.nbytes + y.nbytes + height.nbytes + validity.nbytes),
        )

    def _calculate_content_hash(self) -> str:
        return semantic_hash(
            {
                "cache_key_id": self.key.cache_key_id,
                "x_coordinates_mm": self.x_coordinates_mm,
                "y_coordinates_mm": self.y_coordinates_mm,
                "height_mm": self.height_mm,
                "validity": self.validity,
            }
        )

    def verify_integrity(self) -> bool:
        """Return whether metadata, arrays, and stored digest still agree."""

        try:
            if self.key.cache_key_id != stable_content_id(
                "surface_tile_cache_key", self.key.identity_preimage()
            ):
                return False
            return self.content_hash == self._calculate_content_hash()
        except (ContractViolation, TypeError, ValueError):
            return False


class CacheStatus(StrEnum):
    MEMORY_HIT = "MEMORY_HIT"
    DISK_HIT = "DISK_HIT"
    MISS_GENERATED = "MISS_GENERATED"
    GENERATED_NOT_CACHED = "GENERATED_NOT_CACHED"
    CORRUPTION_REGENERATED = "CORRUPTION_REGENERATED"


@dataclass(frozen=True, slots=True)
class CacheLookup:
    payload: TilePayload
    cache_status: CacheStatus
    reason_code: str


@dataclass(frozen=True, slots=True)
class TileCacheStats:
    tile_requests: int
    memory_hits: int
    disk_hits: int
    cache_misses: int
    generated_tiles: int
    regenerated_tiles: int
    corruption_events: int
    evicted_tiles: int
    oversized_tiles_not_cached: int
    disk_writes: int
    resident_tiles: int
    memory_payload_bytes: int
    memory_budget_bytes: int
    disk_cache_enabled: bool
    full_domain_rt10_dense_created: bool = False

    @property
    def cache_hits(self) -> int:
        return self.memory_hits + self.disk_hits

    @property
    def hit_count(self) -> int:
        return self.cache_hits

    @property
    def miss_count(self) -> int:
        return self.cache_misses

    @property
    def regeneration_count(self) -> int:
        return self.regenerated_tiles

    @property
    def payload_within_budget(self) -> bool:
        return self.memory_payload_bytes <= self.memory_budget_bytes


@dataclass(slots=True)
class _MemoryEntry:
    key: TileCacheKey
    payload: TilePayload


class ContentAddressedTileCache:
    """Thread-safe, bounded LRU cache with optional non-canonical disk storage."""

    is_canonical = False

    def __init__(
        self,
        memory_budget_bytes: int = int(DEFAULT_MEMORY_CACHE_BUDGET_MIB * MIB),
        *,
        disk_cache_enabled: bool = False,
        disk_cache_directory: Path | str | None = None,
        disk_budget_bytes: int = int(DEFAULT_DISK_CACHE_BUDGET_MIB * MIB),
    ) -> None:
        if isinstance(memory_budget_bytes, bool) or not isinstance(memory_budget_bytes, int):
            raise ContractViolation("memory_budget_bytes must be an integer")
        if memory_budget_bytes <= 0:
            raise ContractViolation("memory_budget_bytes must be positive")
        if isinstance(disk_budget_bytes, bool) or not isinstance(disk_budget_bytes, int):
            raise ContractViolation("disk_budget_bytes must be an integer")
        if disk_budget_bytes <= 0:
            raise ContractViolation("disk_budget_bytes must be positive")
        if disk_cache_enabled and disk_cache_directory is None:
            raise ContractViolation(
                "disk_cache_directory is required when persistent tile cache is enabled"
            )

        self.memory_budget_bytes = memory_budget_bytes
        self.disk_cache_enabled = bool(disk_cache_enabled)
        self.disk_budget_bytes = disk_budget_bytes
        self.disk_cache_directory = (
            Path(disk_cache_directory).expanduser().resolve()
            if disk_cache_directory is not None
            else None
        )
        if self.disk_cache_enabled:
            assert self.disk_cache_directory is not None
            self.disk_cache_directory.mkdir(parents=True, exist_ok=True)

        self._memory: OrderedDict[str, _MemoryEntry] = OrderedDict()
        self._memory_payload_bytes = 0
        self._lock = threading.RLock()
        self._tile_requests = 0
        self._memory_hits = 0
        self._disk_hits = 0
        self._cache_misses = 0
        self._generated_tiles = 0
        self._regenerated_tiles = 0
        self._corruption_events = 0
        self._evicted_tiles = 0
        self._oversized_tiles_not_cached = 0
        self._disk_writes = 0

    @classmethod
    def from_config(cls, config: MaterializationConfig) -> ContentAddressedTileCache:
        return cls(
            config.memory_cache_budget_bytes,
            disk_cache_enabled=config.disk_cache_enabled,
            disk_cache_directory=config.disk_cache_directory,
            disk_budget_bytes=config.disk_cache_budget_bytes,
        )

    @property
    def memory_payload_bytes(self) -> int:
        with self._lock:
            return self._memory_payload_bytes

    @property
    def stats(self) -> TileCacheStats:
        return self.stats_snapshot()

    def stats_snapshot(self) -> TileCacheStats:
        with self._lock:
            return TileCacheStats(
                tile_requests=self._tile_requests,
                memory_hits=self._memory_hits,
                disk_hits=self._disk_hits,
                cache_misses=self._cache_misses,
                generated_tiles=self._generated_tiles,
                regenerated_tiles=self._regenerated_tiles,
                corruption_events=self._corruption_events,
                evicted_tiles=self._evicted_tiles,
                oversized_tiles_not_cached=self._oversized_tiles_not_cached,
                disk_writes=self._disk_writes,
                resident_tiles=len(self._memory),
                memory_payload_bytes=self._memory_payload_bytes,
                memory_budget_bytes=self.memory_budget_bytes,
                disk_cache_enabled=self.disk_cache_enabled,
            )

    def get(self, key: TileCacheKey) -> TilePayload | None:
        """Look up a tile without generating it; integrity failures are misses."""

        with self._lock:
            self._tile_requests += 1
            payload, _, corrupted = self._lookup_locked(key)
            if payload is None:
                self._cache_misses += 1
                if corrupted:
                    self._corruption_events += 1
                return None
            return payload

    def put(self, key: TileCacheKey, payload: TilePayload) -> bool:
        """Insert a verified payload, returning whether it fits the memory LRU."""

        with self._lock:
            self._validate_payload_for_key(key, payload)
            stored = self._store_memory_locked(key, payload)
            if self.disk_cache_enabled:
                self._write_disk_locked(key, payload)
            return stored

    def get_or_create(
        self,
        key: TileCacheKey,
        factory: Callable[[], TilePayload],
    ) -> CacheLookup:
        """Return a verified tile, rebuilding a miss or corrupted cache entry."""

        # Generation is intentionally serialized under this lock.  It prevents
        # two threads from producing and accounting for the same key twice; the
        # evaluator remains responsible for coordinate-level determinism.
        with self._lock:
            self._tile_requests += 1
            payload, status, corrupted = self._lookup_locked(key)
            if payload is not None:
                return CacheLookup(payload, status, M01ReasonCode.OK.value)

            self._cache_misses += 1
            if corrupted:
                self._corruption_events += 1
            generated = factory()
            self._validate_payload_for_key(key, generated)
            self._generated_tiles += 1
            if corrupted:
                self._regenerated_tiles += 1
            stored = self._store_memory_locked(key, generated)
            if self.disk_cache_enabled:
                self._write_disk_locked(key, generated)

            if corrupted:
                generated_status = CacheStatus.CORRUPTION_REGENERATED
                reason = M01ReasonCode.CACHE_CORRUPTION_REGENERATED.value
            elif stored:
                generated_status = CacheStatus.MISS_GENERATED
                reason = M01ReasonCode.OK.value
            else:
                generated_status = CacheStatus.GENERATED_NOT_CACHED
                reason = M01ReasonCode.OK.value
            return CacheLookup(generated, generated_status, reason)

    def clear_memory(self) -> None:
        """Drop deletable memory entries without touching the optional disk cache."""

        with self._lock:
            self._memory.clear()
            self._memory_payload_bytes = 0

    def corrupt_memory_entry_for_testing(self, key: TileCacheKey) -> None:
        """Deterministically corrupt one resident byte for integrity regression tests."""

        with self._lock:
            entry = self._memory.get(key.cache_key_id)
            if entry is None:
                raise KeyError(key.cache_key_id)
            height = entry.payload.height_mm
            height.setflags(write=True)
            height.flat[0] = np.nextafter(height.flat[0], math.inf)
            height.setflags(write=False)

    def _lookup_locked(self, key: TileCacheKey) -> tuple[TilePayload | None, CacheStatus, bool]:
        corrupted = False
        entry = self._memory.get(key.cache_key_id)
        if entry is not None:
            if entry.key == key and entry.payload.verify_integrity():
                self._memory.move_to_end(key.cache_key_id)
                self._memory_hits += 1
                return entry.payload, CacheStatus.MEMORY_HIT, False
            self._discard_memory_locked(key.cache_key_id)
            corrupted = True

        if self.disk_cache_enabled:
            disk_payload, disk_corrupted = self._read_disk_locked(key)
            corrupted = corrupted or disk_corrupted
            if disk_payload is not None:
                self._disk_hits += 1
                self._store_memory_locked(key, disk_payload)
                return disk_payload, CacheStatus.DISK_HIT, corrupted
        return None, CacheStatus.MISS_GENERATED, corrupted

    def _validate_payload_for_key(self, key: TileCacheKey, payload: TilePayload) -> None:
        if payload.key != key or payload.key.cache_key_id != key.cache_key_id:
            raise ContractViolation("tile factory returned a payload for a different cache key")
        if not payload.verify_integrity():
            raise ContractViolation("tile factory returned a corrupt payload")

    def _store_memory_locked(self, key: TileCacheKey, payload: TilePayload) -> bool:
        existing = self._memory.pop(key.cache_key_id, None)
        if existing is not None:
            self._memory_payload_bytes -= existing.payload.payload_bytes
        if payload.payload_bytes > self.memory_budget_bytes:
            self._oversized_tiles_not_cached += 1
            return False
        while (
            self._memory
            and self._memory_payload_bytes + payload.payload_bytes > self.memory_budget_bytes
        ):
            _, evicted = self._memory.popitem(last=False)
            self._memory_payload_bytes -= evicted.payload.payload_bytes
            self._evicted_tiles += 1
        self._memory[key.cache_key_id] = _MemoryEntry(key, payload)
        self._memory_payload_bytes += payload.payload_bytes
        if self._memory_payload_bytes > self.memory_budget_bytes:  # defensive invariant
            raise ContractViolation("memory tile cache exceeded its configured payload budget")
        return True

    def _discard_memory_locked(self, key_id: str) -> None:
        entry = self._memory.pop(key_id, None)
        if entry is not None:
            self._memory_payload_bytes -= entry.payload.payload_bytes

    def _disk_path(self, key: TileCacheKey) -> Path:
        assert self.disk_cache_directory is not None
        digest = key.cache_key_id.rsplit(":", maxsplit=1)[-1]
        return self.disk_cache_directory / f"{digest}.npz"

    def _write_disk_locked(self, key: TileCacheKey, payload: TilePayload) -> None:
        path = self._disk_path(key)
        metadata = json.dumps(
            {
                "cache_key_id": key.cache_key_id,
                "content_hash": payload.content_hash,
                "format": "M01_TILE_NPZ_1",
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        assert self.disk_cache_directory is not None
        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w+b",
                prefix=".m01-tile-",
                suffix=".tmp",
                dir=self.disk_cache_directory,
                delete=False,
            ) as stream:
                temporary_name = stream.name
                np.savez(
                    stream,
                    x_coordinates_mm=payload.x_coordinates_mm,
                    y_coordinates_mm=payload.y_coordinates_mm,
                    height_mm=payload.height_mm,
                    validity=payload.validity.astype(np.uint8, copy=False),
                    metadata=np.frombuffer(metadata, dtype=np.uint8),
                )
                stream.flush()
                os.fsync(stream.fileno())
            Path(temporary_name).replace(path)
            temporary_name = None
            self._disk_writes += 1
            self._enforce_disk_budget_locked()
        finally:
            if temporary_name is not None:
                Path(temporary_name).unlink(missing_ok=True)

    def _read_disk_locked(self, key: TileCacheKey) -> tuple[TilePayload | None, bool]:
        path = self._disk_path(key)
        if not path.is_file():
            return None, False
        try:
            with np.load(path, allow_pickle=False) as archive:
                required = {
                    "x_coordinates_mm",
                    "y_coordinates_mm",
                    "height_mm",
                    "validity",
                    "metadata",
                }
                if set(archive.files) != required:
                    raise ValueError("unexpected disk tile members")
                metadata_bytes = np.asarray(archive["metadata"], dtype=np.uint8).tobytes()
                metadata = json.loads(metadata_bytes.decode("utf-8"))
                if (
                    metadata.get("format") != "M01_TILE_NPZ_1"
                    or metadata.get("cache_key_id") != key.cache_key_id
                ):
                    raise ValueError("disk tile key/format mismatch")
                payload = TilePayload(
                    key=key,
                    x_coordinates_mm=archive["x_coordinates_mm"],
                    y_coordinates_mm=archive["y_coordinates_mm"],
                    height_mm=archive["height_mm"],
                    validity=np.asarray(archive["validity"], dtype=np.bool_),
                )
                if metadata.get("content_hash") != payload.content_hash:
                    raise ValueError("disk tile content hash mismatch")
            os.utime(path, None)
            return payload, False
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            path.unlink(missing_ok=True)
            return None, True

    def _enforce_disk_budget_locked(self) -> None:
        assert self.disk_cache_directory is not None
        files = sorted(
            self.disk_cache_directory.glob("*.npz"),
            key=lambda item: (item.stat().st_mtime_ns, item.name),
        )
        total = sum(item.stat().st_size for item in files)
        for item in files:
            if total <= self.disk_budget_bytes:
                break
            size = item.stat().st_size
            item.unlink(missing_ok=True)
            total -= size


# Requirement-facing concise alias.
TileCache = ContentAddressedTileCache


@dataclass(frozen=True, slots=True)
class MaterializedTile:
    payload: TilePayload
    receipt: MaterializationReceipt

    @property
    def height_mm(self) -> NDArray[np.float64]:
        return self.payload.height_mm

    @property
    def validity(self) -> NDArray[np.bool_]:
        return self.payload.validity


class TileMaterializer:
    """Stream lazy tiles for one immutable realization."""

    normal_path_builds_full_domain_rt10_dense = False

    def __init__(
        self,
        evaluator: SurfaceEvaluator | Any,
        surface_realization_id: str | None = None,
        *,
        logical_domain: Domain2D | None = None,
        generator_version: str | None = None,
        query_contract_version: str = QUERY_CONTRACT_VERSION,
        config: MaterializationConfig | None = None,
        cache: ContentAddressedTileCache | None = None,
    ) -> None:
        self.evaluator = evaluator
        self.surface_realization_id = _resolve_realization_id(evaluator, surface_realization_id)
        self.logical_domain = logical_domain if logical_domain is not None else Domain2D()
        evaluator_spec = getattr(evaluator, "spec", None)
        inferred_generator_version = getattr(evaluator, "generator_version", None)
        if inferred_generator_version is None:
            inferred_generator_version = getattr(evaluator_spec, "generator_version", None)
        self.generator_version = generator_version or (
            inferred_generator_version
            if isinstance(inferred_generator_version, str) and inferred_generator_version
            else "unknown-evaluator-version"
        )
        if not query_contract_version:
            raise ContractViolation("query_contract_version must be a non-empty string")
        self.query_contract_version = query_contract_version
        self.config = config if config is not None else MaterializationConfig()
        self.cache = (
            cache if cache is not None else ContentAddressedTileCache.from_config(self.config)
        )

    @property
    def stats(self) -> TileCacheStats:
        return self.cache.stats

    def tile_coordinates_for_footprint(
        self,
        footprint: QueryFootprint,
        *,
        reference_rt_mm: float,
        lod: LODLevel | int = LODLevel.RT_OVER_5,
    ) -> tuple[tuple[int, int], ...]:
        self._validate_footprint(footprint)
        level = _coerce_lod(lod)
        spacing = level.spacing_mm(reference_rt_mm)
        return tile_coordinates_for_footprint(
            footprint,
            spacing_mm=spacing,
            core_shape=self.config.core_shape,
            logical_domain=self.logical_domain,
        )

    def sample_tile(
        self,
        footprint: QueryFootprint,
        tile_coordinate: tuple[int, int],
        *,
        reference_rt_mm: float,
        lod: LODLevel | int = LODLevel.RT_OVER_5,
        active_bands: Sequence[int] | None = None,
    ) -> MaterializedTile:
        """Materialize one core+halo tile through the canonical evaluator."""

        self._validate_footprint(footprint)
        coordinate = _tile_coordinate(tile_coordinate)
        level = _coerce_lod(lod)
        spacing = level.spacing_mm(reference_rt_mm)
        bands = level.active_bands if active_bands is None else _active_bands(active_bands)
        if not _tile_core_intersects_footprint(
            coordinate,
            footprint,
            spacing,
            self.config.core_shape,
            self.logical_domain,
        ):
            raise ContractViolation(
                "requested tile core does not intersect the active query footprint",
                details={"tile_coordinate": coordinate, "footprint_id": footprint.footprint_id},
            )

        q_max = math.pi / spacing
        key = TileCacheKey(
            surface_realization_id=self.surface_realization_id,
            generator_version=self.generator_version,
            query_contract_version=self.query_contract_version,
            materialization_method_version=MATERIALIZATION_METHOD_VERSION,
            lod=int(level),
            active_bands=bands,
            tile_coordinate=coordinate,
            core_shape=self.config.core_shape,
            halo_samples=self.config.halo_samples,
            spacing_mm=spacing,
            q_max_rad_per_mm=q_max,
            fields=("height_mm", "validity"),
        )
        lookup = self.cache.get_or_create(key, lambda: self._generate_tile(key))
        omitted_height, omitted_slope, bound_known = _omitted_band_bounds(self.evaluator, q_max)
        reason = lookup.reason_code
        if (
            reason == M01ReasonCode.OK.value
            and not bound_known
            and level is not LODLevel.RT_OVER_10
        ):
            reason = M01ReasonCode.RESOLUTION_REFINEMENT_REQUIRED.value

        receipt_preimage = {
            "surface_realization_id": self.surface_realization_id,
            "footprint_id": footprint.footprint_id,
            "tile_coordinate": coordinate,
            "lod": int(level),
            "active_bands": bands,
            "core_shape": self.config.core_shape,
            "halo_samples": self.config.halo_samples,
            "spacing_mm": spacing,
            "omitted_height_bound_mm": omitted_height,
            "omitted_slope_bound": omitted_slope,
            "content_hash": lookup.payload.content_hash,
            "cache_status": lookup.cache_status.value,
            "reason_code": reason,
            "payload_bytes": lookup.payload.payload_bytes,
        }
        receipt = MaterializationReceipt(
            receipt_id=stable_content_id("surface_materialization_receipt", receipt_preimage),
            surface_realization_id=self.surface_realization_id,
            footprint_id=footprint.footprint_id,
            tile_coordinate=coordinate,
            lod=int(level),
            active_bands=bands,
            core_shape=self.config.core_shape,
            halo_samples=self.config.halo_samples,
            spacing_mm=spacing,
            omitted_height_bound_mm=omitted_height,
            omitted_slope_bound=omitted_slope,
            content_hash=lookup.payload.content_hash,
            cache_status=lookup.cache_status.value,
            reason_code=reason,
            payload_bytes=lookup.payload.payload_bytes,
        )
        return MaterializedTile(lookup.payload, receipt)

    def iter_footprint_tiles(
        self,
        footprint: QueryFootprint,
        *,
        reference_rt_mm: float,
        lod: LODLevel | int = LODLevel.RT_OVER_5,
        active_bands: Sequence[int] | None = None,
    ) -> Iterator[MaterializedTile]:
        """Stream tiles in canonical y-major order without a full-domain array."""

        coordinates = self.tile_coordinates_for_footprint(
            footprint, reference_rt_mm=reference_rt_mm, lod=lod
        )
        for coordinate in coordinates:
            yield self.sample_tile(
                footprint,
                coordinate,
                reference_rt_mm=reference_rt_mm,
                lod=lod,
                active_bands=active_bands,
            )

    def sample_visualization_window(
        self,
        window_mm: tuple[float, float, float, float],
        grid_shape: tuple[int, int] = (1024, 1024),
        *,
        low_pass_method: str = VISUALIZATION_LOW_PASS_METHOD,
    ) -> VisualizationSample:
        return sample_visualization_window(
            self.evaluator,
            self.surface_realization_id,
            window_mm,
            grid_shape,
            logical_domain=self.logical_domain,
            low_pass_method=low_pass_method,
        )

    def _validate_footprint(self, footprint: QueryFootprint) -> None:
        if not isinstance(footprint, QueryFootprint):
            raise ContractViolation("footprint must be a QueryFootprint")
        if not footprint.inside(self.logical_domain):
            raise ActiveFootprintDomainError(
                "active query footprint exceeds the logical parent domain",
                details={
                    "reason_code": M01ReasonCode.ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN.value,
                    "footprint_id": footprint.footprint_id,
                },
            )

    def _generate_tile(self, key: TileCacheKey) -> TilePayload:
        ny, nx = key.core_shape
        halo = key.halo_samples
        tile_x, tile_y = key.tile_coordinate
        global_x_indices = tile_x * nx + np.arange(-halo, nx + halo, dtype=np.int64)
        global_y_indices = tile_y * ny + np.arange(-halo, ny + halo, dtype=np.int64)
        # Multiplication from global integer indices, rather than cumulative
        # addition, makes every shared coordinate bitwise identical.
        x = self.logical_domain.x_min_mm + global_x_indices.astype(np.float64) * key.spacing_mm
        y = self.logical_domain.y_min_mm + global_y_indices.astype(np.float64) * key.spacing_mm
        x_grid, y_grid = np.meshgrid(x, y, indexing="xy")
        validity = (
            (x_grid >= self.logical_domain.x_min_mm)
            & (x_grid <= self.logical_domain.x_max_mm)
            & (y_grid >= self.logical_domain.y_min_mm)
            & (y_grid <= self.logical_domain.y_max_mm)
        )
        height = np.zeros(x_grid.shape, dtype=np.float64)
        if np.any(validity):
            evaluated, evaluator_validity = _evaluate_height(
                self.evaluator,
                x_grid[validity],
                y_grid[validity],
                derivative_order=0,
                q_max_rad_per_mm=key.q_max_rad_per_mm,
                low_pass_method="M01_TILE_NYQUIST_BANDLIMIT_1",
            )
            height[validity] = evaluated
            combined = validity.copy()
            combined[validity] = evaluator_validity
            validity = combined
        return TilePayload(key, x, y, height, validity)


def tile_coordinates_for_footprint(
    footprint: QueryFootprint,
    *,
    spacing_mm: float,
    core_shape: tuple[int, int] = DEFAULT_TILE_CORE_SHAPE,
    logical_domain: Domain2D | None = None,
) -> tuple[tuple[int, int], ...]:
    """Return domain-anchored tile coordinates covering a footprint."""

    domain = logical_domain if logical_domain is not None else Domain2D()
    if not isinstance(footprint, QueryFootprint):
        raise ContractViolation("footprint must be a QueryFootprint")
    if not footprint.inside(domain):
        raise ActiveFootprintDomainError(
            "active query footprint exceeds the logical parent domain",
            details={
                "reason_code": M01ReasonCode.ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN.value,
                "footprint_id": footprint.footprint_id,
            },
        )
    spacing = _positive_finite(spacing_mm, "spacing_mm")
    ny, nx = _shape_2d(core_shape, "core_shape")
    tile_width = nx * spacing
    tile_height = ny * spacing
    x_first = max(0, math.floor((footprint.x_min_mm - domain.x_min_mm) / tile_width))
    x_last = max(0, math.floor((footprint.x_max_mm - domain.x_min_mm) / tile_width))
    y_first = max(0, math.floor((footprint.y_min_mm - domain.y_min_mm) / tile_height))
    y_last = max(0, math.floor((footprint.y_max_mm - domain.y_min_mm) / tile_height))
    return tuple(
        (tile_x, tile_y)
        for tile_y in range(y_first, y_last + 1)
        for tile_x in range(x_first, x_last + 1)
    )


def sample_visualization_window(
    evaluator: SurfaceEvaluator | Any,
    surface_realization_id: str | None = None,
    window_mm: tuple[float, float, float, float] = (0.0, 150.0, 0.0, 150.0),
    grid_shape: tuple[int, int] = (1024, 1024),
    *,
    logical_domain: Domain2D | None = None,
    low_pass_method: str = VISUALIZATION_LOW_PASS_METHOD,
) -> VisualizationSample:
    """Sample a public visualization grid at its display Nyquist cutoff.

    This is a visualization derivative, not solver geometry.  The evaluator is
    asked for an explicit low-pass cutoff before values are placed on the grid;
    no full-fine parent array is constructed or point-sampled.
    """

    realization_id = _resolve_realization_id(evaluator, surface_realization_id)
    domain = logical_domain if logical_domain is not None else Domain2D()
    ny, nx = _shape_2d(grid_shape, "grid_shape", minimum=2)
    window = _window(window_mm)
    if not (domain.contains(window[0], window[2]) and domain.contains(window[1], window[3])):
        raise ActiveFootprintDomainError(
            "visualization window exceeds the logical parent domain",
            details={
                "reason_code": M01ReasonCode.ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN.value,
                "window_mm": window,
            },
        )
    if not isinstance(low_pass_method, str) or not low_pass_method.strip():
        raise ContractViolation("low_pass_method must be a non-empty string")

    x = np.linspace(window[0], window[1], nx, dtype=np.float64)
    y = np.linspace(window[2], window[3], ny, dtype=np.float64)
    dx = (window[1] - window[0]) / (nx - 1)
    dy = (window[3] - window[2]) / (ny - 1)
    q_max = min(math.pi / dx, math.pi / dy)
    x_grid, y_grid = np.meshgrid(x, y, indexing="xy")
    height, validity = _evaluate_height(
        evaluator,
        x_grid,
        y_grid,
        derivative_order=0,
        q_max_rad_per_mm=q_max,
        low_pass_method=low_pass_method,
    )
    return make_visualization_sample(
        surface_realization_id=realization_id,
        window_mm=window,
        x_coordinates_mm=x,
        y_coordinates_mm=y,
        height_mm=height,
        validity=validity,
        visualization_q_max_rad_per_mm=q_max,
        low_pass_method=low_pass_method,
    )


def _evaluate_height(
    evaluator: Any,
    x_mm: NDArray[np.float64],
    y_mm: NDArray[np.float64],
    *,
    derivative_order: int,
    q_max_rad_per_mm: float,
    low_pass_method: str,
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    if x_mm.shape != y_mm.shape:
        raise ContractViolation("evaluator coordinate arrays must have the same shape")
    method = getattr(evaluator, "evaluate", None)
    if not callable(method):
        raise ContractViolation("surface evaluator must provide evaluate(x_mm, y_mm, ...)")

    result = _invoke_evaluator(
        method,
        x_mm,
        y_mm,
        derivative_order=derivative_order,
        q_max_rad_per_mm=q_max_rad_per_mm,
        low_pass_method=low_pass_method,
    )
    height_value: Any
    validity_value: Any | None = None
    if isinstance(result, np.ndarray):
        height_value = result
    elif isinstance(result, Mapping):
        height_value = _first_present(result, ("height_mm", "height", "values"))
        validity_value = _first_present_optional(
            result, ("validity", "validity_mask", "quality_mask")
        )
    elif isinstance(result, tuple) and len(result) == 2:
        height_value, validity_value = result
    else:
        height_value = _first_attribute(result, ("height_mm", "height", "values"))
        validity_value = _first_attribute_optional(
            result, ("validity", "validity_mask", "quality_mask")
        )

    declared_shape = _declared_evaluator_shape(result)
    height = np.asarray(height_value, dtype=np.float64)
    if (
        height.shape != x_mm.shape
        and height.ndim == 1
        and height.size == x_mm.size
        and declared_shape == x_mm.shape
    ):
        height = height.reshape(x_mm.shape)
    if height.shape != x_mm.shape:
        raise ContractViolation(
            "evaluator height shape must exactly preserve coordinate input shape",
            details={"expected_shape": x_mm.shape, "actual_shape": height.shape},
        )
    if not np.isfinite(height).all():
        raise ContractViolation("evaluator cannot encode missing height as NaN/Inf")
    validity: NDArray[np.bool_]
    if validity_value is None:
        validity = np.ones(height.shape, dtype=np.bool_)
    else:
        validity = np.asarray(validity_value, dtype=np.bool_)
        if (
            validity.shape != x_mm.shape
            and validity.ndim == 1
            and validity.size == x_mm.size
            and declared_shape == x_mm.shape
        ):
            validity = validity.reshape(x_mm.shape)
        if validity.shape != x_mm.shape:
            raise ContractViolation(
                "evaluator validity shape must exactly preserve coordinate input shape"
            )
    return np.array(height, dtype=np.float64, order="C", copy=True), np.array(
        validity, dtype=np.bool_, order="C", copy=True
    )


def _invoke_evaluator(
    method: Callable[..., Any],
    x_mm: NDArray[np.float64],
    y_mm: NDArray[np.float64],
    *,
    derivative_order: int,
    q_max_rad_per_mm: float,
    low_pass_method: str,
) -> Any:
    """Call standard evaluators without swallowing a TypeError from their body."""

    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        return method(x_mm, y_mm, derivative_order, q_max_rad_per_mm)

    parameters = signature.parameters
    has_var_keyword = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()
    )
    kwargs: dict[str, Any] = {}
    positional: list[Any] = [x_mm, y_mm]
    _bind_evaluator_option(
        parameters,
        has_var_keyword,
        positional,
        kwargs,
        ("derivative_order",),
        derivative_order,
        "derivative_order",
    )
    _bind_evaluator_option(
        parameters,
        has_var_keyword,
        positional,
        kwargs,
        ("q_max_rad_per_mm", "q_max"),
        q_max_rad_per_mm,
        "q_max_rad_per_mm",
    )
    _bind_evaluator_option(
        parameters,
        has_var_keyword,
        positional,
        kwargs,
        ("low_pass_method", "low_pass"),
        low_pass_method,
        "low_pass_method",
        optional=True,
    )
    return method(*positional, **kwargs)


def _bind_evaluator_option(
    parameters: Mapping[str, inspect.Parameter],
    has_var_keyword: bool,
    positional: list[Any],
    kwargs: dict[str, Any],
    candidate_names: tuple[str, ...],
    value: Any,
    canonical_name: str,
    *,
    optional: bool = False,
) -> None:
    parameter = next((parameters[name] for name in candidate_names if name in parameters), None)
    if parameter is not None:
        if parameter.kind is inspect.Parameter.POSITIONAL_ONLY:
            positional.append(value)
        else:
            kwargs[parameter.name] = value
    elif has_var_keyword:
        kwargs[canonical_name] = value
    elif not optional:
        # A two-argument evaluator is accepted for simple analytic fixtures; it
        # cannot claim the optional q-filter capability through this adapter.
        return


def _omitted_band_bounds(evaluator: Any, q_max: float) -> tuple[float, float, bool]:
    method = getattr(evaluator, "omitted_band_bounds", None)
    if callable(method):
        result = method(q_max)
        if isinstance(result, Mapping):
            height = result.get("height_bound_mm")
            slope = result.get("slope_bound")
        elif isinstance(result, tuple) and len(result) == 2:
            height, slope = result
        else:
            height = getattr(result, "height_bound_mm", None)
            slope = getattr(result, "slope_bound", None)
        if height is None or slope is None:
            raise ContractViolation(
                "omitted_band_bounds must return height_bound_mm and slope_bound"
            )
        return (
            _nonnegative_finite(height, "omitted_height_bound_mm"),
            _nonnegative_finite(slope, "omitted_slope_bound"),
            True,
        )
    maximum_q = getattr(evaluator, "maximum_q_rad_per_mm", None)
    if maximum_q is not None and _nonnegative_finite(maximum_q, "maximum_q_rad_per_mm") <= q_max:
        return 0.0, 0.0, True
    # A finite sentinel remains serializable while making the unknown bound
    # maximally conservative.  The receipt is marked refinement-required.
    unknown = float(np.finfo(np.float64).max)
    return unknown, unknown, False


def _tile_core_intersects_footprint(
    coordinate: tuple[int, int],
    footprint: QueryFootprint,
    spacing_mm: float,
    core_shape: tuple[int, int],
    domain: Domain2D,
) -> bool:
    tile_x, tile_y = coordinate
    ny, nx = core_shape
    x_min = domain.x_min_mm + tile_x * nx * spacing_mm
    x_max = x_min + (nx - 1) * spacing_mm
    y_min = domain.y_min_mm + tile_y * ny * spacing_mm
    y_max = y_min + (ny - 1) * spacing_mm
    return not (
        x_max < footprint.x_min_mm
        or x_min > footprint.x_max_mm
        or y_max < footprint.y_min_mm
        or y_min > footprint.y_max_mm
    )


def _resolve_realization_id(evaluator: Any, explicit: str | None) -> str:
    inferred = getattr(evaluator, "surface_realization_id", None)
    if inferred is None:
        realization = getattr(evaluator, "realization", None)
        inferred = getattr(realization, "surface_realization_id", None)
    if explicit is not None and (not isinstance(explicit, str) or not explicit):
        raise ContractViolation("surface_realization_id must be a non-empty string")
    if inferred is not None and (not isinstance(inferred, str) or not inferred):
        raise ContractViolation("evaluator surface_realization_id must be a non-empty string")
    if explicit is not None and inferred is not None and explicit != inferred:
        raise ContractViolation("explicit surface_realization_id does not match evaluator identity")
    resolved = explicit if explicit is not None else inferred
    if resolved is None:
        raise ContractViolation(
            "surface_realization_id is required when evaluator does not expose it"
        )
    return resolved


def _points_2d(value: ArrayLike | None, name: str) -> NDArray[np.float64]:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != 2 or array.shape[0] == 0:
        raise ContractViolation(f"{name} must have shape (n, 2) with n >= 1")
    if not np.isfinite(array).all():
        raise ContractViolation(f"{name} must contain only finite coordinates")
    return np.array(array, dtype=np.float64, order="C", copy=True)


def _polyline_length(points: NDArray[np.float64]) -> float:
    if len(points) < 2:
        return 0.0
    return float(np.sum(np.linalg.norm(np.diff(points, axis=0), axis=1), dtype=np.float64))


def _positive_finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float | np.number):
        raise ContractViolation(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ContractViolation(f"{name} must be positive and finite")
    return result


def _nonnegative_finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float | np.number):
        raise ContractViolation(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ContractViolation(f"{name} must be non-negative and finite")
    return result


def _shape_2d(value: tuple[int, int], name: str, *, minimum: int = 1) -> tuple[int, int]:
    if not isinstance(value, tuple) or len(value) != 2:
        raise ContractViolation(f"{name} must be a two-integer tuple")
    if any(isinstance(item, bool) or not isinstance(item, int) for item in value):
        raise ContractViolation(f"{name} must be a two-integer tuple")
    if any(item < minimum for item in value):
        raise ContractViolation(f"{name} dimensions must be >= {minimum}")
    return value


def _tile_coordinate(value: tuple[int, int]) -> tuple[int, int]:
    coordinate = _shape_2d(value, "tile_coordinate", minimum=0)
    return coordinate


def _coerce_lod(value: LODLevel | int) -> LODLevel:
    if isinstance(value, bool):
        raise ContractViolation("LOD must be one of Rt/5, Rt/8, or Rt/10")
    try:
        return LODLevel(value)
    except ValueError as error:
        raise ContractViolation("LOD must be one of Rt/5, Rt/8, or Rt/10") from error


def _active_bands(value: Sequence[int]) -> tuple[int, ...]:
    bands = tuple(value)
    if bands != tuple(sorted(set(bands))) or any(
        isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in bands
    ):
        raise ContractViolation("active_bands must be unique sorted non-negative integers")
    if not bands:
        raise ContractViolation("at least one active band is required")
    return bands


def _window(value: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    if not isinstance(value, tuple) or len(value) != 4:
        raise ContractViolation("window_mm must be (x_min, x_max, y_min, y_max)")
    if any(
        isinstance(item, bool)
        or not isinstance(item, int | float | np.number)
        or not math.isfinite(float(item))
        for item in value
    ):
        raise ContractViolation("visualization window must contain finite coordinates")
    result = tuple(float(item) for item in value)
    if result[1] <= result[0] or result[3] <= result[2]:
        raise ContractViolation("visualization window extents must be positive")
    return result  # type: ignore[return-value]


def _string_attribute(instance: Any, name: str, default: str) -> str:
    value = getattr(instance, name, default)
    return value if isinstance(value, str) and value else default


def _first_present(mapping: Mapping[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in mapping:
            return mapping[name]
    raise ContractViolation("evaluator result does not contain a height field")


def _first_present_optional(mapping: Mapping[str, Any], names: tuple[str, ...]) -> Any | None:
    for name in names:
        if name in mapping:
            return mapping[name]
    return None


def _first_attribute(instance: Any, names: tuple[str, ...]) -> Any:
    for name in names:
        if hasattr(instance, name):
            return getattr(instance, name)
    raise ContractViolation("evaluator result does not expose a height field")


def _first_attribute_optional(instance: Any, names: tuple[str, ...]) -> Any | None:
    for name in names:
        if hasattr(instance, name):
            return getattr(instance, name)
    return None


def _declared_evaluator_shape(result: Any) -> tuple[int, ...] | None:
    if isinstance(result, Mapping):
        value = result.get("query_shape", result.get("input_shape"))
    else:
        value = getattr(result, "query_shape", getattr(result, "input_shape", None))
    if value is None:
        return None
    try:
        return tuple(int(item) for item in value)
    except (TypeError, ValueError):
        raise ContractViolation("evaluator result declares an invalid input/query shape") from None


__all__ = [
    "DEFAULT_MEMORY_CACHE_BUDGET_MIB",
    "DEFAULT_TILE_CORE_SHAPE",
    "DEFAULT_TILE_HALO_SAMPLES",
    "LOD_RT_OVER_5",
    "LOD_RT_OVER_8",
    "LOD_RT_OVER_10",
    "MATERIALIZATION_METHOD_ID",
    "MATERIALIZATION_METHOD_VERSION",
    "NORMAL_PATH_BUILDS_FULL_DOMAIN_RT10_DENSE",
    "VISUALIZATION_LOW_PASS_METHOD",
    "ActiveFootprintDomainError",
    "CacheLookup",
    "CacheStatus",
    "ContentAddressedTileCache",
    "FootprintGuard",
    "LODLevel",
    "MaterializationConfig",
    "MaterializationLOD",
    "MaterializedTile",
    "SurfaceEvaluator",
    "TileCache",
    "TileCacheKey",
    "TileCacheStats",
    "TileKey",
    "TileMaterializer",
    "TilePayload",
    "derive_query_footprint",
    "sample_visualization_window",
    "tile_coordinates_for_footprint",
]
