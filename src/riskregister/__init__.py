"""Public API of the risk register package."""

from __future__ import annotations

from .models import Appetite, Control, KRI, Risk
from .registry import DataError, Registry, load_registry, save_registry
from .scales import (
    IMPACT,
    LIKELIHOOD,
    LEVEL_EN,
    LEVEL_ORDER,
    exceeds_appetite,
    level,
    reduction_pct,
    score,
)

__version__ = "1.0.0"

__all__ = [
    "Appetite",
    "Control",
    "DataError",
    "IMPACT",
    "KRI",
    "LEVEL_EN",
    "LEVEL_ORDER",
    "LIKELIHOOD",
    "Registry",
    "Risk",
    "exceeds_appetite",
    "level",
    "load_registry",
    "reduction_pct",
    "save_registry",
    "score",
]
