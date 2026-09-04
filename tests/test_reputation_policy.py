from decimal import Decimal

import pytest

from backend.canon.policies.reputation import ReputationPolicy
from backend.core.reputation import ReputationBand, ReputationContext


def make_context(score: str) -> ReputationContext:
    return ReputationContext(
        reputation_score=Decimal(score),
        transaction_count=10,
        successful_transaction_count=9,
        blocked_transaction_count=1,
    )


def test_high_reputation_is_good():
    policy = ReputationPolicy()

    decision = policy.evaluate(make_context("0.90"))

    assert decision.band == ReputationBand.GOOD


def test_middle_reputation_requires_review():
    policy = ReputationPolicy()

    decision = policy.evaluate(make_context("0.55"))

    assert decision.band == ReputationBand.REVIEW


def test_low_reputation_is_poor():
    policy = ReputationPolicy()

    decision = policy.evaluate(make_context("0.25"))

    assert decision.band == ReputationBand.POOR


def test_score_is_clamped():
    policy = ReputationPolicy()

    high = policy.evaluate(make_context("2.00"))
    low = policy.evaluate(make_context("-1.00"))

    assert high.score == Decimal("1")
    assert low.score == Decimal("0")


def test_invalid_thresholds_fail():
    with pytest.raises(ValueError):
        ReputationPolicy(
            good_threshold=Decimal("0.40"),
            poor_threshold=Decimal("0.70"),
        )