"""M00 result extension owned by the M03 single-spine module.

The extension deliberately keeps accepted points, committed events, rejected
attempts, and derived products in different dataset classes.  The records here
only add M03 payloads; authoritative point/event/receipt identities remain
owned by M00 (and numerical trial identities remain owned by M02).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

from spine_sim.foundation.errors import ContractViolation
from spine_sim.foundation.models import (
    CertificationStatus,
    Maturity,
    RecordBase,
    SourceIdentity,
    StatusTuple,
)
from spine_sim.foundation.registry import (
    CompatibilityClass,
    DataClassification,
    DatasetClass,
    DatasetDescriptor,
    FieldMetadata,
    RelationDescriptor,
    ResultExtensionDescriptor,
)

from .contracts import M03_SCHEMA_VERSION, Matrix3, Vector2, Vector3, Vector6, m03_maturity

M03_EXTENSION_SCHEMA_VERSION = M03_SCHEMA_VERSION

RUN_REQUESTS_DATASET = "m03.run_requests"
ACCEPTED_STATE_HISTORY_DATASET = "m03.accepted_state_history"
SUPPORT_CANDIDATE_HISTORY_DATASET = "m03.support_candidate_history"
CONTACT_SUPPORT_HISTORY_DATASET = "m03.contact_support_history"
COMMITTED_EVENT_PAYLOADS_DATASET = "m03.committed_event_payloads"
RELEASE_OPERATION_HISTORY_DATASET = "m03.release_operation_history"
REJECTED_DIAGNOSTICS_DATASET = "m03.rejected_diagnostics"
WORK_LEDGER_DATASET = "m03.work_ledger"
CONTACT_CYCLE_RECORDS_DATASET = "m03.contact_cycle_records"
CAPABILITY_STATUS_DATASET = "m03.capability_status"
DERIVED_SUMMARIES_DATASET = "m03.derived_summaries"
PLOT_RECIPE_MANIFEST_DATASET = "m03.plot_recipe_manifest"

M03_DATASET_IDS = (
    RUN_REQUESTS_DATASET,
    ACCEPTED_STATE_HISTORY_DATASET,
    SUPPORT_CANDIDATE_HISTORY_DATASET,
    CONTACT_SUPPORT_HISTORY_DATASET,
    COMMITTED_EVENT_PAYLOADS_DATASET,
    RELEASE_OPERATION_HISTORY_DATASET,
    REJECTED_DIAGNOSTICS_DATASET,
    WORK_LEDGER_DATASET,
    CONTACT_CYCLE_RECORDS_DATASET,
    CAPABILITY_STATUS_DATASET,
    DERIVED_SUMMARIES_DATASET,
    PLOT_RECIPE_MANIFEST_DATASET,
)

CORE_ACCEPTED_POINTS_DATASET = "core.accepted_points.common"
CORE_COMMITTED_EVENTS_DATASET = "core.committed_events.events"
CORE_REJECTED_TRIALS_DATASET = "core.rejected_trials.diagnostics"
CORE_COMMIT_RECEIPTS_DATASET = "core.transactions.receipts"


@dataclass(frozen=True, slots=True)
class M03ResultRecord(RecordBase):
    """Mandatory schema/status/source/maturity columns for every M03 row."""

    run_id: str
    case_id: str
    schema_version: str
    status: StatusTuple
    source_identity: SourceIdentity
    maturity: Maturity
    certification_status: CertificationStatus

    def __post_init__(self) -> None:
        if self.schema_version != M03_EXTENSION_SCHEMA_VERSION:
            raise ContractViolation("unsupported M03 result-extension schema")
        if self.status.certification_status is not self.certification_status:
            raise ContractViolation("M03 row status and certification metadata disagree")
        if self.certification_status is not CertificationStatus.NOT_CERTIFIABLE:
            raise ContractViolation("M03 analytic/synthetic outputs are not certifiable")


@dataclass(frozen=True, slots=True)
class RunRequestRecord(M03ResultRecord):
    __dataset_id__ = RUN_REQUESTS_DATASET

    request_id: str
    request_kind: str
    contract_id: str
    contract_version: str
    call_mode: str
    request_hash: str
    resolved_config_hash: str
    parameter_bundle_id: str
    parameter_bundle_hash: str
    surface_query_handle_id: str
    surface_realization_id: str
    resolved_request_payload: dict[str, Any]
    diagnostic_level: str
    output_policy: str
    commit_receipt_id: str | None


@dataclass(frozen=True, slots=True)
class AcceptedStateHistoryRecord(M03ResultRecord):
    __dataset_id__ = ACCEPTED_STATE_HISTORY_DATASET

    state_record_id: str
    point_id: str
    parent_point_id: str | None
    accepted_state_id: str
    parent_accepted_state_id: str
    commit_receipt_id: str | None
    config_hash: str
    parameter_bundle_id: str
    surface_realization_id: str
    accepted_point_index: int
    x_total_mm: float
    drag_elapsed_time_s: float
    operation_phase: str
    operation_path_coordinate_mm: float
    cycle_id: str
    event_sequence: int
    base_position_global_mm: Vector3
    base_rotation_global_from_base: Matrix3
    root_position_global_mm: Vector3
    tip_center_global_mm: Vector3
    a0_global: Vector3
    a_t_global: Vector3
    global_from_local: Matrix3
    local_from_global: Matrix3
    reference_point_id: str
    query_receipt_id: str
    query_lod_purpose: str
    query_error_bound_mm: float
    query_quality: str
    query_domain_status: str
    query_nonsmooth: bool
    query_nonunique: bool
    active_candidate_ids: tuple[str, ...]
    active_support_ids: tuple[str, ...]
    full_body_minimum_clearance_mm: float
    cone_clearance_mm: float
    shaft_clearance_mm: float
    mount_clearance_mm: float
    wrench_a_on_b_global_at_o_n_n_mm: Vector6
    opposite_wrench_b_on_a_global_at_o_n_n_mm: Vector6
    grip_resistance_rx_n: float
    task_resistance_n: float
    task_direction_global: Vector3
    force_resolution_n: float
    beam_tip_translation_global_mm: Vector3
    beam_tip_rotation_global_rad: Vector3
    beam_tip_translation_needle_mm: Vector3
    beam_tip_rotation_needle_rad: Vector3
    beam_root_force_global_n: Vector3
    beam_root_moment_global_n_mm: Vector3
    section_resultants_needle_n_n_mm: Vector6
    beam_energy_n_mm: float
    beam_model_state: str
    spring_state: str
    spring_compression_mm: float
    spring_remaining_travel_mm: float
    spring_force_n: float
    spring_hard_stop_reaction_n: float
    spring_energy_n_mm: float
    primary_mechanical_state: str
    contact_motion_states: tuple[str, ...]
    quality_solve_state: str
    geometric_candidate: bool
    loaded_contact: bool
    frictionally_stable: bool
    load_bearing: bool
    five_stage_reason_codes: tuple[str, ...]
    five_stage_evidence_refs: tuple[str, ...]
    residual_block_payloads: tuple[dict[str, Any], ...]
    complementarity_residual: float
    contact_soc_residual: float
    graph_residual: float
    jacobian_quality: str
    work_ledger_id: str
    damage_status: str
    strength_status: str
    failure_prediction_allowed: bool
    experimentally_validated: str
    not_certifiable: bool


@dataclass(frozen=True, slots=True)
class SupportCandidateHistoryRecord(M03ResultRecord):
    __dataset_id__ = SUPPORT_CANDIDATE_HISTORY_DATASET

    candidate_record_id: str
    point_id: str
    commit_receipt_id: str | None
    candidate_id: str
    support_id: str
    candidate_origin: str
    candidate_point_global_mm: Vector3
    feature_id: str
    chart_id: str
    legal_gap_mm: float
    effective_gap_mm: float
    cap_margin_mm: float
    normal_global: Vector3
    tangent_1_global: Vector3
    tangent_2_global: Vector3
    is_current_cominimal: bool
    is_previous_active: bool
    is_nearby_switch_candidate: bool
    local_minimum_verified: bool
    empty_ball_verified: bool
    full_candidate_comparison_verified: bool
    finite_cap_legal: bool
    query_receipt_id: str
    lod_purpose: str
    error_bound_mm: float
    coverage_certified: bool
    nonsmooth: bool
    nonunique: bool
    rejection_reason: str | None


@dataclass(frozen=True, slots=True)
class ContactSupportHistoryRecord(M03ResultRecord):
    __dataset_id__ = CONTACT_SUPPORT_HISTORY_DATASET

    contact_record_id: str
    point_id: str
    commit_receipt_id: str | None
    support_id: str
    candidate_id: str
    active: bool
    near_support: bool
    point_global_mm: Vector3
    normal_global: Vector3
    tangent_1_global: Vector3
    tangent_2_global: Vector3
    legal_gap_mm: float
    effective_gap_mm: float
    normal_multiplier_n: float
    tangential_multiplier_n: Vector2
    contact_force_global_n: Vector3
    objective_slip_increment_global_mm: Vector3
    objective_slip_increment_local_mm: Vector2
    motion_state: str
    support_migrated: bool
    friction_margin_n: float


@dataclass(frozen=True, slots=True)
class CommittedEventPayloadRecord(M03ResultRecord):
    __dataset_id__ = COMMITTED_EVENT_PAYLOADS_DATASET

    event_payload_id: str
    event_id: str
    commit_receipt_id: str | None
    event_kind: str
    raw_signed_guard: float
    raw_guard_unit: str
    zero_value: float
    admissible_side: str
    crossing_direction: str
    bracket_ref: str | None
    probe_refs: tuple[str, ...]
    earliestness_ref: str
    simultaneous_group_ids: tuple[str, ...]
    cascade_ids: tuple[str, ...]
    pre_response_hash: str
    event_response_hash: str
    transition_response_hash: str
    post_response_hash: str
    old_primary_state: str
    new_primary_state: str
    old_orthogonal_states: tuple[str, ...]
    new_orthogonal_states: tuple[str, ...]
    support_ids: tuple[str, ...]
    branch_id: str
    path_coordinate_mm: float
    cycle_id: str
    pre_wrench_global_at_o_n_n_mm: Vector6
    event_wrench_global_at_o_n_n_mm: Vector6
    post_wrench_global_at_o_n_n_mm: Vector6
    pre_beam_energy_n_mm: float
    post_beam_energy_n_mm: float
    pre_spring_energy_n_mm: float
    post_spring_energy_n_mm: float
    remaining_stored_energy_n_mm: float
    released_recoverable_energy_n_mm: float
    one_sided_consistency: bool


@dataclass(frozen=True, slots=True)
class ReleaseOperationHistoryRecord(M03ResultRecord):
    __dataset_id__ = RELEASE_OPERATION_HISTORY_DATASET

    operation_record_id: str
    point_id: str
    commit_receipt_id: str | None
    event_id: str | None
    cycle_id: str
    operation_phase: str
    segment_id: str
    interpolation: str
    path_coordinate_kind: str
    path_coordinate_mm: float
    x_total_mm: float
    physical_operation_time_s: float | None
    physical_operation_time_status: StatusTuple
    swept_envelope_id: str
    signed_guard_payloads: tuple[dict[str, Any], ...]
    quality_gate_passed: bool
    termination_kind: str
    lifecycle_kind: str
    remaining_travel_mm: float
    remaining_stored_energy_n_mm: float


@dataclass(frozen=True, slots=True)
class RejectedDiagnosticRecord(M03ResultRecord):
    __dataset_id__ = REJECTED_DIAGNOSTICS_DATASET

    diagnostic_id: str
    trial_id: str
    attempt_kind: str
    parent_point_id: str
    parent_accepted_state_id: str
    reason_family: str
    reason_code: str
    failure_axis: str
    raw_residual: float
    raw_residual_unit: str
    raw_guard: float | None
    raw_guard_unit: str | None
    solver_trace_ref: str | None
    surface_quality: str
    rollback_token: str
    accepted_state_advanced: bool
    path_advanced: bool
    time_advanced: bool
    slip_advanced: bool
    work_advanced: bool
    cycle_advanced: bool
    event_history_advanced: bool

    def __post_init__(self) -> None:
        M03ResultRecord.__post_init__(self)
        if any(
            (
                self.accepted_state_advanced,
                self.path_advanced,
                self.time_advanced,
                self.slip_advanced,
                self.work_advanced,
                self.cycle_advanced,
                self.event_history_advanced,
            )
        ):
            raise ContractViolation("rejected M03 diagnostics cannot advance accepted history")


@dataclass(frozen=True, slots=True)
class WorkLedgerRecord(M03ResultRecord):
    __dataset_id__ = WORK_LEDGER_DATASET

    work_ledger_id: str
    start_point_id: str
    end_point_id: str
    commit_receipt_id: str | None
    accepted_interval_index: int
    base_or_actuator_input_work_n_mm: float
    delta_beam_energy_n_mm: float
    delta_spring_energy_n_mm: float
    rigid_contact_energy_n_mm: float
    friction_dissipation_n_mm: float
    material_dissipation_n_mm: float
    returned_recoverable_energy_n_mm: float
    remaining_stored_energy_n_mm: float
    closure_error_n_mm: float
    normalized_closure_error: float
    cumulative_input_work_n_mm: float
    cumulative_friction_dissipation_n_mm: float
    cumulative_material_dissipation_n_mm: float
    cumulative_returned_energy_n_mm: float

    def __post_init__(self) -> None:
        M03ResultRecord.__post_init__(self)
        if self.rigid_contact_energy_n_mm != 0.0 or self.material_dissipation_n_mm != 0.0:
            raise ContractViolation("rigid/no-damage M03 energy channels must remain zero")
        if self.friction_dissipation_n_mm < 0.0 or self.returned_recoverable_energy_n_mm < 0.0:
            raise ContractViolation("dissipated/returned energy cannot be negative")


@dataclass(frozen=True, slots=True)
class ContactCycleRecord(M03ResultRecord):
    __dataset_id__ = CONTACT_CYCLE_RECORDS_DATASET

    cycle_record_id: str
    cycle_id: str
    lifecycle_kind: str
    start_point_id: str
    end_point_id: str | None
    commit_receipt_id: str | None
    support_ids: tuple[str, ...]
    release_event_id: str | None
    recontact_event_id: str | None
    reengagement_event_id: str | None
    start_x_total_mm: float
    end_x_total_mm: float | None
    start_drag_elapsed_time_s: float
    end_drag_elapsed_time_s: float | None
    right_censored: bool


@dataclass(frozen=True, slots=True)
class CapabilityStatusRecord(M03ResultRecord):
    __dataset_id__ = CAPABILITY_STATUS_DATASET

    capability_record_id: str
    branch_id: str
    capability_id: str
    capability_state: str
    reason_code: str
    material_model_id: str
    material_substate: str
    strength_substate: str
    return_path_status: str
    structural_model_status: str
    failure_prediction_allowed: bool
    damage_intents: tuple[str, ...]
    damage_write_set: tuple[str, ...]
    initiation_utilization: None
    current_capacity_scale: None
    fracture_energy_n_per_mm: None
    yield_margin: None
    fracture_margin: None
    experimentally_validated: str
    not_certifiable: bool
    commit_receipt_id: str | None

    def __post_init__(self) -> None:
        M03ResultRecord.__post_init__(self)
        if self.material_model_id != "no_damage" or self.failure_prediction_allowed:
            raise ContractViolation("M03 capability row must preserve no_damage boundary")
        if self.damage_intents or self.damage_write_set:
            raise ContractViolation("no_damage capability cannot expose damage writes")
        if any(
            value is not None
            for value in (
                self.initiation_utilization,
                self.current_capacity_scale,
                self.fracture_energy_n_per_mm,
                self.yield_margin,
                self.fracture_margin,
            )
        ):
            raise ContractViolation("damage/strength values are typed unavailable in M03")
        if self.experimentally_validated != "NOT_ASSESSED" or not self.not_certifiable:
            raise ContractViolation("M03 capability evidence cannot claim experimental validation")


@dataclass(frozen=True, slots=True)
class DerivedSummaryRecord(M03ResultRecord):
    __dataset_id__ = DERIVED_SUMMARIES_DATASET

    summary_id: str
    summary_kind: str
    included_dataset_classes: tuple[str, ...]
    definition_id: str
    definition_version: str
    definition_hash: str
    input_accepted_point_ids: tuple[str, ...]
    input_raw_links: tuple[str, ...]
    right_censored: bool
    summary_payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class PlotRecipeManifestRecord(M03ResultRecord):
    __dataset_id__ = PLOT_RECIPE_MANIFEST_DATASET

    summary_id: str
    summary_kind: str
    included_dataset_classes: tuple[str, ...]
    recipe_id: str
    recipe_family: str
    recipe_version: str
    definition_hash: str
    field_ids: tuple[str, ...]
    grouping_fields: tuple[str, ...]
    filter_fields: tuple[str, ...]
    event_kinds: tuple[str, ...]
    raw_dataset_links: tuple[str, ...]
    rejected_opt_in: bool
    smoothing: str
    missing_data_policy: str
    recipe_payload: dict[str, Any]


_M03_SCHEMA_MATURITY = m03_maturity()

_SHAPES: dict[str, tuple[int, ...]] = {
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

_UNITS: dict[str, str] = {
    "x_total_mm": "mm",
    "drag_elapsed_time_s": "s",
    "operation_path_coordinate_mm": "mm",
    "path_coordinate_mm": "mm",
    "start_x_total_mm": "mm",
    "end_x_total_mm": "mm",
    "start_drag_elapsed_time_s": "s",
    "end_drag_elapsed_time_s": "s",
    "physical_operation_time_s": "s",
    "remaining_travel_mm": "mm",
    "base_position_global_mm": "mm",
    "root_position_global_mm": "mm",
    "tip_center_global_mm": "mm",
    "candidate_point_global_mm": "mm",
    "point_global_mm": "mm",
    "legal_gap_mm": "mm",
    "effective_gap_mm": "mm",
    "cap_margin_mm": "mm",
    "error_bound_mm": "mm",
    "query_error_bound_mm": "mm",
    "full_body_minimum_clearance_mm": "mm",
    "cone_clearance_mm": "mm",
    "shaft_clearance_mm": "mm",
    "mount_clearance_mm": "mm",
    "beam_tip_translation_global_mm": "mm",
    "beam_tip_translation_needle_mm": "mm",
    "objective_slip_increment_global_mm": "mm",
    "objective_slip_increment_local_mm": "mm",
    "spring_compression_mm": "mm",
    "spring_remaining_travel_mm": "mm",
    "beam_tip_rotation_global_rad": "rad",
    "beam_tip_rotation_needle_rad": "rad",
    "normal_multiplier_n": "N",
    "tangential_multiplier_n": "N",
    "contact_force_global_n": "N",
    "grip_resistance_rx_n": "N",
    "task_resistance_n": "N",
    "force_resolution_n": "N",
    "beam_root_force_global_n": "N",
    "spring_force_n": "N",
    "spring_hard_stop_reaction_n": "N",
    "friction_margin_n": "N",
    "beam_root_moment_global_n_mm": "N*mm",
    "section_resultants_needle_n_n_mm": "N,N*mm",
    "wrench_a_on_b_global_at_o_n_n_mm": "N,N*mm",
    "opposite_wrench_b_on_a_global_at_o_n_n_mm": "N,N*mm",
    "pre_wrench_global_at_o_n_n_mm": "N,N*mm",
    "event_wrench_global_at_o_n_n_mm": "N,N*mm",
    "post_wrench_global_at_o_n_n_mm": "N,N*mm",
}


def _unit(name: str) -> str:
    if name in _UNITS:
        return _UNITS[name]
    if name.endswith("_n_mm") or "energy_n_mm" in name or "work_n_mm" in name:
        return "N*mm"
    if name.endswith("_mm"):
        return "mm"
    if name.endswith("_n"):
        return "N"
    return "1"


def _dtype(annotation: Any, name: str) -> str:
    if name in _SHAPES:
        return "float64"
    text = str(annotation)
    if text in {"float", "float | None"}:
        return "float64"
    if text in {"int", "int | None"}:
        return "int64"
    if text in {"bool", "bool | None"}:
        return "bool"
    return "utf8"


def _frame_reference(name: str) -> tuple[str, str]:
    if "global" in name or "wrench" in name:
        return "GLOBAL", "M03_BASE_REFERENCE_O"
    if "needle" in name:
        return "NEEDLE_LOCAL", "NEEDLE_ROOT"
    if name.endswith("_mm") or name.endswith("_s") or name.endswith("_n"):
        return "M03_DECLARED_SCALAR_FRAME", "M03_DECLARED_PATH_OR_ENTITY"
    return "NOT_APPLICABLE", "NOT_APPLICABLE"


def _fields(
    dataset_id: str,
    record_type: type[RecordBase],
    classification: DataClassification,
    primary_keys: tuple[str, ...],
) -> tuple[FieldMetadata, ...]:
    indices = tuple(dict.fromkeys(("run_id", "case_id", *primary_keys)))
    cadence = {
        DatasetClass.ACCEPTED: "each committed accepted point or point-by-entity row",
        DatasetClass.EVENT: "each committed event/operation/cycle lifecycle row",
        DatasetClass.REJECTED: "each rejected trial/probe/branch/rollback",
        DatasetClass.TRANSACTION: "once per resolved run request under receipt transaction",
        DatasetClass.SUMMARY: "versioned derived rebuild or recipe publication",
    }
    dataset_class = _CLASS_BY_DATASET[dataset_id]
    result: list[FieldMetadata] = []
    for item in dataclasses.fields(record_type):
        name = item.name
        unit = _unit(name)
        frame, reference = _frame_reference(name)
        shape = _SHAPES.get(name, ())
        dtype = _dtype(item.type, name)
        optional = "None" in str(item.type) or item.type is None
        result.append(
            FieldMetadata(
                field_id=f"{dataset_id}.{name}",
                namespace="m03",
                owner_module="M03",
                semantics=(
                    f"M03 {dataset_id.rsplit('.', 1)[-1]} {name.replace('_', ' ')}; "
                    "meaning and sampling are frozen by M03_SINGLE_SPINE_REQUIREMENTS 1.0.0"
                ),
                classification=classification,
                dtype=dtype,
                shape=shape,
                dimensions=tuple(f"component_{index}" for index in range(len(shape))),
                raggedness="fixed_shape" if shape else "scalar_or_canonical_json",
                unit=unit,
                frame=frame,
                reference_point=reference,
                sign_semantics="declared M03 global/local/path convention",
                action_semantics=(
                    "A_on_B contact action at declared O for wrench/force fields; "
                    "otherwise owner state/evidence semantics"
                ),
                indices=indices,
                sampling_cadence=cadence[dataset_class],
                storage_frequency=cadence[dataset_class],
                ownership=(
                    "M03 receipt-backed canonical raw"
                    if classification is DataClassification.CANONICAL_RAW
                    else "M03 isolated diagnostic"
                    if classification is DataClassification.DIAGNOSTIC
                    else "M03 rebuildable derived product with raw links"
                ),
                null_policy=(
                    "typed null only with explicit capability/status/reason"
                    if optional
                    else "not_null"
                ),
                source_identity=SourceIdentity.DEV_POLICY,
                authority_refs=(
                    "M03_SINGLE_SPINE_REQUIREMENTS 1.0.0 §11-14",
                    "A_TO_B 1.0.0",
                    "M00_FOUNDATION_REQUIREMENTS 1.0.0 §9",
                ),
                maturity=_M03_SCHEMA_MATURITY,
                introduced_version=M03_EXTENSION_SCHEMA_VERSION,
                deprecated_version=None,
                storage_dataset=dataset_id,
                encoding="parquet_zstd_lossless",
                precision="float64" if dtype == "float64" else "exact_or_canonical_json",
                required=not optional,
            )
        )
    return tuple(result)


_CLASS_BY_DATASET = {
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


def _dataset(
    dataset_id: str,
    record_type: type[RecordBase],
    primary_keys: tuple[str, ...],
    *,
    default_visible: bool,
) -> DatasetDescriptor:
    dataset_class = _CLASS_BY_DATASET[dataset_id]
    classification = {
        DatasetClass.ACCEPTED: DataClassification.CANONICAL_RAW,
        DatasetClass.EVENT: DataClassification.CANONICAL_RAW,
        DatasetClass.REJECTED: DataClassification.DIAGNOSTIC,
        DatasetClass.TRANSACTION: DataClassification.CANONICAL_RAW,
        DatasetClass.SUMMARY: DataClassification.DERIVED,
    }[dataset_class]
    return DatasetDescriptor(
        dataset_id=dataset_id,
        namespace="m03",
        owner_module="M03",
        schema_version=M03_EXTENSION_SCHEMA_VERSION,
        dataset_class=dataset_class,
        record_type=record_type,
        fields=_fields(dataset_id, record_type, classification, primary_keys),
        primary_keys=primary_keys,
        partition_keys=("case_id",),
        default_visible=default_visible,
        source_identity=SourceIdentity.DEV_POLICY,
    )


def _core_relation(
    suffix: str,
    left_dataset: str,
    left_key: str,
    right_dataset: str,
    right_key: str,
) -> RelationDescriptor:
    return RelationDescriptor(
        relation_id=f"m03.relation.{suffix}",
        left_dataset=left_dataset,
        right_dataset=right_dataset,
        left_keys=(left_key,),
        right_keys=(right_key,),
        cardinality="many-to-one",
    )


def m03_result_extension() -> ResultExtensionDescriptor:
    """Return the complete frozen 12-dataset ``m03`` registry extension."""

    tables = (
        _dataset(RUN_REQUESTS_DATASET, RunRequestRecord, ("request_id",), default_visible=True),
        _dataset(
            ACCEPTED_STATE_HISTORY_DATASET,
            AcceptedStateHistoryRecord,
            ("state_record_id",),
            default_visible=True,
        ),
        _dataset(
            SUPPORT_CANDIDATE_HISTORY_DATASET,
            SupportCandidateHistoryRecord,
            ("candidate_record_id",),
            default_visible=True,
        ),
        _dataset(
            CONTACT_SUPPORT_HISTORY_DATASET,
            ContactSupportHistoryRecord,
            ("contact_record_id",),
            default_visible=True,
        ),
        _dataset(
            COMMITTED_EVENT_PAYLOADS_DATASET,
            CommittedEventPayloadRecord,
            ("event_payload_id",),
            default_visible=True,
        ),
        _dataset(
            RELEASE_OPERATION_HISTORY_DATASET,
            ReleaseOperationHistoryRecord,
            ("operation_record_id",),
            default_visible=True,
        ),
        _dataset(
            REJECTED_DIAGNOSTICS_DATASET,
            RejectedDiagnosticRecord,
            ("diagnostic_id",),
            default_visible=False,
        ),
        _dataset(
            WORK_LEDGER_DATASET,
            WorkLedgerRecord,
            ("work_ledger_id",),
            default_visible=True,
        ),
        _dataset(
            CONTACT_CYCLE_RECORDS_DATASET,
            ContactCycleRecord,
            ("cycle_record_id",),
            default_visible=True,
        ),
        _dataset(
            CAPABILITY_STATUS_DATASET,
            CapabilityStatusRecord,
            ("capability_record_id",),
            default_visible=True,
        ),
        _dataset(
            DERIVED_SUMMARIES_DATASET,
            DerivedSummaryRecord,
            ("summary_id",),
            default_visible=True,
        ),
        _dataset(
            PLOT_RECIPE_MANIFEST_DATASET,
            PlotRecipeManifestRecord,
            ("recipe_id",),
            default_visible=True,
        ),
    )
    relations = (
        _core_relation(
            "accepted_state_to_point",
            ACCEPTED_STATE_HISTORY_DATASET,
            "point_id",
            CORE_ACCEPTED_POINTS_DATASET,
            "point_id",
        ),
        _core_relation(
            "candidate_to_point",
            SUPPORT_CANDIDATE_HISTORY_DATASET,
            "point_id",
            CORE_ACCEPTED_POINTS_DATASET,
            "point_id",
        ),
        _core_relation(
            "contact_to_point",
            CONTACT_SUPPORT_HISTORY_DATASET,
            "point_id",
            CORE_ACCEPTED_POINTS_DATASET,
            "point_id",
        ),
        _core_relation(
            "event_payload_to_event",
            COMMITTED_EVENT_PAYLOADS_DATASET,
            "event_id",
            CORE_COMMITTED_EVENTS_DATASET,
            "event_id",
        ),
        _core_relation(
            "rejected_to_trial",
            REJECTED_DIAGNOSTICS_DATASET,
            "trial_id",
            CORE_REJECTED_TRIALS_DATASET,
            "trial_id",
        ),
        _core_relation(
            "work_to_end_point",
            WORK_LEDGER_DATASET,
            "end_point_id",
            CORE_ACCEPTED_POINTS_DATASET,
            "point_id",
        ),
        _core_relation(
            "accepted_state_to_receipt",
            ACCEPTED_STATE_HISTORY_DATASET,
            "commit_receipt_id",
            CORE_COMMIT_RECEIPTS_DATASET,
            "receipt_id",
        ),
    )
    return ResultExtensionDescriptor(
        namespace="m03",
        owner_module="M03",
        extension_schema_version=M03_EXTENSION_SCHEMA_VERSION,
        tables=tables,
        arrays=(),
        relations=relations,
        common_keys=("run_id", "case_id"),
        source_identity=SourceIdentity.DEV_POLICY,
        maturity=_M03_SCHEMA_MATURITY,
        compatibility_class=CompatibilityClass.ADDITIVE_MINOR,
    )


def m03_dataset_ids() -> tuple[str, ...]:
    return M03_DATASET_IDS


def m03_field_metadata(field_id: str) -> FieldMetadata:
    for dataset in m03_result_extension().tables:
        for field in dataset.fields:
            if field.field_id == field_id:
                return field
    raise KeyError(field_id)


__all__ = [
    "ACCEPTED_STATE_HISTORY_DATASET",
    "CAPABILITY_STATUS_DATASET",
    "COMMITTED_EVENT_PAYLOADS_DATASET",
    "CONTACT_CYCLE_RECORDS_DATASET",
    "CONTACT_SUPPORT_HISTORY_DATASET",
    "DERIVED_SUMMARIES_DATASET",
    "M03_DATASET_IDS",
    "PLOT_RECIPE_MANIFEST_DATASET",
    "REJECTED_DIAGNOSTICS_DATASET",
    "RELEASE_OPERATION_HISTORY_DATASET",
    "RUN_REQUESTS_DATASET",
    "SUPPORT_CANDIDATE_HISTORY_DATASET",
    "WORK_LEDGER_DATASET",
    "AcceptedStateHistoryRecord",
    "CapabilityStatusRecord",
    "CommittedEventPayloadRecord",
    "ContactCycleRecord",
    "ContactSupportHistoryRecord",
    "DerivedSummaryRecord",
    "PlotRecipeManifestRecord",
    "RejectedDiagnosticRecord",
    "ReleaseOperationHistoryRecord",
    "RunRequestRecord",
    "SupportCandidateHistoryRecord",
    "WorkLedgerRecord",
    "m03_dataset_ids",
    "m03_field_metadata",
    "m03_result_extension",
]
