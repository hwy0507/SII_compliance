"""Check the real scale routing contract including current-tick consumption."""
from types import SimpleNamespace
import unittest
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import feedback_tick_contract_20261013 as module


class FeedbackTickTest(unittest.TestCase):
    def test_current_scale_and_yield_share_tick_without_double_scaling(self):
        original_twist=module.body_twist
        module.body_twist=lambda *a:np.zeros(6)
        try:
            for fix in (False,True):
                e=SimpleNamespace(observation_mode='direct_esn',execution_mode='twist',model=None,_hand_id=0,
                    data=SimpleNamespace(time=0.,qpos=np.zeros(7),qvel=np.zeros(7)),
                    current_predictive_wbc_feedback_scale=1.,_last_policy_wbc_scale=1.,
                    previous_torque=np.zeros(7),previous_joint_velocity_command=np.zeros(7),
                    applied_action=SimpleNamespace(wbc_scale=1.,cartesian_yield_twist=np.zeros(6)))
                e._wbc_command=lambda t:SimpleNamespace(task_twist_world=np.zeros(6),position_error_m=np.zeros(3))
                e._physics_step=lambda t:e._wbc_command(t)
                trace=module.FeedbackTickContract(e,fix);trace.install()
                scales=np.array([.84,.68,.84,1.]);twists=np.arange(24).reshape(4,6)*.001
                for scale,twist in zip(scales,twists):
                    e.current_predictive_wbc_feedback_scale=e._last_policy_wbc_scale
                    e._last_policy_wbc_scale=scale;e.applied_action.cartesian_yield_twist=twist
                    for _ in range(10):e._physics_step(e.data.time);e.data.time+=.004
                arrays={k:np.array([r[k] for r in trace.rows]) for k in trace.rows[0]}
                result=module.audit_scale_trace(arrays,dict(wbc_scale=scales,yield_twist=twists),fix)
                self.assertEqual(result['measured_scale_lag_policy_ticks'],0 if fix else 1)
        finally:module.body_twist=original_twist


if __name__=='__main__':unittest.main()
