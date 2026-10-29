"""Describe physical train-only directional/load exposure, without fitting.

Bins are descriptive, not acceptance gates. No validation/test observations
are summarized, and no source trajectory or current model is modified.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import read, sha, write


def describe(obs, action):
    direction = obs[:, 45:48]
    load = np.max(np.abs(obs[:, 39:45] / [8., 8., 8., 1., 1., 1.]), axis=1)
    bins = {}
    for axis, name in enumerate('XYZ'):
        for sign in (-1, 1):
            mask = direction[:, axis] * sign >= .8
            bins[f'{name}{sign:+d}'] = dict(
                frames=int(mask.sum()),
                estimated_load_over_0_1_frames=int(np.sum(mask & (load > .1))),
                estimated_load_below_1e_6_frames=int(np.sum(mask & (load <= 1e-6))))
    # An independent scalar count checks every bin, including empty ones.
    for axis, name in enumerate('XYZ'):
        for sign in (-1, 1):
            row = bins[f'{name}{sign:+d}']
            assert row['frames'] == sum(float(x[axis]) * sign >= .8 for x in direction)
            assert row['estimated_load_over_0_1_frames'] == sum(
                float(x[axis]) * sign >= .8 and float(l) > .1 for x, l in zip(direction, load))
    return dict(frames=len(obs), direction_min=direction.min(0).tolist(),
                direction_max=direction.max(0).tolist(),
                distinct_directions_at_6_decimals=len(np.unique(np.round(direction, 6), axis=0)),
                bins=bins, position_error_min_m=obs[:, 20:23].min(0).tolist(),
                position_error_max_m=obs[:, 20:23].max(0).tolist(),
                requested_action_rms=np.sqrt(np.mean(action**2, axis=0)).tolist())


def audit(training, output):
    assert not output.exists(), 'Preserve previous evidence'
    data = training / 'data/training_data.npz'
    metadata_path = training / 'data/DATA_COMPLETE.json'
    metadata = read(metadata_path)
    assert sha(data) == metadata['training_data_sha256']
    rows, scenes = [], {}
    with np.load(data, allow_pickle=False) as z:
        for entry in metadata['lineage']:
            if entry['split'] != 'train':
                continue
            mask = z['episode'] == entry['episode']
            assert mask.sum() == entry['frames'] and np.all(z['train'][mask])
            obs = z['observation'][mask]
            action = z['requested_teacher_action'][mask]
            assert np.isfinite(obs).all() and np.isfinite(action).all()
            trajectory = Path(entry['folder']) / 'trajectory.npz'
            assert sha(trajectory) == entry['hashes']['trajectory.npz']
            with np.load(trajectory, allow_pickle=False) as raw:
                np.testing.assert_array_equal(obs, raw['observation'])
                np.testing.assert_array_equal(action, raw['action'])
            rows.append(dict(id=entry['id'], scene=entry['scene'],
                             trajectory_sha256=sha(trajectory), **describe(obs, action)))
            scenes.setdefault(entry['scene'], []).append((obs, action))
    assert Counter(r['scene'] for r in rows) == Counter(rod=8, ball=8, corner=8)
    assert sum(r['frames'] for r in rows) == 12600
    report = dict(status='complete_train_only_direction_description',
        created_utc=datetime.now(timezone.utc).isoformat(),
        training_data_sha256=sha(data), metadata_sha256=sha(metadata_path),
        source_sha256=sha(Path(__file__)), rows=rows,
        excluded_validation_identities=metadata['validation_identities'],
        scenes={s: describe(np.concatenate([a for a, _ in pairs]),
                            np.concatenate([a for _, a in pairs])) for s, pairs in scenes.items()},
        limitation='Descriptive directional bins (component >=0.8) and scaled estimated-load bins; '
        'not contact labels, qualification gates or a causal proof. All 24 train identities and their '
        'exact physical observations/actions checked. Validation/test data not summarized; '
        'no new physics, fitting, model selection, or claim of repair.')
    write(output, report)
    print({s: v['bins'] for s, v in report['scenes'].items()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--training', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit(args.training.resolve(), args.output.resolve())
