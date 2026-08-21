#!/usr/bin/env python3
"""Corridor revalidation: does the restored geometry block FW / pass teacher?"""
from __future__ import annotations

import os as _os

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import lift_experiment as L
from extraction_experiment import NeutralPolicy

import itertools
grid = []
for yo in (0.03, 0.05, 0.07):
    for tl in (22.0, 25.0):
        grid.append(("static", yo, tl))
for b in grid:
    env = L.build_env(*b, seed=7)
    fw = L.rollout(env, 7, NeutralPolicy())
    env.close()
    env = L.build_env(*b, seed=7)
    tea = L.rollout(env, 7, teacher=L.LiftTeacher(y_yield=0.85, pre_t=2.85))
    env.close()
    print(f"{b} FW : done={int(fw['completed'])} held<={fw['held_until_s']:.2f} "
          f"Fint={fw['Fint']:.0f} peak={fw['peak']:.0f}")
    print(f"{b} TEA: done={int(tea['completed'])} held<={tea['held_until_s']:.2f} "
          f"Fint={tea['Fint']:.0f} peak={tea['peak']:.0f} dodge={tea['dodge_mm']:.0f}mm")
print("CHECK-DONE")
