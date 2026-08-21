#!/usr/bin/env python3
"""Train-only safe CEM policy improvement for a multi-contact Direct ESN.

The controller's 32-D deployed observation, fixed multi-scale reservoir,
nominal PaperMPC controller, residual-torque budget, and FR3 safety limits are
unchanged.  CEM only learns seven bounded multiplicative gains applied to the
linear readout rows.  Physical contact properties appear only while MuJoCo
generates train-only rollouts/rewards, never as policy inputs.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_paper_mpc_benchmark import run_rollout  # noqa: E402
from vmc_compliance_baseline import load_controller  # noqa: E402
from wbc_velocity_residual_env import VelocityResidualFixture  # noqa: E402


def parse_ints(value: str) -> list[int]:
    values = list(dict.fromkeys(int(item.strip()) for item in value.split(",") if item.strip()))
    if not values:
        raise argparse.ArgumentTypeError("list cannot be empty")
    return values


def hand_fixture(rng: np.random.Generator) -> VelocityResidualFixture:
    """Random physical hand-proxy contact; its parameters remain hidden."""

    return VelocityResidualFixture(
        rod_stroke_m=float(rng.uniform(0.160, 0.176)),
        rod_height_m=float(rng.uniform(0.539, 0.542)),
        rod_start_time_s=float(rng.uniform(0.90, 1.03)),
        rod_approach_side="positive_y", impactor_type="hand_proxy", rod_cycles=2,
        cycle_period_s=float(rng.uniform(0.66, 0.72)),
        impactor_mass_kg=float(rng.uniform(0.18, 0.50)),
        rod_slide_damping=float(rng.uniform(0.6, 4.0)),
        rod_driver_kp=float(rng.uniform(2500.0, 9000.0)),
        rod_driver_force_limit_n=float(rng.uniform(150.0, 300.0)),
        contact_time_constant_s=float(rng.uniform(0.008, 0.025)),
    )


def fixtures_for_seed(seed: int, count: int) -> list[VelocityResidualFixture]:
    return [hand_fixture(np.random.default_rng(np.uint64(seed) * 6151 + index + 1))
            for index in range(count)]


def summarize(rows: list[dict]) -> dict:
    return {
        "count": len(rows),
        "success_rate": float(np.mean([bool(row["task_success"]) for row in rows])),
        "mean_at_grasp_err_mm": float(np.mean([float(row["at_grasp_err_mm"]) for row in rows])),
        "mean_peak_force_n": float(np.mean([float(row["obstacle_force_n"]) for row in rows])),
        "mean_peak_torque_nm": float(np.mean([float(row["peak_torque_nm"]) for row in rows])),
        "mean_contact_bout_count": float(np.mean([int(row["contact_bout_count"]) for row in rows])),
        "hard_limit_count": int(sum(bool(row["hard_limit"]) for row in rows)),
    }


def objective(summary: dict) -> float:
    """Success dominates; safety/efficiency terms only separate candidates."""

    return (1000.0 * summary["success_rate"] - summary["mean_at_grasp_err_mm"]
            - 0.020 * summary["mean_peak_force_n"]
            - 0.050 * summary["mean_peak_torque_nm"]
            - 0.100 * summary["mean_contact_bout_count"]
            - 200.0 * summary["hard_limit_count"])


def apply_log_gains(controller, parent_readout: np.ndarray, log_gains: np.ndarray) -> np.ndarray:
    gains = np.asarray(log_gains, dtype=float)
    if gains.shape != (7,) or not np.all(np.isfinite(gains)):
        raise ValueError("log-gains must be a finite seven-vector")
    factors = np.exp(np.clip(gains, -0.75, 0.75))
    controller.set_readout(parent_readout * factors[:, None])
    return factors


def evaluate(model_path: Path, parent_readout: np.ndarray, log_gains: np.ndarray,
             menagerie: Path, budget: float, seeds: list[int], fixture_count: int,
             label: str) -> tuple[dict, list[dict], np.ndarray]:
    controller = load_controller(model_path)
    factors = apply_log_gains(controller, parent_readout, log_gains)
    rows: list[dict] = []
    for seed in seeds:
        for fixture_index, fixture in enumerate(fixtures_for_seed(seed, fixture_count)):
            row = run_rollout(
                menagerie, fixture, impactor_kind="multicontact_hand_proxy", controller=controller,
                residual_scale=budget, seed=seed, verbose_name=f"{label}/fx{fixture_index}",
            )
            row["fixture_index"] = fixture_index
            rows.append(row)
    return summarize(rows), rows, factors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--base-esn", type=Path, required=True)
    parser.add_argument("--budget", type=float, default=0.05)
    parser.add_argument("--train-seeds", type=parse_ints, required=True)
    parser.add_argument("--fixture-count", type=int, default=2)
    parser.add_argument("--iterations", type=int, default=6)
    parser.add_argument("--population", type=int, default=16)
    parser.add_argument("--elite-count", type=int, default=5)
    parser.add_argument("--initial-std", type=float, default=0.18)
    parser.add_argument("--minimum-std", type=float, default=0.035)
    parser.add_argument("--rng-seed", type=int, default=20261471)
    parser.add_argument("--out-model", type=Path, required=True)
    parser.add_argument("--out-summary", type=Path, required=True)
    args = parser.parse_args()
    if not 0.0 < args.budget <= 1.0:
        raise SystemExit("budget must be in (0, 1]")
    if args.fixture_count < 1 or args.iterations < 1 or args.population < 2:
        raise SystemExit("fixture-count, iterations, and population must be positive")
    if not 1 <= args.elite_count < args.population:
        raise SystemExit("elite-count must be in [1, population)")
    if min(args.initial_std, args.minimum_std) <= 0.0:
        raise SystemExit("standard deviations must be positive")

    parent = load_controller(args.base_esn)
    if not hasattr(parent, "readout_copy") or not hasattr(parent, "set_readout"):
        raise SystemExit("base-esn must be a Direct ESN checkpoint")
    parent_readout = parent.readout_copy()
    rng = np.random.default_rng(args.rng_seed)
    mean = np.zeros(7)
    std = np.full(7, args.initial_std)
    best = {"objective": -np.inf, "log_gains": np.zeros(7), "summary": None,
            "rows": None, "factors": None}
    history: list[dict] = []
    started = time.time()

    for iteration in range(args.iterations):
        candidates = [np.zeros(7)]
        candidates.extend(np.clip(mean + rng.normal(size=(args.population - 1, 7)) * std, -0.75, 0.75))
        scored: list[dict] = []
        for index, gains in enumerate(candidates):
            summary, rows, factors = evaluate(
                args.base_esn, parent_readout, gains, args.menagerie, args.budget,
                args.train_seeds, args.fixture_count, f"cem_i{iteration}_c{index}",
            )
            value = objective(summary)
            record = {"candidate": index, "log_gains": gains.tolist(), "gain_factors": factors.tolist(),
                      "objective": value, "summary": summary}
            scored.append(record)
            if value > best["objective"]:
                best = {"objective": value, "log_gains": gains.copy(), "summary": summary,
                        "rows": rows, "factors": factors.copy()}
        scored.sort(key=lambda item: item["objective"], reverse=True)
        elite = np.asarray([item["log_gains"] for item in scored[:args.elite_count]])
        mean = np.mean(elite, axis=0)
        std = np.maximum(np.std(elite, axis=0), args.minimum_std)
        history.append({"iteration": iteration, "elite": scored[:args.elite_count],
                        "distribution_mean": mean.tolist(), "distribution_std": std.tolist(),
                        "best_so_far_objective": best["objective"]})
        print(json.dumps({"elapsed_s": round(time.time() - started, 2), "iteration": iteration,
                          "elite_objectives": [round(x["objective"], 6) for x in scored[:args.elite_count]],
                          "best_so_far": round(best["objective"], 6), "mean": mean.tolist()}), flush=True)

    final = load_controller(args.base_esn)
    factors = apply_log_gains(final, parent_readout, best["log_gains"])
    args.out_model.parent.mkdir(parents=True, exist_ok=True)
    args.out_summary.parent.mkdir(parents=True, exist_ok=True)
    final.save_npz(args.out_model)
    output = {
        "schema_version": 1,
        "method": "multicontact_multiscale_direct_esn_safe_readout_cem",
        "status": "training_only_not_a_heldout_claim",
        "base_esn": str(args.base_esn), "output_model": str(args.out_model), "budget": args.budget,
        "observation_contract": "q, qdot, nominal_twist, pose_error, wbc_twist_error only",
        "forbidden_inputs": "contact force; apparatus parameters; obstacle pose/velocity/geometry; contact direction label; pulse timing/count; future release",
        "optimization_space": "seven bounded log-gains applied to frozen multi-scale ESN linear-readout output rows",
        "safety_contract": "same torque-residual budget and FR3 hard torque limits as base ESN/VMC",
        "objective": "1000*success_rate - grasp_error_mm - .02*peak_force_N - .05*peak_torque_Nm - .1*contact_bouts - 200*hard_limits",
        "train_contact_distribution": "positive_y finite-mass ellipsoidal hand_proxy on damped force-limited MuJoCo slide",
        "train_seeds": args.train_seeds, "fixture_count": args.fixture_count,
        "fixture_generator": "hand_fixture(seed*6151 + fixture_index + 1)",
        "cem": {"iterations": args.iterations, "population_including_parent": args.population,
                "elite_count": args.elite_count, "initial_std": args.initial_std,
                "minimum_std": args.minimum_std, "rng_seed": args.rng_seed},
        "selected_log_gains": best["log_gains"].tolist(), "selected_gain_factors": factors.tolist(),
        "train_summary": best["summary"], "train_rows": best["rows"], "history": history,
    }
    args.out_summary.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"out_model": str(args.out_model), "train_summary": best["summary"],
                      "gain_factors": factors.tolist()}, indent=2), flush=True)


if __name__ == "__main__":
    main()
