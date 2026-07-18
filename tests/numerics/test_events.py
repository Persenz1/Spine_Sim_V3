from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field, replace

import pytest

from spine_sim.foundation.canonical import semantic_hash
from spine_sim.foundation.errors import ContractViolation
from spine_sim.numerics.config import NumericsConfig
from spine_sim.numerics.contracts import (
    EventAdmissibleSide,
    EventCertificateKind,
    EventChannelRegistration,
    EventDetectionMode,
    EventRootMethod,
    EventTriggerDirection,
    M02ReasonCode,
    ReturnPathCapability,
    ReturnPathMode,
)
from spine_sim.numerics.events import (
    CascadeEvaluation,
    EquilibriumGuardSnapshot,
    EventCascadeEngine,
    EventCoverageDeclaration,
    EventEngine,
    EventRegistry,
    EventSearchRequest,
    EventSideEvaluation,
    OwnerEventEnclosure,
    evaluate_event_post_sides,
)


def digest(value: object) -> str:
    return semantic_hash(value)


def channel(
    channel_id: str,
    *,
    direction: EventTriggerDirection = EventTriggerDirection.EITHER,
    predecessors: tuple[str, ...] = (),
    capabilities: tuple[EventCertificateKind, ...] = (EventCertificateKind.ADAPTIVE_PROBE_SPACING,),
) -> EventChannelRegistration:
    return EventChannelRegistration.create(
        channel_id=channel_id,
        owner_id=f"owner-{channel_id}",
        entity_ids=(f"entity-{channel_id}",),
        event_kind="OWNER_DEFINED_EVENT",
        guard_id=f"guard-{channel_id}",
        guard_version="1.0.0",
        raw_guard_unit="mm",
        zero_level=0.0,
        admissible_side=EventAdmissibleSide.BOTH_WITH_GRAPH_RULE,
        trigger_direction=direction,
        applicability_predicate_id=f"applicable-{channel_id}",
        branch_state_scope=("branch",),
        detection_mode=(
            EventDetectionMode.SIGN_CHANGE_AND_TOUCH
            if direction is EventTriggerDirection.TOUCH
            else EventDetectionMode.SIGN_CHANGE
        ),
        no_event_certificate_capabilities=capabilities,
        dependency_predecessors=predecessors,
        transition_owner=f"owner-{channel_id}",
        post_event_side_request_id=f"post-{channel_id}",
        metadata_unit="mm",
    )


def adaptive_coverage(
    channel_id: str,
    *,
    spacing: float = 0.1,
    complete: bool = True,
    requires_balance: bool = False,
) -> EventCoverageDeclaration:
    return EventCoverageDeclaration(
        certificate_id=f"coverage-{channel_id}",
        channel_id=channel_id,
        kind=EventCertificateKind.ADAPTIVE_PROBE_SPACING,
        certificate_hash=digest((channel_id, spacing, complete)),
        complete=complete,
        certifies_no_event=False,
        maximum_probe_spacing_mm=spacing,
        raw_guard_zero_tolerance=1.0e-10,
        requires_balance_recompute=requires_balance,
    )


def request(
    channels: tuple[EventChannelRegistration, ...],
    coverage: tuple[EventCoverageDeclaration, ...],
    *,
    start: float = 0.0,
    end: float = 1.0,
    lref: float = 1.0,
) -> EventSearchRequest:
    return EventSearchRequest(
        search_id="search",
        target_id="target",
        trial_id="trial",
        parent_accepted_state_id="state-0",
        interval_start_mm=start,
        interval_end_mm=end,
        characteristic_length_mm=lref,
        channels=channels,
        coverage=coverage,
    )


