"""Generate the frozen M00 VALIDATION_ONLY bundle; contains no physical model."""

from __future__ import annotations

import argparse
import dataclasses
import json
import platform
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .canonical import semantic_hash, source_file_hash, stable_content_id
from .config import (
    ConfigField,
    ConfigLayer,
    ConfigLayerLevel,
    ConfigSchema,
    ParameterOwnership,
    resolve_config,
)
from .integrity import VerifyMode
from .models import (
    AcceptedPointBase,
    AttemptOutcome,
    AuthorityRef,
    CapabilityStatus,
    CertificationStatus,
    CommittedEventBase,
    Maturity,
    PhysicalFeasibility,
    RecordBase,
    RegisteredArrayPayload,
    RejectedTrialBase,
    SourceIdentity,
    StatusTuple,
    SummaryBase,
    ValuePresence,
    ValueProvenance,
)
from .reader import ResultReader
from .registry import (
    BUNDLE_SCHEMA_VERSION,
    RESULT_API_VERSION,
    ArrayDescriptor,
    CompatibilityClass,
    DataClassification,
    DatasetClass,
    DatasetDescriptor,
    FieldMetadata,
    RelationDescriptor,
    ResultExtensionDescriptor,
    SchemaRegistry,
)
from .replay import make_replay_manifest
from .writer import ResultWriter, make_run_envelope

DEMO_DESIGN_ID = stable_content_id("design", {"fixture": "M00_VALIDATION_ONLY"})
DEMO_SEED_ID = stable_content_id("seed", {"fixture": "M00_VALIDATION_ONLY", "rng": "NONE"})
DEMO_SURFACE_ID = stable_content_id(
    "surface", {"fixture": "M00_VALIDATION_ONLY", "surface": "NONE"}
)
DEMO_CASE_ID = stable_content_id(
    "case",
    {
        "design_id": DEMO_DESIGN_ID,
        "seed_id": DEMO_SEED_ID,
        "surface_realization_id": DEMO_SURFACE_ID,
    },
)
DEMO_DATASET_ID = "validation_m00.accepted_points.samples"
DEMO_ARRAY_FIELD_ID = "validation_m00.arrays.sample_matrix"


@dataclass(frozen=True, slots=True)
class ValidationOnlySample(RecordBase):
    __dataset_id__ = DEMO_DATASET_ID

    run_id: str
    case_id: str
    point_id: str
    sample_value: float
    source_identity: SourceIdentity


def _field(
    dataset: str,
    name: str,
    dtype: str,
    *,
    unit: str = "1",
    shape: tuple[int | None, ...] = (),
    frame: str = "NOT_APPLICABLE",
    reference: str = "NOT_APPLICABLE",
) -> FieldMetadata:
    return FieldMetadata(
        field_id=f"{dataset}.{name}",
        namespace="validation_m00",
        owner_module="M00_VALIDATION_FIXTURE",
        semantics=f"VALIDATION_ONLY synthetic {name.replace('_', ' ')}; no physical meaning",
        classification=DataClassification.CANONICAL_RAW,
        dtype=dtype,
        shape=shape,
        dimensions=("validation_row", "validation_column") if shape else (),
        raggedness="fixed" if shape else "scalar",
        unit=unit,
        frame=frame,
        reference_point=reference,
        sign_semantics="VALIDATION_ONLY arbitrary positive direction",
        action_semantics="NOT_APPLICABLE_NO_PHYSICS",
        indices=("run_id", "case_id", "point_id"),
        sampling_cadence="per_accepted_validation_point",
        storage_frequency="every_validation_fixture_record",
        ownership="accepted" if dataset == DEMO_DATASET_ID else "array",
        null_policy="not_null",
        source_identity=SourceIdentity.VALIDATION_ONLY,
        authority_refs=("M00_FOUNDATION_REQUIREMENTS 1.0.0 §15.4",),
        maturity=Maturity.validation_only_implemented(),
        introduced_version="1.0.0",
        deprecated_version=None,
        storage_dataset=dataset,
        encoding="parquet_zstd_lossless" if not shape else "zarr_v3_lossless",
        precision="float64" if dtype == "float64" else "exact",
        required=True,
    )


