"""Finite disposable optimizer timing; no simulator, model save or acceptance.

Compare CPU and CUDA with the same closed training checkpoint and replay batch.
Running training snapshots and environments are never edited by this probe.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--registration', type=Path, required=True)
    p.add_argument('--backend', choices=['cpu', 'cuda'], required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    from rl_recovery_control_20261016 import verify_checkpoint, read, digest
    from rl_goal_stage_20261016 import write
    reg = read(a.registration)
    assert platform.node() == 'airpig'
    assert reg['schema'] == 'sii-goal-update-backend-probe-v1'
    assert reg['warmup_updates'] == 2 and reg['timed_updates'] == 100
    assert os.environ.get('JAX_PLATFORMS') == a.backend
    assert os.environ.get('XLA_PYTHON_CLIENT_PREALLOCATE') == 'false'
    assert all(os.environ.get(k) == '1' for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'])
    assert not a.output.exists()
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::')[1].lstrip('/')
    assert int((cg/'memory.max').read_text()) <= 2*1024**3
    assert (cg/'memory.swap.max').read_text().strip() == '0'
    cp = Path(reg['checkpoint'])
    checked = verify_checkpoint(cp)
    assert digest(cp/'office_runner.json') == reg['runner_sha256']
    spec = read(cp.parent/'PROTOCOL.json')
    result = dict(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
        registration_sha256=digest(a.registration), source_sha256=digest(Path(__file__)),
        checkpoint=str(cp), checkpoint_hashes=checked['hashes'], backend=a.backend,
        simulation=False, model_saved=False, acceptance=False,
        cpu_affinity=sorted(os.sched_getaffinity(0)))
    write(a.output, result)
    try:
        assert result['cpu_affinity'] == [reg['cpu']], 'Require actual CPU affinity, not only systemd AllowedCPUs'
        if reg.get('resources'):
            import goal_compute_backend_20261016 as guard
            assert digest(Path(guard.__file__)) == reg['backend_guard_source_sha256']
            assert guard.backend(reg) == a.backend
            result['compute_runtime'] = guard.runtime_info(reg, expected_cpu=reg['cpu'])
            guard.check_backend_resume(spec, reg, {'backend_migration': True})
            assert not guard.gpu_admission_reason(reg, guard.gpu_snapshot())
        sys.path.insert(0, spec['parameter_source'])
        import numpy as np
        import jax
        from official_parameter_agent import OfficialParameterAgent
        from multistep_rl_replay_20261009 import MultiStepReplay
        config = spec['agent_config']
        agent = OfficialParameterAgent(seed=spec['seed'], total_steps=spec['maximum_steps'],
            utd=spec['utd'], gamma=config['gamma'], entropy_coef=config['temp_target_entropy_coef'],
            initial_temperature=config['temp_initial_value'], action_dimension=config['action_dimension'])
        agent.load(cp)
        runner = read(cp/'office_runner.json')
        replay = MultiStepReplay(runner['step'], config['action_dimension'], reg['seed'],
                                 n_step=config['n_step'], gamma=config['gamma'])
        with np.load(cp/'office_replay.npz', allow_pickle=False) as raw:
            assert set(raw.files) == set(replay.data)
            for key in replay.data:
                assert raw[key].shape == replay.data[key].shape
                replay.data[key][:] = raw[key]
        replay.count = runner['step']
        assert replay.data['terminated'][-1]
        replay.last_terminal = replay.count-1
        indices = np.random.default_rng(reg['seed']).integers(replay.count, size=256)
        batch = replay.at(indices)
        result['batch_indices'] = indices.tolist()
        result['devices'] = [str(d) for d in jax.devices()]
        result['device_kinds'] = [d.device_kind for d in jax.devices()]
        assert all(d.platform == ('gpu' if a.backend == 'cuda' else 'cpu') for d in jax.devices())
        before = agent.updates
        timings = []
        first_metrics = None
        # float conversion synchronizes device work before stopping each timer.
        for i in range(reg['warmup_updates']+reg['timed_updates']):
            start = time.perf_counter()
            info = agent.update(batch)
            leaves = jax.tree_util.tree_leaves(info)
            assert all(np.isfinite(np.asarray(v)).all() for v in leaves)
            if first_metrics is None:
                first_metrics = jax.tree_util.tree_map(lambda v: np.asarray(v).tolist(), info)
            timings.append(time.perf_counter()-start)
        steady = np.asarray(timings[reg['warmup_updates']:])
        assert agent.updates-before == 102
        result.update(status='passed', discarded_updates=102, first_metrics=first_metrics,
            warmup_seconds=timings[:2], timed_total_seconds=float(steady.sum()),
            update_seconds_median=float(np.median(steady)), update_seconds_p90=float(np.quantile(steady,.9)),
            timed_updates_per_second=float(len(steady)/steady.sum()),
            checkpoint_hashes_unchanged=all(digest(cp/k)==v for k,v in checked['hashes'].items()),
            interpretation='Fixed replay-batch disposable optimizer throughput only. No policy benefit, full-loop speedup, CPU/GPU exact numerical equivalence or deployment claim.')
        assert result['checkpoint_hashes_unchanged']
        result['gpu_snapshot'] = subprocess.run(['nvidia-smi', '--query-gpu=name,temperature.gpu,memory.used,memory.total',
            '--format=csv,noheader'], capture_output=True, text=True, timeout=15).stdout.strip()
    except BaseException as exc:
        result.update(status='failed_preserved', error=repr(exc))
        raise
    finally:
        result.update(ended_utc=datetime.now(timezone.utc).isoformat(),
            memory_peak_bytes=int((cg/'memory.peak').read_text()),
            memory_events=(cg/'memory.events').read_text())
        write(a.output, result)
    print(json.dumps({k:result[k] for k in ['status','backend','timed_updates_per_second','memory_peak_bytes']}))


if __name__ == '__main__':
    main()
