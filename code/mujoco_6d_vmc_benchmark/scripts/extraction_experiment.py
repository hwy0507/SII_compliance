"""Extraction-scenario compliance training: ESN vs MLP vs FW.

Scenario: bare-arm under-board extraction on FR3 + vendored Pink-IK WBC.
The static board blocks the carry corridor; pure tracking never crosses.
Escape = slow the WBC feedback (wbc_scale channel) + persistent -z yield
(twist channel) while inside the corridor, release after crossing.

Both students are deployed UNGATED (activation=1, same as training targets)
for architectural fairness; the ESN keeps its reservoir state.

Stages: probe | data | train | eval
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import mujoco
import numpy as np

from direct_esn_compliance import (
    DirectESNConfig, DirectESNController, DirectESNObservation)
from wbc_velocity_residual_core import VelocityResidualSafetyConfig
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv

MENAGERIE = Path("/home/arm1/vmc_mujoco_runtime/mujoco_menagerie")
URDF = Path(__file__).resolve().parent.parent / "assets/fr3_pin/fr3.urdf"
OUT = Path("/home/arm1/vmc_mujoco_runtime/outputs/extraction_esn")

BOARDS = {"low": 0.605, "mid": 0.615, "high": 0.625, "heldout": 0.610}
CORRIDOR_X_IN = 0.56      # start slowing/dipping before the board edge
CORRIDOR_X_OUT = 0.26     # release after the far edge
DIP_CLEARANCE = 0.065     # palm depth below the board underside to hold
WBC_SLOW_ACTION = 0.875   # action[0] giving wbc_scale ~= 0.30
WASHOUT = 10


SCENARIO_SAFETY = VelocityResidualSafetyConfig(maximum_linear_yield_mps=0.50, minimum_wbc_scale=0.10)


def make_env(board_z: float | None, seed: int):
    return PandaWBCVelocityResidualEnv(
        menagerie=MENAGERIE, fan_ye_model_npz=None, fan_ye_train_summary_json=None,
        observation_mode="direct_esn", rod_enabled=False, seed=seed, robot="fr3",
        execution_mode="twist", wbc_backend="pink", wbc_urdf_path=URDF,
        table_board_underside_z=board_z, safety_config=SCENARIO_SAFETY)


class Teacher:
    """Position-rule corridor escape (hand pose is FK of q: deployable)."""

    def __init__(self, board_z: float | None) -> None:
        self.board_z = board_z

    def act(self, hand_x: float, hand_z: float, nominal_vx: float = 0.0) -> np.ndarray:
        action = np.zeros(7)
        if self.board_z is None:
            return action
        z_target = self.board_z - DIP_CLEARANCE
        # Phase gate: dip only in the carry phase (nominal twist moving -x).
        # During descent (twist mostly -z) the corridor x-window also matches,
        # and dipping there would drive the fingers into the table/block.
        carrying = nominal_vx < -0.02
        if carrying and CORRIDOR_X_OUT < hand_x < CORRIDOR_X_IN and hand_z > z_target:
            depth = hand_z - z_target
            action[0] = 1.0  # WBC feedback authority -> minimum (0.10)
            action[3] = -float(np.clip(depth / 0.05, 0.0, 1.0))  # P-hold yield
        return action


class NeutralPolicy:
    def reset(self) -> None: ...

    def act(self, *args, **kwargs):
        class R:
            bounded_filter_action = np.zeros(7)
        return R()


class UngatedESN:
    """ESN deployed with activation gating disabled (parity with training)."""

    def __init__(self, model: DirectESNController) -> None:
        self.model = model

    def reset(self) -> None:
        self.model.reset()

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None):
        from esn_compliance import ESNObservation
        feature = self.model.advance(
            ESNObservation(joint_position, joint_velocity, wbc_task_twist),
            pose_error, twist_error)
        return self.model.action_from_feature(feature, activation=1.0)


class UngatedMLP:
    """MLPComplianceController inference without the error-activation gate."""

    def __init__(self, inner) -> None:
        self.inner = inner

    def reset(self) -> None:
        self.inner.reset()

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None):
        observation = np.concatenate([
            np.asarray(joint_position, dtype=float),
            np.asarray(joint_velocity, dtype=float),
            np.asarray(wbc_task_twist, dtype=float),
            np.asarray(pose_error, dtype=float) if pose_error is not None else np.zeros(6),
            np.asarray(twist_error, dtype=float) if twist_error is not None else np.zeros(6),
        ])
        c = self.inner
        normalized = (observation - c.mean) / c.std
        hidden = np.tanh(normalized @ c.w1.T + c.b1)
        bounded = np.tanh(hidden @ c.w2.T + c.b2)

        class R:
            pass
        r = R()
        r.bounded_filter_action = np.concatenate(
            [[max(0.0, float(bounded[0]))], np.clip(bounded[1:], -1.0, 1.0)])
        return r


def board_force(env) -> float:
    bid = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "extraction_board")
    if bid < 0:
        return 0.0
    total = 0.0
    for c in range(env.data.ncon):
        con = env.data.contact[c]
        if con.geom1 == bid or con.geom2 == bid:
            wrench = np.zeros(6)
            mujoco.mj_contactForce(env.model, env.data, c, wrench)
            total += float(np.linalg.norm(wrench[:3]))
    return total


def rollout(env, seed: int, policy, *, teacher: Teacher | None = None, collect: bool = False):
    env.reset(seed=seed, options={"fixture_index": 0})
    observations: list[DirectESNObservation] = []
    actions: list[np.ndarray] = []
    errors, forces, hand_x = [], [], []
    done, info = False, {}
    while not done:
        d = env.diagnostics()
        hand = env.data.xpos[env._hand_id]
        if teacher is not None:
            action = teacher.act(float(hand[0]), float(hand[2]),
                                 float(d["nominal_twist"][0]))
        else:
            action = np.asarray(policy.act(
                d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"],
            ).bounded_filter_action, dtype=float)
        if collect:
            observations.append(DirectESNObservation(
                d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                d["wbc_pose_error"], d["wbc_twist_error"]))
            actions.append(action.copy())
        errors.append(float(np.linalg.norm(d["wbc_pose_error"][:3])))
        forces.append(board_force(env))
        hand_x.append(float(hand[0]))
        _, _, done, _, info = env.step(action)
    e, f, x = np.asarray(errors), np.asarray(forces), np.asarray(hand_x)
    metrics = dict(
        crossed=bool(x[-1] < CORRIDOR_X_OUT), x_final=float(x[-1]),
        force_peak=float(f.max()), force_integral=float(f.sum() * 0.04),
        contact_s=float((f > 0.5).sum() * 0.04),
        err_final_mm=float(e[-1] * 1000.0), peak_torque=float(info["peak_torque_nm"]),
        hard_limit=bool(info["hard_torque_limit"]), finite=bool(info["finite_state"]))
    return (observations, actions, metrics) if collect else metrics


def stage_probe():
    for name, board in BOARDS.items():
        env = make_env(board, seed=7)
        fw = rollout(env, 7, NeutralPolicy())
        teacher = rollout(env, 7, None, teacher=Teacher(board))
        print(f"[{name} z={board}] FW: crossed={fw['crossed']} x={fw['x_final']:.3f} "
              f"Fint={fw['force_integral']:.0f}Ns err={fw['err_final_mm']:.1f}mm | "
              f"teacher: crossed={teacher['crossed']} x={teacher['x_final']:.3f} "
              f"Fint={teacher['force_integral']:.0f}Ns err={teacher['err_final_mm']:.1f}mm "
              f"tau={teacher['peak_torque']:.1f}")
        env.close()


def stage_data():
    episodes = []
    for name in ("low", "mid", "high", None):
        for seed in (7, 20260817, 1234):
            env = make_env(BOARDS[name] if name else None, seed=seed)
            obs, acts, metrics = rollout(env, seed, None, teacher=Teacher(
                BOARDS[name] if name else None), collect=True)
            episodes.append(dict(name=name or "no_board", seed=seed, obs=obs,
                                 actions=acts, metrics=metrics))
            print(f"  data {name or 'no_board'}/s{seed}: T={len(obs)} crossed={metrics['crossed']}")
            env.close()
    np.savez_compressed(OUT / "teacher_data.npz", episodes=np.asarray(episodes, dtype=object))
    print(f"saved {len(episodes)} episodes")


def stage_train():
    with np.load(OUT / "teacher_data.npz", allow_pickle=True) as archive:
        episodes = list(archive["episodes"])
    for seed in (11, 29, 97):
        model = DirectESNController(DirectESNConfig(seed=seed))
        feats, tgts = [], []
        for episode in episodes:
            feats.append(model.features(episode["obs"], washout_steps=WASHOUT))
            tgts.append(np.clip(np.asarray(episode["actions"][WASHOUT:]), -1.0, 1.0))
        mse = model.fit_readout(np.concatenate(feats), np.concatenate(tgts))
        model.save_npz(OUT / f"esn_s{seed}.npz")
        print(f"  esn seed={seed} MSE={mse:.5f}")
    # MLP: same data, two-layer tanh net, torch
    import torch
    xs = np.concatenate([np.stack([
        np.concatenate([o.joint_position, o.joint_velocity, o.wbc_task_twist,
                        o.wbc_pose_error, o.wbc_twist_error])
        for o in ep["obs"][WASHOUT:]]) for ep in episodes])
    ys = np.concatenate([np.asarray(ep["actions"][WASHOUT:]) for ep in episodes])
    mean, std = xs.mean(0), xs.std(0) + 1e-8
    xn = torch.tensor((xs - mean) / std, dtype=torch.float32)
    yn = torch.tensor(ys, dtype=torch.float32)
    torch.manual_seed(0)
    net = torch.nn.Sequential(torch.nn.Linear(32, 64), torch.nn.Tanh(),
                              torch.nn.Linear(64, 7), torch.nn.Tanh())
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    for epoch in range(3000):
        idx = torch.randint(0, len(xn), (4096,))
        loss = torch.nn.functional.mse_loss(net(xn[idx]), yn[idx])
        opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad():
        print(f"  mlp final MSE={torch.nn.functional.mse_loss(net(xn), yn).item():.5f}")
    w1, b1, w2, b2 = [p.detach().numpy().copy() for p in net.parameters()]
    np.savez_compressed(OUT / "mlp.npz", controller_family=np.asarray(["mlp_baseline"]),
                        mean=mean, std=std, w1=w1, b1=b1, w2=w2, b2=b2)
    print("students saved")


def stage_eval():
    from mlp_compliance_baseline import MLPComplianceController
    methods = ([("fw", None, None)]
               + [(f"esn_s{s}", OUT / f"esn_s{s}.npz", "esn") for s in (11, 29, 97)]
               + [("mlp", OUT / "mlp.npz", "mlp")]
               + [("teacher", None, "teacher")])
    rows = []
    for label, path, kind in methods:
        for board_name in ("low", "mid", "high", "heldout"):
            for seed in (7, 1234):
                env = make_env(BOARDS[board_name], seed=seed)
                if kind == "teacher":
                    m = rollout(env, seed, None, teacher=Teacher(BOARDS[board_name]))
                elif kind is None:
                    m = rollout(env, seed, NeutralPolicy())
                elif kind == "esn":
                    m = rollout(env, seed, UngatedESN(DirectESNController.from_npz(path)))
                else:
                    m = rollout(env, seed, UngatedMLP(MLPComplianceController.from_npz(path)))
                rows.append(dict(method=label, board=board_name, seed=seed, **m))
                env.close()
        ok = sum(r["crossed"] for r in rows if r["method"] == label)
        print(f"  eval {label}: crossed {ok}/8")
    json.dump(rows, open(OUT / "eval.json", "w"), indent=1)
    import collections
    by = collections.defaultdict(list)
    for r in rows:
        by[r["method"]].append(r)
    print(f"{'method':10s} {'cross':>7s} {'Fint':>7s} {'Fpk':>6s} {'errF':>7s} {'tau':>6s}")
    for label, rs in by.items():
        cr = sum(r["crossed"] for r in rs)
        print(f"{label:10s} {cr:3d}/{len(rs):<3d}  "
              f"{np.mean([r['force_integral'] for r in rs]):6.1f} "
              f"{np.mean([r['force_peak'] for r in rs]):5.0f} "
              f"{np.mean([r['err_final_mm'] for r in rs]):6.1f} "
              f"{np.mean([r['peak_torque'] for r in rs]):5.1f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="all", choices=("probe", "data", "train", "eval", "all"))
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if args.stage in ("probe", "all"):
        print("== probe =="); stage_probe()
    if args.stage in ("data", "all"):
        print("== data =="); stage_data()
    if args.stage in ("train", "all"):
        print("== train =="); stage_train()
    if args.stage in ("eval", "all"):
        print("== eval =="); stage_eval()
    print(f"done {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
