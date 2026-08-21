#!/usr/bin/env python3
"""Fair validation-selection/test evaluation for ESN versus VMC.

Both methods share the same residual-budget candidates and matched randomized
fixtures.  ESN reservoir seed/budget and VMC stiffness/budget are selected on
validation seeds only; held-out test seeds are evaluated exactly once after
selection.  No contact truth or obstacle state is exposed to either policy.
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
from run_paper_mpc_benchmark import (  # noqa: E402
    SEED,
    perturb_fixture,
    run_rollout,
)
from vmc_compliance_baseline import SpringCarriageConfig  # noqa: E402
from vmc_torque_baseline import VMCTorqueBaseline  # noqa: E402
from wbc_velocity_residual_env import default_velocity_residual_fixtures  # noqa: E402


def parse_seeds(value: str) -> list[int]:
    seeds = list(dict.fromkeys(int(token.strip()) for token in value.split(",") if token.strip()))
    if not seeds:
        raise argparse.ArgumentTypeError("seed list cannot be empty")
    return seeds


def scenarios():
    fixtures = default_velocity_residual_fixtures()
    rows = []
    for index, fixture in enumerate(fixtures):
        rows.append((f"rod_fx{index}", "rod", fixture, False, index))
        rows.append((f"ball_fx{index}", "ball", replace(fixture, impactor_type="ball"), False, 4 + index))
    for index in (0, 2):
        rows.append((f"board_fx{index}", "board", replace(fixtures[index], rod_start_time_s=99.0), True, 8 + index))
    return rows


def aggregate(rows: list[dict]) -> dict:
    if not rows:
        return {"success_rate": 0.0, "mean_at_grasp_err_mm": float("inf"), "mean_force_n": float("inf"), "count": 0}
    return {
        "success_rate": float(np.mean([bool(row["task_success"]) for row in rows])),
        "mean_at_grasp_err_mm": float(np.mean([float(row["at_grasp_err_mm"]) for row in rows])),
        "mean_force_n": float(np.mean([float(row["obstacle_force_n"]) for row in rows])),
        "count": len(rows),
    }


def selection_key(summary: dict) -> tuple[float, float]:
    # Success is primary; tracking error breaks ties. This rule is fixed before
    # test evaluation and is identical for ESN and VMC.
    return (summary["success_rate"], -summary["mean_at_grasp_err_mm"])


def evaluate_esn(menagerie: Path, model_path: Path, budget: float, seeds: list[int], jitter: tuple[float, float, float], label: str) -> list[dict]:
    controller = __import__("vmc_compliance_baseline")  # keep import order compatible with server runtime
    del controller
    from vmc_compliance_baseline import load_controller
    policy = load_controller(model_path)
    rows = []
    for seed in seeds:
        for name, kind, fixture, board, scenario_index in scenarios():
            fixture = perturb_fixture(fixture, seed=seed, scenario_index=scenario_index,
                                      rod_stroke_jitter_m=jitter[0], rod_height_jitter_m=jitter[1],
                                      rod_start_jitter_s=jitter[2])
            rows.append(run_rollout(menagerie, fixture, impactor_kind=kind, controller=policy,
                                    lift_board=board, residual_scale=budget, seed=seed,
                                    rod_stroke_jitter_m=jitter[0], rod_height_jitter_m=jitter[1],
                                    rod_start_jitter_s=jitter[2], verbose_name=label + "/" + name))
    return rows


def evaluate_vmc(menagerie: Path, k: float, budget: float, seeds: list[int], jitter: tuple[float, float, float], label: str) -> list[dict]:
    base = SpringCarriageConfig(k_translation_base=2.2, k_rotation_base=0.18)
    config = replace(base, k_translation_base=k, k_rotation_base=base.k_rotation_base * k / base.k_translation_base)
    rows = []
    for seed in seeds:
        for name, kind, fixture, board, scenario_index in scenarios():
            fixture = perturb_fixture(fixture, seed=seed, scenario_index=scenario_index,
                                      rod_stroke_jitter_m=jitter[0], rod_height_jitter_m=jitter[1],
                                      rod_start_jitter_s=jitter[2])
            policy = VMCTorqueBaseline(config, TORQUE_LIMITS * budget)
            rows.append(run_rollout(menagerie, fixture, impactor_kind=kind, controller=policy,
                                    lift_board=board, residual_scale=budget, seed=seed,
                                    rod_stroke_jitter_m=jitter[0], rod_height_jitter_m=jitter[1],
                                    rod_start_jitter_s=jitter[2], verbose_name=label + "/" + name))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--esn-101", type=Path, required=True)
    parser.add_argument("--esn-202", type=Path, required=True)
    parser.add_argument("--esn-303", type=Path, required=True)
    parser.add_argument("--validation-seeds", type=parse_seeds, default=[20260819, 20260820, 20260821, 20260822, 20260823])
    parser.add_argument("--test-seeds", type=parse_seeds, default=[20260824, 20260825, 20260826, 20260827, 20260828])
    parser.add_argument("--budgets", type=str, default="0.02,0.03,0.05,0.08")
    parser.add_argument("--vmc-k-values", type=str, default="1.5,2.2,3.2,4.6")
    parser.add_argument("--stroke-jitter-m", type=float, default=0.002)
    parser.add_argument("--height-jitter-m", type=float, default=0.0015)
    parser.add_argument("--start-jitter-s", type=float, default=0.015)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    budgets = [float(value) for value in args.budgets.split(",")]
    k_values = [float(value) for value in args.vmc_k_values.split(",")]
    if any(not 0.0 < value <= 1.0 for value in budgets) or any(value <= 0.0 for value in k_values):
        raise SystemExit("budgets must be in (0,1], k values must be positive")
    jitter = (args.stroke_jitter_m, args.height_jitter_m, args.start_jitter_s)
    candidates = []
    t0 = time.time()

    esn_paths = {"esn101": args.esn_101, "esn202": args.esn_202, "esn303": args.esn_303}
    for model_name, model_path in esn_paths.items():
        for budget in budgets:
            label = f"{model_name}_b{budget:g}"
            rows = evaluate_esn(args.menagerie, model_path, budget, args.validation_seeds, jitter, label)
            summary = aggregate(rows)
            candidates.append({"family": "esn", "model": model_name, "budget": budget, "summary": summary, "validation_rows": rows})
            print(f"[{time.time()-t0:7.1f}s] {label}: {summary}", flush=True)
    for k in k_values:
        for budget in budgets:
            label = f"vmc_k{k:g}_b{budget:g}"
            rows = evaluate_vmc(args.menagerie, k, budget, args.validation_seeds, jitter, label)
            summary = aggregate(rows)
            candidates.append({"family": "vmc", "k": k, "budget": budget, "summary": summary, "validation_rows": rows})
            print(f"[{time.time()-t0:7.1f}s] {label}: {summary}", flush=True)

    selected = {}
    for family in ("esn", "vmc"):
        family_candidates = [candidate for candidate in candidates if candidate["family"] == family]
        selected[family] = max(family_candidates, key=lambda candidate: selection_key(candidate["summary"]))
        selected[family] = {key: value for key, value in selected[family].items() if key != "validation_rows"}
        print("selected", family, selected[family], flush=True)

    test_rows = []
    esn_selected = selected["esn"]
    esn_path = esn_paths[esn_selected["model"]]
    test_rows.extend(evaluate_esn(args.menagerie, esn_path, esn_selected["budget"], args.test_seeds, jitter, "selected_esn"))
    vmc_selected = selected["vmc"]
    test_rows.extend(evaluate_vmc(args.menagerie, vmc_selected["k"], vmc_selected["budget"], args.test_seeds, jitter, "selected_vmc"))
    output = {
        "schema_version": 2,
        "protocol": "shared_budget_validation_selection_then_heldout_test",
        "selection_rule": [
            "maximize validation success_rate",
            "break success-rate ties by minimizing validation mean_at_grasp_err_mm",
        ],
        "validation_seeds": args.validation_seeds,
        "test_seeds": args.test_seeds,
        "budget_candidates": budgets,
        "vmc_k_candidates": k_values,
        "jitter": {"stroke_m": jitter[0], "height_m": jitter[1], "start_s": jitter[2]},
        # Keep all candidate summaries in the result artifact.  This is enough
        # to audit the pre-declared selection decision without duplicating the
        # much larger per-rollout validation traces.
        "validation_candidates": [
            {key: value for key, value in candidate.items() if key != "validation_rows"}
            for candidate in candidates
        ],
        "selected": selected,
        "test_summary": {
            "esn": aggregate([row for row in test_rows if row["name"].startswith("selected_esn/")]),
            "vmc": aggregate([row for row in test_rows if row["name"].startswith("selected_vmc/")]),
        },
        "test_rows": test_rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"out": str(args.out), "test_summary": output["test_summary"], "selected": selected}, indent=2))


if __name__ == "__main__":
    main()
