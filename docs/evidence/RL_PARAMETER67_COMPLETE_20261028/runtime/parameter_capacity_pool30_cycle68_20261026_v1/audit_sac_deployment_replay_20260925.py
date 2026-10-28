"""No-physics same-DGX CUDA SAC deployment adapter replay, including fixed fallback."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tools')]
import numpy as np
from canonical48_sac_deployment_20260925 import load_policy, require, sha
import audit_paired_deployment_replay_20260924 as original
import run_canonical48_sac_20260925 as entry


def independent_actor(training):
    import gymnasium as gym
    from stable_baselines3 import SAC
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    model = SAC.load(training / 'sac_final.zip', device='cuda')

    class SpacesOnly(gym.Env):
        observation_space = model.observation_space
        action_space = model.action_space
        def reset(self, *args, **kwargs):
            raise RuntimeError('No physics')
        def step(self, *args, **kwargs):
            raise RuntimeError('No physics')

    normalizer = VecNormalize.load(training / 'vecnormalize_train_only.pkl', DummyVecEnv([SpacesOnly]))
    normalizer.training = False
    normalizer.norm_reward = False

    def predict(raw):
        observation = raw.astype(np.float32)
        action, _ = model.predict(normalizer.normalize_obs(observation[None])[0], deterministic=True)
        return np.clip(np.asarray(action, dtype=np.float64), model.action_space.low, model.action_space.high)

    return predict, normalizer


def fixed_proof(manifest, hashes):
    argv = manifest['argv']
    require(argv.count('--proof-root') == 1, 'Unique training-bound proof path required')
    root = Path(argv[argv.index('--proof-root') + 1])
    require(root.is_absolute(), 'Explicit absolute original proof required')
    # SAC has new source/protocol additions; verify original proof subset and base protocol.
    require(entry.verify_proofs(root, manifest) == manifest['proof_sha256'], 'Original proof provenance drift')
    for mode in ('parameter6', 'direct7'):
        for name in ('manifest.json', 'COMPLETE.json', 'PARITY.json'):
            hashes[str(root / mode / name)] = sha(root / mode / name)
    folder = root / 'direct7/gym/episode_00000'
    data, contract, result = original.read_episode(folder, hashes)
    parity = json.loads((root / 'direct7/PARITY.json').read_text())
    require(sha(folder / 'rollout.mjb') == parity['model_mjb_sha256'], 'Original proof MJB changed')
    require(len(data['observation']) == 600 and not np.any(data['policy_action']) and not result['invalid_physics'],
            'Require original full600 zero direct7 proof')
    require(contract['mode'] == 'direct7' and contract['adapter_train_nominal_options'] == manifest['nominal_options'],
            'Fixed proof adapter/nominal differs')
    return data['observation'], str(folder)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--training-directory', type=Path, required=True)
    parser.add_argument('--branch', choices=('online_only', 'demo_prefill'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Never overwrite replay evidence')
    training = args.training_directory.resolve()
    manifest = json.loads((training / 'manifest.json').read_text())
    policy = normalizer = None
    report = dict(passed=False, branch=args.branch, mode='direct7', simulator_steps=0, gradient_updates=0,
                  samples=600, input_sha256={}, splits={})
    hashes = report['input_sha256']
    try:
        policy, metadata = load_policy(training, args.branch, 'cuda')
        predict, normalizer = independent_actor(training)
        before = policy.actor.statistics()
        reference_before = original.np.asarray(normalizer.obs_rms.mean).copy(), original.np.asarray(normalizer.obs_rms.var).copy(), original.np.asarray(normalizer.obs_rms.count).copy()
        for split in ('train', 'validation'):
            folder = training / 'eval' / split / 'sac/episode_00000'
            data, contract, result = original.read_episode(folder, hashes)
            require(contract['mode'] == 'direct7' and contract['adapter_train_nominal_options'] == metadata['nominal_options'],
                    'Actual evaluation adapter/nominal differs')
            actual = original.replay(policy, predict, data['observation'], metadata, recorded=data)
            fallback = proof_path = None
            if len(data['observation']) < 600:
                proof_raw, proof_path = fixed_proof(manifest, hashes)
                fallback = original.replay(policy, predict, proof_raw, metadata)
            report['splits'][split] = dict(actual_evaluation=actual,
                actual_evaluation_safety_terminated=bool(result['invalid_physics']), fallback=fallback,
                fallback_proof_path=proof_path,
                end_to_end_exact=actual['end_to_end_exact'] and (fallback is None or fallback['end_to_end_exact']))
        after = policy.actor.statistics()
        checks = {str(i): original.compare(a, b, 0., 'adapter normalization') for i, (a, b) in enumerate(zip(before, after))}
        reference_after = normalizer.obs_rms.mean, normalizer.obs_rms.var, normalizer.obs_rms.count
        checks.update({'reference_' + str(i): original.compare(a, b, 0., 'original evaluation normalization')
                       for i, (a, b) in enumerate(zip(reference_before, reference_after))})
        for path in (training / 'manifest.json', training / 'COMPLETE.json', training / 'sac_final.zip',
                     training / 'vecnormalize_train_only.pkl', Path(__file__),
                     ROOT / 'scripts/canonical48_sac_deployment_20260925.py',
                     ROOT / 'scripts/run_panel_sac_deployment_20260925.py',
                     ROOT / 'scripts/canonical48_paired_deployment_20260924.py',
                     ROOT / 'tools/audit_paired_deployment_replay_20260924.py',
                     ROOT / 'scripts/canonical48_vmc_tuning_20260924.py'):
            hashes[str(path)] = sha(path)
        require(all(sha(path) == value for path, value in hashes.items()), 'Replay inputs changed')
        report.update(passed=True, metadata=metadata, normalizer_checks=checks,
                      end_to_end_exact=all(value['end_to_end_exact'] for value in report['splits'].values()),
                      limitation='Fixed fallback is archived policy input replay, never invented future learned-policy physics. Both actual short episodes and all failures remain preserved.')
    except BaseException as error:
        import traceback
        report.update(error=repr(error), traceback=traceback.format_exc())
        raise
    finally:
        if policy is not None:
            policy.close()
        if normalizer is not None:
            normalizer.close()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
        print(json.dumps(dict(passed=report['passed'], branch=args.branch)))


if __name__ == '__main__':
    main()
