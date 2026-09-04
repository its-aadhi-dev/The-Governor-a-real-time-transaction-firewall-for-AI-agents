from __future__ import annotations

from backend.canon.policies.reputation import ReputationPolicy
from backend.core.reputation import ReputationContext, ReputationDecision
from backend.database.repositories.reputation import ReputationRepository


class ReputationService:
    """
    Application service for persistent reputation state.
    """

    def __init__(
        self,
        *,
        reputation_repository: ReputationRepository,
        policy: ReputationPolicy | None = None,
    ) -> None:
        self.reputation_repository = reputation_repository
        self.policy = policy or ReputationPolicy()

    def evaluate(
        self,
        *,
        agent_id: str,
    ) -> ReputationDecision:
        record = self.reputation_repository.get_or_create(
            agent_id=agent_id,
        )

        context = ReputationContext(
            reputation_score=record.reputation_score,
            transaction_count=record.transaction_count,
            successful_transaction_count=(
                record.successful_transaction_count
            ),
            blocked_transaction_count=(
                record.blocked_transaction_count
            ),
        )

        return self.policy.evaluate(context)

    def record_success(self, *, agent_id: str):
        return self.reputation_repository.record_success(
            agent_id=agent_id,
        )

    def record_suspicious_block(self, *, agent_id: str):
        return self.reputation_repository.record_suspicious_block(
            agent_id=agent_id,
        )