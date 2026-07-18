"""M02 numerical orchestration public package."""

from .config import DEFAULT_NUMERICS_CONFIG, NumericsConfig
from .continuation import ContinuationTrialEngine
from .events import EventCascadeEngine, EventEngine, EventRegistry
from .nonlinear import NonlinearSolver
from .result_extension import m02_result_extension
from .service import NumericsService

__all__ = [
    "DEFAULT_NUMERICS_CONFIG",
    "ContinuationTrialEngine",
    "EventCascadeEngine",
    "EventEngine",
    "EventRegistry",
    "NonlinearSolver",
    "NumericsConfig",
    "NumericsService",
    "m02_result_extension",
]