@dataclass
class CountingProbe:
    functions: dict[str, Callable[[float], float]]
    balance: bool = False
    calls: list[float] = field(default_factory=list)

    def __call__(
        self, oriented_path_position_mm: float, channel_ids: tuple[str, ...]
    ) -> EquilibriumGuardSnapshot:
        position = oriented_path_position_mm
        self.calls.append(position)
        values = {key: self.functions[key](position) for key in channel_ids}
        balance_hash = digest(("balanced-uz", position, values)) if self.balance else None
        return EquilibriumGuardSnapshot(
            oriented_path_position_mm=position,
            raw_guard_values=values,
            raw_guard_units={key: "mm" for key in channel_ids},
            equilibrium_quality_passed=True,
            equilibrium_response_hash=digest(("equilibrium", position, values)),
            quality_hashes=(digest(("quality", position, values)),),
            balance_response_hash=balance_hash,
            balance_recomputed=self.balance,
            coverage_refs=tuple(f"coverage-{key}" for key in channel_ids),
        )


def test_linear_crossing_is_bracketed_and_localized() -> None:
    registration = channel("cross", direction=EventTriggerDirection.RISING)
    probe = CountingProbe({"cross": lambda x: x - 0.4})
    result = EventEngine().search(request((registration,), (adaptive_coverage("cross"),)), probe)
    assert result.success and not result.no_event
    assert result.located_group is not None
    assert result.located_group.oriented_path_position_mm == pytest.approx(0.4, abs=0.01)
    assert result.earliestness_certificate is not None
    assert result.earliestness_certificate.no_earlier_event_proven
    assert result.brackets[0].localization_error_mm <= 0.01
    assert len(probe.calls) == len(result.probes)


def test_brent_dekker_preserves_bracket_and_records_safe_interpolation() -> None:
    registration = channel("brent")
    result = EventEngine().search(
        request((registration,), (adaptive_coverage("brent", spacing=0.2),)),
        CountingProbe({"brent": lambda x: x**3 - 0.03}),
    )
    assert result.success
    assert len(result.brackets) == 1
    bracket = result.brackets[0]
    assert bracket.root_method is EventRootMethod.BRENT
    assert bracket.left_guard_value * bracket.right_guard_value <= 0.0
    assert bracket.localization_error_mm <= 0.01
    assert bracket.iterations <= 80
    assert result.algorithm_switches == ()


def test_unsafe_brent_interpolation_switches_to_bisection_and_stays_bracketed() -> None:
    registration = channel("flat")
    result = EventEngine().search(
        request((registration,), (adaptive_coverage("flat", spacing=0.2),)),
        CountingProbe({"flat": lambda x: (x - 0.43) ** 3}),
    )
    assert result.success
    bracket = result.brackets[0]
    assert bracket.root_method is EventRootMethod.BISECTION
    assert bracket.left_guard_value * bracket.right_guard_value <= 0.0
    assert bracket.localization_error_mm <= 0.01
    assert result.algorithm_switches == ("flat:BRENT_TO_BISECTION",)


def test_bracket_solver_obeys_configured_iteration_limit() -> None:
    registration = channel("limited")
    engine = EventEngine(
        NumericsConfig.resolved(
            event_position_tol_over_lref=1.0e-12,
            max_bracket_iterations=1,
        )
    )
    result = engine.search(
        request((registration,), (adaptive_coverage("limited", spacing=0.2),)),
        CountingProbe({"limited": lambda x: (x - 0.43) ** 3}),
    )
    assert not result.success
    assert result.failure is not None
    assert result.failure.reason_code is M02ReasonCode.EVENT_ROOT_NONCONVERGENCE
    assert sum(item.stage == "ROOT" for item in result.probes) <= 1


