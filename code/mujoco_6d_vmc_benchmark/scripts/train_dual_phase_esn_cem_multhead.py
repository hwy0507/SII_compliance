#!/usr/bin/env python3
"""Train an independent multi-head ESN with constrained CEM search.

The only trainable object is the readout of a fixed ESN reservoir.  Each
candidate is evaluated in the same MuJoCo dual-board development conditions;
no VMC checkpoint, action, trace, or parameter is opened.  The objective is
lexicographic in the physical audit and lift floor before it considers
collision softness, preventing a candidate from winning by simply avoiding a
required board contact.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from direct_esn_compliance import MultiHeadDirectESNController, DirectESNConfig
from evaluate_dual_phase_robustness import RobustCondition, run_one, selected_conditions


def make_readout_basis(model: MultiHeadDirectESNController, dimension: int, seed: int) -> np.ndarray:
    if dimension < 1:
        raise ValueError("basis dimension must be positive")
    rng = np.random.default_rng(seed)
    basis = rng.standard_normal((len(model.HEAD_NAMES), dimension, 7, model.feature_dimension))
    norms = np.linalg.norm(basis.reshape(len(model.HEAD_NAMES), dimension, -1), axis=2)
    basis /= norms[:, :, None, None]
    return basis


def controller_from_theta(
    config: DirectESNConfig, basis: np.ndarray, theta: np.ndarray, readout_scale: float,
) -> MultiHeadDirectESNController:
    model = MultiHeadDirectESNController(config)
    heads = float(readout_scale) * np.einsum("hd,hdxy->hxy", theta, basis)
    model.set_readout_heads(heads)
    return model


def row_cost(row: dict[str, object], lift_floor_m: float) -> float:
    """Five-metric softness cost with explicit infeasibility penalties."""

    pre, post = row["pregrasp"], row["postgrasp"]
    assert isinstance(pre, dict) and isinstance(post, dict)
    if not bool(row["physical_audit_pass"]):
        missing = int(not bool(pre["contact"])) + int(not bool(post["contact"]))
        penetration = 1000.0 * max(float(pre["max_penetration_m"]), float(post["max_penetration_m"]))
        return 100.0 + 20.0 * missing + min(80.0, 5.0 * penetration)
    lift_deficit = max(0.0, lift_floor_m - float(row["final_target_lift_m"]))
    if lift_deficit > 0.0:
        return 80.0 + 20.0 * lift_deficit / 0.010
    return float(
        float(pre["peak_force_n"]) / 30.0
        + float(pre["contact_impulse_ns"]) / 7.0
        + float(post["peak_force_n"]) / 8.0
        + float(post["contact_impulse_ns"]) / 0.7
        + float(row["peak_jerk_mps3"]) / 1400.0
    )


def evaluate_theta(
    config: DirectESNConfig, basis: np.ndarray, theta: np.ndarray, readout_scale: float,
    conditions: tuple[RobustCondition, ...], budget: float, menagerie: Path, label: str,
    lift_floor_m: float,
) -> tuple[tuple[int, int, float, float], list[dict[str, object]]]:
    controller = controller_from_theta(config, basis, theta, readout_scale)
    rows = [run_one(menagerie, label, controller, condition, budget=budget) for condition in conditions]
    physical_count = int(sum(bool(row["physical_audit_pass"]) for row in rows))
    lift_count = int(sum(
        bool(row["physical_audit_pass"]) and float(row["final_target_lift_m"]) >= lift_floor_m
        for row in rows
    ))
    costs = np.asarray([row_cost(row, lift_floor_m) for row in rows], dtype=float)
    # CVaR-like tail objective: the upper quartile matters after the hard
    # constraints, so one easy condition cannot hide a difficult one.
    cvar = float(np.mean(costs[costs >= np.quantile(costs, 0.75)]))
    mean_cost = float(np.mean(costs))
    rank = (physical_count, lift_count, -cvar, -mean_cost)
    return rank, rows


def scalar_rank(rank: tuple[int, int, float, float], count: int) -> float:
    return float(1000.0 * rank[0] + 100.0 * rank[1] + rank[2] + 0.1 * rank[3] - 1000.0 * count)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--budget", type=float, default=0.04)
    parser.add_argument("--iterations", type=int, default=6)
    parser.add_argument("--population", type=int, default=16)
    parser.add_argument("--elite-count", type=int, default=6)
    parser.add_argument("--basis-dimension", type=int, default=24)
    parser.add_argument("--initial-sigma", type=float, default=0.55)
    parser.add_argument("--min-sigma", type=float, default=0.08)
    parser.add_argument("--readout-scale", type=float, default=0.28)
    parser.add_argument("--reservoir-size", type=int, default=240)
    parser.add_argument("--spectral-radius", type=float, default=0.94)
    parser.add_argument("--input-scale", type=float, default=0.45)
    parser.add_argument("--time-constant", type=float, default=0.08)
    parser.add_argument("--yield-smoothing-alpha", type=float, default=0.85)
    parser.add_argument("--lift-floor-mm", type=float, default=195.0)
    parser.add_argument("--seed", type=int, default=20268401)
    parser.add_argument("--train-split", choices=("v4_development",), default="v4_development")
    args = parser.parse_args()
    if min(args.iterations, args.population, args.elite_count, args.basis_dimension, args.reservoir_size) < 1:
        raise ValueError("iteration/population/elite/basis/reservoir parameters must be positive")
    if args.elite_count > args.population or args.min_sigma <= 0.0 or args.initial_sigma <= 0.0:
        raise ValueError("elite count and CEM sigmas are invalid")
    if not 0.0 < args.budget <= 1.0 or args.lift_floor_mm <= 0.0:
        raise ValueError("budget and lift floor must be positive")
    conditions = selected_conditions(args.train_split)
    if not conditions or any(item.split != args.train_split for item in conditions):
        raise RuntimeError("training is restricted to the predeclared development split")
    config = DirectESNConfig(
        reservoir_size=args.reservoir_size, spectral_radius=args.spectral_radius,
        input_scale=args.input_scale, time_constant_s=args.time_constant,
        yield_smoothing_alpha=args.yield_smoothing_alpha, seed=args.seed,
    )
    zero = MultiHeadDirectESNController(config)
    basis = make_readout_basis(zero, args.basis_dimension, args.seed + 1)
    theta = np.zeros((len(zero.HEAD_NAMES), args.basis_dimension), dtype=float)
    sigma = float(args.initial_sigma)
    rng = np.random.default_rng(args.seed + 2)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    floor_m = args.lift_floor_mm / 1000.0
    best_rank, best_rows = evaluate_theta(
        config, basis, theta, args.readout_scale, conditions, args.budget,
        args.menagerie, "ESN_cem_multhead_zero", floor_m,
    )
    best_theta = theta.copy()
    records: list[dict[str, object]] = []
    print(json.dumps({"iteration": -1, "rank": best_rank, "best": best_rank}, default=float), flush=True)
    for iteration in range(args.iterations):
        candidates = [theta.copy()]
        if args.population > 1:
            candidates.extend(theta + sigma * rng.standard_normal(theta.shape) for _ in range(args.population - 1))
        evaluations: list[tuple[tuple[int, int, float, float], np.ndarray, list[dict[str, object]]]] = []
        for index, candidate in enumerate(candidates):
            candidate = np.clip(candidate, -3.0, 3.0)
            rank, rows = evaluate_theta(
                config, basis, candidate, args.readout_scale, conditions, args.budget,
                args.menagerie, f"ESN_cem_multhead_{iteration:02d}_{index:02d}", floor_m,
            )
            evaluations.append((rank, candidate, rows))
        evaluations.sort(key=lambda item: item[0], reverse=True)
        elites = evaluations[:args.elite_count]
        elite_theta = np.asarray([item[1] for item in elites])
        theta = np.mean(elite_theta, axis=0)
        empirical_sigma = np.std(elite_theta, axis=0)
        # Keep exploration alive in dimensions that happen to agree across a
        # small elite set, while allowing rapid concentration elsewhere.
        sigma = max(args.min_sigma, float(0.75 * sigma + 0.25 * np.mean(empirical_sigma)))
        if evaluations[0][0] > best_rank:
            best_rank, best_theta, best_rows = evaluations[0][0], evaluations[0][1].copy(), evaluations[0][2]
        record = {
            "iteration": iteration, "sigma": sigma, "best_rank": best_rank,
            "generation_best_rank": evaluations[0][0], "elite_ranks": [item[0] for item in elites],
            "best_physical_audit": [bool(row["physical_audit_pass"]) for row in best_rows],
            "best_lift_mm": [1000.0 * float(row["final_target_lift_m"]) for row in best_rows],
        }
        records.append(record)
        print(json.dumps(record, default=float), flush=True)
    final = controller_from_theta(config, basis, best_theta, args.readout_scale)
    model_path = args.out_dir / "esn_cem_multhead_independent_best.npz"
    final.save_npz(model_path)
    summary = {
        "schema_version": 1,
        "method": "independent_direct_esn_cem_multhead",
        "status": "development_only_not_confirmatory",
        "training_source": "own MuJoCo rollout physical audit and softness metrics only; no VMC checkpoint, trace, action, or parameter was read",
        "student_observation_contract": final.contract()["student_input_fields"],
        "forbidden_online_inputs": final.contract()["forbidden_online_inputs"],
        "phase_gate_contract": final.contract()["phase_gate"],
        "training_split": args.train_split,
        "training_conditions": [asdict(item) for item in conditions],
        "config": asdict(config),
        "cem": {key: getattr(args, key) for key in (
            "iterations", "population", "elite_count", "basis_dimension",
            "initial_sigma", "min_sigma", "readout_scale", "seed",
        )},
        "lift_floor_mm": args.lift_floor_mm,
        "best_rank": best_rank,
        "best_physical_audit": [bool(row["physical_audit_pass"]) for row in best_rows],
        "best_final_lift_mm": [1000.0 * float(row["final_target_lift_m"]) for row in best_rows],
        "best_theta": best_theta.tolist(), "model": str(model_path), "iterations": records,
    }
    summary_path = args.out_dir / "cem_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=float) + "\n", encoding="utf-8")
    print(json.dumps({"model": str(model_path), "summary": str(summary_path), "best_rank": best_rank}, default=float, indent=2))


if __name__ == "__main__":
    main()
