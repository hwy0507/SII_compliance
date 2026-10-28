#!/usr/bin/env python3
"""Independent action/state/substep audit for the 2026-10-01 comparison."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from current_student_policy_20260921 import load_current


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def audit_one(case, model=None):
    folder = Path(case)
    result = json.loads((folder / "rollout.json").read_text())
    with np.load(folder / "rollout.npz", allow_pickle=False) as trace:
        obs = trace["observation"].astype(np.float64)
        saved = trace["applied_action"].astype(np.float64)
        replay_error = None
        state_error = None
        if model is not None:
            actor = load_current(Path(model))
            actor.reset()
            replay = np.stack([actor.act(row) for row in obs]).astype(np.float64)
            replay_error = float(np.max(np.abs(replay - saved)))
            if "reservoir_state" in trace and trace["reservoir_state"].shape[1] == 128:
                # Current ESN adapters expose the reservoir state through obj.
                state = getattr(actor, "obj", actor)
                expected = trace["reservoir_state"].astype(np.float64)
                # The final state is captured after act() for each row.
                states = []
                actor.reset()
                for row in obs:
                    actor.act(row)
                    states.append(np.asarray(state.state, dtype=np.float64).copy())
                state_error = float(np.max(np.abs(np.asarray(states) - expected)))
        with np.load(folder / "rollout_metrics" / "substep_metrics.npz", allow_pickle=False) as metrics:
            dt = metrics["dt"].astype(np.float64)
            error = metrics["error"].astype(np.float64)
            rmse = float(np.sqrt(np.sum(error * error * dt[:, None]) / np.sum(dt)))
            speed = float(np.max(np.linalg.norm(metrics["twist"][:, :3].astype(np.float64), axis=1)))
            torque = float(np.max(np.abs(metrics["qfrc_actuator"].astype(np.float64))))
            duration = float(np.sum(dt))
    reported = result["metrics"]
    return {
        "folder": str(folder), "model": None if model is None else str(model),
        "model_sha256": None if model is None else sha(model),
        "result_model_sha256": result.get("neural_logging", {}).get("model_sha256"),
        "task_success": result.get("task_success"), "strict_success": result.get("strict_success"),
        "physical_valid": result.get("physical_valid"), "placement_complete": result.get("placement_complete"),
        "final_task_stage": result.get("final_task_stage"), "contact_coverage_valid": result.get("contact_coverage_valid"),
        "external_penetration_mm": 1000.0 * result["stats"]["max_external_penetration_m"],
        "position_rmse_3d_mm": 1000.0 * rmse, "peak_torque_nm": torque, "peak_speed_mps": speed,
        "reported_position_rmse_3d_mm": 1000.0 * reported["position_rmse_3d_m"],
        "reported_peak_torque_nm": reported["generalized_actuator_torque_peak_nm"],
        "reported_peak_speed_mps": reported["linear_speed_peak_mps"],
        "duration_s": duration, "physical_substeps": len(dt),
        "action_replay_max_abs": replay_error, "reservoir_state_replay_max_abs": state_error,
        "rod_contact": result["stats"].get("contact_diagnostics", {}).get("rod_longest_run"),
        "files_sha256": {str(p.relative_to(folder)): sha(p) for p in sorted(folder.rglob("*")) if p.is_file()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--vmc", type=Path, required=True)
    ap.add_argument("--esn", type=Path, required=True)
    ap.add_argument("--esn-model", type=Path, required=True)
    ap.add_argument("--mlp", type=Path, required=True)
    ap.add_argument("--mlp-model", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    rows = [audit_one(args.vmc), audit_one(args.esn, args.esn_model), audit_one(args.mlp, args.mlp_model)]
    for row in rows:
        if abs(row["position_rmse_3d_mm"] - row["reported_position_rmse_3d_mm"]) > 1e-5:
            raise ValueError("RMSE replay mismatch")
        if abs(row["peak_torque_nm"] - row["reported_peak_torque_nm"]) > 1e-5:
            raise ValueError("torque replay mismatch")
        if abs(row["peak_speed_mps"] - row["reported_peak_speed_mps"]) > 1e-7:
            raise ValueError("speed replay mismatch")
        if abs(row["duration_s"] - 55.0) > 1e-7 or row["physical_substeps"] != 550000:
            raise ValueError("physical horizon mismatch")
        if row["action_replay_max_abs"] is not None and row["action_replay_max_abs"] > 1e-10:
            raise ValueError("action replay mismatch")
    report = {
        "contract": "VMC teacher versus pure ESN/MLP closed-loop v4 development audit",
        "cases": rows,
        "limitations": [
            "Development dt=1e-4; no formal dt=5e-5 rerun unlocked because neither student passed strict.",
            "The common scene fails contact coverage for all three; task success and strict success remain separate.",
            "Penetration is bound to the saved substep metric/result metadata; no hardware conclusion.",
        ],
    }
    (args.output / "AUDIT.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
