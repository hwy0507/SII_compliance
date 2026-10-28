"""Trace/correct direct-ESN feedback authority timing, without gain changes.

The existing action adapter deliberately neutralizes composition scale to1.
Its feedback authority must consume the current filtered scale at the same
servo tick as that action's Cartesian residual, not the preceding policy tick.
"""
import numpy as np
from run_benchmark import body_twist


class FeedbackTickContract:
    def __init__(self,env,fix=False):
        assert env.observation_mode=='direct_esn' and env.execution_mode=='twist'
        self.env=env;self.fix=fix;self.rows=[];self.in_physics=False
        self.original_physics=env._physics_step;self.original_command=env._wbc_command
        self.pending=None

    def command(self,t):
        env=self.env
        result=self.original_command(t)
        if self.in_physics:
            # Record at actual WBC consumption, not at the filter output.
            assert self.pending is None,'Expected one WBC command per servo step'
            self.pending=dict(time_s=float(env.data.time),
                current_filtered_scale=float(getattr(env,'_last_policy_wbc_scale',1.)),
                consumed_feedback_scale=float(env.current_predictive_wbc_feedback_scale),
                composition_scale=float(env.applied_action.wbc_scale),
                yield_twist=env.applied_action.cartesian_yield_twist.copy(),
                nominal_twist=result.task_twist_world.copy(),
                measured_twist=body_twist(env.model,env.data,env._hand_id),
                qpos=env.data.qpos[:7].copy(),qvel=env.data.qvel[:7].copy(),
                position_error=result.position_error_m.copy())
        return result

    def physics(self,t):
        env=self.env
        if self.fix:
            env.current_predictive_wbc_feedback_scale=float(env._last_policy_wbc_scale)
        self.in_physics=True
        try:
            result=self.original_physics(t)
            assert self.pending is not None
            self.pending.update(applied_torque=env.previous_torque.copy(),
                joint_velocity_command=env.previous_joint_velocity_command.copy())
            self.rows.append(self.pending);self.pending=None
            return result
        finally:self.in_physics=False

    def install(self):
        self.env._wbc_command=self.command;self.env._physics_step=self.physics


def audit_scale_trace(rows,chain,fix):
    assert len(rows['time_s'])==10*len(chain['wbc_scale'])
    expected=np.repeat(chain['wbc_scale'],10)
    np.testing.assert_array_equal(rows['current_filtered_scale'],expected)
    expected_consumed=expected if fix else np.repeat(np.r_[1.,chain['wbc_scale'][:-1]],10)
    np.testing.assert_array_equal(rows['consumed_feedback_scale'],expected_consumed)
    np.testing.assert_array_equal(rows['composition_scale'],np.ones(len(expected)))
    np.testing.assert_array_equal(rows['yield_twist'],np.repeat(chain['yield_twist'],10,axis=0))
    return dict(same_tick_scale=bool(fix),composition_scale_neutral=True,
        measured_scale_lag_policy_ticks=0 if fix else 1,
        wrong_tick_fraction=float(np.mean(rows['consumed_feedback_scale']!=expected)),
        max_current_vs_consumed_scale_error=float(np.max(abs(rows['consumed_feedback_scale']-expected))),
        servo_steps=len(expected))
