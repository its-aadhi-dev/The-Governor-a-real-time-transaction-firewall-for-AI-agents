import pytest

from backend.core.models import SystemDecision
from backend.payments.authorization import (
    PaymentAuthorizationError,
    require_payment_authorization,
)


def test_allow_permits_payment():
    require_payment_authorization(decision=SystemDecision.ALLOW)


@pytest.mark.parametrize(
    "decision",
    [
        SystemDecision.REVIEW,
        SystemDecision.BLOCK,
        SystemDecision.FALLBACK,
    ],
)
def test_non_allow_decisions_are_rejected(decision):
    with pytest.raises(PaymentAuthorizationError):
        require_payment_authorization(decision=decision)