from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MerchantQuote:
	merchant_id: str
	item_id: str
	price: Decimal
	currency: str = "INR"


class MerchantAgent:
	"""Merchant-side proposal component backed by catalog/policy data."""

	def __init__(self, merchant_id: str) -> None:
		self.merchant_id = merchant_id

	def quote(self, *, item_id: str, price: Decimal) -> MerchantQuote:
		if price <= Decimal("0"):
			raise ValueError("Merchant price must be greater than zero.")
		return MerchantQuote(self.merchant_id, item_id, price)
