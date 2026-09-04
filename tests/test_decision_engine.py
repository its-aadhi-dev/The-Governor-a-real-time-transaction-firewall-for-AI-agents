from decimal import Decimal

import pytest

from backend.canon.decision.engine import DecisionEngine
from backend.core.decision import DecisionContext
from backend.core.models import SystemDecision


def make_context(
    *,
    pricing_blocked: bool = False,
    pricing_requires_review: bool = False,
    velocity_blocked: bool = False,
    reputation_poor: bool = False,
    collusion_requires_review: bool = False,
    risk_score: str = "0.00",
) -> DecisionContext:
    return DecisionContext(
        pricing_blocked=pricing_blocked,
        pricing_requires_review=pricing_requires_review,
        velocity_blocked=velocity_blocked,
        reputation_poor=reputation_poor,
        collusion_requires_review=collusion_requires_review,
        risk_score=Decimal(risk_score),
    )


def test_safe_transaction_is_allowed():
    result = DecisionEngine().decide(make_context())

    assert result.decision == SystemDecision.ALLOW
    assert result.requires_human_review is False


def test_pricing_block_takes_precedence():
    result = DecisionEngine().decide(
        make_context(pricing_blocked=True, risk_score="0.10")
    )

    assert result.decision == SystemDecision.BLOCK


def test_velocity_block_takes_precedence():
    result = DecisionEngine().decide(
        make_context(velocity_blocked=True, risk_score="0.20")
    )

    assert result.decision == SystemDecision.BLOCK


def test_critical_risk_blocks():
    result = DecisionEngine().decide(make_context(risk_score="0.80"))

    assert result.decision == SystemDecision.BLOCK


def test_review_signal_requires_review():
    result = DecisionEngine().decide(
        make_context(pricing_requires_review=True, risk_score="0.20")
    )

    assert result.decision == SystemDecision.REVIEW
    assert result.requires_human_review is True


def test_high_risk_requires_review():
    result = DecisionEngine().decide(make_context(risk_score="0.60"))

    assert result.decision == SystemDecision.REVIEW


def test_poor_reputation_with_high_risk_can_fallback():
    result = DecisionEngine(enable_fallback=True).decide(
        make_context(reputation_poor=True, risk_score="0.60")
    )

    assert result.decision == SystemDecision.FALLBACK
    assert result.fallback_allowed is True


def test_fallback_can_be_disabled():
    result = DecisionEngine(enable_fallback=False).decide(
        make_context(reputation_poor=True, risk_score="0.60")
    )

    assert result.decision == SystemDecision.REVIEW


def test_hard_block_beats_fallback():
    result = DecisionEngine().decide(
        make_context(
            pricing_blocked=True,
            reputation_poor=True,
            risk_score="0.80",
        )
    )

    assert result.decision == SystemDecision.BLOCK


def test_critical_risk_beats_review():
    result = DecisionEngine().decide(
        make_context(
            pricing_requires_review=True,
            collusion_requires_review=True,
            risk_score="0.90",
        )
    )

    assert result.decision == SystemDecision.BLOCK


def test_exact_high_risk_threshold_requires_review():
    engine = DecisionEngine(
        high_risk_threshold=Decimal("0.50"),
        critical_risk_threshold=Decimal("0.75"),
    )

    result = engine.decide(make_context(risk_score="0.50"))

    assert result.decision == SystemDecision.REVIEW


def test_exact_critical_threshold_blocks():
    engine = DecisionEngine(
        high_risk_threshold=Decimal("0.50"),
        critical_risk_threshold=Decimal("0.75"),
    )

    result = engine.decide(make_context(risk_score="0.75"))

    assert result.decision == SystemDecision.BLOCK