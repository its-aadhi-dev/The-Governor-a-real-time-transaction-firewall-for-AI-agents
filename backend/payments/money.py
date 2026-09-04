from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class MoneyConversionError(ValueError):
    pass


def to_minor_units(
    amount: Decimal,
    *,
    minor_unit: int = 2,
) -> int:
    """
    Convert an exact Decimal monetary amount into provider minor units.
    """
    if amount <= Decimal("0"):
        raise MoneyConversionError(
            "Payment amount must be greater than zero."
        )

    if minor_unit < 0:
        raise MoneyConversionError(
            "Currency minor unit cannot be negative."
        )

    quantizer = Decimal("1").scaleb(-minor_unit)
    normalized = amount.quantize(quantizer, rounding=ROUND_HALF_UP)

    if normalized != amount:
        raise MoneyConversionError(
            "Amount cannot be represented in the configured "
            "currency minor unit."
        )

    scaled = normalized * (Decimal("10") ** minor_unit)
    return int(scaled)