from decimal import Decimal

from backend.core.governor_state import GovernorState


def test_governor_state_defaults():
    state = GovernorState(
        agent_id="buyer-001",
        reputation_score=Decimal("1.00"),
        transaction_count=0,
        successful_transaction_count=0,
        blocked_transaction_count=0,
        last_transaction_at=None,
        minimum_observed_price=None,
        maximum_observed_price=None,
    )

    assert state.agent_id == "buyer-001"
    assert state.reputation_score == Decimal("1.00")
    assert state.transaction_count == 0
    assert state.minimum_observed_price is None
    assert state.maximum_observed_price is None