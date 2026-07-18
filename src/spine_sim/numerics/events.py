"""Unified signed-event coverage, localization, ordering, and cascade engine."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from itertools import pairwise
from typing import Protocol

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation

from .config import DEFAULT_NUMERICS_CONFIG, NumericsConfig
from .contracts import (
    CascadeRound,
    EventBracket,
    EventCertificateKind,
    EventChannelRegistration,
    EventDependencyEdge,
    EventEarliestnessCertificate,
    EventRootMethod,
    EventTriggerDirection,
    LocatedEventGroup,
    M02ReasonCode,
    ReturnPathCapability,
    ReturnPathMode,
    SimultaneousEventGroup,
)


@dataclass(frozen=True, slots=True)
class OwnerEventEnclosure:
    """Versioned owner candidate enclosure, required for stationary/touch roots."""

    enclosure_id: str
    left_position_mm: float
    right_position_mm: float
    touch_candidate: bool
    owner_proof_hash: str

    def __post_init__(self) -> None:
        if not self.enclosure_id or len(self.owner_proof_hash) != 64:
            raise ContractViolation("event enclosure requires an ID and full proof hash")
        if not all(math.isfinite(value) for value in self.interval):
            raise ContractViolation("event enclosure endpoints must be finite")
        if self.right_position_mm < self.left_position_mm:
            raise ContractViolation("event enclosure endpoints are reversed")

    @property
    def interval(self) -> tuple[float, float]:
        return self.left_position_mm, self.right_position_mm


@dataclass(frozen=True, slots=True)
class EventCoverageDeclaration:
    """Owner's explicit interval coverage capability and evidence."""

    certificate_id: str
    channel_id: str
    kind: EventCertificateKind
    certificate_hash: str
    complete: bool
    certifies_no_event: bool
    maximum_probe_spacing_mm: float | None
    raw_guard_zero_tolerance: float
    candidate_enclosures: tuple[OwnerEventEnclosure, ...] = ()
    requires_balance_recompute: bool = False

    def __post_init__(self) -> None:
        if not self.certificate_id or not self.channel_id:
            raise ContractViolation("coverage declaration requires certificate/channel IDs")
        if len(self.certificate_hash) != 64:
            raise ContractViolation("coverage certificate hash must be a full SHA-256 digest")
        if not math.isfinite(self.raw_guard_zero_tolerance) or self.raw_guard_zero_tolerance < 0.0:
            raise ContractViolation("raw guard zero tolerance must be finite and nonnegative")
        if self.maximum_probe_spacing_mm is not None and (
            not math.isfinite(self.maximum_probe_spacing_mm) or self.maximum_probe_spacing_mm <= 0.0
        ):
            raise ContractViolation("maximum event probe spacing must be finite and positive")
        if self.kind is EventCertificateKind.ADAPTIVE_PROBE_SPACING and (
            self.maximum_probe_spacing_mm is None
        ):
            raise ContractViolation("adaptive probe-spacing certificate requires a maximum spacing")
        if self.certifies_no_event and self.candidate_enclosures:
            raise ContractViolation("no-event certificate cannot also declare root candidates")
        if not self.complete and self.certifies_no_event:
            raise ContractViolation("incomplete evidence cannot certify no event")


@dataclass(frozen=True, slots=True)
class EquilibriumGuardSnapshot:
    """One fresh, complete equilibrium solve followed by raw guard evaluation."""

    oriented_path_position_mm: float
    raw_guard_values: Mapping[str, float]
    raw_guard_units: Mapping[str, str]
    equilibrium_quality_passed: bool
    equilibrium_response_hash: str
    quality_hashes: tuple[str, ...]
    balance_response_hash: str | None
    balance_recomputed: bool
    coverage_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not math.isfinite(self.oriented_path_position_mm):
            raise ContractViolation("event probe position must be finite")
        if set(self.raw_guard_values) != set(self.raw_guard_units):
            raise ContractViolation("event probe guard value/unit channel sets differ")
        if not self.raw_guard_values:
            raise ContractViolation("event probe must contain raw guard values")
        if any(not math.isfinite(value) for value in self.raw_guard_values.values()):
            raise ContractViolation("event probe contains NaN/Inf guard values")
        if any(not unit for unit in self.raw_guard_units.values()):
            raise ContractViolation("event probe guard units cannot be empty")
        if not self.equilibrium_quality_passed:
            raise ContractViolation("unconverged equilibrium cannot be used for event detection")
        if len(self.equilibrium_response_hash) != 64:
            raise ContractViolation("event equilibrium response requires a full hash")
        if self.balance_response_hash is not None and len(self.balance_response_hash) != 64:
            raise ContractViolation("balance response hash must be a full SHA-256 digest")
        if any(len(value) != 64 for value in self.quality_hashes):
            raise ContractViolation("event quality references must be full hashes")


class EquilibriumEventProbe(Protocol):
    """Owner callback. Every invocation must perform a fresh side-effect-free solve."""

    def __call__(
        self,
        oriented_path_position_mm: float,
        channel_ids: tuple[str, ...],
    ) -> EquilibriumGuardSnapshot: ...


@dataclass(frozen=True, slots=True)
class EventProbeEvidence:
    probe_id: str
    probe_hash: str
    stage: str
    snapshot: EquilibriumGuardSnapshot


