from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from backend.core.models import SystemDecision


@dataclass(frozen=True)
class DecisionContext:
    pricing_blocked: bool
    pricing_requires_review: bool

    velocity_blocked: bool

    reputation_poor: bool

    collusion_requires_review: bool

    risk_score: Decimal


@dataclass(frozen=True)
class DecisionResult:
    decision: SystemDecision
    reason: str
    risk_score: Decimal
    requires_human_review: bool
    fallback_allowed: bool