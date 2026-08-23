#!/usr/bin/env python3
"""Head-on blocking board sweep: flat ceiling (0-15 deg) directly above the
lift column.  The arm slams into the underside and must detour AROUND it.
Sweep: tilt, z_off (height above grasp), board width hy."""
from __future__ import annotations

import os as _os

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import numpy as np

import lift_experiment as L
from extraction_experiment import NeutralPolicy

L.STATIC_HY = 0.06      # wider: the edge is further, real detour needed
L.STATIC_Z = 0.02       # lower: underside firmly blocks the rising hand
for tilt in (8.0, 10.0, 12.0):
    _os.environ["LIFT_BOARD_TILT_DEG"] = str(tilt)
    for y_off in (0.0, 0.02, 0.05):
        env = L.build_env("static", y_off, tilt, seed=7)
        fw = L.rollout(env, 7, NeutralPolicy())
        env.close()
        env = L.build_env("static", y_off, tilt, seed=7)
        tea = L.rollout(env, 7, teacher=L.LiftTeacher(y_yield=0.85, pre_t=2.7))
        env.close()
        tag = f"tilt={tilt:3.0f} y={y_off:.2f}"
        print(f"{tag:22s} FW : ok={int(fw['completed'])} held<={fw['held_until_s']:4.2f} "
              f"Fint={fw['Fint']:5.0f} peak={fw['peak']:4.0f} dodge={fw['dodge_mm']:4.0f}mm "
              f"errF={fw['errF_mm']:5.1f}mm")
        print(f"{'':22s} TEA: ok={int(tea['completed'])} held<={tea['held_until_s']:4.2f} "
              f"Fint={tea['Fint']:5.0f} peak={tea['peak']:4.0f} dodge={tea['dodge_mm']:4.0f}mm "
              f"errF={tea['errF_mm']:5.1f}mm")
