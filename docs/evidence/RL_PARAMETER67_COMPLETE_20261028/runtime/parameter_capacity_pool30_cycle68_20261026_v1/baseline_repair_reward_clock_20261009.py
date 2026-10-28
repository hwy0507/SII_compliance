"""Executed torque smoothness at the registered 250 Hz actuator update rate.

MuJoCo holds each motor torque through 80 formal physical substeps. Dividing
the jump by the integration step spuriously scales this cost by 80. Accumulate
all recorded changes, but use the actuator's actual 4 ms update interval.
This is a servo-command smoothness measure, not a continuous torque derivative.
"""
import math
import numpy as np

SERVO_DT = .004
TIME_BASE = 'executed_motor_torque_changes_at_250Hz_not_physics_dt'


def slew_cost_rows(torque, rates, previous=None, servo_dt=SERVO_DT, horizon=55.):
    torque = np.asarray(torque, dtype=float); rates = np.asarray(rates, dtype=float)
    assert torque.ndim == 2 and torque.shape[1] == 7 and len(torque)
    assert rates.shape == (7,) and np.all(rates > 0) and servo_dt > 0 and horizon > 0
    assert np.isfinite(torque).all() and np.isfinite(rates).all()
    prev = torque[0] if previous is None else np.asarray(previous, dtype=float)
    assert prev.shape == (7,) and np.isfinite(prev).all()
    changes = np.diff(np.vstack((prev, torque)), axis=0)
    ratio = changes/(servo_dt*rates)
    # Logged actuator values are float32. Allow their rounding, not a larger
    # control-rate jump. A violation must stop the audit rather than be clipped.
    assert np.max(abs(ratio)) <= 1.+1e-5, 'Recorded motor change exceeds servo slew bound'
    return np.sum(ratio**2, axis=1)*servo_dt/horizon


def remaining_slew_bound(elapsed, horizon=55., servo_dt=SERVO_DT):
    remaining = max(0., horizon-float(elapsed))
    # A partial remaining servo interval can still contain one update.
    updates = max(0, math.ceil(remaining/servo_dt-1e-8))
    return 7*updates*servo_dt/horizon
