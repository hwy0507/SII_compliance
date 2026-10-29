"""Qualify saved demonstrations, retaining failures and original task gates.

Recomputes substep arithmetic and binds source/data hashes. This does not
re-integrate MuJoCo and does not certify the frozen test Task/Strict gates.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

import mujoco
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def qualify(folder):
    destination = folder / 'DEMONSTRATION_QUALIFICATION.json'
    if destination.exists():
        raise FileExistsError(destination)
    execution = read(folder / 'execution.json')
    legacy = read(folder / 'legacy.json')
    actor_audit = read(folder / 'INDEPENDENT_AUDIT.json')
    inputs = ['execution.json', 'legacy.json', 'teacher.json', 'scene.mjb',
              'trajectory.npz', 'filter.npz', 'substeps.npz',
              'SOURCE_HASHES.json', 'source.tar.gz', 'INDEPENDENT_AUDIT.json']
    if execution['scene'] == 'rod':
        inputs.append('ROD_YIELD_REJOIN_AUDIT_V3.json')
    hashes = {name: sha(folder / name) for name in inputs}
    for key, name in [('model_sha256', 'scene.mjb'),
                      ('trajectory_sha256', 'trajectory.npz'),
                      ('substeps_sha256', 'substeps.npz'),
                      ('teacher_config_sha256', 'teacher.json')]:
        if execution[key] != hashes[name]:
            raise ValueError(f'Execution hash mismatch: {name}')
    for name, digest in actor_audit['input_hashes'].items():
        if sha(folder / name) != digest:
            raise ValueError(f'Stale actor audit: {name}')
    source_hashes = read(folder / 'SOURCE_HASHES.json')
    with tarfile.open(folder / 'source.tar.gz') as archive:
        for name, digest in source_hashes.items():
            if hashlib.sha256(archive.extractfile(name).read()).hexdigest() != digest:
                raise ValueError(f'Source archive mismatch: {name}')
    wrapper = 'tools/run_registered_special_coverage_20261029.py'
    if source_hashes.get(wrapper) != execution['wrapper_sha256']:
        raise ValueError('Missing or mismatched executed wrapper source')
    with np.load(folder / 'substeps.npz', allow_pickle=False) as z:
        raw = {key: z[key] for key in z.files}
    with np.load(folder / 'trajectory.npz', allow_pickle=False) as z:
        trajectory = {key: z[key] for key in z.files}
    n = len(raw['time'])
    assert raw['torque'].shape == raw['joint_velocity'].shape == (n, 7)
    assert all(raw[k].shape == (n,) for k in
               ['time', 'dt', 'external_penetration_m', 'disturbance_force_n'])
    assert n == execution['substeps'] == execution['steps'] * 800
    assert execution['physics_dt_s'] == .00005
    np.testing.assert_allclose(raw['dt'], .00005, atol=0, rtol=0)
    np.testing.assert_allclose(raw['time'], np.arange(1, n + 1) * .00005,
                               atol=1e-8, rtol=0)
    np.testing.assert_allclose(raw['time'][799::800], trajectory['time'], atol=1e-8, rtol=0)
    finite = all(np.isfinite(v).all() for v in (*raw.values(), *trajectory.values()))
    model = mujoco.MjModel.from_binary_path(str(folder / 'scene.mjb'))
    # Existing FR3 motors have direct unit gear; no arbitrary ctrl/torque
    # conversion is inferred for a different actuator configuration.
    np.testing.assert_array_equal(model.actuator_gear[:7, 0], np.ones(7))
    limits = np.max(np.abs(model.actuator_ctrlrange[:7]), axis=1)
    np.testing.assert_array_equal(limits, execution['actuator_torque_limits_nm'])
    peak = np.max(np.abs(raw['torque']), axis=0)
    np.testing.assert_array_equal(peak, execution['peak_torque_nm'])
    max_penetration = float(np.max(raw['external_penetration_m']))
    contacts = execution['contacts']
    recorded_penetration = max((v['max_penetration_m'] for v in contacts.values()), default=0.)
    np.testing.assert_allclose(max_penetration, recorded_penetration, atol=1e-12, rtol=0)
    checks = dict(complete=execution['status'] == 'complete', finite=bool(finite),
                  penetration_within_02mm=max_penetration <= .0002,
                  actuator_limits=bool(np.all(peak <= limits + 1e-8)),
                  actor_filter_replay=actor_audit['status'] == 'passed')
    scene = execution['scene']
    if scene == 'corner':
        task = bool(legacy['object_placed_on_table'] and legacy['scenario_success'])
        contact = bool(legacy['valid_contact'] and legacy['first_apron_contact_s'] is not None)
        checks['no_legacy_physics_failure'] = not any(
            'physics' in s or 'penetration' in s or 'upstream' in s
            for s in legacy.get('failure_reasons', []))
    else:
        task = bool(legacy['success'])
        hand_names = {'hand', 'fr3_hand', 'left_finger', 'right_finger'}
        name = 'push_rod_geom' if scene == 'rod' else 'primitive_free_ball_geom'
        physical_hand = any(v['duration_s'] > 0. and v['peak_force_n'] > .05
                            for body, v in contacts.get(name, {}).get('per_body', {}).items()
                            if body in hand_names)
        contact = bool(legacy['real_contact'] and physical_hand)
        checks['no_legacy_physics_failure'] = not bool(legacy['invalid_physics'])
        if scene == 'rod':
            behavior = read(folder / 'ROD_YIELD_REJOIN_AUDIT_V3.json')
            for name, digest in behavior['hashes'].items():
                if (folder / name).is_file() and sha(folder / name) != digest:
                    raise ValueError(f'Stale rod behavior audit: {name}')
            contact = bool(contact and behavior['status'] == 'passed')
    safety = all(checks.values())
    force_contact = raw['disturbance_force_n'] > .05
    contact_dt = float(np.sum(raw['dt'][force_contact]))
    comfortable = np.all(np.abs(raw['torque']) <= .5 * limits, axis=1)
    result = dict(schema='sii-real-special-demonstration-qualification-v1',
                  status='qualified' if task and safety and contact else 'failed_preserved',
                  scene=scene, task_success=task, safety_valid=safety, scene_contact_valid=contact,
                  checks=checks, trajectory_sha256=hashes['trajectory.npz'],
                  execution_sha256=hashes['execution.json'], input_hashes=hashes,
                  audit_source_sha256=sha(Path(__file__)), substeps=n,
                  metrics=dict(peak_torque_nm=peak.tolist(),
                               peak_joint_velocity_radps=np.max(np.abs(raw['joint_velocity']), axis=0).tolist(),
                               max_external_penetration_m=max_penetration,
                               disturbance_contact_s=contact_dt,
                               disturbance_contact_comfort_proxy=(float(np.sum(raw['dt'][force_contact & comfortable])) / contact_dt
                                                                  if contact_dt else None)),
                  limitations='Saved substep arithmetic, not independent dynamics integration. Rod/ball disturbance contact is a proxy, not measured human contact. Development scene gates, not frozen test certification.')
    destination.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    print(json.dumps(qualify(parser.parse_args().folder.resolve()), indent=2))
