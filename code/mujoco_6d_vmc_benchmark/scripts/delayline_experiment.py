#!/usr/bin/env python3
"""v18: delay-line augmented ESN -- the architecture fix for the delayed-cue
task (user decision: modify the algorithm structure).

Why: the cue at t~1.1 predicts the strike at t~3.15 (2 s gap).  The stock
reservoir forgets in <1 s and the memoryless MLP cannot bridge at all
(measured: nobody anticipates; peaks stay at FW level).  The textbook ESN
remedy (Jaeger) is an explicit delay line: the student's input is the
concatenation of K encoded observations at fixed lags, so at decision time
(t~2.85) the buffer still contains the cue window.  The reservoir then only
integrates over one stride.

Controllers compared:
  FW          rigid baseline
  VMC         author's spring carriage (tuned)
  MLP         memoryless student on raw observations
  MLP-DL      memoryless student on the SAME delay line (ablation: does the
              delay information alone suffice, or does the reservoir earn
              its place?)
  ESN-DL      reservoir over the delay line (proposed)

Stages: probe | data | train | dagger | eval
"""
from __future__ import annotations

import json
import os as _os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import direct_esn_compliance as _dec
from direct_esn_compliance import (DirectESNConfig, DirectESNController,
                                   DirectESNObservation,
                                   encode_direct_esn_observation)
import lift_experiment as L
from extraction_experiment import (NeutralPolicy, UngatedESN, UngatedMLP,
                                   VMCScheduled, WASHOUT, _atanh_targets,
                                   _engaged_mask)

TAPS, STRIDE = 5, 10          # 5 taps x 0.4 s = 2.0 s window
RAW_DIM = _dec.DEPLOYABLE_INPUT_DIMENSION      # 32
DL_DIM = RAW_DIM * TAPS                        # 160
_dec.DEPLOYABLE_INPUT_DIMENSION = DL_DIM       # patch BEFORE any controller

OUT = Path(_os.environ.get("DL_OUT", "/home/arm1/vmc_mujoco_runtime/outputs/dl_esn"))
DATA_GRID = (
    ("strike_cue", 2.95, 0.64, 2.0), ("strike_cue", 3.00, 0.64, 2.0),
    ("strike_cue", 3.05, 0.63, 2.0),
    ("strike_none", 0.0, 0.0, 0.0),
    ("plank_arm", 3.00, 0.76, 1.0),
    ("static", 0.05, 25.0),
)
HELDOUT = (("strike_cue", 3.00, 0.62, 1.8), ("static", 0.05, 22.0))
EVAL_BOARDS = DATA_GRID[:5] + (("static", 0.05, 25.0),) + HELDOUT
SEEDS = (11, 29, 97, 123, 555)
DL_GRID = (dict(), dict(reservoir_size=240), dict(spectral_radius=1.05),
           dict(time_constant_s=0.3, reservoir_size=240),
           dict(input_scale=0.65), dict(ridge_lambda=1e-5, reservoir_size=240))


def _expert_for(entry):
    """Scenario-aware label generator: anticipate only on cued boards."""
    if entry[0] == "strike_none":
        return None                      # do-nothing expert
    cfg = OUT / "teacher_cfg.json"
    kw = json.load(open(cfg)) if cfg.exists() else {"y_yield": 0.6, "pre_t": 2.85}
    return L.LiftTeacher(y_yield=kw["y_yield"], pre_t=kw["pre_t"])


class _R:
    def __init__(self, a):
        self.bounded_filter_action = a


from extraction_mlp_train import AugObs  # shared pickle namespace


class DelayLineESN:
    """Reservoir over the delay-line-augmented input (deployable ring buffer)."""

    def __init__(self, model: DirectESNController, taps: int = TAPS, stride: int = STRIDE) -> None:
        self.model, self.taps, self.stride = model, taps, stride
        self.reset()

    def reset(self) -> None:
        self.model.reset()
        self._buf: list[np.ndarray] = []

    def _augmented(self) -> np.ndarray:
        taps = []
        for k in range(self.taps):
            idx = len(self._buf) - 1 - k * self.stride
            taps.append(self._buf[max(0, idx)])
        return np.concatenate(taps[::-1])          # oldest -> newest

    def observe(self, obs: DirectESNObservation) -> np.ndarray:
        """Push one raw observation, return the reservoir feature."""
        self._buf.append(encode_direct_esn_observation(obs))
        return self.model._advance_encoded(self._augmented())

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None):
        obs = DirectESNObservation(joint_position, joint_velocity, wbc_task_twist,
                                   pose_error, twist_error)
        feature = self.observe(obs)
        action = self.model.action_from_feature(feature, activation=1.0)
        return _R(np.asarray(action.bounded_filter_action, dtype=float))


