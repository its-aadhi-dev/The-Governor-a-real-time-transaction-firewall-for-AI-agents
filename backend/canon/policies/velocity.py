from __future__ import annotations

from backend.core.velocity import VelocityContext, VelocityDecision


class VelocityPolicy:
	"""
	Deterministic transaction velocity policy.

	This policy contains no database code.
	"""

	def __init__(
		self,
		*,
		max_transactions: int,
		window_seconds: int,
	) -> None:
		if max_transactions <= 0:
			raise ValueError(
				"max_transactions must be greater than zero."
			)

		if window_seconds <= 0:
			raise ValueError(
				"window_seconds must be greater than zero."
			)

		self.max_transactions = max_transactions
		self.window_seconds = window_seconds

	def evaluate(
		self,
		context: VelocityContext,
	) -> VelocityDecision:
		if context.transaction_count >= self.max_transactions:
			return VelocityDecision(
				allowed=False,
				reason=(
					"Transaction velocity limit exceeded "
					"for the current payment window."
				),
				transaction_count=context.transaction_count,
				limit=self.max_transactions,
				window_seconds=self.window_seconds,
			)

		return VelocityDecision(
			allowed=True,
			reason="Transaction velocity is within policy.",
			transaction_count=context.transaction_count,
			limit=self.max_transactions,
			window_seconds=self.window_seconds,
		)