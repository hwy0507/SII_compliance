"""Read-only supervision of the finite classical search; never dispatch or retry.

Only completed, independently audited receipts enter the developing table. The
watcher writes to a separate directory and exits on completion or an anomaly.
It neither changes a controller nor requires task success to accept a result.
"""
import argparse
from collections import Counter
from datetime import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time

from classical_acceptance_20261010 import read, write, sha, now, hashes, rank_candidates


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_row(root, row):
    job = row['job']
    run = root / job['name']
    require(run.parent == root, 'Invalid job path')
    require(row['status'] == 'complete', 'Incomplete row in completed list')
    require(read(root / (job['name'] + '.execution.json')) == row, 'Receipt mismatch')
    audit = read(run / 'AUDIT.json')
    require(audit == row['audit'], 'Audit values changed')
    require(sha(run / 'AUDIT.json') == row['audit_sha256'], 'Audit hash mismatch')
    require(sha(run / 'rollout.npz') == row['trace_sha256'] == audit['trace_sha256'], 'Trace hash mismatch')
    require(sha(run / 'rollout.mjb') == audit['model_sha256'], 'Model hash mismatch')
    require(read(run / 'execution.json')['status'] == 'complete', 'Worker not complete')
    require(read(root / (job['name'] + '.config.json')) == {'parameters': job['parameters']}, 'Parameters changed')
    checks = row['checks']
    expected = {'shield', 'dynamic'} if job['controller'] in ('vmc', 'admittance') else {'shield'}
    require({c['kind'] for c in checks} == expected and len(checks) == len(expected), 'Missing controller audit')
    for check in checks:
        path = root / (job['name'] + '.' + check['kind'] + '.json')
        require(check['returncode'] == 0 and read(path)['status'] == 'passed', 'Controller audit failed')
        require(sha(path) == check['sha256'], 'Controller audit hash mismatch')
    require(0 < audit['physical_seconds'] <= 55.000001, 'Invalid physical duration')
    require(not audit['task_success'] or audit['full_horizon'], 'Short episode reported successful')
    return dict(candidate=job['candidate'], method=job['controller'], condition=job['condition_id'],
        task=audit['task_success'], strict=audit['strict_success'], full_horizon=audit['full_horizon'],
        final_stage=audit['stage'], abort_reason=audit['abort_reason'],
        rmse_mm=audit['rmse_mm'], peak_torque_nm=audit['peak_torque_nm'],
        peak_speed_mps=audit['peak_speed_mps'], penetration_mm=audit['penetration_mm'],
        placement_error_xy_m=audit['placement_error_xy_m'],
        model_sha256=audit['model_sha256'], trace_sha256=row['trace_sha256'],
        audit_sha256=row['audit_sha256'])