@dataclass(frozen=True, slots=True)
class EventSearchRequest:
    search_id: str
    target_id: str
    trial_id: str
    parent_accepted_state_id: str
    interval_start_mm: float
    interval_end_mm: float
    characteristic_length_mm: float
    channels: tuple[EventChannelRegistration, ...]
    coverage: tuple[EventCoverageDeclaration, ...]

    def __post_init__(self) -> None:
        for value in (self.search_id, self.target_id, self.trial_id, self.parent_accepted_state_id):
            if not value:
                raise ContractViolation("event search identity fields cannot be empty")
        if not all(math.isfinite(value) for value in self.interval):
            raise ContractViolation("event search interval must be finite")
        if self.interval_end_mm <= self.interval_start_mm:
            raise ContractViolation("event search interval must follow target orientation")
        if not math.isfinite(self.characteristic_length_mm) or self.characteristic_length_mm <= 0:
            raise ContractViolation("event search requires explicit positive characteristic length")
        channel_ids = tuple(item.channel_id for item in self.channels)
        coverage_ids = tuple(item.channel_id for item in self.coverage)
        if not channel_ids or len(channel_ids) != len(set(channel_ids)):
            raise ContractViolation("event search channels must be unique and nonempty")
        if len(coverage_ids) != len(set(coverage_ids)) or set(channel_ids) != set(coverage_ids):
            raise ContractViolation(
                "every applicable event channel requires exactly one coverage declaration"
            )
        for declaration in self.coverage:
            for enclosure in declaration.candidate_enclosures:
                if (
                    enclosure.left_position_mm < self.interval_start_mm
                    or enclosure.right_position_mm > self.interval_end_mm
                ):
                    raise ContractViolation(
                        "event candidate enclosure lies outside the requested search interval",
                        details={
                            "channel_id": declaration.channel_id,
                            "enclosure_id": enclosure.enclosure_id,
                            "search_interval": self.interval,
                            "candidate_interval": enclosure.interval,
                        },
                    )

    @property
    def interval(self) -> tuple[float, float]:
        return self.interval_start_mm, self.interval_end_mm


@dataclass(frozen=True, slots=True)
class EventSearchFailure:
    reason_code: M02ReasonCode
    stage: str
    channel_ids: tuple[str, ...]
    structured_details: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class EventSearchResult:
    result_id: str
    result_hash: str
    success: bool
    no_event: bool
    located_group: LocatedEventGroup | None
    simultaneous_group: SimultaneousEventGroup | None
    brackets: tuple[EventBracket, ...]
    earliestness_certificate: EventEarliestnessCertificate | None
    probes: tuple[EventProbeEvidence, ...]
    algorithm_switches: tuple[str, ...]
    failure: EventSearchFailure | None


