"""Loss-only migration, same-start pairing and predecessor dispatch barriers."""
from copy import deepcopy
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from goal_actor_regularization_20261016 import check_actor_regularization_migration, make_actor_regularized_adapter
from goal_actor_regularization_pilot_20261016 import prepare, validate_pair, require_predecessor_complete
from rl_goal_stage_20261016 import read, write, digest, manifest, launch, run
import test_goal_stage_continuation_20261016 as fixtures


class ActorRegularizationTests(unittest.TestCase):
    def test_only_registered_loss_coefficient_can_change(self):
        saved=dict(n_step=25,actor_bc_alpha=0.,gamma=.9995,seed=3)
        current=dict(saved,actor_bc_alpha=1.)
        check_actor_regularization_migration(saved,current)
        for bad in (dict(current,gamma=.99),dict(current,n_step=1),dict(current,seed=4),
                    dict(current,actor_bc_alpha=2.),dict(current,extra=True)):
            with self.assertRaises(ValueError):check_actor_regularization_migration(saved,bad)
        with self.assertRaises(ValueError):check_actor_regularization_migration(current,current)

    def test_strict_loader_retains_state_and_rejects_wrong_path_or_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cp=root/'source';cp.mkdir()
            cfg=dict(n_step=25,actor_bc_alpha=0.,seed=3)
            write(cp/'official_agent_state.json',dict(config=cfg,moments=[3,7],counter=123))
            base=root/'base.py'
            base.write_text('''from dataclasses import make_dataclass
from types import SimpleNamespace
import json
from pathlib import Path
class OfficialParameterAgent:
    def __init__(self):
        self.config=dict(n_step=25,actor_bc_alpha=0.,seed=3)
        Cfg=make_dataclass('Cfg',[('n_step',int),('actor_bc_alpha',float)])
        self.raw_agent=SimpleNamespace(_cfg=Cfg(25,0.))
    def load(self,path):
        state=json.loads((Path(path)/'official_agent_state.json').read_text())
        assert state['config']==self.config
        self.moments=state['moments'];self.counter=state['counter']
''')
            adapter=make_actor_regularized_adapter(base,cp,manifest(cp));agent=adapter()
            agent.load(cp)
            self.assertEqual(agent.moments,[3,7]);self.assertEqual(agent.counter,123)
            self.assertEqual(agent.config['actor_bc_alpha'],1.)
            self.assertEqual(agent.raw_agent._cfg.actor_bc_alpha,1.)
            wrong=root/'wrong';shutil.copytree(cp,wrong)
            with self.assertRaisesRegex(ValueError,'Unregistered'):agent.load(wrong)
            state=read(cp/'official_agent_state.json');state['counter']=999
            write(cp/'official_agent_state.json',state)
            with self.assertRaisesRegex(ValueError,'changed'):agent.load(cp)
            # Later alpha1 checkpoints take the ordinary strict-load path.
            state.update(config=agent.config,counter=124)
            write(wrong/'official_agent_state.json',state);agent.load(wrong)
            self.assertEqual(agent.counter,124)

    def fixture(self,base):
        old,reg,state=fixtures.StageContinuationTests().fixture(base)
        tools=Path(__file__).resolve().parents[1]/'tools'
        for name in ('rl_recovery_control_20261016.py','goal_compute_backend_20261016.py'):
            shutil.copy2(tools/name,old/'source/tools'/name)
        reg.update(source_manifest=manifest(old/'source'),runtime='/runtime',python=sys.executable,
            dispatch_lock='/unused/lock',minimum_free_disk=50*1024**3,training_convergence={'window':32})
        reg['jobs'][0].update(reward_variant='task_safety',hp='direct_explore')
        write(old/'REGISTRATION.json',reg)
        state['registration_sha256']=digest(old/'REGISTRATION.json');write(old/'execution.json',state)
        for job in reg['jobs']:
            path=Path(job['output'])/'PROTOCOL.json';spec=read(path)
            spec.update(goal_registration_sha256=state['registration_sha256'],
                reward_variant=job['reward_variant'],hyperparameter_id=job['hp'])
            spec['agent_config']['actor_bc_alpha']=0.
            write(path,spec)
        probe=base/'probe';probe.mkdir()
        write(probe/'COMPARISON.json',dict(checkpoint_hashes_unchanged=True,training_treatment_deployed=False,
            arms={str(a):dict(status='passed',discarded_updates=256,actual_actor_bc_alpha=float(a)) for a in (0,1)}))
        return old,probe,old/'direct/checkpoint_0011000'

    def test_preparation_preserves_parent_and_isolated_snapshot_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,probe,cp=self.fixture(base);before=manifest(old)
            reg=prepare(old,cp,probe,base/'pair')
            self.assertEqual(manifest(old),before)
            self.assertEqual(len(require_predecessor_complete(reg)),4)
            self.assertTrue(all(j['checkpoint']==str(cp) and j['limit']==22000 for j in reg['jobs']))
            check=subprocess.run([sys.executable,'-I','-c',
                'import sys;sys.path.insert(0,sys.argv[1]);from rl_goal_stage_20261016 import read,verify_inputs;verify_inputs(read(sys.argv[2]))',
                str(base/'pair/source/tools'),str(base/'pair/REGISTRATION.json')],cwd=base,
                env=dict(os.environ,PYTHONPATH=''),capture_output=True,text=True,timeout=20)
            self.assertEqual(check.returncode,0,check.stderr)
            self.assertFalse((base/'pair/LAUNCH.json').exists())

    def test_pair_parameter_evidence_and_seed_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,probe,cp=self.fixture(base)
            reg=prepare(old,cp,probe,base/'pair')
            for key,value in (('seed',99),('checkpoint','/other'),('actor_bc_alpha',.5)):
                bad=deepcopy(reg);bad['jobs'][1][key]=value
                with self.assertRaises(AssertionError):validate_pair(bad)
            parameter=base/'pair/parameter_bc1/official_parameter_agent.py'
            original=parameter.read_text();parameter.write_text(original+'# changed\n')
            with self.assertRaises(AssertionError):validate_pair(reg)
            parameter.write_text(original)
            write(probe/'COMPARISON.json',{'changed':True})
            with self.assertRaises(AssertionError):validate_pair(reg)

    def test_running_or_wrong_registration_predecessor_cannot_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);old,probe,cp=self.fixture(base)
            state=read(old/'execution.json')
            write(old/'execution.json',dict(state,status='running',active={'job':'vmc'}))
            reg=prepare(old,cp,probe,base/'pair')
            for action in (launch,run):
                with self.assertRaises(AssertionError):action(base/'pair')
            self.assertFalse((base/'pair/LAUNCH.json').exists())
            self.assertFalse((base/'pair/execution.json').exists())
            write(old/'execution.json',dict(state,registration_sha256='wrong'))
            with self.assertRaises(AssertionError):require_predecessor_complete(reg)


if __name__=='__main__':unittest.main()
