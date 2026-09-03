from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import uuid4

from backend.core.models import NegotiationProposal, NegotiationStatus, ProposalType
from backend.database.repositories.catalog import CatalogRepository
from backend.database.repositories.negotiation import NegotiationRepository
from backend.marketplace.negotiation import NegotiationEngine


class NegotiationService:
    """Coordinate negotiation protocol decisions and persisted messages."""

    def __init__(self, negotiation_repository: NegotiationRepository):
        self.negotiation_repository = negotiation_repository
        self.catalog = CatalogRepository(negotiation_repository.db)

    def start(
        self,
        *,
        buyer_agent_id: str,
        merchant_id: str,
        catalog_item_id: str,
        asking_price: Decimal,
        currency: str = "INR",
    ):
        if asking_price <= Decimal("0"):
            raise ValueError("Asking price must be greater than zero.")
        if currency.upper() != "INR":
            raise ValueError("Only INR negotiations are currently supported.")

        item = self.catalog.get(catalog_item_id)
        if item is None:
            raise ValueError(f"Catalog item '{catalog_item_id}' does not exist.")
        if item.merchant_id != merchant_id:
            raise ValueError("Catalog item does not belong to the requested merchant.")

        return self.negotiation_repository.create(
            negotiation_id=f"neg_{uuid4().hex}",
            buyer_agent_id=buyer_agent_id,
            merchant_agent_id=merchant_id,
            item_id=catalog_item_id,
        )

    def create_offer(
        self,
        *,
        negotiation,
        price: Decimal,
        transaction_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> NegotiationProposal:
        engine = NegotiationEngine(
            merchant_floor_price=self._floor_price(negotiation.item_id),
        )
        round_number = negotiation.proposal_count + 1
        result = engine.validate_offer(
            price=price,
            round_number=round_number,
            negotiation_id=negotiation.negotiation_id,
            transaction_id=transaction_id or f"txn_{negotiation.negotiation_id}",
            agent_id=agent_id or negotiation.buyer_agent_id,
        )
        if result.proposal is None:
            raise ValueError(result.message or "Offer rejected.")
        self._persist_proposal(negotiation, result.proposal)
        return result.proposal

    def accept(
        self,
        *,
        negotiation,
        price: Decimal,
        transaction_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> NegotiationProposal:
        engine = NegotiationEngine(
            merchant_floor_price=self._floor_price(negotiation.item_id),
        )
        proposal = engine.accept(
            price=price,
            round_number=max(negotiation.proposal_count, 1),
            negotiation_id=negotiation.negotiation_id,
            transaction_id=transaction_id or f"txn_{negotiation.negotiation_id}",
            agent_id=agent_id or negotiation.buyer_agent_id,
        )
        self._persist_proposal(negotiation, proposal)
        negotiation.status = NegotiationStatus.ACCEPTED.value
        self.negotiation_repository.db.flush()
        return proposal

    def _floor_price(self, item_id: str) -> Decimal:
        item = self.catalog.get(item_id)
        if item is None:
            raise ValueError(f"Catalog item '{item_id}' does not exist.")
        return Decimal(item.base_price)

    def _persist_proposal(self, negotiation, proposal: NegotiationProposal) -> None:
        self.negotiation_repository.add_message(
            message_id=f"msg_{uuid4().hex}",
            negotiation_id=negotiation.negotiation_id,
            agent_id=proposal.agent_id,
            message_type=proposal.proposal_type.value,
            message=proposal.message,
            sequence_number=proposal.sequence_number,
            proposed_price=proposal.proposed_price,
            currency=proposal.currency,
        )
        negotiation.proposal_count = proposal.sequence_number
        if proposal.proposal_type == ProposalType.OFFER:
            negotiation.status = NegotiationStatus.OPEN.value
        self.negotiation_repository.db.flush()