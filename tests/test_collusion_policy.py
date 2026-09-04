from decimal import Decimal

import pytest

from backend.canon.policies.collusion import CollusionPolicy
from backend.core.collusion import CollusionContext, CollusionVerdict


def make_context(
    *,
    buyer_count: int,
    pair_count: int,
) -> CollusionContext:
    ratio = (
        Decimal(pair_count) / Decimal(buyer_count)
        if buyer_count > 0
        else Decimal("0")
    )

    return CollusionContext(
        buyer_agent_id="buyer-001",
        merchant_id="merchant-001",
        buyer_transaction_count=buyer_count,
        buyer_merchant_transaction_count=pair_count,
        concentration_ratio=ratio,
    )


def test_low_concentration_is_normal():
    policy = CollusionPolicy(
        minimum_pair_transactions=5,
        review_concentration=Decimal("0.80"),
    )

    decision = policy.evaluate(make_context(buyer_count=10, pair_count=4))

    assert decision.verdict == CollusionVerdict.NORMAL


def test_high_concentration_requires_review():
    policy = CollusionPolicy(
        minimum_pair_transactions=5,
        review_concentration=Decimal("0.80"),
    )

    decision = policy.evaluate(make_context(buyer_count=10, pair_count=8))

    assert decision.verdict == CollusionVerdict.REVIEW


def test_small_sample_does_not_trigger_review():
    policy = CollusionPolicy(
        minimum_pair_transactions=5,
        review_concentration=Decimal("0.80"),
    )

    decision = policy.evaluate(make_context(buyer_count=2, pair_count=2))

    assert decision.verdict == CollusionVerdict.NORMAL


def test_zero_history_is_normal():
    policy = CollusionPolicy()

    decision = policy.evaluate(make_context(buyer_count=0, pair_count=0))

    assert decision.verdict == CollusionVerdict.NORMAL


def test_invalid_configuration_fails():
    with pytest.raises(ValueError):
        CollusionPolicy(minimum_pair_transactions=0)

    with pytest.raises(ValueError):
        CollusionPolicy(review_concentration=Decimal("0"))