from __future__ import annotations

from decimal import Decimal
from typing import Any

import razorpay

from backend.core.models import PaymentResult, PaymentStatus
from backend.payments.money import to_minor_units


class RazorpayGatewayError(RuntimeError):
	pass


class RazorpayAdapter:
	"""
	Thin wrapper around the Razorpay SDK.

	Provider-specific objects are contained here.
	"""

	provider_name = "razorpay"

	def __init__(
		self,
		*,
		key_id: str,
		key_secret: str,
		client: Any | None = None,
	) -> None:
		self.key_id = key_id
		self.client = client or razorpay.Client(auth=(key_id, key_secret))

	def create_order(
		self,
		*,
		transaction_id: str,
		amount: Decimal,
		currency: str,
	) -> PaymentResult:
		minor_amount = to_minor_units(amount)
		normalized_currency = currency.upper()
		receipt = f"gov-{transaction_id}"[:40]

		try:
			order = self.client.order.create(
				data={
					"amount": minor_amount,
					"currency": normalized_currency,
					"receipt": receipt,
					"notes": {"transaction_id": transaction_id},
				}
			)
		except Exception as exc:
			raise RazorpayGatewayError(
				f"Razorpay order creation failed: {exc}"
			) from exc

		order_id = str(order["id"])
		return PaymentResult(
			transaction_id=transaction_id,
			status=PaymentStatus.PENDING,
			provider=self.provider_name,
			success=False,
			amount=amount,
			currency=normalized_currency,
			order_id=order_id,
			provider_reference=order_id,
		)
