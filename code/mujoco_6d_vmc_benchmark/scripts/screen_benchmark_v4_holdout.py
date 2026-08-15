#!/usr/bin/env python3
"""Screen the frozen V4 five-side, impact-timing holdout fixture set.

The fixture geometry and controller selector are frozen from the V4 development
phase.  This script evaluates only fresh impact timings, producing a test set
for a later rigid/impedance/VMC ladder without retuning any controller.

This is deliberately a five-side axis-coverage test: ``positive_z`` is
excluded because it has not yet met the stable-rejoin validity gate.  It must
not be described as sign-complete or arbitrary 3-D impact coverage.
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


# These five geometries passed the V4 development pilot.  They are intentionally
# copied rather than imported from the pilot script: the pilot remains an
# immutable development record, while this file declares the frozen holdout.
V4_HOLDOUT_CASES = (
    {"rod_approach_side": "negative_x", "rod_stroke_m": 0.080, "rod_height_m": 0.540, "rod_center_x_m": 0.55, "rod_center_y_m": 0.0},
    {"rod_approach_side": "positive_x", "rod_stroke_m": 0.130, "rod_height_m": 0.540, "rod_center_x_m": 0.55, "rod_center_y_m": 0.0},
    {"rod_approach_side": "negative_y", "rod_stroke_m": 0.170, "rod_height_m": 0.540, "rod_center_x_m": 0.55, "rod_center_y_m": 0.0},
    {"rod_approach_side": "positive_y", "rod_stroke_m": 0.170, "rod_height_m": 0.540, "rod_center_x_m": 0.55, "rod_center_y_m": 0.0},
    {"rod_approach_side": "negative_z", "rod_stroke_m": 0.050, "rod_height_m": 0.540, "rod_center_x_m": 0.60, "rod_center_y_m": 0.0},
)

# Neither value overlaps the V4 development-pilot timings (1.060, 1.140 s).
# They are held out impact-timing realizations of the same frozen geometry;
# this is timing generalization, not a claim of geometric generalization.
DEFAULT_HOLDOUT_START_TIMES_S = (0.995, 1.100)
PILOT_START_TIMES_S = (1.060, 1.140)


def _axis(side: str) -> str:
    return side.rsplit("_", maxsplit=1)[1]


def _fixture_row(row: dict[str, Any]) -> dict[str, Any]:
    """Return only immutable replay parameters and explanatory metadata."""
    return {key: row[key] for key in (
        "fixture_id", "rod_approach_side", "approach_axis", "approach_polarity",
        "timing_bin", "realized_impulse_bin", "rod_start_time_s", "rod_stroke_m",
        "rod_height_m", "rod_center_x_m", "rod_center_y_m", "grasp_time_s",
        "remove_rod_when_disabled", "physical_geometry",
    )}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    parser.add_argument("--start-times", type=float, nargs="+", default=list(DEFAULT_HOLDOUT_START_TIMES_S))
    args = parser.parse_args()
    if not args.start_times:
        raise ValueError("V4 holdout requires one or more held-out impact times")
    if set(args.start_times) & set(PILOT_START_TIMES_S):
        raise ValueError("V4 holdout timings must not overlap the V4 development pilot")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    config = replace(
        VMCConfig(zeta=0.8),
        carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * 8.0,
        carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * 8.0,
    )
    candidates: list[dict[str, Any]] = []
    for case_index, case in enumerate(V4_HOLDOUT_CASES):
        for timing_index, start_time_s in enumerate(args.start_times):
            fixture_id = f"v4holdout_{case['rod_approach_side']}_c{case_index}_t{timing_index}"
            fixture_dir = args.output_dir / fixture_id
            fixture_dir.mkdir(parents=True, exist_ok=True)
            common = dict(
                menagerie=args.menagerie, kappa=np.asarray(WARM_START_KAPPA), output_dir=fixture_dir,
                render_gif=False, config=config, contact_time_constant_s=0.015,
                recovery_kappa=np.asarray(WARM_START_KAPPA), recovery_ramp_s=0.08,
                recovery_drive_scale_factor=14.0 / 8.0, grasp_time_s=2.40,
                rod_start_time_s=float(start_time_s), explicit_translational_carriage=True,
                carriage_mass_kg=1.0, controller_mode="vmc_taper",
                remove_rod_when_disabled=True, recovery_gate_hold_s=0.28,
                recovery_gate_taper_s=0.04, **case,
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
                "fixture_id": fixture_id, **case,
                "approach_axis": _axis(case["rod_approach_side"]),
                "approach_polarity": case["rod_approach_side"].split("_", maxsplit=1)[0],
                "timing_bin": "early_holdout" if timing_index == 0 else "late_holdout",
                "rod_start_time_s": float(start_time_s), "grasp_time_s": 2.40,
                "remove_rod_when_disabled": True,
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
    selected: list[dict[str, Any]] = []
    for row in candidates:
        row["realized_impulse_bin"] = _impulse_bin(valid_impulses, row["selector_contact_impulse_ns"]) if row["selector_valid"] else None
        if row["selector_valid"]:
            selected.append(_fixture_row(row))
    manifest = {
        "schema_version": 4,
        "stage": "frozen V4 five-side axis-coverage holdout benchmark",
        "scope": "five physically validated axis-aligned approach sides across x/y/z; not sign-complete because positive_z remains excluded; not arbitrary continuous 3-D impact",
        "relationship_to_v2_v3_v4_pilot": "V2/V3 and the V4 geometry-development pilot were not used to tune a controller here. This is a held-out impact-timing realization of the frozen five-side geometry, not an independent geometry-generalization claim.",
        "selection_controller": {
            "name": "fixed six-dimensional tapered VMC selector", "kappa_vector": WARM_START_KAPPA,
            "contact_drive_scale": 8.0, "recovery_drive_scale": 14.0,
            "purpose": "fixture validity screening only; never used to rank controllers or tune their parameters",
        },
        "effective_collision_gate": {
            "minimum_peak_contact_force_n": EFFECTIVE_FORCE_N,
            "minimum_contact_impulse_ns": EFFECTIVE_IMPULSE_NS,
        },
        "validity_gate": "finite + rod-hand contact + effective collision + stable 5 mm/80 ms rejoin + lift + hold + no hard torque limit + valid matched no-rod task",
        "candidate_design": {
            "frozen_cases": list(V4_HOLDOUT_CASES), "held_out_start_times_s": args.start_times,
            "excluded_development_pilot_start_times_s": list(PILOT_START_TIMES_S),
        },
        "candidates": candidates,
        "splits": {"development": [], "train": [], "validation": [], "test": selected},
    }
    args.output_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({
        "candidate_count": len(candidates), "effective_fixture_count": len(selected),
        "effective_by_axis": {axis: sum(row["approach_axis"] == axis and row["selector_valid"] for row in candidates) for axis in ("x", "y", "z")},
        "output_manifest": str(args.output_manifest),
    }, indent=2))


if __name__ == "__main__":
    main()
