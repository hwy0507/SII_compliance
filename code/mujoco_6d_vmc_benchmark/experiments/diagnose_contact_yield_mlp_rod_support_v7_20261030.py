"""Compare saved fixed27 rod rollouts with the locked v7 training support.

This analysis reads saved trajectories and fitted-data arrays only. It performs
no physics integration, fitting, actor replay, model selection, or test access.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'outputs'
FIT = BASE / 'contact_yield_recovery_retrain_20261030_v7'
DEV = BASE / 'contact_yield_recovery_student_development_20261030_v7'
OUT = ROOT.parents[1] / 'docs/evidence/nonrl_v9_candidate_catalogue_20261029'
DEST = OUT / 'CONTACT_YIELD_MLP_ROD_SUPPORT_DIAGNOSIS_V7_20261030.json'
FIELDS = np.array([14, 15, 16, 20, 21, 22, 26, 27, 28,
                   39, 40, 41, 42, 43, 44, 45, 46, 47])
FAMILIES = ('esn_ridge', 'rnn_scratch', 'mlp_scratch')
SEEDS = (2026102801, 2026102802, 2026102803)
WINDOWS = ((0., 4.4), (4.4, 4.7), (4.7, 5.), (5., 8.),
           (8., 12.76), (12.76, 20.))
ANCHORS = (4.4, 4.48, 4.6, 4.72, 4.76, 5., 8., 11., 12., 12.76)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def expand(values, scale):
    scaled = np.clip(values[:, FIELDS] / scale, -12., 12.)
    return np.concatenate((scaled, np.abs(scaled)), axis=1)


def nearest(query, reference, reference_sqnorm, scale):
    q = expand(query, scale)
    distances, indices = [], []
    for start in range(0, len(q), 16):
        block = q[start:start + 16]
        d2 = np.maximum(np.sum(block * block, axis=1)[:, None]
                        + reference_sqnorm[None, :]
                        - 2. * block @ reference.T, 0.)
        idx = np.argmin(d2, axis=1)
        distances.extend(np.sqrt(d2[np.arange(len(block)), idx] / q.shape[1]))
        indices.extend(idx)
    return np.asarray(distances), np.asarray(indices, dtype=int)


def main():
    assert not DEST.exists(), 'Preserve any previous diagnosis receipt'
    fit_execution = read(FIT / 'execution.json')
    fit_audit = read(FIT / 'FIT_AUDIT.json')
    model_lock = read(FIT / 'MODEL_LOCK.json')
    data_meta = read(FIT / 'data/DATA_COMPLETE.json')
    review = read(DEV / 'REVIEW.json')
    assert fit_execution['status'] == 'complete'
    assert len(fit_execution['fits']) == 75
    assert fit_audit['status'] == 'passed'
    assert model_lock['status'] == 'frozen' and len(model_lock['models']) == 9
    assert review['status'] == 'verified_fixed27_development_diagnosis'
    assert review['no_final_test_performed'] is True
    assert set(review['failed_ids']) == {
        'rod_00__special_mlp_scratch_s2026102802',
        'rod_00__special_mlp_scratch_s2026102803'}

    data_path = FIT / 'data/training_data.npz'
    assert sha(data_path) == data_meta['training_data_sha256']
    assert fit_execution['dataset_sha256'] == data_meta['training_data_sha256']
    with np.load(data_path, allow_pickle=False) as data:
        observations = data['observation'].copy()
        targets = data['requested_teacher_action'].copy()
        train = data['train'].copy().astype(bool)
    assert observations.shape == (21500, 48)
    assert targets.shape == (21500, 7) and train.shape == (21500,)
    scale = np.maximum(observations[train][:, FIELDS].std(axis=0), .005)
    reference = expand(observations[train], scale)
    reference_targets = targets[train]
    reference_sqnorm = np.sum(reference * reference, axis=1)
    validation_distance, _ = nearest(
        observations[~train], reference, reference_sqnorm, scale)
    validation_p95 = float(np.quantile(validation_distance, .95))

    rows = []
    for family in FAMILIES:
        for seed in SEEDS:
            case_id = f'rod_00__special_{family}_s{seed}'
            folder = DEV / 'episodes' / case_id / 'rod'
            trajectory = folder / 'trajectory.npz'
            metrics_path = folder.parent / 'METRICS.json'
            with np.load(trajectory, allow_pickle=False) as tape:
                obs = tape['observation'].copy()
                actions = tape['action'].copy()
                times = tape['time'].copy()
            distance, index = nearest(obs, reference, reference_sqnorm, scale)
            metric = read(metrics_path)
            reviewed = next(row for row in review['rows']
                            if row['method'] == metric['method']
                            and row['condition'] == 'rod_00')
            assert metric['task_success'] == reviewed['task_success']
            assert metric['strict_success'] == reviewed['strict_success']
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
            if family == 'mlp_scratch' and seed in SEEDS[1:]:
                for target_time in ANCHORS:
                    i = int(np.argmin(np.abs(times - target_time)))
                    label = reference_targets[index[i]]
                    anchors.append(dict(
                        time_s=float(times[i]),
                        nearest_training_distance=float(distance[i]),
                        student_action=actions[i].tolist(),
                        nearest_training_teacher_label=label.tolist(),
                        action_gap_l2=float(np.linalg.norm(actions[i] - label))))
            rows.append(dict(
                case_id=case_id, task_success=metric['task_success'],
                strict_success=metric['strict_success'],
                machine_compliant=metric['machine_compliant'],
                completion_time_s=metric['completion_time_s'],
                max_external_penetration_m=metric['max_external_penetration_m'],
                windows=windows, anchors=anchors,
                input_hashes=dict(trajectory_sha256=sha(trajectory),
                                  metrics_sha256=sha(metrics_path))))

    result = dict(
        schema='sii-contact-yield-mlp-rod-support-diagnosis-v7-v1',
        status='complete_saved_history_support_diagnosis',
        dataset_sha256=data_meta['training_data_sha256'],
        fit_execution_sha256=sha(FIT / 'execution.json'),
        fit_audit_sha256=sha(FIT / 'FIT_AUDIT.json'),
        model_lock_sha256=sha(FIT / 'MODEL_LOCK.json'),
        development_registration_sha256=sha(DEV / 'REGISTRATION.json'),
        development_execution_sha256=sha(DEV / 'execution.json'),
        development_review_sha256=sha(DEV / 'REVIEW.json'),
        analyzer_sha256=sha(Path(__file__)),
        feature_contract=dict(
            fields=FIELDS.tolist(),
            normalization='training-only standard deviation, floor 0.005; clip [-12,12]; append absolute value',
            distance='exact nearest-frame RMS Euclidean distance in the expanded 36-dimensional feature space',
            training_frames=int(train.sum()), validation_frames=int((~train).sum()),
            validation_distance_p50=float(np.quantile(validation_distance, .50)),
            validation_distance_p95=validation_p95,
            validation_distance_max=float(np.max(validation_distance))),
        rows=rows,
        limitations=[
            'Only saved rod_00 development trajectories were analyzed; the isolated final test set was not read.',
            'Nearest-frame distance is descriptive and is not a calibrated OOD probability or causal test.',
            'A nearest training teacher label is not a teacher rollout on the queried state and is not a new demonstration.',
            'The analysis performs no physics integration, fitting, actor replay, model selection, or gate change.'],
        new_physics_steps=0, new_optimizer_updates=0)
    OUT.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2,
                               allow_nan=False) + '\n')
    print(DEST)
    print('dataset', result['dataset_sha256'], 'validation_p95', validation_p95)
    for row in rows:
        print(row['case_id'], 'Task/Strict', row['task_success'], row['strict_success'],
              'penetration_mm', row['max_external_penetration_m'] * 1000.,
              'outside_fraction', [round(x['fraction_above_validation_p95'], 3)
                                  for x in row['windows']])


if __name__ == '__main__':
    main()
