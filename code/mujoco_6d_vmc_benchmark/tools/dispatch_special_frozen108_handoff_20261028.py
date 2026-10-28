"""Bounded original-fit handoff to the already frozen108 dispatcher and audits.

Does not start, stop, resume or modify training. No retries or replacement
experiments: failures are retained for review. Goal completion is never set.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def require(value, reason):
    if not value:
        raise ValueError(reason)


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def identity(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
    except FileNotFoundError:
        return None


def service(name):
    output = subprocess.check_output(['systemctl', '--user', 'show', name,
        '-p', 'ActiveState', '-p', 'Result', '-p', 'MainPID'], text=True)
    return dict(line.split('=', 1) for line in output.splitlines())


def parent_ready(plan, current, ticks, handoff, fitted):
    if current['ActiveState'] in ('active', 'deactivating'):
        if current['ActiveState'] == 'active':
            require(int(current['MainPID']) == plan['parent_pid']
                    and ticks == plan['parent_start_ticks'], 'Original fitting process changed')
        else:
            require(int(current['MainPID']) in (0, plan['parent_pid'])
                    and ticks in (None, plan['parent_start_ticks']), 'Parent exit identity changed')
        require(handoff['status'] != 'failed_preserved' and fitted['status'] != 'failed_preserved',
                'Parent recorded a failure')
        return False
    require(ticks != plan['parent_start_ticks'], 'Parent still present outside service')
    require(current['ActiveState'] == 'inactive' and current['Result'] == 'success', 'Parent service did not end cleanly')
    require(handoff['status'] == 'fitting_complete_pending_test_review'
            and fitted['status'] == 'complete', 'Original fitting incomplete')
    require(len(fitted['fits']) == 75 and all(r['status'] == 'complete' for r in fitted['fits']),
            'Complete75 fits required')
    return True


def prepare(root, preparation):
    require(not root.exists(), 'Use a new handoff directory')
    p = read(preparation / 'REGISTRATION.json')
    for name, digest in p['tools_sha256'].items():
        require(sha(preparation/'tools'/name) == digest, 'Frozen dispatcher sources changed')
    for name, digest in p['input_hashes'].items():
        require(sha(Path(name)) == digest, 'Frozen dispatcher inputs changed')
    require(not (preparation / 'execution.json').exists() and not Path(p['evaluation']).exists(),
            'Frozen108 already dispatched; inspect instead')
    current = service(p['handoff_service'])
    pid = int(current['MainPID'])
    ticks = identity(pid)
    require(current['ActiveState'] == 'active' and ticks is not None, 'Bind actual live fitting parent')
    require(read(Path(p['handoff']) / 'execution.json')['status'] == 'fitting_students', 'Wrong handoff stage')
    require(read(Path(p['training']) / 'execution.json')['status'] == 'training', 'Original fitting not running')
    root.mkdir(parents=True)
    snapshot = root / 'tools'
    snapshot.mkdir()
    for name in ('dispatch_special_frozen108_handoff_20261028.py', 'prepare_special_frozen_test_20261028.py',
                 'audit_special_frozen108_20261028.py', 'report_special_frozen108_20261028.py',
                 'plot_nonrl_new30_learning_20261026.py'):
        shutil.copy2(ROOT / 'tools' / name, snapshot / name)
    plan = dict(schema='sii-special-frozen108-handoff-v1', registered_utc=now(),
        source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_note='Exact precommit source bytes pinned by snapshot hashes; base commit alone is not a source identity',
        preparation=str(preparation), preparation_sha256=sha(preparation/'REGISTRATION.json'),
        parent_service=p['handoff_service'], parent_pid=pid, parent_start_ticks=ticks,
        parent_handoff=p['handoff'], training=p['training'], evaluation=p['evaluation'],
        python=p['python'], working_directory=str(ROOT), wait_seconds=7200,
        snapshot_sha256={f.name: sha(f) for f in snapshot.glob('*.py')},
        resources=dict(simulators=1, threads=1, memory_max_bytes=3221225472, swap_bytes=0),
        scope='Wait only for this parent, invoke original frozen108 fit-audit/test dispatcher once, '
              'then saved-evidence audit and actual final plots. No training/retry/new conditions.',
        completion='Artifacts ready for visual inspection and archive; not automatic goal completion')
    write(root/'REGISTRATION.json', plan)
    print(json.dumps(dict(root=str(root), parent_pid=pid, start_ticks=ticks,
                         registration_sha256=sha(root/'REGISTRATION.json'))))


def run(root):
    lock = (root/'.handoff.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    require(not (root/'execution.json').exists(), 'Do not duplicate/restart this handoff')
    plan = read(root/'REGISTRATION.json')
    require(plan['schema'] == 'sii-special-frozen108-handoff-v1', 'Wrong plan')
    cg = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    limit = (cg/'memory.max').read_text().strip()
    require(limit != 'max' and int(limit) <= 3221225472 and (cg/'memory.swap.max').read_text().strip() == '0', 'Real <=3GiB/swap0 required')
    require(all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')), 'Single numerical thread required')
    preparation = Path(plan['preparation'])
    state = dict(status='waiting_for_original_fitting', started_utc=now(),
                 registration_sha256=sha(root/'REGISTRATION.json'))
    write(root/'execution.json', state)

    def verify():
        require(sha(root/'REGISTRATION.json') == state['registration_sha256'], 'Handoff plan changed')
        require(sha(preparation/'REGISTRATION.json') == plan['preparation_sha256'], 'Frozen preparation changed')
        require(sha(Path(__file__)) == plan['snapshot_sha256'][Path(__file__).name], 'Handoff source changed')
        for name, h in plan['snapshot_sha256'].items():
            require(sha(root/'tools'/name) == h, 'Postprocessing snapshot changed')

    def child(stage, command):
        verify()
        state.update(status=stage, updated_utc=now(), command=command)
        write(root/'execution.json', state)
        with (root/(stage+'.log')).open('x') as output:
            subprocess.run(command, cwd=plan['working_directory'], stdout=output,
                           stderr=subprocess.STDOUT, check=True)

    try:
        verify()
        deadline = time.monotonic()+plan['wait_seconds']
        while True:
            current = service(plan['parent_service'])
            handoff = read(Path(plan['parent_handoff'])/'execution.json')
            fitted = read(Path(plan['training'])/'execution.json')
            ready = parent_ready(plan, current, identity(plan['parent_pid']), handoff, fitted)
            state.update(last_checked_utc=now(), parent_service=current,
                         completed_fits=sum(r['status']=='complete' for r in fitted['fits']),
                         current_fit=fitted.get('current'))
            write(root/'execution.json', state)
            if ready:
                break
            require(time.monotonic() < deadline, 'Bounded wait expired; original training untouched')
            time.sleep(10)
        require(sha(Path(plan['training'])/'MODEL_LOCK.json') == handoff['model_lock_sha256'], 'Parent model lock mismatch')
        child('frozen_fit_audit_and_108', [plan['python'], str(preparation/'tools/prepare_special_frozen_test_20261028.py'),
                                        '--root', str(preparation), '--run'])
        child('independent_saved_evidence_audit', [plan['python'], str(root/'tools/audit_special_frozen108_20261028.py'),
              '--preparation', str(preparation), '--output', str(root/'FINAL_AUDIT.json')])
        child('selected_learning_curves', [plan['python'], str(root/'tools/plot_nonrl_new30_learning_20261026.py'),
              '--root', plan['training'], '--output', str(root/'LEARNING_CURVES')])
        child('six_metric_presentation', [plan['python'], str(root/'tools/report_special_frozen108_20261028.py'),
              '--audit', str(root/'FINAL_AUDIT.json'), '--output', str(root/'PRESENTATION')])
        state.update(status='complete_pending_visual_review_and_archive', ended_utc=now(),
                     final_audit_sha256=sha(root/'FINAL_AUDIT.json'))
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc), ended_utc=now())
        raise
    finally:
        write(root/'execution.json', state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--preparation', type=Path)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.run:
        run(args.root.resolve())
    else:
        require(args.preparation is not None, 'Need existing frozen preparation')
        prepare(args.root.resolve(), args.preparation.resolve())
