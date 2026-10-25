"""Finite critic-only diagnostic with fixed Bellman labels on real replay.

Compare uniform sampling and registered terminal oversampling. Actor, alpha and
Bellman labels stay fixed; no physics, policy claim or formal checkpoint update.
This isolates fitting/weighting from moving bootstrapped targets, not online
performance or proof that a different replay distribution is better for RL.
"""
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


def write(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def main(args):
    torch.set_num_threads(1)
    protocol = json.loads(args.registration.read_text())
    os.sched_setaffinity(0, {protocol['cpu']})
    if sha(__file__) != protocol['source_sha256']:
        raise ValueError('Registered diagnostic source drift')
    path = Path(protocol['checkpoints'][args.controller]['path'])
    if sha(path) != protocol['checkpoints'][args.controller]['sha256']:
        raise ValueError('Immutable complete-cycle checkpoint changed')
    root = Path(protocol['runtime'])
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner, assert_finite_parameters
    checkpoint = torch.load(path, map_location='cpu', weights_only=False)
    if checkpoint['controller'] != args.controller or checkpoint['boundary'] != 'complete_condition_cycle':
        raise ValueError('Expected the registered complete-cycle interface snapshot')
    state, arrays = checkpoint['learner'], checkpoint['replay']['arrays']
    learner = PublishedLearner(root, dimension=arrays['actions'].shape[1], direct=args.controller == 'direct',
        seed=protocol['seed'], device=args.device, algorithm=state['algorithm'],
        critic_layer_norm=state['critic_layer_norm'], numerical_amendments=state['numerical_amendments'])
    learner.load_state_dict(state)
    agent = learner.learner.agent
    if state['algorithm'] != 'cheq':
        raise ValueError('This registered diagnostic requires the five-critic ensemble')
    torch.manual_seed(protocol['seed'])
    labels = np.empty_like(arrays['rewards'])
    with torch.no_grad():
        for start in range(0, len(labels), 8192):
            end = min(start+8192, len(labels))
            obs = torch.as_tensor(arrays['next_observations'][start:end], device=args.device)
            action, log_pi = agent.get_action_and_log_prob(obs)
            target = torch.minimum(agent.get_q_value(obs, action, 0, target=True),
                agent.get_q_value(obs, action, 1, target=True))-float(state['alpha'])*log_pi
            labels[start:end] = arrays['rewards'][start:end]+(1-arrays['dones'][start:end])*.9995*target.cpu().numpy()
    args.output.mkdir(parents=True, exist_ok=False)
    np.save(args.output/'fixed_bellman_labels.npy', labels)
    terminal = np.flatnonzero(arrays['dones'].reshape(-1) == 1)
    ordinary = np.flatnonzero(arrays['dones'].reshape(-1) == 0)
    if not len(terminal) or not np.array_equal(labels[terminal], arrays['rewards'][terminal]):
        raise ValueError('Terminal labels must equal unbootstrapped rewards')
    diagnostic = np.random.default_rng(protocol['seed']).choice(ordinary, min(4096, len(ordinary)), replace=False)

    def errors(indices):
        with torch.no_grad():
            obs = torch.as_tensor(arrays['observations'][indices], device=args.device)
            action = torch.as_tensor(arrays['actions'][indices], device=args.device)
            q = torch.stack([agent.get_q_value(obs, action, i) for i in range(agent.ensemble_size)])
            target = torch.as_tensor(labels[indices], device=args.device)
            return float((q-target).abs().mean())

    def terminal_mask_errors():
        with torch.no_grad():
            obs = torch.as_tensor(arrays['observations'][terminal], device=args.device)
            action = torch.as_tensor(arrays['actions'][terminal], device=args.device)
            q = torch.stack([agent.get_q_value(obs, action, i) for i in range(agent.ensemble_size)])
            target = torch.as_tensor(labels[terminal], device=args.device)
            error = (q-target).abs().squeeze(-1)
            mask = torch.as_tensor(arrays['masks'][terminal].T, device=args.device).bool()
            if error.shape != mask.shape:
                raise ValueError('Terminal prediction/mask shape mismatch')
            result = {}
            for name, selected in [('in_bag', mask), ('out_of_bag', ~mask)]:
                count = int(selected.sum())
                result[name] = dict(count=count,
                    mae=float(error[selected].mean()) if count else None)
            return result

    results = []
    for fraction in protocol['terminal_sampling_fractions']:
        learner.load_state_dict(state)
        rng = np.random.default_rng(protocol['seed'])
        initial = dict(terminal_mae=errors(terminal), ordinary_fixed_label_mae=errors(diagnostic),
            terminal_mask_errors=terminal_mask_errors())
        name = 'uniform' if fraction == 0 else 'terminal_'+str(int(100*fraction))+'pct'
        with (args.output/(name+'.jsonl')).open('x', buffering=1) as log:
            for update in range(protocol['updates_per_variant']):
                count = protocol['batch_size']
                if fraction:
                    n = int(count*fraction)
                    index = np.r_[rng.choice(terminal, n), rng.choice(ordinary, count-n)]
                else:
                    index = rng.integers(len(labels), size=count)
                obs = torch.as_tensor(arrays['observations'][index], device=args.device)
                action = torch.as_tensor(arrays['actions'][index], device=args.device)
                target = torch.as_tensor(labels[index], device=args.device)
                masks = torch.as_tensor(arrays['masks'][index], device=args.device)
                losses = []
                for i in range(agent.ensemble_size):
                    error = (agent.get_q_value(obs, action, i)-target).square().reshape(-1)
                    losses.append((error*masks[:, i]).sum()/masks[:, i].sum())
                loss = torch.stack(losses).sum()
                learner.learner.q_optimizer.zero_grad()
                loss.backward()
                learner.learner.q_optimizer.step()
                assert_finite_parameters(agent)
                if (update+1) % 100 == 0:
                    row = dict(variant=name, updates=update+1, loss=float(loss.detach()),
                        terminal_mae=errors(terminal), ordinary_fixed_label_mae=errors(diagnostic),
                        terminal_mask_errors=terminal_mask_errors(),
                        updated_unix=time.time())
                    log.write(json.dumps(row, allow_nan=False)+'\n')
                    write(args.output/'PROGRESS.json', row)
        unchanged = all(torch.equal(value.detach().cpu(), state['agent'][key].cpu())
            for key, value in agent.state_dict().items() if not key.startswith('ensemble.'))
        if not unchanged or not torch.equal(learner.learner.log_alpha.detach().cpu(), state['log_alpha'].cpu()):
            raise AssertionError('Fixed actor, targets or temperature unexpectedly changed')
        # Auxiliary critic weights are archived for diagnosis only; never used
        # as a policy continuation or silently merged into formal training.
        weights = args.output/(name+'_auxiliary_critics.pt')
        torch.save({k: v.detach().cpu() for k, v in agent.state_dict().items()
                    if k.startswith('ensemble.')}, weights)
        results.append(dict(name=name, initial=initial, final=row,
            auxiliary_critic_weights_sha256=sha(weights),
            actor_targets_temperature_exact=True))
    write(args.output/'FINISHED.json', dict(controller=args.controller, results=results,
        checkpoint_sha256=sha(path), fixed_labels_sha256=sha(args.output/'fixed_bellman_labels.npy'),
        source_sha256=sha(__file__), registration_sha256=sha(args.registration),
        terminal_rows=len(terminal), total_rows=len(labels),
        target_pair='frozen critics0/1; one sampled next action per replay row',
        actor_temperature_and_targets_updated=False, formal_policy_weights_changed=False,
        scope='in_sample_fixed_label_critic_fitting_only', convergence_claim=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--controller', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', required=True)
    args = parser.parse_args()
    try:
        main(args)
    except BaseException as error:
        args.output.mkdir(parents=True, exist_ok=True)
        write(args.output/'FAILURE.json', dict(error=repr(error), source_sha256=sha(__file__)))
        raise
