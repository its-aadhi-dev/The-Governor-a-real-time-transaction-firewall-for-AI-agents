from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class BuyerRequest:
	buyer_agent_id: str
	merchant_id: str
	item_id: str
	maximum_price: Decimal


class BuyerAgent:
	"""Buyer-side proposal generator; never an authorization source."""

	def __init__(self, agent_id: str) -> None:
		self.agent_id = agent_id

	def create_request(
		self,
		*,
		merchant_id: str,
		item_id: str,
		maximum_price: Decimal,
	) -> BuyerRequest:
		if maximum_price <= Decimal("0"):
			raise ValueError("Maximum price must be greater than zero.")
		return BuyerRequest(self.agent_id, merchant_id, item_id, maximum_price)

	def propose_price(self, *, target_price: Decimal) -> Decimal:
		if target_price <= Decimal("0"):
			raise ValueError("Target price must be greater than zero.")
		return target_price
