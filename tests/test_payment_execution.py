from decimal import Decimal

import pytest

from backend.core.models import PaymentResult, PaymentStatus, SystemDecision
from backend.services.governor import GovernorService


class FakePaymentService:
    def __init__(self):
        self.calls = []

    def create_payment_order(self, *, transaction_id, amount, currency):
        self.calls.append(
            {
                "transaction_id": transaction_id,
                "amount": amount,
                "currency": currency,
            }
        )

        return PaymentResult(
            transaction_id=transaction_id,
            status=PaymentStatus.PENDING,
            success=False,
            amount=amount,
            currency=currency,
            provider="razorpay",
            order_id="order_test_123",
            provider_reference="order_test_123",
        )


class FakeTransaction:
    def __init__(
        self,
        *,
        transaction_id="txn-1",
        decision=SystemDecision.ALLOW.value,
        status="APPROVED",
        requested_price=Decimal("299.00"),
        authorized_price=Decimal("299.00"),
        currency="INR",
    ):
        self.transaction_id = transaction_id
        self.decision = decision
        self.status = status
        self.requested_price = requested_price
        self.authorized_price = authorized_price
        self.currency = currency
        self.razorpay_order_id = None


class FakeTransactionRepository:
    def __init__(self, transaction):
        self.transaction = transaction

    def get(self, transaction_id):
        if transaction_id == self.transaction.transaction_id:
            return self.transaction
        return None

    def set_authorized_amount(self, transaction, amount):
        transaction.authorized_price = amount
        return transaction

    def set_razorpay_order(self, transaction, *, order_id):
        transaction.razorpay_order_id = order_id
        return transaction


class FakeLifecycleService:
    def __init__(self):
        self.payment_pending_calls = []

    def mark_payment_pending(self, transaction_id):
        self.payment_pending_calls.append(transaction_id)


def build_service(transaction):
    payment_service = FakePaymentService()
    repository = FakeTransactionRepository(transaction)
    lifecycle = FakeLifecycleService()

    service = GovernorService(
        governor=None,
        transaction_repository=repository,
        lifecycle_service=lifecycle,
        payment_service=payment_service,
    )

    return service, payment_service, repository, lifecycle


def test_allow_creates_payment_order_and_moves_to_pending():
    transaction = FakeTransaction()

    service, payment_service, repository, lifecycle = build_service(transaction)

    result = service.execute_payment(
        context=type(
            "Context",
            (),
            {"transaction_id": transaction.transaction_id},
        )()
    )

    assert result.status == PaymentStatus.PENDING
    assert payment_service.calls == [
        {
            "transaction_id": "txn-1",
            "amount": Decimal("299.00"),
            "currency": "INR",
        }
    ]
    assert repository.transaction.razorpay_order_id == "order_test_123"
    assert lifecycle.payment_pending_calls == ["txn-1"]


@pytest.mark.parametrize(
    "decision",
    [
        SystemDecision.REVIEW.value,
        SystemDecision.BLOCK.value,
        SystemDecision.FALLBACK.value,
    ],
)
def test_non_allow_decision_cannot_create_payment(decision):
    transaction = FakeTransaction(decision=decision)

    service, payment_service, _, _ = build_service(transaction)

    with pytest.raises(ValueError):
        service.execute_payment(
            context=type(
                "Context",
                (),
                {"transaction_id": transaction.transaction_id},
            )()
        )

    assert payment_service.calls == []


def test_payment_requires_approved_status():
    transaction = FakeTransaction(
        decision=SystemDecision.ALLOW.value,
        status="GOVERNANCE_PENDING",
    )

    service, payment_service, _, _ = build_service(transaction)

    with pytest.raises(ValueError):
        service.execute_payment(
            context=type(
                "Context",
                (),
                {"transaction_id": transaction.transaction_id},
            )()
        )

    assert payment_service.calls == []