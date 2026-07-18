from __future__ import annotations

import math

import numpy as np
import pytest

from spine_sim.surface.contracts import Domain2D, M01ReasonCode
from spine_sim.surface.materialization import (
    NORMAL_PATH_BUILDS_FULL_DOMAIN_RT10_DENSE,
    VISUALIZATION_LOW_PASS_METHOD,
    ActiveFootprintDomainError,
    CacheStatus,
    ContentAddressedTileCache,
    FootprintGuard,
    LODLevel,
    MaterializationConfig,
    TileCacheKey,
    TileMaterializer,
    TilePayload,
    derive_query_footprint,
    sample_visualization_window,
)


class CoordinateEvaluator:
    """Small deterministic fixture which records requested filters and shapes."""

    surface_realization_id = "surface-realization:test-coordinate-field"
    generator_version = "test-coordinate-evaluator-1"
    maximum_q_rad_per_mm = 1.0e6

    def __init__(self) -> None:
        self.calls: list[tuple[tuple[int, ...], int, float | None, str | None]] = []

    def evaluate(
        self,
        x_mm: np.ndarray,
        y_mm: np.ndarray,
        derivative_order: int = 0,
        q_max_rad_per_mm: float | None = None,
        low_pass_method: str | None = None,
    ) -> np.ndarray:
        self.calls.append((x_mm.shape, derivative_order, q_max_rad_per_mm, low_pass_method))
        # A coordinate-only function makes overlap checks exact and exposes any
        # footprint-relative origin accidentally introduced by materialization.
        return x_mm * 0.125 + y_mm * 0.0625


def _materializer(
    evaluator: CoordinateEvaluator | None = None,
    *,
    core_shape: tuple[int, int] = (16, 16),
    halo_samples: int = 2,
    cache: ContentAddressedTileCache | None = None,
) -> TileMaterializer:
    fixture = evaluator if evaluator is not None else CoordinateEvaluator()
    return TileMaterializer(
        fixture,
        config=MaterializationConfig(
            core_shape=core_shape,
            halo_samples=halo_samples,
            memory_cache_budget_mib=1.0,
        ),
        cache=cache,
    )


def _key(tile_x: int, *, core_shape: tuple[int, int] = (2, 2)) -> TileCacheKey:
    return TileCacheKey(
        surface_realization_id="surface-realization:test-cache",
        generator_version="test-1",
        query_contract_version="1.0.0",
        materialization_method_version="1.0.0",
        lod=5,
        active_bands=(0,),
        tile_coordinate=(tile_x, 0),
        core_shape=core_shape,
        halo_samples=0,
        spacing_mm=0.2,
        q_max_rad_per_mm=math.pi / 0.2,
    )


def _payload(key: TileCacheKey, value: float) -> TilePayload:
    ny, nx = key.core_shape
    x = np.arange(nx, dtype=np.float64) * key.spacing_mm
    y = np.arange(ny, dtype=np.float64) * key.spacing_mm
    return TilePayload(
        key,
        x,
        y,
        np.full((ny, nx), value, dtype=np.float64),
        np.ones((ny, nx), dtype=np.bool_),
    )


