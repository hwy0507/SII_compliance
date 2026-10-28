"""Policy-independent interpolation of bounded 25Hz commands at250Hz.

No new cutoff/gain: the transition spans exactly one existing policy period.
Raw policy and the existing action filter remain unchanged and are logged.
"""
from dataclasses import replace
import numpy as np
from wbc_velocity_residual_core import FilteredVelocityResidualAction
from run_benchmark import CONTROL_DT
from audited_velocity_env import RL_DT


class ServoActionBridge:
    def __init__(self,env):
        assert abs(CONTROL_DT-.004)<1e-12 and abs(RL_DT-.04)<1e-12
        self.env=env;self.original=env._physics_step
        self.start=env.applied_action;self.target=env.applied_action
        self.feedback_only=(getattr(env,'observation_mode',None)=='direct_esn'
                            and getattr(env,'execution_mode',None)=='twist')
        self.start_scale=self.target_scale=float(env.applied_action.wbc_scale)
        self.tick=0;self.rows=[]

    def __call__(self,t):
        env=self.env;n=round(RL_DT/CONTROL_DT)
        if self.tick%n==0:
            self.start=self.target;self.target=env.applied_action
            self.start_scale=self.target_scale
            self.target_scale=float(env._last_policy_wbc_scale if self.feedback_only else self.target.wbc_scale)
        fraction=(self.tick%n+1)/n
        scale=(1-fraction)*self.start_scale+fraction*self.target_scale
        yield_twist=(1-fraction)*self.start.cartesian_yield_twist+fraction*self.target.cartesian_yield_twist
        # direct_esn consumes scale in feedback only; never double-apply it to
        # the composed joint command or read its deliberate neutral scale=1.
        composition_scale=1. if self.feedback_only else scale
        env.applied_action=replace(self.target,wbc_scale=composition_scale,cartesian_yield_twist=yield_twist.copy())
        env.current_predictive_wbc_feedback_scale=scale
        self.rows.append(dict(time_s=float(t),fraction=fraction,wbc_scale=scale,yield_twist=yield_twist.copy(),
            start_scale=self.start_scale,target_scale=self.target_scale,composition_scale=composition_scale,
            start_twist=self.start.cartesian_yield_twist.copy(),target_twist=self.target.cartesian_yield_twist.copy()))
        self.tick+=1
        return self.original(t)
