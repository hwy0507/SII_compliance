"""Finite 1-vs-32-step SERL target study from formal clock cycle9.

Historical multi-step behavior returns have off-policy bias. No promotion,
physics, actor-input changes, or mutations of the authoritative replay.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temp.replace(path)


def derive(arrays, groups, horizon, gamma):
    n = len(arrays['rewards'])
    reward = np.zeros(n, np.float64)
    bootstrap = np.zeros(n, np.float32)
    endpoints = np.zeros(n, np.int64)
    lengths = np.zeros(n, np.int32)
    for ids in groups.values():
        ids = np.asarray(ids)
        for offset in range(horizon):
            count = len(ids)-offset
            if count <= 0:
                break
            reward[ids[:count]] += gamma**offset * arrays['rewards'][ids[offset:], 0]
        steps = np.minimum(horizon, len(ids)-np.arange(len(ids)))
        end = ids[np.arange(len(ids))+steps-1]
        endpoints[ids] = end
        lengths[ids] = steps
        bootstrap[ids] = (gamma**(steps-1)) * (1-arrays['dones'][end, 0])
    return dict(rewards=reward.astype(np.float32), bootstrap=bootstrap,
                endpoints=endpoints, lengths=lengths)


def main(args):
    os.sched_setaffinity(0, {0})
    torch.set_num_threads(1)
    reg = json.loads(args.registration.read_text())
    assert reg['outer_updates_per_arm'] == 2000 and reg['horizons'] == [1, 32]
    assert reg['record_every'] == 100 and reg['auxiliary_weights_promoted'] is False
    for name, h in reg['source_hashes'].items():
        assert sha(Path(__file__).with_name(name)) == h, name
    for item in [reg['checkpoint'], reg['review']]:
        assert sha(item['path']) == item['sha256']
    sys.path.insert(0, reg['adapter_runtime'])
    from serl_clock_state_adapter_20261026 import SerlClockLearner
    from validate_serl_state_20261026 import digest
    args.output.mkdir(exist_ok=False)
    ck = torch.load(reg['checkpoint']['path'], weights_only=False, map_location='cpu')
    assert ck['cycle'] == 9 and ck['boundary'] == 'complete_condition_cycle'
    review = json.loads(Path(reg['review']['path']).read_text())
    assert review['passed'] and review['methods']['direct']['checkpoint_sha256'] == reg['checkpoint']['sha256']
    initial, arrays = ck['learner'], ck['replay']['arrays']
    parent_digest, replay_digest = digest(initial), digest(ck['replay'])
    size = ck['replay']['size']
    assert size == 400935 and len(arrays['rewards']) == size
    groups, visited, journal_receipts = {}, np.zeros(size, bool), []
    for path in reg['journals']:
        rows = 0
        with Path(path).open() as f:
            for line in f:
                row = json.loads(line)
                i = row['step']-1
                assert 0 <= i < size and not visited[i]
                visited[i] = True
                assert np.float32(row['reward']) == arrays['rewards'][i, 0]
                assert bool(row['done']) == bool(arrays['dones'][i, 0])
                groups.setdefault((row['cycle'], row['condition']), []).append(i)
                rows += 1
        journal_receipts.append(dict(path=path, sha256=sha(path), rows=rows))
    assert visited.all() and len(groups) == 300
    for ids in groups.values():
        assert all(a < b for a, b in zip(ids, ids[1:]))
        assert arrays['dones'][ids[-1], 0] == 1 and arrays['dones'][ids[:-1]].sum() == 0
        np.testing.assert_array_equal(arrays['observations'][ids, 48],
                                      ((1375-np.arange(len(ids)))/1375).astype(np.float32))
        np.testing.assert_array_equal(arrays['next_observations'][ids, 48],
                                      ((1374-np.arange(len(ids)))/1375).astype(np.float32))
        np.testing.assert_array_equal(arrays['next_observations'][ids[:-1]], arrays['observations'][ids[1:]])
    gamma = .9995
    derived = {h: derive(arrays, groups, h, gamma) for h in reg['horizons']}
    np.testing.assert_array_equal(derived[1]['rewards'], arrays['rewards'][:, 0])
    np.testing.assert_array_equal(derived[1]['bootstrap'], 1-arrays['dones'][:, 0])
    np.testing.assert_array_equal(derived[1]['endpoints'], np.arange(size))
    # Independent scalar summation at every terminal-adjacent row and a random sample.
    selected = set(np.random.default_rng(27).choice(size, 1000, replace=False).tolist())
    for ids in groups.values():
        selected.update(ids[-33:])
        for j, i in enumerate(ids):
            if i not in selected:
                continue
            stop = min(j+32, len(ids))
            value = sum(float(arrays['rewards'][ids[k], 0])*gamma**(k-j) for k in range(j, stop))
            assert derived[32]['rewards'][i] == np.float32(value)
            assert derived[32]['endpoints'][i] == ids[stop-1]
            expected = 0. if stop == len(ids) else gamma**(stop-j-1)
            assert derived[32]['bootstrap'][i] == np.float32(expected)
    write(args.output/'REPLAY_GATE.json', dict(passed=True, rows=size, episodes=len(groups),
          journals=journal_receipts, scalar_checked=len(selected), original_replay_sha256=replay_digest,
          new_optimizer_updates=0, one_step_exact=True, clocks_and_adjacency_exact=True,
          derived_sha256={str(h): digest(d) for h, d in derived.items()}))
    terminals = np.flatnonzero(arrays['dones'][:, 0])
    sample = np.random.default_rng(reg['seed']).choice(np.flatnonzero(arrays['dones'][:, 0] == 0), 4096, replace=False)
    results = []
    for horizon in reg['horizons']:
        a = SerlClockLearner(Path(reg['runtime']), upstream=Path(reg['upstream']),
            upstream_manifest=Path(reg['upstream_manifest']), dimension=7, direct=True,
            seed=reg['seed'], device='cuda:0')
        a.load_state_dict(copy.deepcopy(initial))
        assert digest(a.state_dict()) == parent_digest
        jax = a.jax
        original_batch = a.batch
        def batch_adapter(values):
            result = original_batch(values)
            if '_bootstrap' in values:
                result['masks'] = jax.device_put(values['_bootstrap'])
            return result
        a.batch = batch_adapter
        def select(ids, h):
            d = derived[h]
            values = {k: v[ids] for k, v in arrays.items()}
            values['rewards'] = d['rewards'][ids, None]
            values['next_observations'] = arrays['next_observations'][d['endpoints'][ids]]
            values['_bootstrap'] = d['bootstrap'][ids]
            return values
        plain = original_batch({k: v[sample[:256]] for k, v in arrays.items()})
        transformed = a.batch(select(sample[:256], 1))
        assert digest(jax.device_get(plain)) == digest(jax.device_get(transformed))
        def diagnose():
            before = digest(a.state_dict())
            t = a.batch(select(terminals, 1))
            q = np.asarray(a.agent.forward_critic(t['observations'], t['actions'], rng=jax.random.PRNGKey(261)))
            error = abs(q-np.asarray(t['rewards'])[None])
            out = dict(terminal_mae=float(error.mean()), terminal_p95=float(np.percentile(error, 95)), terminal_max=float(error.max()))
            for h in reg['horizons']:
                s = a.batch(select(sample, h))
                key, ak = jax.random.split(jax.random.PRNGKey(262))
                actions, _ = a.agent._compute_next_actions(s, ak)
                tq = a.agent.forward_target_critic(s['next_observations'], actions, rng=key)
                target = s['rewards']+gamma*s['masks']*tq[jax.numpy.array([7, 3])].min(axis=0)
                pred = np.asarray(a.agent.forward_critic(s['observations'], s['actions'], rng=key))
                out['td_mae_'+str(h)] = float(abs(pred-np.asarray(target)[None]).mean())
            out.update(replay_q_mean=float(pred.mean()), replay_q_abs_p95=float(np.percentile(abs(pred), 95)),
                replay_q_min=float(pred.min()), replay_q_max=float(pred.max()), temperature=float(a.agent.forward_temperature()))
            assert digest(a.state_dict()) == before
            return out
        entry = dict(horizon=horizon, initial_full_state_sha256=parent_digest, initial=diagnose(), curve=[])
        rng = np.random.default_rng(reg['seed'])
        start = time.time()
        for update in range(reg['outer_updates_per_arm']):
            ids = rng.integers(size, size=32768)
            metrics = a.update(select(ids, horizon))
            if (update+1) % reg['record_every'] == 0:
                row = dict(outer_updates=update+1, critic_updates=8*(update+1), metrics=metrics, diagnostic=diagnose(), time=time.time())
                entry['curve'].append(row)
                write(args.output/'PROGRESS.json', dict(horizon=horizon, **row))
        assert a.learner.num_gradient_steps-initial['num_gradient_steps'] == 16000
        entry.update(final=diagnose(), elapsed_s=time.time()-start, sampling_rng_sha256=digest(rng.bit_generator.state))
        results.append(entry)
        write(args.output/('horizon'+str(horizon)+'.json'), entry)
    assert results[0]['initial'] == results[1]['initial']
    assert results[0]['sampling_rng_sha256'] == results[1]['sampling_rng_sha256']
    assert digest(initial) == parent_digest and digest(ck['replay']) == replay_digest
    assert sha(reg['checkpoint']['path']) == reg['checkpoint']['sha256']
    write(args.output/'FINISHED.json', dict(passed=True, results=results,
        checkpoint_sha256=reg['checkpoint']['sha256'], registration_sha256=sha(args.registration),
        new_physics=0, auxiliary_critic_updates=32000, auxiliary_actor_updates=4000,
        auxiliary_weights_saved=False, parent_unchanged=True,
        limitations=['Historical off-policy n-step return is biased for the current policy; no importance correction.',
                    'No online task, safety, convergence, or formal GPU utilization conclusion.',
                    'All initial optimizer state and official 10/2/noentropy/8:1 preserved; only critic target horizon differs.']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args)
    except BaseException as error:
        args.output.mkdir(exist_ok=True)
        write(args.output/'FAILURE.json', dict(error=repr(error)))
        raise
