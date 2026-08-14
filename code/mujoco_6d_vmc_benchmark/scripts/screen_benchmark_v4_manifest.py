#!/usr/bin/env python3
"""Screen an independent axis-aligned multi-direction physical V4 suite.

V4 leaves the frozen V2/V3 fixtures untouched.  Unlike V2/V3's mirrored
lateral rod, each candidate constructs its own finite-mass MuJoCo rod support,
slide axis, and cylinder orientation for ±x, ±y, or ±z approach.  A fixed
tapered-VMC selector establishes fixture validity only; it is never a ranked
benchmark method.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from run_benchmark import VMCConfig
from run_rod_perturbation_benchmark import ROD_APPROACH_SIDES, run_episode


WARM_START_KAPPA = [27.579838, 52.550787, 48.699427, 35.859580, 40.719830, 34.766858]
EFFECTIVE_FORCE_N = 15.0
EFFECTIVE_IMPULSE_NS = 0.45


def _valid(summary: dict[str, Any], *, require_contact: bool) -> tuple[bool, list[str]]:
    task, rod, torque = summary["task_validity"], summary["rod_diagnostics"], summary["torque"]
    reasons: list[str] = []
    if not task["simulation_finite"]:
        reasons.append("nonfinite")
    if require_contact and not task["rod_hand_contact_observed"]:
        reasons.append("missing_rod_hand_contact")
    if require_contact and rod["peak_contact_force_n"] < EFFECTIVE_FORCE_N:
        reasons.append("below_effective_force")
    if require_contact and rod["contact_impulse_ns"] < EFFECTIVE_IMPULSE_NS:
        reasons.append("below_effective_impulse")
    if require_contact and summary["phase_analysis"]["rejoin_time_s"] is None:
        reasons.append("no_stable_rejoin")
    if not task["target_lifted_after_recovery"]:
        reasons.append("target_not_lifted")
    if not task["target_held_at_end"]:
        reasons.append("target_not_held")
    if torque["hard_limit_fraction"] != 0.0:
        reasons.append("hard_torque_limit")
    return not reasons, reasons


def _impulse_bin(values: list[float], value: float) -> str:
    low, high = np.quantile(np.asarray(values, dtype=float), [1.0 / 3.0, 2.0 / 3.0])
    return "low" if value <= low else "medium" if value <= high else "high"


def _axis(side: str) -> str:
    return side.rsplit("_", maxsplit=1)[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    parser.add_argument("--sides", choices=ROD_APPROACH_SIDES, nargs="+", default=list(ROD_APPROACH_SIDES))
    parser.add_argument("--start-times", type=float, nargs="+", default=[1.020, 1.120])
    parser.add_argument("--strokes", type=float, nargs="+", default=[0.155, 0.170])
    parser.add_argument("--height", type=float, default=0.540)
    parser.add_argument("--rod-center-x", type=float, default=0.55)
    parser.add_argument("--rod-center-y", type=float, default=0.0)
    args = parser.parse_args()
    if not args.sides or not args.start_times or not args.strokes:
        raise ValueError("V4 candidate axes must be non-empty")
    if not 0.0 < args.height or not np.all(np.isfinite((args.rod_center_x, args.rod_center_y))):
        raise ValueError("V4 interaction geometry must be finite and have positive height")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = replace(
        VMCConfig(zeta=0.8),
        carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * 8.0,
        carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * 8.0,
    )
    candidates: list[dict[str, Any]] = []
    for side in args.sides:
        for timing_index, start in enumerate(args.start_times):
            for stroke_index, stroke in enumerate(args.strokes):
                fixture_id = f"v4_{side}_t{timing_index}_s{stroke_index}"
                fixture_dir = args.output_dir / fixture_id
                fixture_dir.mkdir(parents=True, exist_ok=True)
                common = dict(
                    menagerie=args.menagerie, kappa=np.asarray(WARM_START_KAPPA), output_dir=fixture_dir,
                    render_gif=False, config=config, rod_stroke_m=float(stroke), contact_time_constant_s=0.015,
                    recovery_kappa=np.asarray(WARM_START_KAPPA), recovery_ramp_s=0.08,
                    recovery_drive_scale_factor=14.0 / 8.0, grasp_time_s=2.40,
                    rod_start_time_s=float(start), explicit_translational_carriage=True, carriage_mass_kg=1.0,
                    rod_height_m=float(args.height), controller_mode="vmc_taper", rod_approach_side=side,
                    rod_center_x_m=float(args.rod_center_x), rod_center_y_m=float(args.rod_center_y),
                    remove_rod_when_disabled=True,
                    recovery_gate_hold_s=0.28, recovery_gate_taper_s=0.04,
                )
                rod = run_episode(rod_enabled=True, **common)
                no_rod_dir = fixture_dir / "no_rod"
                no_rod_dir.mkdir(parents=True, exist_ok=True)
                no_rod = run_episode(
                    output_dir=no_rod_dir, rod_enabled=False,
                    **{key: value for key, value in common.items() if key != "output_dir"},
                )
                rod_valid, rod_reasons = _valid(rod, require_contact=True)
                no_rod_valid, no_rod_reasons = _valid(no_rod, require_contact=False)
                geometry = rod["rod_motion"]
                candidates.append({
                    "fixture_id": fixture_id, "rod_approach_side": side,
                    "approach_axis": _axis(side), "approach_polarity": side.split("_", maxsplit=1)[0],
                    "timing_bin": "earlier" if timing_index == 0 else "later",
                    "stroke_bin": "moderate" if stroke_index == 0 else "strong",
                    "rod_start_time_s": float(start), "rod_stroke_m": float(stroke),
                    "rod_height_m": float(args.height), "rod_center_x_m": float(args.rod_center_x),
                    "rod_center_y_m": float(args.rod_center_y), "grasp_time_s": 2.40,
                    "physical_geometry": {
                        key: geometry[key] for key in (
                            "support_position_m", "slide_axis_world", "rod_long_axis_world",
                            "cylinder_quaternion_wxyz", "physical_geometry",
                        )
                    },
                    "selector_valid": bool(rod_valid and no_rod_valid),
                    "selector_invalid_reasons": rod_reasons + [f"no_rod:{reason}" for reason in no_rod_reasons],
                    "selector_peak_contact_force_n": rod["rod_diagnostics"]["peak_contact_force_n"],
                    "selector_contact_impulse_ns": rod["rod_diagnostics"]["contact_impulse_ns"],
                    "selector_rejoin_latency_s": rod["phase_analysis"]["release_to_rejoin_latency_s"],
                })
    valid_impulses = [row["selector_contact_impulse_ns"] for row in candidates if row["selector_valid"]]
    selected: list[dict[str, Any]] = []
    for row in candidates:
        row["realized_impulse_bin"] = _impulse_bin(valid_impulses, row["selector_contact_impulse_ns"]) if row["selector_valid"] else None
        if row["selector_valid"]:
            selected.append({key: row[key] for key in (
                "fixture_id", "rod_approach_side", "approach_axis", "approach_polarity",
                "timing_bin", "stroke_bin", "realized_impulse_bin", "rod_start_time_s",
                "rod_stroke_m", "rod_height_m", "rod_center_x_m", "rod_center_y_m", "grasp_time_s", "physical_geometry",
            )})
    manifest = {
        "schema_version": 4,
        "stage": "frozen axis-aligned multi-direction physical rod benchmark",
        "scope": "six physical axis-aligned support/slide/orientation geometries (±x, ±y, ±z); not arbitrary continuous 3-D impact directions",
        "relationship_to_v2_v3": "independent V4 candidate geometry; V2/V3 fixtures and metrics remain frozen",
        "selection_controller": {
            "name": "fixed six-dimensional tapered VMC selector", "kappa_vector": WARM_START_KAPPA,
            "contact_drive_scale": 8.0, "recovery_drive_scale": 14.0,
            "purpose": "fixture validity screening only; never used to rank controllers",
        },
        "effective_collision_gate": {"minimum_peak_contact_force_n": EFFECTIVE_FORCE_N, "minimum_contact_impulse_ns": EFFECTIVE_IMPULSE_NS},
        "validity_gate": "finite + rod-hand contact + effective collision + stable 5 mm/80 ms rejoin + lift + hold + no hard torque limit + valid matched no-rod task",
        "candidate_design": {"approach_sides": args.sides, "start_times_s": args.start_times, "strokes_m": args.strokes, "interaction_height_m": args.height, "rod_center_x_m": args.rod_center_x, "rod_center_y_m": args.rod_center_y},
        "candidates": candidates, "splits": {"train": [], "validation": [], "test": selected},
    }
    args.output_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"candidate_count": len(candidates), "effective_fixture_count": len(selected), "effective_by_axis": {axis: sum(row["approach_axis"] == axis and row["selector_valid"] for row in candidates) for axis in ("x", "y", "z")}, "output_manifest": str(args.output_manifest)}, indent=2))


if __name__ == "__main__":
    main()