class Monitor:
    def __init__(self, root):
        self.root = root.resolve()
        self.registration_hash = sha(root / 'REGISTRATION.json')
        self.reg = read(root / 'REGISTRATION.json')
        require(self.reg['schema'] == 'classical-local-boundary-search-v1', 'Wrong campaign')
        require(hashes(root / 'source') == self.reg['source_hashes'], 'Source mismatch')
        require(hashes(root / 'parameter') == self.reg['parameter_hashes'], 'Controller source mismatch')
        self.cache = {}

    def snapshot(self, rehash=False):
        root, reg = self.root, self.reg
        require(sha(root / 'REGISTRATION.json') == self.registration_hash, 'Registration changed')
        state_bytes = (root / 'execution.json').read_bytes()
        state = json.loads(state_bytes)
        require(state['registration_sha256'] == self.registration_hash, 'Execution registration mismatch')
        rows = state['completed']
        names = [r['job']['name'] for r in rows]
        require(len(names) == len(set(names)), 'Duplicate completed job')
        require(set(self.cache) <= set(names), 'Completed results disappeared')
        planned = {j['name']: j for j in reg['jobs']}
        selection_path = root / 'SELECTION.json'
        if selection_path.exists():
            selection = read(selection_path)
            screen = [r for r in rows if r['job']['name'] in planned]
            require(len(screen) == len(reg['jobs']), 'Premature confirmation selection')
            require(selection['registration_sha256'] == self.registration_hash, 'Selection registration mismatch')
            ranked = rank_candidates(reg, screen)
            require(selection['ranked'] == ranked, 'Selection differs from registered ranking')
            expected = []
            for method in ('vmc', 'admittance', 'impedance'):
                for selected in ranked[method][:2]:
                    c = selected['candidate']
                    for condition in reg['confirmation_conditions']:
                        expected.append(dict(name=c['name']+'__'+condition, candidate=c['name'],
                            controller=method, fixture='frozen', condition_id=condition, parameters=c['parameters']))
            require(selection['jobs'] == expected, 'Confirmation conditions or parameters changed')
            planned.update({j['name']: j for j in expected})
        require(len(rows) <= reg['max_episodes'], 'Budget exceeded')
        terminal = state['status'] != 'running'
        results = []
        for row in rows:
            name = row['job']['name']
            require(planned.get(name) == row['job'], 'Unregistered job')
            fingerprint = json.dumps(row, sort_keys=True)
            if name in self.cache:
                require(self.cache[name][0] == fingerprint, 'Completed receipt changed')
            if rehash or terminal or name not in self.cache:
                self.cache[name] = (fingerprint, verify_row(root, row))
                run = root/name
                provenance = read(run/'execution.json')['runtime_provenance']
                condition = next(c for c in reg['conditions'] if c['id']==row['job']['condition_id'])
                require(condition['role']=='development' and provenance['condition']==condition, 'Wrong condition identity')
                require(provenance['registration_sha256']==self.registration_hash, 'Worker registration mismatch')
                require(provenance['physics_dt_s']==reg['physics_dt_s'], 'Wrong physics timestep')
                require(self.cache[name][1]['model_sha256']==reg['frozen_model_sha256'], 'Frozen model changed')
                fixture = read(run/'DIAGNOSTIC_FIXTURE.json')
                require(fixture['fixture']=='frozen' and not fixture['diagnostic_only'] and not fixture['changes'], 'Diagnostic geometry in benchmark')
                arguments = read(run/'rollout.json')['arguments']
                require(all(arguments[k]==v for k,v in condition['overrides'].items()), 'Actual settings differ from registered condition')
                self.cache[name][1]['seed'] = arguments['seed']
                self.cache[name][1]['plan_sha256'] = fixture['plan_sha256']
            results.append(self.cache[name][1])
        if state['status'] == 'complete':
            require(selection_path.exists() and len(rows) == reg['max_episodes'] == len(planned), 'Incomplete campaign marked complete')
        for condition in {r['condition'] for r in results}:
            require(len({r['plan_sha256'] for r in results if r['condition']==condition})==1, 'Routes differ within condition')
        active = state.get('active')
        if active:
            require(planned.get(active['name']) == active, 'Unregistered active job')
        active_jobs = state.get('active_jobs', [active] if active else [])
        require(len({j['name'] for j in active_jobs})==len(active_jobs), 'Duplicate active job')
        require(not set(names) & {j['name'] for j in active_jobs}, 'Completed job dispatched again')
        for job in active_jobs:
            require(planned.get(job['name'])==job, 'Unregistered parallel job')
        lanes=state.get('parallel_lanes',1)
        require(lanes in (1,2) and len(active_jobs)<=lanes, 'Excess concurrent lanes')
        if lanes==2:
            amendment=read(root/'DISPATCH_V2.json')
            require(sha(root/'DISPATCH_V2.json')==state['dispatch_amendment_sha256'], 'Resource amendment changed')
            require(amendment['registration_sha256']==self.registration_hash and amendment['simulators']==2, 'Wrong parallel registration')
        durations = [(datetime.fromisoformat(r['ended_utc'])-datetime.fromisoformat(r['started_utc'])).total_seconds() for r in rows]
        summaries = []
        for c in reg['candidates']:
            rr = [r for r in results if r['candidate'] == c['name']]
            summaries.append(dict(candidate=c['name'],method=c['controller'],evaluated=len(rr),
                task=sum(r['task'] for r in rr), strict=sum(r['strict'] for r in rr),
                physical_early_failures=sum(not r['full_horizon'] for r in rr),
                conditions=[r['condition'] for r in rr]))
        median = statistics.median(durations) if durations else None
        return dict(status='verified_complete' if state['status']=='complete' else 'verified_partial',
            updated_utc=now(), campaign_status=state['status'], campaign_error=state.get('error'),
            execution_sha256=hashlib.sha256(state_bytes).hexdigest(), registration_sha256=self.registration_hash,
            completed=len(rows), budget=reg['max_episodes'], active=active,active_jobs=active_jobs,parallel_lanes=lanes,
            completed_by_method=dict(Counter(r['method'] for r in results)),
            median_episode_wall_seconds=median,
            approximate_remaining_hours=None if median is None else median*(reg['max_episodes']-len(rows))/3600/lanes,
            candidates=summaries, rows=results, additional_physics_steps=0, final_test_reads=0,
            interpretation='Development parameter trials, not final selected-policy success rates. Task failures remain valid audited outcomes. Zero evaluated means pending, not zero success. ETA uses completed wall times and can change.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--watch', action='store_true')
    p.add_argument('--unit', default='sii-classical-strengthen-20261010-v1.service')
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    with (a.output/'monitor.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        last = None
        inactive_count = 0
        try:
            monitor = Monitor(a.root)
            while True:
                result = monitor.snapshot()
                if a.watch:
                    unit = subprocess.run(['systemctl','--user','is-active',a.unit],capture_output=True,text=True,timeout=10)
                    result['coordinator_service'] = unit.stdout.strip()
                    inactive_count = inactive_count + 1 if result['campaign_status']=='running' and unit.returncode else 0
                    require(inactive_count < 3, 'Coordinator inactive for three samples but execution still running')
                write(a.output/'LATEST.json',result)
                key = (result['completed'],result['campaign_status'])
                if key != last:
                    print(json.dumps({k:result[k] for k in ('updated_utc','campaign_status','completed','budget','completed_by_method','approximate_remaining_hours')}) ,flush=True)
                    last = key
                if not a.watch or result['campaign_status'] != 'running':
                    if a.watch:
                        write(a.output/'CLOSE.json',result)
                    return
                time.sleep(60)
        except BaseException as exc:
            write(a.output/'ALERT.json',dict(status='monitor_failed',created_utc=now(),error=repr(exc),
                action='Read-only monitor exited; no simulation was killed, restarted or dispatched. Inspect the original coordinator and preserve failures.'))
            raise


if __name__ == '__main__':
    main()
