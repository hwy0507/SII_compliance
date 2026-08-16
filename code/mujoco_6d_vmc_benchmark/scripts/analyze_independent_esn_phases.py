#!/usr/bin/env python3
"""Phase-resolved analysis for paired independent WBC residual runs.

The physical rod schedule is used here only for offline analysis.  It never
enters either deployed MLP/ESN observation or the direct-controller safety
filter.  The output shows whether a paired ESN difference arises during nominal
motion, physical loading, or post-release rejoin.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


METHODS = ("current_mlp", "fan_ye_esn")
PHASES = ("pre_contact", "loading", "recovery", "post_grasp")


def _distribution(values: list[float]) -> dict[str, float | int]:
    array = np.asarray(values, dtype=float)
    return {
        "mean": float(np.mean(array)),
        "std": float(np.std(array, ddof=0)),
        "count": int(array.size),
    }


def _phase_mask(time_s: np.ndarray, start_s: float, grasp_s: float, phase: str) -> np.ndarray:
    release_s = start_s + 0.64
    if phase == "pre_contact":
        return time_s < start_s
    if phase == "loading":
        return (time_s >= start_s) & (time_s <= release_s)
    if phase == "recovery":
        return (time_s > release_s) & (time_s < grasp_s)
    if phase == "post_grasp":
        return time_s >= grasp_s
    raise ValueError(f"unknown phase: {phase}")


def _trace_metrics(path: Path, fixture: dict[str, Any]) -> dict[str, dict[str, float]]:
    with np.load(path) as trace:
        time_s = np.asarray(trace["rod_time"], dtype=float)
        position_error_m = np.linalg.norm(
            np.asarray(trace["rod_ee_position"], dtype=float)
            - np.asarray(trace["nominal_position"], dtype=float),
            axis=1,
        )
        torque = np.max(np.abs(np.asarray(trace["rod_torque"], dtype=float)), axis=1)
        scale = np.asarray(trace["rod_wbc_scale"], dtype=float)
        yield_norm = np.linalg.norm(np.asarray(trace["rod_yield_twist"], dtype=float), axis=1)
        gate = np.asarray(trace.get("rod_authority_gate", np.zeros_like(time_s)), dtype=float)
    result: dict[str, dict[str, float]] = {}
    for phase in PHASES:
        mask = _phase_mask(time_s, float(fixture["rod_start_time_s"]), float(fixture["grasp_time_s"]), phase)
        if not np.any(mask):
            raise RuntimeError(f"trace {path} has no samples for {phase}")
        result[phase] = {
            "tracking_rmse_mm": float(np.sqrt(np.mean(position_error_m[mask] ** 2)) * 1000.0),
            "tracking_peak_mm": float(np.max(position_error_m[mask]) * 1000.0),
            "mean_wbc_slowdown": float(np.mean(1.0 - scale[mask])),
            "mean_yield_twist_norm": float(np.mean(yield_norm[mask])),
            "mean_authority_gate": float(np.mean(gate[mask])),
            "peak_torque_nm": float(np.max(torque[mask])),
        }
    return result


def _report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-root", type=Path, required=True)
    parser.add_argument("--profile", default="balanced")
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-markdown", type=Path, default=None)
    args = parser.parse_args()
    run_dirs = sorted(path for path in args.campaign_root.glob(f"{args.profile}_seed*") if path.is_dir())
    if not run_dirs:
        raise FileNotFoundError(f"no runs for profile {args.profile!r}")
    rows: list[dict[str, Any]] = []
    metric_names = (
        "tracking_rmse_mm", "tracking_peak_mm", "mean_wbc_slowdown",
        "mean_yield_twist_norm", "mean_authority_gate", "peak_torque_nm",
    )
    for run_dir in run_dirs:
        reports = {
            method: _report(run_dir / method / "validation" / "wbc_velocity_residual_paired_evaluation.json")
            for method in METHODS
        }
        records = {method: report["records"] for method, report in reports.items()}
        if len(records["current_mlp"]) != len(records["fan_ye_esn"]):
            raise RuntimeError(f"mismatched fixture count in {run_dir}")
        for index, (mlp_record, esn_record) in enumerate(zip(records["current_mlp"], records["fan_ye_esn"], strict=True)):
            if mlp_record["fixture"] != esn_record["fixture"]:
                raise RuntimeError(f"mismatched fixture at {run_dir}, index {index}")
            fixture = mlp_record["fixture"]
            phase_by_method = {
                method: _trace_metrics(run_dir / method / "validation" / f"fixture_{index:02d}_paired_trace.npz", fixture)
                for method in METHODS
            }
            for phase in PHASES:
                difference = {
                    name: phase_by_method["fan_ye_esn"][phase][name] - phase_by_method["current_mlp"][phase][name]
                    for name in metric_names
                }
                rows.append({
                    "run_id": run_dir.name,
                    "fixture_index": index,
                    "phase": phase,
                    "mlp": phase_by_method["current_mlp"][phase],
                    "esn": phase_by_method["fan_ye_esn"][phase],
                    "difference_esn_minus_mlp": difference,
                })
    by_phase: dict[str, Any] = {}
    for phase in PHASES:
        phase_rows = [row for row in rows if row["phase"] == phase]
        by_phase[phase] = {
            metric: _distribution([row["difference_esn_minus_mlp"][metric] for row in phase_rows])
            for metric in metric_names
        }
    output = {
        "controller_family": "independent_wbc_velocity_residual",
        "uses_vmc": False,
        "profile": args.profile,
        "rows": rows,
        "by_phase_esn_minus_mlp": by_phase,
    }
    output_json = args.output_json or args.campaign_root / f"{args.profile}_phase_analysis.json"
    output_json.write_text(json.dumps(output, indent=2) + "\n")
    output_markdown = args.output_markdown or args.campaign_root / f"{args.profile}_phase_analysis.md"
    lines = [
        f"# {args.profile} phase-resolved ESN minus MLP", "",
        "Negative tracking/torque values favor ESN. Positive slowdown/yield values mean ESN used more residual authority.", "",
        "| phase | d tracking RMSE (mm) | d peak torque (Nm) | d slowdown | d yield norm | d authority gate |", "",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for phase in PHASES:
        values = by_phase[phase]
        lines.append(
            f"| {phase} | {values['tracking_rmse_mm']['mean']:.3f} +/- {values['tracking_rmse_mm']['std']:.3f} | "
            f"{values['peak_torque_nm']['mean']:.3f} +/- {values['peak_torque_nm']['std']:.3f} | "
            f"{values['mean_wbc_slowdown']['mean']:.4f} | {values['mean_yield_twist_norm']['mean']:.4f} | "
            f"{values['mean_authority_gate']['mean']:.4f} |"
        )
    output_markdown.write_text("\n".join(lines) + "\n")
    print(json.dumps({"output_json": str(output_json), "by_phase": by_phase}, indent=2))


if __name__ == "__main__":
    main()
