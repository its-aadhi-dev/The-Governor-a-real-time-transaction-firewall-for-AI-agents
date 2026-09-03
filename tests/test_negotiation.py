from decimal import Decimal

import pytest

from backend.core.models import NegotiationStatus, ProposalType
from backend.marketplace.negotiation import NegotiationEngine


def test_offer_above_floor_is_valid():
    engine = NegotiationEngine(merchant_floor_price=Decimal("900.00"))
    result = engine.validate_offer(price=Decimal("1000.00"), round_number=1)

    assert result.status == NegotiationStatus.OPEN
    assert result.proposal is not None
    assert result.proposal.proposal_type == ProposalType.OFFER
    assert result.proposal.proposed_price == Decimal("1000.00")


def test_offer_below_floor_is_countered():
    engine = NegotiationEngine(merchant_floor_price=Decimal("900.00"))
    result = engine.validate_offer(price=Decimal("700.00"), round_number=1)

    assert result.status == NegotiationStatus.COUNTERED
    assert result.proposal is None


def test_accept_above_floor():
    engine = NegotiationEngine(merchant_floor_price=Decimal("900.00"))
    proposal = engine.accept(price=Decimal("950.00"), round_number=2)

    assert proposal.proposal_type == ProposalType.ACCEPT
    assert proposal.proposed_price == Decimal("950.00")


def test_accept_below_floor_fails():
    engine = NegotiationEngine(merchant_floor_price=Decimal("900.00"))
    with pytest.raises(ValueError):
        engine.accept(price=Decimal("800.00"), round_number=2)