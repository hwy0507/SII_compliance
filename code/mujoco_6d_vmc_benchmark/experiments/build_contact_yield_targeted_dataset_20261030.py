"""Append only qualified targeted rod-recovery teacher suffixes to the shared fit set."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
RECOVERY = ROOT/'outputs/contact_yield_targeted_recovery_20261030_v1'
BASE = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v3'
OUTPUT = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v4'
ACCEPTED = ('rod_mlp01_post_yield_5p2s', 'rod_mlp01_late_yield_7s')
EXPECTED = (*ACCEPTED, 'rod_mlp03_prepenetration_4p48s',
            'rod_mlp03_prepenetration_4p60s')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                     allow_nan=False) + '\n')


def build(output=OUTPUT):
    output = Path(output).resolve()
    assert output == OUTPUT.resolve() and not output.exists()
    reg = read(RECOVERY/'REGISTRATION.json')
    state = read(RECOVERY/'execution.json')
    assert state['status'] == 'complete_four_recovery_probes_pending_shared_data_decision'
    assert state['registration_sha256'] == sha(RECOVERY/'REGISTRATION.json')
    assert [row['id'] for row in state['rows']] == list(EXPECTED)
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT/name) == digest, name

    base_meta = read(BASE/'data/DATA_COMPLETE.json')
    base_state = read(BASE/'execution.json')
    base_lock = read(BASE/'MODEL_LOCK.json')
    assert base_state['status'] == 'complete'
    assert base_state['model_lock_sha256'] == sha(BASE/'MODEL_LOCK.json')
    assert base_lock['status'] == 'frozen'
    assert base_meta['training_data_sha256'] == sha(BASE/'data/training_data.npz')
    assert base_meta['episodes'] == 34 and base_meta['qualified_episodes'] == 30
    with np.load(BASE/'data/training_data.npz', allow_pickle=False) as archive:
        arrays = {key: archive[key].copy() for key in archive.files}
    assert arrays['observation'].shape == (18500, 48)
    assert arrays['requested_teacher_action'].shape == (18500, 7)
    assert int(np.sum(arrays['importance'] == 0.)) == 1175
    assert len(np.unique(arrays['episode'][arrays['train']])) == 28
    assert len(np.unique(arrays['episode'][~arrays['train']])) == 6

    from audit_special_scene_metrics_v2_20261030 import episode as audit_metrics
    additions = []
    for offset, identity in enumerate(ACCEPTED):
        case = next(case for case in reg['cases'] if case['id'] == identity)
        row = next(row for row in state['rows'] if row['id'] == identity)
        folder = Path(row['folder'])
        assert row['qualified'] is True and folder.is_dir()
        handoff = read(folder/'HANDOFF_REVIEW.json')
        qualification = read(folder/'DEMONSTRATION_QUALIFICATION.json')
        independent = read(folder/'INDEPENDENT_AUDIT.json')
        execution = read(folder/'execution.json')
        assert handoff['status'] == 'reviewed' and handoff['qualified']
        assert handoff['teacher_suffix_candidate_only'] and handoff['no_training_performed']
        assert handoff['no_final_test_performed'] and independent['status'] == 'passed'
        assert qualification['status'] == 'qualified'
        assert all(qualification[key] is True for key in
                   ('task_success', 'safety_valid', 'scene_contact_valid'))
        assert all(sha(folder/name) == digest
                   for name, digest in qualification['input_hashes'].items())
        duration = 20.0
        metrics = audit_metrics(folder, case['model']['name'],
                                case['condition']['id'], duration)
        assert metrics['task_success'] and metrics['strict_success']
        assert metrics['machine_compliant']
        assert execution['status'] == 'complete'
        assert execution['physics_dt_s'] == 0.00005
        assert execution['steps'] == 500 and execution['substeps'] == 400000
        assert execution['student_checkpoint_sha256'] == case['model']['checkpoint_sha256']
        with np.load(folder/'trajectory.npz', allow_pickle=False) as archive:
            observations = archive['observation'].copy()
            applied = archive['action'].copy()
        with np.load(folder/'handoff_actions.npz', allow_pickle=False) as archive:
            handoff_actions = {key: archive[key].copy() for key in archive.files}
        prefix = case['student_steps']
        assert observations.shape == (500, 48) and applied.shape == (500, 7)
        assert handoff_actions['physical_step_completed'].all()
        assert not handoff_actions['teacher_loss_mask'][:prefix].any()
        assert handoff_actions['teacher_loss_mask'][prefix:].all()
        assert np.all(handoff_actions['role'][:prefix] == 'student_prefix')
        assert np.all(handoff_actions['role'][prefix:] == 'executed_teacher_suffix')
        np.testing.assert_array_equal(handoff_actions['teacher'][prefix:], applied[prefix:])
        np.testing.assert_array_equal(handoff_actions['student'][:prefix], applied[:prefix])
        old = BASE.parent/'contact_yield_recovery_student_development_20261030_v1/episodes'/(
            'rod_00__special_mlp_scratch_s2026102801')/'rod'
        assert sha(folder/'scene.mjb') == sha(old/'scene.mjb')
        with np.load(old/'trajectory.npz', allow_pickle=False) as archive:
            np.testing.assert_array_equal(observations[:prefix], archive['observation'][:prefix])
            np.testing.assert_array_equal(applied[:prefix], archive['action'][:prefix])

        episode_id = int(arrays['episode'].max()) + 1
        arrays['observation'] = np.concatenate((arrays['observation'], observations))
        target = applied.copy()
        target[:prefix] = applied[:prefix]
        arrays['requested_teacher_action'] = np.concatenate(
            (arrays['requested_teacher_action'], target))
        arrays['episode'] = np.concatenate((arrays['episode'],
                                             np.full(500, episode_id, np.int64)))
        arrays['train'] = np.concatenate((arrays['train'], np.ones(500, bool)))
        arrays['physical_execution'] = np.concatenate(
            (arrays['physical_execution'], np.ones(500, bool)))
        arrays['importance'] = np.concatenate((arrays['importance'],
            np.r_[np.zeros(prefix), np.ones(500-prefix)].astype(np.float64)))
        additions.append(dict(episode=episode_id, id=identity, scene='rod', split='train',
            source_folder=str(folder), source_identity=case['condition']['id'],
            family=case['model']['family'], seed=case['model']['seed'],
            student_prefix_steps=prefix, teacher_supervised_steps=500-prefix, frames=500,
            expected_duration_s=20.0, task_success=True, strict_success=True,
            machine_compliant=True, teacher_suffix_only=True, zero_loss_warmup=True,
            trajectory_sha256=sha(folder/'trajectory.npz'),
            handoff_actions_sha256=sha(folder/'handoff_actions.npz'),
            qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'),
            review_sha256=sha(folder/'HANDOFF_REVIEW.json'),
            independent_audit_sha256=sha(folder/'INDEPENDENT_AUDIT.json'),
            checkpoint_sha256=case['model']['checkpoint_sha256']))

    arrays['teacher_action'] = arrays['requested_teacher_action'].copy()
    assert arrays['observation'].shape == (19500, 48)
    assert arrays['requested_teacher_action'].shape == (19500, 7)
    assert int(np.sum(arrays['importance'] == 0.)) == 1480
    assert int(np.sum(arrays['importance'] == 1.)) == 18020
    assert len(np.unique(arrays['episode'][arrays['train']])) == 30
    assert len(np.unique(arrays['episode'][~arrays['train']])) == 6

    output.mkdir(parents=True)
    (output/'data').mkdir()
    np.savez_compressed(output/'data/training_data.npz', **arrays)
    dataset_path = output/'data/training_data.npz'
    lineage = list(base_meta['lineage'])
    for addition in additions:
        lineage.append(dict(episode=addition['episode'], id=addition['id'], scene='rod',
            split='train', folder=addition['source_folder'], frames=500, reused=False,
            augmented=True, student_prefix_steps=addition['student_prefix_steps'],
            supervised_frames=addition['teacher_supervised_steps'],
            hashes={'trajectory.npz': addition['trajectory_sha256'],
                    'handoff_actions.npz': addition['handoff_actions_sha256']}))
    metadata = dict(base_meta)
    metadata.update(schema='sii-vmc-special-scenes-recovery-augmented-v2',
        augmentation_round=2, training_data_sha256=sha(dataset_path),
        parent_data_sha256=base_meta['training_data_sha256'], episodes=36,
        qualified_episodes=30, frames=19500, pure_qualified_episodes=30,
        augmented_recovery_episodes=6, zero_weight_warmup_frames=1480,
        teacher_supervised_recovery_frames=2270, all_real_execution=True,
        lineage=lineage, targeted_recovery_augmentation=additions,
        rejected_targeted_probes=[dict(id=row['id'], qualified=False,
            reason='Independent safety/contact gate failed; retained outside training data',
            folder=row['folder'], review_sha256=row['review_sha256'])
            for row in state['rows'] if row['id'] not in ACCEPTED],
        validation_identities=base_meta['validation_identities'], validation_unchanged=True,
        selection='Same six pure-teacher validation identities; no recovery data in validation or selection.')
    write(output/'data/DATA_COMPLETE.json', metadata)
    registration = read(BASE/'REGISTRATION.json')
    registration.update(schema='sii-contact-yield-scrape-recovery-fair-refit-v2',
        dataset_sha256=metadata['training_data_sha256'],
        parent_dataset_sha256=base_meta['training_data_sha256'],
        fit_parent_data_sha256=sha(BASE/'data/training_data.npz'),
        targeted_recovery_registration_sha256=sha(RECOVERY/'REGISTRATION.json'),
        targeted_recovery_execution_sha256=sha(RECOVERY/'execution.json'),
        targeted_recovery_cases=additions, excluded_probe_ids=[row['id'] for row in state['rows']
                                                               if row['id'] not in ACCEPTED],
        seeds=[2026102801, 2026102802, 2026102803], candidates_per_family_seed=12,
        neural_updates=32000,
        selection='Minimum requested-action MSE on the same six original pure-teacher validation identities; no recovery row is validation data.',
        recurrent_warmup='Actual observed student prefixes have importance zero; no counterfactual teacher prefix labels.',
        comparison='ESN, RNN, and MLP share the same 34-episode parent dataset plus the same two newly qualified teacher suffixes and identical validation identities; equal candidate counts and neural update budgets.',
        final_test='Unseen108 remains sealed until all nine fixed27 development candidates pass the existing gates.')
    write(output/'REGISTRATION.json', registration)
    write(output/'RECOVERY_AUGMENTATION.json', dict(
        status='verified_two_actual_teacher_suffixes_only',
        parent_data_sha256=base_meta['training_data_sha256'],
        new_data_sha256=metadata['training_data_sha256'], episodes=additions,
        excluded_failed_probe_ids=[row['id'] for row in state['rows'] if row['id'] not in ACCEPTED],
        counterfactual_prefix_rows_used_as_teacher_labels=0,
        zero_weight_prefix_rows=sum(x['student_prefix_steps'] for x in additions),
        teacher_supervised_rows=sum(x['teacher_supervised_steps'] for x in additions),
        all_included_task_strict_machine_pass=True))
    write(output/'execution.json', dict(status='dataset_complete',
        dataset_sha256=metadata['training_data_sha256'], parent_data_sha256=base_meta['training_data_sha256'],
        model_lock_sha256=None, recovery_registration_sha256=sha(RECOVERY/'REGISTRATION.json'),
        recovery_execution_sha256=sha(RECOVERY/'execution.json')))
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(build(args.output), ensure_ascii=False, indent=2))
