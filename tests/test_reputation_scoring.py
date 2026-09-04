from decimal import Decimal

from backend.canon.policies.reputation import ReputationPolicy


def test_success_delta_is_small_positive():
    policy = ReputationPolicy()

    delta = policy.success_delta()

    assert delta.score_change == Decimal("0.02")


def test_suspicious_block_delta_is_negative():
    policy = ReputationPolicy()

    delta = policy.suspicious_block_delta()

    assert delta.score_change == Decimal("-0.10")