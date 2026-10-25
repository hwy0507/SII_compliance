"""Drain complete cycles and resume registered performance-only continuations.

Preserves original checkpoints, failed attempts, learner/optimizer/replay/RNG
state and complete-cycle history. Never treats migration as convergence. Each
controller retains its CPU/GPU/sampler allocation. A COORDINATOR_STOP file stops
future dispatch; already launched learners have their own STOP_REQUESTED gate.
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def main(args):
    torch.set_num_threads(1)
    os.sched_setaffinity(0, {args.cpu})
    registration = json.loads(args.registration.read_text())
    runtime = Path(registration['runtime'])
    if sha(runtime/'RUNTIME.json') != registration['runtime_sha256']:
        raise ValueError('Registered runtime mismatch')
    sys.path.insert(0, str(runtime/'source/tools'))
    from train_published_compliance_20261025 import validate_resume_protocol
    parent_digest = registration['resume_parent_registration']['sha256']
    validate_resume_protocol(parent_digest, registration, sha(args.registration))
    old_jobs = json.loads((args.parent_run/'LAUNCH.json').read_text())['jobs']
    identities = {j['controller']: identity(j['pid']) for j in old_jobs}
    if len(old_jobs) != 4 or any(v is None for v in identities.values()):
        raise ValueError('All four original learners must be live before requesting migration')
    executions = {j['controller']: json.loads((args.parent_run/j['controller']/'EXECUTION.json').read_text())
        for j in old_jobs}
    if any(e['protocol_sha256'] != parent_digest for e in executions.values()):
        raise ValueError('Original learners differ from the registered continuation parent')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'parent_checkpoints').mkdir()
    shutil.copy2(__file__, args.output/'coordinator_source.py.txt')
    write(args.output/'COORDINATOR.json', dict(pid=os.getpid(), started_unix=time.time(),
        parent_run=str(args.parent_run), registration=str(args.registration),
        source_sha256=sha(Path(__file__)), original_process_identities=identities,
        convergence_claim=False, scope='performance-only exact learner/replay continuation at cycle boundary'))
    for job in old_jobs:
        path = args.parent_run/job['controller']/'STOP_REQUESTED'
        with path.open('x') as stream:
            json.dump(dict(reason='registered performance-only continuation at complete cycle boundary',
                coordinator=str(args.output), requested_unix=time.time()), stream)
    launched, children, parent_states = [], {}, {}
    env = dict(os.environ, MUJOCO_GL='disable', OMP_NUM_THREADS='1',
        OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    try:
        while True:
            if (args.output/'COORDINATOR_STOP').exists():
                write(args.output/'DISPATCH_STOPPED.json', dict(launched=launched,
                    note='Already launched learners remain independently managed'))
                return
            for job in old_jobs:
                method = job['controller']
                if method in children:
                    if children[method].poll() is not None:
                        raise RuntimeError('Continuation learner exited during migration: '+method)
                    continue
                folder = args.parent_run/method
                if (folder/'FAILURE.json').exists():
                    raise RuntimeError('Original learner failed while draining: '+method)
                if identity(job['pid']) == identities[method]:
                    continue
                finished = json.loads((folder/'FINISHED.json').read_text())
                checkpoint = args.output/'parent_checkpoints'/(method+'.pt')
                shutil.copy2(folder/'checkpoint_latest.pt', checkpoint)
                state = torch.load(checkpoint, map_location='cpu', weights_only=False)
                if (state['boundary'] != 'complete_condition_cycle'
                        or state['steps'] != finished['steps']
                        or state['controller'] != method or state['protocol_sha256'] != parent_digest):
                    raise ValueError('Original learner did not save the required complete-cycle checkpoint')
                execution = executions[method]
                parent_states[method] = dict(steps=state['steps'], updates=state['learner']['num_gradient_steps'],
                    cycle=state['cycle'], checkpoint_sha256=sha(checkpoint))
                command = [sys.executable, '-B', str(runtime/'source/tools/train_published_compliance_20261025.py'),
                    '--runtime', str(runtime), '--registration', str(args.registration),
                    '--output', str(args.output/method), '--controller', method,
                    '--algorithm', execution['algorithm'], '--seed', str(execution['seed']),
                    '--device', execution['device'], '--cpus', ','.join(map(str, job['cpus'])),
                    '--workers', str(execution['workers']), '--resume', str(checkpoint)]
                # Child must see the original allocation before the trainer
                # binds its learner and samplers to their distinct cores.
                os.sched_setaffinity(0, set(job['cpus']) | {args.cpu})
                try:
                    with (args.output/(method+'.log')).open('xb') as log:
                        child = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)
                finally:
                    os.sched_setaffinity(0, {args.cpu})
                children[method] = child
                launched.append(dict(controller=method, pid=child.pid, gpu=job['gpu'],
                    cpus=job['cpus'], command=command))
                write(args.output/'LAUNCH.json', dict(started_unix=time.time(), jobs=launched,
                    registration=str(args.registration), parent_run=str(args.parent_run),
                    parent_states=parent_states, restart='exact optimizer/RNG/replay continuation, complete cycle'))
                del state
            progress = {}
            for method in children:
                path = args.output/method/'PROGRESS.json'
                if path.exists():
                    progress[method] = json.loads(path.read_text())
            write(args.output/'MIGRATION_PROGRESS.json', dict(updated_unix=time.time(),
                launched=[j['controller'] for j in launched], progress=progress, parent_states=parent_states))
            if len(progress) == 4 and all(progress[m]['steps'] > parent_states[m]['steps']
                    and progress[m]['updates'] > parent_states[m]['updates'] for m in progress):
                archive = args.output/'cycle_archive'
                with (args.output/'cycle_archive.log').open('xb') as log:
                    monitor = subprocess.Popen(['taskset', '-c', str(args.cpu), sys.executable, '-B',
                        str(runtime/'source/tools/archive_published_cycle_checkpoints_20261025.py'),
                        '--run', str(args.output), '--output', str(archive)], stdout=log,
                        stderr=subprocess.STDOUT, env=env, start_new_session=True)
                write(args.output/'MIGRATION_FINISHED.json', dict(ended_unix=time.time(),
                    all_new_learners_updated=True, archive_pid=monitor.pid,
                    parent_states=parent_states, convergence_claim=False))
                return
            time.sleep(5)
    except BaseException as error:
        write(args.output/'MIGRATION_FAILURE.json', dict(error=repr(error), launched=launched,
            note='Retain all originals and launched jobs; inspect before any retry'))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-run', type=Path, required=True)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cpu', type=int, default=54)
    main(parser.parse_args())
