#!/usr/bin/env python3
"""Create an independent WBC-aware fixture pool for ESN selection only.

This generator leaves every V2/V3/V4 artifact untouched.  It physical-screens
new timing realizations with a frozen VMC-gated selector, then assigns valid
fixtures to ESN train/validation splits.  It never creates an ESN test set:
the frozen WBC-aware V4 ladder remains the later final evaluation boundary.
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


# Physical rod geometries established in V4 development.  A fixture is defined
# by geometry *and timing*; all timing values below are new and excluded from
# V2/V3/V4/PPO historical runs listed in the training protocol.
ESN_WBC_CASES = (
    {"rod_approach_side": "negative_x", "rod_stroke_m": 0.080, "rod_height_m": 0.540, "rod_center_x_m": 0.55, "rod_center_y_m": 0.0},
    {"rod_approach_side": "positive_x", "rod_stroke_m": 0.130, "rod_height_m": 0.540, "rod_center_x_m": 0.55, "rod_center_y_m": 0.0},
    {"rod_approach_side": "negative_y", "rod_stroke_m": 0.170, "rod_height_m": 0.540, "rod_center_x_m": 0.55, "rod_center_y_m": 0.0},
    {"rod_approach_side": "positive_y", "rod_stroke_m": 0.170, "rod_height_m": 0.540, "rod_center_x_m": 0.55, "rod_center_y_m": 0.0},
    {"rod_approach_side": "negative_z", "rod_stroke_m": 0.050, "rod_height_m": 0.540, "rod_center_x_m": 0.60, "rod_center_y_m": 0.0},
)
DEFAULT_TRAIN_START_TIMES_S = (0.930, 1.180)
DEFAULT_VALIDATION_START_TIMES_S = (0.955, 1.205)
HISTORICAL_START_TIMES_S = (
    0.980, 0.995, 1.020, 1.040, 1.0423509355133431, 1.0535300287689722,
    1.055, 1.060, 1.0629702374023486, 1.070, 1.0781610928318661, 1.085,
    1.0863016782046457, 1.0954695590692798, 1.100, 1.107206213053218,
    1.111581734716849, 1.115, 1.120, 1.140, 1.160,
)


def _axis(side: str) -> str:
    return side.rsplit("_", maxsplit=1)[1]


def _fixture_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: row[key] for key in (
        "fixture_id", "split", "rod_approach_side", "approach_axis", "approach_polarity",
        "timing_bin", "realized_impulse_bin", "rod_start_time_s", "rod_stroke_m",
        "rod_height_m", "rod_center_x_m", "rod_center_y_m", "grasp_time_s",
        "remove_rod_when_disabled", "physical_geometry",
    )}


def _assert_fresh_times(train_times: tuple[float, ...], validation_times: tuple[float, ...]) -> None:
    all_times = (*train_times, *validation_times)
    if not train_times or not validation_times or not np.all(np.isfinite(all_times)):
        raise ValueError("ESN train and validation timing sets must both be non-empty and finite")
    if len(set(all_times)) != len(all_times):
        raise ValueError("train and validation impact timings must be disjoint")
    if any(np.isclose(candidate, historical, atol=1e-9) for candidate in all_times for historical in HISTORICAL_START_TIMES_S):
        raise ValueError("ESN timing values must not overlap the recorded V2/V3/V4/PPO timing list")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    parser.add_argument("--train-start-times", type=float, nargs="+", default=list(DEFAULT_TRAIN_START_TIMES_S))
    parser.add_argument("--validation-start-times", type=float, nargs="+", default=list(DEFAULT_VALIDATION_START_TIMES_S))
    parser.add_argument(
        "--sides", choices=[case["rod_approach_side"] for case in ESN_WBC_CASES], nargs="+",
        default=[case["rod_approach_side"] for case in ESN_WBC_CASES],
        help="Optional physical pre-screen subset. A final manifest must retain all intended sides.",
    )
    args = parser.parse_args()
    train_times, validation_times = tuple(args.train_start_times), tuple(args.validation_start_times)
    _assert_fresh_times(train_times, validation_times)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    config = replace(
        VMCConfig(zeta=0.8),
        carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * 8.0,
        carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * 8.0,
    )
    candidates: list[dict[str, Any]] = []
    split_times = (("train", train_times), ("validation", validation_times))
    for split, times in split_times:
        for case_index, case in enumerate(ESN_WBC_CASES):
            if case["rod_approach_side"] not in args.sides:
                continue
            for timing_index, start_time_s in enumerate(times):
                fixture_id = f"esn_wbc_{split}_{case['rod_approach_side']}_c{case_index}_t{timing_index}"
                fixture_dir = args.output_dir / fixture_id
                fixture_dir.mkdir(parents=True, exist_ok=True)
                common = dict(
                    menagerie=args.menagerie, kappa=np.asarray(WARM_START_KAPPA), output_dir=fixture_dir,
                    render_gif=False, config=config, contact_time_constant_s=0.015,
                    recovery_kappa=np.asarray(WARM_START_KAPPA), recovery_ramp_s=0.08,
                    recovery_drive_scale_factor=14.0 / 8.0, grasp_time_s=2.40,
                    rod_start_time_s=float(start_time_s), explicit_translational_carriage=True,
                    carriage_mass_kg=1.0, controller_mode="vmc_gated", remove_rod_when_disabled=True,
                    recovery_gate_hold_s=0.28, recovery_gate_taper_s=0.04,
                    reference_source="fixed_panda_wbc", **case,
                )
                rod = run_episode(rod_enabled=True, **common)
                no_rod_dir = fixture_dir / "no_rod"
                no_rod_dir.mkdir(parents=True, exist_ok=True)
                no_rod = run_episode(output_dir=no_rod_dir, rod_enabled=False, **{key: value for key, value in common.items() if key != "output_dir"})
                rod_valid, rod_reasons = _valid(rod, require_contact=True)
                no_rod_valid, no_rod_reasons = _valid(no_rod, require_contact=False)
                geometry = rod["rod_motion"]
                candidates.append({
                    "fixture_id": fixture_id, "split": split, **case,
                    "approach_axis": _axis(case["rod_approach_side"]),
                    "approach_polarity": case["rod_approach_side"].split("_", maxsplit=1)[0],
                    "timing_bin": f"{split}_{timing_index}", "rod_start_time_s": float(start_time_s),
                    "grasp_time_s": 2.40, "remove_rod_when_disabled": True,
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
    for row in candidates:
        row["realized_impulse_bin"] = _impulse_bin(valid_impulses, row["selector_contact_impulse_ns"]) if row["selector_valid"] else None
    selected = [_fixture_row(row) for row in candidates if row["selector_valid"]]
    manifest = {
        "schema_version": 1,
        "stage": "WBC-aware ESN train/validation physical fixture screening",
        "scope": "new impact-timing realizations over five physically validated axis-aligned rod geometries; not sign-complete because positive_z remains excluded; not arbitrary continuous 3-D impact coverage",
        "data_boundary": "V2/V3/V4 artifacts are frozen. This manifest is the only allowable pool for ESN readout/hyperparameter/safety selection. The frozen WBC-aware V4 ladder remains a later one-shot test and must not be used for selection.",
        "reference_source": "fixed_panda_wbc",
        "selection_controller": {
            "name": "fixed six-dimensional VMC-gated selector", "kappa_vector": WARM_START_KAPPA,
            "contact_drive_scale": 8.0, "recovery_drive_scale": 14.0,
            "purpose": "fixture validity screening only; never an ESN teacher, ranking method or tuning target",
        },
        "effective_collision_gate": {"minimum_peak_contact_force_n": EFFECTIVE_FORCE_N, "minimum_contact_impulse_ns": EFFECTIVE_IMPULSE_NS},
        "validity_gate": "finite + rod-hand contact + effective collision + stable 5 mm/80 ms rejoin + lift + hold + no hard torque limit + valid matched no-rod task",
        "candidate_design": {
            "cases": [case for case in ESN_WBC_CASES if case["rod_approach_side"] in args.sides], "train_start_times_s": list(train_times),
            "validation_start_times_s": list(validation_times),
            "excluded_recorded_v2_v3_v4_ppo_start_times_s": list(HISTORICAL_START_TIMES_S),
        },
        "candidates": candidates,
        "splits": {
            "train": [row for row in selected if row["split"] == "train"],
            "validation": [row for row in selected if row["split"] == "validation"],
            "test": [],
        },
    }
    args.output_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({
        "candidate_count": len(candidates),
        "effective_train_fixture_count": len(manifest["splits"]["train"]),
        "effective_validation_fixture_count": len(manifest["splits"]["validation"]),
        "effective_by_axis": {axis: sum(row["approach_axis"] == axis and row["selector_valid"] for row in candidates) for axis in ("x", "y", "z")},
        "output_manifest": str(args.output_manifest),
    }, indent=2))


if __name__ == "__main__":
    main()
