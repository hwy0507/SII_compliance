#!/usr/bin/env python3
"""Fresh validation/test selection for multi-contact CEM ESN versus VMC.

Both Direct-ESN candidates are already frozen before validation.  Their
training-only CEM seeds must be disjoint from the validation/test seeds.  VMC
selects stiffness and residual budget independently on validation; only the
two family winners run once on held-out fixtures.
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


def floats(value: str) -> list[float]:
    values = list(dict.fromkeys(float(item.strip()) for item in value.split(",") if item.strip()))
    if not values or any(not np.isfinite(item) or item <= 0.0 for item in values):
        raise argparse.ArgumentTypeError("list must contain positive finite values")
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


def score(summary: dict) -> tuple[float, float]:
    return summary["success_rate"], -summary["mean_at_grasp_err_mm"]


def eval_esn(menagerie: Path, model: Path, budget: float, seeds: list[int], count: int, label: str) -> list[dict]:
    controller = load_controller(model)
    rows: list[dict] = []
    for seed in seeds:
        for index, fx in enumerate(fixtures(seed, count)):
            controller.reset()
            row = run_rollout(menagerie, fx, impactor_kind="multicontact_hand_proxy", controller=controller,
                              residual_scale=budget, seed=seed, verbose_name=f"{label}/fx{index}")
            row["fixture_index"] = index
            rows.append(row)
    return rows


def eval_vmc(menagerie: Path, k: float, budget: float, seeds: list[int], count: int, label: str) -> list[dict]:
    base = SpringCarriageConfig(k_translation_base=2.2, k_rotation_base=0.18)
    cfg = replace(base, k_translation_base=k, k_rotation_base=base.k_rotation_base * k / base.k_translation_base)
    rows: list[dict] = []
    for seed in seeds:
        for index, fx in enumerate(fixtures(seed, count)):
            row = run_rollout(menagerie, fx, impactor_kind="multicontact_hand_proxy",
                              controller=VMCTorqueBaseline(cfg, TORQUE_LIMITS * budget),
                              residual_scale=budget, seed=seed, verbose_name=f"{label}/fx{index}")
            row["fixture_index"] = index
            rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--esn-parent", type=Path, required=True)
    parser.add_argument("--esn-cem", type=Path, required=True)
    parser.add_argument("--esn-budget", type=float, default=0.05)
    parser.add_argument("--validation-seeds", type=ints, required=True)
    parser.add_argument("--test-seeds", type=ints, required=True)
    parser.add_argument("--fixture-count", type=int, default=4)
    parser.add_argument("--vmc-budgets", type=floats, default=[0.02, 0.03, 0.05])
    parser.add_argument("--vmc-k-values", type=floats, default=[1.0, 1.5, 2.2, 3.2])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 0.0 < args.esn_budget <= 1.0:
        raise SystemExit("esn-budget must be in (0,1]")
    if args.fixture_count < 1 or set(args.validation_seeds) & set(args.test_seeds):
        raise SystemExit("fixture-count must be positive and validation/test seeds disjoint")

    started = time.time()
    esn_candidates: list[dict] = []
    for name, model in (("multiscale_bc_parent", args.esn_parent), ("multiscale_cem", args.esn_cem)):
        rows = eval_esn(args.menagerie, model, args.esn_budget, args.validation_seeds, args.fixture_count, name + "_validation")
        summary = aggregate(rows)
        esn_candidates.append({"model": name, "path": str(model), "budget": args.esn_budget, "summary": summary})
        print(f"[{time.time() - started:7.1f}s] {name}: {summary}", flush=True)
    vmc_candidates: list[dict] = []
    for k in args.vmc_k_values:
        for budget in args.vmc_budgets:
            summary = aggregate(eval_vmc(args.menagerie, k, budget, args.validation_seeds, args.fixture_count,
                                         f"vmc_k{k:g}_b{budget:g}_validation"))
            vmc_candidates.append({"k": k, "budget": budget, "summary": summary})
            print(f"[{time.time() - started:7.1f}s] vmc k{k:g} b{budget:g}: {summary}", flush=True)
    selected_esn = max(esn_candidates, key=lambda item: score(item["summary"]))
    selected_vmc = max(vmc_candidates, key=lambda item: score(item["summary"]))
    print("selected", json.dumps({"esn": selected_esn, "vmc": selected_vmc}, indent=2), flush=True)
    esn_rows = eval_esn(args.menagerie, Path(selected_esn["path"]), selected_esn["budget"], args.test_seeds,
                        args.fixture_count, "selected_esn_test")
    vmc_rows = eval_vmc(args.menagerie, selected_vmc["k"], selected_vmc["budget"], args.test_seeds,
                        args.fixture_count, "selected_vmc_test")
    output = {
        "schema_version": 1,
        "protocol": "multicontact_multiscale_esn_train_only_cem_then_validation_selection_then_heldout",
        "status": "confirmatory_after_train_only_cem",
        "algorithm": "frozen 32-D observation/multi-scale reservoir; CEM optimizes seven bounded output-row gains only",
        "observation_contract": "q, qdot, nominal_twist, pose_error, wbc_twist_error only; no force, apparatus, obstacle, direction label, timing, or future-release input",
        "selection_rule": ["maximize validation task_success rate", "break ties with minimum validation at-grasp error"],
        "validation_seeds": args.validation_seeds, "test_seeds": args.test_seeds,
        "fixture_count_per_seed": args.fixture_count, "fixture_generator": "fixture(seed*6151 + fixture_index + 1)",
        "esn_candidates": esn_candidates, "vmc_candidates": vmc_candidates,
        "selected": {"esn": selected_esn, "vmc": selected_vmc},
        "test_summary": {"esn": aggregate(esn_rows), "vmc": aggregate(vmc_rows)},
        "test_rows": esn_rows + vmc_rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"elapsed_s": time.time() - started, "selected": output["selected"],
                      "test_summary": output["test_summary"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
