#!/usr/bin/env python3
"""Development-only screen of ESN dynamics on inclined-board contacts.

The VMC reference is evaluated once.  Every ESN candidate uses the same
32-dimensional deployable observation, action budget, teacher archives, and
MuJoCo fixtures.  Board/contact quantities are used only to score completed
rollouts; they are never supplied to a controller.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evaluate_inclined_lift_four_method import fixture, make_vmc, run_one  # noqa: E402
from vmc_compliance_baseline import load_controller  # noqa: E402


def aggregate(rows: list[dict]) -> dict:
    return {
        "count": len(rows),
        "success_count": int(sum(bool(row["task_success"]) for row in rows)),
        "success_rate": float(np.mean([bool(row["task_success"]) for row in rows])),
        "mean_peak_force_n": float(np.mean([row["board_peak_force_n"] for row in rows])),
        "mean_impulse_ns": float(np.mean([row["board_contact_impulse_ns"] for row in rows])),
        "mean_postcontact_error_mm": float(np.mean([row["peak_postcontact_error_mm"] for row in rows])),
        "mean_peak_torque_nm": float(np.mean([row["peak_torque_nm"] for row in rows])),
        "geometry_valid_rate": float(np.mean([row["geometry_valid_postgrasp"] for row in rows])),
    }


def evaluate(menagerie: Path, label: str, controller, *, budget: float,
             tilts: list[float], yaws: list[float], seeds: list[int]) -> list[dict]:
    rows: list[dict] = []
    for tilt in tilts:
        for yaw in yaws:
            for seed in seeds:
                if hasattr(controller, "reset"):
                    controller.reset()
                # Keep exactly the deterministic board-jitter convention of
                # the four-method evaluator.
                offset = float(np.random.default_rng(
                    seed * 1009 + int(round(tilt * 10)) + int(round(yaw * 100))
                ).uniform(-0.008, 0.008))
                row = run_one(
                    menagerie, label, controller, seed=seed, tilt=tilt,
                    budget=budget, board_y_offset_m=offset, board_yaw_deg=yaw,
                )
                # Per-step rows are unnecessary for development screening and
                # make candidate manifests needlessly large.
                row.pop("rows", None)
                rows.append(row)
    return rows


def relative_loss(summary: dict, vmc: dict) -> float:
    """Predeclared equal-weight physical loss relative to fixed VMC."""

    keys = ("mean_peak_force_n", "mean_impulse_ns", "mean_postcontact_error_mm")
    return float(sum(summary[key] / max(vmc[key], 1.0e-9) for key in keys) / len(keys))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--esns", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--tilts", type=float, nargs="+", default=[37.5])
    parser.add_argument("--yaws", type=float, nargs="+", default=[75.0, 105.0])
    parser.add_argument("--budget", type=float, default=0.02)
    args = parser.parse_args()
    if not 0.0 < args.budget <= 1.0:
        raise SystemExit("budget must be in (0, 1]")
    if len(set(args.esns)) != len(args.esns):
        raise SystemExit("duplicate ESN paths")

    started = time.time()
    vmc_rows = evaluate(
        args.menagerie, "VMC_validation", make_vmc(args.budget), budget=args.budget,
        tilts=args.tilts, yaws=args.yaws, seeds=args.seeds,
    )
    vmc_summary = aggregate(vmc_rows)
    print(json.dumps({"method": "VMC", "summary": vmc_summary}), flush=True)

    candidates: list[dict] = []
    all_rows = list(vmc_rows)
    for path in args.esns:
        controller = load_controller(path)
        label = path.stem
        rows = evaluate(
            args.menagerie, label, controller, budget=args.budget,
            tilts=args.tilts, yaws=args.yaws, seeds=args.seeds,
        )
        summary = aggregate(rows)
        loss = relative_loss(summary, vmc_summary)
        candidate = {
            "label": label,
            "model": str(path),
            "reservoir": controller.contract()["reservoir"],
            "summary": summary,
            "relative_physical_loss_vs_vmc": loss,
        }
        candidates.append(candidate)
        all_rows.extend(rows)
        print(json.dumps({"candidate": label, "summary": summary,
                          "relative_physical_loss_vs_vmc": loss}), flush=True)

    # Primary endpoint is task success.  Ties are broken by the predeclared
    # equal-weight force/impulse/post-contact-error loss relative to VMC.
    selected = max(
        candidates,
        key=lambda item: (item["summary"]["success_rate"],
                          -item["relative_physical_loss_vs_vmc"]),
    )
    output = {
        "schema_version": 1,
        "protocol": "inclined_lift_esn_dynamics_development_screen",
        "status": "development_only_not_confirmatory",
        "observation_contract": "q, qdot, nominal_twist, pose_error, wbc_twist_error (32-D); no board/contact truth",
        "fixed_budget": args.budget,
        "training_contract": "all candidate checkpoints must use the same successful teacher traces and neutral trace",
        "selection_rule": "maximize success rate; break ties by minimum equal-weight mean of peak-force, impulse, and post-contact-error ratios to fixed VMC",
        "tilts_deg": args.tilts,
        "yaws_deg": args.yaws,
        "seeds": args.seeds,
        "vmc": vmc_summary,
        "candidates": candidates,
        "selected": selected,
        "rows": all_rows,
        "elapsed_s": time.time() - started,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"selected": selected, "elapsed_s": output["elapsed_s"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
