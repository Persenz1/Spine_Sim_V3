from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest
from scripts.run_m03_campaign import _canonical_history_artifact

from spine_sim.foundation.canonical import canonical_json_bytes, semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.integrity import VerifyMode, committed_markers, verify_bundle
from spine_sim.foundation.reader import ResultReader
from spine_sim.foundation.registry import SchemaRegistry
from spine_sim.foundation.replay import ReplayMode, compare_replay
from spine_sim.foundation.writer import ResultWriter, make_run_envelope
from spine_sim.numerics.events import EventEngine
from spine_sim.single_spine.contracts import (
    EmbeddedErrorClass,
    FailureAxis,
    StandaloneTerminalStatus,
)
from spine_sim.single_spine.demo_validation_only import _resolved_config
from spine_sim.single_spine.kernel import IntrinsicSingleSpineKernel
from spine_sim.single_spine.persistence import (
    StandalonePersistenceContext,
    persist_standalone_execution,
)
from spine_sim.single_spine.result_extension import (
    ACCEPTED_STATE_HISTORY_DATASET,
    COMMITTED_EVENT_PAYLOADS_DATASET,
    CONTACT_CYCLE_RECORDS_DATASET,
    REJECTED_DIAGNOSTICS_DATASET,
    RELEASE_OPERATION_HISTORY_DATASET,
    RUN_REQUESTS_DATASET,
    SUPPORT_CANDIDATE_HISTORY_DATASET,
    WORK_LEDGER_DATASET,
    m03_result_extension,
)
from spine_sim.single_spine.standalone import (
    StandaloneDriverConfig,
    StandaloneSingleSpineDriver,
    UnavailableInitialPose,
    _DriverFailure,
    _ExecutionContext,
    _m02_config,
)
from tests.single_spine.test_standalone import _AnalyticPlaneKernel, _request


def _coarse_config(request: object, *, drag_step_mm: float) -> StandaloneDriverConfig:
    base = StandaloneDriverConfig.resolved(request)  # type: ignore[arg-type]
    payload = dataclasses.asdict(base)
    payload["drag_step_mm"] = drag_step_mm
    payload.pop("config_id")
    payload.pop("config_hash")
    return dataclasses.replace(
        base,
        drag_step_mm=drag_step_mm,
        config_id=stable_content_id("m03_test_driver_config", payload),
        config_hash=semantic_hash(payload),
    )


def _writer_and_request(destination: Path) -> tuple[ResultWriter, object]:
    registry = SchemaRegistry()
    registry.register_extension(m03_result_extension())
    registry_hash = registry.freeze()
    run_config = _resolved_config("m03_standalone_persistence_test_run")
    envelope = make_run_envelope(
        registry_hash=registry_hash,
        resolved_run_config=run_config,
        operation_kind="M03_STANDALONE_TEST",
        operation_profile="PERSISTENCE_ROUNDTRIP",
        source_file_hashes={},
        replay_manifest={"scope": "test"},
        git_commit="TEST",
        dirty_status="clean",
        provenance_labels=("TEST", "not_certifiable"),
    )
    request = _request(envelope.run_id)
    writer = ResultWriter.create_run_bundle(
        destination,
        registry=registry,
        run_envelope=envelope,
    )
    writer.write_resolved_config_and_provenance(
        run_config,
        provenance={"scope": "test"},
        replay_manifest={"scope": "test"},
    )
    writer.create_case_shard(
        request.case_id,
        design_id="design:m03-standalone-test",
        seed_id="seed:m03-standalone-test",
        surface_realization_id=(request.surface_query_handle.realization.surface_realization_id),
        resolved_case_config=_resolved_config("m03_standalone_persistence_test_case"),
    )
    return writer, request


