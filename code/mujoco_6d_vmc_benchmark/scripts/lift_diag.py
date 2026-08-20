#!/usr/bin/env python3
"""Diagnose which joints saturate and when during board contact."""
from __future__ import annotations

import os as _os
import numpy as np

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import lift_experiment as L
from extraction_experiment import NeutralPolicy, board_force


def diag(policy_name: str, policy=None, teacher=None):
    env = L.build_env(L.Y_OFF_DEFAULT, L.TILT_DEFAULT, 7)
    env.reset(seed=7, options={"fixture_index": 0})
    limits = np.asarray([87.0] * 4 + [12.0] * 3)
    first_trip = None
    done, step = False, 0
    rows = []
    while not done:
        t = step * 0.04
        f = board_force(env)
        tau = env._last_torque_components["total"][:7] if env._last_torque_components else np.zeros(7)
        at_limit = np.where(np.abs(tau) > 0.98 * limits)[0]
        hand = env.data.xpos[env._hand_id]
        if (f > 5.0 or len(at_limit)) and step % 5 == 0:
            rows.append((t, f, tuple(at_limit + 1), tau.copy(),
                         float(hand[1]), env.applied_action.wbc_scale))
        if len(at_limit) and first_trip is None:
            first_trip = (t, tuple(at_limit + 1), f)
        d = env.diagnostics()
        args = (d["joint_position"], d["joint_velocity"], d["nominal_twist"])
        kw = dict(pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
        if teacher is not None:
            action = np.asarray(teacher.act(*args, **kw, hand_x=float(hand[0]),
                                            hand_y=float(hand[1]), hand_z=float(hand[2]),
                                            contact=f > 2.0, time_s=t), dtype=float)
        else:
            action = np.asarray(policy.act(*args, **kw).bounded_filter_action, dtype=float)
        _, _, done, _, info = env.step(action)
        step += 1
    print(f"### {policy_name}: hard={info['hard_torque_limit']} ok={info['task_success']}")
    if first_trip:
        print(f"  first limit trip t={first_trip[0]:.2f}s joints={first_trip[1]} force={first_trip[2]:.0f}N")
    for t, f, jl, tau, hy, sc in rows[:30]:
        print(f"  t={t:4.2f} F={f:6.1f}N limit_j={jl} tau567=[{tau[4]:+.1f},{tau[5]:+.1f},{tau[6]:+.1f}] "
              f"hand_y={hy:+.3f} scale={sc:.2f}")
    env.close()


diag("FW", policy=NeutralPolicy())
diag("teacher y0.85", teacher=L.LiftTeacher(y_yield=0.85, slow=1.0))
