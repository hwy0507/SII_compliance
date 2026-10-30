"""Append only the two independently qualified v6 seed01 teacher suffixes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
from collect_special_scene_actions_20261028 import read, sha, write
from audit_special_scene_metrics_v2_20261030 import episode as audit_episode

RECOVERY = ROOT/'outputs/contact_yield_v6_mlp_rod_handoff_20261030_v1'
PARENT = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v6'
OUTPUT = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v7'
ACCEPTED = ('v6_rod_mlp01_handoff_4p48s', 'v6_rod_mlp01_handoff_4p60s')
EXPECTED = (*ACCEPTED, 'v6_rod_mlp03_handoff_4p48s', 'v6_rod_mlp03_handoff_4p60s')


def build(output=OUTPUT):
    output = Path(output).resolve()
    assert output == OUTPUT.resolve() and not output.exists()
    reg, state = read(RECOVERY/'REGISTRATION.json'), read(RECOVERY/'execution.json')
    assert state['status'] == 'complete_four_recovery_probes_pending_shared_data_decision'
    assert state['registration_sha256'] == sha(RECOVERY/'REGISTRATION.json')
    assert [r['id'] for r in state['rows']] == list(EXPECTED)
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT/name) == digest, name
    parent_meta = read(PARENT/'data/DATA_COMPLETE.json')
    parent_state, parent_lock, parent_audit = (read(PARENT/n) for n in
        ('execution.json', 'MODEL_LOCK.json', 'FIT_AUDIT.json'))
    assert parent_state['status'] == 'complete'
    assert parent_state['model_lock_sha256'] == sha(PARENT/'MODEL_LOCK.json')
    assert parent_lock['status'] == 'frozen' and parent_audit['status'] == 'passed'
    assert parent_meta['schema'] == 'sii-vmc-special-scenes-recovery-augmented-v3'
    assert parent_meta['augmentation_round'] == 3 and parent_meta['episodes'] == 38
    assert parent_meta['frames'] == 20500 and parent_meta['zero_weight_warmup_frames'] == 1707
    assert parent_meta['training_data_sha256'] == sha(PARENT/'data/training_data.npz')
    with np.load(PARENT/'data/training_data.npz', allow_pickle=False) as archive:
        arrays = {k: archive[k].copy() for k in archive.files}
    assert arrays['observation'].shape == (20500, 48)
    assert arrays['requested_teacher_action'].shape == (20500, 7)
    assert int(np.sum(arrays['importance'] == 0.)) == 1707
    assert int(np.sum(arrays['importance'] == 1.)) == 18793
    assert len(np.unique(arrays['episode'][arrays['train']])) == 32
    assert len(np.unique(arrays['episode'][~arrays['train']])) == 6

    additions, excluded = [], []
    for case, row in zip(reg['cases'], state['rows']):
        assert case['id'] == row['id'] and row['prefix_pairing_max_abs'] == 0.
        folder = Path(row['folder'])
        review = read(folder/'HANDOFF_REVIEW.json')
        qualification = read(folder/'DEMONSTRATION_QUALIFICATION.json')
        independent = read(folder/'INDEPENDENT_AUDIT.json')
        assert review['status'] == 'reviewed' and review['no_training_performed']
        assert review['no_final_test_performed'] and independent['status'] == 'passed'
        assert all(sha(folder/name) == digest for name, digest in
                   qualification['input_hashes'].items())
        if case['id'] not in ACCEPTED:
            assert row['qualified'] is False and qualification['status'] == 'failed_preserved'
            excluded.append(dict(id=case['id'], folder=str(folder),
                                 qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'),
                                 reason='Frozen 0.20 mm penetration limit failed; retained outside training data'))
            continue

        assert row['qualified'] is True and review['qualified']
        assert review['teacher_suffix_candidate_only']
        assert qualification['status'] == 'qualified'
        assert all(qualification[key] is True for key in
                   ('task_success', 'safety_valid', 'scene_contact_valid'))
        condition, model = case['condition'], case['model']
        metrics = audit_episode(folder, model['name'], condition['id'], 20.)
        assert metrics['task_success'] and metrics['strict_success'] and metrics['machine_compliant']
        execution = read(folder/'execution.json')
        assert execution['status'] == 'complete' and execution['physics_dt_s'] == .00005
        assert execution['steps'] == 500 and execution['substeps'] == 400000
        assert execution['student_checkpoint_sha256'] == model['checkpoint_sha256']
        with np.load(folder/'trajectory.npz', allow_pickle=False) as archive:
            observations, actions = archive['observation'].copy(), archive['action'].copy()
        with np.load(folder/'handoff_actions.npz', allow_pickle=False) as archive:
            handoff = {key: archive[key].copy() for key in archive.files}
        prefix = case['student_steps']
        assert observations.shape == (500, 48) and actions.shape == (500, 7)
        assert handoff['physical_step_completed'].all()
        assert not handoff['teacher_loss_mask'][:prefix].any()
        assert handoff['teacher_loss_mask'][prefix:].all()
        assert np.all(handoff['role'][:prefix] == 'student_prefix')
        assert np.all(handoff['role'][prefix:] == 'executed_teacher_suffix')
        np.testing.assert_array_equal(handoff['student'][:prefix], actions[:prefix])
        np.testing.assert_array_equal(handoff['teacher'][prefix:], actions[prefix:])

        original = (ROOT/'outputs/contact_yield_recovery_student_development_20261030_v5'
                    /'episodes'/f"{condition['id']}__{model['name']}"/'rod')
        assert sha(folder/'scene.mjb') == sha(original/'scene.mjb')
        with np.load(original/'trajectory.npz', allow_pickle=False) as archive:
            np.testing.assert_array_equal(observations[:prefix], archive['observation'][:prefix])
            np.testing.assert_array_equal(actions[:prefix], archive['action'][:prefix])

        episode_id = int(arrays['episode'].max()) + 1
        arrays['observation'] = np.concatenate((arrays['observation'], observations))
        arrays['requested_teacher_action'] = np.concatenate((arrays['requested_teacher_action'], actions.copy()))
        arrays['episode'] = np.concatenate((arrays['episode'], np.full(500, episode_id, np.int64)))
        arrays['train'] = np.concatenate((arrays['train'], np.ones(500, bool)))
        arrays['physical_execution'] = np.concatenate((arrays['physical_execution'], np.ones(500, bool)))
        weights = np.r_[np.zeros(prefix), np.ones(500-prefix)].astype(np.float64)
        arrays['importance'] = np.concatenate((arrays['importance'], weights))
        additions.append(dict(episode=episode_id, id=case['id'], scene='rod', split='train',
            source_folder=str(folder), source_identity=condition['id'], family=model['family'],
            seed=model['seed'], student_prefix_steps=prefix, teacher_supervised_steps=500-prefix,
            frames=500, expected_duration_s=20., task_success=True, strict_success=True,
            machine_compliant=True, teacher_suffix_only=True, zero_loss_warmup=True,
            trajectory_sha256=sha(folder/'trajectory.npz'),
            handoff_actions_sha256=sha(folder/'handoff_actions.npz'),
            qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'),
            review_sha256=sha(folder/'HANDOFF_REVIEW.json'),
            independent_audit_sha256=sha(folder/'INDEPENDENT_AUDIT.json'),
            checkpoint_sha256=model['checkpoint_sha256']))

    arrays['teacher_action'] = arrays['requested_teacher_action'].copy()
    assert arrays['observation'].shape == (21500, 48)
    assert arrays['requested_teacher_action'].shape == (21500, 7)
    assert int(np.sum(arrays['importance'] == 0.)) == 1934
    assert int(np.sum(arrays['importance'] == 1.)) == 19566
    assert len(np.unique(arrays['episode'][arrays['train']])) == 34
    assert len(np.unique(arrays['episode'][~arrays['train']])) == 6
    assert np.all(arrays['physical_execution'])

    output.mkdir(parents=True)
    (output/'data').mkdir()
    data_path = output/'data/training_data.npz'
    np.savez_compressed(data_path, **arrays)
    lineage = list(parent_meta['lineage'])
    for addition in additions:
        lineage.append(dict(episode=addition['episode'], id=addition['id'], scene='rod',
            split='train', folder=addition['source_folder'], frames=500, reused=False,
            augmented=True, student_prefix_steps=addition['student_prefix_steps'],
            supervised_frames=addition['teacher_supervised_steps'], hashes={
                'trajectory.npz': addition['trajectory_sha256'],
                'handoff_actions.npz': addition['handoff_actions_sha256']}))
    metadata = dict(parent_meta)
    metadata.update(schema='sii-vmc-special-scenes-recovery-augmented-v4', augmentation_round=4,
        parent_data_sha256=parent_meta['training_data_sha256'], training_data_sha256=sha(data_path),
        episodes=40, qualified_episodes=30, pure_qualified_episodes=30, frames=21500,
        augmented_recovery_episodes=10, zero_weight_warmup_frames=1934,
        teacher_supervised_recovery_frames=3566, all_real_execution=True, lineage=lineage,
        v6_rod_handoff_augmentation=additions, excluded_v6_probes=excluded,
        validation_identities=parent_meta['validation_identities'], validation_unchanged=True,
        selection='Same six pure-teacher validation identities; no recovery rows in validation or selection.')
    write(output/'data/DATA_COMPLETE.json', metadata)
    registration = dict(read(PARENT/'REGISTRATION.json'))
    registration.update(schema='sii-contact-yield-v6-rod-handoff-fair-refit-v1',
        parent_data_sha256=parent_meta['training_data_sha256'], dataset_sha256=sha(data_path),
        handoff_registration_sha256=sha(RECOVERY/'REGISTRATION.json'),
        handoff_execution_sha256=sha(RECOVERY/'execution.json'),
        handoff_cases=additions, excluded_probe_ids=[row['id'] for row in excluded],
        seeds=[2026102801, 2026102802, 2026102803], candidates_per_family_seed=12,
        neural_updates=32000,
        selection='Minimum requested-action MSE on the same six original pure-teacher validation identities; no recovery row is validation.',
        comparison='ESN, RNN, and MLP share all prior qualified data plus the same two new qualified seed01 suffixes; all failed seed03 probes are excluded.',
        final_test='Final108 remains sealed pending the fixed27 development review and separate final handoff approval.')
    write(output/'REGISTRATION.json', registration)
    write(output/'RECOVERY_AUGMENTATION.json', dict(
        status='verified_two_actual_seed01_teacher_suffixes_only',
        parent_data_sha256=parent_meta['training_data_sha256'], new_data_sha256=sha(data_path),
        included=additions, excluded=excluded,
        counterfactual_prefix_rows_used_as_teacher_labels=0,
        zero_weight_prefix_rows=sum(row['student_prefix_steps'] for row in additions),
        teacher_supervised_rows=sum(row['teacher_supervised_steps'] for row in additions)))
    write(output/'execution.json', dict(status='dataset_complete', dataset_sha256=sha(data_path),
        parent_data_sha256=parent_meta['training_data_sha256'], model_lock_sha256=None,
        handoff_registration_sha256=sha(RECOVERY/'REGISTRATION.json'),
        handoff_execution_sha256=sha(RECOVERY/'execution.json')))
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(build(args.output), ensure_ascii=False, indent=2))
