from pathlib import Path
import copy
import hashlib
import json
import sys
import tempfile
import unittest
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from continue_published_completed_stage_20261025 import prepare_state,verify_boundary
from validate_published_finite_check_20261025 import digest
from train_published_compliance_20261025 import validate_resume_protocol


class CompletedStageTests(unittest.TestCase):
    def test_scientific_lr_preparation_preserves_every_other_state(self):
        original=dict(cycles=[dict(cycle=7)],replay=dict(observations=np.ones((4,49),np.float32)),
            learner=dict(actor_optimizer=dict(param_groups=[dict(lr=3e-4)],state={0:dict(exp_avg=torch.ones(4),step=torch.tensor(4))}),
                         agent={'weight':torch.ones(3)},rng=np.random.default_rng(4).bit_generator.state))
        before=digest(original)
        same,receipt=prepare_state(original,None)
        self.assertEqual(digest(same),before)
        changed,receipt=prepare_state(original,.1)
        self.assertAlmostEqual(changed['learner']['actor_optimizer']['param_groups'][0]['lr'],3e-5)
        self.assertEqual(changed['cycles'],[])
        self.assertTrue(receipt['all_other_state_exact'])
        self.assertEqual(digest(original),before)
        changed['learner']['agent']['weight'].zero_()
        self.assertEqual(digest(original),before)
        with self.assertRaises(ValueError):prepare_state(original,.5)
        bad=copy.deepcopy(original);bad['learner']['actor_optimizer']['param_groups'][0]['lr']=3e-5
        with self.assertRaises(ValueError):prepare_state(bad,.1)

    def test_boundary_rejects_partial_wrong_cycle_and_failed_receipt(self):
        state=dict(boundary='complete_condition_cycle',controller='direct',protocol_sha256='p',cycle=7,steps=100)
        finished=dict(steps=100,status='stopped_at_complete_cycle')
        verify_boundary(state,finished,'direct','p',7,'reviewed_hash')
        for key,value in [('boundary','partial'),('cycle',6),('steps',99),('protocol_sha256','other')]:
            with self.assertRaises(ValueError):verify_boundary(dict(state,**{key:value}),finished,'direct','p',7,'reviewed_hash')
        with self.assertRaises(ValueError):verify_boundary(state,dict(finished,status='failure'),'direct','p',7,'reviewed_hash')

    def test_protocol_allows_only_explicit_stage_metadata_and_preserves_objective(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'runtime';root.mkdir()
            for name in ['PARAMETER_HASHES.json','ROBOT_ASSET_HASHES.json','CHEQ_HASHES.json','SOURCE_HASHES.json']:
                (root/name).write_text('{}')
            old=dict(runtime=str(root),reward={'success':25},gamma=.9995,performance_amendment=dict(kind='device_replay_cache_only',replay_device_cache=True))
            parent=Path(directory)/'parent.json';parent.write_text(json.dumps(old));h=hashlib.sha256(parent.read_bytes()).hexdigest()
            stage=dict(kind='reviewed_complete_stage',new_cycles=2,parent_cycle=7,actor_learning_rate_factor=.1,review={'sha256':'reviewhash'})
            new=dict(old,completed_stage_continuation=stage,resume_parent_registration=dict(path=str(parent),sha256=h),
                     performance_amendment=dict(kind='frozen_target_gradients_only',replay_device_cache=True,freeze_target_gradients=True,algorithm_scope=['cheq']))
            validate_resume_protocol(h,new,'new')
            for key,value in [('gamma',.99),('reward',{'success':50})]:
                with self.assertRaisesRegex(ValueError,'training contract'):validate_resume_protocol(h,dict(new,**{key:value}),'new')
            for key,value in [('actor_learning_rate_factor',.5),('new_cycles',0),('review',{}),('kind','other')]:
                bad=dict(new,completed_stage_continuation=dict(stage,**{key:value}))
                with self.assertRaisesRegex(ValueError,'completed-stage'):validate_resume_protocol(h,bad,'new')


if __name__=='__main__':unittest.main()
