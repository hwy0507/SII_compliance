#!/usr/bin/env python3
"""Validity-gated search for independent six-spring VMC stiffness vectors.

This is deliberately a small, transparent design-of-experiments search rather
than an opaque RL policy.  Each candidate is evaluated against the same
physical rod trajectory and an independently matched no-rod control.  A
candidate is excluded if either physical grasp task is invalid.  Valid
candidates are reported as a Pareto set over recovery, tracking, torque, and
motion smoothness; no controller-specific disturbance is introduced.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
RUNNER = SCRIPT_DIR / "run_rod_perturbation_benchmark.py"
PLOTTER = SCRIPT_DIR / "plot_trajectory_results.py"

# The primary contact direction is world-y.  The candidate set therefore
# explores compliant y/rotation channels while retaining x/z support for the
# grasp.  It also includes isotropic low/high controls and is intentionally
# recorded in the output so it can be expanded or replaced by CMA-ES later.
CANDIDATES: dict[str, list[float]] = {
    "isotropic_35": [35, 35, 35, 35, 35, 35],
    "isotropic_20": [20, 20, 20, 20, 20, 20],
    "isotropic_50": [50, 50, 50, 50, 50, 50],
    "y_soft": [35, 16, 35, 35, 24, 35],
    "y_soft_pitch": [42, 14, 42, 32, 16, 30],
    "supported_y_soft": [55, 18, 55, 38, 20, 34],
    "very_y_soft": [48, 10, 48, 28, 12, 26],
    "balanced_anisotropic": [45, 22, 48, 34, 22, 32],
}

SCENARIOS = {
    "nominal": {"rod_stroke": 0.16, "rod_height": 0.54, "rod_start": 1.08, "grasp_time": 2.10},
    # Same model and contact law, simply a larger common physical excursion
    # and a later closure so every controller has equal time to recover.
    "hard": {"rod_stroke": 0.20, "rod_height": 0.54, "rod_start": 1.08, "grasp_time": 2.28},
}


def _run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _valid(summary: dict[str, Any], require_contact: bool) -> tuple[bool, list[str]]:
    task = summary["task_validity"]
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
    if summary["torque"]["hard_limit_fraction"] != 0.0:
        failures.append("hard_torque_limit")
    return not failures, failures


def _dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Pareto dominance for lower-is-better metrics after validity gating."""
    keys = ("peak_paired_rod_offset_mm", "recovery_rmse_mm", "rejoin_latency_s", "peak_torque_nm", "speed_p95_mps")
    return all(left[key] <= right[key] for key in keys) and any(left[key] < right[key] for key in keys)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scenario", choices=tuple(SCENARIOS), default="hard")
    parser.add_argument("--candidates", nargs="+", choices=tuple(CANDIDATES), default=list(CANDIDATES))
    parser.add_argument("--damping-ratio", type=float, default=0.8)
    parser.add_argument("--carriage-drive-scale", type=float, default=8.0)
    parser.add_argument("--carriage-mass-kg", type=float, default=1.0)
    args = parser.parse_args()
    if min(args.damping_ratio, args.carriage_drive_scale, args.carriage_mass_kg) <= 0.0:
        raise ValueError("controller scales must be positive")

    fixture = SCENARIOS[args.scenario]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for name in args.candidates:
        vector = CANDIDATES[name]
        candidate_dir = args.output_dir / name
        rod_dir = candidate_dir / "rod"
        no_rod_dir = candidate_dir / "no_rod"
        tag = "kvec_" + "_".join(f"{value:.3g}" for value in vector)
        trace_name = f"rod_perturbation_{tag}_trace.npz"
        summary_name = f"rod_perturbation_{tag}_summary.json"
        common = [
            "--menagerie", str(args.menagerie), "--controller-mode", "vmc",
            "--kappa-vector", *(str(value) for value in vector),
            "--damping-ratio", str(args.damping_ratio),
            "--carriage-drive-scale", str(args.carriage_drive_scale),
            "--recovery-carriage-drive-scale", str(args.carriage_drive_scale),
            "--recovery-ramp", "0.08", "--contact-time-constant", "0.015",
            "--rod-stroke", str(fixture["rod_stroke"]), "--rod-height", str(fixture["rod_height"]),
            "--rod-start-time", str(fixture["rod_start"]), "--grasp-time", str(fixture["grasp_time"]),
            "--explicit-translational-carriage", "--carriage-mass-kg", str(args.carriage_mass_kg),
        ]
        if not (rod_dir / summary_name).is_file():
            _run([sys.executable, str(RUNNER), "--output-dir", str(rod_dir), *common])
        if not (no_rod_dir / summary_name).is_file():
            _run([sys.executable, str(RUNNER), "--output-dir", str(no_rod_dir), *common, "--disable-rod"])
        figure_dir = candidate_dir / "figures"
        metrics_path = figure_dir / "trajectory_error_metrics.json"
        if not metrics_path.is_file():
            _run([
                sys.executable, str(PLOTTER), "--rod-trace", str(rod_dir / trace_name),
                "--no-rod-trace", str(no_rod_dir / trace_name), "--output-dir", str(figure_dir),
                "--grasp-time", str(fixture["grasp_time"]),
            ])
        rod_summary = _load(rod_dir / summary_name)
        no_rod_summary = _load(no_rod_dir / summary_name)
        paired = _load(metrics_path)
        valid, failures = _valid(rod_summary, require_contact=True)
        no_rod_valid, no_rod_failures = _valid(no_rod_summary, require_contact=False)
        if not no_rod_valid:
            valid = False
            failures += [f"no_rod:{failure}" for failure in no_rod_failures]
        response = rod_summary["six_spring_response"]
        record = {
            "candidate": name,
            "kappa_vector": vector,
            "valid": valid,
            "invalid_reasons": failures,
            "peak_paired_rod_offset_mm": paired["peak_paired_rod_offset_mm"],
            "recovery_rmse_mm": response["tracking"]["recovery_position_rmse_m"] * 1000.0 if "tracking" in response else rod_summary["tracking"]["recovery_position_rmse_m"] * 1000.0,
            "rejoin_latency_s": rod_summary["phase_analysis"]["release_to_rejoin_latency_s"],
            "peak_torque_nm": rod_summary["torque"]["applied_peak_nm"],
            "speed_p95_mps": rod_summary["motion"]["recovery_speed_p95_mps"],
            "peak_contact_force_n": rod_summary["rod_diagnostics"]["peak_contact_force_n"],
            "contact_impulse_ns": rod_summary["rod_diagnostics"]["contact_impulse_ns"],
        }
        # A transparent tie-breaker only; scientific claims use the Pareto set.
        if valid:
            record["screening_score"] = (
                0.45 * record["peak_paired_rod_offset_mm"]
                + 0.35 * record["recovery_rmse_mm"]
                + 4.0 * float(record["rejoin_latency_s"])
                + 0.05 * record["peak_torque_nm"]
                + 0.30 * record["speed_p95_mps"]
            )
        else:
            record["screening_score"] = None
        records.append(record)

    valid_records = [record for record in records if record["valid"]]
    pareto = [
        record["candidate"] for record in valid_records
        if not any(other is not record and _dominates(other, record) for other in valid_records)
    ]
    best = min(valid_records, key=lambda record: float(record["screening_score"])) if valid_records else None
    report = {
        "protocol": {
            "scenario": args.scenario,
            "fixture": fixture,
            "controller": "VMC with explicit translational virtual carriage; independent [x,y,z,roll,pitch,yaw] stiffness multipliers",
            "fairness": "Every candidate receives the identical rod, reference, torque limits, task gate, and matched no-rod run. Rigid/impedance are not modified or handicapped.",
            "validity_gate": "finite + physical rod-hand contact + stable rejoin + lift + hold + no hard torque limit + valid matched no-rod task",
        },
        "candidates": records,
        "pareto_candidates": pareto,
        "screening_best": None if best is None else best["candidate"],
    }
    (args.output_dir / "sixd_kappa_search_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
