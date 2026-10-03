"""Bounded GPU timing on engineering-only checkpoints; no physics or candidates.

The original checkpoints stay byte-identical. Probe weights are discarded;
timing updates are separately counted, never credited as office training.
"""
import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('probe-root', 'parameter-source', 'output'):
        p.add_argument('--'+key, type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    cgroup = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory = int((cgroup/'memory.max').read_text()); assert memory <= 3*1024**3
    assert all(os.environ[k] == '1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    receipt = json.loads((a.probe_root/'execution.json').read_text())
    assert receipt['status'] == 'complete' and receipt['physics_steps'] == 0 and receipt['engineering_only']
    state = dict(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(Path(__file__)), probe_receipt_sha256=sha(a.probe_root/'execution.json'),
        python=sys.executable, host=platform.node(), argv=sys.argv, memory_max=memory,
        environment={k: os.environ.get(k) for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
            'JAX_PLATFORMS', 'XLA_PYTHON_CLIENT_PREALLOCATE', 'XLA_PYTHON_CLIENT_MEM_FRACTION')},
        engineering_only=True, physics_steps=0, candidate_checkpoints_produced=0, rows=[])
    write(out/'execution.json', state)
    try:
        sys.path.insert(0, str(a.parameter_source.resolve()))
        from official_parameter_agent import OfficialParameterAgent, BATCH_SIZE, UPSTREAM_COMMIT
        import jax
        state.update(jax=jax.__version__, numpy=np.__version__, devices=[str(d) for d in jax.devices()],
            upstream_commit=UPSTREAM_COMMIT, adapter_sha256=sha(a.parameter_source/'official_parameter_agent.py'))
        assert all(d.platform == 'gpu' for d in jax.devices()), 'Profile the registered GPU learner, not a CPU fallback'
        def sync(agent):
            raw = agent.raw_agent
            jax.block_until_ready((raw._actor, raw._critic, raw._target_critic, raw._temperature, raw._rng))
        for dimension in (5, 7):
            cp = a.probe_root/f'dimension_{dimension}'
            reference = next(r['hashes'] for r in receipt['rows'] if r['action_dimension'] == dimension)
            for name, digest in reference.items():
                assert sha(cp/name) == digest
            start = time.perf_counter()
            agent = OfficialParameterAgent(seed=2026100301, total_steps=80000, utd=2,
                gamma=.9995, entropy_coef=-2., initial_temperature=.0001, action_dimension=dimension)
            sync(agent); construction_s = time.perf_counter()-start
            start = time.perf_counter(); agent.load(cp); sync(agent); load_s = time.perf_counter()-start
            with np.load(cp/'office_replay.npz') as z:
                batch = {k: z[k][:BATCH_SIZE].copy() for k in z.files}
            assert batch['observation'].shape == (BATCH_SIZE, 48)
            inherited = agent.updates; rows = []
            for index in range(41):
                start = time.perf_counter()
                agent.sample_action(batch['observation'][index%BATCH_SIZE],
                    previous_transition=dict(reward=-.01, terminated=False, truncated=False), training=True)
                sampled = time.perf_counter()
                agent.update(batch); agent.update(batch); sync(agent)
                ended = time.perf_counter()
                rows.append(dict(cycle=index, phase='cold' if index == 0 else 'warmup' if index <= 8 else 'timed',
                    action_s=sampled-start, two_updates_s=ended-sampled, action_and_two_updates_s=ended-start))
            assert agent.updates-inherited == 82
            for name, digest in reference.items():
                assert sha(cp/name) == digest
            timed = [r for r in rows if r['phase'] == 'timed']; assert len(timed) == 32
            row = dict(action_dimension=dimension, construction_s=construction_s, load_s=load_s,
                engineering_updates=82, inherited_engineering_updates=inherited,
                cold_cycle_s=rows[0]['action_and_two_updates_s'], timings=rows,
                steady_action_mean_s=float(np.mean([r['action_s'] for r in timed])),
                steady_two_updates_mean_s=float(np.mean([r['two_updates_s'] for r in timed])),
                steady_cycle_p95_s=float(np.percentile([r['action_and_two_updates_s'] for r in timed], 95)),
                checkpoint_byte_identity_verified=True, checkpoint_hashes=reference)
            state['rows'].append(row); write(out/'execution.json', state)
            del agent; gc.collect()
        state.update(status='complete', engineering_updates=164,
            caveats=['This is isolated GPU learner timing, not three-learner contention or end-to-end physics throughput.',
                'Fixed engineering replay inputs; all resulting weights are discarded and never selected/evaluated.',
                'Cold starts, checkpoint IO, simulation and audits are additional; not an equal-compute claim.'])
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc)); raise
    finally:
        state.update(ended_utc=datetime.now(timezone.utc).isoformat(), memory_peak=int((cgroup/'memory.peak').read_text()))
        write(out/'execution.json', state)
    print(json.dumps(dict(status=state['status'], engineering_updates=164,
        rows=[{k:r[k] for k in ('action_dimension','construction_s','load_s','cold_cycle_s',
            'steady_action_mean_s','steady_two_updates_mean_s','steady_cycle_p95_s')} for r in state['rows']])))


if __name__ == '__main__':
    main()
