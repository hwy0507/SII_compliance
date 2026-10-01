"""Independent pure-ESN replay and physical-substep audit for one rollout."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from current_student_policy_20260921 import load_current  # noqa: E402


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stem", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = {key: args.stem.with_name(args.stem.name + suffix) for key, suffix in (
        ("result", ".json"), ("trace", ".npz"), ("world", ".mjb"))}
    paths["substeps"] = args.stem.parent / (args.stem.name + "_metrics") / "substep_metrics.npz"
    result = json.loads(paths["result"].read_text())
    checkpoint_sha = sha(args.checkpoint)
    world_sha = sha(paths["world"])
    if result["neural_logging"]["model_sha256"] != checkpoint_sha:
        raise AssertionError("checkpoint hash differs from evaluator record")
    if result["model_sha256"] != world_sha:
        raise AssertionError("MJB hash differs from evaluator record")
    if result["arguments"]["hybrid_vmc_blend"] != 0 or result["neural_logging"]["observation_dim"] != 48:
        raise AssertionError("not a canonical48D student rollout")
    actor = load_current(args.checkpoint)
    with np.load(paths["trace"], allow_pickle=False) as trace:
        if trace["observation"].shape[1] != 48:
            raise AssertionError("observation is not canonical48D")
        actions, states = [], []
        has_reservoir = "reservoir_state" in trace and (hasattr(actor, "state") or hasattr(actor, "obj"))
        for obs in trace["observation"]:
            actions.append(actor.act(obs))
            if has_reservoir:
                state_obj = actor if hasattr(actor, "state") else actor.obj
                states.append(state_obj.state.copy())
        action_error = float(np.max(np.abs(np.asarray(actions) - trace["applied_action"])))
        state_error = (float(np.max(np.abs(np.asarray(states) - trace["reservoir_state"])))
                       if has_reservoir else None)
        count = len(actions)
    if action_error >= 1e-10 or (state_error is not None and state_error >= 1e-10):
        raise AssertionError(f"ESN replay mismatch: {action_error}, {state_error}")
    with np.load(paths["substeps"], allow_pickle=False) as raw:
        dt = raw["dt"].astype(np.float64)
        error = raw["error"].astype(np.float64)
        rmse = float(np.sqrt(np.sum(error * error * dt[:, None]) / dt.sum()))
        speed = float(np.max(np.linalg.norm(raw["twist"][:, :3].astype(np.float64), axis=1)))
        torque = float(np.max(np.abs(raw["qfrc_actuator"])))
        physical_steps = len(dt)
        physical_duration = float(dt.sum())
    np.testing.assert_allclose(
        [rmse, speed, torque],
        [result["metrics"]["position_rmse_3d_m"], result["metrics"]["linear_speed_peak_mps"],
         result["metrics"]["generalized_actuator_torque_peak_nm"]], rtol=2e-7, atol=1e-8)
    np.testing.assert_allclose(physical_duration, result["arguments"]["duration"], rtol=0, atol=1e-7)
    report = {
        "passed": True, "task_success": result["task_success"], "strict_success": result["strict_success"],
        "final_stage": result["final_task_stage"], "action_count": count,
        "action_replay_max_abs": action_error, "reservoir_replay_max_abs": state_error,
        "physical_steps": physical_steps, "physical_duration_s": physical_duration,
        "independent_position_rmse_m": rmse, "independent_peak_speed_mps": speed,
        "independent_peak_torque_nm": torque,
        "external_penetration_mm": 1000 * result["stats"]["max_external_penetration_m"],
        "files_sha256": {key: sha(path) for key, path in paths.items()},
        "checkpoint_sha256": checkpoint_sha, "audit_tool_sha256": sha(__file__),
        "source_sha256": result["source_sha256"], "arguments": result["arguments"],
        "limitation": "Development simulation replay, not an independent closed-loop physics or hardware trial."
    }
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
