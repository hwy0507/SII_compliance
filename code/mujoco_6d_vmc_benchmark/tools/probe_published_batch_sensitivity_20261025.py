"""Finite batch-size sensitivity on frozen real replay and saved learner state.

Each variant restores the same actor, critics, targets, optimizers, alpha and RNG.
Equal optimizer updates are not equal sampled-row budgets or online experience.
This diagnostic cannot establish a superior online policy or change live runs.
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
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def main(args):
    protocol = json.loads(args.registration.read_text())
    if sha(__file__) != protocol['source_sha256']:
        raise ValueError('Frozen diagnostic source drift')
    os.sched_setaffinity(0, {protocol['cpu']})
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

    results, initial_reference = [], None
    for batch_size in protocol['batch_sizes'][args.controller]:
        learner.load_state_dict(copy.deepcopy(state))
        rng = np.random.default_rng(protocol['seed'])
        initial = diagnose()
        if initial_reference is None:
            initial_reference = initial
        elif initial != initial_reference:
            raise AssertionError('Variants did not start from identical diagnostic state')
        start = time.time()
        with (args.output/f'batch_{batch_size}.jsonl').open('x', buffering=1) as log:
            for update in range(protocol['updates_per_variant']):
                indices = rng.integers(len(arrays['rewards']), size=batch_size)
                metrics = learner.update({k: v[indices] for k, v in arrays.items()})
                if (update+1) % 100 == 0:
                    row = dict(batch_size=batch_size, updates=update+1, metrics=metrics,
                        diagnostic=diagnose(), updated_unix=time.time())
                    log.write(json.dumps(row, allow_nan=False)+'\n')
                    write(args.output/'PROGRESS.json', row)
        if learner.learner.num_gradient_steps-state['num_gradient_steps'] != protocol['updates_per_variant']:
            raise AssertionError('Incorrect diagnostic update budget')
        weights = args.output/f'batch_{batch_size}_auxiliary_learner.pt'
        torch.save(learner.state_dict(), weights)
        results.append(dict(batch_size=batch_size, initial=initial, final=row,
            sampled_rows=batch_size*protocol['updates_per_variant'], elapsed_s=time.time()-start,
            auxiliary_weights_sha256=sha(weights)))
    write(args.output/'FINISHED.json', dict(controller=args.controller, results=results,
        checkpoint_sha256=item['sha256'], registration_sha256=sha(args.registration),
        source_sha256=sha(__file__), fresh_networks=False, new_physical_transitions=0,
        formal_policy_changed=False, convergence_claim=False,
        limitation='Offline moving-target full-learner sensitivity, equal updates but unequal sampled rows; '
                   'no UTD or downstream online-performance conclusion'))


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
