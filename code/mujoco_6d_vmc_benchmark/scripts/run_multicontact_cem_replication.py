#!/usr/bin/env python3
"""Fixed-policy independent replication for multi-contact CEM ESN vs VMC.

This is intentionally not a selection script: the CEM ESN checkpoint/budget
and VMC stiffness/budget were frozen by a prior validation procedure.  It only
runs those two policies once on a new, disjoint randomized fixture set.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_benchmark import TORQUE_LIMITS  # noqa: E402
from run_paper_mpc_benchmark import run_rollout  # noqa: E402
from vmc_compliance_baseline import SpringCarriageConfig, load_controller  # noqa: E402
from vmc_torque_baseline import VMCTorqueBaseline  # noqa: E402
from wbc_velocity_residual_env import VelocityResidualFixture  # noqa: E402


def ints(value: str) -> list[int]:
    values = list(dict.fromkeys(int(item.strip()) for item in value.split(",") if item.strip()))
    if not values:
        raise argparse.ArgumentTypeError("list cannot be empty")
    return values


def fixture(rng: np.random.Generator) -> VelocityResidualFixture:
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


def fixtures(seed: int, count: int) -> list[VelocityResidualFixture]:
    return [fixture(np.random.default_rng(np.uint64(seed) * 6151 + index + 1))
            for index in range(count)]


def aggregate(rows: list[dict]) -> dict:
    return {
        "count": len(rows),
        "success_rate": float(np.mean([bool(row["task_success"]) for row in rows])),
        "mean_at_grasp_err_mm": float(np.mean([float(row["at_grasp_err_mm"]) for row in rows])),
        "mean_peak_force_n": float(np.mean([float(row["obstacle_force_n"]) for row in rows])),
        "mean_peak_torque_nm": float(np.mean([float(row["peak_torque_nm"]) for row in rows])),
        "mean_contact_bout_count": float(np.mean([int(row["contact_bout_count"]) for row in rows])),
        "hard_limit_count": int(sum(bool(row["hard_limit"]) for row in rows)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--esn", type=Path, required=True)
    parser.add_argument("--esn-budget", type=float, default=0.05)
    parser.add_argument("--vmc-k", type=float, default=1.0)
    parser.add_argument("--vmc-budget", type=float, default=0.02)
    parser.add_argument("--seeds", type=ints, required=True)
    parser.add_argument("--fixture-count", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 0.0 < args.esn_budget <= 1.0 or not 0.0 < args.vmc_budget <= 1.0:
        raise SystemExit("budgets must be in (0,1]")
    if args.fixture_count < 1:
        raise SystemExit("fixture-count must be positive")

    esn = load_controller(args.esn)
    base = SpringCarriageConfig(k_translation_base=2.2, k_rotation_base=0.18)
    cfg = replace(base, k_translation_base=args.vmc_k,
                  k_rotation_base=base.k_rotation_base * args.vmc_k / base.k_translation_base)
    vmc = VMCTorqueBaseline(cfg, TORQUE_LIMITS * args.vmc_budget)
    esn_rows: list[dict] = []
    vmc_rows: list[dict] = []
    start = time.time()
    for seed in args.seeds:
        for index, fx in enumerate(fixtures(seed, args.fixture_count)):
            esn.reset()
            row = run_rollout(args.menagerie, fx, impactor_kind="multicontact_hand_proxy", controller=esn,
                              residual_scale=args.esn_budget, seed=seed, verbose_name=f"frozen_cem_esn/fx{index}")
            row["fixture_index"] = index
            esn_rows.append(row)
            row = run_rollout(args.menagerie, fx, impactor_kind="multicontact_hand_proxy", controller=vmc,
                              residual_scale=args.vmc_budget, seed=seed, verbose_name=f"frozen_vmc/fx{index}")
            row["fixture_index"] = index
            vmc_rows.append(row)
        print(f"[{time.time() - start:7.1f}s] seed {seed}: esn={aggregate(esn_rows)} vmc={aggregate(vmc_rows)}", flush=True)
    output = {
        "schema_version": 1,
        "protocol": "independent_fixed_policy_replication_multicontact_cem_esn_vs_validation_selected_vmc",
        "status": "confirmatory_replication_no_reselection_or_retraining",
        "algorithm": "frozen multi-contact multi-scale Direct ESN with train-only CEM output-row gains",
        "observation_contract": "q, qdot, nominal_twist, pose_error, wbc_twist_error only; no force, apparatus, obstacle, direction label, timing, or future-release input",
        "fixture_generator": "fixture(seed*6151 + fixture_index + 1)",
        "seeds": args.seeds, "fixture_count_per_seed": args.fixture_count,
        "frozen_esn": {"path": str(args.esn), "budget": args.esn_budget},
        "frozen_vmc": {"k": args.vmc_k, "budget": args.vmc_budget},
        "summary": {"esn": aggregate(esn_rows), "vmc": aggregate(vmc_rows)},
        "rows": esn_rows + vmc_rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"elapsed_s": time.time() - start, "summary": output["summary"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
