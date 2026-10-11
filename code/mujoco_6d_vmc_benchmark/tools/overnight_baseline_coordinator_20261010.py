"""One-shot 15-hour local baseline handoff.

The currently registered classical search owns the simulator lock first. This
coordinator waits for its normal completion, then prepares a fresh RL
continuation from immutable saved checkpoints. It never edits old receipts,
restarts a live job, uses the server for compute, opens final conditions, or
turns a finite run into a convergence claim.
"""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def now():
    return datetime.now(timezone.utc)


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def active_rl_units():
    result = subprocess.run(
        ['systemctl', '--user', 'list-units', '--type=service', '--state=running',
         '--no-legend', '--plain'], capture_output=True, text=True, check=True)
    return [line for line in result.stdout.splitlines()
            if 'sii-local-rl-' in line or 'sii-convergence-' in line]


def classical_state(root):
    state = read(root / 'execution.json')
    if state.get('status') == 'failed_preserved':
        raise RuntimeError('Classical search failed; preserve it and do not dispatch RL')
    return state


def prepare_rl(benchmark, base_rl, run_root, deadline):
    if run_root.exists():
        raise RuntimeError(f'RL handoff directory already exists: {run_root}')
    command = [sys.executable, str(benchmark / 'tools/launch_rl_convergence_20261010.py'),
               'prepare', '--root', str(base_rl / 'campaign_v2'), '--run-root', str(run_root)]
    subprocess.run(command, check=True)
    registration_path = run_root / 'REGISTRATION.json'
    registration = read(registration_path)
    registration['authorization'] = (
        '2026-10-10 user: one-shot overnight 15-hour local baseline handoff; '
        'classical search first, then saved-checkpoint RL continuation')
    registration['dispatch_deadline_utc'] = deadline.isoformat()
    registration['deadline_basis'] = (
        'User-authorized one-shot 15-hour window measured from coordinator start; '
        'a finite safety stop, not a convergence criterion')
    registration['server_compute'] = False
    registration['classical_prerequisite'] = str(
        benchmark / 'outputs/classical_boundary_search_20261010_v1/execution.json')
    write(registration_path, registration)
    return registration_path


def run(args, lock_path):
    # Own a separate orchestration lock; the learner owns the simulator lock.
    # Never overwrite an earlier attempt, including one that failed at startup.
    with (args.output / 'coordinator.lock').open('a') as guard:
        fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (args.output / 'execution.json').exists():
            raise RuntimeError('Existing execution receipt; use a new output directory')
        try:
            return run_once(args, lock_path)
        except BaseException as exc:
            path = args.output / 'execution.json'
            state = read(path) if path.exists() else {}
            state.update(status='failed_preserved', error=repr(exc), ended_utc=now().isoformat())
            write(path, state)
            raise


def run_child(command):
    result = subprocess.run(command, check=False)
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command)
    return result


def run_once(args, lock_path):
    started = now()
    deadline = started + timedelta(hours=getattr(args, 'safety_hours', 15))
    state = dict(status='waiting_for_classical', started_utc=started.isoformat(),
                 deadline_utc=deadline.isoformat(), host=os.uname().nodename,
                 server_compute=False, final_test_reads=0, rl_run_root=None,
                 classical_completed=None, failures=[])
    write(args.output / 'execution.json', state)
    while True:
        if now() >= deadline:
            state.update(status='stopped_at_deadline', ended_utc=now().isoformat(),
                         reason='Classical prerequisite did not finish within 15-hour window')
            write(args.output / 'execution.json', state)
            return
        current = classical_state(args.classical_root)
        state['classical_completed'] = len(current.get('completed', []))
        state['classical_status'] = current.get('status')
        write(args.output / 'execution.json', state)
        if current.get('status') == 'complete':
            break
        time.sleep(60)

    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if active_rl_units():
            raise RuntimeError('An RL training service is active; do not duplicate it')
        available_kib = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                                 if line.startswith('MemAvailable:')))
        if available_kib < 7 * 1024 * 1024:
            raise RuntimeError(f'Insufficient memory for two RL lanes: {available_kib} KiB')
        run_root = args.rl_parent / getattr(args, 'run_name', 'overnight_15h_20261010')
        state.update(status='preparing_rl',available_memory_kib=available_kib,
                     rl_run_root=str(run_root))
        write(args.output / 'execution.json', state)
        prepare_rl(args.benchmark, args.rl_parent, run_root, deadline)
        registration = read(run_root / 'REGISTRATION.json')
        if getattr(args, 'authorization', None):
            registration['authorization'] = args.authorization
            registration['deadline_basis'] = 'Agent-selected finite safety horizon under renewed user authority; not an extension of the expired overnight window or convergence criterion'
            write(run_root / 'REGISTRATION.json', registration)
        if getattr(args, 'reuse_development_root', None):
            from office_v7_uniform24_20261008 import sha
            registration['reuse_development'] = {}
            for name, parent in registration['parents'].items():
                if parent['scheduled_limit'] != 110000:
                    continue
                segment = args.reuse_development_root.resolve() / (name + '_closed110000')
                if segment.resolve() != Path(parent['segment']).resolve():
                    raise RuntimeError('Reused development is not the registered parent checkpoint')
                audit = Path(str(segment) + '.development_audit.json')
                registration['reuse_development'][name] = dict(segment=str(segment),
                    audit=str(audit), audit_sha256=sha(audit))
            write(run_root / 'REGISTRATION.json', registration)
        command = [sys.executable, str(args.benchmark / 'tools/launch_rl_convergence_20261010.py'),
                   'run', '--root', str(args.rl_parent / 'campaign_v2'), '--run-root', str(run_root)]
        state.update(status='running_rl',rl_registration=str(run_root / 'REGISTRATION.json'),
                     rl_command=command)
        write(args.output / 'execution.json', state)
        # The child rechecks resources and acquires this lock atomically itself.
        # A competing campaign in this handoff gap causes a safe child failure.
        fcntl.flock(lock, fcntl.LOCK_UN)
        try:
            if now() >= deadline:
                raise TimeoutError('Dispatch deadline reached during preparation')
            result = run_child(command)
            state.update(status='complete_review_required' if result.returncode == 0
                         else 'failed_preserved', rl_returncode=result.returncode)
        except BaseException as exc:
            state.update(status='failed_preserved', error=repr(exc))
            if isinstance(exc, subprocess.CalledProcessError):
                state['rl_returncode'] = exc.returncode
            raise
        finally:
            state['ended_utc'] = now().isoformat()
            write(args.output / 'execution.json', state)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--benchmark', type=Path, required=True)
    p.add_argument('--classical-root', type=Path, required=True)
    p.add_argument('--rl-parent', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--run-name', default='overnight_15h_20261010')
    p.add_argument('--safety-hours', type=float, default=15)
    p.add_argument('--authorization')
    p.add_argument('--reuse-development-root', type=Path)
    a = p.parse_args()
    for field in ('benchmark', 'classical_root', 'rl_parent'):
        setattr(a, field, getattr(a, field).resolve())
    if a.safety_hours <= 0 or Path(a.run_name).name != a.run_name or a.run_name in ('.', '..'):
        p.error('Positive safety hours and a single run directory name required')
    a.output = a.output.resolve()
    a.output.mkdir(parents=True, exist_ok=True)
    lock_path = a.benchmark / 'outputs/baseline_local_rl_20261009/.local-rl-compute.lock'
    run(a, lock_path)


if __name__ == '__main__':
    main()
