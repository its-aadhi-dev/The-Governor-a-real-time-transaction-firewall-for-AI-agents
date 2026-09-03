from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Tuple
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database.models.price_observation import PriceObservationModel


class PriceObservationRepository:
    """Persistence access for transaction-backed historical prices."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        *,
        transaction_id: str,
        buyer_agent_id: str,
        merchant_agent_id: str,
        item_id: str,
        base_price: Decimal,
        agreed_price: Decimal,
        currency: str = "INR",
    ) -> PriceObservationModel:
        if base_price <= Decimal("0") or agreed_price <= Decimal("0"):
            raise ValueError("Observed prices must be greater than zero.")
        if currency.upper() != "INR":
            raise ValueError("Only INR price observations are currently supported.")

        discount_percent = (base_price - agreed_price) / base_price * Decimal("100")
        observation = PriceObservationModel(
            observation_id=f"obs_{uuid4().hex}",
            transaction_id=transaction_id,
            buyer_agent_id=buyer_agent_id,
            merchant_agent_id=merchant_agent_id,
            item_id=item_id,
            base_price=base_price,
            agreed_price=agreed_price,
            discount_percent=discount_percent,
            observed_at=datetime.now(timezone.utc),
        )
        self.session.add(observation)
        self.session.flush()
        return observation

    def get_price_range(
        self,
        *,
        catalog_item_id: str,
        merchant_id: str,
    ) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        statement = select(
            func.min(PriceObservationModel.agreed_price),
            func.max(PriceObservationModel.agreed_price),
        ).where(
            PriceObservationModel.item_id == catalog_item_id,
            PriceObservationModel.merchant_agent_id == merchant_id,
        )
        minimum, maximum = self.session.execute(statement).one()
        return minimum, maximum