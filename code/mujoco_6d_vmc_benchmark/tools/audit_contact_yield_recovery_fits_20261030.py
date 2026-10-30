"""Audit all finite fits and replay nine models with frozen test actor code.

Reads only training/validation demonstrations, never test trajectories/labels.
Source versions need not have identical unused branches; actual selected
checkpoints must produce the recorded exported actions on every demonstration.
"""
import argparse
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path

import numpy as np

from train_special_scene_models_20261028 import SEEDS, RATES, DECAYS, UPDATES, read, sha, now


FIELDS = [*range(14, 17), *range(20, 23), *range(26, 29), *range(39, 48)]


def require(value, reason):
    if not value:
        raise ValueError(reason)


def load_class(source, filename, classname):
    path = source / 'scripts' / filename
    spec = importlib.util.spec_from_file_location('audit_frozen_' + filename[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, classname)


def audit(root, physics_source):
    state = read(root / 'execution.json')
    lock = read(root / 'MODEL_LOCK.json')
    require(state['status'] == 'complete' and lock['status'] == 'frozen', 'Fitting still incomplete')
    require(sha(root / 'MODEL_LOCK.json') == state['model_lock_sha256'], 'Changed model lock')
    source = read(root / 'FITTING_SOURCE.json')
    for path, digest in source['source_hashes'].items():
        require(sha(root / 'fitting_source' / path) == digest, f'Changed fitting source: {path}')
    for path, digest in state['fitting_input_hashes'].items():
        require(sha(root / path) == digest, f'Changed fitting input: {path}')
    data_sha = sha(root / 'data/training_data.npz')
    require(data_sha == lock['training_data_sha256'] == state['data_sha256'], 'Wrong dataset')
    metadata = read(root / 'data/DATA_COMPLETE.json')
    require(metadata['episodes'] == 34 and metadata['qualified_episodes'] == 30
            and metadata['augmented_recovery_episodes'] == 4, 'Wrong dataset population')
    with np.load(root / 'data/training_data.npz', allow_pickle=False) as z:
        obs, target, episode, train = [z[k].copy() for k in (
            'observation', 'requested_teacher_action', 'episode', 'train')]
        require(z['physical_execution'].all(), 'Nonphysical data present')
        importance = z['importance'].copy()
    require(obs.shape == (len(target), 48) and target.shape[1] == 7, 'Wrong interface')
    require(len(np.unique(episode[train])) == 28 and len(np.unique(episode[~train])) == 6, 'Wrong split')
    require(not set(episode[train]).intersection(episode[~train]), 'Episode leakage')
    for row in metadata['lineage']:
        ids = np.flatnonzero(episode == row['episode'])
        require(len(ids) == row['frames'] and np.all(train[ids] == (row['split'] == 'train')), 'Lineage split changed')
        path = Path(row['folder']) / 'trajectory.npz'
        require(sha(path) == row['hashes']['trajectory.npz'], 'Lineage trajectory changed')
        with np.load(path, allow_pickle=False) as z:
            np.testing.assert_array_equal(obs[ids], z['observation'])
            np.testing.assert_array_equal(target[ids], z['action'])
        if row.get('augmented'):
            prefix = row['student_prefix_steps']
            require(row['split'] == 'train' and row['supervised_frames'] == len(ids)-prefix,
                    'Invalid recovery lineage')
            require(np.all(importance[ids[:prefix]] == 0) and np.all(importance[ids[prefix:]] == 1),
                    'Recovery prefix must be zero-loss and teacher suffix supervised')
        else:
            require(np.all(importance[ids] == 1), 'Pure demonstration weights changed')
    rows = state['fits']
    require(len(rows) == 75 and len({r['name'] for r in rows}) == 75, 'Expected 75 unique fit jobs')
    require(all(r['status'] == 'complete' for r in rows), 'Incomplete fit retained in roster')
    groups = defaultdict(list)
    schedules = defaultdict(set)
    checked = []
    for row in rows:
        out = Path(row['output'])
        info = read(out / 'TRAINING_COMPLETE.json')
        require(sha(out / 'TRAINING_COMPLETE.json') == row['metadata_sha256'], 'Changed fit receipt')
        require(sha(out / 'checkpoint.npz') == row['checkpoint_sha256'] == info['checkpoint_sha256'], 'Changed fit checkpoint')
        require(info.get('data_sha256', info.get('training_data_sha256')) == data_sha, 'Fit used different data')
        require(info['fields'] == FIELDS and info['seed'] == row['seed'], 'Wrong observation fields or seed')
        for path, digest in info['source_sha256'].items():
            require(source['source_hashes'].get(path) == digest, 'Candidate source drift')
        with np.load(out / 'exported_replay.npz', allow_pickle=False) as z:
            prediction = z['prediction']
            np.testing.assert_array_equal(z['episode'], episode)
            require(prediction.shape == target.shape and np.isfinite(prediction).all(), 'Invalid exported actions')
            mse = float(np.mean((prediction[~train] - target[~train]) ** 2))
        if row['family'] == 'esn_ridge':
            candidates = info['candidates']
            grid = {(r['rho'], r['input_gain'], r['ridge']) for r in candidates}
            require(len(candidates) == 12 and grid == {(r, g, l) for r in (.5, .8) for g in (.08, .25, .6) for l in (.001, .1)}, 'Wrong ESN grid')
            for candidate in candidates:
                require(sha(out / (candidate['name'] + '.npz')) == candidate['checkpoint_sha256'], 'Changed ESN candidate')
            require(info['selected']['holdout_mse'] == min(c['holdout_mse'] for c in candidates), 'Wrong ESN selection')
            expected_mse = info['selected']['holdout_mse']
        else:
            require(info['updates'] == info['selected_update'] == UPDATES, 'Wrong neural update/selection budget')
            require(info['checkpoint_selection'] == 'final' and info['target'] == 'requested', 'Wrong neural objective')
            require(info['precision'] == 'float64' and info['width'] == 128, 'Wrong neural configuration')
            require(info['learning_rate'] in RATES and info['weight_decay'] in DECAYS, 'Wrong neural grid')
            require(info['action_delta_weight'] == info['drift_weight'] == 0, 'Unregistered temporal objective')
            require(info['numpy_torch_max_abs'] <= 5e-5, 'Failed neural export parity')
            require(sha(out / 'exported_replay.npz') == info['exported_replay_sha256'], 'Changed neural replay')
            require(sha(out / 'schedule.json') == info['schedule_sha256'], 'Changed exposure schedule')
            schedules[row['seed']].add(info['schedule_sha256'])
            expected_mse = info['groups']['real_identity_validation']['action_mse']
        require(abs(mse - expected_mse) <= 1e-12, 'Reported validation loss does not match saved actions')
        groups[(row['family'], row['seed'])].append((expected_mse, row['name'], info))
        checked.append(dict(name=row['name'], validation_mse=mse, checkpoint_sha256=row['checkpoint_sha256']))
    expected_groups = {(f, s) for f in ('esn_ridge', 'mlp_scratch', 'rnn_scratch') for s in SEEDS}
    require(set(groups) == expected_groups, 'Missing family/seed')
    require(all(len(v) == 1 for v in schedules.values()) and set(schedules) == set(SEEDS), 'Unequal neural exposure schedules')
    for (family, seed), candidates in groups.items():
        require(len(candidates) == (1 if family == 'esn_ridge' else 12), 'Missing candidates')
        if family != 'esn_ridge':
            require({(c[2]['learning_rate'], c[2]['weight_decay']) for c in candidates}
                    == {(r, d) for r in RATES for d in DECAYS}, 'Incomplete neural grid')
    require(len(lock['models']) == 9, 'Wrong final model count')
    require(Counter((m['family'], m['seed']) for m in lock['models']) == Counter({p: 1 for p in expected_groups}), 'Duplicate/missing selected models')
    esn = load_class(physics_source, 'office_vmc_memory_esn_20260927.py', 'OfficeVMCMemoryESN')
    neural = load_class(physics_source, 'office_mlp_rnn_20261002.py', 'OfficeMLPRNN')
    replays = []
    for model in lock['models']:
        selection = min(groups[(model['family'], model['seed'])], key=lambda x: (x[0], x[1]))
        require(model['selected_trial'] == selection[1] and model['validation_mse'] == selection[0], 'Model lock not validation minimum')
        checkpoint = Path(model['checkpoint'])
        require(sha(checkpoint) == model['checkpoint_sha256'], 'Selected checkpoint changed')
        with np.load(checkpoint, allow_pickle=False) as z:
            require('state_delta_readout' not in z.files or not bool(z['state_delta_readout']), 'Unsupported state-delta extension')
        actor = (esn if model['family'] == 'esn_ridge' else neural)(checkpoint)
        with np.load(checkpoint.parent / 'exported_replay.npz', allow_pickle=False) as z:
            expected = z['prediction']
        maximum = 0.
        previous = None
        for i, (eid, observation) in enumerate(zip(episode, obs)):
            if eid != previous:
                actor.reset()
                previous = eid
            action = actor.act(observation)
            require(np.isfinite(action).all(), 'Nonfinite frozen actor output')
            maximum = max(maximum, float(np.max(np.abs(action - expected[i]))))
        require(np.isfinite(maximum) and maximum <= 1e-12, 'Frozen actor differs from fitting export')
        replays.append(dict(name=model['name'], observations=len(obs), max_abs_error=maximum))
    return dict(schema='sii-special-fit-audit-v1', status='passed', audited_utc=now(),
                dataset_sha256=data_sha, model_lock_sha256=sha(root / 'MODEL_LOCK.json'),
                candidate_jobs=checked, frozen_actor_replays=replays,
                same_neural_schedule_sha256={str(k): next(iter(v)) for k, v in schedules.items()},
                frozen_actor_source_sha256={name: sha(physics_source / 'scripts' / name) for name in (
                    'office_vmc_memory_esn_20260927.py', 'office_mlp_rnn_20261002.py')},
                scope='All30 data reconstruction, all75 fit receipts/108 candidates, identical per-seed neural exposures, validation-only selection, all9 old-runtime actor replays. No test episodes or independent dynamics integration.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--physics-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(args.root.resolve(), args.physics_source.resolve())
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(status=result['status'], models=len(result['frozen_actor_replays']))))
