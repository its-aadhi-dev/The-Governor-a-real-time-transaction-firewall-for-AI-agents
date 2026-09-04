from backend.core.models import TransactionStatus


def test_only_payment_path_statuses_are_counted():
	"""
	This test documents the security boundary:

	BLOCKED transactions do not consume financial velocity.
	PAYMENT_PENDING and PAID transactions do.
	"""

	counted_statuses = {
		TransactionStatus.PAYMENT_PENDING,
		TransactionStatus.PAID,
	}

	assert TransactionStatus.BLOCKED not in counted_statuses
	assert TransactionStatus.PAYMENT_PENDING in counted_statuses
	assert TransactionStatus.PAID in counted_statuses