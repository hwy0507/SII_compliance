"""Read-only training diagnostics; never read heldout conditions or select weights.

Snapshot only completed episode receipts. Actor saturation, common filtering,
training success and optimizer diagnostics are different signals, not a claim
that a controller has converged. Running execution files are captured once.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import numpy as np
from office_v7_uniform24_20261008 import read, write, sha, now


def inspect_segment(path, condition_ids):
    state = read(path/'execution.json')
    specification = read(path/'PROTOCOL.json')
    rows = [r for r in state['rows'] if 'result' in r]
    episodes = []
    for row in rows:
        assert row['condition_id'] in condition_ids
        run = Path(row['run'])
        assert sha(run/'AUDIT.json') == row['audit_sha256']
        assert sha(run/'rollout.npz') == row['trace_sha256']
        audit = read(run/'AUDIT.json')
        with np.load(run/'baseline_policy.npz') as p, np.load(run/'execution_chain.npz') as c:
            raw = p['raw_action']; observation = p['observation']; action = p['action']
            filtered = c['filtered_action']
            assert raw.shape == (row['steps'], specification['agent_config']['action_dimension'])
            assert observation.shape == (row['steps'], 48)
            assert action.shape == filtered.shape == (row['steps'], 7)
            assert all(np.isfinite(v).all() for v in (raw, observation, action, filtered))
            assert abs(raw).max() <= 1.000001
            change = np.max(abs(action-filtered), axis=1)
            episode = dict(episode=row['episode'], condition=row['condition_id'], steps=row['steps'],
                return_value=row['return_value'], task=bool(audit['task_success']),
                strict=bool(audit['strict_success']), full=bool(audit['full_horizon']),
                stage=audit['stage'], abort_reason=audit.get('abort_reason'),
                raw_actor_abs95_fraction=float(np.mean(abs(raw) >= .95)),
                raw_actor_std_per_channel=np.std(raw, axis=0).tolist(),
                controller_action_abs95_fraction=float(np.mean(abs(action) >= .95)),
                common_filter_changed_step_fraction=float(np.mean(change > 1e-6)),
                controller_action_all_zero=bool(np.all(action == 0)),
                trace_sha256=row['trace_sha256'], audit_sha256=row['audit_sha256'])
        episodes.append(episode)
    # A writer may still be appending. Read only complete JSONL lines; do not
    # mistake a partially written last line for a corrupt optimizer update.
    optimizer = dict(complete_lines=0, trailing_partial_line=False, first=None, last=None)
    metrics = {}
    with (path/'optimizer.jsonl').open('rb') as stream:
        for line in stream:
            if not line.endswith(b'\n'):
                optimizer['trailing_partial_line'] = True
                break
            value = json.loads(line)
            optimizer['complete_lines'] += 1
            if optimizer['first'] is None: optimizer['first'] = value
            optimizer['last'] = value
            for key, number in value['metrics'].items():
                assert np.isfinite(number), (path, value['step'], key)
                x = metrics.setdefault(key, dict(min=number, max=number, count=0, sum=0.))
                x['min'] = min(x['min'], number); x['max'] = max(x['max'], number)
                x['count'] += 1; x['sum'] += number
    optimizer['metrics'] = {k:dict(min=v['min'], max=v['max'], count=v['count'],
                                 mean=v['sum']/v['count']) for k,v in metrics.items()}
    return dict(path=str(path), status=state['status'], state_steps=state['steps'],
        state_episodes=state['episodes'], state_updates=state.get('updates'),
        inherited=state.get('resumed_from'), diagnostics=state.get('diagnostics'),
        complete_segment_episodes=len(episodes), complete_segment_steps=sum(r['steps'] for r in episodes),
        task=sum(r['task'] for r in episodes), strict=sum(r['strict'] for r in episodes),
        short=sum(not r['full'] for r in episodes),
        failed_stage_counts=dict(Counter(r['stage'] for r in episodes if not r['task'])),
        abort_reasons=dict(Counter(str(r['abort_reason']) for r in episodes if not r['full'])),
        optimizer=optimizer, episodes=episodes,
        protocol_sha256=sha(path/'PROTOCOL.json'),
        scope='Counts cover completed episodes in this segment only; inherited episodes are separately identified. Optimizer log can be slightly newer than captured state. No convergence claim.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); assert not a.output.exists()
    protocol = read(a.root/'PROTOCOL.json')
    assert sha(a.root/'CONDITIONS.json') == protocol['condition_file_sha256']
    conditions = {c['id'] for c in read(a.root/'CONDITIONS.json')['conditions'] if c['role'] == 'train'}
    paths = sorted([*a.root.glob('rl/*/continued_v5'), *a.root.glob('rl/*/trained_v8'),
                    *a.root.glob('rl/*/continued_v9')])
    result = dict(created_utc=now(), source_sha256=sha(__file__), segments=[],
        note='Diagnostic only; no final conditions accessed, no weight selection, no new physics. '
             'Parameter-impedance zero action7 is intentional native torque execution, not zero actuator effort.')
    for path in paths:
        if (path/'execution.json').exists():
            value = inspect_segment(path, conditions); result['segments'].append(value)
            print(json.dumps({k:value[k] for k in ('path','status','state_steps','complete_segment_episodes','task','strict','short')}), flush=True)
    jobs_path = a.root/('RL_JOBS_CORRECTED.json' if (a.root/'RL_JOBS_CORRECTED.json').exists() else 'RL_JOBS.json')
    if jobs_path.exists():
        result['resources'] = []
        for job in read(jobs_path)['jobs']:
            pid = int(subprocess.check_output(['systemctl','--user','show',job['unit'],
                                              '-p','MainPID','--value'], text=True).strip())
            resource = dict(unit=job['unit'], pid=pid)
            if pid:
                try:
                    relative = Path(f'/proc/{pid}/cgroup').read_text().split('::', 1)[1].strip().lstrip('/')
                    cg = Path('/sys/fs/cgroup')/relative
                    resource['cgroup'] = str(cg)
                    resource['counters'] = {name:(cg/name).read_text().strip() for name in
                        ('memory.current','memory.peak','memory.max','memory.events','memory.swap.max')}
                except FileNotFoundError:
                    resource['exited_during_snapshot'] = True
            result['resources'].append(resource)
    write(a.output, result)


if __name__ == '__main__': main()
