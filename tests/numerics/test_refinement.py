from __future__ import annotations

import pytest

from spine_sim.foundation.errors import ContractViolation
from spine_sim.numerics.refinement import (
    RefinementObservation,
    assess_h_h2_h4,
    assess_rt8_to_rt10,
)


def observation(
    name: str,
    step: float,
    *,
    lod: int = 10,
    event: float = 1.0,
    support: float = 2.0,
    normal: float = 10.0,
    force: float = 5.0,
    work: float = 20.0,
    order: tuple[str, ...] = ("contact", "release"),
) -> RefinementObservation:
    return RefinementObservation(
        observation_id=name,
        step_size_mm=step,
        event_tolerance_mm=0.01,
        m01_lod=lod,
        event_position_mm=event,
        unique_support_position_mm=support,
        normal_angle_deg=normal,
        force_summary_n=force,
        work_summary_n_mm=work,
        event_order=order,
    )


def test_h_h2_h4_reports_second_order_convergence() -> None:
    result = assess_h_h2_h4(
        observation("h", 0.4, event=1.04, force=5.2, work=20.8),
        observation("h2", 0.2, event=1.01, force=5.05, work=20.2),
        observation("h4", 0.1, event=1.0, force=5.0, work=20.0),
    )
    assert result.passed
    assert result.observed_event_order == pytest.approx(2.0)
    assert result.observed_force_order == pytest.approx(2.0)
    assert result.event_order_matched


def test_h_h2_h4_rejects_non_nested_levels_and_changed_event_order() -> None:
    with pytest.raises(ContractViolation, match="h/h2"):
        assess_h_h2_h4(
            observation("h", 0.5),
            observation("h2", 0.2),
            observation("h4", 0.1),
        )
    result = assess_h_h2_h4(
        observation("h", 0.4, event=1.04),
        observation("h2", 0.2, event=1.01, order=("release", "contact")),
        observation("h4", 0.1, event=1.0),
    )
    assert not result.passed
    assert "EVENT_ORDER_CHANGED" in result.failed_gates


def test_rt8_to_rt10_exact_frozen_gates_pass_at_limits() -> None:
    rt = 0.1
    result = assess_rt8_to_rt10(
        observation(
            "rt8",
            0.01,
            lod=8,
            event=1.001,
            support=2.002,
            normal=11.0,
            force=5.05,
            work=20.2,
        ),
        observation("rt10", 0.005, lod=10),
        reference_rt_mm=rt,
    )
    assert result.passed


@pytest.mark.parametrize(
    ("field", "expected_gate"),
    [
        ("event", "EVENT_POSITION_GT_0.01_RT"),
        ("support", "UNIQUE_SUPPORT_GT_0.02_RT"),
        ("normal", "NORMAL_GT_1_DEG"),
        ("force", "FORCE_SUMMARY_GT_1_PERCENT"),
        ("work", "WORK_SUMMARY_GT_1_PERCENT"),
        ("order", "EVENT_ORDER_CHANGED"),
    ],
)
def test_rt8_to_rt10_does_not_loosen_any_failed_gate(field: str, expected_gate: str) -> None:
    values: dict[str, object] = {
        "event": 1.0,
        "support": 2.0,
        "normal": 10.0,
        "force": 5.0,
        "work": 20.0,
        "order": ("contact", "release"),
    }
    values[field] = {
        "event": 1.002,
        "support": 2.003,
        "normal": 11.1,
        "force": 5.051,
        "work": 20.21,
        "order": ("release", "contact"),
    }[field]
    result = assess_rt8_to_rt10(
        observation("rt8", 0.01, lod=8, **values),  # type: ignore[arg-type]
        observation("rt10", 0.005, lod=10),
        reference_rt_mm=0.1,
    )
    assert not result.passed
    assert expected_gate in result.failed_gates


def test_rt_gate_requires_fixed_positive_reference_and_exact_lods() -> None:
    with pytest.raises(ContractViolation, match="Rt/8"):
        assess_rt8_to_rt10(
            observation("wrong", 0.01, lod=5),
            observation("rt10", 0.005, lod=10),
            reference_rt_mm=0.1,
        )
    with pytest.raises(ContractViolation, match="positive"):
        assess_rt8_to_rt10(
            observation("rt8", 0.01, lod=8),
            observation("rt10", 0.005, lod=10),
            reference_rt_mm=0.0,
        )
