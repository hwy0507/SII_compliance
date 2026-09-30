#!/usr/bin/env python3
"""Run a strict paired rigid/impedance/VMC ladder on one rod fixture.

Every controller sees the same Panda model, nominal reference, rod trajectory,
task gate, torque slew limit, and paired no-rod control.  The script refuses to
describe a rod run as valid unless it both contacts the Panda hand and finishes
the physical grasp task.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
RUNNER = SCRIPT_DIR / "run_rod_perturbation_benchmark.py"
PLOTTER = SCRIPT_DIR / "plot_trajectory_results.py"


def _run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _finished(run_dir: Path, no_rod_dir: Path, summary_name: str) -> bool:
    return all(path.is_file() for path in (
        run_dir / summary_name,
        no_rod_dir / summary_name,
    ))


def _validity(summary: dict[str, Any], require_contact: bool) -> tuple[bool, list[str]]:
    task = summary["task_validity"]
    torque = summary["torque"]
    failures: list[str] = []
    if not task["simulation_finite"]:
        failures.append("nonfinite_simulation")
    if require_contact and not task["rod_hand_contact_observed"]:
        failures.append("missing_rod_hand_contact")
    if require_contact and summary["phase_analysis"]["rejoin_time_s"] is None:
        failures.append("no_stable_rejoin")
    if not task["target_lifted_after_recovery"]:
        failures.append("target_not_lifted")
    if not task["target_held_at_end"]:
        failures.append("target_not_held")
    if torque["hard_limit_fraction"] != 0.0:
        failures.append("hard_torque_limit")
    return not failures, failures


def _row(mode: str, summary: dict[str, Any], metrics: dict[str, Any], valid: bool, failures: list[str]) -> dict[str, Any]:
    response = summary["six_spring_response"]
    rod = summary["rod_diagnostics"]
    motion = summary["motion"]
    torque = summary["torque"]
    phase = summary["phase_analysis"]
    return {
        "controller": mode,
        "valid": valid,
        "invalid_reasons": failures,
        "peak_nominal_error_mm": response["peak_end_effector_nominal_deviation_m"] * 1000.0,
        "peak_paired_rod_offset_mm": metrics["peak_paired_rod_offset_mm"],
        "nominal_position_rmse_mm": metrics["nominal_position_rmse_mm"],
        # This comes from the runner's phase analysis, which merges <=20 ms
        # solver-scale contact gaps.  It is the canonical value rather than a
        # plot-only re-computation.
        "release_to_rejoin_latency_s": phase["release_to_rejoin_latency_s"],
        "peak_contact_force_n": rod["peak_contact_force_n"],
        "contact_impulse_ns": rod["contact_impulse_ns"],
        "peak_torque_nm": torque["applied_peak_nm"],
        "peak_torque_ratio": torque["applied_peak_ratio"],
        "speed_p95_mps": motion["recovery_speed_p95_mps"],
        "jerk_peak_mps3": motion["jerk_peak_mps3"],
        "secondary_contact_count": phase["secondary_contact_count"],
        "target_lifted": summary["task_validity"]["target_lifted_after_recovery"],
        "target_held": summary["task_validity"]["target_held_at_end"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--controllers", nargs="+", choices=("rigid", "impedance", "vmc"), default=["rigid", "impedance", "vmc"])
    parser.add_argument("--kappa", type=float, default=35.0)
    parser.add_argument("--damping-ratio", type=float, default=0.8)
    parser.add_argument("--carriage-drive-scale", type=float, default=8.0)
    parser.add_argument("--rod-stroke", type=float, default=0.16)
    parser.add_argument("--rod-height", type=float, default=0.54)
    parser.add_argument("--grasp-time", type=float, default=2.10)
    parser.add_argument("--explicit-vmc", action="store_true", help="Use the validated explicit translational VMC carriage for the VMC row.")
    parser.add_argument("--carriage-mass-kg", type=float, default=1.0)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    common = [
        "--menagerie", str(args.menagerie), "--kappas", str(args.kappa),
        "--damping-ratio", str(args.damping_ratio),
        "--carriage-drive-scale", str(args.carriage_drive_scale),
        "--recovery-carriage-drive-scale", str(args.carriage_drive_scale),
        "--recovery-kappa", str(args.kappa), "--recovery-ramp", "0.08",
        "--contact-time-constant", "0.015", "--rod-stroke", str(args.rod_stroke),
        "--rod-height", str(args.rod_height), "--grasp-time", str(args.grasp_time),
    ]
    trace_name = f"rod_perturbation_kappa_{args.kappa:.2f}_trace.npz"
    summary_name = f"rod_perturbation_kappa_{args.kappa:.2f}_summary.json"
    for mode in args.controllers:
        run_dir = args.output_dir / mode
        no_rod_dir = args.output_dir / f"{mode}_no_rod"
        controller_args = ["--controller-mode", mode]
        if mode == "vmc" and args.explicit_vmc:
            controller_args += ["--explicit-translational-carriage", "--carriage-mass-kg", str(args.carriage_mass_kg)]
        if not _finished(run_dir, no_rod_dir, summary_name):
            _run([sys.executable, str(RUNNER), "--output-dir", str(run_dir), *common, *controller_args])
            _run([sys.executable, str(RUNNER), "--output-dir", str(no_rod_dir), *common, *controller_args, "--disable-rod"])
        _run([
            sys.executable, str(PLOTTER), "--rod-trace", str(run_dir / trace_name),
            "--no-rod-trace", str(no_rod_dir / trace_name), "--output-dir", str(run_dir / "figures"),
            "--grasp-time", str(args.grasp_time),
        ])
        summary = _load(run_dir / summary_name)
        no_rod_summary = _load(no_rod_dir / summary_name)
        metrics = _load(run_dir / "figures" / "trajectory_error_metrics.json")
        valid, failures = _validity(summary, require_contact=True)
        no_rod_valid, no_rod_failures = _validity(no_rod_summary, require_contact=False)
        if not no_rod_valid:
            valid = False
            failures += [f"no_rod:{reason}" for reason in no_rod_failures]
        rows.append(_row(mode, summary, metrics, valid, failures))

    protocol = {
        "controllers": args.controllers,
        "kappa": args.kappa,
        "damping_ratio": args.damping_ratio,
        "carriage_drive_scale": args.carriage_drive_scale,
        "rod_stroke_m": args.rod_stroke,
        "rod_height_m": args.rod_height,
        "grasp_time_s": args.grasp_time,
        "explicit_vmc": args.explicit_vmc,
        "validity_definition": "finite + physical rod-hand contact + stable rejoin + lift + hold + no hard torque limit + valid paired no-rod task",
    }
    (args.output_dir / "baseline_ladder_summary.json").write_text(json.dumps({"protocol": protocol, "rows": rows}, indent=2) + "\n")
    columns = list(rows[0]) if rows else []
    with (args.output_dir / "baseline_ladder_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"protocol": protocol, "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
