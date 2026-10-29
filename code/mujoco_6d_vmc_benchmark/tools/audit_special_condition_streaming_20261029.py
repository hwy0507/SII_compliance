"""Same saved-evidence condition audit with bounded-memory substep arithmetic.

Original provenance/clock/completion checks execute verbatim. No simulation,
model selection or gate changes. This is not independent dynamics integration.
"""
import argparse
from contextlib import ExitStack
import inspect
import math
from pathlib import Path
import zipfile
from unittest.mock import patch

import numpy as np

import audit_special_frozen108_20261028 as original
import audit_special_complete_condition_20261028 as condition_audit
from collect_special_scene_coverage_20261029 import require_resources

ORIGINAL_SHA = '98bd7a7c0ae89ba6b282d2f4e5e5c6e64ef2aa4da115e8b70207426257ae95fe'
CONDITION_SHA = '64eae236f16b1973e93f8388f6737a5ffd29d5f7b451c5c3ee3dc739269e0fdc'
CHUNK_ROWS = 4096


class Rows:
    def __init__(self, archive, name, stack):
        self.stream = stack.enter_context(archive.open(name + '.npy'))
        version = np.lib.format.read_magic(self.stream)
        if version == (1, 0):
            shape, fortran, dtype = np.lib.format.read_array_header_1_0(self.stream)
        elif version == (2, 0):
            shape, fortran, dtype = np.lib.format.read_array_header_2_0(self.stream)
        else:
            raise ValueError('Unsupported NPY version')
        original.require(not fortran and len(shape) in (1, 2) and dtype.kind == 'f',
                         'Expected C-order numeric floating telemetry')
        self.shape, self.dtype = shape, dtype
        self.width = math.prod(shape[1:])
        self.remaining = shape[0]

    def read(self, count):
        original.require(0 < count <= self.remaining, 'Invalid chunk length')
        size = count * self.width * self.dtype.itemsize
        raw = self.stream.read(size)
        original.require(len(raw) == size, 'Truncated NPY data')
        self.remaining -= count
        return np.frombuffer(raw, dtype=self.dtype).reshape((count,) + self.shape[1:])

    def finish(self):
        original.require(self.remaining == 0 and not self.stream.read(1), 'Trailing or unread NPY data')


def arithmetic(run, chunk_rows=CHUNK_ROWS):
    original.require(chunk_rows > 0, 'Positive chunk required')
    sums = {k: [] for k in ('duration', 'contact', 'within', 'error', 'impulse', 'exceed')}
    peaks = dict(torque=0., penetration=-math.inf, speed=0., force=-math.inf, ratio=0.)
    threshold = np.array([43.5] * 4 + [6.] * 3)
    with ExitStack() as stack:
        metrics = stack.enter_context(zipfile.ZipFile(run/'rollout_metrics/substep_metrics.npz'))
        research = stack.enter_context(zipfile.ZipFile(run/'research_substeps.npz'))
        arrays = {k: Rows(metrics, k, stack) for k in ('dt', 'qfrc_actuator', 'error', 'twist')}
        arrays.update({k: Rows(research, k, stack) for k in
                      ('contact_force_sum', 'external_penetration_m', 'edge_penetration_m')})
        n = arrays['dt'].shape[0]
        original.require(n > 0 and all(v.shape[0] == n for v in arrays.values()), 'Substeps not aligned')
        for k in ('dt', 'external_penetration_m', 'edge_penetration_m'):
            original.require(arrays[k].shape == (n,), 'Unexpected scalar channel shape')
        for k, width in (('qfrc_actuator', 7), ('error', 3), ('twist', 6), ('contact_force_sum', 6)):
            original.require(arrays[k].shape == (n, width), 'Unexpected vector channel shape')
        for offset in range(0, n, chunk_rows):
            a = {k: v.read(min(chunk_rows, n-offset)) for k, v in arrays.items()}
            dt, torque, error, twist = [a[k].astype(float) for k in ('dt', 'qfrc_actuator', 'error', 'twist')]
            force = a['contact_force_sum'][:, 2].astype(float)
            penetration = 1000 * np.maximum(a['external_penetration_m'], a['edge_penetration_m'])
            original.require(all(np.isfinite(v).all() for v in (dt, torque, error, twist, force, penetration)),
                             'Nonfinite telemetry needs explicit failure review')
            original.require(np.allclose(dt, .00005, rtol=0, atol=1e-12), 'Physical dt mismatch')
            torque = np.abs(torque[:, :7])
            contact = force > .05
            within = np.all(torque <= threshold*(1+1e-6), axis=1)
            for key, value in (
                ('duration', dt.sum()), ('contact', dt[contact].sum()),
                ('within', dt[contact & within].sum()),
                ('error', np.sum(np.sum(error**2, axis=1)*dt)),
                ('impulse', np.sum(force[contact]*dt[contact])),
                ('exceed', dt[contact & ~within].sum())):
                sums[key].append(float(value))
            for key, value in (('torque', torque.max()), ('penetration', penetration.max()),
                               ('speed', np.linalg.norm(twist[:, :3], axis=1).max()),
                               ('force', force.max()), ('ratio', (torque/(2*threshold)).max())):
                peaks[key] = max(peaks[key], float(value))
        for v in arrays.values():
            v.finish()
    total = {k: math.fsum(v) for k, v in sums.items()}
    return dict(substeps=n, duration=total['duration'], contact=total['contact'],
                comfort=total['within']/total['contact'] if total['contact'] else None,
                rmse=1000*math.sqrt(total['error']/total['duration']),
                impulse=total['impulse'], exceed=total['exceed'], **peaks)


