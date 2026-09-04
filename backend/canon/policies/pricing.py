from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class PricingVerdict(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class PricingContext:
    catalog_price: Decimal
    negotiated_price: Decimal
    merchant_floor_price: Decimal

    historical_min_price: Decimal | None = None
    historical_max_price: Decimal | None = None


@dataclass(frozen=True)
class PricingDecision:
    verdict: PricingVerdict
    reason: str
    discount_amount: Decimal
    discount_percentage: Decimal


class PricingPolicy:
    """
    Deterministic economic policy.

    This policy evaluates only price-related constraints.
    It does not authorize payment.
    """

    def __init__(
        self,
        *,
        review_discount_percentage: Decimal = Decimal("20"),
    ) -> None:
        if review_discount_percentage < Decimal("0"):
            raise ValueError(
                "Review discount percentage cannot be negative."
            )

        self.review_discount_percentage = review_discount_percentage

    def evaluate(
        self,
        context: PricingContext,
    ) -> PricingDecision:
        if context.catalog_price <= Decimal("0"):
            raise ValueError("Catalog price must be greater than zero.")

        if context.negotiated_price <= Decimal("0"):
            return PricingDecision(
                verdict=PricingVerdict.BLOCK,
                reason="Negotiated price must be greater than zero.",
                discount_amount=context.catalog_price,
                discount_percentage=Decimal("100"),
            )

        if context.merchant_floor_price <= Decimal("0"):
            raise ValueError(
                "Merchant floor price must be greater than zero."
            )

        if context.negotiated_price < context.merchant_floor_price:
            discount_amount = (
                context.catalog_price - context.negotiated_price
            )
            discount_percentage = (
                discount_amount / context.catalog_price
            ) * Decimal("100")

            return PricingDecision(
                verdict=PricingVerdict.BLOCK,
                reason="Negotiated price is below merchant floor.",
                discount_amount=discount_amount,
                discount_percentage=discount_percentage,
            )

        discount_amount = (
            context.catalog_price - context.negotiated_price
        )

        discount_percentage = (
            discount_amount / context.catalog_price
        ) * Decimal("100")

        if (
            context.historical_min_price is not None
            and context.negotiated_price < context.historical_min_price
        ):
            return PricingDecision(
                verdict=PricingVerdict.REVIEW,
                reason=(
                    "Negotiated price is below the historical "
                    "observed price range."
                ),
                discount_amount=discount_amount,
                discount_percentage=discount_percentage,
            )

        if (
            context.historical_max_price is not None
            and context.negotiated_price > context.historical_max_price
        ):
            return PricingDecision(
                verdict=PricingVerdict.ALLOW,
                reason=(
                    "Negotiated price is above the historical "
                    "observed price range."
                ),
                discount_amount=discount_amount,
                discount_percentage=discount_percentage,
            )

        if discount_percentage > self.review_discount_percentage:
            return PricingDecision(
                verdict=PricingVerdict.REVIEW,
                reason="Discount exceeds automatic approval threshold.",
                discount_amount=discount_amount,
                discount_percentage=discount_percentage,
            )

        return PricingDecision(
            verdict=PricingVerdict.ALLOW,
            reason="Negotiated price is within pricing policy.",
            discount_amount=discount_amount,
            discount_percentage=discount_percentage,
        )