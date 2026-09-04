from decimal import Decimal
from unittest.mock import Mock

from backend.core.models import PaymentStatus
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
        amount=Decimal("1000.00"),
        currency="INR",
    )

    assert result.order_id == "order_TEST123"
    gateway.create_order.assert_called_once_with(
        transaction_id="tx-001",
        amount=Decimal("1000.00"),
        currency="INR",
    )