def test_standalone_history_roundtrips_with_one_real_m00_receipt(tmp_path: Path) -> None:
    writer, request = _writer_and_request(tmp_path / "standalone.spine-result")
    execution = StandaloneSingleSpineDriver(
        kernel=_AnalyticPlaneKernel(release_once=True, fail_during_research=True),
        config=_coarse_config(request, drag_step_mm=10.0),
    ).execute(request)
    assert execution.rejected_trials

    published = persist_standalone_execution(
        writer=writer,
        request=request,
        execution=execution,
        context=StandalonePersistenceContext(
            "design:m03-standalone-test",
            "seed:m03-standalone-test",
            "M03_STANDALONE_PERSISTENCE_TEST_TX",
        ),
    )
    retry = persist_standalone_execution(
        writer=writer,
        request=request,
        execution=execution,
        context=StandalonePersistenceContext(
            "design:m03-standalone-test",
            "seed:m03-standalone-test",
            "M03_STANDALONE_PERSISTENCE_TEST_TX",
        ),
    )
    assert retry.receipt_id == published.receipt_id
    assert retry.rejected_diagnostic_paths == published.rejected_diagnostic_paths
    writer.finalize_case(request.case_id)
    writer.publish_run_manifest()

    assert verify_bundle(writer.root, VerifyMode.FULL).passed
    assert published.artifact_backed_accepted_point_count == 0
    assert published.response_only_accepted_point_count == len(execution.accepted_points)
    assert published.unrepresentable_candidate_count == 0
    reader = ResultReader.open(writer.root, VerifyMode.FULL)
    accepted = reader.query(
        ACCEPTED_STATE_HISTORY_DATASET,
        ("point_id", "commit_receipt_id", "maturity"),
    ).read_all()
    assert accepted.num_rows == published.accepted_point_count == len(execution.accepted_points)
    assert {item["commit_receipt_id"] for item in accepted.to_pylist()} == {published.receipt_id}
    maturity = json.loads(accepted.to_pylist()[0]["maturity"])
    assert maturity["numerically_verified"]["status"] == "NOT_ASSESSED"

    assert reader.query(
        COMMITTED_EVENT_PAYLOADS_DATASET,
        ("event_id", "commit_receipt_id"),
    ).read_all().num_rows == len(execution.committed_events)
    assert reader.query(
        RELEASE_OPERATION_HISTORY_DATASET,
        ("operation_record_id", "commit_receipt_id"),
    ).read_all().num_rows == len(execution.operation_segments)
    assert reader.query(
        WORK_LEDGER_DATASET,
        ("work_ledger_id", "commit_receipt_id"),
    ).read_all().num_rows == len(execution.accepted_points)
    assert (
        reader.query(
            CONTACT_CYCLE_RECORDS_DATASET,
            ("cycle_record_id", "commit_receipt_id"),
        )
        .read_all()
        .num_rows
        == published.contact_cycle_count
    )
    assert (
        reader.query(
            RUN_REQUESTS_DATASET,
            ("request_id", "commit_receipt_id"),
        )
        .read_all()
        .to_pylist()[0]["commit_receipt_id"]
        == published.receipt_id
    )

    rejected = (
        reader.query(
            REJECTED_DIAGNOSTICS_DATASET,
            ("trial_id", "accepted_state_advanced", "event_history_advanced"),
            include_diagnostics=True,
        )
        .read_all()
        .to_pylist()
    )
    assert len(rejected) == len(published.rejected_diagnostic_paths) == 1
    assert not rejected[0]["accepted_state_advanced"]
    assert not rejected[0]["event_history_advanced"]


class _ContractRejectingKernel(_AnalyticPlaneKernel):
    def evaluate_trial(self, request: object) -> object:
        if self.calls:
            raise ContractViolation("injected A-to-B contract rejection")
        return super().evaluate_trial(request)  # type: ignore[arg-type]


class _AlwaysContractRejectingKernel(_AnalyticPlaneKernel):
    def evaluate_trial(self, request: object) -> object:
        del request
        raise ContractViolation("injected initial A-to-B contract rejection")


