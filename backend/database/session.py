from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from backend.database.engine import engine


SessionLocal = sessionmaker(
	bind=engine,
	class_=Session,
	autoflush=False,
	autocommit=False,
	expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
	"""Provide one database session per request and close it afterward."""

	db = SessionLocal()

	try:
		yield db
	finally:
		db.close()
