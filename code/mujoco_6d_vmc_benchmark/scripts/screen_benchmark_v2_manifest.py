#!/usr/bin/env python3
"""Physically screen and freeze the direction/time/impulse-stratified V2 suite.

Candidate geometry is never ranked by controller score.  A fixed, declared
six-channel VMC selector merely establishes whether a candidate is an
effective, task-valid physical rod collision.  Every retained fixture is then
frozen for all later controller comparisons.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from run_benchmark import VMCConfig
from run_rod_perturbation_benchmark import run_episode


WARM_START_KAPPA = [27.579838, 52.550787, 48.699427, 35.859580, 40.719830, 34.766858]
EFFECTIVE_FORCE_N = 15.0
EFFECTIVE_IMPULSE_NS = 0.45


def _valid(summary: dict[str, Any], *, require_contact: bool) -> tuple[bool, list[str]]:
    task = summary["task_validity"]
    rod = summary["rod_diagnostics"]
    torque = summary["torque"]
    failures: list[str] = []
    if not task["simulation_finite"]:
        failures.append("nonfinite")
    if require_contact and not task["rod_hand_contact_observed"]:
        failures.append("missing_rod_hand_contact")
    if require_contact and rod["peak_contact_force_n"] < EFFECTIVE_FORCE_N:
        failures.append("below_effective_force")
    if require_contact and rod["contact_impulse_ns"] < EFFECTIVE_IMPULSE_NS:
        failures.append("below_effective_impulse")
    if require_contact and summary["phase_analysis"]["rejoin_time_s"] is None:
        failures.append("no_stable_rejoin")
    if not task["target_lifted_after_recovery"]:
        failures.append("target_not_lifted")
    if not task["target_held_at_end"]:
        failures.append("target_not_held")
    if torque["hard_limit_fraction"] != 0.0:
        failures.append("hard_torque_limit")
    return not failures, failures


def _impulse_bin(values: list[float], value: float) -> str:
    if len(values) < 3:
        return "unbinned"
    low, high = np.quantile(np.asarray(values, dtype=float), [1.0 / 3.0, 2.0 / 3.0])
    return "low" if value <= low else "medium" if value <= high else "high"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    parser.add_argument("--strokes", type=float, nargs="+", default=[0.160, 0.170, 0.175])
    parser.add_argument("--start-times", type=float, nargs="+", default=[1.020, 1.080, 1.140])
    parser.add_argument("--height", type=float, default=0.540)
    parser.add_argument("--grasp-time", type=float, default=2.40)
    parser.add_argument("--force-threshold", type=float, default=EFFECTIVE_FORCE_N)
    parser.add_argument("--impulse-threshold", type=float, default=EFFECTIVE_IMPULSE_NS)
    args = parser.parse_args()
    if args.force_threshold != EFFECTIVE_FORCE_N or args.impulse_threshold != EFFECTIVE_IMPULSE_NS:
        raise ValueError("V2 uses the frozen 15 N / 0.45 Ns effective-collision gate")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = replace(
        VMCConfig(zeta=0.8),
        carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * 8.0,
        carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * 8.0,
    )
    candidates: list[dict[str, Any]] = []
    for side in ("negative_y", "positive_y"):
        for timing_index, start in enumerate(args.start_times):
            for stroke_index, stroke in enumerate(args.strokes):
                fixture_id = f"v2_{side}_t{timing_index}_s{stroke_index}"
                fixture_dir = args.output_dir / fixture_id
                common = dict(
                    menagerie=args.menagerie, kappa=np.asarray(WARM_START_KAPPA), output_dir=fixture_dir,
                    render_gif=False, config=config, rod_stroke_m=float(stroke), contact_time_constant_s=0.015,
                    recovery_kappa=np.asarray(WARM_START_KAPPA), recovery_ramp_s=0.08,
                    recovery_drive_scale_factor=14.0 / 8.0, grasp_time_s=args.grasp_time,
                    rod_start_time_s=float(start), explicit_translational_carriage=True, carriage_mass_kg=1.0,
                    rod_height_m=args.height, controller_mode="vmc_taper", rod_approach_side=side,
                    recovery_gate_hold_s=0.28, recovery_gate_taper_s=0.04,
                )
                rod = run_episode(rod_enabled=True, **common)
                no_rod = run_episode(output_dir=fixture_dir / "no_rod", rod_enabled=False, **{key: value for key, value in common.items() if key != "output_dir"})
                rod_valid, rod_failures = _valid(rod, require_contact=True)
                no_rod_valid, no_rod_failures = _valid(no_rod, require_contact=False)
                candidates.append({
                    "fixture_id": fixture_id,
                    "rod_approach_side": side,
                    "timing_bin": ("early", "middle", "late")[timing_index] if len(args.start_times) == 3 else f"timing_{timing_index}",
                    "requested_stroke_bin": ("low", "medium", "high")[stroke_index] if len(args.strokes) == 3 else f"stroke_{stroke_index}",
                    "rod_stroke_m": float(stroke), "rod_height_m": args.height,
                    "rod_start_time_s": float(start), "grasp_time_s": args.grasp_time,
                    "selector_valid": bool(rod_valid and no_rod_valid),
                    "selector_invalid_reasons": rod_failures + [f"no_rod:{item}" for item in no_rod_failures],
                    "selector_peak_contact_force_n": rod["rod_diagnostics"]["peak_contact_force_n"],
                    "selector_contact_impulse_ns": rod["rod_diagnostics"]["contact_impulse_ns"],
                    "selector_rejoin_latency_s": rod["phase_analysis"]["release_to_rejoin_latency_s"],
                })
    impulses = [row["selector_contact_impulse_ns"] for row in candidates if row["selector_valid"]]
    selected = []
    for row in candidates:
        row["realized_impulse_bin"] = _impulse_bin(impulses, row["selector_contact_impulse_ns"]) if row["selector_valid"] else None
        if row["selector_valid"]:
            selected.append({key: row[key] for key in (
                "fixture_id", "rod_approach_side", "timing_bin", "requested_stroke_bin", "realized_impulse_bin",
                "rod_stroke_m", "rod_height_m", "rod_start_time_s", "grasp_time_s",
            )})
    manifest = {
        "schema_version": 2,
        "stage": "frozen direction/time/impulse-stratified physical rod benchmark",
        "selection_controller": {
            "name": "fixed six-dimensional tapered VMC selector",
            "kappa_vector": WARM_START_KAPPA,
            "contact_drive_scale": 8.0,
            "recovery_drive_scale": 14.0,
            "error_gate_hold_s": 0.28,
            "error_gate_taper_s": 0.04,
            "purpose": "fixture validity screening only; never used to rank controllers",
        },
        "effective_collision_gate": {"minimum_peak_contact_force_n": EFFECTIVE_FORCE_N, "minimum_contact_impulse_ns": EFFECTIVE_IMPULSE_NS},
        "validity_gate": "finite + rod-hand contact + effective collision + stable 5 mm/80 ms rejoin + lift + hold + no hard torque limit + valid matched no-rod task",
        "candidate_design": {"approach_sides": ["negative_y", "positive_y"], "start_times_s": args.start_times, "strokes_m": args.strokes, "height_m": args.height},
        "candidates": candidates,
        "splits": {"train": [], "validation": [], "test": selected},
    }
    args.output_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"candidate_count": len(candidates), "effective_fixture_count": len(selected), "output_manifest": str(args.output_manifest)}, indent=2))


if __name__ == "__main__":
    main()
