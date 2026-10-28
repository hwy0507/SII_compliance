"""Read-only parameter-shield recurrence and action-effect audit.

Replays recorded virtual storage inputs, not physics or the native controller.
Measures action attenuation without interpreting it as learning or passivity.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def episode(folder, method, prior, shield_class):
    report = read(folder/'CONTROLLER_REPAIR.json')
    if report['controller'] != method or report['prior'] != prior['center']:
        raise ValueError('Controller or nominal parameters differ from frozen runtime')
    trace = read(folder/'parameter_trace.json')
    journal = [json.loads(line) for line in (folder/'actor_intervals.jsonl').read_text().splitlines()]
    if len(trace) != len(journal) or not trace:
        raise ValueError('Missing or misaligned parameter trace')
    shield = shield_class(method, prior)
    errors = {}
    for saved in trace:
        shield.update(saved['raw_action'], saved['offset'], saved['velocity'])
        replayed = shield.records[-1]
        if set(replayed) != set(saved):
            raise ValueError('Shield record fields changed')
        for name in saved:
            x, y = np.asarray(replayed[name]), np.asarray(saved[name])
            if x.shape != y.shape or not np.isfinite(y).all():
                raise ValueError('Nonfinite or malformed parameter trace: '+name)
            error = float(np.max(abs(x-y)))
            errors[name] = max(errors.get(name, 0.), error)
    if max(errors.values()) > 1e-10:
        raise ValueError('Shield recurrence mismatch: '+str(errors))
    raw = np.asarray([r['raw_action'] for r in trace])
    applied = np.asarray([r['applied_parameters'] for r in trace])
    previous = np.asarray([r['previous_parameters'] for r in trace])
    requested = np.asarray([r['requested_parameters'] for r in trace])
    scale = np.asarray([r['energy_scale'] for r in trace])
    executed = np.asarray([r['executed_action'] for r in journal])
    np.testing.assert_array_equal(raw, [r['action'] for r in journal])
    with np.load(folder/'parameter_actions.npz', allow_pickle=False) as arrays:
        for name, value in [('raw_action', raw), ('parameters', applied),
                            ('executed_action', executed), ('energy_scale', scale)]:
            np.testing.assert_array_equal(arrays[name], value)
    center, bounds = np.asarray(prior['center']), np.asarray(prior['bounds'])
    desired = center*np.exp(raw*prior['action_log_span'])
    bounded = np.clip(desired, bounds[:, 0], bounds[:, 1])
    rate_limited = np.any(abs(np.log(requested/bounded)) > 1e-10, axis=1)
    if np.any(applied < bounds[:, 0]-1e-10) or np.any(applied > bounds[:, 1]+1e-10):
        raise ValueError('Applied parameters violate registered bounds')
    if np.max(abs(np.log(applied/previous))) > prior['max_log_rate_per_s']/prior['update_hz']+1e-10:
        raise ValueError('Applied parameter log-rate violates registered bound')
    terminal = read(folder/'TERMINAL.json')
    inputs = ['CONTROLLER_REPAIR.json', 'parameter_trace.json', 'parameter_actions.npz',
              'actor_intervals.jsonl', 'TERMINAL.json']
    metrics = dict(case_id=folder.name, rows=len(trace),
        strict_success=bool(terminal['result']['strict_success']),
        shield_max_abs_error=max(errors.values()),
        bound_limited_rows=int(np.any(abs(desired-bounded) > 1e-10, axis=1).sum()),
        rate_limited_rows=int(rate_limited.sum()),
        energy_limited_rows=int((scale < 1-1e-10).sum()),
        minimum_energy_scale=float(scale.min()),
        minimum_tank_j=min(r['energy_after_j'] for r in trace),
        nonzero_executed_action_rows=int(np.any(executed != 0, axis=1).sum()),
        nonnominal_parameter_rows=int(np.any(abs(np.log(applied/center)) > 1e-10, axis=1).sum()),
        action_abs_mean_per_dimension=np.mean(abs(raw), axis=0).tolist(),
        parameter_ratio_min_per_dimension=np.min(applied/center, axis=0).tolist(),
        parameter_ratio_max_per_dimension=np.max(applied/center, axis=0).tolist(),
        parameter_abs_log_ratio_mean_per_dimension=np.mean(abs(np.log(applied/center)), axis=0).tolist(),
        input_hashes={name: sha(folder/name) for name in inputs})
    return metrics


def main(args):
    os.sched_setaffinity(0, {args.cpu})
    root = args.runtime.resolve()
    for manifest, directory in [('SOURCE_HASHES.json', 'source'), ('PARAMETER_HASHES.json', 'parameter')]:
        for name, digest in read(root/manifest).items():
            if sha(root/directory/name) != digest:
                raise ValueError('Frozen runtime source changed: '+name)
    sys.path[:0] = [str(root/'source/tools'), str(root/'source/scripts'), str(root/'parameter')]
    from controllers import ParameterShield
    priors = read(root/'parameter/PRIORS.json')['methods']
    protocol = read(args.registration)
    condition_ids = {c['id'] for c in protocol['conditions']}
    args.output.mkdir(parents=True, exist_ok=False)
    result = dict(captured_unix=time.time(), run=str(args.run.resolve()), cycle=args.cycle,
        runtime=str(root), source_sha256=sha(Path(__file__)),
        runtime_manifest_sha256=sha(root/'RUNTIME.json'), registration_sha256=sha(args.registration),
        new_physics_steps=0, optimizer_updates=0, methods={},
        scope='Recorded storage-state inputs and shield recurrence only; no independent physics, '
              'native-controller reconstruction, passivity or policy-improvement claim.')
    for method in ('impedance', 'admittance', 'vmc'):
        folder = args.run/method/f'cycle_{args.cycle:05d}'
        cases = sorted(p for p in folder.iterdir() if p.is_dir())
        cycles = read(args.run/method/'CYCLES.json')['cycles']
        if not any(c['cycle'] == args.cycle for c in cycles):
            raise ValueError('Requested cycle has not completed')
        if read(args.run/method/'EXECUTION.json')['protocol_sha256'] != sha(args.registration):
            raise ValueError('Run registration mismatch')
        if {p.name for p in cases} != condition_ids:
            raise ValueError('Complete-cycle condition coverage mismatch')
        rows = [episode(p, method, priors[method], ParameterShield) for p in cases]
        counts = ('rows', 'bound_limited_rows', 'rate_limited_rows', 'energy_limited_rows',
                  'nonzero_executed_action_rows', 'nonnominal_parameter_rows')
        totals = {name: sum(r[name] for r in rows) for name in counts}
        totals.update(episodes=len(rows), parameter_keys=priors[method]['keys'],
            strict_successes=sum(r['strict_success'] for r in rows),
            shield_max_abs_error=max(r['shield_max_abs_error'] for r in rows),
            minimum_energy_scale=min(r['minimum_energy_scale'] for r in rows),
            minimum_tank_j=min(r['minimum_tank_j'] for r in rows))
        for name in ('action_abs_mean_per_dimension', 'parameter_abs_log_ratio_mean_per_dimension'):
            totals[name] = (sum(np.asarray(r[name])*r['rows'] for r in rows)/totals['rows']).tolist()
        for name, fn in [('parameter_ratio_min_per_dimension', np.min),
                         ('parameter_ratio_max_per_dimension', np.max)]:
            totals[name] = fn([r[name] for r in rows], axis=0).tolist()
        result['methods'][method] = dict(summary=totals, episodes=rows)
        (args.output/(method+'.json')).write_text(json.dumps(result['methods'][method], indent=2, allow_nan=False)+'\n')
    (args.output/'AUDIT.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--cycle', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cpu', type=int, default=54)
    main(parser.parse_args())
