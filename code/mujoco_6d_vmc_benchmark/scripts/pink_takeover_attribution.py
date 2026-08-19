"""Attribution experiment: is full-takeover instability caused by ESN (model
class) or by imitation learning (training paradigm)?

Trains on the SAME expert data as pink_takeover_experiment and deploys at
FULL authority:

  - mlp      : 32->64->7 tanh MLP, no memory  (paradigm same, model changed)
  - esn_fast : DirectESN with time_constant 0.01 s (model same, lag removed)
  - esn_slow : reference run, time_constant 0.12 s (reproduces the failure)

Also probes the effective damping d(tau)/d(qdot) of each at home.
"""
import os
os.environ.setdefault("MUJOCO_GL", "osmesa")
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, ".")
from direct_esn_compliance import (  # noqa: E402
    DirectESNConfig, DirectESNController, DirectESNObservation,
    encode_direct_esn_observation)
from pink_takeover_experiment import OUT, make_env, scenarios  # noqa: E402
from pink_takeover_experiment import TakeoverStudent  # noqa: E402
from run_benchmark import TORQUE_LIMITS  # noqa: E402

WASHOUT = 10
ARCH = "gc"   # takeover+GC target: dynamic part only


def load_xy():
    with np.load(OUT / "expert_data.npz", allow_pickle=True) as archive:
        episodes = list(archive["episodes"])
    xs, ys = [], []
    for episode in episodes:
        x = np.asarray([encode_direct_esn_observation(o) for o in episode["obs"]])
        y = episode["targets"][ARCH]
        xs.append(x[WASHOUT:]); ys.append(y[WASHOUT:])
    return np.concatenate(xs), np.concatenate(ys), episodes


class StudentMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(32, 64), nn.Tanh(), nn.Linear(64, 7), nn.Tanh())

    def forward(self, x):
        return self.net(x)


class MLPStudent:
    """Torch-trained MLP wrapped in the deployment controller interface."""

    def __init__(self, net, mean, std):
        self.net = net.eval()
        self.mean = mean
        self.std = std

    def reset(self):
        pass

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None):
        obs = np.asarray(encode_direct_esn_observation(DirectESNObservation(
            joint_position, joint_velocity, wbc_task_twist,
            pose_error if pose_error is not None else np.zeros(6),
            twist_error if twist_error is not None else np.zeros(6))), dtype=float)
        with torch.no_grad():
            out = self.net(torch.from_numpy((obs - self.mean) / self.std).float()).numpy()
        return SimpleAction(np.clip(out, -1.0, 1.0))


class SimpleAction:
    def __init__(self, a):
        self.bounded_filter_action = a


def train_mlp(x, y, seed):
    torch.manual_seed(seed)
    net = StudentMLP()
    mean, std = x.mean(0), x.std(0) + 1e-6
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    xt = torch.from_numpy(((x - mean) / std)).float()
    yt = torch.from_numpy(y).float()
    ds = torch.utils.data.TensorDataset(xt, yt)
    loader = torch.utils.data.DataLoader(ds, batch_size=256, shuffle=True)
    for epoch in range(60):
        for xb, yb in loader:
            opt.zero_grad()
            loss = ((net(xb) - yb) ** 2).mean()
            loss.backward()
            opt.step()
    with torch.no_grad():
        mse = ((net(xt) - yt) ** 2).mean().item()
    return MLPStudent(net, mean, std), mse


def train_esn(episodes, time_constant, seed):
    config = DirectESNConfig(seed=seed, time_constant_s=time_constant)
    model = DirectESNController(config)
    feats, tgts = [], []
    for episode in episodes:
        feats.append(model.features(episode["obs"], washout_steps=WASHOUT))
        tgts.append(np.clip(episode["targets"][ARCH][WASHOUT:], -1.0, 1.0))
    mse = model.fit_readout(np.concatenate(feats), np.concatenate(tgts))
    return TakeoverStudent(model), mse


def eval_full(controller, mode="torque_takeover_gc", seeds=(7, 20260817)):
    rows = []
    for seed in seeds:
        for name, spec in scenarios():
            env = make_env(mode, seed, rod=spec["rod"], dual=spec["dual"])
            env.reset(seed=seed, options={"fixture_index": spec["fixture"]})
            if hasattr(controller, "reset"):
                controller.reset()
            done, info, errs = False, {}, []
            while not done:
                d = env.diagnostics()
                errs.append(float(np.linalg.norm(d["wbc_pose_error"][:3])))
                a = controller.act(
                    d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                    pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"]
                ).bounded_filter_action
                _, _, done, _, info = env.step(a)
            env.close()
            rows.append(dict(scenario=name, seed=seed, success=bool(info["task_success"]),
                             peak=float(np.asarray(errs).max() * 1000),
                             tau=float(info["peak_torque_nm"])))
    ok = sum(r["success"] for r in rows)
    peak = np.mean([r["peak"] for r in rows])
    return ok, len(rows), peak, rows


def probe_damping(controller, env, q0, J):
    limits = TORQUE_LIMITS

    def tau_at(qdot):
        a = controller.act(q0, qdot, np.zeros(6), pose_error=np.zeros(6),
                           twist_error=-J @ qdot).bounded_filter_action
        return a * limits

    eps = 0.05
    K = np.zeros(7)
    for i in range(7):
        dq = np.zeros(7); dq[i] = eps
        K[i] = (tau_at(dq)[i] - tau_at(-dq)[i]) / (2 * eps)
    return K


def main():
    x, y, episodes = load_xy()
    env = make_env("torque_takeover_gc", 7)
    env.reset(seed=7, options={"fixture_index": 0})
    q0 = env.data.qpos[:7].copy()
    J = env.diagnostics()["hand_jacobian"]
    env.close()
    Kv = np.array([42., 42., 36., 32., 9., 8., 6.])

    variants = []
    for seed in (11, 29):
        mlp, mse = train_mlp(x, y, seed)
        variants.append((f"mlp_s{seed}", mlp, mse))
    for tc in (0.12, 0.01):
        esn, mse = train_esn(episodes, tc, 29)
        variants.append((f"esn_tau{tc}_s29", esn, mse))

    print(f"{'variant':18s} {'trainMSE':>9s} {'damping diag (learned)':>42s} | {'succ':>7s} {'peakErr':>9s}")
    for name, ctrl, mse in variants:
        K = probe_damping(ctrl, env, q0, J)
        ok, n, peak, _ = eval_full(ctrl)
        diag = " ".join(f"{v:5.1f}" for v in K)
        print(f"{name:18s} {mse:9.5f} [{diag}] | {ok:3d}/{n:<3d} {peak:8.0f}mm")
    print(f"{'expert servo':18s} {'-':>9s} [{' '.join(f'{v:5.1f}' for v in Kv)}]")


if __name__ == "__main__":
    main()