class DelayLineEnsemble:
    def __init__(self, members: list[DelayLineESN]) -> None:
        self.members = members

    def reset(self) -> None:
        for m in self.members:
            m.reset()

    def act(self, *args, **kwargs):
        actions = [np.asarray(m.act(*args, **kwargs).bounded_filter_action, dtype=float)
                   for m in self.members]
        return _R(np.mean(actions, axis=0))


def _dl_features(member: DelayLineESN, episode) -> np.ndarray:
    member.reset()
    feats = [member.observe(o) for o in episode["obs"]]
    return np.asarray(feats, dtype=float)


def fit_dl(episodes, seed: int, cfg: dict) -> DelayLineESN:
    model = DirectESNController(DirectESNConfig(seed=seed, **cfg))
    member = DelayLineESN(model)
    feats, tgts, sm_f, sm_t = [], [], [], []
    for ep in episodes:
        f = _dl_features(member, ep)
        t = np.clip(np.asarray(ep["actions"]), -1.0, 1.0)
        feats.append(f[WASHOUT:])
        tgts.append(t[WASHOUT:])
        sm_f.append(np.diff(f, axis=0))
        sm_t.append(np.diff(_atanh_targets(t), axis=0))
    f_all = np.concatenate(feats)
    t_all = np.concatenate(tgts)
    t_at = _atanh_targets(t_all)
    mask = _engaged_mask(t_all)
    f_aug = np.concatenate([f_all, f_all[mask]])
    t_aug = np.concatenate([t_at, t_at[mask]])
    model.fit_readout(f_aug, t_aug,
                      smoothness_features=np.concatenate(sm_f),
                      smoothness_weight=0.05,
                      smoothness_targets=np.concatenate(sm_t),
                      fit_bias=True)
    return DelayLineESN(model)


def _write_dl_episodes(episodes, path: Path) -> None:
    """Augmented-field episodes for the MLP-DL subprocess (same info set)."""
    aug = []
    for ep in episodes:
        obs = list(ep["obs"])
        per_field = {k: [] for k in ("joint_position", "joint_velocity", "wbc_task_twist")}
        buf = []
        for o in obs:
            buf.append(o)
            for k in per_field:
                idx = len(buf) - 1
                taps = [buf[max(0, idx - kk * STRIDE)] for kk in range(TAPS)]
                per_field[k].append(np.concatenate([getattr(t, k) for t in taps[::-1]]))
        aug_obs = [AugObs(per_field["joint_position"][i], per_field["joint_velocity"][i],
                          per_field["wbc_task_twist"][i],
                          o.wbc_pose_error, o.wbc_twist_error)
                   for i, o in enumerate(obs)]
        aug.append(dict(obs=np.asarray(aug_obs, dtype=object),
                        actions=ep["actions"],
                        weights=ep.get("weights", np.ones(len(obs)))))
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, episodes=np.asarray(aug, dtype=object))


def _mlp_subprocess(out_dir: Path, data_path: Path, hidden: int = 256) -> None:
    r = subprocess.run([sys.executable, str(Path(__file__).parent / "extraction_mlp_train.py")],
                       capture_output=True, text=True,
                       env={**_os.environ, "EXT_OUT": str(out_dir),
                            "MLP_HIDDEN": str(hidden), "MLP_EPOCHS": "15000",
                            "DL_DATA": str(data_path)})
    if r.returncode != 0:
        raise RuntimeError(f"mlp subprocess failed: {r.stderr[-500:]}")


