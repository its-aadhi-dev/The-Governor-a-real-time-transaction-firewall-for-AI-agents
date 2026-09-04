from __future__ import annotations

from dataclasses import dataclass


class ReplayDetectedError(RuntimeError):
    """Raised when a transaction identity has already been consumed."""


@dataclass(frozen=True)
class ReplayDecision:
    replayed: bool
    reason: str


class ReplayGuard:
    """
    Transaction-identity replay guard.

    The durable transaction repository remains authoritative. This class
    provides the Canon-level decision boundary without maintaining its own
    mutable in-memory state.
    """

    def evaluate(self, *, transaction_exists: bool) -> ReplayDecision:
        if transaction_exists:
            return ReplayDecision(
                replayed=True,
                reason="Transaction identity has already been consumed.",
            )

        return ReplayDecision(
            replayed=False,
            reason="Transaction identity is fresh.",
        )

    def require_fresh(self, *, transaction_exists: bool) -> None:
        decision = self.evaluate(
            transaction_exists=transaction_exists
        )

        if decision.replayed:
            raise ReplayDetectedError(
                decision.reason
            )