def validation_extension() -> ResultExtensionDescriptor:
    dataset = DatasetDescriptor(
        dataset_id=DEMO_DATASET_ID,
        namespace="validation_m00",
        owner_module="M00_VALIDATION_FIXTURE",
        schema_version="1.0.0",
        dataset_class=DatasetClass.ACCEPTED,
        record_type=ValidationOnlySample,
        fields=(
            _field(DEMO_DATASET_ID, "run_id", "utf8"),
            _field(DEMO_DATASET_ID, "case_id", "utf8"),
            _field(DEMO_DATASET_ID, "point_id", "utf8"),
            _field(DEMO_DATASET_ID, "sample_value", "float64"),
            _field(DEMO_DATASET_ID, "source_identity", "utf8"),
        ),
        primary_keys=("point_id",),
        partition_keys=("case_id",),
        default_visible=False,
        source_identity=SourceIdentity.VALIDATION_ONLY,
    )
    array_field = _field(
        "validation_m00.arrays",
        "sample_matrix",
        "float64",
        unit="1",
        shape=(None, None),
        frame="M00_VALIDATION_FRAME",
        reference="M00_VALIDATION_ORIGIN",
    )
    return ResultExtensionDescriptor(
        namespace="validation_m00",
        owner_module="M00_VALIDATION_FIXTURE",
        extension_schema_version="1.0.0",
        tables=(dataset,),
        arrays=(ArrayDescriptor(array_field, "1.0.0", default_chunk_shape=(2, 2)),),
        relations=(
            RelationDescriptor(
                "validation_m00.relation.core_point_to_sample",
                "core.accepted_points.common",
                DEMO_DATASET_ID,
                ("point_id",),
                ("point_id",),
                "one-to-one",
            ),
        ),
        common_keys=("run_id", "case_id", "point_id"),
        source_identity=SourceIdentity.VALIDATION_ONLY,
        maturity=Maturity.validation_only_implemented(),
        compatibility_class=CompatibilityClass.ADDITIVE_MINOR,
    )


def _demo_schema() -> ConfigSchema:
    return ConfigSchema(
        "M00_VALIDATION_ONLY_CONFIG",
        "1.0.0",
        (
            ConfigField(
                "foundation.canonical_numeric_dtype",
                str,
                ParameterOwnership.NUMERICAL_CONFIGURATION,
                "M00_FOUNDATION_REQUIREMENTS 1.0.0 §3.2",
                SourceIdentity.ACCEPTED_AUTHORITY,
                locked=True,
                enum_values=("float64",),
            ),
            ConfigField(
                "validation_only.sequence_scale",
                float,
                ParameterOwnership.RUN_AND_PLOT_CONFIGURATION,
                "M00_FOUNDATION_REQUIREMENTS 1.0.0 §15.4",
                SourceIdentity.VALIDATION_ONLY,
                dimension="dimensionless",
            ),
        ),
    )


def _resolved_config(kind: str) -> Any:
    schema = _demo_schema()
    authority = ConfigLayer(
        ConfigLayerLevel.L1_AUTHORITY,
        "M00_VALIDATION_ONLY:inline-authority",
        semantic_hash("float64"),
        {"foundation": {"canonical_numeric_dtype": "float64"}},
        SourceIdentity.ACCEPTED_AUTHORITY,
    )
    validation = ConfigLayer(
        ConfigLayerLevel.L2_ISOLATED,
        "M00_VALIDATION_ONLY:inline-fixture",
        semantic_hash({"sequence_scale": 1.0}),
        {"validation_only": {"sequence_scale": {"value": 1.0, "unit": "1"}}},
        SourceIdentity.VALIDATION_ONLY,
        "validation_only",
    )
    return resolve_config(schema, (authority, validation), config_kind=kind)


