"""Bounded handoff from the existing collection to audited student fitting.

Never starts/restarts collection or changes a failed demonstration. A single
guarded process waits for the registered live collector to end, checks all30,
builds the dataset, and runs the finite existing training grid. Test evaluation
requires subsequent model/export review and is not launched here.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from collect_special_scene_actions_20261028 import read, sha, validate, write

ROOT = Path(__file__).resolve().parents[1]
SERVICE = 'sii-special-collection-v4-20261028.service'


def now():
    return datetime.now(timezone.utc).isoformat()


def identity(pid):
    stat = Path(f'/proc/{pid}/stat')
    return stat.read_text().rsplit(')', 1)[1].split()[19] if stat.exists() else None


def service(name=SERVICE):
    text = subprocess.check_output(['systemctl', '--user', 'show', name,
                                    '-p', 'ActiveState', '-p', 'MainPID', '-p', 'Result'], text=True)
    return dict(line.split('=', 1) for line in text.strip().splitlines())


def prepare(root, collection, training, service_name=SERVICE):
    if root.exists() or training.exists():
        raise FileExistsError('Dispatch and training destinations must be new')
    validate(collection / 'COLLECTION_PLAN.json')
    current = service(service_name)
    pid = int(current['MainPID'])
    tick = identity(pid)
    if current['ActiveState'] != 'active' or not tick:
        raise ValueError('Register against the actual live original collector')
    sources = list((ROOT / 'scripts').glob('*.py')) + [ROOT / 'tools' / name for name in (
        'dispatch_special_scene_learning_20261028.py', 'collect_special_scene_actions_20261028.py',
        'build_special_scene_dataset_v2_20261028.py', 'review_special_collection_probe_20261028.py',
        'train_special_scene_models_20261028.py', 'train_paper_context_esn_20261003.py',
        'train_office_mlp_rnn_20261002.py', 'optimize_tool_contact_20261002.py')]
    plan = dict(schema='sii-special-collection-learning-handoff-v1', registered_utc=now(),
                collection=str(collection), training=str(training), service=service_name,
                collector_pid=pid, collector_start_ticks=tick,
                collection_plan_sha256=sha(collection / 'COLLECTION_PLAN.json'),
                source_hashes={str(p.relative_to(ROOT)): sha(p) for p in sources},
                wait_seconds=7200, source_base_commit=subprocess.check_output(
                    ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                limits=dict(simulators=1, threads=1, memory_max_bytes=3*1024**3, swap_bytes=0),
                budget=dict(identities=30, seeds=3, candidates_per_family_seed=12,
                            neural_updates_per_candidate=32000, expected_trainer_jobs=75),
                failure_rule='Preserve receipts and stop this handoff on any nonqualified case, source drift, changed process, timeout or subprocess error; never stop/restart collector',
                completion='Finite fitting only; no automatic frozen-test evaluation or goal completion')
    root.mkdir(parents=True)
    write(root / 'REGISTRATION.json', plan)
    print(json.dumps(dict(registration=str(root / 'REGISTRATION.json'), collector_pid=pid,
                          collector_start_ticks=tick, sha256=sha(root / 'REGISTRATION.json'))))


def run(root):
    plan = read(root / 'REGISTRATION.json')
    cg = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    limit = (cg / 'memory.max').read_text().strip()
    if limit == 'max' or int(limit) > 3*1024**3 or (cg / 'memory.swap.max').read_text().strip() != '0':
        raise RuntimeError('Real cgroup <=3GiB and zero swap required')
    if any(os.environ.get(k) != '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')):
        raise RuntimeError('Single numerical thread required')
    lock = (root / '.dispatch.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state_path = root / 'execution.json'
    if state_path.exists():
        raise FileExistsError('Existing dispatch must be inspected, never blindly restarted')
    state = dict(status='waiting_for_original_collection', started_utc=now(),
                 registration_sha256=sha(root / 'REGISTRATION.json'), collector_pid=plan['collector_pid'])
    write(state_path, state)
    collection = Path(plan['collection'])
    training = Path(plan['training'])

    def check_inputs():
        if sha(collection / 'COLLECTION_PLAN.json') != plan['collection_plan_sha256']:
            raise ValueError('Collection plan changed')
        for name, digest in plan['source_hashes'].items():
            if sha(ROOT / name) != digest:
                raise ValueError(f'Dispatch source changed: {name}')

    def child(name, arguments):
        state.update(status=name, updated_utc=now())
        write(state_path, state)
        with (root / (name + '.log')).open('x') as log:
            rc = subprocess.run([sys.executable, *arguments], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode
        if rc:
            raise RuntimeError(f'{name} exited {rc}; original log preserved')

    try:
        check_inputs()
        deadline = time.monotonic() + plan['wait_seconds']
        while True:
            current = service(plan['service'])
            progress = read(collection / 'COLLECTION_PROGRESS.json')
            state.update(last_checked_utc=now(), completed_collection=len(progress['episodes']),
                         current_collection=progress.get('current'))
            write(state_path, state)
            if current['ActiveState'] == 'active':
                if (int(current['MainPID']) != plan['collector_pid']
                        or identity(plan['collector_pid']) != plan['collector_start_ticks']):
                    raise ValueError('Original collector identity changed')
            else:
                if identity(plan['collector_pid']) == plan['collector_start_ticks']:
                    raise RuntimeError('Collector still present outside its registered service')
                if current['ActiveState'] != 'inactive' or current['Result'] != 'success':
                    raise RuntimeError(f'Original service did not end cleanly: {current}')
                if progress['status'] != 'qualified_complete' or len(progress['episodes']) != 30:
                    raise ValueError('Original30 incomplete or contains nonqualified demonstrations')
                break
            if time.monotonic() >= deadline:
                raise TimeoutError('Bounded handoff wait expired; collector was not stopped')
            time.sleep(5)
        check_inputs()
        if training.exists():
            raise FileExistsError('Training root appeared during wait')
        child('reviewing_all30', [str(ROOT / 'tools/review_special_collection_probe_20261028.py'),
              '--collection', str(collection), '--output', str(root / 'COLLECTION_REVIEW.json')])
        if not read(root / 'COLLECTION_REVIEW.json')['all30_qualified']:
            raise ValueError('Full review did not qualify')
        child('building_dataset', [str(ROOT / 'tools/build_special_scene_dataset_v2_20261028.py'),
              '--plan', str(collection / 'COLLECTION_PLAN.json'), '--output', str(training)])
        check_inputs()
        child('fitting_students', [str(ROOT / 'tools/train_special_scene_models_20261028.py'),
              '--root', str(training), '--run'])
        fitted = read(training / 'execution.json')
        if fitted['status'] != 'complete' or len(read(training / 'MODEL_LOCK.json')['models']) != 9:
            raise ValueError('Fitting did not produce all nine frozen models')
        state.update(status='fitting_complete_pending_test_review', ended_utc=now(),
                     model_lock_sha256=sha(training / 'MODEL_LOCK.json'))
        write(state_path, state)
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc), ended_utc=now())
        write(state_path, state)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--collection', type=Path)
    parser.add_argument('--training', type=Path)
    parser.add_argument('--service', default=SERVICE)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.run:
        run(args.root.resolve())
    else:
        if args.collection is None or args.training is None:
            parser.error('Preparation requires --collection and --training')
        prepare(args.root.resolve(), args.collection.resolve(), args.training.resolve(), args.service)
