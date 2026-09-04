from decimal import Decimal

import pytest

from backend.core.models import CommerceItem, ProposalType
from backend.marketplace.buyer import BuyerAgent
from backend.marketplace.merchant import MerchantAgent
from backend.marketplace.live_session import LiveNegotiationSession


ITEM = CommerceItem(
    item_id="item-1",
    item_name="Governor Test Item",
    base_price=Decimal("1000.00"),
    currency="INR",
)


def make_session(
    *,
    maximum_price=Decimal("980.00"),
    asking_price=Decimal("1000.00"),
    floor_price=Decimal("900.00"),
):
    return LiveNegotiationSession(
        buyer=BuyerAgent("buyer-agent"),
        merchant=MerchantAgent("merchant-agent"),
        merchant_floor_price=floor_price,
        item=ITEM,
        negotiation_id="neg-1",
        transaction_id="txn-1",
        maximum_price=maximum_price,
        asking_price=asking_price,
    )


def test_live_agents_reach_agreement():
    result = make_session().run()

    assert result.transaction_id == "txn-1"
    assert result.final_proposal.proposal_type == ProposalType.ACCEPT
    assert result.deal.agreed_price > Decimal("0")
    assert len(result.turns) >= 2


def test_live_agents_record_buyer_merchant_turns():
    result = make_session().run()
    actors = [turn.actor for turn in result.turns]

    assert actors[0] == "buyer"
    assert "merchant" in actors
    assert actors[-1] == "buyer"


def test_live_agents_never_agree_above_buyer_limit():
    result = make_session(
        maximum_price=Decimal("905.00"),
        asking_price=Decimal("1000.00"),
        floor_price=Decimal("900.00"),
    ).run()

    assert result.deal.agreed_price <= Decimal("905.00")


def test_live_agents_reject_unreachable_price():
    with pytest.raises(ValueError):
        make_session(
            maximum_price=Decimal("800.00"),
            asking_price=Decimal("1000.00"),
            floor_price=Decimal("900.00"),
        ).run()
