from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from backend.core.models import TransactionIntent
from backend.database.models.transaction import TransactionModel
from backend.database.repositories.agent import AgentRepository
from backend.database.repositories.catalog import CatalogRepository
from backend.database.repositories.merchant import MerchantRepository
from backend.database.repositories.negotiation import NegotiationRepository
from backend.database.repositories.transaction import TransactionRepository


class TransactionService:
	"""Coordinate transaction validation and persistence."""

	def __init__(self, db: Session):
		self.db = db
		self.agents = AgentRepository(db)
		self.merchants = MerchantRepository(db)
		self.catalog = CatalogRepository(db)
		self.negotiations = NegotiationRepository(db)
		self.transactions = TransactionRepository(db)

	def create_transaction(self, intent: TransactionIntent) -> TransactionModel:
		buyer = self.agents.get(intent.buyer_agent_id)
		if buyer is None:
			raise ValueError(f"Buyer agent '{intent.buyer_agent_id}' does not exist.")

		merchant_agent = self.agents.get(intent.merchant_agent_id)
		if merchant_agent is None:
			raise ValueError(
				f"Merchant agent '{intent.merchant_agent_id}' does not exist."
			)

		item = self.catalog.get(intent.item_id)
		if item is None:
			raise ValueError(f"Catalog item '{intent.item_id}' does not exist.")
		if intent.currency.upper() != item.currency.upper():
			raise ValueError("Transaction currency does not match catalog currency.")

		negotiation = self.negotiations.get(intent.negotiation_id)
		if negotiation is None:
			raise ValueError(
				f"Negotiation '{intent.negotiation_id}' does not exist."
			)
		if (
			negotiation.buyer_agent_id != intent.buyer_agent_id
			or negotiation.merchant_agent_id != intent.merchant_agent_id
			or negotiation.item_id != intent.item_id
		):
			raise ValueError("Negotiation does not match the transaction participants or item.")

		existing = self.transactions.get_by_idempotency_key(intent.idempotency_key)
		if existing is not None:
			return existing

		return self.transactions.create(
			transaction_id=intent.transaction_id,
			idempotency_key=intent.idempotency_key,
			negotiation_id=intent.negotiation_id,
			buyer_agent_id=intent.buyer_agent_id,
			merchant_agent_id=intent.merchant_agent_id,
			item_id=intent.item_id,
			requested_price=Decimal(intent.requested_price),
			currency=intent.currency,
		)