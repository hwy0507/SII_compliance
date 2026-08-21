"""Static contracts for the Paper-MPC benchmark evaluation protocol."""

from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "run_paper_mpc_benchmark.py"


def test_paper_mpc_benchmark_exposes_explicit_multi_seed_evaluation() -> None:
    source = SCRIPT.read_text()

    assert '"--eval-seeds"' in source
    assert "seed=seed" in source
    assert "env.reset(seed=seed" in source
    assert "seed=int(seed)" in source
    assert "write_results(args.out, results, eval_seeds)" in source


def test_paper_mpc_benchmark_sidecar_contains_seed_aggregates() -> None:
    source = SCRIPT.read_text()

    assert "summarize_results(results, eval_seeds)" in source
    assert '"success_rate"' in source
    assert '"std"' in source
    assert "summary_path = out.with_name" in source


def test_contact_force_uses_the_function_argument_not_process_global_state() -> None:
    source = SCRIPT.read_text()

    assert "pair & robot_geoms" in source
    assert "robot_geobs_cache" not in source


def test_paper_mpc_benchmark_exposes_a_reproducible_sensor_noise_knob() -> None:
    source = SCRIPT.read_text()

    assert '"--joint-velocity-noise-std"' in source
    assert "joint_velocity_noise_std=joint_velocity_noise_std" in source
    assert '"joint_velocity_noise_std": float(joint_velocity_noise_std)' in source
