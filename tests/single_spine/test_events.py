from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import cast

import pytest

from spine_sim.foundation.canonical import semantic_hash
from spine_sim.foundation.errors import ContractViolation
from spine_sim.numerics.contracts import (
    EventAdmissibleSide,
    EventCertificateKind,
    EventDetectionMode,
    M02ReasonCode,
    ResidualKind,
)
from spine_sim.numerics.events import (
    CascadeEvaluation,
    EquilibriumGuardSnapshot,
    EventCascadeEngine,
    EventCoverageDeclaration,
    EventEngine,
    EventSearchRequest,
    OwnerEventEnclosure,
)
from spine_sim.single_spine.contracts import (
    EmbeddedErrorClass,
    EventCandidateResponse,
    FailureAxis,
    ResidualBlockReport,
    SingleSpineTrialResponse,
)
from spine_sim.single_spine.events import (
    M03_SIGNED_EVENT_SPECS,
    M03EventFamily,
    M03EventKind,
    M03EventProbeContext,
    bridge_guard_samples_to_m02,
    bridge_residual_blocks_to_m02,
    bridge_response_to_m02_event_snapshot,
    evaluate_m03_event_post_reassembly,
    m03_event_registrations,
    m03_event_registry,
    m03_event_spec,
    make_m03_coverage_declaration,
    raw_signed_guards_from_response,
)


def digest(value: object) -> str:
    return semantic_hash(value)


@dataclass(frozen=True)
class FakeLinearization:
    branch_id: str = "branch:stick"


@dataclass(frozen=True)
class FakeDiagnostics:
    residual_blocks: tuple[ResidualBlockReport, ...]
    failure_axis: FailureAxis = FailureAxis.NONE
    error_class: EmbeddedErrorClass = EmbeddedErrorClass.OK
    complementarity_residual: float = 0.0
    contact_soc_residual: float = 0.0
    graph_residual: float = 0.0
    geometric_closure_residual_mm: float = 0.0
    beam_residual_mm: float = 0.0
    spring_residual_n: float = 0.0
    work_balance_error_n_mm: float = 0.0


@dataclass(frozen=True)
class FakeStateEvents:
    all_event_candidates: tuple[EventCandidateResponse, ...]
    simultaneous_event_set: tuple[str, ...] = ()
    earliest_event_fraction: float | None = None
    event_fraction_bracket: tuple[float, float] | None = None
    per_contact_motion_states: tuple[str, ...] = ("STICKING_INTERIOR",)
    event_one_sided_consistency: bool = True


@dataclass(frozen=True)
class FakeGeometry:
    query_receipt_ids: tuple[str, ...] = ("m01-query-receipt",)
    tip_center_global_mm: tuple[float, float, float] = (0.0, 0.0, 0.05)
    active_support_ids: tuple[str, ...] = ("support",)
    supports: tuple[str, ...] = ("support-response",)


@dataclass(frozen=True)
class FakeStructure:
    beam_tip_translation_global_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    beam_tip_rotation_global_rad: tuple[float, float, float] = (0.0, 0.0, 0.0)
    spring_compression_mm: float = 0.0
    beam_energy_n_mm: float = 0.0


@dataclass(frozen=True)
class FakeWrench:
    wrench_uniqueness: str = "unique"
    rank: int = 6
    nullspace_basis: tuple[tuple[float, ...], ...] = ()
    admissible_wrench_graph_handle: str | None = None
    force: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class FakeMaterial:
    trial_damage_intents: tuple[str, ...] = ()
    friction_dissipation_trial_n_mm: float = 0.0


@dataclass(frozen=True)
class FakeWork:
    closure_error_n_mm: float = 0.0


@dataclass(frozen=True)
class FakeTransaction:
    request_hash: str
    opaque_trial_state_handle: str
    provisional_commit_intent: str
    accepted_history_version_read: int = 7
    damage_snapshot_version_read: int = 11
    damage_intents: tuple[str, ...] = ()
    damage_write_set: tuple[str, ...] = ()


