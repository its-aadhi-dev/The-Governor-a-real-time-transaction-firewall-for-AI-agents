from decimal import Decimal
from unittest.mock import Mock

from backend.canon.governor import Governor
from backend.canon.risk.engine import RiskEngine
from backend.core.collusion import CollusionContext
from backend.core.governance import GovernanceContext
from backend.core.models import SystemDecision
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