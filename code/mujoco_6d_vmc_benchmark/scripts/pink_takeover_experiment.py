"""Residual vs full-takeover ESN architectures on the vendored Pink-IK WBC (FR3).

Nominal stack: Autolife Pink differential-IK WBC (vendored, adapted to FR3)
-> shared velocity servo -> torque.  One fixed expert controller
(Pink WBC + servo + bounded residual ESN) generates demonstrations.  Three
students with IDENTICAL ESN hyperparameters and IDENTICAL data imitate it
under different deployment architectures:

  A  residual      : action = residual torque  (3% budget), deployed ON TOP
                     of the running velocity servo.      [current system]
  B  takeover_gc   : action = total torque minus gravity bias (100% authority),
                     gravity-comp feedthrough only, NO velocity servo.
  C  takeover      : action = total torque including gravity (100% authority),
                     nothing else runs.

Stages (run with --stage all):
  data    expert rollouts -> per-step (obs, torque components) npz
  train   fit A/B/C readouts (episode-wise reservoir features, washout)
  dagger  one DAgger round for B/C: expert shadow labels on student states
  eval    all methods x {fx0..fx3, dual, no-rod} x seeds -> json summary
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from direct_esn_compliance import (
    DirectESNConfig, DirectESNController, DirectESNObservation,)
from run_benchmark import TORQUE_LIMITS
from run_direct_esn_mujoco import resolve_override_fixture
from vmc_compliance_baseline import load_controller
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv

MENAGERIE = Path("/home/arm1/vmc_mujoco_runtime/mujoco_menagerie")
URDF = Path(__file__).resolve().parent.parent / "assets/fr3_pin/fr3.urdf"
EXPERT_ESN = Path(
    "/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_fixture23_coverage_20260817"
    "/torque_mode/esn_bc_251.npz")
OUT = Path("/home/arm1/vmc_mujoco_runtime/outputs/pink_takeover")

RESIDUAL_SCALE = 0.03
DATA_SEEDS = (7, 20260817, 1234)
EVAL_SEEDS = (7, 20260817, 1234)
WASHOUT = 10

# Takeover students must NOT inherit the residual policy's error-gated
# activation (total torque — gravity! — is needed even at zero tracking
# error).  DirectESNConfig validates gains as positive, so the gating is
# bypassed at deployment through a wrapper that calls the controller with
# activation=1.0 directly instead of patching the core config.
class TakeoverStudent:
    """DirectESN deployed at full authority with activation gating disabled."""

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


def make_env(execution_mode: str, seed: int, *, rod: bool = True, dual: bool = False):
    env = PandaWBCVelocityResidualEnv(
        menagerie=MENAGERIE, fan_ye_model_npz=None, fan_ye_train_summary_json=None,
        observation_mode="direct_esn", rod_enabled=rod, seed=seed, robot="fr3",
        execution_mode=execution_mode, residual_torque_scale=RESIDUAL_SCALE,
        wbc_backend="pink", wbc_urdf_path=URDF)
    if dual:
        fixtures, _ = resolve_override_fixture(
            0.178, 0.541, 1.085, None, 2, rod_cycles=2, cycle_period_s=1.8)
        env.fixtures = fixtures
    return env


def scenarios():
    for index in range(4):
        yield f"fx{index}", dict(rod=True, dual=False, fixture=index)
    yield "dual", dict(rod=True, dual=True, fixture=0)
    yield "no_rod", dict(rod=False, dual=False, fixture=0)


def expert_action(expert, diagnostics):
    action = expert.act(
        diagnostics["joint_position"], diagnostics["joint_velocity"],
        diagnostics["nominal_twist"],
        pose_error=diagnostics["wbc_pose_error"],
        twist_error=diagnostics["wbc_twist_error"])
    return action.bounded_filter_action


def rollout_collect(env, fixture_index, expert, seed, *, shadow: bool = False, student=None):
    """Run one episode; return (obs[T,32], expert targets dict, info).

    ``shadow=True`` rolls out the STUDENT in the env while the expert labels
    are computed on the visited states via the env's shadow servo channel.
    """
    env.reset(seed=seed, options={"fixture_index": fixture_index})
    obs_seq: list[DirectESNObservation] = []
    tgt = {"res": [], "gc": [], "full": []}
    residual_limits = env.residual_torque_limits
    expert.reset() if hasattr(expert, "reset") else None
    if student is not None and hasattr(student, "reset"):
        student.reset()
    done, info, step = False, {}, 0
    while not done:
        diagnostics = env.diagnostics()
        obs_seq.append(DirectESNObservation(
            diagnostics["joint_position"], diagnostics["joint_velocity"],
            diagnostics["nominal_twist"],
            diagnostics["wbc_pose_error"], diagnostics["wbc_twist_error"]))
        if shadow:
            env.expert_residual_torque = expert_action(expert, diagnostics) * residual_limits
            action = student.act(
                diagnostics["joint_position"], diagnostics["joint_velocity"],
                diagnostics["nominal_twist"],
                pose_error=diagnostics["wbc_pose_error"],
                twist_error=diagnostics["wbc_twist_error"]).bounded_filter_action
            _, _, done, _, info = env.step(action)
            components = env.diagnostics()["shadow_torque_components"]
        else:
            action = expert_action(expert, diagnostics)
            _, _, done, _, info = env.step(action)
            components = env.diagnostics()["torque_components"]
        # The torque decomposition of the substep that just executed pairs
        # with the observation collected from the state the action came from.
        tgt["res"].append(components["policy"] / residual_limits)
        tgt["gc"].append((components["total"] - components["bias"]) / TORQUE_LIMITS)
        tgt["full"].append(components["total"] / TORQUE_LIMITS)
        step += 1
    env.expert_residual_torque = None
    return obs_seq, {k: np.asarray(v, dtype=float) for k, v in tgt.items()}, info


def stage_data():
    expert = load_controller(EXPERT_ESN)
    episodes = []
    for seed in DATA_SEEDS:
        for name, spec in scenarios():
            env = make_env("torque_residual", seed, rod=spec["rod"], dual=spec["dual"])
            obs, targets, info = rollout_collect(env, spec["fixture"], expert, seed)
            episodes.append(dict(name=name, seed=seed, obs=obs, targets=targets,
                                 success=bool(info["task_success"])))
            print(f"  data {name}/s{seed}: T={len(obs)} success={info['task_success']}")
            env.close()
    np.savez_compressed(
        OUT / "expert_data.npz",
        episodes=np.asarray(episodes, dtype=object),
        allow_pickle=True)
    print(f"saved {len(episodes)} episodes -> {OUT/'expert_data.npz'}")


def load_episodes():
    with np.load(OUT / "expert_data.npz", allow_pickle=True) as archive:
        return list(archive["episodes"])


TARGET_KEY = {"residual": "res", "takeover_gc": "gc", "takeover": "full"}


def fit_student(episodes, arch: str, seed: int) -> DirectESNController:
    model = DirectESNController(DirectESNConfig(seed=seed))
    features_all, targets_all = [], []
    for episode in episodes:
        features = model.features(episode["obs"], washout_steps=WASHOUT)
        features_all.append(features)
        targets_all.append(np.clip(episode["targets"][TARGET_KEY[arch]][WASHOUT:], -1.0, 1.0))
    mse = model.fit_readout(np.concatenate(features_all), np.concatenate(targets_all))
    print(f"  fit {arch} seed={seed}: train MSE={mse:.5f}")
    return model


def stage_train():
    episodes = load_episodes()
    for arch in ("residual", "takeover_gc", "takeover"):
        for seed in (11, 29, 97):
            model = fit_student(episodes, arch, seed)
            path = OUT / f"student_{arch}_s{seed}.npz"
            model.save_npz(path)
    print("students saved")


def stage_dagger():
    """One DAgger round for the takeover students on expert shadow labels."""
    episodes = load_episodes()
    expert = load_controller(EXPERT_ESN)
    for arch in ("takeover_gc", "takeover"):
        mode = "torque_takeover_gc" if arch == "takeover_gc" else "torque_takeover"
        student = TakeoverStudent(DirectESNController.from_npz(OUT / f"student_{arch}_s29.npz"))
        new_episodes = []
        for seed in DATA_SEEDS[:2]:
            for name, spec in scenarios():
                env = make_env(mode, seed, rod=spec["rod"], dual=spec["dual"])
                obs, targets, info = rollout_collect(
                    env, spec["fixture"], expert, seed, shadow=True, student=student)
                new_episodes.append(dict(name=f"dagger_{name}", seed=seed, obs=obs,
                                         targets=targets, success=bool(info["task_success"])))
                print(f"  dagger {arch} {name}/s{seed}: T={len(obs)} success={info['task_success']}")
                env.close()
        for seed in (11, 29, 97):
            model = fit_student(episodes + new_episodes, arch, seed)
            model.save_npz(OUT / f"student_{arch}_s{seed}_d.npz")
    print("dagger students saved")


def eval_one(label, mode, controller, spec, seed, dual: bool):
    env = make_env(mode, seed, rod=spec["rod"], dual=dual)
    env.reset(seed=seed, options={"fixture_index": spec["fixture"]})
    if controller is not None and hasattr(controller, "reset"):
        controller.reset()
    done, info, errs = False, {}, []
    while not done:
        diagnostics = env.diagnostics()
        errs.append(float(np.linalg.norm(diagnostics["wbc_pose_error"][:3])))
        if controller is None:
            action = np.zeros(7)
        else:
            action = controller.act(
                diagnostics["joint_position"], diagnostics["joint_velocity"],
                diagnostics["nominal_twist"],
                pose_error=diagnostics["wbc_pose_error"],
                twist_error=diagnostics["wbc_twist_error"]).bounded_filter_action
        _, _, done, _, info = env.step(action)
    errs = np.asarray(errs)
    env.close()
    return {
        "label": label, "scenario": spec["name"], "seed": seed,
        "success": bool(info["task_success"]),
        "peak_err_mm": float(errs.max() * 1000.0),
        "at_grasp_mm": float(errs[min(int(2.4 / 0.04), len(errs) - 1)] * 1000.0),
        "final_err_mm": float(errs[-1] * 1000.0),
        "rmse_mm": float(np.sqrt((errs ** 2).mean()) * 1000.0),
        "peak_torque_nm": float(info["peak_torque_nm"]),
        "hard_limit": bool(info["hard_torque_limit"]),
        "finite": bool(info["finite_state"]),
    }


def stage_eval():
    results = []
    methods = [
        ("pink_fw", "torque_residual", None),
        ("residual_A", "torque_residual", OUT / "student_residual_s29.npz"),
    ]
    for arch, mode in (("takeover_gc", "torque_takeover_gc"), ("takeover", "torque_takeover")):
        for seed in (11, 29, 97):
            for suffix in ("", "_d"):
                path = OUT / f"student_{arch}_s{seed}{suffix}.npz"
                if path.exists():
                    methods.append((f"{arch}{suffix}_s{seed}", mode, path))
    for label, mode, path in methods:
        controller = None if path is None else load_controller(path)
        if controller is not None and mode.startswith("torque_takeover"):
            controller = TakeoverStudent(controller)
        for seed in EVAL_SEEDS:
            for name, spec in scenarios():
                spec = dict(spec)
                spec["name"] = name
                results.append(eval_one(label, mode, controller, spec, seed,
                                        dual=(name == "dual")))
        print(f"  evaluated {label}")
    with open(OUT / "eval_results.json", "w") as handle:
        json.dump(results, handle, indent=1)
    # Compact table
    by_label: dict[str, list] = {}
    for row in results:
        by_label.setdefault(row["label"], []).append(row)
    print(f"{'method':22s} {'success':>8s} {'peakErr':>8s} {'rmse':>8s} {'peakTau':>8s} {'hardLim':>8s}")
    for label, rows in by_label.items():
        ok = sum(r["success"] for r in rows)
        print(f"{label:22s} {ok:3d}/{len(rows):<3d}  "
              f"{np.mean([r['peak_err_mm'] for r in rows]):7.1f} "
              f"{np.mean([r['rmse_mm'] for r in rows]):7.1f} "
              f"{np.mean([r['peak_torque_nm'] for r in rows]):7.1f} "
              f"{sum(r['hard_limit'] for r in rows):6d}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="all",
                        choices=("data", "train", "dagger", "eval", "all"))
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    started = time.time()
    if args.stage in ("data", "all"):
        print("== stage: data =="); stage_data()
    if args.stage in ("train", "all"):
        print("== stage: train =="); stage_train()
    if args.stage in ("dagger", "all"):
        print("== stage: dagger =="); stage_dagger()
    if args.stage in ("eval", "all"):
        print("== stage: eval =="); stage_eval()
    print(f"done in {time.time()-started:.0f}s")


if __name__ == "__main__":
    main()
