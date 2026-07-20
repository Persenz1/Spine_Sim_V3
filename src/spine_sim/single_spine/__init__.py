"""Stable high-level entry points for the M03 single-spine product."""

from .campaigns import (
    frozen_campaign_streaming_plan,
    frozen_interaction_records,
    frozen_streaming_plan,
    frozen_surface_specs,
    frozen_synthetic_surface_specs,
    frozen_trend_campaign,
    frozen_trend_cases,
)
from .contracts import (
    canonical_local_frame,
    m03_maturity,
    m03_status,
    make_baseline_parameter_bundle,
    make_embedded_request,
    make_initial_single_spine_state,
    make_metadata,
    make_rigid_pose,
    make_standalone_request,
    parameter_evidence,
)
from .kernel import IntrinsicSingleSpineKernel, make_needle_identity
from .persistence import (
    StandalonePersistenceContext,
    StandalonePersistenceResult,
    persist_standalone_execution,
)
from .plot_recipes import (
    build_plot_recipe_manifest_records,
    get_m03_plot_recipe,
    m03_plot_recipe_registry,
    m03_plot_recipes,
)
from .result_extension import m03_dataset_ids, m03_field_metadata, m03_result_extension
from .standalone import (
    ResolvedInitialPose,
    StandaloneDriverConfig,
    StandaloneExecution,
    StandaloneSingleSpineDriver,
    UnavailableInitialPose,
    run_standalone_single_spine,
)
from .summaries import build_m03_summaries, rebuild_m03_summaries

__all__ = [
    "IntrinsicSingleSpineKernel",
    "ResolvedInitialPose",
    "StandaloneDriverConfig",
    "StandaloneExecution",
    "StandalonePersistenceContext",
    "StandalonePersistenceResult",
    "StandaloneSingleSpineDriver",
    "UnavailableInitialPose",
    "build_m03_summaries",
    "build_plot_recipe_manifest_records",
    "canonical_local_frame",
    "frozen_campaign_streaming_plan",
    "frozen_interaction_records",
    "frozen_streaming_plan",
    "frozen_surface_specs",
    "frozen_synthetic_surface_specs",
    "frozen_trend_campaign",
    "frozen_trend_cases",
    "get_m03_plot_recipe",
    "m03_dataset_ids",
    "m03_field_metadata",
    "m03_maturity",
    "m03_plot_recipe_registry",
    "m03_plot_recipes",
    "m03_result_extension",
    "m03_status",
    "make_baseline_parameter_bundle",
    "make_embedded_request",
    "make_initial_single_spine_state",
    "make_metadata",
    "make_needle_identity",
    "make_rigid_pose",
    "make_standalone_request",
    "parameter_evidence",
    "persist_standalone_execution",
    "rebuild_m03_summaries",
    "run_standalone_single_spine",
]
