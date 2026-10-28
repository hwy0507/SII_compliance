"""Paired, finite critic-only clock diagnosis on immutable CHEQ replay.

Not an online learner or policy evaluator: replay mixing contexts stay fixed.
The actor, alpha, physics and formal checkpoints are never changed. Both arms
have the same extra input/parameter count; the control receives zero there.
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
from torch import nn


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def known_clock(local_step, horizon=1375):
    step = np.asarray(local_step)
    if not np.issubdtype(step.dtype, np.integer) or np.any(step < 0) or np.any(step >= horizon):
        raise ValueError('Invalid known elapsed action index')
    return ((horizon-step)/horizon).astype(np.float32), ((horizon-step-1)/horizon).astype(np.float32)


def extend_critic(q):
    """Append one zero-initialized column after the original obs/action inputs."""
    net = copy.deepcopy(q.q_net)
    old = net[0]
    if not isinstance(old, nn.Linear):
        raise ValueError('Expected upstream Linear first layer')
    new = nn.Linear(old.in_features+1, old.out_features, bias=old.bias is not None,
                    device=old.weight.device, dtype=old.weight.dtype)
    with torch.no_grad():
        new.weight[:, :-1].copy_(old.weight)
        new.weight[:, -1].zero_()
        if old.bias is not None:
            new.bias.copy_(old.bias)
    net[0] = new
    net.requires_grad_(True)
    return net


def bellman(rewards, dones, minimum, log_pi, alpha, gamma):
    return rewards + (1-dones)*gamma*(minimum-alpha*log_pi)


def predict(nets, obs, actions, clock):
    x = torch.cat((obs, actions, clock[:, None]), dim=1)
    return torch.stack([net(x).flatten() for net in nets])


def main(args):
    p = json.loads(args.registration.read_text())
    if sha(__file__) != p['source_sha256']:
        raise ValueError('Frozen diagnostic source drift')
    for name, expected in p['support_source_hashes'].items():
        if sha(Path(__file__).with_name(name)) != expected:
            raise ValueError('Frozen diagnostic support source drift: '+name)
    item = p['methods'][args.method]
    os.sched_setaffinity(0, {item['cpu']})
    torch.set_num_threads(1)
    root = Path(p['runtime'])
    if sha(root/'RUNTIME.json') != p['runtime_sha256']:
        raise ValueError('Runtime manifest drift')
    for name, digest in json.loads((root/'SOURCE_HASHES.json').read_text()).items():
        if sha(root/'source'/name) != digest:
            raise ValueError('Frozen runtime source drift: '+name)
    for key in ('checkpoint', 'clock', 'clock_review'):
        if sha(item[key]) != item[key+'_sha256']:
            raise ValueError('Immutable input drift: '+key)
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    from validate_published_finite_check_20261025 import digest
    from diagnose_published_value_bound_20261025 import soft_upper_bound
    ck = torch.load(item['checkpoint'], map_location='cpu', weights_only=False)
    if (ck['controller'] != args.method or ck['cycle'] != 1 or
            ck['boundary'] != 'complete_condition_cycle' or
            ck['replay']['size'] != ck['steps'] or ck['replay']['cursor'] != ck['steps']):
        raise ValueError('Expected complete, unwrapped frozen cycle1 replay')
    arrays, state = ck['replay']['arrays'], ck['learner']
    replay_digest, state_digest = digest(ck['replay']), digest(state)
    clock = np.load(item['clock'], allow_pickle=False)
    current, nxt = known_clock(clock['local_step'])
    np.testing.assert_array_equal(current, clock['current_remaining_fraction'])
    np.testing.assert_array_equal(nxt, clock['next_remaining_fraction'])
    review = json.loads(Path(item['clock_review']).read_text())['methods'][args.method]
    if review['checkpoint_sha256'] != item['checkpoint_sha256']:
        raise ValueError('Clock provenance mismatch')
    train_ids = [i for i, ep in enumerate(review['episodes']) if ep['cycle'] == 0]
    test_ids = [i for i, ep in enumerate(review['episodes']) if ep['cycle'] == 1]
    if len(train_ids) != 30 or len(test_ids) != 30 or len(current) != ck['steps']:
        raise ValueError('Expected two complete 30-condition cycles')
    train = np.flatnonzero(np.isin(clock['episode_id'], train_ids))
    test = np.flatnonzero(np.isin(clock['episode_id'], test_ids))
    if len(train)+len(test) != len(current) or np.intersect1d(train, test).size:
        raise ValueError('Invalid probe-update/diagnostic partition')
    if p.get('fit_all_replay', False):
        train = np.arange(len(current))
    learner = PublishedLearner(root, dimension=arrays['actions'].shape[1], direct=args.method=='direct',
        seed=p['seeds'][0], device=p['device'], algorithm='cheq',
        critic_layer_norm=state['critic_layer_norm'], numerical_amendments=state['numerical_amendments'])
    agent = learner.learner.agent
    fresh_critics = copy.deepcopy(agent.ensemble.state_dict()) if p.get('fresh_critics', False) else None
    agent.load_state_dict(state['agent'])
    if fresh_critics is not None:
        agent.ensemble.load_state_dict(fresh_critics)
        agent.ensemble_targets.load_state_dict(fresh_critics)
    if not all(torch.equal(v.detach().cpu(), state['agent']['actor.'+k])
               for k, v in agent.actor.state_dict().items()):
        raise AssertionError('Frozen checkpoint actor mismatch')
    agent.requires_grad_(False)
    original_agent_digest = digest(agent.state_dict())
    alpha, gamma = float(state['alpha']), learner.learner.gamma
    data = {k: torch.as_tensor(v, device=p['device']) for k, v in arrays.items()}
    clocks = [torch.as_tensor(v, device=p['device']) for v in (current, nxt)]
    bound = float(soft_upper_bound(alpha, gamma, 1375, learner.spaces.action_space.low,
                                  learner.spaces.action_space.high))
    # Initial clock weights are exactly zero; arms start at the same function.
    initial = nn.ModuleList([extend_critic(q) for q in agent.ensemble])
    initial_targets = nn.ModuleList([extend_critic(q) for q in agent.ensemble_targets])
    initial_hash = digest(initial.state_dict())
    with torch.no_grad():
        ix = torch.as_tensor(train[:256], device=p['device'])
        ref = torch.stack([q(data['observations'][ix], data['actions'][ix]).flatten() for q in agent.ensemble])
        pred = predict(initial, data['observations'][ix], data['actions'][ix], clocks[0][ix])
        torch.testing.assert_close(pred, ref, rtol=2e-5, atol=2e-5)
    args.output.mkdir(exist_ok=False)
    selections = {}
    partitions = ([('fit_all_replay', train), ('replayed_cycle1', test)]
                  if p.get('fit_all_replay', False) else
                  [('fit_cycle0', train), ('probe_withheld_cycle1', test)])
    for name, indices in partitions:
        nonterminal = indices[arrays['dones'][indices, 0] == 0]
        sample = np.random.default_rng(715).choice(nonterminal, 4096, replace=False)
        terminal = indices[arrays['dones'][indices, 0] == 1]
        selections[name] = (sample, terminal)

    def diagnose(nets, targets, use_clock):
        result = {}
        with torch.random.fork_rng(devices=[torch.device(p['device']).index]), torch.no_grad():
            torch.manual_seed(10071)
            for name, (sample, terminal) in selections.items():
                ix = torch.as_tensor(sample, device=p['device'])
                ti = torch.as_tensor(terminal, device=p['device'])
                c = clocks[0] if use_clock else torch.zeros_like(clocks[0])
                nc = clocks[1] if use_clock else torch.zeros_like(clocks[1])
                q = predict(nets, data['observations'][ix], data['actions'][ix], c[ix])
                action, lp = agent.get_action_and_log_prob(data['next_observations'][ix])
                tq = predict(targets, data['next_observations'][ix], action, nc[ix])
                # Integrate over all ten equally likely random-two choices for
                # diagnostics only. Training still samples one original pair.
                expected_min = torch.stack([torch.minimum(tq[i], tq[j])
                    for i in range(5) for j in range(i+1, 5)]).mean(0)
                y = bellman(data['rewards'][ix, 0], data['dones'][ix, 0], expected_min,
                            lp.flatten(), alpha, gamma)
                term_q = predict(nets, data['observations'][ti], data['actions'][ti], c[ti])
                err = (term_q-data['rewards'][ti, 0]).abs()
                mask = data['masks'][ti].T.bool()
                result[name] = dict(q_mean=float(q.mean()), bellman_mae=float((q-y).abs().mean()),
                    terminal_mae=float(err.mean()), in_bag_terminal_mae=float(err[mask].mean()),
                    out_of_bag_terminal_mae=float(err[~mask].mean()),
                    above_global_bound_fraction=float((q > bound+.01).float().mean()),
                    terminal_count=len(terminal), sample_count=len(sample))
        return result

    results = []
    write(args.output/'STARTED.json', dict(pid=os.getpid(), source_sha256=sha(__file__),
        registration_sha256=sha(args.registration), checkpoint_sha256=item['checkpoint_sha256'],
        replay_sha256=replay_digest, actor_dimension=49, raw_observation_dimension=48,
        critic_initialization='fresh' if fresh_critics is not None else 'parent',
        frozen_actor_sha256=digest(agent.actor.state_dict()),
        new_physics=0, initial_critic_sha256=initial_hash, cpu=item['cpu'], device=p['device'],
        alpha=alpha, gamma=gamma, global_soft_upper_bound=bound, started_unix=time.time()))
    for seed in p['seeds']:
        sampling_hash = None
        for arm in p['arm_order'][args.method]:
            use_clock = arm == 'known_clock'
            nets, targets = copy.deepcopy(initial), copy.deepcopy(initial_targets)
            targets.requires_grad_(False)
            if digest(nets.state_dict()) != initial_hash:
                raise AssertionError('Unpaired initialization')
            optimizer = torch.optim.Adam(nets.parameters(), lr=p['learning_rate'])
            rng = np.random.default_rng(seed)
            torch.manual_seed(seed)
            c = clocks[0] if use_clock else torch.zeros_like(clocks[0])
            nc = clocks[1] if use_clock else torch.zeros_like(clocks[1])
            entry = dict(seed=seed, arm=arm, initial=diagnose(nets, targets, use_clock), curve=[])
            sampling = hashlib.sha256()
            for step in range(p['updates_per_arm']):
                indices = rng.choice(train, p['batch_size'], replace=True)
                pair = rng.choice(5, 2, replace=False)
                sampling.update(indices.tobytes()); sampling.update(pair.tobytes())
                ix = torch.as_tensor(indices, device=p['device'])
                with torch.no_grad():
                    action, lp = agent.get_action_and_log_prob(data['next_observations'][ix])
                    x = torch.cat((data['next_observations'][ix], action, nc[ix, None]), dim=1)
                    minimum = torch.minimum(targets[int(pair[0])](x), targets[int(pair[1])](x)).flatten()
                    y = bellman(data['rewards'][ix, 0], data['dones'][ix, 0], minimum,
                                lp.flatten(), alpha, gamma)
                q = predict(nets, data['observations'][ix], data['actions'][ix], c[ix])
                mask = data['masks'][ix].T
                if (mask.sum(1) == 0).any():
                    raise AssertionError('Empty ensemble mask')
                loss = (((q-y)**2*mask).sum(1)/mask.sum(1)).sum()
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()
                with torch.no_grad():
                    for target, source in zip(targets.parameters(), nets.parameters()):
                        target.mul_(1-p['tau']).add_(source, alpha=p['tau'])
                if (step+1) % p['record_every'] == 0:
                    if not torch.isfinite(loss) or not all(torch.isfinite(v).all() for v in nets.parameters()):
                        raise FloatingPointError('Nonfinite diagnostic critic')
                    row = dict(update=step+1, loss=float(loss), metrics=diagnose(nets, targets, use_clock),
                               updated_unix=time.time())
                    entry['curve'].append(row)
                    write(args.output/'PROGRESS.json', dict(method=args.method, seed=seed, arm=arm, **row))
            entry['sampling_sha256'] = sampling.hexdigest()
            if sampling_hash is not None and entry['sampling_sha256'] != sampling_hash:
                raise AssertionError('Unequal paired replay or critic-pair stream')
            sampling_hash = entry['sampling_sha256']
            entry['final'] = entry['curve'][-1]['metrics']
            results.append(entry)
            write(args.output/f'{seed}_{arm}.json', entry)
    if (digest(agent.state_dict()) != original_agent_digest or digest(state) != state_digest or
            digest(ck['replay']) != replay_digest or sha(item['checkpoint']) != item['checkpoint_sha256']):
        raise AssertionError('Frozen input/actor changed')
    write(args.output/'FINISHED.json', dict(method=args.method, results=results,
        registration_sha256=sha(args.registration), actor_and_replay_unchanged=True,
        critic_updates=len(results)*p['updates_per_arm'], actor_updates=0, new_physics=0,
        auxiliary_weights_saved=False, formal_training_changed=False, finished_unix=time.time(),
        limitations=p['limitations']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--method', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args)
    except BaseException as error:
        args.output.mkdir(exist_ok=True)
        write(args.output/'FAILURE.json', dict(error=repr(error), failed_unix=time.time()))
        raise
