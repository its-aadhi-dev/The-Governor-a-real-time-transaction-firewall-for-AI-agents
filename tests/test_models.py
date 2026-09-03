from decimal import Decimal

import pytest
from pydantic import ValidationError

from backend.core.models import (
    AgentIdentity,
    AgentRole,
    AgentStatus,
    CommerceItem,
    NegotiationProposal,
    ProposalType,
    TransactionIntent,
)


def test_commerce_item_accepts_decimal_price():

    item = CommerceItem(
        item_id="item_001",
        item_name="Compute Credits",
        base_price=Decimal("1500.00"),
        currency="inr",
    )

    assert item.base_price == Decimal("1500.00")
    assert item.currency == "INR"


def test_invalid_negative_price_is_rejected():

    with pytest.raises(ValidationError):

        CommerceItem(
            item_id="item_001",
            item_name="Invalid Item",
            base_price=Decimal("-1.00"),
            currency="INR",
        )


def test_agent_identity_is_strongly_typed():

    agent = AgentIdentity(
        agent_id="buyer_001",
        role=AgentRole.BUYER,
        status=AgentStatus.ACTIVE,
    )

    assert agent.role == AgentRole.BUYER
    assert agent.trust_score == Decimal("1.0000")


def test_unknown_fields_are_rejected():

    with pytest.raises(ValidationError):

        CommerceItem(
            item_id="item_001",
            item_name="Compute",
            base_price=Decimal("1000.00"),
            currency="INR",
            unauthorized_override=True,
        )


def test_proposal_is_not_payment_authorization():

    proposal = NegotiationProposal(
        proposal_id="proposal_001",
        negotiation_id="neg_001",
        transaction_id="txn_001",
        agent_id="buyer_001",
        role=AgentRole.BUYER,
        proposal_type=ProposalType.OFFER,
        proposed_price=Decimal("1500.00"),
        currency="INR",
        message="I can pay ₹1500.",
        sequence_number=1,
    )

    assert proposal.proposed_price == Decimal("1500.00")

    assert not hasattr(
        proposal,
        "authorization_id",
    )
    
from decimal import Decimal

import pytest
from pydantic import ValidationError

from backend.core.models import (
    AgentIdentity,
    AgentRole,
    AgentStatus,
    CommerceItem,
    NegotiationProposal,
    ProposalType,
    TransactionIntent,
)


def test_commerce_item_accepts_decimal_price():

    item = CommerceItem(
        item_id="item_001",
        item_name="Compute Credits",
        base_price=Decimal("1500.00"),
        currency="inr",
    )

    assert item.base_price == Decimal("1500.00")
    assert item.currency == "INR"


def test_invalid_negative_price_is_rejected():

    with pytest.raises(ValidationError):

        CommerceItem(
            item_id="item_001",
            item_name="Invalid Item",
            base_price=Decimal("-1.00"),
            currency="INR",
        )


def test_agent_identity_is_strongly_typed():

    agent = AgentIdentity(
        agent_id="buyer_001",
        role=AgentRole.BUYER,
        status=AgentStatus.ACTIVE,
    )

    assert agent.role == AgentRole.BUYER
    assert agent.trust_score == Decimal("1.0000")


def test_unknown_fields_are_rejected():

    with pytest.raises(ValidationError):

        CommerceItem(
            item_id="item_001",
            item_name="Compute",
            base_price=Decimal("1000.00"),
            currency="INR",
            unauthorized_override=True,
        )


def test_proposal_is_not_payment_authorization():

    proposal = NegotiationProposal(
        proposal_id="proposal_001",
        negotiation_id="neg_001",
        transaction_id="txn_001",
        agent_id="buyer_001",
        role=AgentRole.BUYER,
        proposal_type=ProposalType.OFFER,
        proposed_price=Decimal("1500.00"),
        currency="INR",
        message="I can pay ₹1500.",
        sequence_number=1,
    )

    assert proposal.proposed_price == Decimal("1500.00")

    assert not hasattr(
        proposal,
        "authorization_id",
    )