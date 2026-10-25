"""Same-host, same-user GPU leases for SPT jobs; no SSH or environment installation.

Four independent learners, at most one per GPU. Physics stays single-threaded
per learner. All checkouts on this host must use the same resource directory.
"""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess

GIB = 1024**3


def gpu_info(device):
    rows = subprocess.check_output([
        'nvidia-smi', '-i', str(device),
        '--query-gpu=uuid,name,memory.free,temperature.gpu',
        '--format=csv,noheader,nounits'], text=True, timeout=15).strip().splitlines()
    if len(rows) != 1:
        raise ValueError('Register exactly one GPU per job')
    uuid, name, free, temperature = [x.strip() for x in rows[0].split(',')]
    if not re.fullmatch(r'GPU-[a-fA-F0-9-]+', uuid):
        raise ValueError('A full GPU UUID is required; MIG is not supported')
    return dict(uuid=uuid, name=name, free_mib=int(free), temperature_c=int(temperature))


def parse_cpus(value):
    cpus = [int(x) for x in value.split(',')]
    if not cpus or min(cpus) < 0 or len(set(cpus)) != len(cpus):
        raise ValueError('Use distinct, nonnegative CPU IDs separated by commas')
    return sorted(cpus)


def register(device, cpus, memory_gib):
    ids = parse_cpus(cpus)
    if not set(ids) <= os.sched_getaffinity(0):
        raise ValueError('Registered CPU IDs are not available on this host')
    if not 4 <= memory_gib <= 32:
        raise ValueError('Server per-job RAM limit must be 4..32 GiB')
    info = gpu_info(device)
    return dict(server_compute=True, learning_backend='cuda', gpu_uuid=info['uuid'],
                gpu_registration=info, cpus=ids, threads=1, simulators=1, utd=1,
                memory_max_bytes=memory_gib*GIB, swap_max_bytes=0,
                max_parallel_jobs=4, gpu_pool_fraction='0.8',
                gpu_min_free_mib=8192, gpu_max_temperature_c=80,
                # Fixed per-user host namespace: two checkouts cannot evade leases.
                lease_directory=f'/tmp/sii-spt-gpu-leases-{os.getuid()}')


def environment(resources):
    if not resources.get('server_compute'):
        return dict(JAX_PLATFORMS='cpu', XLA_PYTHON_CLIENT_PREALLOCATE='false')
    return dict(JAX_PLATFORMS='cuda', CUDA_VISIBLE_DEVICES=resources['gpu_uuid'],
                XLA_PYTHON_CLIENT_PREALLOCATE='false',
                XLA_PYTHON_CLIENT_MEM_FRACTION=resources['gpu_pool_fraction'])


def runtime_info(resources):
    for key, value in environment(resources).items():
        if os.environ.get(key) != value:
            raise ValueError('Registered backend environment differs: '+key)
    expected_cpus = resources.get('cpus', [resources.get('cpu')])
    if set(os.sched_getaffinity(0)) != set(expected_cpus):
        raise ValueError('CPU affinity differs from registration')
    import jax
    devices = jax.devices()
    expected = 'gpu' if resources.get('server_compute') else 'cpu'
    if len(devices) != 1 or devices[0].platform != expected:
        raise ValueError('Actual JAX backend differs; never silently fall back to CPU')
    return dict(learning_backend='cuda' if expected == 'gpu' else 'cpu',
                devices=[str(d) for d in devices], device_kinds=[d.device_kind for d in devices],
                cpu_affinity=sorted(os.sched_getaffinity(0)), jax_version=jax.__version__,
                simulator_backend='cpu', gpu_uuid=resources.get('gpu_uuid'))


def boundary(resources):
    info = gpu_info(resources['gpu_uuid'])
    # During training memory is already allocated; do not reuse the startup free-RAM test.
    return info, 'gpu_temperature' if info['temperature_c'] >= resources['gpu_max_temperature_c'] else None


def process_identity(pid):
    try:
        # comm can contain spaces and parentheses; field 22 follows the last ')'.
        tail = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return tail[19]
    except (OSError, IndexError):
        return None


def memory_requirement(new_cap, active):
    return new_cap + sum(max(0, cap-current) for cap, current in active) + 4*GIB


@contextmanager
def lease(resources, root, family):
    """Serialize admission, reserve outstanding RAM, hold GPU/CPU/slot locks.

    Caller inherits returned FDs into the trainer, so crashes do not free a
    live child's device lease. A live cgroup also keeps its RAM reservation.
    """
    directory = Path(resources['lease_directory'])
    directory.mkdir(mode=0o700, exist_ok=True)
    if directory.is_symlink() or directory.stat().st_uid != os.getuid():
        raise ValueError('Unsafe GPU lease directory')
    held = []; record = None

    def acquire(name):
        stream = (directory/name).open('a')
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            stream.close(); raise
        held.append(stream)

    try:
        with (directory/'admission.lock').open('a') as gate:
            fcntl.flock(gate, fcntl.LOCK_EX)
            acquire(resources['gpu_uuid']+'.lock')
            for cpu in resources['cpus']:
                acquire(f'cpu-{cpu}.lock')
            for slot in range(resources['max_parallel_jobs']):
                try:
                    acquire(f'slot-{slot}.lock'); break
                except BlockingIOError:
                    continue
            else:
                raise ValueError('All four GPU job slots are occupied')
            info = gpu_info(resources['gpu_uuid'])
            if info['free_mib'] < resources['gpu_min_free_mib'] or info['temperature_c'] >= resources['gpu_max_temperature_c']:
                raise ValueError('GPU memory/temperature admission failed')
            busy = subprocess.check_output(['nvidia-smi', '-i', resources['gpu_uuid'],
                '--query-compute-apps=pid', '--format=csv,noheader,nounits'], text=True, timeout=15).strip()
            if busy:
                raise ValueError('Selected GPU already has compute processes; do not duplicate/evict them')
            active = []
            for path in directory.glob('*.reservation.json'):
                old = json.loads(path.read_text())
                current_path = Path(old['cgroup'])/'memory.current'
                events_path = Path(old['cgroup'])/'cgroup.events'
                populated = events_path.exists() and 'populated 1' in events_path.read_text()
                alive = process_identity(old['pid']) == old['process_start']
                if alive or populated:
                    current = int(current_path.read_text()) if current_path.exists() else 0
                    active.append((old['memory_max_bytes'], current))
            available = next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()
                             if x.startswith('MemAvailable:'))
            if available < memory_requirement(resources['memory_max_bytes'], active):
                raise ValueError('Insufficient host RAM including other jobs outstanding reservations')
            cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
            record = directory/f'{os.getpid()}-{process_identity(os.getpid())}.reservation.json'
            record.write_text(json.dumps(dict(pid=os.getpid(), process_start=process_identity(os.getpid()),
                cgroup=str(cg), root=str(root), family=family,
                memory_max_bytes=resources['memory_max_bytes'])))
        yield held
    finally:
        # Keep reservation receipts. Dead PID + empty/disappeared cgroup makes them inactive.
        for stream in held:
            stream.close()
