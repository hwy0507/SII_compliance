"""Replay saved RL interval rewards with the exact frozen reward implementation.

No learner, actor, updates, physics or heldout access. The initial potential
was not saved by the worker: initialize it arbitrarily and explicitly exclude
the first reward of EACH episode. It does not affect rewarder state, so all
later rewards (including terminal penalties) can be checked without inference.
This is pipeline consistency, not independent physical interval reconstruction.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import numpy as np
from research72_checkpoint_20261003 import checkpoint_hashes


def read(path): return json.loads(Path(path).read_text())
def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def replay_episode(module, config, intervals, expected, success):
    assert len(intervals) == len(expected)+1 and intervals[0] is None
    assert len(expected) > 1 and np.isfinite(expected).all()
    # Source runner uses these original denominator constants.
    assert config['horizon_s'] == 55. and config['error_scale_m'] == .12
    rewarder = module.OfficeReward(module.RewardConfig(**config))
    current = 0.  # Not claimed to be the actual initial task potential.
    rewards = []; terms_total = {}; terminal_terms = None
    for index, interval in enumerate(intervals[1:]):
        final = index == len(expected)-1
        item = module.IntervalMetrics(elapsed_s=interval['elapsed_s'],
            error_cost=interval['error_integral']/(55*.12**2),
            bounded_error_cost=interval['bounded_error_integral']/55,
            peak_torque_ratio=interval['peak_torque_ratio'],
            peak_torque_nm_per_joint=interval['peak_torque_nm_per_joint'],
            max_position_error_m=interval['max_position_error_m'], substeps=interval['substeps'])
        reward, terms = rewarder(item, interval['executed_action'], current_potential=current,
            next_potential=interval['potential'], terminated=final, success=final and success,
            failure=final and not success,
            terminal_reason=('original_strict_success' if success else 'original_horizon_or_abort') if final else None)
        current = interval['potential']; rewards.append(reward)
        if index:
            for key in ('task', 'progress', 'error', 'peak_torque', 'time', 'smooth', 'failure_continuation'):
                terms_total[key] = terms_total.get(key, 0.) + terms[key]
        if final: terminal_terms = {key: terms[key] for key in (
            'task', 'failure_continuation', 'terminated', 'success', 'failure', 'effective_next_potential')}
    reconstructed = np.asarray(rewards, dtype=np.float32)
    np.testing.assert_array_equal(reconstructed[1:], expected[1:])
    return dict(checked_rewards=len(expected)-1, excluded_first_rewards=1,
        checked_reward_max_abs=0., checked_return_float64=float(np.sum(rewards[1:])),
        checked_term_sums=terms_total, terminal=terminal_terms,
        saved_interval_count=len(expected), saved_substeps=sum(i['substeps'] for i in intervals[1:]),
        saved_elapsed_s=sum(i['elapsed_s'] for i in intervals[1:]))


def audit(manifest_path):
    manifest_digest = sha(manifest_path); manifest = read(manifest_path)
    checkpoint = Path(manifest['checkpoint']); hashes = checkpoint_hashes(checkpoint)
    assert hashes == manifest['hashes']
    protocol_path = Path(manifest['training_protocol']); protocol = read(protocol_path)
    assert sha(protocol_path) == manifest['training_protocol_sha256']
    sources = protocol['source_sha256']
    assert all(sha(path)==digest for path,digest in sources.items())
    paths = [Path(p) for p in sources if Path(p).name=='rewards.py']
    assert len(paths)==1
    spec = importlib.util.spec_from_file_location('sii_reward_replay_frozen', paths[0])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module; spec.loader.exec_module(module)
    execution_path = checkpoint.parent/'execution.json'
    execution_digest = sha(execution_path); execution = read(execution_path)
    assert execution['status']=='complete'
    runner = read(checkpoint/'office_runner.json')
    assert runner['step']==execution['steps']==manifest['cumulative_physics_steps']
    assert runner['episode_boundary'] and runner['pending_transition'] is None
    replay_path = checkpoint/'office_replay.npz'
    assert sha(replay_path)==runner['replay']['sha256']
    with np.load(replay_path, allow_pickle=False) as z:
        rewards = z['reward'].copy(); terminal = z['terminated'].copy()
    assert rewards.shape == terminal.shape == (execution['steps'],)
    assert rewards.dtype == terminal.dtype == np.float32
    cursor = execution.get('resumed_from', {}).get('inherited_steps', 0)
    rows = []
    for original in execution['rows']:
        start, end = original['step_before'], original['step_after']
        assert start == cursor and end-start == original['steps']
        run = Path(original['run']); interval_path = run/'RL_INTERVALS.json'
        intervals_digest = sha(interval_path); intervals = read(interval_path)
        assert sha(run/'AUDIT.json') == original['audit_sha256']
        assert sha(run/'rollout.npz') == original['trace_sha256']
        result = read(run/'AUDIT.json')
        success = bool(result['task_success'] and result['strict_success'])
        assert success == bool(original['result']['task_success'] and original['result']['strict_success'])
        np.testing.assert_array_equal(terminal[start:end], np.r_[np.zeros(end-start-1), 1.])
        checked = replay_episode(module, protocol['reward'], intervals, rewards[start:end], success)
        assert sha(interval_path)==intervals_digest
        rows.append(dict(run=str(run), condition_id=original['condition_id'],
            audit_sha256=original['audit_sha256'], trace_sha256=original['trace_sha256'],
            saved_interval_sha256=intervals_digest, step_start=start, step_end=end, **checked))
        cursor = end
    assert cursor == execution['steps']
    assert sum(r['checked_rewards']+r['excluded_first_rewards'] for r in rows)==execution['new_segment_steps']
    assert sha(manifest_path)==manifest_digest and sha(execution_path)==execution_digest
    assert checkpoint_hashes(checkpoint)==hashes
    assert all(sha(path)==digest for path,digest in sources.items())
    return dict(manifest=str(manifest_path), manifest_sha256=manifest_digest,
        checkpoint=str(checkpoint), checkpoint_hashes=hashes,
        training_protocol_sha256=sha(protocol_path), execution_sha256=execution_digest,
        frozen_reward_source=str(paths[0]), frozen_reward_sha256=sha(paths[0]),
        controller=manifest['controller'], seed=manifest['seed'], reward_config=protocol['reward'],
        cumulative_steps=execution['steps'], new_segment_steps=execution['new_segment_steps'], rows=rows,
        checked_rewards=sum(r['checked_rewards'] for r in rows),
        excluded_first_rewards=sum(r['excluded_first_rewards'] for r in rows))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, action='append', required=True)
    p.add_argument('--output', type=Path, required=True); args=p.parse_args()
    assert not args.output.exists() and len(set(args.manifest))==len(args.manifest)
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=int((cg/'memory.max').read_text()); assert memory<=3*1024**3
    result=dict(status='complete', created_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(__file__), host=platform.node(), python=sys.executable, numpy=np.__version__,
        argv=sys.argv, memory_max=memory, actor_calls=0, gradient_updates=0, physics_steps=0, sealed_reads=0,
        results=[audit(p.resolve()) for p in args.manifest],
        limits=['First reward of every episode excluded because initial potential was not saved; never inferred from the reward being checked.',
            'Saved interval metrics are inputs here, not independently reconstructed from physical substeps.',
            'Verifies frozen reward-to-replay consistency, not optimizer gradients, terminal next observations, convergence or task success.',
            'Checked return/term sums omit each first reward and are not complete episode returns.'])
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps(dict(sha256=sha(args.output), models=len(result['results']),
        checked_rewards=sum(r['checked_rewards'] for r in result['results']),
        excluded=sum(r['excluded_first_rewards'] for r in result['results']))))


if __name__=='__main__': main()