@dataclass(frozen=True)
class FakeResponse:
    response_id: str
    response_hash: str
    diagnostics: FakeDiagnostics
    state_events: FakeStateEvents
    transaction: FakeTransaction
    linearization: FakeLinearization = FakeLinearization()
    geometry_contact: FakeGeometry = FakeGeometry()
    structure: FakeStructure = FakeStructure()
    wrench: FakeWrench = FakeWrench()
    material_damage: FakeMaterial = FakeMaterial()
    work: FakeWork = FakeWork()


def residual(
    block_id: str = "force_equilibrium",
    *,
    semantics: str = "interface force equilibrium",
    raw_norm: float = 0.01,
    raw_unit: str = "N",
    normalized_norm: float = 0.1,
    passed: bool = True,
) -> ResidualBlockReport:
    return ResidualBlockReport(
        block_id=block_id,
        semantics=semantics,
        raw_norm=raw_norm,
        raw_unit=raw_unit,
        reference_norm=1.0,
        absolute_tolerance=0.02,
        relative_tolerance=0.0,
        scale_id=f"scale:{block_id}",
        normalized_norm=normalized_norm,
        hard=True,
        passed=passed,
    )


def candidate(
    kind: M03EventKind,
    raw_value: float,
    *,
    suffix: str = "0",
) -> EventCandidateResponse:
    spec = m03_event_spec(kind)
    return EventCandidateResponse(
        event_id=f"event:{kind.value}:{suffix}",
        event_kind=kind.value,
        raw_guard=raw_value,
        raw_guard_unit=spec.raw_guard_unit,
        zero_value=spec.zero_level,
        admissible_side=spec.admissible_side.value,
        direction=spec.trigger_direction.value,
        event_fraction=0.5,
        bracket=(0.4, 0.6),
        coverage_certificate_id=f"coverage:{kind.value}",
    )


def fake_response(
    label: str,
    *,
    candidates: tuple[EventCandidateResponse, ...] | None = None,
    residuals: tuple[ResidualBlockReport, ...] | None = None,
    one_sided: bool = True,
    failure_axis: FailureAxis = FailureAxis.NONE,
    error_class: EmbeddedErrorClass = EmbeddedErrorClass.OK,
) -> SingleSpineTrialResponse:
    fake = FakeResponse(
        response_id=f"response:{label}",
        response_hash=digest(("response", label)),
        diagnostics=FakeDiagnostics(
            residuals if residuals is not None else (residual(),),
            failure_axis,
            error_class,
        ),
        state_events=FakeStateEvents(
            candidates
            if candidates is not None
            else (candidate(M03EventKind.TIP_CONTACT_ESTABLISH, 0.0),),
            event_one_sided_consistency=one_sided,
        ),
        transaction=FakeTransaction(
            request_hash=digest(("request", label)),
            opaque_trial_state_handle=f"opaque:{label}",
            provisional_commit_intent=f"intent:{label}",
        ),
    )
    return cast(SingleSpineTrialResponse, fake)


def test_frozen_registry_covers_every_required_family_and_has_no_priority() -> None:
    assert {item.family for item in M03_SIGNED_EVENT_SPECS} == set(M03EventFamily)
    assert len(M03_SIGNED_EVENT_SPECS) == len(M03EventKind) == 32
    assert all(item.event_priority is None for item in M03_SIGNED_EVENT_SPECS)
    registry = m03_event_registry()
    assert len(registry.registrations) == 32

    kinds = {item.kind for item in M03_SIGNED_EVENT_SPECS}
    assert {
        M03EventKind.TIP_CONTACT_ESTABLISH,
        M03EventKind.CONTACT_LOAD_ONSET,
        M03EventKind.CONTACT_RELEASE,
        M03EventKind.FRICTION_CONE_REACHED,
        M03EventKind.SLIP_ONSET_CONFIRMED,
        M03EventKind.SUPPORT_SWITCH,
        M03EventKind.CAP_LEGALITY_LOSS,
        M03EventKind.SPRING_HARD_STOP,
        M03EventKind.CONE_COLLISION,
        M03EventKind.OUT_OF_DOMAIN,
        M03EventKind.GEOMETRY_UNCERTAIN,
        M03EventKind.PRELOAD_TARGET_REACHED,
        M03EventKind.RELEASE_PATH_START,
        M03EventKind.SWEPT_COLLISION,
        M03EventKind.RECONTACT_ZERO_LOAD,
        M03EventKind.REENGAGEMENT,
        M03EventKind.TRAVEL_COMPLETE,
    } <= kinds
    assert not any("MATERIAL" in item.kind.value for item in M03_SIGNED_EVENT_SPECS)
    assert not any("YIELD" in item.kind.value for item in M03_SIGNED_EVENT_SPECS)


