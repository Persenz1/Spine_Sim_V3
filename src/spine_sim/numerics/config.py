"""Resolved DEV numerical policy for M02.

These values are software starting points from the frozen M02 contract.  They
are deliberately kept separate from material, contact, and mechanism physics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from spine_sim.foundation.errors import ContractViolation

from .contracts import ContractMetadata, DiagnosticLevel, SemanticContract


@dataclass(frozen=True, slots=True, kw_only=True)
class NumericsConfig(SemanticContract):
    """Fully resolved, hash-addressed M02 numerical configuration."""

    __semantic_kind__ = "resolved_numerics_config"

    initial_step_over_lref: float = 0.5
    maximum_step_over_lref: float = 1.0
    minimum_step_over_lref: float = 0.001
    growth_factor: float = 1.5
    shrink_factor: float = 0.5
    max_retries_per_parent: int = 12
    easy_newton_max: int = 8
    hard_newton_min: int = 21
    hard_backtrack_min: int = 3
    force_atol_n: float = 1.0e-6
    default_rtol: float = 1.0e-5
    normalized_ncp_atol: float = 1.0e-8
    normalized_graph_atol: float = 1.0e-8
    max_newton_iterations: int = 50
    armijo_c1: float = 1.0e-4
    line_search_contraction: float = 0.5
    max_backtracks: int = 20
    min_line_search_factor: float = 2.0**-20
    event_position_tol_over_lref: float = 0.01
    simultaneous_tol_over_lref: float = 0.01
    max_bracket_iterations: int = 80
    max_same_position_cascade: int = 50
    default_diagnostic_level: DiagnosticLevel = DiagnosticLevel.STANDARD
    default_case_cache_mib: int = 256
    canonical_reduction_order: str = "OWNER_ID_BLOCK_ID_COMPONENT_INDEX"
    thread_policy: str = "EXPLICIT_CALLER_CONTROLLED"
    source_policy_id: str = "DEV_BOOTSTRAP_PROFILE:M02_NUMERICS_REQUIREMENTS_1.0.0"
    metadata: ContractMetadata

    @classmethod
    def resolved(cls, **overrides: Any) -> NumericsConfig:
        """Create a validated resolved config; every override changes its ID/hash."""

        return cls.create(metadata_unit="1", **overrides)

    @property
    def config_id(self) -> str:
        return self.metadata.semantic_id

    @property
    def config_hash(self) -> str:
        return self.metadata.semantic_hash

    def regular_initial_step_mm(self, characteristic_length_mm: float) -> float:
        self._validate_lref(characteristic_length_mm)
        return self.initial_step_over_lref * characteristic_length_mm

    def regular_minimum_step_mm(self, characteristic_length_mm: float) -> float:
        self._validate_lref(characteristic_length_mm)
        return self.minimum_step_over_lref * characteristic_length_mm

    def regular_maximum_step_mm(self, characteristic_length_mm: float) -> float:
        self._validate_lref(characteristic_length_mm)
        return self.maximum_step_over_lref * characteristic_length_mm

    def event_position_tolerance_mm(self, characteristic_length_mm: float) -> float:
        self._validate_lref(characteristic_length_mm)
        return self.event_position_tol_over_lref * characteristic_length_mm

    def simultaneous_tolerance_mm(self, characteristic_length_mm: float) -> float:
        self._validate_lref(characteristic_length_mm)
        return self.simultaneous_tol_over_lref * characteristic_length_mm

    def __post_init__(self) -> None:
        positive = (
            "initial_step_over_lref",
            "maximum_step_over_lref",
            "minimum_step_over_lref",
            "growth_factor",
            "shrink_factor",
            "force_atol_n",
            "default_rtol",
            "normalized_ncp_atol",
            "normalized_graph_atol",
            "armijo_c1",
            "line_search_contraction",
            "min_line_search_factor",
            "event_position_tol_over_lref",
            "simultaneous_tol_over_lref",
        )
        for name in positive:
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0.0:
                raise ContractViolation(f"{name} must be finite and positive")
        positive_ints = (
            "max_retries_per_parent",
            "easy_newton_max",
            "hard_newton_min",
            "hard_backtrack_min",
            "max_newton_iterations",
            "max_backtracks",
            "max_bracket_iterations",
            "max_same_position_cascade",
            "default_case_cache_mib",
        )
        for name in positive_ints:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ContractViolation(f"{name} must be a positive integer")
        if self.minimum_step_over_lref >= self.initial_step_over_lref:
            raise ContractViolation("minimum regular step must be below the initial step")
        if self.initial_step_over_lref > self.maximum_step_over_lref:
            raise ContractViolation("initial regular step cannot exceed the maximum")
        if self.growth_factor <= 1.0:
            raise ContractViolation("continuation growth factor must exceed one")
        if not 0.0 < self.shrink_factor < 1.0:
            raise ContractViolation("continuation shrink factor must lie in (0, 1)")
        if self.hard_newton_min <= self.easy_newton_max:
            raise ContractViolation("hard Newton threshold must exceed the easy threshold")
        if self.hard_newton_min > self.max_newton_iterations:
            raise ContractViolation("hard Newton threshold exceeds the iteration limit")
        if not 0.0 < self.armijo_c1 < 1.0:
            raise ContractViolation("Armijo c1 must lie in (0, 1)")
        if not 0.0 < self.line_search_contraction < 1.0:
            raise ContractViolation("line-search contraction must lie in (0, 1)")
        if self.min_line_search_factor > self.line_search_contraction:
            raise ContractViolation("minimum line-search factor is inconsistent")
        if not self.canonical_reduction_order.strip() or not self.thread_policy.strip():
            raise ContractViolation("deterministic reduction/thread policy is required")
        if not self.source_policy_id.strip():
            raise ContractViolation("resolved config must identify its source policy")
        self._validate_metadata()

    @staticmethod
    def _validate_lref(value: float) -> None:
        if not math.isfinite(value) or value <= 0.0:
            raise ContractViolation("characteristic_length_mm must be finite and positive")


DEFAULT_NUMERICS_CONFIG = NumericsConfig.resolved()