def test_kernel_contract_violation_preserves_contract_failure_axis() -> None:
    request = _request("contract-rejection")
    execution = StandaloneSingleSpineDriver(kernel=_ContractRejectingKernel()).execute(request)

    assert execution.response.failure_axis is FailureAxis.CONTRACT_REJECTION
    assert execution.response.terminal_status is StandaloneTerminalStatus.CAPABILITY_TERMINATION
    assert execution.rejected_trials[-1].failure_axis is FailureAxis.CONTRACT_REJECTION
    assert execution.rejected_trials[-1].reason_code == "M03_KERNEL_CONTRACT_REJECTION"
    assert execution.trial_snapshots[-1].response is None
    assert "ContractViolation" in (execution.trial_snapshots[-1].exception_detail or "")


def test_initial_contract_failure_has_typed_unavailable_pose_without_fake_evidence() -> None:
    request = _request("initial-contract-rejection")
    execution = StandaloneSingleSpineDriver(kernel=_AlwaysContractRejectingKernel()).execute(
        request
    )

    evidence = execution.resolved_initial_pose
    assert isinstance(evidence, UnavailableInitialPose)
    assert execution.response.failure_axis is FailureAxis.CONTRACT_REJECTION
    assert execution.response.terminal_status is StandaloneTerminalStatus.CAPABILITY_TERMINATION
    assert execution.trial_call_count == 1
    assert evidence.reason_code == "M03_KERNEL_CONTRACT_REJECTION"
    assert evidence.query_receipt_ids == ()
    assert evidence.response_hash is None
    assert not hasattr(evidence, "actual_minimum_clearance_mm")


def test_pretrial_domain_failure_has_typed_unavailable_pose_and_zero_trials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request("pretrial-domain-failure")

    def fail_before_query(
        _self: StandaloneSingleSpineDriver,
        _context: _ExecutionContext,
    ) -> object:
        raise _DriverFailure(
            "M01_OUT_OF_DOMAIN",
            FailureAxis.DOMAIN_ERROR,
            "injected path-domain rejection before any query",
        )

    monkeypatch.setattr(StandaloneSingleSpineDriver, "_seed_pose", fail_before_query)
    execution = StandaloneSingleSpineDriver(kernel=_AnalyticPlaneKernel()).execute(request)

    evidence = execution.resolved_initial_pose
    assert isinstance(evidence, UnavailableInitialPose)
    assert execution.response.failure_axis is FailureAxis.DOMAIN_ERROR
    assert execution.response.terminal_status is StandaloneTerminalStatus.DOMAIN_TERMINATION
    assert execution.trial_call_count == 0
    assert execution.trial_snapshots == ()
    assert canonical_json_bytes(_canonical_history_artifact(execution))
    assert evidence.reason_code == "M01_OUT_OF_DOMAIN"
    assert evidence.query_receipt_ids == ()
    assert evidence.response_hash is None


