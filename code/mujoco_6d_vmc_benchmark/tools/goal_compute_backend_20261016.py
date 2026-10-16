"""Explicit local learning backend; physics workers remain CPU-only."""
import os
import subprocess


GPU_RESOURCES = dict(learning_backend='cuda', gpu_device=0,
                     gpu_admission_free_mib=4096, gpu_max_temperature_c=80,
                     gpu_allocator_fraction='0.125')


def backend(reg):
    resources = (reg or {}).get('resources', {})
    name = resources.get('learning_backend', 'cpu')
    if name not in ('cpu', 'cuda'):
        raise ValueError('Unsupported learning backend')
    if name == 'cuda':
        if any(resources.get(k) != v for k, v in GPU_RESOURCES.items()):
            raise ValueError('GPU resource envelope must be explicitly registered')
    return name


def environment(reg):
    result = dict(JAX_PLATFORMS=backend(reg), XLA_PYTHON_CLIENT_PREALLOCATE='false')
    if backend(reg) == 'cuda':
        result.update(CUDA_VISIBLE_DEVICES='0', XLA_PYTHON_CLIENT_MEM_FRACTION='0.125')
    return result


def check_environment(reg, *, expected_cpu, environ=None, affinity=None):
    environ = os.environ if environ is None else environ
    affinity = os.sched_getaffinity(0) if affinity is None else affinity
    for k, v in environment(reg).items():
        if environ.get(k) != v:
            raise ValueError(f'Learning backend environment mismatch: {k}')
    if set(affinity) != {int(expected_cpu)}:
        raise ValueError('Actual CPU affinity differs from registered single core')


def gpu_snapshot():
    result = subprocess.run(['nvidia-smi', '--query-gpu=index,uuid,memory.free,temperature.gpu',
                             '--format=csv,noheader,nounits'], check=True, capture_output=True,
                            text=True, timeout=15)
    rows = [r.split(',') for r in result.stdout.strip().splitlines()]
    if len(rows) != 1 or len(rows[0]) != 4:
        raise ValueError('This resource registration supports exactly one local GPU')
    index, uuid, free, temperature = [x.strip() for x in rows[0]]
    return dict(index=int(index), uuid=uuid, free_mib=int(free), temperature_c=int(temperature))


def gpu_admission_reason(reg, snapshot):
    if backend(reg) != 'cuda':
        return None
    resources = reg['resources']
    if snapshot['index'] != resources['gpu_device']:
        return 'gpu_device_mismatch'
    if snapshot['free_mib'] < resources['gpu_admission_free_mib']:
        return 'gpu_memory_reserve'
    if snapshot['temperature_c'] >= resources['gpu_max_temperature_c']:
        return 'gpu_temperature'
    return None


def runtime_info(reg, *, expected_cpu):
    check_environment(reg, expected_cpu=expected_cpu)
    import jax
    devices = jax.devices()
    expected = 'gpu' if backend(reg) == 'cuda' else 'cpu'
    if not devices or any(d.platform != expected for d in devices):
        raise ValueError('JAX selected a different actual backend')
    return dict(learning_backend=backend(reg), cpu_affinity=sorted(os.sched_getaffinity(0)),
                platforms=[d.platform for d in devices], devices=[str(d) for d in devices],
                device_kinds=[d.device_kind for d in devices], jax_version=jax.__version__,
                simulator_backend='cpu', gpu_allocator_scope='JAX pool fraction; not a hard total GPU memory cap')


def check_backend_resume(parent, reg, job):
    previous = parent.get('learning_backend', 'cpu')
    if previous != backend(reg) and not (job and job.get('backend_migration') and
                                         previous == 'cpu' and backend(reg) == 'cuda'):
        raise ValueError('Backend change requires explicit CPU-to-CUDA migration registration')
