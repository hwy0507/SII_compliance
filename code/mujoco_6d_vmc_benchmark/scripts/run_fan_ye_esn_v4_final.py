#!/usr/bin/env python3
"""One-shot WBC-aware V4 final holdout evaluation of a frozen Fan Ye ESN-VMC.

This runner deliberately has no teacher-envelope options.  It accepts a
pretrained readout and verifies that the frozen V4 manifest and existing
fixed-Panda-WBC VMC-gated comparator contain the exact same fixture IDs before
any MuJoCo episode is run.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from fan_ye_esn_policy import FanYeVMCPolicy
from run_benchmark import VMCConfig
from run_benchmark_v2_ladder import METRICS, _trace, _valid
from run_rod_perturbation_benchmark import run_episode
from screen_benchmark_v4_manifest import WARM_START_KAPPA


def verify_final_contract(manifest: dict, baseline: dict) -> list[dict]:
    """Reject accidental development/validation or proxy/WBC result mixing."""

    if manifest.get("stage") != "frozen V4 five-side axis-coverage holdout benchmark":
        raise ValueError("expected the frozen V4 final holdout manifest")
    fixtures = manifest.get("splits", {}).get("test", [])
    if not fixtures:
        raise ValueError("V4 manifest has no effective test fixture")
    protocol = baseline.get("protocol", {})
    if protocol.get("reference_source") != "fixed_panda_wbc":
        raise ValueError("baseline ladder is not fixed_panda_wbc")
    expected = {fixture["fixture_id"] for fixture in fixtures}
    gated = [row for row in baseline.get("rows", []) if row.get("controller") == "vmc_gated"]
    if {row.get("fixture_id") for row in gated} != expected:
        raise ValueError("baseline VMC-gated fixture IDs differ from frozen V4 manifest")
    if not all(row.get("valid") for row in gated):
        raise ValueError("baseline VMC-gated is not valid on every V4 fixture")
    return fixtures


def run_fixture(menagerie: Path, output_dir: Path, fixture: dict, policy: FanYeVMCPolicy) -> dict:
    config = replace(VMCConfig(zeta=0.8), carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * 8.0, carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * 8.0)
    common = dict(
        menagerie=menagerie, kappa=np.asarray(WARM_START_KAPPA), render_gif=False, config=config,
        rod_stroke_m=fixture["rod_stroke_m"], contact_time_constant_s=0.015,
        recovery_kappa=np.asarray(WARM_START_KAPPA), recovery_ramp_s=0.08, recovery_drive_scale_factor=14.0 / 8.0,
        grasp_time_s=fixture["grasp_time_s"], rod_start_time_s=fixture["rod_start_time_s"], explicit_translational_carriage=True,
        carriage_mass_kg=1.0, rod_height_m=fixture["rod_height_m"], rod_center_x_m=fixture["rod_center_x_m"], rod_center_y_m=fixture["rod_center_y_m"],
        controller_mode="vmc_gated", rod_approach_side=fixture["rod_approach_side"], remove_rod_when_disabled=bool(fixture.get("remove_rod_when_disabled", False)),
        recovery_gate_hold_s=0.28, recovery_gate_taper_s=0.04, reference_source="fixed_panda_wbc",
        compliance_policy=policy, policy_update_hz=policy.config.update_hz, policy_contact_drive_scale=policy.config.contact_drive_scale,
    )
    rod_dir = output_dir / fixture["fixture_id"] / "fan_ye_esn_vmc"
    rod_dir.mkdir(parents=True, exist_ok=True)
    rod = run_episode(output_dir=rod_dir, rod_enabled=True, **common)
    policy.reset()
    no_rod_dir = rod_dir / "no_rod"
    no_rod_dir.mkdir(parents=True, exist_ok=True)
    no_rod = run_episode(output_dir=no_rod_dir, rod_enabled=False, **common)
    rod_trace, no_rod_trace = _trace(rod_dir), _trace(no_rod_dir)
    paired = np.linalg.norm(rod_trace["ee_position"] - no_rod_trace["ee_position"], axis=1)
    rod_valid, rod_failures = _valid(rod, no_rod=False)
    no_rod_valid, no_rod_failures = _valid(no_rod, no_rod=True)
    motion, torque, tracking, phase, info = rod["motion"], rod["torque"], rod["tracking"], rod["phase_analysis"], rod["rod_diagnostics"]
    return {
        "controller": "fan_ye_esn_vmc", "fixture_id": fixture["fixture_id"], "approach_side": fixture["rod_approach_side"], "timing_bin": fixture["timing_bin"], "impulse_bin": fixture["realized_impulse_bin"],
        "valid": rod_valid and no_rod_valid, "invalid_reasons": rod_failures + [f"no_rod:{item}" for item in no_rod_failures],
        "peak_paired_offset_mm": float(np.max(paired) * 1000.0), "paired_offset_rmse_mm": float(np.sqrt(np.mean(paired ** 2)) * 1000.0),
        "recovery_rmse_mm": tracking["recovery_position_rmse_m"] * 1000.0, "recovery_iae_mm_s": tracking["recovery_iae_m_s"] * 1000.0,
        "rejoin_latency_s": phase["release_to_rejoin_latency_s"], "yield_peak_error_mm": rod["six_spring_response"]["peak_end_effector_nominal_deviation_m"] * 1000.0,
        "rebound_ratio": tracking["post_release_rebound_ratio"], "post_contact_speed_p95_mps": motion["post_contact_speed_p95_mps"], "post_contact_jerk_p95_mps3": motion["post_contact_jerk_p95_mps3"], "peak_jerk_mps3": motion["jerk_peak_mps3"],
        "peak_torque_nm": torque["applied_peak_nm"], "torque_p95_nm": torque["applied_p95_nm"], "torque_rms_nm": torque["applied_rms_nm"], "torque_rate_peak_nmps": torque["torque_rate_peak_nmps"],
        "peak_contact_force_n": info["peak_contact_force_n"], "contact_impulse_ns": info["contact_impulse_ns"],
        "task_success": rod["task_validity"]["target_lifted_after_recovery"] and rod["task_validity"]["target_held_at_end"], "no_rod_task_success": no_rod["task_validity"]["target_lifted_after_recovery"] and no_rod["task_validity"]["target_held_at_end"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--baseline-ladder", type=Path, required=True)
    parser.add_argument("--model-npz", type=Path, required=True)
    parser.add_argument("--train-summary-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest, baseline = json.loads(args.manifest.read_text()), json.loads(args.baseline_ladder.read_text())
    fixtures = verify_final_contract(manifest, baseline)
    rows = [run_fixture(args.menagerie, args.output_dir, fixture, FanYeVMCPolicy(args.model_npz, args.train_summary_json)) for fixture in fixtures]
    valid = [row for row in rows if row["valid"]]
    aggregate = {metric: None if not valid else float(np.mean([row[metric] for row in valid if row[metric] is not None])) for metric in METRICS}
    payload = {"stage": "one-shot frozen WBC-aware V4 final holdout; no V4 tuning", "reference_source": "fixed_panda_wbc", "manifest": str(args.manifest), "baseline_ladder": str(args.baseline_ladder), "fixture_count": len(rows), "valid_count": len(valid), "aggregate_valid": aggregate, "rows": rows, "warning": "Do not use this result to tune the ESN teacher or action envelope."}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "fan_ye_esn_v4_final.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"valid": f"{len(valid)}/{len(rows)}", "aggregate": aggregate}, indent=2))


if __name__ == "__main__":
    main()
