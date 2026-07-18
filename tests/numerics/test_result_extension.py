from __future__ import annotations

import dataclasses
import re
from pathlib import Path
from typing import Any

import pytest

from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    AttemptOutcome,
    CapabilityStatus,
    CertificationStatus,
    Maturity,
    MaturityStatus,
    PhysicalFeasibility,
    SourceIdentity,
    StatusTuple,
    ValuePresence,
)
from spine_sim.foundation.registry import DataClassification, DatasetClass, SchemaRegistry
from spine_sim.numerics.result_extension import (
    ACCEPTED_STEP_NUMERICS_DATASET,
    CASCADE_ROUNDS_DATASET,
    CONTINUATION_ATTEMPTS_DATASET,
    CONTINUATION_TARGETS_DATASET,
    CORE_ACCEPTED_POINTS_DATASET,
    CORE_COMMIT_RECEIPTS_DATASET,
    CORE_COMMITTED_EVENTS_DATASET,
    CORE_REJECTED_TRIALS_DATASET,
    EVENT_BRACKETS_DATASET,
    EVENT_CHANNEL_REGISTRATIONS_DATASET,
    EVENT_DEPENDENCIES_DATASET,
    EVENT_EARLIESTNESS_CERTIFICATES_DATASET,
    EVENT_PROBES_DATASET,
    FAILURE_DIAGNOSTICS_DATASET,
    ITERATION_TRACES_DATASET,
    M01_COMPATIBILITY_RESULTS_DATASET,
    M02_EXTENSION_SCHEMA_VERSION,
    M02_REGISTERED_DATASET_IDS,
    REFINEMENT_STUDIES_DATASET,
    REJECTED_EVENT_BRACKETS_DATASET,
    REJECTED_ITERATION_TRACES_DATASET,
    REJECTED_TRIAL_DIAGNOSTICS_DATASET,
    REPLAY_STEPS_DATASET,
    RESIDUAL_BLOCK_SUMMARIES_DATASET,
    SIMULTANEOUS_EVENT_GROUPS_DATASET,
    TRANSACTION_TRACE_DATASET,
    ContinuationAttemptRecord,
    DiagnosticLevel,
    DiagnosticRecordKind,
    DiagnosticStorageContext,
    EventBracketRecord,
    IterationTraceRecord,
    M01CompatibilityResultRecord,
    RefinementStudyRecord,
    RejectedEventBracketRecord,
    RejectedIterationTraceRecord,
    diagnostic_persistence_policy,
    m02_dataset_ids,
    m02_result_extension,
    numerics_result_extension,
    should_persist_diagnostic,
)


def _status() -> StatusTuple:
    return StatusTuple(
        ValuePresence.PRESENT,
        CapabilityStatus.SUPPORTED,
        AttemptOutcome.NOT_ATTEMPTED,
        PhysicalFeasibility.NOT_ASSESSED,
        CertificationStatus.NOT_ASSESSED,
        "M02_TEST_EVIDENCE",
        "typed software-contract fixture",
    )


def _sample_value(field: dataclasses.Field[Any]) -> Any:
    annotation = str(field.type)
    if field.name == "schema_version":
        return M02_EXTENSION_SCHEMA_VERSION
    if "StatusTuple" in annotation:
        return _status()
    if "SourceIdentity" in annotation:
        return SourceIdentity.DEV_POLICY
    if "Maturity" in annotation:
        return Maturity.validation_only_implemented()
    if "CertificationStatus" in annotation:
        return CertificationStatus.NOT_ASSESSED
    if "None" in annotation:
        return None
    if annotation == "bool":
        return False
    if annotation == "float":
        return 1.0
    if annotation == "int":
        return 1
    if "tuple" in annotation:
        return ()
    return f"fixture:{field.name}"


def _sample_record(record_type: type[Any]) -> Any:
    values = {field.name: _sample_value(field) for field in dataclasses.fields(record_type)}
    if record_type is IterationTraceRecord:
        values.update(point_id="point:accepted", accepted_state_advanced=True)
    if record_type is EventBracketRecord:
        values["event_id"] = "event:committed"
    if record_type in {RejectedIterationTraceRecord, RejectedEventBracketRecord}:
        values["trial_id"] = "trial:rejected"
    return record_type(**values)


