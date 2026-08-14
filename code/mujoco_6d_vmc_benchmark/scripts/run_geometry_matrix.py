#!/usr/bin/env python3
"""Run a paired, validity-gated rod geometry matrix for the VMC benchmark."""

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

# Operational fixture categories, deliberately separate from human-safety
# limits.  They prevent a one-sample grazing contact from being compared as if
# it were the same disturbance as the validated nominal rod press.
NO_CONTACT_PEAK_N = 1.0
NOMINAL_CONTACT_MIN_N = 9.0
NOMINAL_CONTACT_MAX_N = 30.0


def _run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _valid(summary: dict[str, Any], require_contact: bool) -> tuple[bool, list[str]]:
    task = summary["task_validity"]
    failures = []
    if not task["simulation_finite"]:
        failures.append("nonfinite_simulation")
    if require_contact and not task["rod_hand_contact_observed"]:
        failures.append("missing_rod_hand_contact")
    if require_contact and summary["rod_diagnostics"]["peak_contact_force_n"] < NO_CONTACT_PEAK_N:
        failures.append("ineffective_contact_force")
    if require_contact and summary["phase_analysis"]["rejoin_time_s"] is None:
        failures.append("no_stable_rejoin")
    if not task["target_lifted_after_recovery"]:
        failures.append("target_not_lifted")
    if not task["target_held_at_end"]:
        failures.append("target_not_held")
    if summary["torque"]["hard_limit_fraction"] != 0.0:
        failures.append("hard_torque_limit")
    return not failures, failures


def _finished(run_dir: Path, no_rod_dir: Path, summary_name: str) -> bool:
    return all(path.is_file() for path in (
        run_dir / summary_name,
        no_rod_dir / summary_name,
        run_dir / "figures" / "trajectory_error_metrics.json",
    ))


def _contact_regime(peak_force_n: float, impulse_ns: float) -> str:
    """Classify the realised rod–hand interaction before controller ranking."""
    if peak_force_n < NO_CONTACT_PEAK_N or impulse_ns <= 0.0:
        return "no_contact"
    if peak_force_n < NOMINAL_CONTACT_MIN_N:
        return "grazing_contact"
    if peak_force_n <= NOMINAL_CONTACT_MAX_N:
        return "nominal_contact"
    return "high_impact"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--heights", type=float, nargs="+", default=[0.53, 0.54, 0.55])
    parser.add_argument("--strokes", type=float, nargs="+", default=[0.14, 0.16, 0.18])
    parser.add_argument("--kappa", type=float, default=35.0)
    parser.add_argument("--damping-ratio", type=float, default=0.8)
    parser.add_argument("--carriage-drive-scale", type=float, default=8.0)
    parser.add_argument("--grasp-time", type=float, default=2.10)
    parser.add_argument("--carriage-mass-kg", type=float, default=1.0)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    trace_name = f"rod_perturbation_kappa_{args.kappa:.2f}_trace.npz"
    summary_name = f"rod_perturbation_kappa_{args.kappa:.2f}_summary.json"
    common = [
        "--menagerie", str(args.menagerie), "--controller-mode", "vmc", "--kappas", str(args.kappa),
        "--damping-ratio", str(args.damping_ratio), "--carriage-drive-scale", str(args.carriage_drive_scale),
        "--recovery-carriage-drive-scale", str(args.carriage_drive_scale), "--recovery-kappa", str(args.kappa),
        "--recovery-ramp", "0.08", "--contact-time-constant", "0.015", "--grasp-time", str(args.grasp_time),
        "--explicit-translational-carriage", "--carriage-mass-kg", str(args.carriage_mass_kg),
    ]
    for height in args.heights:
        for stroke in args.strokes:
            name = f"h{height:.3f}_s{stroke:.3f}".replace(".", "p")
            run_dir = args.output_dir / name
            no_rod_dir = args.output_dir / f"{name}_no_rod"
            scenario = ["--rod-height", str(height), "--rod-stroke", str(stroke)]
            if not _finished(run_dir, no_rod_dir, summary_name):
                _run([sys.executable, str(RUNNER), "--output-dir", str(run_dir), *common, *scenario])
                _run([sys.executable, str(RUNNER), "--output-dir", str(no_rod_dir), *common, *scenario, "--disable-rod"])
            # Rendering/metrics are inexpensive post-processing and are
            # always refreshed, even when the deterministic physics traces
            # were resumed from disk.
            _run([
                sys.executable, str(PLOTTER), "--rod-trace", str(run_dir / trace_name),
                "--no-rod-trace", str(no_rod_dir / trace_name), "--output-dir", str(run_dir / "figures"),
                "--grasp-time", str(args.grasp_time),
            ])
            summary = _load(run_dir / summary_name)
            no_rod_summary = _load(no_rod_dir / summary_name)
            metrics = _load(run_dir / "figures" / "trajectory_error_metrics.json")
            valid, failures = _valid(summary, require_contact=True)
            no_rod_valid, no_rod_failures = _valid(no_rod_summary, require_contact=False)
            if not no_rod_valid:
                valid = False
                failures += [f"no_rod:{reason}" for reason in no_rod_failures]
            response = summary["six_spring_response"]
            rod = summary["rod_diagnostics"]
            phase = summary["phase_analysis"]
            contact_regime = _contact_regime(rod["peak_contact_force_n"], rod["contact_impulse_ns"])
            rows.append({
                "height_m": height, "stroke_m": stroke, "valid": valid, "invalid_reasons": failures,
                "contact_regime": contact_regime,
                "contact_peak_n": rod["peak_contact_force_n"], "contact_impulse_ns": rod["contact_impulse_ns"],
                "peak_nominal_error_mm": response["peak_end_effector_nominal_deviation_m"] * 1000.0,
                "paired_offset_mm": metrics["peak_paired_rod_offset_mm"],
                "rmse_mm": metrics["nominal_position_rmse_mm"],
                "rejoin_latency_s": phase["release_to_rejoin_latency_s"],
                "peak_torque_nm": summary["torque"]["applied_peak_nm"],
                "jerk_peak_mps3": summary["motion"]["jerk_peak_mps3"],
                "secondary_contact_count": phase["secondary_contact_count"],
                "lift": summary["task_validity"]["target_lifted_after_recovery"],
                "hold": summary["task_validity"]["target_held_at_end"],
            })
    protocol = {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()}
    protocol["validity_definition"] = "finite + effective physical contact (>=1 N) + stable rejoin + lift + hold + no hard torque limit + valid no-rod pair"
    protocol["contact_regimes"] = {
        "no_contact": f"peak force < {NO_CONTACT_PEAK_N:.0f} N or zero impulse",
        "grazing_contact": f"{NO_CONTACT_PEAK_N:.0f} <= peak force < {NOMINAL_CONTACT_MIN_N:.0f} N",
        "nominal_contact": f"{NOMINAL_CONTACT_MIN_N:.0f} <= peak force <= {NOMINAL_CONTACT_MAX_N:.0f} N",
        "high_impact": f"peak force > {NOMINAL_CONTACT_MAX_N:.0f} N",
    }
    protocol["ranking_rule"] = "Only nominal_contact rows are comparable benchmark cases; high_impact rows are stress tests, grazing/no-contact rows are reported but excluded from ranking."
    payload = {"protocol": protocol, "rows": rows}
    (args.output_dir / "geometry_matrix_summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    with (args.output_dir / "geometry_matrix_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
