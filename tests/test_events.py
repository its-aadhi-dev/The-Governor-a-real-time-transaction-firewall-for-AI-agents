from decimal import Decimal
from uuid import uuid4

from backend.database import Base, engine
from backend.database.models.agent import AgentModel
from backend.database.models.catalog import CatalogItemModel
from backend.database.models.merchant import MerchantModel
from backend.database.models.negotiation import NegotiationModel
from backend.database.models.transaction import TransactionModel
from backend.database.repositories.event import EventRepository
from backend.database.session import SessionLocal


def test_event_sequence_is_monotonic():
    Base.metadata.create_all(bind=engine)
    suffix = uuid4().hex
    buyer_id = f"event_buyer_{suffix}"
    merchant_id = f"event_merchant_{suffix}"
    item_id = f"event_item_{suffix}"
    negotiation_id = f"event_neg_{suffix}"
    transaction_id = f"event_txn_{suffix}"

    db = SessionLocal()
    try:
        db.add_all(
            [
                AgentModel(agent_id=buyer_id, role="BUYER", status="ACTIVE"),
                AgentModel(
                    agent_id=merchant_id,
                    role="MERCHANT",
                    status="ACTIVE",
                    merchant_id=merchant_id,
                ),
                MerchantModel(merchant_id=merchant_id, display_name="Event Merchant", active=True),
                CatalogItemModel(
                    item_id=item_id,
                    merchant_id=merchant_id,
                    item_name="Event Item",
                    base_price=Decimal("1000.00"),
                    currency="INR",
                    available_quantity=10,
                    active=True,
                ),
                NegotiationModel(
                    negotiation_id=negotiation_id,
                    buyer_agent_id=buyer_id,
                    merchant_agent_id=merchant_id,
                    item_id=item_id,
                    status="ACCEPTED",
                ),
                TransactionModel(
                    transaction_id=transaction_id,
                    idempotency_key=f"event_idem_{suffix}",
                    negotiation_id=negotiation_id,
                    buyer_agent_id=buyer_id,
                    merchant_agent_id=merchant_id,
                    item_id=item_id,
                    requested_price=Decimal("900.00"),
                    currency="INR",
                    status="CREATED",
                ),
            ]
        )
        db.flush()
        events = EventRepository(db)
        first = events.append(
            transaction_id=transaction_id,
            event_type="TRANSACTION_CREATED",
            actor_id=buyer_id,
            payload={},
        )
        second = events.append(
            transaction_id=transaction_id,
            event_type="GOVERNOR_EVALUATING",
            actor_id="governor",
            payload={},
        )
        db.commit()

        stored = events.list_for_transaction(transaction_id)
        assert first.sequence_number == 1
        assert second.sequence_number == 2
        assert [event.event_type for event in stored] == [
            "TRANSACTION_CREATED",
            "GOVERNOR_EVALUATING",
        ]
    finally:
        db.rollback()
        db.close()