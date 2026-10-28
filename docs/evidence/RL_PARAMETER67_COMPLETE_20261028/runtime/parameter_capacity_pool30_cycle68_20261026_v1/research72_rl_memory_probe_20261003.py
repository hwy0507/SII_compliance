"""Bounded learner memory test with measured physics-queue memory ballast.

No simulation, train/test condition reads, candidates or saved learned weights.
Uses the unchanged engineering-only 7D checkpoint and discards eight updates.
The ballast approximates allocation pressure, not a real concurrent simulator.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('runtime', 'probe-root', 'parameter-source', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--ballast-bytes', type=int, required=True)
    args = parser.parse_args()
    assert 0 < args.ballast_bytes <= 1200*1024**2
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    assert int((cg/'memory.max').read_text()) == 3*1024**3
    assert all(os.environ[k] == '1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    state = dict(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
        stage='imports', source_sha256=sha(__file__), command=sys.argv, python=sys.executable,
        new_physics_steps=0, candidate_checkpoints_produced=0, engineering_updates=0,
        ballast_bytes=args.ballast_bytes, memory_max_bytes=3*1024**3,
        limitation='Synthetic allocation pressure, not three GPU learners plus real physics or an end-to-end training continuation.',
        samples=[])
    def save():
        state['memory_current_bytes'] = int((cg/'memory.current').read_text())
        state['memory_peak_bytes'] = int((cg/'memory.peak').read_text())
        state['memory_events'] = (cg/'memory.events').read_text()
        (out/'execution.json').write_text(json.dumps(state, indent=2, allow_nan=False)+'\n')
    save()
    try:
        sys.path.insert(0, str(args.runtime.resolve()/'tools'))
        # Match the actual training process imports and full replay allocation.
        from research72_train_rl_20261003 import Replay
        from research72_checkpoint_20261003 import checkpoint_hashes
        import numpy as np
        sys.path.insert(0, str(args.parameter_source.resolve()))
        from official_parameter_agent import OfficialParameterAgent, BATCH_SIZE
        import jax
        assert all(d.platform == 'gpu' for d in jax.devices())
        receipt = json.loads((args.probe_root/'execution.json').read_text())
        assert receipt['status'] == 'complete' and receipt['physics_steps'] == 0 and receipt['engineering_only']
        reference = next(r['hashes'] for r in receipt['rows'] if r['action_dimension'] == 7)
        cp = args.probe_root/'dimension_7'
        assert checkpoint_hashes(cp) == reference
        state.update(probe_receipt_sha256=sha(args.probe_root/'execution.json'),
            checkpoint_hashes=reference, jax=jax.__version__, numpy=np.__version__,
            train_source_sha256=sha(args.runtime/'tools/research72_train_rl_20261003.py'),
            agent_source_sha256=sha(args.parameter_source/'official_parameter_agent.py'),
            stage='ballast_and_replay_allocation')
        save()
        ballast = np.ones(args.ballast_bytes, dtype=np.uint8)
        replay = Replay(80000, 7, 2026100301+53)
        for values in replay.data.values(): values.fill(0.)
        state['stage'] = 'agent_construction'; save()
        agent = OfficialParameterAgent(seed=2026100301, total_steps=80000, utd=2,
            gamma=.9995, entropy_coef=-2., initial_temperature=.0001, action_dimension=7)
        agent.load(cp)
        with np.load(cp/'office_replay.npz') as data:
            batch = {k: data[k][:BATCH_SIZE].copy() for k in data.files}
        state['stage'] = 'four_action_plus_two_update_cycles'; save()
        inherited = agent.updates
        for index in range(4):
            start = time.perf_counter()
            agent.sample_action(batch['observation'][index],
                previous_transition=dict(reward=-.01, terminated=False, truncated=False), training=True)
            agent.update(batch); agent.update(batch)
            raw = agent.raw_agent
            jax.block_until_ready((raw._actor, raw._critic, raw._target_critic, raw._temperature, raw._rng))
            state['engineering_updates'] = agent.updates-inherited
            state['samples'].append(dict(cycle=index, elapsed_s=time.perf_counter()-start,
                memory_current_bytes=int((cg/'memory.current').read_text())))
            save()
        assert agent.updates-inherited == 8 and ballast[0] == ballast[-1] == 1
        assert checkpoint_hashes(cp) == reference
        state.update(status='complete', stage='complete', original_checkpoint_byte_identity=True,
            weights_discarded=True, selected_as_candidate=False)
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc))
        raise
    finally:
        state['ended_utc'] = datetime.now(timezone.utc).isoformat(); save()
    print(json.dumps({k:state[k] for k in ('status','engineering_updates','memory_peak_bytes','ballast_bytes')}))


if __name__ == '__main__':
    main()
