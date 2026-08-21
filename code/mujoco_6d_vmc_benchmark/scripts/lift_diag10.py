#!/usr/bin/env python3
"""Does any reservoir config bridge the delayed cue (peak drop on the cue
board without false positives on the none board)?"""
from __future__ import annotations

import os as _os

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import numpy as np

import lift_experiment as L
from extraction_experiment import UngatedESN, _fit_esn, NeutralPolicy

with np.load(L.OUT / "teacher_data.npz", allow_pickle=True) as archive:
    raw = list(archive["episodes"])
episodes = [dict(obs=list(ep["obs"]), actions=ep["actions"], weights=ep["weights"])
            for ep in raw]

boards = (("strike_cue", 3.00, 0.64, 2.0), ("strike_none", 0.0, 0.0, 0.0))
for cfg in (dict(spectral_radius=0.75),
            dict(time_constant_s=0.5, spectral_radius=0.95, reservoir_size=240),
            dict(time_constant_s=0.3, spectral_radius=0.95, reservoir_size=240)):
    model, _ = _fit_esn(episodes, 11, cfg)
    esn = UngatedESN(model)
    for b in boards:
        env = L.build_env(*b, seed=7)
        m = L.rollout(env, 7, esn)
        env.close()
        print(f"ESN {cfg} {b[0]}: peak={m['peak']:5.0f}N Fint={m['Fint']:5.1f} "
              f"errF={m['errF_mm']:5.1f}mm dodge={m['dodge_mm']:5.0f}mm", flush=True)
env = L.build_env(*boards[0], seed=7)
fw = L.rollout(env, 7, NeutralPolicy())
env.close()
print(f"FW reference cue board: peak={fw['peak']:.0f}N")
env = L.build_env("strike_cue", 3.00, 0.64, 2.0, seed=7)
tea = L.rollout(env, 7, teacher=L.LiftTeacher(y_yield=0.85, pre_t=2.85))
env.close()
print(f"TEA reference cue board: peak={tea['peak']:.0f}N")
print("BRIDGE-CHECK-DONE")
