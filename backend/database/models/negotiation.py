from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NegotiationModel(Base):
    __tablename__ = "negotiations"

    negotiation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    buyer_agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False, index=True)
    merchant_agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("catalog_items.item_id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN", index=True)
    proposal_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    messages = relationship(
        "NegotiationMessageModel",
        back_populates="negotiation",
        cascade="all, delete-orphan",
        order_by="NegotiationMessageModel.sequence_number",
    )