from __future__ import annotations

from decimal import Decimal

from backend.core.collusion import (
    CollusionContext,
    CollusionDecision,
    CollusionVerdict,
)


class CollusionPolicy:
    """
    Deterministic relationship-level anomaly policy.

    A suspicious relationship is sent to REVIEW.
    The policy does not directly block payment.
    """

    def __init__(
        self,
        *,
        minimum_pair_transactions: int = 5,
        review_concentration: Decimal = Decimal("0.80"),
    ) -> None:
        if minimum_pair_transactions <= 0:
            raise ValueError(
                "minimum_pair_transactions must be greater than zero."
            )

        if not (
            Decimal("0") < review_concentration <= Decimal("1")
        ):
            raise ValueError(
                "review_concentration must be between 0 and 1."
            )

        self.minimum_pair_transactions = minimum_pair_transactions
        self.review_concentration = review_concentration

    def evaluate(
        self,
        context: CollusionContext,
    ) -> CollusionDecision:
        if context.buyer_transaction_count <= 0:
            return CollusionDecision(
                verdict=CollusionVerdict.NORMAL,
                concentration_ratio=Decimal("0"),
                reason="No prior buyer transaction history exists.",
            )

        if context.buyer_merchant_transaction_count < (
            self.minimum_pair_transactions
        ):
            return CollusionDecision(
                verdict=CollusionVerdict.NORMAL,
                concentration_ratio=context.concentration_ratio,
                reason=(
                    "Buyer-merchant transaction history is below "
                    "the minimum sample size."
                ),
            )

        if context.concentration_ratio >= self.review_concentration:
            return CollusionDecision(
                verdict=CollusionVerdict.REVIEW,
                concentration_ratio=context.concentration_ratio,
                reason=(
                    "Buyer transaction activity is unusually "
                    "concentrated on this merchant."
                ),
            )

        return CollusionDecision(
            verdict=CollusionVerdict.NORMAL,
            concentration_ratio=context.concentration_ratio,
            reason="Buyer-merchant transaction concentration is normal.",
        )