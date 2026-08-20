#!/usr/bin/env python3
"""1) Action-stream compare ESN vs MLP vs teacher on the default board --
where do they diverge after the dodge release?  2) Teacher viability on
candidate heldout boards."""
from __future__ import annotations

import os as _os
import numpy as np

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import lift_experiment as L
from extraction_experiment import board_force


def stream(name, policy=None, teacher=None):
    env = L.build_env(L.Y_OFF_DEFAULT, L.TILT_DEFAULT, 7)
    env.reset(seed=7, options={"fixture_index": 0})
    if hasattr(policy, "reset"):
        policy.reset()
    rows = []
    done, step = False, 0
    while not done:
        t = step * 0.04
        d = env.diagnostics()
        hand = env.data.xpos[env._hand_id]
        f = board_force(env)
        args = (d["joint_position"], d["joint_velocity"], d["nominal_twist"])
        kw = dict(pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
        if teacher is not None:
            a = np.asarray(teacher.act(*args, **kw, hand_x=float(hand[0]), hand_y=float(hand[1]),
                                       hand_z=float(hand[2]), contact=f > 2.0, time_s=t,
                                       nominal_y=float(d["nominal_position"][1])), dtype=float)
        else:
            a = np.asarray(policy.act(*args, **kw).bounded_filter_action, dtype=float)
        if 4.0 <= t <= 6.0 and step % 10 == 0:
            obj = env.data.xpos[env._target_body_id]
            rows.append((t, a[0], a[2], float(np.linalg.norm(obj - hand)), f))
        _, _, done, _, _ = env.step(a)
        step += 1
    env.close()
    print(f"### {name}")
    for t, s, y, dist, f in rows:
        print(f"  t={t:4.2f} slow={s:+.2f} y_yield={y:+.2f} hand-obj={dist*1000:4.0f}mm F={f:5.1f}N"
              + ("  <-- BLOCK LOST" if dist > 0.2 else ""))


esn, mlp = L._students()
stream("teacher", teacher=L.LiftTeacher(y_yield=0.85, pre_t=2.70))
stream("mlp", policy=mlp)
stream("esn", policy=esn)

print("\n### teacher on candidate heldouts")
for y_off, tilt in ((0.05, 23.0), (0.05, 22.0), (0.06, 23.0), (0.04, 23.0),
                     (0.06, 20.0), (0.04, 20.0), (0.05, 26.0), (0.03, 22.0)):
    env = L.build_env(y_off, tilt, 7)
    m = L.rollout(env, 7, teacher=L.LiftTeacher(y_yield=0.85, pre_t=2.70))
    env.close()
    print(f"  ({y_off},{tilt}): {L._fmt(m)}")
