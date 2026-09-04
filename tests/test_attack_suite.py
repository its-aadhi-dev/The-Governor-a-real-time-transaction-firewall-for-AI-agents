from types import SimpleNamespace

import pytest

from attacks.runner import AttackRunner
from attacks.scenarios import AttackScenario, AttackType, default_scenarios


def test_default_attack_suite_contains_required_scenarios():
    scenarios = default_scenarios()
    names = {scenario.name for scenario in scenarios}

    assert names == {
        "legitimate_transaction",
        "price_floor_attack",
        "velocity_attack",
        "reputation_attack",
        "collusion_attack",
        "replay_attack",
    }


def test_attack_types_are_explicit():
    scenarios = default_scenarios()

    assert {scenario.attack_type for scenario in scenarios} == {
        AttackType.LEGITIMATE,
        AttackType.PRICE,
        AttackType.VELOCITY,
        AttackType.REPUTATION,
        AttackType.COLLUSION,
        AttackType.REPLAY,
    }


def test_attack_runner_passes_when_production_evaluator_matches():
    def evaluator(scenario):
        return SimpleNamespace(
            decision=SimpleNamespace(
                decision=SimpleNamespace(value=scenario.expected_decision)
            )
        )

    result = AttackRunner(evaluator).run(default_scenarios()[0])

    assert result.passed is True
    assert result.actual_decision == "ALLOW"
    assert result.error is None


def test_attack_runner_detects_wrong_decision():
    def evaluator(_scenario):
        return SimpleNamespace(
            decision=SimpleNamespace(
                decision=SimpleNamespace(value="ALLOW")
            )
        )

    scenario = next(
        item for item in default_scenarios() if item.name == "price_floor_attack"
    )
    result = AttackRunner(evaluator).run(scenario)

    assert result.passed is False
    assert result.actual_decision == "ALLOW"
    assert result.scenario.expected_decision == "BLOCK"


def test_attack_runner_records_evaluator_failure():
    def evaluator(_scenario):
        raise RuntimeError("governor failure")

    result = AttackRunner(evaluator).run(default_scenarios()[0])

    assert result.passed is False
    assert result.actual_decision == "ERROR"
    assert result.error == "governor failure"


def test_invalid_scenario_is_rejected():
    with pytest.raises(ValueError):
        AttackScenario(
            name="",
            attack_type=AttackType.PRICE,
            description="test",
            expected_decision="BLOCK",
            payload={},
        )
