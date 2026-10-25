"""Finite Bellman-discount sensitivity on fixed real replay and learner states.

Changes only learner gamma in isolated auxiliary arms, retaining stored rewards
(including shaping formed with gamma .9995). This deliberately probes target
sensitivity; it is not a valid reproduction with a consistently changed shaped
objective, fresh training, online policy comparison, or convergence evidence.
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

from validate_published_finite_check_20261025 import digest


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def main(args):
    protocol = json.loads(args.registration.read_text())
    if sha(__file__) != protocol['source_sha256']:
        raise ValueError('Frozen diagnostic source drift')
    os.sched_setaffinity(0, {protocol['cpus'][args.controller]})
    os.nice(protocol['nice'])
    if sha(Path(__file__).with_name('validate_published_finite_check_20261025.py')) != protocol['digest_helper_sha256']:
        raise ValueError('Frozen state-digest helper drift')
    torch.set_num_threads(1)
    item = protocol['checkpoints'][args.controller]
    if sha(item['path']) != item['sha256']:
        raise ValueError('Frozen complete-cycle checkpoint drift')
    checkpoint = torch.load(item['path'], map_location='cpu', weights_only=False)
    if checkpoint['controller'] != args.controller or checkpoint['boundary'] != 'complete_condition_cycle':
        raise ValueError('Expected same-controller complete-cycle checkpoint')
    root = Path(protocol['runtime'])
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    state, arrays = checkpoint['learner'], checkpoint['replay']['arrays']
    original_state_digest = digest(state)
    learner = PublishedLearner(root, dimension=arrays['actions'].shape[1], direct=args.controller == 'direct',
        seed=protocol['seed'], device=args.device, algorithm=state['algorithm'],
        critic_layer_norm=state['critic_layer_norm'], numerical_amendments=state['numerical_amendments'])
    terminal = np.flatnonzero(arrays['dones'].reshape(-1) == 1)
    ordinary = np.flatnonzero(arrays['dones'].reshape(-1) == 0)
    sample = np.random.default_rng(protocol['seed']).choice(ordinary, 4096, replace=False)
    args.output.mkdir(parents=True, exist_ok=False)

    def diagnose():
        agent = learner.learner.agent
        with torch.no_grad():
            obs = torch.as_tensor(arrays['observations'][terminal], device=args.device)
            act = torch.as_tensor(arrays['actions'][terminal], device=args.device)
            q = torch.stack([agent.get_q_value(obs, act, i) for i in range(agent.ensemble_size)]).squeeze(-1)
            reward = torch.as_tensor(arrays['rewards'][terminal].reshape(-1), device=args.device)
            error = abs(q-reward)
            mask = torch.as_tensor(arrays['masks'][terminal].T, device=args.device).bool()
            obs = torch.as_tensor(arrays['observations'][sample], device=args.device)
            act = torch.as_tensor(arrays['actions'][sample], device=args.device)
            ordinary_q = torch.stack([agent.get_q_value(obs, act, i) for i in range(agent.ensemble_size)])
            return dict(terminal_mae=float(error.mean()), in_bag_mae=float(error[mask].mean()),
                out_of_bag_mae=float(error[~mask].mean()), ordinary_replay_q_mean=float(ordinary_q.mean()),
                ordinary_replay_q_std=float(ordinary_q.std()), alpha=float(learner.learner.alpha))

    results, initial_reference, initial_digest_reference = [], None, None
    for gamma in protocol['discounts'][args.controller]:
        batch_size = protocol['batch_size']
        learner.load_state_dict(copy.deepcopy(state))
        for parameter in learner.learner.agent.parameters():
            parameter.grad = None
        initial_state_digest = digest(learner.state_dict())
        learner.learner.gamma = gamma
        rng = np.random.default_rng(protocol['seed'])
        initial = diagnose()
        if initial_reference is None:
            initial_reference = initial
            initial_digest_reference = initial_state_digest
        elif initial != initial_reference or initial_state_digest != initial_digest_reference:
            raise AssertionError('Variants did not start from identical diagnostic state')
        start = time.time()
        with (args.output/f'gamma_{gamma}.jsonl').open('x', buffering=1) as log:
            for update in range(protocol['updates_per_variant']):
                indices = rng.integers(len(arrays['rewards']), size=batch_size)
                metrics = learner.update({k: v[indices] for k, v in arrays.items()})
                if (update+1) % 100 == 0:
                    row = dict(gamma=gamma, batch_size=batch_size, updates=update+1, metrics=metrics,
                        diagnostic=diagnose(), updated_unix=time.time())
                    log.write(json.dumps(row, allow_nan=False)+'\n')
                    write(args.output/'PROGRESS.json', row)
        if learner.learner.num_gradient_steps-state['num_gradient_steps'] != protocol['updates_per_variant']:
            raise AssertionError('Incorrect diagnostic update budget')
        weights = args.output/f'gamma_{gamma}_auxiliary_learner.pt'
        torch.save(dict(learner=learner.state_dict(), auxiliary_bellman_gamma=gamma, stored_shaping_gamma=.9995, formal_comparison_eligible=False), weights)
        if digest(state) != original_state_digest:
            raise AssertionError('Auxiliary arm mutated original parent state')
        results.append(dict(gamma=gamma, terminal_discount_after_1374_steps=gamma**1374,
            initial_state_sha256=initial_state_digest, parent_state_unchanged=True, batch_size=batch_size, initial=initial, final=row,
            sampled_rows=batch_size*protocol['updates_per_variant'], elapsed_s=time.time()-start,
            auxiliary_weights_sha256=sha(weights)))
    write(args.output/'FINISHED.json', dict(controller=args.controller, results=results,
        checkpoint_sha256=item['sha256'], registration_sha256=sha(args.registration),
        source_sha256=sha(__file__), fresh_networks=False, new_physical_transitions=0,
        formal_policy_changed=False, convergence_claim=False,
        limitation='Offline moving-target Bellman-discount sensitivity, equal updates and sampled-row budgets. '
                   'Stored rewards retain original .9995 shaping; no consistent alternate-objective reproduction, '
                   'fresh-network, online-performance or algorithm-selection conclusion'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--controller', required=True)
    parser.add_argument('--device', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args)
    except BaseException as error:
        args.output.mkdir(parents=True, exist_ok=True)
        write(args.output/'FAILURE.json', dict(error=repr(error)))
        raise
