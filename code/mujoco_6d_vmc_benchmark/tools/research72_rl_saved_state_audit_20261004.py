"""Independently inspect completed RL manifests/replay; no JAX or physics.

Checks persisted state consistency, not actual optimizer restoration, training
continuation, actor action parity, or task performance.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np

from research72_checkpoint_20261003 import checkpoint_hashes


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def audit(manifest_path):
    manifest_hash = sha(manifest_path)
    manifest = read(manifest_path)
    checkpoint = Path(manifest['checkpoint'])
    hashes = checkpoint_hashes(checkpoint)
    assert hashes == manifest['hashes']
    protocol_path = Path(manifest['training_protocol'])
    assert sha(protocol_path) == manifest['training_protocol_sha256']
    protocol = read(protocol_path)
    execution_path = checkpoint.parent / 'execution.json'
    execution_hash = sha(execution_path)
    execution = read(execution_path)
    assert execution['status'] == 'complete'
    runner = read(checkpoint / 'office_runner.json')
    agent = read(checkpoint / 'official_agent_state.json')
    assert runner['episode_boundary'] and runner['automatic_exact_resume_supported']
    assert runner['pending_transition'] is None
    steps = runner['step']
    assert steps == execution['steps'] == agent['interactions'] == agent['reward_samples']
    assert steps == manifest['cumulative_physics_steps'] == runner['replay']['count']
    assert agent['updates'] == execution['updates']
    assert agent['config'] == protocol['agent_config']
    assert manifest['seed'] == protocol['seed'] == agent['config']['seed']
    assert manifest['controller'] == protocol['controller']
    dimension = 5 if manifest['controller'] == 'impedance' else 7
    assert agent['config']['action_dimension'] == dimension
    assert runner['episode'] == execution['episodes']
    assert 0 < steps <= runner['replay']['capacity'] == protocol['maximum_new_physics_steps']
    replay_path = checkpoint / 'office_replay.npz'
    assert sha(replay_path) == runner['replay']['sha256']
    shapes = dict(observation=(steps, 48), next_observation=(steps, 48),
                  action=(steps, dimension), reward=(steps,), terminated=(steps,), truncated=(steps,))
    with np.load(replay_path, allow_pickle=False) as replay:
        assert set(replay.files) == set(shapes)
        for key, shape in shapes.items():
            assert replay[key].shape == shape and replay[key].dtype == np.float32
            assert np.isfinite(replay[key]).all()
        assert np.isin(replay['terminated'], [0., 1.]).all()
        assert (replay['truncated'] == 0).all()
        assert replay['terminated'].sum() == runner['episode']
        assert replay['terminated'][-1] == 1
        assert np.max(np.abs(replay['action'])) <= 1.
    for state in (runner['exploration_rng'], runner['replay']['rng_state']):
        rng = np.random.default_rng()
        rng.bit_generator.state = state
        assert rng.bit_generator.state == state
    np.testing.assert_array_equal(runner['condition_order'],
                                  np.random.default_rng(manifest['seed'] + 100).permutation(32))
    parent = execution.get('resumed_from', {})
    assert execution['new_segment_steps'] == steps - parent.get('inherited_steps', 0)
    assert execution['new_segment_episodes'] == runner['episode'] - parent.get('inherited_episodes', 0)
    assert all('step_after' in row and row.get('ended_utc') for row in execution['rows'])
    for row in execution['rows']:
        assert sha(Path(row['run']) / 'AUDIT.json') == row['audit_sha256']
        assert sha(Path(row['run']) / 'rollout.npz') == row['trace_sha256']
    assert sum(row['step_after'] - row['step_before'] for row in execution['rows']) == execution['new_segment_steps']
    assert all(sha(path) == value for path, value in protocol['source_sha256'].items())
    assert sha(Path(protocol['parameter_source']) / 'PRIORS.json') == protocol['prior_file_sha256']
    assert checkpoint_hashes(checkpoint) == hashes
    assert sha(execution_path) == execution_hash and sha(manifest_path) == manifest_hash
    return dict(manifest=str(manifest_path), manifest_sha256=manifest_hash,
                checkpoint=str(checkpoint), checkpoint_files_verified=len(hashes),
                training_protocol_sha256=sha(protocol_path), execution_sha256=execution_hash,
                source_files_verified=len(protocol['source_sha256']), family=manifest['family'],
                controller=manifest['controller'], seed=manifest['seed'], action_dimension=dimension,
                cumulative_steps=steps, cumulative_episodes=runner['episode'], cumulative_updates=agent['updates'],
                new_segment_steps=execution['new_segment_steps'], inherited_steps=parent.get('inherited_steps', 0),
                replay_shapes=shapes, episode_boundary=True, rng_states_loadable=True,
                note='No learner loaded, no updates/actions/physics; actual resumed training remains a separate check.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', action='append', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    assert len(set(args.manifest)) == len(args.manifest)
    result = dict(schema='sii-research72-rl-saved-state-audit-v1',
                  created_utc=datetime.now(timezone.utc).isoformat(),
                  host=platform.node(), python=sys.executable, numpy=np.__version__, argv=sys.argv,
                  source_sha256={str(Path(__file__).resolve()): sha(__file__),
                                 str(Path(__file__).with_name('research72_checkpoint_20261003.py').resolve()):
                                     sha(Path(__file__).with_name('research72_checkpoint_20261003.py'))},
                  physics_steps=0, gradient_updates=0, actor_calls=0, sealed_reads=0,
                  rows=[audit(path.resolve()) for path in args.manifest])
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(output=str(args.output), sha256=sha(args.output), verified=len(result['rows']))))


if __name__ == '__main__':
    main()
