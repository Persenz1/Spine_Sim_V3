"""VALIDATION_ONLY compatibility harness between M02 orchestration and M01 surfaces.

The production numerics service does not own :class:`QueryFootprint`, tiles, or
surface geometry.  This module deliberately acts as a small mock physical
owner: it creates immutable M01 realizations, derives complete swept geometry
footprints through the M01 public API, and returns audit data that an M02
integration test can consume.  Nothing here is an A/B physical implementation.

Materialization receipts contain cache hit/miss state and are therefore
diagnostic.  Every invariant below compares coordinate-anchored tile keys,
content hashes, query identities, values, and quality metadata; receipt IDs are
never part of a semantic comparison or result hash.
"""

from __future__ import annotations

import json
import math
import resource
import sys
import time
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any, Final

import numpy as np
from numpy.typing import NDArray

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.surface import (
    BoundaryMode,
    Domain2D,
    FootprintGuard,
    LODLevel,
    M01ReasonCode,
    MaterializationConfig,
    QueryFootprint,
    QueryResponse,
    SurfaceFamily,
    SurfaceProvider,
    SurfaceQuery,
    TileMaterializer,
    derive_query_footprint,
    make_latent_noise_identity,
    make_synthetic_source_descriptor,
    synthetic_parameters_for_tier,
)
from spine_sim.surface.materialization import (
    NORMAL_PATH_BUILDS_FULL_DOMAIN_RT10_DENSE,
    MaterializedTile,
)

M01_COMPATIBILITY_SCHEMA_VERSION = "1.0.0"
SURFACE_SCALE_REFERENCE_RT_MM = 0.05
PRIMARY_QUERY_PROBE_RADIUS_MM = 0.10
SECONDARY_QUERY_PROBE_RADIUS_MM = 0.05
PATH_LENGTH_MM = 100.0
PATH_Y_MM = 75.0
PATH_POINTS_MM: Final[tuple[tuple[float, float], ...]] = (
    (25.0, PATH_Y_MM),
    (125.0, PATH_Y_MM),
)
ROOT_SEED_DEFAULT = 0x6D30325F6D30315F636F6D7061745F31


class M01CompatibilityPanel(StrEnum):
    """Frozen M02/M01 compatibility panel identities."""

    SMOKE_4 = "M02_M01_SMOKE_4"
    STANDARD_64 = "M02_M01_STANDARD_64"
    STRESS_256 = "M02_M01_STRESS_256"


@dataclass(frozen=True, slots=True)
class _PanelPolicy:
    scenario_count: int
    diagnostic_level: str
    standard_witness_scenarios: int


_PANEL_POLICIES: Final[dict[M01CompatibilityPanel, _PanelPolicy]] = {
    M01CompatibilityPanel.SMOKE_4: _PanelPolicy(4, "FULL", 4),
    M01CompatibilityPanel.STANDARD_64: _PanelPolicy(64, "STANDARD", 64),
    M01CompatibilityPanel.STRESS_256: _PanelPolicy(256, "COMPACT", 32),
}

_PANEL_ALIASES: Final[dict[str, M01CompatibilityPanel]] = {
    "smoke": M01CompatibilityPanel.SMOKE_4,
    "smoke_4": M01CompatibilityPanel.SMOKE_4,
    "standard": M01CompatibilityPanel.STANDARD_64,
    "standard_64": M01CompatibilityPanel.STANDARD_64,
    "stress": M01CompatibilityPanel.STRESS_256,
    "stress_256": M01CompatibilityPanel.STRESS_256,
}


@dataclass(frozen=True, slots=True)
class GeometryFixture:
    """VALIDATION_ONLY array layout input owned by the mock physical owner."""

    fixture_id: str
    spines_x: int
    spines_y: int
    spacing_mm: float

    @property
    def spine_count(self) -> int:
        return self.spines_x * self.spines_y

    def as_dict(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "spines_x": self.spines_x,
            "spines_y": self.spines_y,
            "spacing_mm": self.spacing_mm,
            "spine_count": self.spine_count,
            "source_identity": "VALIDATION_ONLY",
        }


GEOMETRY_FIXTURES: Final[tuple[GeometryFixture, ...]] = (
    GeometryFixture("SINGLE_SPINE", 1, 1, 0.0),
    GeometryFixture("ARRAY_2X2_S4", 2, 2, 4.0),
    GeometryFixture("ARRAY_2X6_S6", 2, 6, 6.0),
    GeometryFixture("ARRAY_6X2_S6", 6, 2, 6.0),
    GeometryFixture("ARRAY_6X6_S6", 6, 6, 6.0),
)

# This mock envelope includes separately named tip, body, and installation
# extrema.  Its values are validation geometry, not an A/B parameter set.
_LOCAL_GEOMETRY_ENVELOPE: Final[tuple[tuple[str, float, float], ...]] = (
    ("tip", -0.10, 0.0),
    ("tip", 0.10, 0.0),
    ("body", -0.60, -0.25),
    ("body", 0.60, 0.25),
    ("installation", -0.75, -0.50),
    ("installation", 0.75, 0.50),
)

_FULL_GUARD = FootprintGuard(
    probe_radius_mm=PRIMARY_QUERY_PROBE_RADIUS_MM,
    trusted_scale_halo_mm=0.025,
    derivative_search_halo_mm=0.040,
    tile_halo_mm=0.020,
    declared_clearance_guard_mm=0.030,
)

_MATERIALIZATION_CONFIG = MaterializationConfig(
    core_shape=(2, 2),
    halo_samples=1,
    memory_cache_budget_mib=0.125,
    disk_cache_enabled=False,
)


