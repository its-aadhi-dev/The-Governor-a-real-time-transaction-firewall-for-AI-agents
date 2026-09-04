from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class CollusionVerdict(str, Enum):
    NORMAL = "NORMAL"
    REVIEW = "REVIEW"


@dataclass(frozen=True)
class CollusionContext:
    buyer_agent_id: str
    merchant_id: str

    buyer_transaction_count: int
    buyer_merchant_transaction_count: int

    concentration_ratio: Decimal


@dataclass(frozen=True)
class CollusionDecision:
    verdict: CollusionVerdict
    concentration_ratio: Decimal
    reason: str