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

sys.path.insert(0, ".")
from direct_esn_compliance import (  # noqa: E402
    DirectESNConfig, DirectESNController, DirectESNObservation,
    encode_direct_esn_observation)
from pink_takeover_experiment import OUT  # noqa: E402  (light import: paths only)

# Heavy env stack is imported lazily inside the eval part; importing it here
# would load pinocchio/osqp/OSMesa whose native libraries corrupt the heap for
# subsequent heavy BLAS training in the same process (SIGSEGV).


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


class MLPStudent:
    """Pure-numpy 32->64->7 tanh MLP (Adam, manually trained) deployed as a
    controller.  Numpy keeps torch's OpenMP out of the pinocchio/osqp process."""

    def __init__(self, w1, b1, w2, b2, mean, std):
        self.w1, self.b1, self.w2, self.b2 = w1, b1, w2, b2
        self.mean, self.std = mean, std

    def reset(self):
        pass

    def _forward(self, x):
        h = np.tanh(x @ self.w1.T + self.b1)
        return np.tanh(h @ self.w2.T + self.b2)

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None):
        obs = np.asarray(encode_direct_esn_observation(DirectESNObservation(
            joint_position, joint_velocity, wbc_task_twist,
            pose_error if pose_error is not None else np.zeros(6),
            twist_error if twist_error is not None else np.zeros(6))), dtype=float)
        out = self._forward((obs - self.mean) / self.std)
        return SimpleAction(np.clip(out, -1.0, 1.0))


def train_mlp(x, y, seed, epochs=60, batch=256, lr=1e-3, wd=1e-5):
    rng = np.random.default_rng(seed)
    w1 = rng.normal(0, (2.0 / 32) ** 0.5, (64, 32))
    b1 = np.zeros(64)
    w2 = rng.normal(0, (2.0 / 64) ** 0.5, (7, 64))
    b2 = np.zeros(7)
    mean, std = x.mean(0), x.std(0) + 1e-6
    xn = (x - mean) / std
    params = [w1, b1, w2, b2]
    m = [np.zeros_like(p) for p in params]
    v = [np.zeros_like(p) for p in params]
    n = len(xn)
    step = 0
    for _ in range(epochs):
        order = rng.permutation(n)
        for start in range(0, n, batch):
            idx = order[start:start + batch]
            xb, yb = xn[idx], y[idx]
            h_pre = xb @ w1.T + b1
            h = np.tanh(h_pre)
            out = np.tanh(h @ w2.T + b2)
            d_out = (out - yb) * (1 - out ** 2) / len(idx)
            g_w2 = d_out.T @ h + wd * w2
            g_b2 = d_out.sum(0) + wd * b2
            d_h = (d_out @ w2) * (1 - h ** 2)
            g_w1 = d_h.T @ xb + wd * w1
            g_b1 = d_h.sum(0) + wd * b1
            grads = [g_w1, g_b1, g_w2, g_b2]
            step += 1
            for i, (p, g) in enumerate(zip(params, grads)):
                m[i] = 0.9 * m[i] + 0.1 * g
                v[i] = 0.999 * v[i] + 0.001 * g * g
                mhat = m[i] / (1 - 0.9 ** step)
                vhat = v[i] / (1 - 0.999 ** step)
                p -= lr * mhat / (np.sqrt(vhat) + 1e-8)
    mse = float(((MLPStudent(w1, b1, w2, b2, mean, std)._forward(xn) - y) ** 2).mean())
    return MLPStudent(w1, b1, w2, b2, mean, std), mse


class SimpleAction:
    def __init__(self, a):
        self.bounded_filter_action = a


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
    from pink_takeover_experiment import make_env, scenarios
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
    from run_benchmark import TORQUE_LIMITS as limits

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


def part_train():
    """Training process: numpy + data only (no mujoco/pinocchio in-process)."""
    x, y, episodes = load_xy()
    print(f"data x={x.shape}")
    for seed in (11, 29):
        mlp, mse = train_mlp(x, y, seed)
        np.savez(OUT / f"attr_mlp_s{seed}.npz", w1=mlp.w1, b1=mlp.b1, w2=mlp.w2,
                 b2=mlp.b2, mean=mlp.mean, std=mlp.std)
        print(f"mlp_s{seed} mse={mse:.5f}")
    for tc in (0.12, 0.01):
        esn, mse = train_esn(episodes, tc, 29)
        esn.model.save_npz(OUT / f"attr_esn_tau{tc}_s29.npz")
        print(f"esn_tau{tc}_s29 mse={mse:.5f}")


def part_eval():
    """Eval process: envs + probes only (no heavy BLAS training)."""
    from pink_takeover_experiment import make_env, TakeoverStudent as _TS
    globals()["TakeoverStudent"] = _TS
    env = make_env("torque_takeover_gc", 7)
    env.reset(seed=7, options={"fixture_index": 0})
    q0 = env.data.qpos[:7].copy()
    J = env.diagnostics()["hand_jacobian"]
    env.close()
    Kv = np.array([42., 42., 36., 32., 9., 8., 6.])

    variants = []
    for seed in (11, 29):
        with np.load(OUT / f"attr_mlp_s{seed}.npz") as a:
            ctrl = MLPStudent(a["w1"], a["b1"], a["w2"], a["b2"], a["mean"], a["std"])
        variants.append((f"mlp_s{seed}", ctrl, float("nan")))
    for tc in (0.12, 0.01):
        variants.append((f"esn_tau{tc}_s29",
                         TakeoverStudent(DirectESNController.from_npz(
                             OUT / f"attr_esn_tau{tc}_s29.npz")), float("nan")))

    print(f"{'variant':18s} {'damping diag (learned)':>42s} | {'succ':>7s} {'peakErr':>9s}")
    for name, ctrl, _ in variants:
        K = probe_damping(ctrl, env, q0, J)
        ok, n, peak, _ = eval_full(ctrl)
        diag = " ".join(f"{v:5.1f}" for v in K)
        print(f"{name:18s} [{diag}] | {ok:3d}/{n:<3d} {peak:8.0f}mm")
    print(f"{'expert servo':18s} [{' '.join(f'{v:5.1f}' for v in Kv)}]")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", choices=("train", "eval"), required=True)
    part = parser.parse_args().part
    # Import the env stack lazily so the train part never loads it.
    if part == "train":
        part_train()
    else:
        part_eval()
