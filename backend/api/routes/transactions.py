from __future__ import annotations

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.events import (
    PAYMENT_VERIFICATION_FAILED,
    PAYMENT_VERIFIED,
)
from backend.core.governance import GovernanceContext
from backend.core.models import TransactionIntent
from backend.database.repositories.catalog import CatalogRepository
from backend.database.repositories.event import EventRepository
from backend.database.repositories.ledger import LedgerRepository
from backend.database.repositories.transaction import DuplicateTransactionError
from backend.database.session import get_db
from backend.services.governor_factory import build_governor_service
from backend.services.transaction_service import TransactionService
from backend.database.repositories.negotiation import (
    NegotiationRepository,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])

class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str

class CreateTransactionRequest(BaseModel):
    intent: TransactionIntent


@router.post("")
def create_transaction(
    request: CreateTransactionRequest,
    db: Session = Depends(get_db),
):
    try:
        transaction = TransactionService(db).create_transaction(request.intent)
        db.commit()
    except DuplicateTransactionError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "requested_price": str(transaction.requested_price),
        "currency": transaction.currency,
    }


@router.get("/{transaction_id}/events")
def get_transaction_events(
    transaction_id: str,
    db: Session = Depends(get_db),
):
    if TransactionService(db).transactions.get(transaction_id) is None:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    events = EventRepository(db).list_for_transaction(transaction_id)
    return {
        "transaction_id": transaction_id,
        "events": [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "actor_id": event.actor_id,
                "sequence_number": event.sequence_number,
                "payload": event.payload,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ],
    }


@router.get("/{transaction_id}/audit")
def get_transaction_audit(
    transaction_id: str,
    db: Session = Depends(get_db),
):
    transaction_service = TransactionService(db)

    transaction = transaction_service.transactions.get(
        transaction_id
    )

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found.",
        )

    events = EventRepository(db).list_for_transaction(
        transaction_id
    )

    negotiation_repository = NegotiationRepository(db)

    negotiation = negotiation_repository.get(
        transaction.negotiation_id
    )

    negotiation_messages = []

    if negotiation is not None:
        negotiation_messages = (
            negotiation_repository.list_messages(
                negotiation.negotiation_id
            )
        )

    ledger_repository = LedgerRepository(db)

    ledger_blocks = ledger_repository.list_for_transaction(
        transaction_id
    )

    ledger_service = build_governor_service(
        db
    ).ledger_service

    return {
        "transaction_id": transaction_id,

        "transaction": {
            "status": transaction.status,
            "decision": transaction.decision,
            "requested_price": str(
                transaction.requested_price
            ),
            "authorized_price": (
                str(transaction.authorized_price)
                if transaction.authorized_price
                is not None
                else None
            ),
            "currency": transaction.currency,
            "razorpay_order_id":
                transaction.razorpay_order_id,
        },

        "negotiation": {
            "negotiation_id": (
                negotiation.negotiation_id
                if negotiation is not None
                else transaction.negotiation_id
            ),
            "status": (
                negotiation.status
                if negotiation is not None
                else None
            ),
            "proposal_count": (
                negotiation.proposal_count
                if negotiation is not None
                else 0
            ),
            "messages": [
                {
                    "message_id": message.message_id,
                    "agent_id": message.agent_id,
                    "message_type": message.message_type,
                    "message": message.message,
                    "proposed_price": (
                        str(message.proposed_price)
                        if message.proposed_price
                        is not None
                        else None
                    ),
                    "currency": message.currency,
                    "sequence_number":
                        message.sequence_number,
                }
                for message in negotiation_messages
            ],
        },

        "events": [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "actor_id": event.actor_id,
                "sequence_number":
                    event.sequence_number,
                "payload": event.payload,
                "created_at":
                    event.created_at.isoformat(),
            }
            for event in events
        ],

        "ledger": [
            {
                "sequence_number":
                    block.sequence_number,
                "event_type":
                    block.event_type,
                "block_hash":
                    block.block_hash,
                "previous_hash":
                    block.previous_hash,
                "signature":
                    block.signature,
                "signer_public_key":
                    block.signer_public_key,
                "created_at":
                    block.created_at.isoformat(),
                "valid":
                    ledger_service.verify_block(
                        block
                    ),
            }
            for block in ledger_blocks
        ],

        "ledger_integrity":
            ledger_service.verify_chain(),
    }

