from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from backend.core.reputation import (
    ReputationBand,
    ReputationContext,
    ReputationDecision,
)


class ReputationPolicy:
    """
    Deterministic reputation classification.

    This policy does not modify the database.
    """

    def __init__(
        self,
        *,
        good_threshold: Decimal = Decimal("0.70"),
        poor_threshold: Decimal = Decimal("0.40"),
    ) -> None:
        if not (
            Decimal("0") <= poor_threshold < good_threshold <= Decimal("1")
        ):
            raise ValueError(
                "Thresholds must satisfy 0 <= poor < good <= 1."
            )

        self.good_threshold = good_threshold
        self.poor_threshold = poor_threshold

    def evaluate(
        self,
        context: ReputationContext,
    ) -> ReputationDecision:
        score = max(
            Decimal("0"),
            min(Decimal("1"), context.reputation_score),
        )

        if score >= self.good_threshold:
            return ReputationDecision(
                band=ReputationBand.GOOD,
                score=score,
                reason="Agent reputation is within the trusted range.",
            )

        if score <= self.poor_threshold:
            return ReputationDecision(
                band=ReputationBand.POOR,
                score=score,
                reason="Agent reputation is below the trusted range.",
            )

        return ReputationDecision(
            band=ReputationBand.REVIEW,
            score=score,
            reason="Agent reputation requires additional scrutiny.",
        )

    def success_delta(self) -> ReputationDelta:
        return ReputationDelta(
            score_change=Decimal("0.02"),
            reason="Successful payment-path transaction.",
        )

    def suspicious_block_delta(self) -> ReputationDelta:
        return ReputationDelta(
            score_change=Decimal("-0.10"),
            reason="Transaction blocked for suspicious policy behavior.",
        )


@dataclass(frozen=True)
class ReputationDelta:
    score_change: Decimal
    reason: str