from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from backend.core.events import (
    GOVERNOR_ALLOW,
    GOVERNOR_BLOCK,
    GOVERNOR_EVALUATING,
    GOVERNOR_FALLBACK,
    GOVERNOR_REVIEW,
    PAYMENT_FAILED,
    PAYMENT_PAID,
    PAYMENT_PENDING,
)
from backend.core.models import SystemDecision, TransactionStatus
from backend.database.repositories.event import EventRepository
from backend.database.repositories.transaction import TransactionRepository


class TransactionLifecycleService:
    """Perform controlled transaction transitions and record events."""

    def __init__(self, db: Session):
        self.db = db
        self.transactions = TransactionRepository(db)
        self.events = EventRepository(db)

    def start_governance(self, transaction_id: str):
        transaction = self.transactions.transition(
            self._get(transaction_id), TransactionStatus.GOVERNANCE_PENDING
        )
        self.events.append(
            transaction_id=transaction_id,
            event_type=GOVERNOR_EVALUATING,
            actor_id="governor",
            payload={},
        )
        return transaction

    def apply_governor_decision(
        self,
        transaction_id: str,
        decision: SystemDecision,
        *,
        risk_score: Optional[Decimal] = None,
    ):
        transaction = self._get(transaction_id)
        mapping = {
            SystemDecision.ALLOW: (TransactionStatus.APPROVED, GOVERNOR_ALLOW),
            SystemDecision.REVIEW: (TransactionStatus.REVIEW, GOVERNOR_REVIEW),
            SystemDecision.BLOCK: (TransactionStatus.BLOCKED, GOVERNOR_BLOCK),
            SystemDecision.FALLBACK: (TransactionStatus.FALLBACK, GOVERNOR_FALLBACK),
        }
        target_status, event_type = mapping[decision]
        transaction = self.transactions.transition(
            transaction, target_status, decision=decision
        )
        if risk_score is not None:
            transaction.risk_score = risk_score
        self.events.append(
            transaction_id=transaction_id,
            event_type=event_type,
            actor_id="governor",
            payload={
                "decision": decision.value,
                "risk_score": str(risk_score) if risk_score is not None else None,
            },
        )
        return transaction

    def mark_payment_pending(self, transaction_id: str):
        transaction = self.transactions.transition(
            self._get(transaction_id), TransactionStatus.PAYMENT_PENDING
        )
        self.events.append(
            transaction_id=transaction_id,
            event_type=PAYMENT_PENDING,
            actor_id="governor",
            payload={},
        )
        return transaction

    def mark_paid(
        self,
        transaction_id: str,
        *,
        amount: Decimal,
        provider_reference: Optional[str] = None,
    ):
        transaction = self._get(transaction_id)
        transaction.authorized_price = amount
        transaction = self.transactions.transition(transaction, TransactionStatus.PAID)
        self.events.append(
            transaction_id=transaction_id,
            event_type=PAYMENT_PAID,
            actor_id="razorpay",
            payload={"amount": str(amount), "provider_reference": provider_reference},
        )
        return transaction

    def mark_failed(self, transaction_id: str, *, reason: str):
        transaction = self.transactions.transition(
            self._get(transaction_id), TransactionStatus.FAILED
        )
        self.events.append(
            transaction_id=transaction_id,
            event_type=PAYMENT_FAILED,
            actor_id="razorpay",
            payload={"reason": reason},
        )
        return transaction

    def _get(self, transaction_id: str):
        transaction = self.transactions.get(transaction_id)
        if transaction is None:
            raise ValueError(f"Transaction '{transaction_id}' does not exist.")
        return transaction