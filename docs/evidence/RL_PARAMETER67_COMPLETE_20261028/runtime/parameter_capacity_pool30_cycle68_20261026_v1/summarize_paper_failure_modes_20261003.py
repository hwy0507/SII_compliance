"""Describe all final failure signatures from independent sampled-state audits.

These are overlapping observed conditions, not proven causal explanations or
new success gates. Development, designed, random and formal cohorts stay apart.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--placement-audits', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    report_hash = sha(a.report)
    report = json.loads(a.report.read_text())
    execution = a.placement_audits/'execution.json'
    state = json.loads(execution.read_text())
    assert state['status'] == 'complete' and state['report_sha256'] == report_hash
    assert len(state['rows']) == len(report['rows'])
    rows = []
    grouped = defaultdict(list)
    for index, (source, audited) in enumerate(zip(report['rows'], state['rows'])):
        assert source['run'] == audited['run'] and source['trace_sha256'] == audited['trace_sha256']
        row = {k: source[k] for k in ('name', 'tier', 'condition', 'run', 'task_success', 'strict_success', 'stage', 'trace_sha256')}
        labels = []
        if not source['full_horizon']:
            assert audited['status'] == 'aborted_failure_preserved'
            labels.append('safety_abort:' + source['abort_reason'])
        else:
            path = a.placement_audits/(f'{index:03d}_' + source['name'] + '.json')
            assert sha(path) == audited['audit_sha256']
            check = json.loads(path.read_text())
            assert check['task_success'] == source['task_success']
            final = check['independent_final_state_checks'][0]
            row.update(final_sample=final, audit_sha256=sha(path),
                       valid_final_13_samples=sum(c['valid'] for c in check['independent_final_state_checks']))
            if not source['task_success']:
                if check['max_lift_from_saved_frames_m'] <= .1: labels.append('insufficient_lift')
                if final['xy_error_m'] >= .025: labels.append('final_xy_outside_target')
                if final['z_error_m'] >= .015: labels.append('final_height_outside_target')
                if not final['supported']: labels.append('no_final_target_surface_support')
                if final['robot_contact']: labels.append('final_payload_robot_contact')
                if not final['open_fingers']: labels.append('fingers_not_fully_open')
                if final['speed_mps'] >= .015: labels.append('payload_linear_speed_above_gate')
                if final['angular_speed_radps'] >= .15: labels.append('payload_angular_speed_above_gate')
                if not all(c['valid'] for c in check['independent_final_state_checks']):
                    labels.append('final_13_sample_hold_not_satisfied')
        if source['penetration_mm'] > .2: labels.append('external_penetration_above_gate')
        if source['edge_penetration_mm'] > .2: labels.append('edge_penetration_above_gate')
        assert bool(labels) == (not source['strict_success'])
        row['observed_signatures'] = labels
        rows.append(row); grouped[(source['tier'], source['name'])].append(row)
    groups = []
    for (tier, name), sample in grouped.items():
        groups.append(dict(tier=tier, name=name, n=len(sample),
                           task_successes=sum(r['task_success'] for r in sample),
                           strict_successes=sum(r['strict_success'] for r in sample),
                           signature_counts=dict(Counter(s for r in sample for s in r['observed_signatures']))))
    assert sha(a.report) == report_hash
    result = dict(created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=sha(Path(__file__)),
                  report_sha256=report_hash, placement_audit_index_sha256=sha(execution), rows=rows, groups=groups,
                  limitations=['Post-hoc descriptive classification, not a new gate or selection endpoint.',
                      'Labels overlap; their counts must not be summed as independent failures.',
                      'Final states establish failure signatures, not which algorithmic mechanism caused them.',
                      'Target support and robot contact are reconstructed at saved 25 Hz states.',
                      'Every failed, successful and aborted selected row is included; cohorts remain separate.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps(dict(rows=len(rows), groups=len(groups), sha256=sha(a.output))))


if __name__ == '__main__':
    main()