@dataclass(frozen=True, slots=True)
class _Scenario:
    scenario_index: int
    scenario_id: str
    common_random_number_group_id: str
    surface_spec_id: str
    surface_realization_id: str
    surface_definition_hash: str
    seed_id: str
    latent_noise_id: str
    parameter_point: dict[str, Any]
    handle: Any
    query: SurfaceQuery

    def audit_dict(self) -> dict[str, Any]:
        return {
            "scenario_index": self.scenario_index,
            "scenario_id": self.scenario_id,
            "common_random_number_group_id": self.common_random_number_group_id,
            "surface_spec_id": self.surface_spec_id,
            "surface_realization_id": self.surface_realization_id,
            "surface_definition_hash": self.surface_definition_hash,
            "seed_id": self.seed_id,
            "latent_noise_id": self.latent_noise_id,
            "parameter_point": self.parameter_point,
        }


@dataclass(frozen=True, slots=True)
class _Probe:
    probe_id: str
    purpose: str
    x_mm: float
    y_mm: float
    lod: LODLevel
    probe_radius_mm: float

    @property
    def spacing_mm(self) -> float:
        return self.lod.spacing_mm(self.probe_radius_mm)

    @property
    def q_max_rad_per_mm(self) -> float:
        return math.pi / self.spacing_mm


_PATH_PROBES: Final[tuple[_Probe, ...]] = (
    _Probe(
        "AHEAD_RT5",
        "ahead",
        PATH_POINTS_MM[0][0],
        PATH_Y_MM,
        LODLevel.RT_OVER_5,
        PRIMARY_QUERY_PROBE_RADIUS_MM,
    ),
    _Probe(
        "EVENT_RT8",
        "event_probe",
        75.0,
        PATH_Y_MM,
        LODLevel.RT_OVER_8,
        PRIMARY_QUERY_PROBE_RADIUS_MM,
    ),
    _Probe(
        "WITNESS_RT8",
        "acceptance_witness_baseline",
        PATH_POINTS_MM[-1][0],
        PATH_Y_MM,
        LODLevel.RT_OVER_8,
        PRIMARY_QUERY_PROBE_RADIUS_MM,
    ),
    _Probe(
        "WITNESS_RT10",
        "acceptance_witness_refined",
        PATH_POINTS_MM[-1][0],
        PATH_Y_MM,
        LODLevel.RT_OVER_10,
        PRIMARY_QUERY_PROBE_RADIUS_MM,
    ),
)

_SECONDARY_RADIUS_PROBE = _Probe(
    "PROBE_RADIUS_0_05_RT8",
    "probe_radius_identity_check",
    75.0,
    PATH_Y_MM,
    LODLevel.RT_OVER_8,
    SECONDARY_QUERY_PROBE_RADIUS_MM,
)


def _resolve_panel(value: M01CompatibilityPanel | str) -> M01CompatibilityPanel:
    if isinstance(value, M01CompatibilityPanel):
        return value
    normalized = str(value).strip()
    if normalized in _PANEL_ALIASES:
        return _PANEL_ALIASES[normalized]
    try:
        return M01CompatibilityPanel(normalized)
    except ValueError as error:
        allowed = ", ".join(item.value for item in M01CompatibilityPanel)
        raise ValueError(f"unknown M01 compatibility panel; expected one of {allowed}") from error


def _parameter_feature(point: tuple[int, int, int, int]) -> tuple[float, ...]:
    h_index, sq_index, lc_index, orientation_index = point
    if orientation_index == 0:
        anisotropy = 0.0
        direction_cos = 0.0
        direction_sin = 0.0
    else:
        anisotropy = 1.0
        direction = (0.0, math.pi / 4.0, math.pi / 2.0)[orientation_index - 1]
        direction_cos = math.cos(2.0 * direction)
        direction_sin = math.sin(2.0 * direction)
    return (
        h_index / 2.0,
        sq_index / 2.0,
        lc_index / 2.0,
        anisotropy,
        direction_cos,
        direction_sin,
    )


def _distance_squared(first: tuple[float, ...], second: tuple[float, ...]) -> float:
    return sum((left - right) ** 2 for left, right in zip(first, second, strict=True))


def _maximin_score(
    candidate: tuple[int, int, int, int],
    selected: list[tuple[int, int, int, int]],
    counts: tuple[Counter[int], ...],
    features: dict[tuple[int, int, int, int], tuple[float, ...]],
) -> tuple[float, int, tuple[int, ...]]:
    minimum_distance = min(
        _distance_squared(features[candidate], features[existing]) for existing in selected
    )
    marginal_load = sum(counts[axis][candidate[axis]] for axis in range(4))
    return minimum_distance, -marginal_load, tuple(-item for item in candidate)


@lru_cache(maxsize=1)
def _balanced_maximin_order() -> tuple[tuple[int, int, int, int], ...]:
    """Return a deterministic greedy maximin ordering of the 108-point design."""

    candidates = tuple(
        (h_index, sq_index, lc_index, orientation_index)
        for h_index in range(3)
        for sq_index in range(3)
        for lc_index in range(3)
        for orientation_index in range(4)
    )
    features = {candidate: _parameter_feature(candidate) for candidate in candidates}
    selected: list[tuple[int, int, int, int]] = [candidates[0]]
    remaining = set(candidates[1:])
    while remaining:
        counts = tuple(Counter(item[axis] for item in selected) for axis in range(4))
        # max() chooses the greatest distance, then the least-used marginal,
        # then a deterministic reverse-lexicographic tiebreak.
        chosen = max(
            remaining,
            key=lambda candidate: _maximin_score(candidate, selected, counts, features),
        )
        selected.append(chosen)
        remaining.remove(chosen)
    return tuple(selected)


