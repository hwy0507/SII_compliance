"""Independent complete-cycle resource handoffs after retiring old dispatchers.

Three existing CHEQ learners retain full state; the never-launched fourth starts
fresh only after its own SAC sampler releases the cores. No cross-method warmup
barrier, no partial-cycle resume, no learning or physics changes, no retries.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import torch
from prioritize_published_fresh_sampling_20261025 import (
    METHODS, identity, read, remaining_cycles, sha, validate_boundary, write,
)


def validate_plan(plan, allowed):
    if set(plan['methods']) != set(METHODS) or plan['total_cycles'] != 6:
        raise ValueError('Require four methods and original six-cycle budget')
    used = set(plan['reserved_cpus']) | {plan['coordinator_cpu']}
    for i, method in enumerate(METHODS):
        spec = plan['methods'][method]; allocation = spec['allocation']; cpus = allocation['cpus']
        if (allocation['workers'] != 12 or allocation['gpu'] != i or len(cpus) != 13
                or len(set(cpus)) != 13 or set(cpus) & used or not set(cpus) <= set(allowed)):
            raise ValueError('Invalid CPU/GPU allocation')
        used.update(cpus)
        roles = [p['role'] for p in spec['parents']]
        if roles.count('sac') != 1 or roles.count('fresh') != (0 if spec['never_launched'] else 1):
            raise ValueError('Missing or duplicated source parent')
        if len(roles) != len(set(roles)) or set(roles) - {'sac','fresh'}:
            raise ValueError('Unexpected source parent')
        for other, other_spec in plan['methods'].items():
            if other != method:
                for parent in other_spec['parents']:
                    if set(cpus) & set(parent['cpus']):
                        raise ValueError('Overlap with still-draining sibling')


def check_parent(parent):
    folder = Path(parent['folder'])
    if identity(parent['pid']) != parent['start_ticks']:
        raise ValueError('Parent process identity changed')
    command = Path('/proc', str(parent['pid']), 'cmdline').read_bytes().rstrip(b'\0').split(b'\0')
    if [v.decode() for v in command] != parent['command']:
        raise ValueError('Parent command changed')
    if sha(folder/'EXECUTION.json') != parent['execution_sha256'] or (folder/'FAILURE.json').exists():
        raise ValueError('Parent execution changed or failed')
    stop = folder/'STOP_REQUESTED'
    expected = parent['existing_stop_sha256']
    if (stop.exists() != (expected is not None)) or (expected and sha(stop) != expected):
        raise ValueError('Unexpected stop request')


def check_retired(spec):
    if identity(spec['pid']) is not None:
        raise ValueError('Old coordinator has not exited')
    receipt = read(spec['stopped_receipt'])
    if sorted(j['controller'] for j in receipt['launched']) != sorted(spec['expected_methods']):
        raise ValueError('Old coordinator launched an unexpected learner')


def check_inputs(plan):
    for item in plan['immutable_files']:
        if sha(item['path']) != item['sha256']:
            raise ValueError('Immutable input drift: '+item['path'])


def main(plan_path):
    plan = read(plan_path)
    validate_plan(plan, os.sched_getaffinity(0))
    if sha(__file__) != plan['source_sha256']:
        raise ValueError('Frozen coordinator drift')
    check_inputs(plan)
    for spec in plan['retired_coordinators']:
        check_retired(spec)
    for spec in plan['methods'].values():
        if spec['never_launched'] and Path(spec['original_fresh_folder']).exists():
            raise ValueError('Claimed fresh interface already has a run')
        for parent in spec['parents']:
            check_parent(parent)
    out = Path(plan['output']); out.mkdir(parents=True, exist_ok=False)
    (out/'parent_checkpoints').mkdir(); cpu = plan['coordinator_cpu']
    os.sched_setaffinity(0, {cpu}); torch.set_num_threads(1)
    env = dict(os.environ, MUJOCO_GL='disable', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    write(out/'EXECUTION.json', dict(pid=os.getpid(), started_unix=time.time(), plan=str(plan_path),
        plan_sha256=sha(plan_path), scope='per-method complete-cycle priority; six total cycles'))
    launched, children, parent_states, updated = [], {}, {}, {}
    try:
        for method, spec in plan['methods'].items():
            for parent in spec['parents']:
                if parent['existing_stop_sha256'] is not None:
                    continue
                with (Path(parent['folder'])/'STOP_REQUESTED').open('x') as stream:
                    json.dump(dict(reason='registered independent complete-cycle handoff',
                        plan=str(plan_path), requested_unix=time.time()), stream)
        write(out/'DRAIN_REQUESTED.json', dict(unix=time.time(), methods=plan['methods'],
            note='Existing Impedance SAC stop retained unchanged; others newly requested'))
        with (out/'migration_archive.log').open('xb') as log:
            archive = subprocess.Popen([sys.executable,'-B',plan['archive_tool'],'--run',str(out),
                '--output',str(out/'migration_archive'),'--migration-only'],env=env,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        write(out/'MIGRATION_ARCHIVE.json', dict(pid=archive.pid))
        while len(updated) < 4:
            if (out/'COORDINATOR_STOP').exists():
                write(out/'DISPATCH_STOPPED.json',dict(launched=launched,
                    note='Existing parent stop requests and live children remain independently managed')); return
            for method, spec in plan['methods'].items():
                if method in children:
                    if children[method].poll() is not None:
                        raise RuntimeError('New learner exited before handoff completion: '+method)
                    p = out/method/'PROGRESS.json'
                    if p.exists():
                        progress = read(p)
                        if (progress['steps'] > parent_states[method]['steps']
                                and progress['updates'] > parent_states[method]['updates']):
                            updated[method] = progress
                    continue
                if method in updated:
                    continue
                released = True
                for parent in spec['parents']:
                    folder = Path(parent['folder'])
                    if (folder/'FAILURE.json').exists():
                        raise RuntimeError('Parent failed while draining: '+str(folder))
                    tick = identity(parent['pid'])
                    if tick == parent['start_ticks']:
                        released = False
                    elif tick is not None:
                        raise ValueError('Parent PID reused')
                if not released:
                    continue
                check_inputs(plan)
                receipts = {}; resume = None; remaining = plan['total_cycles']
                base_state = dict(steps=0,updates=0,cycle=-1)
                for parent in spec['parents']:
                    folder = Path(parent['folder']); checkpoint = folder/'checkpoint_latest.pt'
                    state = torch.load(checkpoint,map_location='cpu',weights_only=False)
                    execution = read(folder/'EXECUTION.json')
                    episodes = [json.loads(line) for line in (folder/'episodes.jsonl').read_text().splitlines()]
                    validate_boundary(state,read(folder/'FINISHED.json'),execution,method,
                        parent['registration_sha256'],plan['conditions'],episodes)
                    digest = sha(checkpoint)
                    receipts[parent['role']] = dict(checkpoint=str(checkpoint),sha256=digest,
                        steps=state['steps'],updates=state['learner']['num_gradient_steps'],cycle=state['cycle'])
                    if parent['role'] == 'fresh':
                        remaining = remaining_cycles(state,plan['total_cycles'])
                        resume = out/'parent_checkpoints'/(method+'.pt')
                        shutil.copy2(checkpoint,resume)
                        if sha(resume) != digest:
                            raise ValueError('Full-state checkpoint byte copy mismatch')
                        base_state = dict(receipts['fresh'])
                    del state
                parent_states[method] = dict(base_state,remaining_cycles=remaining,
                    fresh_start=spec['never_launched'])
                write(out/(method+'_PARENT_REVIEW.json'),dict(parents=receipts,
                    state_reset=spec['never_launched'],remaining_cycles=remaining,convergence_claim=False))
                if remaining == 0:
                    updated[method] = dict(scope='six original cycles already completed'); continue
                allocation = spec['allocation']
                command = [sys.executable,'-B',str(Path(plan['runtime'])/'source/tools/train_published_compliance_20261025.py'),
                    '--runtime',plan['runtime'],'--registration',plan['registration'],'--output',str(out/method),
                    '--controller',method,'--algorithm','cheq','--seed',str(plan['seed']),
                    '--device','cuda:'+str(allocation['gpu']),'--cpus',','.join(map(str,allocation['cpus'])),
                    '--workers',str(allocation['workers']),'--cycles',str(remaining)]
                if resume is not None:
                    command += ['--resume',str(resume)]
                os.sched_setaffinity(0,set(allocation['cpus'])|{cpu})
                try:
                    with (out/(method+'.log')).open('xb') as log:
                        child = subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                finally:
                    os.sched_setaffinity(0,{cpu})
                children[method] = child
                launched.append(dict(controller=method,pid=child.pid,gpu=allocation['gpu'],cpus=allocation['cpus'],command=command))
                write(out/'LAUNCH.json',dict(jobs=launched,registration=plan['registration'],parent_states=parent_states))
            write(out/'PROGRESS.json',dict(state='draining_or_resuming_independently',updated_unix=time.time(),
                launched=launched,updated=updated,parent_states=parent_states))
            time.sleep(5)
        write(out/'DISPATCH_FINISHED.json',dict(unix=time.time(),all_four_updated=True,
            parent_states=parent_states,convergence_claim=False))
        for folder in plan['retired_archives']:
            stop = Path(folder)/'MONITOR_STOP'
            if not stop.exists():
                with stop.open('x') as stream:
                    json.dump(dict(reason='All registered old learners exited and full boundary states preserved',
                        plan=str(plan_path),unix=time.time()),stream)
        # Keep the growing-LAUNCH archive alive through every finite stage cycle.
        # This avoids another archive handoff or requiring all children alive at once.
        while True:
            active = {}; finished = {}
            for method, child in children.items():
                code = child.poll(); active[method] = code is None
                if code is not None:
                    folder = out/method
                    if code or (folder/'FAILURE.json').exists():
                        raise RuntimeError('Finite stage learner failed: '+method)
                    finished[method] = read(folder/'FINISHED.json')
            write(out/'PROGRESS.json',dict(state='observing_original_finite_budget',updated_unix=time.time(),
                active=active,finished=finished,parent_states=parent_states))
            if not any(active.values()):
                break
            time.sleep(10)
        write(out/'MIGRATION_FINISHED.json',dict(unix=time.time(),scope='finite learners exited; archive may finish',
            convergence_claim=False,finished=finished))
    except BaseException as error:
        write(out/'MIGRATION_FAILURE.json',dict(error=repr(error),launched=launched,
            note='Preserve parents and children; no automatic retry or blanket termination'))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True)
    main(parser.parse_args().plan)
