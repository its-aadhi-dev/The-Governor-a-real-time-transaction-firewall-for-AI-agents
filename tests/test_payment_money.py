from decimal import Decimal

import pytest

from backend.payments.money import MoneyConversionError, to_minor_units


def test_inr_conversion():
    assert to_minor_units(Decimal("299.00")) == 29900


def test_zero_amount_fails():
    with pytest.raises(MoneyConversionError):
        to_minor_units(Decimal("0.00"))


def test_negative_amount_fails():
    with pytest.raises(MoneyConversionError):
        to_minor_units(Decimal("-10.00"))


def test_decimal_is_exact():
    assert to_minor_units(Decimal("999.99")) == 99999