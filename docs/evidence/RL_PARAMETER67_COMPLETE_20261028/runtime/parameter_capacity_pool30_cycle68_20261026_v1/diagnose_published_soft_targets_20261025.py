"""Read-only soft Bellman target and CHEQ mixing diagnostics on frozen states.

Average all uniformly sampled critic pairs, rather than selecting one favorable
pair. Policy-vs-replay action values are model predictions, not measured returns
or proof of extrapolation error. Bootstrap masks and finite-horizon terminal
semantics remain unchanged. No optimizer or physical environment is run.
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def summary(values):
    a = np.asarray(values, dtype=np.float64)
    if not a.size:
        return None
    if not np.isfinite(a).all():
        raise ValueError('Nonfinite diagnostic values')
    return dict(count=int(a.size), mean=float(a.mean()), minimum=float(a.min()),
                p50=float(np.median(a)), p95=float(np.percentile(a, 95)), maximum=float(a.max()))


def pair_minimum_expectation(q):
    """Exact expectation over uniform distinct critic pairs for each replay row."""
    q = np.asarray(q)
    if q.ndim != 2 or len(q) < 2:
        raise ValueError('Expected critics by transitions, at least two critics')
    return np.stack([np.minimum(q[i], q[j]) for i, j in combinations(range(len(q)), 2)]).mean(axis=0)


def target_terms(reward, done, future_q, log_pi, alpha, gamma):
    values = [np.asarray(v, dtype=np.float64) for v in (reward, done, future_q, log_pi)]
    if any(v.ndim != 1 or v.shape != values[0].shape for v in values):
        raise ValueError('Expected equally sized vectors; no broadcast allowed')
    reward, done, future_q, log_pi = values
    if not np.isin(done, [0, 1]).all():
        raise ValueError('Expected binary terminal mask')
    discount = (1-done)*gamma
    entropy = -discount*alpha*log_pi
    future = discount*future_q
    return dict(reward=reward, discounted_entropy=entropy, discounted_future_q=future,
                target=reward+entropy+future)


def main(args):
    protocol = json.loads(args.registration.read_text())
    if sha(__file__) != protocol['source_sha256']:
        raise ValueError('Diagnostic source differs from registration')
    os.sched_setaffinity(0, {protocol['cpu']})
    os.nice(19)  # CPU54 also hosts the already-running physical evaluator.
    torch.set_num_threads(1)
    root = Path(protocol['runtime'])
    for filename in ('RUNTIME.json', 'SOURCE_HASHES.json', 'CHEQ_HASHES.json'):
        if sha(root/filename) != protocol['runtime_hashes'][filename]:
            raise ValueError('Runtime manifest drift: '+filename)
    adapter = root/'source/tools/published_compliance_learner_20261025.py'
    hashes = json.loads((root/'SOURCE_HASHES.json').read_text())
    if sha(adapter) != hashes['tools/'+adapter.name]:
        raise ValueError('Frozen adapter drift')
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    out = Path(protocol['output'])
    out.mkdir(parents=True, exist_ok=False)
    result = dict(started_unix=time.time(), optimizer_updates=0, new_physical_transitions=0,
                  formal_state_changed=False, convergence_claim=False, snapshots=[])
    for item in protocol['snapshots']:
        if sha(item['checkpoint']) != item['sha256']:
            raise ValueError('Frozen checkpoint drift')
        checkpoint = torch.load(item['checkpoint'], map_location='cpu', weights_only=False)
        if (checkpoint['boundary'] != 'complete_condition_cycle'
                or checkpoint['cycle'] != item['cycle'] or checkpoint['controller'] != item['method']):
            raise ValueError('Not the registered complete-cycle checkpoint')
        state, arrays = checkpoint['learner'], checkpoint['replay']['arrays']
        learner = PublishedLearner(root, dimension=arrays['actions'].shape[1],
            direct=item['method'] == 'direct', seed=protocol['seed'], device=item['device'],
            algorithm=state['algorithm'], critic_layer_norm=state['critic_layer_norm'],
            numerical_amendments=state['numerical_amendments'])
        agent = learner.learner.agent
        agent.load_state_dict(state['agent'])
        gamma, alpha = learner.learner.gamma, float(state['alpha'])
        row = dict(method=item['method'], cycle=item['cycle'], steps=checkpoint['steps'],
            checkpoint_sha256=item['sha256'], alpha=alpha, gamma=gamma, groups={})
        rng = np.random.default_rng(protocol['seed'])
        ordinary = np.flatnonzero(arrays['dones'].reshape(-1) == 0)
        terminal = np.flatnonzero(arrays['dones'].reshape(-1) == 1)
        sample = rng.choice(ordinary, min(protocol['sample_size'], len(ordinary)), replace=False)
        def q_values(obs, act, target=False):
            if state['algorithm'] == 'cheq':
                values = [agent.get_q_value(obs, act, i, target=target).reshape(-1)
                          for i in range(agent.ensemble_size)]
            else:
                nets = [agent.qf1_target, agent.qf2_target] if target else [agent.qf1, agent.qf2]
                values = [net(obs, act).reshape(-1) for net in nets]
            return torch.stack(values).cpu().numpy()
        with torch.no_grad():
            for label, indices in [('nonterminal_sample', sample), ('all_terminal', terminal)]:
                if not len(indices):
                    row['groups'][label] = None
                    continue
                obs, nxt, act = [torch.as_tensor(arrays[k][indices], device=item['device'])
                    for k in ('observations', 'next_observations', 'actions')]
                replay_q = q_values(obs, act)
                policy_act, policy_log_pi = agent.get_action_and_log_prob(obs)
                policy_q = q_values(obs, policy_act)
                next_act, next_log_pi = agent.get_action_and_log_prob(nxt)
                next_q = q_values(nxt, next_act, target=True)
                terms = target_terms(arrays['rewards'][indices].reshape(-1),
                    arrays['dones'][indices].reshape(-1), pair_minimum_expectation(next_q),
                    next_log_pi.cpu().numpy().reshape(-1), alpha, gamma)
                metric = dict(count=len(indices), target_components={k: summary(v) for k, v in terms.items()},
                    replay_q=summary(replay_q), current_policy_q=summary(policy_q),
                    predicted_policy_minus_replay_pair_minimum=summary(
                        pair_minimum_expectation(policy_q)-pair_minimum_expectation(replay_q)),
                    policy_differential_entropy=summary(-policy_log_pi.cpu().numpy()),
                    next_policy_differential_entropy=summary(-next_log_pi.cpu().numpy()),
                    replay_actions_sha256=hashlib.sha256(arrays['actions'][indices].tobytes()).hexdigest(),
                    sampled_indices_sha256=hashlib.sha256(indices.tobytes()).hexdigest())
                td_error = abs(replay_q-terms['target'])
                if state['algorithm'] == 'cheq':
                    mask = arrays['masks'][indices].T.astype(bool)
                    metric['in_bag_td_absolute_error'] = summary(td_error[mask])
                    metric['out_of_bag_td_absolute_error'] = summary(td_error[~mask])
                    uncertainty = policy_q.std(axis=0, ddof=1)  # same correction as upstream torch.std
                    weight = np.clip((uncertainty-.2)/(.02-.2)*.8+.2, .2, 1.)
                    recorded_context = arrays['observations'][indices, -1]
                    metric.update(policy_ensemble_uncertainty=summary(uncertainty),
                        implied_next_mixing_weight=summary(weight),
                        implied_minimum_weight_fraction=float(np.mean(uncertainty >= .2)),
                        recorded_mixing_context=summary(recorded_context),
                        recorded_minimum_weight_fraction=float(np.mean(np.isclose(recorded_context, .2, atol=1e-7, rtol=0))))
                else:
                    metric['td_absolute_error'] = summary(td_error)
                if label == 'all_terminal' and not np.array_equal(terms['target'], terms['reward']):
                    raise AssertionError('Terminal bootstrap was not exactly zero')
                row['groups'][label] = metric
        if not all(torch.equal(v.cpu(), state['agent'][k].cpu()) for k, v in agent.state_dict().items()):
            raise AssertionError('Read-only diagnostic changed network weights')
        if any(p.grad is not None for p in agent.parameters()) or learner.learner.num_gradient_steps != 0:
            raise AssertionError('Unexpected gradient or optimizer update')
        row['network_state_unchanged'] = True
        result['snapshots'].append(row)
        (out/f"{item['method']}_cycle_{item['cycle']:05d}.json").write_text(json.dumps(row, indent=2, allow_nan=False)+'\n')
        print(json.dumps(dict(method=item['method'], cycle=item['cycle'], status='diagnosed')), flush=True)
        del learner, agent, checkpoint, arrays, state
        torch.cuda.empty_cache()
    result.update(finished_unix=time.time(), registration_sha256=sha(args.registration),
        limitations=[
            'Fixed replay samples; two complete cycles have different replay sizes and training histories.',
            'One stochastic policy action per sampled state, all critic pairs averaged exactly.',
            'Value differences are model predictions, not ground-truth action improvement or proof of bias.',
            'Recorded context is behavior-time context; implied weight uses the frozen current critic and sampled action.',
            'Terminal next observation is a storage placeholder with exactly zero bootstrap.',
            'Out-of-bag denotes bootstrap withholding, not unseen task evaluation.',
            'No convergence, final ranking, SPT reference or formal training change.'])
    (out/'SUMMARY.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args())
