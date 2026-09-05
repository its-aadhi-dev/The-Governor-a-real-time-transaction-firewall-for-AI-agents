from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.governance import GovernanceContext
from backend.core.models import (
    NegotiationStatus,
    TransactionIntent,
)
from backend.database.repositories.agent import AgentRepository
from backend.database.repositories.catalog import CatalogRepository
from backend.database.repositories.merchant import MerchantRepository
from backend.database.repositories.negotiation import NegotiationRepository
from backend.database.session import get_db
from backend.marketplace.buyer import BuyerAgent
from backend.marketplace.live_session import LiveNegotiationSession
from backend.marketplace.merchant import MerchantAgent
from backend.services.governor_factory import build_governor_service
from backend.services.transaction_service import TransactionService


router = APIRouter(prefix="/voice", tags=["Voice"])


class VoiceCommerceRequest(BaseModel):
    merchant_id: str | None = None
    item_id: str | None = None
    maximum_price: Decimal = Field(gt=0)
    currency: str = "INR"


@router.get("/market")
def get_voice_market(
    db: Session = Depends(get_db),
):
    merchants = MerchantRepository(db).list_active()
    catalog = CatalogRepository(db)

    result = []

    for merchant in merchants:
        items = catalog.list_for_merchant(merchant.merchant_id)

        result.append(
            {
                "merchant_id": merchant.merchant_id,
                "display_name": merchant.display_name,
                "items": [
                    {
                        "item_id": item.item_id,
                        "item_name": item.item_name,
                        "base_price": str(item.base_price),
                        "currency": item.currency,
                        "available_quantity": item.available_quantity,
                    }
                    for item in items
                    if item.active and item.available_quantity > 0
                ],
            }
        )

    return {
        "merchants": result,
    }


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

    if item is None:
        if not request.merchant_id:
            raise HTTPException(
                status_code=400,
                detail="merchant_id or item_id is required.",
            )

        items = catalog.list_for_merchant(request.merchant_id)

        items = [
            candidate
            for candidate in items
            if candidate.active and candidate.available_quantity > 0
        ]

        if not items:
            raise HTTPException(
                status_code=404,
                detail="Merchant has no available catalog items.",
            )

        item = items[0]

    if not item.active:
        raise HTTPException(
            status_code=409,
            detail="Catalog item is inactive.",
        )

    if item.available_quantity <= 0:
        raise HTTPException(
            status_code=409,
            detail="Catalog item is unavailable.",
        )

    merchant_id = item.merchant_id

    merchant = MerchantRepository(db).get(merchant_id)

    if merchant is None or not merchant.active:
        raise HTTPException(
            status_code=404,
            detail="Merchant not found or inactive.",
        )

    # Stable voice buyer identity.
    #
    # Keeping this persistent means velocity and reputation
    # can observe repeated voice transactions.
    buyer_agent_id = "voice_buyer_01"

    buyer = BuyerAgent(buyer_agent_id)
    merchant_agent = MerchantAgent(merchant_id)

    AgentRepository(db).get_or_create(
        agent_id=buyer_agent_id,
        role="BUYER",
        display_name="Voice Buyer",
    )

    merchant_agent_id = f"merchant_agent_{merchant_id}"

    AgentRepository(db).get_or_create(
        agent_id=merchant_agent_id,
        role="MERCHANT",
        display_name=merchant.display_name,
        merchant_id=merchant_id,
    )

    transaction_id = f"txn_{uuid4().hex}"
    negotiation_id = f"neg_{uuid4().hex}"

    buyer_request = buyer.create_request(
        merchant_id=merchant_id,
        item_id=item.item_id,
        maximum_price=request.maximum_price,
    )

    negotiation_repository = NegotiationRepository(db)

    negotiation = negotiation_repository.create(
        negotiation_id=negotiation_id,
        buyer_agent_id=buyer_agent_id,
        merchant_agent_id=merchant_agent_id,
        item_id=item.item_id,
    )

    floor_discount = Decimal(str(settings.max_discount_percent)) / Decimal("100")
    session_floor_price = (
        Decimal(item.base_price) * (Decimal("1") - floor_discount)
    ).quantize(Decimal("0.01"))

    session = LiveNegotiationSession(
        buyer=buyer,
        merchant=merchant_agent,
        merchant_floor_price=session_floor_price,
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
        negotiation.status = NegotiationStatus.REJECTED.value
        db.flush()
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    # Persist every negotiation turn.
    for turn in result.turns:
        negotiation_repository.add_message(
            message_id=f"msg_{uuid4().hex}",
            negotiation_id=negotiation_id,
            agent_id=(
                buyer_agent_id
                if turn.actor == "buyer"
                else merchant_agent_id
            ),
            message_type=turn.turn_type,
            message=f"{turn.turn_type} at INR {turn.price}",
            sequence_number=turn.round_number,
            proposed_price=turn.price,
            currency=result.deal.currency,
        )

    negotiation.status = NegotiationStatus.ACCEPTED.value
    negotiation.proposal_count = len(result.turns)

    db.flush()

    # The negotiation is now complete. Convert the accepted
    # deal into the security-boundary TransactionIntent.
    intent = TransactionIntent(
        transaction_id=result.deal.transaction_id,
        negotiation_id=result.deal.negotiation_id,
        buyer_agent_id=result.deal.buyer_agent_id,
        merchant_agent_id=merchant_agent_id,
        item=result.deal.item,
        requested_price=result.deal.agreed_price,
        currency=result.deal.currency,
        idempotency_key=f"voice-{result.deal.transaction_id}",
    )

    transaction_service = TransactionService(db)

    try:
        transaction = transaction_service.create_transaction(intent)

        governance_service = build_governor_service(db)

        governance_service.lifecycle_service.start_governance(
            transaction.transaction_id
        )

        evaluation = governance_service.evaluate_transaction(
            context=GovernanceContext(
                transaction_id=transaction.transaction_id,
                buyer_agent_id=buyer_agent_id,
                merchant_id=merchant_agent_id,
                catalog_item_id=item.item_id,
                catalog_price=Decimal(item.base_price),
                negotiated_price=Decimal(result.deal.agreed_price),
                merchant_floor_price=Decimal(item.base_price),
                historical_min_price=None,
                historical_max_price=None,
            )
        )

        db.commit()

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "transaction_id": transaction.transaction_id,
        "negotiation_id": result.deal.negotiation_id,
        "buyer_agent_id": buyer_agent_id,
        "merchant_id": merchant_id,
        "item": result.deal.item,
        "agreed_price": str(result.deal.agreed_price),
        "currency": result.deal.currency,
        "governor": {
            "decision": evaluation.decision.decision.value,
            "reason": evaluation.decision.reason,
            "risk_score": str(evaluation.risk.score),
            "risk_level": evaluation.risk.level.value,
        },
        "turns": [
            {
                "actor": turn.actor,
                "agent_id": (
                    buyer_agent_id
                    if turn.actor == "buyer"
                    else merchant_agent_id
                ),
                "turn_type": turn.turn_type,
                "price": str(turn.price),
                "round_number": turn.round_number,
            }
            for turn in result.turns
        ],
    }
