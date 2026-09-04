from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.repositories.catalog import CatalogRepository
from backend.database.repositories.merchant import MerchantRepository
from backend.marketplace.buyer import BuyerAgent
from backend.marketplace.merchant import MerchantAgent
from backend.marketplace.live_session import LiveNegotiationSession
from backend.database.session import get_db


router = APIRouter(prefix="/voice", tags=["Voice"])


class VoiceCommerceRequest(BaseModel):
    merchant_id: str | None = None
    item_id: str | None = None
    maximum_price: Decimal = Field(gt=0)
    currency: str = "INR"


@router.post("/negotiate")
def negotiate_from_voice(
    request: VoiceCommerceRequest,
    db: Session = Depends(get_db),
):
    if request.currency.upper() != "INR":
        raise HTTPException(
            status_code=400,
            detail="Only INR voice commerce is currently supported.",
        )

    catalog = CatalogRepository(db)

    # Resolve merchant/item explicitly when supplied.
    item = None

    if request.item_id:
        item = catalog.get(request.item_id)

        if item is None:
            raise HTTPException(
                status_code=404,
                detail="Catalog item not found.",
            )

        if request.merchant_id and item.merchant_id != request.merchant_id:
            raise HTTPException(
                status_code=400,
                detail="Catalog item does not belong to the requested merchant.",
            )

    # For the first voice flow, use the first active catalog item
    # when the UI has not selected an item yet.
    if item is None:
        if not request.merchant_id:
            raise HTTPException(
                status_code=400,
                detail="merchant_id or item_id is required.",
            )

        items = catalog.list_for_merchant(request.merchant_id)

        if not items:
            raise HTTPException(
                status_code=404,
                detail="Merchant has no active catalog items.",
            )

        item = items[0]

    if item.available_quantity <= 0:
        raise HTTPException(
            status_code=409,
            detail="Catalog item is unavailable.",
        )

    buyer_agent_id = f"voice_buyer_{uuid4().hex[:12]}"
    transaction_id = f"txn_{uuid4().hex}"
    negotiation_id = f"neg_{uuid4().hex}"

    buyer = BuyerAgent(buyer_agent_id)
    merchant = MerchantAgent(item.merchant_id)

    buyer_request = buyer.create_request(
        merchant_id=item.merchant_id,
        item_id=item.item_id,
        maximum_price=request.maximum_price,
    )

    session = LiveNegotiationSession(
        buyer=buyer,
        merchant=merchant,
        merchant_floor_price=Decimal(item.base_price),
        item={
            "item_id": item.item_id,
            "item_name": item.item_name,
            "base_price": Decimal(item.base_price),
            "currency": item.currency,
        },
        negotiation_id=negotiation_id,
        transaction_id=transaction_id,
        maximum_price=buyer_request.maximum_price,
        asking_price=Decimal(item.base_price),
    )

    try:
        result = session.run()
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "transaction_id": result.transaction_id,
        "negotiation_id": result.deal.negotiation_id,
        "merchant_id": result.deal.merchant_agent_id,
        "buyer_agent_id": result.deal.buyer_agent_id,
        "item": result.deal.item,
        "agreed_price": str(result.deal.agreed_price),
        "currency": result.deal.currency,
        "turns": [
            {
                "actor": turn.actor,
                "agent_id": turn.agent_id,
                "turn_type": turn.turn_type,
                "price": str(turn.price),
                "round_number": turn.round_number,
            }
            for turn in result.turns
        ],
    }