def _parameter_point(scenario_index: int) -> dict[str, Any]:
    order = _balanced_maximin_order()
    block, within_block = divmod(scenario_index, len(order))
    rotated_index = (within_block + block * 37) % len(order)
    h_index, sq_index, lc_index, orientation_index = order[rotated_index]
    H = (0.5, 0.7, 0.9)[h_index]
    sq_ratio = (0.25, 1.0, 4.0)[sq_index]
    lc_ratio = (5.0, 20.0, 80.0)[lc_index]
    anisotropy_ratio = 1.0 if orientation_index == 0 else 2.0
    direction = (
        None
        if orientation_index == 0
        else (0.0, math.pi / 4.0, math.pi / 2.0)[orientation_index - 1]
    )
    return {
        "maximin_design_rank": rotated_index,
        "maximin_design_block": block,
        "H": H,
        "Sq_over_reference_Rt": sq_ratio,
        "lc_over_reference_Rt": lc_ratio,
        "anisotropy_ratio": anisotropy_ratio,
        "anisotropy_direction_rad": direction,
        "surface_scale_reference_Rt_mm": SURFACE_SCALE_REFERENCE_RT_MM,
    }


def _synthetic_parameters(point: dict[str, Any]) -> dict[str, Any]:
    parameters = synthetic_parameters_for_tier(
        "medium",
        surface_scale_reference_Rt_mm=SURFACE_SCALE_REFERENCE_RT_MM,
        anisotropy_ratio=float(point["anisotropy_ratio"]),
        anisotropy_direction_rad=point["anisotropy_direction_rad"],
        modes_per_band=4,
    )
    sq_ratio = float(point["Sq_over_reference_Rt"])
    lc_ratio = float(point["lc_over_reference_Rt"])
    parameters.update(
        {
            "roughness_tier": "explicit",
            "H": float(point["H"]),
            "Sq_over_reference_Rt": sq_ratio,
            "Sq_mm": sq_ratio * SURFACE_SCALE_REFERENCE_RT_MM,
            "lc_over_reference_Rt": lc_ratio,
            "lc_mm": lc_ratio * SURFACE_SCALE_REFERENCE_RT_MM,
        }
    )
    return parameters


def _create_scenario(
    provider: SurfaceProvider,
    descriptor: Any,
    scenario_index: int,
    root_seed: int,
) -> _Scenario:
    point = _parameter_point(scenario_index)
    creation = provider.create_surface_spec(
        descriptor,
        SurfaceFamily.SELF_AFFINE_GAUSSIAN,
        _synthetic_parameters(point),
    )
    if creation.spec is None:
        raise RuntimeError(
            f"M01 rejected compatibility surface spec: {creation.status.explanation}"
        )
    latent = make_latent_noise_identity(
        root_seed,
        scenario_index,
        latent_noise_namespace="m02.m01.compatibility.independent_scenarios",
    )
    realized = provider.create_realization(
        descriptor,
        creation.spec,
        latent_identity=latent,
    )
    if realized.realization is None or realized.handle is None:
        raise RuntimeError(f"M01 rejected compatibility realization: {realized.status.explanation}")
    scenario_id = stable_content_id(
        "m02_m01_compatibility_scenario",
        {
            "surface_spec_id": realized.realization.surface_spec_id,
            "surface_realization_id": realized.realization.surface_realization_id,
            "seed_id": latent.seed_id,
            "parameter_point": point,
        },
    )
    return _Scenario(
        scenario_index=scenario_index,
        scenario_id=scenario_id,
        common_random_number_group_id=stable_content_id(
            "m02_m01_common_random_number_group",
            {"surface_realization_id": realized.realization.surface_realization_id},
        ),
        surface_spec_id=realized.realization.surface_spec_id,
        surface_realization_id=realized.realization.surface_realization_id,
        surface_definition_hash=realized.realization.definition_hash,
        seed_id=latent.seed_id,
        latent_noise_id=latent.latent_noise_id,
        parameter_point=point,
        handle=realized.handle,
        query=SurfaceQuery(realized.handle),
    )


def _fixture_geometry_offsets(fixture: GeometryFixture) -> NDArray[np.float64]:
    if fixture.spines_x < 1 or fixture.spines_y < 1:
        raise ValueError("fixture spine counts must be positive")
    if fixture.spine_count > 1 and fixture.spacing_mm <= 0.0:
        raise ValueError("array fixture spacing must be positive")
    x_sites = (
        np.arange(fixture.spines_x, dtype=np.float64) - (fixture.spines_x - 1) / 2.0
    ) * fixture.spacing_mm
    y_sites = (
        np.arange(fixture.spines_y, dtype=np.float64) - (fixture.spines_y - 1) / 2.0
    ) * fixture.spacing_mm
    points = {
        (float(site_x + local_x), float(site_y + local_y))
        for site_x in x_sites
        for site_y in y_sites
        for _, local_x, local_y in _LOCAL_GEOMETRY_ENVELOPE
    }
    return np.asarray(sorted(points), dtype=np.float64)


def _derive_fixture_footprint(
    fixture: GeometryFixture,
    domain: Domain2D,
) -> tuple[QueryFootprint, NDArray[np.float64]]:
    offsets = _fixture_geometry_offsets(fixture)
    footprint = derive_query_footprint(
        path_points_mm=np.asarray(PATH_POINTS_MM, dtype=np.float64),
        geometry_offsets_mm=offsets,
        guard_mm=_FULL_GUARD,
        logical_domain=domain,
        maximum_path_length_mm=PATH_LENGTH_MM,
        derivation_method=f"M02_VALIDATION_ONLY_{fixture.fixture_id}_FULL_ENVELOPE_1",
    )
    return footprint, offsets


def _new_materializer(scenario: _Scenario) -> TileMaterializer:
    realization = scenario.handle.realization
    return TileMaterializer(
        scenario.handle.evaluator,
        scenario.surface_realization_id,
        logical_domain=realization.logical_domain,
        generator_version=realization.generator_version,
        query_contract_version=realization.query_contract_version,
        config=_MATERIALIZATION_CONFIG,
    )


