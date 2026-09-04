from backend.core.models import TransactionStatus


VELOCITY_COUNTED_STATUSES = frozenset(
	{
		TransactionStatus.PAYMENT_PENDING,
		TransactionStatus.PAID,
	}
)
