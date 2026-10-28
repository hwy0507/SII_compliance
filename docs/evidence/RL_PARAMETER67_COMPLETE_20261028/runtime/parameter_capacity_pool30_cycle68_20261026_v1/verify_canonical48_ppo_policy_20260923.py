"""Offline single-observation prediction parity, no simulation or new training."""
import argparse
import os
import platform
from pathlib import Path
import sys
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import numpy as np
import torch
import stable_baselines3
from canonical48_ppo_policy_20260923 import Canonical48PPO
from canonical48_rl_env_20260923 import save_json,sha


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pilot',type=Path,default=ROOT/'outputs/canonical48_ppo_pilot_20260923_r1')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
    policy=Canonical48PPO(args.pilot/'ppo_final.zip',args.pilot/'vecnormalize_train_only.pkl')
    before=(policy.normalizer.obs_rms.mean.copy(),policy.normalizer.obs_rms.var.copy(),policy.normalizer.obs_rms.count)
    comparisons={}
    try:
        # Train fixture only. Compare CPU deployment against actions already
        # emitted by frozen GPU evaluation, avoiding same-call self comparison.
        for name,path in [('train_ppo',args.pilot/'eval/train/ppo/episode_00000/actor_trace.npz')]:
            with np.load(path,allow_pickle=False) as archive:
                observations,expected=archive['observation'],archive['action']
                actions=np.array([policy.act(obs) for obs in observations])
            error=np.abs(actions-expected)
            comparisons[name]=dict(samples=len(actions),max_abs_error=float(error.max()),
                within_atol_1e6=bool(np.allclose(actions,expected,atol=1e-6,rtol=0)),
                trace_sha256=sha(path))
            np.savez_compressed(args.output/(name+'_prediction.npz'),action=actions,expected=expected)
        # Stress observation normalization clipping independently of task data.
        probes=np.vstack((np.zeros(48),np.full(48,1e8),np.full(48,-1e8)))
        normalized=policy.normalizer.normalize_obs(probes.astype(np.float32))
        clipping=dict(clip_obs=policy.normalizer.clip_obs,epsilon=policy.normalizer.epsilon,
            maximum_normalized_abs=float(np.max(np.abs(normalized))),
            positive_probe_clipped=bool(np.all(normalized[1]==policy.normalizer.clip_obs)),
            negative_probe_clipped=bool(np.all(normalized[2]==-policy.normalizer.clip_obs)))
        frozen=bool(np.array_equal(before[0],policy.normalizer.obs_rms.mean)
            and np.array_equal(before[1],policy.normalizer.obs_rms.var)
            and before[2]==policy.normalizer.obs_rms.count)
        report=dict(comparisons=comparisons,normalization_frozen=frozen,clipping=clipping,
            runtime=dict(python=sys.version,machine=platform.machine(),numpy=np.__version__,
                torch=torch.__version__,stable_baselines3=stable_baselines3.__version__),
            checkpoint_sha256=sha(args.pilot/'ppo_final.zip'),
            normalizer_sha256=sha(args.pilot/'vecnormalize_train_only.pkl'),
            inference='SB3 CPU with float32 actor boundary; saved mean/var/epsilon/clip; Tanh actor and SB3 Box action clipping',
            actor_observation_dimension=48,action_dimension=7,actor_privileged_fields=[],
            server_physics_not_run=True,policy_source_sha256=sha(ROOT/'scripts/canonical48_ppo_policy_20260923.py'))
        report['passed']=all(v['within_atol_1e6'] for v in comparisons.values()) and frozen
        save_json(args.output/'PARITY.json',report)
        if not report['passed']:raise AssertionError('PPO inference parity failed')
        print(report)
    finally:policy.close()


if __name__=='__main__':main()
