from __future__ import annotations

from dataclasses import replace

import pytest

from spine_sim.foundation.canonical import semantic_hash
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    AttemptOutcome,
    CapabilityStatus,
    CertificationStatus,
    PhysicalFeasibility,
    StatusTuple,
    ValuePresence,
)
from spine_sim.numerics.contracts import (
    CommitReceiptRef,
    ContinuationControlMode,
    ContinuationDirection,
    ContinuationTarget,
    DerivativeCapability,
    DerivativeKind,
    DiagnosticLevel,
    EventAdmissibleSide,
    EventCertificateKind,
    EventChannelRegistration,
    EventDetectionMode,
    EventProbeRequest,
    EventProbeResult,
    EventTriggerDirection,
    FailureDiagnostic,
    FailureFamily,
    M02ReasonCode,
    OpaqueTrialStateRef,
    PhysicalEvaluationRequest,
    PhysicalEvaluationResponse,
    ProvisionalIntent,
    ReductionNorm,
    ResidualBlock,
    ResidualKind,
    ReturnPathCapability,
    ReturnPathMode,
    RollbackToken,
    TrialLifecycleState,
    TrialPhase,
    TrialStep,
    validate_trial_transition,
)


def digest(value: object) -> str:
    return semantic_hash(value)


def make_target(**overrides: object) -> ContinuationTarget:
    values: dict[str, object] = {
        "target_id": "target-1",
        "parent_accepted_state_id": "state-0",
        "parent_commit_receipt_id": "receipt-0",
        "parent_state_hash": digest("state-0"),
        "continuation_coordinate_id": "drag-x",
        "coordinate_unit": "mm",
        "start_value": 0.0,
        "target_value": 100.0,
        "direction": ContinuationDirection.INCREASING,
        "oriented_path_mapping_id": "path-map-1",
        "characteristic_length_mm": 10.0,
        "characteristic_length_source": "owner:Rt",
        "control_mode": ContinuationControlMode.MONOTONE_SCALAR_TARGET,
        "physical_owner_ids": ("synthetic-owner",),
        "required_event_channel_ids": ("event-1",),
        "resolved_numerics_config_id": "config-1",
        "resolved_numerics_config_hash": digest("config-1"),
        "external_dependency_refs": ("surface-1",),
        "request_id": "request-1",
        "request_hash": digest("request-1"),
        "idempotency_namespace": "case-1",
        "metadata_unit": "mm",
    }
    values.update(overrides)
    return ContinuationTarget.create(**values)


def make_channel(**overrides: object) -> EventChannelRegistration:
    values: dict[str, object] = {
        "channel_id": "event-1",
        "owner_id": "owner-1",
        "entity_ids": ("entity-1",),
        "event_kind": "OWNER_DEFINED_CONTACT_RELEASE",
        "guard_id": "guard-1",
        "guard_version": "1.0.0",
        "raw_guard_unit": "N",
        "zero_level": 0.0,
        "admissible_side": EventAdmissibleSide.NONNEGATIVE,
        "trigger_direction": EventTriggerDirection.FALLING,
        "applicability_predicate_id": "applicable-1",
        "branch_state_scope": ("branch-1",),
        "detection_mode": EventDetectionMode.SIGN_CHANGE,
        "no_event_certificate_capabilities": (EventCertificateKind.ADAPTIVE_PROBE_SPACING,),
        "dependency_predecessors": (),
        "transition_owner": "owner-1",
        "post_event_side_request_id": "post-side-1",
        "metadata_unit": "N",
    }
    values.update(overrides)
    return EventChannelRegistration.create(**values)


def test_contract_metadata_is_stable_and_complete() -> None:
    first = make_target()
    second = make_target()
    assert first.semantic_id == second.semantic_id
    assert first.semantic_hash == second.semantic_hash
    assert first.schema_version == "1.0.0"
    assert first.metadata.unit == "mm"
    assert first.metadata.status.reason_code == M02ReasonCode.OK.value
    assert first.metadata.maturity.experimentally_validated.status.value == "BLOCKED_UNAVAILABLE"
    assert first.metadata.certification_status.value == "NOT_CERTIFIABLE"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("start_value", float("nan")),
        ("target_value", float("inf")),
        ("characteristic_length_mm", 0.0),
        ("parent_state_hash", "short"),
        ("coordinate_unit", ""),
        ("physical_owner_ids", ("owner", "owner")),
    ],
)
def test_target_rejects_invalid_scalar_identity_and_unit(field: str, value: object) -> None:
    with pytest.raises(ContractViolation):
        make_target(**{field: value})