def test_m02_extension_registers_frozen_minimum_plus_additive_rejected_trace_datasets() -> None:
    descriptor = m02_result_extension()
    registry = SchemaRegistry()
    registry.register_extension(descriptor)
    digest = registry.freeze()

    assert descriptor.namespace == "m02"
    assert descriptor.owner_module == "M02"
    assert descriptor.extension_schema_version == "1.0.0"
    assert descriptor.common_keys == ("run_id", "case_id")
    assert descriptor.arrays == ()
    assert len(descriptor.tables) == 20
    assert tuple(item.dataset_id for item in descriptor.tables) == M02_REGISTERED_DATASET_IDS
    assert m02_dataset_ids() == M02_REGISTERED_DATASET_IDS
    assert numerics_result_extension() == descriptor
    assert set(M02_REGISTERED_DATASET_IDS) <= set(registry.datasets)
    assert digest == registry.snapshot_hash


def test_all_m02_record_types_match_and_validate_against_registered_schema() -> None:
    descriptor = m02_result_extension()
    registry = SchemaRegistry()
    registry.register_extension(descriptor)
    registry.freeze()

    for dataset in descriptor.tables:
        assert dataset.record_type is not None
        record = _sample_record(dataset.record_type)
        assert record.__dataset_id__ == dataset.dataset_id
        assert registry.validate_record(record) is dataset


def test_dataset_classes_strictly_isolate_accepted_event_rejected_and_transaction_rows() -> None:
    classes = {item.dataset_id: item.dataset_class for item in m02_result_extension().tables}
    assert classes == {
        CONTINUATION_TARGETS_DATASET: DatasetClass.INDEX,
        CONTINUATION_ATTEMPTS_DATASET: DatasetClass.REJECTED,
        ACCEPTED_STEP_NUMERICS_DATASET: DatasetClass.ACCEPTED,
        RESIDUAL_BLOCK_SUMMARIES_DATASET: DatasetClass.ACCEPTED,
        ITERATION_TRACES_DATASET: DatasetClass.ACCEPTED,
        REJECTED_ITERATION_TRACES_DATASET: DatasetClass.REJECTED,
        EVENT_CHANNEL_REGISTRATIONS_DATASET: DatasetClass.INDEX,
        EVENT_PROBES_DATASET: DatasetClass.REJECTED,
        EVENT_BRACKETS_DATASET: DatasetClass.EVENT,
        REJECTED_EVENT_BRACKETS_DATASET: DatasetClass.REJECTED,
        EVENT_EARLIESTNESS_CERTIFICATES_DATASET: DatasetClass.REJECTED,
        SIMULTANEOUS_EVENT_GROUPS_DATASET: DatasetClass.EVENT,
        EVENT_DEPENDENCIES_DATASET: DatasetClass.EVENT,
        CASCADE_ROUNDS_DATASET: DatasetClass.EVENT,
        REJECTED_TRIAL_DIAGNOSTICS_DATASET: DatasetClass.REJECTED,
        TRANSACTION_TRACE_DATASET: DatasetClass.TRANSACTION,
        REPLAY_STEPS_DATASET: DatasetClass.TRANSACTION,
        FAILURE_DIAGNOSTICS_DATASET: DatasetClass.REJECTED,
        REFINEMENT_STUDIES_DATASET: DatasetClass.SUMMARY,
        M01_COMPATIBILITY_RESULTS_DATASET: DatasetClass.SUMMARY,
    }

    descriptor = m02_result_extension()
    rejected = {
        item.dataset_id for item in descriptor.tables if item.dataset_class is DatasetClass.REJECTED
    }
    assert rejected
    assert all(
        not item.default_visible for item in descriptor.tables if item.dataset_id in rejected
    )
    assert all(
        field.classification is DataClassification.DIAGNOSTIC
        for item in descriptor.tables
        if item.dataset_id in rejected
        for field in item.fields
    )
    assert all(
        field.classification is DataClassification.CANONICAL_RAW
        for item in descriptor.tables
        if item.dataset_class in {DatasetClass.ACCEPTED, DatasetClass.EVENT}
        for field in item.fields
    )


def test_every_m02_field_has_complete_metadata_and_no_experimental_claim() -> None:
    descriptor = m02_result_extension()
    for dataset in descriptor.tables:
        assert dataset.namespace == "m02"
        assert dataset.owner_module == "M02"
        assert dataset.schema_version == M02_EXTENSION_SCHEMA_VERSION
        for field in dataset.fields:
            assert field.namespace == "m02"
            assert field.owner_module == "M02"
            assert field.semantics
            assert field.dtype
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
            assert field.authority_refs
            assert field.storage_dataset == dataset.dataset_id
            assert field.encoding == "parquet_zstd_lossless"
            assert (
                field.maturity.experimentally_validated.status is MaturityStatus.BLOCKED_UNAVAILABLE
            )

    validation_ids = {REFINEMENT_STUDIES_DATASET, M01_COMPATIBILITY_RESULTS_DATASET}
    assert all(
        item.source_identity is SourceIdentity.VALIDATION_ONLY
        for item in descriptor.tables
        if item.dataset_id in validation_ids
    )