class UngatedMLPDL:
    """Memoryless inference over the SAME delay-line information set."""

    def __init__(self, inner) -> None:
        self.inner = inner

    def reset(self) -> None:
        self.inner.reset()
        self._buf: list[tuple] = []

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None):
        self._buf.append((np.asarray(joint_position, dtype=float),
                          np.asarray(joint_velocity, dtype=float),
                          np.asarray(wbc_task_twist, dtype=float)))
        jp = np.concatenate([self._buf[max(0, len(self._buf) - 1 - k * STRIDE)][0]
                             for k in range(TAPS)][::-1])
        jv = np.concatenate([self._buf[max(0, len(self._buf) - 1 - k * STRIDE)][1]
                             for k in range(TAPS)][::-1])
        tw = np.concatenate([self._buf[max(0, len(self._buf) - 1 - k * STRIDE)][2]
                             for k in range(TAPS)][::-1])
        observation = np.concatenate([
            jp, jv, tw,
            np.asarray(pose_error, dtype=float) if pose_error is not None else np.zeros(6),
            np.asarray(twist_error, dtype=float) if twist_error is not None else np.zeros(6),
        ])
        c = self.inner
        normalized = (observation - c.mean) / c.std
        hidden = np.tanh(normalized @ c.w1.T + c.b1)
        bounded = np.tanh(hidden @ c.w2.T + c.b2)
        return _R(np.concatenate(
            [[max(0.0, float(bounded[0]))], np.clip(bounded[1:], -1.0, 1.0)]))


def _load_mlp(out_dir: Path, dl: bool = False):
    from mlp_compliance_baseline import MLPComplianceController
    members = [MLPComplianceController.from_npz(p)
               for p in sorted(out_dir.glob("mlp_s*.npz"))]
    if dl:
        members = [UngatedMLPDL(m) for m in members]
    else:
        members = [UngatedMLP(m) for m in members]
    return L.EnsemblePolicy(members)


def stage_probe() -> None:
    print("== probe: cue-board teacher selection ==")
    best, best_mean = None, float("inf")
    target = ("strike_cue", 3.00, 0.64, 2.0)
    for y in (0.5, 0.6, 0.85):
        for pre in (2.80, 2.85, 2.90):
            scores = []
            for b in (target, ("strike_cue", 2.95, 0.64, 2.0), ("strike_cue", 3.05, 0.63, 2.0)):
                env = L.build_env(*b, seed=7)
                m = L.rollout(env, 7, teacher=L.LiftTeacher(y_yield=y, pre_t=pre))
                env.close()
                scores.append(m["score"])
            mean = float(np.mean(scores))
            print(f"  y={y} pre={pre}: cue-mean={mean:.2f}")
            if mean < best_mean:
                best, best_mean = (y, pre), mean
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump({"y_yield": best[0], "pre_t": best[1]}, open(OUT / "teacher_cfg.json", "w"))
    print(f"  selected {best} -> teacher_cfg.json")


def stage_data() -> None:
    print("== data: scenario-aware teacher rollouts ==")
    episodes = []
    for entry in DATA_GRID:
        env = L.build_env(*entry, seed=7, noise=L.DATA_NOISE)
        m, ep = L.rollout(env, 7, teacher=_expert_for(entry), collect=True)
        env.close()
        episodes.append(ep)
        print(f"  {entry}: {L._fmt(m)}")
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "teacher_data.npz", episodes=np.asarray(episodes, dtype=object))
    print(f"  saved {len(episodes)} episodes")


def _load_episodes() -> list:
    with np.load(OUT / "teacher_data.npz", allow_pickle=True) as archive:
        raw = list(archive["episodes"])
    return [dict(obs=list(ep["obs"]), actions=ep["actions"], weights=ep["weights"])
            for ep in raw]


