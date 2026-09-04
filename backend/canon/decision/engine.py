from __future__ import annotations

from decimal import Decimal

from backend.core.decision import DecisionContext, DecisionResult
from backend.core.models import SystemDecision


class DecisionEngine:
    """
    Canonical deterministic Governor decision engine.

    This layer is the only component that converts policy/risk
    signals into the final system decision.
    """

    def __init__(
        self,
        *,
        critical_risk_threshold: Decimal = Decimal("0.75"),
        high_risk_threshold: Decimal = Decimal("0.50"),
        enable_fallback: bool = True,
    ) -> None:
        if not (
            Decimal("0")
            <= high_risk_threshold
            < critical_risk_threshold
            <= Decimal("1")
        ):
            raise ValueError(
                "Risk thresholds must satisfy "
                "0 <= high < critical <= 1."
            )

        self.critical_risk_threshold = critical_risk_threshold
        self.high_risk_threshold = high_risk_threshold
        self.enable_fallback = enable_fallback

    def decide(self, context: DecisionContext) -> DecisionResult:
        if context.pricing_blocked:
            return DecisionResult(
                decision=SystemDecision.BLOCK,
                reason="Pricing policy contains a hard violation.",
                risk_score=context.risk_score,
                requires_human_review=False,
                fallback_allowed=False,
            )

        if context.velocity_blocked:
            return DecisionResult(
                decision=SystemDecision.BLOCK,
                reason="Transaction velocity limit has been exceeded.",
                risk_score=context.risk_score,
                requires_human_review=False,
                fallback_allowed=False,
            )

        if context.risk_score >= self.critical_risk_threshold:
            return DecisionResult(
                decision=SystemDecision.BLOCK,
                reason="Risk score is in the critical range.",
                risk_score=context.risk_score,
                requires_human_review=False,
                fallback_allowed=False,
            )

        if (
            self.enable_fallback
            and context.reputation_poor
            and context.risk_score >= self.high_risk_threshold
        ):
            return DecisionResult(
                decision=SystemDecision.FALLBACK,
                reason=(
                    "Agent reputation is poor and transaction risk "
                    "is too high for automatic approval."
                ),
                risk_score=context.risk_score,
                requires_human_review=True,
                fallback_allowed=True,
            )

        if (
            context.pricing_requires_review
            or context.collusion_requires_review
            or context.reputation_poor
            or context.risk_score >= self.high_risk_threshold
        ):
            return DecisionResult(
                decision=SystemDecision.REVIEW,
                reason="Transaction requires additional governance review.",
                risk_score=context.risk_score,
                requires_human_review=True,
                fallback_allowed=self.enable_fallback,
            )

        return DecisionResult(
            decision=SystemDecision.ALLOW,
            reason="Transaction satisfies current governance policies.",
            risk_score=context.risk_score,
            requires_human_review=False,
            fallback_allowed=False,
        )