#!/usr/bin/env python3
"""Run a reproducible multi-axis V4 *development* pilot after geometry probes.

This is intentionally not a final controller-ranking test set.  Its role is
to verify that the geometries selected by physical development probes retain
valid collisions, recovery, and grasp success at two fresh impact times.
V2/V3 remain frozen and untouched; a future V4 holdout must use geometries and
timings not used here.
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
from screen_benchmark_v4_manifest import EFFECTIVE_FORCE_N, EFFECTIVE_IMPULSE_NS, WARM_START_KAPPA, _impulse_bin, _valid


V4_AXIS_PILOT_CASES = (
    {"rod_approach_side": "negative_x", "rod_stroke_m": 0.080, "rod_height_m": 0.540, "rod_center_x_m": 0.55, "rod_center_y_m": 0.0},
    {"rod_approach_side": "positive_x", "rod_stroke_m": 0.130, "rod_height_m": 0.540, "rod_center_x_m": 0.55, "rod_center_y_m": 0.0},
    {"rod_approach_side": "negative_y", "rod_stroke_m": 0.170, "rod_height_m": 0.540, "rod_center_x_m": 0.55, "rod_center_y_m": 0.0},
    {"rod_approach_side": "positive_y", "rod_stroke_m": 0.170, "rod_height_m": 0.540, "rod_center_x_m": 0.55, "rod_center_y_m": 0.0},
    {"rod_approach_side": "negative_z", "rod_stroke_m": 0.050, "rod_height_m": 0.540, "rod_center_x_m": 0.60, "rod_center_y_m": 0.0},
)


def _axis(side: str) -> str:
    return side.rsplit("_", maxsplit=1)[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    parser.add_argument("--start-times", type=float, nargs="+", default=[1.060, 1.140])
    args = parser.parse_args()
    if not args.start_times:
        raise ValueError("V4 axis pilot requires one or more fresh start times")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = replace(
        VMCConfig(zeta=0.8),
        carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * 8.0,
        carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * 8.0,
    )
    candidates: list[dict[str, Any]] = []
    for case_index, case in enumerate(V4_AXIS_PILOT_CASES):
        for timing_index, start_time_s in enumerate(args.start_times):
            fixture_id = f"v4pilot_{case['rod_approach_side']}_c{case_index}_t{timing_index}"
            fixture_dir = args.output_dir / fixture_id
            fixture_dir.mkdir(parents=True, exist_ok=True)
            common = dict(
                menagerie=args.menagerie, kappa=np.asarray(WARM_START_KAPPA), output_dir=fixture_dir,
                render_gif=False, config=config, contact_time_constant_s=0.015,
                recovery_kappa=np.asarray(WARM_START_KAPPA), recovery_ramp_s=0.08,
                recovery_drive_scale_factor=14.0 / 8.0, grasp_time_s=2.40,
                rod_start_time_s=float(start_time_s), explicit_translational_carriage=True, carriage_mass_kg=1.0,
                controller_mode="vmc_taper", remove_rod_when_disabled=True,
                recovery_gate_hold_s=0.28, recovery_gate_taper_s=0.04, **case,
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
                "fixture_id": fixture_id, **case, "approach_axis": _axis(case["rod_approach_side"]),
                "approach_polarity": case["rod_approach_side"].split("_", maxsplit=1)[0],
                "timing_bin": "earlier" if timing_index == 0 else "later", "rod_start_time_s": float(start_time_s),
                "grasp_time_s": 2.40,
                "physical_geometry": {key: geometry[key] for key in (
                    "support_position_m", "slide_axis_world", "rod_long_axis_world",
                    "cylinder_quaternion_wxyz", "physical_geometry",
                )},
                "selector_valid": bool(rod_valid and no_rod_valid),
                "selector_invalid_reasons": rod_reasons + [f"no_rod:{reason}" for reason in no_rod_reasons],
                "selector_peak_contact_force_n": rod["rod_diagnostics"]["peak_contact_force_n"],
                "selector_contact_impulse_ns": rod["rod_diagnostics"]["contact_impulse_ns"],
                "selector_rejoin_latency_s": rod["phase_analysis"]["release_to_rejoin_latency_s"],
            })
    valid_impulses = [row["selector_contact_impulse_ns"] for row in candidates if row["selector_valid"]]
    development = []
    for row in candidates:
        row["realized_impulse_bin"] = _impulse_bin(valid_impulses, row["selector_contact_impulse_ns"]) if row["selector_valid"] else None
        if row["selector_valid"]:
            development.append({key: row[key] for key in row if key not in {"selector_valid", "selector_invalid_reasons", "selector_peak_contact_force_n", "selector_contact_impulse_ns", "selector_rejoin_latency_s"}})
    manifest = {
        "schema_version": 4,
        "stage": "V4 axis-coverage geometry development pilot",
        "scope": "five physically instantiated axis-aligned approach sides across x/y/z; not sign-complete because positive_z did not satisfy stable rejoin during geometry development",
        "use_restriction": "development validation only; do not use for final controller ranking or as an independent V4 test claim",
        "relationship_to_v2_v3": "independent V4 geometry development; frozen V2/V3 fixtures and metrics are not modified",
        "selection_controller": {"name": "fixed six-dimensional tapered VMC selector", "kappa_vector": WARM_START_KAPPA, "purpose": "fixture validity only"},
        "effective_collision_gate": {"minimum_peak_contact_force_n": EFFECTIVE_FORCE_N, "minimum_contact_impulse_ns": EFFECTIVE_IMPULSE_NS},
        "validity_gate": "finite + rod-hand contact + effective collision + stable 5 mm/80 ms rejoin + lift + hold + no hard torque limit + valid matched no-rod task",
        "candidate_design": {"cases": list(V4_AXIS_PILOT_CASES), "fresh_start_times_s": args.start_times},
        "candidates": candidates,
        "splits": {"development": development, "train": [], "validation": [], "test": []},
    }
    args.output_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"candidate_count": len(candidates), "effective_fixture_count": len(development), "effective_by_axis": {axis: sum(row["approach_axis"] == axis and row["selector_valid"] for row in candidates) for axis in ("x", "y", "z")}, "output_manifest": str(args.output_manifest)}, indent=2))


if __name__ == "__main__":
    main()
