#!/usr/bin/env python3
"""Train an independent Direct ESN by MuJoCo antithetic policy search.

This is the proposed-method training path for the dual-board task.  It starts
with a zero ESN readout and never opens a VMC checkpoint, VMC teacher trace,
or VMC action.  The fixed recurrent reservoir is a temporal feature map; a
low-dimensional, deterministic basis parameterizes its readout.  Antithetic
random-search updates that readout solely from scalar returns of the ESN's own
MuJoCo rollouts.

Board/contact/object truth appears only inside the environment's *training
return*.  It is not in ``DirectESNController.act`` and never becomes a policy
feature.  Train conditions must be the predeclared development split from
``evaluate_dual_phase_robustness``; held-out conditions are forbidden here.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from direct_esn_compliance import DirectESNConfig, DirectESNController
from evaluate_dual_phase_robustness import RobustCondition, run_one, selected_conditions


def rollout_return(row: dict[str, object]) -> float:
    """Scalar training-only return with hard physical validity before softness.

    The policy never receives any item used below.  A policy cannot gain by
    avoiding either contact: the physical audit demands both intended contacts,
    a real grasp and carry, correct contact partners, no object-board contact,
    no reset overlap, finite state, and bounded penetration.
    """

    pre = row["pregrasp"]
    post = row["postgrasp"]
    assert isinstance(pre, dict) and isinstance(post, dict)
    if not bool(row["physical_audit_pass"]):
        missing = int(not bool(pre["contact"])) + int(not bool(post["contact"]))
        penetration_mm = 1000.0 * max(
            float(pre["max_penetration_m"]), float(post["max_penetration_m"]),
        )
        return float(-120.0 - 30.0 * missing - min(50.0, 5.0 * penetration_mm))
    normalized_cost = (
        float(pre["peak_force_n"]) / 30.0
        + float(pre["contact_impulse_ns"]) / 7.0
        + float(post["peak_force_n"]) / 8.0
        + float(post["contact_impulse_ns"]) / 0.7
        + float(row["peak_jerk_mps3"]) / 1400.0
    )
    # A physical-valid rollout earns 100 before its five declared softness
    # costs.  This scale makes failing the task worse than any plausible
    # improvement in a single contact metric.
    return float(100.0 - 16.0 * normalized_cost)


def make_readout_basis(
    model: DirectESNController, dimension: int, seed: int,
) -> np.ndarray:
    """Fixed orthonormal-ish search directions in the ESN readout space."""

    if dimension < 1:
        raise ValueError("basis dimension must be positive")
    rng = np.random.default_rng(seed)
    basis = rng.standard_normal((dimension, 7, model.feature_dimension))
    # Normalize each direction so ARS exploration scale is meaningful and does
    # not silently grow with reservoir size.
    basis /= np.linalg.norm(basis.reshape(dimension, -1), axis=1)[:, None, None]
    return basis


def controller_from_theta(
    config: DirectESNConfig, basis: np.ndarray, theta: np.ndarray, readout_scale: float,
) -> DirectESNController:
    model = DirectESNController(config)
    readout = float(readout_scale) * np.tensordot(theta, basis, axes=(0, 0))
    model.set_readout(readout)
    return model


def evaluate_theta(
    config: DirectESNConfig, basis: np.ndarray, theta: np.ndarray,
    readout_scale: float, conditions: tuple[RobustCondition, ...], budget: float,
    menagerie: Path, label: str,
) -> tuple[float, list[dict[str, object]]]:
    controller = controller_from_theta(config, basis, theta, readout_scale)
    rows = [run_one(menagerie, label, controller, condition, budget=budget) for condition in conditions]
    return float(np.mean([rollout_return(row) for row in rows])), rows


def choose_conditions(
    conditions: tuple[RobustCondition, ...], count: int, seed: int,
) -> tuple[RobustCondition, ...]:
    if not 1 <= count <= len(conditions):
        raise ValueError("conditions per direction must be in [1, train-condition count]")
    rng = np.random.default_rng(seed)
    indices = rng.choice(len(conditions), size=count, replace=False)
    return tuple(conditions[int(index)] for index in indices)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--budget", type=float, default=0.04)
    parser.add_argument("--iterations", type=int, default=8)
    parser.add_argument("--directions", type=int, default=8)
    parser.add_argument("--conditions-per-direction", type=int, default=2)
    parser.add_argument("--basis-dimension", type=int, default=32)
    parser.add_argument("--exploration-sigma", type=float, default=0.30)
    parser.add_argument("--learning-rate", type=float, default=0.18)
    parser.add_argument("--theta-clip", type=float, default=3.0)
    parser.add_argument("--readout-scale", type=float, default=0.24)
    parser.add_argument("--reservoir-size", type=int, default=240)
    parser.add_argument("--spectral-radius", type=float, default=0.94)
    parser.add_argument("--input-scale", type=float, default=0.45)
    parser.add_argument("--time-constant", type=float, default=0.08)
    parser.add_argument("--yield-smoothing-alpha", type=float, default=0.85)
    parser.add_argument("--seed", type=int, default=20266301)
    args = parser.parse_args()
    if min(args.iterations, args.directions, args.basis_dimension, args.reservoir_size) < 1:
        raise ValueError("iterations, directions, basis dimension and reservoir size must be positive")
    if min(args.exploration_sigma, args.learning_rate, args.theta_clip, args.readout_scale) <= 0.0:
        raise ValueError("ARS scales must be positive")
    if not 0.0 < args.budget <= 1.0:
        raise ValueError("budget must lie in (0, 1]")
    conditions = selected_conditions("development")
    if not conditions or any(item.split != "development" for item in conditions):
        raise RuntimeError("only predeclared development conditions may train the ESN")
    config = DirectESNConfig(
        reservoir_size=args.reservoir_size, spectral_radius=args.spectral_radius,
        input_scale=args.input_scale, time_constant_s=args.time_constant,
        yield_smoothing_alpha=args.yield_smoothing_alpha, seed=args.seed,
    )
    zero = DirectESNController(config)
    basis = make_readout_basis(zero, args.basis_dimension, args.seed + 1)
    theta = np.zeros(args.basis_dimension, dtype=float)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    initial_return, initial_rows = evaluate_theta(
        config, basis, theta, args.readout_scale, conditions, args.budget, args.menagerie, "ESN_zero_readout",
    )
    best_theta, best_return, best_rows = theta.copy(), initial_return, initial_rows
    records = []
    rng = np.random.default_rng(args.seed + 2)
    for iteration in range(args.iterations):
        directions = rng.standard_normal((args.directions, args.basis_dimension))
        directions /= np.linalg.norm(directions, axis=1)[:, None]
        plus_returns, minus_returns, direction_records = [], [], []
        for index, direction in enumerate(directions):
            # Every plus/minus pair sees exactly the same predeclared physical
            # conditions, providing a finite-difference estimate without VMC.
            pair_conditions = choose_conditions(
                conditions, args.conditions_per_direction,
                args.seed + 1009 * iteration + 37 * index,
            )
            plus_theta = np.clip(theta + args.exploration_sigma * direction, -args.theta_clip, args.theta_clip)
            minus_theta = np.clip(theta - args.exploration_sigma * direction, -args.theta_clip, args.theta_clip)
            plus_score, plus_rows = evaluate_theta(
                config, basis, plus_theta, args.readout_scale, pair_conditions,
                args.budget, args.menagerie, f"ESN_ars_{iteration:02d}_{index:02d}_plus",
            )
            minus_score, minus_rows = evaluate_theta(
                config, basis, minus_theta, args.readout_scale, pair_conditions,
                args.budget, args.menagerie, f"ESN_ars_{iteration:02d}_{index:02d}_minus",
            )
            plus_returns.append(plus_score)
            minus_returns.append(minus_score)
            direction_records.append({
                "conditions": [asdict(item) for item in pair_conditions],
                "plus_return": plus_score, "minus_return": minus_score,
                "plus_physical_audit_pass": [bool(row["physical_audit_pass"]) for row in plus_rows],
                "minus_physical_audit_pass": [bool(row["physical_audit_pass"]) for row in minus_rows],
            })
        all_returns = np.asarray([*plus_returns, *minus_returns], dtype=float)
        return_scale = max(float(np.std(all_returns)), 1.0)
        gradient = np.mean(
            (np.asarray(plus_returns) - np.asarray(minus_returns))[:, None] * directions,
            axis=0,
        ) / return_scale
        theta = np.clip(theta + args.learning_rate * gradient, -args.theta_clip, args.theta_clip)
        current_return, current_rows = evaluate_theta(
            config, basis, theta, args.readout_scale, conditions,
            args.budget, args.menagerie, f"ESN_ars_{iteration:02d}_mean",
        )
        if current_return > best_return:
            best_theta, best_return, best_rows = theta.copy(), current_return, current_rows
        record = {
            "iteration": iteration, "return_scale": return_scale,
            "mean_plus_return": float(np.mean(plus_returns)),
            "mean_minus_return": float(np.mean(minus_returns)),
            "mean_policy_return": current_return,
            "mean_policy_physical_audit_pass": [bool(row["physical_audit_pass"]) for row in current_rows],
            "best_return_so_far": best_return, "direction_records": direction_records,
        }
        records.append(record)
        print(json.dumps(record), flush=True)
    final = controller_from_theta(config, basis, best_theta, args.readout_scale)
    model_path = args.out_dir / "esn_ars_independent_best.npz"
    final.save_npz(model_path)
    summary = {
        "schema_version": 1,
        "method": "independent_direct_esn_antithetic_random_search",
        "status": "development_only_not_confirmatory",
        "training_source": "own MuJoCo rollout scalar returns only; no VMC checkpoint, trace, action, or parameter was read",
        "student_observation_contract": final.contract()["student_input_fields"],
        "forbidden_online_inputs": final.contract()["forbidden_online_inputs"],
        "training_conditions": [asdict(item) for item in conditions],
        "config": asdict(config),
        "ars": {key: getattr(args, key) for key in (
            "iterations", "directions", "conditions_per_direction", "basis_dimension",
            "exploration_sigma", "learning_rate", "theta_clip", "readout_scale", "seed",
        )},
        "initial_return": initial_return,
        "initial_physical_audit": [bool(row["physical_audit_pass"]) for row in initial_rows],
        "best_return": best_return,
        "best_physical_audit": [bool(row["physical_audit_pass"]) for row in best_rows],
        "best_theta": best_theta.tolist(), "model": str(model_path), "iterations": records,
    }
    summary_path = args.out_dir / "ars_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"model": str(model_path), "summary": str(summary_path), "best_return": best_return}, indent=2))


if __name__ == "__main__":
    main()
