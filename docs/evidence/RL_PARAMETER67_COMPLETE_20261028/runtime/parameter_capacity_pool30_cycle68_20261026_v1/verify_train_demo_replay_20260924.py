"""Exercise the real SB3 replay/normalization boundary without simulation or training."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import gymnasium as gym
import stable_baselines3 as sb3
from stable_baselines3.common.buffers import ReplayBuffer
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.policies import BasePolicy

DEMO_MANIFEST = '9f9092c03abcbf80cbf3e036552fbd9d6a214cdd21af8dded5eed1c402eb0a56'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


class NoSimulationEnv(gym.Env):
    observation_space = gym.spaces.Box(-np.inf, np.inf, (48,), np.float32)
    action_space = gym.spaces.Box(np.array([0., -1., -1., -1., -1., -1., -1.], np.float32), np.ones(7, np.float32))

    def reset(self, **kwargs):
        raise AssertionError('This verification must never reset a simulator')

    def step(self, action):
        raise AssertionError('This verification must never execute actions')


def validate(data):
    shapes = {'observations': (600, 48), 'next_observations': (600, 48),
              'actions_execution': (600, 7), 'actions_sac': (600, 7),
              'rewards': (600, 1), 'dones': (600, 1), 'timeouts': (600, 1),
              'next_observation_valid': (600, 1)}
    require(set(data) == set(shapes), 'Unexpected input fields')
    for key, shape in shapes.items():
        require(data[key].shape == shape and np.isfinite(data[key]).all(), 'Invalid array: ' + key)
        require(data[key].dtype == (np.bool_ if key == 'next_observation_valid' else np.float32), 'Wrong dtype: ' + key)
    done = np.zeros((600, 1), np.float32)
    done[-1] = 1
    require(np.array_equal(data['dones'], done) and not data['timeouts'].any(), 'Finite terminal must disable bootstrap')
    require(np.array_equal(data['next_observation_valid'], done == 0), 'Invalid next mask')
    require(np.array_equal(data['next_observations'][:-1], data['observations'][1:]), 'Broken next chain')
    require(np.array_equal(data['next_observations'][-1], data['observations'][-1]), 'Wrong marked terminal placeholder')
    action = data['actions_execution']
    space = NoSimulationEnv.action_space
    require(np.all(action >= space.low) and np.all(action <= space.high), 'Action outside environment bounds')
    # BasePolicy.scale_action needs only the action space, not a trained model.
    carrier = type('ActionSpaceOnly', (), {'action_space': space})()
    require(np.array_equal(data['actions_sac'], BasePolicy.scale_action(carrier, action)), 'SAC action scale mismatch')


def verify(demo):
    demo = Path(demo).resolve()
    require(sha(demo / 'manifest.json') == DEMO_MANIFEST, 'Expected pinned train-only r2 manifest')
    manifest = json.loads((demo / 'manifest.json').read_text())
    for name, digest in manifest['artifact_sha256'].items():
        require(sha(demo / name) == digest, 'Dataset artifact drift')
    with np.load(demo / 'demonstration.npz', allow_pickle=False) as archive:
        data = {k: archive[k] for k in archive.files}
    validate(data)
    buffer = ReplayBuffer(1024, NoSimulationEnv.observation_space, NoSimulationEnv.action_space,
                          device='cpu', n_envs=1, optimize_memory_usage=False, handle_timeout_termination=True)
    normalizer = VecNormalize(DummyVecEnv([NoSimulationEnv]), norm_obs=True, norm_reward=False, clip_obs=12.)
    # Deliberately nonidentity, synthetic statistics: this tests normalization
    # once at sample-time without fitting statistics to demo/validation/test.
    normalizer.obs_rms.mean = np.linspace(-.7, .7, 48)
    normalizer.obs_rms.var = np.linspace(.2, 2., 48)
    normalizer.obs_rms.count = 123.
    normalizer.training = False
    before = (normalizer.obs_rms.mean.copy(), normalizer.obs_rms.var.copy(), normalizer.obs_rms.count)
    try:
        for i in range(600):
            buffer.add(data['observations'][i:i+1], data['next_observations'][i:i+1],
                       data['actions_sac'][i:i+1], data['rewards'][i], data['dones'][i],
                       [{'TimeLimit.truncated': False}])
        require(buffer.size() == 600 and buffer.pos == 600 and not buffer.full, 'Wrong replay size')
        checks = {}
        for stored, key in [('observations', 'observations'), ('next_observations', 'next_observations'),
                            ('actions', 'actions_sac'), ('rewards', 'rewards'), ('dones', 'dones'), ('timeouts', 'timeouts')]:
            actual = getattr(buffer, stored)[:600]
            if actual.ndim == 3:
                actual = actual[:, 0]
            require(np.array_equal(actual, data[key]), 'Replay storage mismatch: ' + stored)
            checks[stored] = 'raw exact'
        # Deterministic full index coverage through the real sampler rather
        # than random subsampling which could miss the last transition.
        sampled = buffer._get_samples(np.arange(600), env=normalizer)
        expected = {'observations': normalizer.normalize_obs(data['observations']),
                    'next_observations': normalizer.normalize_obs(data['next_observations']),
                    'actions': data['actions_sac'], 'rewards': data['rewards'], 'dones': data['dones']}
        for key, target in expected.items():
            require(np.array_equal(getattr(sampled, key).cpu().numpy(), target), 'Sample mismatch: ' + key)
        bootstrap_mask = 1 - sampled.dones.cpu().numpy()
        require(np.array_equal(bootstrap_mask.astype(bool), data['next_observation_valid']), 'Terminal placeholder would bootstrap')
        require(not np.array_equal(expected['observations'], data['observations']), 'Synthetic normalization is ineffective')
        require(np.array_equal(before[0], normalizer.obs_rms.mean) and np.array_equal(before[1], normalizer.obs_rms.var)
                and before[2] == normalizer.obs_rms.count, 'Sampling changed normalization statistics')
    finally:
        normalizer.close()
    return dict(passed=True,transitions=600,simulator_steps=0,gradient_updates=0,sb3_version=sb3.__version__,
                storage_checks=checks,sample_observation_normalized_once=True,sample_rewards_unchanged=True,
                terminal_bootstrap_disabled=True,normalizer_statistics_unchanged=True,
                normalizer_test='Fixed synthetic nonidentity statistics; no fitting or training normalizer produced',
                limitations='Standard ReplayBuffer prefill integration only; not RLPD balanced sampling or SAC learning',
                source_sha256=sha(__file__),demo_manifest_sha256=sha(demo/'manifest.json'),
                demo_artifact_sha256=manifest['artifact_sha256'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    require(not args.output.exists(),'Fresh evidence file required')
    report=verify(args.demo)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report))


if __name__=='__main__':
    main()
