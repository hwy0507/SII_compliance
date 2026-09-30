"""Frozen paired-policy inference; no environment construction or physics steps."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
from canonical48_vmc_tuning_20260924 import Canonical48VMCTuning

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def frozen_training(directory, mode):
    directory = Path(directory).resolve()
    if (directory/'FAILED.json').exists():
        raise ValueError('Training has FAILED marker; COMPLETE cannot override it')
    manifest = json.loads((directory/'manifest.json').read_text())
    complete = json.loads((directory/'COMPLETE.json').read_text())
    expected_mode = 'parameter6' if mode == 'nominal_train_vmc' else mode
    if complete['status'] != 'complete' or complete['mode'] != expected_mode or manifest['mode'] != expected_mode:
        raise ValueError('Require completed matching training branch')
    if complete['training_steps'] != 8192 or complete['recorded_transitions'] != 8192:
        raise ValueError('Require fixed final8192, not an intermediate checkpoint')
    if not complete['source_unchanged'] or not complete['normalization_frozen']:
        raise ValueError('Training source/normalization verification absent')
    for filename, key in (('ppo_final.zip', 'checkpoint_sha256'), ('vecnormalize_train_only.pkl', 'normalizer_sha256')):
        if sha(directory/filename) != complete[key]:
            raise ValueError('Frozen training artifact hash mismatch: '+filename)
    nominal = manifest['nominal_options']
    training_options = json.loads(manifest['fixture_specs']['train']['command']['environment']['CORE_VMC_CONFIG'])
    if nominal != training_options:
        raise ValueError('Adapter options are not the full original training options')
    for source in ('scripts/canonical48_vmc_tuning_20260924.py', 'scripts/run_vmc_6d_constrained_push_20260918.py'):
        if sha(ROOT/source) != manifest['source_hashes'][source]:
            raise ValueError('Frozen analytic execution source mismatch: '+source)
    return manifest, complete, copy.deepcopy(nominal)


class FrozenActor:
    def __init__(self, directory, mode, device):
        import gymnasium as gym
        import torch
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
        torch.set_num_threads(1)
        low = -np.ones(6, dtype=np.float32) if mode == 'parameter6' else np.array([0]+[-1]*6, dtype=np.float32)

        class SpacesOnly(gym.Env):
            observation_space = gym.spaces.Box(-np.inf, np.inf, (48,), dtype=np.float32)
            action_space = gym.spaces.Box(low, np.ones_like(low), dtype=np.float32)
            def reset(self, *args, **kwargs):
                raise RuntimeError('Inference spaces have no simulation')
            def step(self, *args, **kwargs):
                raise RuntimeError('Inference spaces have no simulation')

        self.model = PPO.load(Path(directory)/'ppo_final.zip', device=device)
        if self.model.num_timesteps != 8192 or self.model.observation_space.shape != (48,):
            raise ValueError('Wrong model budget or observation contract')
        if not (np.array_equal(self.model.action_space.low, low) and np.array_equal(self.model.action_space.high, np.ones_like(low))):
            raise ValueError('Wrong policy action Box')
        self.normalizer = VecNormalize.load(Path(directory)/'vecnormalize_train_only.pkl', DummyVecEnv([SpacesOnly]))
        if self.normalizer.observation_space.shape != (48,) or not self.normalizer.norm_obs:
            raise ValueError('Wrong training normalization contract')
        self.normalizer.training = False
        self.normalizer.norm_reward = False
        self.low, self.high = low, np.ones_like(low)

    def act(self, raw):
        # Both Gym reset and step return float32; preserve this exact cast order.
        normalized = self.normalizer.normalize_obs(np.asarray(raw, dtype=np.float32)[None])[0]
        action, _ = self.model.predict(normalized, deterministic=True)
        action = np.asarray(action, dtype=np.float64)
        if action.shape != self.low.shape or not np.isfinite(action).all():
            raise ValueError('Invalid deterministic policy output')
        return np.clip(action, self.low, self.high)

    def statistics(self):
        rms = self.normalizer.obs_rms
        return (rms.mean.copy(), rms.var.copy(), np.asarray(rms.count).copy())

    def close(self):
        self.normalizer.close()


class PairedExecutionPolicy:
    """The only raw48 -> action7 adapter used by the new panel entry point."""
    def __init__(self, mode, nominal_options, actor=None):
        if mode not in ('parameter6', 'direct7', 'nominal_train_vmc'):
            raise ValueError('Unknown paired deployment mode')
        if (mode == 'nominal_train_vmc') != (actor is None):
            raise ValueError('Learned modes require their own frozen actor')
        self.mode, self.actor = mode, actor
        self.kind = 'paired_'+mode
        self.controller = Canonical48VMCTuning(copy.deepcopy(nominal_options))
        self.reset()

    def reset(self):
        self.controller.reset()
        self.log = {k: [] for k in ('observation', 'policy_action', 'execution_action', 'log_scale', 'stiffness', 'damping')}

    def act(self, observation):
        raw = np.asarray(observation)
        if raw.dtype != np.float64 or raw.shape != (48,) or not np.isfinite(raw).all():
            raise ValueError('Deployment backend requires original finite raw float64 canonical48')
        request = np.zeros(6) if self.actor is None else np.asarray(self.actor.act(raw), dtype=np.float64)
        low = np.array([0]+[-1]*6) if self.mode == 'direct7' else -np.ones(6)
        if request.shape != low.shape or not np.isfinite(request).all():
            raise ValueError('Invalid policy request')
        request = np.clip(request, low, 1.)
        if self.mode == 'direct7':
            action = request.copy()
        else:
            # Never feed rounded actor input or normalized values to the VMC.
            action = self.controller.act(raw, request)
        record = dict(observation=raw, policy_action=request, execution_action=action,
                      log_scale=self.controller.log_scale, stiffness=self.controller.base.k, damping=self.controller.base.b)
        for key, value in record.items():
            self.log[key].append(np.asarray(value).copy())
        return action

    def close(self):
        if self.actor is not None:
            self.actor.close()


def load_policy(directory, mode, device=None):
    manifest, complete, nominal = frozen_training(directory, mode)
    device = device or manifest['device']
    actor = None if mode == 'nominal_train_vmc' else FrozenActor(directory, mode, device)
    policy = PairedExecutionPolicy(mode, nominal, actor)
    metadata = dict(mode=mode, device=device, trained_device=manifest['device'], training_steps=8192,
        training_manifest_sha256=sha(Path(directory)/'manifest.json'), training_complete_sha256=sha(Path(directory)/'COMPLETE.json'),
        checkpoint_sha256=complete['checkpoint_sha256'], normalizer_sha256=complete['normalizer_sha256'],
        nominal_options=nominal, actor_observation='raw48 cast float32, then own frozen VecNormalize',
        backend_observation='original raw float64 canonical48; wrench[39:45]',
        adapter_active=mode != 'direct7', episode_reset='VMC filter/offset/velocity and log gains; frozen normalizer unchanged',
        runtime_CORE_rule='Unchanged fixture environment; never adapter nominal source',
        source_sha256={str(Path(__file__).relative_to(ROOT)): sha(__file__)})
    return policy, metadata
