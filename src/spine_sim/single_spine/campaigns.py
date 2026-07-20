"""Frozen M03 single-spine trend and synthetic-surface campaign plans.

This module describes cases; it does not schedule work, evaluate a surface, or
retain solver histories.  The primary plan is the deliberately sparse design
from M03 requirements section 4.2, not a Cartesian DOE.  M01 owns surface
identity, so the campaign stores public ``SurfaceSpec`` and latent-noise
identities and lets a runner create/open the corresponding realization.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from spine_sim.surface import (
    BoundaryMode,
    LatentNoiseIdentity,
    RoughnessTier,
    SurfaceFamily,
    SurfaceProvider,
    SurfaceRealization,
    SurfaceSpec,
    make_latent_noise_identity,
    make_synthetic_source_descriptor,
    synthetic_parameters_for_tier,
)

from .contracts import (
    SURFACE_SCALE_REFERENCE_RT_MM,
    MountMode,
    SingleSpineParameterBundle,
    make_baseline_parameter_bundle,
)

TREND_CASE_COUNT = 36
INTERACTION_RECORD_COUNT = 12
SHARED_INTERACTION_REFERENCE_COUNT = 6
SYNTHETIC_CAMPAIGN_CASE_COUNT = 38
FROZEN_TREND_PLAN_ID = "M03_FROZEN_TREND_36_V1"
FROZEN_STREAMING_PLAN_ID = "M03_SYNTHETIC_36_PLUS_2_STREAMING_V1"

RT_GRID_MM = (0.05, 0.10)
DIAMETER_GRID_MM = (0.60, 0.80)
ALPHA_GRID_DEG = (50.0, 60.0, 70.0, 80.0)
YOUNGS_MODULUS_GRID_MPA = (200000.0, 205000.0, 210000.0)
POISSON_RATIO_GRID = (0.28, 0.29, 0.30)
FRICTION_GRID = (0.15, 0.25, 0.40, 0.60, 0.80)
SPRING_STIFFNESS_GRID_N_PER_MM = (0.1, 0.2, 0.5, 1.0, 2.0)


class TrendPanel(StrEnum):
    """Frozen comparison panels; membership may overlap after de-duplication."""

    GEOMETRY_MAIN_EFFECT = "GEOMETRY_MAIN_EFFECT"
    FRICTION_CONDITIONAL_OFAT = "FRICTION_CONDITIONAL_OFAT"
    MOUNT_CONDITIONAL_OFAT = "MOUNT_CONDITIONAL_OFAT"
    BENDING_CONDITIONAL_OFAT = "BENDING_CONDITIONAL_OFAT"
    YOUNGS_MODULUS_CONDITIONAL_OFAT = "YOUNGS_MODULUS_CONDITIONAL_OFAT"
    POISSON_RATIO_CONDITIONAL_OFAT = "POISSON_RATIO_CONDITIONAL_OFAT"
    RT_FRICTION_INTERACTION = "RT_FRICTION_INTERACTION"
    DIAMETER_SPRING_INTERACTION = "DIAMETER_SPRING_INTERACTION"
    ALPHA_MOUNT_INTERACTION = "ALPHA_MOUNT_INTERACTION"


class SurfaceCampaignRole(StrEnum):
    PRIMARY_MEDIUM = "PRIMARY_MEDIUM"
    GENTLE_SMOKE = "GENTLE_SMOKE"
    SHARP_SMOKE = "SHARP_SMOKE"


class CampaignRunKind(StrEnum):
    PRIMARY_TREND = "PRIMARY_TREND"
    BASELINE_SMOKE = "BASELINE_SMOKE"


@dataclass(frozen=True, slots=True)
class TrendParameters:
    """The physical design coordinates that define one distinct trend case."""

    tip_radius_mm: float = 0.05
    diameter_mm: float = 0.80
    alpha_deg: float = 60.0
    youngs_modulus_mpa: float | None = 210000.0
    poisson_ratio: float | None = 0.30
    friction_coefficient: float = 0.40
    bending_enabled: bool = True
    mount_mode: MountMode = MountMode.INDEPENDENT_AXIAL_SPRINGS
    spring_stiffness_n_per_mm: float | None = 0.5

    def __post_init__(self) -> None:
        for name in ("tip_radius_mm", "diameter_mm", "alpha_deg", "friction_coefficient"):
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.tip_radius_mm <= 0.0 or self.diameter_mm <= 0.0:
            raise ValueError("tip radius and diameter must be positive")
        if not 0.0 < self.alpha_deg < 90.0:
            raise ValueError("alpha_deg must lie strictly between zero and 90 degrees")
        if self.friction_coefficient < 0.0:
            raise ValueError("friction_coefficient cannot be negative")
        if self.bending_enabled:
            if self.youngs_modulus_mpa is None or self.poisson_ratio is None:
                raise ValueError("bending-on trend cases require E and nu")
            if not math.isfinite(self.youngs_modulus_mpa) or self.youngs_modulus_mpa <= 0.0:
                raise ValueError("youngs_modulus_mpa must be finite and positive")
            if not math.isfinite(self.poisson_ratio) or not -1.0 < self.poisson_ratio < 0.5:
                raise ValueError("poisson_ratio is outside the elastic stability range")
        elif self.youngs_modulus_mpa is not None or self.poisson_ratio is not None:
            raise ValueError("bending-off trend cases must not carry meaningless E or nu")
        if self.mount_mode is MountMode.RIGID_MOUNT:
            if self.spring_stiffness_n_per_mm is not None:
                raise ValueError("rigid-mount trend cases must not carry an effective ks")
        elif self.spring_stiffness_n_per_mm is None:
            raise ValueError("independent-spring trend cases require an explicit ks")
        elif (
            not math.isfinite(self.spring_stiffness_n_per_mm)
            or self.spring_stiffness_n_per_mm <= 0.0
        ):
            raise ValueError("spring stiffness must be finite and positive")

    def parameter_bundle(self) -> SingleSpineParameterBundle:
        """Expand all frozen defaults through the public M03 contract factory."""

        return make_baseline_parameter_bundle(
            tip_radius_mm=self.tip_radius_mm,
            diameter_mm=self.diameter_mm,
            alpha_deg=self.alpha_deg,
            youngs_modulus_mpa=(
                210000.0 if self.youngs_modulus_mpa is None else self.youngs_modulus_mpa
            ),
            poisson_ratio=0.30 if self.poisson_ratio is None else self.poisson_ratio,
            friction_coefficient=self.friction_coefficient,
            bending_enabled=self.bending_enabled,
            mount_mode=self.mount_mode,
            spring_stiffness_n_per_mm=self.spring_stiffness_n_per_mm,
        )


BASELINE_TREND_PARAMETERS = TrendParameters()


@dataclass(frozen=True, slots=True)
class TrendCase:
    ordinal: int
    case_id: str
    parameters: TrendParameters
    parameter_bundle: SingleSpineParameterBundle
    panels: tuple[TrendPanel, ...]

    def __post_init__(self) -> None:
        if self.ordinal < 0:
            raise ValueError("trend case ordinal cannot be negative")
        if not self.case_id or not self.panels or len(set(self.panels)) != len(self.panels):
            raise ValueError("trend case requires an ID and unique panel memberships")
        if self.parameter_bundle != self.parameters.parameter_bundle():
            raise ValueError("trend case parameters and expanded parameter bundle disagree")
        expected = f"m03-trend-{self.parameter_bundle.parameter_bundle_id}"
        if self.case_id != expected:
            raise ValueError("trend case ID must be derived from the parameter bundle identity")

    @property
    def design_id(self) -> str:
        """The parameter-bundle identity is the design identity before surface pairing."""

        return self.parameter_bundle.parameter_bundle_id


@dataclass(frozen=True, slots=True)
class InteractionRecord:
    """One of the 12 requested interaction observations.

    ``shared_case_reference`` is populated only when the requested interaction
    point was already present in geometry/conditional OFAT.  It therefore
    records reuse rather than scheduling a duplicate run.
    """

    record_id: str
    panel: TrendPanel
    first_parameter: str
    first_value: float | str
    second_parameter: str
    second_value: float | str
    case_id: str
    shared_case_reference: str | None
    shared_from_panel: TrendPanel | None

    def __post_init__(self) -> None:
        interaction_panels = {
            TrendPanel.RT_FRICTION_INTERACTION,
            TrendPanel.DIAMETER_SPRING_INTERACTION,
            TrendPanel.ALPHA_MOUNT_INTERACTION,
        }
        if self.panel not in interaction_panels:
            raise ValueError("interaction record must use an interaction panel")
        if not self.record_id or not self.first_parameter or not self.second_parameter:
            raise ValueError("interaction record identities cannot be empty")
        if (self.shared_case_reference is None) != (self.shared_from_panel is None):
            raise ValueError("shared case reference and source panel must be declared together")
        if self.shared_case_reference is not None and self.shared_case_reference != self.case_id:
            raise ValueError("an interaction may only reuse its resolved distinct case")

    @property
    def reuses_existing_case(self) -> bool:
        return self.shared_case_reference is not None


@dataclass(frozen=True, slots=True)
class SharedCaseReference:
    interaction_record_id: str
    case_id: str
    existing_panel: TrendPanel


@dataclass(frozen=True, slots=True)
class TrendCampaignPlan:
    plan_id: str
    cases: tuple[TrendCase, ...]
    interaction_records: tuple[InteractionRecord, ...]
    shared_case_references: tuple[SharedCaseReference, ...]

    def __post_init__(self) -> None:
        if self.plan_id != FROZEN_TREND_PLAN_ID:
            raise ValueError("unsupported M03 trend plan ID")
        if len(self.cases) != TREND_CASE_COUNT:
            raise ValueError("the frozen M03 trend plan must contain exactly 36 cases")
        if len(self.interaction_records) != INTERACTION_RECORD_COUNT:
            raise ValueError("the frozen M03 plan must preserve 12 interaction records")
        if len(self.shared_case_references) != SHARED_INTERACTION_REFERENCE_COUNT:
            raise ValueError("the frozen M03 plan must preserve six shared case references")
        if tuple(case.ordinal for case in self.cases) != tuple(range(TREND_CASE_COUNT)):
            raise ValueError("trend case ordinals must be contiguous and deterministic")
        case_ids = tuple(case.case_id for case in self.cases)
        if len(set(case_ids)) != TREND_CASE_COUNT:
            raise ValueError("trend case IDs must be distinct")
        parameters = tuple(case.parameters for case in self.cases)
        if len(set(parameters)) != TREND_CASE_COUNT:
            raise ValueError("trend parameter points must be distinct")
        bundle_ids = tuple(case.parameter_bundle.parameter_bundle_id for case in self.cases)
        if len(set(bundle_ids)) != TREND_CASE_COUNT:
            raise ValueError("trend parameter bundles must be distinct")
        if any(record.case_id not in case_ids for record in self.interaction_records):
            raise ValueError("every interaction record must reference a distinct trend case")
        expected_shared = tuple(
            SharedCaseReference(
                record.record_id,
                record.case_id,
                record.shared_from_panel,
            )
            for record in self.interaction_records
            if record.shared_from_panel is not None
        )
        if self.shared_case_references != expected_shared:
            raise ValueError("shared case references must be the exact interaction reuse records")
        expected_panel_counts = {
            TrendPanel.GEOMETRY_MAIN_EFFECT: 16,
            TrendPanel.FRICTION_CONDITIONAL_OFAT: 5,
            TrendPanel.MOUNT_CONDITIONAL_OFAT: 6,
            TrendPanel.BENDING_CONDITIONAL_OFAT: 2,
            TrendPanel.YOUNGS_MODULUS_CONDITIONAL_OFAT: 3,
            TrendPanel.POISSON_RATIO_CONDITIONAL_OFAT: 3,
            TrendPanel.RT_FRICTION_INTERACTION: 4,
            TrendPanel.DIAMETER_SPRING_INTERACTION: 4,
            TrendPanel.ALPHA_MOUNT_INTERACTION: 4,
        }
        if {
            panel: len(self.cases_for_panel(panel)) for panel in TrendPanel
        } != expected_panel_counts:
            raise ValueError("frozen trend panel membership is incomplete")

    @property
    def baseline_case(self) -> TrendCase:
        return self.case_for_parameters(BASELINE_TREND_PARAMETERS)

    def case_for_parameters(self, parameters: TrendParameters) -> TrendCase:
        for case in self.cases:
            if case.parameters == parameters:
                return case
        raise KeyError("parameter point is not part of the frozen 36-case plan")

    def cases_for_panel(self, panel: TrendPanel) -> tuple[TrendCase, ...]:
        return tuple(case for case in self.cases if panel in case.panels)

    def iter_cases(self, start: int = 0, stop: int | None = None) -> Iterable[TrendCase]:
        resolved_stop = len(self.cases) if stop is None else stop
        if not 0 <= start <= resolved_stop <= len(self.cases):
            raise ValueError("invalid trend case slice")
        yield from self.cases[start:resolved_stop]


@dataclass(slots=True)
class _CaseBuilder:
    parameters: TrendParameters
    parameter_bundle: SingleSpineParameterBundle
    panels: list[TrendPanel]


def _add_case(
    builders: dict[TrendParameters, _CaseBuilder],
    parameters: TrendParameters,
    panel: TrendPanel,
) -> bool:
    existing = builders.get(parameters)
    if existing is not None:
        if panel not in existing.panels:
            existing.panels.append(panel)
        return False
    builders[parameters] = _CaseBuilder(parameters, parameters.parameter_bundle(), [panel])
    return True


def _spring_parameters(
    *,
    tip_radius_mm: float = 0.05,
    diameter_mm: float = 0.80,
    alpha_deg: float = 60.0,
    friction_coefficient: float = 0.40,
    youngs_modulus_mpa: float = 210000.0,
    poisson_ratio: float = 0.30,
    spring_stiffness_n_per_mm: float = 0.5,
) -> TrendParameters:
    return TrendParameters(
        tip_radius_mm=tip_radius_mm,
        diameter_mm=diameter_mm,
        alpha_deg=alpha_deg,
        youngs_modulus_mpa=youngs_modulus_mpa,
        poisson_ratio=poisson_ratio,
        friction_coefficient=friction_coefficient,
        bending_enabled=True,
        mount_mode=MountMode.INDEPENDENT_AXIAL_SPRINGS,
        spring_stiffness_n_per_mm=spring_stiffness_n_per_mm,
    )


def _rigid_parameters(*, alpha_deg: float = 60.0) -> TrendParameters:
    return TrendParameters(
        alpha_deg=alpha_deg,
        mount_mode=MountMode.RIGID_MOUNT,
        spring_stiffness_n_per_mm=None,
    )


def frozen_trend_campaign() -> TrendCampaignPlan:
    """Build the exact 36-case sparse trend design and its audit records."""

    builders: dict[TrendParameters, _CaseBuilder] = {}

    # 2 Rt x 2 d x 4 alpha = 16 geometry cases.
    for tip_radius_mm in RT_GRID_MM:
        for diameter_mm in DIAMETER_GRID_MM:
            for alpha_deg in ALPHA_GRID_DEG:
                _add_case(
                    builders,
                    _spring_parameters(
                        tip_radius_mm=tip_radius_mm,
                        diameter_mm=diameter_mm,
                        alpha_deg=alpha_deg,
                    ),
                    TrendPanel.GEOMETRY_MAIN_EFFECT,
                )

    # Conditional OFAT records are deliberately merged with the baseline case.
    for friction_coefficient in FRICTION_GRID:
        _add_case(
            builders,
            _spring_parameters(friction_coefficient=friction_coefficient),
            TrendPanel.FRICTION_CONDITIONAL_OFAT,
        )
    _add_case(builders, _rigid_parameters(), TrendPanel.MOUNT_CONDITIONAL_OFAT)
    for spring_stiffness_n_per_mm in SPRING_STIFFNESS_GRID_N_PER_MM:
        _add_case(
            builders,
            _spring_parameters(spring_stiffness_n_per_mm=spring_stiffness_n_per_mm),
            TrendPanel.MOUNT_CONDITIONAL_OFAT,
        )
    _add_case(builders, BASELINE_TREND_PARAMETERS, TrendPanel.BENDING_CONDITIONAL_OFAT)
    _add_case(
        builders,
        TrendParameters(
            youngs_modulus_mpa=None,
            poisson_ratio=None,
            bending_enabled=False,
        ),
        TrendPanel.BENDING_CONDITIONAL_OFAT,
    )
    for youngs_modulus_mpa in YOUNGS_MODULUS_GRID_MPA:
        _add_case(
            builders,
            _spring_parameters(youngs_modulus_mpa=youngs_modulus_mpa),
            TrendPanel.YOUNGS_MODULUS_CONDITIONAL_OFAT,
        )
    for poisson_ratio in POISSON_RATIO_GRID:
        _add_case(
            builders,
            _spring_parameters(poisson_ratio=poisson_ratio),
            TrendPanel.POISSON_RATIO_CONDITIONAL_OFAT,
        )

    interaction_specs: list[
        tuple[TrendPanel, str, float | str, str, float | str, TrendParameters]
    ] = []
    for tip_radius_mm in RT_GRID_MM:
        for friction_coefficient in (0.15, 0.80):
            interaction_specs.append(
                (
                    TrendPanel.RT_FRICTION_INTERACTION,
                    "tip_radius_mm",
                    tip_radius_mm,
                    "friction_coefficient",
                    friction_coefficient,
                    _spring_parameters(
                        tip_radius_mm=tip_radius_mm,
                        friction_coefficient=friction_coefficient,
                    ),
                )
            )
    for diameter_mm in DIAMETER_GRID_MM:
        for spring_stiffness_n_per_mm in (0.1, 2.0):
            interaction_specs.append(
                (
                    TrendPanel.DIAMETER_SPRING_INTERACTION,
                    "diameter_mm",
                    diameter_mm,
                    "spring_stiffness_n_per_mm",
                    spring_stiffness_n_per_mm,
                    _spring_parameters(
                        diameter_mm=diameter_mm,
                        spring_stiffness_n_per_mm=spring_stiffness_n_per_mm,
                    ),
                )
            )
    for alpha_deg in (50.0, 80.0):
        for mount_mode in (
            MountMode.RIGID_MOUNT,
            MountMode.INDEPENDENT_AXIAL_SPRINGS,
        ):
            parameters = (
                _rigid_parameters(alpha_deg=alpha_deg)
                if mount_mode is MountMode.RIGID_MOUNT
                else _spring_parameters(alpha_deg=alpha_deg)
            )
            interaction_specs.append(
                (
                    TrendPanel.ALPHA_MOUNT_INTERACTION,
                    "alpha_deg",
                    alpha_deg,
                    "mount_mode",
                    mount_mode.value,
                    parameters,
                )
            )

    pending_records: list[
        tuple[
            str,
            TrendPanel,
            str,
            float | str,
            str,
            float | str,
            TrendParameters,
            TrendPanel | None,
        ]
    ] = []
    for index, (
        panel,
        first_parameter,
        first_value,
        second_parameter,
        second_value,
        parameters,
    ) in enumerate(interaction_specs, start=1):
        existing = builders.get(parameters)
        shared_from = existing.panels[0] if existing is not None else None
        _add_case(builders, parameters, panel)
        pending_records.append(
            (
                f"M03_INTERACTION_{index:02d}",
                panel,
                first_parameter,
                first_value,
                second_parameter,
                second_value,
                parameters,
                shared_from,
            )
        )

    cases = tuple(
        TrendCase(
            ordinal=index,
            case_id=f"m03-trend-{builder.parameter_bundle.parameter_bundle_id}",
            parameters=builder.parameters,
            parameter_bundle=builder.parameter_bundle,
            panels=tuple(builder.panels),
        )
        for index, builder in enumerate(builders.values())
    )
    case_by_parameters = {case.parameters: case for case in cases}
    interaction_records = tuple(
        InteractionRecord(
            record_id=record_id,
            panel=panel,
            first_parameter=first_parameter,
            first_value=first_value,
            second_parameter=second_parameter,
            second_value=second_value,
            case_id=case_by_parameters[parameters].case_id,
            shared_case_reference=(case_by_parameters[parameters].case_id if shared_from else None),
            shared_from_panel=shared_from,
        )
        for (
            record_id,
            panel,
            first_parameter,
            first_value,
            second_parameter,
            second_value,
            parameters,
            shared_from,
        ) in pending_records
    )
    shared_case_references = tuple(
        SharedCaseReference(record.record_id, record.case_id, record.shared_from_panel)
        for record in interaction_records
        if record.shared_from_panel is not None
    )
    return TrendCampaignPlan(
        FROZEN_TREND_PLAN_ID,
        cases,
        interaction_records,
        shared_case_references,
    )


def frozen_trend_cases() -> tuple[TrendCase, ...]:
    return frozen_trend_campaign().cases


def frozen_interaction_records() -> tuple[InteractionRecord, ...]:
    return frozen_trend_campaign().interaction_records


@dataclass(frozen=True, slots=True)
class SyntheticSurfaceCampaignSpec:
    """One M01 specification plus the explicit seed used to realize it."""

    role: SurfaceCampaignRole
    roughness_tier: RoughnessTier
    root_seed: int
    surface_seed_index: int
    surface_spec: SurfaceSpec
    latent_noise_identity: LatentNoiseIdentity
    surface_realization: SurfaceRealization
    intended_case_count: int
    statistical_sample: bool = False

    def __post_init__(self) -> None:
        expected = {
            SurfaceCampaignRole.PRIMARY_MEDIUM: (RoughnessTier.MEDIUM, 30301, 36),
            SurfaceCampaignRole.GENTLE_SMOKE: (RoughnessTier.GENTLE, 30302, 1),
            SurfaceCampaignRole.SHARP_SMOKE: (RoughnessTier.SHARP, 30303, 1),
        }[self.role]
        if (self.roughness_tier, self.root_seed, self.intended_case_count) != expected:
            raise ValueError("surface campaign role does not match its frozen tier/seed/count")
        if self.surface_seed_index != 0:
            raise ValueError("M03 fixed witnesses use surface_seed_index=0")
        if self.statistical_sample:
            raise ValueError("the three fixed M03 seeds are witnesses, not statistical samples")
        if self.latent_noise_identity.root_seed != self.root_seed:
            raise ValueError("surface seed and latent-noise identity disagree")
        if self.latent_noise_identity.surface_seed_index != self.surface_seed_index:
            raise ValueError("surface seed index and latent-noise identity disagree")
        if self.surface_spec.family is not SurfaceFamily.SELF_AFFINE_GAUSSIAN:
            raise ValueError("M03 synthetic campaigns require self-affine Gaussian M01 specs")
        if self.surface_spec.boundary_mode is not BoundaryMode.ERROR:
            raise ValueError("M03 campaign surfaces must preserve ERROR boundary semantics")
        parameters = self.surface_spec.parameter_map()
        if parameters["roughness_tier"] != self.roughness_tier.value:
            raise ValueError("M01 surface spec roughness tier mismatch")
        if parameters["surface_scale_reference_Rt_mm"] != SURFACE_SCALE_REFERENCE_RT_MM:
            raise ValueError("surface scale reference Rt must stay frozen at 0.05 mm")
        if parameters["anisotropy_ratio"] != 1.0:
            raise ValueError("M03 fixed synthetic witnesses are isotropic")
        expected_direction = 0.0 if self.role is SurfaceCampaignRole.PRIMARY_MEDIUM else None
        if parameters["anisotropy_direction_rad"] != expected_direction:
            raise ValueError("M03 campaign anisotropy direction does not match its frozen input")
        if self.surface_realization.surface_spec_id != self.surface_spec.surface_spec_id:
            raise ValueError("surface realization belongs to a different M01 surface spec")
        if self.surface_realization.seed_id != self.latent_noise_identity.seed_id:
            raise ValueError("surface realization and seed identity disagree")
        if self.surface_realization.latent_noise_id != self.latent_noise_identity.latent_noise_id:
            raise ValueError("surface realization and latent-noise identity disagree")

    @property
    def surface_spec_id(self) -> str:
        return self.surface_spec.surface_spec_id

    @property
    def latent_noise_id(self) -> str:
        return self.latent_noise_identity.latent_noise_id

    @property
    def seed_id(self) -> str:
        return self.latent_noise_identity.seed_id

    @property
    def surface_realization_id(self) -> str:
        return self.surface_realization.surface_realization_id


def _surface_campaign_spec(
    role: SurfaceCampaignRole,
    tier: RoughnessTier,
    root_seed: int,
    intended_case_count: int,
) -> SyntheticSurfaceCampaignSpec:
    direction = 0.0 if role is SurfaceCampaignRole.PRIMARY_MEDIUM else None
    parameters = synthetic_parameters_for_tier(
        tier,
        surface_scale_reference_Rt_mm=SURFACE_SCALE_REFERENCE_RT_MM,
        anisotropy_ratio=1.0,
        anisotropy_direction_rad=direction,
    )
    source = make_synthetic_source_descriptor()
    provider = SurfaceProvider()
    creation = provider.create_surface_spec(
        source,
        SurfaceFamily.SELF_AFFINE_GAUSSIAN,
        parameters,
    )
    if creation.spec is None:
        raise RuntimeError(
            f"frozen M03 {role.value} surface spec was rejected: {creation.status.reason_code}"
        )
    latent = make_latent_noise_identity(
        root_seed,
        0,
        latent_noise_namespace=f"m03.single_spine.{role.value.lower()}",
    )
    realized = provider.create_realization(source, creation.spec, latent_identity=latent)
    if realized.realization is None:
        raise RuntimeError(
            f"frozen M03 {role.value} realization was rejected: {realized.status.reason_code}"
        )
    return SyntheticSurfaceCampaignSpec(
        role,
        tier,
        root_seed,
        0,
        creation.spec,
        latent,
        realized.realization,
        intended_case_count,
    )


def frozen_synthetic_surface_specs() -> tuple[SyntheticSurfaceCampaignSpec, ...]:
    """Return primary-medium, gentle-smoke, and sharp-smoke M01 specifications."""

    return (
        _surface_campaign_spec(
            SurfaceCampaignRole.PRIMARY_MEDIUM,
            RoughnessTier.MEDIUM,
            30301,
            36,
        ),
        _surface_campaign_spec(
            SurfaceCampaignRole.GENTLE_SMOKE,
            RoughnessTier.GENTLE,
            30302,
            1,
        ),
        _surface_campaign_spec(
            SurfaceCampaignRole.SHARP_SMOKE,
            RoughnessTier.SHARP,
            30303,
            1,
        ),
    )


def frozen_surface_specs() -> tuple[SyntheticSurfaceCampaignSpec, ...]:
    """Concise alias for the three frozen synthetic campaign specifications."""

    return frozen_synthetic_surface_specs()


@dataclass(frozen=True, slots=True)
class CampaignPathQueryPolicy:
    path_policy_id: str = "M03_COMMON_100MM_PATH_V1"
    query_policy_id: str = "M03_LAZY_FOOTPRINT_QUERY_V1"
    start_x_mm: float = 25.0
    start_y_mm: float = 75.0
    travel_mm: float = 100.0
    drag_direction_local: str = "+local-x"
    ahead_spacing_over_rt: float = 1.0 / 5.0
    event_support_spacing_over_rt: float = 1.0 / 8.0
    acceptance_witness_spacing_over_rt: float = 1.0 / 10.0
    lazy_active_footprint_only: bool = True
    full_domain_dense_grid_allowed: bool = False

    def __post_init__(self) -> None:
        if (self.start_x_mm, self.start_y_mm, self.travel_mm) != (25.0, 75.0, 100.0):
            raise ValueError("unsupported M03 paired campaign path")
        if self.drag_direction_local != "+local-x":
            raise ValueError("the frozen M03 drag direction is +local-x")
        if (
            self.ahead_spacing_over_rt,
            self.event_support_spacing_over_rt,
            self.acceptance_witness_spacing_over_rt,
        ) != (1.0 / 5.0, 1.0 / 8.0, 1.0 / 10.0):
            raise ValueError("M03 query LOD ratios must preserve the M01/M02 contract")
        if not self.lazy_active_footprint_only or self.full_domain_dense_grid_allowed:
            raise ValueError("M03 campaigns require lazy footprints and prohibit dense grids")


@dataclass(frozen=True, slots=True)
class StreamingCampaignCase:
    ordinal: int
    execution_case_id: str
    run_kind: CampaignRunKind
    surface_role: SurfaceCampaignRole
    surface_spec_id: str
    seed_id: str
    latent_noise_id: str
    surface_realization_id: str
    trend_case_id: str | None
    parameter_bundle: SingleSpineParameterBundle
    path_policy_id: str
    query_policy_id: str
    requested_diagnostic_level: str = "STANDARD"


@dataclass(frozen=True, slots=True)
class CampaignStreamingCursor:
    plan_id: str
    next_ordinal: int

    def __post_init__(self) -> None:
        if self.plan_id != FROZEN_STREAMING_PLAN_ID:
            raise ValueError("cursor belongs to a different M03 streaming plan")
        if not 0 <= self.next_ordinal <= SYNTHETIC_CAMPAIGN_CASE_COUNT:
            raise ValueError("streaming cursor ordinal is outside the frozen plan")

    def to_dict(self) -> dict[str, str | int]:
        return {"plan_id": self.plan_id, "next_ordinal": self.next_ordinal}

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> CampaignStreamingCursor:
        plan_id = payload.get("plan_id")
        next_ordinal = payload.get("next_ordinal")
        if (
            not isinstance(plan_id, str)
            or isinstance(next_ordinal, bool)
            or not isinstance(next_ordinal, int)
        ):
            raise ValueError("invalid M03 streaming cursor payload")
        return cls(plan_id, next_ordinal)


@dataclass(frozen=True, slots=True)
class CampaignStreamingPlan:
    """Bounded-history execution order for 36 primary cases plus two smokes."""

    plan_id: str
    trend_campaign: TrendCampaignPlan
    surfaces: tuple[SyntheticSurfaceCampaignSpec, ...]
    path_query_policy: CampaignPathQueryPolicy
    maximum_full_histories_in_memory: int = 1
    checkpoint_interval_cases: int = 1
    retain_completed_full_history: bool = False
    pause_resume_supported: bool = True
    semantic_replay_required: bool = True
    required_per_case_metrics: tuple[str, ...] = (
        "accepted_count",
        "trial_count",
        "committed_event_count",
        "query_count",
        "wall_time_seconds",
        "peak_rss_bytes",
        "cache_payload_bytes",
        "cache_hit_count",
        "cache_miss_count",
        "cache_regeneration_count",
        "artifact_size_bytes",
        "terminal_status",
        "failure_axis",
        "reason_code",
        "replay_manifest_id",
        "final_receipt_id",
    )

    def __post_init__(self) -> None:
        if self.plan_id != FROZEN_STREAMING_PLAN_ID:
            raise ValueError("unsupported M03 streaming plan ID")
        if len(self.trend_campaign.cases) != TREND_CASE_COUNT:
            raise ValueError("streaming plan requires the frozen 36-case trend campaign")
        if tuple(surface.role for surface in self.surfaces) != tuple(SurfaceCampaignRole):
            raise ValueError("streaming plan requires primary, gentle, and sharp surfaces")
        if self.maximum_full_histories_in_memory != 1 or self.retain_completed_full_history:
            raise ValueError("M03 streaming may retain at most the active FULL history")
        if self.checkpoint_interval_cases != 1:
            raise ValueError("M03 streaming checkpoints case by case")
        if not self.pause_resume_supported or not self.semantic_replay_required:
            raise ValueError("M03 campaigns must support pause/resume and semantic replay")
        expected_metrics = {
            "accepted_count",
            "trial_count",
            "committed_event_count",
            "query_count",
            "wall_time_seconds",
            "peak_rss_bytes",
            "cache_payload_bytes",
            "cache_hit_count",
            "cache_miss_count",
            "cache_regeneration_count",
            "artifact_size_bytes",
            "terminal_status",
            "failure_axis",
            "reason_code",
            "replay_manifest_id",
            "final_receipt_id",
        }
        if set(self.required_per_case_metrics) != expected_metrics:
            raise ValueError("M03 per-case performance metrics are incomplete")
        if len({self.case_at(index).execution_case_id for index in range(self.case_count)}) != (
            self.case_count
        ):
            raise ValueError("M03 execution case IDs must be distinct")

    @property
    def case_count(self) -> int:
        return SYNTHETIC_CAMPAIGN_CASE_COUNT

    @property
    def primary_case_count(self) -> int:
        return TREND_CASE_COUNT

    @property
    def smoke_case_count(self) -> int:
        return 2

    def surface_for_role(self, role: SurfaceCampaignRole) -> SyntheticSurfaceCampaignSpec:
        return next(surface for surface in self.surfaces if surface.role is role)

    def case_at(self, ordinal: int) -> StreamingCampaignCase:
        if not 0 <= ordinal < self.case_count:
            raise IndexError("streaming case ordinal is outside the frozen plan")
        path = self.path_query_policy
        if ordinal < TREND_CASE_COUNT:
            trend_case = self.trend_campaign.cases[ordinal]
            surface = self.surface_for_role(SurfaceCampaignRole.PRIMARY_MEDIUM)
            return StreamingCampaignCase(
                ordinal,
                (
                    f"m03-case-{surface.surface_realization_id}-"
                    f"{trend_case.parameter_bundle.parameter_bundle_id}"
                ),
                CampaignRunKind.PRIMARY_TREND,
                surface.role,
                surface.surface_spec_id,
                surface.seed_id,
                surface.latent_noise_id,
                surface.surface_realization_id,
                trend_case.case_id,
                trend_case.parameter_bundle,
                path.path_policy_id,
                path.query_policy_id,
            )
        surface = self.surfaces[ordinal - TREND_CASE_COUNT + 1]
        bundle = self.trend_campaign.baseline_case.parameter_bundle
        return StreamingCampaignCase(
            ordinal,
            f"m03-case-{surface.surface_realization_id}-{bundle.parameter_bundle_id}",
            CampaignRunKind.BASELINE_SMOKE,
            surface.role,
            surface.surface_spec_id,
            surface.seed_id,
            surface.latent_noise_id,
            surface.surface_realization_id,
            None,
            bundle,
            path.path_policy_id,
            path.query_policy_id,
        )

    def iter_cases(
        self,
        start: int = 0,
        stop: int | None = None,
    ) -> Iterable[StreamingCampaignCase]:
        resolved_stop = self.case_count if stop is None else stop
        if not 0 <= start <= resolved_stop <= self.case_count:
            raise ValueError("invalid streaming case slice")
        for ordinal in range(start, resolved_stop):
            yield self.case_at(ordinal)

    def initial_cursor(self) -> CampaignStreamingCursor:
        return CampaignStreamingCursor(self.plan_id, 0)

    def iter_from_cursor(
        self,
        cursor: CampaignStreamingCursor,
        *,
        maximum_cases: int | None = None,
    ) -> tuple[tuple[StreamingCampaignCase, ...], CampaignStreamingCursor]:
        if cursor.plan_id != self.plan_id:
            raise ValueError("cursor belongs to a different M03 streaming plan")
        if maximum_cases is not None and maximum_cases < 0:
            raise ValueError("maximum_cases cannot be negative")
        stop = self.case_count
        if maximum_cases is not None:
            stop = min(stop, cursor.next_ordinal + maximum_cases)
        selected = tuple(self.iter_cases(cursor.next_ordinal, stop))
        return selected, CampaignStreamingCursor(self.plan_id, stop)


def frozen_campaign_streaming_plan() -> CampaignStreamingPlan:
    return CampaignStreamingPlan(
        FROZEN_STREAMING_PLAN_ID,
        frozen_trend_campaign(),
        frozen_synthetic_surface_specs(),
        CampaignPathQueryPolicy(),
    )


def frozen_streaming_plan() -> CampaignStreamingPlan:
    """Concise alias for the frozen M03 synthetic campaign streaming plan."""

    return frozen_campaign_streaming_plan()


__all__ = [
    "ALPHA_GRID_DEG",
    "BASELINE_TREND_PARAMETERS",
    "DIAMETER_GRID_MM",
    "FRICTION_GRID",
    "FROZEN_STREAMING_PLAN_ID",
    "FROZEN_TREND_PLAN_ID",
    "INTERACTION_RECORD_COUNT",
    "POISSON_RATIO_GRID",
    "RT_GRID_MM",
    "SHARED_INTERACTION_REFERENCE_COUNT",
    "SPRING_STIFFNESS_GRID_N_PER_MM",
    "SYNTHETIC_CAMPAIGN_CASE_COUNT",
    "TREND_CASE_COUNT",
    "YOUNGS_MODULUS_GRID_MPA",
    "CampaignPathQueryPolicy",
    "CampaignRunKind",
    "CampaignStreamingCursor",
    "CampaignStreamingPlan",
    "InteractionRecord",
    "SharedCaseReference",
    "StreamingCampaignCase",
    "SurfaceCampaignRole",
    "SyntheticSurfaceCampaignSpec",
    "TrendCampaignPlan",
    "TrendCase",
    "TrendPanel",
    "TrendParameters",
    "frozen_campaign_streaming_plan",
    "frozen_interaction_records",
    "frozen_streaming_plan",
    "frozen_surface_specs",
    "frozen_synthetic_surface_specs",
    "frozen_trend_campaign",
    "frozen_trend_cases",
]
