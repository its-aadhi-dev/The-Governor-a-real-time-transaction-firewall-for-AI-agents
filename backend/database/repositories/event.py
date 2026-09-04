from __future__ import annotations

from typing import List, Optional
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database.models.event import TransactionEventModel


class EventRepository:
    """Append-only persistence access for transaction events."""

    def __init__(self, db: Session):
        self.db = db

    def append(
        self,
        *,
        transaction_id: str,
        event_type: str,
        actor_id: Optional[str],
        payload: dict,
    ) -> TransactionEventModel:
        last_sequence = self.db.scalar(
            select(func.max(TransactionEventModel.sequence_number)).where(
                TransactionEventModel.transaction_id == transaction_id
            )
        )
        event = TransactionEventModel(
            event_id=f"evt_{uuid4().hex}",
            transaction_id=transaction_id,
            event_type=event_type,
            actor_id=actor_id,
            sequence_number=int(last_sequence or 0) + 1,
            payload=payload,
        )
        self.db.add(event)
        self.db.flush()

        pending_events = self.db.info.setdefault(
            "governor_pending_events",
            [],
        )
        pending_events.append(event)

        return event

    def list_for_transaction(self, transaction_id: str) -> List[TransactionEventModel]:
        statement = (
            select(TransactionEventModel)
            .where(TransactionEventModel.transaction_id == transaction_id)
            .order_by(TransactionEventModel.sequence_number.asc())
        )
        return list(self.db.scalars(statement).all())