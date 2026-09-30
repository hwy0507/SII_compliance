"""Resource-bounded canonical-contract PPO development pilot, never paper evidence."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import queue
import sys
import time
import traceback

os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import numpy as np
import torch
import mujoco
import stable_baselines3 as sb3
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from canonical48_rl_env_20260923 import (
    Canonical48Env, load_fixture_specs, run_episode, resource_check, save_json, sha,
    MANIFEST_SHA256)


def zero_parity(spec, menagerie, output):
    """Direct policy injection vs Gym queue; both use restored CURRENT runner."""
    publish = queue.Queue()
    run_episode(spec, menagerie, output/'direct'/'rollout', publish, queue.Queue(),
                duration=6.4, direct_action=lambda _: np.zeros(7))
    status, result, _ = publish.get(timeout=5.)
    if status != 'terminal':
        raise RuntimeError(result)
    env = Canonical48Env(spec, menagerie, output/'gym', duration=6.4)
    try:
        env.reset()
        done = False
        while not done:
            _, _, done, _, _ = env.step(np.zeros(7))
    finally:
        env.close()
    arrays = {}
    for filename in ('actor_trace.npz', 'physics_states.npz', 'contact_samples.npz', 'rollout.npz'):
        with np.load(output/'direct'/filename, allow_pickle=False) as direct, np.load(
                output/'gym'/'episode_00000'/filename, allow_pickle=False) as bridged:
            if direct.files != bridged.files:
                raise AssertionError('Trace key mismatch')
            for key in direct.files:
                a,b = direct[key],bridged[key]
                equal = np.array_equal(a,b, equal_nan=True) if a.dtype.kind in 'fc' else np.array_equal(a,b)
                arrays[f'{filename}:{key}'] = dict(shape=list(a.shape), equal=bool(equal))
                if not equal:
                    raise AssertionError(f'Zero parity failed {filename}:{key}')
    report = dict(passed=True, duration_s=6.4, action_steps=160, arrays=arrays,
        meaning='Gym queue equals direct zero policy in same restored current runner; not historical teacher parity')
    save_json(output/'ZERO_PARITY.json', report)
    return report


class Progress(BaseCallback):
    def __init__(self, output, start, checkpoint_every=0):
        super().__init__()
        self.output, self.start = output, start
        self.checkpoint_every = checkpoint_every
        self.last_checkpoint = 0

    def _save_periodic(self):
        step = self.num_timesteps
        if (not self.checkpoint_every or not step or step % self.checkpoint_every
                or step == self.last_checkpoint):
            return
        folder = self.output/'checkpoints'
        folder.mkdir(exist_ok=True)
        prefix = f'step_{step:08d}'
        self.model.save(folder/(prefix+'.zip'))
        self.model.get_vec_normalize_env().save(folder/(prefix+'_vecnormalize.pkl'))
        save_json(folder/(prefix+'.json'),dict(timesteps=step,updates=self.model._n_updates,
            elapsed_s=time.time()-self.start,selection='fixed train-step interval; no validation selection',
            checkpoint_sha256=sha(folder/(prefix+'.zip')),
            resumability='Policy, optimizer and normalization saved; exact simulator/RNG continuation is not promised'))
        self.last_checkpoint=step

    def _on_rollout_start(self):
        # The previous rollout update is complete at this boundary. Saving
        # here does not freeze an untrained just-collected rollout.
        self._save_periodic()

    def _on_training_end(self):
        self._save_periodic()

    def _on_step(self):
        if self.num_timesteps % 32 == 0:
            state = dict(status='training', pid=os.getpid(), timesteps=self.num_timesteps,
                elapsed_s=time.time()-self.start, resources=resource_check(),
                cuda_allocated_mib=torch.cuda.memory_allocated()/2**20 if torch.cuda.is_available() else 0)
            save_json(self.output/'progress.json', state)
        return True


def evaluate(spec, menagerie, output, model=None, normalizer=None):
    env = Canonical48Env(spec, menagerie, output)
    total = 0.
    try:
        observation, _ = env.reset()
        done = False
        while not done:
            if model is None:
                action = np.zeros(7)
            else:
                normalized = normalizer.normalize_obs(observation[None])[0]
                action, _ = model.predict(normalized, deterministic=True)
            observation, reward, done, _, info = env.step(action)
            total += reward
        return dict(**info['evaluation'], episode_reward=total)
    finally:
        env.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--assets', type=Path, default=ROOT/'outputs/canonical_rl_assets_20260923')
    parser.add_argument('--steps', type=int, default=640)
    parser.add_argument('--seed', type=int, default=20260923)
    parser.add_argument('--device', choices=['cpu','cuda'], default='cuda')
    parser.add_argument('--checkpoint-every', type=int, default=0)
    parser.add_argument('--proof-only', action='store_true')
    args = parser.parse_args()
    if args.checkpoint_every < 0 or args.checkpoint_every % 64:
        raise ValueError('checkpoint interval must be zero or a positive multiple of rollout64')
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    start = time.time()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    allowed = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, allowed[:2])
    if args.device == 'cuda':
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA requested but unavailable; device access must be enabled')
        torch.cuda.set_per_process_memory_fraction(.15)
    specs, intersections = load_fixture_specs(args.assets)
    menagerie = args.assets/'menagerie'
    manifest = dict(status='started', pid=os.getpid(), start_unix=start, argv=sys.argv,
        scope='Canonical48/action7 current runtime, reconstructed manifest push subset; development only',
        historical_teacher_runtime_reproduced=False, publication_ready=False,
        selection='first push row in train/validation by manifest order; no performance selection',
        source_manifest_sha256=MANIFEST_SHA256, split_intersections=intersections,
        source_fixtures=specs, test_episode_data_used=False, office_data_used=False,
        observation_dim=48, action_dim=7, actor_privileged_fields=[], critic_privileged_fields=[],
        reward='causal48 pose/rotation/estimated force and action penalties; phase progress and terminal safety labels reward-only',
        versions=dict(python=sys.version,mujoco=mujoco.__version__,numpy=np.__version__,torch=torch.__version__,sb3=sb3.__version__),
        device=args.device, gpu=torch.cuda.get_device_name() if args.device=='cuda' else None,
        resource_limits=dict(cpu_affinity=sorted(os.sched_getaffinity(0)),threads=1,envs=1,
            max_rss_gib=7.,min_system_available_gib=2.5,gpu_fraction=.15),
        training=dict(timesteps=args.steps,seed=args.seed,n_steps=64,batch_size=64,n_epochs=3,
            gamma=.995,gae_lambda=.95,learning_rate=3e-4,net_arch=[128,128],log_std_init=-2.,
            normalization='VecNormalize fitted online on train only; frozen evaluation',
            checkpoint_selection='fixed final budget; no validation selection',
            periodic_checkpoint_interval=args.checkpoint_every),
        source_hashes={str(p.relative_to(ROOT)):sha(p) for folder in ('scripts','src')
            for p in (ROOT/folder).rglob('*.py')},
        runner_hash=sha(__file__),
        asset_hashes={str(p.relative_to(menagerie)):sha(p) for p in menagerie.rglob('*') if p.is_file()})
    save_json(args.output/'manifest.json',manifest)
    save_json(args.output/'progress.json',dict(status='zero_parity',pid=os.getpid()))
    try:
        zero_parity(specs['train'], menagerie, args.output/'zero_parity')
        if args.proof_only:
            save_json(args.output/'COMPLETE.json',dict(status='proof_passed',elapsed_s=time.time()-start))
            return
        train_env = Canonical48Env(specs['train'],menagerie,args.output/'train')
        normalized = VecNormalize(DummyVecEnv([lambda:train_env]), norm_obs=True,norm_reward=False,clip_obs=12.)
        try:
            model = sb3.PPO('MlpPolicy',normalized,learning_rate=3e-4,n_steps=64,batch_size=64,
                n_epochs=3,gamma=.995,gae_lambda=.95,seed=args.seed,device=args.device,
                policy_kwargs=dict(net_arch=[128,128],log_std_init=-2.),verbose=0)
            model.learn(args.steps,callback=Progress(args.output,start,args.checkpoint_every))
            model.save(args.output/'ppo_final.zip')
            normalized.save(args.output/'vecnormalize_train_only.pkl')
            normalized.training=False
        finally:
            normalized.close()
        # Reload the frozen checkpoint, so evaluation verifies the deliverable.
        model = sb3.PPO.load(args.output/'ppo_final.zip',device=args.device)
        normalization_before = normalized.obs_rms.mean.copy(), normalized.obs_rms.var.copy(), normalized.obs_rms.count
        results = {}
        for split in ('train','validation'):
            for kind in ('zero','ppo'):
                save_json(args.output/'progress.json',dict(status='evaluation',split=split,policy=kind,
                    elapsed_s=time.time()-start,pid=os.getpid(),resources=resource_check()))
                results[f'{split}/{kind}'] = evaluate(specs[split],menagerie,args.output/'eval'/split/kind,
                    model if kind=='ppo' else None,normalized)
                save_json(args.output/'evaluation.json',results)
        assert np.array_equal(normalization_before[0],normalized.obs_rms.mean)
        assert np.array_equal(normalization_before[1],normalized.obs_rms.var)
        assert normalization_before[2] == normalized.obs_rms.count
        save_json(args.output/'COMPLETE.json',dict(status='complete',results=results,
            elapsed_s=time.time()-start,normalization_frozen=True,checkpoint_sha256=sha(args.output/'ppo_final.zip'),
            publication_ready=False,resources=resource_check()))
        save_json(args.output/'progress.json',dict(status='complete',elapsed_s=time.time()-start,pid=os.getpid()))
    except BaseException as error:
        save_json(args.output/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),
            elapsed_s=time.time()-start,pid=os.getpid()))
        raise


if __name__ == '__main__':
    main()
