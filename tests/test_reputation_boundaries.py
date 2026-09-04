from backend.core.constants import VELOCITY_COUNTED_STATUSES
from backend.core.models import TransactionStatus


def test_blocked_transaction_is_not_payment_path_state():
    assert TransactionStatus.BLOCKED not in VELOCITY_COUNTED_STATUSES


def test_failed_payment_is_not_velocity_counted():
    assert TransactionStatus.FAILED not in VELOCITY_COUNTED_STATUSES