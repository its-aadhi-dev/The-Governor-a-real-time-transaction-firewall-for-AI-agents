from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AttackType(str, Enum):
    LEGITIMATE = "LEGITIMATE"
    PRICE = "PRICE"
    VELOCITY = "VELOCITY"
    REPUTATION = "REPUTATION"
    COLLUSION = "COLLUSION"
    REPLAY = "REPLAY"


@dataclass(frozen=True)
class AttackScenario:
    """Description of one adversarial or legitimate benchmark case."""

    name: str
    attack_type: AttackType
    description: str
    expected_decision: str
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Scenario name is required.")
        if not self.description.strip():
            raise ValueError("Scenario description is required.")
        if not self.expected_decision.strip():
            raise ValueError("Expected decision is required.")


def default_scenarios() -> tuple[AttackScenario, ...]:
    return (
        AttackScenario(
            name="legitimate_transaction",
            attack_type=AttackType.LEGITIMATE,
            description="Normal transaction inside configured governance limits.",
            expected_decision="ALLOW",
            payload={
                "price_mode": "normal",
                "velocity_mode": "normal",
                "reputation_mode": "good",
                "collusion_mode": "normal",
                "replay_mode": "fresh",
            },
        ),
        AttackScenario(
            name="price_floor_attack",
            attack_type=AttackType.PRICE,
            description="Requested price violates the merchant floor boundary.",
            expected_decision="BLOCK",
            payload={
                "price_mode": "below_floor",
                "velocity_mode": "normal",
                "reputation_mode": "good",
                "collusion_mode": "normal",
                "replay_mode": "fresh",
            },
        ),
        AttackScenario(
            name="velocity_attack",
            attack_type=AttackType.VELOCITY,
            description="Buyer exceeds the configured financial velocity boundary.",
            expected_decision="BLOCK",
            payload={
                "price_mode": "normal",
                "velocity_mode": "blocked",
                "reputation_mode": "good",
                "collusion_mode": "normal",
                "replay_mode": "fresh",
            },
        ),
        AttackScenario(
            name="reputation_attack",
            attack_type=AttackType.REPUTATION,
            description="Buyer presents a poor reputation signal.",
            expected_decision="REVIEW",
            payload={
                "price_mode": "normal",
                "velocity_mode": "normal",
                "reputation_mode": "poor",
                "collusion_mode": "normal",
                "replay_mode": "fresh",
            },
        ),
        AttackScenario(
            name="collusion_attack",
            attack_type=AttackType.COLLUSION,
            description="Buyer activity is unusually concentrated on one merchant.",
            expected_decision="REVIEW",
            payload={
                "price_mode": "normal",
                "velocity_mode": "normal",
                "reputation_mode": "good",
                "collusion_mode": "concentrated",
                "replay_mode": "fresh",
            },
        ),
        AttackScenario(
            name="replay_attack",
            attack_type=AttackType.REPLAY,
            description="Previously consumed transaction identity is reused.",
            expected_decision="BLOCK",
            payload={
                "price_mode": "normal",
                "velocity_mode": "normal",
                "reputation_mode": "good",
                "collusion_mode": "normal",
                "replay_mode": "replayed",
            },
        ),
    )
