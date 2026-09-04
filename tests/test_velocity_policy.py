from datetime import datetime, timezone

from backend.canon.policies.velocity import VelocityPolicy
from backend.core.velocity import VelocityContext


def make_context(count: int) -> VelocityContext:
	now = datetime.now(timezone.utc)

	return VelocityContext(
		agent_id="buyer-001",
		window_seconds=60,
		transaction_count=count,
		window_started_at=now,
	)


def test_velocity_allows_below_limit():
	policy = VelocityPolicy(
		max_transactions=5,
		window_seconds=60,
	)

	decision = policy.evaluate(
		make_context(4)
	)

	assert decision.allowed is True
	assert decision.transaction_count == 4


def test_velocity_blocks_at_limit():
	policy = VelocityPolicy(
		max_transactions=5,
		window_seconds=60,
	)

	decision = policy.evaluate(
		make_context(5)
	)

	assert decision.allowed is False
	assert decision.transaction_count == 5


def test_velocity_blocks_above_limit():
	policy = VelocityPolicy(
		max_transactions=5,
		window_seconds=60,
	)

	decision = policy.evaluate(
		make_context(6)
	)

	assert decision.allowed is False