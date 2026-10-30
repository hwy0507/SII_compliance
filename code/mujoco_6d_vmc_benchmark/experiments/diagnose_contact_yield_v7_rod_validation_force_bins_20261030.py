"""Post-selection diagnostic of v7 rod validation action error by sensed load."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from current_student_policy_20260921 import load_current

FIT = ROOT / 'outputs/contact_yield_recovery_retrain_20261030_v7'
EVIDENCE = ROOT.parents[1] / 'docs/evidence/nonrl_v9_candidate_catalogue_20261029'
DEST = EVIDENCE / 'CONTACT_YIELD_V7_ROD_VALIDATION_FORCE_BINS_20261030_V2.json'
ROD_VALIDATION_EPISODES = (8, 9)
FORCE_FIELDS = slice(39, 45)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def mse(prediction, target):
    return np.mean((prediction - target) ** 2, axis=0)


def main():
    assert not DEST.exists(), 'Preserve prior evidence and use a new versioned output.'
    execution = read(FIT / 'execution.json')
    audit = read(FIT / 'FIT_AUDIT.json')
    lock = read(FIT / 'MODEL_LOCK.json')
    metadata = read(FIT / 'data/DATA_COMPLETE.json')
    assert execution['status'] == 'complete' and audit['status'] == 'passed'
    assert lock['status'] == 'frozen' and len(lock['models']) == 9
    data_path = FIT / 'data/training_data.npz'
    dataset_sha = sha(data_path)
    assert dataset_sha == metadata['training_data_sha256'] == lock['training_data_sha256']
    assert audit['dataset_sha256'] == dataset_sha
    assert audit['model_lock_sha256'] == sha(FIT / 'MODEL_LOCK.json')
    with np.load(data_path, allow_pickle=False) as data:
        obs = data['observation'].copy()
        targets = data['requested_teacher_action'].copy()
        episode_ids = data['episode'].copy()
        train = data['train'].copy()
        importance = data['importance'].copy()
    assert obs.shape == (21500, 48) and targets.shape == (21500, 7)
    lineages = {int(item['episode']): item for item in metadata['lineage']}
    assert all(lineages[index]['id'] in ('rod_08', 'rod_09') and
               lineages[index]['split'] == 'validation'
               for index in ROD_VALIDATION_EPISODES)

    rows = []
    models = []
    for entry in lock['models']:
        checkpoint = Path(entry['checkpoint'])
        assert sha(checkpoint) == entry['checkpoint_sha256']
        assert sha(Path(entry['metadata'])) == entry['metadata_sha256']
        models.append((entry, load_current(checkpoint)))

    for episode_id in ROD_VALIDATION_EPISODES:
        mask = episode_ids == episode_id
        lineage = lineages[episode_id]
        source_trajectory = Path(lineage['folder']) / 'trajectory.npz'
        assert sha(source_trajectory) == lineage['trajectory_sha256']
        assert mask.sum() == lineage['frames'] == 500
        assert not train[mask].any() and importance[mask].min() > 0
        observations = obs[mask]
        target = targets[mask]
        force = np.linalg.norm(observations[:, FORCE_FIELDS], axis=1)
        threshold = float(np.quantile(force, .8))
        high = force >= threshold
        low = ~high
        predictions = []
        for entry, actor in models:
            actor.reset()
            prediction = np.asarray([actor.act(frame) for frame in observations])
            assert prediction.shape == target.shape and np.isfinite(prediction).all()
            predictions.append((entry, prediction))
            rows.append(dict(
                episode=lineages[episode_id]['id'], family=entry['family'], seed=entry['seed'],
                selected_validation_mse=entry['validation_mse'],
                force_norm_p50=float(np.quantile(force, .5)),
                force_norm_p80=threshold, force_norm_p95=float(np.quantile(force, .95)),
                high_load_fraction=float(high.mean()),
                overall=dict(frames=int(len(force)), action_mse=float(np.mean((prediction-target)**2)),
                             action_channel_mse=mse(prediction, target).tolist()),
                lower_load=dict(frames=int(low.sum()), action_mse=float(np.mean((prediction[low]-target[low])**2)),
                                action_channel_mse=mse(prediction[low], target[low]).tolist()),
                high_load=dict(frames=int(high.sum()), action_mse=float(np.mean((prediction[high]-target[high])**2)),
                               action_channel_mse=mse(prediction[high], target[high]).tolist())))

    source_files = [Path(__file__), ROOT/'scripts/current_student_policy_20260921.py',
                    ROOT/'scripts/office_mlp_rnn_20261002.py',
                    ROOT/'scripts/office_vmc_memory_esn_20260927.py']
    result = dict(
        schema='sii-contact-yield-v7-rod-validation-force-bins-v2',
        status='complete_post_selection_validation_force_stratification',
        dataset_sha256=dataset_sha,
        fit_execution_sha256=sha(FIT/'execution.json'),
        fit_audit_sha256=sha(FIT/'FIT_AUDIT.json'),
        model_lock_sha256=sha(FIT/'MODEL_LOCK.json'),
        analyzer_sha256=sha(Path(__file__)),
        validation_trajectory_sha256={lineages[i]['id']: lineages[i]['trajectory_sha256']
                                      for i in ROD_VALIDATION_EPISODES},
        source_sha256={str(path.relative_to(ROOT)): sha(path) for path in source_files},
        feature='L2 norm of canonical48 estimated-wrench fields [39:45]',
        strata='Per-episode lower 80% versus upper 20% force-norm frames; threshold is descriptive, not a safety or event gate.',
        rows=rows,
        interpretation_limitations=[
            'Both rod08 and rod09 are the registered validation identities used for model selection; these post-selection slices are descriptive, not independent generalization evidence.',
            'The sensed-wrench bins are not a calibrated human-contact classifier or exact contact-event label.',
            'No model selection, fitting, actor deployment, physics integration, gate change, or final-test access occurred.'],
        new_physics_steps=0, new_optimizer_updates=0, model_reselection=False,
        final_test_accessed=False)
    DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(DEST)
    for row in rows:
        if row['episode'] == 'rod_08':
            print(row['family'], row['seed'],
                  'overall', round(row['overall']['action_mse'], 8),
                  'low', round(row['lower_load']['action_mse'], 8),
                  'high', round(row['high_load']['action_mse'], 8),
                  'ratio', round(row['high_load']['action_mse']/row['lower_load']['action_mse'], 3))


if __name__ == '__main__':
    main()
