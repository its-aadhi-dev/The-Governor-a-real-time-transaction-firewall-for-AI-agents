from decimal import Decimal

import pytest

from backend.payments.razorpay import RazorpayAdapter, RazorpayGatewayError


class FakeOrderClient:
    def __init__(self):
        self.calls = []

    def create(self, *, data):
        self.calls.append(data)
        return {
            "id": "order_TEST123",
            "amount": data["amount"],
            "currency": data["currency"],
            "receipt": data["receipt"],
            "status": "created",
        }


class FakeRazorpayClient:
    def __init__(self):
        self.order = FakeOrderClient()


def test_create_order_converts_to_minor_units():
    client = FakeRazorpayClient()
    gateway = RazorpayAdapter(
        key_id="test_key",
        key_secret="test_secret",
        client=client,
    )

    result = gateway.create_order(
        transaction_id="tx-001",
        amount=Decimal("1250.50"),
        currency="inr",
    )

    assert result.order_id == "order_TEST123"
    assert result.amount == Decimal("1250.50")
    assert result.currency == "INR"
    assert result.status.value == "PENDING"
    assert client.order.calls[0]["amount"] == 125050


class FailingOrderClient:
    def create(self, *, data):
        raise RuntimeError("provider unavailable")


class FailingRazorpayClient:
    def __init__(self):
        self.order = FailingOrderClient()


def test_provider_failure_is_wrapped():
    gateway = RazorpayAdapter(
        key_id="test_key",
        key_secret="test_secret",
        client=FailingRazorpayClient(),
    )

    with pytest.raises(RazorpayGatewayError):
        gateway.create_order(
            transaction_id="tx-002",
            amount=Decimal("500.00"),
            currency="INR",
        )