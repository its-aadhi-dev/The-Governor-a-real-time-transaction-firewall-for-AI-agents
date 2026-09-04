from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from backend.core.models import NegotiatedDeal, NegotiationProposal
from backend.marketplace.buyer import BuyerAgent
from backend.marketplace.merchant import MerchantAgent
from backend.marketplace.negotiation import NegotiationEngine


AgentTurnType = Literal["OFFER", "COUNTER_OFFER", "ACCEPT"]


@dataclass(frozen=True)
class AgentTurn:
    actor: str
    agent_id: str
    turn_type: AgentTurnType
    price: Decimal
    round_number: int


@dataclass(frozen=True)
class LiveNegotiationResult:
    transaction_id: str
    turns: tuple[AgentTurn, ...]
    final_proposal: NegotiationProposal
    deal: NegotiatedDeal


class LiveNegotiationSession:
    """Run buyer/merchant negotiation without authorizing payment."""

    def __init__(
        self,
        *,
        buyer: BuyerAgent,
        merchant: MerchantAgent,
        merchant_floor_price: Decimal,
        item,
        negotiation_id: str,
        transaction_id: str,
        maximum_price: Decimal,
        asking_price: Decimal,
        max_rounds: int = 5,
    ) -> None:
        if maximum_price <= Decimal("0"):
            raise ValueError("Maximum price must be greater than zero.")
        if asking_price <= Decimal("0"):
            raise ValueError("Asking price must be greater than zero.")

        self.buyer = buyer
        self.merchant = merchant
        self.merchant_floor_price = merchant_floor_price
        self.item = item
        self.negotiation_id = negotiation_id
        self.transaction_id = transaction_id
        self.maximum_price = maximum_price
        self.asking_price = asking_price
        self.engine = NegotiationEngine(
            merchant_floor_price=merchant_floor_price,
            max_rounds=max_rounds,
        )

    def run(self) -> LiveNegotiationResult:
        turns: list[AgentTurn] = []
        buyer_price = self.buyer.initial_offer(
            asking_price=self.asking_price,
            maximum_price=self.maximum_price,
        )
        buyer_result = self.engine.validate_offer(
            price=buyer_price,
            round_number=1,
            negotiation_id=self.negotiation_id,
            transaction_id=self.transaction_id,
            agent_id=self.buyer.agent_id,
        )
        if buyer_result.proposal is None:
            raise ValueError(
                buyer_result.message or "Buyer offer could not be created."
            )

        turns.append(
            AgentTurn(
                actor="buyer",
                agent_id=self.buyer.agent_id,
                turn_type="OFFER",
                price=buyer_price,
                round_number=1,
            )
        )

        if self.buyer.should_accept(
            offered_price=self.asking_price,
            maximum_price=self.maximum_price,
        ):
            final = self.engine.accept(
                price=self.asking_price,
                round_number=2,
                negotiation_id=self.negotiation_id,
                transaction_id=self.transaction_id,
                agent_id=self.buyer.agent_id,
            )
            turns.append(
                AgentTurn(
                    actor="buyer",
                    agent_id=self.buyer.agent_id,
                    turn_type="ACCEPT",
                    price=self.asking_price,
                    round_number=2,
                )
            )
            return self._result(turns, final)

        counter_price = self.merchant.counter_price(
            buyer_price=buyer_price,
            asking_price=self.asking_price,
            floor_price=self.merchant_floor_price,
        )
        if counter_price > self.maximum_price:
            counter_price = self.maximum_price.quantize(Decimal("0.01"))

        if counter_price <= buyer_price:
            if buyer_price < self.merchant_floor_price:
                raise ValueError("Buyer and merchant could not reach an agreement.")
            final = self.engine.accept(
                price=buyer_price,
                round_number=2,
                negotiation_id=self.negotiation_id,
                transaction_id=self.transaction_id,
                agent_id=self.buyer.agent_id,
            )
            turns.append(
                AgentTurn(
                    actor="buyer",
                    agent_id=self.buyer.agent_id,
                    turn_type="ACCEPT",
                    price=buyer_price,
                    round_number=2,
                )
            )
            return self._result(turns, final)

        counter = self.engine.merchant_counter_offer(
            buyer_price=buyer_price,
            merchant_price=counter_price,
            round_number=2,
            negotiation_id=self.negotiation_id,
            transaction_id=self.transaction_id,
            agent_id=self.merchant.merchant_id,
        )
        turns.append(
            AgentTurn(
                actor="merchant",
                agent_id=self.merchant.merchant_id,
                turn_type="COUNTER_OFFER",
                price=counter_price,
                round_number=2,
            )
        )
        if not self.buyer.should_accept(
            offered_price=counter_price,
            maximum_price=self.maximum_price,
        ):
            raise ValueError("Buyer and merchant could not reach an agreement.")

        final = self.engine.accept(
            price=counter_price,
            round_number=3,
            negotiation_id=self.negotiation_id,
            transaction_id=self.transaction_id,
            agent_id=self.buyer.agent_id,
        )
        turns.append(
            AgentTurn(
                actor="buyer",
                agent_id=self.buyer.agent_id,
                turn_type="ACCEPT",
                price=counter_price,
                round_number=3,
            )
        )
        return self._result(turns, final)

    def _result(
        self,
        turns: list[AgentTurn],
        final_proposal: NegotiationProposal,
    ) -> LiveNegotiationResult:
        deal = NegotiatedDeal(
            transaction_id=self.transaction_id,
            negotiation_id=self.negotiation_id,
            buyer_agent_id=self.buyer.agent_id,
            merchant_agent_id=self.merchant.merchant_id,
            item=self.item,
            agreed_price=final_proposal.proposed_price,
            currency=final_proposal.currency,
            proposal_count=final_proposal.sequence_number,
            final_proposal_id=final_proposal.proposal_id,
        )
        return LiveNegotiationResult(
            transaction_id=self.transaction_id,
            turns=tuple(turns),
            final_proposal=final_proposal,
            deal=deal,
        )
