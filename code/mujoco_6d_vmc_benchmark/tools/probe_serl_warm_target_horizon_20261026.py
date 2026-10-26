"""Finite one-step versus 32-step probe from the fully trained formal13 state.

Both arms restore identical network/optimizer/RNG, use identical replay row draws
and official 8:1 updates. No physics, saved weights, or formal target migration.
The historical multistep serialization marker remains intact in memory; the
registered batch target is explicitly selected here, and no checkpoint is emitted.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import sys
import time


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(path, data):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def main(args):
    os.sched_setaffinity(0, {54})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    reg = json.loads(args.registration.read_text())
    assert reg['horizons'] == [32, 1] and reg['batch_size'] == 65536
    assert reg['outer_updates_per_arm'] == 2000 and reg['record_every'] == 100
    assert reg['auxiliary_weights_promoted'] is False
    for ref in [reg['checkpoint'], reg['cycle_review'], reg['health_review']]:
        assert sha(ref['path']) == ref['sha256']
    for name, h in reg['source_hashes'].items():
        assert sha(Path(__file__).with_name(name)) == h
    sys.path.insert(0, reg['adapter_runtime'])
    for name, h in reg['adapter_hashes'].items():
        assert sha(Path(reg['adapter_runtime'])/name) == h
    sys.path.insert(0, reg['base_adapter_runtime'])
    from train_serl_state_20261026 import Replay
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner, replay_class
    from serl_multistep_replay_gather_20261026 import optimized_class
    from serl_multistep_batch_transfer_20261026 import transfer_class
    from validate_serl_state_20261026 import digest
    ck = torch.load(reg['checkpoint']['path'], map_location='cpu', weights_only=False)
    assert ck['cycle'] == 13 and ck['boundary'] == 'complete_condition_cycle'
    review = json.loads(Path(reg['cycle_review']['path']).read_text())
    health = json.loads(Path(reg['health_review']['path']).read_text())
    assert review['passed'] and health['network_optimizer_rng_unchanged']
    assert review['methods']['direct']['checkpoint_sha256'] == health['checkpoint_sha256'] == reg['checkpoint']['sha256']
    parent_digest = digest(ck['learner']); replay_digest = digest(ck['replay'])
    arrays = ck['replay']['arrays']; extra = ck['replay']['multistep_target_extension']
    assert not extra['pending']
    ready = np.asarray(extra['ready'], np.int64)
    assert len(ready) == ck['replay']['size'] and np.array_equal(np.sort(ready), np.arange(len(ready)))
    terminal = np.flatnonzero(arrays['dones'][:, 0]); assert len(terminal) == 420
    ids = np.random.default_rng(reg['seed']).choice(ck['replay']['size'], 4096, replace=False)

    def select(rows, horizon):
        assert horizon in (1, 32)
        values = {k: v[rows] for k, v in arrays.items() if k not in ('rewards', 'next_observations')}
        if horizon == 32:
            values.update(rewards=extra['target_rewards'][rows, None], next_observations=arrays['next_observations'][extra['target_endpoints'][rows]], _bootstrap=extra['target_bootstrap'][rows])
        else:
            values.update(rewards=arrays['rewards'][rows], next_observations=arrays['next_observations'][rows], _bootstrap=1.-arrays['dones'][rows, 0])
        return values

    # Verify the control arm's first entire batch and RNG against the actual
    # deployed sampler before any optimization. One-step terminal rows coincide.
    replay = optimized_class(replay_class(Replay))(7, 49, reg['seed'])
    replay.load_state_dict(copy.deepcopy(ck['replay']))
    rng = np.random.default_rng(); rng.bit_generator.state = copy.deepcopy(ck['replay']['rng'])
    first_rows = ready[rng.integers(len(ready), size=65536)]
    assert digest(select(first_rows, 32)) == digest(replay.sample(65536))
    assert digest(rng.bit_generator.state) == digest(replay.rng.bit_generator.state)
    assert digest(select(terminal, 1)) == digest(select(terminal, 32))
    del replay
    cls = transfer_class(SerlMultistepLearner); results = []
    for horizon in reg['horizons']:
        learner = cls(Path(reg['runtime']), upstream=Path(reg['upstream']), upstream_manifest=Path(reg['upstream_manifest']), dimension=7, direct=True, seed=20261026, device='cuda:0')
        learner.load_state_dict(copy.deepcopy(ck['learner']))
        assert digest(learner.state_dict()) == parent_digest
        rng = np.random.default_rng(); rng.bit_generator.state = copy.deepcopy(ck['replay']['rng'])
        draws_hash = hashlib.sha256()

        def diagnose():
            before = digest(learner.state_dict()); jax = learner.jax
            key, actionkey = jax.random.split(jax.random.PRNGKey(262))
            t = learner.batch(select(terminal, 1))
            tq = np.asarray(learner.agent.forward_critic(t['observations'], t['actions'], rng=key))
            error = np.abs(tq - np.asarray(t['rewards'])[None])
            result = dict(terminal_mae=float(error.mean()), terminal_max=float(error.max()), temperature=float(learner.agent.forward_temperature()))
            for h in (1, 32):
                tb = learner.batch(select(ids, h))
                pred = learner.agent.forward_critic(tb['observations'], tb['actions'], rng=key)
                acts, _ = learner.agent._compute_next_actions(tb, actionkey)
                targetq = learner.agent.forward_target_critic(tb['next_observations'], acts, rng=key)
                _, pairkey = jax.random.split(key); pair = jax.random.randint(pairkey, (2,), 0, 10)
                target = tb['rewards'] + .9995*tb['masks']*targetq[pair].min(axis=0)
                result[f'td{h}_mae'] = float(np.abs(np.asarray(pred-target[None])).mean())
            result['q_mean'] = float(np.asarray(pred).mean())
            obs = jax.tree_util.tree_map(lambda x: x[:1024], tb['observations'])
            mode = learner.agent.sample_actions(obs, argmax=True)
            def objective(actions):
                return learner.agent.forward_critic(obs, actions, rng=key).mean(axis=0).sum()
            gradients = np.asarray(jax.grad(objective)(mode))
            assert np.isfinite(gradients).all()
            result['mode_q_gradient_abs_mean'] = np.abs(gradients).mean(axis=0).tolist()
            result['mode_public0_mean'] = float(np.asarray((mode[:, 0]+1)*.5).mean())
            result['mode_residual_abs_mean'] = float(np.abs(np.asarray(mode[:, 1:])).mean())
            assert digest(learner.state_dict()) == before
            return result

        initial = diagnose(); points = []; durations = []; losses = []
        for step in range(1, 2001):
            rows = ready[rng.integers(len(ready), size=65536)]
            draws_hash.update(rows.tobytes())
            start = time.perf_counter(); metrics = learner.update(select(rows, horizon))
            durations.append(time.perf_counter()-start); losses.append(float(metrics['serl/critic/critic_loss']))
            if step % 100 == 0:
                point = dict(outer_updates=step, critic_updates=step*8, **diagnose(), last100_critic_loss=float(np.mean(losses[-100:])), last100_outer_seconds=float(np.mean(durations[-100:])))
                points.append(point)
                write(args.output/f'horizon{horizon}_PROGRESS.json', dict(initial=initial, points=points))
                print(horizon, step, point['terminal_mae'], point['td1_mae'], point['td32_mae'], flush=True)
        final = learner.state_dict()
        assert final['num_gradient_steps'] - ck['learner']['num_gradient_steps'] == 16000
        assert digest(ck['learner']) == parent_digest and digest(ck['replay']) == replay_digest
        result = dict(horizon=horizon, initial=initial, initial_learner_digest=parent_digest, initial_replay_digest=replay_digest, sampled_rows_sha256=draws_hash.hexdigest(), final_sample_rng_digest=digest(rng.bit_generator.state), outer_updates=2000, critic_updates=16000, actor_updates=2000, sampled_rows=65536*2000, points=points, first_outer_seconds=durations[0], mean_outer_seconds_excluding_first=float(np.mean(durations[1:])), weights_saved=False)
        results.append(result); write(args.output/f'horizon{horizon}_RESULT.json', result)
        del learner
    assert results[0]['initial'] == results[1]['initial']
    assert results[0]['sampled_rows_sha256'] == results[1]['sampled_rows_sha256']
    assert results[0]['final_sample_rng_digest'] == results[1]['final_sample_rng_digest']
    assert sha(reg['checkpoint']['path']) == reg['checkpoint']['sha256']
    write(args.output/'REVIEW.json', dict(passed=True, checkpoint=reg['checkpoint'], results=results, total_critic_updates=32000, total_actor_updates=4000, new_physics=0, weights_saved=False, formal_state_unchanged=True, convergence_claim=False, limitation='Paired frozen replay probe from warm formal13; not physical task improvement or unbiased multistep calibration. Gradient magnitude alone does not establish useful direction. Formal14 remains unchanged. Shared GPU timings are not isolated throughput. No saved auxiliary state may be promoted.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args())
