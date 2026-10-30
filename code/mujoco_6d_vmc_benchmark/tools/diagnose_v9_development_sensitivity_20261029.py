"""One-step input sensitivity on teacher train/validation histories only.

Synthetic coordinate interventions do not certify physical closed-loop stability.
No test trajectories, fitting, model selection, or physics integration are used.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

from current_student_policy_20260921 import load_current

DATA_SHA = '120173888964ee0545393cd0d2685c794f7aa261626463fa7c10fc981b9c6407'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(values):
    x = np.asarray(values)
    assert len(x) and np.isfinite(x).all()
    return dict(n=len(x), median=float(np.median(x)), p95=float(np.quantile(x, .95)),
                maximum=float(x.max()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--training', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists(), 'Preserve existing evidence'
    lock_path = args.training/'MODEL_LOCK.json'
    data_path = args.training/'data/training_data.npz'
    metadata_path = args.training/'data/DATA_COMPLETE.json'
    assert sha(data_path) == DATA_SHA
    lock = json.loads(lock_path.read_text())
    metadata = json.loads(metadata_path.read_text())
    lineage = {row['episode']: row for row in metadata['lineage']}
    with np.load(data_path, allow_pickle=False) as z:
        obs, episode, train = (z[k].copy() for k in ('observation', 'episode', 'train'))
    assert obs.shape == (15750, 48) and int(train.sum()) == 12600
    # One registered teacher identity per scene/split; deterministic stride.
    chosen = [row for row in metadata['lineage'] if row['id'].endswith(('_00', '_08'))]
    assert len(chosen) == 6 and len(lock['models']) == 9
    interventions = [('position_error_1mm', (20, 21, 22), .001),
                     ('estimated_force_0p1N', (39, 40, 41), .1)]
    rows = []
    for model in lock['models']:
        checkpoint = Path(model['checkpoint'])
        assert sha(checkpoint) == model['checkpoint_sha256']
        actor = load_current(checkpoint)
        for source in chosen:
            ids = np.flatnonzero(episode == source['episode'])
            assert len(ids) == source['frames']
            assert np.all(train[ids] == (source['split'] == 'train'))
            actor.reset()
            measures = {name: dict(delta=[], saturation=[]) for name, _, _ in interventions}
            replay_check = 0.
            for step, index in enumerate(ids):
                ob = obs[index]
                if step % 10 == 0:
                    # Every intervention starts with exactly the same unperturbed
                    # recurrent history. No perturbed state leaks to later frames.
                    baseline = copy.deepcopy(actor).act(ob)
                    np.testing.assert_array_equal(copy.deepcopy(actor).act(ob.copy()), baseline)
                    for name, fields, amount in interventions:
                        for field in fields:
                            for sign in (-1, 1):
                                modified = ob.copy()
                                modified[field] += sign*amount
                                action = copy.deepcopy(actor).act(modified)
                                assert np.isfinite(action).all() and action.shape == (7,)
                                measures[name]['delta'].append(float(np.max(np.abs(action[1:]-baseline[1:]))))
                                measures[name]['saturation'].append(bool(np.any(np.abs(action[1:]) >= .999)))
                actual = actor.act(ob)
                if step % 10 == 0:
                    replay_check = max(replay_check, float(np.max(np.abs(actual-baseline))))
            assert replay_check == 0
            rows.append(dict(method=model['name'], family=model['family'], seed=model['seed'],
                teacher_identity=source['id'], scene=source['scene'], split=source['split'],
                frames=len(ids), checkpoint_sha256=sha(checkpoint), clone_replay_error=replay_check,
                interventions={name: dict(residual_action_max_abs_change=summary(value['delta']),
                    perturbed_residual_saturation_fraction=float(np.mean(value['saturation'])))
                    for name, value in measures.items()}))
        assert sha(checkpoint) == model['checkpoint_sha256']
        print(model['name'], flush=True)
    assert sha(data_path) == DATA_SHA
    assert len(rows) == 54
    result = dict(status='development_diagnostic_only', dataset_sha256=DATA_SHA,
        model_lock_sha256=sha(lock_path), metadata_sha256=sha(metadata_path),
        diagnostic_source_sha256=sha(Path(__file__)),
        actor_source_sha256={name: sha(Path(__file__).parents[1]/'scripts'/name) for name in
            ('current_student_policy_20260921.py', 'office_vmc_memory_esn_20260927.py', 'office_mlp_rnn_20261002.py')},
        intervention_protocol=interventions, sample_stride=10,
        caveats=['Single-coordinate synthetic interventions, not dynamically consistent states.',
                 'One-step policy sensitivity is not closed-loop stability or a causal attribution.',
                 'Saturation includes pre-existing saturation; it is not a newly-induced rate.',
                 'Normalized requested actions before the common filter, not physical torques.',
                 'No refit or parameter selection; no unseen-test inputs consumed.'], rows=rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
