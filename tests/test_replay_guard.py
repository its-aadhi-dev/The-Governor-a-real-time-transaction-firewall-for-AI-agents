import pytest

from backend.canon.replay import (
    ReplayDetectedError,
    ReplayGuard,
)


def test_fresh_transaction_identity_is_allowed():
    guard = ReplayGuard()

    decision = guard.evaluate(
        transaction_exists=False
    )

    assert decision.replayed is False
    assert decision.reason == "Transaction identity is fresh."


def test_consumed_transaction_identity_is_replay():
    guard = ReplayGuard()

    decision = guard.evaluate(
        transaction_exists=True
    )

    assert decision.replayed is True
    assert (
        decision.reason
        == "Transaction identity has already been consumed."
    )


def test_replay_is_rejected():
    guard = ReplayGuard()

    with pytest.raises(ReplayDetectedError):
        guard.require_fresh(
            transaction_exists=True
        )
