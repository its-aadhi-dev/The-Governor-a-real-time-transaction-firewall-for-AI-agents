from __future__ import annotations

from backend.core.models import TransactionStatus


class InvalidTransactionTransition(Exception):
	"""Raised when a transaction attempts an illegal state transition."""


ALLOWED_TRANSITIONS: dict[
	TransactionStatus,
	frozenset[TransactionStatus],
] = {
	TransactionStatus.CREATED: frozenset(
		{TransactionStatus.GOVERNANCE_PENDING, TransactionStatus.EXPIRED}
	),
	TransactionStatus.GOVERNANCE_PENDING: frozenset(
		{
			TransactionStatus.APPROVED,
			TransactionStatus.REVIEW,
			TransactionStatus.BLOCKED,
			TransactionStatus.FALLBACK,
			TransactionStatus.EXPIRED,
		}
	),
	TransactionStatus.APPROVED: frozenset(
		{TransactionStatus.PAYMENT_PENDING, TransactionStatus.FAILED}
	),
	TransactionStatus.REVIEW: frozenset(
		{
			TransactionStatus.APPROVED,
			TransactionStatus.BLOCKED,
			TransactionStatus.FALLBACK,
			TransactionStatus.EXPIRED,
		}
	),
	TransactionStatus.FALLBACK: frozenset(
		{
			TransactionStatus.PAYMENT_PENDING,
			TransactionStatus.FAILED,
			TransactionStatus.EXPIRED,
		}
	),
	TransactionStatus.PAYMENT_PENDING: frozenset(
		{
			TransactionStatus.PAID,
			TransactionStatus.FAILED,
			TransactionStatus.EXPIRED,
		}
	),
	TransactionStatus.PAID: frozenset(),
	TransactionStatus.BLOCKED: frozenset(),
	TransactionStatus.FAILED: frozenset(),
	TransactionStatus.EXPIRED: frozenset(),
}


def validate_transition(
	current: TransactionStatus,
	target: TransactionStatus,
) -> None:
	"""Validate one transaction state transition."""

	if current == target:
		raise InvalidTransactionTransition(
			f"Transaction is already in state {current.value}."
		)

	if target not in ALLOWED_TRANSITIONS.get(current, frozenset()):
		raise InvalidTransactionTransition(
			f"Invalid transaction transition: {current.value} -> {target.value}"
		)
