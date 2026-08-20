#!/usr/bin/env python3
"""Find board placement where the carried block never clips the board
(z_off / y_off sweep), checking held_until + completed via the pipeline rollout."""
from __future__ import annotations

import os as _os

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import lift_experiment as L
from extraction_experiment import NeutralPolicy


def run(name, *, y=0.85, y_off=0.05, tilt=25.0, pre=2.80):
    env = L.build_env(y_off, tilt, 7)
    if y > 0:
        m = L.rollout(env, 7, teacher=L.LiftTeacher(y_yield=y, pre_t=pre))
    else:
        m = L.rollout(env, 7, NeutralPolicy())
    env.close()
    print(f"{name:24s} {L._fmt(m)}")


_os.environ.pop("LIFT_BOARD_Z_OFF", None)
run("y0.05 z0 FW", y=0.0)
run("y0.05 z0 T", y=0.85)
for z_off in (0.03, 0.05):
    _os.environ["LIFT_BOARD_Z_OFF"] = str(z_off)
    run(f"z_off{z_off} FW", y=0.0)
    run(f"z_off{z_off} T", y=0.85)
_os.environ.pop("LIFT_BOARD_Z_OFF", None)
for y_off in (0.07, 0.09):
    run(f"y_off{y_off} FW", y=0.0, y_off=y_off)
    run(f"y_off{y_off} T", y=0.85, y_off=y_off)
