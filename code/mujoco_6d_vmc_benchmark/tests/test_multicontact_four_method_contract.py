"""Static safety/fairness contracts for the comprehensive four-method run."""

from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"


def test_mlp_training_converts_per_trace_budget_to_the_declared_deployment_unit() -> None:
    source = (SCRIPTS / "train_mlp_baseline.py").read_text()
    assert '"--target-budget"' in source
    assert "obs, act, trace_budget = _load_episode" in source
    assert "act * trace_budget / args.target_budget" in source
    assert '"trace_provenance"' in source


def test_four_method_runner_keeps_nominal_papermpc_residual_free_and_matches_fixtures() -> None:
    source = (SCRIPTS / "run_multicontact_four_method_benchmark.py").read_text()
    assert '("paper_mpc_nominal_only", None' in source
    assert '"fixture(seed*6151 + fixture_index + 1)"' in source
    assert '"four-method-test requires --mlp and --esn"' in source
    assert "no force, apparatus, geometry, direction label, time, or future input" in source


def test_mlp_validation_selection_is_separate_from_the_fixed_policy_test() -> None:
    source = (SCRIPTS / "run_multicontact_four_method_benchmark.py").read_text()
    assert 'choices=("mlp-validation", "four-method-test")' in source
    assert '"selection_only; frozen PaperMPC/VMC/ESN not evaluated or reselected"' in source
    assert '"maximize task success count"' in source
