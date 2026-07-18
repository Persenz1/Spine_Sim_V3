"""Damped smooth and semismooth Newton orchestration for M02.

The owner supplies residual blocks and a versioned derivative.  This module
only solves the declared numerical system; it never assigns physical branch,
stability, uniqueness, or feasibility meaning to a converged iterate.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from spine_sim.foundation.canonical import semantic_hash, stable_content_id
from spine_sim.foundation.errors import ContractViolation

from .config import DEFAULT_NUMERICS_CONFIG, NumericsConfig
from .contracts import (
    ComplementarityQuality,
    DerivativeCapability,
    DerivativeKind,
    GraphQuality,
    HardInequalityQuality,
    M02ReasonCode,
    NonlinearMethod,
    ResidualBlock,
)
from .quality import QualityGateReport, assess_numerical_quality

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class NonlinearEvaluation:
    """One complete owner evaluation at an iterate."""

    residual_blocks: tuple[ResidualBlock, ...]
    generalized_derivative: FloatArray
    hard_inequalities: tuple[HardInequalityQuality, ...] = ()
    complementarity_qualities: tuple[ComplementarityQuality, ...] = ()
    graph_qualities: tuple[GraphQuality, ...] = ()
    quality_warning_ids: tuple[str, ...] = ()
    owner_response_hash: str = ""

    def __post_init__(self) -> None:
        if not self.residual_blocks:
            raise ContractViolation("nonlinear evaluation requires residual blocks")
        rows = sum(len(block.raw_values) for block in self.residual_blocks)
        derivative = np.asarray(self.generalized_derivative, dtype=np.float64)
        if derivative.ndim != 2 or derivative.shape[0] != rows:
            raise ContractViolation(
                "generalized derivative rows must match residual components",
                details={"derivative_shape": derivative.shape, "residual_components": rows},
            )
        if not np.all(np.isfinite(derivative)):
            raise ContractViolation("generalized derivative contains NaN/Inf")
        if self.owner_response_hash and len(self.owner_response_hash) != 64:
            raise ContractViolation("owner_response_hash must be a full SHA-256 digest")

    @property
    def scaled_residual_vector(self) -> FloatArray:
        values = [
            value / block.scale_value
            for block in self.residual_blocks
            for value in block.raw_values
        ]
        return np.asarray(values, dtype=np.float64)

    @property
    def scaled_derivative(self) -> FloatArray:
        scales = np.asarray(
            [block.scale_value for block in self.residual_blocks for _ in block.raw_values],
            dtype=np.float64,
        )
        return np.asarray(self.generalized_derivative, dtype=np.float64) / scales[:, None]

    def quality_report(self) -> QualityGateReport:
        return assess_numerical_quality(
            self.residual_blocks,
            self.hard_inequalities,
            self.complementarity_qualities,
            self.graph_qualities,
            warning_ids=self.quality_warning_ids,
        )


class NonlinearOwnerProblem(Protocol):
    """Side-effect-free owner numerical problem."""

    @property
    def derivative_capability(self) -> DerivativeCapability: ...

    def evaluate(self, iterate: FloatArray) -> NonlinearEvaluation: ...


@dataclass(frozen=True, slots=True)
class NonlinearIterationRecord:
    iteration: int
    iterate: tuple[float, ...]
    owner_response_hash: str
    quality_report_hash: str
    dimensionless_merit: float
    step_norm: float | None
    accepted_line_factor: float | None
    backtracks: int
    linear_solve_residual: float | None
    matrix_rank: int | None
    condition_number: float | None
    warning_ids: tuple[str, ...]
    algorithm_switches: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NonlinearSolveResult:
    result_id: str
    result_hash: str
    method: NonlinearMethod
    converged: bool
    reason_code: M02ReasonCode
    iterate: tuple[float, ...]
    iterations: int
    total_backtracks: int
    final_quality: QualityGateReport | None
    final_residual_blocks: tuple[ResidualBlock, ...]
    records: tuple[NonlinearIterationRecord, ...]
    derivative_capability_id: str
    numerical_convergence_only: bool
    physical_stability_assessed: bool
    physical_uniqueness_assessed: bool
    physical_feasibility_assessed: bool
    trust_region_backend_available: bool


class NonlinearSolver:
    """M02 nonlinear solver with explicit capability and line-search gates."""

    def __init__(self, config: NumericsConfig = DEFAULT_NUMERICS_CONFIG) -> None:
        self.config = config

    def solve(
        self,
        problem: NonlinearOwnerProblem,
        initial_iterate: Sequence[float],
        *,
        method: NonlinearMethod = NonlinearMethod.DAMPED_NEWTON,
        validation_only: bool = False,
    ) -> NonlinearSolveResult:
        iterate = np.asarray(initial_iterate, dtype=np.float64)
        if iterate.ndim != 1 or iterate.size == 0 or not np.all(np.isfinite(iterate)):
            raise ContractViolation("initial nonlinear iterate must be a finite nonempty vector")
        capability = problem.derivative_capability
        self._validate_capability(capability, method, validation_only=validation_only)
        if method is NonlinearMethod.TRUST_REGION:
            return self._result(
                method=method,
                converged=False,
                reason=M02ReasonCode.UNSUPPORTED_CONTROL_MODE,
                iterate=iterate,
                evaluations=(),
                records=(),
                capability=capability,
                total_backtracks=0,
                trust_region_backend_available=False,
            )

        records: list[NonlinearIterationRecord] = []
        evaluations: list[NonlinearEvaluation] = []
        total_backtracks = 0
        evaluation = problem.evaluate(iterate.copy())
        self._validate_evaluation_columns(evaluation, iterate.size)
        evaluations.append(evaluation)

        for iteration in range(self.config.max_newton_iterations + 1):
            quality = evaluation.quality_report()
            if quality.accepted:
                records.append(
                    self._record(
                        iteration,
                        iterate,
                        evaluation,
                        quality,
                        step_norm=None,
                        line_factor=None,
                        backtracks=0,
                        linear_residual=None,
                        rank=None,
                        condition=None,
                        warnings=(),
                        switches=(),
                    )
                )
                return self._result(
                    method=method,
                    converged=True,
                    reason=M02ReasonCode.OK,
                    iterate=iterate,
                    evaluations=evaluations,
                    records=records,
                    capability=capability,
                    total_backtracks=total_backtracks,
                    trust_region_backend_available=False,
                )
            if iteration == self.config.max_newton_iterations:
                break

            residual = evaluation.scaled_residual_vector
            derivative = evaluation.scaled_derivative
            step, linear_residual, rank, condition, warnings, switches = self._linear_step(
                derivative, residual
            )
            if step is None:
                records.append(
                    self._record(
                        iteration,
                        iterate,
                        evaluation,
                        quality,
                        step_norm=None,
                        line_factor=None,
                        backtracks=0,
                        linear_residual=linear_residual,
                        rank=rank,
                        condition=condition,
                        warnings=warnings,
                        switches=switches,
                    )
                )
                return self._result(
                    method=method,
                    converged=False,
                    reason=M02ReasonCode.LINEAR_SOLVE_FAILURE,
                    iterate=iterate,
                    evaluations=evaluations,
                    records=records,
                    capability=capability,
                    total_backtracks=total_backtracks,
                    trust_region_backend_available=False,
                )

            accepted = self._armijo(problem, iterate, step, quality.dimensionless_merit)
            if accepted is None:
                records.append(
                    self._record(
                        iteration,
                        iterate,
                        evaluation,
                        quality,
                        step_norm=float(np.linalg.norm(step)),
                        line_factor=None,
                        backtracks=self.config.max_backtracks,
                        linear_residual=linear_residual,
                        rank=rank,
                        condition=condition,
                        warnings=warnings,
                        switches=switches,
                    )
                )
                total_backtracks += self.config.max_backtracks
                return self._result(
                    method=method,
                    converged=False,
                    reason=M02ReasonCode.LINE_SEARCH_EXHAUSTED,
                    iterate=iterate,
                    evaluations=evaluations,
                    records=records,
                    capability=capability,
                    total_backtracks=total_backtracks,
                    trust_region_backend_available=False,
                )
            next_iterate, next_evaluation, line_factor, backtracks = accepted
            records.append(
                self._record(
                    iteration,
                    iterate,
                    evaluation,
                    quality,
                    step_norm=float(np.linalg.norm(line_factor * step)),
                    line_factor=line_factor,
                    backtracks=backtracks,
                    linear_residual=linear_residual,
                    rank=rank,
                    condition=condition,
                    warnings=warnings,
                    switches=switches,
                )
            )
            total_backtracks += backtracks
            iterate = next_iterate
            evaluation = next_evaluation
            self._validate_evaluation_columns(evaluation, iterate.size)
            evaluations.append(evaluation)

        return self._result(
            method=method,
            converged=False,
            reason=M02ReasonCode.NONLINEAR_NONCONVERGENCE,
            iterate=iterate,
            evaluations=evaluations,
            records=records,
            capability=capability,
            total_backtracks=total_backtracks,
            trust_region_backend_available=False,
        )

    def _armijo(
        self,
        problem: NonlinearOwnerProblem,
        iterate: FloatArray,
        step: FloatArray,
        initial_merit: float,
    ) -> tuple[FloatArray, NonlinearEvaluation, float, int] | None:
        phi = 0.5 * initial_merit * initial_merit
        factor = 1.0
        for backtracks in range(self.config.max_backtracks + 1):
            candidate = iterate + factor * step
            if np.all(np.isfinite(candidate)):
                candidate_evaluation = problem.evaluate(candidate.copy())
                self._validate_evaluation_columns(candidate_evaluation, iterate.size)
                candidate_merit = candidate_evaluation.quality_report().dimensionless_merit
                candidate_phi = 0.5 * candidate_merit * candidate_merit
                sufficient = phi * (1.0 - 2.0 * self.config.armijo_c1 * factor)
                if candidate_phi <= sufficient:
                    return candidate, candidate_evaluation, factor, backtracks
            if backtracks == self.config.max_backtracks:
                break
            factor *= self.config.line_search_contraction
            if factor < self.config.min_line_search_factor:
                break
        return None

    @staticmethod
    def _linear_step(
        derivative: FloatArray,
        residual: FloatArray,
    ) -> tuple[
        FloatArray | None,
        float,
        int,
        float,
        tuple[str, ...],
        tuple[str, ...],
    ]:
        rank = int(np.linalg.matrix_rank(derivative))
        condition = float(np.linalg.cond(derivative))
        warnings: list[str] = []
        switches: list[str] = []
        if rank < min(derivative.shape):
            warnings.append("M02_LINEAR_RANK_DEFICIENT")
        if not math.isfinite(condition) or condition > 1.0e12:
            warnings.append("M02_LINEAR_CONDITION_WARNING")
        try:
            if derivative.shape[0] == derivative.shape[1] and rank == derivative.shape[1]:
                step = np.linalg.solve(derivative, -residual)
            else:
                switches.append("DIRECT_TO_RANK_REVEALING_LEAST_SQUARES")
                step, _, _, _ = np.linalg.lstsq(derivative, -residual, rcond=None)
        except np.linalg.LinAlgError:
            return None, math.inf, rank, condition, tuple(warnings), tuple(switches)
        linear_residual = float(np.linalg.norm(derivative @ step + residual))
        if not np.all(np.isfinite(step)) or not math.isfinite(linear_residual):
            return None, linear_residual, rank, condition, tuple(warnings), tuple(switches)
        return step, linear_residual, rank, condition, tuple(warnings), tuple(switches)

    @staticmethod
    def _validate_evaluation_columns(evaluation: NonlinearEvaluation, unknowns: int) -> None:
        if evaluation.generalized_derivative.shape[1] != unknowns:
            raise ContractViolation(
                "generalized derivative columns must match unknown count",
                details={
                    "derivative_columns": evaluation.generalized_derivative.shape[1],
                    "unknowns": unknowns,
                },
            )

    @staticmethod
    def _validate_capability(
        capability: DerivativeCapability,
        method: NonlinearMethod,
        *,
        validation_only: bool,
    ) -> None:
        if capability.kind is DerivativeKind.UNAVAILABLE:
            raise ContractViolation("owner derivative capability is unavailable")
        if (
            capability.kind is DerivativeKind.FINITE_DIFFERENCE_VALIDATION_ONLY
            and not validation_only
        ):
            raise ContractViolation("finite differences are restricted to VALIDATION_ONLY/debug")
        if not validation_only and not capability.production_safe:
            raise ContractViolation(
                "production nonlinear solve requires a production-safe derivative"
            )
        if method is NonlinearMethod.SEMISMOOTH_GENERALIZED_NEWTON:
            if not capability.nonsmooth_supported or capability.kind not in {
                DerivativeKind.GENERALIZED_JACOBIAN,
                DerivativeKind.JACOBIAN_VECTOR_PRODUCT,
                DerivativeKind.VERSIONED_TANGENT,
            }:
                raise ContractViolation(
                    "semismooth Newton requires a generalized nonsmooth derivative capability"
                )

    @staticmethod
    def _record(
        iteration: int,
        iterate: FloatArray,
        evaluation: NonlinearEvaluation,
        quality: QualityGateReport,
        *,
        step_norm: float | None,
        line_factor: float | None,
        backtracks: int,
        linear_residual: float | None,
        rank: int | None,
        condition: float | None,
        warnings: tuple[str, ...],
        switches: tuple[str, ...],
    ) -> NonlinearIterationRecord:
        return NonlinearIterationRecord(
            iteration=iteration,
            iterate=tuple(float(value) for value in iterate),
            owner_response_hash=evaluation.owner_response_hash,
            quality_report_hash=quality.report_hash,
            dimensionless_merit=quality.dimensionless_merit,
            step_norm=step_norm,
            accepted_line_factor=line_factor,
            backtracks=backtracks,
            linear_solve_residual=linear_residual,
            matrix_rank=rank,
            condition_number=condition,
            warning_ids=tuple(sorted({*quality.warning_ids, *warnings})),
            algorithm_switches=switches,
        )

    @staticmethod
    def _result(
        *,
        method: NonlinearMethod,
        converged: bool,
        reason: M02ReasonCode,
        iterate: FloatArray,
        evaluations: Sequence[NonlinearEvaluation],
        records: Sequence[NonlinearIterationRecord],
        capability: DerivativeCapability,
        total_backtracks: int,
        trust_region_backend_available: bool,
    ) -> NonlinearSolveResult:
        final_evaluation = evaluations[-1] if evaluations else None
        final_quality = final_evaluation.quality_report() if final_evaluation else None
        payload = {
            "method": method.value,
            "converged": converged,
            "reason_code": reason.value,
            "iterate": tuple(float(value) for value in iterate),
            "records": records,
            "derivative_capability_id": capability.capability_id,
            "numerical_convergence_only": True,
            "physical_stability_assessed": False,
            "physical_uniqueness_assessed": False,
            "physical_feasibility_assessed": False,
            "trust_region_backend_available": trust_region_backend_available,
        }
        return NonlinearSolveResult(
            result_id=stable_content_id("m02_nonlinear_solve", payload),
            result_hash=semantic_hash(payload),
            method=method,
            converged=converged,
            reason_code=reason,
            iterate=tuple(float(value) for value in iterate),
            iterations=max(len(evaluations) - 1, 0),
            total_backtracks=total_backtracks,
            final_quality=final_quality,
            final_residual_blocks=final_evaluation.residual_blocks if final_evaluation else (),
            records=tuple(records),
            derivative_capability_id=capability.capability_id,
            numerical_convergence_only=True,
            physical_stability_assessed=False,
            physical_uniqueness_assessed=False,
            physical_feasibility_assessed=False,
            trust_region_backend_available=trust_region_backend_available,
        )


@dataclass(frozen=True, slots=True)
class TrustRegionAdapter:
    """Frozen adapter hook; the full trust-region backend is unavailable in M02 v1."""

    adapter_id: str = "M02.TRUST_REGION.ADAPTER.1.0.0"
    backend_available: bool = False
    reason_code: str = "M02_TRUST_REGION_BACKEND_UNSUPPORTED"
