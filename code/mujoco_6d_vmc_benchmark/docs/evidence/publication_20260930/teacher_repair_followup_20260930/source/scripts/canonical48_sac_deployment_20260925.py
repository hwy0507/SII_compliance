"""Frozen final SAC inference through the unchanged direct7 execution layer."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import zipfile
import numpy as np
from canonical48_paired_deployment_20260924 import PairedExecutionPolicy, sha

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def frozen_training(directory, branch):
    directory = Path(directory).resolve()
    require(branch in ('online_only', 'demo_prefill'), 'Undeclared SAC branch')
    require(not (directory / 'FAILED.json').exists(), 'FAILED training cannot deploy')
    manifest = json.loads((directory / 'manifest.json').read_text())
    complete = json.loads((directory / 'COMPLETE.json').read_text())
    require(complete['status'] == 'complete' and complete['mode'] == manifest['mode'] == 'direct7', 'Incomplete/wrong direct7 run')
    require(complete['branch'] == manifest['branch'] == branch, 'Wrong SAC branch')
    require(complete['seed'] == manifest['training']['seed'] == 20260923, 'Wrong SAC seed')
    require(manifest['algorithm'] == 'standard SAC' and manifest['training']['steps'] == 8192,
            'Wrong algorithm or manifest training budget')
    require(complete['training_steps'] == complete['recorded_transitions'] == 8192 and complete['updates'] == 8092,
            'Only final8192/8092 may deploy')
    require(complete['optimizer_steps'] == dict(actor=8092, critic=8092, entropy=8092), 'Actual optimizer budget incomplete')
    require(complete['normalization_frozen'] and complete['source_unchanged'], 'Final source/RMS check absent')
    require(manifest['device'] == 'cuda', 'Training device must be CUDA')
    require(manifest['data_budget'] == dict(online=8192, demo=600 if branch == 'demo_prefill' else 0,
                                          total=8792 if branch == 'demo_prefill' else 8192, offline_updates=0), 'Changed data budget')
    for filename, key in (('sac_final.zip', 'checkpoint_sha256'), ('vecnormalize_train_only.pkl', 'normalizer_sha256')):
        require(sha(directory / filename) == complete[key], 'Final artifact changed: ' + filename)
    with zipfile.ZipFile(directory / 'sac_final.zip') as archive:
        data = json.loads(archive.read('data'))
    require(data['seed'] == 20260923 and data['num_timesteps'] == 8192 and data['_n_updates'] == 8092, 'Final zip metadata mismatch')
    for filename, digest in manifest['source_hashes'].items():
        require((ROOT / filename).resolve().is_relative_to(ROOT) and sha(ROOT / filename) == digest,
                'Original frozen training source changed: ' + filename)
    nominal = manifest['nominal_options']
    require(nominal == json.loads(manifest['fixture_specs']['train']['command']['environment']['CORE_VMC_CONFIG']),
            'Nominal must come from original training manifest')
    return manifest, complete, copy.deepcopy(nominal)


class FrozenSACActor:
    def __init__(self, directory, device='cuda'):
        import gymnasium as gym
        import torch
        from stable_baselines3 import SAC
        from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
        require(device == 'cuda' and torch.cuda.is_available(), 'Same-DGX CUDA required, no fallback')
        torch.set_num_threads(1)
        self.model = SAC.load(Path(directory) / 'sac_final.zip', device=device)
        require(self.model.seed == 20260923 and self.model.num_timesteps == 8192 and self.model._n_updates == 8092,
                'Wrong loaded model seed/budget')
        self.low = np.array([0] + [-1] * 6, dtype=np.float32)
        self.high = np.ones(7, dtype=np.float32)
        require(self.model.observation_space.shape == (48,) and
                np.array_equal(self.model.action_space.low, self.low) and
                np.array_equal(self.model.action_space.high, self.high), 'Wrong canonical48/direct7 Box')
        model = self.model

        class SpacesOnly(gym.Env):
            observation_space = model.observation_space
            action_space = model.action_space
            def reset(self, *args, **kwargs):
                raise RuntimeError('Inference spaces have no physics')
            def step(self, *args, **kwargs):
                raise RuntimeError('Inference spaces have no physics')

        self.normalizer = VecNormalize.load(Path(directory) / 'vecnormalize_train_only.pkl', DummyVecEnv([SpacesOnly]))
        require(self.normalizer.observation_space.shape == (48,) and self.normalizer.norm_obs and
                not self.normalizer.norm_reward and self.normalizer.clip_obs == 12. and self.normalizer.epsilon == 1e-8,
                'Wrong own training normalization')
        self.normalizer.training = False
        self.normalizer.norm_reward = False
        self.initial_statistics = self.statistics()

    def act(self, raw):
        normalized = self.normalizer.normalize_obs(np.asarray(raw, dtype=np.float32)[None])[0]
        action, _ = self.model.predict(normalized, deterministic=True)
        action = np.asarray(action, dtype=np.float64)
        require(action.shape == (7,) and np.isfinite(action).all(), 'Invalid deterministic SAC action')
        return np.clip(action, self.low, self.high)

    def statistics(self):
        rms = self.normalizer.obs_rms
        return rms.mean.copy(), rms.var.copy(), np.asarray(rms.count).copy()

    def close(self):
        try:
            require(all(np.array_equal(a, b) for a, b in zip(self.initial_statistics, self.statistics())),
                    'Deployment changed training RMS')
        finally:
            self.normalizer.close()


def load_policy(directory, branch, device='cuda'):
    manifest, complete, nominal = frozen_training(directory, branch)
    actor = FrozenSACActor(directory, device)
    policy = PairedExecutionPolicy('direct7', nominal, actor)
    metadata = dict(mode='direct7', branch=branch, algorithm='standard SAC', device=device, trained_device=manifest['device'],
        training_steps=8192, training_updates=8092, seed=20260923,
        training_manifest_sha256=sha(Path(directory) / 'manifest.json'),
        training_complete_sha256=sha(Path(directory) / 'COMPLETE.json'),
        checkpoint_sha256=complete['checkpoint_sha256'], normalizer_sha256=complete['normalizer_sha256'],
        nominal_options=nominal, actor_observation='raw48 cast float32, then own frozen VecNormalize',
        backend_observation='original raw float64 canonical48; unchanged direct7 execution', adapter_active=False,
        episode_reset='Unchanged PairedExecutionPolicy reset; frozen SAC RMS unchanged',
        runtime_CORE_rule='Unchanged fixture environment; never adapter nominal source',
        source_sha256={'scripts/canonical48_sac_deployment_20260925.py': sha(__file__),
                       'scripts/canonical48_paired_deployment_20260924.py': sha(ROOT / 'scripts/canonical48_paired_deployment_20260924.py')})
    return policy, metadata
