"""Atomic read-only training snapshots; separate random/mixed/learned episodes.

No model selection, simulation, updates, or final-condition access. A running
episode is never silently counted as a completed failure or success.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from office_v7_uniform24_20261008 import read, write, sha, now


def inspect(segment):
    payload = (segment/'execution.json').read_bytes()
    state = json.loads(payload)
    spec = read(segment/'PROTOCOL.json')
    warmup = spec['warmup_steps']
    rows = []
    for row in state['rows']:
        if 'result' not in row:
            continue
        run = Path(row['run'])
        assert sha(run/'AUDIT.json') == row['audit_sha256']
        audit = read(run/'AUDIT.json')
        split = ('random_warmup' if row['step_after'] <= warmup else
                 'learned_behavior' if row['step_before'] >= warmup else 'mixed_warmup_and_learning')
        with np.load(run/'baseline_policy.npz', allow_pickle=False) as trace:
            raw = trace['raw_action'].astype(float)
            assert len(raw) == row['steps'] and np.isfinite(raw).all()
            statistics = dict(mean=raw.mean(0).tolist(), std=raw.std(0).tolist(),
                abs95_fraction=float(np.mean(abs(raw) >= .95)),
                mean_absolute_change=float(abs(np.diff(raw, axis=0)).mean()))
        rows.append(dict(episode=row['episode'], condition=row['condition_id'], group=split,
            steps=row['steps'], step_before=row['step_before'], step_after=row['step_after'],
            task=audit['task_success'], strict=audit['strict_success'], full_horizon=audit['full_horizon'],
            final_stage=audit['stage'], rmse_mm=audit['rmse_mm'], peak_torque_nm=audit['peak_torque_nm'],
            peak_speed_mps=audit['peak_speed_mps'], penetration_mm=audit['penetration_mm'],
            placement_error_xy_m=audit['placement_error_xy_m'], abort_reason=audit['abort_reason'],
            raw_action=statistics, audit_sha256=row['audit_sha256'], trace_sha256=row['trace_sha256']))
    groups = {}
    for name in ('random_warmup','mixed_warmup_and_learning','learned_behavior'):
        selected = [r for r in rows if r['group'] == name]
        groups[name] = dict(episodes=len(selected), task=sum(r['task'] for r in selected),
                           strict=sum(r['strict'] for r in selected))
    first = last = None
    optimizers = 0
    path = segment/'optimizer.jsonl'
    if path.exists():
        with path.open('rb') as stream:
            for line in stream:
                if not line.endswith(b'\n'):
                    break
                record = json.loads(line)
                # Snapshot membership: a running writer may advance after the
                # captured execution receipt. Later updates are not this snapshot.
                if record['step'] > state['steps']:
                    break
                assert all(np.isfinite(v) for v in record['metrics'].values())
                first = record if first is None else first
                last = record
                optimizers += 1
    return dict(segment=str(segment), status=state['status'],
        captured_execution_sha256=hashlib.sha256(payload).hexdigest(),
        training_protocol_sha256=sha(segment/'PROTOCOL.json'), steps=state['steps'],
        updates=state.get('updates'), inherited_steps=state.get('resumed_from',{}).get('inherited_steps',0),
        groups=groups, episodes=rows, unfinished_episodes=len(state['rows'])-len(rows),
        complete_optimizer_rows_through_snapshot=optimizers, first_optimizer=first, last_optimizer=last,
        checkpoints=[dict(path=r['path'], step=r['step'], file_count=len(r['hashes'])) for r in state['checkpoint_rows']],
        interpretation='Within-training behavior on differing identities, not a paired evaluation or trained-policy success rate. Warmup/mixed excluded from learned group.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    jobs = read(a.root/'PROTOCOL.json')['jobs']
    names = ['direct_office_task_smoke']+[j['name']+'_segment011k' for j in jobs]
    report = dict(created_utc=now(), source_sha256=sha(__file__), segments=[], not_started=[],
                  new_physics_steps=0, gradient_updates=0, heldout_reads=0)
    for name in names:
        if (a.root/name/'execution.json').exists():
            report['segments'].append(inspect(a.root/name))
        else:
            report['not_started'].append(name)
    write(a.output, report)
    for s in report['segments']:
        print(Path(s['segment']).name, s['status'], s['steps'], s['groups'])


if __name__ == '__main__':
    main()
