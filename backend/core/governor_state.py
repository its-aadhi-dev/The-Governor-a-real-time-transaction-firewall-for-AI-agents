from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class GovernorState:
    """SQLAlchemy-independent state supplied to Governor policies."""

    agent_id: str
    reputation_score: Decimal
    transaction_count: int
    successful_transaction_count: int
    blocked_transaction_count: int
    last_transaction_at: Optional[datetime]
    minimum_observed_price: Optional[Decimal]
    maximum_observed_price: Optional[Decimal]