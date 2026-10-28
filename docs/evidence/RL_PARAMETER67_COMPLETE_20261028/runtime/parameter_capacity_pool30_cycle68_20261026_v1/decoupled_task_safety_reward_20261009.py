"""Proposed train-only safety cost, separate from original Task terminal reward."""
from audit_decoupled_task_safety_reward_20261009 import safety_potential,SAFETY_WEIGHT


class TaskSafetyPenalty:
    def __init__(self):
        self.peak=0.;self.ended=False

    def __call__(self,interval_peak_m,*,terminated,elapsed_s,horizon_s=55.):
        assert not self.ended and 0<elapsed_s<=horizon_s+1e-6
        # Validate even a value below the previous peak, including NaN.
        safety_potential(interval_peak_m)
        next_peak=max(self.peak,interval_peak_m)
        incremental=SAFETY_WEIGHT*(safety_potential(next_peak)-safety_potential(self.peak))
        continuation=(SAFETY_WEIGHT*(1.-safety_potential(next_peak))
                      if terminated and elapsed_s<horizon_s-1e-7 else 0.)
        self.peak=next_peak;self.ended=terminated
        return incremental+continuation,dict(external_peak_m=next_peak,
            safety_peak_cost=incremental,safety_failure_continuation=continuation)
