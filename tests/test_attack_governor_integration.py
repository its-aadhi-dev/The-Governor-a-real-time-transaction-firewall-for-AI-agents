from attacks.governor_adapter import AttackGovernorAdapter
from attacks.runner import AttackRunner
from attacks.scenarios import default_scenarios


def test_attack_suite_runs_against_real_governor():
    results = AttackRunner(AttackGovernorAdapter().evaluate).run_all(
        default_scenarios()
    )
    by_name = {result.scenario.name: result for result in results}

    assert by_name["legitimate_transaction"].actual_decision == "ALLOW"
    assert by_name["price_floor_attack"].actual_decision == "BLOCK"
    assert by_name["velocity_attack"].actual_decision == "BLOCK"
    assert by_name["reputation_attack"].actual_decision == "REVIEW"
    assert by_name["collusion_attack"].actual_decision == "REVIEW"
    assert by_name["replay_attack"].actual_decision == "BLOCK"


def test_attack_suite_reports_implemented_controls_as_passes():
    results = AttackRunner(AttackGovernorAdapter().evaluate).run_all(
        default_scenarios()
    )

    assert all(result.passed for result in results)


def test_replay_attack_is_blocked_by_identity_boundary():
    from attacks.runner import AttackRunner
    from attacks.scenarios import default_scenarios

    replay = next(
        scenario
        for scenario in default_scenarios()
        if scenario.name == "replay_attack"
    )

    runner = AttackRunner(lambda _: None)

    result = runner.run_identity_attack(
        replay,
        transaction_identity_exists=True,
    )

    assert result.actual_decision == "BLOCK"
    assert result.passed is True