def test_registry_keeps_friction_boundary_slip_and_recontact_reengagement_distinct() -> None:
    friction = m03_event_spec(M03EventKind.FRICTION_CONE_REACHED)
    all_stick = m03_event_spec(M03EventKind.ALL_STICK_BRANCH_LOSS)
    slip = m03_event_spec(M03EventKind.SLIP_ONSET_CONFIRMED)
    assert friction.raw_guard_unit == all_stick.raw_guard_unit == "N"
    assert slip.raw_guard_unit == "mm"
    assert all_stick.dependency_predecessors == (M03EventKind.FRICTION_CONE_REACHED,)
    assert set(slip.dependency_predecessors) == {
        M03EventKind.FRICTION_CONE_REACHED,
        M03EventKind.ALL_STICK_BRANCH_LOSS,
    }

    recontact = m03_event_spec(M03EventKind.RECONTACT_ZERO_LOAD)
    reengagement = m03_event_spec(M03EventKind.REENGAGEMENT)
    assert recontact.raw_guard_unit == "mm"
    assert reengagement.raw_guard_unit == "N"
    assert M03EventKind.RELOAD_TARGET_REACHED in reengagement.dependency_predecessors


def test_swept_and_touch_channels_require_their_declared_certificates() -> None:
    collision = m03_event_spec(M03EventKind.SWEPT_COLLISION)
    assert collision.detection_mode is EventDetectionMode.SWEPT_COLLISION
    assert EventCertificateKind.SWEPT_NO_EVENT in collision.certificate_capabilities
    tangency = m03_event_spec(M03EventKind.TIP_CONTACT_TANGENCY)
    assert EventCertificateKind.STATIONARY_TOUCH_ENCLOSURE in tangency.certificate_capabilities
    with pytest.raises(ContractViolation, match="not declared"):
        make_m03_coverage_declaration(
            event_kind=M03EventKind.TIP_CONTACT_TANGENCY,
            certificate_id="wrong",
            certificate_kind=EventCertificateKind.ADAPTIVE_PROBE_SPACING,
            certificate_hash=digest("wrong"),
            complete=True,
            certifies_no_event=False,
            maximum_probe_spacing_mm=0.1,
            raw_guard_zero_tolerance=1.0e-9,
        )


def test_raw_dimensional_guard_rejects_unit_side_and_nonfinite_changes() -> None:
    response = fake_response(
        "guard",
        candidates=(candidate(M03EventKind.CONTACT_LOAD_ONSET, 0.2),),
    )
    guard = raw_signed_guards_from_response(response)[0]
    assert guard.raw_unit == "N"
    assert guard.raw_value == 0.2
    assert guard.on_admissible_side

    original = response.state_events.all_event_candidates[0]
    with pytest.raises(ContractViolation, match="unit changed"):
        raw_signed_guards_from_response(
            fake_response("wrong-unit", candidates=(replace(original, raw_guard_unit="mm"),))
        )
    with pytest.raises(ContractViolation, match="admissible side"):
        raw_signed_guards_from_response(
            fake_response(
                "wrong-side",
                candidates=(replace(original, admissible_side="NONPOSITIVE"),),
            )
        )
    with pytest.raises(ContractViolation, match="NaN/Inf"):
        raw_signed_guards_from_response(
            fake_response("nan", candidates=(replace(original, raw_guard=float("nan")),))
        )


