#!/usr/bin/env python3
"""Train the memoryless MLP compliance baseline on the coverage expert traces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bootstrap_direct_esn_multifixture import _load_episode  # noqa: E402
from mlp_compliance_baseline import MLPBaselineConfig, MLPComplianceController  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expert-traces", type=Path, nargs="+", required=True)
    parser.add_argument("--no-rod-expert-trace", type=Path, required=True)
    parser.add_argument("--output-model", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--hidden-units", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=400)
    parser.add_argument("--learning-rate", type=float, default=1.0e-3)
    parser.add_argument("--weight-decay", type=float, default=1.0e-4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--washout-steps", type=int, default=3)
    parser.add_argument("--target-budget", type=float, required=True,
                        help="deployment residual budget; recorded trace actions are rescaled to this unit")
    args = parser.parse_args()
    if not 0.0 < args.target_budget <= 1.0:
        raise ValueError("target-budget must lie in (0, 1]")

    import torch
    from torch import nn

    observations, actions, trace_provenance = [], [], []
    for path in [*args.expert_traces, args.no_rod_expert_trace]:
        obs, act, trace_budget = _load_episode(path, 1, "bounded_action")
        if trace_budget is None:
            raise ValueError(
                f"{path}: --target-budget requires residual_budget_fraction provenance")
        # ``bounded_action`` is normalized by the residual budget used to
        # record this trace.  A student deployed at another budget must learn
        # the equivalent physical torque, rather than silently inheriting a
        # trace-dependent scale.  This is the same conversion used by the
        # Direct-ESN bootstrap and does not change its observation contract.
        act = np.clip(act * trace_budget / args.target_budget, -1.0, 1.0)
        observations.append(np.asarray([np.concatenate([o.joint_position, o.joint_velocity, o.wbc_task_twist,
                                                        o.wbc_pose_error, o.wbc_twist_error]) for o in obs]))
        actions.append(np.asarray(act))
        trace_provenance.append({"path": str(path), "trace_budget": float(trace_budget),
                                 "target_budget": float(args.target_budget),
                                 "action_unit_conversion": "clip(action * trace_budget / target_budget, -1, 1)"})
        if args.washout_steps:
            observations[-1] = observations[-1][args.washout_steps:]
            actions[-1] = actions[-1][args.washout_steps:]
    X = np.concatenate(observations, axis=0)
    Y = np.concatenate(actions, axis=0)
    mean, std = X.mean(axis=0), X.std(axis=0) + 1.0e-6

    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    indices = rng.permutation(len(X))
    n_val = max(256, int(0.1 * len(X)))
    val_idx, train_idx = indices[:n_val], indices[n_val:]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = nn.Sequential(
        nn.Linear(32, args.hidden_units), nn.Tanh(),
        nn.Linear(args.hidden_units, 7), nn.Tanh(),
    ).to(device)
    xt = torch.tensor((X - mean) / std, dtype=torch.float32, device=device)
    yt = torch.tensor(Y, dtype=torch.float32, device=device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate,
                                 weight_decay=args.weight_decay)
    best_val, best_state, patience, bad = float("inf"), None, 40, 0
    for epoch in range(args.epochs):
        model.train()
        optimizer.zero_grad()
        loss = nn.functional.mse_loss(model(xt[train_idx]), yt[train_idx])
        loss.backward()
        optimizer.step()
        model.eval()
        with torch.no_grad():
            val = float(nn.functional.mse_loss(model(xt[val_idx]), yt[val_idx]))
        if val < best_val - 1.0e-6:
            best_val, best_state, bad = val, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(best_state)
    weights = {k: v.detach().cpu().numpy() for k, v in model.state_dict().items()}
    controller = MLPComplianceController(
        MLPBaselineConfig(hidden_units=args.hidden_units), mean, std,
        weights["0.weight"], weights["0.bias"], weights["2.weight"], weights["2.bias"])
    args.output_model.parent.mkdir(parents=True, exist_ok=True)
    controller.save_npz(args.output_model)
    summary = {
        "method": "mlp_baseline_behavior_cloning", "model": str(args.output_model),
        "hidden_units": args.hidden_units, "epochs_run": epoch + 1,
        "best_val_mse": best_val, "train_samples": int(len(train_idx)), "device": device,
        "traces": [str(p) for p in [*args.expert_traces, args.no_rod_expert_trace]],
        "target_budget": float(args.target_budget),
        "trace_provenance": trace_provenance,
    }
    args.output_summary.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
