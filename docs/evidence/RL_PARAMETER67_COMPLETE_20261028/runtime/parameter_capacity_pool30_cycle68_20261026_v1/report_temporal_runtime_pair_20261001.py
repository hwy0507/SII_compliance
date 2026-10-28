"""Audit both archived runtimes and summarize this fixed-checkpoint diagnostic."""
import argparse
import json
from pathlib import Path

import numpy as np
from audit_temporal_narrow_screen_20261001 import audit, sha
from current_student_policy_20260921 import load_current


def summarize_window(run, method):
    with np.load(run / f"{method}_combined_v4.npz", allow_pickle=False) as trace:
        mask = trace["neuron_time"] >= 45.0
        obs = trace["observation"][mask]
        action = trace["applied_action"][mask]
        with np.load(run / f"{method}_temporal.npz", allow_pickle=False) as model:
            normalized = (obs - model["mean"]) / model["std"]
        result = {
            "window": "policy samples with neuron_time >= 45 s; descriptive, not phase-matched across methods",
            "samples": int(mask.sum()),
            "position_error_min_mm": float(1000 * np.min(trace["task_position_error_m"][mask])),
            "position_error_median_mm": float(1000 * np.median(trace["task_position_error_m"][mask])),
            "speed_median_mps": float(np.median(trace["task_speed_mps"][mask])),
            "ready_max_s": float(np.max(trace["task_ready_s"][mask])),
            "raw_action_mean": action.mean(axis=0).tolist(),
            "raw_action_std": action.std(axis=0).tolist(),
            "normalization_abs_gt12_fraction": float(np.mean(np.abs(normalized) > 12)),
        }
        if method == "esn":
            state = trace["reservoir_state"][mask]
            result["reservoir_abs_gt095_fraction"] = float(np.mean(np.abs(state) > .95))
            result["reservoir_delta_rms"] = float(np.sqrt(np.mean(trace["reservoir_delta"][mask] ** 2)))
            actor = load_current(run / "esn_temporal.npz")
            reset_actions = []
            for row in obs:
                actor.reset()
                reset_actions.append(actor.act(row))
            reset_actions = np.asarray(reset_actions)
            result["offline_reset_action_mean"] = reset_actions.mean(axis=0).tolist()
            result["offline_reset_action_rms_difference"] = float(np.sqrt(np.mean((reset_actions-action)**2)))
            result["offline_reset_caveat"] = "same recorded inputs only; this is not a closed-loop memory-ablation outcome"
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    state = json.loads((args.new / "execution.json").read_text())
    if state["status"] != "complete":
        raise RuntimeError("Pair incomplete; do not report as finished")
    pairs = []
    for method in ("esn", "mlp"):
        old, new = audit(args.old, method), audit(args.new, method)
        if old["checkpoint_sha256"] != new["checkpoint_sha256"]:
            raise ValueError("Checkpoint changed")
        if old["source_sha256"] != new["source_sha256"]:
            raise ValueError("Evaluator source hashes changed")
        arguments = []
        for root in (args.old, args.new):
            original = json.loads((root / f"{method}_combined_v4.json").read_text())["arguments"]
            arguments.append({k: v for k, v in original.items() if k not in ("output", "esn_model")})
        if arguments[0] != arguments[1]:
            raise ValueError("Physical/evaluation arguments changed")
        pairs.append(dict(method=method, prior_runtime=old, frozen_runtime=new,
                          frozen_late_window=summarize_window(args.new, method),
                          delta={key: new[key]-old[key] for key in ("position_rmse_3d_mm", "peak_torque_nm", "peak_speed_mps", "external_penetration_mm")}))
    report = dict(pairs=pairs, frozen_execution=state,
                  frozen_execution_sha256=sha(args.new / "execution.json"),
                  report_source_sha256=sha(Path(__file__)),
                  limitations=["One fixed checkpoint pair and one scene seed; no generalization rate.",
                               "Historical 3.14.0 runtime inferred from model compatibility, not a complete historical environment lock.",
                               "Two virtual environments can differ beyond MuJoCo; not an isolated engine-version causal experiment.",
                               "Late-window diagnostics are descriptive; no teacher-error or reservoir-causality claim.",
                               "Development dt=1e-4 only; unchanged strict success is still required for formal evaluation."])
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps([{k: row[k] for k in ("method", "delta", "frozen_late_window")} for row in pairs], indent=2))


if __name__ == "__main__":
    main()
