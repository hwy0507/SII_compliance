from copy import deepcopy
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from goal_tracking_pilot_20261016 import validate_pair,prepare,require_predecessor_complete,verify_pilot_preflight
from goal_payload_occupancy_reward_20261016 import CONFIG
from goal_tracking_reward_20261016 import PARAMETER_CONFIG
from rl_goal_stage_20261016 import read,write,digest,manifest,interaction_budget,verify_inputs
from screen_goal_rl_convergence_20261016 import collect
from report_goal_tracking_pair_20261016 import validate_protocol
import test_goal_stage_continuation_20261016 as fixtures
import test_goal_reward_signal_20261016 as reward_fixtures


class OccupancyPilotTests(unittest.TestCase):
    def pair(self):
        jobs=[dict(name=name,output='/'+name,unit=name,checkpoint=None,inherited_steps=0,limit=44000,
            controller='impedance',reward='metric',reward_variant='payload_shaping',hp='parameter_balanced',
            seed=5,credit_migration=False) for name in ('impedance_control','impedance_occupancy')]
        jobs[1]['payload_occupancy_guidance']=dict(CONFIG)
        return dict(experiment_kind='fresh_parameter_occupancy_pilot',jobs=jobs,
            maximum_new_interactions=88000,new_interactions_per_family=44000,optimizer_schedule_steps=1000000)

    def test_one_cycle_pair_cannot_mix_reward_model_seed_or_budget(self):
        reg=self.pair();validate_pair(reg);self.assertEqual(interaction_budget(reg),44000)
        for fields in ({'seed':6},{'checkpoint':'/old/cp'},{'limit':11000},{'controller':'admittance'},
                       {'tracking_guidance':PARAMETER_CONFIG},{'payload_occupancy_guidance':dict(CONFIG,weight=40.)}):
            bad=deepcopy(reg);bad['jobs'][1].update(fields)
            with self.assertRaises(AssertionError):validate_pair(bad)
        bad=deepcopy(reg);bad['jobs'][0]['payload_occupancy_guidance']=CONFIG
        with self.assertRaises(AssertionError):validate_pair(bad)

    def test_preparation_freezes_standalone_dependencies_and_waits_for_four_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,reg,state=fixtures.StageContinuationTests().fixture(base)
            for name in ('rl_recovery_control_20261016.py',):
                shutil.copy2(Path(__file__).resolve().parents[1]/'tools'/name,old/'source/tools'/name)
            reg['source_manifest']=manifest(old/'source');reg['training_convergence']={'window_episodes':32}
            write(old/'REGISTRATION.json',reg)
            state['registration_sha256']=digest(old/'REGISTRATION.json')
            state.update(status='running',active={'job':'admittance'});write(old/'execution.json',state)
            cp=old/'impedance/checkpoint_0011000';spec=read(cp.parent/'PROTOCOL.json')
            spec.update(reward=dict(mode='metric',error_weight=4),reward_variant='payload_shaping')
            write(cp.parent/'PROTOCOL.json',spec)
            receipt=base/'reward.json';write(receipt,dict(protocol_snapshot=spec,protocol_sha256=digest(cp.parent/'PROTOCOL.json'),
                execution_snapshot=dict(rows=[dict(ended_utc='closed',episode=7,step_after=11000)])))
            before=manifest(old);new=base/'pair'
            registered=prepare(old,new,cp,receipt,'impedance',True)
            self.assertEqual(manifest(old),before);validate_pair(registered);verify_inputs(registered)
            self.assertEqual(registered['parameter_manifest'],reg['parameter_manifest'])
            self.assertEqual(registered['source_manifest']['tools/baseline_repair_worker_20261008.py'],
                             reg['source_manifest']['tools/baseline_repair_worker_20261008.py'])
            check=subprocess.run([sys.executable,'-I','-c',
                'import sys;sys.path.insert(0,sys.argv[1]);from goal_tracking_pilot_20261016 import validate_pair;from rl_goal_stage_20261016 import read;validate_pair(read(sys.argv[2]))',
                str(new/'source/tools'),str(new/'REGISTRATION.json')],cwd=base,env=dict(os.environ,PYTHONPATH=''),
                capture_output=True,text=True,timeout=20)
            self.assertEqual(check.returncode,0,check.stderr)
            with self.assertRaises(AssertionError):require_predecessor_complete(registered)
            with self.assertRaises(FileNotFoundError):verify_pilot_preflight(registered)
            self.assertFalse((new/'LAUNCH.json').exists());self.assertFalse((new/'execution.json').exists())
            result=collect(new)
            self.assertFalse(result['four_family_scope']);self.assertFalse(result['all_training_candidates'])

    def test_reports_reject_missing_occupancy_and_decompose_its_actual_terms(self):
        job=self.pair()['jobs'][1]
        spec=dict(goal_registration_sha256='h',seed=5,controller='impedance',reward_variant='payload_shaping',
            hyperparameter_id=job['hp'],segment_limit=44000,maximum_steps=1000000,warmup_steps=5000,utd=1,
            agent_config=dict(n_step=25),reward=dict(mode='metric'))
        with self.assertRaises(ValueError):validate_protocol(spec,job,'h')
        spec['payload_occupancy_guidance']=CONFIG;validate_protocol(spec,job,'h')
        row,logs,original=reward_fixtures.RewardSignalTests().fixture()
        logs[0]['terms']['payload_occupancy']=-.003
        logs[1]['terms']['payload_occupancy_failure_continuation']=-.02
        logs[0]['terms']['final_reward']-=.003;logs[1]['terms']['final_reward']-=.02
        row['return_value']-=.023
        from diagnose_goal_reward_signal_20261016 import decompose
        result=decompose(row,logs,original)
        self.assertAlmostEqual(result['undiscounted_components']['payload_occupancy'],-.003)
        self.assertAlmostEqual(result['undiscounted_components']['payload_occupancy_failure_continuation'],-.02)


if __name__=='__main__':unittest.main()
