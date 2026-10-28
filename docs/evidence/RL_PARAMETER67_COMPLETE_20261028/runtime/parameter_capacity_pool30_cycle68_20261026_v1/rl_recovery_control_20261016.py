"""Fail-closed local recovery dispatch; no acceptance or process termination."""
from datetime import datetime, timezone
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess

GIB = 1024 ** 3
MEMORY_MAX = 3 * GIB
RESERVE = 768 * 1024 ** 2
BENCH = Path(__file__).resolve().parents[1]
PYTHON = BENCH.parents[2] / '.venv-sii-local-rl/bin/python'
TRAINER = BENCH / 'tools/train_v4_recovery_rl_20261016.py'
WORKER_NAMES = {
    'train_baseline_repair_rl_20261008.py', 'train_v4_recovery_rl_20261016.py',
    'baseline_repair_worker_20261008.py', 'research72_online_worker_20261003.py',
}


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_new(path, data):
    with Path(path).open('x') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')


def dispatch_reason(deadline, now, available, workers):
    if now >= deadline:
        return 'dispatch_deadline_elapsed'
    if workers:
        return 'existing_rl_worker'
    if available < MEMORY_MAX + RESERVE:
        return 'insufficient_memory_with_reserve'
    return None


def active_workers(proc=Path('/proc')):
    found = []
    for p in proc.iterdir():
        if not p.name.isdigit():
            continue
        try:
            if (p/'comm').read_text().strip() not in ('python', 'python3'):
                continue
            args = (p/'cmdline').read_bytes().decode().split('\0')
            if WORKER_NAMES.intersection(Path(a).name for a in args):
                found.append(int(p.name))
        except (FileNotFoundError, ProcessLookupError):
            continue
        # Permission failures must not be interpreted as an empty process table.
    return found


def verify_checkpoint(cp):
    old = read(cp.parent/'execution.json')
    row = next(r for r in old['checkpoint_rows'] if Path(r['path']) == cp)
    runner = read(cp/'office_runner.json')
    if not runner['episode_boundary'] or runner.get('pending_transition') is not None:
        raise ValueError('checkpoint is not a complete episode boundary')
    if not all(digest(cp/k) == v for k, v in row['hashes'].items()):
        raise ValueError('checkpoint hash mismatch')
    if runner['step'] != row['step']:
        raise ValueError('checkpoint step mismatch')
    return row


def systemd_command(reg):
    root = Path(reg['parent_root'])
    runtime = BENCH/'outputs/baseline_local_rl_20261009/runtime'
    env = dict(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               NUMEXPR_NUM_THREADS='1', JAX_PLATFORMS='cpu', SII_RL_UTD='1',
               XLA_PYTHON_CLIENT_PREALLOCATE='false', SII_REWARD_PAYLOAD_TELEMETRY='1',
               SII_LOCAL_RUNTIME=str(runtime), MUJOCO_MENAGERIE_PATH=str(runtime/'menagerie'))
    command = ['systemd-run', '--user', '--unit='+reg['unit'],
               '--property=MemoryMax=3G', '--property=MemorySwapMax=0',
               '--property=CPUQuota=100%', '--property=CPUAffinity=1',
               '--property=TasksMax=256', '--working-directory='+str(BENCH)]
    command += ['--setenv='+k+'='+v for k, v in env.items()]
    command += [str(PYTHON), str(TRAINER), '--root', str(root),
                '--output', reg['output'], '--parameter-source', str(root/'parameter_fullrange'),
                '--seed', str(reg['seed']), '--steps', str(reg['maximum_steps']),
                '--reward', 'office_task', '--reward-variant', 'task_safety',
                '--hyperparameter-id', 'direct_explore', '--resume-checkpoint', reg['checkpoint']]
    return command


def prepare(root, destination):
    if not PYTHON.is_file():
        raise FileNotFoundError('Registered local interpreter is missing: '+str(PYTHON))
    protocol = read(root/'PROTOCOL.json')
    old = read(root/'direct_task_safety/execution.json')
    cp = Path(old['checkpoint_rows'][-1]['path'])
    checked = verify_checkpoint(cp)
    registration = dict(schema='sii-v4-recovery-20261016', parent_root=str(root),
        parent_protocol_sha256=digest(root/'PROTOCOL.json'), checkpoint=str(cp),
        inherited_steps=checked['step'], inherited_actual_utd=2, resumed_utd=1,
        checkpoint_hashes=checked['hashes'], trainer_sha256=digest(TRAINER),
        output=str(destination/'direct_task_safety'),
        seed=protocol['budgets']['training_seeds'][0],
        maximum_steps=protocol['budgets']['rl_steps_per_family_seed'],
        dispatch_deadline_utc=protocol['training_dispatch_deadline_utc'],
        unit='sii-rl-v4-recovery-'+destination.name.replace('_','-'),
        memory_max=MEMORY_MAX, memory_swap_max=0, numerical_threads=1,
        memory_reserve=RESERVE, simultaneous_simulators=1, server_compute=False,
        acceptance_allowed=False,
        stop_procedure='Create parent_root/STOP_REQUESTED; wait for trainer checkpoint/exit. Never terminate a launch-container parent while its simulator is alive.',
        status='prepared_not_launched')
    destination.mkdir(parents=True, exist_ok=False)
    write_new(destination/'REGISTRATION.json', registration)
    write_new(destination/'COMMAND.json', systemd_command(registration))
    return registration


def launch(destination):
    reg = read(destination/'REGISTRATION.json')
    # Host /proc and user systemd bus must be available; run outside app sandbox.
    if len(list(Path('/proc').glob('[0-9]*'))) < 20:
        raise RuntimeError('Host process visibility required for duplicate check')
    with (BENCH/'outputs/.v4_recovery_dispatch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        available = next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()
                         if x.startswith('MemAvailable:'))
        workers = active_workers()
        reason = dispatch_reason(datetime.fromisoformat(reg['dispatch_deadline_utc']),
                                 datetime.now(timezone.utc), available, workers)
        if reason:
            raise RuntimeError(f'{reason}; available={available}; workers={workers}')
        root = Path(reg['parent_root'])
        if digest(root/'PROTOCOL.json') != reg['parent_protocol_sha256'] or digest(TRAINER) != reg['trainer_sha256']:
            raise ValueError('registered source/config changed')
        verify_checkpoint(Path(reg['checkpoint']))
        if Path(reg['output']).exists() or (destination/'LAUNCH.json').exists():
            raise FileExistsError('Never reuse a recovery attempt')
        command = systemd_command(reg)
        if command != read(destination/'COMMAND.json'):
            raise ValueError('registered command changed')
        # A failed dispatch also consumes this unique attempt; never retry blindly.
        write_new(destination/'LAUNCH.json', dict(command=command, available_bytes=available,
            attempted_utc=datetime.now(timezone.utc).isoformat(), status='dispatch_attempt'))
        subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'launch'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'prepare':
        print(json.dumps(prepare(args.root.resolve(), args.destination.resolve()), indent=2))
    else:
        launch(args.destination.resolve())


if __name__ == '__main__':
    main()
