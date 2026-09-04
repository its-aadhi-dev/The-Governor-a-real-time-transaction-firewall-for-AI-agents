from __future__ import annotations

from backend.canon.governor import Governor, GovernorEvaluation
from backend.core.events import (
    GOVERNOR_ALLOW,
    GOVERNOR_BLOCK,
    GOVERNOR_FALLBACK,
    GOVERNOR_REVIEW,
)
from backend.core.governance import GovernanceContext
from backend.core.models import SystemDecision, TransactionStatus


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
        ledger_service=None,
    ) -> None:
        self.governor = governor
        self.transaction_repository = transaction_repository
        self.lifecycle_service = lifecycle_service
        self.ledger_service = ledger_service

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

        if self.ledger_service is not None:
            event_types = {
                SystemDecision.ALLOW: GOVERNOR_ALLOW,
                SystemDecision.REVIEW: GOVERNOR_REVIEW,
                SystemDecision.BLOCK: GOVERNOR_BLOCK,
                SystemDecision.FALLBACK: GOVERNOR_FALLBACK,
            }
            self.ledger_service.append(
                event_type=event_types[evaluation.decision.decision],
                transaction_id=context.transaction_id,
                payload={
                    "transaction_id": context.transaction_id,
                    "decision": evaluation.decision.decision.value,
                    "risk_score": str(evaluation.risk.score),
                    "risk_level": evaluation.risk.level.value,
                    "reason": evaluation.decision.reason,
                    "policy_version": "1",
                },
            )
        return evaluation