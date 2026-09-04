from __future__ import annotations

from dataclasses import dataclass

from backend.canon.decision.engine import DecisionEngine
from backend.canon.policies.collusion import CollusionPolicy, CollusionVerdict
from backend.canon.policies.pricing import (
    PricingContext,
    PricingDecision,
    PricingPolicy,
    PricingVerdict,
)
from backend.canon.policies.reputation import (
    ReputationBand,
    ReputationPolicy,
    ReputationDecision,
)
from backend.canon.risk.engine import RiskEngine
from backend.core.collusion import CollusionDecision
from backend.core.decision import DecisionContext, DecisionResult
from backend.core.governance import GovernanceContext
from backend.core.risk import RiskAssessment
from backend.core.velocity import VelocityDecision
from backend.services.collusion import CollusionService
from backend.services.reputation import ReputationService
from backend.services.velocity import VelocityService


@dataclass(frozen=True)
class GovernorEvaluation:
    pricing: PricingDecision
    velocity: VelocityDecision
    reputation: ReputationDecision
    collusion: CollusionDecision
    risk: RiskAssessment
    decision: DecisionResult


class Governor:
    """
    Deterministic transaction firewall.

    The Governor orchestrates independent policy services and converts
    their outputs into one canonical decision.

    It does not execute payment-provider operations.
    """

    def __init__(
        self,
        *,
        pricing_policy: PricingPolicy | None = None,
        velocity_service: VelocityService,
        reputation_service: ReputationService,
        collusion_service: CollusionService,
        risk_engine: RiskEngine | None = None,
        decision_engine: DecisionEngine | None = None,
    ) -> None:
        self.pricing_policy = pricing_policy or PricingPolicy()
        self.velocity_service = velocity_service
        self.reputation_service = reputation_service
        self.collusion_service = collusion_service
        self.risk_engine = risk_engine or RiskEngine()
        self.decision_engine = decision_engine or DecisionEngine()

    def evaluate(self, *, context: GovernanceContext) -> GovernorEvaluation:
        pricing = self.pricing_policy.evaluate(
            PricingContext(
                catalog_price=context.catalog_price,
                negotiated_price=context.negotiated_price,
                merchant_floor_price=context.merchant_floor_price,
                historical_min_price=context.historical_min_price,
                historical_max_price=context.historical_max_price,
            )
        )

        velocity = self.velocity_service.evaluate(
            buyer_agent_id=context.buyer_agent_id,
        )

        reputation = self.reputation_service.evaluate(
            agent_id=context.buyer_agent_id,
        )

        collusion = self.collusion_service.evaluate(
            buyer_agent_id=context.buyer_agent_id,
            merchant_id=context.merchant_id,
        )

        risk = self.risk_engine.assess(
            pricing=pricing,
            velocity=velocity,
            reputation=reputation,
            collusion=collusion,
        )

        decision = self.decision_engine.decide(
            DecisionContext(
                pricing_blocked=pricing.verdict == PricingVerdict.BLOCK,
                pricing_requires_review=pricing.verdict == PricingVerdict.REVIEW,
                velocity_blocked=not velocity.allowed,
                reputation_poor=reputation.band == ReputationBand.POOR,
                collusion_requires_review=(
                    collusion.verdict == CollusionVerdict.REVIEW
                ),
                risk_score=risk.score,
            )
        )

        return GovernorEvaluation(
            pricing=pricing,
            velocity=velocity,
            reputation=reputation,
            collusion=collusion,
            risk=risk,
            decision=decision,
        )