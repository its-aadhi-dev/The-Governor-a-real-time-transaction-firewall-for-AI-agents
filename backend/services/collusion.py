from __future__ import annotations

from decimal import Decimal

from backend.canon.policies.collusion import CollusionPolicy
from backend.core.collusion import CollusionContext, CollusionDecision
from backend.database.repositories.collusion import CollusionRepository


class CollusionService:
    """
    Loads persistent relationship history and evaluates it.
    """

    def __init__(
        self,
        *,
        collusion_repository: CollusionRepository,
        policy: CollusionPolicy | None = None,
    ) -> None:
        self.collusion_repository = collusion_repository
        self.policy = policy or CollusionPolicy()

    def evaluate(
        self,
        *,
        buyer_agent_id: str,
        merchant_id: str,
    ) -> CollusionDecision:
        buyer_count, pair_count = (
            self.collusion_repository.get_relationship_counts(
                buyer_agent_id=buyer_agent_id,
                merchant_id=merchant_id,
            )
        )

        if buyer_count == 0:
            ratio = Decimal("0")
        else:
            ratio = Decimal(pair_count) / Decimal(buyer_count)

        context = CollusionContext(
            buyer_agent_id=buyer_agent_id,
            merchant_id=merchant_id,
            buyer_transaction_count=buyer_count,
            buyer_merchant_transaction_count=pair_count,
            concentration_ratio=ratio,
        )

        return self.policy.evaluate(context)