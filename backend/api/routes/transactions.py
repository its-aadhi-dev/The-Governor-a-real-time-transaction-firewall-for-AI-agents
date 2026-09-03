from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.models import TransactionIntent
from backend.database.repositories.transaction import DuplicateTransactionError
from backend.database.session import get_db
from backend.services.transaction_service import TransactionService


router = APIRouter(prefix="/transactions", tags=["Transactions"])


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