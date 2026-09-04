from decimal import Decimal

import pytest

from backend.core.models import (
	CommerceItem,
	NegotiatedDeal,
	NegotiationStatus,
	ProposalType,
)
from backend.services.negotiation_service import NegotiationService


class FakeCatalogItem:
	def __init__(
		self,
		*,
		item_id="item-1",
		merchant_id="merchant-1",
		item_name="Test Item",
		base_price=Decimal("1000.00"),
		currency="INR",
	):
		self.item_id = item_id
		self.merchant_id = merchant_id
		self.item_name = item_name
		self.base_price = base_price
		self.currency = currency


class FakeCatalogRepository:
	def __init__(self, db):
		self.item = FakeCatalogItem()

	def get(self, item_id):
		if item_id == self.item.item_id:
			return self.item
		return None


class FakeDB:
	def flush(self):
		pass


class FakeNegotiationRepository:
	def __init__(self):
		self.db = FakeDB()

	def add_message(self, **kwargs):
		return kwargs


def make_service():
	service = NegotiationService(FakeNegotiationRepository())
	service.catalog = FakeCatalogRepository(service.negotiation_repository.db)
	return service


def make_negotiation():
	return type(
		"Negotiation",
		(),
		{
			"negotiation_id": "neg-1",
			"buyer_agent_id": "buyer-1",
			"merchant_agent_id": "merchant-1",
			"item_id": "item-1",
			"status": NegotiationStatus.ACCEPTED.value,
			"proposal_count": 2,
		},
	)()


def make_acceptance():
	return type(
		"Acceptance",
		(),
		{
			"proposal_id": "proposal-2",
			"negotiation_id": "neg-1",
			"transaction_id": "txn-1",
			"agent_id": "buyer-1",
			"proposal_type": ProposalType.ACCEPT,
			"proposed_price": Decimal("950.00"),
			"currency": "INR",
			"sequence_number": 2,
		},
	)()


def test_accepted_negotiation_creates_negotiated_deal():
	service = make_service()
	deal = service.finalize_deal(
		negotiation=make_negotiation(),
		final_proposal=make_acceptance(),
	)

	assert isinstance(deal, NegotiatedDeal)
	assert deal.transaction_id == "txn-1"
	assert deal.negotiation_id == "neg-1"
	assert deal.buyer_agent_id == "buyer-1"
	assert deal.merchant_agent_id == "merchant-1"
	assert deal.agreed_price == Decimal("950.00")
	assert deal.final_proposal_id == "proposal-2"
	assert deal.status == NegotiationStatus.ACCEPTED


def test_negotiated_deal_creates_transaction_intent():
	service = make_service()
	deal = NegotiatedDeal(
		transaction_id="txn-1",
		negotiation_id="neg-1",
		buyer_agent_id="buyer-1",
		merchant_agent_id="merchant-1",
		item=CommerceItem(
			item_id="item-1",
			item_name="Test Item",
			base_price=Decimal("1000.00"),
			currency="INR",
		),
		agreed_price=Decimal("950.00"),
		currency="INR",
		status=NegotiationStatus.ACCEPTED,
		proposal_count=2,
		final_proposal_id="proposal-2",
	)

	intent = service.create_transaction_intent(
		deal=deal,
		idempotency_key="idem-1",
	)

	assert intent.transaction_id == "txn-1"
	assert intent.negotiation_id == "neg-1"
	assert intent.buyer_agent_id == "buyer-1"
	assert intent.merchant_agent_id == "merchant-1"
	assert intent.item.item_id == "item-1"
	assert intent.requested_price == Decimal("950.00")
	assert intent.currency == "INR"
	assert intent.idempotency_key == "idem-1"


def test_unaccepted_negotiation_cannot_create_deal():
	service = make_service()
	negotiation = make_negotiation()
	negotiation.status = NegotiationStatus.OPEN.value

	with pytest.raises(ValueError):
		service.finalize_deal(
			negotiation=negotiation,
			final_proposal=make_acceptance(),
		)


def test_non_accept_proposal_cannot_create_deal():
	service = make_service()
	offer = make_acceptance()
	offer.proposal_type = ProposalType.OFFER

	with pytest.raises(ValueError):
		service.finalize_deal(
			negotiation=make_negotiation(),
			final_proposal=offer,
		)


def test_wrong_negotiation_cannot_create_deal():
	service = make_service()
	acceptance = make_acceptance()
	acceptance.negotiation_id = "different-negotiation"

	with pytest.raises(ValueError):
		service.finalize_deal(
			negotiation=make_negotiation(),
			final_proposal=acceptance,
		)


def test_non_accepted_deal_cannot_create_transaction_intent():
	service = make_service()
	deal = NegotiatedDeal(
		transaction_id="txn-1",
		negotiation_id="neg-1",
		buyer_agent_id="buyer-1",
		merchant_agent_id="merchant-1",
		item=CommerceItem(
			item_id="item-1",
			item_name="Test Item",
			base_price=Decimal("1000.00"),
			currency="INR",
		),
		agreed_price=Decimal("950.00"),
		currency="INR",
		status=NegotiationStatus.OPEN,
		proposal_count=1,
		final_proposal_id="proposal-1",
	)

	with pytest.raises(ValueError):
		service.create_transaction_intent(
			deal=deal,
			idempotency_key="idem-1",
		)