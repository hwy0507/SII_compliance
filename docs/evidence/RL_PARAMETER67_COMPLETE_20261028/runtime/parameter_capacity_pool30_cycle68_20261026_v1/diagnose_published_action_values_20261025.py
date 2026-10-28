"""Frozen-state action preferences and CHEQ uncertainty, with no optimizer.

Evaluate both checkpoints on identical replay observations and candidate actions.
Removing each critic's action-mean is diagnostic only: it is NOT a replacement
uncertainty rule, an advantage calibration, or evidence of actual action quality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stats(value):
    value = np.asarray(value, dtype=np.float64)
    if not value.size or not np.isfinite(value).all():
        raise ValueError('Expected nonempty finite diagnostic')
    return dict(mean=float(value.mean()), p50=float(np.median(value)),
                p95=float(np.percentile(value, 95)), maximum=float(value.max()))


def decompose(q):
    """Critics x states x candidate actions; exact variance decomposition."""
    q = np.asarray(q, dtype=np.float64)
    if q.ndim != 3 or q.shape[0] < 2 or not np.isfinite(q).all():
        raise ValueError('Expected finite critics x states x candidates')
    offset = q.mean(axis=2, keepdims=True)
    centered = q-offset
    total = q.var(axis=0, ddof=1).mean(axis=1)
    between_offsets = offset[:, :, 0].var(axis=0, ddof=1)
    action_variance = centered.var(axis=0, ddof=1).mean(axis=1)
    np.testing.assert_allclose(total, between_offsets+action_variance, rtol=1e-9, atol=1e-9)
    return dict(total_ensemble_variance=stats(total),
        action_mean_offset_variance=stats(between_offsets),
        centered_action_variance=stats(action_variance),
        aggregate_offset_variance_fraction=(float(between_offsets.sum()/total.sum())
                                           if total.sum() else None),
        raw_uncertainty=stats(q.std(axis=0, ddof=1)),
        centered_uncertainty=stats(centered.std(axis=0, ddof=1)),
        raw_uncertainty_ge_point2_fraction=float(np.mean(q.std(axis=0, ddof=1) >= .2)),
        centered_uncertainty_ge_point2_fraction=float(np.mean(centered.std(axis=0, ddof=1) >= .2)))


def main(args):
    registration = json.loads(args.registration.read_text())
    if sha(__file__) != registration['source_sha256']:
        raise ValueError('Diagnostic source drift')
    os.sched_setaffinity(0, {registration['cpu']})
    os.nice(10)
    torch.set_num_threads(1)
    root = Path(registration['runtime'])
    for name, digest in registration['runtime_hashes'].items():
        if sha(root/name) != digest:
            raise ValueError('Runtime manifest drift')
    adapter = root/'source/tools/published_compliance_learner_20261025.py'
    if sha(adapter) != json.loads((root/'SOURCE_HASHES.json').read_text())['tools/'+adapter.name]:
        raise ValueError('Adapter drift')
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    out = Path(registration['output'])
    out.mkdir(parents=True, exist_ok=False)
    result = dict(started_unix=time.time(), optimizer_updates=0, physical_transitions=0,
        formal_state_changed=False, convergence_claim=False, methods={})
    for item in registration['methods']:
        states = []
        for snapshot in item['snapshots']:
            if sha(snapshot['path']) != snapshot['sha256']:
                raise ValueError('Checkpoint drift')
            ck = torch.load(snapshot['path'], map_location='cpu', weights_only=False)
            if (ck['boundary'] != 'complete_condition_cycle' or ck['cycle'] != snapshot['cycle']
                    or ck['controller'] != item['method'] or ck['learner']['algorithm'] != 'cheq'):
                raise ValueError('Unexpected checkpoint identity')
            states.append(ck)
        early, late = states
        arrays = early['replay']['arrays']
        for key in arrays:
            if not np.array_equal(arrays[key], late['replay']['arrays'][key][:len(arrays[key])]):
                raise ValueError('Replay prefix changed: '+key)
        # Most recent complete cycle in the earlier checkpoint, excluding terminals.
        lower = int(early['cycles'][-2]['steps'])
        available = np.flatnonzero(arrays['dones'].reshape(-1) == 0)
        available = available[available >= lower]
        rng = np.random.default_rng(registration['seed'])
        indices = rng.choice(available, min(registration['sample_size'], len(available)), replace=False)
        if not len(indices):
            raise ValueError('No registered common states')
        device = item['device']
        obs = torch.as_tensor(arrays['observations'][indices], device=device)
        replay_action = torch.as_tensor(arrays['actions'][indices], device=device)
        learners, candidates, names = [], [replay_action, torch.zeros_like(replay_action)], ['replay', 'nominal_zero']
        for ck in states:
            st = ck['learner']
            learner = PublishedLearner(root, dimension=replay_action.shape[1], direct=item['method']=='direct',
                seed=registration['seed'], device=device, algorithm='cheq',
                critic_layer_norm=st['critic_layer_norm'], numerical_amendments=st['numerical_amendments'])
            learner.learner.agent.load_state_dict(st['agent'])
            learners.append(learner)
            with torch.no_grad():
                candidates.append(learner.learner.agent.get_action(obs, deterministic=True))
                names.append('cycle_'+str(ck['cycle'])+'_deterministic')
                for i in range(registration['stochastic_actions_per_policy']):
                    candidates.append(learner.learner.agent.get_action_and_log_prob(obs)[0])
                    names.append('cycle_'+str(ck['cycle'])+'_sample_'+str(i))
        acts = torch.stack(candidates, dim=1)
        low = torch.as_tensor(learners[0].spaces.action_space.low, device=device)
        high = torch.as_tensor(learners[0].spaces.action_space.high, device=device)
        if not bool(((acts >= low-1e-6) & (acts <= high+1e-6)).all()):
            raise ValueError('Candidate action outside interface')
        obs_many = obs[:, None, :].expand(-1, len(names), -1).reshape(-1, obs.shape[1])
        act_many = acts.reshape(-1, acts.shape[-1])
        row = dict(common_replay_prefix_exact=True, sample_count=len(indices),
            sampled_indices_sha256=hashlib.sha256(indices.tobytes()).hexdigest(),
            candidate_actions_sha256=hashlib.sha256(acts.cpu().numpy().tobytes()).hexdigest(),
            candidate_names=names, snapshots=[])
        for ck, learner in zip(states, learners):
            agent = learner.learner.agent
            snapshot = dict(cycle=ck['cycle'], steps=ck['steps'], critics={})
            with torch.no_grad():
                for target in (False, True):
                    q = torch.stack([agent.get_q_value(obs_many, act_many, i, target=target).reshape(len(indices), len(names))
                                     for i in range(agent.ensemble_size)]).cpu().numpy()
                    metric = decompose(q)
                    metric['candidate_values'] = {}
                    for i, name in enumerate(names):
                        advantage = q[:, :, i]-q[:, :, 0]
                        metric['candidate_values'][name] = dict(q=stats(q[:, :, i]),
                            predicted_minus_replay=stats(advantage),
                            critics_positive_advantage_fraction=float(np.mean(advantage > 0)),
                            all_critics_positive_fraction=float(np.mean((advantage > 0).all(axis=0))),
                            all_critics_negative_fraction=float(np.mean((advantage < 0).all(axis=0))))
                    best = q.argmax(axis=2)
                    metric['all_critics_same_best_candidate_fraction'] = float(np.mean((best == best[0]).all(axis=0)))
                    snapshot['critics']['target' if target else 'online'] = metric
            if any(p.grad is not None for p in agent.parameters()) or learner.learner.num_gradient_steps != 0:
                raise AssertionError('Unexpected training')
            if not all(torch.equal(v.cpu(), ck['learner']['agent'][k]) for k, v in agent.state_dict().items()):
                raise AssertionError('Weights changed')
            snapshot['network_state_unchanged'] = True
            row['snapshots'].append(snapshot)
        result['methods'][item['method']] = row
        (out/(item['method']+'.json')).write_text(json.dumps(row, indent=2, allow_nan=False)+'\n')
        print(json.dumps(dict(method=item['method'], status='diagnosed')), flush=True)
        del learners, states, early, late, arrays, learner, agent, ck
        torch.cuda.empty_cache()
    result.update(finished_unix=time.time(), registration_sha256=sha(args.registration), limitations=[
        'Predicted action preferences have no ground-truth counterfactual returns.',
        'Candidate set is finite, with equal candidate weighting; decomposition depends on that set.',
        'Per-critic centering is diagnostic only and is not used by the running CHEQ controller.',
        'Raw policy actions are evaluated with recorded mixing context, not as executed unmixed actions.',
        'One earlier-cycle replay cohort; no unseen-task evaluation, formal algorithm change, or convergence claim.'])
    (out/'SUMMARY.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args())
