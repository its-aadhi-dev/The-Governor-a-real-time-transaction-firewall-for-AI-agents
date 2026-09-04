from __future__ import annotations

from decimal import Decimal

from backend.canon.policies.collusion import (
    CollusionDecision,
    CollusionVerdict,
)
from backend.canon.policies.pricing import PricingDecision, PricingVerdict
from backend.canon.policies.reputation import (
    ReputationBand,
    ReputationDecision,
)
from backend.core.risk import RiskAssessment, RiskLevel, RiskSignal
from backend.core.velocity import VelocityDecision


class RiskEngine:
    """
    Combines independent policy signals into a normalized risk score.

    The engine does not authorize or execute payments.
    """

    DEFAULT_WEIGHTS = {
        "pricing": Decimal("0.30"),
        "velocity": Decimal("0.30"),
        "reputation": Decimal("0.20"),
        "collusion": Decimal("0.20"),
    }

    def __init__(
        self,
        *,
        weights: dict[str, Decimal] | None = None,
    ) -> None:
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self._validate_weights()

    def _validate_weights(self) -> None:
        required = set(self.DEFAULT_WEIGHTS)

        if set(self.weights) != required:
            raise ValueError(
                f"Risk weights must contain exactly: {sorted(required)}"
            )

        if any(weight < Decimal("0") for weight in self.weights.values()):
            raise ValueError("Risk weights cannot be negative.")

        total = sum(self.weights.values())

        if total != Decimal("1"):
            raise ValueError("Risk weights must sum to exactly 1.00.")

    @staticmethod
    def _pricing_score(decision: PricingDecision) -> tuple[Decimal, str]:
        if decision.verdict == PricingVerdict.BLOCK:
            return Decimal("1.00"), decision.reason

        if decision.verdict == PricingVerdict.REVIEW:
            return Decimal("0.60"), decision.reason

        return Decimal("0.00"), decision.reason

    @staticmethod
    def _velocity_score(decision: VelocityDecision) -> tuple[Decimal, str]:
        if not decision.allowed:
            return Decimal("1.00"), decision.reason

        utilization = (
            Decimal(decision.transaction_count) / Decimal(decision.limit)
        )

        if utilization >= Decimal("0.80"):
            return (
                Decimal("0.50"),
                "Transaction velocity is approaching the configured limit.",
            )

        return Decimal("0.00"), decision.reason

    @staticmethod
    def _reputation_score(
        decision: ReputationDecision,
    ) -> tuple[Decimal, str]:
        if decision.band == ReputationBand.POOR:
            return Decimal("0.90"), decision.reason

        if decision.band == ReputationBand.REVIEW:
            return Decimal("0.50"), decision.reason

        return Decimal("0.00"), decision.reason

    @staticmethod
    def _collusion_score(
        decision: CollusionDecision,
    ) -> tuple[Decimal, str]:
        if decision.verdict == CollusionVerdict.REVIEW:
            return Decimal("0.70"), decision.reason

        return Decimal("0.00"), decision.reason

    @staticmethod
    def _risk_level(score: Decimal) -> RiskLevel:
        if score >= Decimal("0.75"):
            return RiskLevel.CRITICAL

        if score >= Decimal("0.50"):
            return RiskLevel.HIGH

        if score >= Decimal("0.25"):
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def assess(
        self,
        *,
        pricing: PricingDecision,
        velocity: VelocityDecision,
        reputation: ReputationDecision,
        collusion: CollusionDecision,
    ) -> RiskAssessment:
        pricing_score, pricing_reason = self._pricing_score(pricing)
        velocity_score, velocity_reason = self._velocity_score(velocity)
        reputation_score, reputation_reason = self._reputation_score(reputation)
        collusion_score, collusion_reason = self._collusion_score(collusion)

        raw_signals = [
            ("pricing", pricing_score, pricing_reason),
            ("velocity", velocity_score, velocity_reason),
            ("reputation", reputation_score, reputation_reason),
            ("collusion", collusion_score, collusion_reason),
        ]

        signals = tuple(
            RiskSignal(
                name=name,
                score=score,
                weight=self.weights[name],
                reason=reason,
            )
            for name, score, reason in raw_signals
        )

        final_score = sum(
            signal.score * signal.weight
            for signal in signals
        )
        final_score = max(Decimal("0"), min(Decimal("1"), final_score))

        reasons = tuple(
            signal.reason
            for signal in signals
            if signal.score > Decimal("0")
        )

        return RiskAssessment(
            score=final_score,
            level=self._risk_level(final_score),
            signals=signals,
            reasons=reasons,
        )