def test_real_intrinsic_history_persists_full_candidate_artifacts(tmp_path: Path) -> None:
    writer, request = _writer_and_request(tmp_path / "intrinsic.spine-result")
    config = StandaloneDriverConfig.resolved(request)
    kernel = IntrinsicSingleSpineKernel()
    driver = StandaloneSingleSpineDriver(kernel=kernel, config=config)
    driver_context = _ExecutionContext(
        request,
        config,
        kernel,
        EventEngine(_m02_config(request)),
        [],
        [],
        [],
        [],
        [],
    )
    resolved, state, response = driver._resolve_initial_pose(driver_context)
    execution = driver._execution(
        driver_context,
        resolved,
        state,
        StandaloneTerminalStatus.PHYSICAL_TERMINATION,
        "TEST_STOP_AFTER_INITIAL_CLEARANCE",
        FailureAxis.PHYSICAL_INFEASIBLE,
        "Directed persistence test stops after the real intrinsic clearance phase.",
        response.work.remaining_stored_energy_n_mm,
    )
    snapshot = execution.trial_snapshots[-1]
    assert snapshot.kernel_evaluation is not None
    assert canonical_json_bytes(_canonical_history_artifact(execution))
    candidate_evaluation = snapshot.kernel_evaluation.artifacts.candidate_evaluation
    assert len(candidate_evaluation.candidates) > len(
        candidate_evaluation.active_graph_candidate_ids
    )

    published = persist_standalone_execution(
        writer=writer,
        request=request,
        execution=execution,
        context=StandalonePersistenceContext(
            "design:m03-standalone-test",
            "seed:m03-standalone-test",
            "M03_INTRINSIC_ARTIFACT_PERSISTENCE_TEST_TX",
        ),
    )
    assert published.artifact_backed_accepted_point_count == 1
    assert published.response_only_accepted_point_count == 0
    assert published.unrepresentable_candidate_count == 0
    writer.finalize_case(request.case_id)
    writer.publish_run_manifest()
    rows = (
        ResultReader.open(writer.root, VerifyMode.FULL)
        .query(
            SUPPORT_CANDIDATE_HISTORY_DATASET,
            (
                "candidate_id",
                "candidate_origin",
                "local_minimum_verified",
                "empty_ball_verified",
                "full_candidate_comparison_verified",
                "commit_receipt_id",
            ),
        )
        .read_all()
        .to_pylist()
    )
    assert len(rows) == len(candidate_evaluation.candidates)
    assert {item["candidate_id"] for item in rows} == {
        item.candidate_id for item in candidate_evaluation.candidates
    }
    assert any("NEARBY_SWITCH_PROBE" in item["candidate_origin"] for item in rows)
    assert any(item["local_minimum_verified"] for item in rows)
    assert any(item["empty_ball_verified"] for item in rows)
    assert all(item["commit_receipt_id"] == published.receipt_id for item in rows)


def test_idempotent_publication_and_semantic_replay_are_stable(tmp_path: Path) -> None:
    writer, request = _writer_and_request(tmp_path / "left.spine-result")
    execution = StandaloneSingleSpineDriver(
        kernel=_AnalyticPlaneKernel(),
        config=_coarse_config(request, drag_step_mm=100.0),
    ).execute(request)
    context = StandalonePersistenceContext(
        "design:m03-standalone-test",
        "seed:m03-standalone-test",
        "M03_STANDALONE_REPLAY_TEST_TX",
    )
    first = persist_standalone_execution(
        writer=writer,
        request=request,
        execution=execution,
        context=context,
    )
    retry = persist_standalone_execution(
        writer=writer,
        request=request,
        execution=execution,
        context=context,
    )
    assert retry.receipt_id == first.receipt_id
    assert len(committed_markers(writer.root)) == 1

    registry = writer.registry
    envelope = writer.run_envelope
    right = ResultWriter.create_run_bundle(
        tmp_path / "right.spine-result",
        registry=registry,
        run_envelope=envelope,
    )
    run_config = _resolved_config("m03_standalone_persistence_test_run")
    right.write_resolved_config_and_provenance(
        run_config,
        provenance={"scope": "test"},
        replay_manifest={"scope": "test"},
    )
    right.create_case_shard(
        request.case_id,
        design_id=context.design_id,
        seed_id=context.seed_id,
        surface_realization_id=request.surface_query_handle.realization.surface_realization_id,
        resolved_case_config=_resolved_config("m03_standalone_persistence_test_case"),
    )
    replayed = persist_standalone_execution(
        writer=right,
        request=request,
        execution=execution,
        context=context,
    )
    assert replayed.receipt_id == first.receipt_id
    writer.finalize_case(request.case_id)
    writer.publish_run_manifest()
    right.finalize_case(request.case_id)
    right.publish_run_manifest()
    report = compare_replay(writer.root, right.root, mode=ReplayMode.SEMANTIC_REPLAY)
    assert report.equivalent


