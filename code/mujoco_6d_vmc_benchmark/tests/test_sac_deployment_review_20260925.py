"""Independent SAC13 admission/parity tests; synthetic files, no simulator/model inference."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]
import canonical48_sac_deployment_20260925 as adapter
import run_sac_deployment_20260925 as driver

spec = importlib.util.spec_from_file_location('sac13_independent_review', ROOT/'tools/prepare_sac_deployment_20260925.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def save(path, data):
    path.write_text(json.dumps(data))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive_model(path, *, seed=20260923, steps=8192, updates=8092):
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('data', json.dumps(dict(seed=seed, num_timesteps=steps, _n_updates=updates)))


def synthetic_training(tmp_path, monkeypatch, branch='online_only'):
    source = tmp_path/'source'
    source.mkdir()
    core = source/'core.py'
    core.write_text('# synthetic inference-admission fixture; never executed\n')
    monkeypatch.setattr(adapter, 'ROOT', source)
    directory = tmp_path/'training'
    directory.mkdir()
    archive_model(directory/'sac_final.zip')
    (directory/'vecnormalize_train_only.pkl').write_bytes(b'not unpickled by admission test')
    nominal = {'fixture_identity': 800}
    manifest = dict(algorithm='standard SAC', mode='direct7', branch=branch, training=dict(seed=20260923, steps=8192),
                    device='cuda', data_budget=dict(online=8192, demo=600 if branch=='demo_prefill' else 0,
                                                   total=8792 if branch=='demo_prefill' else 8192, offline_updates=0),
                    source_hashes={'core.py': digest(core)}, nominal_options=nominal,
                    fixture_specs={'train': {'command': {'environment': {'CORE_VMC_CONFIG': json.dumps(nominal)}}}})
    complete = dict(status='complete', mode='direct7', branch=branch, seed=20260923, training_steps=8192,
                    recorded_transitions=8192, updates=8092, optimizer_steps=dict(actor=8092, critic=8092, entropy=8092),
                    normalization_frozen=True, source_unchanged=True,
                    checkpoint_sha256=digest(directory/'sac_final.zip'),
                    normalizer_sha256=digest(directory/'vecnormalize_train_only.pkl'))
    save(directory/'manifest.json', manifest)
    save(directory/'COMPLETE.json', complete)
    return directory, manifest, complete


@pytest.mark.parametrize('branch', ['online_only', 'demo_prefill'])
def test_declared_complete_branch_is_admitted_without_loading_a_model(tmp_path, monkeypatch, branch):
    directory, manifest, complete = synthetic_training(tmp_path, monkeypatch, branch)
    actual_manifest, actual_complete, nominal = adapter.frozen_training(directory, branch)
    assert actual_manifest == manifest and actual_complete == complete
    assert nominal == manifest['nominal_options']
    nominal['fixture_identity'] = -1
    assert manifest['nominal_options']['fixture_identity'] == 800


@pytest.mark.parametrize('error', ['wrong_algorithm', 'wrong_branch', 'manifest_budget', 'zip_seed',
                                  'zip_budget', 'zip_updates', 'complete_updates', 'actual_optimizer_updates',
                                  'model_hash', 'normalizer_hash', 'failed_marker', 'source_drift'])
def test_wrong_identity_artifact_or_budget_cannot_deploy(tmp_path, monkeypatch, error):
    directory, manifest, complete = synthetic_training(tmp_path, monkeypatch)
    if error == 'wrong_algorithm':
        manifest['algorithm'] = 'PPO'
    elif error == 'wrong_branch':
        manifest['branch'] = 'demo_prefill'
    elif error == 'manifest_budget':
        manifest['training']['steps'] = 6144
    elif error in ('zip_seed', 'zip_budget', 'zip_updates'):
        kwargs = {'zip_seed': {'seed': 20260924}, 'zip_budget': {'steps': 6144}, 'zip_updates': {'updates': 8091}}[error]
        archive_model(directory/'sac_final.zip', **kwargs)
        # Bind the altered bytes so this exercises the metadata gate, not only SHA.
        complete['checkpoint_sha256'] = digest(directory/'sac_final.zip')
    elif error == 'complete_updates':
        complete['updates'] = 384
    elif error == 'actual_optimizer_updates':
        complete['optimizer_steps']['critic'] = 8091
    elif error == 'model_hash':
        complete['checkpoint_sha256'] = '0'*64
    elif error == 'normalizer_hash':
        complete['normalizer_sha256'] = '0'*64
    elif error == 'failed_marker':
        save(directory/'FAILED.json', {'error': 'synthetic simultaneous COMPLETE and FAILED'})
    else:
        (tmp_path/'source/core.py').write_text('# changed after training\n')
    save(directory/'manifest.json', manifest)
    save(directory/'COMPLETE.json', complete)
    with pytest.raises(ValueError):
        adapter.frozen_training(directory, 'online_only')


def jobs():
    return [dict(method='zero7', fixture={'seed': 9400})] + [
        dict(method=method, fixture={'seed': seed})
        for method in ('online_only', 'demo_prefill') for seed in range(9400, 9406)]


def test_matrix_is_exactly_two_learned_sixes_and_one_zero7_parity():
    keys = prepare.matrix_keys(jobs())
    assert len(keys) == 13 and keys.count(('zero7', 9400)) == 1


def deployment_metadata():
    record = dict(branch='online_only', device='cuda', seed=20260923,
                  checkpoint_sha256='a'*64, normalizer_sha256='b'*64,
                  manifest_sha256='c'*64, complete_sha256='d'*64,
                  nominal_options={'gain': 1.0})
    job = dict(method='online_only', environment={'CORE_VMC_CONFIG': json.dumps({'gain': 1.0, 'fixture': 9400})})
    metadata = dict(algorithm='standard SAC', branch='online_only', mode='direct7',
                    device='cuda', trained_device='cuda', seed=20260923,
                    training_steps=8192, training_updates=8092,
                    checkpoint_sha256=record['checkpoint_sha256'], normalizer_sha256=record['normalizer_sha256'],
                    training_manifest_sha256=record['manifest_sha256'], training_complete_sha256=record['complete_sha256'],
                    nominal_options=copy.deepcopy(record['nominal_options']), adapter_active=False,
                    runtime_fixture_CORE_VMC_CONFIG=json.loads(job['environment']['CORE_VMC_CONFIG']))
    return metadata, record, job


def test_driver_admits_exact_frozen_deployment_metadata():
    driver.validate_metadata(*deployment_metadata())


@pytest.mark.parametrize('field,wrong', [
    ('algorithm', 'PPO'), ('branch', 'demo_prefill'), ('mode', 'parameter6'),
    ('device', 'cpu'), ('trained_device', 'cpu'), ('seed', 20260924),
    ('training_steps', 8191), ('training_updates', 8091),
    ('checkpoint_sha256', 'e'*64), ('normalizer_sha256', 'e'*64),
    ('training_manifest_sha256', 'e'*64), ('training_complete_sha256', 'e'*64),
    ('nominal_options', {'gain': 1.1}), ('adapter_active', True),
    ('runtime_fixture_CORE_VMC_CONFIG', {'gain': 1.0, 'fixture': 9401})])
def test_driver_rejects_metadata_identity_budget_or_backend_drift(field, wrong):
    metadata, record, job = deployment_metadata()
    metadata[field] = wrong
    with pytest.raises(ValueError):
        driver.validate_metadata(metadata, record, job)


@pytest.mark.parametrize('error', ['missing', 'duplicate', 'extra', 'nominal_instead_of_zero7', 'wrong_fixture'])
def test_matrix_omission_duplicate_and_wrong_control_are_rejected(error):
    value = jobs()
    if error == 'missing':
        value.pop()
    elif error == 'duplicate':
        value[-1] = copy.deepcopy(value[-2])
    elif error == 'extra':
        value.append(copy.deepcopy(value[-1]))
    elif error == 'nominal_instead_of_zero7':
        value[0]['method'] = 'nominal_train_vmc'
    else:
        value[-1]['fixture']['seed'] = 9406
    with pytest.raises(ValueError):
        prepare.matrix_keys(value)


def zero_fixture(path, nonzero=False):
    (path/'rollout').mkdir(parents=True)
    (path/'metrics/episode_0').mkdir(parents=True)
    actions = np.zeros((600, 7), np.float64)
    if nonzero:
        actions[100, 2] = .125
    np.savez_compressed(path/'rollout/rollout.npz', observation=np.zeros((600, 48)), action=actions)
    np.savez_compressed(path/'rollout/physics_states.npz', q=np.arange(6, dtype=np.float64))
    np.savez_compressed(path/'rollout/contact_samples.npz', force=np.zeros((2, 3)))
    np.savez_compressed(path/'metrics/episode_0/substep_metrics.npz', time=np.asarray([.00005, .0001]), speed=np.zeros(2))
    (path/'rollout/rollout.mjb').write_bytes(b'synthetic-identical-model-no-physics')
    save(path/'metrics/episode_0/substep_metrics.json', dict(synthetic=True, samples=2))
    save(path/'rollout/rollout.json', dict(arguments={'output': str(path/'rollout/rollout'), 'duration': 24.},
        contact=dict(pairs=['b','a'], robot_geoms=['d','c'], robot_bodies=['f','e'], other_contacts=[]),
        success=False, final_stage=0))


def test_zero7_parity_only_ignores_output_paths_and_known_contact_set_order(tmp_path):
    reference, current = tmp_path/'reference', tmp_path/'current'
    zero_fixture(reference)
    zero_fixture(current)
    result = json.loads((current/'rollout/rollout.json').read_text())
    for key in ('pairs', 'robot_geoms', 'robot_bodies', 'other_contacts'):
        result['contact'][key].reverse()
    save(current/'rollout/rollout.json', result)
    report = prepare.zero_parity(reference, current)
    assert report['passed'] and report['full600']
    assert len(report['input_sha256']) == 14


@pytest.mark.parametrize('error', ['both_nonzero', 'action_drift', 'raw_drift', 'dtype_drift', 'mjb_drift', 'dynamic_json_drift', 'summary_drift'])
def test_nonzero_or_drifted_raw_cannot_pass_zero7_parity(tmp_path, error):
    reference, current = tmp_path/'reference', tmp_path/'current'
    zero_fixture(reference, nonzero=error=='both_nonzero')
    zero_fixture(current, nonzero=error in ('both_nonzero', 'action_drift'))
    if error == 'raw_drift':
        np.savez_compressed(current/'rollout/contact_samples.npz', force=np.ones((2, 3))*.001)
    elif error == 'dtype_drift':
        np.savez_compressed(current/'rollout/physics_states.npz', q=np.arange(6, dtype=np.float32))
    elif error == 'mjb_drift':
        (current/'rollout/rollout.mjb').write_bytes(b'different-model')
    elif error == 'dynamic_json_drift':
        result = json.loads((current/'rollout/rollout.json').read_text())
        result['final_stage'] = 1
        save(current/'rollout/rollout.json', result)
    elif error == 'summary_drift':
        save(current/'metrics/episode_0/substep_metrics.json', dict(synthetic=True, samples=3))
    with pytest.raises(ValueError):
        prepare.zero_parity(reference, current)
