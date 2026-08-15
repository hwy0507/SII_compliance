#!/usr/bin/env python3
"""Evaluate fixed Fan-Ye ESN-VMC against VMC-gated on the ESN validation pool."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from fan_ye_esn_policy import FanYeVMCPolicy
from run_benchmark import VMCConfig
from run_rod_perturbation_benchmark import run_episode
from screen_benchmark_v4_manifest import WARM_START_KAPPA


METRICS = {
    "recovery_rmse_mm": lambda s: 1000.0 * s["tracking"]["recovery_position_rmse_m"],
    "release_to_rejoin_s": lambda s: s["phase_analysis"]["release_to_rejoin_latency_s"],
    "jerk_p95_mps3": lambda s: s["motion"]["post_contact_jerk_p95_mps3"],
    "peak_torque_nm": lambda s: s["torque"]["applied_peak_nm"],
    "torque_rate_peak_nmps": lambda s: s["torque"]["torque_rate_peak_nmps"],
    "peak_contact_force_n": lambda s: s["rod_diagnostics"]["peak_contact_force_n"],
    "contact_impulse_ns": lambda s: s["rod_diagnostics"]["contact_impulse_ns"],
}


def common(menagerie: Path, output_dir: Path, fixture: dict) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    config = replace(
        VMCConfig(zeta=0.8),
        carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * 8.0,
        carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * 8.0,
    )
    return dict(
        menagerie=menagerie, kappa=np.asarray(WARM_START_KAPPA), output_dir=output_dir,
        render_gif=False, config=config, contact_time_constant_s=0.015,
        recovery_kappa=np.asarray(WARM_START_KAPPA), recovery_ramp_s=0.08,
        recovery_drive_scale_factor=14.0 / 8.0, grasp_time_s=float(fixture["grasp_time_s"]),
        rod_start_time_s=float(fixture["rod_start_time_s"]), explicit_translational_carriage=True,
        carriage_mass_kg=1.0, controller_mode="vmc_gated", remove_rod_when_disabled=True,
        recovery_gate_hold_s=0.28, recovery_gate_taper_s=0.04, reference_source="fixed_panda_wbc",
        rod_approach_side=fixture["rod_approach_side"], rod_stroke_m=float(fixture["rod_stroke_m"]),
        rod_height_m=float(fixture["rod_height_m"]), rod_center_x_m=float(fixture["rod_center_x_m"]),
        rod_center_y_m=float(fixture["rod_center_y_m"]),
    )


def valid(summary: dict) -> bool:
    task = summary["task_validity"]
    return bool(task["simulation_finite"] and task["rod_hand_contact_observed"] and task["target_lifted_after_recovery"] and task["target_held_at_end"] and summary["phase_analysis"]["rejoin_time_s"] is not None and summary["torque"]["hard_limit_fraction"] == 0.0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--fixture-pool-json", type=Path, required=True)
    parser.add_argument("--model-npz", type=Path, required=True)
    parser.add_argument("--train-summary-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.fixture_pool_json.read_text())
    fixtures = manifest["splits"]["validation"]
    if manifest.get("reference_source") != "fixed_panda_wbc" or not fixtures:
        raise ValueError("expected a non-empty fixed_panda_wbc validation pool")
    rows = []
    for fixture in fixtures:
        fixture_dir = args.output_dir / fixture["fixture_id"]
        baseline = run_episode(rod_enabled=True, **common(args.menagerie, fixture_dir / "vmc_gated", fixture))
        policy = FanYeVMCPolicy(args.model_npz, args.train_summary_json)
        esn = run_episode(
            rod_enabled=True, compliance_policy=policy, policy_update_hz=policy.config.update_hz,
            policy_contact_drive_scale=policy.config.contact_drive_scale,
            **common(args.menagerie, fixture_dir / "fan_ye_esn_vmc", fixture),
        )
        rows.append({
            "fixture_id": fixture["fixture_id"], "rod_approach_side": fixture["rod_approach_side"],
            "rod_start_time_s": fixture["rod_start_time_s"], "vmc_gated_valid": valid(baseline), "fan_ye_esn_vmc_valid": valid(esn),
            "vmc_gated": {name: fn(baseline) for name, fn in METRICS.items()},
            "fan_ye_esn_vmc": {name: fn(esn) for name, fn in METRICS.items()},
        })
    common_rows = [row for row in rows if row["vmc_gated_valid"] and row["fan_ye_esn_vmc_valid"]]
    aggregate = {method: {metric: float(np.mean([row[method][metric] for row in common_rows])) for metric in METRICS} for method in ("vmc_gated", "fan_ye_esn_vmc")}
    output = {
        "stage": "ESN validation pool only; not frozen WBC-aware V4 final test",
        "reference_source": manifest["reference_source"], "fixture_count": len(rows), "common_valid_count": len(common_rows),
        "validity": {method: sum(row[f"{method}_valid"] for row in rows) for method in ("vmc_gated", "fan_ye_esn_vmc")},
        "aggregate_common_valid": aggregate, "rows": rows,
        "warning": "This is a fixed warm-start teacher validation. Do not tune on V4 or claim final performance before selecting the teacher/action envelope.",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "fan_ye_esn_validation_ladder.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"fixtures": len(rows), "common_valid": len(common_rows), "validity": output["validity"], "aggregate": aggregate}, indent=2))


if __name__ == "__main__":
    main()
