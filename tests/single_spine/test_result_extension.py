from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest

from spine_sim.foundation.canonical import semantic_hash
from spine_sim.foundation.demo_validation_only import (
    DEMO_CASE_ID,
    DEMO_DESIGN_ID,
    DEMO_SEED_ID,
    DEMO_SURFACE_ID,
    _point,
    _resolved_config,
)
from spine_sim.foundation.errors import ContractViolation, QueryError
from spine_sim.foundation.evolution import MissingFieldAdapter, assess_compatibility
from spine_sim.foundation.integrity import VerifyMode, committed_markers, verify_bundle
from spine_sim.foundation.models import (
    AttemptOutcome,
    CapabilityStatus,
    CertificationStatus,
    CommittedEventBase,
    Maturity,
    PhysicalFeasibility,
    RecordBase,
    RejectedTrialBase,
    SourceIdentity,
    StatusTuple,
    ValuePresence,
)
from spine_sim.foundation.reader import JoinSpec, ResultReader
from spine_sim.foundation.registry import (
    CompatibilityClass,
    DataClassification,
    DatasetClass,
    SchemaRegistry,
)
from spine_sim.foundation.writer import ResultWriter, make_run_envelope
from spine_sim.single_spine.plot_recipes import (
    M03_FROZEN_RECIPE_IDS,
    build_plot_recipe_manifest_records,
)
from spine_sim.single_spine.result_extension import (
    ACCEPTED_STATE_HISTORY_DATASET,
    CAPABILITY_STATUS_DATASET,
    COMMITTED_EVENT_PAYLOADS_DATASET,
    CONTACT_CYCLE_RECORDS_DATASET,
    CONTACT_SUPPORT_HISTORY_DATASET,
    CORE_ACCEPTED_POINTS_DATASET,
    CORE_COMMIT_RECEIPTS_DATASET,
    CORE_COMMITTED_EVENTS_DATASET,
    CORE_REJECTED_TRIALS_DATASET,
    DERIVED_SUMMARIES_DATASET,
    M03_DATASET_IDS,
    M03_EXTENSION_SCHEMA_VERSION,
    PLOT_RECIPE_MANIFEST_DATASET,
    REJECTED_DIAGNOSTICS_DATASET,
    RELEASE_OPERATION_HISTORY_DATASET,
    RUN_REQUESTS_DATASET,
    SUPPORT_CANDIDATE_HISTORY_DATASET,
    WORK_LEDGER_DATASET,
    AcceptedStateHistoryRecord,
    CapabilityStatusRecord,
    CommittedEventPayloadRecord,
    ContactCycleRecord,
    ContactSupportHistoryRecord,
    DerivedSummaryRecord,
    PlotRecipeManifestRecord,
    RejectedDiagnosticRecord,
    ReleaseOperationHistoryRecord,
    RunRequestRecord,
    SupportCandidateHistoryRecord,
    WorkLedgerRecord,
    m03_dataset_ids,
    m03_field_metadata,
    m03_result_extension,
)
from spine_sim.single_spine.summaries import build_m03_summaries

POINT_ID = "point:m03-result-extension"
PARENT_POINT_ID = "point:m03-parent"
PARENT_STATE_ID = "state:m03-parent"
ACCEPTED_STATE_ID = "state:m03-accepted"
EVENT_ID = "event:m03-release"
TRIAL_ID = "trial:m03-rejected"

EXPECTED_CLASSES = {
    RUN_REQUESTS_DATASET: DatasetClass.TRANSACTION,
    ACCEPTED_STATE_HISTORY_DATASET: DatasetClass.ACCEPTED,
    SUPPORT_CANDIDATE_HISTORY_DATASET: DatasetClass.ACCEPTED,
    CONTACT_SUPPORT_HISTORY_DATASET: DatasetClass.ACCEPTED,
    COMMITTED_EVENT_PAYLOADS_DATASET: DatasetClass.EVENT,
    RELEASE_OPERATION_HISTORY_DATASET: DatasetClass.EVENT,
    REJECTED_DIAGNOSTICS_DATASET: DatasetClass.REJECTED,
    WORK_LEDGER_DATASET: DatasetClass.ACCEPTED,
    CONTACT_CYCLE_RECORDS_DATASET: DatasetClass.EVENT,
    CAPABILITY_STATUS_DATASET: DatasetClass.ACCEPTED,
    DERIVED_SUMMARIES_DATASET: DatasetClass.SUMMARY,
    PLOT_RECIPE_MANIFEST_DATASET: DatasetClass.SUMMARY,
}

EXPECTED_PRIMARY_KEYS = {
    RUN_REQUESTS_DATASET: ("request_id",),
    ACCEPTED_STATE_HISTORY_DATASET: ("state_record_id",),
    SUPPORT_CANDIDATE_HISTORY_DATASET: ("candidate_record_id",),
    CONTACT_SUPPORT_HISTORY_DATASET: ("contact_record_id",),
    COMMITTED_EVENT_PAYLOADS_DATASET: ("event_payload_id",),
    RELEASE_OPERATION_HISTORY_DATASET: ("operation_record_id",),
    REJECTED_DIAGNOSTICS_DATASET: ("diagnostic_id",),
    WORK_LEDGER_DATASET: ("work_ledger_id",),
    CONTACT_CYCLE_RECORDS_DATASET: ("cycle_record_id",),
    CAPABILITY_STATUS_DATASET: ("capability_record_id",),
    DERIVED_SUMMARIES_DATASET: ("summary_id",),
    PLOT_RECIPE_MANIFEST_DATASET: ("recipe_id",),
}

