#!/usr/bin/env python3
"""Run the pre-registered multi-contact MLP selection or four-method test.

The validation phase is intentionally restricted to predeclared MLP BC
candidates.  The PaperMPC, VMC, and CEM-ESN policies are frozen reference
methods and must not be reselected here.  The test phase evaluates exactly
one selected MLP and the three fixed methods on the same generated fixtures.
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

from mlp_compliance_baseline import MLPComplianceController  # noqa: E402
from run_benchmark import TORQUE_LIMITS  # noqa: E402
from run_paper_mpc_benchmark import run_rollout  # noqa: E402
from vmc_compliance_baseline import SpringCarriageConfig, load_controller  # noqa: E402
from vmc_torque_baseline import VMCTorqueBaseline  # noqa: E402
from wbc_velocity_residual_env import VelocityResidualFixture  # noqa: E402


def ints(value: str) -> list[int]:
    values = list(dict.fromkeys(int(part.strip()) for part in value.split(",") if part.strip()))
    if not values:
        raise argparse.ArgumentTypeError("seed list cannot be empty")
    return values


def candidate(value: str) -> tuple[str, Path]:
    name, sep, path = value.partition("=")
    if not sep or not name or not path:
        raise argparse.ArgumentTypeError("MLP candidate must be LABEL=PATH")
    return name, Path(path)


def fixture(rng: np.random.Generator) -> VelocityResidualFixture:
    """The frozen positive-y, finite-mass hand-proxy coverage distribution."""

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


def finite_stats(rows: list[dict], key: str) -> dict | None:
    values = np.asarray([float(row[key]) for row in rows if row.get(key) is not None and np.isfinite(float(row[key]))])
    if not len(values):
        return None
    return {"mean": float(values.mean()), "std": float(values.std(ddof=0)), "count": int(len(values)),
            "min": float(values.min()), "max": float(values.max())}


def aggregate(rows: list[dict]) -> dict:
    return {
        "count": len(rows),
        "success_count": int(sum(bool(row["task_success"]) for row in rows)),
        "success_rate": float(np.mean([bool(row["task_success"]) for row in rows])),
        "hard_limit_count": int(sum(bool(row["hard_limit"]) for row in rows)),
        "metrics": {key: finite_stats(rows, key) for key in (
            "at_grasp_err_mm", "peak_postimpact_err_mm", "obstacle_force_n", "peak_torque_nm",
            "contact_bout_count", "recovery_s")},
    }


def selection_score(summary: dict) -> tuple[int, float]:
    metric = summary["metrics"]["at_grasp_err_mm"]
    return summary["success_count"], -(metric["mean"] if metric is not None else float("inf"))


def run_method(menagerie: Path, method: str, controller, budget: float, seeds: list[int], count: int) -> list[dict]:
    rows: list[dict] = []
    for seed in seeds:
        for fixture_index, fx in enumerate(fixtures(seed, count)):
            if controller is not None and hasattr(controller, "reset"):
                controller.reset()
            row = run_rollout(
                menagerie, fx, impactor_kind="multicontact_hand_proxy", controller=controller,
                residual_scale=budget, seed=seed, verbose_name=f"{method}/fx{fixture_index}")
            row["method"] = method
            row["fixture_index"] = fixture_index
            row["residual_budget_fraction"] = budget
            rows.append(row)
    return rows


def make_vmc(k: float, budget: float) -> VMCTorqueBaseline:
    base = SpringCarriageConfig(k_translation_base=2.2, k_rotation_base=0.18)
    config = replace(base, k_translation_base=k,
                     k_rotation_base=base.k_rotation_base * k / base.k_translation_base)
    return VMCTorqueBaseline(config, TORQUE_LIMITS * budget)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("mlp-validation", "four-method-test"), required=True)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--seeds", type=ints, required=True)
    parser.add_argument("--fixture-count", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mlp-candidate", action="append", type=candidate, default=[])
    parser.add_argument("--mlp", type=Path)
    parser.add_argument("--mlp-label", default="mlp_bc_selected")
    parser.add_argument("--mlp-budget", type=float, default=0.05)
    parser.add_argument("--esn", type=Path)
    parser.add_argument("--esn-budget", type=float, default=0.05)
    parser.add_argument("--vmc-k", type=float, default=1.0)
    parser.add_argument("--vmc-budget", type=float, default=0.02)
    args = parser.parse_args()
    if args.fixture_count < 1:
        raise SystemExit("fixture-count must be positive")
    if any(not 0.0 < budget <= 1.0 for budget in (args.mlp_budget, args.esn_budget, args.vmc_budget)):
        raise SystemExit("all residual budgets must lie in (0, 1]")

    started = time.time()
    if args.phase == "mlp-validation":
        if not args.mlp_candidate:
            raise SystemExit("mlp-validation needs one or more --mlp-candidate LABEL=PATH")
        candidate_rows, candidate_summaries = {}, []
        for label, path in args.mlp_candidate:
            rows = run_method(args.menagerie, label, MLPComplianceController.from_npz(path), args.mlp_budget,
                              args.seeds, args.fixture_count)
            candidate_rows[label] = rows
            summary = aggregate(rows)
            candidate_summaries.append({"label": label, "path": str(path), "budget": args.mlp_budget,
                                        "summary": summary})
            print(f"[{time.time()-started:7.1f}s] {label}: {summary}", flush=True)
        selected = max(candidate_summaries, key=lambda item: selection_score(item["summary"]))
        output = {
            "schema_version": 1,
            "protocol": "four_method_multicontact_mlp_bc_validation_only",
            "status": "selection_only; frozen PaperMPC/VMC/ESN not evaluated or reselected",
            "selection_rule": ["maximize task success count", "break ties with minimum mean at-grasp error"],
            "seeds": args.seeds, "fixture_count_per_seed": args.fixture_count,
            "fixture_generator": "fixture(seed*6151 + fixture_index + 1)",
            "mlp_observation_contract": "q, qdot, nominal_twist, pose_error, wbc_twist_error (32-D) only",
            "candidates": candidate_summaries, "selected": selected,
            "rows": [row for rows in candidate_rows.values() for row in rows],
        }
    else:
        if args.mlp is None or args.esn is None:
            raise SystemExit("four-method-test requires --mlp and --esn")
        methods = [
            ("paper_mpc_nominal_only", None, args.mlp_budget,
             {"description": "original PaperMPC nominal controller; zero compliance residual"}),
            ("vmc_frozen_k1_budget2pct", make_vmc(args.vmc_k, args.vmc_budget), args.vmc_budget,
             {"k_translation_base": args.vmc_k}),
            (args.mlp_label, MLPComplianceController.from_npz(args.mlp), args.mlp_budget,
             {"checkpoint": str(args.mlp), "training": "behavior cloning only"}),
            ("esn_proposed_frozen_cem", load_controller(args.esn), args.esn_budget,
             {"checkpoint": str(args.esn), "training": "multi-contact BC + train-only CEM readout improvement"}),
        ]
        rows_by_method, configurations = {}, {}
        for label, controller, budget, configuration in methods:
            rows_by_method[label] = run_method(args.menagerie, label, controller, budget, args.seeds,
                                               args.fixture_count)
            configurations[label] = {"residual_budget_fraction": budget, **configuration}
            print(f"[{time.time()-started:7.1f}s] {label}: {aggregate(rows_by_method[label])}", flush=True)
        output = {
            "schema_version": 1,
            "protocol": "four_method_multicontact_independent_heldout_test",
            "status": "confirmatory_fixed_policy_test; no ESN/VMC retraining, reselection, or tuning",
            "seeds": args.seeds, "fixture_count_per_seed": args.fixture_count,
            "fixture_generator": "fixture(seed*6151 + fixture_index + 1)",
            "contact_distribution": "positive_y finite-mass ellipsoidal hand_proxy; fixed physical ranges recorded per row",
            "shared_controls": "same PaperMPC nominal WBC, FR3 torque limits, residual safety clamp, success criterion and fixtures",
            "observation_contract": "learned policies receive q, qdot, nominal_twist, pose_error, wbc_twist_error only; no force, apparatus, geometry, direction label, time, or future input",
            "method_configurations": configurations,
            "summary": {method: aggregate(rows) for method, rows in rows_by_method.items()},
            "rows": [row for rows in rows_by_method.values() for row in rows],
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"elapsed_s": time.time() - started, "summary": output.get("summary"),
                      "selected": output.get("selected")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
