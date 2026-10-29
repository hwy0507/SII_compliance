"""Describe actual train exposure for variable-duration three-scene datasets.

No fitting, simulation, validation statistics, new qualification threshold, or
claim that broader marginal exposure establishes joint support/learnability.
Keeps the existing v8 descriptive bins and reports their per-identity counts.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_v8_train_direction_coverage_20261029 import describe


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def validate_partition(metadata, values):
    """Reject missing/duplicate/leaking identities before computing statistics."""
    rows = metadata['lineage']
    if any(type(r['frames']) is not int or r['frames'] <= 0 for r in rows):
        raise ValueError('Every identity must have a positive integer frame count')
    if metadata['schema'] != 'sii-vmc-special-scenes-dataset-v2':
        raise ValueError('Expected the common physical dataset schema v2')
    if len(rows) != 30 or len({r['episode'] for r in rows}) != 30 or len({r['id'] for r in rows}) != 30:
        raise ValueError('Require 30 distinct episode IDs and names')
    if len({str(Path(r['folder']).resolve()) for r in rows}) != 30:
        raise ValueError('Source folders must be distinct')
    expected = Counter({(s, split): n for s in ('rod', 'ball', 'corner')
                        for split, n in [('train', 8), ('validation', 2)]})
    if Counter((r['scene'], r['split']) for r in rows) != expected:
        raise ValueError('Require eight train and two validation identities per scene')
    for split, key in [('train', 'training_identities'), ('validation', 'validation_identities')]:
        expected_names = [r['id'] for r in rows if r['split'] == split]
        if Counter(metadata[key]) != Counter(expected_names):
            raise ValueError('Named split differs from lineage')
    n = len(values['episode'])
    if n != metadata['frames'] or n != sum(r['frames'] for r in rows):
        raise ValueError('Frame count differs from actual registered lineage')
    shapes = {'observation': (n, 48), 'requested_teacher_action': (n, 7),
              'episode': (n,), 'train': (n,), 'physical_execution': (n,)}
    if any(values[k].shape != shape for k, shape in shapes.items()):
        raise ValueError('Dataset array shapes differ')
    if values['train'].dtype != np.bool_ or values['physical_execution'].dtype != np.bool_:
        raise ValueError('Require explicit boolean split/physical flags')
    if values['episode'].dtype.kind not in 'iu' or not values['physical_execution'].all():
        raise ValueError('Require integer identities and real physical rows')
    if set(np.unique(values['episode'])) != {r['episode'] for r in rows}:
        raise ValueError('Unclaimed or missing episode rows')
    for r in rows:
        mask = values['episode'] == r['episode']
        if mask.sum() != r['frames'] or not np.all(values['train'][mask] == (r['split'] == 'train')):
            raise ValueError('Per-episode count or split leakage')
    return [r for r in rows if r['split'] == 'train']


def audit(training, output):
    if output.exists():
        raise FileExistsError(output)
    data = training / 'data/training_data.npz'
    meta_path = training / 'data/DATA_COMPLETE.json'
    metadata = json.loads(meta_path.read_text())
    data_hash, meta_hash = sha(data), sha(meta_path)
    if data_hash != metadata['training_data_sha256']:
        raise ValueError('Dataset hash mismatch')
    with np.load(data, allow_pickle=False) as z:
        values = {k: z[k] for k in ('observation', 'requested_teacher_action',
                                   'episode', 'train', 'physical_execution')}
    entries = validate_partition(metadata, values)
    rows, scenes = [], {}
    for entry in entries:
        mask = values['episode'] == entry['episode']
        obs, action = values['observation'][mask], values['requested_teacher_action'][mask]
        if not np.isfinite(obs).all() or not np.isfinite(action).all():
            raise ValueError('Nonfinite train samples')
        trajectory = Path(entry['folder']) / 'trajectory.npz'
        digest = sha(trajectory)
        if digest != entry['hashes']['trajectory.npz']:
            raise ValueError('Changed physical train trajectory')
        with np.load(trajectory, allow_pickle=False) as z:
            np.testing.assert_array_equal(obs, z['observation'])
            np.testing.assert_array_equal(action, z['action'])
            np.testing.assert_allclose(z['time'], .04 * np.arange(1, len(obs) + 1), rtol=0, atol=1e-8)
        if sha(trajectory) != digest:
            raise ValueError('Train source changed during read')
        rows.append(dict(id=entry['id'], scene=entry['scene'], trajectory_sha256=digest,
                         **describe(obs, action)))
        scenes.setdefault(entry['scene'], []).append((obs, action))
    if sha(data) != data_hash or sha(meta_path) != meta_hash:
        raise ValueError('Dataset changed during analysis')
    report = dict(status='complete_variable_duration_train_direction_description',
        created_utc=datetime.now(timezone.utc).isoformat(), training_data_sha256=data_hash,
        metadata_sha256=meta_hash, source_sha256=sha(Path(__file__)),
        descriptive_kernel_sha256=sha(Path(__file__).with_name('audit_v8_train_direction_coverage_20261029.py')),
        train_frames=sum(r['frames'] for r in rows), rows=rows,
        excluded_validation_identities=metadata['validation_identities'],
        scenes={s: describe(np.concatenate([a for a, _ in pairs]),
                            np.concatenate([a for _, a in pairs])) for s, pairs in scenes.items()},
        limitation='Actual train-only canonical directions and scaled estimated-load bins, not contact '
        'labels or qualification gates. Validation flags/counts checked, validation statistics excluded. '
        'No new physics, fitting, test-based selection, or proof of sufficient joint coverage. '
        'Physical qualification remains the separate mandatory collection/builder responsibility.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'status': report['status'], 'train_frames': report['train_frames'],
                      'output': str(output)}, ensure_ascii=False))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--training', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit(args.training.resolve(), args.output.resolve())
