"""Report the sampled placement-gate time without altering original results.

The first report interpolated the credited hold to 0.5 s. The existing gate
requires thirteen 0.04 s samples (0.52 s credited), so its observed crossing is
0.02 s later. This diagnostic preserves the original column and adds the exact
sample index derived from the saved final contiguous hold counter.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    report_hash = sha(a.report)
    data = json.loads(a.report.read_text())
    rows = []
    for original in data['rows']:
        row = {k: original[k] for k in ('name', 'tier', 'condition', 'run', 'task_success', 'strict_success', 'trace_sha256')}
        row.update(original_interpolated_estimate_s=original['final_stable_placement_reached_s'],
                   sampled_gate_crossing_s=None, final_valid_sample_count=0)
        if original['task_success']:
            run = Path(original['run'])
            summary = json.loads((run/'rollout.json').read_text())
            assert sha(run/'rollout.npz') == original['trace_sha256']
            n = round(summary['placement_hold_s'] / .04)
            assert abs(n * .04 - summary['placement_hold_s']) < 1e-7
            assert summary['task_success'] and original['full_horizon'] and n >= 13
            with np.load(run/'rollout.npz', allow_pickle=False) as z:
                t = z['time']
                assert len(t) == 1375 and n <= len(t)
                np.testing.assert_allclose(np.diff(t), .04, rtol=0, atol=1e-8)
                sample_index = len(t) - n + 12
                exact = float(t[sample_index])
                assert abs(exact - original['final_stable_placement_reached_s'] - .02) < 1e-6
                row.update(sampled_gate_crossing_s=exact, final_valid_sample_count=n,
                           sample_index=sample_index, first_final_valid_sample_s=float(t[len(t)-n]),
                           correction_s=exact-original['final_stable_placement_reached_s'],
                           summary_sha256=sha(run/'rollout.json'))
        else:
            assert original['final_stable_placement_reached_s'] is None
        rows.append(row)
    assert sha(a.report) == report_hash
    result = dict(created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=sha(Path(__file__)),
                  report_sha256=report_hash, rows=rows,
                  gate_changed=False, original_reports_preserved=True,
                  limitations=['Saved contiguous hold counter establishes onset; independent placement audit reconstructs the final thirteen states.',
                      'This is a 25 Hz sampled gate time, not continuous substep support verification.',
                      'Original final_stable_placement_reached_s interpolates credited hold and is 0.02 s earlier.',
                      'Use sampled_gate_crossing_s for absolute completion time. Paired time differences are unchanged to floating-point tolerance.',
                      'Failed tasks have no completion time and retain their success denominator.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps(dict(rows=len(rows), successful_rows=sum(r['task_success'] for r in rows), sha256=sha(a.output))))


if __name__ == '__main__':
    main()
