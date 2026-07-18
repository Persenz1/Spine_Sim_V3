"""Deterministic h/h2/h4 and M01 LOD refinement acceptance helpers."""

from __future__ import annotations

import math
from dataclasses import dataclass

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation


@dataclass(frozen=True, slots=True)
class RefinementObservation:
    observation_id: str
    step_size_mm: float
    event_tolerance_mm: float
    m01_lod: int
    event_position_mm: float
    unique_support_position_mm: float
    normal_angle_deg: float
    force_summary_n: float
    work_summary_n_mm: float
    event_order: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.observation_id:
            raise ContractViolation("refinement observation ID cannot be empty")
        finite = (
            self.step_size_mm,
            self.event_tolerance_mm,
            self.event_position_mm,
            self.unique_support_position_mm,
            self.normal_angle_deg,
            self.force_summary_n,
            self.work_summary_n_mm,
        )
        if any(not math.isfinite(value) for value in finite):
            raise ContractViolation("refinement observation contains NaN/Inf")
        if self.step_size_mm <= 0.0 or self.event_tolerance_mm <= 0.0:
            raise ContractViolation("refinement step/tolerance must be positive")
        if self.m01_lod <= 0:
            raise ContractViolation("M01 LOD denominator must be positive")


@dataclass(frozen=True, slots=True)
class RefinementAssessment:
    assessment_id: str
    assessment_hash: str
    passed: bool
    event_position_errors_mm: tuple[float, ...]
    force_relative_errors: tuple[float, ...]
    work_relative_errors: tuple[float, ...]
    observed_event_order: float | None
    observed_force_order: float | None
    event_order_matched: bool
    failed_gates: tuple[str, ...]


def assess_h_h2_h4(
    coarse: RefinementObservation,
    medium: RefinementObservation,
    fine: RefinementObservation,
) -> RefinementAssessment:
    """Assess three nested numerical levels without treating a pass as physics validation."""

    if not math.isclose(coarse.step_size_mm, 2.0 * medium.step_size_mm, rel_tol=1e-12):
        raise ContractViolation("coarse/medium observations are not an h/h2 pair")
    if not math.isclose(medium.step_size_mm, 2.0 * fine.step_size_mm, rel_tol=1e-12):
        raise ContractViolation("medium/fine observations are not an h2/h4 pair")
    event_errors = (
        abs(coarse.event_position_mm - fine.event_position_mm),
        abs(medium.event_position_mm - fine.event_position_mm),
        0.0,
    )
    force_errors = (
        _relative_error(coarse.force_summary_n, fine.force_summary_n),
        _relative_error(medium.force_summary_n, fine.force_summary_n),
        0.0,
    )
    work_errors = (
        _relative_error(coarse.work_summary_n_mm, fine.work_summary_n_mm),
        _relative_error(medium.work_summary_n_mm, fine.work_summary_n_mm),
        0.0,
    )
    event_order = _observed_order(event_errors[0], event_errors[1])
    force_order = _observed_order(force_errors[0], force_errors[1])
    order_matched = coarse.event_order == medium.event_order == fine.event_order
    failures: list[str] = []
    comparison_slack = max(1.0e-15, coarse.event_tolerance_mm * 1.0e-12)
    if event_errors[1] > coarse.event_tolerance_mm + comparison_slack:
        failures.append("EVENT_POSITION_NOT_CONVERGED")
    if force_errors[1] > force_errors[0] + 1.0e-15:
        failures.append("FORCE_ERROR_NOT_MONOTONE")
    if work_errors[1] > work_errors[0] + 1.0e-15:
        failures.append("WORK_ERROR_NOT_MONOTONE")
    if not order_matched:
        failures.append("EVENT_ORDER_CHANGED")
    payload = {
        "observation_ids": (coarse.observation_id, medium.observation_id, fine.observation_id),
        "event_position_errors_mm": event_errors,
        "force_relative_errors": force_errors,
        "work_relative_errors": work_errors,
        "observed_event_order": event_order,
        "observed_force_order": force_order,
        "event_order_matched": order_matched,
        "failed_gates": tuple(failures),
    }
    return RefinementAssessment(
        assessment_id=stable_content_id("m02_h_h2_h4_refinement", payload),
        assessment_hash=semantic_hash(payload),
        passed=not failures,
        event_position_errors_mm=event_errors,
        force_relative_errors=force_errors,
        work_relative_errors=work_errors,
        observed_event_order=event_order,
        observed_force_order=force_order,
        event_order_matched=order_matched,
        failed_gates=tuple(failures),
    )


def assess_rt8_to_rt10(
    rt8: RefinementObservation,
    rt10: RefinementObservation,
    *,
    reference_rt_mm: float,
) -> RefinementAssessment:
    """Apply the frozen Rt/8→Rt/10 M01 compatibility start gate exactly."""

    if rt8.m01_lod != 8 or rt10.m01_lod != 10:
        raise ContractViolation("M01 refinement gate requires Rt/8 and Rt/10 observations")
    if not math.isfinite(reference_rt_mm) or reference_rt_mm <= 0.0:
        raise ContractViolation("M01 refinement requires a positive fixed reference Rt")
    event_error = abs(rt8.event_position_mm - rt10.event_position_mm)
    support_error = abs(rt8.unique_support_position_mm - rt10.unique_support_position_mm)
    normal_error = abs(rt8.normal_angle_deg - rt10.normal_angle_deg)
    force_error = _relative_error(rt8.force_summary_n, rt10.force_summary_n)
    work_error = _relative_error(rt8.work_summary_n_mm, rt10.work_summary_n_mm)
    order_matched = rt8.event_order == rt10.event_order
    failures: list[str] = []
    if event_error > 0.01 * reference_rt_mm:
        failures.append("EVENT_POSITION_GT_0.01_RT")
    if support_error > 0.02 * reference_rt_mm:
        failures.append("UNIQUE_SUPPORT_GT_0.02_RT")
    if normal_error > 1.0:
        failures.append("NORMAL_GT_1_DEG")
    if force_error > 0.01:
        failures.append("FORCE_SUMMARY_GT_1_PERCENT")
    if work_error > 0.01:
        failures.append("WORK_SUMMARY_GT_1_PERCENT")
    if not order_matched:
        failures.append("EVENT_ORDER_CHANGED")
    payload = {
        "observation_ids": (rt8.observation_id, rt10.observation_id),
        "reference_rt_mm": reference_rt_mm,
        "event_position_error_mm": event_error,
        "unique_support_error_mm": support_error,
        "normal_error_deg": normal_error,
        "force_relative_error": force_error,
        "work_relative_error": work_error,
        "event_order_matched": order_matched,
        "failed_gates": tuple(failures),
    }
    return RefinementAssessment(
        assessment_id=stable_content_id("m02_rt8_rt10_refinement", payload),
        assessment_hash=semantic_hash(payload),
        passed=not failures,
        event_position_errors_mm=(event_error,),
        force_relative_errors=(force_error,),
        work_relative_errors=(work_error,),
        observed_event_order=None,
        observed_force_order=None,
        event_order_matched=order_matched,
        failed_gates=tuple(failures),
    )


def _relative_error(value: float, reference: float) -> float:
    scale = max(abs(reference), 1.0e-30)
    return abs(value - reference) / scale


def _observed_order(coarse_error: float, medium_error: float) -> float | None:
    if coarse_error <= 0.0 or medium_error <= 0.0:
        return None
    return math.log(coarse_error / medium_error, 2.0)
