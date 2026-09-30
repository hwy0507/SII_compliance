#!/usr/bin/env python3
"""Reproducible engineering pilots; NOT reproductions of a paper's results.

Reuse the repository's legacy rod environments without changing their physics.
The direct actor is 32D -> 7D, the stiffness actor 51D -> 6D. Neither is a
matched replacement for the current four-primitive proprio48 ESN protocol.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MUJOCO_GL", "egl")

import numpy as np
import torch
from stable_baselines3 import PPO, SAC
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecMonitor, VecNormalize
from rl_sixd_stiffness_env import PandaSixDStiffnessEnv, Fixture
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv, VelocityResidualFixture


TRAIN = ((.160, .539, 1.055), (.165, .540, 1.070))
VALIDATION = ((.170, .541, 1.085), (.175, .542, 1.100))


def json_value(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, default=json_value, allow_nan=False) + "\n")


def make_env(kind, menagerie, rows, rod=True, seed=0):
    if kind == "stiffness":
        return PandaSixDStiffnessEnv(
            menagerie=menagerie, fixtures=tuple(Fixture(*r) for r in rows),
            rod_enabled=rod, reference_source="fixed_panda_wbc", seed=seed,
        )
    return PandaWBCVelocityResidualEnv(
        menagerie=menagerie, fixtures=tuple(VelocityResidualFixture(*r) for r in rows),
        fan_ye_model_npz=None, fan_ye_train_summary_json=None,
        observation_mode="direct_esn", rod_enabled=rod, seed=seed,
    )


def factory(kind, menagerie, rank, seed):
    def build():
        return make_env(kind, menagerie, TRAIN, seed=seed + rank)
    return build


def evaluate(args, model=None, normalizer=None):
    rows = []
    for split, fixtures in (("train", TRAIN), ("validation", VALIDATION)):
        for index, fixture in enumerate(fixtures):
            pair = []
            for rod in (True, False):
                env = make_env(args.kind, args.menagerie, (fixture,), rod, args.seed)
                obs, _ = env.reset(seed=args.seed)
                done, total, steps, peak_action = False, 0., 0, 0.
                while not done:
                    if model is None:
                        action = np.zeros(env.action_space.shape, dtype=np.float32)
                    else:
                        action, _ = model.predict(normalizer.normalize_obs(obs), deterministic=True)
                    peak_action = max(peak_action, float(np.max(np.abs(action))))
                    obs, reward, terminated, truncated, info = env.step(action)
                    if not np.isfinite(obs).all() or not np.isfinite(reward):
                        raise RuntimeError("Nonfinite rollout")
                    total += reward
                    steps += 1
                    done = terminated or truncated
                pair.append({"rod": rod, "return": total, "steps": steps,
                             "peak_abs_policy_action": peak_action, "terminal": info})
                env.close()
            contact, no_contact = pair[0]["terminal"], pair[1]["terminal"]
            accepted = bool(contact.get("task_success") and contact.get("effective_collision")
                            and no_contact.get("task_success")
                            and not contact.get("hard_torque_limit")
                            and not no_contact.get("hard_torque_limit"))
            rows.append({"split": split, "fixture_index": index, "fixture": fixture,
                         "paired_legacy_gate": accepted, "pair": pair})
    return {"scope": "legacy rod development only; no office/blind test; no final placement gate",
            "gate_limitation": "legacy lift/hold + effective rod contact + torque + paired no-rod; NOT current physical/placement gate",
            "rows": rows}


class SaveProgress(BaseCallback):
    def __init__(self, output, interval):
        super().__init__()
        self.output, self.interval, self.last = output, interval, 0
        self.started = time.monotonic()

    def _on_step(self):
        if self.num_timesteps - self.last >= self.interval:
            self.last = self.num_timesteps
            stem = self.output / f"checkpoint_{self.num_timesteps}"
            self.model.save(stem)
            self.model.get_env().save(str(stem) + "_vecnormalize.pkl")
            save_json(self.output / "progress.json", {
                "timesteps": self.num_timesteps, "elapsed_s": time.monotonic() - self.started,
                "state": "training", "checkpoint": str(stem) + ".zip"})
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("direct", "stiffness"), required=True)
    parser.add_argument("--algorithm", choices=("ppo", "sac"), required=True)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=8192)
    parser.add_argument("--envs", type=int, default=1,
                        help="Use one in-process environment on the 16-GB desktop.")
    parser.add_argument("--seed", type=int, default=20260923)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refuse to overwrite {args.output}")
    args.output.mkdir(parents=True)
    torch.set_num_threads(1)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    began = time.monotonic()
    env = make_env(args.kind, args.menagerie, TRAIN, seed=args.seed)
    contract = {"observation_shape": env.observation_space.shape, "action_shape": env.action_space.shape}
    settings = {"reward": asdict(env.reward_config)} if args.kind == "direct" else {
        "stiffness_action": asdict(env.action_config), "reference_source": env.reference_source}
    env.close()
    metadata = {
        "purpose": "RL engineering feasibility pilot, not faithful paper reproduction or ESN ranking",
        "command": sys.argv, "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted((ROOT / "scripts").rglob("*.py"))},
        "pilot_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "robot_xml_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in sorted((args.menagerie / "franka_emika_panda").rglob("*.xml"))},
        "versions": {p: importlib.metadata.version(p) for p in
                     ("torch", "stable-baselines3", "gymnasium", "mujoco", "numpy")},
        "python": sys.version, "host": platform.node(),
        "gpu": torch.cuda.get_device_name() if torch.cuda.is_available() else None,
        "args": {k: str(v) if isinstance(v, Path) else v for k,v in vars(args).items()},
        "contract": contract, "settings": settings, "train": TRAIN, "validation": VALIDATION,
        "split_policy": "fixture tuples disjoint; historical development fixtures, not unseen blind test",
        "selection": "fixed final budget; no validation checkpoint selection; no office data",
        "normalization": "VecNormalize fitted on train only; frozen during evaluation",
        "limitations": ["legacy Panda rod only", "not current proprio48",
                        "direct slowdown uses legacy WBC feedback scaling",
                        "stiffness and direct have different plant/controller paths and rewards",
                        "no inference of model superiority from cross-family return"],
    }
    save_json(args.output / "manifest.json", metadata)
    baseline = evaluate(args)
    save_json(args.output / "zero_action_evaluation.json", baseline)
    factories = [factory(args.kind, args.menagerie, i, args.seed) for i in range(args.envs)]
    vector = (DummyVecEnv(factories) if args.envs == 1 else
              SubprocVecEnv(factories, start_method="spawn"))
    vector = VecMonitor(vector, filename=str(args.output / "monitor.csv"))
    vector = VecNormalize(vector, norm_obs=True, norm_reward=False, clip_obs=10.)
    try:
        common = dict(policy="MlpPolicy", env=vector, device=args.device, seed=args.seed,
                      verbose=1, policy_kwargs={"net_arch": [256,256]}, learning_rate=3e-4,
                      gamma=.995, tensorboard_log=str(args.output / "tensorboard"))
        if args.algorithm == "ppo":
            model = PPO(**common, n_steps=256, batch_size=256, n_epochs=5,
                        gae_lambda=.95, clip_range=.15, target_kl=.02)
        else:
            model = SAC(**common, buffer_size=100_000, learning_starts=512,
                        batch_size=256, train_freq=1, gradient_steps=1)
        model.learn(total_timesteps=args.steps, callback=SaveProgress(args.output, 2048))
        model.save(args.output / "final_model")
        vector.save(args.output / "final_vecnormalize.pkl")
        vector.training = False
        learned = evaluate(args, model, vector)
        save_json(args.output / "frozen_evaluation.json", learned)
        summary = {"status": "completed", "algorithm": args.algorithm, "kind": args.kind,
                   "timesteps": model.num_timesteps, "elapsed_s": time.monotonic()-began,
                   "zero_paired_gate": [r["paired_legacy_gate"] for r in baseline["rows"]],
                   "learned_paired_gate": [r["paired_legacy_gate"] for r in learned["rows"]],
                   "publication_ready": False}
        save_json(args.output / "complete.json", summary)
        print(json.dumps(summary), flush=True)
    finally:
        vector.close()


if __name__ == "__main__":
    main()
