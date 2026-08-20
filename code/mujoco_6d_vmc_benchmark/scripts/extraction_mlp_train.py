"""Standalone MLP trainer for the extraction experiment.

Runs in its own process: importing torch (with CUDA) after a long MuJoCo
session in the same interpreter segfaults on this platform, so the train
stage spawns this file via subprocess.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

OUT = Path(os.environ.get("EXT_OUT", "/home/arm1/vmc_mujoco_runtime/outputs/extraction_esn"))
WASHOUT = 10
ENGAGED_OVERSAMPLE = 4


def main() -> None:
    import os
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"mlp training on {device}"
          + (f" ({torch.cuda.get_device_name(0)})" if device == "cuda" else ""), flush=True)
    with np.load(OUT / "teacher_data.npz", allow_pickle=True) as archive:
        episodes = list(archive["episodes"])
    xs = np.concatenate([np.stack([
        np.concatenate([o.joint_position, o.joint_velocity, o.wbc_task_twist,
                        o.wbc_pose_error, o.wbc_twist_error])
        for o in ep["obs"][WASHOUT:]]) for ep in episodes])
    ys = np.concatenate([np.asarray(ep["actions"][WASHOUT:]) for ep in episodes])
    mean, std = xs.mean(0), xs.std(0) + 1e-8
    xn = torch.tensor((xs - mean) / std, dtype=torch.float32, device=device)
    yn = torch.tensor(ys, dtype=torch.float32, device=device)
    import json
    from dataclasses import asdict
    from mlp_compliance_baseline import MLPBaselineConfig
    for tseed in (0, 1, 2, 3, 4):
        torch.manual_seed(tseed)
        hidden = int(os.environ.get('MLP_HIDDEN', '128'))
        net = torch.nn.Sequential(torch.nn.Linear(32, hidden), torch.nn.Tanh(),
                                  torch.nn.Linear(hidden, 7), torch.nn.Tanh()).to(device)
        opt = torch.optim.Adam(net.parameters(), lr=2e-3)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=15000)
        engaged = torch.tensor(np.any(np.abs(ys) > 0.05, axis=1), dtype=torch.float32, device=device)
        weights = 1.0 + (ENGAGED_OVERSAMPLE - 1.0) * engaged
        epochs = int(os.environ.get('MLP_EPOCHS', '15000'))
        for epoch in range(epochs):
            idx = torch.multinomial(weights, 4096, replacement=True)
            loss = torch.nn.functional.mse_loss(net(xn[idx]), yn[idx])
            opt.zero_grad(); loss.backward(); opt.step()
            sched.step()
        with torch.no_grad():
            print(f"mlp seed={tseed} MSE={torch.nn.functional.mse_loss(net(xn), yn).item():.5f}", flush=True)
        w1, b1, w2, b2 = [q.detach().cpu().numpy().copy() for q in net.parameters()]
        np.savez_compressed(
            OUT / f"mlp_s{tseed}.npz", controller_family=np.asarray(["mlp_baseline"]),
            config_json=np.asarray([json.dumps(asdict(MLPBaselineConfig(hidden_units=hidden)))]),
            input_mean=mean, input_std=std, w1=w1, b1=b1, w2=w2, b2=b2)

    print("mlp saved (5 seeds)", flush=True)


if __name__ == "__main__":
    main()
