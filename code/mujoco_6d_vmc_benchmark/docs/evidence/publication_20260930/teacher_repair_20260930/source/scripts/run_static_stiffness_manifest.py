#!/usr/bin/env python3
"""Evaluate a predeclared stiffness-training manifest before any RL training.

Every static sample receives a physical rod run and a matched no-rod task run.
The runner is resumable: completed sample summaries are reused. This creates
the safe initialization set and held-out evaluation protocol for later RL; it
does not train a policy itself.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

from run_rod_perturbation_benchmark import kappa_filename_tag


SCRIPT_DIR = Path(__file__).resolve().parent
RUNNER = SCRIPT_DIR / "run_rod_perturbation_benchmark.py"


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


def _paired_metrics(rod_trace: Path, no_rod_trace: Path) -> dict[str, float]:
    with np.load(rod_trace) as rod, np.load(no_rod_trace) as no_rod:
        if rod["time"].shape != no_rod["time"].shape or not np.allclose(rod["time"], no_rod["time"]):
            raise RuntimeError("paired traces do not share a time grid")
        offset = np.linalg.norm(rod["ee_position"] - no_rod["ee_position"], axis=1)
        return {
            "peak_paired_rod_offset_mm": float(np.max(offset) * 1000.0),
            "paired_offset_rmse_mm": float(np.sqrt(np.mean(offset**2)) * 1000.0),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--splits", nargs="+", choices=("train", "validation", "test"), default=["train", "validation", "test"])
    parser.add_argument("--max-samples", type=int, default=None, help="Optional pilot limit across requested splits.")
    parser.add_argument("--damping-ratio", type=float, default=0.8)
    parser.add_argument("--carriage-drive-scale", type=float, default=8.0)
    parser.add_argument(
        "--recovery-carriage-drive-scale", type=float, default=None,
        help="Absolute carriage drive after rod release; default keeps the contact-stage scale.",
    )
    parser.add_argument("--carriage-mass-kg", type=float, default=1.0)
    parser.add_argument(
        "--kappa-vector", type=float, nargs=6, default=None,
        metavar=("KX", "KY", "KZ", "KROLL", "KPITCH", "KYAW"),
        help="Optional fixed six-spring baseline overriding each manifest sample's initial vector.",
    )
    parser.add_argument("--minimum-peak-contact-force-n", type=float, default=15.0)
    parser.add_argument("--minimum-contact-impulse-ns", type=float, default=0.45)
    args = parser.parse_args()
    recovery_drive = args.carriage_drive_scale if args.recovery_carriage_drive_scale is None else args.recovery_carriage_drive_scale
    if min(args.damping_ratio, args.carriage_drive_scale, recovery_drive, args.carriage_mass_kg, args.minimum_peak_contact_force_n, args.minimum_contact_impulse_ns) <= 0.0:
        raise ValueError("controller scales must be positive")
    manifest = _load(args.manifest)
    samples = [sample for split in args.splits for sample in manifest["splits"][split]]
    if args.max_samples is not None:
        if args.max_samples < 1:
            raise ValueError("max-samples must be positive")
        samples = samples[:args.max_samples]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for sample in samples:
        vector = args.kappa_vector if args.kappa_vector is not None else sample["initial_kappa_vector"]
        tag = kappa_filename_tag(np.asarray(vector, dtype=float))
        summary_name = f"rod_perturbation_{tag}_summary.json"
        trace_name = f"rod_perturbation_{tag}_trace.npz"
        sample_dir = args.output_dir / sample["sample_id"]
        rod_dir, no_rod_dir = sample_dir / "rod", sample_dir / "no_rod"
        common = [
            "--menagerie", str(args.menagerie), "--controller-mode", "vmc",
            "--kappa-vector", *(str(value) for value in vector),
            "--damping-ratio", str(args.damping_ratio), "--carriage-drive-scale", str(args.carriage_drive_scale),
            "--recovery-carriage-drive-scale", str(recovery_drive), "--recovery-ramp", "0.08",
            "--contact-time-constant", "0.015", "--rod-stroke", str(sample["rod_stroke_m"]),
            "--rod-height", str(sample["rod_height_m"]), "--rod-start-time", str(sample["rod_start_time_s"]),
            "--grasp-time", str(sample["grasp_time_s"]), "--explicit-translational-carriage",
            "--carriage-mass-kg", str(args.carriage_mass_kg),
        ]
        if not (rod_dir / summary_name).is_file():
            _run([sys.executable, str(RUNNER), "--output-dir", str(rod_dir), *common])
        if not (no_rod_dir / summary_name).is_file():
            _run([sys.executable, str(RUNNER), "--output-dir", str(no_rod_dir), *common, "--disable-rod"])
        rod_summary, no_rod_summary = _load(rod_dir / summary_name), _load(no_rod_dir / summary_name)
        valid, failures = _valid(rod_summary, require_contact=True)
        diagnostics = rod_summary["rod_diagnostics"]
        if diagnostics["peak_contact_force_n"] < args.minimum_peak_contact_force_n:
            valid = False
            failures.append("ineffective_collision:peak_force")
        if diagnostics["contact_impulse_ns"] < args.minimum_contact_impulse_ns:
            valid = False
            failures.append("ineffective_collision:impulse")
        paired_valid, paired_failures = _valid(no_rod_summary, require_contact=False)
        if not paired_valid:
            valid = False
            failures += [f"no_rod:{failure}" for failure in paired_failures]
        record = {
            "sample_id": sample["sample_id"], "split": sample["split"], "kappa_vector": vector,
            "fixture": {key: sample[key] for key in ("rod_stroke_m", "rod_height_m", "rod_start_time_s", "grasp_time_s")},
            "valid": valid, "invalid_reasons": failures,
            **_paired_metrics(rod_dir / trace_name, no_rod_dir / trace_name),
            "recovery_rmse_mm": rod_summary["tracking"]["recovery_position_rmse_m"] * 1000.0,
            "rejoin_latency_s": rod_summary["phase_analysis"]["release_to_rejoin_latency_s"],
            "peak_torque_nm": rod_summary["torque"]["applied_peak_nm"],
            "jerk_peak_mps3": rod_summary["motion"]["jerk_peak_mps3"],
            "peak_contact_force_n": rod_summary["rod_diagnostics"]["peak_contact_force_n"],
            "contact_impulse_ns": diagnostics["contact_impulse_ns"],
        }
        records.append(record)
    report = {
        "manifest": str(args.manifest), "requested_splits": args.splits, "sample_count": len(records),
        "valid_count": sum(record["valid"] for record in records),
        "controller_override": {
            "kappa_vector": None if args.kappa_vector is None else list(args.kappa_vector),
            "carriage_drive_scale": args.carriage_drive_scale,
            "recovery_carriage_drive_scale": recovery_drive,
        },
        "validity_gate": manifest["training_contract"]["validity_gate"],
        "effective_collision_gate": {
            "minimum_peak_contact_force_n": args.minimum_peak_contact_force_n,
            "minimum_contact_impulse_ns": args.minimum_contact_impulse_ns,
        },
        "records": records,
    }
    (args.output_dir / "static_stiffness_manifest_results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
