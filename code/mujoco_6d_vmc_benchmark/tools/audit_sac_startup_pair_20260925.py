"""Read-only cross-branch initial state and first 101 SAC transitions audit."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import pickle
import zipfile

import numpy as np
import torch


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def initial(folder):
    with zipfile.ZipFile(folder / 'sac_initial.zip') as archive:
        state = torch.load(io.BytesIO(archive.read('policy.pth')), map_location='cpu', weights_only=True)
        variables = torch.load(io.BytesIO(archive.read('pytorch_variables.pth')), map_location='cpu', weights_only=True)
        metadata = json.loads(archive.read('data'))
    state['log_ent_coef'] = variables['log_ent_coef']
    fingerprints = {}
    for name, tensor in sorted(state.items()):
        array = tensor.detach().cpu().numpy()
        fingerprints[name] = dict(shape=list(array.shape), dtype=str(array.dtype),
                                  sha256=hashlib.sha256(array.tobytes()).hexdigest())
    with (folder / 'vecnormalize_initial.pkl').open('rb') as stream:
        normalization = pickle.load(stream)
    rms = dict(mean=np.asarray(normalization.obs_rms.mean).tolist(),
               var=np.asarray(normalization.obs_rms.var).tolist(), count=float(normalization.obs_rms.count),
               clip_obs=normalization.clip_obs, epsilon=normalization.epsilon,
               norm_obs=normalization.norm_obs, norm_reward=normalization.norm_reward)
    require(metadata['seed'] == 20260923 and metadata['num_timesteps'] == metadata['_n_updates'] == 0,
            'Initial model seed or budget differs')
    return fingerprints, rms


def prefix(path, length, only_online=False):
    rows = []
    with path.open() as stream:
        for line in stream:
            if not line.endswith('\n'):
                break  # Live writer's incomplete final row is not evidence yet.
            row = json.loads(line)
            if only_online and row['evidence']['source'] != 'online':
                continue
            rows.append(row)
            if len(rows) == length:
                break
    require(len(rows) == length, 'Insufficient complete evidence rows: ' + str(path))
    return rows


def audit(root):
    preflight = json.loads((root / 'PREFLIGHT.json').read_text())
    result = dict(passed=False, simulations_started=0, gradient_updates=0,
                  preflight_sha256=sha(root / 'PREFLIGHT.json'), branches={})
    initial_states = []
    prefixes = []
    for branch in ('online_only', 'demo_prefill'):
        folder = root / 'training' / branch
        manifest = json.loads((folder / 'manifest.json').read_text())
        artifacts = manifest['initial_artifact_sha256']
        require(all(sha(folder / name) == digest for name, digest in artifacts.items()), 'Initial artifact hash drift')
        fingerprints, rms = initial(folder)
        expected = preflight['initial_probe']['branches'][branch]
        require(fingerprints == expected['initial_policy'], 'Actual initial policy/alpha differs from preflight: ' + branch)
        require(rms == expected['initial_normalization'], 'Actual initial RMS differs from preflight: ' + branch)
        initial_states.append((fingerprints, rms))
        rows = prefix(folder / 'replay_audit/replay_insertions.jsonl', 101, only_online=True)
        for step, row in enumerate(rows, 1):
            require(row['evidence']['online_step'] == step, 'Warmup prefix is not contiguous')
            require(row['index'] == step - 1 + (600 if branch == 'demo_prefill' else 0), 'Replay insertion offset differs')
        optimizer_rows = prefix(folder / 'optimizer_steps.jsonl', 3)
        require({row['optimizer'] for row in optimizer_rows} == {'actor', 'critic', 'entropy'}, 'Missing first optimizer step')
        require(all(row['online_step'] == 101 and row['completed_steps'] == 1 for row in optimizer_rows),
                'First gradient update is not after collecting transition 101')
        prefixes.append(rows)
        result['branches'][branch] = dict(initial_artifact_sha256=artifacts, initial_matches_preflight=True,
            first_optimizer_rows=optimizer_rows,
            online_prefix_sha256=hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
            branch_failed_exists=(folder / 'FAILED.json').exists())
    require(initial_states[0] == initial_states[1], 'Actual two-branch initial states differ')
    keys = ('observation', 'next_observation', 'next_observation_valid', 'buffer_action', 'environment_action',
            'reward', 'done', 'episode_step', 'online_step')
    for step, (left, right) in enumerate(zip(*prefixes), 1):
        for key in keys:
            require(left['evidence'][key] == right['evidence'][key], f'Transition {step} evidence differs: {key}')
        require(left['stored'] == right['stored'], f'Transition {step} actual replay slots differ')
    result.update(passed=True, actual_initial_pair_exact=True, warmup_first100_exact=True,
                  step101_collected_before_first_update_exact=True,
                  compared_evidence_fields=list(keys), actual_replay_all_fields_exact=True,
                  temporal_basis='Reviewed SB3 collect_rollouts stores transition before train; first actor/critic/entropy optimizer events are online step 101.',
                  rng_basis='DGX zero-step preflight proves prefill consumes no NumPy/Torch/CUDA RNG; actual prefix equality corroborates execution. No RNG trace was added to live runs.',
                  limitation='This verifies startup only; expected divergence after the first optimizer update is not a failure.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Do not overwrite startup evidence')
    try:
        result = audit(args.root.resolve())
    except BaseException as error:
        result = dict(passed=False, error=repr(error), simulations_started=0, gradient_updates=0)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as stream:
            json.dump(result, stream, indent=2)
        raise
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
