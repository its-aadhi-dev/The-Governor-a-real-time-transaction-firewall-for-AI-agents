from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class RiskSignal:
    name: str
    score: Decimal
    weight: Decimal
    reason: str


@dataclass(frozen=True)
class RiskAssessment:
    score: Decimal
    level: RiskLevel
    signals: tuple[RiskSignal, ...]
    reasons: tuple[str, ...]