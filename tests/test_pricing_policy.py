from decimal import Decimal

from backend.canon.policies.pricing import (
    PricingContext,
    PricingPolicy,
    PricingVerdict,
)


def make_context(
    *,
    catalog: str,
    negotiated: str,
    floor: str,
    historical_min: str | None = None,
    historical_max: str | None = None,
) -> PricingContext:
    return PricingContext(
        catalog_price=Decimal(catalog),
        negotiated_price=Decimal(negotiated),
        merchant_floor_price=Decimal(floor),
        historical_min_price=(
            Decimal(historical_min)
            if historical_min is not None
            else None
        ),
        historical_max_price=(
            Decimal(historical_max)
            if historical_max is not None
            else None
        ),
    )


def test_normal_discount_is_allowed():
    policy = PricingPolicy(
        review_discount_percentage=Decimal("20")
    )

    decision = policy.evaluate(
        make_context(
            catalog="10000",
            negotiated="9500",
            floor="8500",
        )
    )

    assert decision.verdict == PricingVerdict.ALLOW
    assert decision.discount_percentage == Decimal("5")


def test_price_below_floor_is_blocked():
    policy = PricingPolicy()

    decision = policy.evaluate(
        make_context(
            catalog="10000",
            negotiated="8000",
            floor="8500",
        )
    )

    assert decision.verdict == PricingVerdict.BLOCK


def test_large_discount_requires_review():
    policy = PricingPolicy(
        review_discount_percentage=Decimal("20")
    )

    decision = policy.evaluate(
        make_context(
            catalog="10000",
            negotiated="7800",
            floor="7000",
        )
    )

    assert decision.verdict == PricingVerdict.REVIEW


def test_price_below_historical_range_requires_review():
    policy = PricingPolicy()

    decision = policy.evaluate(
        make_context(
            catalog="10000",
            negotiated="9000",
            floor="8500",
            historical_min="9200",
            historical_max="10200",
        )
    )

    assert decision.verdict == PricingVerdict.REVIEW


def test_price_above_historical_range_is_allowed():
    policy = PricingPolicy()

    decision = policy.evaluate(
        make_context(
            catalog="10000",
            negotiated="10500",
            floor="8500",
            historical_min="9200",
            historical_max="10200",
        )
    )

    assert decision.verdict == PricingVerdict.ALLOW