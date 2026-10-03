"""Negative controls for independent actor replay; zero actual training/physics."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import numpy as np
from research72_rl_actor_replay_20261004 import replay, run_replay, sha


class Agent:
    def __init__(self, dimension=7, mutation=None):
        self.dimension=dimension; self.mutation=mutation
        self.observation_normalizer=SimpleNamespace(obs_rms=SimpleNamespace(mean=np.zeros(48),var=np.ones(48),count=2.))
        self.reward_normalizer=SimpleNamespace(G_rms=SimpleNamespace(mean=np.zeros(1),var=np.ones(1),count=2.),G=np.zeros(1),G_r_max=0.)
    def diagnostics(self):return {'updates': 0}
    def sample_action(self, observation, training):
        assert training is False
        if self.mutation == 'norm':self.observation_normalizer.obs_rms.mean[0]+=1
        if self.mutation == 'input':observation[0]=0
        return observation[:self.dimension].copy()


class Tests(unittest.TestCase):
    def test_both_action_dimensions(self):
        obs=np.full((3,48),.2)
        for dim in (5,7):self.assertEqual(replay(Agent(dim),obs,obs[:,:dim],dim)['samples'],3)

    def test_wrong_action_and_shape_rejected(self):
        obs=np.full((3,48),.2)
        for actions in (np.zeros((3,7)),np.zeros((2,7))):
            with self.assertRaises(AssertionError):replay(Agent(),obs,actions,7)

    def test_mutation_rejected(self):
        obs=np.full((3,48),.2)
        with self.assertRaises(AssertionError):replay(Agent(mutation='norm'),obs,obs[:,:7],7)
        with self.assertRaises(ValueError):replay(Agent(mutation='input'),obs,obs[:,:7],7)

    def test_short_failure_included_and_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);obs=np.full((3,48),.2);actions=obs[:,:7]
            np.savez(root/'rollout.npz',observation=obs,applied_action=actions)
            np.savez(root/'baseline_policy.npz',observation=obs,action=actions,raw_action=actions)
            manifest={'controller':None,'checkpoint':'synthetic-only'}
            for name,value in [('execution.json',{'status':'complete'}),('ADAPTED_RL_CHECKPOINT.json',manifest),
                ('AUDIT.json',dict(adapted_rl=True,normalization_unchanged=True,trace_sha256=sha(root/'rollout.npz'),
                    task_success=False,strict_success=False,full_horizon=False))]:
                (root/name).write_text(json.dumps(value))
            row=run_replay(Agent(),root,manifest,7)
            self.assertFalse(row['full_horizon']);self.assertFalse(row['strict_success'])
            # Link an independent receipt into publication without reading any
            # condition manifest. Then reject changed normalization evidence.
            from research72_comparison_report_20261003 import rl_replay_coverage
            manifest['hashes']={'synthetic':'not-a-real-model'}
            manifest_path=root/'manifest.json';manifest_path.write_text(json.dumps(manifest))
            source=Path(__file__).parent
            receipt=dict(status='complete',physics_steps=0,training_updates=0,condition_manifests_read=False,
                source_sha256=sha(source/'research72_rl_actor_replay_20261004.py'),
                checkpoint_helper_sha256=sha(source/'research72_checkpoint_20261003.py'),
                parameter_source_sha256={},planned_runs=[str(root.resolve())],rows=[row],
                checkpoint_manifest_sha256=sha(manifest_path),checkpoint_hashes=manifest['hashes'])
            receipt_path=root/'receipt.json';receipt_path.write_text(json.dumps(receipt))
            candidates=[dict(name='rl',adapted_rl=dict(manifest=str(manifest_path),manifest_sha256=sha(manifest_path)))]
            physical=[dict(candidate='rl',condition_id='synthetic',run=str(root),metrics=dict(
                trace_sha256=sha(root/'rollout.npz'),task_success=False,strict_success=False,full_horizon=False))]
            self.assertEqual(rl_replay_coverage(candidates,physical,[receipt_path])['independently_replayed'],1)
            receipt['rows'][0]['normalization_unchanged']=False
            receipt_path.write_text(json.dumps(receipt))
            with self.assertRaises(AssertionError):rl_replay_coverage(candidates,physical,[receipt_path])
            np.savez(root/'rollout.npz',observation=obs,applied_action=np.zeros((3,7)))
            with self.assertRaises(AssertionError):run_replay(Agent(),root,manifest,7)


if __name__=='__main__':unittest.main()
