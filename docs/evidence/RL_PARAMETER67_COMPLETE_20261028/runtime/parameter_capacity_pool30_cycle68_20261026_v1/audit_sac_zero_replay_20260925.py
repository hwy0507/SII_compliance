"""No physics: exact zero controls and same-DGX CUDA final SAC input replay."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import traceback


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--reference-run', type=Path, required=True)
    parser.add_argument('--branch', choices=('online_only', 'demo_prefill'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    require = lambda condition, message: None if condition else fail(message)
    require(not args.output.exists(), 'Never overwrite verification evidence')
    source = root / 'source'
    sys.path[:0] = [str(source / 'scripts'), str(source / 'tools')]
    import run_canonical48_sac_20260925 as entry
    from canonical48_sac_audit_20260925 import stats
    import gymnasium as gym
    import numpy as np
    import torch
    from stable_baselines3 import SAC
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.cuda.set_per_process_memory_fraction(.1)
    folder = root / 'training' / args.branch
    report = dict(passed=False, branch=args.branch, mode='direct7', simulator_steps=0, gradient_updates=0,
                  audit_tool_sha256=sha(__file__), zero={}, replay={}, input_sha256={})
    normalizer = None
    try:
        manifest = json.loads((folder / 'manifest.json').read_text())
        complete = json.loads((folder / 'COMPLETE.json').read_text())
        require(not (folder / 'FAILED.json').exists() and complete['status'] == 'complete', 'Run not complete')
        require(complete['seed'] == 20260923 and complete['training_steps'] == 8192 and complete['updates'] == 8092,
                'Unexpected final budget')
        require(manifest['branch'] == args.branch and manifest['mode'] == 'direct7', 'Wrong branch')
        require(manifest['device'] == 'cuda' and torch.cuda.is_available(), 'Same-device CUDA required')
        for name, field in [('sac_final.zip', 'checkpoint_sha256'), ('vecnormalize_train_only.pkl', 'normalizer_sha256')]:
            require(sha(folder / name) == complete[field], 'Final artifact changed')
        require(entry.paired.source_hashes() == manifest['source_hashes'], 'Training source differs')
        for name in ('manifest.json', 'COMPLETE.json', 'sac_final.zip', 'vecnormalize_train_only.pkl'):
            report['input_sha256'][str(folder / name)] = sha(folder / name)
        reference_manifest = json.loads((args.reference_run / 'manifest.json').read_text())
        require(reference_manifest['mode'] == 'direct7' and reference_manifest['training']['seed'] == 20260923,
                'Reference must be original same-mode seed23')
        require(not (args.reference_run / 'FAILED.json').exists(), 'Reference has FAILED marker')
        reference_complete = json.loads((args.reference_run / 'COMPLETE.json').read_text())
        require(reference_complete['status'] == 'complete', 'Reference incomplete')
        for split in ('train', 'validation'):
            reference = args.reference_run / 'eval' / split / 'zero/episode_00000'
            current = folder / 'eval' / split / 'zero/episode_00000'
            comparison = entry.paired.compare_episode(reference, current, 'direct7')
            with np.load(reference / 'transitions.npz', allow_pickle=False) as left, np.load(current / 'transitions.npz', allow_pickle=False) as right:
                require(set(left.files) == set(right.files), 'Zero transition keys differ')
                comparison['transition_arrays'] = {key: entry.paired.finite_exact(left[key], right[key], split + ':' + key)
                                                   for key in left.files}
                require(right['policy_action'].shape == (600, 7), 'Zero must contain 600 direct7 actions')
            for directory in (reference, current):
                for path in directory.iterdir():
                    if path.is_file():
                        report['input_sha256'][str(path)] = sha(path)
            report['zero'][split] = comparison

        model = SAC.load(folder / 'sac_final.zip', device='cuda')
        require(model.seed == 20260923 and model.num_timesteps == 8192 and model._n_updates == 8092, 'Reload metadata mismatch')
        require(model.observation_space.shape == (48,) and model.action_space.shape == (7,), 'Wrong policy dimensions')
        require(np.array_equal(model.action_space.low, np.array([0] + [-1] * 6, np.float32)) and
                np.array_equal(model.action_space.high, np.ones(7, np.float32)), 'Wrong direct7 bounds')

        class SpacesOnly(gym.Env):
            observation_space = model.observation_space
            action_space = model.action_space
            def reset(self, *args, **kwargs):
                raise RuntimeError('No physics permitted')
            def step(self, *args, **kwargs):
                raise RuntimeError('No physics permitted')

        normalizer = VecNormalize.load(folder / 'vecnormalize_train_only.pkl', DummyVecEnv([SpacesOnly]))
        normalizer.training = False
        normalizer.norm_reward = False
        before = stats(normalizer)

        def replay(raw, recorded=None):
            predictions = []
            for observation in raw:
                normalized = normalizer.normalize_obs(observation.astype(np.float32)[None])[0]
                action, _ = model.predict(normalized, deterministic=True)
                action = np.clip(np.asarray(action, np.float64), model.action_space.low, model.action_space.high)
                with torch.no_grad():
                    tensor, _ = model.policy.obs_to_tensor(normalized)
                    actor_output = model.actor(tensor, deterministic=True).cpu().numpy()
                direct = model.policy.unscale_action(actor_output)[0].astype(np.float64)
                require(np.array_equal(action, direct), 'SAC.predict versus deterministic actor differs')
                predictions.append(action)
            predictions = np.asarray(predictions)
            require(np.isfinite(predictions).all() and predictions.shape == (len(raw), 7), 'Invalid replay output')
            if recorded is not None:
                require(np.array_equal(predictions, recorded['policy_action']), 'Actual evaluation policy requests differ')
                require(np.array_equal(predictions, recorded['execution_action']), 'Actual direct7 execution differs')
            return dict(samples=len(raw), predict_vs_actor_exact=True, archived_request_execution_exact=recorded is not None,
                        action_sha256=hashlib.sha256(predictions.tobytes()).hexdigest(), policy_atol=0.)

        def read_episode(directory):
            for name in ('transitions.npz', 'actor_trace.npz', 'transition_contract.json', 'rollout.json', 'rollout.mjb'):
                report['input_sha256'][str(directory / name)] = sha(directory / name)
            with np.load(directory / 'transitions.npz', allow_pickle=False) as archive:
                data = {key: archive[key] for key in archive.files}
            with np.load(directory / 'actor_trace.npz', allow_pickle=False) as trace:
                require(np.array_equal(data['observation'], trace['observation']), 'Archived actor input differs')
                require(np.array_equal(data['execution_action'], trace['action']), 'Archived execution trace differs')
            raw = data['observation']
            require(raw.dtype == np.float64 and raw.shape == (len(raw), 48) and 1 <= len(raw) <= 600, 'Invalid raw48 episode')
            require(data['terminated'][-1] and not data['terminated'][:-1].any() and not data['truncated'].any(), 'Partial/error episode')
            require(not data['next_observation_valid'][-1] and data['next_observation_valid'][:-1].all(), 'Invalid next masks')
            require(np.array_equal(data['next_observation'][:-1], raw[1:]), 'Nonconsecutive boundary observations')
            rollout = json.loads((directory / 'rollout.json').read_text())
            require(abs(rollout['duration_s'] - .04 * len(raw)) < 1e-6, 'Duration differs from actor transitions')
            require(len(raw) == 600 or rollout['invalid_physics'], 'Short episode without safety termination')
            contract = json.loads((directory / 'transition_contract.json').read_text())
            require(contract['mode'] == 'direct7' and contract['adapter_train_nominal_options'] == manifest['nominal_options'],
                    'Episode contract differs')
            return data, rollout

        fallback_raw = None
        for split in ('train', 'validation'):
            data, rollout = read_episode(folder / 'eval' / split / 'sac/episode_00000')
            replay_result = replay(data['observation'], data)
            replay_result['safety_terminated'] = bool(rollout['invalid_physics'])
            replay_result['fallback'] = None
            if len(data['observation']) < 600:
                if fallback_raw is None:
                    argv = manifest['argv']
                    require(argv.count('--proof-root') == 1, 'Ambiguous fixed proof root')
                    proof_root = Path(argv[argv.index('--proof-root') + 1])
                    require(proof_root.is_absolute(), 'Proof path must be explicit absolute path')
                    require(entry.verify_proofs(proof_root, manifest) == manifest['proof_sha256'], 'Fixed proof changed')
                    proof_dir = proof_root / 'direct7/gym/episode_00000'
                    proof_data, proof_rollout = read_episode(proof_dir)
                    require(len(proof_data['observation']) == 600 and not np.any(proof_data['policy_action']) and
                            not proof_rollout['invalid_physics'], 'Fallback is not original 600-step zero proof')
                    parity = json.loads((proof_root / 'direct7/PARITY.json').read_text())
                    require(sha(proof_dir / 'rollout.mjb') == parity['model_mjb_sha256'], 'Fallback model differs')
                    fallback_raw = proof_data['observation']
                    report['fallback_proof_path'] = str(proof_dir)
                replay_result['fallback'] = replay(fallback_raw)
            report['replay'][split] = replay_result
        require(stats(normalizer) == before, 'Replay changed normalization')
        require(all(sha(path) == digest for path, digest in report['input_sha256'].items()), 'Inputs changed during audit')
        report.update(passed=True, device='cuda', same_device=True, normalization_frozen=True,
                      limitation='Policy input replay only; no SAC deployment adapter or new physical trajectory is claimed. Fixed proof fallback, when used, does not invent future learned-policy transitions.')
    except BaseException as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
        raise
    finally:
        if normalizer is not None:
            normalizer.close()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
        print(json.dumps(dict(passed=report['passed'], branch=args.branch)))


def fail(message):
    raise AssertionError(message)


if __name__ == '__main__':
    main()