def test_residual_bridge_preserves_native_units_kind_and_normalization() -> None:
    reports = (
        residual(),
        residual(
            "moment_equilibrium",
            semantics="root moment equilibrium",
            raw_norm=0.02,
            raw_unit="N*mm",
            normalized_norm=0.04,
        ),
        residual(
            "contact_graph",
            semantics="rigid Coulomb graph distance",
            raw_norm=0.0,
            raw_unit="1",
            normalized_norm=0.0,
        ),
    )
    blocks = bridge_residual_blocks_to_m02(fake_response("residual", residuals=reports))
    assert tuple(item.kind for item in blocks) == (
        ResidualKind.FORCE_EQUILIBRIUM,
        ResidualKind.MOMENT_EQUILIBRIUM,
        ResidualKind.GRAPH_DISTANCE,
    )
    assert tuple(item.raw_unit for item in blocks) == ("N", "N*mm", "1")
    assert tuple(item.normalized_norm for item in blocks) == pytest.approx((0.1, 0.04, 0.0))
    assert all(item.hard_acceptance for item in blocks)


def test_residual_bridge_rejects_incoherent_scale_or_pass_flag() -> None:
    with pytest.raises(ContractViolation, match="positive normalized"):
        bridge_residual_blocks_to_m02(
            fake_response(
                "bad-scale",
                residuals=(residual(raw_norm=0.01, normalized_norm=0.0),),
            )
        )
    with pytest.raises(ContractViolation, match="pass flag"):
        bridge_residual_blocks_to_m02(
            fake_response(
                "bad-pass",
                residuals=(residual(raw_norm=0.01, normalized_norm=2.0, passed=False),),
            )
        )


def test_guard_bridge_produces_m02_samples_and_fresh_equilibrium_snapshot() -> None:
    response = fake_response(
        "probe",
        candidates=(candidate(M03EventKind.CAP_LEGALITY_LOSS, 0.03),),
    )
    context = M03EventProbeContext(
        trial_id="trial:event-probe",
        oriented_path_position_mm=12.5,
        trial_fraction=0.25,
        coverage_refs=("sweep-coverage",),
        quality_hashes=(digest("quality"),),
        balance_response_hash=digest("balanced-z"),
        balance_recomputed=True,
    )
    samples = bridge_guard_samples_to_m02(response, context)
    assert len(samples) == 1
    assert samples[0].raw_guard_value == 0.03
    assert samples[0].raw_guard_unit == "mm"
    assert samples[0].balance_recomputed
    assert set(samples[0].coverage_refs) == {
        "coverage:CAP_LEGALITY_LOSS",
        "m01-query-receipt",
        "sweep-coverage",
    }
    snapshot = bridge_response_to_m02_event_snapshot(response, context)
    assert snapshot.raw_guard_values == {samples[0].channel_id: 0.03}
    assert snapshot.equilibrium_response_hash == response.response_hash
    assert snapshot.balance_response_hash == digest("balanced-z")


def test_failed_trial_cannot_become_a_legal_event_guard_sample() -> None:
    context = M03EventProbeContext("trial", 0.0, 0.0)
    with pytest.raises(ContractViolation, match="failed M03 trial"):
        bridge_guard_samples_to_m02(
            fake_response("failed", failure_axis=FailureAxis.NUMERICAL_FAILURE),
            context,
        )
    with pytest.raises(ContractViolation, match="failed hard residual"):
        bridge_guard_samples_to_m02(
            fake_response(
                "hard-fail",
                residuals=(residual(raw_norm=2.0, normalized_norm=2.0, passed=False),),
            ),
            context,
        )