def test_target_direction_must_match_oriented_values() -> None:
    with pytest.raises(ContractViolation, match="direction"):
        make_target(direction=ContinuationDirection.DECREASING)


def test_contract_metadata_detects_post_construction_content_tamper() -> None:
    target = make_target()
    with pytest.raises(ContractViolation, match="semantic ID/hash"):
        replace(target, target_value=90.0)


def test_residual_block_preserves_raw_unit_scale_and_hard_gate() -> None:
    block = ResidualBlock.from_values(
        block_id="force-x",
        owner_id="owner",
        kind=ResidualKind.FORCE_EQUILIBRIUM,
        physical_semantics="force equilibrium x",
        raw_values=(1.9e-6,),
        raw_unit="N",
        reduction_norm=ReductionNorm.L2,
        reference_norm=0.1,
        absolute_tolerance=1.0e-6,
        relative_tolerance=1.0e-5,
        scale_id="force-scale",
        scale_value=1.0,
    )
    assert block.raw_norm == pytest.approx(1.9e-6)
    assert block.normalized_norm == pytest.approx(1.9e-6)
    assert block.accepted
    assert block.metadata.unit == "N"


@pytest.mark.parametrize(
    ("raw_values", "scale_value", "raw_unit"),
    [((float("nan"),), 1.0, "N"), ((1.0,), 0.0, "N"), ((1.0,), 1.0, "mm")],
)
def test_residual_block_rejects_nan_missing_scale_and_wrong_unit(
    raw_values: tuple[float, ...], scale_value: float, raw_unit: str
) -> None:
    with pytest.raises(ContractViolation):
        ResidualBlock.from_values(
            block_id="force-x",
            owner_id="owner",
            kind=ResidualKind.FORCE_EQUILIBRIUM,
            physical_semantics="force equilibrium x",
            raw_values=raw_values,
            raw_unit=raw_unit,
            reference_norm=1.0,
            absolute_tolerance=1.0e-6,
            relative_tolerance=1.0e-5,
            scale_id="force-scale",
            scale_value=scale_value,
        )


def test_touch_registration_requires_stationary_enclosure_capability() -> None:
    with pytest.raises(ContractViolation, match="TOUCH"):
        make_channel(
            trigger_direction=EventTriggerDirection.TOUCH,
            detection_mode=EventDetectionMode.SIGN_CHANGE_AND_TOUCH,
        )


def test_derivative_capability_rejects_production_finite_difference() -> None:
    with pytest.raises(ContractViolation, match="finite differences"):
        DerivativeCapability.create(
            capability_id="fd",
            owner_id="fixture",
            owner_version="1",
            kind=DerivativeKind.FINITE_DIFFERENCE_VALIDATION_ONLY,
            nonsmooth_supported=False,
            production_safe=True,
            derivative_hash=digest("fd"),
            branch_scope="validation",
            metadata_unit="1",
        )


def test_receipt_reference_can_only_point_to_m00_core_identity() -> None:
    with pytest.raises(ContractViolation, match="M00 core receipt"):
        CommitReceiptRef.create(
            receipt_id="receipt",
            committed_state_id="state",
            candidate_hash=digest("candidate"),
            commit_marker_hash=digest("marker"),
            core_receipt_dataset_id="m02.receipts",
            metadata_unit="1",
        )


def test_physical_infeasible_requires_owner_proof() -> None:
    with pytest.raises(ContractViolation, match="owner proof"):
        FailureDiagnostic.create(
            failure_id="failure",
            family=FailureFamily.PHYSICAL_INFEASIBLE,
            reason_code=M02ReasonCode.OWNER_PROVEN_PHYSICAL_INFEASIBLE.value,
            stage="quality",
            parent_accepted_state_id="state-0",
            last_valid_state_id="state-0",
            owner_proof_ref=None,
            original_reason_code=None,
            structured_details=(),
            retryable=False,
            metadata_unit="1",
        )


def test_return_path_contract_never_invents_implicit_reset_path() -> None:
    with pytest.raises(ContractViolation, match="non-explicit"):
        ReturnPathCapability.create(
            owner_id="owner",
            release_event_id="release-1",
            mode=ReturnPathMode.HOLD_AT_RELEASE_POSE,
            path_mapping_id="invented-reset",
            pose_path_ref=None,
            swept_geometry_ref=None,
            reason_code="OWNER_HOLD",
            metadata_unit="1",
        )


