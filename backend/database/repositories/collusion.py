from __future__ import annotations

from backend.database.repositories.transaction import TransactionRepository


class CollusionRepository:
    """
    Provides persistent relationship statistics for collusion analysis.
    """

    def __init__(
        self,
        transaction_repository: TransactionRepository,
    ) -> None:
        self.transaction_repository = transaction_repository

    def get_relationship_counts(
        self,
        *,
        buyer_agent_id: str,
        merchant_id: str,
    ) -> tuple[int, int]:
        buyer_count = self.transaction_repository.count_buyer_transactions(
            buyer_agent_id=buyer_agent_id,
        )

        pair_count = (
            self.transaction_repository.count_buyer_merchant_transactions(
                buyer_agent_id=buyer_agent_id,
                merchant_id=merchant_id,
            )
        )

        return buyer_count, pair_count