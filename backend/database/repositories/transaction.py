from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.lifecycle import validate_transition
from backend.core.constants import VELOCITY_COUNTED_STATUSES
from backend.core.models import SystemDecision, TransactionStatus
from backend.database.models.transaction import TransactionModel


class DuplicateTransactionError(Exception):
	"""Raised when a transaction or idempotency key already exists."""


class TransactionRepository:
	"""Persistence operations for transaction state."""

	def __init__(self, db: Session):
		self.db = db

	def get(self, transaction_id: str) -> Optional[TransactionModel]:
		statement = select(TransactionModel).where(
			TransactionModel.transaction_id == transaction_id
		)
		return self.db.scalar(statement)

	def get_by_idempotency_key(self, idempotency_key: str) -> Optional[TransactionModel]:
		statement = select(TransactionModel).where(
			TransactionModel.idempotency_key == idempotency_key
		)
		return self.db.scalar(statement)

	def create(
		self,
		*,
		transaction_id: str,
		idempotency_key: str,
		negotiation_id: str,
		buyer_agent_id: str,
		merchant_agent_id: str,
		item_id: str,
		requested_price: Decimal,
		currency: str,
	) -> TransactionModel:
		transaction = TransactionModel(
			transaction_id=transaction_id,
			idempotency_key=idempotency_key,
			negotiation_id=negotiation_id,
			buyer_agent_id=buyer_agent_id,
			merchant_agent_id=merchant_agent_id,
			item_id=item_id,
			requested_price=requested_price,
			authorized_price=None,
			currency=currency.upper(),
			status=TransactionStatus.CREATED.value,
			decision=None,
			razorpay_order_id=None,
			fallback_payment_url=None,
			risk_score=Decimal("0.0000"),
			policy_version="canon-v1",
		)
		self.db.add(transaction)
		try:
			self.db.flush()
		except IntegrityError as exc:
			self.db.rollback()
			raise DuplicateTransactionError(
				"Transaction ID or idempotency key already exists."
			) from exc
		return transaction

	def transition(
		self,
		transaction: TransactionModel,
		target: TransactionStatus,
		*,
		decision: Optional[SystemDecision] = None,
	) -> TransactionModel:
		current = TransactionStatus(transaction.status)
		validate_transition(current, target)
		transaction.status = target.value
		if decision is not None:
			transaction.decision = decision.value
		self.db.add(transaction)
		self.db.flush()
		return transaction

	def set_authorized_amount(
		self, transaction: TransactionModel, amount: Decimal
	) -> TransactionModel:
		transaction.authorized_price = amount
		self.db.add(transaction)
		self.db.flush()
		return transaction

	def set_razorpay_order(
		self, transaction: TransactionModel, *, order_id: str
	) -> TransactionModel:
		transaction.razorpay_order_id = order_id
		self.db.add(transaction)
		self.db.flush()
		return transaction

	def set_fallback_url(
		self, transaction: TransactionModel, *, fallback_url: str
	) -> TransactionModel:
		transaction.fallback_payment_url = fallback_url
		self.db.add(transaction)
		self.db.flush()
		return transaction

	def get_spend_snapshot(
		self,
		*,
		buyer_agent_id: str,
		window_minutes: int,
		counted_statuses: Tuple[str, ...],
	) -> Tuple[Decimal, int]:
		if window_minutes <= 0:
			raise ValueError("window_minutes must be greater than zero.")

		cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
		statement = (
			select(
				func.coalesce(func.sum(TransactionModel.authorized_price), Decimal("0")),
				func.count(TransactionModel.transaction_id),
			)
			.where(TransactionModel.buyer_agent_id == buyer_agent_id)
			.where(TransactionModel.created_at >= cutoff)
			.where(TransactionModel.status.in_(counted_statuses))
			.where(TransactionModel.authorized_price.is_not(None))
		)
		amount, count = self.db.execute(statement).one()
		return Decimal(amount or "0"), int(count or 0)

	def count_recent_payment_path_transactions(
		self,
		*,
		buyer_agent_id: str,
		window_start_time: datetime,
	) -> int:
		statement = select(func.count()).select_from(TransactionModel).where(
			TransactionModel.buyer_agent_id == buyer_agent_id,
			TransactionModel.created_at >= window_start_time,
			TransactionModel.status.in_(VELOCITY_COUNTED_STATUSES),
		)

		return int(self.db.scalar(statement) or 0)

	def count_buyer_transactions(
		self,
		*,
		buyer_agent_id: str,
	) -> int:
		statement = select(func.count()).select_from(TransactionModel).where(
			TransactionModel.buyer_agent_id == buyer_agent_id,
			TransactionModel.status.in_(VELOCITY_COUNTED_STATUSES),
		)

		return int(self.db.scalar(statement) or 0)

	def count_buyer_merchant_transactions(
		self,
		*,
		buyer_agent_id: str,
		merchant_id: str,
	) -> int:
		statement = select(func.count()).select_from(TransactionModel).where(
			TransactionModel.buyer_agent_id == buyer_agent_id,
			TransactionModel.merchant_agent_id == merchant_id,
			TransactionModel.status.in_(VELOCITY_COUNTED_STATUSES),
		)

		return int(self.db.scalar(statement) or 0)
