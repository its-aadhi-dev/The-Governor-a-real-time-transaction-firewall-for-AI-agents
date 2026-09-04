from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ReputationBand(str, Enum):
    GOOD = "GOOD"
    REVIEW = "REVIEW"
    POOR = "POOR"


@dataclass(frozen=True)
class ReputationContext:
    reputation_score: Decimal
    transaction_count: int
    successful_transaction_count: int
    blocked_transaction_count: int


@dataclass(frozen=True)
class ReputationDecision:
    band: ReputationBand
    score: Decimal
    reason: str