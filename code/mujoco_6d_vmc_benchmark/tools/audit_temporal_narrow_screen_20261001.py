#!/usr/bin/env python3
"""Independent audit for the narrow temporal-consistency screen.

The evaluator stores a prefix (``esn_combined_v4``) rather than a directory
named ``rollout``.  This audit replays the saved canonical observations and
recomputes all physical metrics from the substep arrays without changing the
rollouts or using diagnostics as actor inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from current_student_policy_20260921 import load_current  # noqa: E402


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def audit(run: Path, kind: str) -> dict:
    prefix = run / f"{kind}_combined_v4"
    result = json.loads(prefix.with_suffix(".json").read_text())
    model = run / ("esn_temporal.npz" if kind == "esn" else "mlp_temporal.npz")
    training = json.loads((run / "TRAINING_COMPLETE.json").read_text())
    if sha(model) != training["checkpoint_sha256"][kind] or sha(model) != result["neural_logging"]["model_sha256"]:
        raise ValueError(f"{run.name}/{kind}: checkpoint hash mismatch")
    if sha(prefix.with_suffix(".mjb")) != result["model_sha256"]:
        raise ValueError(f"{run.name}/{kind}: compiled model hash mismatch")
    with np.load(prefix.with_suffix(".npz"), allow_pickle=False) as trace:
        for key in ("observation", "applied_action", "reservoir_state"):
            if key not in trace:
                continue
            value = trace[key]
            if np.issubdtype(value.dtype, np.number) and not np.isfinite(value).all():
                raise ValueError(f"{run.name}/{kind}: nonfinite trace {key}")
        obs = np.asarray(trace["observation"], dtype=np.float64)
        applied = np.asarray(trace["applied_action"], dtype=np.float64)
        if obs.ndim != 2 or obs.shape[1] != 48 or applied.shape != (len(obs), 7):
            raise ValueError(f"{run.name}/{kind}: actor shape mismatch")
        actor = load_current(model)
        actor.reset()
        replay = np.stack([actor.act(row) for row in obs]).astype(np.float64)
        action_err = float(np.max(np.abs(replay - applied)))
        state_err = None
        if "reservoir_state" in trace and trace["reservoir_state"].shape[1] == 128:
            obj = getattr(actor, "obj", actor)
            actor.reset()
            states = []
            for row in obs:
                actor.act(row)
                states.append(np.asarray(obj.state, dtype=np.float64).copy())
            state_err = float(np.max(np.abs(np.asarray(states) - trace["reservoir_state"])))
    metric_path = prefix.parent / f"{prefix.name}_metrics" / "substep_metrics.npz"
    with np.load(metric_path, allow_pickle=False) as metrics:
        for key in metrics.files:
            value = metrics[key]
            if np.issubdtype(value.dtype, np.number) and not np.isfinite(value).all():
                raise ValueError(f"{run.name}/{kind}: nonfinite metrics {key}")
        dt = np.asarray(metrics["dt"], dtype=np.float64)
        error = np.asarray(metrics["error"], dtype=np.float64)
        if not np.allclose(dt, 1e-4, rtol=0, atol=1e-12):
            raise ValueError(f"{run.name}/{kind}: unexpected physical dt")
        rmse = float(np.sqrt(np.sum(error * error * dt[:, None]) / np.sum(dt)))
        speed = float(np.max(np.linalg.norm(metrics["twist"][:, :3], axis=1)))
        torque = float(np.max(np.abs(metrics["qfrc_actuator"])))
    reported = result["metrics"]
    if abs(rmse - float(reported["position_rmse_3d_m"])) > 1e-5:
        raise ValueError(f"{kind}: RMSE mismatch")
    if abs(speed - float(reported["linear_speed_peak_mps"])) > 1e-7:
        raise ValueError(f"{kind}: speed mismatch")
    if abs(torque - float(reported["generalized_actuator_torque_peak_nm"])) > 1e-5:
        raise ValueError(f"{kind}: torque mismatch")
    if abs(float(np.sum(dt)) - 55.0) > 1e-7 or len(dt) != 550000:
        raise ValueError(f"{kind}: physical horizon mismatch")
    if action_err > 1e-10 or (state_err is not None and state_err > 1e-10):
        raise ValueError(f"{kind}: policy replay mismatch")
    return {
        "run_id": run.name,
        "training_seed": training["seed"] if kind == "esn" else training["mlp_seed"],
        "summary_sha256": sha(prefix.with_suffix(".json")),
        "training_record_sha256": sha(run / "TRAINING_COMPLETE.json"),
        "physical_substep_sha256": sha(metric_path),
        "checkpoint_and_mjb_metadata_hash_match": True,
        "actor_state_and_physical_metrics_finite": True,
        "method": kind.upper(),
        "task_success": bool(result["task_success"]),
        "strict_success": bool(result["strict_success"]),
        "final_task_stage": result["final_task_stage"],
        "placement_complete": bool(result.get("placement_complete", False)),
        "contact_coverage_valid": bool(result.get("contact_coverage_valid", False)),
        "ball_rebound": bool(result.get("ball_rebound", False)),
        "physical_valid": bool(result.get("physical_valid", False)),
        "external_penetration_mm": 1000.0 * float(result["stats"]["max_external_penetration_m"]),
        "position_rmse_3d_mm": 1000.0 * rmse,
        "peak_torque_nm": torque,
        "peak_speed_mps": speed,
        "duration_s": float(np.sum(dt)),
        "physical_substeps": int(len(dt)),
        "action_replay_max_abs": action_err,
        "reservoir_state_replay_max_abs": state_err,
        "rod_longest_run_s": result["stats"].get("contact_diagnostics", {}).get("rod_longest_run", {}).get("duration_s") if result["stats"].get("contact_diagnostics", {}).get("rod_longest_run") else None,
        "checkpoint_sha256": sha(model),
        "rollout_sha256": sha(prefix.with_suffix(".npz")),
        "mjb_sha256": sha(prefix.with_suffix(".mjb")),
        "source_sha256": result["source_sha256"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--extra-run", type=Path, action="append", default=[])
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    rows = []
    for run_name in ("dw025", "dw075"):
        run = args.root / f"esn_mlp_temporal_consistency_narrow_20261001_{run_name}"
        rows.extend([audit(run, "esn"), audit(run, "mlp")])
    for run in args.extra_run:
        rows.extend([audit(run, "esn"), audit(run, "mlp")])
    report = {
        "contract": "independent temporal narrow screen audit",
        "manifest_sha256": "6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3",
        "scene": "office-v5 combined-thick-corner-pillar-v4",
        "development_dt_s": 1e-4,
        "policy_contract": "canonical48D/action7 pure proprioception; actor contact truth false",
        "rows": rows,
        "limitations": [
            "All rows are development dt=1e-4; no formal dt=5e-5 run is unlocked because strict_success is false for all rows.",
            "RMSE, peak torque and peak speed are report metrics; they do not replace task or strict gates.",
            "The raw rollouts and failed rows are retained in each run directory.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
