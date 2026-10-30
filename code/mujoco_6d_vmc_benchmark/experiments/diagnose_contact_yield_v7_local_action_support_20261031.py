"""Measure local teacher-label support along saved v7 rod MLP rollouts.

This is a descriptive nearest-neighbor analysis only. It performs no physics,
fitting, replay, model selection, gate change, or isolated-test access.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIT = ROOT / 'outputs/contact_yield_recovery_retrain_20261030_v7'
DEV = ROOT / 'outputs/contact_yield_recovery_student_development_20261030_v7'
DEST = ROOT.parents[1] / 'docs/evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_V7_MLP_LOCAL_ACTION_SUPPORT_20261031.json'
FIELDS = np.array([14, 15, 16, 20, 21, 22, 26, 27, 28,
                   39, 40, 41, 42, 43, 44, 45, 46, 47])
SEEDS = (2026102801, 2026102802, 2026102803)
WINDOWS = ((0., 4.2), (4.2, 4.7), (4.7, 5.), (5., 8.), (8., 12.76))
K = 10


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def features(values, scale):
    scaled = np.clip(values[:, FIELDS] / scale, -12., 12.)
    return np.concatenate((scaled, np.abs(scaled)), axis=1)


def query_knn(query, reference, reference_sqnorm, scale, k=K):
    q = features(query, scale)
    indices, distances = [], []
    for start in range(0, len(q), 8):
        block = q[start:start + 8]
        d2 = np.maximum(np.sum(block * block, axis=1)[:, None]
                        + reference_sqnorm[None, :]
                        - 2. * block @ reference.T, 0.)
        idx = np.argpartition(d2, k - 1, axis=1)[:, :k]
        values = np.take_along_axis(d2, idx, axis=1)
        order = np.argsort(values, axis=1)
        indices.append(np.take_along_axis(idx, order, axis=1))
        distances.append(np.sqrt(np.take_along_axis(values, order, axis=1)
                                 / q.shape[1]))
    return np.concatenate(distances), np.concatenate(indices)


def summary(values):
    return dict(p50=float(np.quantile(values, .50)),
                p95=float(np.quantile(values, .95)),
                maximum=float(np.max(values)))


def main():
    if DEST.exists():
        raise FileExistsError(f'Preserve prior evidence: {DEST}')
    fit_exec = read(FIT / 'execution.json')
    audit = read(FIT / 'FIT_AUDIT.json')
    lock = read(FIT / 'MODEL_LOCK.json')
    data_meta = read(FIT / 'data/DATA_COMPLETE.json')
    review = read(DEV / 'REVIEW.json')
    assert fit_exec['status'] == 'complete' and len(fit_exec['fits']) == 75
    assert audit['status'] == 'passed' and lock['status'] == 'frozen'
    assert len(lock['models']) == 9
    assert review['status'] == 'verified_fixed27_development_diagnosis'
    assert review['no_final_test_performed'] is True
    failed = {f'rod_00__special_mlp_scratch_s{seed}' for seed in SEEDS[1:]}
    assert set(review['failed_ids']) == failed

    data_path = FIT / 'data/training_data.npz'
    assert sha(data_path) == data_meta['training_data_sha256']
    with np.load(data_path, allow_pickle=False) as data:
        obs = data['observation'].copy()
        actions = data['requested_teacher_action'].copy()
        episodes = data['episode'].copy()
        train = data['train'].copy().astype(bool)
        importance = data['importance'].copy()
    assert obs.shape == (21500, 48) and actions.shape == (21500, 7)
    # Exclude recurrent student warmup rows: only actual teacher targets define support.
    supervised = train & (importance > 0)
    scale = np.maximum(obs[train][:, FIELDS].std(axis=0), .005)
    reference = features(obs[supervised], scale).astype(np.float64)
    reference_actions = actions[supervised]
    reference_episode = episodes[supervised]
    sqnorm = np.sum(reference * reference, axis=1)

    rows = []
    for seed in SEEDS:
        case_id = f'rod_00__special_mlp_scratch_s{seed}'
        folder = DEV / 'episodes' / case_id / 'rod'
        trajectory = folder / 'trajectory.npz'
        metrics_path = folder.parent / 'METRICS.json'
        with np.load(trajectory, allow_pickle=False) as tape:
            query = tape['observation'].copy()
            student_actions = tape['action'].copy()
            times = tape['time'].copy()
        assert query.shape == (500, 48) and student_actions.shape == (500, 7)
        distances, nearest = query_knn(query, reference, sqnorm, scale)
        local_actions = reference_actions[nearest]
        local_mean = np.mean(local_actions, axis=1)
        label_spread = np.sqrt(np.mean(
            (local_actions - local_mean[:, None, :]) ** 2, axis=(1, 2)))
        student_gap = np.sqrt(np.mean((student_actions - local_mean) ** 2, axis=1))
        neighbor_episode_mix = np.mean(
            reference_episode[nearest] != reference_episode[nearest][:, :1], axis=1)

        windows = []
        for start, end in WINDOWS:
            mask = (times >= start) & (times < end)
            assert mask.any()
            windows.append(dict(
                start_s=start, end_s=end, frames=int(mask.sum()),
                nearest_feature_rms=summary(distances[mask, 0]),
                ten_neighbor_teacher_action_spread=summary(label_spread[mask]),
                student_to_neighbor_mean_action_gap=summary(student_gap[mask]),
                neighbor_cross_episode_fraction=float(np.mean(neighbor_episode_mix[mask]))))

        metric = read(metrics_path)
        reviewed = next(row for row in review['rows']
                        if row['method'] == metric['method'] and row['condition'] == 'rod_00')
        assert metric['task_success'] == reviewed['task_success']
        assert metric['strict_success'] == reviewed['strict_success']
        rows.append(dict(
            case_id=case_id, task_success=metric['task_success'],
            strict_success=metric['strict_success'],
            machine_compliant=metric['machine_compliant'],
            maximum_external_penetration_m=metric['max_external_penetration_m'],
            windows=windows,
            input_hashes=dict(trajectory_sha256=sha(trajectory),
                              metrics_sha256=sha(metrics_path))))

    result = dict(
        schema='sii-contact-yield-v7-mlp-local-action-support-v1',
        status='complete_saved_history_descriptive_analysis',
        dataset_sha256=data_meta['training_data_sha256'],
        dataset_metadata_sha256=sha(FIT / 'data/DATA_COMPLETE.json'),
        fit_execution_sha256=sha(FIT / 'execution.json'),
        fit_audit_sha256=sha(FIT / 'FIT_AUDIT.json'),
        model_lock_sha256=sha(FIT / 'MODEL_LOCK.json'),
        development_review_sha256=sha(DEV / 'REVIEW.json'),
        analyzer_sha256=sha(Path(__file__)),
        feature_contract=dict(fields=FIELDS.tolist(),
                              scale='training observation std, floor 0.005',
                              transform='clip scaled values to [-12,12], append absolute values',
                              reference='training rows with positive importance only',
                              k=K,
                              distance='exact Euclidean distance divided by sqrt(36) in expanded feature space',
                              action='requested teacher action from the same nearest training frames',
                              supervised_reference_frames=int(supervised.sum()),
                              excluded_zero_weight_training_frames=int(np.sum(train & (importance == 0)))),
        rows=rows,
        limitations=[
            'Nearest teacher actions are labels from neighboring observed states, not counterfactual teacher actions on the student state.',
            'The 10-neighbor action spread is descriptive and is affected by temporal correlation and episode sampling.',
            'The post-contact state and action gaps occur at or after the first penetration region; they do not identify a pre-impact causal action.',
            'Only fixed27 rod development rollouts and registered v7 training data were read; final108 was not read.',
            'No physics integration, model fitting, actor/filter replay, model selection, or gate changes were performed.'],
        new_physics_steps=0, new_optimizer_updates=0)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2,
                               allow_nan=False) + '\n')
    print(DEST)
    print('dataset', result['dataset_sha256'], 'teacher frames', int(supervised.sum()))
    for row in rows:
        print(row['case_id'], 'Task/Strict', row['task_success'], row['strict_success'],
              'peak penetration mm', round(row['maximum_external_penetration_m'] * 1000, 6))
        for window in row['windows']:
            print(' ', window['start_s'], window['end_s'],
                  'feature p50/p95', window['nearest_feature_rms']['p50'],
                  window['nearest_feature_rms']['p95'],
                  'student gap p50/p95', window['student_to_neighbor_mean_action_gap']['p50'],
                  window['student_to_neighbor_mean_action_gap']['p95'])


if __name__ == '__main__':
    main()
