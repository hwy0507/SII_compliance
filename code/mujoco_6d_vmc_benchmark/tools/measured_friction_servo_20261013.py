"""Common motor-friction feedforward from encoders, with no policy change.

Uses the same friction model and velocity scale as the existing load observer.
Unlike command-based feedforward, a blocked requested motion adds no torque.
This is an experimental low-level servo, not a recovered historical setting.
"""
import numpy as np


def measured_friction(velocity, friction, damping, velocity_scale=.005):
    v = np.asarray(velocity, dtype=float)
    f = np.asarray(friction, dtype=float)
    b = np.asarray(damping, dtype=float)
    if v.shape != (7,) or f.shape != (7,) or b.shape != (7,):
        raise ValueError('Expected seven robot joints')
    if not all(np.isfinite(x).all() for x in (v, f, b)) or np.any(f < 0) or np.any(b < 0):
        raise ValueError('Invalid motor friction inputs')
    if not np.isfinite(velocity_scale) or velocity_scale <= 0:
        raise ValueError('Invalid encoder velocity scale')
    return f * np.tanh(v / velocity_scale) + b * v
