"""Account actual physical episodes and optimizer work, including discarded work.

Never sum inherited step/update counters. Rebuilt source_episode_rows are
provenance, not new simulation. Running segments are snapshots and lower bounds.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from office_v7_uniform24_20261008 import read, write, sha, now


def optimizer_work(path):
    count = 0
    first = last = None
    digest = hashlib.sha256()
    partial = False
    with path.open('rb') as stream:
        for line in stream:
            if not line.endswith(b'\n'):
                partial = True
                break
            row = json.loads(line)
            if last is not None:
                assert row['update'] == last['update']+1, path
            if first is None: first = row
            last = row
            count += 1
            digest.update(line)
    return dict(logged_updates=count, first_update=first['update'] if first else None,
        last_update=last['update'] if last else None,
        last_step=last['step'] if last else None, trailing_partial_line=partial,
        complete_log_prefix_sha256=digest.hexdigest())


def build(root):
    jobs = read(root/'RL_JOBS_CORRECTED.json')['jobs']
    all_groups = []
    for job in jobs:
        active = Path(job['output'])
        group = active.parent
        segments = []
        physical = {}
        for path in sorted(group.glob('*/execution.json')):
            state = read(path)
            # Save exactly the captured state hash, not a later mutable file.
            state_digest = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
            optimizer = path.parent/'optimizer.jsonl'
            work = optimizer_work(optimizer) if optimizer.exists() else None
            rows = state.get('rows', [])
            new_episodes = []
            for row in rows:
                run = Path(row['run'])
                assert str(run) not in physical, 'Copied rows would double-count physics'
                item = dict(run=str(run), complete='result' in row,
                    steps=row.get('steps'), started_utc=row.get('started_utc'),
                    ended_utc=row.get('ended_utc'))
                if item['complete']:
                    assert sha(run/'AUDIT.json') == row['audit_sha256']
                    audit = read(run/'AUDIT.json')
                    item.update(task=bool(audit['task_success']), strict=bool(audit['strict_success']),
                        full=bool(audit['full_horizon']), physical_seconds=audit['physical_seconds'],
                        audit_sha256=row['audit_sha256'], trace_sha256=row['trace_sha256'])
                physical[str(run)] = item
                new_episodes.append(item)
            rebuild = bool(state.get('physics_rerun') is False and state.get('rebuilt_from'))
            segments.append(dict(path=str(path.parent), status=state['status'],
                cumulative_steps=state.get('steps'), cumulative_updates=state.get('updates'),
                captured_state_canonical_sha256=state_digest,
                optimizer=work, rebuild_from_retained_data=rebuild,
                inherited_provenance_episodes=len(state.get('source_episode_rows', [])),
                physical_attempts=len(new_episodes),
                physically_completed=sum(r['complete'] for r in new_episodes)))
        complete = [r for r in physical.values() if r['complete']]
        selected = next(s for s in segments if s['path'] == str(active))
        recorded = sum(s['optimizer']['logged_updates'] for s in segments if s['optimizer'])
        # Running optimizer logs can be a few steps newer than execution.json.
        retained_updates = max(selected['cumulative_updates'] or 0,
            (selected['optimizer']['last_update'] or 0) if selected['optimizer'] else 0)
        all_groups.append(dict(family=job['family'], seed=job['seed'], active_segment=str(active),
            current_cumulative_steps=selected['cumulative_steps'],
            current_cumulative_updates=selected['cumulative_updates'],
            recorded_optimizer_work=recorded,
            discarded_or_replaced_optimizer_updates_lower_bound=max(0, recorded-retained_updates),
            recorded_rebuild_optimizer_work=sum(s['optimizer']['logged_updates'] for s in segments
                if s['optimizer'] and s['rebuild_from_retained_data']),
            discarded_active_lineage_updates_at_servo_repair=job.get('discarded_gradient_updates', 0),
            physical_attempts=len(physical), physically_completed=len(complete),
            incomplete_attempts=sum(not r['complete'] for r in physical.values()),
            complete_physical_steps=sum(r['steps'] for r in complete),
            complete_physical_seconds=sum(r['physical_seconds'] for r in complete),
            training_task_successes=sum(r['task'] for r in complete),
            training_strict_successes=sum(r['strict'] for r in complete),
            training_short_episodes=sum(not r['full'] for r in complete),
            segment_status_counts=dict(Counter(s['status'] for s in segments)), segments=segments,
            physical_episodes=list(physical.values())))
    return dict(created_utc=now(), source_sha256=sha(__file__), jobs=all_groups,
        protocol_sha256=sha(root/'PROTOCOL.json'), registration_sha256=sha(root/'RL_JOBS_CORRECTED.json'),
        scope='Current repair campaign RL only; no teacher/ESN historical search cost or classical simulations included. '
        'Only actual rows count as physics; inherited/rebuilt rows do not. Logged optimizer updates are a lower bound '
        'if a process failed before logging or a log is missing. Rebuild updates are a subset, not an extra addend. '
        'Do not sum overlapping segment wall times as elapsed wall time. Running snapshots can differ slightly across counters. '
        'Training scores include old-reward exploration and cannot replace final-policy evaluation.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    result = build(a.root)
    write(a.output, result)
    for job in result['jobs']:
        print({k:job[k] for k in ('family','seed','current_cumulative_steps','recorded_optimizer_work',
            'recorded_rebuild_optimizer_work','physically_completed','training_task_successes')}, flush=True)
