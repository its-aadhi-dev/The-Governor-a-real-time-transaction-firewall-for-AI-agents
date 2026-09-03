from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PriceObservationModel(Base):
    __tablename__ = "price_observations"

    observation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    buyer_agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False, index=True)
    merchant_agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("catalog_items.item_id"), nullable=False, index=True)
    base_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    agreed_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)


Index(
    "ix_price_pair_time",
    PriceObservationModel.buyer_agent_id,
    PriceObservationModel.merchant_agent_id,
    PriceObservationModel.observed_at,
)