def test_changed_final_root_witness_at_same_position_is_contract_rejected() -> None:
    registration = channel("unstable")

    class InconsistentProbe:
        def __init__(self) -> None:
            self.base = CountingProbe({"unstable": lambda x: x - 0.43})
            self.root_witness_calls = 0

        def __call__(
            self, oriented_path_position_mm: float, channel_ids: tuple[str, ...]
        ) -> EquilibriumGuardSnapshot:
            position = oriented_path_position_mm
            snapshot = self.base(position, channel_ids)
            if math.isclose(position, 0.43, rel_tol=0.0, abs_tol=1.0e-14):
                self.root_witness_calls += 1
                if self.root_witness_calls > 1:
                    changed_values = dict(snapshot.raw_guard_values)
                    changed_values["unstable"] = 0.25
                    return replace(
                        snapshot,
                        raw_guard_values=changed_values,
                        equilibrium_response_hash=digest(("changed-root-witness", position)),
                    )
            return snapshot

    with pytest.raises(ContractViolation, match="disagree semantically"):
        EventEngine().search(
            request((registration,), (adaptive_coverage("unstable", spacing=0.1),)),
            InconsistentProbe(),
        )


@pytest.mark.parametrize(
    ("direction", "expected_event"),
    [
        (EventTriggerDirection.RISING, True),
        (EventTriggerDirection.FALLING, False),
        (EventTriggerDirection.EITHER, True),
    ],
)
def test_trigger_direction_uses_actual_target_traversal(
    direction: EventTriggerDirection, expected_event: bool
) -> None:
    registration = channel("direction", direction=direction)
    result = EventEngine().search(
        request((registration,), (adaptive_coverage("direction"),)),
        CountingProbe({"direction": lambda x: x - 0.5}),
    )
    assert result.success
    assert result.no_event is (not expected_event)


def test_same_sign_endpoints_with_two_interior_roots_are_both_detected() -> None:
    registration = channel("double")
    result = EventEngine().search(
        request((registration,), (adaptive_coverage("double", spacing=0.05),)),
        CountingProbe({"double": lambda x: (x - 0.25) * (x - 0.75)}),
    )
    assert result.success and not result.no_event
    assert len(result.brackets) == 2
    assert result.located_group is not None
    assert result.located_group.oriented_path_position_mm == pytest.approx(0.25, abs=0.01)


def test_same_sign_endpoints_without_interval_certificate_are_rejected() -> None:
    registration = channel(
        "uncertified",
        capabilities=(EventCertificateKind.SIGN_CHANGE_BRACKETS,),
    )
    coverage = EventCoverageDeclaration(
        certificate_id="endpoint-only",
        channel_id="uncertified",
        kind=EventCertificateKind.SIGN_CHANGE_BRACKETS,
        certificate_hash=digest("endpoint-only"),
        complete=True,
        certifies_no_event=False,
        maximum_probe_spacing_mm=None,
        raw_guard_zero_tolerance=1.0e-10,
    )
    result = EventEngine().search(
        request((registration,), (coverage,)),
        CountingProbe({"uncertified": lambda x: (x - 0.25) * (x - 0.75)}),
    )
    assert not result.success
    assert result.failure is not None
    assert result.failure.reason_code is M02ReasonCode.EVENT_COVERAGE_UNAVAILABLE
    assert dict(result.failure.structured_details)["reason"].startswith("same-sign")


def test_incomplete_channel_coverage_rejects_trial_without_probing() -> None:
    registration = channel("incomplete")
    probe = CountingProbe({"incomplete": lambda x: x - 0.5})
    result = EventEngine().search(
        request(
            (registration,),
            (adaptive_coverage("incomplete", complete=False),),
        ),
        probe,
    )
    assert not result.success
    assert result.failure is not None
    assert result.failure.reason_code is M02ReasonCode.EVENT_COVERAGE_UNAVAILABLE
    assert probe.calls == []