def stage_train() -> None:
    print("== train: ESN-DL grid + MLP + MLP-DL ==")
    episodes = _load_episodes()
    (OUT / "mlp_raw").mkdir(parents=True, exist_ok=True)
    (OUT / "mlp_dl").mkdir(parents=True, exist_ok=True)
    _mlp_subprocess(OUT / "mlp_raw", OUT / "teacher_data.npz")
    _write_dl_episodes(episodes, OUT / "teacher_data_dl.npz")
    _mlp_subprocess(OUT / "mlp_dl", OUT / "teacher_data_dl.npz")
    print("  MLP and MLP-DL trained")
    best_cfg, best_val = None, float("inf")
    val = ("strike_cue", 3.00, 0.64, 2.0)
    for cfg in DL_GRID:
        ens = DelayLineEnsemble([fit_dl(episodes, s, cfg) for s in (11, 29)])
        env = L.build_env(*val, seed=7)
        m = L.rollout(env, 7, ens)
        env.close()
        print(f"  grid {cfg} -> val cue peak={m['peak']:.0f} score={m['score']:.2f}")
        if m["peak"] < best_val:
            best_cfg, best_val = cfg, m["peak"]
    print(f"  selected {best_cfg}")
    json.dump(best_cfg, open(OUT / "dl_cfg.json", "w"))
    for s in SEEDS:
        fit_dl(episodes, s, best_cfg).model.save_npz(OUT / f"dl_s{s}.npz")
    print("  ESN-DL saved")


def _dl_ensemble(path_glob="dl_s*.npz") -> DelayLineEnsemble:
    return DelayLineEnsemble(
        [DelayLineESN(DirectESNController.from_npz(p)) for p in sorted(OUT.glob(path_glob))])


def stage_dagger() -> None:
    print("== dagger: relabel ESN-DL-visited states ==")
    episodes = _load_episodes()
    ens = _dl_ensemble()
    for entry in DATA_GRID + HELDOUT:
        env = L.build_env(*entry, seed=7, noise=L.DATA_NOISE)
        m, ep = L.rollout(env, 7, policy=ens, teacher=_expert_for(entry), collect=True)
        env.close()
        episodes.append(dict(obs=list(ep["obs"]), actions=ep["actions"],
                             weights=ep["weights"]))
        print(f"  {entry}: {L._fmt(m)}")
    np.savez_compressed(OUT / "teacher_data.npz", episodes=np.asarray(episodes, dtype=object))
    cfg = json.load(open(OUT / "dl_cfg.json"))
    for s in SEEDS:
        fit_dl(episodes, s, cfg).model.save_npz(OUT / f"dl_s{s}.npz")
    _mlp_subprocess(OUT / "mlp_raw", OUT / "teacher_data.npz")
    _write_dl_episodes(episodes, OUT / "teacher_data_dl.npz")
    _mlp_subprocess(OUT / "mlp_dl", OUT / "teacher_data_dl.npz")
    print("  refit done")


def stage_eval() -> None:
    print("== eval: FW / VMC / MLP / MLP-DL / ESN-DL ==")
    controllers = [("FW", NeutralPolicy()), ("VMC", L._tuned_vmc()),
                   ("MLP", _load_mlp(OUT / "mlp_raw")),
                   ("MLP-DL", _load_mlp(OUT / "mlp_dl", dl=True)),
                   ("ESN-DL", _dl_ensemble())]
    results = {n: [] for n, _ in controllers}
    for entry in EVAL_BOARDS:
        for name, policy in controllers:
            env = L.build_env(*entry, seed=7)
            m = L.rollout(env, 7, policy)
            env.close()
            results[name].append(m)
            print(f"  {entry} {name:7s}: {L._fmt(m)}")
    print("\n== podium ==")
    for name, ms in results.items():
        print(f"  {name:7s} score={np.mean([m['score'] for m in ms]):6.2f} "
              f"peak={np.mean([m['peak'] for m in ms]):6.1f} "
              f"Fint={np.mean([m['Fint'] for m in ms]):6.1f} "
              f"errF={np.mean([m['errF_mm'] for m in ms]):5.1f} "
              f"ok={100*np.mean([m['completed'] for m in ms]):3.0f}%")
    table = {n: {k: float(np.mean([m[k] for m in ms])) for k in
                 ("Fint", "peak", "errF_mm", "score")} for n, ms in results.items()}
    json.dump(table, open(OUT / "eval_table.json", "w"), indent=1)


def main() -> None:
    import argparse
    stage = argparse.ArgumentParser().parse_args() if False else None
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    stages = {"probe": stage_probe, "data": stage_data, "train": stage_train,
              "dagger": stage_dagger, "eval": stage_eval}
    todo = stages.values() if which == "all" else [stages[which]]
    for fn in todo:
        fn()


if __name__ == "__main__":
    main()
