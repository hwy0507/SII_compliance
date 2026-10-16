from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from goal_tracking_pilot_20261016 import validate_pair, require_predecessor_complete, verify_pilot_preflight
from goal_tracking_reward_20261016 import CONFIG, PARAMETER_CONFIG
from rl_goal_stage_20261016 import write, digest
import test_goal_stage_continuation_20261016 as fixtures


class TrackingPilotTests(unittest.TestCase):
    def test_impedance_pair_is_fresh_and_only_extra_tracking_cost_differs(self):
        reg=self.pair();reg['experiment_kind']='fresh_parameter_tracking_pilot'
        for job in reg['jobs']:
            job.update(name=job['name'].replace('direct','impedance'),controller='impedance',
                       reward='metric',reward_variant='payload_shaping',hp='parameter_balanced')
        reg['jobs'][1]['tracking_guidance']=dict(PARAMETER_CONFIG)
        validate_pair(reg)
        for key,value in (('seed',6),('checkpoint','/old/model'),('hp','direct_explore'),('controller','admittance')):
            bad=deepcopy(reg);bad['jobs'][1][key]=value
            with self.assertRaises(AssertionError):validate_pair(bad)
        bad=deepcopy(reg);bad['jobs'][1]['tracking_guidance']=CONFIG
        with self.assertRaises(AssertionError):validate_pair(bad)

    def pair(self):
        jobs = [dict(name=name,output='/'+name,unit=name,checkpoint=None,inherited_steps=0,
            limit=11000,controller=None,reward='office_task',reward_variant='task_safety',
            hp='direct_explore',seed=5,credit_migration=False) for name in ('direct_control','direct_tracking')]
        jobs[1]['tracking_guidance'] = dict(CONFIG)
        return dict(experiment_kind='fresh_direct_tracking_pilot',jobs=jobs,maximum_new_interactions=22000,
                    new_interactions_per_family=11000,optimizer_schedule_steps=1000000)

    def test_only_reward_differs_and_both_arms_are_fresh(self):
        reg = self.pair(); validate_pair(reg)
        for key, value in (('seed',6),('checkpoint','/old/model'),('limit',22000),('controller','vmc')):
            bad = deepcopy(reg); bad['jobs'][1][key] = value
            with self.assertRaises(AssertionError): validate_pair(bad)
        bad = deepcopy(reg); bad['jobs'][0]['tracking_guidance'] = CONFIG
        with self.assertRaises(AssertionError): validate_pair(bad)

    def test_launch_gate_requires_all_four_predecessor_checkpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous, _, state = fixtures.StageContinuationTests().fixture(Path(tmp))
            reg = self.pair()
            reg['pilot_predecessor'] = dict(root=str(previous),registration_sha256=digest(previous/'REGISTRATION.json'))
            self.assertEqual(len(require_predecessor_complete(reg)),4)
            write(previous/'execution.json',dict(state,status='running',active={'job':'vmc'}))
            with self.assertRaises(AssertionError): require_predecessor_complete(reg)
            state['jobs'][0]['returncode'] = 1
            write(previous/'execution.json',state)
            with self.assertRaises(AssertionError): require_predecessor_complete(reg)

    def test_missing_arm_or_changed_guidance_cannot_pass_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); reg = self.pair(); reg['run_root'] = str(root)
            reg['pilot_probe'] = dict(checkpoint='/cp',hashes={'x':'h'},reward_receipt_sha256='r')
            write(root/'REGISTRATION.json',reg)
            result = dict(status='passed',registration_sha256=digest(root/'REGISTRATION.json'),
                initial_networks_equal=True,checkpoint_hashes_unchanged=True,gradient_updates=2,
                model_saved=False,simulation=False,source_checkpoint='/cp',source_checkpoint_hashes={'x':'h'},
                reward_receipt_sha256='r',arms={j['name']:dict(fresh_before=True,n_step=25,finite_update=True,
                    terminal_window_checked=True,guidance=j.get('tracking_guidance')) for j in reg['jobs']})
            write(root/'CREDIT_PREFLIGHT.json',result); verify_pilot_preflight(reg)
            result['arms']['direct_tracking']['guidance'] = None
            write(root/'CREDIT_PREFLIGHT.json',result)
            with self.assertRaises(AssertionError): verify_pilot_preflight(reg)
            del result['arms']['direct_tracking']
            write(root/'CREDIT_PREFLIGHT.json',result)
            with self.assertRaises(AssertionError): verify_pilot_preflight(reg)


if __name__ == '__main__': unittest.main()
