from __future__ import annotations

from backend.core.models import SystemDecision


class PaymentAuthorizationError(RuntimeError):
    pass


def require_payment_authorization(*, decision: SystemDecision) -> None:
    if decision != SystemDecision.ALLOW:
        raise PaymentAuthorizationError(
            "Payment can only be created for an ALLOW decision."
        )