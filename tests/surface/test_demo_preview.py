from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from spine_sim.foundation.errors import QueryError
from spine_sim.foundation.integrity import VerifyMode
from spine_sim.foundation.reader import ResultReader
from spine_sim.surface import (
    SurfaceFamily,
    SurfaceProvider,
    make_latent_noise_identity,
    make_synthetic_source_descriptor,
)
from spine_sim.surface.demo_validation_only import DemoArtifacts, generate_validation_demo
from spine_sim.surface.materialization import sample_visualization_window
from spine_sim.surface.preview.recipes import (
    HEIGHT_MAP_2D,
    OBLIQUE_3D_SURFACE,
    render_preview,
    sample_from_result_reader,
)
from spine_sim.surface.result_extension import (
    SOURCE_AVAILABILITY_DATASET,
    SURFACE_REALIZATIONS_DATASET,
    VALIDATION_RESULTS_DATASET,
)
from spine_sim.surface.synthetic import SyntheticEvaluator, synthetic_parameters_for_tier


@pytest.fixture(scope="module")
def demo(tmp_path_factory: pytest.TempPathFactory) -> DemoArtifacts:
    destination = tmp_path_factory.mktemp("m01-demo") / "M01_TEST.spine-result"
    return generate_validation_demo(destination, grid_shape=(18, 18), render_previews=False)


def test_demo_bundle_full_integrity_reader_roundtrip_and_validation_matrix(
    demo: DemoArtifacts,
) -> None:
    reader = ResultReader.open(demo.bundle_path, VerifyMode.FULL)
    realizations = reader.query(SURFACE_REALIZATIONS_DATASET).read_all().to_pylist()
    assert len(realizations) == 3
    assert len({row["surface_realization_id"] for row in realizations}) == 3
    assert {row["latent_noise_id"] for row in realizations} == {realizations[0]["latent_noise_id"]}
    assert {row["material_label"] for row in realizations} == {"synthetic_unidentified"}

    validation = (
        reader.query(VALIDATION_RESULTS_DATASET, include_non_default=True).read_all().to_pylist()
    )
    fixture_names = {row["fixture_id"] for row in validation}
    assert validation and all(row["passed"] for row in validation)
    assert {
        "analytic_plane",
        "analytic_slope",
        "analytic_sinusoid_1d",
        "analytic_gaussian_bump",
        "analytic_gaussian_pit",
        "analytic_groove_v",
        "analytic_known_nearest_feature_switch",
        "validation_only_heightfield_triangulation",
    } <= fixture_names

    unavailable = (
        reader.query(SOURCE_AVAILABILITY_DATASET, include_non_default=True).read_all().to_pylist()
    )
    assert {row["reason_code"] for row in unavailable} == {
        "M01_MEASURED_IMPORT_DEFERRED",
        "M01_EXTERNAL_MESH_IMPORT_DEFERRED",
    }
    summary = json.loads(demo.summary_path.read_text(encoding="utf-8"))
    assert summary["full_integrity_verification"] == "PASS"
    assert summary["full_domain_rt10_dense_created"] is False
    assert summary["experimentally_validated"] == "BLOCKED_UNAVAILABLE"
    assert summary["certification_status"] == "NOT_CERTIFIABLE"

    visible_ids = {item.dataset_id for item in reader.list_datasets().entries}
    assert VALIDATION_RESULTS_DATASET not in visible_ids
    assert SOURCE_AVAILABILITY_DATASET not in visible_ids
    with pytest.raises(QueryError, match="explicit opt-in"):
        reader.query(VALIDATION_RESULTS_DATASET).read_all()
    relation_ids = {item["relation_id"] for item in reader.list_relations().relations}
    assert "m01.relation.realization_to_surface_validation_results" in relation_ids


def test_saved_samples_render_only_the_two_frozen_recipes(
    demo: DemoArtifacts, tmp_path: Path
) -> None:
    pytest.importorskip("matplotlib")
    reader = ResultReader.open(demo.bundle_path)
    sample = sample_from_result_reader(reader, demo.case_ids[0])
    original_hash = sample.source_hash
    manifests = []
    for recipe in (HEIGHT_MAP_2D, OBLIQUE_3D_SURFACE):
        output = tmp_path / f"{recipe}.png"
        manifest = render_preview(sample, recipe, output, dpi=72, maximum_3d_grid=32)
        assert output.is_file() and output.stat().st_size > 0
        assert output.with_suffix(".plot_manifest.json").is_file()
        assert manifest.recipe == recipe
        assert manifest.source_data_hash == original_hash
        assert manifest.source_identity.startswith("DEV_POLICY")
        assert manifest.certification_status == "NOT_CERTIFIABLE"
        manifests.append(manifest)
    assert {item.recipe for item in manifests} == {HEIGHT_MAP_2D, OBLIQUE_3D_SURFACE}
    assert sample.source_hash == original_hash
    assert np.isfinite(sample.height_mm).all()

    with pytest.raises(ValueError, match="unsupported"):
        render_preview(sample, "contact_force_heatmap", tmp_path / "forbidden.png")
    with pytest.raises(ValueError, match="material identity"):
        render_preview(
            sample,
            HEIGHT_MAP_2D,
            tmp_path / "material.png",
            title_label="concrete",
        )


def test_plot_before_query_does_not_advance_synthetic_state(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    provider = SurfaceProvider()
    spec_result = provider.create_surface_spec(
        make_synthetic_source_descriptor(),
        SurfaceFamily.SELF_AFFINE_GAUSSIAN,
        synthetic_parameters_for_tier(
            "gentle", lambda_min_declared_trust_mm=9.375, modes_per_band=8
        ),
    )
    assert spec_result.spec is not None
    latent = make_latent_noise_identity(20260718, 9, latent_noise_namespace="m01.plot-order")
    realization_result = provider.create_realization(
        make_synthetic_source_descriptor(), spec_result.spec, latent_identity=latent
    )
    assert realization_result.handle is not None
    evaluator = realization_result.handle.evaluator
    reference = SyntheticEvaluator(spec_result.spec, latent).evaluate(
        [11.25, 72.5, 143.75], [91.0, 4.5, 52.25], derivative_order=2
    )

    sample = sample_visualization_window(
        evaluator,
        surface_realization_id=realization_result.handle.realization.surface_realization_id,
        grid_shape=(24, 24),
    )
    render_preview(sample, HEIGHT_MAP_2D, tmp_path / "plot-before-query.png", dpi=72)
    after_plot = evaluator.evaluate([11.25, 72.5, 143.75], [91.0, 4.5, 52.25], derivative_order=2)

    np.testing.assert_array_equal(after_plot.height, reference.height)
    np.testing.assert_array_equal(after_plot.gradient, reference.gradient)
    np.testing.assert_array_equal(after_plot.hessian, reference.hessian)