def test_m02_relations_only_reference_m00_core_identity_authorities() -> None:
    descriptor = m02_result_extension()
    datasets = {item.dataset_id: item for item in descriptor.tables}
    allowed_targets = {
        CORE_ACCEPTED_POINTS_DATASET,
        CORE_COMMITTED_EVENTS_DATASET,
        CORE_REJECTED_TRIALS_DATASET,
        CORE_COMMIT_RECEIPTS_DATASET,
    }
    assert {item.right_dataset for item in descriptor.relations} == allowed_targets
    for relation in descriptor.relations:
        assert relation.left_dataset in datasets
        assert relation.right_dataset in allowed_targets
        local_fields = {
            item.field_id.rsplit(".", 1)[-1] for item in datasets[relation.left_dataset].fields
        }
        assert set(relation.left_keys) <= local_fields
        assert relation.cardinality == "many-to-one"

    # M02 owns no competing core record or array identity.
    assert descriptor.arrays == ()
    assert all(
        item.record_type is not None and item.record_type.__dataset_id__.startswith("m02.")
        for item in descriptor.tables
    )


def test_m00_owned_receipt_is_optional_only_for_transaction_staging_rows() -> None:
    descriptor = m02_result_extension()
    datasets = {item.dataset_id: item for item in descriptor.tables}
    staging_datasets = {
        ACCEPTED_STEP_NUMERICS_DATASET,
        CASCADE_ROUNDS_DATASET,
        EVENT_BRACKETS_DATASET,
        EVENT_DEPENDENCIES_DATASET,
        ITERATION_TRACES_DATASET,
        RESIDUAL_BLOCK_SUMMARIES_DATASET,
        SIMULTANEOUS_EVENT_GROUPS_DATASET,
    }

    for dataset_id in staging_datasets:
        receipt = next(
            item
            for item in datasets[dataset_id].fields
            if item.field_id.endswith(".commit_receipt_id")
        )
        assert not receipt.required
        assert receipt.null_policy == (
            "null only during M00 transaction staging; atomically patched before publication"
        )

    # The relation still points to the authoritative M00 receipt dataset; the
    # M00 transaction patches the value before publishing the immutable shard.
    receipt_relations = {
        item.left_dataset: item.right_dataset
        for item in descriptor.relations
        if item.left_dataset in staging_datasets and item.left_keys == ("commit_receipt_id",)
    }
    assert receipt_relations == {
        ACCEPTED_STEP_NUMERICS_DATASET: CORE_COMMIT_RECEIPTS_DATASET,
        CASCADE_ROUNDS_DATASET: CORE_COMMIT_RECEIPTS_DATASET,
        EVENT_BRACKETS_DATASET: CORE_COMMIT_RECEIPTS_DATASET,
        EVENT_DEPENDENCIES_DATASET: CORE_COMMIT_RECEIPTS_DATASET,
        ITERATION_TRACES_DATASET: CORE_COMMIT_RECEIPTS_DATASET,
        RESIDUAL_BLOCK_SUMMARIES_DATASET: CORE_COMMIT_RECEIPTS_DATASET,
        SIMULTANEOUS_EVENT_GROUPS_DATASET: CORE_COMMIT_RECEIPTS_DATASET,
    }


def test_rejected_attempt_cannot_publish_state_or_receipt() -> None:
    values = {
        field.name: _sample_value(field) for field in dataclasses.fields(ContinuationAttemptRecord)
    }
    with pytest.raises(ContractViolation):
        ContinuationAttemptRecord(
            **{
                **values,
                "accepted_state_advanced": True,
                "commit_receipt_id": "receipt:forbidden",
            }
        )


def test_receipt_backed_trace_and_bracket_reject_uncommitted_diagnostic_shapes() -> None:
    trace_values = {
        field.name: _sample_value(field) for field in dataclasses.fields(IterationTraceRecord)
    }
    with pytest.raises(ContractViolation, match="receipt-backed accepted solves"):
        IterationTraceRecord(**trace_values)

    bracket_values = {
        field.name: _sample_value(field) for field in dataclasses.fields(EventBracketRecord)
    }
    with pytest.raises(ContractViolation, match="receipt-backed committed events"):
        EventBracketRecord(**bracket_values)

    rejected_trace = _sample_record(RejectedIterationTraceRecord)
    rejected_bracket = _sample_record(RejectedEventBracketRecord)
    assert rejected_trace.trial_id == "trial:rejected"
    assert rejected_trace.point_id is None
    assert rejected_trace.commit_receipt_id is None
    assert not rejected_trace.accepted_state_advanced
    assert rejected_bracket.trial_id == "trial:rejected"
    assert rejected_bracket.commit_receipt_id is None
    assert not rejected_bracket.accepted_state_advanced


