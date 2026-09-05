import hashlib
import hmac

from backend.payments.razorpay import RazorpayAdapter


class FakeClient:
    pass


def make_signature(
    *,
    secret: str,
    order_id: str,
    payment_id: str,
) -> str:
    payload = f"{order_id}|{payment_id}".encode("utf-8")

    return hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()


def test_valid_razorpay_signature_verifies():
    secret = "test_secret"
    order_id = "order_test_123"
    payment_id = "pay_test_456"

    adapter = RazorpayAdapter(
        key_id="rzp_test_key",
        key_secret=secret,
        client=FakeClient(),
    )

    signature = make_signature(
        secret=secret,
        order_id=order_id,
        payment_id=payment_id,
    )

    assert adapter.verify_payment_signature(
        order_id=order_id,
        payment_id=payment_id,
        signature=signature,
    )


def test_invalid_razorpay_signature_is_rejected():
    adapter = RazorpayAdapter(
        key_id="rzp_test_key",
        key_secret="test_secret",
        client=FakeClient(),
    )

    assert not adapter.verify_payment_signature(
        order_id="order_test_123",
        payment_id="pay_test_456",
        signature="invalid_signature",
    )


def test_signature_cannot_be_reused_with_different_order():
    secret = "test_secret"

    adapter = RazorpayAdapter(
        key_id="rzp_test_key",
        key_secret=secret,
        client=FakeClient(),
    )

    signature = make_signature(
        secret=secret,
        order_id="order_original",
        payment_id="pay_test_456",
    )

    assert not adapter.verify_payment_signature(
        order_id="order_attacker",
        payment_id="pay_test_456",
        signature=signature,
    )
    