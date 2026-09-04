from __future__ import annotations

from backend.canon.policies.collusion import CollusionDecision
from backend.canon.policies.pricing import PricingDecision
from backend.canon.policies.reputation import ReputationDecision
from backend.canon.risk.engine import RiskEngine
from backend.core.risk import RiskAssessment
from backend.core.velocity import VelocityDecision


class RiskService:
    """
    Application service that combines policy decisions.
    """

    def __init__(self, *, risk_engine: RiskEngine | None = None) -> None:
        self.risk_engine = risk_engine or RiskEngine()

    def assess(
        self,
        *,
        pricing: PricingDecision,
        velocity: VelocityDecision,
        reputation: ReputationDecision,
        collusion: CollusionDecision,
    ) -> RiskAssessment:
        return self.risk_engine.assess(
            pricing=pricing,
            velocity=velocity,
            reputation=reputation,
            collusion=collusion,
        )