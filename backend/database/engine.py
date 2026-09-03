from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from backend.core.config import settings


def create_engine_from_settings() -> Engine:
	"""Create the SQLAlchemy engine from application configuration."""

	database_url = settings.database_url
	connect_args: dict[str, object] = {}

	if database_url.startswith("sqlite"):
		connect_args["check_same_thread"] = False

	return create_engine(
		database_url,
		connect_args=connect_args,
		pool_pre_ping=True,
		future=True,
	)


engine = create_engine_from_settings()
