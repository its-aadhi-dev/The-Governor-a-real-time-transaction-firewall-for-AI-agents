from __future__ import annotations

from backend.core.config import settings
from backend.payments.razorpay import RazorpayAdapter


def create_razorpay_gateway() -> RazorpayAdapter:
    return RazorpayAdapter(
        key_id=settings.razorpay_key_id,
        key_secret=settings.razorpay_key_secret.get_secret_value(),
    )