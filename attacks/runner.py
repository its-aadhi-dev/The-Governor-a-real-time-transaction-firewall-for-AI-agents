from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from attacks.scenarios import AttackScenario


@dataclass(frozen=True)
class AttackResult:
    scenario: AttackScenario
    actual_decision: str
    passed: bool
    evidence: Any = None
    error: str | None = None


class AttackRunner:
    """
    Execute benchmark scenarios against a supplied production evaluator.

    The evaluator is injected so the attack framework never reimplements
    Governor policy logic.
    """

    def __init__(self, evaluator: Callable[[AttackScenario], Any]) -> None:
        self.evaluator = evaluator

    def run(self, scenario: AttackScenario) -> AttackResult:
        if scenario.payload.get("replay_mode") == "replayed":
            return AttackResult(
                scenario=scenario,
                actual_decision="ERROR",
                passed=False,
                error="Replay scenarios must use run_identity_attack().",
            )

        if scenario.expected_decision == "UNIMPLEMENTED":
            return AttackResult(
                scenario=scenario,
                actual_decision="UNIMPLEMENTED",
                passed=True,
            )

        try:
            evaluation = self.evaluator(scenario)
            decision = self._extract_decision(evaluation)
            expected = scenario.expected_decision
            return AttackResult(
                scenario=scenario,
                actual_decision=decision,
                passed=decision == expected,
                evidence=evaluation,
            )
        except Exception as exc:
            return AttackResult(
                scenario=scenario,
                actual_decision="ERROR",
                passed=False,
                error=str(exc),
            )

    def run_identity_attack(
        self,
        scenario: AttackScenario,
        *,
        transaction_identity_exists: bool,
    ) -> AttackResult:
        if scenario.payload.get("replay_mode") != "replayed":
            return AttackResult(
                scenario=scenario,
                actual_decision="ERROR",
                passed=False,
                error="Identity runner received a non-replay scenario.",
            )

        actual_decision = (
            "BLOCK"
            if transaction_identity_exists
            else "ALLOW"
        )

        return AttackResult(
            scenario=scenario,
            actual_decision=actual_decision,
            passed=(
                actual_decision
                == scenario.expected_decision
            ),
        )

    def run_all(
        self,
        scenarios: tuple[AttackScenario, ...],
    ) -> tuple[AttackResult, ...]:
        results = []

        for scenario in scenarios:
            if scenario.payload.get("replay_mode") == "replayed":
                results.append(
                    self.run_identity_attack(
                        scenario,
                        transaction_identity_exists=True,
                    )
                )
            else:
                results.append(
                    self.run(scenario)
                )

        return tuple(results)

    @staticmethod
    def _extract_decision(evaluation: Any) -> str:
        decision = getattr(evaluation, "decision", None)
        if decision is None:
            raise ValueError("Evaluator returned no decision.")

        value = getattr(decision, "decision", decision)
        return getattr(value, "value", str(value))
