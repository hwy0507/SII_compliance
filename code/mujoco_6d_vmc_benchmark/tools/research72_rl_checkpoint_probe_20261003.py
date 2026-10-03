"""No-physics regression of official RL updates, recursive hashes and reload.

Uses known training observations, synthetic rewards and actions solely for an
engineering check. These weights must never be evaluated as trained baselines.
"""
import argparse
import gc
import json
import os
from pathlib import Path
import sys
import numpy as np
from optimize_tool_contact_20261002 import sha, write, now
from research72_checkpoint_20261003 import checkpoint_hashes
from research72_train_rl_20261003 import Replay


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--parameter-source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    assert int((cg/'memory.max').read_text()) <= 3*1024**3
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    sys.path.insert(0, str(a.parameter_source))
    from official_parameter_agent import OfficialParameterAgent, BATCH_SIZE
    import jax
    with np.load(a.data) as z:
        obs = z['observation'][z['train'].astype(bool)][:600].astype(np.float32)
    assert obs.shape == (600,48)
    state = dict(status='running', started_utc=now(), source_sha256=sha(Path(__file__)),
        checkpoint_helper_sha256=sha(Path(__file__).with_name('research72_checkpoint_20261003.py')),
        data_sha256=sha(a.data), physics_steps=0, engineering_only=True, rows=[])
    write(out/'execution.json', state)
    def construct(dimension):
        return OfficialParameterAgent(seed=2026100301, total_steps=80000, utd=2,
            gamma=.9995, entropy_coef=-2., initial_temperature=.0001, action_dimension=dimension)
    def arrays(agent):
        raw = agent.raw_agent
        return [np.asarray(x).copy() for x in jax.tree_util.tree_leaves(
            (raw._actor,raw._critic,raw._target_critic,raw._temperature,raw._rng))]
    try:
        for dimension in (5,7):
            agent = construct(dimension)
            replay = Replay(1024, dimension, 1403)
            rng = np.random.default_rng(1404)
            pending = None
            for i in range(512):
                action = agent.sample_action(obs[i], previous_transition=pending, training=True)
                reward = -float(rng.uniform(0,.1))
                terminal = i == 511
                replay.add(observation=obs[i], action=action, reward=reward,
                    terminated=float(terminal), truncated=0., next_observation=obs[i+1])
                pending = dict(reward=reward, terminated=terminal, truncated=False)
            agent.consume_transition(**pending)
            for _ in range(2):
                agent.update(replay.sample(BATCH_SIZE))
            cp = out/f'dimension_{dimension}'
            agent.save(cp)
            replay_state = replay.save(cp/'office_replay.npz')
            restored = Replay(1024, dimension, 9999)
            restored.restore(cp/'office_replay.npz', replay_state)
            hashes = checkpoint_hashes(cp)
            before = agent.diagnostics()
            batches = [replay.sample(BATCH_SIZE) for _ in range(3)]
            for batch in batches:
                reloaded = restored.sample(BATCH_SIZE)
                for key in batch:
                    np.testing.assert_array_equal(batch[key], reloaded[key])
            expected_actions = []
            for i,batch in enumerate(batches):
                expected_actions.append(agent.sample_action(obs[512+i], training=True))
                agent.update(batch)
            expected = arrays(agent)
            expected_diagnostics = agent.diagnostics()
            del agent
            gc.collect()
            agent = construct(dimension)
            agent.load(cp)
            assert agent.diagnostics() == before
            for i,batch in enumerate(batches):
                actual = agent.sample_action(obs[512+i], training=True)
                np.testing.assert_array_equal(actual, expected_actions[i])
                agent.update(batch)
            actual = arrays(agent)
            assert len(expected) == len(actual)
            for x,y in zip(expected, actual):
                np.testing.assert_array_equal(x,y)
            assert agent.diagnostics() == expected_diagnostics
            assert checkpoint_hashes(cp) == hashes
            state['rows'].append(dict(action_dimension=dimension, files=len(hashes), hashes=hashes,
                exact_future_action_and_update_replay=True, exact_replay_rng_restore=True,
                compared_state_arrays=len(actual),
                initial_updates=2, replayed_updates=3, diagnostics=agent.diagnostics()))
            write(out/'execution.json',state)
            del agent, expected, actual
            gc.collect()
        state['status'] = 'complete'
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc))
        raise
    finally:
        state['ended_utc'] = now()
        write(out/'execution.json', state)
    print(json.dumps(dict(status=state['status'], dimensions=[5,7], physics_steps=0)))


if __name__ == '__main__':
    main()
