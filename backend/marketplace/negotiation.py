from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from backend.core.models import NegotiationProposal, NegotiationStatus, ProposalType


@dataclass(frozen=True)
class NegotiationResult:
	status: NegotiationStatus
	proposal: Optional[NegotiationProposal] = None
	message: Optional[str] = None


class NegotiationEngine:
	"""Deterministically establish whether a commercial agreement exists."""

	def __init__(self, *, merchant_floor_price: Decimal, max_rounds: int = 5) -> None:
		if merchant_floor_price <= Decimal("0"):
			raise ValueError("Merchant floor price must be greater than zero.")
		if max_rounds <= 0:
			raise ValueError("Maximum negotiation rounds must be greater than zero.")
		self.merchant_floor_price = merchant_floor_price
		self.max_rounds = max_rounds

	def validate_offer(
		self,
		*,
		price: Decimal,
		round_number: int,
		negotiation_id: str = "negotiation",
		transaction_id: str = "transaction",
		agent_id: str = "buyer",
	) -> NegotiationResult:
		if price <= Decimal("0"):
			raise ValueError("Offer price must be greater than zero.")
		if round_number < 1:
			raise ValueError("Round number must be at least one.")
		if round_number > self.max_rounds:
			return NegotiationResult(
				status=NegotiationStatus.EXPIRED,
				message="Maximum negotiation rounds exceeded.",
			)
		if price < self.merchant_floor_price:
			return NegotiationResult(
				status=NegotiationStatus.COUNTERED,
				message="Offer is below merchant floor price.",
			)

		return NegotiationResult(
			status=NegotiationStatus.OPEN,
			proposal=NegotiationProposal(
				proposal_id=f"proposal_{uuid4().hex}",
				negotiation_id=negotiation_id,
				transaction_id=transaction_id,
				agent_id=agent_id,
				role="BUYER",
				proposal_type=ProposalType.OFFER,
				proposed_price=price,
				currency="INR",
				sequence_number=round_number,
			),
		)

	def merchant_counter_offer(
		self,
		*,
		buyer_price: Decimal,
		merchant_price: Decimal,
		round_number: int,
		negotiation_id: str = "negotiation",
		transaction_id: str = "transaction",
		agent_id: str = "merchant",
	) -> NegotiationProposal:
		if merchant_price <= buyer_price:
			raise ValueError("Merchant counter price must be greater than buyer offer.")
		if round_number < 1 or round_number > self.max_rounds:
			raise ValueError("Counter-offer round is outside the negotiation limit.")
		return NegotiationProposal(
			proposal_id=f"proposal_{uuid4().hex}",
			negotiation_id=negotiation_id,
			transaction_id=transaction_id,
			agent_id=agent_id,
			role="MERCHANT",
			proposal_type=ProposalType.COUNTER_OFFER,
			proposed_price=merchant_price,
			currency="INR",
			sequence_number=round_number,
		)

	def accept(
		self,
		*,
		price: Decimal,
		round_number: int,
		negotiation_id: str = "negotiation",
		transaction_id: str = "transaction",
		agent_id: str = "buyer",
	) -> NegotiationProposal:
		if price < self.merchant_floor_price:
			raise ValueError("Cannot accept a price below merchant floor price.")
		if round_number < 1 or round_number > self.max_rounds:
			raise ValueError("Acceptance round is outside the negotiation limit.")
		return NegotiationProposal(
			proposal_id=f"proposal_{uuid4().hex}",
			negotiation_id=negotiation_id,
			transaction_id=transaction_id,
			agent_id=agent_id,
			role="BUYER",
			proposal_type=ProposalType.ACCEPT,
			proposed_price=price,
			currency="INR",
			sequence_number=round_number,
		)
