"""Give a fresh finite CHEQ stage the SAC sampler cores at complete cycles.

Wait for both existing coordinators to finish before touching their learners.
Stop only registered jobs through their complete-cycle STOP_REQUESTED contract.
Preserve every parent state and resume CHEQ with the remaining original budget.
No learner settings, physics, retries or artificial GPU load are introduced.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import torch

METHODS = ('direct', 'impedance', 'admittance', 'vmc')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def identity(pid):
    try:
        stat = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
        return None if stat[0] == 'Z' else stat[19]
    except FileNotFoundError:
        return None


def validate_allocations(plan, allowed):
    if set(plan['allocations']) != set(METHODS) or plan['total_cycles'] != 6:
        raise ValueError('Require four methods and the original six-cycle budget')
    used = set(plan['reserved_cpus']) | {plan['coordinator_cpu']}
    for i, method in enumerate(METHODS):
        allocation = plan['allocations'][method]
        cpus = allocation['cpus']
        if (allocation['gpu'] != i or allocation['workers'] != 12
                or len(cpus) != 13 or len(set(cpus)) != 13
                or not set(cpus) <= set(allowed) or set(cpus) & used):
            raise ValueError('Invalid or overlapping allocation: '+method)
        for role in ('fresh', 'sac'):
            for other, old in plan[role]['expected_allocations'].items():
                if other != method and set(cpus) & set(old['cpus']):
                    raise ValueError('Allocation overlaps draining sibling')
        used.update(cpus)


def remaining_cycles(state, total):
    if (state['boundary'] != 'complete_condition_cycle' or not state['cycles']
            or [v['cycle'] for v in state['cycles']] != list(range(state['cycle']+1))
            or state['cycles'][-1]['steps'] != state['steps']):
        raise ValueError('Require complete contiguous cycle history')
    remaining = total - state['cycle'] - 1
    if remaining < 0:
        raise ValueError('Original stage budget already exceeded')
    return remaining


def validate_boundary(state, finished, execution, method, protocol, conditions, episodes):
    if (state['boundary'] != 'complete_condition_cycle' or state['steps'] != finished['steps']
            or finished['status'] != 'stopped_at_complete_cycle'
            or state['controller'] != method or state['protocol_sha256'] != protocol
            or state['seed'] != execution['seed']
            or state['learner']['algorithm'] != execution['algorithm']
            or not state['cycles'] or state['cycles'][-1]['cycle'] != state['cycle']
            or state['cycles'][-1]['steps'] != state['steps']):
        raise ValueError('Parent is not the registered complete boundary')
    rows = [e for e in episodes if e['cycle'] == state['cycle']]
    if (len(rows) != len(conditions) or {e['condition'] for e in rows} != set(conditions)
            or max(e['total_steps'] for e in rows) != state['steps']):
        raise ValueError('Parent cycle does not contain the complete condition set')


def jobs_ready(spec):
    run = Path(spec['run'])
    for name in ('MIGRATION_FAILURE.json', 'DISPATCH_FAILURE.json'):
        if (run/name).exists():
            raise RuntimeError('Existing coordinator failed: '+str(run/name))
    current = identity(spec['coordinator_pid'])
    if current is not None and current != spec['coordinator_start_ticks']:
        raise ValueError('Coordinator PID reused')
    if not (run/spec['finished_receipt']).exists():
        if current is None:
            raise RuntimeError('Coordinator exited without handoff receipt')
        return None
    if current is not None:
        return None
    receipt = read(run/spec['finished_receipt'])
    if not receipt[spec['finished_key']]:
        raise ValueError('Coordinator has not confirmed real updates')
    jobs = read(run/'LAUNCH.json')['jobs']
    if len(jobs) != 4 or {j['controller'] for j in jobs} != set(METHODS):
        raise ValueError('Missing or duplicated original learners')
    answer = {}
    for job in jobs:
        method = job['controller']; folder = run/method
        execution = read(folder/'EXECUTION.json')
        allocation = spec['expected_allocations'][method]
        tick = identity(job['pid'])
        if (tick is None or execution['pid'] != job['pid']
                or execution['protocol_sha256'] != spec['registration_sha256']
                or execution['algorithm'] != spec['algorithm']
                or execution['cpus'] != allocation['cpus'] or job['cpus'] != allocation['cpus']
                or execution['workers'] != allocation['workers']
                or execution['device'] != 'cuda:'+str(allocation['gpu'])
                or (folder/'FAILURE.json').exists() or (folder/'STOP_REQUESTED').exists()):
            raise ValueError('Unexpected original learner state: '+method)
        command = Path('/proc', str(job['pid']), 'cmdline').read_bytes().rstrip(b'\0').split(b'\0')
        if [v.decode() for v in command] != job['command']:
            raise ValueError('Original process command mismatch')
        progress = read(folder/'PROGRESS.json')
        if progress['updates'] <= 0:
            raise ValueError('Original learner has not updated')
        answer[method] = dict(job=job, start_ticks=tick, execution=execution, progress=progress)
    return answer


def main(plan_path):
    plan = read(plan_path)
    validate_allocations(plan, os.sched_getaffinity(0))
    if sha(__file__) != plan['source_sha256']:
        raise ValueError('Coordinator source drift')
    for item in plan['immutable_files']:
        if sha(item['path']) != item['sha256']:
            raise ValueError('Registered input drift: '+item['path'])
    out = Path(plan['output']); out.mkdir(parents=True, exist_ok=False)
    (out/'parent_checkpoints').mkdir()
    cpu = plan['coordinator_cpu']; os.sched_setaffinity(0, {cpu})
    torch.set_num_threads(1)
    write(out/'EXECUTION.json', dict(pid=os.getpid(), plan=str(plan_path), plan_sha256=sha(plan_path),
        started_unix=time.time(), convergence_claim=False))
    env = dict(os.environ, MUJOCO_GL='disable', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    children, launched, completed, states = {}, [], {}, {}
    try:
        while True:
            if (out/'COORDINATOR_STOP').exists():
                write(out/'DISPATCH_STOPPED.json', dict(launched=launched)); return
            ready = {role: jobs_ready(plan[role]) for role in ('fresh', 'sac')}
            write(out/'PROGRESS.json', dict(state='waiting_for_existing_coordinators',
                ready={k: v is not None for k,v in ready.items()}, updated_unix=time.time()))
            if all(v is not None for v in ready.values()):
                break
            time.sleep(5)
        # Validate every dependency first; only then ask the eight learners to drain.
        write(out/'PARENTS.json', ready)
        for role, records in ready.items():
            for method, record in records.items():
                if identity(record['job']['pid']) != record['start_ticks']:
                    raise ValueError('Original learner exited before drain request')
                with (Path(plan[role]['run'])/method/'STOP_REQUESTED').open('x') as stream:
                    json.dump(dict(reason='registered complete-cycle resource prioritization',
                        plan=str(plan_path), requested_unix=time.time()), stream)
        with (out/'migration_archive.log').open('xb') as log:
            monitor = subprocess.Popen([sys.executable, '-B', plan['archive_tool'], '--run', str(out),
                '--output', str(out/'migration_archive'), '--migration-only'], env=env,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write(out/'MIGRATION_ARCHIVE.json', dict(pid=monitor.pid))
        while len(completed) < 4:
            if (out/'COORDINATOR_STOP').exists():
                write(out/'DISPATCH_STOPPED.json', dict(launched=launched,
                    note='Parents retain stop requests; inspect before resuming')); return
            for method, child in children.items():
                if child.poll() is not None:
                    raise RuntimeError('Resumed learner exited during resource handoff: '+method)
            for method in METHODS:
                if method in completed:
                    continue
                if method in children:
                    child = children[method]
                    folder = out/method
                    if child.poll() is not None:
                        raise RuntimeError('Resumed learner exited before first update: '+method)
                    if (folder/'PROGRESS.json').exists():
                        progress = read(folder/'PROGRESS.json')
                        if (progress['steps'] > states[method]['steps']
                                and progress['updates'] > states[method]['updates']):
                            completed[method] = dict(scope='resumed_and_updated', progress=progress)
                    continue
                released = True
                for role in ('fresh', 'sac'):
                    record = ready[role][method]; folder = Path(plan[role]['run'])/method
                    if (folder/'FAILURE.json').exists():
                        raise RuntimeError('Parent failed while draining: '+str(folder))
                    current = identity(record['job']['pid'])
                    if current == record['start_ticks']:
                        released = False
                    elif current is not None:
                        raise ValueError('Parent PID reused while draining')
                if not released:
                    continue
                for item in plan['immutable_files']:
                    if sha(item['path']) != item['sha256']:
                        raise ValueError('Registered input drift during wait')
                parent_receipts = {}
                for role in ('sac', 'fresh'):
                    spec = plan[role]; folder = Path(spec['run'])/method
                    checkpoint = folder/'checkpoint_latest.pt'
                    state = torch.load(checkpoint, map_location='cpu', weights_only=False)
                    episodes = [json.loads(line) for line in (folder/'episodes.jsonl').read_text().splitlines()]
                    validate_boundary(state, read(folder/'FINISHED.json'), ready[role][method]['execution'],
                        method, spec['registration_sha256'], plan['conditions'], episodes)
                    parent_receipts[role] = dict(checkpoint=str(checkpoint), sha256=sha(checkpoint),
                        cycle=state['cycle'], steps=state['steps'], updates=state['learner']['num_gradient_steps'])
                    if role == 'sac':
                        del state
                remaining = remaining_cycles(state, plan['total_cycles'])
                states[method] = dict(parent_receipts['fresh'], remaining_cycles=remaining)
                write(out/(method+'_PARENT_REVIEW.json'), dict(parents=parent_receipts,
                    remaining_cycles=remaining, state_reset=False, convergence_claim=False))
                if remaining == 0:
                    completed[method] = dict(scope='original_budget_already_completed')
                    del state; continue
                dest = out/'parent_checkpoints'/(method+'.pt')
                shutil.copy2(checkpoint, dest)
                if sha(dest) != parent_receipts['fresh']['sha256']:
                    raise ValueError('Parent byte copy mismatch')
                del state
                allocation = plan['allocations'][method]
                command = [sys.executable, '-B', str(Path(plan['runtime'])/'source/tools/train_published_compliance_20261025.py'),
                    '--runtime', plan['runtime'], '--registration', plan['fresh']['registration'],
                    '--output', str(out/method), '--controller', method, '--algorithm', 'cheq',
                    '--seed', str(ready['fresh'][method]['execution']['seed']), '--device', 'cuda:'+str(allocation['gpu']),
                    '--cpus', ','.join(map(str, allocation['cpus'])), '--workers', str(allocation['workers']),
                    '--resume', str(dest), '--cycles', str(remaining)]
                os.sched_setaffinity(0, set(allocation['cpus']) | {cpu})
                try:
                    with (out/(method+'.log')).open('xb') as log:
                        child = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                finally:
                    os.sched_setaffinity(0, {cpu})
                children[method] = child
                launched.append(dict(controller=method, pid=child.pid, gpu=allocation['gpu'],
                    cpus=allocation['cpus'], command=command))
                write(out/'LAUNCH.json', dict(jobs=launched, registration=plan['fresh']['registration'],
                    parent_run=plan['fresh']['run'], parent_states=states))
            write(out/'PROGRESS.json', dict(state='draining_or_resuming', launched=launched,
                completed=completed, parent_states=states, updated_unix=time.time()))
            time.sleep(5)
        with (out/'cycle_archive.log').open('xb') as log:
            monitor = subprocess.Popen([sys.executable, '-B', plan['archive_tool'], '--run', str(out),
                '--output', str(out/'cycle_archive')], env=env, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True) if launched else None
        write(out/'MIGRATION_FINISHED.json', dict(ended_unix=time.time(), completed=completed,
            archive_pid=monitor.pid if monitor else None, convergence_claim=False))
    except BaseException as error:
        write(out/'MIGRATION_FAILURE.json', dict(error=repr(error), launched=launched,
            note='Preserve every parent and live child; no retry or blanket termination'))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    main(parser.parse_args().plan)