def test_100_mm_narrow_and_wide_footprints_share_coordinate_anchored_tile() -> None:
    path = np.array(((25.0, 75.0), (125.0, 75.0)))
    narrow = derive_query_footprint(
        path_points_mm=path,
        geometry_offsets_mm=np.array(((0.0, -1.0), (0.0, 1.0))),
        guard_mm=FootprintGuard(probe_radius_mm=1.0, tile_halo_mm=0.5),
    )
    wide = derive_query_footprint(
        path_points_mm=path,
        geometry_offsets_mm=np.array(((0.0, -3.0), (0.0, 3.0))),
        guard_mm=FootprintGuard(probe_radius_mm=2.0, tile_halo_mm=1.0),
    )

    assert narrow.x_max_mm - narrow.x_min_mm == pytest.approx(102.0)
    assert wide.x_max_mm - wide.x_min_mm == pytest.approx(104.0)
    assert narrow.footprint_id != wide.footprint_id

    first = _materializer()
    second = _materializer()
    narrow_tiles = set(
        first.tile_coordinates_for_footprint(narrow, reference_rt_mm=10.0, lod=LODLevel.RT_OVER_5)
    )
    wide_tiles = set(
        second.tile_coordinates_for_footprint(wide, reference_rt_mm=10.0, lod=LODLevel.RT_OVER_5)
    )
    shared_coordinate = min(narrow_tiles & wide_tiles, key=lambda item: (item[1], item[0]))
    narrow_tile = first.sample_tile(
        narrow,
        shared_coordinate,
        reference_rt_mm=10.0,
        lod=LODLevel.RT_OVER_5,
    )
    wide_tile = second.sample_tile(
        wide,
        shared_coordinate,
        reference_rt_mm=10.0,
        lod=LODLevel.RT_OVER_5,
    )

    assert narrow_tile.payload.key == wide_tile.payload.key
    assert narrow_tile.payload.content_hash == wide_tile.payload.content_hash
    np.testing.assert_array_equal(
        narrow_tile.payload.x_coordinates_mm, wide_tile.payload.x_coordinates_mm
    )
    np.testing.assert_array_equal(
        narrow_tile.payload.y_coordinates_mm, wide_tile.payload.y_coordinates_mm
    )
    np.testing.assert_array_equal(narrow_tile.height_mm, wide_tile.height_mm)


def test_footprint_outside_parent_is_rejected_without_clamp_or_wrap() -> None:
    with pytest.raises(ActiveFootprintDomainError) as caught:
        derive_query_footprint(
            path_points_mm=np.array(((1.0, 10.0), (50.0, 10.0))),
            geometry_offsets_mm=np.array(((-2.0, -1.0), (2.0, 1.0))),
            guard_mm=1.0,
        )

    assert caught.value.code == M01ReasonCode.ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN.value
    assert (
        caught.value.details["reason_code"] == M01ReasonCode.ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN.value
    )
    assert caught.value.details["requested_bounds_mm"][0] == pytest.approx(-2.0)
    assert caught.value.details["policy"] == "reject_without_wrap_clamp_crop_or_path_shortening"


def test_lod_spacing_and_band_sets_are_strictly_nested() -> None:
    levels = (LODLevel.RT_OVER_5, LODLevel.RT_OVER_8, LODLevel.RT_OVER_10)
    assert tuple(level.label for level in levels) == ("Rt/5", "Rt/8", "Rt/10")
    assert tuple(level.spacing_mm(2.0) for level in levels) == pytest.approx((0.4, 0.25, 0.2))
    assert levels[0].active_bands == (0,)
    assert levels[1].active_bands == (0, 1)
    assert levels[2].active_bands == (0, 1, 2)
    assert set(levels[0].active_bands) < set(levels[1].active_bands)
    assert set(levels[1].active_bands) < set(levels[2].active_bands)

    footprint = derive_query_footprint(swept_points_mm=np.array(((10.0, 10.0), (11.0, 11.0))))
    materializer = _materializer(core_shape=(8, 8), halo_samples=1)
    receipts = [
        materializer.sample_tile(
            footprint,
            materializer.tile_coordinates_for_footprint(footprint, reference_rt_mm=2.0, lod=level)[
                0
            ],
            reference_rt_mm=2.0,
            lod=level,
        ).receipt
        for level in levels
    ]
    assert tuple(receipt.spacing_mm for receipt in receipts) == pytest.approx((0.4, 0.25, 0.2))
    assert tuple(receipt.active_bands for receipt in receipts) == (
        (0,),
        (0, 1),
        (0, 1, 2),
    )


def test_cache_is_bounded_lru_and_reports_hits_and_eviction_order() -> None:
    keys = tuple(_key(index) for index in range(3))
    payloads = tuple(_payload(key, float(index)) for index, key in enumerate(keys))
    budget = payloads[0].payload_bytes * 2
    cache = ContentAddressedTileCache(memory_budget_bytes=budget)

    assert cache.put(keys[0], payloads[0])
    assert cache.put(keys[1], payloads[1])
    assert cache.get(keys[0]) is payloads[0]  # make key 0 most recently used
    assert cache.put(keys[2], payloads[2])

    assert cache.get(keys[0]) is payloads[0]
    assert cache.get(keys[1]) is None
    assert cache.get(keys[2]) is payloads[2]
    stats = cache.stats_snapshot()
    assert stats.evicted_tiles == 1
    assert stats.memory_hits == 3
    assert stats.cache_misses == 1
    assert stats.resident_tiles == 2
    assert stats.memory_payload_bytes == budget
    assert stats.payload_within_budget


