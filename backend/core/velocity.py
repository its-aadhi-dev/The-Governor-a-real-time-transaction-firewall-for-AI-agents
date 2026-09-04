from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class VelocityContext:
	agent_id: str
	window_seconds: int
	transaction_count: int
	window_started_at: datetime


@dataclass(frozen=True)
class VelocityDecision:
	allowed: bool
	reason: str
	transaction_count: int
	limit: int
	window_seconds: int


def window_start(
	*,
	now: datetime,
	window_seconds: int,
) -> datetime:
	return now - timedelta(seconds=window_seconds)