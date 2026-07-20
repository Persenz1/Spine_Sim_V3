"""Typed public contracts for the frozen M03 A-M0 single-spine product.

The module contains values only.  It deliberately has no mutable solver state,
surface evaluator, plotting dependency, or array-level physics.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar

import numpy as np

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    AttemptOutcome,
    AuthorityRef,
    CapabilityStatus,
    CertificationStatus,
    Maturity,
    MaturityEvidence,
    MaturityStatus,
    PhysicalFeasibility,
    SourceIdentity,
    StatusTuple,
    ValuePresence,
    ValueProvenance,
)

M03_SCHEMA_VERSION = "1.0.0"
M03_REQUIREMENTS_ID = "M03_SINGLE_SPINE_REQUIREMENTS 1.0.0"
A_TO_B_CONTRACT_ID = "A_TO_B"
A_TO_B_CONTRACT_VERSION = "1.0.0"
M03_UNIT_SYSTEM = "N-mm-MPa"
SURFACE_SCALE_REFERENCE_RT_MM = 0.05

Vector2 = tuple[float, float]
Vector3 = tuple[float, float, float]
Vector6 = tuple[float, float, float, float, float, float]
Matrix3 = tuple[Vector3, Vector3, Vector3]
Matrix6 = tuple[Vector6, Vector6, Vector6, Vector6, Vector6, Vector6]


class ParameterRole(StrEnum):
    FIXED_ENGINEERING = "FIXED_ENGINEERING"
    DESIGN_VARIABLE = "DESIGN_VARIABLE"
    DEV_PRIOR_UNCERTAINTY = "DEV_PRIOR_UNCERTAINTY"
    NUMERICAL_CONFIGURATION = "NUMERICAL_CONFIGURATION"
    VALIDATION_CONFIGURATION = "VALIDATION_CONFIGURATION"


class CallMode(StrEnum):
    EMBEDDED_CONSTITUTIVE_TRIAL = "embedded_constitutive_trial"


class MountMode(StrEnum):
    RIGID_MOUNT = "RIGID_MOUNT"
    INDEPENDENT_AXIAL_SPRINGS = "INDEPENDENT_AXIAL_SPRINGS"


class PrimaryMechanicalState(StrEnum):
    OPEN = "OPEN"
    TIP_ZERO_LOAD = "TIP_ZERO_LOAD"
    PRELOAD_BUILD = "PRELOAD_BUILD"
    ATTACHED_STICK = "ATTACHED_STICK"
    ATTACHED_SLIDE = "ATTACHED_SLIDE"
    REATTACHED_ENTRY = "REATTACHED_ENTRY"
    RELEASE_TRANSITION = "RELEASE_TRANSITION"
    REVERSIBLE_RETURN = "REVERSIBLE_RETURN"
    TRAVEL_COMPLETE = "TRAVEL_COMPLETE"


class ContactMotionState(StrEnum):
    OPEN = "OPEN"
    TOUCH_ZERO_LOAD = "TOUCH_ZERO_LOAD"
    STICKING_INTERIOR = "STICKING_INTERIOR"
    STICKING_AT_CONE_BOUNDARY = "STICKING_AT_CONE_BOUNDARY"
    ROLLING_NO_SLIP = "ROLLING_NO_SLIP"
    SLIDING_COMMITTED = "SLIDING_COMMITTED"
    SUPPORT_SWITCH_PENDING = "SUPPORT_SWITCH_PENDING"
    RELEASE_PENDING = "RELEASE_PENDING"


class SpringState(StrEnum):
    RIGID_LOCKED = "RIGID_LOCKED"
    AT_ORIGINAL_LENGTH = "AT_ORIGINAL_LENGTH"
    COMPRESSING = "COMPRESSING"
    HARD_STOP = "HARD_STOP"


class BeamModelState(StrEnum):
    BENDING_OFF = "BENDING_OFF"
    EB_ELASTIC = "EB_ELASTIC"
    STRUCTURAL_MODEL_OUT_OF_RANGE = "STRUCTURAL_MODEL_OUT_OF_RANGE"


class MaterialSubstate(StrEnum):
    NO_DAMAGE_MODEL = "NO_DAMAGE_MODEL"


class NeedleStrengthSubstate(StrEnum):
    NEEDLE_STRENGTH_UNAVAILABLE = "NEEDLE_STRENGTH_UNAVAILABLE"


class OperationPhase(StrEnum):
    INITIAL_CLEARANCE = "INITIAL_CLEARANCE"
    INITIAL_SEARCH = "INITIAL_SEARCH"
    INITIAL_PRELOAD = "INITIAL_PRELOAD"
    DRAG = "DRAG"
    UNLOAD = "UNLOAD"
    DRIVE_OFF_UNLOCK = "DRIVE_OFF_UNLOCK"
    REVERSE_SEARCH = "REVERSE_SEARCH"
    LIFT_OFF = "LIFT_OFF"
    RESEARCH = "RESEARCH"
    RELOAD = "RELOAD"
    HOLD_RELEASE_POSE = "HOLD_RELEASE_POSE"
    COMPLETE = "COMPLETE"


class StandaloneTerminalStatus(StrEnum):
    TRAVEL_COMPLETE = "TRAVEL_COMPLETE"
    HOLD_AT_RELEASE_POSE = "HOLD_AT_RELEASE_POSE"
    PHYSICAL_TERMINATION = "PHYSICAL_TERMINATION"
    DOMAIN_TERMINATION = "DOMAIN_TERMINATION"
    CAPABILITY_TERMINATION = "CAPABILITY_TERMINATION"
    NUMERICAL_TERMINATION = "NUMERICAL_TERMINATION"
    TRANSACTION_TERMINATION = "TRANSACTION_TERMINATION"


class RequestedTangentMode(StrEnum):
    NONE = "none"
    ALGORITHMIC = "algorithmic"
    GENERALIZED_ONE_SIDED = "generalized_one_sided"
    SECANT = "secant"


class TangentStatus(StrEnum):
    SMOOTH_CONSISTENT = "smooth_consistent"
    GENERALIZED_ONE_SIDED = "generalized_one_sided"
    BRANCH_DEPENDENT = "branch_dependent"
    SECANT_ONLY = "secant_only"
    CONSTRAINT_SET_VALUED = "constraint_set_valued"
    UNAVAILABLE = "unavailable"


class WrenchUniqueness(StrEnum):
    UNIQUE = "unique"
    REPRESENTATIVE_WITH_INTERNAL_NONUNIQUENESS = "representative_with_internal_nonuniqueness"
    SET_VALUED_CONSTRAINT = "set_valued_constraint"


class EmbeddedErrorClass(StrEnum):
    OK = "OK"
    OPEN_RESPONSE = "OPEN_RESPONSE"
    EVENT_REDUCTION_REQUIRED = "EVENT_REDUCTION_REQUIRED"
    OUT_OF_DOMAIN = "OUT_OF_DOMAIN"
    GEOMETRY_UNCERTAIN = "GEOMETRY_UNCERTAIN"
    BODY_COLLISION_INVALID = "BODY_COLLISION_INVALID"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    PARAMETER_UNAVAILABLE = "PARAMETER_UNAVAILABLE"
    EQUILIBRIUM_INFEASIBLE = "EQUILIBRIUM_INFEASIBLE"
    EQUILIBRIUM_DEGENERATE = "EQUILIBRIUM_DEGENERATE"
    NUMERICAL_NONCONVERGENCE = "NUMERICAL_NONCONVERGENCE"
    STALE_SNAPSHOT = "STALE_SNAPSHOT"
    DAMAGE_CONFLICT_REQUIRES_RESOLVE = "DAMAGE_CONFLICT_REQUIRES_RESOLVE"
    CONTRACT_VIOLATION = "CONTRACT_VIOLATION"


class FailureAxis(StrEnum):
    NONE = "NONE"
    NUMERICAL_FAILURE = "NUMERICAL_FAILURE"
    PHYSICAL_INFEASIBLE = "PHYSICAL_INFEASIBLE"
    CONTRACT_REJECTION = "CONTRACT_REJECTION"
    DOMAIN_ERROR = "DOMAIN_ERROR"
    TRANSACTION_FAILURE = "TRANSACTION_FAILURE"
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"


class M03ReasonCode(StrEnum):
    OK = "M03_OK"
    INVALID_REQUEST = "M03_INVALID_REQUEST"
    KINEMATIC_MODE_UNSUPPORTED = "M03_KINEMATIC_MODE_UNSUPPORTED"
    DUPLICATE_NORMAL_LOAD = "M03_DUPLICATE_NORMAL_LOAD"
    INITIAL_POSE_INFEASIBLE = "M03_INITIAL_POSE_INFEASIBLE"
    PRELOAD_INFEASIBLE = "M03_PRELOAD_INFEASIBLE"
    RELEASE_RETURN_PATH_UNAVAILABLE = "M03_RELEASE_RETURN_PATH_UNAVAILABLE"
    HOLD_AT_RELEASE_POSE = "M03_HOLD_AT_RELEASE_POSE"
    BODY_COLLISION_INVALID = "M03_BODY_COLLISION_INVALID"
    FINITE_CAP_SUPPORT_UNAVAILABLE = "M03_FINITE_CAP_SUPPORT_UNAVAILABLE"
    TASK_DIRECTION_INVALID = "M03_TASK_DIRECTION_INVALID"
    MATERIAL_DAMAGE_UNAVAILABLE = "M03_MATERIAL_DAMAGE_UNAVAILABLE"
    NEEDLE_STRENGTH_CERTIFICATION_UNAVAILABLE = "M03_NEEDLE_STRENGTH_CERTIFICATION_UNAVAILABLE"
    STRUCTURAL_MODEL_OUT_OF_RANGE = "M03_STRUCTURAL_MODEL_OUT_OF_RANGE"
    GEOMETRY_UNCERTAIN = "M03_GEOMETRY_UNCERTAIN"
    HARD_RESIDUAL_QUALITY_FAILED = "M03_HARD_RESIDUAL_QUALITY_FAILED"
    CONTRACT_VIOLATION_DUPLICATE_NORMAL_LOAD = "CONTRACT_VIOLATION_DUPLICATE_NORMAL_LOAD"


class LODPurpose(StrEnum):
    AHEAD = "ahead"
    EVENT_SUPPORT = "event_support"
    ACCEPTANCE_WITNESS = "acceptance_witness"

    @property
    def spacing_over_rt(self) -> float:
        return {
            LODPurpose.AHEAD: 1.0 / 5.0,
            LODPurpose.EVENT_SUPPORT: 1.0 / 8.0,
            LODPurpose.ACCEPTANCE_WITNESS: 1.0 / 10.0,
        }[self]


def m03_maturity(*, numerically_verified: bool = False) -> Maturity:
    """Return the mandatory four-column M03 maturity without certification uplift."""

    return Maturity(
        MaturityEvidence(
            MaturityStatus.SPEC_DEFINED,
            "M03 frozen software/physics product contract",
            M03_REQUIREMENTS_ID,
            ("docs/simulator_development/requirements/M03_SINGLE_SPINE_REQUIREMENTS.md",),
        ),
        MaturityEvidence(
            MaturityStatus.PASSED_WITH_EVIDENCE,
            "M03 A-M0 code implementation",
            M03_SCHEMA_VERSION,
            ("src/spine_sim/single_spine",),
        ),
        MaturityEvidence(
            MaturityStatus.PASSED_WITH_EVIDENCE
            if numerically_verified
            else MaturityStatus.NOT_ASSESSED,
            "analytic/synthetic M03 numerical verification",
            M03_SCHEMA_VERSION if numerically_verified else None,
            ("reports/m03/M03_VALIDATION_REPORT.md",) if numerically_verified else (),
        ),
        MaturityEvidence(
            MaturityStatus.NOT_ASSESSED,
            "no target-wall single-spine experiment has been assessed",
            None,
        ),
    )


def m03_status(
    reason: M03ReasonCode | str = M03ReasonCode.OK,
    *,
    capability: CapabilityStatus = CapabilityStatus.SUPPORTED,
    outcome: AttemptOutcome = AttemptOutcome.ACCEPTED,
    feasibility: PhysicalFeasibility = PhysicalFeasibility.NOT_ASSESSED,
    explanation: str = "M03 value is available for DEV_PRIOR analytic/synthetic scope",
) -> StatusTuple:
    presence = ValuePresence.PRESENT
    if capability in {CapabilityStatus.UNAVAILABLE, CapabilityStatus.NOT_APPLICABLE}:
        presence = ValuePresence.NULL
    reason_value = reason.value if isinstance(reason, M03ReasonCode) else reason
    return StatusTuple(
        presence,
        capability,
        outcome,
        feasibility,
        CertificationStatus.NOT_CERTIFIABLE,
        reason_value,
        explanation,
        (M03_REQUIREMENTS_ID,),
    )


def _authority_refs() -> tuple[AuthorityRef, ...]:
    items = (
        ("theory/evidence_reassessment/engineering_fixed_context.md", "1.0.0"),
        ("theory/modules/A_INTEGRATED_MODEL.md", "1.0.0 accepted"),
        ("theory/interfaces/A_TO_B_CONTRACT.md", "1.0.0 accepted"),
        (
            "docs/simulator_development/requirements/M03_SINGLE_SPINE_REQUIREMENTS.md",
            "1.0.0 frozen",
        ),
    )
    return tuple(
        AuthorityRef(path, version, semantic_hash({"path": path, "version": version}), "M03")
        for path, version in items
    )


@dataclass(frozen=True, slots=True)
class SemanticMetadata:
    schema_version: str
    semantic_id: str
    semantic_hash: str
    unit_system: str
    status: StatusTuple
    source_identity: SourceIdentity
    requirement_origin: str
    value_provenance: tuple[ValueProvenance, ...]
    authority_refs: tuple[AuthorityRef, ...]
    maturity: Maturity
    certification_status: CertificationStatus

    def __post_init__(self) -> None:
        if self.schema_version != M03_SCHEMA_VERSION:
            raise ContractViolation("unsupported M03 schema version")
        if self.unit_system != M03_UNIT_SYSTEM:
            raise ContractViolation("M03 objects require the N-mm-MPa unit system")
        if self.certification_status is not CertificationStatus.NOT_CERTIFIABLE:
            raise ContractViolation("M03 A-M0 objects are not certifiable")
        if self.status.certification_status is not self.certification_status:
            raise ContractViolation("metadata status/certification mismatch")


def make_metadata(
    kind: str,
    payload: Any,
    *,
    source_identity: SourceIdentity = SourceIdentity.ACCEPTED_AUTHORITY,
    status: StatusTuple | None = None,
    numerically_verified: bool = False,
) -> SemanticMetadata:
    digest = semantic_hash(payload)
    object_id = stable_content_id(kind, {"schema_version": M03_SCHEMA_VERSION, "hash": digest})
    provenance = (
        ValueProvenance(
            source_id=M03_REQUIREMENTS_ID,
            source_hash=semantic_hash(M03_REQUIREMENTS_ID),
            field_path=kind,
            source_identity=source_identity,
        ),
    )
    return SemanticMetadata(
        M03_SCHEMA_VERSION,
        object_id,
        digest,
        M03_UNIT_SYSTEM,
        status if status is not None else m03_status(),
        source_identity,
        M03_REQUIREMENTS_ID,
        provenance,
        _authority_refs(),
        m03_maturity(numerically_verified=numerically_verified),
        CertificationStatus.NOT_CERTIFIABLE,
    )


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ContractViolation(f"{name} must be a finite number")
    return float(value)


def _positive(value: float, name: str) -> float:
    result = _finite(value, name)
    if result <= 0.0:
        raise ContractViolation(f"{name} must be positive")
    return result


def _vector3(value: Vector3, name: str) -> Vector3:
    if len(value) != 3:
        raise ContractViolation(f"{name} must contain three components")
    return tuple(_finite(component, name) for component in value)  # type: ignore[return-value]


def _matrix3(value: Matrix3, name: str) -> Matrix3:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (3, 3) or not np.isfinite(array).all():
        raise ContractViolation(f"{name} must be a finite 3x3 matrix")
    if not np.allclose(array.T @ array, np.eye(3), atol=1.0e-10, rtol=1.0e-10):
        raise ContractViolation(f"{name} must be orthonormal")
    if not math.isclose(float(np.linalg.det(array)), 1.0, abs_tol=1.0e-10):
        raise ContractViolation(f"{name} must be a right-handed rotation")
    return value


@dataclass(frozen=True, slots=True)
class ParameterEvidence:
    parameter_name: str
    canonical_unit: str
    role: ParameterRole
    source_identity: SourceIdentity
    requirement_origin: str
    value_provenance: str
    authority_reference: str
    status: StatusTuple
    maturity: Maturity
    certification_status: CertificationStatus = CertificationStatus.NOT_CERTIFIABLE

    def __post_init__(self) -> None:
        if not self.parameter_name or not self.canonical_unit:
            raise ContractViolation("parameter evidence requires a name and explicit unit")
        if self.certification_status is not CertificationStatus.NOT_CERTIFIABLE:
            raise ContractViolation("DEV_PRIOR parameters cannot be certified")


def parameter_evidence(
    name: str,
    unit: str,
    role: ParameterRole,
    source: SourceIdentity,
    provenance: str,
) -> ParameterEvidence:
    return ParameterEvidence(
        name,
        unit,
        role,
        source,
        M03_REQUIREMENTS_ID,
        provenance,
        "docs/simulator_development/requirements/M03_SINGLE_SPINE_REQUIREMENTS.md",
        m03_status(),
        m03_maturity(),
    )


@dataclass(frozen=True, slots=True)
class NeedleParameterBundle:
    tip_radius_mm: float
    diameter_mm: float
    exposed_length_mm: float
    alpha_rad: float
    beta_rad: float
    cone_half_angle_rad: float
    cone_length_mm: float
    mount_radius_mm: float
    mount_length_mm: float
    cap_blend_coordinate_mm: float
    evidence: tuple[ParameterEvidence, ...]
    metadata: SemanticMetadata

    REQUIRED_EVIDENCE: ClassVar[frozenset[str]] = frozenset(
        {
            "tip_radius_mm",
            "diameter_mm",
            "exposed_length_mm",
            "alpha_rad",
            "beta_rad",
            "cone_half_angle_rad",
            "cone_length_mm",
            "mount_radius_mm",
            "mount_length_mm",
            "cap_blend_coordinate_mm",
        }
    )

    def __post_init__(self) -> None:
        for name in (
            "tip_radius_mm",
            "diameter_mm",
            "exposed_length_mm",
            "cone_half_angle_rad",
            "cone_length_mm",
            "mount_radius_mm",
            "mount_length_mm",
        ):
            _positive(getattr(self, name), name)
        alpha = _finite(self.alpha_rad, "alpha_rad")
        beta = _finite(self.beta_rad, "beta_rad")
        if not 0.0 < alpha < math.pi / 2.0:
            raise ContractViolation("alpha_rad must lie strictly between 0 and pi/2")
        if not -math.pi <= beta <= math.pi:
            raise ContractViolation("beta_rad must lie in [-pi, pi]")
        if not 0.0 < self.cone_half_angle_rad < math.pi / 2.0:
            raise ContractViolation("cone half angle must lie strictly between 0 and pi/2")
        blend = _finite(self.cap_blend_coordinate_mm, "cap_blend_coordinate_mm")
        if not -self.tip_radius_mm <= blend < self.tip_radius_mm:
            raise ContractViolation("finite-cap blend coordinate must lie on the sphere")
        if self.diameter_mm <= 2.0 * self.tip_radius_mm:
            raise ContractViolation("shaft diameter must exceed the local tip diameter")
        if self.cone_length_mm >= self.exposed_length_mm:
            raise ContractViolation("cone must fit inside the exposed needle length")
        if {item.parameter_name for item in self.evidence} != self.REQUIRED_EVIDENCE:
            raise ContractViolation("needle bundle evidence is incomplete or duplicated")


@dataclass(frozen=True, slots=True)
class ContactParameterBundle:
    model_id: str
    friction_coefficient: float
    normal_compliance_mm_per_n: float
    numerical_soc_projection_scale: float
    evidence: tuple[ParameterEvidence, ...]
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.model_id != "rigid_signorini_coulomb":
            raise ContractViolation("M03 production contact model is rigid_signorini_coulomb")
        mu = _finite(self.friction_coefficient, "friction_coefficient")
        if mu < 0.0:
            raise ContractViolation("friction coefficient cannot be negative")
        if _finite(self.normal_compliance_mm_per_n, "normal_compliance_mm_per_n") != 0.0:
            raise ContractViolation("M03 physical normal contact compliance is exactly zero")
        if _positive(self.numerical_soc_projection_scale, "numerical_soc_projection_scale") <= 0:
            raise AssertionError("unreachable")
        names = {item.parameter_name for item in self.evidence}
        expected = {
            "model_id",
            "friction_coefficient",
            "normal_compliance_mm_per_n",
            "numerical_soc_projection_scale",
        }
        if names != expected:
            raise ContractViolation("contact bundle evidence is incomplete or duplicated")


@dataclass(frozen=True, slots=True)
class BeamParameterBundle:
    bending_enabled: bool
    model_id: str
    youngs_modulus_mpa: float | None
    poisson_ratio: float | None
    maximum_rotation_rad: float
    minimum_slenderness_ratio: float
    maximum_tip_deflection_over_length: float
    evidence: tuple[ParameterEvidence, ...]
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.model_id != "euler_bernoulli":
            raise ContractViolation("production beam registry only supports euler_bernoulli")
        if self.bending_enabled:
            if self.youngs_modulus_mpa is None or self.poisson_ratio is None:
                raise ContractViolation("bending-on requires explicit E and nu")
            _positive(self.youngs_modulus_mpa, "youngs_modulus_mpa")
            nu = _finite(self.poisson_ratio, "poisson_ratio")
            if not -1.0 < nu < 0.5:
                raise ContractViolation("poisson_ratio must lie in the elastic stability range")
        elif self.youngs_modulus_mpa is not None or self.poisson_ratio is not None:
            raise ContractViolation("bending-off must not carry meaningless E/nu values")
        _positive(self.maximum_rotation_rad, "maximum_rotation_rad")
        _positive(self.minimum_slenderness_ratio, "minimum_slenderness_ratio")
        _positive(
            self.maximum_tip_deflection_over_length,
            "maximum_tip_deflection_over_length",
        )
        expected = {
            "bending_enabled",
            "model_id",
            "youngs_modulus_mpa",
            "poisson_ratio",
            "maximum_rotation_rad",
            "minimum_slenderness_ratio",
            "maximum_tip_deflection_over_length",
        }
        if {item.parameter_name for item in self.evidence} != expected:
            raise ContractViolation("beam bundle evidence is incomplete or duplicated")


@dataclass(frozen=True, slots=True)
class MountParameterBundle:
    mode: MountMode
    spring_stiffness_n_per_mm: float | None
    minimum_compression_mm: float
    maximum_compression_mm: float
    evidence: tuple[ParameterEvidence, ...]
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        minimum = _finite(self.minimum_compression_mm, "minimum_compression_mm")
        maximum = _positive(self.maximum_compression_mm, "maximum_compression_mm")
        if minimum != 0.0 or maximum != 4.0:
            raise ContractViolation("M03 spring travel is frozen to [0, 4] mm")
        if self.mode is MountMode.RIGID_MOUNT:
            if self.spring_stiffness_n_per_mm is not None:
                raise ContractViolation("rigid mount cannot carry an effective ks")
        elif self.spring_stiffness_n_per_mm is None:
            raise ContractViolation("independent spring mount requires explicit ks")
        else:
            _positive(self.spring_stiffness_n_per_mm, "spring_stiffness_n_per_mm")
        expected = {
            "mode",
            "spring_stiffness_n_per_mm",
            "minimum_compression_mm",
            "maximum_compression_mm",
        }
        if {item.parameter_name for item in self.evidence} != expected:
            raise ContractViolation("mount bundle evidence is incomplete or duplicated")


@dataclass(frozen=True, slots=True)
class NoDamageParameterBundle:
    material_model_id: str
    failure_prediction_allowed: bool
    material_dissipation_enabled: bool
    damage_store_writable: bool
    evidence: tuple[ParameterEvidence, ...]
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.material_model_id != "no_damage":
            raise ContractViolation("M03 first release only supports no_damage")
        if (
            self.failure_prediction_allowed
            or self.material_dissipation_enabled
            or self.damage_store_writable
        ):
            raise ContractViolation("no_damage cannot predict failure, dissipate, or write damage")
        expected = {
            "material_model_id",
            "failure_prediction_allowed",
            "material_dissipation_enabled",
            "damage_store_writable",
        }
        if {item.parameter_name for item in self.evidence} != expected:
            raise ContractViolation("no-damage bundle evidence is incomplete or duplicated")


@dataclass(frozen=True, slots=True)
class NumericalParameterBundle:
    initial_step_over_rt: float
    maximum_step_over_rt: float
    minimum_step_over_rt: float
    event_position_tolerance_over_rt: float
    force_absolute_tolerance_n: float
    force_relative_tolerance: float
    work_absolute_tolerance_n_mm: float
    work_relative_tolerance: float
    maximum_newton_iterations: int
    maximum_event_iterations: int
    maximum_same_position_cascade: int
    acceptance_force_resolution_n: float
    acceptance_work_resolution_n_mm: float
    evidence: tuple[ParameterEvidence, ...]
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        for name in (
            "initial_step_over_rt",
            "maximum_step_over_rt",
            "minimum_step_over_rt",
            "event_position_tolerance_over_rt",
            "force_absolute_tolerance_n",
            "force_relative_tolerance",
            "work_absolute_tolerance_n_mm",
            "work_relative_tolerance",
            "acceptance_force_resolution_n",
            "acceptance_work_resolution_n_mm",
        ):
            _positive(getattr(self, name), name)
        if not self.minimum_step_over_rt <= self.initial_step_over_rt <= self.maximum_step_over_rt:
            raise ContractViolation("continuation step ratios are not ordered")
        for name in (
            "maximum_newton_iterations",
            "maximum_event_iterations",
            "maximum_same_position_cascade",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ContractViolation(f"{name} must be a positive integer")
        field_names = {item.name for item in dataclasses.fields(self)} - {"evidence", "metadata"}
        if {item.parameter_name for item in self.evidence} != field_names:
            raise ContractViolation("numerical bundle evidence is incomplete or duplicated")


@dataclass(frozen=True, slots=True)
class SingleSpineParameterBundle:
    needle: NeedleParameterBundle
    contact: ContactParameterBundle
    beam: BeamParameterBundle
    mount: MountParameterBundle
    material: NoDamageParameterBundle
    numerical: NumericalParameterBundle
    surface_scale_reference_rt_mm: float
    declared_physical_compliance_components: tuple[str, ...]
    parameter_bundle_id: str
    parameter_bundle_hash: str
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.surface_scale_reference_rt_mm != SURFACE_SCALE_REFERENCE_RT_MM:
            raise ContractViolation("surface scale reference Rt is frozen to 0.05 mm")
        expected_components: list[str] = []
        if self.beam.bending_enabled:
            expected_components.append("euler_bernoulli_beam")
        if self.mount.mode is MountMode.INDEPENDENT_AXIAL_SPRINGS:
            expected_components.append("independent_axial_spring")
        if tuple(expected_components) != self.declared_physical_compliance_components:
            raise ContractViolation("physical compliance declaration is duplicated or incomplete")
        if self.contact.normal_compliance_mm_per_n != 0.0:
            raise ContractViolation("contact compliance cannot duplicate structural compliance")
        payload = self.identity_payload()
        expected_hash = semantic_hash(payload)
        expected_id = stable_content_id("m03_parameter_bundle", payload)
        if self.parameter_bundle_hash != expected_hash or self.parameter_bundle_id != expected_id:
            raise ContractViolation("parameter bundle identity/hash mismatch")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "needle": dataclasses.asdict(self.needle),
            "contact": dataclasses.asdict(self.contact),
            "beam": dataclasses.asdict(self.beam),
            "mount": dataclasses.asdict(self.mount),
            "material": dataclasses.asdict(self.material),
            "numerical": dataclasses.asdict(self.numerical),
            "surface_scale_reference_rt_mm": self.surface_scale_reference_rt_mm,
            "declared_physical_compliance_components": self.declared_physical_compliance_components,
        }


def _bundle_component_metadata(kind: str, payload: dict[str, Any]) -> SemanticMetadata:
    return make_metadata(kind, payload, source_identity=SourceIdentity.DEV_POLICY)


def make_baseline_parameter_bundle(
    *,
    tip_radius_mm: float = 0.05,
    diameter_mm: float = 0.8,
    alpha_deg: float = 60.0,
    beta_deg: float = 0.0,
    youngs_modulus_mpa: float = 210000.0,
    poisson_ratio: float = 0.30,
    friction_coefficient: float = 0.40,
    bending_enabled: bool = True,
    mount_mode: MountMode = MountMode.INDEPENDENT_AXIAL_SPRINGS,
    spring_stiffness_n_per_mm: float | None = 0.5,
) -> SingleSpineParameterBundle:
    """Construct the fully expanded frozen baseline with no hidden runtime defaults."""

    rt = _positive(tip_radius_mm, "tip_radius_mm")
    diameter = _positive(diameter_mm, "diameter_mm")
    alpha = math.radians(_finite(alpha_deg, "alpha_deg"))
    beta = math.radians(_finite(beta_deg, "beta_deg"))
    half_angle = math.radians(15.0)
    blend = -rt * math.sin(half_angle)
    tangent_radius = rt * math.cos(half_angle)
    cone_length = (diameter / 2.0 - tangent_radius) / math.tan(half_angle)
    if cone_length <= 0.0:
        raise ContractViolation("derived tangent cone length is not positive")

    needle_values = {
        "tip_radius_mm": rt,
        "diameter_mm": diameter,
        "exposed_length_mm": 4.0,
        "alpha_rad": alpha,
        "beta_rad": beta,
        "cone_half_angle_rad": half_angle,
        "cone_length_mm": cone_length,
        "mount_radius_mm": max(0.6, diameter),
        "mount_length_mm": 1.0,
        "cap_blend_coordinate_mm": blend,
    }
    fixed_names = {"tip_radius_mm", "diameter_mm", "exposed_length_mm", "alpha_rad", "beta_rad"}
    needle_evidence = tuple(
        parameter_evidence(
            name,
            "rad" if name.endswith("_rad") else "mm",
            ParameterRole.DESIGN_VARIABLE
            if name in {"tip_radius_mm", "diameter_mm", "alpha_rad"}
            else ParameterRole.FIXED_ENGINEERING
            if name in fixed_names
            else ParameterRole.DEV_PRIOR_UNCERTAINTY,
            SourceIdentity.FIXED_ENGINEERING if name in fixed_names else SourceIdentity.DEV_POLICY,
            "frozen M03 value"
            if name in fixed_names
            else "explicit tangent composite-geometry implementation value",
        )
        for name in needle_values
    )
    needle = NeedleParameterBundle(
        **needle_values,
        evidence=needle_evidence,
        metadata=_bundle_component_metadata("m03_needle_parameters", needle_values),
    )

    resolved_mu = _finite(friction_coefficient, "friction_coefficient")
    contact_values = {
        "model_id": "rigid_signorini_coulomb",
        "friction_coefficient": resolved_mu,
        "normal_compliance_mm_per_n": 0.0,
        "numerical_soc_projection_scale": 1.0,
    }
    contact = ContactParameterBundle(
        model_id="rigid_signorini_coulomb",
        friction_coefficient=resolved_mu,
        normal_compliance_mm_per_n=0.0,
        numerical_soc_projection_scale=1.0,
        evidence=tuple(
            parameter_evidence(
                name,
                "1" if name != "normal_compliance_mm_per_n" else "mm/N",
                ParameterRole.NUMERICAL_CONFIGURATION
                if name == "numerical_soc_projection_scale"
                else ParameterRole.DEV_PRIOR_UNCERTAINTY
                if name == "friction_coefficient"
                else ParameterRole.FIXED_ENGINEERING,
                SourceIdentity.DEV_POLICY
                if name in {"friction_coefficient", "numerical_soc_projection_scale"}
                else SourceIdentity.ACCEPTED_AUTHORITY,
                "frozen rigid contact / DEV sensitivity",
            )
            for name in contact_values
        ),
        metadata=_bundle_component_metadata("m03_contact_parameters", contact_values),
    )

    beam_values: dict[str, Any] = {
        "bending_enabled": bending_enabled,
        "model_id": "euler_bernoulli",
        "youngs_modulus_mpa": _finite(youngs_modulus_mpa, "youngs_modulus_mpa")
        if bending_enabled
        else None,
        "poisson_ratio": _finite(poisson_ratio, "poisson_ratio") if bending_enabled else None,
        "maximum_rotation_rad": 0.15,
        "minimum_slenderness_ratio": 4.0,
        "maximum_tip_deflection_over_length": 0.10,
    }
    beam = BeamParameterBundle(
        **beam_values,
        evidence=tuple(
            parameter_evidence(
                name,
                "MPa" if name == "youngs_modulus_mpa" else "rad" if name.endswith("_rad") else "1",
                ParameterRole.DEV_PRIOR_UNCERTAINTY
                if name in {"youngs_modulus_mpa", "poisson_ratio"}
                else ParameterRole.NUMERICAL_CONFIGURATION
                if name.startswith("maximum_") or name.startswith("minimum_")
                else ParameterRole.FIXED_ENGINEERING,
                SourceIdentity.DEV_POLICY,
                "DEV handbook range or model-validity gate",
            )
            for name in beam_values
        ),
        metadata=_bundle_component_metadata("m03_beam_parameters", beam_values),
    )

    if mount_mode is MountMode.RIGID_MOUNT:
        spring_stiffness_n_per_mm = None
    mount_values = {
        "mode": mount_mode,
        "spring_stiffness_n_per_mm": spring_stiffness_n_per_mm,
        "minimum_compression_mm": 0.0,
        "maximum_compression_mm": 4.0,
    }
    mount = MountParameterBundle(
        mode=mount_mode,
        spring_stiffness_n_per_mm=spring_stiffness_n_per_mm,
        minimum_compression_mm=0.0,
        maximum_compression_mm=4.0,
        evidence=tuple(
            parameter_evidence(
                name,
                "N/mm"
                if name == "spring_stiffness_n_per_mm"
                else "mm"
                if "compression" in name
                else "1",
                ParameterRole.DEV_PRIOR_UNCERTAINTY
                if name == "spring_stiffness_n_per_mm"
                else ParameterRole.DESIGN_VARIABLE
                if name == "mode"
                else ParameterRole.FIXED_ENGINEERING,
                SourceIdentity.DEV_POLICY
                if name == "spring_stiffness_n_per_mm"
                else SourceIdentity.FIXED_ENGINEERING,
                "A-authoritative mount branch",
            )
            for name in mount_values
        ),
        metadata=_bundle_component_metadata("m03_mount_parameters", mount_values),
    )

    material_values = {
        "material_model_id": "no_damage",
        "failure_prediction_allowed": False,
        "material_dissipation_enabled": False,
        "damage_store_writable": False,
    }
    material = NoDamageParameterBundle(
        material_model_id="no_damage",
        failure_prediction_allowed=False,
        material_dissipation_enabled=False,
        damage_store_writable=False,
        evidence=tuple(
            parameter_evidence(
                name,
                "1",
                ParameterRole.FIXED_ENGINEERING,
                SourceIdentity.DEV_POLICY,
                "frozen no_damage capability gate",
            )
            for name in material_values
        ),
        metadata=_bundle_component_metadata("m03_no_damage_parameters", material_values),
    )

    numerical_values: dict[str, float | int] = {
        "initial_step_over_rt": 0.5,
        "maximum_step_over_rt": 1.0,
        "minimum_step_over_rt": 0.001,
        "event_position_tolerance_over_rt": 0.01,
        "force_absolute_tolerance_n": 1.0e-6,
        "force_relative_tolerance": 1.0e-5,
        "work_absolute_tolerance_n_mm": 1.0e-9,
        "work_relative_tolerance": 1.0e-5,
        "maximum_newton_iterations": 50,
        "maximum_event_iterations": 80,
        "maximum_same_position_cascade": 50,
        "acceptance_force_resolution_n": 1.0e-6,
        "acceptance_work_resolution_n_mm": 1.0e-9,
    }
    numerical = NumericalParameterBundle(
        initial_step_over_rt=0.5,
        maximum_step_over_rt=1.0,
        minimum_step_over_rt=0.001,
        event_position_tolerance_over_rt=0.01,
        force_absolute_tolerance_n=1.0e-6,
        force_relative_tolerance=1.0e-5,
        work_absolute_tolerance_n_mm=1.0e-9,
        work_relative_tolerance=1.0e-5,
        maximum_newton_iterations=50,
        maximum_event_iterations=80,
        maximum_same_position_cascade=50,
        acceptance_force_resolution_n=1.0e-6,
        acceptance_work_resolution_n_mm=1.0e-9,
        evidence=tuple(
            parameter_evidence(
                name,
                "N" if name.endswith("_n") else "N*mm" if name.endswith("_n_mm") else "1",
                ParameterRole.NUMERICAL_CONFIGURATION,
                SourceIdentity.DEV_POLICY,
                "resolved convergence configuration",
            )
            for name in numerical_values
        ),
        metadata=_bundle_component_metadata("m03_numerical_parameters", numerical_values),
    )

    components: list[str] = []
    if bending_enabled:
        components.append("euler_bernoulli_beam")
    if mount_mode is MountMode.INDEPENDENT_AXIAL_SPRINGS:
        components.append("independent_axial_spring")
    identity_payload = {
        "needle": dataclasses.asdict(needle),
        "contact": dataclasses.asdict(contact),
        "beam": dataclasses.asdict(beam),
        "mount": dataclasses.asdict(mount),
        "material": dataclasses.asdict(material),
        "numerical": dataclasses.asdict(numerical),
        "surface_scale_reference_rt_mm": SURFACE_SCALE_REFERENCE_RT_MM,
        "declared_physical_compliance_components": tuple(components),
    }
    return SingleSpineParameterBundle(
        needle,
        contact,
        beam,
        mount,
        material,
        numerical,
        SURFACE_SCALE_REFERENCE_RT_MM,
        tuple(components),
        stable_content_id("m03_parameter_bundle", identity_payload),
        semantic_hash(identity_payload),
        make_metadata(
            "m03_parameter_bundle_metadata",
            identity_payload,
            source_identity=SourceIdentity.DEV_POLICY,
        ),
    )


@dataclass(frozen=True, slots=True)
class LocalFrame:
    frame_id: str
    e_x_global: Vector3
    e_y_global: Vector3
    e_z_global: Vector3 = (0.0, 0.0, 1.0)
    metadata: SemanticMetadata | None = None

    def __post_init__(self) -> None:
        ex = np.asarray(_vector3(self.e_x_global, "e_x_global"), dtype=np.float64)
        ey = np.asarray(_vector3(self.e_y_global, "e_y_global"), dtype=np.float64)
        ez = np.asarray(_vector3(self.e_z_global, "e_z_global"), dtype=np.float64)
        basis = np.column_stack((ex, ey, ez))
        if not np.allclose(basis.T @ basis, np.eye(3), atol=1.0e-10, rtol=1.0e-10):
            raise ContractViolation("local frame basis must be orthonormal")
        if not np.allclose(np.cross(ez, ex), ey, atol=1.0e-10, rtol=1.0e-10):
            raise ContractViolation("local e_y must equal global_Z cross local e_x")
        if not math.isclose(float(np.linalg.det(basis)), 1.0, abs_tol=1.0e-10):
            raise ContractViolation("local frame must be right handed")


def canonical_local_frame() -> LocalFrame:
    payload = {
        "frame_id": "M03_LOCAL_CANONICAL",
        "e_x_global": (1.0, 0.0, 0.0),
        "e_y_global": (0.0, 1.0, 0.0),
        "e_z_global": (0.0, 0.0, 1.0),
    }
    return LocalFrame(
        "M03_LOCAL_CANONICAL",
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
        make_metadata("m03_local_frame", payload),
    )


@dataclass(frozen=True, slots=True)
class RigidPose:
    position_mm: Vector3
    rotation_global_from_local: Matrix3
    expressed_frame_id: str
    reference_point_id: str
    length_unit: str
    angle_unit: str
    pose_version: str
    pose_id: str

    def __post_init__(self) -> None:
        _vector3(self.position_mm, "position_mm")
        _matrix3(self.rotation_global_from_local, "rotation_global_from_local")
        if self.length_unit != "mm" or self.angle_unit != "rad":
            raise ContractViolation("pose must explicitly use mm and rad")
        expected = stable_content_id(
            "m03_pose",
            {
                "position_mm": self.position_mm,
                "rotation_global_from_local": self.rotation_global_from_local,
                "expressed_frame_id": self.expressed_frame_id,
                "reference_point_id": self.reference_point_id,
                "pose_version": self.pose_version,
            },
        )
        if self.pose_id != expected:
            raise ContractViolation("pose identity mismatch")


def make_rigid_pose(
    position_mm: Vector3,
    *,
    rotation_global_from_local: Matrix3 = (
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    ),
    expressed_frame_id: str = "GLOBAL",
    reference_point_id: str = "M03_BASE_REFERENCE_O",
) -> RigidPose:
    resolved_position = _vector3(position_mm, "position_mm")
    payload = {
        "position_mm": resolved_position,
        "rotation_global_from_local": rotation_global_from_local,
        "expressed_frame_id": expressed_frame_id,
        "reference_point_id": reference_point_id,
        "pose_version": "M03_GLOBAL_LEFT_MULTIPLY_1",
    }
    return RigidPose(
        position_mm=resolved_position,
        rotation_global_from_local=rotation_global_from_local,
        expressed_frame_id=expressed_frame_id,
        reference_point_id=reference_point_id,
        length_unit="mm",
        angle_unit="rad",
        pose_version="M03_GLOBAL_LEFT_MULTIPLY_1",
        pose_id=stable_content_id("m03_pose", payload),
    )


@dataclass(frozen=True, slots=True)
class PrescribedBaseIncrement:
    translation_global_mm: Vector3
    rotation_global_rad: Vector3
    interpolation: str
    increment_basis: tuple[str, ...]
    expressed_frame_id: str
    reference_point_id: str
    length_unit: str = "mm"
    angle_unit: str = "rad"

    def __post_init__(self) -> None:
        _vector3(self.translation_global_mm, "translation_global_mm")
        rotation = _vector3(self.rotation_global_rad, "rotation_global_rad")
        if any(abs(item) > 0.0 for item in rotation):
            raise ContractViolation(
                "M03_KINEMATIC_MODE_UNSUPPORTED: embedded rotation increments are not certified"
            )
        if self.length_unit != "mm" or self.angle_unit != "rad":
            raise ContractViolation("base increment requires explicit mm/rad units")
        if self.interpolation != "linear_translation_global":
            raise ContractViolation("unsupported base-increment interpolation")


@dataclass(frozen=True, slots=True)
class NeedleIdentity:
    needle_id: str
    unit_id: str
    geometry_id: str
    structure_parameter_id: str
    material_parameter_id: str
    needle_strength_parameter_id: str

    def __post_init__(self) -> None:
        if any(not item for item in dataclasses.astuple(self)):
            raise ContractViolation("needle identity fields must be non-empty")


@dataclass(frozen=True, slots=True)
class AcceptedSupportState:
    support_id: str
    candidate_id: str
    point_global_mm: Vector3
    normal_global: Vector3
    tangent_basis_global: tuple[Vector3, Vector3]
    normal_multiplier_n: float
    tangential_multiplier_n: Vector2
    accumulated_slip_mm: float
    motion_state: ContactMotionState

    def __post_init__(self) -> None:
        _vector3(self.point_global_mm, "point_global_mm")
        normal = np.asarray(_vector3(self.normal_global, "normal_global"))
        if not math.isclose(float(np.linalg.norm(normal)), 1.0, abs_tol=1.0e-9):
            raise ContractViolation("support normal must be unit length")
        for tangent in self.tangent_basis_global:
            vector = np.asarray(_vector3(tangent, "tangent_basis_global"))
            if not math.isclose(float(np.linalg.norm(vector)), 1.0, abs_tol=1.0e-9):
                raise ContractViolation("support tangents must be unit length")
            if not math.isclose(float(np.dot(vector, normal)), 0.0, abs_tol=1.0e-9):
                raise ContractViolation("support tangents must be normal-orthogonal")
        if _finite(self.normal_multiplier_n, "normal_multiplier_n") < 0.0:
            raise ContractViolation("normal multiplier cannot be negative")
        if _finite(self.accumulated_slip_mm, "accumulated_slip_mm") < 0.0:
            raise ContractViolation("accumulated slip cannot be negative")


@dataclass(frozen=True, slots=True)
class ImmutableSingleSpineState:
    state_id: str
    state_version: int
    base_pose: RigidPose
    primary_state: PrimaryMechanicalState
    active_supports: tuple[AcceptedSupportState, ...]
    beam_tip_translation_global_mm: Vector3
    beam_tip_rotation_global_rad: Vector3
    spring_state: SpringState
    spring_compression_mm: float
    total_path_x_mm: float
    drag_elapsed_time_s: float
    contact_cycle_id: int
    event_sequence_number: int
    cumulative_friction_dissipation_n_mm: float
    cumulative_input_work_n_mm: float
    accepted_response_hash: str
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.state_version < 0 or self.contact_cycle_id < 0 or self.event_sequence_number < 0:
            raise ContractViolation("state/cycle/event versions cannot be negative")
        _vector3(self.beam_tip_translation_global_mm, "beam_tip_translation_global_mm")
        _vector3(self.beam_tip_rotation_global_rad, "beam_tip_rotation_global_rad")
        for name in (
            "spring_compression_mm",
            "total_path_x_mm",
            "drag_elapsed_time_s",
            "cumulative_friction_dissipation_n_mm",
        ):
            if _finite(getattr(self, name), name) < 0.0:
                raise ContractViolation(f"{name} cannot be negative")
        _finite(self.cumulative_input_work_n_mm, "cumulative_input_work_n_mm")


def make_initial_single_spine_state(base_pose: RigidPose) -> ImmutableSingleSpineState:
    accepted_response_hash = semantic_hash("M03_INITIAL_OPEN_RESPONSE")
    payload = {
        "base_pose_id": base_pose.pose_id,
        "state_version": 0,
        "primary_state": PrimaryMechanicalState.OPEN,
        "active_supports": (),
        "beam_tip_translation_global_mm": (0.0, 0.0, 0.0),
        "beam_tip_rotation_global_rad": (0.0, 0.0, 0.0),
        "spring_state": SpringState.AT_ORIGINAL_LENGTH,
        "spring_compression_mm": 0.0,
        "total_path_x_mm": 0.0,
        "drag_elapsed_time_s": 0.0,
        "contact_cycle_id": 0,
        "event_sequence_number": 0,
        "cumulative_friction_dissipation_n_mm": 0.0,
        "cumulative_input_work_n_mm": 0.0,
        "accepted_response_hash": accepted_response_hash,
    }
    state_id = stable_content_id("m03_single_spine_state", payload)
    return ImmutableSingleSpineState(
        state_id,
        0,
        base_pose,
        PrimaryMechanicalState.OPEN,
        (),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        SpringState.AT_ORIGINAL_LENGTH,
        0.0,
        0.0,
        0.0,
        0,
        0,
        0.0,
        0.0,
        accepted_response_hash,
        make_metadata("m03_initial_state", payload),
    )


@dataclass(frozen=True, slots=True)
class SharedDamageStoreSnapshot:
    snapshot_id: str
    version: int
    content_hash: str
    schema_id: str
    read_only: bool = True

    def __post_init__(self) -> None:
        if self.version < 0 or not self.read_only:
            raise ContractViolation("no_damage shared snapshot must be immutable")


@dataclass(frozen=True, slots=True)
class TrialIdentity:
    global_step_id: str
    global_trial_id: str
    newton_iteration_id: str
    caller_sequence_id: str

    def __post_init__(self) -> None:
        if any(not item for item in dataclasses.astuple(self)):
            raise ContractViolation("trial identity fields must be non-empty")


@dataclass(frozen=True, slots=True)
class EventLocationConfig:
    locate_events: bool
    allowed_event_categories: tuple[str, ...]
    suggested_maximum_increment_fraction: float
    numerical_config_id: str

    def __post_init__(self) -> None:
        fraction = _finite(
            self.suggested_maximum_increment_fraction,
            "suggested_maximum_increment_fraction",
        )
        if not 0.0 < fraction <= 1.0:
            raise ContractViolation("suggested event increment fraction must lie in (0,1]")


@dataclass(frozen=True, slots=True)
class QualityRequest:
    diagnostic_level: str
    require_residual_blocks: bool
    require_graph_quality: bool
    require_nonuniqueness: bool
    require_geometry_witness: bool
    fatal_quality_checks_enabled: bool = True

    def __post_init__(self) -> None:
        if not self.fatal_quality_checks_enabled:
            raise ContractViolation("caller cannot disable fatal M03 quality checks")


@dataclass(frozen=True, slots=True)
class ContinuationHint:
    opaque_handle: str
    branch_id: str
    source_response_hash: str


_DUPLICATE_LOAD_FIELDS = frozenset(
    {
        "Pz",
        "pz",
        "per_spine_normal_force",
        "single_spine_Pz",
        "single_spine_pz",
        "normal_force_target",
    }
)


@dataclass(frozen=True, slots=True)
class EmbeddedSingleSpineTrialRequest:
    contract_id: str
    contract_version: str
    call_mode: CallMode
    needle_identity: NeedleIdentity
    surface_query_handle: Any
    base_pose_n: RigidPose
    prescribed_base_increment: PrescribedBaseIncrement
    immutable_single_spine_state_n: ImmutableSingleSpineState
    shared_damage_store_snapshot: SharedDamageStoreSnapshot
    parameter_bundle: SingleSpineParameterBundle
    trial_identity: TrialIdentity
    requested_tangent_mode: RequestedTangentMode
    event_location_config: EventLocationConfig
    quality_request: QualityRequest
    continuation_hint: ContinuationHint | None
    local_frame: LocalFrame
    task_direction_global: Vector3
    request_id: str
    request_hash: str
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.contract_id != A_TO_B_CONTRACT_ID:
            raise ContractViolation("embedded request contract_id must be A_TO_B")
        if self.contract_version != A_TO_B_CONTRACT_VERSION:
            raise ContractViolation("embedded request contract_version must be 1.0.0")
        if self.call_mode is not CallMode.EMBEDDED_CONSTITUTIVE_TRIAL:
            raise ContractViolation("embedded_constitutive_trial is the only B call mode")
        handle = self.surface_query_handle
        if not hasattr(handle, "realization") or not hasattr(handle, "handle_id"):
            raise ContractViolation("surface_query_handle must be an M01 public query handle")
        if self.parameter_bundle.needle.beta_rad != 0.0:
            raise ContractViolation("M03_KINEMATIC_MODE_UNSUPPORTED: nonzero beta is read-only")
        direction = np.asarray(_vector3(self.task_direction_global, "task_direction_global"))
        if not math.isclose(float(np.linalg.norm(direction)), 1.0, abs_tol=1.0e-10):
            raise ContractViolation("M03_TASK_DIRECTION_INVALID: task direction must be unit")
        if self.base_pose_n.pose_id != self.immutable_single_spine_state_n.base_pose.pose_id:
            raise ContractViolation("base pose and immutable history snapshot disagree")
        expected_hash = semantic_hash(self.identity_payload())
        expected_id = stable_content_id("m03_embedded_request", self.identity_payload())
        if self.request_hash != expected_hash or self.request_id != expected_id:
            raise ContractViolation("embedded request identity/hash mismatch")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "call_mode": self.call_mode,
            "needle_identity": self.needle_identity,
            "surface_query_handle_id": self.surface_query_handle.handle_id,
            "base_pose_id": self.base_pose_n.pose_id,
            "prescribed_base_increment": self.prescribed_base_increment,
            "immutable_state_id": self.immutable_single_spine_state_n.state_id,
            "damage_snapshot_id": self.shared_damage_store_snapshot.snapshot_id,
            "parameter_bundle_id": self.parameter_bundle.parameter_bundle_id,
            "trial_identity": self.trial_identity,
            "requested_tangent_mode": self.requested_tangent_mode,
            "event_location_config": self.event_location_config,
            "quality_request": self.quality_request,
            "continuation_hint": self.continuation_hint,
            "local_frame": self.local_frame,
            "task_direction_global": self.task_direction_global,
        }

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> EmbeddedSingleSpineTrialRequest:
        duplicate = sorted(_DUPLICATE_LOAD_FIELDS.intersection(values))
        if duplicate:
            raise ContractViolation(
                "CONTRACT_VIOLATION_DUPLICATE_NORMAL_LOAD",
                details={
                    "reason_code": M03ReasonCode.DUPLICATE_NORMAL_LOAD.value,
                    "fields": duplicate,
                },
            )
        expected = {item.name for item in dataclasses.fields(cls)}
        unknown = sorted(set(values) - expected)
        missing = sorted(expected - set(values))
        if unknown or missing:
            raise ContractViolation(
                "M03 embedded request fields do not match the frozen contract",
                details={"unknown": unknown, "missing": missing},
            )
        return cls(**values)


def make_embedded_request(
    *,
    needle_identity: NeedleIdentity,
    surface_query_handle: Any,
    base_pose_n: RigidPose,
    prescribed_base_increment: PrescribedBaseIncrement,
    immutable_single_spine_state_n: ImmutableSingleSpineState,
    parameter_bundle: SingleSpineParameterBundle,
    trial_identity: TrialIdentity,
    local_frame: LocalFrame | None = None,
    task_direction_global: Vector3 | None = None,
    requested_tangent_mode: RequestedTangentMode = RequestedTangentMode.GENERALIZED_ONE_SIDED,
) -> EmbeddedSingleSpineTrialRequest:
    frame = canonical_local_frame() if local_frame is None else local_frame
    task = frame.e_x_global if task_direction_global is None else task_direction_global
    damage_hash = semantic_hash({"model": "no_damage", "version": 0})
    snapshot = SharedDamageStoreSnapshot(
        stable_content_id("m03_no_damage_snapshot", {"hash": damage_hash}),
        0,
        damage_hash,
        "A_TO_B_SHARED_DAMAGE_STORE_1.0.0_NO_DAMAGE_VIEW",
    )
    event_config = EventLocationConfig(True, ("all_m03_signed_events",), 1.0, "M03_NUMERICS_1")
    quality = QualityRequest("STANDARD", True, True, True, True)
    payload = {
        "contract_id": A_TO_B_CONTRACT_ID,
        "contract_version": A_TO_B_CONTRACT_VERSION,
        "call_mode": CallMode.EMBEDDED_CONSTITUTIVE_TRIAL,
        "needle_identity": needle_identity,
        "surface_query_handle_id": surface_query_handle.handle_id,
        "base_pose_id": base_pose_n.pose_id,
        "prescribed_base_increment": prescribed_base_increment,
        "immutable_state_id": immutable_single_spine_state_n.state_id,
        "damage_snapshot_id": snapshot.snapshot_id,
        "parameter_bundle_id": parameter_bundle.parameter_bundle_id,
        "trial_identity": trial_identity,
        "requested_tangent_mode": requested_tangent_mode,
        "event_location_config": event_config,
        "quality_request": quality,
        "continuation_hint": None,
        "local_frame": frame,
        "task_direction_global": task,
    }
    return EmbeddedSingleSpineTrialRequest(
        A_TO_B_CONTRACT_ID,
        A_TO_B_CONTRACT_VERSION,
        CallMode.EMBEDDED_CONSTITUTIVE_TRIAL,
        needle_identity,
        surface_query_handle,
        base_pose_n,
        prescribed_base_increment,
        immutable_single_spine_state_n,
        snapshot,
        parameter_bundle,
        trial_identity,
        requested_tangent_mode,
        event_config,
        quality,
        None,
        frame,
        task,
        stable_content_id("m03_embedded_request", payload),
        semantic_hash(payload),
        make_metadata("m03_embedded_request_metadata", payload),
    )


@dataclass(frozen=True, slots=True)
class StageEvidence:
    value: bool
    reason_code: str
    evidence_references: tuple[str, ...]
    criteria_version: str = "M03_FIVE_STAGE_1.0.0_PROPOSED_SUPPLEMENT"


@dataclass(frozen=True, slots=True)
class FiveStageFunnel:
    geometric_candidate: StageEvidence
    loaded_contact: StageEvidence
    frictionally_stable: StageEvidence
    load_bearing: StageEvidence
    released: StageEvidence
    recontacted_zero_load: StageEvidence
    reengaged: StageEvidence

    def __post_init__(self) -> None:
        if self.load_bearing.value and not (
            self.loaded_contact.value and self.frictionally_stable.value
        ):
            raise ContractViolation("load_bearing requires loaded and frictionally stable")
        if self.reengaged.value and not self.recontacted_zero_load.value:
            raise ContractViolation("reengagement requires a prior zero-load recontact")


@dataclass(frozen=True, slots=True)
class WrenchResponse:
    direction: str
    force_global_n: Vector3
    moment_global_at_o_n_mm: Vector3
    expressed_frame_id: str
    reference_point_id: str
    reference_point_position_global_mm: Vector3
    force_unit: str
    moment_unit: str
    opposite_wrench_b_on_a: Vector6
    grip_resistance_rx_n: float
    task_resistance_n: float
    task_direction_global: Vector3
    wrench_uniqueness: WrenchUniqueness
    admissible_wrench_graph_handle: str | None
    rank: int
    nullspace_basis: tuple[Vector6, ...]
    reference_transport_work_invariant: bool

    def __post_init__(self) -> None:
        if self.direction != "A_on_B":
            raise ContractViolation("canonical M03 wrench direction is A_on_B")
        force = _vector3(self.force_global_n, "force_global_n")
        moment = _vector3(self.moment_global_at_o_n_mm, "moment_global_at_o_n_mm")
        reference = _vector3(
            self.reference_point_position_global_mm,
            "reference_point_position_global_mm",
        )
        del reference
        if self.force_unit != "N" or self.moment_unit != "N*mm":
            raise ContractViolation("wrench units must be N and N*mm")
        expected_opposite = tuple(-item for item in (*force, *moment))
        if not np.allclose(
            np.asarray(self.opposite_wrench_b_on_a),
            np.asarray(expected_opposite),
            atol=0.0,
            rtol=0.0,
        ):
            raise ContractViolation("opposite_wrench_B_on_A must be the exact negative")
        if not 0 <= self.rank <= 6:
            raise ContractViolation("wrench rank must lie in [0,6]")
        if self.wrench_uniqueness is WrenchUniqueness.SET_VALUED_CONSTRAINT:
            if self.admissible_wrench_graph_handle is None or not self.nullspace_basis:
                raise ContractViolation("set-valued wrench requires graph and nullspace evidence")

    @property
    def wrench_a_on_b(self) -> Vector6:
        return (*self.force_global_n, *self.moment_global_at_o_n_mm)


@dataclass(frozen=True, slots=True)
class ContactSupportResponse:
    support_id: str
    candidate_id: str
    point_global_mm: Vector3
    feature_type: str
    chart_id: str
    legal_cap_gap_mm: float
    effective_gap_mm: float
    normal_global: Vector3
    tangent_basis_global: tuple[Vector3, Vector3]
    contact_force_global_n: Vector3
    normal_multiplier_n: float
    tangential_multiplier_n: Vector2
    objective_slip_increment_global_mm: Vector3
    objective_slip_increment_local_mm: Vector2
    accumulated_slip_if_committed_preview_mm: float
    motion_state: ContactMotionState
    rolling_without_slip: bool
    cap_legality_margin_mm: float


@dataclass(frozen=True, slots=True)
class GeometryContactResponse:
    active_support_ids: tuple[str, ...]
    near_contact_support_ids: tuple[str, ...]
    supports: tuple[ContactSupportResponse, ...]
    candidate_ids: tuple[str, ...]
    tip_center_global_mm: Vector3
    current_axis_global: Vector3
    initial_axis_global: Vector3
    cone_gap_mm: float | None
    shaft_gap_mm: float | None
    mount_gap_mm: float | None
    minimum_full_body_clearance_mm: float | None
    query_receipt_ids: tuple[str, ...]
    query_quality: str
    geometry_uncertainty_mm: float | None
    nonsmooth: bool
    footprint_id: str | None
    lod_purpose: LODPurpose
    candidate_any: bool
    candidate_robust: bool


@dataclass(frozen=True, slots=True)
class StructureResponse:
    needle_bending_enabled: bool
    beam_model_id: str
    beam_model_state: BeamModelState
    beam_tip_translation_global_mm: Vector3
    beam_tip_rotation_global_rad: Vector3
    beam_tip_translation_needle_mm: Vector3
    beam_tip_rotation_needle_rad: Vector3
    beam_root_reaction_force_global_n: Vector3
    beam_root_reaction_moment_global_n_mm: Vector3
    section_resultants_needle: Vector6
    beam_energy_n_mm: float
    mount_mode: MountMode
    spring_state: SpringState
    spring_compression_mm: float
    spring_force_n: float
    remaining_spring_travel_mm: float
    hard_stop_reaction_n: float
    spring_energy_n_mm: float
    optional_contact_compression_mm: None
    optional_contact_energy_n_mm: float
    yield_margin: None
    fracture_margin: None
    needle_strength_status: NeedleStrengthSubstate

    def __post_init__(self) -> None:
        if (
            self.optional_contact_compression_mm is not None
            or self.optional_contact_energy_n_mm != 0
        ):
            raise ContractViolation("rigid contact cannot store physical compression energy")
        if self.yield_margin is not None or self.fracture_margin is not None:
            raise ContractViolation("needle strength margins are unavailable in M03")
        if self.needle_strength_status is not NeedleStrengthSubstate.NEEDLE_STRENGTH_UNAVAILABLE:
            raise ContractViolation("M03 strength status must remain unavailable")


@dataclass(frozen=True, slots=True)
class MaterialDamageResponse:
    material_model_id: str
    evidence_status: str
    queried_patch_ids: tuple[str, ...]
    damage_read_set_with_versions: tuple[str, ...]
    trial_damage_intents: tuple[str, ...]
    damage_write_set: tuple[str, ...]
    initiation_utilization: None
    current_capacity_scale: None
    failure_mode_weights: tuple[float, ...]
    material_substate: MaterialSubstate
    friction_dissipation_trial_n_mm: float
    material_dissipation_trial_n_mm: float
    released_recoverable_energy_trial_n_mm: float
    damage_conflict_signature: None
    failure_prediction_allowed: bool
    fracture_energy_n_per_mm: None
    status: StatusTuple

    def __post_init__(self) -> None:
        if self.material_model_id != "no_damage":
            raise ContractViolation("M03 material response must be no_damage")
        if any((self.trial_damage_intents, self.damage_write_set, self.failure_mode_weights)):
            raise ContractViolation("no_damage cannot return damage intents/write sets/modes")
        if self.initiation_utilization is not None or self.current_capacity_scale is not None:
            raise ContractViolation("no_damage material capacity fields are NOT_APPLICABLE")
        if self.material_dissipation_trial_n_mm != 0.0:
            raise ContractViolation("no_damage material dissipation is exactly zero")
        if self.failure_prediction_allowed or self.fracture_energy_n_per_mm is not None:
            raise ContractViolation("M03 cannot predict material failure or fracture energy")


@dataclass(frozen=True, slots=True)
class EventCandidateResponse:
    event_id: str
    event_kind: str
    raw_guard: float
    raw_guard_unit: str
    zero_value: float
    admissible_side: str
    direction: str
    event_fraction: float | None
    bracket: tuple[float, float] | None
    coverage_certificate_id: str | None
    owner: str = "M03"


@dataclass(frozen=True, slots=True)
class StateEventsResponse:
    primary_mechanical_state: PrimaryMechanicalState
    per_contact_motion_states: tuple[ContactMotionState, ...]
    spring_substate: SpringState
    material_substate: MaterialSubstate
    needle_strength_substate: NeedleStrengthSubstate
    quality_solve_state: str
    all_event_candidates: tuple[EventCandidateResponse, ...]
    simultaneous_event_set: tuple[str, ...]
    earliest_event_fraction: float | None
    event_fraction_bracket: tuple[float, float] | None
    suggested_common_increment_fraction: float
    event_one_sided_consistency: bool
    terminal_or_continuable: str
    five_stage: FiveStageFunnel
    operation_phase: OperationPhase | None

    def __post_init__(self) -> None:
        fraction = _finite(
            self.suggested_common_increment_fraction,
            "suggested_common_increment_fraction",
        )
        if not 0.0 < fraction <= 1.0:
            raise ContractViolation("suggested common increment must lie in (0,1]")


@dataclass(frozen=True, slots=True)
class LinearizationResponse:
    tangent_or_secant_matrix: Matrix6 | None
    row_wrench_frame_and_reference: str
    column_increment_basis: tuple[str, ...]
    linearization_point: str
    tangent_status: TangentStatus
    branch_id: str
    finite_difference_check_metadata: str | None


@dataclass(frozen=True, slots=True)
class ResidualBlockReport:
    block_id: str
    semantics: str
    raw_norm: float
    raw_unit: str
    reference_norm: float
    absolute_tolerance: float
    relative_tolerance: float
    scale_id: str
    normalized_norm: float
    hard: bool
    passed: bool

    def __post_init__(self) -> None:
        for name in (
            "raw_norm",
            "reference_norm",
            "absolute_tolerance",
            "relative_tolerance",
            "normalized_norm",
        ):
            if _finite(getattr(self, name), name) < 0.0:
                raise ContractViolation(f"{name} cannot be negative")
        if self.hard and not self.passed and self.normalized_norm <= 1.0:
            raise ContractViolation("failed hard residual must exceed its normalized gate")


@dataclass(frozen=True, slots=True)
class DiagnosticsResponse:
    residual_blocks: tuple[ResidualBlockReport, ...]
    complementarity_residual: float
    contact_soc_residual: float
    graph_residual: float
    geometric_closure_residual_mm: float
    beam_residual_mm: float
    spring_residual_n: float
    work_balance_error_n_mm: float
    generalized_jacobian_rank: int
    generalized_jacobian_condition: float | None
    jacobian_quality: str
    force_distribution_nonuniqueness: bool
    parameter_evidence_status: str
    surface_data_quality: str
    uncertainty_bound_mm: float | None
    error_class: EmbeddedErrorClass
    error_detail: str
    failure_axis: FailureAxis
    original_reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TransactionResponse:
    opaque_trial_state_handle: str
    rollback_token: str
    provisional_commit_intent: str
    accepted_history_version_read: int
    damage_snapshot_version_read: int
    request_hash: str
    response_hash: str
    idempotency_key: str
    damage_intents: tuple[str, ...] = ()
    damage_write_set: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.damage_intents or self.damage_write_set:
            raise ContractViolation("M03 no_damage transaction cannot write DamageStore")


@dataclass(frozen=True, slots=True)
class WorkIncrementResponse:
    base_or_actuator_input_work_n_mm: float
    delta_beam_energy_n_mm: float
    delta_spring_energy_n_mm: float
    friction_dissipation_n_mm: float
    material_dissipation_n_mm: float
    returned_recoverable_energy_n_mm: float
    remaining_stored_energy_n_mm: float
    closure_error_n_mm: float
    normalized_closure_error: float


@dataclass(frozen=True, slots=True)
class SingleSpineTrialResponse:
    contract_id: str
    contract_version: str
    response_id: str
    response_hash: str
    wrench: WrenchResponse
    geometry_contact: GeometryContactResponse
    structure: StructureResponse
    material_damage: MaterialDamageResponse
    state_events: StateEventsResponse
    linearization: LinearizationResponse
    diagnostics: DiagnosticsResponse
    work: WorkIncrementResponse
    transaction: TransactionResponse
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if (
            self.contract_id != A_TO_B_CONTRACT_ID
            or self.contract_version != A_TO_B_CONTRACT_VERSION
        ):
            raise ContractViolation("response must preserve accepted A_TO_B 1.0.0 identity")
        if self.transaction.response_hash != self.response_hash:
            raise ContractViolation("transaction response hash must match response")
        if self.diagnostics.error_class is EmbeddedErrorClass.OPEN_RESPONSE:
            if any(abs(item) > 0.0 for item in self.wrench.wrench_a_on_b):
                raise ContractViolation("embedded OPEN_RESPONSE must return zero contact wrench")


@dataclass(frozen=True, slots=True)
class InitialPosePolicy:
    policy_id: str
    minimum_gap_formula: str
    approach_direction: str
    full_body_clearance_required: bool


@dataclass(frozen=True, slots=True)
class SearchPolicy:
    mode: str
    direction: str
    earliest_finite_cap_contact: bool
    fixed_local_x: bool

    def __post_init__(self) -> None:
        if self.mode != "NESTED_Z_SEARCH":
            raise ContractViolation("M03 standalone baseline requires NESTED_Z_SEARCH")


@dataclass(frozen=True, slots=True)
class PreloadPolicy:
    target_normal_force_n: float
    homotopy_start: float
    homotopy_end: float
    minimum_homotopy_points: int

    def __post_init__(self) -> None:
        if self.target_normal_force_n != 0.5:
            raise ContractViolation("standalone normal target is frozen to 0.5 N")
        if self.homotopy_start != 0.0 or self.homotopy_end != 1.0:
            raise ContractViolation("standalone preload must use eta 0->1")
        if self.minimum_homotopy_points < 2:
            raise ContractViolation("preload cannot jump directly from zero to target")


@dataclass(frozen=True, slots=True)
class DragPolicy:
    direction: str
    travel_mm: float
    speed_mm_per_s: float
    path_clock_mapping: str

    def __post_init__(self) -> None:
        if self.direction != "+local-x" or self.travel_mm != 100.0:
            raise ContractViolation("standalone drag is frozen to +local-x for 100 mm")
        if self.speed_mm_per_s != 1.0:
            raise ContractViolation("standalone drag speed is frozen to 1 mm/s")


@dataclass(frozen=True, slots=True)
class ReleasePolicy:
    policy_id: str
    phases: tuple[OperationPhase, ...]
    operation_speed_mm_per_s: float | None
    hold_if_path_unavailable: bool

    def __post_init__(self) -> None:
        required = (
            OperationPhase.UNLOAD,
            OperationPhase.DRIVE_OFF_UNLOCK,
            OperationPhase.LIFT_OFF,
            OperationPhase.RESEARCH,
            OperationPhase.RELOAD,
        )
        if self.policy_id != "LIFT_OFF_RESEARCH_V1" or self.phases != required:
            raise ContractViolation("release policy must be frozen LIFT_OFF_RESEARCH_V1")
        if self.operation_speed_mm_per_s is not None:
            _positive(self.operation_speed_mm_per_s, "operation_speed_mm_per_s")
        if not self.hold_if_path_unavailable:
            raise ContractViolation("unavailable release path must hold at release pose")


@dataclass(frozen=True, slots=True)
class StandaloneSingleSpineRunRequest:
    schema_version: str
    operation_id: str
    run_id: str
    case_id: str
    parameter_bundle: SingleSpineParameterBundle
    surface_query_handle: Any
    local_frame: LocalFrame
    task_direction_global: Vector3
    reference_point_id: str
    initial_pose_policy: InitialPosePolicy
    search_policy: SearchPolicy
    preload_policy: PreloadPolicy
    drag_policy: DragPolicy
    release_policy: ReleasePolicy
    quality_request: QualityRequest
    diagnostic_level: str
    output_policy: str
    material_model_id: str
    damage_capability: CapabilityStatus
    strength_capability: CapabilityStatus
    resolved_config_hash: str
    request_id: str
    request_hash: str
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.schema_version != M03_SCHEMA_VERSION:
            raise ContractViolation("unsupported standalone request schema")
        if self.parameter_bundle.needle.beta_rad != 0.0:
            raise ContractViolation("M03_KINEMATIC_MODE_UNSUPPORTED: beta must be zero")
        if self.material_model_id != "no_damage":
            raise ContractViolation("standalone first release is no_damage")
        if self.damage_capability is not CapabilityStatus.NOT_APPLICABLE:
            raise ContractViolation("damage capability must be NOT_APPLICABLE")
        if self.strength_capability is not CapabilityStatus.UNAVAILABLE:
            raise ContractViolation("strength certification must be UNAVAILABLE")
        if not hasattr(self.surface_query_handle, "handle_id"):
            raise ContractViolation("standalone requires an immutable M01 query handle")
        direction = np.asarray(_vector3(self.task_direction_global, "task_direction_global"))
        if not math.isclose(float(np.linalg.norm(direction)), 1.0, abs_tol=1.0e-10):
            raise ContractViolation("standalone task direction must be unit length")


@dataclass(frozen=True, slots=True)
class StandaloneSingleSpineRunResponse:
    schema_version: str
    run_id: str
    case_id: str
    request_hash: str
    config_hash: str
    surface_realization_id: str
    parameter_bundle_id: str
    terminal_status: StandaloneTerminalStatus
    terminal_reason_code: str
    completed_travel: bool
    final_state: ImmutableSingleSpineState
    accepted_point_ids: tuple[str, ...]
    committed_event_ids: tuple[str, ...]
    rejected_trial_ids: tuple[str, ...]
    dataset_references: tuple[str, ...]
    summary_references: tuple[str, ...]
    replay_manifest_id: str | None
    final_pose: RigidPose
    remaining_travel_mm: float
    remaining_stored_energy_n_mm: float
    unavailable_protocol_reason: str | None
    experimentally_validated: MaturityStatus
    not_certifiable: bool
    damage_status: MaterialSubstate
    strength_status: NeedleStrengthSubstate
    failure_axis: FailureAxis
    metadata: SemanticMetadata

    def __post_init__(self) -> None:
        if self.schema_version != M03_SCHEMA_VERSION:
            raise ContractViolation("unsupported standalone response schema")
        if self.completed_travel != (
            self.terminal_status is StandaloneTerminalStatus.TRAVEL_COMPLETE
        ):
            raise ContractViolation("completed travel must agree with terminal status")
        if self.completed_travel and not math.isclose(
            self.final_state.total_path_x_mm, 100.0, abs_tol=1.0e-9
        ):
            raise ContractViolation("travel complete requires cumulative 100 mm")
        if self.terminal_status is StandaloneTerminalStatus.HOLD_AT_RELEASE_POSE:
            if self.unavailable_protocol_reason is None or self.remaining_travel_mm <= 0.0:
                raise ContractViolation("release hold requires reason and remaining travel")
        if self.experimentally_validated is not MaturityStatus.NOT_ASSESSED:
            raise ContractViolation("M03 experimental maturity is NOT_ASSESSED")
        if not self.not_certifiable:
            raise ContractViolation("all M03 outputs are not_certifiable")


def make_standalone_request(
    *,
    run_id: str,
    case_id: str,
    parameter_bundle: SingleSpineParameterBundle,
    surface_query_handle: Any,
    local_frame: LocalFrame | None = None,
) -> StandaloneSingleSpineRunRequest:
    frame = canonical_local_frame() if local_frame is None else local_frame
    initial = InitialPosePolicy(
        "FULL_BODY_CERTIFIED_CLEARANCE_V1",
        "max(0.20*Rt, epsilon_query + 0.01*Rt)",
        "+global-Z",
        True,
    )
    search = SearchPolicy("NESTED_Z_SEARCH", "-global-Z", True, True)
    preload = PreloadPolicy(0.5, 0.0, 1.0, 6)
    drag = DragPolicy("+local-x", 100.0, 1.0, "drag_elapsed_time_s=x_total_mm/1")
    release = ReleasePolicy(
        "LIFT_OFF_RESEARCH_V1",
        (
            OperationPhase.UNLOAD,
            OperationPhase.DRIVE_OFF_UNLOCK,
            OperationPhase.LIFT_OFF,
            OperationPhase.RESEARCH,
            OperationPhase.RELOAD,
        ),
        None,
        True,
    )
    quality = QualityRequest("STANDARD", True, True, True, True)
    resolved = {
        "schema_version": M03_SCHEMA_VERSION,
        "operation_id": "standalone_single_spine_driver",
        "run_id": run_id,
        "case_id": case_id,
        "parameter_bundle_id": parameter_bundle.parameter_bundle_id,
        "surface_query_handle_id": surface_query_handle.handle_id,
        "local_frame": frame,
        "task_direction_global": frame.e_x_global,
        "reference_point_id": "M03_BASE_REFERENCE_O",
        "initial_pose_policy": initial,
        "search_policy": search,
        "preload_policy": preload,
        "drag_policy": drag,
        "release_policy": release,
        "quality_request": quality,
        "diagnostic_level": "STANDARD",
        "output_policy": "STANDARD_ACCEPTED_RAW_AND_COMMITTED_EVENTS",
        "material_model_id": "no_damage",
        "damage_capability": CapabilityStatus.NOT_APPLICABLE,
        "strength_capability": CapabilityStatus.UNAVAILABLE,
    }
    request_hash = semantic_hash(resolved)
    return StandaloneSingleSpineRunRequest(
        M03_SCHEMA_VERSION,
        "standalone_single_spine_driver",
        run_id,
        case_id,
        parameter_bundle,
        surface_query_handle,
        frame,
        frame.e_x_global,
        "M03_BASE_REFERENCE_O",
        initial,
        search,
        preload,
        drag,
        release,
        quality,
        "STANDARD",
        "STANDARD_ACCEPTED_RAW_AND_COMMITTED_EVENTS",
        "no_damage",
        CapabilityStatus.NOT_APPLICABLE,
        CapabilityStatus.UNAVAILABLE,
        request_hash,
        stable_content_id("m03_standalone_request", resolved),
        request_hash,
        make_metadata(
            "m03_standalone_request_metadata", resolved, source_identity=SourceIdentity.DEV_POLICY
        ),
    )


__all__ = [
    "A_TO_B_CONTRACT_ID",
    "A_TO_B_CONTRACT_VERSION",
    "M03_SCHEMA_VERSION",
    "SURFACE_SCALE_REFERENCE_RT_MM",
    "AcceptedSupportState",
    "BeamModelState",
    "BeamParameterBundle",
    "CallMode",
    "ContactMotionState",
    "ContactParameterBundle",
    "ContactSupportResponse",
    "ContinuationHint",
    "DiagnosticsResponse",
    "EmbeddedErrorClass",
    "EmbeddedSingleSpineTrialRequest",
    "EventCandidateResponse",
    "EventLocationConfig",
    "FailureAxis",
    "FiveStageFunnel",
    "GeometryContactResponse",
    "ImmutableSingleSpineState",
    "InitialPosePolicy",
    "LODPurpose",
    "LinearizationResponse",
    "LocalFrame",
    "M03ReasonCode",
    "MaterialDamageResponse",
    "MaterialSubstate",
    "Matrix3",
    "Matrix6",
    "MountMode",
    "MountParameterBundle",
    "NeedleIdentity",
    "NeedleParameterBundle",
    "NeedleStrengthSubstate",
    "NoDamageParameterBundle",
    "NumericalParameterBundle",
    "OperationPhase",
    "ParameterEvidence",
    "ParameterRole",
    "PreloadPolicy",
    "PrescribedBaseIncrement",
    "PrimaryMechanicalState",
    "QualityRequest",
    "ReleasePolicy",
    "RequestedTangentMode",
    "ResidualBlockReport",
    "RigidPose",
    "SearchPolicy",
    "SemanticMetadata",
    "SharedDamageStoreSnapshot",
    "SingleSpineParameterBundle",
    "SingleSpineTrialResponse",
    "SpringState",
    "StageEvidence",
    "StandaloneSingleSpineRunRequest",
    "StandaloneSingleSpineRunResponse",
    "StandaloneTerminalStatus",
    "StateEventsResponse",
    "StructureResponse",
    "TangentStatus",
    "TransactionResponse",
    "TrialIdentity",
    "Vector2",
    "Vector3",
    "Vector6",
    "WorkIncrementResponse",
    "WrenchResponse",
    "WrenchUniqueness",
    "canonical_local_frame",
    "m03_maturity",
    "m03_status",
    "make_baseline_parameter_bundle",
    "make_embedded_request",
    "make_initial_single_spine_state",
    "make_metadata",
    "make_rigid_pose",
    "make_standalone_request",
    "parameter_evidence",
]