def test_stationary_touch_uses_owner_enclosure_not_blackbox_guessing() -> None:
    registration = channel(
        "touch",
        direction=EventTriggerDirection.TOUCH,
        capabilities=(EventCertificateKind.STATIONARY_TOUCH_ENCLOSURE,),
    )
    enclosure = OwnerEventEnclosure(
        enclosure_id="touch-enclosure",
        left_position_mm=0.2,
        right_position_mm=0.8,
        touch_candidate=True,
        owner_proof_hash=digest("stationary-owner-proof"),
    )
    coverage = EventCoverageDeclaration(
        certificate_id="coverage-touch",
        channel_id="touch",
        kind=EventCertificateKind.STATIONARY_TOUCH_ENCLOSURE,
        certificate_hash=digest("coverage-touch"),
        complete=True,
        certifies_no_event=False,
        maximum_probe_spacing_mm=None,
        raw_guard_zero_tolerance=1.0e-5,
        candidate_enclosures=(enclosure,),
    )
    result = EventEngine().search(
        request((registration,), (coverage,)),
        CountingProbe({"touch": lambda x: (x - 0.5) ** 2}),
    )
    assert result.success and result.located_group is not None
    assert result.located_group.oriented_path_position_mm == pytest.approx(0.5, abs=0.01)
    assert result.brackets[0].touch_enclosure
    assert result.brackets[0].root_method.value == "TOUCH_ENCLOSURE"


def test_candidate_enclosure_outside_search_interval_is_rejected_before_probing() -> None:
    registration = channel(
        "outside-touch",
        direction=EventTriggerDirection.TOUCH,
        capabilities=(EventCertificateKind.STATIONARY_TOUCH_ENCLOSURE,),
    )
    coverage = EventCoverageDeclaration(
        certificate_id="coverage-outside-touch",
        channel_id="outside-touch",
        kind=EventCertificateKind.STATIONARY_TOUCH_ENCLOSURE,
        certificate_hash=digest("coverage-outside-touch"),
        complete=True,
        certifies_no_event=False,
        maximum_probe_spacing_mm=None,
        raw_guard_zero_tolerance=1.0e-5,
        candidate_enclosures=(
            OwnerEventEnclosure(
                enclosure_id="outside-enclosure",
                left_position_mm=-0.01,
                right_position_mm=0.25,
                touch_candidate=True,
                owner_proof_hash=digest("outside-enclosure-proof"),
            ),
        ),
    )
    with pytest.raises(ContractViolation, match="outside the requested search interval"):
        request((registration,), (coverage,))


def test_every_b_scan_bracket_root_and_event_probe_recomputes_balance() -> None:
    registration = channel("b-balance", direction=EventTriggerDirection.RISING)
    probe = CountingProbe(
        {"b-balance": lambda x: x * x - 0.25},
        balance=True,
    )
    result = EventEngine().search(
        request(
            (registration,),
            (adaptive_coverage("b-balance", requires_balance=True),),
        ),
        probe,
    )
    deliberately_bad_a_event_fraction_predictor = 0.9
    assert deliberately_bad_a_event_fraction_predictor != pytest.approx(
        result.located_group.oriented_path_position_mm if result.located_group else -1.0
    )
    assert result.success and result.located_group is not None
    assert result.located_group.oriented_path_position_mm == pytest.approx(0.5, abs=0.01)
    assert len(result.probes) == len(probe.calls)
    assert all(item.snapshot.balance_recomputed for item in result.probes)
    assert all(item.snapshot.balance_response_hash for item in result.probes)


def test_required_b_balance_cannot_reuse_an_unbalanced_probe() -> None:
    registration = channel("b-balance")
    with pytest.raises(ContractViolation, match="balance"):
        EventEngine().search(
            request(
                (registration,),
                (adaptive_coverage("b-balance", requires_balance=True),),
            ),
            CountingProbe({"b-balance": lambda x: x - 0.5}, balance=False),
        )


def test_large_and_halved_scan_spacing_preserve_event_order() -> None:
    channels = (channel("early"), channel("late"))
    functions = {"early": lambda x: x - 0.3, "late": lambda x: x - 0.7}
    coarse = EventEngine().search(
        request(
            channels, tuple(adaptive_coverage(item.channel_id, spacing=0.2) for item in channels)
        ),
        CountingProbe(functions),
    )
    fine = EventEngine().search(
        request(
            channels, tuple(adaptive_coverage(item.channel_id, spacing=0.1) for item in channels)
        ),
        CountingProbe(functions),
    )
    assert coarse.located_group is not None and fine.located_group is not None
    assert coarse.located_group.channel_ids == fine.located_group.channel_ids == ("early",)
    assert coarse.located_group.oriented_path_position_mm == pytest.approx(
        fine.located_group.oriented_path_position_mm, abs=0.01
    )
    assert {item.channel_id for item in coarse.brackets} == {"early", "late"}


