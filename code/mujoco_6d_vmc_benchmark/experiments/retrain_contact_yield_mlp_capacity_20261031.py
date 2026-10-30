"""Run and independently audit a bounded MLP-width development sweep."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / 'outputs/contact_yield_recovery_retrain_20261030_v7'
TARGET = ROOT / 'outputs/contact_yield_mlp_capacity_20261031_v1'
SEEDS = (2026102801, 2026102802, 2026102803)
WIDTHS = (128, 256, 384)
RATES = (3e-4, 1e-3)
DECAYS = (1e-5, 1e-4)
UPDATES = 32000
MAX_MEMORY = 3 * 1024**3


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def source_files():
    return (sorted((ROOT / 'scripts').glob('*.py')) + [
        ROOT / 'tools/train_contact_yield_recovery_neural_20261030.py',
        ROOT / 'tools/optimize_tool_contact_20261002.py',
    ])


def freeze_source():
    destination = TARGET / 'fitting_source'
    if destination.exists():
        manifest = read(TARGET / 'FITTING_SOURCE.json')
        for name, digest in manifest['source_sha256'].items():
            if sha(destination / name) != digest:
                raise ValueError(f'frozen source changed: {name}')
        return manifest
    destination.mkdir(parents=True)
    hashes = {}
    for source in source_files():
        relative = str(source.relative_to(ROOT))
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes[relative] = sha(source)
    manifest = dict(schema='contact-yield-mlp-capacity-source-v1', created_utc=now(),
                    base_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                         cwd=ROOT.parents[1],
                                                         text=True).strip(),
                    source_sha256=hashes)
    write(TARGET / 'FITTING_SOURCE.json', manifest)
    return manifest


def model_lock():
    return read(PARENT / 'MODEL_LOCK.json')


def verify_parent():
    state = read(PARENT / 'execution.json')
    fit_audit = read(PARENT / 'FIT_AUDIT.json')
    lock = model_lock()
    metadata = read(PARENT / 'data/DATA_COMPLETE.json')
    data = PARENT / 'data/training_data.npz'
    if state.get('status') != 'complete' or fit_audit.get('status') != 'passed':
        raise ValueError('parent fair fit and independent audit must be complete')
    if metadata.get('training_data_sha256') != sha(data):
        raise ValueError('parent dataset hash mismatch')
    if lock.get('status') != 'frozen' or len(lock.get('models', [])) != 9:
        raise ValueError('parent nine-model lock is incomplete')
    if metadata.get('episodes') != 40 or metadata.get('frames') != 21500:
        raise ValueError('unexpected parent dataset population')
    if sum(row['family'] == 'mlp_scratch' for row in lock['models']) != 3:
        raise ValueError('parent MLP seed set is incomplete')
    return dict(state_sha256=sha(PARENT / 'execution.json'),
                fit_audit_sha256=sha(PARENT / 'FIT_AUDIT.json'),
                model_lock_sha256=sha(PARENT / 'MODEL_LOCK.json'),
                dataset_sha256=sha(data), metadata_sha256=sha(PARENT / 'data/DATA_COMPLETE.json'))


def prepare():
    if TARGET.exists():
        raise FileExistsError(f'refusing to overwrite {TARGET}')
    parent_hashes = verify_parent()
    TARGET.mkdir(parents=True)
    (TARGET / 'data').mkdir()
    shutil.copy2(PARENT / 'data/training_data.npz', TARGET / 'data/training_data.npz')
    shutil.copy2(PARENT / 'data/DATA_COMPLETE.json', TARGET / 'data/DATA_COMPLETE.json')
    fits = []
    for seed in SEEDS:
        for width, rate, decay in itertools.product(WIDTHS, RATES, DECAYS):
            rate_tag = f'{rate:.0e}'.replace('-', 'm').replace('+', 'p')
            decay_tag = f'{decay:.0e}'.replace('-', 'm').replace('+', 'p')
            name = f'mlp_s{seed}_w{width}_lr{rate_tag}_wd{decay_tag}'
            fits.append(dict(name=name, seed=seed, width=width, learning_rate=rate,
                             weight_decay=decay, updates=UPDATES, status='pending'))
    registration = dict(
        schema='contact-yield-mlp-capacity-development-v1', registered_utc=now(),
        purpose='Test whether single-hidden-layer MLP capacity limits v7 teacher-action fit; this is a development diagnostic, not a new final comparison.',
        parent_run=str(PARENT), parent_hashes=parent_hashes,
        dataset_sha256=parent_hashes['dataset_sha256'], episodes=40, frames=21500,
        train_validation_identity='unchanged v7 split; six registered validation episodes; no final108 access',
        inputs='same canonical48-derived 18 proprioceptive fields, same train-only scaling, labels and weights',
        model='stateless single-hidden-layer MLP, action7; only hidden width varies',
        widths=list(WIDTHS), learning_rates=list(RATES), weight_decays=list(DECAYS),
        candidates_per_seed=12, candidates_total=len(fits), neural_updates_per_candidate=UPDATES,
        optimization='same requested-action objective, float64, absolute inputs, cosine LR, global loss, raw slowdown training path',
        selection='minimum real_identity_validation action MSE per seed; no fixed27 or final108 outcomes used',
        resources=dict(cpu_affinity=[6], threads=1, memory_max_bytes=MAX_MEMORY, swap_bytes=0,
                       simulators=0, physics_steps=0), fits=fits)
    write(TARGET / 'REGISTRATION.json', registration)
    write(TARGET / 'execution.json', dict(status='prepared', prepared_utc=now(), fits=fits,
                                          completed=0, expected=len(fits)))
    freeze_source()
    print(json.dumps(dict(status='prepared', target=str(TARGET), candidates=len(fits),
                          dataset_sha256=parent_hashes['dataset_sha256']), indent=2))


def amend_registration():
    registration_path = TARGET / 'REGISTRATION.json'
    state_path = TARGET / 'execution.json'
    if not registration_path.is_file() or not state_path.is_file():
        raise FileNotFoundError('initial registration is required')
    state = read(state_path)
    if state.get('status') != 'prepared' or state.get('completed') != 0:
        raise RuntimeError('amendment is allowed only before the first candidate')
    amendment_path = TARGET / 'REGISTRATION_AMENDMENT_1.json'
    if amendment_path.exists():
        raise FileExistsError(amendment_path)
    amendment = dict(schema='contact-yield-mlp-capacity-registration-amendment-v1',
                     created_utc=now(), registration_sha256=sha(registration_path),
                     coordinator_sha256=sha(__file__),
                     change='The container does not expose cpu.max. CPUQuota is therefore not asserted; systemd AllowedCPUs=6 and taskset -c 6 still restrict execution to one CPU. MemoryMax=3G and MemorySwapMax=0 remain mandatory and are checked by the worker.',
                     unchanged=['dataset and hash', 'candidate grid and count', 'seed identities',
                                '32k update budget', 'validation and selection rule',
                                'physical model, gates, actor inputs, filter, actuator limits and dt'],
                     failed_preflight=dict(error='FileNotFoundError reading cgroup cpu.max after memory, swap and CPU-affinity checks',
                                           candidates_started=0, physics_steps=0, optimizer_updates=0))
    write(amendment_path, amendment)
    state.setdefault('preflight_failures', []).append(amendment['failed_preflight'])
    write(state_path, state)
    print(json.dumps(dict(status='amendment_recorded', path=str(amendment_path)), indent=2))


def resource_guard():
    cgroup = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory = (cgroup / 'memory.max').read_text().strip()
    swap = (cgroup / 'memory.swap.max').read_text().strip()
    affinity = sorted(os.sched_getaffinity(0))
    if memory == 'max' or int(memory) > MAX_MEMORY or swap != '0' or affinity != [6]:
        raise RuntimeError(f'wrong resource scope: memory={memory}, swap={swap}, affinity={affinity}')
    cpu_file = cgroup / 'cpu.max'
    return dict(memory_max=memory, memory_swap_max=swap, cpu_affinity=affinity,
                cpu_max=cpu_file.read_text().strip() if cpu_file.is_file() else None,
                cpu_control='single-CPU affinity' if not cpu_file.is_file() else 'affinity and cpu.max')


def run():
    registration = read(TARGET / 'REGISTRATION.json')
    amendment = read(TARGET / 'REGISTRATION_AMENDMENT_1.json')
    if (amendment['registration_sha256'] != sha(TARGET / 'REGISTRATION.json')
            or amendment['coordinator_sha256'] != sha(__file__)):
        raise ValueError('registration amendment or coordinator hash mismatch')
    state_path = TARGET / 'execution.json'
    state = read(state_path)
    if state.get('status') not in ('prepared', 'training', 'stopped_at_candidate_boundary'):
        raise RuntimeError(f'refusing to run from status={state.get("status")}')
    try:
        resources = resource_guard()
    except Exception as exc:
        state.setdefault('preflight_failures', []).append(dict(time_utc=now(), error=repr(exc)))
        write(state_path, state)
        raise
    parent_hashes = verify_parent()
    if parent_hashes != registration['parent_hashes']:
        raise ValueError('parent inputs changed since registration')
    source = freeze_source()
    lock_path = ROOT / 'outputs/.local-rl-compute.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a') as compute_lock:
        fcntl.flock(compute_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state.update(status='training', started_utc=state.get('started_utc', now()),
                     resources=resources, python=sys.executable, source_sha256=source['source_sha256'])
        write(state_path, state)
        env = dict(os.environ, PYTHONPATH=f"{TARGET / 'fitting_source/scripts'}:{TARGET / 'fitting_source/tools'}",
                   OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
                   SII_SOURCE_BASE_COMMIT=source['base_commit'])
        trainer = TARGET / 'fitting_source/tools/train_contact_yield_recovery_neural_20261030.py'
        metadata = TARGET / 'data/DATA_COMPLETE.json'
        data = TARGET / 'data/training_data.npz'
        completed = {row['name'] for row in state['fits'] if row['status'] == 'complete'}
        for row in registration['fits']:
            if row['name'] in completed:
                record = next(item for item in state['fits'] if item['name'] == row['name'])
                if sha(Path(record['output']) / 'checkpoint.npz') != record['checkpoint_sha256']:
                    raise ValueError(f"completed checkpoint changed: {row['name']}")
                continue
            if (TARGET / 'STOP_REQUESTED').exists():
                state.update(status='stopped_at_candidate_boundary', stopped_utc=now())
                write(state_path, state)
                return
            output = TARGET / 'learning' / row['name']
            log = TARGET / 'logs' / f"{row['name']}.log"
            if output.exists() or log.exists():
                raise FileExistsError(f"incomplete candidate preserved: {row['name']}")
            command = [sys.executable, str(trainer), '--data', str(data), '--metadata', str(metadata),
                       '--kind', 'mlp', '--width', str(row['width']), '--seed', str(row['seed']),
                       '--updates', str(UPDATES), '--target', 'requested', '--absolute-inputs',
                       '--precision', 'float64', '--learning-rate', str(row['learning_rate']),
                       '--weight-decay', str(row['weight_decay']), '--action-delta-weight', '0',
                       '--lr-schedule', 'cosine', '--global-loss', '--raw-slowdown-loss', '--selection', 'final',
                       '--output', str(output)]
            row.update(status='running', started_utc=now(), output=str(output), command=command)
            state['current'] = row['name']
            state['fits'] = [dict(item) if item['name'] != row['name'] else dict(row)
                             for item in state['fits']]
            write(state_path, state)
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open('x') as stream:
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                        stderr=subprocess.STDOUT, pass_fds=(compute_lock.fileno(),))
            if result.returncode:
                row.update(status='failed_preserved', returncode=result.returncode, ended_utc=now())
                state['fits'] = [dict(item) if item['name'] != row['name'] else dict(row)
                                 for item in state['fits']]
                state.update(status='failed_preserved', error=f"candidate {row['name']} exited {result.returncode}",
                             ended_utc=now())
                write(state_path, state)
                return
            complete = output / 'TRAINING_COMPLETE.json'
            if not complete.is_file():
                raise RuntimeError(f'missing completion receipt for {row["name"]}')
            result_meta = read(complete)
            if result_meta.get('data_sha256') != registration['dataset_sha256']:
                raise ValueError(f'dataset lineage mismatch: {row["name"]}')
            row.update(status='complete', ended_utc=now(),
                       checkpoint_sha256=sha(output / 'checkpoint.npz'),
                       metadata_sha256=sha(complete), wall_seconds=result_meta.get('wall_seconds'))
            state['fits'] = [dict(item) if item['name'] != row['name'] else dict(row)
                             for item in state['fits']]
            state['completed'] = sum(item['status'] == 'complete' for item in state['fits'])
            write(state_path, state)
        state.update(status='complete', ended_utc=now())
        write(state_path, state)


def review():
    registration = read(TARGET / 'REGISTRATION.json')
    state = read(TARGET / 'execution.json')
    if state.get('status') != 'complete' or state.get('completed') != len(registration['fits']):
        raise RuntimeError('all candidates must complete before review')
    from office_mlp_rnn_20261002 import OfficeMLPRNN
    data = TARGET / 'data/training_data.npz'
    with np.load(data, allow_pickle=False) as z:
        obs, target, episodes, train = (z['observation'].copy(), z['requested_teacher_action'].copy(),
                                        z['episode'].copy(), z['train'].copy())
    train_ids = np.unique(episodes[train])
    val_ids = np.unique(episodes[~train])
    scores = {}
    rows = []
    for fit in state['fits']:
        output = Path(fit['output'])
        if sha(output / 'checkpoint.npz') != fit['checkpoint_sha256']:
            raise ValueError(f"checkpoint hash mismatch: {fit['name']}")
        actor = OfficeMLPRNN(output / 'checkpoint.npz')
        if actor.kind != 'mlp' or actor.width != registration['fits'][
                next(i for i, item in enumerate(registration['fits']) if item['name'] == fit['name'])]['width']:
            raise ValueError(f"model metadata mismatch: {fit['name']}")
        with np.load(output / 'exported_replay.npz', allow_pickle=False) as z:
            exported, exported_episodes = z['prediction'].copy(), z['episode'].copy()
        if not np.array_equal(exported_episodes, episodes):
            raise ValueError(f"replay episode mismatch: {fit['name']}")
        replay = np.empty_like(exported)
        for episode in np.unique(episodes):
            actor.reset()
            ids = np.flatnonzero(episodes == episode)
            replay[ids] = np.asarray([actor.act(obs[index]) for index in ids])
        replay_error = float(np.max(np.abs(replay - exported)))
        if replay_error > 5e-5:
            raise ValueError(f"actor replay mismatch {fit['name']}: {replay_error}")
        validation = ~train
        mse = float(np.mean((replay[validation] - target[validation]) ** 2))
        expected = read(output / 'TRAINING_COMPLETE.json')['groups']['real_identity_validation']['action_mse']
        if abs(mse - float(expected)) > 1e-12:
            raise ValueError(f"validation score mismatch {fit['name']}: {mse} vs {expected}")
        fit_metadata = read(output / 'TRAINING_COMPLETE.json')
        row = dict(name=fit['name'], seed=fit['seed'], width=fit['width'],
                   parameters=int(fit_metadata['trainable_parameters']),
                   validation_mse=mse, actor_replay_max_error=replay_error,
                   checkpoint_sha256=fit['checkpoint_sha256'], metadata_sha256=fit['metadata_sha256'])
        rows.append(row)
        scores.setdefault(fit['seed'], []).append(row)
    selected = []
    for seed, candidates in sorted(scores.items()):
        best = min(candidates, key=lambda item: (item['validation_mse'], item['name']))
        selected.append(dict(family='mlp_scratch', seed=seed, width=best['width'],
                             selected_trial=best['name'], validation_mse=best['validation_mse'],
                             checkpoint=str(TARGET / 'learning' / best['name'] / 'checkpoint.npz'),
                             checkpoint_sha256=best['checkpoint_sha256']))
    audit = dict(schema='contact-yield-mlp-capacity-fit-audit-v1', status='passed',
                 registration_sha256=sha(TARGET / 'REGISTRATION.json'),
                 execution_sha256=sha(TARGET / 'execution.json'),
                 dataset_sha256=sha(data), candidates=len(rows), selected=selected, rows=rows,
                 fixed27_accessed=False, final108_accessed=False, physics_steps=0,
                 optimizer_updates=sum(UPDATES for _ in rows))
    write(TARGET / 'FIT_AUDIT.json', audit)
    write(TARGET / 'MODEL_LOCK.json', dict(schema='contact-yield-mlp-capacity-model-lock-v1',
                                            status='frozen', created_utc=now(),
                                            selection='minimum independently recomputed requested-action MSE on the same six v7 development validation identities',
                                            data_sha256=sha(data), candidates_per_seed=len(WIDTHS)*len(RATES)*len(DECAYS),
                                            models=selected))
    print(json.dumps(dict(status='passed', target=str(TARGET), selected=selected), indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'amend', 'run', 'review'))
    args = parser.parse_args()
    if args.mode == 'prepare':
        prepare()
    elif args.mode == 'amend':
        amend_registration()
    elif args.mode == 'run':
        run()
    else:
        review()


if __name__ == '__main__':
    main()
