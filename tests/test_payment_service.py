from decimal import Decimal
from unittest.mock import Mock

import pytest

from backend.core.models import PaymentStatus, SystemDecision
from backend.payments.authorization import PaymentAuthorizationError
from backend.services.payment import PaymentService


def test_payment_service_creates_provider_order():
    gateway = Mock()
    gateway.create_order.return_value = Mock(
        status=PaymentStatus.PENDING,
        order_id="order_TEST123",
        amount=Decimal("1000.00"),
        currency="INR",
    )

    service = PaymentService(gateway=gateway)
    result = service.create_payment_order(
        transaction_id="tx-001",
        decision=SystemDecision.ALLOW,
        authorized_amount=Decimal("1000.00"),
        currency="INR",
    )

    assert result.order_id == "order_TEST123"
    gateway.create_order.assert_called_once_with(
        transaction_id="tx-001",
        amount=Decimal("1000.00"),
        currency="INR",
    )


def test_payment_service_rejects_non_allow_before_gateway_call():
    gateway = Mock()
    service = PaymentService(gateway=gateway)

    with pytest.raises(PaymentAuthorizationError):
        service.create_payment_order(
            transaction_id="tx-002",
            decision=SystemDecision.REVIEW,
            authorized_amount=Decimal("1000.00"),
            currency="INR",
        )

    gateway.create_order.assert_not_called()