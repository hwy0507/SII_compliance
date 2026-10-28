"""Read-only data/learning diagnosis for the frozen non-RL cohort.

Writes a new evidence directory; never modifies datasets, models or rollouts.
Training loss points are last-minibatch values, not epoch means.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--matrix', type=Path, help='Completed new matrix, used diagnostically only')
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    dataset = a.parent / 'data/training_data.npz'
    metadata = a.parent / 'data/DATA_COMPLETE.json'
    meta = read(metadata)
    assert sha(dataset) == meta['training_data_sha256']
    with np.load(dataset, allow_pickle=False) as z:
        obs, ep, train, target, importance = [z[k] for k in (
            'observation', 'episode', 'train', 'requested_teacher_action', 'importance')]
        assert bool(z['physical_execution'].all())
    assert all(np.isfinite(v).all() for v in (obs, target, importance))
    assert np.all(importance > 0)
    train_ids, val_ids = set(ep[train].tolist()), set(ep[~train].tolist())
    assert not train_ids & val_ids
    # Whole trajectory digest catches duplicate content across different IDs.
    trajectory_hashes = {}
    for e in np.unique(ep):
        mask = ep == e
        digest = hashlib.sha256(obs[mask].tobytes() + target[mask].tobytes()).hexdigest()
        trajectory_hashes.setdefault(digest, []).append(int(e))
    cross_split_duplicates = [v for v in trajectory_hashes.values()
                              if train_ids.intersection(v) and val_ids.intersection(v)]
    assert not cross_split_duplicates
    # Diagnostic only: force estimate is actor input, not a true contact label.
    load = np.linalg.norm(obs[:, 39:42], axis=1)
    sets = {'all': np.ones(len(ep), dtype=bool), 'force_estimate_gt_1N': load > 1,
            'force_estimate_le_1N': load <= 1}
    n = len(ep)
    output = {
        'dataset_sha256': sha(dataset), 'metadata_sha256': sha(metadata),
        'model_lock_sha256': sha(a.parent / 'MODEL_LOCK.json'),
        'frames': n, 'train_episodes': len(train_ids), 'validation_episodes': len(val_ids),
        'cross_split_duplicate_trajectories': cross_split_duplicates,
        'lineage_task_successes': sum(bool(x['task_success']) for x in meta['lineage']),
        'lineage_strict_successes': sum(bool(x['strict_success']) for x in meta['lineage']),
        'teacher_configs': sorted(set(x['teacher_config_sha256'] for x in meta['lineage'])),
        'data_limitations': meta['limitations'],
        'zero_target_frame_fraction': float(np.mean(np.max(np.abs(target), axis=1) <= 1e-6)),
        'models': [],
        'interpretation': 'Offline imitation diagnostics; no proof of closed-loop success or convergence. Force estimate strata are not actual human contact masks.',
    }
    histories = []
    for model in read(a.parent / 'MODEL_LOCK.json')['models']:
        if model['name'] not in ('esn_gradient_s2026101301', 'rnn_scratch_s2026101301', 'mlp_scratch_s2026101301'):
            continue
        checkpoint = Path(model['checkpoint'])
        assert sha(checkpoint) == model['checkpoint_sha256']
        folder = checkpoint.parent
        history = read(folder / 'history.json')
        with np.load(folder / 'exported_replay.npz', allow_pickle=False) as z:
            prediction = z['prediction']; assert np.array_equal(z['episode'], ep)
        assert prediction.shape == target.shape
        error = (prediction - target) ** 2
        row = {'name': model['name'], 'checkpoint_sha256': sha(checkpoint),
               'history_sha256': sha(folder / 'history.json'),
               'replay_sha256': sha(folder / 'exported_replay.npz'),
               'selected_update': model['selected_update'], 'history': history,
               'last_2k_validation_relative_change': history[-1]['validation_mse'] / history[-3]['validation_mse'] - 1,
               'strata': {}}
        for split, split_mask in [('train', train), ('validation', ~train)]:
            row['strata'][split] = {}
            for name, mask in sets.items():
                use = mask & split_mask
                row['strata'][split][name] = {'frames': int(use.sum()),
                    'mse': float(error[use].mean()) if use.any() else None,
                    'mse_by_action': error[use].mean(0).tolist() if use.any() else None}
        assert np.isclose(row['strata']['validation']['all']['mse'], model['validation_mse'], atol=1e-8, rtol=0)
        output['models'].append(row)
        histories.append((model['name'], history))
    if a.matrix:
        from scipy.spatial import cKDTree
        report = read(a.matrix / 'REPORT.json')
        assert report['status'] == 'complete'
        fields = sorted(set(range(14, 17)) | set(range(20, 23)) | set(range(26, 29)) | set(range(39, 48)))
        scale = np.maximum(obs[train][:, fields].std(0), 0.005)
        tree = cKDTree(obs[train][:, fields] / scale)
        validation_distance = tree.query(obs[~train][:, fields] / scale, workers=1)[0]
        threshold = float(np.quantile(validation_distance, .95))
        coverage = {'fields': fields, 'train_only_scale': scale.tolist(),
                    'validation_distance_p95': threshold,
                    'definition': 'Nearest train observation Euclidean distance in 18 train-standardized actor fields; ignores history and is descriptive, not a safety gate.',
                    'matrix_sha256': sha(a.matrix / 'REPORT.json'), 'methods': []}
        for model in output['models']:
            distances, stages, receipts = [], [], []
            for row in report['rows']:
                if row['method'] != model['name']:
                    continue
                trace = Path(row['run']) / 'rollout.npz'
                assert sha(trace) == row['trace_sha256']
                with np.load(trace, allow_pickle=False) as z:
                    distances.extend(tree.query(z['observation'][:, fields] / scale, workers=1)[0].tolist())
                    stages.append(int(z['stage'][-1]))
                receipts.append({'condition': row['condition'], 'trace_sha256': sha(trace)})
            values = np.asarray(distances)
            unique, counts = np.unique(stages, return_counts=True)
            coverage['methods'].append({'name': model['name'], 'frames': len(values),
                'distance_p50': float(np.median(values)), 'distance_p95': float(np.quantile(values, .95)),
                'fraction_above_teacher_validation_p95': float(np.mean(values > threshold)),
                'terminal_stage_counts': dict(zip(map(str, unique.tolist()), counts.tolist())),
                'receipts': receipts})
        output['coverage'] = coverage
    (a.output / 'DIAGNOSIS.json').write_text(json.dumps(output, indent=2, ensure_ascii=False) + '\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for name, history in histories:
        label = name.replace('_s2026101301', '')
        axes[0].semilogy([h['update'] for h in history], [h['validation_mse'] for h in history], 'o-', label=label)
        points = [h for h in history if 'last_train_loss' in h]
        axes[1].semilogy([h['update'] for h in points], [h['last_train_loss'] for h in points], 'o-', label=label)
    axes[0].set_title('Full validation action MSE')
    axes[1].set_title('Last minibatch loss (not epoch average)')
    for ax in axes:
        ax.set_xlabel('Optimizer updates'); ax.grid(alpha=.25); ax.legend()
    fig.tight_layout(); fig.savefig(a.output / 'learning_diagnostics.png', dpi=180)
    plt.close(fig)
    print(json.dumps({k:v for k,v in output.items() if k != 'models'}, indent=2))


if __name__ == '__main__':
    main()
