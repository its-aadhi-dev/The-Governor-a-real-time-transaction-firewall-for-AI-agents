from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class GovernanceContext:
    transaction_id: str

    buyer_agent_id: str
    merchant_id: str
    catalog_item_id: str

    catalog_price: Decimal
    negotiated_price: Decimal
    merchant_floor_price: Decimal

    historical_min_price: Decimal | None
    historical_max_price: Decimal | None