def test_simultaneous_roots_are_all_retained_and_dependency_sorted() -> None:
    channels = (
        channel("close-old"),
        channel("establish-new", predecessors=("close-old",)),
    )
    functions = {"close-old": lambda x: x - 0.4, "establish-new": lambda x: x - 0.405}
    result = EventEngine().search(
        request(
            channels,
            tuple(adaptive_coverage(item.channel_id, spacing=0.05) for item in channels),
            lref=10.0,
        ),
        CountingProbe(functions),
    )
    assert result.simultaneous_group is not None
    assert set(result.simultaneous_group.channel_ids) == {"close-old", "establish-new"}
    assert result.simultaneous_group.canonical_independent_order == (
        "close-old",
        "establish-new",
    )
    assert len(result.simultaneous_group.dependency_edges) == 1


def test_simultaneous_group_uses_transitive_position_closure() -> None:
    channels = (channel("first"), channel("middle"), channel("last"))
    result = EventEngine().search(
        request(
            channels,
            tuple(adaptive_coverage(item.channel_id, spacing=0.05) for item in channels),
        ),
        CountingProbe(
            {
                "first": lambda x: x - 0.4,
                "middle": lambda x: x - 0.409,
                "last": lambda x: x - 0.418,
            }
        ),
    )
    assert result.success and result.simultaneous_group is not None
    assert set(result.simultaneous_group.channel_ids) == {"first", "middle", "last"}


def test_overlapping_root_brackets_are_simultaneous_beyond_position_tolerance() -> None:
    channels = (channel("overlap-a"), channel("overlap-b"))
    coverage = tuple(
        replace(
            adaptive_coverage(item.channel_id, spacing=0.1),
            raw_guard_zero_tolerance=3.0e-7,
        )
        for item in channels
    )
    engine = EventEngine(
        NumericsConfig.resolved(
            event_position_tol_over_lref=0.05,
            simultaneous_tol_over_lref=0.01,
        )
    )
    result = engine.search(
        request(channels, coverage),
        CountingProbe(
            {
                "overlap-a": lambda x: (x - 0.413) ** 3,
                "overlap-b": lambda x: (x - 0.43) ** 3,
            }
        ),
    )
    assert result.success and result.simultaneous_group is not None
    first, second = result.brackets
    assert max(first.left_position_mm, second.left_position_mm) <= min(
        first.right_position_mm, second.right_position_mm
    )
    witness_positions = tuple(
        next(
            item for item in result.probes if item.probe_id == bracket.probe_ids[-1]
        ).snapshot.oriented_path_position_mm
        for bracket in result.brackets
    )
    assert abs(witness_positions[0] - witness_positions[1]) > 0.01
    assert set(result.simultaneous_group.channel_ids) == {"overlap-a", "overlap-b"}


def test_independent_simultaneous_ids_only_order_records_not_physics() -> None:
    channels = (channel("z-event"), channel("a-event"))
    result = EventEngine().search(
        request(
            channels,
            tuple(adaptive_coverage(item.channel_id) for item in channels),
            lref=10.0,
        ),
        CountingProbe({"z-event": lambda x: x - 0.5, "a-event": lambda x: x - 0.5}),
    )
    assert result.simultaneous_group is not None
    assert result.simultaneous_group.canonical_independent_order == ("a-event", "z-event")
    assert set(result.simultaneous_group.channel_ids) == {"a-event", "z-event"}


def test_dependency_cycle_is_a_contract_rejection() -> None:
    with pytest.raises(ContractViolation, match="cycle"):
        EventRegistry(
            (
                channel("one", predecessors=("two",)),
                channel("two", predecessors=("one",)),
            )
        )