def _probe_tile_coordinate(materializer: TileMaterializer, probe: _Probe) -> tuple[int, int]:
    selector = derive_query_footprint(
        swept_points_mm=np.asarray(((probe.x_mm, probe.y_mm),), dtype=np.float64),
        guard_mm=max(probe.spacing_mm * 0.25, 1.0e-9),
        logical_domain=materializer.logical_domain,
        maximum_path_length_mm=None,
        derivation_method="M02_VALIDATION_ONLY_LOCAL_PROBE_TILE_SELECTOR_1",
    )
    candidates = materializer.tile_coordinates_for_footprint(
        selector,
        reference_rt_mm=probe.probe_radius_mm,
        lod=probe.lod,
    )
    ny, nx = materializer.config.core_shape
    del ny
    expected = (
        math.floor((probe.x_mm - materializer.logical_domain.x_min_mm) / (nx * probe.spacing_mm)),
        math.floor(
            (probe.y_mm - materializer.logical_domain.y_min_mm)
            / (materializer.config.core_shape[0] * probe.spacing_mm)
        ),
    )
    if expected not in candidates:
        raise RuntimeError("M01 local probe tile selector did not include the containing tile")
    return expected


def _sample_probe_tile(
    materializer: TileMaterializer,
    footprint: QueryFootprint,
    probe: _Probe,
) -> MaterializedTile:
    coordinate = _probe_tile_coordinate(materializer, probe)
    return materializer.sample_tile(
        footprint,
        coordinate,
        reference_rt_mm=probe.probe_radius_mm,
        lod=probe.lod,
    )


def _canonical_tile_ref(tile: MaterializedTile) -> dict[str, Any]:
    return {
        "cache_key_id": tile.payload.key.cache_key_id,
        "surface_realization_id": tile.payload.key.surface_realization_id,
        "lod": tile.payload.key.lod,
        "active_bands": list(tile.payload.key.active_bands),
        "tile_coordinate": list(tile.payload.key.tile_coordinate),
        "spacing_mm": tile.payload.key.spacing_mm,
        "q_max_rad_per_mm": tile.payload.key.q_max_rad_per_mm,
        "content_hash": tile.payload.content_hash,
        "validity_hash": semantic_hash(tile.payload.validity),
    }


def _receipt_diagnostic(tile: MaterializedTile, *, include_id: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "cache_status": tile.receipt.cache_status,
        "reason_code": tile.receipt.reason_code,
        "payload_bytes": tile.receipt.payload_bytes,
    }
    if include_id:
        result["receipt_id"] = tile.receipt.receipt_id
    return result


def _query_probe(query: SurfaceQuery, probe: _Probe) -> QueryResponse:
    return query.query_height_differential(
        [[probe.x_mm, probe.y_mm]],
        derivative_order=1,
        q_max_rad_per_mm=probe.q_max_rad_per_mm,
    )


def _query_quality_ref(response: QueryResponse) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for field_id in ("height_mm", "surface_point_mm", "gradient", "outward_normal"):
        field = response.field(field_id)
        fields[field_id] = {
            "values": None if field.values is None else np.asarray(field.values).tolist(),
            "validity": field.validity.tolist(),
            "capability": field.capability.value,
            "reason_code": field.status.reason_code,
            "quality_status": field.quality_status.value,
            "error_bound": field.error_bound,
        }
    semantic = {
        "surface_realization_id": response.surface_realization_id,
        "surface_spec_id": response.surface_spec_id,
        "query_contract_version": response.query_contract_version,
        "query_id": response.query_id,
        "requested_hash": response.requested_points_or_region_hash,
        "capability": response.capability.value,
        "reason_code": response.status.reason_code,
        "domain_status": [item.value for item in response.domain_status],
        "quality_status": [item.value for item in response.quality_status],
        "quality_mask": response.quality_mask.tolist(),
        "trusted_scale_status": response.trusted_scale_status.value,
        "convergence_level": response.convergence_level.value,
        "error_bound": response.error_bound,
        "fields": fields,
    }
    return {"semantic_hash": semantic_hash(semantic), **semantic}


def _field_values(response: QueryResponse, field_id: str) -> NDArray[np.float64]:
    values = response.field(field_id).values
    if values is None or not response.field(field_id).validity[0]:
        raise RuntimeError(f"M01 compatibility query field is unavailable: {field_id}")
    result: NDArray[np.float64] = np.asarray(values, dtype=np.float64)
    return result


def _relative_delta(first: float, second: float) -> float:
    return abs(first - second) / max(abs(first), abs(second), 1.0e-15)