def _status(
    *, outcome: AttemptOutcome = AttemptOutcome.ACCEPTED, reason: str = "VALIDATION_ONLY"
) -> StatusTuple:
    return StatusTuple(
        ValuePresence.PRESENT,
        CapabilityStatus.SUPPORTED,
        outcome,
        PhysicalFeasibility.NOT_ASSESSED,
        CertificationStatus.NOT_CERTIFIABLE,
        reason,
        "M00 software validation only; no physical interpretation",
        ("M00_FOUNDATION_REQUIREMENTS 1.0.0",),
    )


def _authority_refs(source_hashes: dict[str, str]) -> tuple[AuthorityRef, ...]:
    return tuple(
        AuthorityRef(path, "frozen/current", digest, "whole-file")
        for path, digest in sorted(source_hashes.items())
    )


def _point(
    run_id: str,
    index: int,
    parent_state_id: str,
    state_id: str,
    source_hashes: dict[str, str],
) -> AcceptedPointBase:
    point_id = stable_content_id("point", {"case": DEMO_CASE_ID, "index": index, "state": state_id})
    provenance = (
        ValueProvenance(
            "M00_VALIDATION_ONLY",
            semantic_hash(index),
            "sample_value",
            SourceIdentity.VALIDATION_ONLY,
        ),
    )
    return AcceptedPointBase(
        run_id=run_id,
        case_id=DEMO_CASE_ID,
        design_id=DEMO_DESIGN_ID,
        seed_id=DEMO_SEED_ID,
        surface_realization_id=DEMO_SURFACE_ID,
        point_id=point_id,
        accepted_point_index=index,
        accepted_state_id=state_id,
        parent_state_id=parent_state_id,
        commit_receipt_id=None,
        operation_kind="M00_VALIDATION_ONLY",
        stage="VALIDATION_SEQUENCE",
        path_kind="VALIDATION_INDEX",
        path_coordinate=float(index),
        path_unit="1",
        accepted_increment=1.0,
        physical_time_value=None,
        physical_time_status=StatusTuple(
            ValuePresence.NULL,
            CapabilityStatus.NOT_APPLICABLE,
            AttemptOutcome.NOT_ATTEMPTED,
            PhysicalFeasibility.NOT_ASSESSED,
            CertificationStatus.NOT_CERTIFIABLE,
            "NO_PHYSICAL_TIME",
            "validation sequence has no physical time",
        ),
        event_sequence=index,
        simultaneous_group_ids=(),
        cascade_ids=(),
        module_payload_refs=(f"validation_m00.sample:{index}",),
        residual_refs=(),
        graph_refs=(),
        quality_refs=("M00_VALIDATION_ONLY",),
        work_ledger_refs=(),
        source_identity=SourceIdentity.VALIDATION_ONLY,
        requirement_origin="M00_FOUNDATION_REQUIREMENTS 1.0.0 §15.4",
        value_provenance=provenance,
        authority_refs=_authority_refs(source_hashes),
        maturity=Maturity.validation_only_implemented(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        request_hash=semantic_hash({"validation_index": index}),
        response_hash=semantic_hash({"validation_state": state_id}),
        replay_step_hash=semantic_hash(
            {"index": index, "parent": parent_state_id, "state": state_id}
        ),
    )


def _git_state(repo_root: Path) -> tuple[str, str]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
        ).strip()
        dirty = (
            "dirty"
            if subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=repo_root, text=True
            ).strip()
            else "clean"
        )
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE", "UNAVAILABLE"
    return commit, dirty


