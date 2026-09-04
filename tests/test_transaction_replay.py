from decimal import Decimal
from unittest.mock import Mock

import pytest

from backend.core.models import CommerceItem, TransactionIntent
from backend.canon.replay import ReplayDetectedError
from backend.services.transaction_service import TransactionService


def make_intent(*, transaction_id: str, idempotency_key: str):
    return TransactionIntent(
        transaction_id=transaction_id,
        negotiation_id="neg-1",
        buyer_agent_id="buyer-1",
        merchant_agent_id="merchant-1",
        item=CommerceItem(
            item_id="item-1",
            item_name="Test Item",
            base_price=Decimal("1000.00"),
            currency="INR",
        ),
        requested_price=Decimal("950.00"),
        currency="INR",
        idempotency_key=idempotency_key,
    )


def test_transaction_identity_replay_is_rejected():
    service = object.__new__(TransactionService)

    service.transactions = Mock()
    service.transactions.get_by_idempotency_key.return_value = None
    service.transactions.get.return_value = Mock(
        transaction_id="txn-1"
    )

    from backend.canon.replay import ReplayGuard

    service.replay_guard = ReplayGuard()

    with pytest.raises(ReplayDetectedError):
        service.replay_guard.require_fresh(
            transaction_exists=(
                service.transactions.get("txn-1")
                is not None
            )
        )