def side(side_name: str, *, parent: str = "state-0") -> EventSideEvaluation:
    components = tuple(
        (name, digest((side_name, name)))
        for name in (
            "unknowns",
            "residuals",
            "graph",
            "guards",
            "wrench",
            "energy",
            "quality",
            "intents",
        )
    )
    return EventSideEvaluation(
        side=side_name,
        response_hash=digest((side_name, "response")),
        component_hashes=components,
        parent_accepted_state_id=parent,
        event_coordinate_mm=0.4,
    )


def test_event_post_invokes_distinct_complete_reassembly_callbacks() -> None:
    counts = {"pre": 0, "transition": 0, "post": 0}

    def pre_solver(_: float, __: tuple[str, ...]) -> EventSideEvaluation:
        counts["pre"] += 1
        return side("PRE_EVENT")

    def transition(_: tuple[str, ...]) -> tuple[str, ...]:
        counts["transition"] += 1
        return ("intent",)

    def post_solver(_: float, __: tuple[str, ...], ___: tuple[str, ...]) -> EventSideEvaluation:
        counts["post"] += 1
        return side("POST_EVENT")

    result = evaluate_event_post_sides(
        event_coordinate_mm=0.4,
        simultaneous_channel_ids=("event",),
        pre_solver=pre_solver,
        transition=transition,
        post_solver=post_solver,
    )
    assert result.complete_recompute
    assert counts == {"pre": 1, "transition": 1, "post": 1}
    assert result.pre_side.response_hash != result.post_side.response_hash


def test_event_post_rejects_callbacks_at_a_different_coordinate() -> None:
    def wrong_side(side_name: str) -> EventSideEvaluation:
        return replace(side(side_name), event_coordinate_mm=0.5)

    with pytest.raises(ContractViolation, match="requested event coordinate"):
        evaluate_event_post_sides(
            event_coordinate_mm=0.4,
            simultaneous_channel_ids=("event",),
            pre_solver=lambda _coordinate, _channels: wrong_side("PRE_EVENT"),
            transition=lambda _channels: ("intent",),
            post_solver=lambda _coordinate, _channels, _intents: wrong_side("POST_EVENT"),
        )


def test_event_side_rejects_missing_old_wrench_recompute_evidence() -> None:
    with pytest.raises(ContractViolation, match="complete reassembly"):
        EventSideEvaluation(
            side="POST_EVENT",
            response_hash=digest("post"),
            component_hashes=(("residuals", digest("residuals")),),
            parent_accepted_state_id="state-0",
            event_coordinate_mm=0.4,
        )


def cascade_evaluation(index: int, active_rounds: int = 2) -> CascadeEvaluation:
    active = (f"event-{index}",) if index < active_rounds else ()
    return CascadeEvaluation(
        state_hash=digest(("state", index)),
        event_signature_hash=digest(("signature", index)),
        event_channel_ids=active,
        transition_intent_ids=(f"intent-{index}",) if active else (),
        zero_progress_intent_ids=(),
        guard_margin_improvement=float(index + 1),
        equilibrium_response_hash=digest(("response", index)),
    )


def test_same_position_cascade_reregisters_until_clear() -> None:
    calls: list[int] = []

    def evaluate(index: int) -> CascadeEvaluation:
        calls.append(index)
        return cascade_evaluation(index)

    result = EventCascadeEngine().run(
        cascade_id="cascade",
        event_coordinate_mm=0.4,
        evaluate_round=evaluate,
    )
    assert result.converged
    assert len(result.rounds) == 2
    assert calls == [0, 1, 2]


