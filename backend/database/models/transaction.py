from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TransactionModel(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    negotiation_id: Mapped[str] = mapped_column(ForeignKey("negotiations.negotiation_id"), nullable=False, index=True)
    buyer_agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False, index=True)
    merchant_agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("catalog_items.item_id"), nullable=False, index=True)
    requested_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    authorized_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    decision: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    fallback_payment_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    policy_version: Mapped[str] = mapped_column(String(100), nullable=False, default="canon-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    buyer_agent = relationship("AgentModel", foreign_keys=[buyer_agent_id], back_populates="buyer_transactions")
    merchant_agent = relationship("AgentModel", foreign_keys=[merchant_agent_id])
    item = relationship("CatalogItemModel")


Index("ix_transactions_buyer_created", TransactionModel.buyer_agent_id, TransactionModel.created_at)
Index("ix_transactions_merchant_created", TransactionModel.merchant_agent_id, TransactionModel.created_at)