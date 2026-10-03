"""Independent frozen-RL actor replay from completed evaluation traces.

No simulator, updates, checkpoint selection or condition-manifest reads. Run one
model at a time after evaluation, including its failed/short completed episodes.
Parameter-law/servo verification remains the separate physical/filter audit.
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


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def normalization_hash(agent):
    digest = hashlib.sha256()
    for name, normalizer in [('observation', agent.observation_normalizer.obs_rms),
                             ('reward', agent.reward_normalizer.G_rms)]:
        for key in ('mean', 'var', 'count'):
            value = np.asarray(getattr(normalizer, key))
            digest.update((name+key+str(value.shape)+str(value.dtype)).encode())
            digest.update(value.tobytes())
    for key in ('G', 'G_r_max'):
        value = np.asarray(getattr(agent.reward_normalizer, key))
        digest.update((key+str(value.shape)+str(value.dtype)).encode())
        digest.update(value.tobytes())
    return digest.hexdigest()


def replay(agent, observations, actions, dimension):
    assert observations.ndim == 2 and observations.shape[1] == 48 and len(observations)
    assert actions.shape == (len(observations), dimension)
    assert np.isfinite(observations).all() and np.isfinite(actions).all()
    assert np.max(np.abs(actions)) <= 1.000001
    before = agent.diagnostics(); normalizers = normalization_hash(agent)
    for observation, expected in zip(observations, actions):
        value = observation.copy(); value.setflags(write=False)
        actual = agent.sample_action(value, training=False)
        np.testing.assert_array_equal(actual, expected)
    assert agent.diagnostics() == before, 'Inference changed counters/diagnostics'
    assert normalization_hash(agent) == normalizers, 'Inference changed normalization'
    return dict(samples=len(observations), raw_actor_replay_max_abs=0.,
                normalization_unchanged=True, counters_unchanged=True,
                observation_not_mutated=True)


def run_replay(agent, run, manifest, dimension):
    state = read(run/'execution.json')
    assert state['status'] == 'complete', 'Incomplete episodes are not completed replay evidence'
    audit = read(run/'AUDIT.json')
    assert audit['adapted_rl'] and audit['normalization_unchanged']
    assert sha(run/'rollout.npz') == audit['trace_sha256']
    assert read(run/'ADAPTED_RL_CHECKPOINT.json') == manifest
    files = ('execution.json', 'AUDIT.json', 'rollout.npz', 'baseline_policy.npz',
             'ADAPTED_RL_CHECKPOINT.json')
    before = {name: sha(run/name) for name in files}
    with np.load(run/'baseline_policy.npz', allow_pickle=False) as policy, \
         np.load(run/'rollout.npz', allow_pickle=False) as trace:
        np.testing.assert_array_equal(policy['observation'], trace['observation'])
        np.testing.assert_array_equal(policy['action'], trace['applied_action'])
        checks = replay(agent, policy['observation'], policy['raw_action'], dimension)
        if manifest['controller'] is None:
            np.testing.assert_array_equal(policy['raw_action'], policy['action'])
    assert before == {name: sha(run/name) for name in files}
    return dict(run=str(run.resolve()), evidence_sha256=before,
                task_success=audit['task_success'], strict_success=audit['strict_success'],
                full_horizon=audit['full_horizon'], **checks)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint-manifest', type=Path, required=True)
    p.add_argument('--parameter-source', type=Path, required=True)
    p.add_argument('--runs', nargs='+', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    assert len(set(p.resolve() for p in args.runs)) == len(args.runs)
    assert not args.output.exists()
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory = int((cg/'memory.max').read_text()); assert memory <= 3*1024**3
    manifest = read(args.checkpoint_manifest); checkpoint = Path(manifest['checkpoint'])
    assert checkpoint_hashes(checkpoint) == manifest['hashes']
    training = read(manifest['training_protocol'])
    assert sha(manifest['training_protocol']) == manifest['training_protocol_sha256']
    assert sha(args.parameter_source/'PRIORS.json') == training['prior_file_sha256']
    assert training['controller'] == manifest['controller']
    source_files = {str(f.resolve()): sha(f) for f in args.parameter_source.rglob('*')
                    if f.is_file() and f.suffix in ('.py','.json')}
    for path, digest in source_files.items():
        assert training['source_sha256'][path] == digest, 'Parameter/agent source changed'
    state = dict(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
        host=platform.node(), python=sys.executable, numpy=np.__version__, memory_max=memory,
        source_sha256=sha(__file__), checkpoint_helper_sha256=sha(Path(__file__).with_name('research72_checkpoint_20261003.py')),
        checkpoint_manifest=str(args.checkpoint_manifest.resolve()), checkpoint_manifest_sha256=sha(args.checkpoint_manifest),
        checkpoint_hashes=manifest['hashes'], parameter_source_sha256=source_files,
        planned_runs=[str(p.resolve()) for p in args.runs], rows=[], physics_steps=0, training_updates=0,
        condition_manifests_read=False,
        scope='Exact independent inference replay for all supplied completed episodes; no success filter.',
        limitations=['Parameter-controller state/servo torque is not reconstructed by this actor replay.',
            'Action provenance/normalization check, not a new task outcome or a sensor-realism proof.',
            'All planned final episodes must additionally be checked against this supplied-run ledger.'])
    def save():
        args.output.write_text(json.dumps(state, indent=2, allow_nan=False)+'\n')
    save()
    try:
        sys.path.insert(0, str(args.parameter_source.resolve()))
        from official_parameter_agent import OfficialParameterAgent
        cp = read(checkpoint/'official_agent_state.json'); config=cp['config']; utd=cp['utd']
        assert config == training['agent_config']
        agent = OfficialParameterAgent(seed=config['seed'], total_steps=int(config['learning_rate_decay_step'])//utd,
            utd=utd, gamma=config['gamma'], entropy_coef=config['temp_target_entropy_coef'],
            initial_temperature=config['temp_initial_value'], action_dimension=config['action_dimension'])
        agent.load(checkpoint)
        for run in args.runs:
            state['rows'].append(run_replay(agent, run.resolve(), manifest, config['action_dimension']))
            save()
        assert checkpoint_hashes(checkpoint) == manifest['hashes']
        assert all(sha(path) == digest for path, digest in source_files.items())
        assert sha(args.checkpoint_manifest) == state['checkpoint_manifest_sha256']
        state['status']='complete'
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc)); raise
    finally:
        state['ended_utc']=datetime.now(timezone.utc).isoformat(); save()
    print(json.dumps(dict(status=state['status'], episodes=len(state['rows']),
                         samples=sum(r['samples'] for r in state['rows']), output_sha256=sha(args.output))))


if __name__ == '__main__':
    main()
