from __future__ import annotations

from datetime import datetime, timezone

from backend.canon.policies.velocity import VelocityPolicy
from backend.core.velocity import (
	VelocityContext,
	VelocityDecision,
	window_start,
)
from backend.database.repositories.velocity import VelocityRepository


class VelocityService:
	"""
	Loads persistent transaction history and evaluates velocity.
	"""

	def __init__(
		self,
		*,
		velocity_repository: VelocityRepository,
		max_transactions: int = 5,
		window_seconds: int = 60,
	) -> None:
		self.velocity_repository = velocity_repository
		self.max_transactions = max_transactions
		self.window_seconds = window_seconds

	def evaluate(
		self,
		*,
		buyer_agent_id: str,
		now: datetime | None = None,
	) -> VelocityDecision:
		current_time = now or datetime.now(timezone.utc)

		start = window_start(
			now=current_time,
			window_seconds=self.window_seconds,
		)

		count = self.velocity_repository.count_payment_path_transactions(
			buyer_agent_id=buyer_agent_id,
			window_start_time=start,
		)

		context = VelocityContext(
			agent_id=buyer_agent_id,
			window_seconds=self.window_seconds,
			transaction_count=count,
			window_started_at=start,
		)

		policy = VelocityPolicy(
			max_transactions=self.max_transactions,
			window_seconds=self.window_seconds,
		)

		return policy.evaluate(context)