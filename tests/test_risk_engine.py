from datetime import datetime, timezone
from decimal import Decimal

import pytest

from backend.canon.policies.collusion import CollusionPolicy
from backend.canon.policies.pricing import PricingPolicy
from backend.canon.policies.reputation import ReputationPolicy
from backend.canon.policies.velocity import VelocityPolicy
from backend.canon.risk.engine import RiskEngine
from backend.core.collusion import CollusionContext
from backend.core.reputation import ReputationContext
from backend.core.risk import RiskLevel
from backend.core.velocity import VelocityContext
from backend.canon.policies.pricing import PricingContext


def test_all_normal_signals_produce_low_risk():
    pricing = PricingPolicy().evaluate(
        PricingContext(
            catalog_price=Decimal("10000"),
            negotiated_price=Decimal("9500"),
            merchant_floor_price=Decimal("8500"),
        )
    )
    velocity = VelocityPolicy(max_transactions=5, window_seconds=60).evaluate(
        VelocityContext(
            agent_id="buyer-001",
            window_seconds=60,
            transaction_count=1,
            window_started_at=datetime.now(timezone.utc),
        )
    )
    reputation = ReputationPolicy().evaluate(
        ReputationContext(
            reputation_score=Decimal("0.95"),
            transaction_count=20,
            successful_transaction_count=20,
            blocked_transaction_count=0,
        )
    )
    collusion = CollusionPolicy().evaluate(
        CollusionContext(
            buyer_agent_id="buyer-001",
            merchant_id="merchant-001",
            buyer_transaction_count=10,
            buyer_merchant_transaction_count=2,
            concentration_ratio=Decimal("0.20"),
        )
    )

    assessment = RiskEngine().assess(
        pricing=pricing,
        velocity=velocity,
        reputation=reputation,
        collusion=collusion,
    )

    assert assessment.score == Decimal("0.00")
    assert assessment.level == RiskLevel.LOW


def test_multiple_signals_raise_risk():
    pricing = PricingPolicy().evaluate(
        PricingContext(
            catalog_price=Decimal("10000"),
            negotiated_price=Decimal("6000"),
            merchant_floor_price=Decimal("5000"),
        )
    )
    velocity = VelocityPolicy(max_transactions=5, window_seconds=60).evaluate(
        VelocityContext(
            agent_id="buyer-001",
            window_seconds=60,
            transaction_count=5,
            window_started_at=datetime.now(timezone.utc),
        )
    )
    reputation = ReputationPolicy().evaluate(
        ReputationContext(
            reputation_score=Decimal("0.20"),
            transaction_count=20,
            successful_transaction_count=8,
            blocked_transaction_count=12,
        )
    )
    collusion = CollusionPolicy().evaluate(
        CollusionContext(
            buyer_agent_id="buyer-001",
            merchant_id="merchant-001",
            buyer_transaction_count=10,
            buyer_merchant_transaction_count=9,
            concentration_ratio=Decimal("0.90"),
        )
    )

    assessment = RiskEngine().assess(
        pricing=pricing,
        velocity=velocity,
        reputation=reputation,
        collusion=collusion,
    )

    assert assessment.score > Decimal("0.75")
    assert assessment.level == RiskLevel.CRITICAL
    assert len(assessment.signals) == 4
    assert len(assessment.reasons) == 4


def test_risk_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        RiskEngine(
            weights={
                "pricing": Decimal("0.40"),
                "velocity": Decimal("0.30"),
                "reputation": Decimal("0.20"),
                "collusion": Decimal("0.20"),
            }
        )


def test_negative_risk_weight_fails():
    with pytest.raises(ValueError):
        RiskEngine(
            weights={
                "pricing": Decimal("-0.10"),
                "velocity": Decimal("0.40"),
                "reputation": Decimal("0.30"),
                "collusion": Decimal("0.40"),
            }
        )