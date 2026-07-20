"""Rebuildable, versioned M03 summaries derived from committed raw history.

The builders in this module intentionally accept only M03 accepted-history and
committed-event record types.  Rejected trials are therefore outside the input
boundary by construction.  Every returned summary retains its definition hash,
the accepted point identities, and links back to every raw record it consumed.
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import pairwise
from typing import Any

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation

from .result_extension import (
    ACCEPTED_STATE_HISTORY_DATASET,
    COMMITTED_EVENT_PAYLOADS_DATASET,
    CONTACT_CYCLE_RECORDS_DATASET,
    WORK_LEDGER_DATASET,
    AcceptedStateHistoryRecord,
    CommittedEventPayloadRecord,
    ContactCycleRecord,
    DerivedSummaryRecord,
    M03ResultRecord,
    WorkLedgerRecord,
)

M03_SUMMARY_DEFINITION_VERSION = "1.0.0"

FIRST_LOADED_CONTACT_DEFINITION_ID = "m03.summary.first_loaded_contact"
FIRST_LOAD_BEARING_DEFINITION_ID = "m03.summary.first_load_bearing"
FALSE_ENGAGEMENT_DEFINITION_ID = "m03.summary.false_engagement_episodes"
RELEASE_LIFECYCLE_DEFINITION_ID = "m03.summary.release_lifecycle"
CYCLE_PATH_FRACTION_DEFINITION_ID = "m03.summary.cycle_path_fractions"
MULTI_PEAK_DEFINITION_ID = "m03.summary.multi_peak_raw_links"
WORK_ENERGY_DEFINITION_ID = "m03.summary.work_energy"

M03_SUMMARY_DEFINITION_IDS = (
    FIRST_LOADED_CONTACT_DEFINITION_ID,
    FIRST_LOAD_BEARING_DEFINITION_ID,
    FALSE_ENGAGEMENT_DEFINITION_ID,
    RELEASE_LIFECYCLE_DEFINITION_ID,
    CYCLE_PATH_FRACTION_DEFINITION_ID,
    MULTI_PEAK_DEFINITION_ID,
    WORK_ENERGY_DEFINITION_ID,
)

_DEFINITION_TEXT: dict[str, str] = {
    FIRST_LOADED_CONTACT_DEFINITION_ID: (
        "Earliest committed accepted point with loaded_contact=true on cumulative x_total_mm; "
        "absence through the declared observation limit is right-censored."
    ),
    FIRST_LOAD_BEARING_DEFINITION_ID: (
        "Earliest committed accepted point with load_bearing=true on cumulative x_total_mm; "
        "absence through the declared observation limit is right-censored."
    ),
    FALSE_ENGAGEMENT_DEFINITION_ID: (
        "Maximal contiguous accepted-point episodes with any geometric, loaded, or "
        "frictionally-stable lane true while load_bearing remains false."
    ),
    RELEASE_LIFECYCLE_DEFINITION_ID: (
        "Committed release chains linked to later committed recontact and positive-load "
        "reengagement records; missing downstream events remain explicitly censored."
    ),
    CYCLE_PATH_FRACTION_DEFINITION_ID: (
        "Cycle count plus loaded and load-bearing fractions of the observed cumulative-x "
        "increments, using the state at each accepted interval endpoint."
    ),
    MULTI_PEAK_DEFINITION_ID: (
        "Unsmooth per-cycle strict local maxima of positive Rx with point-level raw links "
        "and the drop to the next raw trough before the following peak."
    ),
    WORK_ENERGY_DEFINITION_ID: (
        "Positive trapezoidal resisting work over committed cumulative-x intervals plus "
        "accepted-ledger friction dissipation and returned recoverable energy."
    ),
}


def _definition_hash(definition_id: str) -> str:
    return semantic_hash(
        {
            "definition_id": definition_id,
            "definition_version": M03_SUMMARY_DEFINITION_VERSION,
            "definition": _DEFINITION_TEXT[definition_id],
            "smoothing": "NONE",
            "rejected_rows": "EXCLUDED",
        }
    )


def _raw_link(dataset_id: str, record_id: str) -> str:
    return f"{dataset_id}#{record_id}"


def _accepted_links(records: Sequence[AcceptedStateHistoryRecord]) -> tuple[str, ...]:
    return tuple(
        _raw_link(ACCEPTED_STATE_HISTORY_DATASET, item.state_record_id) for item in records
    )


def _event_links(records: Sequence[CommittedEventPayloadRecord]) -> tuple[str, ...]:
    return tuple(
        _raw_link(COMMITTED_EVENT_PAYLOADS_DATASET, item.event_payload_id) for item in records
    )


def _cycle_links(records: Sequence[ContactCycleRecord]) -> tuple[str, ...]:
    return tuple(_raw_link(CONTACT_CYCLE_RECORDS_DATASET, item.cycle_record_id) for item in records)


def _work_links(records: Sequence[WorkLedgerRecord]) -> tuple[str, ...]:
    return tuple(_raw_link(WORK_LEDGER_DATASET, item.work_ledger_id) for item in records)


def _validate_common_identity(
    accepted: Sequence[AcceptedStateHistoryRecord],
    events: Sequence[CommittedEventPayloadRecord],
    cycles: Sequence[ContactCycleRecord],
    ledger: Sequence[WorkLedgerRecord],
) -> None:
    reference = accepted[0]
    rows: tuple[M03ResultRecord, ...] = (*accepted, *events, *cycles, *ledger)
    for row in rows:
        if row.run_id != reference.run_id or row.case_id != reference.case_id:
            raise ContractViolation("M03 summary inputs must belong to one run and case")
        if row.schema_version != reference.schema_version:
            raise ContractViolation("M03 summary inputs must share one schema version")
        if row.certification_status is not reference.certification_status:
            raise ContractViolation("M03 summary inputs disagree on certification status")
        receipt_id = getattr(row, "commit_receipt_id", None)
        if not isinstance(receipt_id, str) or not receipt_id:
            raise ContractViolation("M03 summaries consume only receipt-backed committed raw rows")
    ledger_indices = tuple(item.accepted_interval_index for item in ledger)
    if len(ledger_indices) != len(set(ledger_indices)):
        raise ContractViolation("work-ledger interval indices must be unique for summary rebuild")


def _ordered_accepted(
    records: Sequence[AcceptedStateHistoryRecord],
) -> tuple[AcceptedStateHistoryRecord, ...]:
    if not records:
        raise ContractViolation("M03 summaries require at least one accepted raw point")
    ordered = tuple(sorted(records, key=lambda item: item.accepted_point_index))
    indices = tuple(item.accepted_point_index for item in ordered)
    if len(indices) != len(set(indices)):
        raise ContractViolation("accepted point indices must be unique for summary rebuild")
    for left, right in pairwise(ordered):
        if right.x_total_mm < left.x_total_mm:
            raise ContractViolation("cumulative x_total_mm cannot decrease across accepted history")
        if right.drag_elapsed_time_s < left.drag_elapsed_time_s:
            raise ContractViolation("drag elapsed time cannot reset across accepted history")
    return ordered


def _summary(
    definition_id: str,
    accepted: Sequence[AcceptedStateHistoryRecord],
    *,
    payload: dict[str, Any],
    raw_links: tuple[str, ...],
    right_censored: bool,
    includes_events: bool = False,
) -> DerivedSummaryRecord:
    reference = accepted[0]
    definition_hash = _definition_hash(definition_id)
    accepted_ids = tuple(item.point_id for item in accepted)
    summary_preimage = {
        "case_id": reference.case_id,
        "definition_id": definition_id,
        "definition_version": M03_SUMMARY_DEFINITION_VERSION,
        "definition_hash": definition_hash,
        "accepted_point_ids": accepted_ids,
        "raw_links": raw_links,
        "right_censored": right_censored,
        "payload": payload,
    }
    return DerivedSummaryRecord(
        run_id=reference.run_id,
        case_id=reference.case_id,
        schema_version=reference.schema_version,
        status=reference.status,
        source_identity=reference.source_identity,
        maturity=reference.maturity,
        certification_status=reference.certification_status,
        summary_id=stable_content_id("m03-derived-summary", summary_preimage),
        summary_kind=definition_id.removeprefix("m03.summary.").upper(),
        included_dataset_classes=("accepted", "event") if includes_events else ("accepted",),
        definition_id=definition_id,
        definition_version=M03_SUMMARY_DEFINITION_VERSION,
        definition_hash=definition_hash,
        input_accepted_point_ids=accepted_ids,
        input_raw_links=raw_links,
        right_censored=right_censored,
        summary_payload=payload,
    )


def _input_range(accepted: Sequence[AcceptedStateHistoryRecord]) -> dict[str, Any]:
    return {
        "first_point_id": accepted[0].point_id,
        "last_point_id": accepted[-1].point_id,
        "first_accepted_point_index": accepted[0].accepted_point_index,
        "last_accepted_point_index": accepted[-1].accepted_point_index,
        "first_x_total_mm": accepted[0].x_total_mm,
        "last_x_total_mm": accepted[-1].x_total_mm,
    }


def _first_stage_summary(
    accepted: Sequence[AcceptedStateHistoryRecord],
    *,
    definition_id: str,
    field: str,
    observation_limit_mm: float,
) -> DerivedSummaryRecord:
    observed = next(
        (
            item
            for item in accepted
            if item.x_total_mm <= observation_limit_mm and bool(getattr(item, field))
        ),
        None,
    )
    censored = observed is None
    payload: dict[str, Any] = {
        "stage_field": field,
        "observed": observed is not None,
        "first_point_id": None if observed is None else observed.point_id,
        "first_distance_mm": None if observed is None else observed.x_total_mm,
        "first_drag_elapsed_time_s": (None if observed is None else observed.drag_elapsed_time_s),
        "observation_limit_mm": observation_limit_mm,
        "censor_coordinate_mm": min(accepted[-1].x_total_mm, observation_limit_mm),
        "input_accepted_id_range": _input_range(accepted),
    }
    return _summary(
        definition_id,
        accepted,
        payload=payload,
        raw_links=_accepted_links(accepted),
        right_censored=censored,
    )


def _false_engagement_summary(
    accepted: Sequence[AcceptedStateHistoryRecord],
) -> DerivedSummaryRecord:
    episodes: list[dict[str, Any]] = []
    start_index: int | None = None
    for index, item in enumerate(accepted):
        active = (
            item.geometric_candidate or item.loaded_contact or item.frictionally_stable
        ) and not item.load_bearing
        if active and start_index is None:
            start_index = index
        if start_index is not None and (not active or index == len(accepted) - 1):
            end_index = index if active else index - 1
            episode_rows = accepted[start_index : end_index + 1]
            is_censored = active and index == len(accepted) - 1
            episodes.append(
                {
                    "episode_index": len(episodes),
                    "start_point_id": episode_rows[0].point_id,
                    "end_point_id": episode_rows[-1].point_id,
                    "start_x_total_mm": episode_rows[0].x_total_mm,
                    "end_x_total_mm": episode_rows[-1].x_total_mm,
                    "path_span_mm": episode_rows[-1].x_total_mm - episode_rows[0].x_total_mm,
                    "geometric_candidate_observed": any(
                        row.geometric_candidate for row in episode_rows
                    ),
                    "loaded_contact_observed": any(row.loaded_contact for row in episode_rows),
                    "frictionally_stable_observed": any(
                        row.frictionally_stable for row in episode_rows
                    ),
                    "right_censored": is_censored,
                    "raw_point_links": tuple(
                        _raw_link(ACCEPTED_STATE_HISTORY_DATASET, row.state_record_id)
                        for row in episode_rows
                    ),
                }
            )
            start_index = None
    censored = bool(episodes and episodes[-1]["right_censored"])
    return _summary(
        FALSE_ENGAGEMENT_DEFINITION_ID,
        accepted,
        payload={
            "episode_count": len(episodes),
            "episodes": tuple(episodes),
            "input_accepted_id_range": _input_range(accepted),
        },
        raw_links=_accepted_links(accepted),
        right_censored=censored,
    )


def _state_for_event(
    event: CommittedEventPayloadRecord,
    accepted: Sequence[AcceptedStateHistoryRecord],
) -> AcceptedStateHistoryRecord | None:
    exact = tuple(
        item
        for item in accepted
        if item.cycle_id == event.cycle_id
        and abs(item.operation_path_coordinate_mm - event.path_coordinate_mm) <= 1.0e-12
    )
    if len(exact) == 1:
        return exact[0]
    return None


def _event_measurement(
    event_id: str | None,
    event_by_id: dict[str, CommittedEventPayloadRecord],
    accepted: Sequence[AcceptedStateHistoryRecord],
) -> dict[str, Any] | None:
    if event_id is None:
        return None
    event = event_by_id.get(event_id)
    if event is None:
        return {
            "event_id": event_id,
            "event_kind": None,
            "cycle_id": None,
            "path_coordinate_mm": None,
            "x_total_mm": None,
            "drag_elapsed_time_s": None,
            "accepted_point_id": None,
            "measurement_status": "EVENT_RAW_LINK_UNAVAILABLE",
        }
    state = _state_for_event(event, accepted)
    return {
        "event_id": event.event_id,
        "event_kind": event.event_kind,
        "cycle_id": event.cycle_id,
        "path_coordinate_mm": event.path_coordinate_mm,
        "x_total_mm": None if state is None else state.x_total_mm,
        "drag_elapsed_time_s": None if state is None else state.drag_elapsed_time_s,
        "accepted_point_id": None if state is None else state.point_id,
        "measurement_status": (
            "EXACT_ACCEPTED_POINT_MATCH" if state is not None else "EVENT_PATH_COORDINATE_ONLY"
        ),
    }


def _spacing(
    start: dict[str, Any] | None, end: dict[str, Any] | None
) -> tuple[float | None, float | None, str]:
    if start is None or end is None:
        return None, None, "RIGHT_CENSORED"
    start_x = start["x_total_mm"]
    end_x = end["x_total_mm"]
    start_t = start["drag_elapsed_time_s"]
    end_t = end["drag_elapsed_time_s"]
    distance: float | None
    if isinstance(start_x, float) and isinstance(end_x, float):
        distance = abs(end_x - start_x)
        basis = "CUMULATIVE_X_TOTAL"
    else:
        start_path = start["path_coordinate_mm"]
        end_path = end["path_coordinate_mm"]
        distance = (
            abs(end_path - start_path)
            if isinstance(start_path, float) and isinstance(end_path, float)
            else None
        )
        basis = "EVENT_PATH_COORDINATE" if distance is not None else "UNAVAILABLE"
    elapsed = (
        max(0.0, end_t - start_t)
        if isinstance(start_t, float) and isinstance(end_t, float)
        else None
    )
    return distance, elapsed, basis


def _event_kind(event: CommittedEventPayloadRecord) -> str:
    return event.event_kind.upper().replace("-", "_")


def _release_chains_from_events(
    events: Sequence[CommittedEventPayloadRecord],
) -> tuple[tuple[str, str | None, str | None, str], ...]:
    chains: list[tuple[str, str | None, str | None, str]] = []
    for index, event in enumerate(events):
        if _event_kind(event) != "RELEASE":
            continue
        recontact_id: str | None = None
        reengagement_id: str | None = None
        for later in events[index + 1 :]:
            kind = _event_kind(later)
            if recontact_id is None and kind in {"RECONTACT", "CONTACT_ESTABLISHED"}:
                recontact_id = later.event_id
            if recontact_id is not None and kind in {"REENGAGEMENT", "REATTACHED_ENTRY"}:
                reengagement_id = later.event_id
                break
            if kind == "RELEASE":
                break
        chains.append((event.event_id, recontact_id, reengagement_id, event.cycle_id))
    return tuple(chains)


def _release_lifecycle_summary(
    accepted: Sequence[AcceptedStateHistoryRecord],
    events: Sequence[CommittedEventPayloadRecord],
    cycles: Sequence[ContactCycleRecord],
) -> DerivedSummaryRecord:
    event_by_id = {item.event_id: item for item in events}
    event_chains = {item[0]: item for item in _release_chains_from_events(events)}
    linked_release_ids: set[str] = set()
    raw_chains: list[tuple[str, str | None, str | None, str]] = []
    for cycle in cycles:
        if cycle.release_event_id is None:
            continue
        linked_release_ids.add(cycle.release_event_id)
        fallback = event_chains.get(cycle.release_event_id)
        raw_chains.append(
            (
                cycle.release_event_id,
                cycle.recontact_event_id or (None if fallback is None else fallback[1]),
                cycle.reengagement_event_id or (None if fallback is None else fallback[2]),
                cycle.cycle_id,
            )
        )
    raw_chains.extend(
        chain for chain in event_chains.values() if chain[0] not in linked_release_ids
    )

    chains: list[dict[str, Any]] = []
    for release_id, recontact_id, reengagement_id, cycle_id in raw_chains:
        release = _event_measurement(release_id, event_by_id, accepted)
        recontact = _event_measurement(recontact_id, event_by_id, accepted)
        reengagement = _event_measurement(reengagement_id, event_by_id, accepted)
        recontact_distance, recontact_time, recontact_basis = _spacing(release, recontact)
        reengagement_distance, reengagement_time, reengagement_basis = _spacing(
            release, reengagement
        )
        chains.append(
            {
                "cycle_id": cycle_id,
                "recontact_cycle_id": (None if recontact is None else recontact.get("cycle_id")),
                "reengagement_cycle_id": (
                    None if reengagement is None else reengagement.get("cycle_id")
                ),
                "release": release,
                "recontact": recontact,
                "reengagement": reengagement,
                "release_to_recontact_distance_mm": recontact_distance,
                "release_to_recontact_drag_elapsed_time_s": recontact_time,
                "release_to_recontact_distance_basis": recontact_basis,
                "release_to_recontact_right_censored": recontact_id is None,
                "release_to_reengagement_distance_mm": reengagement_distance,
                "release_to_reengagement_drag_elapsed_time_s": reengagement_time,
                "release_to_reengagement_distance_basis": reengagement_basis,
                "release_to_reengagement_right_censored": reengagement_id is None,
                "physical_operation_time_s": None,
                "physical_operation_time_status": "UNAVAILABLE_OPERATION_SPEED_NOT_DECLARED",
            }
        )
    censored = any(
        item["release_to_recontact_right_censored"]
        or item["release_to_reengagement_right_censored"]
        for item in chains
    )
    return _summary(
        RELEASE_LIFECYCLE_DEFINITION_ID,
        accepted,
        payload={
            "release_chain_count": len(chains),
            "chains": tuple(chains),
            "input_accepted_id_range": _input_range(accepted),
        },
        raw_links=(*_accepted_links(accepted), *_event_links(events), *_cycle_links(cycles)),
        right_censored=censored,
        includes_events=True,
    )


def _path_measure(
    accepted: Sequence[AcceptedStateHistoryRecord], field: str
) -> tuple[float, float | None]:
    observed = 0.0
    selected = 0.0
    for left, right in pairwise(accepted):
        span = right.x_total_mm - left.x_total_mm
        observed += span
        if bool(getattr(right, field)):
            selected += span
    return observed, selected / observed if observed > 0.0 else None


def _cycle_path_summary(
    accepted: Sequence[AcceptedStateHistoryRecord], cycles: Sequence[ContactCycleRecord]
) -> DerivedSummaryRecord:
    observed_path, loaded_fraction = _path_measure(accepted, "loaded_contact")
    _, load_bearing_fraction = _path_measure(accepted, "load_bearing")
    observed_cycle_ids = [item.cycle_id for item in accepted if item.cycle_id.strip()]
    observed_cycle_ids.extend(item.cycle_id for item in cycles if item.cycle_id.strip())
    cycle_ids = tuple(dict.fromkeys(observed_cycle_ids))
    censored_cycle_ids = tuple(item.cycle_id for item in cycles if item.right_censored)
    payload: dict[str, Any] = {
        "contact_cycle_count": len(cycle_ids),
        "cycle_ids": cycle_ids,
        "right_censored_cycle_ids": censored_cycle_ids,
        "observed_path_mm": observed_path,
        "loaded_path_fraction": loaded_fraction,
        "load_bearing_path_fraction": load_bearing_fraction,
        "path_fraction_status": (
            "PRESENT" if observed_path > 0.0 else "UNAVAILABLE_ZERO_OBSERVED_PATH"
        ),
        "input_accepted_id_range": _input_range(accepted),
    }
    return _summary(
        CYCLE_PATH_FRACTION_DEFINITION_ID,
        accepted,
        payload=payload,
        raw_links=(*_accepted_links(accepted), *_cycle_links(cycles)),
        right_censored=bool(censored_cycle_ids),
        includes_events=bool(cycles),
    )


def _multi_peak_summary(
    accepted: Sequence[AcceptedStateHistoryRecord], cycles: Sequence[ContactCycleRecord]
) -> DerivedSummaryRecord:
    rows_by_cycle: dict[str, list[AcceptedStateHistoryRecord]] = {}
    for item in accepted:
        rows_by_cycle.setdefault(item.cycle_id, []).append(item)
    cycle_payloads: list[dict[str, Any]] = []
    for cycle_id, rows in rows_by_cycle.items():
        peaks: list[dict[str, Any]] = []
        peak_indices = [
            index
            for index in range(1, len(rows) - 1)
            if rows[index].grip_resistance_rx_n > 0.0
            and rows[index].grip_resistance_rx_n > rows[index - 1].grip_resistance_rx_n
            and rows[index].grip_resistance_rx_n >= rows[index + 1].grip_resistance_rx_n
        ]
        for peak_number, index in enumerate(peak_indices):
            next_peak = (
                peak_indices[peak_number + 1] if peak_number + 1 < len(peak_indices) else len(rows)
            )
            trough_rows = rows[index + 1 : next_peak]
            trough = min(trough_rows, key=lambda item: item.grip_resistance_rx_n, default=None)
            peak = rows[index]
            peaks.append(
                {
                    "peak_index": peak_number,
                    "peak_point_id": peak.point_id,
                    "peak_x_total_mm": peak.x_total_mm,
                    "peak_value_n": peak.grip_resistance_rx_n,
                    "drop_to_next_raw_trough_n": (
                        None
                        if trough is None
                        else max(0.0, peak.grip_resistance_rx_n - trough.grip_resistance_rx_n)
                    ),
                    "next_raw_trough_point_id": None if trough is None else trough.point_id,
                    "raw_neighbor_point_ids": (
                        rows[index - 1].point_id,
                        peak.point_id,
                        rows[index + 1].point_id,
                    ),
                    "raw_record_link": _raw_link(
                        ACCEPTED_STATE_HISTORY_DATASET, peak.state_record_id
                    ),
                }
            )
        cycle_payloads.append(
            {
                "cycle_id": cycle_id,
                "peak_count": len(peaks),
                "peaks": tuple(peaks),
                "raw_cycle_record_links": tuple(
                    _raw_link(ACCEPTED_STATE_HISTORY_DATASET, item.state_record_id) for item in rows
                ),
            }
        )
    censored_cycle_ids = {item.cycle_id for item in cycles if item.right_censored}
    return _summary(
        MULTI_PEAK_DEFINITION_ID,
        accepted,
        payload={
            "smoothing": "NONE",
            "peak_rule": "STRICT_LEFT_AND_NONSTRICT_RIGHT_LOCAL_MAXIMUM",
            "cycles": tuple(cycle_payloads),
            "total_peak_count": sum(item["peak_count"] for item in cycle_payloads),
            "input_accepted_id_range": _input_range(accepted),
        },
        raw_links=(*_accepted_links(accepted), *_cycle_links(cycles)),
        right_censored=bool(censored_cycle_ids),
        includes_events=bool(cycles),
    )


def _work_energy_summary(
    accepted: Sequence[AcceptedStateHistoryRecord], ledger: Sequence[WorkLedgerRecord]
) -> DerivedSummaryRecord:
    positive_resisting_work = 0.0
    for left, right in pairwise(accepted):
        span = right.x_total_mm - left.x_total_mm
        left_force = max(0.0, left.grip_resistance_rx_n)
        right_force = max(0.0, right.grip_resistance_rx_n)
        positive_resisting_work += 0.5 * (left_force + right_force) * span
    friction = sum(item.friction_dissipation_n_mm for item in ledger)
    returned = sum(item.returned_recoverable_energy_n_mm for item in ledger)
    payload: dict[str, Any] = {
        "positive_resisting_work_n_mm": positive_resisting_work,
        "friction_dissipation_n_mm": friction,
        "returned_recoverable_energy_n_mm": returned,
        "ledger_interval_count": len(ledger),
        "integration_rule": "RAW_ACCEPTED_TRAPEZOID_POSITIVE_RX_OVER_CUMULATIVE_X",
        "input_accepted_id_range": _input_range(accepted),
    }
    return _summary(
        WORK_ENERGY_DEFINITION_ID,
        accepted,
        payload=payload,
        raw_links=(*_accepted_links(accepted), *_work_links(ledger)),
        right_censored=False,
    )


def build_m03_summaries(
    accepted_states: Sequence[AcceptedStateHistoryRecord],
    *,
    committed_events: Sequence[CommittedEventPayloadRecord] = (),
    contact_cycles: Sequence[ContactCycleRecord] = (),
    work_ledger: Sequence[WorkLedgerRecord] = (),
    observation_limit_mm: float = 100.0,
) -> tuple[DerivedSummaryRecord, ...]:
    """Rebuild all seven frozen M03 summary families from canonical raw rows.

    The returned products are descriptive only.  They never consume rejected
    diagnostics and intentionally define no binary outcome, aggregate ranking,
    uncertainty interval, or material/strength inference.
    """

    if observation_limit_mm <= 0.0:
        raise ContractViolation("summary observation limit must be positive")
    accepted = _ordered_accepted(accepted_states)
    events = tuple(committed_events)
    cycles = tuple(contact_cycles)
    ledger = tuple(sorted(work_ledger, key=lambda item: item.accepted_interval_index))
    _validate_common_identity(accepted, events, cycles, ledger)
    return (
        _first_stage_summary(
            accepted,
            definition_id=FIRST_LOADED_CONTACT_DEFINITION_ID,
            field="loaded_contact",
            observation_limit_mm=observation_limit_mm,
        ),
        _first_stage_summary(
            accepted,
            definition_id=FIRST_LOAD_BEARING_DEFINITION_ID,
            field="load_bearing",
            observation_limit_mm=observation_limit_mm,
        ),
        _false_engagement_summary(accepted),
        _release_lifecycle_summary(accepted, events, cycles),
        _cycle_path_summary(accepted, cycles),
        _multi_peak_summary(accepted, cycles),
        _work_energy_summary(accepted, ledger),
    )


def rebuild_m03_summaries(
    accepted_states: Sequence[AcceptedStateHistoryRecord],
    *,
    committed_events: Sequence[CommittedEventPayloadRecord] = (),
    contact_cycles: Sequence[ContactCycleRecord] = (),
    work_ledger: Sequence[WorkLedgerRecord] = (),
    observation_limit_mm: float = 100.0,
) -> tuple[DerivedSummaryRecord, ...]:
    """Explicitly named alias used by bundle-integrity rebuild checks."""

    return build_m03_summaries(
        accepted_states,
        committed_events=committed_events,
        contact_cycles=contact_cycles,
        work_ledger=work_ledger,
        observation_limit_mm=observation_limit_mm,
    )
