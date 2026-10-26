"""Independently replay the saved public action filter, without physics updates.

Verifies the frozen filter source/config, reset state, inputs linked to the actor
journal, all returned values and saturation/rate-limit flags. It does not claim
to replay the native torque controller, downstream WBC authority override, or
joint actuator safety layer.
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


def replay_arrays(metadata, arrays, requested, filter_class, config_class):
    if metadata['observation_mode'] != 'direct_esn' or metadata['execution_mode'] != 'twist':
        raise ValueError('Actor-to-filter linkage requires the registered direct_esn twist execution')
    filt = filter_class(config_class(**metadata['config']))
    if filt.wbc_scale != metadata['initial_wbc_scale'] or not np.array_equal(
            filt.cartesian_yield_twist, metadata['initial_yield_twist']):
        raise ValueError('Recorded filter did not start at the frozen reset state')
    count = len(requested)
    if not count or requested.shape != (count, 7) or not np.isfinite(requested).all():
        raise ValueError('Invalid actor journal actions')
    shapes = dict(requested_action=(count, 7), dt=(count,), wbc_scale=(count,),
        yield_twist=(count, 6), clipped=(count, 7), amplitude_saturated=(count,), slew_limited=(count,))
    for key, shape in shapes.items():
        if arrays[key].shape != shape or not np.isfinite(arrays[key]).all():
            raise ValueError('Invalid filter telemetry: '+key)
    if not np.all(arrays['dt'] == .04):
        raise ValueError('Filter clock differs from registered actor period')
    if not np.array_equal(arrays['requested_action'], np.clip(requested, -1., 1.)):
        raise ValueError('Actor journal and actual filter inputs differ')
    for i in range(count):
        result = filt.filter(arrays['requested_action'][i], arrays['dt'][i])
        expected = dict(wbc_scale=result.wbc_scale, yield_twist=result.cartesian_yield_twist,
            clipped=result.raw_action_clipped, amplitude_saturated=result.amplitude_saturated,
            slew_limited=result.slew_limited)
        for key, value in expected.items():
            if not np.array_equal(value, arrays[key][i]):
                raise ValueError(f'Filter replay differs at decision {i}: {key}')
    return dict(decisions=count, common_filter_replay_max_abs=0.,
        actor_journal_to_filter_inputs_exact=True, flags_exact=True)


def audit(folder):
    extension = json.loads((folder/'AUDIT_EXTENSION.json').read_text())
    if not extension['completed']:
        raise ValueError('Episode audit did not complete')
    for name, field in [('audit_filter.json', 'filter_metadata_sha256'),
                        ('audit_filter.npz', 'filter_trace_sha256')]:
        if sha(folder/name) != extension[field]:
            raise ValueError('Filter evidence hash mismatch: '+name)
    adapter = json.loads((folder/'ADAPTER.json').read_text())
    root = Path(adapter['runtime'])
    source = root/'source/scripts/wbc_velocity_residual_core.py'
    metadata = json.loads((folder/'audit_filter.json').read_text())
    hashes = json.loads((root/'SOURCE_HASHES.json').read_text())
    if sha(source) != hashes['scripts/wbc_velocity_residual_core.py'] or sha(source) != metadata['source_sha256']:
        raise ValueError('Frozen public filter source mismatch')
    name = 'independent_frozen_public_filter'
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    requested = np.asarray([json.loads(line)['executed_action']
        for line in (folder/'actor_intervals.jsonl').read_text().splitlines()])
    with np.load(folder/'audit_filter.npz', allow_pickle=False) as trace:
        arrays = {key: trace[key] for key in trace.files}
    if extension['filter_samples'] != len(requested):
        raise ValueError('Filter receipt/journal counts disagree')
    with np.load(folder/'rollout.npz', allow_pickle=False) as physical:
        if not np.array_equal(requested, physical['applied_action']):
            raise ValueError('Actor journal actions differ from physical trace')
    result = replay_arrays(metadata, arrays, requested,
        module.VelocityResidualActionFilter, module.VelocityResidualSafetyConfig)
    return dict(result, passed=True, filter_replay_verified=True,
        scope='public filter inputs, state recurrence, clipping, slew limiting and returned values',
        native_controller_or_actuator_layer_replayed=False,
        downstream_wbc_authority_override_replayed=False, simulation_steps=0,
        source_sha256=sha(Path(__file__)), frozen_filter_source_sha256=sha(source),
        evidence_sha256={name: sha(folder/name) for name in ['audit_filter.json', 'audit_filter.npz',
            'AUDIT_EXTENSION.json', 'actor_intervals.jsonl', 'rollout.npz']})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episode', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.episode)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, indent=2))