def test_trial_state_machine_rejects_commit_without_prepare() -> None:
    with pytest.raises(ContractViolation, match="illegal"):
        validate_trial_transition(
            TrialLifecycleState.NUMERICALLY_ELIGIBLE,
            TrialLifecycleState.COMMITTED,
        )


def test_trial_state_machine_accepts_prepare_commit_path() -> None:
    validate_trial_transition(
        TrialLifecycleState.CANDIDATE_FROZEN,
        TrialLifecycleState.PREPARED,
    )
    validate_trial_transition(TrialLifecycleState.PREPARED, TrialLifecycleState.COMMITTED)


def make_event_trial() -> TrialStep:
    return TrialStep.create(
        trial_id="trial-event",
        target_id="target",
        parent_accepted_state_id="state-0",
        phase=TrialPhase.EVENT_PROBE,
        attempt_index=0,
        retry_index=0,
        cascade_round=0,
        requested_coordinate=0.5,
        oriented_path_position_mm=0.5,
        trial_fraction=0.5,
        requested_step_mm=0.5,
        predictor_refs=(),
        branch_request_refs=("branch",),
        event_channel_subset=("event-1",),
        bracket_ref="bracket-1",
        simultaneous_group_ref=None,
        evaluation_cache_key="cache",
        request_hash=digest("trial-event"),
        accepted_state_advanced=False,
        metadata_unit="mm",
    )


def owner_response_status(
    *, physical: PhysicalFeasibility = PhysicalFeasibility.NOT_ASSESSED
) -> StatusTuple:
    return StatusTuple(
        ValuePresence.PRESENT,
        CapabilityStatus.SUPPORTED,
        AttemptOutcome.ACCEPTED,
        physical,
        CertificationStatus.NOT_CERTIFIABLE,
        "OWNER_VALIDATION_RESPONSE",
        "synthetic owner protocol fixture",
    )


def make_physical_response(**overrides: object) -> PhysicalEvaluationResponse:
    trial = make_event_trial()
    opaque = OpaqueTrialStateRef.create(
        state_ref="opaque-state",
        owner_id="owner",
        owner_version="1",
        parent_accepted_state_id="state-0",
        parent_state_hash=digest("state-0"),
        trial_id=trial.trial_id,
        metadata_unit="1",
    )
    rollback = RollbackToken.create(
        token_ref="rollback",
        owner_id="owner",
        run_id="run",
        trial_id=trial.trial_id,
        parent_accepted_state_id="state-0",
        parent_state_hash=digest("state-0"),
        token_version="1",
        metadata_unit="1",
    )
    derivative = DerivativeCapability.create(
        capability_id="derivative",
        owner_id="owner",
        owner_version="1",
        kind=DerivativeKind.GENERALIZED_JACOBIAN,
        nonsmooth_supported=True,
        production_safe=True,
        derivative_hash=digest("derivative"),
        branch_scope="branch",
        metadata_unit="1",
    )
    residual = ResidualBlock.from_values(
        block_id="force",
        owner_id="owner",
        kind=ResidualKind.FORCE_EQUILIBRIUM,
        physical_semantics="force balance",
        raw_values=(0.0,),
        raw_unit="N",
        reference_norm=1.0,
        absolute_tolerance=1.0e-6,
        relative_tolerance=1.0e-5,
        scale_id="force-scale",
        scale_value=1.0,
    )
    intent = ProvisionalIntent.create(
        intent_id="intent",
        owner_id="owner",
        intent_kind="OPAQUE_UPDATE",
        payload_hash=digest("intent"),
        read_set=("state",),
        write_set=("state",),
        dependency_versions=("state-v1",),
        zero_progress=False,
        metadata_unit="1",
    )
    values: dict[str, object] = {
        "response_id": "response",
        "request_id": "evaluation-request",
        "request_hash": digest("evaluation-request"),
        "owner_id": "owner",
        "owner_version": "1",
        "opaque_trial_state_ref": opaque,
        "rollback_token": rollback,
        "unknown_vector": (0.0,),
        "unknown_units": ("mm",),
        "residual_blocks": (residual,),
        "derivative_capability": derivative,
        "hard_inequalities": (),
        "complementarity_qualities": (),
        "graph_qualities": (),
        "guard_samples": (),
        "provisional_intents": (intent,),
        "surface_realization_refs": ("surface",),
        "surface_coverage_refs": ("coverage",),
        "physical_feasibility_proof_ref": None,
        "capability_status": CapabilityStatus.SUPPORTED,
        "status": owner_response_status(),
        "determinism_hash": digest("determinism"),
        "metadata_unit": "1",
    }
    values.update(overrides)
    return PhysicalEvaluationResponse.create(**values)


