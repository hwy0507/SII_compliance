"""Replay the first stochastic action of an actual resumed RL segment.

An independent learner loads the immutable parent, but makes no updates and
executes no physics. This checks the first resumed action/normalizer/RNG path;
it does not certify all subsequent updates or replace final frozen-policy replay.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys

import numpy as np

from research72_checkpoint_20261003 import checkpoint_hashes


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check_lineage(parent_manifest, parent_protocol, parent_execution, runner,
                  child_protocol, child_execution):
    """Check an atomic child snapshot; it may still be running after row zero."""
    assert parent_execution['status'] == 'complete'
    assert child_execution['status'] in ('running', 'complete')
    assert runner['episode_boundary'] and runner['automatic_exact_resume_supported']
    assert runner['pending_transition'] is None
    inherited = child_execution['resumed_from']
    assert inherited['checkpoint'] == parent_manifest['checkpoint']
    assert inherited['hashes'] == parent_manifest['hashes']
    assert inherited['inherited_steps'] == runner['step'] == parent_execution['steps']
    assert runner['step'] == parent_manifest['cumulative_physics_steps']
    assert inherited['inherited_episodes'] == runner['episode'] == parent_execution['episodes']
    for key in ('protocol_sha256', 'seed', 'controller', 'reward', 'agent_config',
                'utd', 'maximum_new_physics_steps', 'prior_file_sha256',
                'training_condition_ids', 'warmup_steps', 'source_sha256'):
        assert parent_protocol[key] == child_protocol[key], 'Changed continuation contract: '+key
    assert runner['step'] >= parent_protocol['warmup_steps'], 'Random warmup override is outside this audit'
    assert child_execution['new_segment_steps'] == child_execution['steps'] - runner['step']
    assert child_execution['new_segment_episodes'] == child_execution['episodes'] - runner['episode']
    assert child_execution['updates'] > parent_execution['updates'], 'No actual resumed update observed'
    row = child_execution['rows'][0]
    assert row.get('ended_utc') and row['step_after'] > row['step_before']
    assert row['step_before'] == runner['step'] and row['episode'] == runner['episode']
    assert row['steps'] == row['step_after'] - row['step_before']
    order = parent_protocol['training_condition_ids']
    assert row['condition_id'] == order[runner['episode'] % len(order)]
    assert child_execution['steps'] >= row['step_after']
    return row


def replay_first(agent, observation, expected, saved_state):
    assert agent.interactions == saved_state['interactions']
    assert agent.updates == saved_state['updates']
    assert agent.reward_samples == saved_state['reward_samples']
    np.testing.assert_array_equal(np.asarray(agent.raw_agent._rng), saved_state['jax_rng'])
    before = agent.diagnostics()
    actual = agent.sample_action(observation.copy(), previous_transition=None, training=True)
    np.testing.assert_array_equal(actual, expected)
    assert agent.interactions == saved_state['interactions'] + 1
    assert agent.updates == saved_state['updates']
    assert agent.reward_samples == saved_state['reward_samples']
    return dict(first_action_max_abs=0., before=before, after=agent.diagnostics(),
                action=actual.tolist(), sampling_mode='training=True, no pending transition')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-manifest', type=Path, required=True)
    parser.add_argument('--child-segment', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'))
    group = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory = int((group/'memory.max').read_text())
    assert memory <= 3*1024**3
    manifest = read(args.parent_manifest)
    checkpoint = Path(manifest['checkpoint'])
    hashes = checkpoint_hashes(checkpoint)
    assert hashes == manifest['hashes']
    parent_path = Path(manifest['training_protocol'])
    assert sha(parent_path) == manifest['training_protocol_sha256']
    parent_protocol = read(parent_path)
    parent_execution_path = checkpoint.parent/'execution.json'
    parent_execution = read(parent_execution_path)
    runner = read(checkpoint/'office_runner.json')
    child_protocol_path = args.child_segment/'PROTOCOL.json'
    child_protocol = read(child_protocol_path)
    # Read once: later progress in this live file must not masquerade as our snapshot.
    child_bytes = (args.child_segment/'execution.json').read_bytes()
    child_execution = json.loads(child_bytes)
    row = check_lineage(manifest, parent_protocol, parent_execution, runner,
                        child_protocol, child_execution)
    inherited = child_execution['resumed_from']
    assert inherited['training_protocol_sha256'] == sha(parent_path)
    assert inherited['parent_execution_sha256'] == sha(parent_execution_path)
    run = Path(row['run'])
    assert read(run/'execution.json')['status'] == 'complete'
    assert sha(run/'AUDIT.json') == row['audit_sha256']
    assert sha(run/'rollout.npz') == row['trace_sha256']
    paths = [args.parent_manifest, parent_path, parent_execution_path, child_protocol_path,
             run/'execution.json', run/'AUDIT.json', run/'rollout.npz', run/'baseline_policy.npz']
    immutable = {str(p.resolve()): sha(p) for p in paths}
    for path, digest in parent_protocol['source_sha256'].items():
        assert sha(path) == digest
    parameter = Path(parent_protocol['parameter_source'])
    assert sha(parameter/'PRIORS.json') == parent_protocol['prior_file_sha256']
    with np.load(run/'baseline_policy.npz', allow_pickle=False) as policy, \
         np.load(run/'rollout.npz', allow_pickle=False) as trace:
        np.testing.assert_array_equal(policy['observation'], trace['observation'])
        np.testing.assert_array_equal(policy['action'], trace['applied_action'])
        assert len(policy['raw_action']) == row['steps']
        observation = policy['observation'][0].astype(np.float32)
        expected = policy['raw_action'][0].copy()
    state = dict(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
        host=platform.node(), python=sys.executable, numpy=np.__version__, memory_max=memory,
        source_sha256=sha(__file__), helper_sha256=sha(Path(__file__).with_name('research72_checkpoint_20261003.py')),
        immutable_evidence_sha256=immutable,
        child_execution_snapshot_sha256=hashlib.sha256(child_bytes).hexdigest(),
        child_execution_snapshot=child_execution, parent_checkpoint_hashes=hashes,
        sealed_reads=0, physics_steps=0, gradient_updates=0, actor_calls=0,
        limitations=['Only the first stochastic action is independently replayed.',
            'Later optimizer updates and replay-buffer inheritance need their own evidence.',
            'No new task outcome or final-test policy evaluation.'])
    def save():
        args.output.write_text(json.dumps(state, indent=2, allow_nan=False)+'\n')
    save()
    try:
        sys.path.insert(0, str(parameter))
        from official_parameter_agent import OfficialParameterAgent
        import jax
        saved = read(checkpoint/'official_agent_state.json')
        config = saved['config']; utd = saved['utd']
        assert config == parent_protocol['agent_config']
        agent = OfficialParameterAgent(seed=config['seed'], total_steps=config['learning_rate_decay_step']//utd,
            utd=utd, gamma=config['gamma'], entropy_coef=config['temp_target_entropy_coef'],
            initial_temperature=config['temp_initial_value'], action_dimension=config['action_dimension'])
        agent.load(checkpoint)
        state['replay'] = replay_first(agent, observation, expected, saved)
        state.update(actor_calls=1, jax=jax.__version__, backend=jax.default_backend())
        assert checkpoint_hashes(checkpoint) == hashes
        assert {str(p.resolve()): sha(p) for p in paths} == immutable
        assert all(sha(path) == digest for path, digest in parent_protocol['source_sha256'].items())
        state['status'] = 'complete'
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc)); raise
    finally:
        state['ended_utc'] = datetime.now(timezone.utc).isoformat(); save()
    print(json.dumps(dict(status=state['status'], actor_calls=1, output_sha256=sha(args.output))))


if __name__ == '__main__':
    main()
