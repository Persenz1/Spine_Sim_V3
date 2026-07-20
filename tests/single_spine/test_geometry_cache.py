from __future__ import annotations

import numpy as np

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.single_spine import geometry as geometry_module
from spine_sim.single_spine.contracts import (
    canonical_local_frame,
    make_baseline_parameter_bundle,
)
from spine_sim.single_spine.geometry import (
    build_composite_needle_geometry,
    engineering_initial_axis,
    make_swept_needle_geometry,
    resolve_tip_pose,
)


def test_bounded_immutable_geometry_cache_preserves_frozen_identities() -> None:
    bundle = make_baseline_parameter_bundle()
    frame = canonical_local_frame()
    axis = np.asarray(
        engineering_initial_axis(frame, bundle.needle.alpha_rad, bundle.needle.beta_rad),
        dtype=np.float64,
    )
    center = np.array([73.125, 74.875, 0.625], dtype=np.float64)
    root = center - bundle.needle.exposed_length_mm * axis
    pose = resolve_tip_pose(
        rigid_root_global_mm=tuple(float(item) for item in root),  # type: ignore[arg-type]
        local_frame=frame,
        needle=bundle.needle,
    )

    build_composite_needle_geometry.cache_clear()
    first = build_composite_needle_geometry(
        tip_pose=pose,
        needle=bundle.needle,
        axial_sample_count=17,
        radial_sample_count=8,
    )
    second = build_composite_needle_geometry(
        tip_pose=pose,
        needle=bundle.needle,
        axial_sample_count=17,
        radial_sample_count=8,
    )
    sweep = make_swept_needle_geometry((first, second))
    repeated_sweep = make_swept_needle_geometry([first, second])

    assert second is first
    assert repeated_sweep is sweep
    assert first.geometry_hash == semantic_hash(first.identity_payload())
    assert first.geometry_id == stable_content_id(
        "m03_composite_needle_geometry",
        first.identity_payload(),
    )
    assert sweep.sweep_hash == semantic_hash(sweep.identity_payload())
    assert sweep.sweep_id == stable_content_id(
        "m03_swept_needle_geometry",
        sweep.identity_payload(),
    )
    assert build_composite_needle_geometry.cache_info().maxsize == 4
    assert geometry_module._make_swept_needle_geometry_cached.cache_info().maxsize == 4
    assert geometry_module._composite_identity_pair.cache_info().maxsize == 4
    assert geometry_module._sweep_identity_pair.cache_info().maxsize == 4