@router.post("/{transaction_id}/checkout")
def checkout_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
):
    transaction_service = TransactionService(db)
    transaction = transaction_service.transactions.get(transaction_id)

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found.",
        )

    catalog = CatalogRepository(db)
    item = catalog.get(transaction.item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Catalog item not found.",
        )

    governor_service = build_governor_service(db)

    context = GovernanceContext(
        transaction_id=transaction.transaction_id,
        buyer_agent_id=transaction.buyer_agent_id,
        merchant_id=transaction.merchant_agent_id,
        catalog_item_id=transaction.item_id,
        catalog_price=item.base_price,
        negotiated_price=transaction.requested_price,
        merchant_floor_price=item.base_price,
        historical_min_price=None,
        historical_max_price=None,
    )

    try:
        payment_result = governor_service.execute_payment(
            context=context,
        )

        db.commit()

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    return {
        "transaction_id": transaction.transaction_id,
        "status": payment_result.status.value,
        "success": payment_result.success,
        "provider": payment_result.provider,
        "amount": str(payment_result.amount),
        "currency": payment_result.currency,
        "order_id": payment_result.order_id,
        "provider_reference": payment_result.provider_reference,
        "key_id": settings.razorpay_key_id.get_secret_value(),
    }

@router.post("/{transaction_id}/verify-payment")
def verify_payment(
    transaction_id: str,
    request: VerifyPaymentRequest,
    db: Session = Depends(get_db),
):
    transaction_service = TransactionService(db)

    transaction = transaction_service.transactions.get(
        transaction_id
    )

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found.",
        )

    if transaction.razorpay_order_id is None:
        raise HTTPException(
            status_code=409,
            detail="Transaction does not have a Razorpay order.",
        )

    if transaction.razorpay_order_id != request.razorpay_order_id:
        raise HTTPException(
            status_code=400,
            detail="Razorpay order does not match the transaction.",
        )

    if transaction.status != "PAYMENT_PENDING":
        raise HTTPException(
            status_code=409,
            detail=(
                "Payment verification requires a "
                "PAYMENT_PENDING transaction."
            ),
        )

    governor_service = build_governor_service(db)
    events = EventRepository(db)

    valid = governor_service.payment_service.verify_payment_signature(
        order_id=transaction.razorpay_order_id,
        payment_id=request.razorpay_payment_id,
        signature=request.razorpay_signature,
    )

    if not valid:
        events.append(
            transaction_id=transaction.transaction_id,
            event_type=PAYMENT_VERIFICATION_FAILED,
            actor_id="governor",
            payload={
                "order_id": transaction.razorpay_order_id,
                "payment_id": request.razorpay_payment_id,
                "reason": "Invalid Razorpay payment signature.",
            },
        )

        governor_service.ledger_service.append(
            event_type=PAYMENT_VERIFICATION_FAILED,
            transaction_id=transaction.transaction_id,
            payload={
                "order_id": transaction.razorpay_order_id,
                "payment_id": request.razorpay_payment_id,
                "reason": "Invalid Razorpay payment signature.",
            },
        )

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay payment signature.",
        )

    events.append(
        transaction_id=transaction.transaction_id,
        event_type=PAYMENT_VERIFIED,
        actor_id="governor",
        payload={
            "order_id": transaction.razorpay_order_id,
            "payment_id": request.razorpay_payment_id,
        },
    )

    governor_service.ledger_service.append(
        event_type=PAYMENT_VERIFIED,
        transaction_id=transaction.transaction_id,
        payload={
            "order_id": transaction.razorpay_order_id,
            "payment_id": request.razorpay_payment_id,
        },
    )

    amount = (
        transaction.authorized_price
        or transaction.requested_price
    )

    governor_service.lifecycle_service.mark_paid(
        transaction.transaction_id,
        amount=amount,
        provider_reference=request.razorpay_payment_id,
    )

    governor_service.ledger_service.append(
        event_type="PAYMENT_PAID",
        transaction_id=transaction.transaction_id,
        payload={
            "order_id": transaction.razorpay_order_id,
            "payment_id": request.razorpay_payment_id,
            "amount": str(amount),
            "currency": transaction.currency,
        },
    )

    db.commit()

    return {
        "transaction_id": transaction.transaction_id,
        "status": "PAID",
        "provider": "razorpay",
        "payment_id": request.razorpay_payment_id,
        "order_id": transaction.razorpay_order_id,
        "amount": str(amount),
        "currency": transaction.currency,
    }