EXPECTED_SHAPES = {
    "base_position_global_mm": (3,),
    "base_rotation_global_from_base": (3, 3),
    "root_position_global_mm": (3,),
    "tip_center_global_mm": (3,),
    "a0_global": (3,),
    "a_t_global": (3,),
    "global_from_local": (3, 3),
    "local_from_global": (3, 3),
    "wrench_a_on_b_global_at_o_n_n_mm": (6,),
    "opposite_wrench_b_on_a_global_at_o_n_n_mm": (6,),
    "task_direction_global": (3,),
    "beam_tip_translation_global_mm": (3,),
    "beam_tip_rotation_global_rad": (3,),
    "beam_tip_translation_needle_mm": (3,),
    "beam_tip_rotation_needle_rad": (3,),
    "beam_root_force_global_n": (3,),
    "beam_root_moment_global_n_mm": (3,),
    "section_resultants_needle_n_n_mm": (6,),
    "candidate_point_global_mm": (3,),
    "point_global_mm": (3,),
    "normal_global": (3,),
    "tangent_1_global": (3,),
    "tangent_2_global": (3,),
    "tangential_multiplier_n": (2,),
    "contact_force_global_n": (3,),
    "objective_slip_increment_global_mm": (3,),
    "objective_slip_increment_local_mm": (2,),
    "pre_wrench_global_at_o_n_n_mm": (6,),
    "event_wrench_global_at_o_n_n_mm": (6,),
    "post_wrench_global_at_o_n_n_mm": (6,),
}


def _status(*, rejected: bool = False) -> StatusTuple:
    return StatusTuple(
        ValuePresence.NULL if rejected else ValuePresence.PRESENT,
        CapabilityStatus.SUPPORTED,
        AttemptOutcome.REJECTED_TRIAL if rejected else AttemptOutcome.ACCEPTED,
        PhysicalFeasibility.NOT_ASSESSED if rejected else PhysicalFeasibility.FEASIBLE,
        CertificationStatus.NOT_CERTIFIABLE,
        "M03_REJECTED_FIXTURE" if rejected else "M03_ACCEPTED_FIXTURE",
        "Deterministic M03 result-extension fixture.",
        last_valid_state_id=PARENT_STATE_ID if rejected else None,
    )


def _unavailable_status() -> StatusTuple:
    return StatusTuple(
        ValuePresence.NULL,
        CapabilityStatus.UNAVAILABLE,
        AttemptOutcome.NOT_ATTEMPTED,
        PhysicalFeasibility.NOT_ASSESSED,
        CertificationStatus.NOT_CERTIFIABLE,
        "OPERATION_SPEED_NOT_DECLARED",
        "Physical return-operation time is intentionally unavailable.",
    )


def _shape_value(shape: tuple[int, ...], offset: float = 0.0) -> Any:
    if len(shape) == 1:
        return tuple(float(index + 1) / 10.0 + offset for index in range(shape[0]))
    if len(shape) == 2:
        return tuple(
            tuple(float(row * shape[1] + column + 1) / 10.0 + offset for column in range(shape[1]))
            for row in range(shape[0])
        )
    raise AssertionError(shape)


def _sample_value(field: dataclasses.Field[Any]) -> Any:
    annotation = str(field.type)
    if field.name == "schema_version":
        return M03_EXTENSION_SCHEMA_VERSION
    if field.name == "status":
        return _status()
    if field.name == "source_identity":
        return SourceIdentity.DEV_POLICY
    if field.name == "maturity":
        return Maturity.validation_only_implemented()
    if field.name == "certification_status":
        return CertificationStatus.NOT_CERTIFIABLE
    if field.name in EXPECTED_SHAPES:
        return _shape_value(EXPECTED_SHAPES[field.name])
    if "StatusTuple" in annotation:
        return _unavailable_status()
    if annotation == "None" or "None" in annotation:
        return None
    if annotation == "bool":
        return False
    if annotation == "float":
        return 0.125
    if annotation == "int":
        return 0
    if "tuple" in annotation:
        return ()
    if "dict" in annotation:
        return {"fixture": "M03_VALIDATION_ONLY"}
    return f"fixture:{field.name}"


