"""Post-hoc sampled trajectory divergence; no dynamics, fitting or selection.

Compare every prequalified formal model with its frozen development anchor.
This diagnoses sensitivity between two resolutions, not a convergence proof.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def first_crossing(time, values, threshold):
    indices = np.flatnonzero(values > threshold)
    return float(time[indices[0]]) if len(indices) else None


def transitions(time, stages):
    indices = np.r_[0, np.flatnonzero(np.diff(stages)) + 1]
    return [dict(time_s=float(time[i]), stage=int(stages[i])) for i in indices]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    report_hash = sha(a.report)
    report = json.loads(a.report.read_text())
    dev = {r['name']: r for r in report['rows'] if r['tier'] == 'development'}
    formal = [r for r in report['rows'] if r['tier'] == 'formal_resolution']
    assert len(formal) == 7
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    windows = [('before_ball', 0., 2.), ('ball_to_hand', 2., 4.),
               ('hand_to_rod', 4., 13.), ('rod_command', 13., 22.5),
               ('after_rod_command', 22.5, 55.01)]
    rows, curves = [], []
    for f in formal:
        d = dev[f['name']]
        assert d['full_horizon'] and f['full_horizon']
        paths = [Path(row['run']) / 'rollout.npz' for row in (d, f)]
        for path, row in zip(paths, (d, f)):
            assert sha(path) == row['trace_sha256']
        with np.load(paths[0], allow_pickle=False) as x, np.load(paths[1], allow_pickle=False) as y:
            t = x['time'].copy()
            assert len(t) == 1375 and np.max(np.abs(t - y['time'])) < 1e-6
            hand = 1000 * np.linalg.norm(x['hand'] - y['hand'], axis=1)
            payload = 1000 * np.linalg.norm(x['object_position'] - y['object_position'], axis=1)
            action = np.max(np.abs(x['applied_action'] - y['applied_action']), axis=1)
            joint = np.max(np.abs(x['qpos'][:, :7] - y['qpos'][:, :7]), axis=1)
            mismatch = (x['stage'] != y['stage'])
            metrics = dict(hand_mm=hand, payload_mm=payload, action_linf=action, joint_linf_rad=joint)
            item = dict(name=f['name'], development_run=d['run'], formal_run=f['run'],
                        development_trace_sha256=d['trace_sha256'], formal_trace_sha256=f['trace_sha256'],
                        development_task=d['task_success'], formal_task=f['task_success'],
                        development_strict=d['strict_success'], formal_strict=f['strict_success'],
                        sample_alignment_max_abs_s=float(np.max(np.abs(t - y['time']))),
                        first_hand_above_mm={str(v): first_crossing(t, hand, v) for v in (1., 5., 10.)},
                        first_payload_above_mm={str(v): first_crossing(t, payload, v) for v in (1., 5., 10.)},
                        first_action_above={str(v): first_crossing(t, action, v) for v in (.01, .1)},
                        first_stage_mismatch_s=first_crossing(t, mismatch, .5),
                        stage_mismatch_samples=int(mismatch.sum()),
                        development_transitions=transitions(t, x['stage']),
                        formal_transitions=transitions(t, y['stage']), windows={})
            for label, start, stop in windows:
                mask = (t >= start - 1e-8) & (t < stop - 1e-8)
                item['windows'][label] = dict(start_s=start, stop_s=stop, n=int(mask.sum()),
                    **{key + '_max': float(values[mask].max()) for key, values in metrics.items()})
            rows.append(item)
            curves.append((t, hand, payload, action))
        for path, row in zip(paths, (d, f)):
            assert sha(path) == row['trace_sha256']
    assert sha(a.report) == report_hash
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(len(rows), 2, figsize=(13, 2.4 * len(rows)), sharex=True)
    for i, (row, (t, hand, payload, action)) in enumerate(zip(rows, curves)):
        ax, bx = axes[i]
        ax.plot(t, np.maximum(hand, 1e-6), label='hand difference')
        ax.plot(t, np.maximum(payload, 1e-6), label='payload difference', alpha=.8)
        ax.set_yscale('log'); ax.set_ylabel('distance (mm)')
        ax.set_title(row['name'], fontsize=9)
        bx.plot(t, action, color='tab:orange'); bx.set_ylabel('action difference (L-inf)')
        bx.set_title('task: development=' + str(row['development_task']) + ', formal=' + str(row['formal_task']), fontsize=9)
        for panel in (ax, bx):
            panel.grid(alpha=.2)
            for value in (2., 4., 13., 22.5):
                panel.axvline(value, color='gray', alpha=.3, linewidth=.7)
        if i == 0: ax.legend(fontsize=8)
    for ax in axes[-1]: ax.set_xlabel('recorded time (s)')
    fig.suptitle('Same frozen anchor: dt=1e-4 vs 5e-5 (post-hoc 25 Hz trajectory diagnostic)', fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, .975))
    fig.savefig(out/'divergence.png', dpi=140)
    fig.savefig(out/'divergence.pdf')
    plt.close(fig)
    result = dict(created_utc=datetime.now(timezone.utc).isoformat(), host=platform.node(),
                  python=sys.executable, argv=sys.argv, source_sha256=sha(Path(__file__)),
                  report_sha256=report_hash, rows=rows,
                  limitations=['Post-hoc diagnostic; not used for training, selection, or gate changes.',
                    '25 Hz saved states/actions; threshold times are sampled, not exact physical event times.',
                    'Two resolutions establish sensitivity, not the true solution or convergence order.',
                    'After state/phase divergence, reference progress and contact histories can differ.',
                    'Windows denote the anchor command schedule, not equalized actual contact exposure.'],
                  artifacts={name: sha(out/name) for name in ('divergence.png', 'divergence.pdf')})
    with (out/'DIVERGENCE.json').open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    with (out/'thresholds.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['name', 'first_hand_1mm_s', 'first_payload_1mm_s',
            'first_stage_mismatch_s', 'before_ball_hand_max_mm', 'before_ball_payload_max_mm'])
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(name=row['name'], first_hand_1mm_s=row['first_hand_above_mm']['1.0'],
                first_payload_1mm_s=row['first_payload_above_mm']['1.0'],
                first_stage_mismatch_s=row['first_stage_mismatch_s'],
                before_ball_hand_max_mm=row['windows']['before_ball']['hand_mm_max'],
                before_ball_payload_max_mm=row['windows']['before_ball']['payload_mm_max']))
    print(json.dumps(dict(models=len(rows), output=str(out), report_sha256=report_hash)))


if __name__ == '__main__':
    main()