def test_repeated_state_or_signature_is_structured_zeno_candidate() -> None:
    repeated_state = digest("same-state")

    def evaluate(index: int) -> CascadeEvaluation:
        return CascadeEvaluation(
            state_hash=repeated_state,
            event_signature_hash=digest(("signature", index)),
            event_channel_ids=("event",),
            transition_intent_ids=(f"intent-{index}",),
            zero_progress_intent_ids=(),
            guard_margin_improvement=0.0,
            equilibrium_response_hash=digest(("response", index)),
        )

    result = EventCascadeEngine().run(
        cascade_id="cascade",
        event_coordinate_mm=0.4,
        evaluate_round=evaluate,
    )
    assert not result.converged
    assert result.reason_code is M02ReasonCode.ZENO_CANDIDATE
    assert dict(result.structured_details)["repeated_state_hash"] == repeated_state


def test_repeated_signature_with_new_state_and_positive_progress_can_clear() -> None:
    same_signature = digest("same-active-signature")

    def evaluate(index: int) -> CascadeEvaluation:
        active = ("event",) if index < 3 else ()
        return CascadeEvaluation(
            state_hash=digest(("progressing-state", index)),
            event_signature_hash=same_signature,
            event_channel_ids=active,
            transition_intent_ids=(f"intent-{index}",) if active else (),
            zero_progress_intent_ids=(),
            guard_margin_improvement=float(index + 1),
            equilibrium_response_hash=digest(("response", index)),
        )

    result = EventCascadeEngine().run(
        cascade_id="cascade",
        event_coordinate_mm=0.4,
        evaluate_round=evaluate,
    )
    assert result.converged
    assert len(result.rounds) == 3


def test_cascade_hard_round_limit_never_skips_event() -> None:
    engine = EventCascadeEngine(NumericsConfig.resolved(max_same_position_cascade=2))
    result = engine.run(
        cascade_id="cascade",
        event_coordinate_mm=0.4,
        evaluate_round=lambda index: cascade_evaluation(index, active_rounds=10),
    )
    assert not result.converged
    assert result.reason_code is M02ReasonCode.ZENO_CANDIDATE
    assert dict(result.structured_details)["maximum_rounds"] == "2"


def return_capability(mode: ReturnPathMode) -> ReturnPathCapability:
    explicit = mode is ReturnPathMode.EXPLICIT_RETURN_PATH
    return ReturnPathCapability.create(
        owner_id="release-owner",
        release_event_id="release",
        mode=mode,
        path_mapping_id="return-map" if explicit else None,
        pose_path_ref="return-pose" if explicit else None,
        swept_geometry_ref="return-sweep" if explicit else None,
        reason_code=f"OWNER_{mode.value}",
        metadata_unit="1",
    )


def test_release_explicit_return_sweep_uses_same_recontact_earliestness() -> None:
    registration = channel("recontact", direction=EventTriggerDirection.RISING)
    probe = CountingProbe({"recontact": lambda x: x - 0.65})
    result = EventEngine().search_explicit_return_path(
        return_capability(ReturnPathMode.EXPLICIT_RETURN_PATH),
        request((registration,), (adaptive_coverage("recontact"),)),
        probe,
    )
    assert result.success and result.located_group is not None
    assert result.located_group.oriented_path_position_mm == pytest.approx(0.65, abs=0.01)
    assert any(item.stage == "EVENT_POINT" for item in result.probes)


@pytest.mark.parametrize(
    "mode",
    [
        ReturnPathMode.HOLD_AT_RELEASE_POSE,
        ReturnPathMode.UNSUPPORTED,
        ReturnPathMode.UNAVAILABLE,
    ],
)
def test_owner_without_explicit_return_path_is_not_auto_reset_or_swept(
    mode: ReturnPathMode,
) -> None:
    registration = channel("recontact")
    probe = CountingProbe({"recontact": lambda x: x - 0.5})
    result = EventEngine().search_explicit_return_path(
        return_capability(mode),
        request((registration,), (adaptive_coverage("recontact"),)),
        probe,
    )
    assert not result.success
    assert result.failure is not None
    assert dict(result.failure.structured_details)["return_path_mode"] == mode.value
    assert probe.calls == []
