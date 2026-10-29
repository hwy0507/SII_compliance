"""Check leakage guards and compare actual v8 statistics, without training."""
import argparse
import copy
import json
from pathlib import Path

import numpy as np

from audit_special_coverage_dataset_20261029 import audit, sha, validate_partition


def check(output):
    if output.exists():
        raise FileExistsError(output)
    root = Path(__file__).resolve().parents[1]
    # In-memory identity fixture exercises variable lengths only. It is never
    # written as a physical dataset, qualification receipt, or training input.
    rows = []
    for scene in ('rod', 'ball', 'corner'):
        for i in range(10):
            index = len(rows)
            rows.append(dict(episode=index, id=f'{scene}{i}', scene=scene,
                             split='train' if i < 8 else 'validation',
                             frames=index + 1, folder=f'/synthetic/{scene}{i}'))
    ep = np.concatenate([np.full(r['frames'], r['episode']) for r in rows])
    n = len(ep)
    values = dict(episode=ep, train=np.concatenate([np.full(r['frames'], r['split'] == 'train') for r in rows]),
                  physical_execution=np.ones(n, dtype=bool), observation=np.zeros((n, 48)),
                  requested_teacher_action=np.zeros((n, 7)))
    meta = dict(schema='sii-vmc-special-scenes-dataset-v2', lineage=rows, frames=n,
                training_identities=[r['id'] for r in rows if r['split'] == 'train'],
                validation_identities=[r['id'] for r in rows if r['split'] == 'validation'])
    assert len(validate_partition(meta, values)) == 24
    mutations = {
        'validation_row_marked_train': lambda m, v: v['train'].__setitem__(np.flatnonzero(v['episode'] == 8)[0], True),
        'unclaimed_identity': lambda m, v: v['episode'].__setitem__(0, 99),
        'duplicate_folder': lambda m, v: m['lineage'][1].update(folder=m['lineage'][0]['folder']),
        'wrong_frame_count': lambda m, v: m['lineage'][0].update(frames=2),
        'empty_episode': lambda m, v: m['lineage'][0].update(frames=0),
        'nonphysical_row': lambda m, v: v['physical_execution'].__setitem__(0, False),
        'wrong_named_split': lambda m, v: m['training_identities'].__setitem__(0, 'ball8'),
        'integer_split_flag': lambda m, v: v.update(train=v['train'].astype(int)),
        'wrong_action_shape': lambda m, v: v.update(requested_teacher_action=np.zeros((n, 6))),
    }
    rejected = []
    for name, mutate in mutations.items():
        m, v = copy.deepcopy(meta), copy.deepcopy(values)
        mutate(m, v)
        try:
            validate_partition(m, v)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError('Malformed dataset accepted: ' + name)
    regpath = root/'outputs/nonrl_ball_coverage_probe_20261029_v5/REGISTRATION.json'
    reg = json.loads(regpath.read_text())
    for name, digest in reg['source_sha256'].items():
        assert sha(root/name) == digest, name
    output.mkdir(parents=True)
    actual = audit(root/'outputs/special_scene_retrain_20261029_v8', output/'V8_ACTUAL_COVERAGE.json')
    previous_path = root.parent.parent/'docs/evidence/NONRL_INTENT_RECOVERY_20261029/V8_TRAIN_DIRECTION_COVERAGE.json'
    previous = json.loads(previous_path.read_text())
    for key in ('training_data_sha256', 'metadata_sha256', 'rows', 'scenes', 'excluded_validation_identities'):
        assert actual[key] == previous[key], key
    assert actual['train_frames'] == 12600
    report = dict(status='passed', synthetic_variable_duration_frames=n,
                  synthetic_only='In-memory partition guard fixtures, not physical/fitting evidence',
                  rejected=rejected, actual_train_frames=actual['train_frames'],
                  actual_statistics_exactly_equal_to_previous=True,
                  actual_report_sha256=sha(output/'V8_ACTUAL_COVERAGE.json'),
                  previous_report_sha256=sha(previous_path),
                  v5_bound_source_count=len(reg['source_sha256']),
                  v5_registration_sha256=sha(regpath),
                  sources={p.name: sha(p) for p in [Path(__file__), Path(__file__).with_name('audit_special_coverage_dataset_20261029.py')]},
                  limitation='No new coverage collection, training, or evidence of repaired closed-loop performance.')
    with (output/'CHECK.json').open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    check(parser.parse_args().output.resolve())
