"""Run exactly the reviewed two SAC commands once; never retry or manage peers."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import traceback


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def save(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def verify(root, expected_plan, expected_self):
    require(sha(__file__) == expected_self, 'Supervisor source changed')
    require(sha(root / 'PLAN.json') == expected_plan, 'Reviewed PLAN changed')
    plan = json.loads((root / 'PLAN.json').read_text())
    require(plan['status'] == 'prepared_not_started', 'Plan is not prepared')
    for name, field in [('BUILD.json', 'build_sha256'), ('PREFLIGHT.json', 'preflight_sha256')]:
        require(sha(root / name) == plan[field], name + ' changed')
    preflight = json.loads((root / 'PREFLIGHT.json').read_text())
    require(preflight['passed'] and preflight['simulator_steps'] == preflight['gradient_updates'] == 0,
            'No passing zero-step preflight')
    require(not (root / 'PREFLIGHT_FAILED.json').exists(), 'Failed preflight exists')
    source = root / 'source'
    actual = {str(p.relative_to(source)): sha(p) for p in sorted(source.rglob('*'))
              if p.is_file() and '__pycache__' not in p.parts}
    require(actual == plan['source_sha256'], 'Frozen source changed')
    require(all(not ((source / name).stat().st_mode & 0o222) for name in actual), 'Writable source')
    require(sha(root / 'demo/manifest.json') == plan['demo']['manifest_sha256'], 'Demo manifest changed')
    for name, digest in plan['demo']['artifact_sha256'].items():
        require(sha(root / 'demo' / name) == digest, 'Demo changed: ' + name)
    require([j['branch'] for j in plan['jobs']] == ['online_only', 'demo_prefill'], 'Unexpected jobs')
    require(plan['max_workers'] == 2 and plan['global_worker_cap'] == 4, 'Unexpected worker cap')
    for job in plan['jobs']:
        branch = job['branch']
        require(Path(job['output']) == root / 'training' / branch, 'Unexpected output path')
        require(Path(job['log']) == root / (branch + '.log'), 'Unexpected log path')
        require(job['command'][:5] == ['/usr/bin/timeout', '--signal=TERM', '--kill-after=15s', '7200s',
                                     '/home/arm1/vmc_mujoco_runtime/.venv/bin/python'], 'Unexpected timeout/runtime')
        require(job['command'][5:7] == ['-u', str(source / 'tools/run_canonical48_sac_20260925.py')],
                'Unexpected entry')
        require(job['online_steps'] == 8192 and job['expected_updates'] == 8092, 'Budget changed')
        require(not Path(job['output']).exists() and not Path(job['log']).exists(), 'Output/log collision')
    for name in ('supervisor', 'training'):
        require(not (root / name).exists(), 'Existing run state: ' + name)
    memory = {line.split(':')[0]: int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()}
    require(memory['MemAvailable'] * 1024 >= 2.5 * 1024 ** 3, 'Available system memory below 2.5 GiB')
    return plan, dict(mem_available_bytes=memory['MemAvailable'] * 1024,
                      cpu_affinity=sorted(os.sched_getaffinity(0)), checked_unix=time.time())


def outcome(job, returncode):
    folder = Path(job['output'])
    failed = folder / 'FAILED.json'
    complete = folder / 'COMPLETE.json'
    result = dict(returncode=returncode, ended_unix=time.time(),
                  branch_failed_exists=failed.exists(), branch_complete_exists=complete.exists())
    if failed.exists():
        result['branch_failed_sha256'] = sha(failed)
    if complete.exists():
        result['branch_complete_sha256'] = sha(complete)
    if returncode == 124:
        reason = 'GNU timeout reached the fixed 7200-second deadline'
    elif returncode == 137:
        reason = 'SIGKILL exit 137; timeout kill-after or external/OOM kill, cause not uniquely known'
    elif returncode < 0:
        reason = 'Owned timeout process terminated by signal ' + str(-returncode)
    elif returncode != 0:
        reason = 'Owned timeout command returned nonzero exit ' + str(returncode)
    elif failed.exists():
        reason = 'Branch has FAILED.json despite process exit 0'
    elif not complete.exists():
        reason = 'Process exit 0 without branch COMPLETE.json'
    elif json.loads(complete.read_text()).get('status') != 'complete':
        reason = 'Branch COMPLETE.json has unexpected status'
    else:
        reason = None
    result.update(status='complete' if reason is None else 'failed', failure_reason=reason)
    return result


def cleanup(owned):
    """Only newly created timeout process groups, bounded TERM then KILL."""
    active = [(process, row) for process, row in owned if process.poll() is None]
    for process, row in active:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            row['supervisor_cleanup_signal'] = 'TERM'
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and any(process.poll() is None for process, _ in active):
        time.sleep(.2)
    for process, row in active:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
                row['supervisor_cleanup_signal'] = 'KILL'
            except ProcessLookupError:
                pass
        try:
            process.wait(timeout=5)
            row.update(returncode=process.returncode, ended_unix=time.time(), status='failed',
                       failure_reason='Supervisor interrupted or failed; owned process group cleaned up')
        except subprocess.TimeoutExpired:
            row.update(status='failed', failure_reason='Owned process did not reap within cleanup bound')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--supervisor-sha256', required=True)
    parser.add_argument('--launch', action='store_true', help='Only after explicit review authorization')
    args = parser.parse_args()
    root = args.root.resolve()
    plan, resources = verify(root, args.plan_sha256, args.supervisor_sha256)
    if not args.launch:
        print(json.dumps(dict(passed=True, simulations_started=0, gradient_updates=0, jobs=2, resources=resources)))
        return
    folder = root / 'supervisor'
    folder.mkdir(exist_ok=False)
    state = dict(pid=os.getpid(), started_unix=time.time(), status='running',
                 plan_sha256=args.plan_sha256, supervisor_sha256=args.supervisor_sha256,
                 resources=resources, jobs=[], retries=0, max_owned_workers=2,
                 external_worker_coordination='Root must verify at most 2 existing physical workers before launch')
    owned = []
    logs = []

    def interrupted(signum, frame):
        raise RuntimeError('Supervisor received signal ' + str(signum))

    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, interrupted)
    try:
        save(folder / 'status.json', state)
        for job in plan['jobs']:
            row = dict(branch=job['branch'], command=job['command'], output=job['output'],
                       log=job['log'], environment=job['environment'], status='starting')
            state['jobs'].append(row)
            save(folder / 'status.json', state)
            try:
                log = Path(job['log']).open('xb')
                logs.append(log)
                process = subprocess.Popen(job['command'], stdout=log, stderr=subprocess.STDOUT,
                    env=dict(os.environ, **job['environment']), cwd=root / 'source', start_new_session=True)
                owned.append((process, row))
                row.update(status='running', timeout_pid=process.pid, process_group_id=process.pid,
                           started_unix=time.time())
            except Exception as error:
                row.update(status='failed', returncode=None, ended_unix=time.time(),
                           failure_reason='Launch failed without retry: ' + repr(error))
            save(folder / 'status.json', state)
        while any(process.poll() is None for process, _ in owned):
            for process, row in owned:
                if process.poll() is not None and row['status'] == 'running':
                    job = next(job for job in plan['jobs'] if job['branch'] == row['branch'])
                    row.update(outcome(job, process.returncode))
                    save(folder / 'status.json', state)
            time.sleep(1)
        for process, row in owned:
            if row['status'] == 'running':
                job = next(job for job in plan['jobs'] if job['branch'] == row['branch'])
                row.update(outcome(job, process.returncode))
        state.update(status='complete' if all(row['status'] == 'complete' for row in state['jobs']) else 'failed',
                     ended_unix=time.time())
    except BaseException as error:
        for signum in (signal.SIGTERM, signal.SIGINT):
            signal.signal(signum, signal.SIG_IGN)
        cleanup(owned)
        state.update(status='failed', ended_unix=time.time(), error=repr(error), traceback=traceback.format_exc())
        raise
    finally:
        for log in logs:
            log.close()
        save(folder / 'status.json', state)
        save(folder / ('COMPLETE.json' if state['status'] == 'complete' else 'FAILED.json'), state)
    if state['status'] != 'complete':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
