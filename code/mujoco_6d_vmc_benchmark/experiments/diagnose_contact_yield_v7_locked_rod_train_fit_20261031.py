"""Audit locked models' requested-action fit on the exact rod_00 train episode."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from current_student_policy_20260921 import load_current

FIT = ROOT / 'outputs/contact_yield_recovery_retrain_20261030_v7'
TEACHER = ROOT / 'outputs/contact_yield_scrape_collection_20261030_v1/rod_00/rod'
DEST = ROOT.parents[1] / 'docs/evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_V7_LOCKED_ROD_TRAIN_FIT_20261031.json'
WINDOWS = ((0., 4.2), (4.2, 4.7), (4.7, 5.), (5., 8.), (8., 12.76))
SEEDS = (2026102801, 2026102802, 2026102803)
FAMILIES = ('esn_ridge', 'rnn_scratch', 'mlp_scratch')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    if DEST.exists():
        raise FileExistsError(f'Preserve prior evidence: {DEST}')
    execution = read(FIT / 'execution.json')
    audit = read(FIT / 'FIT_AUDIT.json')
    lock = read(FIT / 'MODEL_LOCK.json')
    data_meta = read(FIT / 'data/DATA_COMPLETE.json')
    assert execution['status'] == 'complete' and len(execution['fits']) == 75
    assert audit['status'] == 'passed' and lock['status'] == 'frozen'
    assert len(lock['models']) == 9
    data_path = FIT / 'data/training_data.npz'
    assert sha(data_path) == data_meta['training_data_sha256']
    with np.load(data_path, allow_pickle=False) as data:
        ids = np.flatnonzero(data['episode'] == 0)
        train = data['train'][ids]
        observations = data['observation'][ids].copy()
        target = data['requested_teacher_action'][ids].copy()
        importance = data['importance'][ids].copy()
    assert len(ids) == 500 and train.all() and np.all(importance > 0)
    with np.load(TEACHER / 'trajectory.npz', allow_pickle=False) as tape:
        teacher_obs = tape['observation'].copy()
        teacher_action = tape['action'].copy()
        times = tape['time'].copy()
    assert np.array_equal(observations, teacher_obs)
    assert np.array_equal(target, teacher_action)
    assert times.shape == (500,) and np.all(np.isfinite(observations))

    rows = []
    for family in FAMILIES:
        for seed in SEEDS:
            model = next(m for m in lock['models']
                         if m['family'] == family and m['seed'] == seed)
            checkpoint = Path(model['checkpoint'])
            assert sha(checkpoint) == model['checkpoint_sha256']
            actor = load_current(checkpoint)
            actor.reset()
            prediction = np.asarray([actor.act(obs) for obs in observations])
            error = prediction - target
            windows = []
            for start, end in WINDOWS:
                mask = (times >= start) & (times < end)
                values = error[mask]
                windows.append(dict(
                    start_s=start, end_s=end, frames=int(mask.sum()),
                    requested_action_rmse=float(np.sqrt(np.mean(values ** 2))),
                    per_action_channel_rmse=np.sqrt(np.mean(values ** 2, axis=0)).tolist(),
                    max_abs_error=float(np.max(np.abs(values)))) )
            anchor = int(np.argmin(np.abs(times - 4.68)))
            rows.append(dict(
                family=family, seed=seed, selected_trial=model['selected_trial'],
                checkpoint_sha256=model['checkpoint_sha256'],
                full_episode_rmse=float(np.sqrt(np.mean(error ** 2))),
                windows=windows,
                at_4p68=dict(time_s=float(times[anchor]),
                             teacher_action=target[anchor].tolist(),
                             model_action=prediction[anchor].tolist(),
                             error=error[anchor].tolist())))

    result = dict(
        schema='sii-contact-yield-v7-locked-rod-training-fit-v1',
        status='complete_locked_model_train_sequence_replay',
        dataset_sha256=data_meta['training_data_sha256'],
        data_metadata_sha256=sha(FIT / 'data/DATA_COMPLETE.json'),
        fit_execution_sha256=sha(FIT / 'execution.json'),
        fit_audit_sha256=sha(FIT / 'FIT_AUDIT.json'),
        model_lock_sha256=sha(FIT / 'MODEL_LOCK.json'),
        teacher_episode_sha256=sha(TEACHER / 'trajectory.npz'),
        analyzer_sha256=sha(Path(__file__)),
        exact_training_identity=dict(dataset_episode=0, frames=500,
                                     observations_exactly_match_teacher=True,
                                     requested_action_labels_exactly_match_teacher=True,
                                     all_training_rows_positive_weight=True),
        rows=rows,
        limitations=[
            'This is a training-set fit diagnostic on rod_00, not independent validation or closed-loop evidence.',
            'The locked checkpoints were selected using the registered six pure-teacher validation identities; this analysis does not reselect them.',
            'Requested-action errors do not by themselves predict filter response or physical collision outcomes.',
            'No physics, optimizer update, model selection, or final108 access occurred.'],
        new_physics_steps=0, new_optimizer_updates=0, model_reselection=False)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2,
                               allow_nan=False) + '\n')
    print(DEST)
    print('exact teacher training identity verified:', len(observations), 'frames')
    for row in rows:
        window = next(w for w in row['windows'] if w['start_s'] == 4.2)
        print(row['family'], row['seed'], 'episode RMSE', row['full_episode_rmse'],
              '4.2-4.7 RMSE', window['requested_action_rmse'],
              '4.68 action error', np.round(row['at_4p68']['error'], 6).tolist())


if __name__ == '__main__':
    main()