def _refinement_witness(
    baseline: QueryResponse,
    refined: QueryResponse,
    probe_radius_mm: float,
) -> dict[str, Any]:
    point_baseline = _field_values(baseline, "surface_point_mm")[0]
    point_refined = _field_values(refined, "surface_point_mm")[0]
    normal_baseline = _field_values(baseline, "outward_normal")[0]
    normal_refined = _field_values(refined, "outward_normal")[0]
    gradient_baseline = _field_values(baseline, "gradient")[0]
    gradient_refined = _field_values(refined, "gradient")[0]
    height_baseline = float(_field_values(baseline, "height_mm")[0])
    height_refined = float(_field_values(refined, "height_mm")[0])

    event_position_baseline = float(point_baseline[0] + height_baseline)
    event_position_refined = float(point_refined[0] + height_refined)
    event_position_delta = abs(event_position_baseline - event_position_refined)
    support_position_delta = float(np.linalg.norm(point_baseline - point_refined))
    cosine = float(np.dot(normal_baseline, normal_refined)) / max(
        float(np.linalg.norm(normal_baseline) * np.linalg.norm(normal_refined)),
        1.0e-15,
    )
    normal_angle_deg = math.degrees(math.acos(min(1.0, max(-1.0, cosine))))
    force_like_baseline = 1.0 + float(np.linalg.norm(gradient_baseline))
    force_like_refined = 1.0 + float(np.linalg.norm(gradient_refined))
    work_like_baseline = force_like_baseline * (PATH_LENGTH_MM + abs(height_baseline))
    work_like_refined = force_like_refined * (PATH_LENGTH_MM + abs(height_refined))
    force_relative_delta = _relative_delta(force_like_baseline, force_like_refined)
    work_relative_delta = _relative_delta(work_like_baseline, work_like_refined)
    order_baseline = (
        "VALIDATION_HEIGHT_GUARD",
        "RISING" if float(gradient_baseline[0]) >= 0.0 else "FALLING",
    )
    order_refined = (
        "VALIDATION_HEIGHT_GUARD",
        "RISING" if float(gradient_refined[0]) >= 0.0 else "FALLING",
    )
    gates = {
        "event_position": event_position_delta <= 0.01 * probe_radius_mm,
        "unique_support_position": support_position_delta <= 0.02 * probe_radius_mm,
        "normal": normal_angle_deg <= 1.0,
        "force_like_summary": force_relative_delta <= 0.01,
        "work_like_summary": work_relative_delta <= 0.01,
        "event_order": order_baseline == order_refined,
    }
    return {
        "source_identity": "VALIDATION_ONLY",
        "baseline_lod": "Rt/8",
        "refined_lod": "Rt/10",
        "event_position_delta_mm": event_position_delta,
        "event_position_tolerance_mm": 0.01 * probe_radius_mm,
        "unique_support_position_delta_mm": support_position_delta,
        "unique_support_position_tolerance_mm": 0.02 * probe_radius_mm,
        "normal_angle_delta_deg": normal_angle_deg,
        "normal_angle_tolerance_deg": 1.0,
        "fixture_force_like_relative_delta": force_relative_delta,
        "fixture_work_like_relative_delta": work_relative_delta,
        "summary_relative_tolerance": 0.01,
        "event_order_baseline": list(order_baseline),
        "event_order_refined": list(order_refined),
        "gates": gates,
        "passed": all(gates.values()),
    }


def _path_geometry_audit(
    fixture: GeometryFixture,
    footprint: QueryFootprint,
    offsets: NDArray[np.float64],
) -> dict[str, Any]:
    path = np.asarray(PATH_POINTS_MM, dtype=np.float64)
    expected = (
        float(np.min(path[:, 0]) + np.min(offsets[:, 0]) - _FULL_GUARD.effective_mm),
        float(np.max(path[:, 0]) + np.max(offsets[:, 0]) + _FULL_GUARD.effective_mm),
        float(np.min(path[:, 1]) + np.min(offsets[:, 1]) - _FULL_GUARD.effective_mm),
        float(np.max(path[:, 1]) + np.max(offsets[:, 1]) + _FULL_GUARD.effective_mm),
    )
    observed = (
        footprint.x_min_mm,
        footprint.x_max_mm,
        footprint.y_min_mm,
        footprint.y_max_mm,
    )
    endpoint_guard_pass = all(
        math.isclose(left, right, rel_tol=0.0, abs_tol=1.0e-12)
        for left, right in zip(expected, observed, strict=True)
    )
    path_length = float(np.sum(np.linalg.norm(np.diff(path, axis=0), axis=1)))
    component_counts = Counter(name for name, _, _ in _LOCAL_GEOMETRY_ENVELOPE)
    return {
        "fixture_id": fixture.fixture_id,
        "footprint_id": footprint.footprint_id,
        "path_points_mm": [list(item) for item in PATH_POINTS_MM],
        "path_length_mm": path_length,
        "logical_parent_domain_mm": [0.0, 150.0, 0.0, 150.0],
        "footprint_bounds_mm": list(observed),
        "footprint_x_extent_mm": footprint.x_max_mm - footprint.x_min_mm,
        "footprint_y_extent_mm": footprint.y_max_mm - footprint.y_min_mm,
        "geometry_offset_count": int(offsets.shape[0]),
        "geometry_component_counts_per_spine": dict(sorted(component_counts.items())),
        "guard_components_mm": {
            "probe_radius_mm": _FULL_GUARD.probe_radius_mm,
            "trusted_scale_halo_mm": _FULL_GUARD.trusted_scale_halo_mm,
            "derivative_search_halo_mm": _FULL_GUARD.derivative_search_halo_mm,
            "tile_halo_mm": _FULL_GUARD.tile_halo_mm,
            "declared_clearance_guard_mm": _FULL_GUARD.declared_clearance_guard_mm,
        },
        "effective_guard_mm": _FULL_GUARD.effective_mm,
        "endpoint_guard_pass": endpoint_guard_pass,
        "full_100_mm_path_pass": math.isclose(path_length, PATH_LENGTH_MM),
        "width_derived_by_m01": True,
    }


def _domain_error_audit(domain: Domain2D) -> dict[str, Any]:
    fixture = GEOMETRY_FIXTURES[-1]
    offsets = _fixture_geometry_offsets(fixture)
    try:
        derive_query_footprint(
            path_points_mm=np.asarray(((0.2, PATH_Y_MM), (100.2, PATH_Y_MM))),
            geometry_offsets_mm=offsets,
            guard_mm=_FULL_GUARD,
            logical_domain=domain,
            maximum_path_length_mm=PATH_LENGTH_MM,
            derivation_method="M02_VALIDATION_ONLY_DOMAIN_ERROR_1",
        )
    except ContractViolation as error:
        reason = str(error.details.get("reason_code", ""))
        policy = str(error.details.get("policy", ""))
        return {
            "reason_code": reason,
            "policy": policy,
            "raw_reason_preserved": reason == M01ReasonCode.ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN.value,
            "no_wrap_clamp_crop_or_shortening": policy
            == "reject_without_wrap_clamp_crop_or_path_shortening",
            "passed": reason == M01ReasonCode.ACTIVE_FOOTPRINT_EXCEEDS_DOMAIN.value
            and policy == "reject_without_wrap_clamp_crop_or_path_shortening",
        }
    return {
        "reason_code": None,
        "policy": None,
        "raw_reason_preserved": False,
        "no_wrap_clamp_crop_or_shortening": False,
        "passed": False,
    }


