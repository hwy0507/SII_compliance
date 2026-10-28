"""Finish reporting an already running108, without dispatching any physics.

Bind the live original service/PID/start tick. Plot completed fitting records,
wait at most12h for that same service to end successfully, then run the existing
full audit, contact diagnostics and presentation. No retries, model selection,
training, new simulations, server computation, or automatic goal completion.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from prepare_special_frozen_test_20261028 import read, require, sha

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ('postprocess_running_special108_20261029.py',
         'prepare_special_frozen_test_20261028.py',
         'audit_special_frozen108_20261028.py',
         'report_special_frozen108_20261028.py',
         'supplement_special_contact_metrics_20261028.py',
         'plot_nonrl_new30_learning_20261026.py',
         'archive_special_frozen108_20261028.py',
         'archive_nonrl_new30_physics_20261026.py')


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def identity(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
    except FileNotFoundError:
        return None


def service(name):
    raw = subprocess.check_output(['systemctl', '--user', 'show', name, '-p',
        'ActiveState', '-p', 'Result', '-p', 'MainPID'], text=True)
    return dict(line.split('=', 1) for line in raw.splitlines())


def ready(plan, current, ticks, execution, preparation):
    """Pure boundary guard; a different live process is never accepted."""
    require(execution['status'] in ('running', 'complete'), 'Matrix failed or unexpected state')
    require(preparation['status'] in ('evaluating_frozen108', 'evaluation_complete_pending_independent_audit'),
            'Preparation failed or unexpected state')
    if current['ActiveState'] in ('active', 'deactivating'):
        if current['ActiveState'] == 'active':
            require(int(current['MainPID']) == plan['parent_pid'] and ticks == plan['parent_start_ticks'],
                    'Original physical service identity changed')
        else:
            require(int(current['MainPID']) in (0, plan['parent_pid']) and ticks in (None, plan['parent_start_ticks']),
                    'Unexpected exiting service identity')
        return False
    require(ticks != plan['parent_start_ticks'], 'Original process remains outside its service')
    require(current['ActiveState'] == 'inactive' and current['Result'] == 'success', 'Original service did not succeed')
    require(execution['status'] == 'complete' and execution['completed'] == execution['expected'] == 108,
            'Original matrix incomplete')
    require(preparation['status'] == 'evaluation_complete_pending_independent_audit', 'Dispatch incomplete')
    return True


def prepare(root, preparation, service_name):
    require(not root.exists(), 'Use new postprocessing directory')
    p = read(preparation / 'REGISTRATION.json')
    evaluation, training = Path(p['evaluation']), Path(p['training'])
    current = service(service_name)
    pid = int(current['MainPID']); ticks = identity(pid)
    require(current['ActiveState'] == 'active' and ticks is not None, 'Bind actual live original108')
    cmd = [s.decode() for s in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0') if s]
    require(any(Path(s).name == 'prepare_special_frozen_test_20261028.py' for s in cmd)
            and '--root' in cmd and '--run' in cmd, 'Wrong original process')
    parent_root = Path(cmd[cmd.index('--root') + 1])
    if not parent_root.is_absolute():
        parent_root = Path(f'/proc/{pid}/cwd').resolve() / parent_root
    require(parent_root.resolve() == preparation, 'Service belongs to another preparation')
    require(read(evaluation / 'execution.json')['status'] == 'running', 'Matrix already terminal')
    require(read(training / 'execution.json')['status'] == 'complete', 'Fitting incomplete')
    require(sha(training / 'MODEL_LOCK.json') == sha(evaluation / 'INPUT_MODEL_LOCK.json'), 'Model lock differs')
    require(not (evaluation / 'FROZEN108_AUDIT.json').exists(), 'Audit exists; inspect instead')
    root.mkdir(parents=True); snapshot = root / 'tools'; snapshot.mkdir()
    for name in TOOLS:
        shutil.copy2(ROOT / 'tools' / name, snapshot / name)
    plan = dict(schema='sii-running108-postprocess-only-v1', registered_utc=now(),
                preparation=str(preparation), preparation_sha256=sha(preparation / 'REGISTRATION.json'),
                training=str(training), evaluation=str(evaluation), working_directory=str(ROOT),
                parent_service=service_name, parent_pid=pid, parent_start_ticks=ticks,
                model_lock_sha256=sha(training / 'MODEL_LOCK.json'), python=sys.executable,
                snapshot_sha256={name: sha(snapshot / name) for name in TOOLS}, wait_seconds=43200,
                resources=dict(threads=1, cpu_quota_percent=50, memory_max_bytes=3221225472, swap_bytes=0),
                scope='Existing running108 only. Completed-fit plots now; full audit/contact/report only after original service ends. No dispatch, retries, fitting, server use or goal completion.')
    write(root / 'REGISTRATION.json', plan)
    print(json.dumps(dict(status='prepared', root=str(root), parent_pid=pid, parent_start_ticks=ticks)))


def run(root):
    lock = (root / '.postprocess.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    require(not (root / 'execution.json').exists(), 'Do not replay this postprocessor')
    plan = read(root / 'REGISTRATION.json')
    require(plan['schema'] == 'sii-running108-postprocess-only-v1', 'Wrong registration')
    cg = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    limit = (cg / 'memory.max').read_text().strip()
    require(limit != 'max' and int(limit) <= 3221225472 and (cg / 'memory.swap.max').read_text().strip() == '0',
            'Actual bounded memory and no swap required')
    require(all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')),
            'Single numerical thread required')
    state = dict(status='starting', started_utc=now(), registration_sha256=sha(root / 'REGISTRATION.json'))
    evaluation, preparation = Path(plan['evaluation']), Path(plan['preparation'])

    def verify():
        require(sha(root / 'REGISTRATION.json') == state['registration_sha256'], 'Registration changed')
        require(sha(preparation / 'REGISTRATION.json') == plan['preparation_sha256'], 'Preparation changed')
        require(sha(Path(__file__)) == plan['snapshot_sha256'][Path(__file__).name], 'Run the frozen postprocessor')
        for name, digest in plan['snapshot_sha256'].items():
            require(sha(root / 'tools' / name) == digest, 'Snapshot changed')
        require(sha(evaluation / 'INPUT_MODEL_LOCK.json') == plan['model_lock_sha256'], 'Evaluation model lock changed')
        require(sha(Path(plan['training']) / 'MODEL_LOCK.json') == plan['model_lock_sha256'], 'Training model lock changed')

    def child(stage, script, arguments):
        verify()
        command = [plan['python'], str(root / 'tools' / script), *map(str, arguments)]
        state.update(status=stage, updated_utc=now(), command=command)
        write(root / 'execution.json', state)
        with (root / (stage + '.log')).open('x') as output:
            subprocess.run(command, cwd=plan['working_directory'], stdout=output, stderr=subprocess.STDOUT, check=True)

    try:
        verify()
        # Check parent identity before doing even read-only work for this batch.
        ready(plan, service(plan['parent_service']), identity(plan['parent_pid']),
              read(evaluation / 'execution.json'), read(preparation / 'execution.json'))
        child('selected_learning_curves', 'plot_nonrl_new30_learning_20261026.py',
              ['--root', plan['training'], '--output', root / 'LEARNING_CURVES'])
        deadline = time.monotonic() + plan['wait_seconds']
        while True:
            verify()
            current = service(plan['parent_service'])
            execution = read(evaluation / 'execution.json')
            prepared = read(preparation / 'execution.json')
            finished = ready(plan, current, identity(plan['parent_pid']), execution, prepared)
            state.update(status='waiting_for_original108', checked_utc=now(), parent_service=current,
                         completed=execution['completed'], expected=108)
            write(root / 'execution.json', state)
            if finished:
                break
            require(time.monotonic() < deadline, 'Bounded observation expired; original physics untouched')
            time.sleep(30)
        child('independent_saved_evidence_audit', 'audit_special_frozen108_20261028.py',
              ['--preparation', preparation, '--output', evaluation / 'FROZEN108_AUDIT.json'])
        require(not (root / 'FINAL_AUDIT.json').exists(), 'Preserve old audit')
        shutil.copy2(evaluation / 'FROZEN108_AUDIT.json', root / 'FINAL_AUDIT.json')
        child('contact_diagnostics', 'supplement_special_contact_metrics_20261028.py',
              ['--audit', root / 'FINAL_AUDIT.json', '--output', root / 'CONTACT_DIAGNOSTICS.json'])
        child('six_metric_presentation', 'report_special_frozen108_20261028.py',
              ['--audit', root / 'FINAL_AUDIT.json', '--output', root / 'PRESENTATION'])
        state.update(status='complete_pending_visual_review_and_archive', ended_utc=now(),
                     final_audit_sha256=sha(root / 'FINAL_AUDIT.json'))
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc), ended_utc=now())
        raise
    finally:
        write(root / 'execution.json', state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--preparation', type=Path)
    parser.add_argument('--service', default='sii-special-frozen108-v8-20261029.service')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.run:
        run(args.root.resolve())
    else:
        require(args.preparation is not None, 'Preparation required')
        prepare(args.root.resolve(), args.preparation.resolve(), args.service)