def test_corrupt_memory_payload_is_regenerated_with_explicit_reason() -> None:
    evaluator = CoordinateEvaluator()
    materializer = _materializer(evaluator, core_shape=(8, 8), halo_samples=1)
    footprint = derive_query_footprint(swept_points_mm=np.array(((20.0, 20.0), (21.0, 21.0))))
    coordinate = materializer.tile_coordinates_for_footprint(footprint, reference_rt_mm=2.0)[0]
    first = materializer.sample_tile(footprint, coordinate, reference_rt_mm=2.0)
    expected = first.height_mm.copy()
    materializer.cache.corrupt_memory_entry_for_testing(first.payload.key)

    rebuilt = materializer.sample_tile(footprint, coordinate, reference_rt_mm=2.0)

    assert rebuilt.receipt.cache_status == CacheStatus.CORRUPTION_REGENERATED.value
    assert rebuilt.receipt.reason_code == M01ReasonCode.CACHE_CORRUPTION_REGENERATED.value
    np.testing.assert_array_equal(rebuilt.height_mm, expected)
    assert materializer.stats.corruption_events == 1
    assert materializer.stats.regenerated_tiles == 1
    assert len(evaluator.calls) == 2


def test_optional_disk_cache_round_trip_uses_verified_payload(
    tmp_path: pytest.TempPathFactory,
) -> None:
    key = _key(0)
    payload = _payload(key, 3.25)
    cache = ContentAddressedTileCache(
        memory_budget_bytes=payload.payload_bytes * 2,
        disk_cache_enabled=True,
        disk_cache_directory=tmp_path,
        disk_budget_bytes=1024 * 1024,
    )
    calls = 0

    def factory() -> TilePayload:
        nonlocal calls
        calls += 1
        return payload

    first = cache.get_or_create(key, factory)
    cache.clear_memory()
    second = cache.get_or_create(key, factory)

    assert first.cache_status is CacheStatus.MISS_GENERATED
    assert second.cache_status is CacheStatus.DISK_HIT
    assert calls == 1
    assert second.payload.content_hash == payload.content_hash
    np.testing.assert_array_equal(second.payload.height_mm, payload.height_mm)


def test_adjacent_tile_halos_have_bitwise_identical_coordinates_and_heights() -> None:
    materializer = _materializer(core_shape=(8, 8), halo_samples=2)
    footprint = derive_query_footprint(swept_points_mm=np.array(((0.5, 0.5), (3.0, 1.0))))
    left = materializer.sample_tile(footprint, (0, 0), reference_rt_mm=1.0, lod=LODLevel.RT_OVER_5)
    right = materializer.sample_tile(footprint, (1, 0), reference_rt_mm=1.0, lod=LODLevel.RT_OVER_5)

    # With core=8 and halo=2, global x indices 6..9 are present in both tiles.
    np.testing.assert_array_equal(
        left.payload.x_coordinates_mm[8:12], right.payload.x_coordinates_mm[0:4]
    )
    np.testing.assert_array_equal(left.height_mm[:, 8:12], right.height_mm[:, 0:4])
    np.testing.assert_array_equal(left.validity[:, 8:12], right.validity[:, 0:4])