def streamed_checks(row, metric, summary, audit):
    a = arithmetic(Path(row['run']))
    c = row['comfort']
    np.testing.assert_array_equal(c['comfort_threshold_nm'], [43.5]*4+[6.]*3)
    for actual, expected, label in (
        (c['comfort_threshold_ratio_of_actuator_limit'], .5, 'Comfort ratio changed'),
        (c['human_force_threshold_n'], .05, 'Contact threshold changed'),
        (c['human_contact_duration_s'], a['contact'], 'Contact duration mismatch'),
        (c['human_comfort_torque_compliance'], a['comfort'], 'Comfort ratio mismatch'),
        (row['peak_torque_nm'], a['torque'], 'Raw peak torque mismatch'),
        (c['max_penetration_mm'], a['penetration'], 'Penetration mismatch'),
        (metric['rmse_mm'], a['rmse'], 'RMSE mismatch'),
        (metric['peak_speed_mps'], a['speed'], 'Peak speed mismatch'),
        (row['duration_s'], a['duration'], 'Episode duration mismatch')):
        original.equal(actual, expected, label)
    reasons = []
    if a['penetration'] > .2+1e-12:
        reasons.append('penetration_gt_0.2mm')
    if a['ratio'] > 1+1e-6:
        reasons.append('actuator_torque_gt_limit')
    if summary.get('abort_reason'):
        reasons.append('episode_abort:'+summary['abort_reason'])
    original.require(reasons == c['machine_safety_violation_reasons'] and
                     bool(reasons) == c['machine_safety_violation'], 'Machine compliance mismatch')
    return dict(method=row['method'], condition=row['condition'], substeps=a['substeps'],
                rmse_mm=a['rmse'], peak_speed_mps=a['speed'], peak_torque_nm=a['torque'],
                human_force_peak_n=a['force'], human_contact_impulse_ns=a['impulse'],
                comfort_exceed_duration_s=a['exceed'],
                failure_stage=audit.get('stage') if not row['task_success'] else None,
                abort_reason=summary.get('abort_reason'))


def verifier():
    original.require(original.sha(Path(original.__file__)) == ORIGINAL_SHA, 'Original audit changed')
    original.require(original.sha(Path(condition_audit.__file__)) == CONDITION_SHA, 'Condition audit changed')
    source = inspect.getsource(original.verify_episode)
    marker = "    with np.load(run / 'rollout_metrics/substep_metrics.npz', allow_pickle=False) as z:"
    original.require(source.count(marker) == 1, 'Unexpected original audit structure')
    prefix = source.split(marker)[0]
    original.require(prefix.rstrip().endswith("equal(row['completion_time_s'], completion, 'Completion time mismatch')"),
                     'Original completion checks must be preserved')
    scope = dict(original.__dict__, streamed_checks=streamed_checks)
    exec(compile(prefix+'    return streamed_checks(row, metric, summary, audit)\n', __file__, 'exec'), scope)
    return scope['verify_episode']


def audit(preparation, condition):
    resources = require_resources()
    with patch.object(condition_audit, 'verify_episode', verifier()):
        result = condition_audit.audit_condition(preparation, condition)
    result['original_condition_auditor_sha256'] = result['auditor_sha256']
    result['auditor_sha256'] = original.sha(Path(__file__))
    result['substep_arithmetic'] = 'all rows, streamed in chunks; unchanged formulas/thresholds; stable partial sums'
    result['chunk_rows'] = CHUNK_ROWS
    result['resources'] = resources
    peak_path = Path(resources['cgroup'])/'memory.peak'
    result['resources']['memory_peak_bytes'] = int(peak_path.read_text())
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--condition', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    original.require(not args.output.exists(), 'Preserve prior audit')
    result = audit(args.preparation.resolve(), args.condition)
    from collect_special_scene_actions_20261028 import write
    write(args.output, result)
    print(result['status'], result['verified_substeps'])
