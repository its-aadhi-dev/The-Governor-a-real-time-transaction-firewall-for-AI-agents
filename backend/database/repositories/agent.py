from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.agent import AgentModel


class AgentRepository:
	"""Database access for persistent agent identities."""

	def __init__(self, db: Session):
		self.db = db

	def get(self, agent_id: str) -> Optional[AgentModel]:
		statement = select(AgentModel).where(AgentModel.agent_id == agent_id)
		return self.db.scalar(statement)

	def create(
		self,
		*,
		agent_id: str,
		role: str,
		display_name: Optional[str] = None,
		merchant_id: Optional[str] = None,
	) -> AgentModel:
		agent = AgentModel(
			agent_id=agent_id,
			role=role,
			display_name=display_name,
			merchant_id=merchant_id,
			status="ACTIVE",
			trust_score=Decimal("1.0000"),
		)
		self.db.add(agent)
		self.db.flush()
		return agent

	def get_or_create(
		self,
		*,
		agent_id: str,
		role: str,
		display_name: Optional[str] = None,
		merchant_id: Optional[str] = None,
	) -> AgentModel:
		existing = self.get(agent_id)
		if existing is not None:
			return existing
		return self.create(
			agent_id=agent_id,
			role=role,
			display_name=display_name,
			merchant_id=merchant_id,
		)