@dataclass
class CountingProbe:
    functions: dict[str, Callable[[float], float]]
    units: dict[str, str]
    calls: list[float] = field(default_factory=list)

    def __call__(
        self,
        oriented_path_position_mm: float,
        channel_ids: tuple[str, ...],
    ) -> EquilibriumGuardSnapshot:
        position = oriented_path_position_mm
        self.calls.append(position)
        values = {key: self.functions[key](position) for key in channel_ids}
        return EquilibriumGuardSnapshot(
            oriented_path_position_mm=position,
            raw_guard_values=values,
            raw_guard_units={key: self.units[key] for key in channel_ids},
            equilibrium_quality_passed=True,
            equilibrium_response_hash=digest(("equilibrium", position, values)),
            quality_hashes=(digest(("quality", position, values)),),
            balance_response_hash=None,
            balance_recomputed=False,
            coverage_refs=tuple(f"coverage:{key}" for key in channel_ids),
        )


def adaptive_coverage(
    channel_id: str,
    *,
    spacing: float = 0.05,
) -> EventCoverageDeclaration:
    return EventCoverageDeclaration(
        certificate_id=f"coverage:{channel_id}",
        channel_id=channel_id,
        kind=EventCertificateKind.ADAPTIVE_PROBE_SPACING,
        certificate_hash=digest(("coverage", channel_id, spacing)),
        complete=True,
        certifies_no_event=False,
        maximum_probe_spacing_mm=spacing,
        raw_guard_zero_tolerance=1.0e-9,
    )


def search_request(
    registrations: tuple,
    coverage: tuple[EventCoverageDeclaration, ...],
    *,
    lref: float = 1.0,
) -> EventSearchRequest:
    return EventSearchRequest(
        search_id="m03-search",
        target_id="target",
        trial_id="trial",
        parent_accepted_state_id="accepted-0",
        interval_start_mm=0.0,
        interval_end_mm=1.0,
        characteristic_length_mm=lref,
        channels=registrations,
        coverage=coverage,
    )


def test_m02_finds_same_sign_interior_events_from_m03_raw_guard() -> None:
    registrations = m03_event_registrations((M03EventKind.SPRING_ORIGINAL_LENGTH,))
    registration = registrations[0]
    probe = CountingProbe(
        {registration.channel_id: lambda x: (x - 0.25) * (x - 0.75)},
        {registration.channel_id: "mm"},
    )
    result = EventEngine().search(
        search_request(registrations, (adaptive_coverage(registration.channel_id),)),
        probe,
    )
    assert result.success and result.located_group is not None
    assert len(result.brackets) == 2
    assert result.located_group.oriented_path_position_mm == pytest.approx(0.25, abs=0.01)
    assert len(probe.calls) == len(result.probes)


def test_m02_localizes_m03_touch_only_with_owner_enclosure() -> None:
    registrations = m03_event_registrations((M03EventKind.TIP_CONTACT_TANGENCY,))
    registration = registrations[0]
    enclosure = OwnerEventEnclosure(
        enclosure_id="tangency-enclosure",
        left_position_mm=0.2,
        right_position_mm=0.8,
        touch_candidate=True,
        owner_proof_hash=digest("tangency-owner-proof"),
    )
    coverage = make_m03_coverage_declaration(
        event_kind=M03EventKind.TIP_CONTACT_TANGENCY,
        certificate_id="touch-coverage",
        certificate_kind=EventCertificateKind.STATIONARY_TOUCH_ENCLOSURE,
        certificate_hash=digest("touch-coverage"),
        complete=True,
        certifies_no_event=False,
        maximum_probe_spacing_mm=None,
        raw_guard_zero_tolerance=1.0e-5,
        candidate_enclosures=(enclosure,),
    )
    result = EventEngine().search(
        search_request(registrations, (coverage,)),
        CountingProbe(
            {registration.channel_id: lambda x: (x - 0.5) ** 2},
            {registration.channel_id: "mm"},
        ),
    )
    assert result.success and result.located_group is not None
    assert result.brackets[0].touch_enclosure
    assert result.located_group.oriented_path_position_mm == pytest.approx(0.5, abs=0.01)