def test_tile_request_order_and_cache_hit_do_not_change_payload() -> None:
    footprint = derive_query_footprint(
        swept_points_mm=np.array(((4.0, 4.0), (8.0, 4.0))), guard_mm=0.25
    )
    forward = _materializer(core_shape=(8, 8), halo_samples=1)
    reverse = _materializer(core_shape=(8, 8), halo_samples=1)
    coordinates = forward.tile_coordinates_for_footprint(
        footprint, reference_rt_mm=2.0, lod=LODLevel.RT_OVER_5
    )
    assert len(coordinates) >= 2

    forward_payloads = {
        coordinate: forward.sample_tile(
            footprint, coordinate, reference_rt_mm=2.0, lod=LODLevel.RT_OVER_5
        ).payload
        for coordinate in coordinates
    }
    reverse_payloads = {
        coordinate: reverse.sample_tile(
            footprint, coordinate, reference_rt_mm=2.0, lod=LODLevel.RT_OVER_5
        ).payload
        for coordinate in reversed(coordinates)
    }
    for coordinate in coordinates:
        np.testing.assert_array_equal(
            forward_payloads[coordinate].height_mm,
            reverse_payloads[coordinate].height_mm,
        )
        assert (
            forward_payloads[coordinate].content_hash == reverse_payloads[coordinate].content_hash
        )

    cached = forward.sample_tile(
        footprint, coordinates[0], reference_rt_mm=2.0, lod=LODLevel.RT_OVER_5
    )
    assert cached.receipt.cache_status == CacheStatus.MEMORY_HIT.value
    np.testing.assert_array_equal(
        cached.payload.height_mm, forward_payloads[coordinates[0]].height_mm
    )


def test_default_visualization_is_1024_square_and_passes_display_nyquist() -> None:
    evaluator = CoordinateEvaluator()
    sample = sample_visualization_window(evaluator)

    expected_q_max = math.pi / (Domain2D().width_mm / 1023)
    assert sample.grid_shape == (1024, 1024)
    assert sample.height_mm.shape == (1024, 1024)
    assert sample.validity.all()
    assert sample.visualization_q_max_rad_per_mm == pytest.approx(expected_q_max)
    assert sample.low_pass_method == VISUALIZATION_LOW_PASS_METHOD
    assert evaluator.calls == [
        ((1024, 1024), 0, pytest.approx(expected_q_max), VISUALIZATION_LOW_PASS_METHOD)
    ]


def test_tile_and_nonsquare_visualization_propagate_their_nyquist_cutoffs() -> None:
    evaluator = CoordinateEvaluator()
    materializer = _materializer(evaluator, core_shape=(4, 4), halo_samples=0)
    footprint = derive_query_footprint(swept_points_mm=np.array(((10.0, 10.0), (10.5, 10.5))))
    coordinate = materializer.tile_coordinates_for_footprint(
        footprint, reference_rt_mm=2.0, lod=LODLevel.RT_OVER_8
    )[0]
    tile = materializer.sample_tile(
        footprint,
        coordinate,
        reference_rt_mm=2.0,
        lod=LODLevel.RT_OVER_8,
    )
    sample = materializer.sample_visualization_window((10.0, 20.0, 30.0, 35.0), (11, 6))

    expected_tile_q = math.pi / (2.0 / 8.0)
    expected_display_q = min(math.pi / (10.0 / 5), math.pi / (5.0 / 10))
    assert tile.payload.key.q_max_rad_per_mm == pytest.approx(expected_tile_q)
    assert evaluator.calls[0][2] == pytest.approx(expected_tile_q)
    assert evaluator.calls[0][3] == "M01_TILE_NYQUIST_BANDLIMIT_1"
    assert sample.visualization_q_max_rad_per_mm == pytest.approx(expected_display_q)
    assert evaluator.calls[1] == (
        (11, 6),
        0,
        pytest.approx(expected_display_q),
        VISUALIZATION_LOW_PASS_METHOD,
    )


def test_normal_rt10_path_streams_only_active_tiles_not_full_parent_dense() -> None:
    evaluator = CoordinateEvaluator()
    materializer = _materializer(evaluator, core_shape=(8, 8), halo_samples=1)
    footprint = derive_query_footprint(swept_points_mm=np.array(((74.0, 74.0), (74.5, 74.5))))

    tiles = tuple(
        materializer.iter_footprint_tiles(footprint, reference_rt_mm=1.0, lod=LODLevel.RT_OVER_10)
    )

    assert NORMAL_PATH_BUILDS_FULL_DOMAIN_RT10_DENSE is False
    assert materializer.normal_path_builds_full_domain_rt10_dense is False
    assert materializer.stats.full_domain_rt10_dense_created is False
    assert tiles
    assert all(tile.payload.height_mm.shape == (10, 10) for tile in tiles)
    assert all(call[0] == (100,) for call in evaluator.calls)
    full_parent_shape = (1501, 1501)
    assert full_parent_shape not in (call[0] for call in evaluator.calls)
