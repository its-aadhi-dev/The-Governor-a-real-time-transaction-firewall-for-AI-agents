from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class BuyerRequest:
	buyer_agent_id: str
	merchant_id: str
	item_id: str
	maximum_price: Decimal


@dataclass(frozen=True)
class BuyerStrategy:
	"""Deterministic buyer behavior independent of authorization."""

	target_discount_percent: Decimal = Decimal("5")
	acceptance_buffer: Decimal = Decimal("0")

	def __post_init__(self):
		if self.target_discount_percent < Decimal("0"):
			raise ValueError("Target discount cannot be negative.")
		if self.target_discount_percent >= Decimal("100"):
			raise ValueError("Target discount must be below 100%.")
		if self.acceptance_buffer < Decimal("0"):
			raise ValueError("Acceptance buffer cannot be negative.")


class BuyerAgent:
	"""Buyer-side proposal generator; never an authorization source."""

	def __init__(
		self,
		agent_id: str,
		*,
		strategy: BuyerStrategy | None = None,
	) -> None:
		if not agent_id:
			raise ValueError("Buyer agent ID is required.")
		self.agent_id = agent_id
		self.strategy = strategy or BuyerStrategy()

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

	def initial_offer(
		self,
		*,
		asking_price: Decimal,
		maximum_price: Decimal,
	) -> Decimal:
		if asking_price <= Decimal("0"):
			raise ValueError("Asking price must be greater than zero.")
		if maximum_price <= Decimal("0"):
			raise ValueError("Maximum price must be greater than zero.")

		discount = (
			asking_price
			* self.strategy.target_discount_percent
			/ Decimal("100")
		)
		target = asking_price - discount

		return min(target, maximum_price).quantize(Decimal("0.01"))

	def should_accept(
		self,
		*,
		offered_price: Decimal,
		maximum_price: Decimal,
	) -> bool:
		if offered_price <= Decimal("0"):
			return False
		return offered_price <= maximum_price + self.strategy.acceptance_buffer