def test_physical_request_keeps_parent_snapshot_and_trial_immutable() -> None:
    trial = make_event_trial()
    request = PhysicalEvaluationRequest.create(
        request_id="evaluation-request",
        trial_step=trial,
        immutable_parent_snapshot_refs=("state-0", "damage-v1"),
        evaluation_purpose="EVENT_GUARD_PROBE",
        requested_continuation_coordinate=0.5,
        unknown_iterate=(0.0,),
        unknown_units=("mm",),
        active_branch_request_refs=("branch",),
        required_residual_block_ids=("force",),
        required_event_channel_ids=("event-1",),
        required_quality_ids=("graph",),
        dependency_coverage_refs=("coverage",),
        diagnostic_level=DiagnosticLevel.STANDARD,
        replay_decision_context_hash=digest("replay-context"),
        metadata_unit="1",
    )
    assert request.trial_step.accepted_state_advanced is False
    assert request.immutable_parent_snapshot_refs[0] == "state-0"
    with pytest.raises(ContractViolation, match="parent snapshot"):
        PhysicalEvaluationRequest.create(
            request_id="bad",
            trial_step=trial,
            immutable_parent_snapshot_refs=("different-state",),
            evaluation_purpose="EVENT_GUARD_PROBE",
            requested_continuation_coordinate=0.5,
            unknown_iterate=(0.0,),
            unknown_units=("mm",),
            active_branch_request_refs=(),
            required_residual_block_ids=(),
            required_event_channel_ids=("event-1",),
            required_quality_ids=(),
            dependency_coverage_refs=(),
            diagnostic_level=DiagnosticLevel.STANDARD,
            replay_decision_context_hash=digest("bad"),
            metadata_unit="1",
        )


def test_physical_response_rejects_duplicate_ids_owner_and_capability_conflicts() -> None:
    valid = make_physical_response()
    assert valid.opaque_trial_state_ref.owner_id == valid.owner_id
    with pytest.raises(ContractViolation, match="residual block IDs"):
        make_physical_response(residual_blocks=(valid.residual_blocks[0],) * 2)
    wrong_opaque = OpaqueTrialStateRef.create(
        state_ref="opaque-other",
        owner_id="other-owner",
        owner_version="1",
        parent_accepted_state_id="state-0",
        parent_state_hash=digest("state-0"),
        trial_id="trial-event",
        metadata_unit="1",
    )
    with pytest.raises(ContractViolation, match="opaque state owner"):
        make_physical_response(opaque_trial_state_ref=wrong_opaque)
    with pytest.raises(ContractViolation, match="capability axis"):
        make_physical_response(capability_status=CapabilityStatus.UNAVAILABLE)


def test_owner_physical_infeasible_response_requires_versioned_proof() -> None:
    infeasible_status = owner_response_status(physical=PhysicalFeasibility.PHYSICAL_INFEASIBLE)
    with pytest.raises(ContractViolation, match="proof"):
        make_physical_response(status=infeasible_status)
    response = make_physical_response(
        status=infeasible_status,
        physical_feasibility_proof_ref="owner-proof:v1",
    )
    assert response.physical_feasibility_proof_ref == "owner-proof:v1"


def test_event_probe_result_requires_event_phase_and_converged_equilibrium() -> None:
    trial = make_event_trial()
    probe_request = EventProbeRequest.create(
        probe_id="probe",
        trial_step=trial,
        parent_accepted_state_id="state-0",
        branch_ref="branch",
        channel_ids=("event-1",),
        required_equilibrium_quality_ids=("force",),
        coverage_request_refs=("coverage",),
        metadata_unit="mm",
    )
    result = EventProbeResult.create(
        probe_id=probe_request.probe_id,
        request_hash=probe_request.semantic_hash,
        trial_id=trial.trial_id,
        oriented_path_position_mm=0.5,
        trial_fraction=0.5,
        equilibrium_response_hash=digest("equilibrium"),
        equilibrium_quality_passed=True,
        guard_samples=(),
        coverage_certificate_refs=("coverage",),
        metadata_unit="mm",
    )
    assert result.equilibrium_quality_passed
    with pytest.raises(ContractViolation, match="illegal"):
        EventProbeResult.create(
            probe_id="bad",
            request_hash=digest("bad"),
            trial_id=trial.trial_id,
            oriented_path_position_mm=0.5,
            trial_fraction=0.5,
            equilibrium_response_hash=digest("equilibrium"),
            equilibrium_quality_passed=False,
            guard_samples=(),
            coverage_certificate_refs=(),
            metadata_unit="mm",
        )
