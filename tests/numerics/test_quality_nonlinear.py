from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest
from numpy.typing import NDArray

from spine_sim.foundation.canonical import semantic_hash
from spine_sim.foundation.errors import ContractViolation
from spine_sim.numerics.contracts import (
    ComplementarityQuality,
    DerivativeCapability,
    DerivativeKind,
    GraphQuality,
    HardInequalityQuality,
    M02ReasonCode,
    NonlinearMethod,
    ResidualBlock,
    ResidualKind,
)
from spine_sim.numerics.nonlinear import (
    NonlinearEvaluation,
    NonlinearSolver,
    TrustRegionAdapter,
)
from spine_sim.numerics.quality import (
    assess_numerical_quality,
    validate_strict_rigid_graph,
)

FloatArray = NDArray[np.float64]


def digest(value: object) -> str:
    return semantic_hash(value)


def capability(
    kind: DerivativeKind = DerivativeKind.ANALYTIC_JACOBIAN,
    *,
    nonsmooth: bool = False,
    production_safe: bool = True,
) -> DerivativeCapability:
    return DerivativeCapability.create(
        capability_id=f"derivative-{kind.value}",
        owner_id="synthetic-owner",
        owner_version="1.0.0",
        kind=kind,
        nonsmooth_supported=nonsmooth,
        production_safe=production_safe,
        derivative_hash=digest((kind.value, nonsmooth, production_safe)),
        branch_scope="VALIDATION_ONLY_FIXTURE",
        metadata_unit="1",
    )


def force_block(value: float, *, scale: float = 1.0, hard: bool = True) -> ResidualBlock:
    return ResidualBlock.from_values(
        block_id="force-equilibrium",
        owner_id="synthetic-owner",
        kind=ResidualKind.FORCE_EQUILIBRIUM,
        physical_semantics="analytic scalar force balance",
        raw_values=(value,),
        raw_unit="N",
        reference_norm=0.0,
        absolute_tolerance=1.0e-10,
        relative_tolerance=0.0,
        scale_id="force-scale",
        scale_value=scale,
        hard_acceptance=hard,
    )


@dataclass
class ScalarProblem:
    function_kind: str
    derivative_capability: DerivativeCapability
    evaluations: int = 0

    def evaluate(self, iterate: FloatArray) -> NonlinearEvaluation:
        self.evaluations += 1
        x = float(iterate[0])
        if self.function_kind == "linear":
            residual, derivative = x - 2.0, 1.0
        elif self.function_kind == "quadratic":
            residual, derivative = x * x - 2.0, 2.0 * x
        elif self.function_kind == "cubic":
            residual, derivative = x**3 - 1.0, 3.0 * x * x
        elif self.function_kind == "semismooth":
            residual, derivative = abs(x) - 1.0, (1.0 if x >= 0.0 else -1.0)
        elif self.function_kind == "wrong-derivative":
            residual, derivative = x - 2.0, -1.0
        else:  # pragma: no cover - test fixture guard
            raise AssertionError(self.function_kind)
        return NonlinearEvaluation(
            residual_blocks=(force_block(residual),),
            generalized_derivative=np.asarray([[derivative]], dtype=np.float64),
            owner_response_hash=digest((self.function_kind, self.evaluations, x)),
        )


def test_total_merit_never_overrides_a_failed_hard_block() -> None:
    hard_failure = ResidualBlock.from_values(
        block_id="hard",
        owner_id="owner",
        kind=ResidualKind.FORCE_EQUILIBRIUM,
        physical_semantics="hard block",
        raw_values=(2.0e-6,),
        raw_unit="N",
        reference_norm=0.0,
        absolute_tolerance=1.0e-6,
        relative_tolerance=0.0,
        scale_id="deliberately-large-search-scale",
        scale_value=1.0e12,
        hard_acceptance=True,
    )
    report = assess_numerical_quality((hard_failure,))
    assert report.dimensionless_merit < 1.0e-15
    assert not report.accepted
    assert report.hard_block_failures == ("hard",)


def test_hard_inequality_complementarity_and_graph_are_separate_gates() -> None:
    inequality = HardInequalityQuality.create(
        quality_id="ineq",
        owner_id="owner",
        semantics="nonpenetration margin",
        raw_margin=-0.2,
        raw_unit="mm",
        absolute_tolerance=0.01,
        scale_id="length",
        scale_value=1.0,
        normalized_violation=0.19,
        passed=False,
        entity_refs=("tip",),
        metadata_unit="mm",
    )
    complementarity = ComplementarityQuality.create(
        quality_id="ncp",
        owner_id="owner",
        primal_violation=0.0,
        dual_violation=0.0,
        complementarity_residual=2.0e-8,
        primal_unit="1",
        dual_unit="1",
        complementarity_unit="1",
        scale_id="ncp-scale",
        scale_value=1.0,
        normalized_norm=2.0e-8,
        absolute_tolerance=1.0e-8,
        relative_tolerance=0.0,
        reference_norm=0.0,
        hard_acceptance=True,
        active_branch="contact",
        metadata_unit="1",
    )
    graph = GraphQuality.create(
        quality_id="graph",
        owner_id="owner",
        graph_id="strict-contact-graph",
        raw_distance=0.0,
        raw_unit="1",
        scale_id="graph-scale",
        scale_value=1.0,
        normalized_distance=0.0,
        absolute_tolerance=1.0e-8,
        relative_tolerance=0.0,
        reference_norm=0.0,
        hard_acceptance=True,
        active_branch="set-valued-boundary",
        set_valued=True,
        degenerate=False,
        rank=1,
        nullspace_dimension=0,
        metadata_unit="1",
    )
    report = assess_numerical_quality(
        (force_block(0.0),),
        (inequality,),
        (complementarity,),
        (graph,),
    )
    assert not report.accepted
    assert report.hard_inequality_failures == ("ineq",)
    assert report.complementarity_failures == ("ncp",)
    assert report.graph_failures == ()


