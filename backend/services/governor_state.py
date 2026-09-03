from __future__ import annotations

from decimal import Decimal
from typing import Optional

from backend.core.governor_state import GovernorState
from backend.database.repositories.price_observation import PriceObservationRepository
from backend.database.repositories.reputation import ReputationRepository


class GovernorStateService:
    """Build policy input from repositories rather than exposing SQL to policies."""

    def __init__(
        self,
        *,
        reputation_repository: ReputationRepository,
        price_observation_repository: PriceObservationRepository,
    ) -> None:
        self.reputation_repository = reputation_repository
        self.price_observation_repository = price_observation_repository

    def get_agent_state(self, *, agent_id: str) -> GovernorState:
        reputation = self.reputation_repository.get_or_create(agent_id=agent_id)
        return self._state_from_reputation(reputation, agent_id=agent_id)

    def get_transaction_state(
        self,
        *,
        agent_id: str,
        catalog_item_id: str,
        merchant_id: str,
    ) -> GovernorState:
        reputation = self.reputation_repository.get_or_create(agent_id=agent_id)
        minimum_price, maximum_price = self.price_observation_repository.get_price_range(
            catalog_item_id=catalog_item_id,
            merchant_id=merchant_id,
        )
        return self._state_from_reputation(
            reputation,
            agent_id=agent_id,
            minimum_observed_price=minimum_price,
            maximum_observed_price=maximum_price,
        )

    def record_price_observation(
        self,
        *,
        transaction_id: str,
        buyer_agent_id: str,
        merchant_agent_id: str,
        catalog_item_id: str,
        base_price: Decimal,
        observed_price: Decimal,
        currency: str = "INR",
    ):
        return self.price_observation_repository.record(
            transaction_id=transaction_id,
            buyer_agent_id=buyer_agent_id,
            merchant_agent_id=merchant_agent_id,
            item_id=catalog_item_id,
            base_price=base_price,
            agreed_price=observed_price,
            currency=currency,
        )

    @staticmethod
    def _state_from_reputation(
        reputation,
        *,
        agent_id: str,
        minimum_observed_price: Optional[Decimal] = None,
        maximum_observed_price: Optional[Decimal] = None,
    ) -> GovernorState:
        transaction_count = (
            reputation.successful_transactions
            + reputation.review_transactions
            + reputation.blocked_transactions
        )
        return GovernorState(
            agent_id=agent_id,
            reputation_score=reputation.trust_score,
            transaction_count=transaction_count,
            successful_transaction_count=reputation.successful_transactions,
            blocked_transaction_count=reputation.blocked_transactions,
            last_transaction_at=reputation.last_transaction_at,
            minimum_observed_price=minimum_observed_price,
            maximum_observed_price=maximum_observed_price,
        )