def test_m02_simultaneous_group_respects_m03_dependency_dag() -> None:
    registrations = m03_event_registrations((M03EventKind.SLIP_ONSET_CONFIRMED,))
    by_kind = {item.event_kind: item for item in registrations}
    functions = {
        by_kind[M03EventKind.FRICTION_CONE_REACHED.value].channel_id: lambda x: 0.400 - x,
        by_kind[M03EventKind.ALL_STICK_BRANCH_LOSS.value].channel_id: lambda x: 0.405 - x,
        by_kind[M03EventKind.SLIP_ONSET_CONFIRMED.value].channel_id: lambda x: x - 0.407,
    }
    units = {item.channel_id: item.raw_guard_unit for item in registrations}
    result = EventEngine().search(
        search_request(
            registrations,
            tuple(adaptive_coverage(item.channel_id) for item in registrations),
        ),
        CountingProbe(functions, units),
    )
    assert result.success and result.simultaneous_group is not None
    expected = tuple(item.channel_id for item in registrations)
    assert set(result.simultaneous_group.channel_ids) == set(expected)
    order = result.simultaneous_group.canonical_independent_order
    assert order.index(by_kind[M03EventKind.FRICTION_CONE_REACHED.value].channel_id) < order.index(
        by_kind[M03EventKind.ALL_STICK_BRANCH_LOSS.value].channel_id
    )
    assert order.index(by_kind[M03EventKind.ALL_STICK_BRANCH_LOSS.value].channel_id) < order.index(
        by_kind[M03EventKind.SLIP_ONSET_CONFIRMED.value].channel_id
    )


def test_m02_cascade_reregisters_m03_guards_and_preserves_zeno_axis() -> None:
    def progressing(index: int) -> CascadeEvaluation:
        active = ("m03.event.contact_release",) if index < 2 else ()
        return CascadeEvaluation(
            state_hash=digest(("state", index)),
            event_signature_hash=digest(("signature", index)),
            event_channel_ids=active,
            transition_intent_ids=(f"intent:{index}",) if active else (),
            zero_progress_intent_ids=(),
            guard_margin_improvement=float(index + 1),
            equilibrium_response_hash=digest(("response", index)),
        )

    result = EventCascadeEngine().run(
        cascade_id="m03-cascade",
        event_coordinate_mm=0.4,
        evaluate_round=progressing,
    )
    assert result.converged and len(result.rounds) == 2

    repeated_state = digest("repeated-state")

    def stalled(index: int) -> CascadeEvaluation:
        return CascadeEvaluation(
            state_hash=repeated_state,
            event_signature_hash=digest(("signature", index)),
            event_channel_ids=("m03.event.contact_release",),
            transition_intent_ids=(f"intent:{index}",),
            zero_progress_intent_ids=(),
            guard_margin_improvement=0.0,
            equilibrium_response_hash=digest(("response", index)),
        )

    zeno = EventCascadeEngine().run(
        cascade_id="m03-zeno",
        event_coordinate_mm=0.4,
        evaluate_round=stalled,
    )
    assert not zeno.converged
    assert zeno.reason_code is M02ReasonCode.ZENO_CANDIDATE


def test_event_post_uses_distinct_complete_response_reassembly() -> None:
    channel_id = m03_event_spec(M03EventKind.CONTACT_RELEASE).channel_id
    calls = {"pre": 0, "transition": 0, "post": 0}

    def pre_solver(_: float, __: tuple[str, ...]) -> SingleSpineTrialResponse:
        calls["pre"] += 1
        return fake_response(
            "pre",
            candidates=(candidate(M03EventKind.CONTACT_RELEASE, 0.0),),
        )

    def transition(_: tuple[str, ...]) -> tuple[str, ...]:
        calls["transition"] += 1
        return ("intent:release",)

    def post_solver(
        _: float,
        __: tuple[str, ...],
        ___: tuple[str, ...],
    ) -> SingleSpineTrialResponse:
        calls["post"] += 1
        return fake_response("post")

    evidence = evaluate_m03_event_post_reassembly(
        event_coordinate_mm=0.4,
        simultaneous_channel_ids=(channel_id,),
        parent_accepted_state_id="accepted-0",
        pre_solver=pre_solver,
        transition=transition,
        post_solver=post_solver,
    )
    assert calls == {"pre": 1, "transition": 1, "post": 1}
    assert evidence.result.complete_recompute
    assert evidence.pre_response_hash != evidence.post_response_hash
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
    assert {name for name, _ in evidence.result.pre_side.component_hashes} == required
    assert {name for name, _ in evidence.result.post_side.component_hashes} == required


