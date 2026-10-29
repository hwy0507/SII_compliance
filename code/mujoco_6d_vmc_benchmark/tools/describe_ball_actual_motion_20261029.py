"""Describe measured free-ball carry/recovery, not only commanded targets.

Read-only saved-trajectory analysis. No dynamics, fitting, new success gates or
claim that hand/object co-motion proves a maintained contact grasp.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

from audit_special_coverage_dataset_20261029 import sha


def describe(time, stage, hand, object_position, target):
    n = len(time)
    arrays = (time, stage, hand, object_position, target)
    if n < 2 or stage.shape != (n,) or any(a.shape != (n, 3) for a in arrays[2:]):
        raise ValueError('Invalid physical trace shapes')
    if not all(np.isfinite(a).all() for a in arrays):
        raise ValueError('Nonfinite physical trace')
    if (not np.all(stage == stage.astype(int)) or np.any(np.diff(stage) < 0)
            or np.any((stage < 0) | (stage > 5))):
        raise ValueError('Require original six-stage free-ball task')
    np.testing.assert_allclose(time, .04 * np.arange(1, n + 1), rtol=0, atol=1e-8)
    rows = []
    for s, name in ((0, 'approach'), (3, 'loaded_lift'), (4, 'carry'), (5, 'recovery')):
        indices = np.flatnonzero(stage == s)
        if not len(indices):
            rows.append(dict(stage=s, name=name, frames=0, reached=False))
            continue
        first, last = int(indices[0]), int(indices[-1])
        # Include the last saved point of the previous stage when available.
        # The true t=0 position is not saved, so approach misses its first 40ms.
        anchor = max(0, first - 1)
        h_delta, o_delta = hand[last] - hand[anchor], object_position[last] - object_position[anchor]
        relative = object_position[anchor:last + 1] - hand[anchor:last + 1]
        commanded = target[first] - target[anchor] if first else None
        length = float(np.linalg.norm(commanded)) if commanded is not None else 0.
        direction = commanded / length if length > 1e-12 else None
        rows.append(dict(stage=s, name=name, frames=len(indices), reached=True,
            anchor_time_s=float(time[anchor]), first_time_s=float(time[first]), last_time_s=float(time[last]),
            commanded_goal_displacement_m=None if commanded is None else commanded.tolist(),
            hand_displacement_m=h_delta.tolist(), object_displacement_m=o_delta.tolist(),
            hand_projection_on_goal_displacement_m=None if direction is None else float(h_delta @ direction),
            object_projection_on_goal_displacement_m=None if direction is None else float(o_delta @ direction),
            relative_position_drift_max_m=float(np.max(np.linalg.norm(relative-relative[0], axis=1))),
            hand_object_distance_min_m=float(np.min(np.linalg.norm(relative, axis=1))),
            hand_object_distance_max_m=float(np.max(np.linalg.norm(relative, axis=1))),
            object_height_range_m=[float(object_position[first:last+1, 2].min()),
                                   float(object_position[first:last+1, 2].max())],
            terminal_hand_target_error_m=float(np.linalg.norm(hand[last]-target[last]))))
    return rows


def inspect(folder, expected=None):
    names = ('legacy.npz', 'legacy.json', 'trajectory.npz', 'execution.json',
             'DEMONSTRATION_QUALIFICATION.json', 'SOURCE_HASHES.json')
    hashes = {name: sha(folder/name) for name in names}
    execution = json.loads((folder/'execution.json').read_text())
    qualification = json.loads((folder/'DEMONSTRATION_QUALIFICATION.json').read_text())
    legacy = json.loads((folder/'legacy.json').read_text())
    if execution['scene'] != 'ball' or execution['status'] != 'complete' or execution['controller_role'] != 'teacher':
        raise ValueError('Only completed actual free-ball teacher traces')
    if execution['trajectory_sha256'] != hashes['trajectory.npz']:
        raise ValueError('Changed teacher trajectory')
    for name in ('execution.json', 'legacy.json', 'trajectory.npz', 'SOURCE_HASHES.json'):
        if qualification['input_hashes'][name] != hashes[name]:
            raise ValueError('Stale qualification input: '+name)
    if expected is not None:
        for name in ('trajectory.npz', 'execution.json', 'DEMONSTRATION_QUALIFICATION.json'):
            if expected['hashes'][name] != hashes[name]:
                raise ValueError('Changed training lineage: '+name)
    with np.load(folder/'trajectory.npz', allow_pickle=False) as z:
        time = z['time'].copy()
    with np.load(folder/'legacy.npz', allow_pickle=False) as z:
        np.testing.assert_array_equal(time, z['time'])
        phases = describe(time, z['stage'], z['position'], z['object_position'], z['target'])
    if any(sha(folder/name) != digest for name, digest in hashes.items()):
        raise ValueError('Trace changed while reading')
    return dict(folder=str(folder), identity=None if expected is None else expected['id'],
        input_sha256=hashes, source_sha256=json.loads((folder/'SOURCE_HASHES.json').read_text()),
        qualification_status=qualification['status'], phases=phases,
        original_final_stage=legacy['final_stage'], original_task_success=legacy['success'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    choice = p.add_mutually_exclusive_group(required=True)
    choice.add_argument('--training', type=Path)
    choice.add_argument('--folders', type=Path, nargs='+')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    metadata_hash = None
    if args.training:
        metadata_path = args.training/'data/DATA_COMPLETE.json'
        metadata_hash = sha(metadata_path)
        metadata = json.loads(metadata_path.read_text())
        if sha(args.training/'data/training_data.npz') != metadata['training_data_sha256']:
            raise ValueError('Training dataset changed')
        entries = [e for e in metadata['lineage'] if e['scene']=='ball' and e['split']=='train']
        if len(entries) != 8 or len({e['id'] for e in entries}) != 8:
            raise ValueError('Require eight distinct train ball identities')
        rows = [inspect(Path(e['folder']), e) for e in entries]
        if sha(metadata_path) != metadata_hash:
            raise ValueError('Training metadata changed')
    else:
        rows = [inspect(folder.resolve()) for folder in args.folders]
    report = dict(status='complete_saved_ball_motion_description',
        created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=sha(Path(__file__)),
        metadata_sha256=metadata_hash, rows=rows,
        limitation='Measured saved 25Hz hand/object positions, not requested target motion alone. '
        'Relative world-position drift includes rotation and is not a slip/contact-force certificate. '
        'No dynamics replay, new qualification gate, fitting, validation/test statistics or claim of repair. '
        'Approach begins at the first saved 40ms point. legacy.npz is snapshot-hashed here; '
        'its positions are not independently reconstructed from MuJoCo state by this tool.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as f:
        json.dump(report, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(dict(status=report['status'], episodes=len(rows), output=str(args.output))))


if __name__ == '__main__':
    main()
