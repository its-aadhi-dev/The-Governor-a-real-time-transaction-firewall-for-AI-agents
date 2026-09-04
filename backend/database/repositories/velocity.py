from __future__ import annotations

from datetime import datetime

from backend.database.repositories.transaction import TransactionRepository


class VelocityRepository:
	"""
	Read-only projection of transaction history for velocity checks.

	No velocity state is maintained in memory.
	"""

	def __init__(
		self,
		transaction_repository: TransactionRepository,
	) -> None:
		self.transaction_repository = transaction_repository

	def count_payment_path_transactions(
		self,
		*,
		buyer_agent_id: str,
		window_start_time: datetime,
	) -> int:
		return self.transaction_repository.count_recent_payment_path_transactions(
			buyer_agent_id=buyer_agent_id,
			window_start_time=window_start_time,
		)