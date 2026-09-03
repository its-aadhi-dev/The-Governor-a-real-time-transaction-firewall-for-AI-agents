from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NegotiationMessageModel(Base):
    __tablename__ = "negotiation_messages"

    message_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    negotiation_id: Mapped[str] = mapped_column(ForeignKey("negotiations.negotiation_id"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False, index=True)
    message_type: Mapped[str] = mapped_column(String(32), nullable=False)
    proposed_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    negotiation = relationship("NegotiationModel", back_populates="messages")