from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MerchantQuote:
	merchant_id: str
	item_id: str
	price: Decimal
	currency: str = "INR"


@dataclass(frozen=True)
class MerchantStrategy:
	"""Deterministic merchant behavior backed by catalog/policy data."""

	counter_step_percent: Decimal = Decimal("2")

	def __post_init__(self):
		if self.counter_step_percent < Decimal("0"):
			raise ValueError("Counter step cannot be negative.")
		if self.counter_step_percent >= Decimal("100"):
			raise ValueError("Counter step must be below 100%.")


class MerchantAgent:
	"""Merchant-side proposal component backed by catalog/policy data."""

	def __init__(
		self,
		merchant_id: str,
		*,
		strategy: MerchantStrategy | None = None,
	) -> None:
		if not merchant_id:
			raise ValueError("Merchant agent ID is required.")
		self.merchant_id = merchant_id
		self.strategy = strategy or MerchantStrategy()

	def quote(self, *, item_id: str, price: Decimal) -> MerchantQuote:
		if price <= Decimal("0"):
			raise ValueError("Merchant price must be greater than zero.")
		return MerchantQuote(self.merchant_id, item_id, price)

	def counter_price(
		self,
		*,
		buyer_price: Decimal,
		asking_price: Decimal,
		floor_price: Decimal,
	) -> Decimal:
		if buyer_price <= Decimal("0"):
			raise ValueError("Buyer price must be greater than zero.")
		if asking_price <= Decimal("0"):
			raise ValueError("Asking price must be greater than zero.")
		if floor_price <= Decimal("0"):
			raise ValueError("Floor price must be greater than zero.")
		if buyer_price >= asking_price:
			return buyer_price

		gap = asking_price - buyer_price
		step = gap * self.strategy.counter_step_percent / Decimal("100")
		return max(asking_price - step, floor_price).quantize(Decimal("0.01"))
