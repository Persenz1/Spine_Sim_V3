"""Frozen M03 signed events and pure bridges to the public M02 API.

M03 owns the physical meaning and raw dimensional value of every guard.  M02
owns interval coverage, root localization, simultaneous-event ordering,
cascades, and transactions.  This module intentionally contains no root
finder, mutable accepted history, or constitutive solve.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.numerics.contracts import (
    EventAdmissibleSide,
    EventCertificateKind,
    EventChannelRegistration,
    EventDetectionMode,
    EventTriggerDirection,
    GuardSample,
    ReductionNorm,
    ResidualBlock,
    ResidualKind,
)
from spine_sim.numerics.events import (
    EquilibriumGuardSnapshot,
    EventCoverageDeclaration,
    EventPostResult,
    EventRegistry,
    EventSideEvaluation,
    OwnerEventEnclosure,
    evaluate_event_post_sides,
)

from .contracts import (
    EmbeddedErrorClass,
    EventCandidateResponse,
    FailureAxis,
    ResidualBlockReport,
    SingleSpineTrialResponse,
)

M03_SIGNED_EVENT_REGISTRY_VERSION = "M03_SIGNED_EVENTS_1.0.0"
M03_INTRINSIC_EVENT_OWNER = "M03_INTRINSIC_SINGLE_SPINE"
M03_STANDALONE_EVENT_OWNER = "M03_STANDALONE_SINGLE_SPINE"
M03_DEFAULT_EVENT_ENTITY_ID = "M03_SINGLE_SPINE"


class M03EventFamily(StrEnum):
    """Frozen event families required by M03 requirements section 10.3."""

    CONTACT_LOAD_RELEASE = "CONTACT_LOAD_RELEASE"
    FRICTION_SLIP = "FRICTION_SLIP"
    SUPPORT_CHART_CAP = "SUPPORT_CHART_CAP"
    SPRING = "SPRING"
    BODY_COLLISION = "BODY_COLLISION"
    DOMAIN_QUALITY = "DOMAIN_QUALITY"
    PRELOAD = "PRELOAD"
    RETURN_OPERATION = "RETURN_OPERATION"
    SWEPT_COLLISION = "SWEPT_COLLISION"
    RECONTACT = "RECONTACT"
    REENGAGEMENT = "REENGAGEMENT"
    TRAVEL = "TRAVEL"


class M03EventKind(StrEnum):
    """Physical event names; these are semantics, not numeric priorities."""

    TIP_CONTACT_ESTABLISH = "TIP_CONTACT_ESTABLISH"
    TIP_CONTACT_TANGENCY = "TIP_CONTACT_TANGENCY"
    CONTACT_LOAD_ONSET = "CONTACT_LOAD_ONSET"
    CONTACT_RELEASE = "CONTACT_RELEASE"
    FRICTION_CONE_REACHED = "FRICTION_CONE_REACHED"
    ALL_STICK_BRANCH_LOSS = "ALL_STICK_BRANCH_LOSS"
    SLIP_ONSET_CONFIRMED = "SLIP_ONSET_CONFIRMED"
    SUPPORT_CHART_SWITCH = "SUPPORT_CHART_SWITCH"
    SUPPORT_SWITCH = "SUPPORT_SWITCH"
    MIGRATION_DEGENERACY = "MIGRATION_DEGENERACY"
    CAP_LEGALITY_LOSS = "CAP_LEGALITY_LOSS"
    SPRING_ORIGINAL_LENGTH = "SPRING_ORIGINAL_LENGTH"
    SPRING_HARD_STOP = "SPRING_HARD_STOP"
    CONE_COLLISION = "CONE_COLLISION"
    SHAFT_COLLISION = "SHAFT_COLLISION"
    MOUNT_COLLISION = "MOUNT_COLLISION"
    OUT_OF_DOMAIN = "OUT_OF_DOMAIN"
    GEOMETRY_UNCERTAIN = "GEOMETRY_UNCERTAIN"
    STRUCTURAL_MODEL_LIMIT = "STRUCTURAL_MODEL_LIMIT"
    PRELOAD_TARGET_REACHED = "PRELOAD_TARGET_REACHED"
    PRELOAD_INFEASIBLE = "PRELOAD_INFEASIBLE"
    RELEASE_PATH_START = "RELEASE_PATH_START"
    RETURN_SEGMENT_START = "RETURN_SEGMENT_START"
    LIFT_OFF_CLEARANCE_REACHED = "LIFT_OFF_CLEARANCE_REACHED"
    RETURN_ENERGY_RESOLVED = "RETURN_ENERGY_RESOLVED"
    RETURN_SEGMENT_END = "RETURN_SEGMENT_END"
    RELEASE_PATH_END = "RELEASE_PATH_END"
    SWEPT_COLLISION = "SWEPT_COLLISION"
    RECONTACT_ZERO_LOAD = "RECONTACT_ZERO_LOAD"
    RELOAD_TARGET_REACHED = "RELOAD_TARGET_REACHED"
    REENGAGEMENT = "REENGAGEMENT"
    TRAVEL_COMPLETE = "TRAVEL_COMPLETE"


@dataclass(frozen=True, slots=True)
class M03SignedEventSpec:
    """One frozen raw-dimensional guard declaration owned by M03."""

    kind: M03EventKind
    family: M03EventFamily
    channel_id: str
    owner_id: str
    raw_guard_semantics: str
    raw_guard_unit: str
    zero_level: float
    admissible_side: EventAdmissibleSide
    trigger_direction: EventTriggerDirection
    detection_mode: EventDetectionMode
    certificate_capabilities: tuple[EventCertificateKind, ...]
    branch_state_scope: tuple[str, ...]
    dependency_predecessors: tuple[M03EventKind, ...] = ()
    event_priority: None = None

    def __post_init__(self) -> None:
        if not self.channel_id.startswith("m03.event."):
            raise ContractViolation("M03 event channel IDs must use the m03.event namespace")
        if self.owner_id not in {
            M03_INTRINSIC_EVENT_OWNER,
            M03_STANDALONE_EVENT_OWNER,
        }:
            raise ContractViolation("M03 event owner is outside the frozen owner boundary")
        if not self.raw_guard_semantics or self.raw_guard_unit not in {"mm", "N", "N*mm", "1"}:
            raise ContractViolation("M03 guards require explicit supported raw dimensional units")
        if not math.isfinite(self.zero_level):
            raise ContractViolation("M03 event zero level must be finite")
        if not self.certificate_capabilities:
            raise ContractViolation("every M03 event requires a no-event certificate capability")
        if len(set(self.certificate_capabilities)) != len(self.certificate_capabilities):
            raise ContractViolation("M03 event certificate capabilities must be unique")
        if len(set(self.dependency_predecessors)) != len(self.dependency_predecessors):
            raise ContractViolation("M03 event dependency predecessors must be unique")
        if self.kind in self.dependency_predecessors:
            raise ContractViolation("M03 event dependency cannot be a self-loop")
        if self.trigger_direction is EventTriggerDirection.TOUCH and (
            EventCertificateKind.STATIONARY_TOUCH_ENCLOSURE not in self.certificate_capabilities
        ):
            raise ContractViolation("M03 TOUCH guards require stationary enclosure evidence")
        if self.detection_mode is EventDetectionMode.SWEPT_COLLISION and (
            EventCertificateKind.SWEPT_NO_EVENT not in self.certificate_capabilities
        ):
            raise ContractViolation("M03 swept guards require swept no-event evidence")
        if self.event_priority is not None:
            raise ContractViolation("M03 event IDs/order cannot encode physical priority")

    def registration(
        self,
        *,
        entity_ids: tuple[str, ...] = (M03_DEFAULT_EVENT_ENTITY_ID,),
    ) -> EventChannelRegistration:
        """Materialize the corresponding public M02 registration."""

        if (
            not entity_ids
            or len(set(entity_ids)) != len(entity_ids)
            or any(not item for item in entity_ids)
        ):
            raise ContractViolation("M03 event entity IDs must be unique and nonempty")
        return EventChannelRegistration.create(
            channel_id=self.channel_id,
            owner_id=self.owner_id,
            entity_ids=entity_ids,
            event_kind=self.kind.value,
            guard_id=f"{self.channel_id}.raw_guard",
            guard_version=M03_SIGNED_EVENT_REGISTRY_VERSION,
            raw_guard_unit=self.raw_guard_unit,
            zero_level=self.zero_level,
            admissible_side=self.admissible_side,
            trigger_direction=self.trigger_direction,
            applicability_predicate_id=f"{self.channel_id}.applicability.v1",
            branch_state_scope=self.branch_state_scope,
            detection_mode=self.detection_mode,
            no_event_certificate_capabilities=self.certificate_capabilities,
            dependency_predecessors=tuple(
                _SPEC_BY_KIND[item].channel_id for item in self.dependency_predecessors
            ),
            transition_owner=self.owner_id,
            post_event_side_request_id=f"{self.channel_id}.post_side.v1",
            metadata_unit=self.raw_guard_unit,
        )


_CROSSING_CERTIFICATES = (
    EventCertificateKind.ADAPTIVE_PROBE_SPACING,
    EventCertificateKind.LIPSCHITZ_ENCLOSURE,
)
_TOUCH_CERTIFICATES = (EventCertificateKind.STATIONARY_TOUCH_ENCLOSURE,)
_SWEPT_CERTIFICATES = (
    EventCertificateKind.SWEPT_NO_EVENT,
    EventCertificateKind.ADAPTIVE_PROBE_SPACING,
)


def _event(
    kind: M03EventKind,
    family: M03EventFamily,
    unit: str,
    semantics: str,
    side: EventAdmissibleSide,
    direction: EventTriggerDirection,
    *,
    owner: str = M03_INTRINSIC_EVENT_OWNER,
    detection: EventDetectionMode = EventDetectionMode.SIGN_CHANGE,
    certificates: tuple[EventCertificateKind, ...] = _CROSSING_CERTIFICATES,
    scope: tuple[str, ...] = ("ALL_APPLICABLE_M03_BRANCHES",),
    predecessors: tuple[M03EventKind, ...] = (),
) -> M03SignedEventSpec:
    return M03SignedEventSpec(
        kind=kind,
        family=family,
        channel_id=f"m03.event.{kind.value.lower()}",
        owner_id=owner,
        raw_guard_semantics=semantics,
        raw_guard_unit=unit,
        zero_level=0.0,
        admissible_side=side,
        trigger_direction=direction,
        detection_mode=detection,
        certificate_capabilities=certificates,
        branch_state_scope=scope,
        dependency_predecessors=predecessors,
    )


M03_SIGNED_EVENT_SPECS: tuple[M03SignedEventSpec, ...] = (
    _event(
        M03EventKind.TIP_CONTACT_ESTABLISH,
        M03EventFamily.CONTACT_LOAD_RELEASE,
        "mm",
        "minimum legal finite-cap gap g_t; positive is open/nonpenetrating",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        scope=("OPEN", "REVERSIBLE_RETURN"),
    ),
    _event(
        M03EventKind.TIP_CONTACT_TANGENCY,
        M03EventFamily.CONTACT_LOAD_RELEASE,
        "mm",
        "stationary zero of the legal finite-cap gap g_t",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.TOUCH,
        detection=EventDetectionMode.SIGN_CHANGE_AND_TOUCH,
        certificates=_TOUCH_CERTIFICATES,
        scope=("OPEN", "REVERSIBLE_RETURN"),
    ),
    _event(
        M03EventKind.CONTACT_LOAD_ONSET,
        M03EventFamily.CONTACT_LOAD_RELEASE,
        "N",
        "maximum active-support normal multiplier minus activation resolution",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.RISING,
        scope=("TIP_ZERO_LOAD", "PRELOAD_BUILD", "REATTACHED_ENTRY"),
        predecessors=(M03EventKind.TIP_CONTACT_ESTABLISH,),
    ),
    _event(
        M03EventKind.CONTACT_RELEASE,
        M03EventFamily.CONTACT_LOAD_RELEASE,
        "N",
        "minimum remaining compressive normal multiplier minus activation resolution",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        scope=("ATTACHED_STICK", "ATTACHED_SLIDE"),
    ),
    _event(
        M03EventKind.FRICTION_CONE_REACHED,
        M03EventFamily.FRICTION_SLIP,
        "N",
        "minimum Coulomb margin mu*lambda_n-norm(lambda_t)",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        scope=("ATTACHED_STICK", "PRELOAD_BUILD", "REATTACHED_ENTRY"),
    ),
    _event(
        M03EventKind.ALL_STICK_BRANCH_LOSS,
        M03EventFamily.FRICTION_SLIP,
        "N",
        "one-sided all-stick redistribution feasibility margin",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        scope=("ATTACHED_STICK",),
        predecessors=(M03EventKind.FRICTION_CONE_REACHED,),
    ),
    _event(
        M03EventKind.SLIP_ONSET_CONFIRMED,
        M03EventFamily.FRICTION_SLIP,
        "mm",
        "objective slip-increment norm minus the declared slip resolution",
        EventAdmissibleSide.NONPOSITIVE,
        EventTriggerDirection.RISING,
        scope=("ATTACHED_STICK",),
        predecessors=(
            M03EventKind.FRICTION_CONE_REACHED,
            M03EventKind.ALL_STICK_BRANCH_LOSS,
        ),
    ),
    _event(
        M03EventKind.SUPPORT_CHART_SWITCH,
        M03EventFamily.SUPPORT_CHART_CAP,
        "mm",
        "active chart/feature legality margin",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        detection=EventDetectionMode.OWNER_ENCLOSURE,
    ),
    _event(
        M03EventKind.SUPPORT_SWITCH,
        M03EventFamily.SUPPORT_CHART_CAP,
        "mm",
        "signed co-minimal support-distance difference",
        EventAdmissibleSide.BOTH_WITH_GRAPH_RULE,
        EventTriggerDirection.EITHER,
        detection=EventDetectionMode.OWNER_ENCLOSURE,
        predecessors=(M03EventKind.SUPPORT_CHART_SWITCH,),
    ),
    _event(
        M03EventKind.MIGRATION_DEGENERACY,
        M03EventFamily.SUPPORT_CHART_CAP,
        "1",
        "scaled minimum singular-value margin of the migration graph",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        detection=EventDetectionMode.OWNER_ENCLOSURE,
    ),
    _event(
        M03EventKind.CAP_LEGALITY_LOSS,
        M03EventFamily.SUPPORT_CHART_CAP,
        "mm",
        "finite spherical-cap axial legality margin",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        detection=EventDetectionMode.OWNER_ENCLOSURE,
    ),
    _event(
        M03EventKind.SPRING_ORIGINAL_LENGTH,
        M03EventFamily.SPRING,
        "mm",
        "spring compression delta_s (the original-length graph boundary)",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.EITHER,
        scope=("AT_ORIGINAL_LENGTH", "COMPRESSING"),
    ),
    _event(
        M03EventKind.SPRING_HARD_STOP,
        M03EventFamily.SPRING,
        "mm",
        "remaining spring travel 4 mm-delta_s",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        scope=("COMPRESSING", "HARD_STOP"),
    ),
    *(
        _event(
            kind,
            M03EventFamily.BODY_COLLISION,
            "mm",
            semantics,
            EventAdmissibleSide.NONNEGATIVE,
            EventTriggerDirection.FALLING,
            detection=EventDetectionMode.SWEPT_COLLISION,
            certificates=_SWEPT_CERTIFICATES,
        )
        for kind, semantics in (
            (M03EventKind.CONE_COLLISION, "minimum cone-to-surface clearance"),
            (M03EventKind.SHAFT_COLLISION, "minimum shaft/envelope-to-surface clearance"),
            (M03EventKind.MOUNT_COLLISION, "minimum mount-envelope-to-surface clearance"),
        )
    ),
    _event(
        M03EventKind.OUT_OF_DOMAIN,
        M03EventFamily.DOMAIN_QUALITY,
        "mm",
        "signed M01 domain-coverage margin",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        detection=EventDetectionMode.OWNER_ENCLOSURE,
    ),
    _event(
        M03EventKind.GEOMETRY_UNCERTAIN,
        M03EventFamily.DOMAIN_QUALITY,
        "1",
        "dimensionless M01 geometry-quality margin after required refinement",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        detection=EventDetectionMode.OWNER_ENCLOSURE,
    ),
    _event(
        M03EventKind.STRUCTURAL_MODEL_LIMIT,
        M03EventFamily.DOMAIN_QUALITY,
        "1",
        "Euler-Bernoulli model-validity margin",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        detection=EventDetectionMode.OWNER_ENCLOSURE,
    ),
    _event(
        M03EventKind.PRELOAD_TARGET_REACHED,
        M03EventFamily.PRELOAD,
        "1",
        "preload homotopy coordinate eta minus one",
        EventAdmissibleSide.NONPOSITIVE,
        EventTriggerDirection.RISING,
        owner=M03_STANDALONE_EVENT_OWNER,
        scope=("PRELOAD_BUILD",),
        predecessors=(M03EventKind.CONTACT_LOAD_ONSET,),
    ),
    _event(
        M03EventKind.PRELOAD_INFEASIBLE,
        M03EventFamily.PRELOAD,
        "1",
        "owner-proven preload branch-feasibility margin",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        owner=M03_STANDALONE_EVENT_OWNER,
        detection=EventDetectionMode.OWNER_ENCLOSURE,
        scope=("PRELOAD_BUILD",),
    ),
    _event(
        M03EventKind.RELEASE_PATH_START,
        M03EventFamily.RETURN_OPERATION,
        "mm",
        "release-operation path coordinate from the committed release pose",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.RISING,
        owner=M03_STANDALONE_EVENT_OWNER,
        scope=("RELEASE_TRANSITION",),
        predecessors=(M03EventKind.CONTACT_RELEASE,),
    ),
    _event(
        M03EventKind.RETURN_SEGMENT_START,
        M03EventFamily.RETURN_OPERATION,
        "mm",
        "current explicit return-segment coordinate from its declared start",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.RISING,
        owner=M03_STANDALONE_EVENT_OWNER,
        scope=("REVERSIBLE_RETURN",),
        predecessors=(M03EventKind.RELEASE_PATH_START,),
    ),
    _event(
        M03EventKind.LIFT_OFF_CLEARANCE_REACHED,
        M03EventFamily.RETURN_OPERATION,
        "mm",
        "certified full-body clearance minus resolved g_start",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.RISING,
        owner=M03_STANDALONE_EVENT_OWNER,
        scope=("LIFT_OFF",),
        predecessors=(M03EventKind.RETURN_SEGMENT_START,),
    ),
    _event(
        M03EventKind.RETURN_ENERGY_RESOLVED,
        M03EventFamily.RETURN_OPERATION,
        "N*mm",
        "resolved work/energy resolution minus remaining recoverable energy",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.RISING,
        owner=M03_STANDALONE_EVENT_OWNER,
        scope=("LIFT_OFF", "REVERSIBLE_RETURN"),
        predecessors=(M03EventKind.RETURN_SEGMENT_START,),
    ),
    _event(
        M03EventKind.RETURN_SEGMENT_END,
        M03EventFamily.RETURN_OPERATION,
        "mm",
        "remaining declared distance in the current explicit return segment",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        owner=M03_STANDALONE_EVENT_OWNER,
        scope=("REVERSIBLE_RETURN", "LIFT_OFF", "RESEARCH"),
        predecessors=(M03EventKind.RETURN_SEGMENT_START,),
    ),
    _event(
        M03EventKind.RELEASE_PATH_END,
        M03EventFamily.RETURN_OPERATION,
        "mm",
        "remaining distance in LIFT_OFF_RESEARCH_V1",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        owner=M03_STANDALONE_EVENT_OWNER,
        scope=("RELOAD", "REVERSIBLE_RETURN"),
        predecessors=(M03EventKind.RETURN_SEGMENT_END,),
    ),
    _event(
        M03EventKind.SWEPT_COLLISION,
        M03EventFamily.SWEPT_COLLISION,
        "mm",
        "minimum full-body clearance on the declared operation sweep",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        owner=M03_STANDALONE_EVENT_OWNER,
        detection=EventDetectionMode.SWEPT_COLLISION,
        certificates=_SWEPT_CERTIFICATES,
        scope=("REVERSIBLE_RETURN", "LIFT_OFF", "RESEARCH"),
    ),
    _event(
        M03EventKind.RECONTACT_ZERO_LOAD,
        M03EventFamily.RECONTACT,
        "mm",
        "earliest legal finite-cap gap on the explicit research corridor",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        owner=M03_STANDALONE_EVENT_OWNER,
        detection=EventDetectionMode.SWEPT_COLLISION,
        certificates=_SWEPT_CERTIFICATES,
        scope=("RESEARCH", "REVERSIBLE_RETURN"),
        predecessors=(M03EventKind.RELEASE_PATH_START,),
    ),
    _event(
        M03EventKind.RELOAD_TARGET_REACHED,
        M03EventFamily.REENGAGEMENT,
        "1",
        "reload homotopy coordinate eta_reload minus one",
        EventAdmissibleSide.NONPOSITIVE,
        EventTriggerDirection.RISING,
        owner=M03_STANDALONE_EVENT_OWNER,
        scope=("RELOAD",),
        predecessors=(M03EventKind.RECONTACT_ZERO_LOAD,),
    ),
    _event(
        M03EventKind.REENGAGEMENT,
        M03EventFamily.REENGAGEMENT,
        "N",
        "new-cycle normal load minus the scale-aware activation resolution",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.RISING,
        owner=M03_STANDALONE_EVENT_OWNER,
        scope=("RELOAD", "REATTACHED_ENTRY"),
        predecessors=(
            M03EventKind.RECONTACT_ZERO_LOAD,
            M03EventKind.RELOAD_TARGET_REACHED,
        ),
    ),
    _event(
        M03EventKind.TRAVEL_COMPLETE,
        M03EventFamily.TRAVEL,
        "mm",
        "remaining standalone drag travel 100 mm-x_total",
        EventAdmissibleSide.NONNEGATIVE,
        EventTriggerDirection.FALLING,
        owner=M03_STANDALONE_EVENT_OWNER,
        scope=("DRAG",),
    ),
)

_SPEC_BY_KIND = {item.kind: item for item in M03_SIGNED_EVENT_SPECS}
_SPEC_BY_EVENT_NAME = {item.kind.value: item for item in M03_SIGNED_EVENT_SPECS}
_SPEC_BY_CHANNEL = {item.channel_id: item for item in M03_SIGNED_EVENT_SPECS}

if len(_SPEC_BY_KIND) != len(M03_SIGNED_EVENT_SPECS):
    raise ContractViolation("M03 signed event kinds must be unique")
if len(_SPEC_BY_CHANNEL) != len(M03_SIGNED_EVENT_SPECS):
    raise ContractViolation("M03 signed event channels must be unique")

M03_SIGNED_EVENT_REGISTRY_HASH = semantic_hash(M03_SIGNED_EVENT_SPECS)


def m03_event_spec(kind: M03EventKind | str) -> M03SignedEventSpec:
    """Return one frozen event specification by kind value or channel ID."""

    if isinstance(kind, M03EventKind):
        return _SPEC_BY_KIND[kind]
    spec = _SPEC_BY_EVENT_NAME.get(kind) or _SPEC_BY_CHANNEL.get(kind)
    if spec is None:
        raise ContractViolation("unknown M03 event kind", details={"event_kind": kind})
    return spec


def _dependency_closure(kinds: Iterable[M03EventKind]) -> frozenset[M03EventKind]:
    selected = set(kinds)
    unknown = selected - set(_SPEC_BY_KIND)
    if unknown:
        raise ContractViolation(
            "unknown M03 event kind in registry selection",
            details={"event_kinds": sorted(item.value for item in unknown)},
        )
    changed = True
    while changed:
        changed = False
        for kind in tuple(selected):
            for predecessor in _SPEC_BY_KIND[kind].dependency_predecessors:
                if predecessor not in selected:
                    selected.add(predecessor)
                    changed = True
    return frozenset(selected)


def m03_event_registrations(
    kinds: Iterable[M03EventKind] | None = None,
    *,
    entity_ids: tuple[str, ...] = (M03_DEFAULT_EVENT_ENTITY_ID,),
) -> tuple[EventChannelRegistration, ...]:
    """Build deterministic M02 registrations, including dependency closure."""

    selected = frozenset(_SPEC_BY_KIND) if kinds is None else _dependency_closure(tuple(kinds))
    registrations = tuple(
        spec.registration(entity_ids=entity_ids)
        for spec in M03_SIGNED_EVENT_SPECS
        if spec.kind in selected
    )
    EventRegistry(registrations)
    return registrations


def m03_event_registry(
    kinds: Iterable[M03EventKind] | None = None,
    *,
    entity_ids: tuple[str, ...] = (M03_DEFAULT_EVENT_ENTITY_ID,),
) -> EventRegistry:
    """Return the validated public M02 registry for M03 physical events."""

    return EventRegistry(m03_event_registrations(kinds, entity_ids=entity_ids))


def make_m03_coverage_declaration(
    *,
    event_kind: M03EventKind,
    certificate_id: str,
    certificate_kind: EventCertificateKind,
    certificate_hash: str,
    complete: bool,
    certifies_no_event: bool,
    maximum_probe_spacing_mm: float | None,
    raw_guard_zero_tolerance: float,
    candidate_enclosures: tuple[OwnerEventEnclosure, ...] = (),
    requires_balance_recompute: bool = False,
) -> EventCoverageDeclaration:
    """Create M02 coverage evidence only when M03 declared that capability."""

    spec = m03_event_spec(event_kind)
    if certificate_kind not in spec.certificate_capabilities:
        raise ContractViolation(
            "coverage certificate kind is not declared by the M03 event",
            details={
                "event_kind": event_kind.value,
                "certificate_kind": certificate_kind.value,
            },
        )
    return EventCoverageDeclaration(
        certificate_id=certificate_id,
        channel_id=spec.channel_id,
        kind=certificate_kind,
        certificate_hash=certificate_hash,
        complete=complete,
        certifies_no_event=certifies_no_event,
        maximum_probe_spacing_mm=maximum_probe_spacing_mm,
        raw_guard_zero_tolerance=raw_guard_zero_tolerance,
        candidate_enclosures=candidate_enclosures,
        requires_balance_recompute=requires_balance_recompute,
    )


@dataclass(frozen=True, slots=True)
class M03RawSignedGuard:
    """Validated raw guard sample before any numerical normalization."""

    event_id: str
    event_kind: M03EventKind
    channel_id: str
    raw_value: float
    raw_unit: str
    zero_level: float
    admissible_side: EventAdmissibleSide
    trigger_direction: EventTriggerDirection
    detection_mode: EventDetectionMode
    coverage_certificate_id: str

    @classmethod
    def from_candidate(cls, candidate: EventCandidateResponse) -> M03RawSignedGuard:
        spec = m03_event_spec(candidate.event_kind)
        if not candidate.event_id:
            raise ContractViolation("M03 event candidate requires an event ID")
        if candidate.owner != "M03":
            raise ContractViolation("M03 event candidate has a foreign semantic owner")
        if not math.isfinite(candidate.raw_guard) or not math.isfinite(candidate.zero_value):
            raise ContractViolation("M03 raw event guards cannot contain NaN/Inf")
        if candidate.raw_guard_unit != spec.raw_guard_unit:
            raise ContractViolation(
                "M03 raw dimensional event guard unit changed",
                details={
                    "event_kind": spec.kind.value,
                    "expected": spec.raw_guard_unit,
                    "actual": candidate.raw_guard_unit,
                },
            )
        if candidate.zero_value != spec.zero_level:
            raise ContractViolation("M03 event candidate changed its frozen raw zero level")
        if candidate.admissible_side != spec.admissible_side.value:
            raise ContractViolation("M03 event candidate changed its admissible side")
        if candidate.direction != spec.trigger_direction.value:
            raise ContractViolation("M03 event candidate changed its trigger direction")
        if candidate.event_fraction is not None and not (
            math.isfinite(candidate.event_fraction) and 0.0 <= candidate.event_fraction <= 1.0
        ):
            raise ContractViolation("M03 event fraction must lie in [0,1]")
        if candidate.bracket is not None:
            left, right = candidate.bracket
            if not all(math.isfinite(item) and 0.0 <= item <= 1.0 for item in (left, right)):
                raise ContractViolation("M03 event-fraction bracket must lie in [0,1]")
            if right < left:
                raise ContractViolation("M03 event-fraction bracket endpoints are reversed")
            if (
                candidate.event_fraction is not None
                and not left <= candidate.event_fraction <= right
            ):
                raise ContractViolation("M03 event fraction lies outside its bracket")
        if not candidate.coverage_certificate_id:
            raise ContractViolation("M03 event guard requires interval coverage evidence")
        return cls(
            event_id=candidate.event_id,
            event_kind=spec.kind,
            channel_id=spec.channel_id,
            raw_value=candidate.raw_guard,
            raw_unit=candidate.raw_guard_unit,
            zero_level=candidate.zero_value,
            admissible_side=spec.admissible_side,
            trigger_direction=spec.trigger_direction,
            detection_mode=spec.detection_mode,
            coverage_certificate_id=candidate.coverage_certificate_id,
        )

    @property
    def raw_signed_offset(self) -> float:
        """Return the unscaled physical guard minus its declared zero level."""

        return self.raw_value - self.zero_level

    @property
    def on_admissible_side(self) -> bool:
        offset = self.raw_signed_offset
        if self.admissible_side is EventAdmissibleSide.NONNEGATIVE:
            return offset >= 0.0
        if self.admissible_side is EventAdmissibleSide.NONPOSITIVE:
            return offset <= 0.0
        return True


def raw_signed_guards_from_response(
    response: SingleSpineTrialResponse,
) -> tuple[M03RawSignedGuard, ...]:
    """Validate every M03 response guard without replacing it by a scaled value."""

    guards = tuple(
        M03RawSignedGuard.from_candidate(item)
        for item in response.state_events.all_event_candidates
    )
    channel_ids = tuple(item.channel_id for item in guards)
    if len(channel_ids) != len(set(channel_ids)):
        raise ContractViolation("M03 response returned duplicate guard channels")
    return guards


def _infer_residual_kind(report: ResidualBlockReport) -> ResidualKind:
    token = f"{report.block_id} {report.semantics}".lower()
    if "moment" in token:
        return ResidualKind.MOMENT_EQUILIBRIUM
    if "force" in token or "interface equilibrium" in token:
        return ResidualKind.FORCE_EQUILIBRIUM
    if "kinematic" in token or (
        report.raw_unit in {"mm", "rad"}
        and any(item in token for item in ("geometric", "closure", "beam"))
    ):
        return ResidualKind.KINEMATIC_COMPATIBILITY
    if "load" in token or "preload" in token:
        return ResidualKind.LOAD_CONTROL
    if any(item in token for item in ("complementarity", "signorini", "ncp", "soc")):
        return ResidualKind.COMPLEMENTARITY_KKT
    if "graph" in token or "coulomb" in token or "friction" in token:
        return ResidualKind.GRAPH_DISTANCE
    if "branch" in token:
        return ResidualKind.ACTIVE_BRANCH
    if "energy" in token or "work" in token:
        return ResidualKind.ENERGY_WORK
    return ResidualKind.OWNER_DEFINED_HARD_QUALITY


def _residual_scale_value(report: ResidualBlockReport) -> float:
    if report.raw_norm == 0.0:
        if report.normalized_norm != 0.0:
            raise ContractViolation("zero raw residual cannot have a nonzero normalized norm")
        return max(report.reference_norm, report.absolute_tolerance, 1.0)
    if report.normalized_norm <= 0.0:
        raise ContractViolation("positive raw residual requires a positive normalized norm")
    value = report.raw_norm / report.normalized_norm
    if not math.isfinite(value) or value <= 0.0:
        raise ContractViolation("M03 residual report does not define a positive M02 scale")
    return value


def bridge_residual_blocks_to_m02(
    response: SingleSpineTrialResponse,
    *,
    entity_refs: tuple[str, ...] = (M03_DEFAULT_EVENT_ENTITY_ID,),
) -> tuple[ResidualBlock, ...]:
    """Convert M03 residual reports to M02 blocks without mixing native units."""

    output: list[ResidualBlock] = []
    for report in response.diagnostics.residual_blocks:
        threshold = report.absolute_tolerance + report.relative_tolerance * report.reference_norm
        if report.passed != (report.raw_norm <= threshold):
            raise ContractViolation("M03 residual pass flag conflicts with its native tolerance")
        scale_value = _residual_scale_value(report)
        block = ResidualBlock.from_values(
            block_id=report.block_id,
            owner_id=M03_INTRINSIC_EVENT_OWNER,
            kind=_infer_residual_kind(report),
            physical_semantics=report.semantics,
            raw_values=(report.raw_norm,),
            raw_unit=report.raw_unit,
            reduction_norm=ReductionNorm.L2,
            reference_norm=report.reference_norm,
            absolute_tolerance=report.absolute_tolerance,
            relative_tolerance=report.relative_tolerance,
            scale_id=report.scale_id,
            scale_value=scale_value,
            hard_acceptance=report.hard,
            branch_ref=response.linearization.branch_id,
            entity_refs=entity_refs,
        )
        if not math.isclose(
            block.normalized_norm,
            report.normalized_norm,
            rel_tol=1.0e-12,
            abs_tol=1.0e-15,
        ):
            raise ContractViolation("M03-to-M02 residual normalization is not lossless")
        output.append(block)
    if len({item.block_id for item in output}) != len(output):
        raise ContractViolation("M03 response returned duplicate residual block IDs")
    return tuple(output)


@dataclass(frozen=True, slots=True)
class M03EventProbeContext:
    """Path identity and balance evidence not duplicated in an M03 response."""

    trial_id: str
    oriented_path_position_mm: float
    trial_fraction: float
    coverage_refs: tuple[str, ...] = ()
    quality_hashes: tuple[str, ...] = ()
    balance_response_hash: str | None = None
    balance_recomputed: bool = False

    def __post_init__(self) -> None:
        if not self.trial_id:
            raise ContractViolation("M03 event probe context requires a trial ID")
        if not math.isfinite(self.oriented_path_position_mm):
            raise ContractViolation("M03 event probe position must be finite")
        if not math.isfinite(self.trial_fraction) or not 0.0 <= self.trial_fraction <= 1.0:
            raise ContractViolation("M03 event probe fraction must lie in [0,1]")
        if len(set(self.coverage_refs)) != len(self.coverage_refs):
            raise ContractViolation("M03 event probe coverage references must be unique")
        if any(len(item) != 64 for item in self.quality_hashes):
            raise ContractViolation("M03 event probe quality hashes must be SHA-256 digests")
        if self.balance_recomputed != (self.balance_response_hash is not None):
            raise ContractViolation("balance recompute flag/hash must be present together")
        if self.balance_response_hash is not None and len(self.balance_response_hash) != 64:
            raise ContractViolation("balance response hash must be a SHA-256 digest")


_EVENT_PROBE_RESPONSE_CLASSES = {
    EmbeddedErrorClass.OK,
    EmbeddedErrorClass.OPEN_RESPONSE,
    EmbeddedErrorClass.EVENT_REDUCTION_REQUIRED,
    EmbeddedErrorClass.EQUILIBRIUM_DEGENERATE,
}


def _assert_event_probe_quality(response: SingleSpineTrialResponse) -> None:
    if len(response.response_hash) != 64:
        raise ContractViolation("M03 event probes require a full response hash")
    if response.diagnostics.failure_axis is not FailureAxis.NONE:
        raise ContractViolation("failed M03 trial cannot enter an M02 event bracket")
    if response.diagnostics.error_class not in _EVENT_PROBE_RESPONSE_CLASSES:
        raise ContractViolation("unconverged/unavailable M03 response is not a legal guard sample")
    if not response.diagnostics.residual_blocks:
        raise ContractViolation("M03 event probes require explicit residual block evidence")
    failed = tuple(
        item.block_id
        for item in response.diagnostics.residual_blocks
        if item.hard and not item.passed
    )
    if failed:
        raise ContractViolation(
            "M03 event guard response failed hard residual quality",
            details={"residual_blocks": failed},
        )


def bridge_guard_samples_to_m02(
    response: SingleSpineTrialResponse,
    context: M03EventProbeContext,
) -> tuple[GuardSample, ...]:
    """Bridge all certified M03 raw guards into public M02 guard samples."""

    _assert_event_probe_quality(response)
    guards = raw_signed_guards_from_response(response)
    quality_hashes = context.quality_hashes or (semantic_hash(response.diagnostics),)
    output: list[GuardSample] = []
    for guard in guards:
        coverage_refs = tuple(
            dict.fromkeys(
                (
                    guard.coverage_certificate_id,
                    *response.geometry_contact.query_receipt_ids,
                    *context.coverage_refs,
                )
            )
        )
        payload = {
            "registry_hash": M03_SIGNED_EVENT_REGISTRY_HASH,
            "event_id": guard.event_id,
            "channel_id": guard.channel_id,
            "trial_id": context.trial_id,
            "position_mm": context.oriented_path_position_mm,
            "trial_fraction": context.trial_fraction,
            "raw_value": guard.raw_value,
            "raw_unit": guard.raw_unit,
            "response_hash": response.response_hash,
        }
        output.append(
            GuardSample.create(
                sample_id=stable_content_id("m03_m02_guard_sample", payload),
                channel_id=guard.channel_id,
                trial_id=context.trial_id,
                oriented_path_position_mm=context.oriented_path_position_mm,
                trial_fraction=context.trial_fraction,
                raw_guard_value=guard.raw_value,
                raw_guard_unit=guard.raw_unit,
                equilibrium_quality_passed=True,
                quality_hashes=quality_hashes,
                owner_response_hash=response.response_hash,
                balance_response_hash=context.balance_response_hash,
                balance_recomputed=context.balance_recomputed,
                coverage_refs=coverage_refs,
                metadata_unit=guard.raw_unit,
            )
        )
    return tuple(output)


def bridge_response_to_m02_event_snapshot(
    response: SingleSpineTrialResponse,
    context: M03EventProbeContext,
) -> EquilibriumGuardSnapshot:
    """Create the fresh equilibrium snapshot consumed by ``M02.EventEngine``."""

    samples = bridge_guard_samples_to_m02(response, context)
    if not samples:
        raise ContractViolation("M02 event probes require every applicable M03 guard sample")
    quality_hashes = context.quality_hashes or (semantic_hash(response.diagnostics),)
    coverage_refs = tuple(
        dict.fromkeys(item for sample in samples for item in sample.coverage_refs)
    )
    return EquilibriumGuardSnapshot(
        oriented_path_position_mm=context.oriented_path_position_mm,
        raw_guard_values={item.channel_id: item.raw_guard_value for item in samples},
        raw_guard_units={item.channel_id: item.raw_guard_unit for item in samples},
        equilibrium_quality_passed=True,
        equilibrium_response_hash=response.response_hash,
        quality_hashes=quality_hashes,
        balance_response_hash=context.balance_response_hash,
        balance_recomputed=context.balance_recomputed,
        coverage_refs=coverage_refs,
    )


def _component_hash(
    response: SingleSpineTrialResponse,
    component: str,
    payload: object,
) -> str:
    return semantic_hash(
        {
            "component": component,
            "request_hash": response.transaction.request_hash,
            "opaque_trial_state_handle": response.transaction.opaque_trial_state_handle,
            "payload": payload,
        }
    )


def m03_event_side_evaluation(
    response: SingleSpineTrialResponse,
    *,
    side: str,
    parent_accepted_state_id: str,
    event_coordinate_mm: float,
) -> EventSideEvaluation:
    """Hash complete event-side assembly evidence into the public M02 type."""

    if side not in {"PRE_EVENT", "POST_EVENT"}:
        raise ContractViolation("M03 event side must be PRE_EVENT or POST_EVENT")
    _assert_event_probe_quality(response)
    if response.diagnostics.error_class is EmbeddedErrorClass.EVENT_REDUCTION_REQUIRED:
        raise ContractViolation(
            "EVENT_REDUCTION_REQUIRED is a bracket/retry response, not complete event/post evidence"
        )
    components: dict[str, object] = {
        "unknowns": (
            response.geometry_contact.tip_center_global_mm,
            response.structure.beam_tip_translation_global_mm,
            response.structure.beam_tip_rotation_global_rad,
            response.structure.spring_compression_mm,
        ),
        "residuals": (
            response.diagnostics.residual_blocks,
            response.diagnostics.complementarity_residual,
            response.diagnostics.contact_soc_residual,
            response.diagnostics.graph_residual,
            response.diagnostics.geometric_closure_residual_mm,
            response.diagnostics.beam_residual_mm,
            response.diagnostics.spring_residual_n,
            response.diagnostics.work_balance_error_n_mm,
        ),
        "graph": (
            response.geometry_contact.active_support_ids,
            response.geometry_contact.supports,
            response.state_events.per_contact_motion_states,
            response.wrench.wrench_uniqueness,
            response.wrench.rank,
            response.wrench.nullspace_basis,
            response.wrench.admissible_wrench_graph_handle,
        ),
        "guards": (
            response.state_events.all_event_candidates,
            response.state_events.simultaneous_event_set,
            response.state_events.earliest_event_fraction,
            response.state_events.event_fraction_bracket,
        ),
        "wrench": response.wrench,
        "energy": (response.structure, response.material_damage, response.work),
        "quality": response.diagnostics,
        "intents": (
            response.transaction.provisional_commit_intent,
            response.transaction.damage_intents,
            response.transaction.damage_write_set,
            response.material_damage.trial_damage_intents,
        ),
    }
    return EventSideEvaluation(
        side=side,
        response_hash=response.response_hash,
        component_hashes=tuple(
            (name, _component_hash(response, name, payload)) for name, payload in components.items()
        ),
        parent_accepted_state_id=parent_accepted_state_id,
        event_coordinate_mm=event_coordinate_mm,
    )


@dataclass(frozen=True, slots=True)
class M03EventPostReassemblyEvidence:
    """Proof that event/pre and event/post used distinct complete M03 responses."""

    result: EventPostResult
    pre_response_id: str
    pre_response_hash: str
    post_response_id: str
    post_response_hash: str
    accepted_history_version_read: int
    damage_snapshot_version_read: int

    def __post_init__(self) -> None:
        if not self.result.complete_recompute:
            raise ContractViolation("M03 event/post evidence must report complete recompute")
        if self.result.pre_callback_count != 1 or self.result.post_callback_count != 1:
            raise ContractViolation("M03 event/post must invoke each full solve exactly once")
        if self.pre_response_id == self.post_response_id:
            raise ContractViolation("M03 event/post cannot reuse a response identity")
        if self.pre_response_hash == self.post_response_hash:
            raise ContractViolation("M03 event/post cannot reuse old response content")


def evaluate_m03_event_post_reassembly(
    *,
    event_coordinate_mm: float,
    simultaneous_channel_ids: tuple[str, ...],
    parent_accepted_state_id: str,
    pre_solver: Callable[[float, tuple[str, ...]], SingleSpineTrialResponse],
    transition: Callable[[tuple[str, ...]], tuple[str, ...]],
    post_solver: Callable[[float, tuple[str, ...], tuple[str, ...]], SingleSpineTrialResponse],
) -> M03EventPostReassemblyEvidence:
    """Use M02 event/post orchestration while enforcing fresh M03 reassembly."""

    if not parent_accepted_state_id:
        raise ContractViolation("M03 event/post requires an immutable accepted parent")
    if not simultaneous_channel_ids or len(set(simultaneous_channel_ids)) != len(
        simultaneous_channel_ids
    ):
        raise ContractViolation("M03 event/post channels must be unique and nonempty")
    unknown = set(simultaneous_channel_ids) - set(_SPEC_BY_CHANNEL)
    if unknown:
        raise ContractViolation(
            "M03 event/post requested unknown channels",
            details={"channel_ids": sorted(unknown)},
        )

    responses: dict[str, SingleSpineTrialResponse] = {}

    def pre_callback(
        coordinate_mm: float,
        channel_ids: tuple[str, ...],
    ) -> EventSideEvaluation:
        response = pre_solver(coordinate_mm, channel_ids)
        pre_channels = {
            m03_event_spec(item.event_kind).channel_id
            for item in response.state_events.all_event_candidates
        }
        # Intrinsic channels must be present in the A response.  Standalone
        # operation channels are evaluated by the outer owner and therefore
        # are deliberately absent from the frozen A-to-B response schema; the
        # complete mechanics/quality assembly is still hashed on both sides.
        response_owned_channels = {
            channel_id
            for channel_id in channel_ids
            if _SPEC_BY_CHANNEL[channel_id].owner_id == M03_INTRINSIC_EVENT_OWNER
        }
        missing_channels = response_owned_channels - pre_channels
        if missing_channels:
            raise ContractViolation(
                "M03 pre-event response omitted a simultaneous raw guard",
                details={"channel_ids": sorted(missing_channels)},
            )
        responses["pre"] = response
        return m03_event_side_evaluation(
            response,
            side="PRE_EVENT",
            parent_accepted_state_id=parent_accepted_state_id,
            event_coordinate_mm=coordinate_mm,
        )

    def transition_callback(channel_ids: tuple[str, ...]) -> tuple[str, ...]:
        intents = transition(channel_ids)
        if not intents or len(set(intents)) != len(intents) or any(not item for item in intents):
            raise ContractViolation("M03 simultaneous transitions require unique owner intents")
        return intents

    def post_callback(
        coordinate_mm: float,
        channel_ids: tuple[str, ...],
        intent_ids: tuple[str, ...],
    ) -> EventSideEvaluation:
        response = post_solver(coordinate_mm, channel_ids, intent_ids)
        pre_response = responses.get("pre")
        if pre_response is None:
            raise ContractViolation("M03 post solve ran before the pre-event solve")
        if response is pre_response:
            raise ContractViolation("M03 post-event callback reused the pre-event response")
        if response.response_id == pre_response.response_id:
            raise ContractViolation("M03 post-event callback reused the pre-event response ID")
        if response.response_hash == pre_response.response_hash:
            raise ContractViolation("M03 post-event callback reused the pre-event response hash")
        if (
            response.transaction.accepted_history_version_read
            != pre_response.transaction.accepted_history_version_read
            or response.transaction.damage_snapshot_version_read
            != pre_response.transaction.damage_snapshot_version_read
        ):
            raise ContractViolation(
                "M03 event/pre and event/post did not use the same parent versions"
            )
        if not response.state_events.event_one_sided_consistency:
            raise ContractViolation("M03 post-event response failed its one-sided consistency gate")
        responses["post"] = response
        return m03_event_side_evaluation(
            response,
            side="POST_EVENT",
            parent_accepted_state_id=parent_accepted_state_id,
            event_coordinate_mm=coordinate_mm,
        )

    result = evaluate_event_post_sides(
        event_coordinate_mm=event_coordinate_mm,
        simultaneous_channel_ids=simultaneous_channel_ids,
        pre_solver=pre_callback,
        transition=transition_callback,
        post_solver=post_callback,
    )
    pre_response = responses["pre"]
    post_response = responses["post"]
    return M03EventPostReassemblyEvidence(
        result=result,
        pre_response_id=pre_response.response_id,
        pre_response_hash=pre_response.response_hash,
        post_response_id=post_response.response_id,
        post_response_hash=post_response.response_hash,
        accepted_history_version_read=pre_response.transaction.accepted_history_version_read,
        damage_snapshot_version_read=pre_response.transaction.damage_snapshot_version_read,
    )


# Descriptive aliases keep the bridge easy to discover without creating a
# second implementation or competing contract.
bridge_m03_residual_blocks = bridge_residual_blocks_to_m02
bridge_m03_guard_samples = bridge_guard_samples_to_m02
evaluate_event_post_reassembly = evaluate_m03_event_post_reassembly


__all__ = [
    "M03_DEFAULT_EVENT_ENTITY_ID",
    "M03_INTRINSIC_EVENT_OWNER",
    "M03_SIGNED_EVENT_REGISTRY_HASH",
    "M03_SIGNED_EVENT_REGISTRY_VERSION",
    "M03_SIGNED_EVENT_SPECS",
    "M03_STANDALONE_EVENT_OWNER",
    "M03EventFamily",
    "M03EventKind",
    "M03EventPostReassemblyEvidence",
    "M03EventProbeContext",
    "M03RawSignedGuard",
    "M03SignedEventSpec",
    "bridge_guard_samples_to_m02",
    "bridge_m03_guard_samples",
    "bridge_m03_residual_blocks",
    "bridge_residual_blocks_to_m02",
    "bridge_response_to_m02_event_snapshot",
    "evaluate_event_post_reassembly",
    "evaluate_m03_event_post_reassembly",
    "m03_event_registrations",
    "m03_event_registry",
    "m03_event_side_evaluation",
    "m03_event_spec",
    "make_m03_coverage_declaration",
    "raw_signed_guards_from_response",
]