def test_moment_requires_explicit_positive_native_tolerance() -> None:
    block = ResidualBlock.from_values(
        block_id="moment",
        owner_id="owner",
        kind=ResidualKind.MOMENT_EQUILIBRIUM,
        physical_semantics="moment equilibrium",
        raw_values=(0.0,),
        raw_unit="N*mm",
        reference_norm=1.0,
        absolute_tolerance=0.0,
        relative_tolerance=1.0e-5,
        scale_id="moment-scale",
        scale_value=10.0,
    )
    with pytest.raises(ContractViolation, match="explicit positive"):
        assess_numerical_quality((block,))


def test_strict_rigid_fixture_uses_set_valued_graph_not_penalty() -> None:
    graph = GraphQuality.create(
        quality_id="rigid",
        owner_id="fixture",
        graph_id="rigid-graph",
        raw_distance=0.0,
        raw_unit="1",
        scale_id="graph-scale",
        scale_value=1.0,
        normalized_distance=0.0,
        absolute_tolerance=1.0e-8,
        relative_tolerance=0.0,
        reference_norm=0.0,
        hard_acceptance=True,
        active_branch="SET_VALUED",
        set_valued=True,
        degenerate=True,
        rank=1,
        nullspace_dimension=1,
        metadata_unit="1",
    )
    validate_strict_rigid_graph(graph)
    with pytest.raises(ContractViolation, match="penalty"):
        validate_strict_rigid_graph(graph, penalty_stiffness=1.0e30)


def test_damped_newton_solves_linear_analytic_root() -> None:
    problem = ScalarProblem("linear", capability())
    result = NonlinearSolver().solve(problem, (0.0,))
    assert result.converged
    assert result.reason_code is M02ReasonCode.OK
    assert result.iterate == pytest.approx((2.0,))
    assert result.iterations == 1
    assert result.total_backtracks == 0
    assert result.numerical_convergence_only
    assert not result.physical_stability_assessed
    assert not result.physical_uniqueness_assessed
    assert not result.physical_feasibility_assessed


def test_damped_newton_solves_nonlinear_root_and_records_line_search() -> None:
    problem = ScalarProblem("quadratic", capability())
    result = NonlinearSolver().solve(problem, (0.5,))
    assert result.converged
    assert result.iterate[0] == pytest.approx(2.0**0.5, abs=1.0e-9)
    assert 1 < result.iterations < 10
    assert all(record.quality_report_hash for record in result.records)


def test_armijo_backtracks_a_large_newton_step() -> None:
    problem = ScalarProblem("cubic", capability())
    result = NonlinearSolver().solve(problem, (0.1,))
    assert result.converged
    assert result.iterate[0] == pytest.approx(1.0, abs=1.0e-9)
    assert result.total_backtracks > 0
    assert any(record.accepted_line_factor not in {None, 1.0} for record in result.records)


def test_semismooth_newton_requires_and_uses_generalized_derivative() -> None:
    problem = ScalarProblem(
        "semismooth",
        capability(DerivativeKind.GENERALIZED_JACOBIAN, nonsmooth=True),
    )
    result = NonlinearSolver().solve(
        problem,
        (0.2,),
        method=NonlinearMethod.SEMISMOOTH_GENERALIZED_NEWTON,
    )
    assert result.converged
    assert result.iterate == pytest.approx((1.0,))


def test_semismooth_newton_rejects_plain_smooth_capability() -> None:
    problem = ScalarProblem("semismooth", capability())
    with pytest.raises(ContractViolation, match="generalized nonsmooth"):
        NonlinearSolver().solve(
            problem,
            (0.2,),
            method=NonlinearMethod.SEMISMOOTH_GENERALIZED_NEWTON,
        )


def test_finite_difference_is_explicitly_validation_only() -> None:
    problem = ScalarProblem(
        "linear",
        capability(
            DerivativeKind.FINITE_DIFFERENCE_VALIDATION_ONLY,
            production_safe=False,
        ),
    )
    with pytest.raises(ContractViolation, match="VALIDATION_ONLY"):
        NonlinearSolver().solve(problem, (0.0,))
    assert NonlinearSolver().solve(problem, (0.0,), validation_only=True).converged


def test_wrong_derivative_exhausts_line_search_without_physical_claim() -> None:
    problem = ScalarProblem("wrong-derivative", capability())
    result = NonlinearSolver().solve(problem, (0.0,))
    assert not result.converged
    assert result.reason_code is M02ReasonCode.LINE_SEARCH_EXHAUSTED
    assert not result.physical_feasibility_assessed


def test_trust_region_is_a_typed_unavailable_backend_hook() -> None:
    adapter = TrustRegionAdapter()
    result = NonlinearSolver().solve(
        ScalarProblem("linear", capability()),
        (0.0,),
        method=NonlinearMethod.TRUST_REGION,
    )
    assert not adapter.backend_available
    assert not result.converged
    assert not result.trust_region_backend_available
