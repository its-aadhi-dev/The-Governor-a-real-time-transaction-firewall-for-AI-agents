from __future__ import annotations

from decimal import Decimal

from backend.core.models import PaymentResult, SystemDecision
from backend.payments.authorization import require_payment_authorization
from backend.payments.razorpay import RazorpayAdapter


class PaymentService:
    """
    Application-layer payment orchestration.

    This service should only be called after Governor authorization.
    """

    def __init__(self, *, gateway: RazorpayAdapter) -> None:
        self.gateway = gateway

    def create_payment_order(
        self,
        *,
        transaction_id: str,
        decision: SystemDecision,
        authorized_amount: Decimal,
        currency: str,
    ) -> PaymentResult:
        require_payment_authorization(decision=decision)

        return self.gateway.create_order(
            transaction_id=transaction_id,
            amount=authorized_amount,
            currency=currency,
        )