def test_transaction_fault_publishes_no_receipt_or_accepted_rows(tmp_path: Path) -> None:
    writer, request = _writer_and_request(tmp_path / "fault.spine-result")
    execution = StandaloneSingleSpineDriver(
        kernel=_AnalyticPlaneKernel(),
        config=_coarse_config(request, drag_step_mm=100.0),
    ).execute(request)

    def fail_event_write(stage: str) -> None:
        if stage == "event_write":
            raise RuntimeError("injected transaction event-write fault")

    writer.fault_injector = fail_event_write
    with pytest.raises(RuntimeError, match="injected transaction event-write fault"):
        persist_standalone_execution(
            writer=writer,
            request=request,
            execution=execution,
            context=StandalonePersistenceContext(
                "design:m03-standalone-test",
                "seed:m03-standalone-test",
                "M03_STANDALONE_FAULT_TEST_TX",
            ),
        )
    assert not committed_markers(writer.root)
    assert not tuple((writer.root / "accepted_points").rglob("*.parquet"))


def test_publication_rejects_reduction_points_and_failed_event_post_gate(tmp_path: Path) -> None:
    writer, request = _writer_and_request(tmp_path / "quality-gates.spine-result")
    execution = StandaloneSingleSpineDriver(
        kernel=_AnalyticPlaneKernel(),
        config=_coarse_config(request, drag_step_mm=100.0),
    ).execute(request)
    context = StandalonePersistenceContext(
        "design:m03-standalone-test",
        "seed:m03-standalone-test",
        "M03_STANDALONE_QUALITY_GATE_TEST_TX",
    )

    accepted_response_id = execution.accepted_points[0].response_id
    accepted_index = next(
        index
        for index, snapshot in enumerate(execution.trial_snapshots)
        if snapshot.response is not None and snapshot.response.response_id == accepted_response_id
    )
    accepted_snapshot = execution.trial_snapshots[accepted_index]
    assert accepted_snapshot.response is not None
    reduction_response = dataclasses.replace(
        accepted_snapshot.response,
        diagnostics=dataclasses.replace(
            accepted_snapshot.response.diagnostics,
            error_class=EmbeddedErrorClass.EVENT_REDUCTION_REQUIRED,
        ),
    )
    reduction_trials = list(execution.trial_snapshots)
    reduction_trials[accepted_index] = dataclasses.replace(
        accepted_snapshot,
        response=reduction_response,
    )
    reduction_execution = dataclasses.replace(
        execution,
        trial_snapshots=tuple(reduction_trials),
    )
    with pytest.raises(ContractViolation, match="not eligible for accepted history"):
        persist_standalone_execution(
            writer=writer,
            request=request,
            execution=reduction_execution,
            context=context,
        )

    post_hash = execution.committed_events[0].post_event_response_hash
    post_index = next(
        index
        for index, snapshot in enumerate(execution.trial_snapshots)
        if snapshot.response is not None and snapshot.response.response_hash == post_hash
    )
    post_snapshot = execution.trial_snapshots[post_index]
    assert post_snapshot.response is not None
    inconsistent_response = dataclasses.replace(
        post_snapshot.response,
        state_events=dataclasses.replace(
            post_snapshot.response.state_events,
            event_one_sided_consistency=False,
        ),
    )
    inconsistent_trials = list(execution.trial_snapshots)
    inconsistent_trials[post_index] = dataclasses.replace(
        post_snapshot,
        response=inconsistent_response,
    )
    inconsistent_execution = dataclasses.replace(
        execution,
        trial_snapshots=tuple(inconsistent_trials),
    )
    with pytest.raises(ContractViolation, match="one-sided consistency"):
        persist_standalone_execution(
            writer=writer,
            request=request,
            execution=inconsistent_execution,
            context=context,
        )
    assert not committed_markers(writer.root)
