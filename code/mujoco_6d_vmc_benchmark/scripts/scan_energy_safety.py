#!/usr/bin/env python3
"""Select an energy-safety configuration on a held-out physical validation set.

The validation geometries are deliberately distinct from frozen V2 and V3
fixtures.  V2/V3 must not be used to tune the tank or smoothing parameters.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import numpy as np

from energy_safety import EnergySafetyConfig
from run_benchmark import VMCConfig
from run_rod_perturbation_benchmark import run_episode


KAPPA_6D = np.asarray([27.579838, 52.550787, 48.699427, 35.859580, 40.719830, 34.766858])
FORCE_GATE_N = 15.0
IMPULSE_GATE_NS = 0.45
METRICS = (
    "recovery_rmse_mm", "recovery_iae_mm_s", "rejoin_latency_s", "post_contact_jerk_p95_mps3",
    "peak_torque_nm", "torque_rate_peak_nmps", "peak_contact_force_n", "contact_impulse_ns",
    "minimum_tank_energy_j", "mean_tank_energy_j", "mean_direction_scale", "mean_energy_scale",
)


def _valid(summary: dict[str, Any], *, no_rod: bool) -> tuple[bool, list[str]]:
    task, torque, rod = summary["task_validity"], summary["torque"], summary["rod_diagnostics"]
    reasons: list[str] = []
    if not task["simulation_finite"]:
        reasons.append("nonfinite")
    if not no_rod and not task["rod_hand_contact_observed"]:
        reasons.append("missing_rod_hand_contact")
    if not no_rod and rod["peak_contact_force_n"] < FORCE_GATE_N:
        reasons.append("below_effective_force")
    if not no_rod and rod["contact_impulse_ns"] < IMPULSE_GATE_NS:
        reasons.append("below_effective_impulse")
    if not no_rod and summary["phase_analysis"]["rejoin_time_s"] is None:
        reasons.append("no_stable_rejoin")
    if not task["target_lifted_after_recovery"]:
        reasons.append("target_not_lifted")
    if not task["target_held_at_end"]:
        reasons.append("target_not_held")
    if torque["hard_limit_fraction"] != 0.0:
        reasons.append("hard_torque_limit")
    return not reasons, reasons


def _fixture_candidates() -> list[dict[str, Any]]:
    """16 distinct timing/height combinations, not present in V2 or V3."""
    fixtures = []
    for side in ("negative_y", "positive_y"):
        for start in (1.040, 1.100):
            for stroke in (0.165, 0.170):
                for height in (0.535, 0.545):
                    fixtures.append({
                        "fixture_id": f"val_{side}_t{start:.3f}_s{stroke:.3f}_h{height:.3f}".replace(".", "p"),
                        "rod_approach_side": side, "rod_start_time_s": start,
                        "rod_stroke_m": stroke, "rod_height_m": height, "grasp_time_s": 2.40,
                    })
    return fixtures


def _common(menagerie: Path, fixture: dict[str, Any], controller_mode: str, config: VMCConfig, energy_config: EnergySafetyConfig | None = None) -> dict[str, Any]:
    uses_carriage = controller_mode.startswith("vmc")
    return dict(
        menagerie=menagerie, kappa=KAPPA_6D, render_gif=False, config=config,
        rod_stroke_m=fixture["rod_stroke_m"], contact_time_constant_s=0.015,
        recovery_kappa=KAPPA_6D, recovery_ramp_s=0.08, recovery_drive_scale_factor=14.0 / 8.0,
        grasp_time_s=fixture["grasp_time_s"], rod_start_time_s=fixture["rod_start_time_s"],
        explicit_translational_carriage=uses_carriage, carriage_mass_kg=1.0,
        rod_height_m=fixture["rod_height_m"], controller_mode=controller_mode,
        rod_approach_side=fixture["rod_approach_side"], recovery_gate_hold_s=0.28,
        recovery_gate_taper_s=0.04, energy_safety_config=energy_config,
    )


def _run_pair(
    menagerie: Path, root: Path, fixture: dict[str, Any], label: str, controller_mode: str,
    config: VMCConfig, energy_config: EnergySafetyConfig | None,
) -> dict[str, Any]:
    run_dir = root / label / fixture["fixture_id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    common = _common(menagerie, fixture, controller_mode, config, energy_config)
    rod = run_episode(output_dir=run_dir, rod_enabled=True, **common)
    no_rod_dir = run_dir / "no_rod"
    no_rod_dir.mkdir(parents=True, exist_ok=True)
    no_rod = run_episode(output_dir=no_rod_dir, rod_enabled=False, **common)
    rod_valid, rod_reasons = _valid(rod, no_rod=False)
    no_rod_valid, no_rod_reasons = _valid(no_rod, no_rod=True)
    safety = rod["stiffness_schedule"]["energy_budget_safety"]
    return {
        "label": label, "fixture_id": fixture["fixture_id"], "valid": rod_valid and no_rod_valid,
        "invalid_reasons": rod_reasons + [f"no_rod:{reason}" for reason in no_rod_reasons],
        "recovery_rmse_mm": 1000.0 * rod["tracking"]["recovery_position_rmse_m"],
        "recovery_iae_mm_s": 1000.0 * rod["tracking"]["recovery_iae_m_s"],
        "rejoin_latency_s": rod["phase_analysis"]["release_to_rejoin_latency_s"],
        "post_contact_jerk_p95_mps3": rod["motion"]["post_contact_jerk_p95_mps3"],
        "peak_torque_nm": rod["torque"]["applied_peak_nm"],
        "torque_rate_peak_nmps": rod["torque"]["torque_rate_peak_nmps"],
        "peak_contact_force_n": rod["rod_diagnostics"]["peak_contact_force_n"],
        "contact_impulse_ns": rod["rod_diagnostics"]["contact_impulse_ns"],
        # These diagnostics make it explicit whether the energy budget itself
        # bound the recovery drive.  Baselines have no safety state, so their
        # entries remain None and never enter their aggregate means.
        "minimum_tank_energy_j": safety["minimum_tank_energy_j"],
        "mean_tank_energy_j": safety["mean_tank_energy_j"],
        "mean_direction_scale": safety["mean_direction_scale"],
        "mean_energy_scale": safety["mean_energy_scale"],
    }


def _aggregate(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    values = [row for row in rows if row["label"] == label]
    valid = [row for row in values if row["valid"]]
    result: dict[str, Any] = {"label": label, "fixture_count": len(values), "valid_count": len(valid)}
    for metric in METRICS:
        numeric = [row[metric] for row in valid if row[metric] is not None]
        result[metric] = None if not numeric else {"mean": float(np.mean(numeric)), "std": float(np.std(numeric)), "count": len(numeric)}
    return result


def _configs() -> dict[str, EnergySafetyConfig]:
    # A small, declared coarse scan.  It isolates tank authority, recharge,
    # direction floor, and smoothing rate without searching V2/V3 test data.
    return {
        "low_tank": EnergySafetyConfig(0.55, 0.08, 0.90, 0.60, 0.30, 0.08, 0.040),
        "default": EnergySafetyConfig(0.80, 0.08, 1.20, 0.60, 0.30, 0.08, 0.040),
        "high_tank": EnergySafetyConfig(1.05, 0.08, 1.50, 0.60, 0.30, 0.08, 0.040),
        "low_recharge": EnergySafetyConfig(0.80, 0.08, 1.20, 0.40, 0.30, 0.08, 0.040),
        "high_recharge": EnergySafetyConfig(0.80, 0.08, 1.20, 0.80, 0.30, 0.08, 0.040),
        "fast_smoothing": EnergySafetyConfig(0.80, 0.08, 1.20, 0.60, 0.30, 0.08, 0.020),
        "slow_smoothing": EnergySafetyConfig(0.80, 0.08, 1.20, 0.60, 0.30, 0.08, 0.080),
        "yield_friendly": EnergySafetyConfig(0.80, 0.08, 1.20, 0.60, 0.15, 0.08, 0.040),
        # The initial coarse sweep can leave the tank comfortably above its
        # reserve.  These declared low-energy cases check the regime in which
        # the budget genuinely binds, instead of confusing a smoothing-only
        # result with an energy-budget result.
        "small_tank": EnergySafetyConfig(0.16, 0.08, 0.30, 0.60, 0.30, 0.08, 0.040),
        "near_empty_tank": EnergySafetyConfig(0.10, 0.08, 0.20, 0.60, 0.30, 0.08, 0.040),
        "near_empty_no_recharge": EnergySafetyConfig(0.10, 0.08, 0.20, 0.00, 0.30, 0.08, 0.040),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = replace(
        VMCConfig(zeta=0.8),
        carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * 8.0,
        carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * 8.0,
    )
    candidates = _fixture_candidates()
    screen_rows: list[dict[str, Any]] = []
    for fixture in candidates:
        row = _run_pair(args.menagerie, args.output_dir / "screen_episodes", fixture, "selector", "vmc_taper", config, None)
        row.update(fixture)
        screen_rows.append(row)
    fixtures = [{key: row[key] for key in ("fixture_id", "rod_approach_side", "rod_start_time_s", "rod_stroke_m", "rod_height_m", "grasp_time_s")} for row in screen_rows if row["valid"]]
    if not fixtures:
        raise RuntimeError("validation candidate set produced no effective physical fixtures")
    validation_manifest = {
        "stage": "energy-safety parameter validation; distinct from frozen V2/V3",
        "candidate_design": {"sides": ["negative_y", "positive_y"], "start_times_s": [1.040, 1.100], "strokes_m": [0.165, 0.170], "heights_m": [0.535, 0.545]},
        "effective_collision_gate": {"minimum_peak_contact_force_n": FORCE_GATE_N, "minimum_contact_impulse_ns": IMPULSE_GATE_NS},
        "candidates": screen_rows, "splits": {"validation": fixtures},
    }
    (args.output_dir / "energy_safety_validation_manifest.json").write_text(json.dumps(validation_manifest, indent=2) + "\n")

    rows: list[dict[str, Any]] = []
    # Ordinary baselines are executed on the same validation set.  The
    # impedance jerk mean becomes a declared feasibility threshold, rather
    # than an arbitrary weighted score across incompatible units.
    for label, mode, safety in (("impedance", "impedance", None), ("vmc_gated", "vmc_gated", None)):
        rows.extend(_run_pair(args.menagerie, args.output_dir / "episodes", fixture, label, mode, config, safety) for fixture in fixtures)
    configs = _configs()
    for label, safety in configs.items():
        rows.extend(_run_pair(args.menagerie, args.output_dir / "episodes", fixture, label, "vmc_energy", config, safety) for fixture in fixtures)
    labels = ("impedance", "vmc_gated", *configs)
    aggregate = [_aggregate(rows, label) for label in labels]
    by_label = {row["label"]: row for row in aggregate}
    impedance_jerk = by_label["impedance"]["post_contact_jerk_p95_mps3"]["mean"]
    feasible = [
        row for row in aggregate if row["label"] in configs and row["valid_count"] == len(fixtures)
        and row["post_contact_jerk_p95_mps3"]["mean"] <= impedance_jerk
    ]
    selected = min(feasible, key=lambda row: (row["recovery_rmse_mm"]["mean"], row["torque_rate_peak_nmps"]["mean"])) if feasible else None
    payload = {
        "protocol": {
            "validation_set": "new timing/height fixtures; V2 and V3 are excluded from tuning",
            "candidate_configurations": {name: asdict(value) for name, value in configs.items()},
            "selection_rule": "require all validation fixtures valid and mean jerk P95 no greater than impedance on the same validation set; among feasible configurations minimize recovery RMSE then torque-rate peak",
        },
        "validation_manifest": "energy_safety_validation_manifest.json",
        "rows": rows, "aggregate": aggregate,
        "impedance_jerk_threshold_mps3": impedance_jerk,
        "feasible_energy_config_labels": [row["label"] for row in feasible],
        "selected_energy_config_label": None if selected is None else selected["label"],
        "selected_energy_config": None if selected is None else asdict(configs[selected["label"]]),
    }
    (args.output_dir / "energy_safety_scan.json").write_text(json.dumps(payload, indent=2) + "\n")
    fieldnames = list(rows[0])
    with (args.output_dir / "energy_safety_scan.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"validation_fixture_count": len(fixtures), "selected_energy_config_label": payload["selected_energy_config_label"], "feasible_energy_config_labels": payload["feasible_energy_config_labels"], "aggregate": aggregate}, indent=2))


if __name__ == "__main__":
    main()