def _run_fixture_path(
    scenario: _Scenario,
    fixture: GeometryFixture,
    footprints: dict[str, QueryFootprint],
    offsets_by_fixture: dict[str, NDArray[np.float64]],
    diagnostic_level: str,
) -> dict[str, Any]:
    current = footprints[fixture.fixture_id]
    if fixture.fixture_id == GEOMETRY_FIXTURES[-1].fixture_id:
        narrow = footprints[GEOMETRY_FIXTURES[0].fixture_id]
        wide = current
        overlap_peer = GEOMETRY_FIXTURES[0].fixture_id
    else:
        narrow = current
        wide = footprints[GEOMETRY_FIXTURES[-1].fixture_id]
        overlap_peer = GEOMETRY_FIXTURES[-1].fixture_id

    dynamic = _new_materializer(scenario)
    prewide = _new_materializer(scenario)
    forward_queries: dict[str, QueryResponse] = {}
    reverse_queries: dict[str, QueryResponse] = {}
    canonical_probes: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    invariant_flags: list[bool] = []

    for probe in _PATH_PROBES:
        dynamic_narrow = _sample_probe_tile(dynamic, narrow, probe)
        dynamic_wide = _sample_probe_tile(dynamic, wide, probe)
        dynamic_warm = _sample_probe_tile(dynamic, narrow, probe)
        query_response = _query_probe(scenario.query, probe)
        forward_queries[probe.probe_id] = query_response
        narrow_ref = _canonical_tile_ref(dynamic_narrow)
        wide_ref = _canonical_tile_ref(dynamic_wide)
        warm_ref = _canonical_tile_ref(dynamic_warm)
        overlap_equal = narrow_ref == wide_ref
        cold_warm_equal = narrow_ref == warm_ref
        invariant_flags.extend((overlap_equal, cold_warm_equal))
        quality_ref = _query_quality_ref(query_response)
        canonical_probes.append(
            {
                "probe_id": probe.probe_id,
                "purpose": probe.purpose,
                "position_mm": [probe.x_mm, probe.y_mm],
                "lod": probe.lod.label,
                "probe_radius_mm": probe.probe_radius_mm,
                "spacing_mm": probe.spacing_mm,
                "canonical_tile_ref": narrow_ref,
                "query_quality_ref_hash": quality_ref["semantic_hash"],
                "domain_status": quality_ref["domain_status"],
                "quality_status": quality_ref["quality_status"],
                "trusted_scale_status": quality_ref["trusted_scale_status"],
                "reason_code": quality_ref["reason_code"],
                "narrow_wide_overlap_equal": overlap_equal,
                "cold_warm_equal": cold_warm_equal,
            }
        )
        if diagnostic_level in {"STANDARD", "FULL"}:
            diagnostic = {
                "probe_id": probe.probe_id,
                "query_quality_ref": quality_ref,
                "cold": _receipt_diagnostic(dynamic_narrow, include_id=diagnostic_level == "FULL"),
                "wide_after_narrow": _receipt_diagnostic(
                    dynamic_wide, include_id=diagnostic_level == "FULL"
                ),
                "warm": _receipt_diagnostic(dynamic_warm, include_id=diagnostic_level == "FULL"),
            }
            diagnostics.append(diagnostic)

    prewide_refs: dict[str, dict[str, Any]] = {}
    for probe in reversed(_PATH_PROBES):
        wide_first = _sample_probe_tile(prewide, wide, probe)
        narrow_after = _sample_probe_tile(prewide, narrow, probe)
        reverse_queries[probe.probe_id] = _query_probe(scenario.query, probe)
        wide_first_ref = _canonical_tile_ref(wide_first)
        narrow_after_ref = _canonical_tile_ref(narrow_after)
        prewide_equal = wide_first_ref == narrow_after_ref
        invariant_flags.append(prewide_equal)
        prewide_refs[probe.probe_id] = wide_first_ref
        if diagnostic_level == "FULL":
            diagnostics.append(
                {
                    "probe_id": f"{probe.probe_id}:prewide",
                    "wide_first": _receipt_diagnostic(wide_first, include_id=True),
                    "narrow_after": _receipt_diagnostic(narrow_after, include_id=True),
                }
            )

    for canonical_probe in canonical_probes:
        probe_id = str(canonical_probe["probe_id"])
        dynamic_ref = canonical_probe["canonical_tile_ref"]
        prewide_equal = dynamic_ref == prewide_refs[probe_id]
        query_order_equal = (
            _query_quality_ref(forward_queries[probe_id])["semantic_hash"]
            == _query_quality_ref(reverse_queries[probe_id])["semantic_hash"]
        )
        canonical_probe["prewide_dynamic_equal"] = prewide_equal
        canonical_probe["query_order_equal"] = query_order_equal
        invariant_flags.extend((prewide_equal, query_order_equal))

    secondary_tile = _sample_probe_tile(dynamic, narrow, _SECONDARY_RADIUS_PROBE)
    secondary_query = _query_probe(scenario.query, _SECONDARY_RADIUS_PROBE)
    probe_radius_identity = (
        secondary_tile.payload.key.surface_realization_id
        == scenario.surface_realization_id
        == forward_queries["EVENT_RT8"].surface_realization_id
        == secondary_query.surface_realization_id
    )
    invariant_flags.append(probe_radius_identity)

    refinement = _refinement_witness(
        forward_queries["WITNESS_RT8"],
        forward_queries["WITNESS_RT10"],
        PRIMARY_QUERY_PROBE_RADIUS_MM,
    )
    invariant_flags.append(bool(refinement["passed"]))
    geometry = _path_geometry_audit(
        fixture,
        current,
        offsets_by_fixture[fixture.fixture_id],
    )
    invariant_flags.extend(
        (bool(geometry["endpoint_guard_pass"]), bool(geometry["full_100_mm_path_pass"]))
    )

    dynamic_stats = dynamic.stats
    prewide_stats = prewide.stats
    cache_audit = {
        "tile_requests": dynamic_stats.tile_requests + prewide_stats.tile_requests,
        "cache_hits": dynamic_stats.cache_hits + prewide_stats.cache_hits,
        "cache_misses": dynamic_stats.cache_misses + prewide_stats.cache_misses,
        "generated_tiles": dynamic_stats.generated_tiles + prewide_stats.generated_tiles,
        "regenerated_tiles": dynamic_stats.regenerated_tiles + prewide_stats.regenerated_tiles,
        "max_resident_payload_bytes": max(
            dynamic_stats.memory_payload_bytes,
            prewide_stats.memory_payload_bytes,
        ),
        "payload_within_budget": dynamic_stats.payload_within_budget
        and prewide_stats.payload_within_budget,
        "full_domain_rt10_dense_created": dynamic_stats.full_domain_rt10_dense_created
        or prewide_stats.full_domain_rt10_dense_created,
    }
    invariant_flags.extend(
        (
            bool(cache_audit["payload_within_budget"]),
            not bool(cache_audit["full_domain_rt10_dense_created"]),
        )
    )

    path_semantic = {
        "scenario_id": scenario.scenario_id,
        "surface_realization_id": scenario.surface_realization_id,
        "fixture_id": fixture.fixture_id,
        "footprint_id": current.footprint_id,
        "geometry": geometry,
        "canonical_probes": canonical_probes,
        "secondary_probe_radius_tile_ref": _canonical_tile_ref(secondary_tile),
        "secondary_probe_radius_query_ref_hash": _query_quality_ref(secondary_query)[
            "semantic_hash"
        ],
        "probe_radius_identity_invariant": probe_radius_identity,
        "refinement": refinement,
    }
    overall_pass = all(invariant_flags)
    result: dict[str, Any] = {
        **path_semantic,
        "common_random_number_group_id": scenario.common_random_number_group_id,
        "overlap_peer_fixture_id": overlap_peer,
        "diagnostic_level": "FULL" if not overall_pass else diagnostic_level,
        "semantic_result_hash": semantic_hash(path_semantic),
        "cache_audit": cache_audit,
        "query_count": len(_PATH_PROBES) * 2 + 1,
        "event_probe_count": 1,
        "logical_step_count": 3,
        "materialization_request_count": int(cache_audit["tile_requests"]),
        "overall_pass": overall_pass,
    }
    if diagnostics or not overall_pass:
        result["diagnostics"] = diagnostics
    if not overall_pass:
        result["failure"] = {
            "failure_family": "CONTRACT_REJECTION",
            "reason_code": "M02_M01_COMPATIBILITY_INVARIANT_FAILED",
            "source_identity": "VALIDATION_ONLY",
        }
    # Receipt IDs, when FULL diagnostics requested them, are intentionally
    # outside path_semantic and therefore outside semantic_result_hash.
    return result


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _parameter_balance(scenarios: list[_Scenario]) -> dict[str, dict[str, int]]:
    fields = (
        "H",
        "Sq_over_reference_Rt",
        "lc_over_reference_Rt",
        "anisotropy_ratio",
        "anisotropy_direction_rad",
    )
    return {
        field: dict(sorted(Counter(str(item.parameter_point[field]) for item in scenarios).items()))
        for field in fields
    }


