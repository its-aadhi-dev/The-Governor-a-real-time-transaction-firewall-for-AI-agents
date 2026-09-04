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

    def run_all(
        self,
        scenarios: tuple[AttackScenario, ...],
    ) -> tuple[AttackResult, ...]:
        return tuple(self.run(scenario) for scenario in scenarios)

    @staticmethod
    def _extract_decision(evaluation: Any) -> str:
        decision = getattr(evaluation, "decision", None)
        if decision is None:
            raise ValueError("Evaluator returned no decision.")

        value = getattr(decision, "decision", decision)
        return getattr(value, "value", str(value))
