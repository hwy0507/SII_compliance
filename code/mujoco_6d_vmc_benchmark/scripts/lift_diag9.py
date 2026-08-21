#!/usr/bin/env python3
"""Sudden-strike sweep: hard fast plank at PAYLOAD height, single timing
cluster t0=3.0.  Objective: FW fails (block flung), teacher passes.
This is the scenario family where anticipation is structurally necessary."""
from __future__ import annotations

import os as _os

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import lift_experiment as L
from extraction_experiment import NeutralPolicy

for v0, force, window in ((2.0, 500, 0.30), (2.0, 800, 0.25), (2.5, 800, 0.20), (2.5, 1200, 0.18)):
    _os.environ["LIFT_PLANK_FORCE"] = str(force)
    _os.environ["LIFT_PLANK_WINDOW"] = str(window)
    _os.environ["LIFT_PLANK_KV"] = "60"
    for h in (0.62, 0.64):
        env = L.build_env("plank_payload", 3.00, h, v0, seed=7)
        fw = L.rollout(env, 7, NeutralPolicy())
        env.close()
        env = L.build_env("plank_payload", 3.00, h, v0, seed=7)
        tea = L.rollout(env, 7, teacher=L.LiftTeacher(y_yield=0.85, pre_t=2.70))
        env.close()
        tag = f"v0={v0} F={force} w={window} h={h}"
        print(f"{tag:34s} FW : done={int(fw['completed'])} held<={fw['held_until_s']:4.2f} "
              f"peak={fw['peak']:4.0f}N Fint={fw['Fint']:5.0f} fin_z={fw['final_obj_z']:6.2f}")
        print(f"{'':34s} TEA: done={int(tea['completed'])} held<={tea['held_until_s']:4.2f} "
              f"peak={tea['peak']:4.0f}N Fint={tea['Fint']:5.0f} fin_z={tea['final_obj_z']:6.2f}")