def _sample_record(
    record_type: type[RecordBase],
    *,
    run_id: str = "run:m03-result-extension",
    **overrides: Any,
) -> RecordBase:
    values = {field.name: _sample_value(field) for field in dataclasses.fields(record_type)}
    values.update(
        run_id=run_id,
        case_id=DEMO_CASE_ID,
        schema_version=M03_EXTENSION_SCHEMA_VERSION,
        status=_status(),
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=Maturity.validation_only_implemented(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
    )

    if record_type is RunRequestRecord:
        values.update(
            request_id="request:m03-result-extension",
            surface_realization_id=DEMO_SURFACE_ID,
            resolved_request_payload={"fixture": "M03_VALIDATION_ONLY"},
            commit_receipt_id=None,
        )
    elif record_type is AcceptedStateHistoryRecord:
        values.update(
            state_record_id="state-record:m03-result-extension",
            point_id=POINT_ID,
            parent_point_id=PARENT_POINT_ID,
            accepted_state_id=ACCEPTED_STATE_ID,
            parent_accepted_state_id=PARENT_STATE_ID,
            commit_receipt_id=None,
            surface_realization_id=DEMO_SURFACE_ID,
            accepted_point_index=0,
            x_total_mm=0.0,
            drag_elapsed_time_s=0.0,
            operation_path_coordinate_mm=0.0,
            cycle_id="cycle:0",
            active_candidate_ids=("candidate:0",),
            active_support_ids=("support:0",),
            contact_motion_states=("STICK",),
            geometric_candidate=True,
            loaded_contact=True,
            frictionally_stable=True,
            load_bearing=True,
            failure_prediction_allowed=False,
            damage_status="NOT_APPLICABLE_NO_DAMAGE_MODEL",
            strength_status="NEEDLE_STRENGTH_UNAVAILABLE",
            experimentally_validated="NOT_ASSESSED",
            not_certifiable=True,
        )
    elif record_type is SupportCandidateHistoryRecord:
        values.update(
            candidate_record_id="candidate-record:0",
            point_id=POINT_ID,
            commit_receipt_id=None,
            candidate_id="candidate:0",
            support_id="support:0",
            finite_cap_legal=True,
            coverage_certified=True,
            rejection_reason=None,
        )
    elif record_type is ContactSupportHistoryRecord:
        values.update(
            contact_record_id="contact-record:0",
            point_id=POINT_ID,
            commit_receipt_id=None,
            candidate_id="candidate:0",
            support_id="support:0",
            active=True,
            motion_state="STICK",
        )
    elif record_type is CommittedEventPayloadRecord:
        values.update(
            event_payload_id="event-payload:m03-release",
            event_id=EVENT_ID,
            commit_receipt_id=None,
            event_kind="RELEASE",
            cycle_id="cycle:0",
            path_coordinate_mm=0.0,
            support_ids=("support:0",),
            released_recoverable_energy_n_mm=0.0,
            one_sided_consistency=True,
        )
    elif record_type is ReleaseOperationHistoryRecord:
        values.update(
            operation_record_id="operation-record:m03-release",
            point_id=POINT_ID,
            commit_receipt_id=None,
            event_id=EVENT_ID,
            cycle_id="cycle:0",
            path_coordinate_mm=0.0,
            x_total_mm=0.0,
            physical_operation_time_s=None,
            physical_operation_time_status=_unavailable_status(),
            quality_gate_passed=True,
        )
    elif record_type is RejectedDiagnosticRecord:
        values.update(
            status=_status(rejected=True),
            diagnostic_id="diagnostic:m03-rejected",
            trial_id=TRIAL_ID,
            parent_point_id=POINT_ID,
            parent_accepted_state_id=ACCEPTED_STATE_ID,
            reason_code="M03_INTENTIONAL_REJECTED_TRIAL",
            accepted_state_advanced=False,
            path_advanced=False,
            time_advanced=False,
            slip_advanced=False,
            work_advanced=False,
            cycle_advanced=False,
            event_history_advanced=False,
        )
    elif record_type is WorkLedgerRecord:
        values.update(
            work_ledger_id="work-ledger:0",
            start_point_id=POINT_ID,
            end_point_id=POINT_ID,
            commit_receipt_id=None,
            accepted_interval_index=0,
            rigid_contact_energy_n_mm=0.0,
            friction_dissipation_n_mm=0.25,
            material_dissipation_n_mm=0.0,
            returned_recoverable_energy_n_mm=0.125,
        )
    elif record_type is ContactCycleRecord:
        values.update(
            cycle_record_id="cycle-record:0",
            cycle_id="cycle:0",
            start_point_id=POINT_ID,
            end_point_id=POINT_ID,
            commit_receipt_id=None,
            support_ids=("support:0",),
            release_event_id=EVENT_ID,
            recontact_event_id=None,
            reengagement_event_id=None,
            start_x_total_mm=0.0,
            end_x_total_mm=0.0,
            start_drag_elapsed_time_s=0.0,
            end_drag_elapsed_time_s=0.0,
            right_censored=True,
        )
    elif record_type is CapabilityStatusRecord:
        values.update(
            capability_record_id="capability-record:no-damage",
            capability_id="NO_DAMAGE_AND_STRENGTH_UNAVAILABLE",
            capability_state="NOT_APPLICABLE",
            reason_code="NEEDLE_STRENGTH_UNAVAILABLE",
            material_model_id="no_damage",
            material_substate="NO_DAMAGE_MODEL",
            strength_substate="NEEDLE_STRENGTH_UNAVAILABLE",
            failure_prediction_allowed=False,
            damage_intents=(),
            damage_write_set=(),
            initiation_utilization=None,
            current_capacity_scale=None,
            fracture_energy_n_per_mm=None,
            yield_margin=None,
            fracture_margin=None,
            experimentally_validated="NOT_ASSESSED",
            not_certifiable=True,
            commit_receipt_id=None,
        )
    elif record_type is DerivedSummaryRecord:
        values.update(
            summary_id="summary:m03-result-extension",
            summary_kind="M03_DESCRIPTIVE_SUMMARY",
            included_dataset_classes=("accepted", "event"),
            definition_id="m03.summary.fixture",
            definition_version="1.0.0",
            input_accepted_point_ids=(POINT_ID,),
            input_raw_links=(f"{ACCEPTED_STATE_HISTORY_DATASET}#state-record",),
            right_censored=False,
            summary_payload={"descriptive_only": True},
        )
    elif record_type is PlotRecipeManifestRecord:
        values.update(
            summary_id="summary:m03-recipe-fixture",
            summary_kind="M03_PLOT_RECIPE_MANIFEST",
            included_dataset_classes=("accepted", "event"),
            recipe_id="m03.recipe.fixture",
            recipe_family="fixture",
            recipe_version="1.0.0",
            field_ids=(f"{ACCEPTED_STATE_HISTORY_DATASET}.x_total_mm",),
            grouping_fields=("case_id",),
            filter_fields=("case_id",),
            event_kinds=("RELEASE",),
            raw_dataset_links=(ACCEPTED_STATE_HISTORY_DATASET,),
            rejected_opt_in=True,
            smoothing="NONE",
            recipe_payload={"read_only": True},
        )
    values.update(overrides)
    return record_type(**values)


def _core_event(run_id: str, point_id: str) -> CommittedEventBase:
    return CommittedEventBase(
        event_id=EVENT_ID,
        source_event_ids=("m03:release-guard",),
        hierarchy="M03_SINGLE_SPINE",
        entity_ids=("spine:0",),
        run_id=run_id,
        case_id=DEMO_CASE_ID,
        design_id=DEMO_DESIGN_ID,
        seed_id=DEMO_SEED_ID,
        surface_realization_id=DEMO_SURFACE_ID,
        event_kind="RELEASE",
        raw_event_function=0.0,
        event_function_unit="N",
        numerical_scaling_id="m03:force-resolution",
        path_coordinate=0.0,
        path_bracket=(0.0, 0.0),
        fraction_basis="x_total_mm",
        localization_error=0.0,
        pre_event_accepted_state_id=PARENT_STATE_ID,
        event_point_trial_id="trial:m03-event-point",
        post_event_accepted_state_id=ACCEPTED_STATE_ID,
        post_event_status=_status(),
        simultaneous_group_id="simultaneous-group:m03-release",
        dependency_edges=(),
        cascade_round=0,
        pre_payload_refs=(f"{ACCEPTED_STATE_HISTORY_DATASET}#{point_id}",),
        event_payload_refs=(f"{COMMITTED_EVENT_PAYLOADS_DATASET}#event-payload",),
        post_payload_refs=(f"{ACCEPTED_STATE_HISTORY_DATASET}#{point_id}",),
        uncertainty_refs=(),
        recoverability="LIFT_OFF_RESEARCH_V1_OR_HOLD",
        stability="ONE_SIDED_CONSISTENT",
        terminal_classification="NON_TERMINAL_RELEASE",
        status=_status(),
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=Maturity.validation_only_implemented(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        committed=True,
        commit_receipt_id=None,
    )


def _core_rejected(run_id: str) -> RejectedTrialBase:
    return RejectedTrialBase(
        trial_id=TRIAL_ID,
        run_id=run_id,
        case_id=DEMO_CASE_ID,
        parent_accepted_state_id=ACCEPTED_STATE_ID,
        request_hash=semantic_hash("m03-rejected-request"),
        candidate_hash=semantic_hash("m03-rejected-candidate"),
        requested_path_target=0.5,
        status=_status(rejected=True),
        reason_codes=("M03_INTENTIONAL_REJECTED_TRIAL",),
        diagnostic_summary="Intentional M03 rejected-trial isolation fixture.",
        optional_full_payload_ref="diagnostic-payload:m03-rejected",
        last_valid_state_id=ACCEPTED_STATE_ID,
        source_identity=SourceIdentity.DEV_POLICY,
    )


def _open_writer(root: Path) -> tuple[ResultWriter, str, dict[str, str]]:
    registry = SchemaRegistry()
    registry.register_extension(m03_result_extension())
    registry_hash = registry.freeze()
    resolved = _resolved_config("m03-result-extension-run")
    source_hashes = {"M03": semantic_hash("m03-result-extension-authority")}
    envelope = make_run_envelope(
        registry_hash=registry_hash,
        resolved_run_config=resolved,
        operation_kind="M03_VALIDATION_ONLY",
        operation_profile="M03_RESULT_EXTENSION_ROUNDTRIP",
        source_file_hashes=source_hashes,
        replay_manifest={"fixture": "M03_RESULT_EXTENSION"},
        git_commit="TEST",
        dirty_status="clean",
        provenance_labels=("VALIDATION_ONLY",),
    )
    writer = ResultWriter.create_run_bundle(root, registry=registry, run_envelope=envelope)
    writer.write_resolved_config_and_provenance(
        resolved,
        provenance={"source_identity": "VALIDATION_ONLY"},
        replay_manifest={"fixture": "M03_RESULT_EXTENSION"},
    )
    writer.create_case_shard(
        DEMO_CASE_ID,
        design_id=DEMO_DESIGN_ID,
        seed_id=DEMO_SEED_ID,
        surface_realization_id=DEMO_SURFACE_ID,
        resolved_case_config=_resolved_config("m03-result-extension-case"),
    )
    return writer, registry_hash, source_hashes


@dataclass(frozen=True, slots=True)
class M03BundleFixture:
    path: Path
    registry_hash: str
    receipt_id: str
    committed_records: dict[str, RecordBase]
    summary_ids: tuple[str, ...]
    recipe_ids: tuple[str, ...]


@pytest.fixture(scope="module")
def m03_result_bundle(tmp_path_factory: pytest.TempPathFactory) -> M03BundleFixture:
    root = tmp_path_factory.mktemp("m03-result-extension") / "m03.spine-result"
    writer, registry_hash, source_hashes = _open_writer(root)
    point = dataclasses.replace(
        _point(
            writer.run_envelope.run_id,
            0,
            PARENT_STATE_ID,
            ACCEPTED_STATE_ID,
            source_hashes,
        ),
        physical_time_value=0.0,
        physical_time_status=_status(),
    )
    core_event = _core_event(writer.run_envelope.run_id, point.point_id)

    run_request = _sample_record(RunRequestRecord, run_id=writer.run_envelope.run_id)
    accepted = _sample_record(
        AcceptedStateHistoryRecord,
        run_id=writer.run_envelope.run_id,
        point_id=point.point_id,
    )
    candidate = _sample_record(
        SupportCandidateHistoryRecord,
        run_id=writer.run_envelope.run_id,
        point_id=point.point_id,
    )
    contact = _sample_record(
        ContactSupportHistoryRecord,
        run_id=writer.run_envelope.run_id,
        point_id=point.point_id,
    )
    work = _sample_record(
        WorkLedgerRecord,
        run_id=writer.run_envelope.run_id,
        start_point_id=point.point_id,
        end_point_id=point.point_id,
    )
    capability = _sample_record(CapabilityStatusRecord, run_id=writer.run_envelope.run_id)
    event_payload = _sample_record(
        CommittedEventPayloadRecord,
        run_id=writer.run_envelope.run_id,
        event_id=core_event.event_id,
    )
    release_operation = _sample_record(
        ReleaseOperationHistoryRecord,
        run_id=writer.run_envelope.run_id,
        point_id=point.point_id,
        event_id=core_event.event_id,
    )
    cycle = _sample_record(
        ContactCycleRecord,
        run_id=writer.run_envelope.run_id,
        start_point_id=point.point_id,
        end_point_id=point.point_id,
        release_event_id=core_event.event_id,
    )

    transaction = writer.begin_transaction(DEMO_CASE_ID, PARENT_STATE_ID, "m03-result-extension")
    transaction.stage_accepted_point(point, accepted, candidate, contact, work, capability)
    transaction.stage_committed_events(core_event, event_payload, release_operation, cycle)
    transaction.stage_transaction_records(run_request)
    transaction.prepare()
    receipt = transaction.commit()

    committed_records = {
        record.__dataset_id__: dataclasses.replace(record, commit_receipt_id=receipt.receipt_id)
        for record in (
            run_request,
            accepted,
            candidate,
            contact,
            work,
            capability,
            event_payload,
            release_operation,
            cycle,
        )
    }
    committed_accepted = committed_records[ACCEPTED_STATE_HISTORY_DATASET]
    committed_event = committed_records[COMMITTED_EVENT_PAYLOADS_DATASET]
    committed_cycle = committed_records[CONTACT_CYCLE_RECORDS_DATASET]
    committed_work = committed_records[WORK_LEDGER_DATASET]
    assert isinstance(committed_accepted, AcceptedStateHistoryRecord)
    assert isinstance(committed_event, CommittedEventPayloadRecord)
    assert isinstance(committed_cycle, ContactCycleRecord)
    assert isinstance(committed_work, WorkLedgerRecord)
    summaries = build_m03_summaries(
        (committed_accepted,),
        committed_events=(committed_event,),
        contact_cycles=(committed_cycle,),
        work_ledger=(committed_work,),
    )
    for summary in summaries:
        writer.write_versioned_summary(summary)
    recipes = build_plot_recipe_manifest_records(
        run_id=writer.run_envelope.run_id,
        case_id=DEMO_CASE_ID,
    )
    for recipe in recipes:
        writer.write_versioned_summary(recipe)

    rejected = _sample_record(
        RejectedDiagnosticRecord,
        run_id=writer.run_envelope.run_id,
        trial_id=TRIAL_ID,
        parent_point_id=point.point_id,
    )
    writer.record_rejected_trial(
        _core_rejected(writer.run_envelope.run_id),
        extension_records=(rejected,),
    )
    writer.finalize_case(DEMO_CASE_ID)
    writer.publish_run_manifest()
    assert verify_bundle(writer.root, VerifyMode.FULL).passed
    return M03BundleFixture(
        writer.root,
        registry_hash,
        receipt.receipt_id,
        committed_records,
        tuple(item.summary_id for item in summaries),
        tuple(item.recipe_id for item in recipes),
    )


def test_exact_twelve_dataset_contract_classes_visibility_and_common_keys() -> None:
    descriptor = m03_result_extension()
    assert descriptor.namespace == "m03"
    assert descriptor.owner_module == "M03"
    assert descriptor.extension_schema_version == M03_EXTENSION_SCHEMA_VERSION
    assert descriptor.common_keys == ("run_id", "case_id")
    assert descriptor.arrays == ()
    assert descriptor.compatibility_class is CompatibilityClass.ADDITIVE_MINOR
    assert descriptor.source_identity is SourceIdentity.DEV_POLICY
    assert tuple(item.dataset_id for item in descriptor.tables) == M03_DATASET_IDS
    assert m03_dataset_ids() == M03_DATASET_IDS
    assert len(descriptor.tables) == 12
    assert {item.dataset_id: item.dataset_class for item in descriptor.tables} == EXPECTED_CLASSES
    assert {
        item.dataset_id: item.primary_keys for item in descriptor.tables
    } == EXPECTED_PRIMARY_KEYS
    assert all(item.partition_keys == ("case_id",) for item in descriptor.tables)
    assert all(
        item.default_visible is (item.dataset_id != REJECTED_DIAGNOSTICS_DATASET)
        for item in descriptor.tables
    )
    for dataset in descriptor.tables:
        local_fields = {item.field_id.rsplit(".", 1)[-1] for item in dataset.fields}
        assert {"run_id", "case_id"} <= local_fields


def test_every_field_has_complete_metadata_and_all_vectors_are_declared_numeric() -> None:
    descriptor = m03_result_extension()
    expected_classification = {
        DatasetClass.ACCEPTED: DataClassification.CANONICAL_RAW,
        DatasetClass.EVENT: DataClassification.CANONICAL_RAW,
        DatasetClass.TRANSACTION: DataClassification.CANONICAL_RAW,
        DatasetClass.REJECTED: DataClassification.DIAGNOSTIC,
        DatasetClass.SUMMARY: DataClassification.DERIVED,
    }
    seen_shaped_names: set[str] = set()
    for dataset in descriptor.tables:
        assert dataset.namespace == "m03"
        assert dataset.owner_module == "M03"
        assert dataset.schema_version == M03_EXTENSION_SCHEMA_VERSION
        assert dataset.source_identity is SourceIdentity.DEV_POLICY
        for field in dataset.fields:
            local_name = field.field_id.rsplit(".", 1)[-1]
            assert field.namespace == "m03"
            assert field.owner_module == "M03"
            assert field.semantics
            assert field.classification is expected_classification[dataset.dataset_class]
            assert field.dtype in {"float64", "int64", "bool", "utf8"}
            assert field.raggedness
            assert field.unit
            assert field.frame
            assert field.reference_point
            assert field.sign_semantics
            assert field.action_semantics
            assert field.indices[:2] == ("run_id", "case_id")
            assert field.sampling_cadence
            assert field.storage_frequency
            assert field.ownership
            assert field.null_policy
            assert field.source_identity is SourceIdentity.DEV_POLICY
            assert field.authority_refs
            assert field.maturity.theory_defined.status
            assert field.maturity.code_implemented.status
            assert field.maturity.numerically_verified.status
            assert field.maturity.experimentally_validated.status
            assert field.introduced_version == M03_EXTENSION_SCHEMA_VERSION
            assert field.deprecated_version is None
            assert field.storage_dataset == dataset.dataset_id
            assert field.encoding == "parquet_zstd_lossless"
            assert field.precision
            if field.shape:
                seen_shaped_names.add(local_name)
                assert field.shape == EXPECTED_SHAPES[local_name]
                assert field.dtype == "float64"
                assert len(field.dimensions) == len(field.shape)
                assert field.raggedness == "fixed_shape"
                assert field.precision == "float64"
            else:
                assert field.dimensions == ()
            assert m03_field_metadata(field.field_id) == field
    assert seen_shaped_names == set(EXPECTED_SHAPES)


def test_all_twelve_representative_record_types_validate_against_frozen_registry() -> None:
    descriptor = m03_result_extension()
    registry = SchemaRegistry()
    registry.register_extension(descriptor)
    registry.freeze()
    assert {item.record_type for item in descriptor.tables} == {
        RunRequestRecord,
        AcceptedStateHistoryRecord,
        SupportCandidateHistoryRecord,
        ContactSupportHistoryRecord,
        CommittedEventPayloadRecord,
        ReleaseOperationHistoryRecord,
        RejectedDiagnosticRecord,
        WorkLedgerRecord,
        ContactCycleRecord,
        CapabilityStatusRecord,
        DerivedSummaryRecord,
        PlotRecipeManifestRecord,
    }
    for dataset in descriptor.tables:
        assert dataset.record_type is not None
        record = _sample_record(dataset.record_type)
        assert registry.validate_record(record) is dataset
        assert set(registry.storage_dict(record)) == {
            item.field_id.rsplit(".", 1)[-1] for item in dataset.fields
        }


def test_registry_relations_and_hash_are_exact_and_deterministic() -> None:
    expected_relations = {
        "m03.relation.accepted_state_to_point": (
            ACCEPTED_STATE_HISTORY_DATASET,
            CORE_ACCEPTED_POINTS_DATASET,
            ("point_id",),
            ("point_id",),
        ),
        "m03.relation.candidate_to_point": (
            SUPPORT_CANDIDATE_HISTORY_DATASET,
            CORE_ACCEPTED_POINTS_DATASET,
            ("point_id",),
            ("point_id",),
        ),
        "m03.relation.contact_to_point": (
            CONTACT_SUPPORT_HISTORY_DATASET,
            CORE_ACCEPTED_POINTS_DATASET,
            ("point_id",),
            ("point_id",),
        ),
        "m03.relation.event_payload_to_event": (
            COMMITTED_EVENT_PAYLOADS_DATASET,
            CORE_COMMITTED_EVENTS_DATASET,
            ("event_id",),
            ("event_id",),
        ),
        "m03.relation.rejected_to_trial": (
            REJECTED_DIAGNOSTICS_DATASET,
            CORE_REJECTED_TRIALS_DATASET,
            ("trial_id",),
            ("trial_id",),
        ),
        "m03.relation.work_to_end_point": (
            WORK_LEDGER_DATASET,
            CORE_ACCEPTED_POINTS_DATASET,
            ("end_point_id",),
            ("point_id",),
        ),
        "m03.relation.accepted_state_to_receipt": (
            ACCEPTED_STATE_HISTORY_DATASET,
            CORE_COMMIT_RECEIPTS_DATASET,
            ("commit_receipt_id",),
            ("receipt_id",),
        ),
    }
    descriptor = m03_result_extension()
    actual = {
        item.relation_id: (
            item.left_dataset,
            item.right_dataset,
            item.left_keys,
            item.right_keys,
        )
        for item in descriptor.relations
    }
    assert actual == expected_relations

    left = SchemaRegistry()
    left.register_extension(descriptor)
    left_hash = left.freeze()
    right = SchemaRegistry()
    right.register_extension(m03_result_extension())
    right_hash = right.freeze()
    assert left_hash == right_hash == left.snapshot_hash == right.snapshot_hash
    assert left.snapshot()["registry_hash"] == left_hash


def test_manifest_and_full_reader_roundtrip_vectors_receipts_and_hashes(
    m03_result_bundle: M03BundleFixture,
) -> None:
    manifest_reader = ResultReader.open(m03_result_bundle.path, VerifyMode.MANIFEST)
    full_reader = ResultReader.open(m03_result_bundle.path, VerifyMode.FULL)
    assert manifest_reader.compatibility_status == "FULL_SCHEMA_SUPPORT"
    assert full_reader.compatibility_status == "FULL_SCHEMA_SUPPORT"
    assert manifest_reader.bundle_info()["registry_hash"] == m03_result_bundle.registry_hash
    assert (
        manifest_reader.bundle_info()["bundle_semantic_hash"]
        == full_reader.bundle_info()["bundle_semantic_hash"]
    )
    assert verify_bundle(m03_result_bundle.path, VerifyMode.MANIFEST).passed
    assert verify_bundle(m03_result_bundle.path, VerifyMode.FULL).passed

    id_fields = {
        RUN_REQUESTS_DATASET: "request_id",
        ACCEPTED_STATE_HISTORY_DATASET: "state_record_id",
        SUPPORT_CANDIDATE_HISTORY_DATASET: "candidate_record_id",
        CONTACT_SUPPORT_HISTORY_DATASET: "contact_record_id",
        COMMITTED_EVENT_PAYLOADS_DATASET: "event_payload_id",
        RELEASE_OPERATION_HISTORY_DATASET: "operation_record_id",
        WORK_LEDGER_DATASET: "work_ledger_id",
        CONTACT_CYCLE_RECORDS_DATASET: "cycle_record_id",
        CAPABILITY_STATUS_DATASET: "capability_record_id",
    }
    for dataset_id, identity_field in id_fields.items():
        fields = (identity_field, "commit_receipt_id")
        manifest_result = manifest_reader.query(dataset_id, fields)
        full_result = full_reader.query(dataset_id, fields)
        assert manifest_result.read_all().to_pylist() == full_result.read_all().to_pylist()
        assert manifest_result.manifest.result_hash == full_result.manifest.result_hash
        assert full_result.manifest.rows_yielded == 1
        row = manifest_reader.query(dataset_id, fields).read_all().to_pylist()[0]
        assert row["commit_receipt_id"] == m03_result_bundle.receipt_id

    accepted_vectors = full_reader.query(
        ACCEPTED_STATE_HISTORY_DATASET,
        (
            "base_position_global_mm",
            "base_rotation_global_from_base",
            "wrench_a_on_b_global_at_o_n_n_mm",
        ),
    ).read_all()
    assert pa.types.is_list(accepted_vectors["base_position_global_mm"].type)
    assert pa.types.is_list(accepted_vectors["base_rotation_global_from_base"].type)
    row = accepted_vectors.to_pylist()[0]
    assert row["base_position_global_mm"] == [0.1, 0.2, pytest.approx(0.3)]
    assert len(row["base_rotation_global_from_base"]) == 3
    assert all(len(item) == 3 for item in row["base_rotation_global_from_base"])
    assert len(row["wrench_a_on_b_global_at_o_n_n_mm"]) == 6
    assert all(type(item) is float for item in row["wrench_a_on_b_global_at_o_n_n_mm"])


def test_accepted_event_rejected_and_summary_storage_are_physically_isolated(
    m03_result_bundle: M03BundleFixture,
) -> None:
    markers = committed_markers(m03_result_bundle.path)
    assert len(markers) == 1
    committed_datasets = set(markers[0][1]["datasets"])
    assert committed_datasets == {
        "core.accepted_points.common",
        "core.committed_events.events",
        "core.transactions.receipts",
        RUN_REQUESTS_DATASET,
        ACCEPTED_STATE_HISTORY_DATASET,
        SUPPORT_CANDIDATE_HISTORY_DATASET,
        CONTACT_SUPPORT_HISTORY_DATASET,
        COMMITTED_EVENT_PAYLOADS_DATASET,
        RELEASE_OPERATION_HISTORY_DATASET,
        WORK_LEDGER_DATASET,
        CONTACT_CYCLE_RECORDS_DATASET,
        CAPABILITY_STATUS_DATASET,
    }
    assert REJECTED_DIAGNOSTICS_DATASET not in committed_datasets
    assert DERIVED_SUMMARIES_DATASET not in committed_datasets
    assert PLOT_RECIPE_MANIFEST_DATASET not in committed_datasets

    reader = ResultReader.open(m03_result_bundle.path, VerifyMode.FULL)
    default_ids = {item.dataset_id for item in reader.list_datasets().entries}
    assert REJECTED_DIAGNOSTICS_DATASET not in default_ids
    assert set(M03_DATASET_IDS) - {REJECTED_DIAGNOSTICS_DATASET} <= default_ids
    with pytest.raises(QueryError, match="explicit include_diagnostics"):
        reader.query(REJECTED_DIAGNOSTICS_DATASET, ("diagnostic_id",))
    rejected = reader.query(
        REJECTED_DIAGNOSTICS_DATASET,
        (
            "diagnostic_id",
            "trial_id",
            "accepted_state_advanced",
            "path_advanced",
            "time_advanced",
            "slip_advanced",
            "work_advanced",
            "cycle_advanced",
            "event_history_advanced",
        ),
        include_diagnostics=True,
    ).read_all()
    assert rejected.num_rows == 1
    row = rejected.to_pylist()[0]
    assert row["trial_id"] == TRIAL_ID
    assert not any(value for key, value in row.items() if key.endswith("_advanced"))

    auxiliary = reader.bundle_info()["auxiliary_datasets"]
    assert REJECTED_DIAGNOSTICS_DATASET in auxiliary
    assert DERIVED_SUMMARIES_DATASET in auxiliary
    assert PLOT_RECIPE_MANIFEST_DATASET in auxiliary


def test_all_core_relations_join_and_receipt_lineage_resolve(
    m03_result_bundle: M03BundleFixture,
) -> None:
    reader = ResultReader.open(m03_result_bundle.path, VerifyMode.FULL)
    relation_ids = {
        item["relation_id"]
        for item in reader.list_relations().relations
        if item["relation_id"].startswith("m03.")
    }
    assert relation_ids == {item.relation_id for item in m03_result_extension().relations}

    point_join = reader.query(
        ACCEPTED_STATE_HISTORY_DATASET,
        ("state_record_id", "point_id"),
        joins=(JoinSpec("m03.relation.accepted_state_to_point"),),
        include_non_default=True,
    ).read_all()
    assert point_join.num_rows == 1
    assert point_join["accepted_state_id"].to_pylist() == [ACCEPTED_STATE_ID]

    for dataset_id, identity_field, point_field, relation_id in (
        (
            SUPPORT_CANDIDATE_HISTORY_DATASET,
            "candidate_record_id",
            "point_id",
            "m03.relation.candidate_to_point",
        ),
        (
            CONTACT_SUPPORT_HISTORY_DATASET,
            "contact_record_id",
            "point_id",
            "m03.relation.contact_to_point",
        ),
        (
            WORK_LEDGER_DATASET,
            "work_ledger_id",
            "end_point_id",
            "m03.relation.work_to_end_point",
        ),
    ):
        joined = reader.query(
            dataset_id,
            (identity_field, point_field),
            joins=(JoinSpec(relation_id),),
            include_non_default=True,
        ).read_all()
        assert joined.num_rows == 1
        assert joined["accepted_state_id"].to_pylist() == [ACCEPTED_STATE_ID]

    receipt_join = reader.query(
        ACCEPTED_STATE_HISTORY_DATASET,
        ("state_record_id", "commit_receipt_id"),
        joins=(JoinSpec("m03.relation.accepted_state_to_receipt"),),
        include_non_default=True,
    ).read_all()
    assert receipt_join["idempotency_key"].to_pylist() == ["m03-result-extension"]

    event_join = reader.query(
        COMMITTED_EVENT_PAYLOADS_DATASET,
        ("event_payload_id", "event_id"),
        joins=(JoinSpec("m03.relation.event_payload_to_event"),),
        include_non_default=True,
    ).read_all()
    assert event_join.num_rows == 1
    assert event_join["committed"].to_pylist() == [True]

    rejected_left = reader.query(
        REJECTED_DIAGNOSTICS_DATASET,
        ("diagnostic_id", "trial_id"),
        include_non_default=True,
        include_diagnostics=True,
    ).read_all()
    rejected_right = reader.query(
        CORE_REJECTED_TRIALS_DATASET,
        ("trial_id", "diagnostic_summary"),
        include_non_default=True,
        include_diagnostics=True,
    ).read_all()
    assert rejected_left.num_rows == rejected_right.num_rows == 1
    assert rejected_left["trial_id"].to_pylist() == rejected_right["trial_id"].to_pylist()
    assert rejected_right["diagnostic_summary"].to_pylist() == [
        "Intentional M03 rejected-trial isolation fixture."
    ]

    lineage = reader.resolve_lineage()
    assert lineage.receipts == (m03_result_bundle.receipt_id,)
    assert EVENT_ID in lineage.events
    assert {PARENT_STATE_ID, ACCEPTED_STATE_ID} <= set(lineage.states)


def test_versioned_summaries_rebuild_and_recipe_manifests_roundtrip(
    m03_result_bundle: M03BundleFixture,
) -> None:
    committed = m03_result_bundle.committed_records
    accepted = committed[ACCEPTED_STATE_HISTORY_DATASET]
    event = committed[COMMITTED_EVENT_PAYLOADS_DATASET]
    cycle = committed[CONTACT_CYCLE_RECORDS_DATASET]
    work = committed[WORK_LEDGER_DATASET]
    assert isinstance(accepted, AcceptedStateHistoryRecord)
    assert isinstance(event, CommittedEventPayloadRecord)
    assert isinstance(cycle, ContactCycleRecord)
    assert isinstance(work, WorkLedgerRecord)
    rebuilt = build_m03_summaries(
        (accepted,),
        committed_events=(event,),
        contact_cycles=(cycle,),
        work_ledger=(work,),
    )

    reader = ResultReader.open(m03_result_bundle.path, VerifyMode.FULL)
    summaries = reader.query(
        DERIVED_SUMMARIES_DATASET,
        (
            "summary_id",
            "definition_id",
            "definition_version",
            "definition_hash",
            "input_accepted_point_ids",
            "input_raw_links",
            "right_censored",
        ),
    ).read_all()
    assert summaries.num_rows == 7
    assert set(summaries["summary_id"].to_pylist()) == set(m03_result_bundle.summary_ids)
    assert set(summaries["summary_id"].to_pylist()) == {item.summary_id for item in rebuilt}
    assert all(value for value in summaries["definition_hash"].to_pylist())
    assert all(value for value in summaries["input_raw_links"].to_pylist())

    default_recipes = reader.query(
        PLOT_RECIPE_MANIFEST_DATASET,
        ("recipe_id", "smoothing", "rejected_opt_in"),
    ).read_all()
    all_recipes = reader.query(
        PLOT_RECIPE_MANIFEST_DATASET,
        ("recipe_id", "smoothing", "rejected_opt_in"),
        include_non_default=True,
    ).read_all()
    assert default_recipes.num_rows == 7
    assert all_recipes.num_rows == 8
    assert set(all_recipes["recipe_id"].to_pylist()) == set(M03_FROZEN_RECIPE_IDS)
    assert set(all_recipes["recipe_id"].to_pylist()) == set(m03_result_bundle.recipe_ids)
    assert set(all_recipes["smoothing"].to_pylist()) == {"NONE"}
    assert set(all_recipes["rejected_opt_in"].to_pylist()) == {True}


@pytest.mark.parametrize(
    ("replacement", "message"),
    (
        ({"base_position_global_mm": (0.0, 1.0)}, "shape does not match"),
        ({"base_position_global_mm": (0.0, 1, 2.0)}, "runtime float64 components"),
        ({"base_position_global_mm": (0.0, float("inf"), 2.0)}, "non-finite"),
        (
            {"base_rotation_global_from_base": ((1.0, 0.0), (0.0, 1.0))},
            "shape does not match",
        ),
    ),
)
def test_invalid_vector_shape_component_type_and_nonfinite_are_rejected(
    replacement: dict[str, Any], message: str
) -> None:
    registry = SchemaRegistry()
    registry.register_extension(m03_result_extension())
    registry.freeze()
    valid = _sample_record(AcceptedStateHistoryRecord)
    invalid = dataclasses.replace(valid, **replacement)
    with pytest.raises(ContractViolation, match=message):
        registry.validate_record(invalid)


def test_no_damage_and_strength_channels_are_typed_unavailable_and_guarded(
    m03_result_bundle: M03BundleFixture,
) -> None:
    reader = ResultReader.open(m03_result_bundle.path, VerifyMode.FULL)
    fields = (
        "material_model_id",
        "material_substate",
        "strength_substate",
        "failure_prediction_allowed",
        "damage_intents",
        "damage_write_set",
        "initiation_utilization",
        "current_capacity_scale",
        "fracture_energy_n_per_mm",
        "yield_margin",
        "fracture_margin",
        "experimentally_validated",
        "not_certifiable",
    )
    row = reader.query(CAPABILITY_STATUS_DATASET, fields).read_all().to_pylist()[0]
    assert row["material_model_id"] == "no_damage"
    assert row["material_substate"] == "NO_DAMAGE_MODEL"
    assert row["strength_substate"] == "NEEDLE_STRENGTH_UNAVAILABLE"
    assert not row["failure_prediction_allowed"]
    assert row["damage_intents"] == "[]"
    assert row["damage_write_set"] == "[]"
    for field in (
        "initiation_utilization",
        "current_capacity_scale",
        "fracture_energy_n_per_mm",
        "yield_margin",
        "fracture_margin",
    ):
        assert row[field] is None
    assert row["experimentally_validated"] == "NOT_ASSESSED"
    assert row["not_certifiable"]

    capability = _sample_record(CapabilityStatusRecord)
    assert isinstance(capability, CapabilityStatusRecord)
    with pytest.raises(ContractViolation, match="no_damage boundary"):
        dataclasses.replace(capability, failure_prediction_allowed=True)
    with pytest.raises(ContractViolation, match="damage writes"):
        dataclasses.replace(capability, damage_write_set=("damage:forbidden",))
    with pytest.raises(ContractViolation, match="typed unavailable"):
        dataclasses.replace(capability, yield_margin=1.0)  # type: ignore[arg-type]


def test_additive_schema_evolution_contract_uses_explicit_null_unavailable_adapter() -> None:
    descriptor = m03_result_extension()
    assert descriptor.compatibility_class is CompatibilityClass.ADDITIVE_MINOR
    assert assess_compatibility(M03_EXTENSION_SCHEMA_VERSION, "1.1.0").status == (
        "PARTIAL_SCHEMA_SUPPORT"
    )
    adapter = MissingFieldAdapter("m03.capability_status.future_optional", "1.1.0")
    adapted = adapter.adapt_row(
        {"capability_record_id": "capability:legacy"},
        bundle_version=M03_EXTENSION_SCHEMA_VERSION,
    )
    assert adapted["future_optional"] is None
    assert adapted["future_optional__status"]["capability_status"] == "UNAVAILABLE"
    assert (
        adapted["future_optional__status"]["reason_code"] == "FIELD_NOT_PRESENT_IN_SCHEMA_VERSION"
    )
