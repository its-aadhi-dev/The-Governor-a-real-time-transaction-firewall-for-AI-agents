from __future__ import annotations

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.governance import GovernanceContext
from backend.core.models import TransactionIntent
from backend.database.repositories.catalog import CatalogRepository
from backend.database.repositories.event import EventRepository
from backend.database.repositories.transaction import DuplicateTransactionError
from backend.database.session import get_db
from backend.services.governor_factory import build_governor_service
from backend.services.transaction_service import TransactionService
from backend.services.governor_factory import build_governor_service

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


@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
):
    transaction = TransactionService(db).transactions.get(transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    return {
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "decision": transaction.decision,
        "requested_price": str(transaction.requested_price),
        "authorized_price": (
            str(transaction.authorized_price)
            if transaction.authorized_price is not None
            else None
        ),
        "currency": transaction.currency,
        "razorpay_order_id": transaction.razorpay_order_id,
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

    try:
        valid = governor_service.payment_service.verify_payment_signature(
            order_id=transaction.razorpay_order_id,
            payment_id=request.razorpay_payment_id,
            signature=request.razorpay_signature,
        )

        if not valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid Razorpay payment signature.",
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

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Payment verification failed: {exc}",
        ) from exc

    return {
        "transaction_id": transaction.transaction_id,
        "status": "PAID",
        "provider": "razorpay",
        "payment_id": request.razorpay_payment_id,
        "order_id": transaction.razorpay_order_id,
        "amount": str(amount),
        "currency": transaction.currency,
    }

    