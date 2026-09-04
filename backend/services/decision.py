from __future__ import annotations

from decimal import Decimal

from backend.canon.decision.engine import DecisionEngine
from backend.core.decision import DecisionContext, DecisionResult


class DecisionService:
    """
    Application-layer wrapper around the canonical DecisionEngine.
    """

    def __init__(self, *, engine: DecisionEngine | None = None) -> None:
        self.engine = engine or DecisionEngine()

    def decide(
        self,
        *,
        pricing_blocked: bool,
        pricing_requires_review: bool,
        velocity_blocked: bool,
        reputation_poor: bool,
        collusion_requires_review: bool,
        risk_score: Decimal,
    ) -> DecisionResult:
        context = DecisionContext(
            pricing_blocked=pricing_blocked,
            pricing_requires_review=pricing_requires_review,
            velocity_blocked=velocity_blocked,
            reputation_poor=reputation_poor,
            collusion_requires_review=collusion_requires_review,
            risk_score=risk_score,
        )

        return self.engine.decide(context)