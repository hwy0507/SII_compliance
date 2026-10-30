"""Audit training-support drift in the two fixed27 MLP rod failures.

This is a saved-trajectory feature-space analysis only. It does not integrate
physics, fit models, change a checkpoint, or inspect the isolated final set.
Nearest teacher labels are descriptive proxies, not counterfactual rollouts.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parents[1] / 'docs/evidence/nonrl_v9_candidate_catalogue_20261029'
FIT = ROOT / 'outputs/contact_yield_recovery_retrain_20261030_v6'
DEV = ROOT / 'outputs/contact_yield_recovery_student_development_20261030_v5'
DEST = OUT / 'CONTACT_YIELD_MLP_ROD_SUPPORT_DIAGNOSIS_20261030.json'
FIELDS = np.array([14, 15, 16, 20, 21, 22, 26, 27, 28,
                   39, 40, 41, 42, 43, 44, 45, 46, 47])
CASES = [
    'rod_00__special_mlp_scratch_s2026102801',
    'rod_00__special_mlp_scratch_s2026102803',
]
WINDOWS = [(0., 4.4), (4.4, 4.7), (4.7, 5.), (5., 8.),
           (8., 12.76), (12.76, 20.)]
ANCHORS = (4.4, 4.48, 4.6, 4.72, 4.76, 5., 8., 11.)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def features(values, scale):
    scaled = np.clip(values[:, FIELDS] / scale, -12., 12.)
    return np.concatenate((scaled, np.abs(scaled)), axis=1)


def nearest(query, reference, reference_sqnorm):
    q = features(query, scale)
    distances, indices = [], []
    for start in range(0, len(q), 16):
        block = q[start:start + 16]
        d2 = np.maximum(np.sum(block * block, axis=1)[:, None]
                        + reference_sqnorm[None, :]
                        - 2. * block @ reference.T, 0.)
        nearest_idx = np.argmin(d2, axis=1)
        nearest_d2 = d2[np.arange(len(block)), nearest_idx]
        distances.extend(np.sqrt(nearest_d2 / q.shape[1]))
        indices.extend(nearest_idx)
    return np.asarray(distances), np.asarray(indices, dtype=int)


def main():
    assert not DEST.exists(), 'Preserve previous diagnosis receipts'
    registration = read(DEV / 'REGISTRATION.json')
    review = read(DEV / 'REVIEW.json')
    assert review['status'] == 'verified_fixed27_development_diagnosis'
    assert review['registration_sha256'] == sha(DEV / 'REGISTRATION.json')
    assert review['execution_sha256'] == sha(DEV / 'execution.json')
    assert set(review['failed_ids']) == set(CASES)
    with np.load(FIT / 'data/training_data.npz', allow_pickle=False) as data:
        observations = data['observation'].copy()
        targets = data['requested_teacher_action'].copy()
        train = data['train'].copy()
    dataset_path = FIT / 'data/training_data.npz'
    dataset_hash = sha(dataset_path)
    complete = read(FIT / 'data/DATA_COMPLETE.json')
    assert complete['training_data_sha256'] == dataset_hash
    global scale
    scale = np.maximum(observations[train][:, FIELDS].std(axis=0), .005)
    reference = features(observations[train], scale)
    reference_targets = targets[train]
    reference_sqnorm = np.sum(reference * reference, axis=1)
    validation_distance, _ = nearest(observations[~train], reference,
                                     reference_sqnorm)
    validation_p95 = float(np.quantile(validation_distance, .95))

    rows = []
    for case_id in CASES:
        folder = DEV / 'episodes' / case_id / 'rod'
        trajectory = folder / 'trajectory.npz'
        metrics_path = folder.parent / 'METRICS.json'
        with np.load(trajectory, allow_pickle=False) as data:
            obs = data['observation'].copy()
            actions = data['action'].copy()
            times = data['time'].copy()
        distance, index = nearest(obs, reference, reference_sqnorm)
        windows = []
        for start, end in WINDOWS:
            mask = (times >= start) & (times < end)
            values = distance[mask]
            windows.append(dict(
                start_s=start, end_s=end, frames=int(mask.sum()),
                distance_p50=float(np.quantile(values, .50)),
                distance_p95=float(np.quantile(values, .95)),
                distance_max=float(np.max(values)),
                fraction_above_validation_p95=float(np.mean(values > validation_p95))))
        anchors = []
        for target_time in ANCHORS:
            i = int(np.argmin(np.abs(times - target_time)))
            nn_action = reference_targets[index[i]]
            anchors.append(dict(
                time_s=float(times[i]),
                nearest_training_distance=float(distance[i]),
                student_requested_action=actions[i].tolist(),
                nearest_training_teacher_action=nn_action.tolist(),
                student_minus_nearest_label=(actions[i] - nn_action).tolist(),
                action_gap_l2=float(np.linalg.norm(actions[i] - nn_action)))
            )
        metric = read(metrics_path)
        reviewed = next(row for row in review['rows']
                        if row['method'] == metric['method']
                        and row['condition'] == 'rod_00')
        assert metric['task_success'] == reviewed['task_success']
        rows.append(dict(
            case_id=case_id, task_success=metric['task_success'],
            strict_success=metric['strict_success'],
            machine_compliant=metric['machine_compliant'],
            max_external_penetration_m=metric['max_external_penetration_m'],
            completion_time_s=metric['completion_time_s'],
            windows=windows, anchors=anchors,
            input_hashes=dict(trajectory_sha256=sha(trajectory),
                              metrics_sha256=sha(metrics_path))))

    result = dict(
        schema='sii-contact-yield-mlp-rod-support-diagnosis-v1',
        status='complete_saved_history_support_diagnosis',
        dataset_sha256=dataset_hash,
        registration_sha256=sha(DEV / 'REGISTRATION.json'),
        execution_sha256=sha(DEV / 'execution.json'),
        review_sha256=sha(DEV / 'REVIEW.json'),
        analyzer_sha256=sha(Path(__file__)),
        feature_contract=dict(fields=FIELDS.tolist(),
            normalization='training-only standard deviation, floor 0.005; clip [-12,12]; concatenate absolute value',
            distance='exact nearest-frame RMS Euclidean distance in the 36-dimensional expanded feature space',
            training_frames=int(train.sum()), validation_frames=int((~train).sum()),
            all_validation_distance_p50=float(np.quantile(validation_distance, .50)),
            all_validation_distance_p95=validation_p95,
            all_validation_distance_max=float(np.max(validation_distance))),
        rows=rows,
        limitations=[
            'Only the two fixed train00 development failure trajectories were inspected; no unseen or final-test input was read.',
            'The distance is descriptive feature-space support, not a calibrated OOD probability or proof of causality.',
            'Nearest training teacher actions are not teacher rollouts on the query state and are not eligible new demonstrations.',
            'This analysis performs no physics integration, fitting, actor replay, model selection, or gate change.'
        ],
        new_physical_steps=0, new_optimizer_updates=0)
    OUT.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2,
                               allow_nan=False) + '\n')
    print(DEST)
    for row in rows:
        print(row['case_id'], row['strict_success'],
              [(w['start_s'], w['end_s'], round(w['distance_p50'], 5),
                round(w['fraction_above_validation_p95'], 3))
               for w in row['windows']])


if __name__ == '__main__':
    main()
