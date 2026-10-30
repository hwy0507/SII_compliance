"""Bounded handoff from an exact live collection to qualified shared data.

No simulation or fitting is launched. All 30 qualifications and the original
retained service's exit status must pass before building the common dataset.
Failures are preserved; a wait timeout is not a collection termination claim.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time

from collect_special_scene_coverage_20261029 import ROOT, read, sha, write, validate, require_resources


def now():
    return datetime.now(timezone.utc).isoformat()


def service(name):
    raw = subprocess.check_output(['systemctl', '--user', 'show', name, '-p', 'MainPID',
        '-p', 'LoadState', '-p', 'ActiveState', '-p', 'SubState', '-p', 'Result',
        '-p', 'InvocationID', '-p', 'ExecMainCode', '-p', 'ExecMainStatus'], text=True)
    return dict(line.split('=', 1) for line in raw.splitlines())


def start_ticks(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
    except FileNotFoundError:
        return None


def terminal_ok(reg, state, unit, ticks):
    if unit['LoadState'] != 'loaded' or unit['InvocationID'] != reg['collection_invocation']:
        raise ValueError('Collection service identity changed or missing; inspect without restarting')
    if unit['MainPID'] != '0':
        if int(unit['MainPID']) != reg['collection_pid'] or ticks != reg['collection_start_ticks']:
            raise ValueError('Collection PID identity changed')
        return False
    if ticks == reg['collection_start_ticks']:
        raise ValueError('Original collection process still exists')
    if unit['SubState'] != 'exited' or unit['Result'] != 'success' or unit['ExecMainCode'] != '1' or unit['ExecMainStatus'] != '0':
        raise ValueError('Collection did not produce a verified successful retained exit')
    if state['status'] != 'qualified_complete' or len(state['episodes']) != 30:
        raise ValueError('All 30 completed qualified demonstrations are required')
    if any(e['status'] != 'qualified' or e['returncode'] != 0 for e in state['episodes']):
        raise ValueError('Nonqualified demonstration retained; no dataset build')
    return True


def prepare(root, collection, training, unit):
    if root.exists() or training.exists():
        raise FileExistsError('Use new handoff and dataset directories')
    plan_path = collection / 'COLLECTION_PLAN.json'
    plan = validate(plan_path)
    current, state = service(unit), read(collection / 'COLLECTION_PROGRESS.json')
    if current['ActiveState'] != 'active' or current['SubState'] != 'running' or state['status'] != 'running':
        raise ValueError('Preparation binds the exact currently live collection')
    pid = int(current['MainPID'])
    cmd = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
    if not any(Path(arg.decode()).name == 'collect_special_scene_coverage_20261029.py' for arg in cmd if arg):
        raise ValueError('Wrong collection process')
    command = [arg.decode() for arg in cmd if arg]
    given = Path(command[command.index('--plan')+1])
    if not given.is_absolute():
        given = Path(f'/proc/{pid}/cwd').resolve() / given
    if given.resolve() != plan_path or state['plan_sha256'] != sha(plan_path):
        raise ValueError('Live collection is not this plan')
    files = [Path(__file__), ROOT/'tools/build_special_coverage_dataset_20261029.py',
             ROOT/'tools/audit_special_coverage_dataset_20261029.py',
             ROOT/'tools/audit_v8_train_direction_coverage_20261029.py',
             ROOT/'tools/describe_ball_actual_motion_20261029.py',
             ROOT/'tools/collect_special_scene_coverage_20261029.py']
    reg = dict(schema='sii-direction-qualified-data-handoff-v1', registered_utc=now(),
        collection=str(collection), training=str(training), collection_service=unit,
        collection_pid=pid, collection_start_ticks=start_ticks(pid),
        collection_invocation=current['InvocationID'],
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        plan_sha256=sha(plan_path), maximum_wait_s=7200,
        source_sha256={str(p.relative_to(ROOT)): sha(p) for p in files},
        episode_ids=[e['id'] for e in plan['episodes']],
        action='Wait exact existing collection, build only if all30 qualified, describe actual train direction/load and ball movement; never fit or evaluate students',
        resources=dict(cpu_affinity=[6], numerical_threads=1, memory_max=3221225472, swap_max=0))
    root.mkdir(parents=True)
    write(root/'REGISTRATION.json', reg)
    print('prepared_not_started', root, sha(root/'REGISTRATION.json'), flush=True)


def run(root):
    guard = (root/'.handoff.lock').open('a')
    fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (root/'execution.json').exists():
        raise FileExistsError('No automatic replay of a handoff')
    resources = require_resources()
    reg = read(root/'REGISTRATION.json')
    collection, training = Path(reg['collection']), Path(reg['training'])
    state = dict(status='waiting_exact_collection', started_utc=now(),
                 registration_sha256=sha(root/'REGISTRATION.json'), resources=resources, observations=[])
    write(root/'execution.json', state)
    def verify_sources():
        if Path('/proc/sys/kernel/random/boot_id').read_text().strip() != reg['boot_id']:
            raise ValueError('Boot changed; inspect original collection')
        if sha(collection/'COLLECTION_PLAN.json') != reg['plan_sha256']:
            raise ValueError('Collection plan changed')
        for name, digest in reg['source_sha256'].items():
            if sha(ROOT/name) != digest:
                raise ValueError('Handoff source changed: '+name)
    try:
        start = time.monotonic()
        while True:
            verify_sources()
            current = service(reg['collection_service'])
            progress = read(collection/'COLLECTION_PROGRESS.json')
            if progress['plan_sha256'] != reg['plan_sha256']:
                raise ValueError('Collection progress belongs to another plan')
            ready = terminal_ok(reg, progress, current, start_ticks(reg['collection_pid']))
            state['observations'].append(dict(utc=now(), completed=len(progress['episodes']),
                current=progress.get('current'), status=progress['status'], service=current))
            write(root/'execution.json', state)
            if ready:
                break
            if time.monotonic()-start >= reg['maximum_wait_s']:
                state.update(status='wait_expired_collection_not_declared_stopped', ended_utc=now())
                write(root/'execution.json', state)
                return
            time.sleep(30)
        if [e['id'] for e in progress['episodes']] != reg['episode_ids']:
            raise ValueError('Collection identities or order differ')
        validate(collection/'COLLECTION_PLAN.json')
        commands = [
            ['build_special_coverage_dataset_20261029.py', '--plan', str(collection/'COLLECTION_PLAN.json'), '--output', str(training)],
            ['audit_special_coverage_dataset_20261029.py', '--training', str(training), '--output', str(root/'TRAIN_DIRECTION_COVERAGE.json')],
            ['describe_ball_actual_motion_20261029.py', '--training', str(training), '--output', str(root/'TRAIN_BALL_ACTUAL_MOTION.json')],
        ]
        for command in commands:
            verify_sources()
            state.update(status='processing', current=command[0], updated_utc=now())
            write(root/'execution.json', state)
            with (root/(command[0]+'.log')).open('x') as log:
                subprocess.run([sys.executable, str(ROOT/'tools'/command[0]), *command[1:]],
                    cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        verify_sources()
        state.update(status='qualified_dataset_ready_for_coverage_review_not_fitted', ended_utc=now(),
            training_data_sha256=sha(training/'data/training_data.npz'),
            metadata_sha256=sha(training/'data/DATA_COMPLETE.json'),
            training_registration_sha256=sha(training/'REGISTRATION.json'),
            train_coverage_sha256=sha(root/'TRAIN_DIRECTION_COVERAGE.json'),
            actual_motion_sha256=sha(root/'TRAIN_BALL_ACTUAL_MOTION.json'))
        write(root/'execution.json', state)
    except BaseException as exc:
        state.update(status='handoff_failed_preserved', error=repr(exc), ended_utc=now())
        write(root/'execution.json', state)
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--collection', type=Path)
    p.add_argument('--training', type=Path)
    p.add_argument('--service')
    p.add_argument('--run', action='store_true')
    a = p.parse_args()
    if a.run:
        run(a.root.resolve())
    else:
        if not all((a.collection, a.training, a.service)):
            p.error('Preparation requires collection, training and service')
        prepare(a.root.resolve(), a.collection.resolve(), a.training.resolve(), a.service)
