from __future__ import annotations

from decimal import Decimal

from backend.core.models import PaymentResult
from backend.payments.razorpay import RazorpayAdapter


class PaymentService:
    """
    Application-layer payment orchestration.

    This service should only be called after Governor authorization.
    """

    def __init__(
        self,
        *,
        gateway: RazorpayAdapter,
    ) -> None:
        self.gateway = gateway

    def create_payment_order(
        self,
        *,
        transaction_id: str,
        amount: Decimal,
        currency: str,
    ) -> PaymentResult:
        if amount <= Decimal("0"):
            raise ValueError(
                "Payment amount must be greater than zero."
            )

        return self.gateway.create_order(
            transaction_id=transaction_id,
            amount=amount,
            currency=currency,
        )

    def verify_payment_signature(
        self,
        *,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        return self.gateway.verify_payment_signature(
            order_id=order_id,
            payment_id=payment_id,
            signature=signature,
        )
        