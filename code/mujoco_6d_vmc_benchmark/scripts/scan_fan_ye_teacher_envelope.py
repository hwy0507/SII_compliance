#!/usr/bin/env python3
"""Validation-only scan of the analytic teacher envelope for Fan Ye ESN-VMC.

The Fan Ye reservoir, WBC reference, physical fixture pool, VMC backend and
action safety projection are deliberately fixed.  Each scan point only changes
the *offline analytic-teacher labels* used to fit the ridge readout.  It reuses
the already-recorded VMC-gated validation comparator after verifying that its
fixture IDs and reference source match exactly.  The frozen WBC-aware V4 final
test is neither read nor written by this tool.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from fan_ye_esn_policy import FanYeVMCPolicy
from run_fan_ye_esn_validation_ladder import METRICS, common, valid
from run_rod_perturbation_benchmark import run_episode
from train_fan_ye_esn_readout import DEPLOYABLE_KEYS, GatedVMCTeacherConfig, fit_readout_from_traces


LOWER_IS_BETTER = (
    "recovery_rmse_mm",
    "release_to_rejoin_s",
    "jerk_p95_mps3",
    "peak_torque_nm",
    "torque_rate_peak_nmps",
    "peak_contact_force_n",
    "contact_impulse_ns",
)


def parse_envelope(value: str) -> tuple[str, GatedVMCTeacherConfig]:
    """Parse ``name,translation,rotation,drive[,causal_gate_filter_seconds]``."""

    parts = [part.strip() for part in value.split(",")]
    if len(parts) not in (4, 5) or not parts[0]:
        raise argparse.ArgumentTypeError("teacher envelope must be name,translation,rotation,drive[,gate_filter_seconds]")
    try:
        config = GatedVMCTeacherConfig(
            translation_log_kappa_softening=float(parts[1]),
            rotation_log_kappa_softening=float(parts[2]),
            recovery_drive_boost=float(parts[3]),
            gate_filter_time_constant_s=float(parts[4]) if len(parts) == 5 else 0.0,
        )
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return parts[0], config


def load_matching_baseline(path: Path, fixtures: list[dict], reference_source: str) -> tuple[dict, dict[str, dict]]:
    baseline = json.loads(path.read_text())
    if baseline.get("reference_source") != reference_source:
        raise ValueError("baseline reference source does not match fixture pool")
    rows = baseline.get("rows", [])
    by_fixture = {row["fixture_id"]: row for row in rows}
    expected = {fixture["fixture_id"] for fixture in fixtures}
    if set(by_fixture) != expected:
        missing, extra = sorted(expected - set(by_fixture)), sorted(set(by_fixture) - expected)
        raise ValueError(f"baseline fixture IDs differ from validation pool; missing={missing}, extra={extra}")
    if baseline.get("validity", {}).get("vmc_gated") != len(fixtures):
        raise ValueError("reused VMC-gated comparator is not valid on every validation fixture")
    return baseline, by_fixture


def write_model_and_summary(
    output_dir: Path,
    model,
    normalizer,
    fit: dict,
    *,
    candidate_index: int,
    teacher_config: GatedVMCTeacherConfig,
    sample_stride: int,
    washout_steps: int,
) -> tuple[Path, Path]:
    model_path = output_dir / "fan_ye_esn_warmstart.npz"
    summary_path = output_dir / "fan_ye_esn_readout_train_summary.json"
    np.savez_compressed(model_path, readout=model.readout, input_normalizer_scales=normalizer.scales)
    summary = {
        "schema_version": 1,
        "stage": "Fan Ye-aligned ESN ridge readout warm-start from causal analytic VMC teacher; validation-only envelope scan",
        "candidate_index": candidate_index,
        "config": asdict(fit["config"]),
        "student_input": list(DEPLOYABLE_KEYS),
        "student_excludes": ["rod_contact", "rod_force", "rod_penetration", "rod_state", "obstacle_pose_or_geometry", "future_release", "fixture_id", "recovery_gate"],
        "teacher": {"type": "causal analytic VMC recovery-gate template", "config": asdict(teacher_config), "source": "existing VMC tracking-error recovery_gate only"},
        "sample_stride": sample_stride,
        "washout_steps": washout_steps,
        "episodes": fit["episodes"],
        "training_samples": fit["training_samples"],
        "readout_training_mse": fit["readout_training_mse"],
        "model_npz": str(model_path),
        "warning": "Teacher fit is not a closed-loop metric. This configuration is being selected only on the independent ESN validation pool; frozen WBC-aware V4 is excluded.",
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    return model_path, summary_path


def aggregate(rows: list[dict]) -> dict:
    return {
        metric: float(np.mean([row["fan_ye_esn_vmc"][metric] for row in rows]))
        for metric in METRICS
    }


def selection_flags(metrics: dict, baseline: dict, *, torque_tolerance: float, force_tolerance: float) -> dict:
    ratios = {key: metrics[key] / baseline[key] for key in LOWER_IS_BETTER}
    safety_eligible = (
        ratios["peak_torque_nm"] <= 1.0 + torque_tolerance
        and ratios["peak_contact_force_n"] <= 1.0 + force_tolerance
    )
    smoothness_eligible = ratios["jerk_p95_mps3"] <= 1.0 and ratios["contact_impulse_ns"] <= 1.0
    recovery_noninferior = ratios["recovery_rmse_mm"] <= 1.0 and ratios["release_to_rejoin_s"] <= 1.0
    return {
        "relative_to_vmc_gated": ratios,
        "safety_eligible": safety_eligible,
        "smoothness_eligible": smoothness_eligible,
        "recovery_noninferior": recovery_noninferior,
        "constrained_rank_score": float(
            ratios["jerk_p95_mps3"] + ratios["contact_impulse_ns"]
            + 0.35 * (ratios["recovery_rmse_mm"] + ratios["release_to_rejoin_s"])
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--timescale-screen-json", type=Path, required=True)
    parser.add_argument("--candidate-index", type=int, default=22)
    parser.add_argument("--train-traces", type=Path, nargs="+", required=True)
    parser.add_argument("--fixture-pool-json", type=Path, required=True)
    parser.add_argument("--baseline-ladder-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--teacher-envelope", type=parse_envelope, action="append", required=True)
    parser.add_argument("--sample-stride", type=int, default=10)
    parser.add_argument("--washout-steps", type=int, default=25)
    parser.add_argument("--peak-torque-tolerance", type=float, default=0.02)
    parser.add_argument("--peak-force-tolerance", type=float, default=0.02)
    args = parser.parse_args()
    if args.peak_torque_tolerance < 0.0 or args.peak_force_tolerance < 0.0:
        raise ValueError("safety tolerances must be non-negative")
    names = [name for name, _ in args.teacher_envelope]
    if len(set(names)) != len(names):
        raise ValueError("teacher envelope names must be unique")
    fixture_pool = json.loads(args.fixture_pool_json.read_text())
    fixtures = fixture_pool.get("splits", {}).get("validation", [])
    reference_source = fixture_pool.get("reference_source")
    if reference_source != "fixed_panda_wbc" or not fixtures:
        raise ValueError("expected a non-empty fixed_panda_wbc validation fixture pool")
    baseline_ladder, baseline_rows = load_matching_baseline(args.baseline_ladder_json, fixtures, reference_source)
    baseline_metrics = baseline_ladder["aggregate_common_valid"]["vmc_gated"]
    screen = json.loads(args.timescale_screen_json.read_text())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scan_rows = []
    for name, teacher_config in args.teacher_envelope:
        run_dir = args.output_dir / name
        run_dir.mkdir(parents=True, exist_ok=True)
        model, normalizer, fit = fit_readout_from_traces(
            screen, candidate_index=args.candidate_index, traces=args.train_traces,
            sample_stride=args.sample_stride, washout_steps=args.washout_steps, teacher_config=teacher_config,
        )
        model_path, summary_path = write_model_and_summary(
            run_dir, model, normalizer, fit, candidate_index=args.candidate_index,
            teacher_config=teacher_config, sample_stride=args.sample_stride, washout_steps=args.washout_steps,
        )
        rows = []
        for fixture in fixtures:
            policy = FanYeVMCPolicy(model_path, summary_path)
            summary = run_episode(
                rod_enabled=True, compliance_policy=policy, policy_update_hz=policy.config.update_hz,
                policy_contact_drive_scale=policy.config.contact_drive_scale,
                **common(args.menagerie, run_dir / fixture["fixture_id"], fixture),
            )
            rows.append({
                "fixture_id": fixture["fixture_id"],
                "baseline_vmc_gated_valid": bool(baseline_rows[fixture["fixture_id"]]["vmc_gated_valid"]),
                "fan_ye_esn_vmc_valid": valid(summary),
                "fan_ye_esn_vmc": {metric: function(summary) for metric, function in METRICS.items()},
            })
        common_rows = [row for row in rows if row["baseline_vmc_gated_valid"] and row["fan_ye_esn_vmc_valid"]]
        metrics = aggregate(common_rows) if common_rows else {metric: None for metric in METRICS}
        flags = selection_flags(metrics, baseline_metrics, torque_tolerance=args.peak_torque_tolerance, force_tolerance=args.peak_force_tolerance) if len(common_rows) == len(fixtures) else None
        scan_rows.append({
            "name": name,
            "teacher_config": asdict(teacher_config),
            "model_npz": str(model_path),
            "train_summary_json": str(summary_path),
            "readout_training_mse": fit["readout_training_mse"],
            "valid_count": len(common_rows),
            "fixture_count": len(fixtures),
            "aggregate_common_valid": metrics,
            "selection": flags,
            "rows": rows,
        })
    eligible = [row for row in scan_rows if row["selection"] and row["selection"]["safety_eligible"]]
    selected_order = sorted(
        eligible,
        key=lambda row: (
            not row["selection"]["smoothness_eligible"],
            not row["selection"]["recovery_noninferior"],
            row["selection"]["constrained_rank_score"],
        ),
    )
    result = {
        "schema_version": 1,
        "stage": "validation-only analytic-teacher envelope selection for fixed Fan Ye ESN-VMC",
        "selection_data_boundary": "Only ESN train traces fit readouts and only the independent ESN validation pool ranks envelopes. Frozen WBC-aware V4 final test is excluded.",
        "fixed_components": ["Fan Ye reservoir candidate #22", "fixed_panda_wbc reference", "physical fixture pool", "vmc_gated backend", "bounded ESN action projection", "torque feasibility and slew safeguards"],
        "baseline_ladder_json": str(args.baseline_ladder_json),
        "baseline_metrics": baseline_metrics,
        "fixture_count": len(fixtures),
        "candidate_index": args.candidate_index,
        "selection_constraints": {
            "all_validation_fixtures_must_be_valid": True,
            "peak_torque_relative_tolerance": args.peak_torque_tolerance,
            "peak_contact_force_relative_tolerance": args.peak_force_tolerance,
            "preference": "jerk P95 and contact impulse no worse than fixed VMC-gated, then recovery RMSE and rejoin latency no worse",
        },
        "runs": scan_rows,
        "provisional_validation_selection": selected_order[0]["name"] if selected_order else None,
        "warning": "The provisional selection is validation-only. It is not a final benchmark result and must be frozen before one-shot evaluation on WBC-aware V4.",
    }
    output_path = args.output_dir / "fan_ye_teacher_envelope_scan.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n")
    compact = [{"name": row["name"], "valid": f'{row["valid_count"]}/{row["fixture_count"]}', "selection": row["selection"]} for row in scan_rows]
    print(json.dumps({"output": str(output_path), "provisional_validation_selection": result["provisional_validation_selection"], "runs": compact}, indent=2))


if __name__ == "__main__":
    main()
