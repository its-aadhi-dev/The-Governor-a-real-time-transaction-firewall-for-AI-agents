from decimal import Decimal
from unittest.mock import Mock

import pytest

from backend.canon.governor import Governor
from backend.canon.risk.engine import RiskEngine
from backend.core.collusion import CollusionContext
from backend.core.governance import GovernanceContext
from backend.core.models import SystemDecision
from backend.core.models import TransactionStatus
from backend.core.reputation import ReputationContext
from backend.core.velocity import VelocityContext
from backend.canon.policies.collusion import CollusionPolicy
from backend.canon.policies.reputation import ReputationPolicy
from backend.canon.policies.velocity import VelocityPolicy
from backend.services.collusion import CollusionService
from backend.services.reputation import ReputationService
from backend.services.velocity import VelocityService


def build_governor(*, velocity_allowed: bool = True):
    velocity_service = Mock()
    velocity_service.evaluate.return_value = Mock(
        allowed=velocity_allowed,
        reason="test",
        transaction_count=0,
        limit=5,
        window_seconds=60,
    )
    reputation_service = Mock()
    reputation_service.evaluate.return_value = Mock(
        band=Mock(value="GOOD"),
        score=Decimal("1.00"),
        reason="test",
    )
    collusion_service = Mock()
    collusion_service.evaluate.return_value = Mock(
        verdict=Mock(value="NORMAL"),
        concentration_ratio=Decimal("0"),
        reason="test",
    )
    return Governor(
        velocity_service=velocity_service,
        reputation_service=reputation_service,
        collusion_service=collusion_service,
        risk_engine=RiskEngine(),
    )


def make_context(transaction_id: str) -> GovernanceContext:
    return GovernanceContext(
        transaction_id=transaction_id,
        buyer_agent_id="buyer-001",
        merchant_id="merchant-001",
        catalog_item_id="item-001",
        catalog_price=Decimal("10000"),
        negotiated_price=Decimal("9500"),
        merchant_floor_price=Decimal("8500"),
        historical_min_price=None,
        historical_max_price=None,
    )


def test_governor_allows_safe_transaction():
    result = build_governor().evaluate(context=make_context("tx-001"))

    assert result.decision.decision == SystemDecision.ALLOW
    assert result.risk.score == Decimal("0.00")


def test_governor_blocks_velocity_failure():
    result = build_governor(velocity_allowed=False).evaluate(
        context=make_context("tx-002")
    )

    assert result.decision.decision == SystemDecision.BLOCK


def make_transaction(
    *,
    decision: str,
    status: str = TransactionStatus.APPROVED.value,
):
    return Mock(
        transaction_id="tx-003",
        status=status,
        decision=decision,
        authorized_price=Decimal("9500.00"),
        requested_price=Decimal("10000.00"),
        currency="INR",
        buyer_agent_id="buyer-001",
        merchant_agent_id="merchant-001",
        item_id="item-001",
    )


def test_execute_payment_uses_authorized_amount_and_marks_pending():
    transaction_repository = Mock()
    transaction_repository.get.return_value = make_transaction(
        decision=SystemDecision.ALLOW.value,
    )
    lifecycle_service = Mock()
    payment_service = Mock()
    payment_service.create_payment_order.return_value = Mock(
        order_id="order_TEST123",
    )
    governor_service = build_governor()
    service = __import__(
        "backend.services.governor",
        fromlist=["GovernorService"],
    ).GovernorService(
        governor=governor_service,
        transaction_repository=transaction_repository,
        lifecycle_service=lifecycle_service,
        payment_service=payment_service,
    )

    result = service.execute_payment(context=make_context("tx-003"))

    assert result.order_id == "order_TEST123"
    payment_service.create_payment_order.assert_called_once_with(
        transaction_id="tx-003",
        amount=Decimal("9500.00"),
        currency="INR",
    )
    transaction_repository.set_razorpay_order.assert_called_once_with(
        transaction_repository.get.return_value,
        order_id="order_TEST123",
    )
    lifecycle_service.mark_payment_pending.assert_called_once_with("tx-003")


def test_execute_payment_rejects_non_allow_without_provider_call():
    transaction_repository = Mock()
    transaction_repository.get.return_value = make_transaction(
        decision=SystemDecision.REVIEW.value,
    )
    payment_service = Mock()
    service = __import__(
        "backend.services.governor",
        fromlist=["GovernorService"],
    ).GovernorService(
        governor=build_governor(),
        transaction_repository=transaction_repository,
        lifecycle_service=Mock(),
        payment_service=payment_service,
    )

    with pytest.raises(ValueError):
        service.execute_payment(context=make_context("tx-003"))

    payment_service.create_payment_order.assert_not_called()