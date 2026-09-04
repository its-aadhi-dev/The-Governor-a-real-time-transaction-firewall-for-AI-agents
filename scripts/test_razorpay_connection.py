from decimal import Decimal
from uuid import uuid4

from backend.payments.factory import create_razorpay_gateway


def main() -> None:
    gateway = create_razorpay_gateway()
    result = gateway.create_order(
        transaction_id=str(uuid4()),
        amount=Decimal("1.00"),
        currency="INR",
    )

    print("Razorpay connection successful.")
    print("Order ID:", result.order_id)
    print("Status:", result.status.value)
    print("Amount:", result.amount)
    print("Currency:", result.currency)


if __name__ == "__main__":
    main()