def generate_validation_bundle(
    destination: str | Path,
    *,
    parquet_compression: str = "zstd",
    zarr_compression_level: int = 3,
    zarr_chunk_shape: tuple[int, ...] = (2, 2),
) -> Path:
    """Write and read back the exact §15.4 M00 no-physics fixture."""

    output = Path(destination)
    repo_root = Path(__file__).resolve().parents[3]
    source_paths = (
        repo_root / "docs/simulator_development/requirements/M00_FOUNDATION_REQUIREMENTS.md",
        repo_root / "theory/system/SYSTEM_INTEGRATED_MODEL.md",
    )
    source_hashes = {
        path.relative_to(repo_root).as_posix(): source_file_hash(path) for path in source_paths
    }
    resolved_run = _resolved_config("resolved_run_config")
    resolved_case = _resolved_config("resolved_case_config")
    registry = SchemaRegistry()
    registry.register_extension(validation_extension())
    registry_hash = registry.freeze()
    git_commit, dirty_status = _git_state(repo_root)
    replay_seed = {
        "case_execution_plan": [DEMO_CASE_ID],
        "idempotency_keys": ["M00_VALIDATION_ONLY_TX_1", "M00_VALIDATION_ONLY_TX_2"],
        "runtime": platform.python_version(),
    }
    envelope = make_run_envelope(
        registry_hash=registry_hash,
        resolved_run_config=resolved_run,
        operation_kind="M00_VALIDATION_ONLY",
        operation_profile="NO_PHYSICS_FOUNDATION_DEMO",
        source_file_hashes=source_hashes,
        replay_manifest=replay_seed,
        git_commit=git_commit,
        dirty_status=dirty_status,
        provenance_labels=("VALIDATION_ONLY", "no_physics", "not_certifiable"),
    )
    replay = make_replay_manifest(
        run_id=envelope.run_id,
        run_fingerprint=envelope.run_fingerprint,
        result_api_version=RESULT_API_VERSION,
        bundle_schema_version=BUNDLE_SCHEMA_VERSION,
        resolved_run_config_hash=resolved_run.semantic_hash,
        resolved_case_config_hashes={DEMO_CASE_ID: resolved_case.semantic_hash},
        source_hashes=source_hashes,
        registry_hash=registry_hash,
        git_commit=git_commit,
        dirty_status=dirty_status,
        case_execution_plan=(DEMO_CASE_ID,),
        idempotency_keys=("M00_VALIDATION_ONLY_TX_1", "M00_VALIDATION_ONLY_TX_2"),
        surface_identities=(DEMO_SURFACE_ID,),
    )
    replay_payload = dataclasses.asdict(replay)
    replay_hash = semantic_hash(replay_payload)
    envelope = dataclasses.replace(
        envelope,
        replay_manifest_id=replay.replay_manifest_id,
        replay_manifest_hash=replay_hash,
    )
    writer = ResultWriter.create_run_bundle(
        output,
        registry=registry,
        run_envelope=envelope,
        parquet_compression=parquet_compression,
        zarr_compression_level=zarr_compression_level,
        zarr_chunk_shape=zarr_chunk_shape,
    )
    writer.write_resolved_config_and_provenance(
        resolved_run,
        provenance={
            "source_identity": "VALIDATION_ONLY",
            "requirement_origin": "M00_FOUNDATION_REQUIREMENTS 1.0.0 §15.4",
            "authority_refs": source_hashes,
            "interpretation_exclusions": [
                "no_surface_physics",
                "no_contact",
                "no_friction",
                "no_beam_or_spring",
                "no_array_or_C_physics",
            ],
        },
        replay_manifest=replay_payload,
    )
    writer.create_case_shard(
        DEMO_CASE_ID,
        design_id=DEMO_DESIGN_ID,
        seed_id=DEMO_SEED_ID,
        surface_realization_id=DEMO_SURFACE_ID,
        resolved_case_config=resolved_case,
    )
    initial_state = stable_content_id("state", {"case": DEMO_CASE_ID, "index": -1})
    state_0 = stable_content_id("state", {"case": DEMO_CASE_ID, "index": 0})
    state_1 = stable_content_id("state", {"case": DEMO_CASE_ID, "index": 1})
    first = _point(envelope.run_id, 0, initial_state, state_0, source_hashes)
    tx1 = writer.begin_transaction(DEMO_CASE_ID, initial_state, "M00_VALIDATION_ONLY_TX_1")
    tx1.stage_accepted_point(
        first,
        ValidationOnlySample(
            envelope.run_id, DEMO_CASE_ID, first.point_id, 1.0, SourceIdentity.VALIDATION_ONLY
        ),
    )
    tx1.stage_state_and_ledger_references(("VALIDATION_ONLY_LEDGER_EMPTY",))
    tx1.prepare()
    receipt_1 = tx1.commit()
    second = _point(envelope.run_id, 1, state_0, state_1, source_hashes)
    event_id = stable_content_id(
        "event", {"case": DEMO_CASE_ID, "index": 1, "kind": "VALIDATION_MARKER"}
    )
    event = CommittedEventBase(
        event_id=event_id,
        source_event_ids=("M00_VALIDATION_ONLY_SOURCE_EVENT",),
        hierarchy="VALIDATION_ONLY",
        entity_ids=("M00_VALIDATION_ENTITY",),
        run_id=envelope.run_id,
        case_id=DEMO_CASE_ID,
        design_id=DEMO_DESIGN_ID,
        seed_id=DEMO_SEED_ID,
        surface_realization_id=DEMO_SURFACE_ID,
        event_kind="VALIDATION_MARKER",
        raw_event_function=0.0,
        event_function_unit="1",
        numerical_scaling_id="NONE_VALIDATION_ONLY",
        path_coordinate=1.0,
        path_bracket=(0.9, 1.0),
        fraction_basis="VALIDATION_INDEX",
        localization_error=0.0,
        pre_event_accepted_state_id=state_0,
        event_point_trial_id="trial:M00_VALIDATION_EVENT_POINT",
        post_event_accepted_state_id=state_1,
        post_event_status=_status(),
        simultaneous_group_id=None,
        dependency_edges=(),
        cascade_round=0,
        pre_payload_refs=("validation:pre",),
        event_payload_refs=("validation:event",),
        post_payload_refs=("validation:post",),
        uncertainty_refs=(),
        recoverability="NOT_APPLICABLE_NO_PHYSICS",
        stability="NOT_APPLICABLE_NO_PHYSICS",
        terminal_classification="NON_TERMINAL_VALIDATION_MARKER",
        status=_status(),
        source_identity=SourceIdentity.VALIDATION_ONLY,
        maturity=Maturity.validation_only_implemented(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        committed=True,
        commit_receipt_id=None,
    )
    tx2 = writer.begin_transaction(DEMO_CASE_ID, state_0, "M00_VALIDATION_ONLY_TX_2")
    tx2.stage_accepted_point(
        second,
        ValidationOnlySample(
            envelope.run_id, DEMO_CASE_ID, second.point_id, 2.0, SourceIdentity.VALIDATION_ONLY
        ),
    )
    tx2.stage_committed_events(event)
    tx2.stage_chunked_array(
        RegisteredArrayPayload(
            DEMO_ARRAY_FIELD_ID,
            DEMO_CASE_ID,
            np.arange(16, dtype=np.float64).reshape(4, 4),
            np.ones((4, 4), dtype=np.bool_),
            np.zeros((4, 4), dtype=np.uint8),
            "1",
            "M00_VALIDATION_FRAME",
            "M00_VALIDATION_ORIGIN",
            SourceIdentity.VALIDATION_ONLY,
        )
    )
    tx2.stage_state_and_ledger_references((receipt_1.receipt_id, event_id))
    tx2.prepare()
    receipt_2 = tx2.commit()
    rejected = RejectedTrialBase(
        trial_id="trial:M00_VALIDATION_ONLY_REJECTED",
        run_id=envelope.run_id,
        case_id=DEMO_CASE_ID,
        parent_accepted_state_id=state_1,
        request_hash=semantic_hash("rejected-request"),
        candidate_hash=semantic_hash("rejected-candidate"),
        requested_path_target=2.0,
        status=StatusTuple(
            ValuePresence.NULL,
            CapabilityStatus.SUPPORTED,
            AttemptOutcome.REJECTED_TRIAL,
            PhysicalFeasibility.NOT_ASSESSED,
            CertificationStatus.NOT_CERTIFIABLE,
            "FAULT_INJECTION_VALIDATION_ONLY",
            "intentional rejected diagnostic",
            last_valid_state_id=state_1,
        ),
        reason_codes=("VALIDATION_ONLY_INTENTIONAL_REJECTION",),
        diagnostic_summary="Intentional M00 diagnostic; no physical meaning.",
        optional_full_payload_ref=None,
        last_valid_state_id=state_1,
        source_identity=SourceIdentity.VALIDATION_ONLY,
    )
    writer.record_rejected_trial(rejected)
    summary = SummaryBase(
        summary_id="summary:M00_VALIDATION_ONLY",
        summary_kind="VALIDATION_ONLY_CASE_SUMMARY",
        schema_version="1.0.0",
        algorithm_id="M00_VALIDATION_COUNT",
        algorithm_version="1.0.0",
        algorithm_hash=semantic_hash("count-two-accepted"),
        source_bundle_hash=semantic_hash((receipt_1.candidate_hash, receipt_2.candidate_hash)),
        source_receipt_set_hash=semantic_hash((receipt_1.receipt_id, receipt_2.receipt_id)),
        included_dataset_classes=("accepted", "event"),
        status_filters=("VALIDATION_ONLY",),
        case_id=DEMO_CASE_ID,
        design_id=DEMO_DESIGN_ID,
        seed_id=DEMO_SEED_ID,
        entity_scope=("M00_VALIDATION_ENTITY",),
        output_field_ids=(f"{DEMO_DATASET_ID}.sample_value",),
        source_identity=SourceIdentity.VALIDATION_ONLY,
        maturity=Maturity.validation_only_implemented(),
        certification_status=CertificationStatus.NOT_CERTIFIABLE,
        created_at_utc_ns=time.time_ns(),
    )
    writer.write_versioned_summary(summary)
    writer.finalize_case(DEMO_CASE_ID)
    writer.publish_run_manifest()
    reader = ResultReader.open(output, VerifyMode.FULL)
    points = reader.query(
        "core.accepted_points.common",
        ("point_id", "accepted_state_id", "parent_state_id"),
        include_non_default=True,
    ).read_all()
    if points.num_rows != 2:
        raise RuntimeError("VALIDATION_ONLY readback did not return two accepted points")
    return output


def catalog_overview(bundle: str | Path) -> dict[str, Any]:
    reader = ResultReader.open(bundle, VerifyMode.MANIFEST)
    default_catalog = reader.list_datasets()
    validation_catalog = reader.list_datasets(include_non_default=True, include_diagnostics=True)
    return {
        "bundle": Path(bundle).as_posix(),
        "label": "VALIDATION_ONLY / no_physics / not_certifiable",
        "bundle_semantic_hash": reader.bundle_info()["bundle_semantic_hash"],
        "default_dataset_count": len(default_catalog.entries),
        "opt_in_dataset_ids": [item.dataset_id for item in validation_catalog.entries],
        "explicit_validation_points": reader.query(
            "core.accepted_points.common",
            ("accepted_point_index", "accepted_state_id", "commit_receipt_id"),
            include_non_default=True,
        )
        .read_all()
        .to_pylist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the M00 VALIDATION_ONLY no-physics bundle"
    )
    parser.add_argument("destination", nargs="?", default="build/M00_VALIDATION_ONLY.spine-result")
    args = parser.parse_args()
    path = generate_validation_bundle(args.destination)
    print(json.dumps(catalog_overview(path), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
