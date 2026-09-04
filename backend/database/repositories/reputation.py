from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.reputation import AgentReputationModel


class ReputationRepository:
    """Persistence access for neutral, historical agent reputation state."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_agent(self, agent_id: str) -> Optional[AgentReputationModel]:
        statement = select(AgentReputationModel).where(
            AgentReputationModel.agent_id == agent_id
        )
        return self.session.scalar(statement)

    def create(
        self,
        *,
        agent_id: str,
        reputation_score: Decimal = Decimal("1.0000"),
    ) -> AgentReputationModel:
        record = AgentReputationModel(
            agent_id=agent_id,
            trust_score=reputation_score,
            successful_transactions=0,
            review_transactions=0,
            blocked_transactions=0,
            policy_violations=0,
            last_violation_at=None,
            last_transaction_at=None,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def get_or_create(self, *, agent_id: str) -> AgentReputationModel:
        existing = self.get_by_agent(agent_id)
        return existing if existing is not None else self.create(agent_id=agent_id)

    def adjust_score(
        self,
        *,
        agent_id: str,
        delta: Decimal,
    ) -> AgentReputationModel:
        record = self.get_or_create(agent_id=agent_id)
        record.trust_score = max(
            Decimal("0"),
            min(Decimal("1"), record.trust_score + delta),
        )
        record.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return record

    def record_success(
        self,
        *,
        agent_id: str,
        score_delta: Decimal = Decimal("0.02"),
    ) -> AgentReputationModel:
        record = self.adjust_score(
            agent_id=agent_id,
            delta=score_delta,
        )
        record.successful_transactions += 1
        record.last_transaction_at = datetime.now(timezone.utc)
        self.session.flush()
        return record

    def record_suspicious_block(
        self,
        *,
        agent_id: str,
        score_delta: Decimal = Decimal("-0.10"),
    ) -> AgentReputationModel:
        record = self.adjust_score(
            agent_id=agent_id,
            delta=score_delta,
        )
        record.blocked_transactions += 1
        record.last_transaction_at = datetime.now(timezone.utc)
        self.session.flush()
        return record

    def record_block(self, *, agent_id: str) -> AgentReputationModel:
        return self.record_suspicious_block(agent_id=agent_id)