def run_m01_compatibility_panel(
    panel: M01CompatibilityPanel | str = M01CompatibilityPanel.SMOKE_4,
    *,
    root_seed: int = ROOT_SEED_DEFAULT,
) -> dict[str, Any]:
    """Run one frozen 20/320/1280-path M01 compatibility panel.

    The returned object is JSON-serializable.  It contains wall time and cache
    diagnostics, while ``semantic_result_hash`` is computed only from stable
    scenario, surface, footprint, query-quality, and tile-content evidence.
    """

    selected = _resolve_panel(panel)
    policy = _PANEL_POLICIES[selected]
    if not 0 <= root_seed < 1 << 128:
        raise ValueError("root_seed must be an unsigned 128-bit integer")
    started = time.perf_counter()
    rss_before = _peak_rss_bytes()
    provider = SurfaceProvider()
    descriptor = make_synthetic_source_descriptor(boundary_mode=BoundaryMode.ERROR)
    scenarios: list[_Scenario] = []
    paths: list[dict[str, Any]] = []
    domain_checks: list[dict[str, Any]] = []

    for scenario_index in range(policy.scenario_count):
        scenario = _create_scenario(provider, descriptor, scenario_index, root_seed)
        scenarios.append(scenario)
        domain = scenario.handle.realization.logical_domain
        footprints: dict[str, QueryFootprint] = {}
        offsets_by_fixture: dict[str, NDArray[np.float64]] = {}
        for fixture in GEOMETRY_FIXTURES:
            footprint, offsets = _derive_fixture_footprint(fixture, domain)
            footprints[fixture.fixture_id] = footprint
            offsets_by_fixture[fixture.fixture_id] = offsets
        domain_check = _domain_error_audit(domain)
        domain_checks.append(
            {
                "scenario_id": scenario.scenario_id,
                "surface_realization_id": scenario.surface_realization_id,
                **domain_check,
            }
        )
        diagnostic_level = (
            "STANDARD"
            if selected is M01CompatibilityPanel.STRESS_256
            and scenario_index < policy.standard_witness_scenarios
            else policy.diagnostic_level
        )
        for fixture in GEOMETRY_FIXTURES:
            paths.append(
                _run_fixture_path(
                    scenario,
                    fixture,
                    footprints,
                    offsets_by_fixture,
                    diagnostic_level,
                )
            )

    surface_ids = {item.surface_realization_id for item in scenarios}
    scenario_ids = {item.scenario_id for item in scenarios}
    failures = [
        {
            "scenario_id": item["scenario_id"],
            "fixture_id": item["fixture_id"],
            **item["failure"],
        }
        for item in paths
        if "failure" in item
    ]
    semantic_payload = {
        "schema_version": M01_COMPATIBILITY_SCHEMA_VERSION,
        "panel_id": selected.value,
        "scenario_ids": [item.scenario_id for item in scenarios],
        "surface_realization_ids": [item.surface_realization_id for item in scenarios],
        "path_semantic_hashes": [str(item["semantic_result_hash"]) for item in paths],
        "domain_reason_codes": [item["reason_code"] for item in domain_checks],
        "surface_scale_reference_Rt_mm": SURFACE_SCALE_REFERENCE_RT_MM,
        "normal_path_builds_full_domain_rt10_dense": NORMAL_PATH_BUILDS_FULL_DOMAIN_RT10_DENSE,
    }
    elapsed = time.perf_counter() - started
    cache_totals = {
        field: sum(int(item["cache_audit"][field]) for item in paths)
        for field in (
            "tile_requests",
            "cache_hits",
            "cache_misses",
            "generated_tiles",
            "regenerated_tiles",
        )
    }
    cache_totals["max_resident_payload_bytes"] = max(
        int(item["cache_audit"]["max_resident_payload_bytes"]) for item in paths
    )
    expected_paths = policy.scenario_count * len(GEOMETRY_FIXTURES)
    overall_pass = (
        len(scenario_ids) == policy.scenario_count
        and len(surface_ids) == policy.scenario_count
        and len(paths) == expected_paths
        and all(bool(item["passed"]) for item in domain_checks)
        and all(bool(item["overall_pass"]) for item in paths)
        and not NORMAL_PATH_BUILDS_FULL_DOMAIN_RT10_DENSE
    )
    report: dict[str, Any] = {
        "schema_version": M01_COMPATIBILITY_SCHEMA_VERSION,
        "panel_id": selected.value,
        "source_identity": "VALIDATION_ONLY",
        "maturity": {
            "theory_defined": "SPEC_DEFINED",
            "code_implemented": "PASSED_WITH_EVIDENCE",
            "numerically_verified": "PASSED_WITH_EVIDENCE" if overall_pass else "FAILED",
            "experimentally_validated": "BLOCKED_UNAVAILABLE",
        },
        "certification_status": "NOT_CERTIFIABLE",
        "physical_owner": "M02_VALIDATION_ONLY_M01_COMPATIBILITY_OWNER",
        "physical_scope": "geometry/cache compatibility only; no A/B physics",
        "panel_design": {
            "algorithm_id": "M02_BALANCED_FACTORIAL_GREEDY_MAXIMIN_1",
            "common_random_number_policy": (
                "one independent SurfaceRealization per scenario shared by all five fixtures"
            ),
            "root_seed": root_seed,
            "surface_scale_reference_Rt_mm": SURFACE_SCALE_REFERENCE_RT_MM,
            "query_probe_radii_mm": [
                SECONDARY_QUERY_PROBE_RADIUS_MM,
                PRIMARY_QUERY_PROBE_RADIUS_MM,
            ],
            "parameter_balance": _parameter_balance(scenarios),
        },
        "diagnostic_policy": {
            "default_level": policy.diagnostic_level,
            "standard_witness_scenarios": policy.standard_witness_scenarios,
            "failure_upgrade": "FULL",
        },
        "counts": {
            "scenario_count": len(scenarios),
            "independent_surface_realization_count": len(surface_ids),
            "fixture_count": len(GEOMETRY_FIXTURES),
            "full_path_count": len(paths),
            "expected_full_path_count": expected_paths,
            "query_count": sum(int(item["query_count"]) for item in paths),
            "logical_step_count": sum(int(item["logical_step_count"]) for item in paths),
            "event_probe_count": sum(int(item["event_probe_count"]) for item in paths),
            "materialization_request_count": sum(
                int(item["materialization_request_count"]) for item in paths
            ),
            "failure_count": len(failures),
        },
        "fixtures": [item.as_dict() for item in GEOMETRY_FIXTURES],
        "scenarios": [item.audit_dict() for item in scenarios],
        "paths": paths,
        "domain_error_checks": domain_checks,
        "failures": failures,
        "cache": {
            **cache_totals,
            "cache_receipts_are_diagnostic": True,
            "receipt_ids_excluded_from_semantic_comparisons": True,
            "normal_path_builds_full_domain_rt10_dense": (
                NORMAL_PATH_BUILDS_FULL_DOMAIN_RT10_DENSE
            ),
        },
        "performance": {
            "wall_time_seconds": elapsed,
            "peak_rss_before_bytes": rss_before,
            "peak_rss_after_bytes": _peak_rss_bytes(),
        },
        "semantic_result_hash": semantic_hash(semantic_payload),
        "overall_pass": overall_pass,
    }
    compact = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    report["performance"]["audit_json_size_estimate_bytes"] = len(compact.encode("utf-8"))
    return report


def write_m01_compatibility_report(path: str | Path, report: dict[str, Any]) -> Path:
    """Atomically write a compatibility audit JSON without adding runtime services."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)
    return destination


__all__ = [
    "GEOMETRY_FIXTURES",
    "M01_COMPATIBILITY_SCHEMA_VERSION",
    "PATH_LENGTH_MM",
    "SURFACE_SCALE_REFERENCE_RT_MM",
    "GeometryFixture",
    "M01CompatibilityPanel",
    "run_m01_compatibility_panel",
    "write_m01_compatibility_report",
]
