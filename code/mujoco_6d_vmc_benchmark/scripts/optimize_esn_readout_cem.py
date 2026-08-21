#!/usr/bin/env python3
"""Safe simulation policy improvement for a frozen Direct-ESN readout.

The reservoir, its deployable 32-D observation contract, the PaperMPC nominal
controller, and the residual-torque safety envelope stay frozen.  Starting
from a behavior-cloned Direct ESN, this script optimizes just seven bounded
log-gains on the output rows using cross-entropy method (CEM) rollouts in
MuJoCo.  It therefore optimizes task behaviour rather than copying a VMC
teacher action more accurately, while adding no force, apparatus-parameter,
obstacle, phase, or future-release input to the policy.

This is a training-only tool.  Its fixture seeds must never overlap with the
validation or held-out test seeds used to make a method claim.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from record_contact_apparatus_traces import train_fixture  # noqa: E402
from run_paper_mpc_benchmark import run_rollout  # noqa: E402
from vmc_compliance_baseline import load_controller  # noqa: E402


def parse_int_list(value: str) -> list[int]:
    values = list(dict.fromkeys(int(item.strip()) for item in value.split(",") if item.strip()))
    if not values:
        raise argparse.ArgumentTypeError("list cannot be empty")
    return values


def fixtures_for_seed(seed: int, count: int) -> list:
    """Draw deterministic, manifest-recoverable physical apparatus fixtures."""

    return [train_fixture(np.random.default_rng(np.uint64(seed) * 1009 + index + 1))
            for index in range(count)]


def apply_log_gains(controller, base_readout: np.ndarray, log_gains: np.ndarray) -> np.ndarray:
    """Apply bounded per-output gains to an ESN's linear readout.

    A gain scales the complete state-dependent output row.  Thus it changes
    the ESN's learned time-history response, not its observation set or the
    residual torque limit.  Exponential parameterization keeps every channel
    orientation unchanged and makes zero the exact BC parent policy.
    """

    gains = np.asarray(log_gains, dtype=float)
    if gains.shape != (7,) or not np.all(np.isfinite(gains)):
        raise ValueError("log_gains must be a finite seven-vector")
    factors = np.exp(np.clip(gains, -0.75, 0.75))
    controller.set_readout(base_readout * factors[:, None])
    return factors


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
    """Lexicographic-like scalar for CEM; success dominates all soft terms."""

    return (
        1000.0 * summary["success_rate"]
        - summary["mean_at_grasp_err_mm"]
        - 0.020 * summary["mean_peak_force_n"]
        - 0.050 * summary["mean_peak_torque_nm"]
        - 0.100 * summary["mean_contact_bout_count"]
        - 200.0 * summary["hard_limit_count"]
    )


def evaluate(model_path: Path, base_readout: np.ndarray, log_gains: np.ndarray,
             menagerie: Path, budget: float, seeds: list[int], fixture_count: int,
             label: str) -> tuple[dict, list[dict], np.ndarray]:
    controller = load_controller(model_path)
    factors = apply_log_gains(controller, base_readout, log_gains)
    rows: list[dict] = []
    for seed in seeds:
        for fixture_index, fixture in enumerate(fixtures_for_seed(seed, fixture_count)):
            row = run_rollout(
                menagerie, fixture, impactor_kind="apparatus_rod", controller=controller,
                residual_scale=budget, seed=seed, verbose_name=f"{label}/fx{fixture_index}",
            )
            row["fixture_index"] = fixture_index
            rows.append(row)
    return summarize(rows), rows, factors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--base-esn", type=Path, required=True,
                        help="behavior-cloned ESN checkpoint used only as readout initialization")
    parser.add_argument("--budget", type=float, required=True)
    parser.add_argument("--train-seeds", type=parse_int_list, required=True)
    parser.add_argument("--fixture-count", type=int, default=2)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--population", type=int, default=12)
    parser.add_argument("--elite-count", type=int, default=4)
    parser.add_argument("--initial-std", type=float, default=0.18)
    parser.add_argument("--minimum-std", type=float, default=0.035)
    parser.add_argument("--rng-seed", type=int, default=20261071)
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
        raise SystemExit("--base-esn must be a Direct ESN checkpoint")
    base_readout = parent.readout_copy()
    if base_readout.shape[0] != 7:
        raise SystemExit("unexpected Direct ESN action dimension")

    rng = np.random.default_rng(args.rng_seed)
    mean = np.zeros(7, dtype=float)
    std = np.full(7, args.initial_std, dtype=float)
    history: list[dict] = []
    best = {"objective": -np.inf, "log_gains": np.zeros(7), "summary": None, "rows": None, "factors": None}
    started = time.time()

    # The exact BC parent is evaluated in every iteration.  It prevents noisy
    # simulator optimization from silently replacing a good readout by a worse
    # sample and makes the improvement trace auditable.
    for iteration in range(args.iterations):
        candidates = [np.zeros(7, dtype=float)]
        candidates.extend(np.clip(
            mean + rng.normal(size=(args.population - 1, 7)) * std,
            -0.75, 0.75,
        ))
        scored = []
        for index, gains in enumerate(candidates):
            summary, rows, factors = evaluate(
                args.base_esn, base_readout, gains, args.menagerie, args.budget,
                args.train_seeds, args.fixture_count, f"cem_i{iteration}_c{index}",
            )
            value = objective(summary)
            record = {
                "candidate": index, "log_gains": gains.tolist(), "gain_factors": factors.tolist(),
                "objective": value, "summary": summary,
            }
            scored.append(record)
            if value > best["objective"]:
                best = {"objective": value, "log_gains": gains.copy(), "summary": summary,
                        "rows": rows, "factors": factors.copy()}
        scored.sort(key=lambda item: item["objective"], reverse=True)
        elite = np.asarray([item["log_gains"] for item in scored[:args.elite_count]], dtype=float)
        mean = np.mean(elite, axis=0)
        std = np.maximum(np.std(elite, axis=0), args.minimum_std)
        history.append({
            "iteration": iteration, "elite": scored[:args.elite_count],
            "distribution_mean": mean.tolist(), "distribution_std": std.tolist(),
            "best_so_far_objective": best["objective"],
        })
        print(json.dumps({
            "elapsed_s": round(time.time() - started, 2), "iteration": iteration,
            "elite_objectives": [round(item["objective"], 6) for item in scored[:args.elite_count]],
            "best_so_far": round(best["objective"], 6), "mean": mean.tolist(),
        }), flush=True)

    final = load_controller(args.base_esn)
    final_factors = apply_log_gains(final, base_readout, best["log_gains"])
    args.out_model.parent.mkdir(parents=True, exist_ok=True)
    args.out_summary.parent.mkdir(parents=True, exist_ok=True)
    final.save_npz(args.out_model)
    result = {
        "schema_version": 1,
        "method": "direct_esn_safe_readout_cem_policy_improvement",
        "status": "training_only_not_a_heldout_claim",
        "base_esn": str(args.base_esn),
        "output_model": str(args.out_model),
        "budget": args.budget,
        "observation_contract": "q, qdot, nominal_twist, pose_error, wbc_twist_error only",
        "forbidden_inputs": "contact force; apparatus parameters; obstacle pose/velocity; pulse timing/count; future release",
        "optimization_space": "seven bounded log-gains applied to frozen ESN linear-readout output rows",
        "safety_contract": "same torque-residual budget and FR3 hard torque limits as base ESN/VMC",
        "objective": "1000*success_rate - grasp_error_mm - .02*peak_force_N - .05*peak_torque_Nm - .1*contact_bouts - 200*hard_limits",
        "train_seeds": args.train_seeds,
        "fixture_count": args.fixture_count,
        "fixture_generator": "train_fixture(seed*1009 + fixture_index + 1)",
        "cem": {"iterations": args.iterations, "population_including_parent": args.population,
                "elite_count": args.elite_count, "initial_std": args.initial_std,
                "minimum_std": args.minimum_std, "rng_seed": args.rng_seed},
        "selected_log_gains": best["log_gains"].tolist(),
        "selected_gain_factors": final_factors.tolist(),
        "train_summary": best["summary"],
        "train_rows": best["rows"],
        "history": history,
    }
    args.out_summary.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"out_model": str(args.out_model), "train_summary": best["summary"],
                      "gain_factors": final_factors.tolist()}, indent=2), flush=True)


if __name__ == "__main__":
    main()
