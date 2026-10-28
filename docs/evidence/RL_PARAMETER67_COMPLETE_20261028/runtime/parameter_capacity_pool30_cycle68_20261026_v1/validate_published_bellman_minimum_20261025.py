"""Two real-network updates validating a registered Bellman-only candidate."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
import torch

from published_bellman_minimum_20261025 import install_bellman_minimum
from validate_published_finite_check_20261025 import digest


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(args):
    p = json.loads(args.registration.read_text())
    for name, expected in p['source_hashes'].items():
        if sha(Path(__file__).with_name(name)) != expected:
            raise ValueError('Preflight source drift')
    if sha(p['checkpoint']) != p['checkpoint_sha256']:
        raise ValueError('Parent checkpoint drift')
    os.sched_setaffinity(0, {p['cpu']})
    torch.set_num_threads(1)
    root = Path(p['runtime'])
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    ck = torch.load(p['checkpoint'], map_location='cpu', weights_only=False)
    state, arrays = ck['learner'], ck['replay']['arrays']
    if ck['cycle'] != 9 or ck['boundary'] != 'complete_condition_cycle':
        raise ValueError('Expected complete cycle9')
    original_digest = digest(state)
    indices = np.r_[np.flatnonzero(arrays['dones'][:, 0] == 0)[:120],
                    np.flatnonzero(arrays['dones'][:, 0] == 1)[:8]]
    batch = {k: v[indices].copy() for k, v in arrays.items()}
    learner = PublishedLearner(root, dimension=arrays['actions'].shape[1], direct=True,
        seed=p['seed'], device=p['device'], algorithm='cheq',
        critic_layer_norm=state['critic_layer_norm'], numerical_amendments=state['numerical_amendments'])
    original_train = learner.learner.train
    tensors = {k: torch.as_tensor(v, device=p['device']) for k, v in batch.items()}
    results, targets = [], []
    for count in (2, 5):
        learner.learner.train = original_train
        learner.load_state_dict(copy.deepcopy(state))
        for parameter in learner.learner.agent.parameters():
            parameter.grad = None
        receipt = install_bellman_minimum(learner.learner, count)
        if count == 2 and learner.learner.train != original_train:
            raise AssertionError('Pair baseline must preserve the exact bound method')
        agent = learner.learner.agent
        with torch.no_grad():
            pair = np.random.choice(5, size=2, replace=False)
            action, log_pi = agent.get_action_and_log_prob(tensors['next_observations'])
            q = torch.stack([agent.get_q_value(tensors['next_observations'], action, i, target=True)
                             for i in range(5)])
            selected = torch.minimum(q[pair[0]], q[pair[1]]) if count == 2 else q.amin(dim=0)
            target = tensors['rewards'].flatten() + (1-tensors['dones'].flatten()) * learner.learner.gamma * (
                selected - learner.learner.alpha*log_pi).view(-1)
            loss = torch.tensor(0., device=p['device'])
            for i in range(5):
                pred = agent.get_q_value(tensors['observations'], tensors['actions'], i).view(-1)
                mask = tensors['masks'][:, i]
                loss = loss + ((pred-target).square()*mask).sum()/mask.sum()
            expected = float(loss)
            targets.append(target.cpu().numpy())
        # Restore weights, Adam state and RNG consumed by the independent expectation.
        learner.load_state_dict(copy.deepcopy(state))
        metrics = learner.update(batch)
        if metrics['agent_train/q_loss'] != expected:
            raise AssertionError('Actual learner loss differs from independent target/mask calculation')
        if learner.learner.num_gradient_steps != state['num_gradient_steps']+1:
            raise AssertionError('Unexpected update count')
        if digest(state) != original_digest:
            raise AssertionError('Original learner state mutated')
        results.append(dict(count=count, expected_q_loss=expected,
            actual_q_loss=metrics['agent_train/q_loss'], patch=receipt,
            independent_loss_exact=True))
    terminal = batch['dones'][:, 0] == 1
    if not np.array_equal(targets[0][terminal], batch['rewards'][terminal, 0]):
        raise AssertionError('Pair terminal bootstrap changed')
    if not np.array_equal(targets[1][terminal], batch['rewards'][terminal, 0]):
        raise AssertionError('All-five terminal bootstrap changed')
    if np.any(targets[1] > targets[0]):
        raise AssertionError('All-five target exceeded sampled pair target at matched state/RNG')
    if sha(p['checkpoint']) != p['checkpoint_sha256']:
        raise AssertionError('Parent checkpoint changed')
    Path(p['output']).write_text(json.dumps(dict(results=results, auxiliary_updates=2,
        new_physics=0, parent_unchanged=True, auxiliary_weights_saved=False,
        terminal_targets_exact=True, all_five_target_never_larger=True,
        registration_sha256=sha(args.registration)), indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args())
