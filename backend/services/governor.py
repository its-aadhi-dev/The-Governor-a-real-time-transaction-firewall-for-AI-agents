from __future__ import annotations

from backend.canon.governor import Governor, GovernorEvaluation
from backend.core.governance import GovernanceContext
from backend.core.models import TransactionStatus


class GovernorService:
    """
    Application-layer transaction governance orchestration.

    Authoritative commercial values are supplied by the caller because the
    current persistence models do not contain a merchant floor or agreed deal.
    """

    def __init__(
        self,
        *,
        governor: Governor,
        transaction_repository,
        lifecycle_service,
    ) -> None:
        self.governor = governor
        self.transaction_repository = transaction_repository
        self.lifecycle_service = lifecycle_service

    def evaluate_transaction(
        self,
        *,
        context: GovernanceContext,
    ) -> GovernorEvaluation:
        transaction = self.transaction_repository.get(context.transaction_id)

        if transaction is None:
            raise ValueError(
                f"Transaction '{context.transaction_id}' was not found."
            )

        if transaction.status != TransactionStatus.GOVERNANCE_PENDING.value:
            raise ValueError(
                "Transaction has already completed governance evaluation."
            )

        if transaction.buyer_agent_id != context.buyer_agent_id:
            raise ValueError("Governance context buyer does not match transaction.")

        if transaction.merchant_agent_id != context.merchant_id:
            raise ValueError(
                "Governance context merchant does not match transaction."
            )

        if transaction.item_id != context.catalog_item_id:
            raise ValueError("Governance context item does not match transaction.")

        evaluation = self.governor.evaluate(context=context)
        self.lifecycle_service.apply_governor_decision(
            context.transaction_id,
            evaluation.decision.decision,
            risk_score=evaluation.risk.score,
        )
        return evaluation