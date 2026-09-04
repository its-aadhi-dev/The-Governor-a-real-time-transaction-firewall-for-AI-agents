from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentReputationModel(Base):
    __tablename__ = "agent_reputation"

    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), primary_key=True)
    trust_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("1.0000"))
    successful_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    review_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    blocked_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    policy_violations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_violation_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_transaction_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    @property
    def reputation_score(self) -> Decimal:
        return self.trust_score

    @property
    def transaction_count(self) -> int:
        return (
            self.successful_transactions
            + self.review_transactions
        )

    @property
    def successful_transaction_count(self) -> int:
        return self.successful_transactions

    @property
    def blocked_transaction_count(self) -> int:
        return self.blocked_transactions