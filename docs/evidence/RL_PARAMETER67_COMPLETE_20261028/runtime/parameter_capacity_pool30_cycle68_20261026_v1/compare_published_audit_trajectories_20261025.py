"""Check observational instrumentation against an identical deterministic run."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def compare(original, instrumented):
    report = dict(original=str(original), instrumented=str(instrumented), arrays={})
    for name in ('rollout.npz', 'rollout_metrics/substep_metrics.npz', 'rollout_ball_detail.npz'):
        with np.load(original/name, allow_pickle=False) as left, np.load(instrumented/name, allow_pickle=False) as right:
            if set(left.files) != set(right.files):
                raise ValueError('Archive fields changed: '+name)
            fields = {}
            for key in left.files:
                x, y = left[key], right[key]
                same_shape = x.shape == y.shape
                # The original task logger uses NaN for an unavailable carry
                # load outside the corresponding gate. This allowance never
                # applies to state, action, torque or any physical telemetry.
                allow_na = name == 'rollout.npz' and key == 'task_carry_load'
                mask_equal = same_shape and np.array_equal(np.isnan(x), np.isnan(y))
                finite = np.isfinite(x) & np.isfinite(y) if same_shape else None
                valid = same_shape and (mask_equal if allow_na else bool(np.all(finite)))
                valid = valid and not np.isinf(x).any() and not np.isinf(y).any()
                exact = bool(valid and np.array_equal(x[finite], y[finite]))
                fields[key] = dict(exact=exact, shape=list(x.shape),
                    allowed_unavailable_entries=int(np.isnan(x).sum()) if allow_na else 0,
                    maximum_finite_abs_difference=float(np.max(abs(x[finite].astype(float)-y[finite].astype(float))))
                        if same_shape and np.any(finite) else None)
            report['arrays'][name] = fields
    report['identical_files'] = {name: (original/name).read_bytes() == (instrumented/name).read_bytes()
        for name in ('rollout.mjb', 'actor_intervals.jsonl', 'TERMINAL.json')}
    report['checkpoint_identical'] = (original.parent/'checkpoint_frozen.pt').read_bytes() == (
        instrumented.parent/'checkpoint_frozen.pt').read_bytes()
    report['passed'] = bool(report['checkpoint_identical'] and all(report['identical_files'].values())
        and all(field['exact'] for fields in report['arrays'].values() for field in fields.values()))
    report['source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--instrumented', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.original, args.instrumented)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'arrays'}, indent=2))
    if not report['passed']:
        raise SystemExit('Observational instrumentation changed trajectory evidence')