class EventRegistry:
    """Validated event registry with deterministic topological layers."""

    def __init__(self, registrations: Iterable[EventChannelRegistration]) -> None:
        items = tuple(registrations)
        self._by_id = {item.channel_id: item for item in items}
        if not items or len(items) != len(self._by_id):
            raise ContractViolation("event registry requires unique, nonempty channel IDs")
        for item in items:
            missing = set(item.dependency_predecessors) - set(self._by_id)
            if missing:
                raise ContractViolation(
                    "event dependency references an unregistered channel",
                    details={"channel_id": item.channel_id, "missing": sorted(missing)},
                )
            if item.channel_id in item.dependency_predecessors:
                raise ContractViolation("event dependency cannot be a self-loop")
        self._layers = self._topological_layers(tuple(sorted(self._by_id)))

    @property
    def registrations(self) -> tuple[EventChannelRegistration, ...]:
        return tuple(self._by_id[key] for key in sorted(self._by_id))

    @property
    def dependency_layers(self) -> tuple[tuple[str, ...], ...]:
        return self._layers

    def layers_for(self, channel_ids: Iterable[str]) -> tuple[tuple[str, ...], ...]:
        selected = set(channel_ids)
        if not selected <= set(self._by_id):
            raise ContractViolation("event ordering requested unknown channel IDs")
        return tuple(
            tuple(channel_id for channel_id in layer if channel_id in selected)
            for layer in self._layers
            if selected.intersection(layer)
        )

    def dependency_edges_for(self, channel_ids: Iterable[str]) -> tuple[EventDependencyEdge, ...]:
        selected = set(channel_ids)
        edges: list[EventDependencyEdge] = []
        for successor in sorted(selected):
            registration = self._by_id[successor]
            for predecessor in sorted(set(registration.dependency_predecessors) & selected):
                payload = {
                    "predecessor": predecessor,
                    "successor": successor,
                    "owner": registration.owner_id,
                }
                edges.append(
                    EventDependencyEdge.create(
                        edge_id=stable_content_id("m02_event_dependency", payload),
                        predecessor_channel_id=predecessor,
                        successor_channel_id=successor,
                        dependency_kind="OWNER_DECLARED_TRANSITION_PRECEDENCE",
                        owner_id=registration.owner_id,
                        metadata_unit="1",
                    )
                )
        return tuple(edges)

    def _topological_layers(self, keys: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
        indegree = {key: len(self._by_id[key].dependency_predecessors) for key in keys}
        successors: dict[str, list[str]] = defaultdict(list)
        for key in keys:
            for predecessor in self._by_id[key].dependency_predecessors:
                successors[predecessor].append(key)
        ready = sorted(key for key, value in indegree.items() if value == 0)
        layers: list[tuple[str, ...]] = []
        visited = 0
        while ready:
            layer = tuple(ready)
            layers.append(layer)
            visited += len(layer)
            next_ready: list[str] = []
            for predecessor in layer:
                for successor in sorted(successors[predecessor]):
                    indegree[successor] -= 1
                    if indegree[successor] == 0:
                        next_ready.append(successor)
            ready = sorted(next_ready)
        if visited != len(keys):
            raise ContractViolation(
                "event dependency DAG contains a cycle",
                details={"reason": M02ReasonCode.EVENT_DEPENDENCY_CYCLE.value},
            )
        return tuple(layers)


@dataclass(frozen=True, slots=True)
class _RootCandidate:
    channel_id: str
    position_mm: float
    bracket: EventBracket


class EventEngine:
    """Coverage-gated signed event engine with fresh equilibrium probes."""

    def __init__(self, config: NumericsConfig = DEFAULT_NUMERICS_CONFIG) -> None:
        self.config = config

    def search(
        self,
        request: EventSearchRequest,
        probe: EquilibriumEventProbe,
    ) -> EventSearchResult:
        registry = EventRegistry(request.channels)
        coverage = {item.channel_id: item for item in request.coverage}
        incomplete = tuple(sorted(key for key, item in coverage.items() if not item.complete))
        if incomplete:
            return self._failure(
                request,
                M02ReasonCode.EVENT_COVERAGE_UNAVAILABLE,
                "coverage",
                incomplete,
                (("incomplete_channels", ",".join(incomplete)),),
            )
        for channel in request.channels:
            declaration = coverage[channel.channel_id]
            if declaration.kind not in channel.no_event_certificate_capabilities:
                return self._failure(
                    request,
                    M02ReasonCode.EVENT_COVERAGE_UNAVAILABLE,
                    "coverage_capability",
                    (channel.channel_id,),
                    (("certificate_kind", declaration.kind.value),),
                )
            if (
                not declaration.certifies_no_event
                and declaration.maximum_probe_spacing_mm is None
                and not declaration.candidate_enclosures
            ):
                return self._failure(
                    request,
                    M02ReasonCode.EVENT_COVERAGE_UNAVAILABLE,
                    "interval_coverage",
                    (channel.channel_id,),
                    (("reason", "same-sign endpoints are not an interval certificate"),),
                )

        channel_ids = tuple(sorted(item.channel_id for item in request.channels))
        evidence: list[EventProbeEvidence] = []
        snapshots_by_position: dict[float, EquilibriumGuardSnapshot] = {}
        probe_counter = 0

        def fresh(position: float, stage: str) -> EventProbeEvidence:
            nonlocal probe_counter
            snapshot = probe(position, channel_ids)
            probe_counter += 1
            if not math.isclose(
                snapshot.oriented_path_position_mm,
                position,
                rel_tol=0.0,
                abs_tol=max(1.0e-12, abs(position) * 1.0e-14),
            ):
                raise ContractViolation("owner event probe returned a different path position")
            if set(snapshot.raw_guard_values) != set(channel_ids):
                raise ContractViolation(
                    "owner event probe did not evaluate every applicable channel"
                )
            previous = snapshots_by_position.get(position)
            if previous is not None and not self._same_probe_semantics(previous, snapshot):
                raise ContractViolation(
                    "fresh event probes at the same path position disagree semantically",
                    details={"position_mm": position, "stage": stage},
                )
            snapshots_by_position[position] = snapshot
            for registration in request.channels:
                if snapshot.raw_guard_units[registration.channel_id] != registration.raw_guard_unit:
                    raise ContractViolation(
                        "raw dimensional event guard unit changed",
                        details={"channel_id": registration.channel_id},
                    )
                declaration = coverage[registration.channel_id]
                if declaration.requires_balance_recompute and not (
                    snapshot.balance_recomputed and snapshot.balance_response_hash is not None
                ):
                    raise ContractViolation(
                        "event probe reused or omitted the required nonlinear balance solve",
                        details={"channel_id": registration.channel_id},
                    )
            payload = {
                "search_id": request.search_id,
                "probe_sequence": probe_counter,
                "stage": stage,
                "snapshot": snapshot,
            }
            item = EventProbeEvidence(
                probe_id=stable_content_id("m02_event_probe", payload),
                probe_hash=semantic_hash(payload),
                stage=stage,
                snapshot=snapshot,
            )
            evidence.append(item)
            return item

        scan_positions = self._scan_positions(request, coverage)
        scan = [fresh(position, "SCAN") for position in scan_positions]
        candidates: list[_RootCandidate] = []
        switches: list[str] = []
        by_channel = {item.channel_id: item for item in request.channels}
        for channel_id in channel_ids:
            declaration = coverage[channel_id]
            if declaration.certifies_no_event:
                continue
            registration = by_channel[channel_id]
            for left, right in pairwise(scan):
                left_value = left.snapshot.raw_guard_values[channel_id] - registration.zero_level
                right_value = right.snapshot.raw_guard_values[channel_id] - registration.zero_level
                if self._directional_crossing(
                    left_value,
                    right_value,
                    registration.trigger_direction,
                    declaration.raw_guard_zero_tolerance,
                ):
                    root = self._locate_sign_change(
                        request,
                        registration,
                        declaration,
                        left.snapshot.oriented_path_position_mm,
                        right.snapshot.oriented_path_position_mm,
                        fresh,
                    )
                    if root is None:
                        return self._failure(
                            request,
                            M02ReasonCode.EVENT_ROOT_NONCONVERGENCE,
                            "root",
                            (channel_id,),
                            (
                                (
                                    "bracket",
                                    f"{left.snapshot.oriented_path_position_mm}:{right.snapshot.oriented_path_position_mm}",
                                ),
                            ),
                            probes=tuple(evidence),
                        )
                    candidate, fallback = root
                    candidates.append(candidate)
                    if fallback:
                        switches.append(f"{channel_id}:BRENT_TO_BISECTION")
            for enclosure in declaration.candidate_enclosures:
                if enclosure.touch_candidate:
                    touch_root = self._locate_touch(
                        request,
                        registration,
                        declaration,
                        enclosure,
                        fresh,
                    )
                    if touch_root is None:
                        return self._failure(
                            request,
                            M02ReasonCode.EVENT_ROOT_NONCONVERGENCE,
                            "touch_root",
                            (channel_id,),
                            (("enclosure_id", enclosure.enclosure_id),),
                            probes=tuple(evidence),
                        )
                    candidates.append(touch_root)

        candidates = self._deduplicate_candidates(
            candidates,
            self.config.event_position_tolerance_mm(request.characteristic_length_mm),
        )
        if not candidates:
            certificate = self._earliestness_certificate(
                request,
                channel_ids,
                coverage,
                request.interval_end_mm,
                evidence,
                (),
                explanation="complete owner coverage proves no applicable event in the interval",
            )
            return self._success(
                request,
                no_event=True,
                located=None,
                simultaneous=None,
                brackets=(),
                certificate=certificate,
                probes=tuple(evidence),
                switches=tuple(switches),
            )

        earliest_candidate = min(
            candidates,
            key=lambda item: (item.position_mm, item.channel_id, item.bracket.bracket_id),
        )
        simultaneous_tolerance = self.config.simultaneous_tolerance_mm(
            request.characteristic_length_mm
        )
        simultaneous_candidates = self._simultaneous_component(
            candidates,
            earliest_candidate,
            simultaneous_tolerance,
        )
        simultaneous_channels = tuple(sorted({item.channel_id for item in simultaneous_candidates}))
        event_position = min(item.position_mm for item in simultaneous_candidates)
        position_tolerance = self.config.event_position_tolerance_mm(
            request.characteristic_length_mm
        )
        pre_position = max(request.interval_start_mm, event_position - position_tolerance)
        pre_probe = fresh(pre_position, "EVENT_PRE_SIDE")
        event_probe = fresh(event_position, "EVENT_POINT")
        brackets = tuple(item.bracket for item in simultaneous_candidates)
        all_brackets = tuple(item.bracket for item in candidates)
        certificate = self._earliestness_certificate(
            request,
            channel_ids,
            coverage,
            min(item.bracket.left_position_mm for item in simultaneous_candidates),
            evidence,
            all_brackets,
            explanation="all applicable channel coverage is closed before the earliest bracket",
        )
        located_payload = {
            "search_id": request.search_id,
            "position_mm": event_position,
            "channels": simultaneous_channels,
            "brackets": tuple(item.bracket_id for item in brackets),
            "certificate": certificate.semantic_id,
        }
        located = LocatedEventGroup.create(
            located_group_id=stable_content_id("m02_located_event_group", located_payload),
            oriented_path_position_mm=event_position,
            localization_tolerance_mm=position_tolerance,
            channel_ids=simultaneous_channels,
            bracket_ids=tuple(item.bracket_id for item in brackets),
            event_probe_ids=tuple(
                item.probe_id
                for item in evidence
                if item.stage in {"ROOT", "ROOT_ENDPOINT", "TOUCH_ROOT", "EVENT_POINT"}
            ),
            earliestness_certificate=certificate,
            pre_event_response_hash=pre_probe.snapshot.equilibrium_response_hash,
            event_point_response_hash=event_probe.snapshot.equilibrium_response_hash,
            metadata_unit="mm",
        )
        edges = registry.dependency_edges_for(simultaneous_channels)
        canonical_order = tuple(
            channel_id
            for layer in registry.layers_for(simultaneous_channels)
            for channel_id in layer
        )
        simultaneous_payload = {
            "located_group": located.located_group_id,
            "position_mm": event_position,
            "channels": simultaneous_channels,
            "edges": tuple(item.edge_id for item in edges),
            "canonical_order": canonical_order,
        }
        simultaneous = SimultaneousEventGroup.create(
            simultaneous_group_id=stable_content_id(
                "m02_simultaneous_event_group", simultaneous_payload
            ),
            oriented_path_position_mm=event_position,
            simultaneous_tolerance_mm=simultaneous_tolerance,
            located_group_ids=(located.located_group_id,),
            channel_ids=simultaneous_channels,
            dependency_edges=edges,
            canonical_independent_order=canonical_order,
            metadata_unit="mm",
        )
        return self._success(
            request,
            no_event=False,
            located=located,
            simultaneous=simultaneous,
            brackets=all_brackets,
            certificate=certificate,
            probes=tuple(evidence),
            switches=tuple(switches),
        )

    def search_explicit_return_path(
        self,
        capability: ReturnPathCapability,
        request: EventSearchRequest,
        probe: EquilibriumEventProbe,
    ) -> EventSearchResult:
        """Apply the identical event rules to an owner-declared release return sweep."""

        if capability.mode is not ReturnPathMode.EXPLICIT_RETURN_PATH:
            return self._failure(
                request,
                M02ReasonCode.EVENT_COVERAGE_UNAVAILABLE,
                "return_path_capability",
                (),
                (("return_path_mode", capability.mode.value),),
            )
        return self.search(request, probe)

    def _locate_sign_change(
        self,
        request: EventSearchRequest,
        registration: EventChannelRegistration,
        coverage: EventCoverageDeclaration,
        initial_left: float,
        initial_right: float,
        fresh: Callable[[float, str], EventProbeEvidence],
    ) -> tuple[_RootCandidate, bool] | None:
        left_evidence = fresh(initial_left, "ROOT_ENDPOINT")
        right_evidence = fresh(initial_right, "ROOT_ENDPOINT")
        a = initial_left
        b = initial_right
        f_a = (
            left_evidence.snapshot.raw_guard_values[registration.channel_id]
            - registration.zero_level
        )
        f_b = (
            right_evidence.snapshot.raw_guard_values[registration.channel_id]
            - registration.zero_level
        )
        zero_tol = coverage.raw_guard_zero_tolerance
        tolerance = self.config.event_position_tolerance_mm(request.characteristic_length_mm)
        probe_ids = [left_evidence.probe_id, right_evidence.probe_id]
        fallback_used = False
        iterations = 0
        if f_a == 0.0:
            b = a
            f_b = f_a
        elif f_b == 0.0:
            a = b
            f_a = f_b
        elif f_a * f_b > 0.0:
            return None
        else:
            # Brent-Dekker maintains (a, b) as the sign-changing bracket, with b
            # the endpoint whose residual has the smaller magnitude.  c and d
            # retain the two preceding b values for the interpolation safeguards.
            if abs(f_a) < abs(f_b):
                a, b = b, a
                f_a, f_b = f_b, f_a
            c = a
            f_c = f_a
            d = c
            used_bisection_last = True
            for iteration_index in range(1, self.config.max_bracket_iterations + 1):
                iterations = iteration_index
                if abs(b - a) <= tolerance and abs(f_b) <= zero_tol:
                    break

                try:
                    if f_a != f_c and f_b != f_c:
                        candidate = (
                            a * f_b * f_c / ((f_a - f_b) * (f_a - f_c))
                            + b * f_a * f_c / ((f_b - f_a) * (f_b - f_c))
                            + c * f_a * f_b / ((f_c - f_a) * (f_c - f_b))
                        )
                    else:
                        denominator = f_b - f_a
                        candidate = (
                            b - f_b * (b - a) / denominator if denominator != 0.0 else math.nan
                        )
                except ArithmeticError:
                    candidate = math.nan

                interpolation_bound = 0.75 * a + 0.25 * b
                machine_tol = max(
                    math.ulp(a),
                    math.ulp(b),
                    math.ulp(c),
                    1.0e-15,
                )
                inside_safe_interval = (
                    min(interpolation_bound, b) < candidate < max(interpolation_bound, b)
                )
                inside_bracket = min(a, b) < candidate < max(a, b)
                interpolation_unsafe = (
                    not math.isfinite(candidate)
                    or not inside_bracket
                    or not inside_safe_interval
                    or (used_bisection_last and abs(candidate - b) >= 0.5 * abs(b - c))
                    or (not used_bisection_last and abs(candidate - b) >= 0.5 * abs(c - d))
                    or (used_bisection_last and abs(b - c) <= machine_tol)
                    or (not used_bisection_last and abs(c - d) <= machine_tol)
                )
                if interpolation_unsafe:
                    candidate = 0.5 * a + 0.5 * b
                    fallback_used = True
                    used_bisection_last = True
                else:
                    used_bisection_last = False

                point = fresh(candidate, "ROOT")
                probe_ids.append(point.probe_id)
                value = (
                    point.snapshot.raw_guard_values[registration.channel_id]
                    - registration.zero_level
                )
                d = c
                c = b
                f_c = f_b
                if value == 0.0:
                    a = candidate
                    b = candidate
                    f_a = value
                    f_b = value
                    break
                if f_a * value < 0.0:
                    b = candidate
                    f_b = value
                else:
                    a = candidate
                    f_a = value
                if abs(f_a) < abs(f_b):
                    a, b = b, a
                    f_a, f_b = f_b, f_a
            if abs(b - a) > tolerance or abs(f_b) > zero_tol:
                return None

        if a <= b:
            left, right = a, b
            f_left, f_right = f_a, f_b
        else:
            left, right = b, a
            f_left, f_right = f_b, f_a
        position = a if abs(f_a) <= abs(f_b) else b
        final_point = fresh(position, "EVENT_POINT_ROOT_WITNESS")
        probe_ids.append(final_point.probe_id)
        final_value = (
            final_point.snapshot.raw_guard_values[registration.channel_id] - registration.zero_level
        )
        bracket_is_valid = (
            abs(f_left) <= zero_tol
            or abs(f_right) <= zero_tol
            or self._directional_crossing(
                f_left,
                f_right,
                registration.trigger_direction,
                zero_tol,
            )
        )
        if abs(final_value) > zero_tol or not bracket_is_valid:
            return None
        payload = {
            "search_id": request.search_id,
            "channel_id": registration.channel_id,
            "left": left,
            "right": right,
            "left_guard": f_left + registration.zero_level,
            "right_guard": f_right + registration.zero_level,
            "root_witness_guard": final_value + registration.zero_level,
            "coverage": coverage.certificate_id,
            "probe_ids": tuple(probe_ids),
        }
        bracket = EventBracket.create(
            bracket_id=stable_content_id("m02_event_bracket", payload),
            channel_id=registration.channel_id,
            left_position_mm=left,
            right_position_mm=right,
            left_guard_value=f_left + registration.zero_level,
            right_guard_value=f_right + registration.zero_level,
            guard_unit=registration.raw_guard_unit,
            root_method=(EventRootMethod.BISECTION if fallback_used else EventRootMethod.BRENT),
            touch_enclosure=False,
            coverage_certificate_ref=coverage.certificate_id,
            probe_ids=tuple(probe_ids),
            iterations=iterations,
            localization_error_mm=right - left,
            converged=True,
            metadata_unit="mm",
        )
        return _RootCandidate(registration.channel_id, position, bracket), fallback_used

    def _locate_touch(
        self,
        request: EventSearchRequest,
        registration: EventChannelRegistration,
        coverage: EventCoverageDeclaration,
        enclosure: OwnerEventEnclosure,
        fresh: Callable[[float, str], EventProbeEvidence],
    ) -> _RootCandidate | None:
        if registration.trigger_direction is not EventTriggerDirection.TOUCH:
            raise ContractViolation("touch enclosure supplied to a non-TOUCH event channel")
        if EventCertificateKind.STATIONARY_TOUCH_ENCLOSURE not in (
            registration.no_event_certificate_capabilities
        ):
            raise ContractViolation("TOUCH channel lacks stationary enclosure capability")
        left = enclosure.left_position_mm
        right = enclosure.right_position_mm
        tolerance = self.config.event_position_tolerance_mm(request.characteristic_length_mm)
        golden = (math.sqrt(5.0) - 1.0) / 2.0
        probe_ids: list[str] = []

        def objective(position: float) -> tuple[float, EventProbeEvidence]:
            item = fresh(position, "TOUCH_ROOT")
            probe_ids.append(item.probe_id)
            value = abs(
                item.snapshot.raw_guard_values[registration.channel_id] - registration.zero_level
            )
            return value, item

        x1 = right - golden * (right - left)
        x2 = left + golden * (right - left)
        f1, _ = objective(x1)
        f2, _ = objective(x2)
        iterations = 0
        while right - left > tolerance and iterations < self.config.max_bracket_iterations:
            iterations += 1
            if f1 <= f2:
                right = x2
                x2 = x1
                f2 = f1
                x1 = right - golden * (right - left)
                f1, _ = objective(x1)
            else:
                left = x1
                x1 = x2
                f1 = f2
                x2 = left + golden * (right - left)
                f2, _ = objective(x2)
        position = x1 if f1 <= f2 else x2
        best_value = min(f1, f2)
        final = fresh(position, "EVENT_POINT_ROOT_WITNESS")
        probe_ids.append(final.probe_id)
        final_value = abs(
            final.snapshot.raw_guard_values[registration.channel_id] - registration.zero_level
        )
        if (
            best_value > coverage.raw_guard_zero_tolerance
            or final_value > coverage.raw_guard_zero_tolerance
            or right - left > tolerance
        ):
            return None
        left_evidence = fresh(left, "ROOT_ENDPOINT")
        right_evidence = fresh(right, "ROOT_ENDPOINT")
        probe_ids.extend((left_evidence.probe_id, right_evidence.probe_id))
        left_value = left_evidence.snapshot.raw_guard_values[registration.channel_id]
        right_value = right_evidence.snapshot.raw_guard_values[registration.channel_id]
        payload = {
            "search_id": request.search_id,
            "channel_id": registration.channel_id,
            "enclosure_id": enclosure.enclosure_id,
            "left": left,
            "right": right,
            "probe_ids": tuple(probe_ids),
        }
        bracket = EventBracket.create(
            bracket_id=stable_content_id("m02_touch_bracket", payload),
            channel_id=registration.channel_id,
            left_position_mm=left,
            right_position_mm=right,
            left_guard_value=left_value,
            right_guard_value=right_value,
            guard_unit=registration.raw_guard_unit,
            root_method=EventRootMethod.TOUCH_ENCLOSURE,
            touch_enclosure=True,
            coverage_certificate_ref=coverage.certificate_id,
            probe_ids=tuple(probe_ids),
            iterations=iterations,
            localization_error_mm=right - left,
            converged=True,
            metadata_unit="mm",
        )
        return _RootCandidate(registration.channel_id, position, bracket)

    def _scan_positions(
        self,
        request: EventSearchRequest,
        coverage: Mapping[str, EventCoverageDeclaration],
    ) -> tuple[float, ...]:
        spacings = tuple(
            item.maximum_probe_spacing_mm
            for item in coverage.values()
            if not item.certifies_no_event and item.maximum_probe_spacing_mm is not None
        )
        positions = {request.interval_start_mm, request.interval_end_mm}
        if spacings:
            spacing = min(spacings)
            count = max(
                1, math.ceil((request.interval_end_mm - request.interval_start_mm) / spacing)
            )
            for index in range(count + 1):
                positions.add(
                    request.interval_start_mm
                    + (request.interval_end_mm - request.interval_start_mm) * index / count
                )
        for declaration in coverage.values():
            for enclosure in declaration.candidate_enclosures:
                positions.update(
                    {
                        enclosure.left_position_mm,
                        0.5 * (enclosure.left_position_mm + enclosure.right_position_mm),
                        enclosure.right_position_mm,
                    }
                )
        return tuple(sorted(positions))

    @staticmethod
    def _same_probe_semantics(
        left: EquilibriumGuardSnapshot,
        right: EquilibriumGuardSnapshot,
    ) -> bool:
        """Require repeat fresh solves at one coordinate to mean the same thing."""

        return (
            left.oriented_path_position_mm == right.oriented_path_position_mm
            and dict(left.raw_guard_values) == dict(right.raw_guard_values)
            and dict(left.raw_guard_units) == dict(right.raw_guard_units)
            and left.equilibrium_quality_passed == right.equilibrium_quality_passed
            and left.equilibrium_response_hash == right.equilibrium_response_hash
            and left.quality_hashes == right.quality_hashes
            and left.balance_response_hash == right.balance_response_hash
            and left.balance_recomputed == right.balance_recomputed
            and left.coverage_refs == right.coverage_refs
        )

    @staticmethod
    def _simultaneous_component(
        candidates: Iterable[_RootCandidate],
        earliest: _RootCandidate,
        tolerance: float,
    ) -> tuple[_RootCandidate, ...]:
        """Return the transitive simultaneous component containing the earliest root."""

        items = tuple(candidates)
        seed = next(index for index, item in enumerate(items) if item is earliest)
        selected = {seed}
        changed = True
        while changed:
            changed = False
            for index, candidate in enumerate(items):
                if index in selected:
                    continue
                if any(
                    EventEngine._simultaneous_related(candidate, items[member], tolerance)
                    for member in selected
                ):
                    selected.add(index)
                    changed = True
        return tuple(
            sorted(
                (items[index] for index in selected),
                key=lambda item: (item.position_mm, item.channel_id, item.bracket.bracket_id),
            )
        )

    @staticmethod
    def _simultaneous_related(
        left: _RootCandidate,
        right: _RootCandidate,
        tolerance: float,
    ) -> bool:
        brackets_overlap = max(
            left.bracket.left_position_mm,
            right.bracket.left_position_mm,
        ) <= min(
            left.bracket.right_position_mm,
            right.bracket.right_position_mm,
        )
        return brackets_overlap or abs(left.position_mm - right.position_mm) <= tolerance

    @staticmethod
    def _directional_crossing(
        left: float,
        right: float,
        direction: EventTriggerDirection,
        zero_tolerance: float,
    ) -> bool:
        left_zero = abs(left) <= zero_tolerance
        right_zero = abs(right) <= zero_tolerance
        if direction is EventTriggerDirection.TOUCH:
            return False
        if direction is EventTriggerDirection.RISING:
            return (left < -zero_tolerance and right >= -zero_tolerance) or (
                left_zero and right > zero_tolerance
            )
        if direction is EventTriggerDirection.FALLING:
            return (left > zero_tolerance and right <= zero_tolerance) or (
                left_zero and right < -zero_tolerance
            )
        return left_zero or right_zero or left * right < 0.0

    @staticmethod
    def _deduplicate_candidates(
        candidates: Iterable[_RootCandidate], tolerance: float
    ) -> list[_RootCandidate]:
        kept: list[_RootCandidate] = []
        for candidate in sorted(candidates, key=lambda item: (item.position_mm, item.channel_id)):
            if any(
                item.channel_id == candidate.channel_id
                and abs(item.position_mm - candidate.position_mm) <= max(tolerance * 0.25, 1.0e-12)
                for item in kept
            ):
                continue
            kept.append(candidate)
        return kept

    @staticmethod
    def _earliestness_certificate(
        request: EventSearchRequest,
        channel_ids: tuple[str, ...],
        coverage: Mapping[str, EventCoverageDeclaration],
        candidate_left: float,
        probes: Iterable[EventProbeEvidence],
        brackets: Iterable[EventBracket],
        *,
        explanation: str,
    ) -> EventEarliestnessCertificate:
        coverage_refs = tuple(coverage[key].certificate_id for key in channel_ids)
        proof_payload = {
            "search_id": request.search_id,
            "interval_start_mm": request.interval_start_mm,
            "candidate_left_mm": candidate_left,
            "channel_ids": channel_ids,
            "coverage_hashes": tuple(coverage[key].certificate_hash for key in channel_ids),
            "probe_hashes": tuple(item.probe_hash for item in probes),
            "bracket_hashes": tuple(item.semantic_hash for item in brackets),
        }
        return EventEarliestnessCertificate.create(
            certificate_id=stable_content_id("m02_event_earliestness", proof_payload),
            interval_start_mm=request.interval_start_mm,
            candidate_left_mm=candidate_left,
            applicable_channel_ids=channel_ids,
            covered_channel_ids=channel_ids,
            coverage_certificate_refs=coverage_refs,
            no_earlier_event_proven=True,
            proof_hash=semantic_hash(proof_payload),
            explanation=explanation,
            metadata_unit="mm",
        )

    @staticmethod
    def _success(
        request: EventSearchRequest,
        *,
        no_event: bool,
        located: LocatedEventGroup | None,
        simultaneous: SimultaneousEventGroup | None,
        brackets: tuple[EventBracket, ...],
        certificate: EventEarliestnessCertificate,
        probes: tuple[EventProbeEvidence, ...],
        switches: tuple[str, ...],
    ) -> EventSearchResult:
        payload = {
            "search_id": request.search_id,
            "no_event": no_event,
            "located_group": located.semantic_id if located else None,
            "simultaneous_group": simultaneous.semantic_id if simultaneous else None,
            "brackets": tuple(item.semantic_hash for item in brackets),
            "certificate": certificate.semantic_hash,
            "probes": tuple(item.probe_hash for item in probes),
            "algorithm_switches": switches,
        }
        return EventSearchResult(
            result_id=stable_content_id("m02_event_search", payload),
            result_hash=semantic_hash(payload),
            success=True,
            no_event=no_event,
            located_group=located,
            simultaneous_group=simultaneous,
            brackets=brackets,
            earliestness_certificate=certificate,
            probes=probes,
            algorithm_switches=switches,
            failure=None,
        )

    @staticmethod
    def _failure(
        request: EventSearchRequest,
        reason: M02ReasonCode,
        stage: str,
        channel_ids: tuple[str, ...],
        details: tuple[tuple[str, str], ...],
        *,
        probes: tuple[EventProbeEvidence, ...] = (),
    ) -> EventSearchResult:
        failure = EventSearchFailure(reason, stage, channel_ids, details)
        payload = {
            "search_id": request.search_id,
            "failure": failure,
            "probe_hashes": tuple(item.probe_hash for item in probes),
        }
        return EventSearchResult(
            result_id=stable_content_id("m02_event_search_failure", payload),
            result_hash=semantic_hash(payload),
            success=False,
            no_event=False,
            located_group=None,
            simultaneous_group=None,
            brackets=(),
            earliestness_certificate=None,
            probes=probes,
            algorithm_switches=(),
            failure=failure,
        )


@dataclass(frozen=True, slots=True)
class EventSideEvaluation:
    """Owner proof that an event side was freshly and completely assembled/solved."""

    side: str
    response_hash: str
    component_hashes: tuple[tuple[str, str], ...]
    parent_accepted_state_id: str
    event_coordinate_mm: float

    def __post_init__(self) -> None:
        required = {
            "unknowns",
            "residuals",
            "graph",
            "guards",
            "wrench",
            "energy",
            "quality",
            "intents",
        }
        supplied = {key for key, _ in self.component_hashes}
        if supplied != required:
            raise ContractViolation(
                "event-side solve lacks complete reassembly evidence",
                details={
                    "missing": sorted(required - supplied),
                    "extra": sorted(supplied - required),
                },
            )
        if len(self.response_hash) != 64 or any(
            len(value) != 64 for _, value in self.component_hashes
        ):
            raise ContractViolation("event-side response/component hashes must be full SHA-256")
        if not self.parent_accepted_state_id or not math.isfinite(self.event_coordinate_mm):
            raise ContractViolation("event-side solve requires parent and finite coordinate")


@dataclass(frozen=True, slots=True)
class EventPostResult:
    pre_side: EventSideEvaluation
    post_side: EventSideEvaluation
    transition_intent_ids: tuple[str, ...]
    pre_callback_count: int
    post_callback_count: int
    complete_recompute: bool


def evaluate_event_post_sides(
    *,
    event_coordinate_mm: float,
    simultaneous_channel_ids: tuple[str, ...],
    pre_solver: Callable[[float, tuple[str, ...]], EventSideEvaluation],
    transition: Callable[[tuple[str, ...]], tuple[str, ...]],
    post_solver: Callable[[float, tuple[str, ...], tuple[str, ...]], EventSideEvaluation],
) -> EventPostResult:
    """Invoke distinct full pre/post owner solves around simultaneous transitions."""

    pre = pre_solver(event_coordinate_mm, simultaneous_channel_ids)
    if pre.side != "PRE_EVENT":
        raise ContractViolation("event pre-side callback returned the wrong side semantics")
    if not math.isclose(pre.event_coordinate_mm, event_coordinate_mm, rel_tol=0.0, abs_tol=0.0):
        raise ContractViolation(
            "event side callback coordinate differs from the requested event coordinate"
        )
    intents = transition(simultaneous_channel_ids)
    post = post_solver(event_coordinate_mm, simultaneous_channel_ids, intents)
    if post.side != "POST_EVENT":
        raise ContractViolation("event post-side callback returned the wrong side semantics")
    if not math.isclose(post.event_coordinate_mm, event_coordinate_mm, rel_tol=0.0, abs_tol=0.0):
        raise ContractViolation(
            "event side callback coordinate differs from the requested event coordinate"
        )
    if pre is post:
        raise ContractViolation("post-event response cannot reuse the pre-event object")
    if pre.parent_accepted_state_id != post.parent_accepted_state_id:
        raise ContractViolation("pre/post event solves must derive from the same accepted parent")
    if not math.isclose(
        pre.event_coordinate_mm, post.event_coordinate_mm, rel_tol=0.0, abs_tol=0.0
    ):
        raise ContractViolation("pre/post event solves must use the same event coordinate")
    return EventPostResult(pre, post, intents, 1, 1, True)


@dataclass(frozen=True, slots=True)
class CascadeEvaluation:
    state_hash: str
    event_signature_hash: str
    event_channel_ids: tuple[str, ...]
    transition_intent_ids: tuple[str, ...]
    zero_progress_intent_ids: tuple[str, ...]
    guard_margin_improvement: float
    equilibrium_response_hash: str

    def __post_init__(self) -> None:
        for value in (self.state_hash, self.event_signature_hash, self.equilibrium_response_hash):
            if len(value) != 64:
                raise ContractViolation("cascade state/signature/response requires full hashes")
        if not math.isfinite(self.guard_margin_improvement):
            raise ContractViolation("cascade guard improvement must be finite")
        if not set(self.zero_progress_intent_ids) <= set(self.transition_intent_ids):
            raise ContractViolation("zero-progress intents must belong to the transition batch")


@dataclass(frozen=True, slots=True)
class CascadeResult:
    converged: bool
    rounds: tuple[CascadeRound, ...]
    reason_code: M02ReasonCode
    structured_details: tuple[tuple[str, str], ...]


class EventCascadeEngine:
    """Re-register same-position guards after every transition and detect Zeno."""

    def __init__(self, config: NumericsConfig = DEFAULT_NUMERICS_CONFIG) -> None:
        self.config = config

    def run(
        self,
        *,
        cascade_id: str,
        event_coordinate_mm: float,
        evaluate_round: Callable[[int], CascadeEvaluation],
    ) -> CascadeResult:
        if not cascade_id or not math.isfinite(event_coordinate_mm):
            raise ContractViolation("cascade requires an ID and finite event coordinate")
        rounds: list[CascadeRound] = []
        seen_states: dict[str, float] = {}
        signature_history: list[str] = []
        seen_intent_signatures: set[str] = set()
        for index in range(self.config.max_same_position_cascade):
            evaluation = evaluate_round(index)
            if not evaluation.event_channel_ids:
                return CascadeResult(True, tuple(rounds), M02ReasonCode.OK, ())
            intent_signature = semantic_hash(evaluation.transition_intent_ids)
            zeno_detail: tuple[str, str] | None = None
            previous_improvement = seen_states.get(evaluation.state_hash)
            if previous_improvement is not None and (
                evaluation.guard_margin_improvement <= previous_improvement
            ):
                zeno_detail = ("repeated_state_hash", evaluation.state_hash)
            elif self._signature_oscillates(
                signature_history,
                evaluation.event_signature_hash,
                evaluation.guard_margin_improvement,
            ):
                zeno_detail = ("event_signature_oscillation", evaluation.event_signature_hash)
            elif intent_signature in seen_intent_signatures and evaluation.zero_progress_intent_ids:
                zeno_detail = (
                    "zero_progress_intents",
                    ",".join(evaluation.zero_progress_intent_ids),
                )
            if zeno_detail is not None:
                return CascadeResult(
                    False,
                    tuple(rounds),
                    M02ReasonCode.ZENO_CANDIDATE,
                    (zeno_detail,),
                )
            seen_states[evaluation.state_hash] = evaluation.guard_margin_improvement
            signature_history.append(evaluation.event_signature_hash)
            seen_intent_signatures.add(intent_signature)
            rounds.append(
                CascadeRound.create(
                    cascade_id=cascade_id,
                    round_index=index,
                    event_coordinate_mm=event_coordinate_mm,
                    state_hash=evaluation.state_hash,
                    event_signature_hash=evaluation.event_signature_hash,
                    event_channel_ids=evaluation.event_channel_ids,
                    transition_intent_ids=evaluation.transition_intent_ids,
                    guard_margin_improvement=evaluation.guard_margin_improvement,
                    equilibrium_response_hash=evaluation.equilibrium_response_hash,
                    metadata_unit="mm",
                )
            )
        return CascadeResult(
            False,
            tuple(rounds),
            M02ReasonCode.ZENO_CANDIDATE,
            (("maximum_rounds", str(self.config.max_same_position_cascade)),),
        )

    @staticmethod
    def _signature_oscillates(
        history: list[str],
        incoming: str,
        guard_margin_improvement: float,
    ) -> bool:
        sequence = [*history, incoming]
        for period in range(1, len(sequence) // 2 + 1):
            if sequence[-period:] != sequence[-2 * period : -period]:
                continue
            if period > 1 or guard_margin_improvement <= 0.0:
                return True
        return False
