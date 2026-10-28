#!/usr/bin/env python3
"""Resumable, bounded overnight ESN campaign for office-v5.

This runner only orchestrates registered evaluator commands. It does not edit
the scene, gates, actor inputs, actuator limits, or checkpoint weights.
Development probes remain labelled as such; formal runs use dt=5e-5.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path("/home/airpig/桌面/hwy/compliance_control/.venv-rl/bin/python")
CAMPAIGN = ROOT / "outputs" / "overnight_esn_combined_campaign_20260928"
LOCK_PATH = CAMPAIGN / ".lock"
MODEL_MEDIUM4 = ROOT / "outputs/esn_office_joint_esn_delayed2_20260928/model_medium4_v1/best.npz"
MODEL_CORNER = ROOT / "outputs/esn_corner_blend05_20260928/model.npz"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def source_hashes() -> dict[str, str]:
    names = [
        "scripts/office_complex_scene_v5_20260917.py",
        "scripts/validate_office_apparatus_v5_20260917.py",
        "scripts/current_student_policy_20260921.py",
        "scripts/office_vmc_memory_esn_20260927.py",
    ]
    return {name: sha(ROOT / name) for name in names if (ROOT / name).exists()}


def running_evaluator() -> bool:
    needle = "validate_office_apparatus_v5_20260917.py"
    out = subprocess.run(["ps", "-eo", "args="], capture_output=True, text=True, check=False).stdout
    return any(needle in line and "overnight_esn_combined_campaign" not in line for line in out.splitlines())


def limited_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[key] = "1"
    return env


def limit_process() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (2 * 60 * 60, 2 * 60 * 60))


def summarize(result_path: Path) -> dict:
    if not result_path.exists():
        return {"result": "missing"}
    try:
        data = json.loads(result_path.read_text())
    except Exception as exc:
        return {"result": "invalid_json", "error": repr(exc)}
    stats = data.get("stats", {})
    metrics = data.get("metrics", {})
    return {
        "task_success": data.get("task_success"),
        "strict_success": data.get("strict_success"),
        "physical_valid": data.get("physical_valid"),
        "final_task_stage": data.get("final_task_stage"),
        "placement_complete": data.get("placement_complete"),
        "contact_coverage_valid": data.get("contact_coverage_valid"),
        "max_external_penetration_mm": 1000.0 * stats.get("max_external_penetration_m", float("nan")),
        "cup_shift_mm": 1000.0 * stats.get("cup_shift_m", float("nan")),
        "cup_tilt_deg": stats.get("cup_tilt_deg"),
        "peak_torque_nm": metrics.get("generalized_actuator_torque_peak_nm"),
        "peak_speed_mps": metrics.get("linear_speed_peak_mps"),
        "position_rmse_3d_m": metrics.get("position_rmse_3d_m"),
        "events": stats.get("events", {}),
        "source_sha256": data.get("source_sha256", {}),
        "model_sha256": data.get("neural_logging", {}).get("model_sha256"),
    }


def run_case(name: str, args: list[str], *, formal: bool = False) -> dict:
    out_prefix = CAMPAIGN / name / "rollout"
    result_path = out_prefix.with_suffix(".json")
    record_path = out_prefix.parent / "execution.json"
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": name,
        "formal": formal,
        "command": [str(PYTHON), *args],
        "cwd": str(ROOT),
        "source_sha256_before": source_hashes(),
        "checkpoint_sha256": {
            str(MODEL_MEDIUM4): sha(MODEL_MEDIUM4) if MODEL_MEDIUM4.exists() else None,
            str(MODEL_CORNER): sha(MODEL_CORNER) if MODEL_CORNER.exists() else None,
        },
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": "planned",
    }
    if result_path.exists():
        manifest["status"] = "existing_preserved"
        manifest["summary"] = summarize(result_path)
        record_path.write_text(json.dumps(manifest, indent=2, allow_nan=False))
        return manifest
    if running_evaluator():
        manifest["status"] = "skipped_existing_evaluator"
        record_path.write_text(json.dumps(manifest, indent=2, allow_nan=False))
        return manifest
    record_path.write_text(json.dumps(manifest, indent=2, allow_nan=False))
    log_path = out_prefix.parent / "run.log"
    command = [str(PYTHON), *args]
    try:
        with log_path.open("w") as log:
            completed = subprocess.run(
                command, cwd=ROOT, env=limited_env(), stdout=log, stderr=subprocess.STDOUT,
                preexec_fn=limit_process, timeout=2 * 60 * 60, check=False,
            )
        manifest["returncode"] = completed.returncode
        manifest["status"] = "completed" if completed.returncode == 0 else "failed_process"
        manifest["summary"] = summarize(result_path)
    except Exception as exc:
        manifest["status"] = "failed_runner"
        manifest["error"] = repr(exc)
    manifest["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    manifest["source_sha256_after"] = source_hashes()
    record_path.write_text(json.dumps(manifest, indent=2, allow_nan=True))
    return manifest


def main() -> int:
    CAMPAIGN.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("campaign already running; exiting without duplicate work")
            return 0

        if running_evaluator():
            print("an evaluator is already running; exiting without duplicate work")
            return 0

        common = [
            "--events", "all", "--task", "pick_place", "--corner-placement",
            "--duration", "55", "--ball-speed", "1.7", "--ball-launch-time-s", "2",
            "--person-stroke", ".2", "--rod-stroke", ".235", "--person-start", "3",
            "--rod-start", "7", "--rod-hold", "6", "--esn-mode", "control",
            "--esn-model", str(MODEL_MEDIUM4), "--hybrid-vmc-blend", ".25",
        ]
        dev = run_case(
            "combined_v4_development",
            ["scripts/validate_office_apparatus_v5_20260917.py", "--output",
             str(CAMPAIGN / "combined_v4_development" / "rollout"),
             "--combined-contact-v2", "--dt", ".0001", *common],
            formal=False,
        )

        # Only a development result that actually passes all unchanged gates may
        # unlock the corresponding formal rerun. A failed probe cannot trigger a
        # gate relaxation or a selective success claim.
        if dev.get("summary", {}).get("strict_success") is True:
            run_case(
                "combined_v4_formal",
                ["scripts/validate_office_apparatus_v5_20260917.py", "--output",
                 str(CAMPAIGN / "combined_v4_formal" / "rollout"),
                 "--combined-contact-v2", "--dt", ".00005", *common],
                formal=True,
            )
        else:
            (CAMPAIGN / "combined_v4_formal_skipped.json").write_text(json.dumps({
                "status": "skipped",
                "reason": "development candidate did not pass unchanged task and strict gates",
                "development_summary": dev.get("summary", {}),
            }, indent=2, allow_nan=True))

        # Always retain two known-valid comparison media/results. They are not
        # relabelled as combined-scene success.
        run_case(
            "corner_only_formal_reference",
            ["scripts/validate_office_apparatus_v5_20260917.py", "--output",
             str(CAMPAIGN / "corner_only_formal_reference" / "rollout"),
             "--events", "settle", "--task", "pick_place", "--corner-placement",
             "--duration", "30", "--dt", ".00005", "--esn-model", str(MODEL_CORNER),
             "--esn-mode", "control", "--hybrid-vmc-blend", ".5"],
            formal=True,
        )
        run_case(
            "delayed_ball_formal_reference",
            ["scripts/validate_office_apparatus_v5_20260917.py", "--output",
             str(CAMPAIGN / "delayed_ball_formal_reference" / "rollout"),
             "--events", "all", "--task", "hold", "--duration", "55",
             "--dt", ".00005", "--ball-speed", "1.7", "--ball-launch-time-s", "2",
             "--person-start", "3", "--rod-start", "9", "--rod-hold", "6",
             "--esn-model", str(MODEL_MEDIUM4), "--esn-mode", "control"],
            formal=True,
        )

        report = {
            "campaign": str(CAMPAIGN),
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "source_sha256": source_hashes(),
            "checkpoint_sha256": {
                str(MODEL_MEDIUM4): sha(MODEL_MEDIUM4),
                str(MODEL_CORNER): sha(MODEL_CORNER),
            },
            "policy_contract": "canonical48D/action7 pure proprioception; no contact truth, ball state, schedule, vision, or distance input",
            "formal_dt_s": 5e-5,
            "development_dt_s": 1e-4,
        }
        (CAMPAIGN / "campaign_complete.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
