from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.negotiation import NegotiationModel
from backend.database.models.negotiation_message import NegotiationMessageModel


class NegotiationRepository:
	"""Persistence operations for negotiations and their messages."""

	def __init__(self, db: Session):
		self.db = db

	def get(self, negotiation_id: str) -> Optional[NegotiationModel]:
		statement = select(NegotiationModel).where(
			NegotiationModel.negotiation_id == negotiation_id
		)
		return self.db.scalar(statement)

	def create(
		self,
		*,
		negotiation_id: str,
		buyer_agent_id: str,
		merchant_agent_id: str,
		item_id: str,
	) -> NegotiationModel:
		negotiation = NegotiationModel(
			negotiation_id=negotiation_id,
			buyer_agent_id=buyer_agent_id,
			merchant_agent_id=merchant_agent_id,
			item_id=item_id,
			status="OPEN",
			proposal_count=0,
		)
		self.db.add(negotiation)
		self.db.flush()
		return negotiation

	def add_message(
		self,
		*,
		message_id: str,
		negotiation_id: str,
		agent_id: str,
		message_type: str,
		message: str,
		sequence_number: int,
		proposed_price: Optional[Decimal] = None,
		currency: str = "INR",
	) -> NegotiationMessageModel:
		negotiation_message = NegotiationMessageModel(
			message_id=message_id,
			negotiation_id=negotiation_id,
			agent_id=agent_id,
			message_type=message_type,
			proposed_price=proposed_price,
			currency=currency.upper(),
			message=message,
			sequence_number=sequence_number,
		)
		self.db.add(negotiation_message)
		self.db.flush()
		return negotiation_message

	def list_messages(self, negotiation_id: str) -> List[NegotiationMessageModel]:
		statement = (
			select(NegotiationMessageModel)
			.where(NegotiationMessageModel.negotiation_id == negotiation_id)
			.order_by(NegotiationMessageModel.sequence_number.asc())
		)
		return list(self.db.scalars(statement).all())
