"""Teacher-only causal readout ablations; no scene, stage or contact inputs.

The original virtual dynamics and common action/actuator limits are unchanged.
Velocity weighting preserves the static compliance; paired input averaging has
unit DC gain and a zero at the 25 Hz controller's Nyquist frequency. Neither is
a closed-loop stability guarantee. Deploy only after physical validation.
"""
import numpy as np
from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics


class StableReadoutTeacher(SixDVirtualDynamics):
    def __init__(self, options=None, velocity_weight=1., pair_average=False):
        super().__init__({} if options is None else options)
        self.velocity_weight = float(velocity_weight)
        if not np.isfinite(self.velocity_weight) or not 0 <= self.velocity_weight <= 1:
            raise ValueError('velocity_weight must be in [0, 1]')
        self.pair_average = bool(pair_average)
        self.previous_wrench = np.zeros(6)
        self.raw_action = np.zeros(7)
        self.effective_wrench = np.zeros(6)

    def reset(self):
        super().reset()
        self.previous_wrench.fill(0.)
        self.raw_action.fill(0.)
        self.effective_wrench.fill(0.)

    def act(self, wrench_world, dt=.04):
        wrench = np.asarray(wrench_world, dtype=float)
        if wrench.shape != (6,) or not np.isfinite(wrench).all() or not 0 < dt <= .04:
            raise ValueError('finite six-dimensional wrench and dt in (0, .04] required')
        self.effective_wrench = ((wrench + self.previous_wrench) * .5
                                 if self.pair_average else wrench.copy())
        self.previous_wrench = wrench.copy()
        self.raw_action = super().act(self.effective_wrench, dt)
        if self.velocity_weight == 1.:
            return self.raw_action.copy()
        residual = self.velocity_weight * self.velocity + self.offset_gain * self.offset
        action = np.zeros(7)
        action[1:] = np.clip(self.R6 @ residual / self.action_limits, -1., 1.)
        action[0] = np.clip(np.linalg.norm(action[1:]) / np.sqrt(6.), 0., 1.)
        return action