def test_validation_records_expose_public_m00_summary_contract() -> None:
    refinement = _sample_record(RefinementStudyRecord)
    compatibility = _sample_record(M01CompatibilityResultRecord)

    assert refinement.summary_id.startswith("m02-refinement-summary:")
    assert refinement.summary_id == refinement.summary_id
    assert refinement.summary_kind == "M02_REFINEMENT_VALIDATION_SUMMARY"
    assert refinement.included_dataset_classes == ("accepted", "event")

    assert compatibility.summary_id == compatibility.compatibility_result_id
    assert "DIAGNOSTIC" in compatibility.summary_kind
    assert compatibility.included_dataset_classes == ("accepted", "event", "rejected")


def test_diagnostic_levels_are_pure_retention_strategies_and_preserve_replay_hashes() -> None:
    accepted_final = DiagnosticStorageContext(accepted=True, final_iteration=True)
    committed_final = DiagnosticStorageContext(committed_event=True, final_bracket=True)
    rejected_retry = DiagnosticStorageContext(rejected_retry=True)
    terminal_failure = DiagnosticStorageContext(terminal_failure=True)

    for level in DiagnosticLevel:
        policy = diagnostic_persistence_policy(level)
        assert policy.preserves_semantic_decisions
        assert not policy.affects_solver_decisions
        assert policy.should_store(DiagnosticRecordKind.SEMANTIC_DECISION)
        assert policy.should_store(DiagnosticRecordKind.RETRY_FAILURE_COUNT)
        assert policy.should_store(DiagnosticRecordKind.RECEIPT_REFERENCE)
        assert policy.should_store(
            DiagnosticRecordKind.ACCEPTED_FINAL_BLOCK_SUMMARY, accepted_final
        )
        assert policy.should_store(
            DiagnosticRecordKind.COMMITTED_EVENT_FINAL_BRACKET, committed_final
        )

    assert not should_persist_diagnostic(
        DiagnosticLevel.COMPACT,
        DiagnosticRecordKind.ACCEPTED_FINAL_ITERATION,
        accepted_final,
    )
    assert should_persist_diagnostic(
        DiagnosticLevel.STANDARD,
        DiagnosticRecordKind.ACCEPTED_FINAL_ITERATION,
        accepted_final,
    )
    assert should_persist_diagnostic(DiagnosticLevel.STANDARD, DiagnosticRecordKind.EVENT_PROBE)
    assert should_persist_diagnostic(
        DiagnosticLevel.STANDARD,
        DiagnosticRecordKind.REJECTED_RETRY_SUMMARY,
        rejected_retry,
    )
    assert should_persist_diagnostic(
        DiagnosticLevel.STANDARD,
        DiagnosticRecordKind.FINAL_FAILURE_TRACE,
        terminal_failure,
    )
    assert not should_persist_diagnostic(
        DiagnosticLevel.STANDARD, DiagnosticRecordKind.OWNER_TRIAL_RESPONSE
    )
    assert should_persist_diagnostic(
        DiagnosticLevel.FULL, DiagnosticRecordKind.OWNER_TRIAL_RESPONSE
    )
    assert should_persist_diagnostic(DiagnosticLevel.FULL, DiagnosticRecordKind.TEMPORARY_BRANCH)
    assert should_persist_diagnostic(DiagnosticLevel.FULL, DiagnosticRecordKind.TRANSACTION_DETAIL)


def test_future_numerics_readme_output_overview_uses_only_registered_ids() -> None:
    """Activate the exact README check as soon as the integration owner adds it."""

    readme = Path(__file__).parents[2] / "src" / "spine_sim" / "numerics" / "README.md"
    if not readme.exists():
        pytest.skip("numerics README is owned by the integration/documentation task")
    text = readme.read_text(encoding="utf-8")
    assert "## 输出概览" in text
    output_overview = text.split("## 输出概览", maxsplit=1)[1]
    documented_ids = set(re.findall(r"`(m02\.[a-z0-9_]+)`", output_overview))
    assert documented_ids == set(M02_REGISTERED_DATASET_IDS)
