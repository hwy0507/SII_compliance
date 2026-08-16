#!/usr/bin/env python3
"""Evaluate frozen MLP and stable-phase ESN checkpoints on new impactor geometries.

This is an inference-only transfer evaluation.  It deliberately keeps the
independent WBC velocity-residual interface separate from VMC: both learned
lanes use the same action filter, velocity/acceleration/torque adapter, WBC
command source, and matched impactor/no-impact protocol.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


METRICS = (
    "recovery_rmse_mm",
    "rejoin_latency_s",
    "peak_recovery_jerk_mps3",
    "contact_impulse_ns",
    "peak_torque_nm",
    "paired_offset_rmse_mm",
)


def _representative(archive_path: Path) -> dict[str, Any]:
    archive = json.loads(archive_path.read_text())
    representative = archive.get("representative")
    if not isinstance(representative, dict) or not representative.get("gate", {}).get("passed", False):
        raise ValueError(f"archive has no gate-passing representative: {archive_path}")
    return representative


def _run_evaluation(
    python: str,
    evaluator: Path,
    output_dir: Path,
    *,
    menagerie: Path,
    manifest: Path,
    fan_ye_model_npz: Path,
    fan_ye_train_summary_json: Path,
    observation_mode: str,
    model: Path,
    vecnormalize: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        python, str(evaluator),
        "--menagerie", str(menagerie),
        "--output-dir", str(output_dir),
        "--fixture-manifest", str(manifest),
        "--fixture-split", "validation",
        "--fan-ye-model-npz", str(fan_ye_model_npz),
        "--fan-ye-train-summary-json", str(fan_ye_train_summary_json),
        "--observation-mode", observation_mode,
        "--reward-profile", "impulse_constrained",
        "--model", str(model),
        "--vecnormalize", str(vecnormalize),
        "--residual-window-end-at-grasp",
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    (output_dir / "evaluation.stdout.log").write_text(result.stdout)
    (output_dir / "evaluation.stderr.log").write_text(result.stderr)
    report_path = output_dir / "wbc_velocity_residual_paired_evaluation.json"
    if result.returncode != 0 or not report_path.is_file():
        raise RuntimeError(f"evaluator failed for {observation_mode}; exit={result.returncode}")
    return json.loads(report_path.read_text())


def _lane_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for record in report["records"]:
        fixture = record["fixture"]
        rows.append({
            "fixture_index": record["fixture_index"],
            "impactor_type": fixture["impactor_type"],
            "fixture": fixture,
            "valid": bool(
                record["task_success"]
                and record["no_rod_task_success"]
                and record["effective_collision"]
                and not record["hard_torque_limit"]
            ),
            **{key: record[key] for key in METRICS},
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-root", type=Path, required=True)
    parser.add_argument("--seed-id", required=True)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--fixture-manifest", type=Path, required=True)
    parser.add_argument("--fan-ye-model-npz", type=Path, required=True)
    parser.add_argument("--fan-ye-train-summary-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--evaluator", type=Path, default=Path(__file__).with_name("evaluate_wbc_velocity_residual.py"))
    args = parser.parse_args()
    if "post_v4_development" not in args.fixture_manifest.as_posix():
        raise ValueError("cross-geometry transfer requires a post-V4 development manifest")
    run_root = args.campaign_root / args.seed_id
    archives = {
        "mlp": run_root / "current_mlp" / "validation_archive" / "wbc_velocity_residual_checkpoint_archive.json",
        "stable_phase_esn": run_root / "fan_ye_esn" / "validation_archive" / "wbc_velocity_residual_checkpoint_archive.json",
    }
    modes = {"mlp": "current_mlp", "stable_phase_esn": "fan_ye_stable_phase_esn"}
    reports: dict[str, dict[str, Any]] = {}
    representatives: dict[str, dict[str, Any]] = {}
    for lane, archive in archives.items():
        representative = _representative(archive)
        representatives[lane] = representative
        reports[lane] = _run_evaluation(
            args.python, args.evaluator, args.output_dir / lane,
            menagerie=args.menagerie, manifest=args.fixture_manifest,
            fan_ye_model_npz=args.fan_ye_model_npz,
            fan_ye_train_summary_json=args.fan_ye_train_summary_json,
            observation_mode=modes[lane], model=Path(representative["model"]),
            vecnormalize=Path(representative["vecnormalize"]),
        )
    lane_rows = {lane: _lane_rows(report) for lane, report in reports.items()}
    paired = []
    for mlp, esn in zip(lane_rows["mlp"], lane_rows["stable_phase_esn"], strict=True):
        if mlp["impactor_type"] != esn["impactor_type"]:
            raise RuntimeError("MLP and ESN transfer fixtures are misaligned")
        paired.append({
            "impactor_type": mlp["impactor_type"],
            "both_valid": mlp["valid"] and esn["valid"],
            "mlp": mlp,
            "stable_phase_esn": esn,
            "delta_esn_minus_mlp": {
                key: None if mlp[key] is None or esn[key] is None else float(esn[key] - mlp[key])
                for key in METRICS
            },
        })
    payload = {
        "stage": "frozen stable-phase ESN cross-geometry transfer; inference only; not V4 final holdout",
        "controller_contract": "independent WBC velocity residual; ESN and VMC are separate algorithms",
        "policy_input": "Panda proprioception, WBC command/error history, and fixed reservoir state only; no contact/force/impactor/future-release input",
        "campaign_root": str(args.campaign_root),
        "seed_id": args.seed_id,
        "fixture_manifest": str(args.fixture_manifest),
        "representatives": {lane: {
            "candidate_id": value.get("candidate_id"),
            "model": value["model"],
            "vecnormalize": value["vecnormalize"],
        } for lane, value in representatives.items()},
        "lanes": lane_rows,
        "paired": paired,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "stable_phase_impactor_transfer.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({
        "seed_id": args.seed_id,
        "valid_pairs": f"{sum(row['both_valid'] for row in paired)}/{len(paired)}",
        "deltas": [{"impactor": row["impactor_type"], **row["delta_esn_minus_mlp"]} for row in paired],
    }, indent=2))


if __name__ == "__main__":
    main()
