"""Replay recorded common torque projection and link it to physical substeps.

Native Cartesian wrench/reference/Jacobian generation is not reconstructed.
The audit covers the subsequent velocity-servo projection, bounds, slew,
previous-command recurrence and actual seven-joint actuator torque linkage.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay_arrays(metadata, arrays, physical, projection, config_class):
    config = config_class(**metadata['config'])
    count = len(arrays['time'])
    if not count:
        raise ValueError('Empty torque projection trace')
    for key in ('time', 'dt', 'scale', 'bias', 'measured', 'command', 'previous', 'limits', 'applied'):
        shape = (count,) if key in ('time', 'dt', 'scale') else (count, 7)
        if arrays[key].shape != shape or not np.isfinite(arrays[key]).all():
            raise ValueError('Invalid torque telemetry: '+key)
    if not np.all(arrays['dt'] == .004) or not np.all(np.diff(arrays['time']) > 0):
        raise ValueError('Torque servo clock differs from registered .004s')
    if not np.array_equal(arrays['limits'], np.broadcast_to(metadata['torque_limits'], (count, 7))):
        raise ValueError('Torque limits differ from original environment')
    previous = np.asarray(metadata['initial_previous_torque'])
    for i in range(count):
        if not np.array_equal(previous, arrays['previous'][i]):
            raise ValueError(f'Torque recurrence mismatch at servo {i}')
        applied, scale = projection(arrays['bias'][i], arrays['measured'][i], arrays['command'][i],
            previous, arrays['dt'][i], config, torque_limits=arrays['limits'][i])
        if not np.array_equal(applied, arrays['applied'][i]) or scale != arrays['scale'][i]:
            raise ValueError(f'Torque replay mismatch at servo {i}')
        if np.any(abs(applied) > arrays['limits'][i]+1e-12):
            raise ValueError('Torque amplitude bound violated')
        if np.any(abs(applied-previous) > np.asarray(config.maximum_torque_rate_nmps)*.004+1e-10):
            raise ValueError('Torque slew bound violated')
        previous = applied
    if physical.shape != (count*80, 11) or not np.isfinite(physical).all():
        raise ValueError('Physical audit does not cover every .004s servo / 80 substeps')
    if not np.all(physical[:, 0] == .00005):
        raise ValueError('Physical timestep drift')
    expected_times = arrays['time'][:, None]+np.arange(1, 81)[None, :]*.00005
    clock_error = float(np.max(abs(physical[:, 10].reshape(count, 80)-expected_times)))
    if clock_error > 1e-9:
        raise ValueError('Physical/servo clock alignment failed')
    physical_torques = physical[:, 1:8].reshape(count, 80, 7)
    if not np.array_equal(physical_torques, np.broadcast_to(arrays['applied'][:, None, :], physical_torques.shape)):
        raise ValueError('Actual actuator torques differ from replayed servo output')
    return dict(servo_calls=count, physical_substeps=count*80,
        projection_replay_max_abs=0., previous_torque_recurrence_exact=True,
        actuator_torque_linkage_exact=True, maximum_clock_alignment_error_s=clock_error,
        amplitude_and_slew_verified=True,
        scaled_projection_calls=int(np.sum(arrays['scale'] < 1.)))


def audit(folder):
    extension = json.loads((folder/'AUDIT_EXTENSION.json').read_text())
    if not extension['completed']:
        raise ValueError('Incomplete observational episode')
    for name, field in [('audit_torque.json', 'torque_metadata_sha256'),
                        ('audit_torque.npz', 'torque_trace_sha256'), ('audit_substeps.npy', 'substeps_sha256')]:
        if sha(folder/name) != extension[field]:
            raise ValueError('Torque audit evidence hash mismatch: '+name)
    root = Path(json.loads((folder/'ADAPTER.json').read_text())['runtime'])
    source = root/'source/scripts/wbc_velocity_residual_core.py'
    metadata = json.loads((folder/'audit_torque.json').read_text())
    hashes = json.loads((root/'SOURCE_HASHES.json').read_text())
    if sha(source) != hashes['scripts/wbc_velocity_residual_core.py'] or sha(source) != metadata['source_sha256']:
        raise ValueError('Frozen torque projection source mismatch')
    name = 'independent_frozen_torque_projection'
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    with np.load(folder/'audit_torque.npz', allow_pickle=False) as trace:
        arrays = {key: trace[key] for key in trace.files}
    if len(arrays['time']) != extension['torque_samples']:
        raise ValueError('Torque receipt count mismatch')
    physical = np.load(folder/'audit_substeps.npy', mmap_mode='r', allow_pickle=False)[:extension['samples']]
    result = replay_arrays(metadata, arrays, physical,
        module.safe_velocity_tracking_torque, module.VelocityResidualSafetyConfig)
    return dict(result, passed=True, simulation_steps=0, source_sha256=sha(Path(__file__)),
        frozen_projection_sha256=sha(source),
        scope='Common torque projection, amplitude/slew, previous-output recurrence and physical torque linkage',
        native_reference_wrench_and_jacobian_reconstructed=False,
        evidence_sha256={name: sha(folder/name) for name in ['audit_torque.json', 'audit_torque.npz',
            'AUDIT_EXTENSION.json', 'audit_substeps.npy']})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episode', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(audit(args.episode), stream, indent=2, allow_nan=False)
        stream.write('\n')