def test_event_post_rejects_old_response_reuse_and_failed_one_sided_gate() -> None:
    channel_id = m03_event_spec(M03EventKind.CONTACT_RELEASE).channel_id
    reused = fake_response(
        "same",
        candidates=(candidate(M03EventKind.CONTACT_RELEASE, 0.0),),
    )
    with pytest.raises(ContractViolation, match="reused the pre-event response"):
        evaluate_m03_event_post_reassembly(
            event_coordinate_mm=0.4,
            simultaneous_channel_ids=(channel_id,),
            parent_accepted_state_id="accepted-0",
            pre_solver=lambda _coordinate, _channels: reused,
            transition=lambda _channels: ("intent:release",),
            post_solver=lambda _coordinate, _channels, _intents: reused,
        )

    with pytest.raises(ContractViolation, match="one-sided consistency"):
        evaluate_m03_event_post_reassembly(
            event_coordinate_mm=0.4,
            simultaneous_channel_ids=(channel_id,),
            parent_accepted_state_id="accepted-0",
            pre_solver=lambda _coordinate, _channels: fake_response(
                "pre-second",
                candidates=(candidate(M03EventKind.CONTACT_RELEASE, 0.0),),
            ),
            transition=lambda _channels: ("intent:release",),
            post_solver=lambda _coordinate, _channels, _intents: fake_response(
                "post-bad-side", one_sided=False
            ),
        )


def test_event_post_accepts_outer_owned_channel_without_forging_intrinsic_guard() -> None:
    channel_id = m03_event_spec(M03EventKind.TRAVEL_COMPLETE).channel_id

    evidence = evaluate_m03_event_post_reassembly(
        event_coordinate_mm=100.0,
        simultaneous_channel_ids=(channel_id,),
        parent_accepted_state_id="accepted-99",
        pre_solver=lambda _coordinate, _channels: fake_response("outer-pre"),
        transition=lambda _channels: ("intent:travel-complete",),
        post_solver=lambda _coordinate, _channels, _intents: fake_response("outer-post"),
    )

    assert evidence.result.complete_recompute
    assert evidence.pre_response_hash != evidence.post_response_hash


def test_event_post_rejects_reduction_request_as_complete_side_evidence() -> None:
    channel_id = m03_event_spec(M03EventKind.CONTACT_RELEASE).channel_id

    with pytest.raises(ContractViolation, match="bracket/retry response"):
        evaluate_m03_event_post_reassembly(
            event_coordinate_mm=0.4,
            simultaneous_channel_ids=(channel_id,),
            parent_accepted_state_id="accepted-0",
            pre_solver=lambda _coordinate, _channels: fake_response(
                "pre-reduction",
                candidates=(candidate(M03EventKind.CONTACT_RELEASE, 0.0),),
                error_class=EmbeddedErrorClass.EVENT_REDUCTION_REQUIRED,
            ),
            transition=lambda _channels: ("intent:release",),
            post_solver=lambda _coordinate, _channels, _intents: fake_response("post"),
        )


def test_subset_registry_includes_dependency_closure() -> None:
    registrations = m03_event_registrations((M03EventKind.REENGAGEMENT,))
    kinds = {item.event_kind for item in registrations}
    assert {
        M03EventKind.RELEASE_PATH_START.value,
        M03EventKind.CONTACT_RELEASE.value,
        M03EventKind.RECONTACT_ZERO_LOAD.value,
        M03EventKind.RELOAD_TARGET_REACHED.value,
        M03EventKind.REENGAGEMENT.value,
    } <= kinds
    reengagement = next(item for item in registrations if item.event_kind == "REENGAGEMENT")
    assert reengagement.admissible_side is EventAdmissibleSide.NONNEGATIVE
