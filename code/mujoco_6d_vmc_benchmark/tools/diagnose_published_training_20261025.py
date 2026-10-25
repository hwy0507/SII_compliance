"""Read-only diagnostics for live published-controller training.

Snapshot each atomic checkpoint before reading. Terminal Q calibration is
reported separately from the mean replay TD loss so sparse terminal errors
cannot disappear in the aggregate. These are diagnostics, not convergence gates.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

import numpy as np
import torch


def read_rows(path):
    if not path.exists():
        return []
    raw = path.read_bytes()
    # Concurrent append may expose one incomplete final line. Do not discard
    # malformed completed lines or reinterpret them as a transient observation.
    lines = raw.splitlines(keepends=True)
    return [json.loads(line) for line in lines if line.endswith(b'\n')]


def summary(values):
    a = np.asarray(values, dtype=float)
    if not a.size:
        return None
    if not np.isfinite(a).all():
        raise ValueError('Nonfinite diagnostic values')
    return dict(count=int(a.size), mean=float(a.mean()), minimum=float(a.min()),
        maximum=float(a.max()), p50=float(np.median(a)), p95=float(np.percentile(a, 95)))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def diagnose(args):
    torch.set_num_threads(1)
    if (args.cycle_archive is None) != (args.cycle is None):
        raise ValueError('Specify both cycle archive and cycle index, or neither')
    out, root = args.output.resolve(), args.runtime.resolve()
    out.mkdir(parents=True, exist_ok=False)
    adapter = root/'source/tools/published_compliance_learner_20261025.py'
    hashes = json.loads((root/'SOURCE_HASHES.json').read_text())
    if sha(adapter) != hashes['tools/published_compliance_learner_20261025.py']:
        raise ValueError('Frozen actor adapter source mismatch')
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    prior = json.loads((root/'parameter/PRIORS.json').read_text())
    report = dict(captured_unix=time.time(), run=str(args.run.resolve()),
        source_sha256=sha(Path(__file__)), runtime_manifest_sha256=sha(root/'RUNTIME.json'),
        convergence_claim=False, optimizer_updates_performed=0, methods={})
    report.update(cycle_archive=str(args.cycle_archive) if args.cycle_archive else None, cycle=args.cycle)
    plot_rows = {}
    for method in ('direct', 'impedance', 'admittance', 'vmc'):
        folder = args.run/method
        checkpoint_path = (args.cycle_archive/method/f'cycle_{args.cycle:05d}.pt'
            if args.cycle_archive else folder/'checkpoint_latest.pt')
        if not checkpoint_path.exists():
            report['methods'][method] = dict(status='no_checkpoint_yet')
            continue
        frozen = out/(method+'_checkpoint.pt')
        with checkpoint_path.open('rb') as source, frozen.open('xb') as target:
            shutil.copyfileobj(source, target)
        checkpoint = torch.load(frozen, weights_only=False, map_location='cpu')
        if checkpoint['controller'] != method:
            raise ValueError('Checkpoint controller mismatch')
        if args.cycle_archive and (checkpoint.get('boundary') != 'complete_condition_cycle'
                or checkpoint['cycle'] != args.cycle):
            raise ValueError('Archive is not the requested complete-cycle snapshot')
        execution = json.loads((folder/'EXECUTION.json').read_text())
        if checkpoint['protocol_sha256'] != execution['protocol_sha256']:
            raise ValueError('Checkpoint/execution registration mismatch')
        state = checkpoint['learner']
        dimension = 7 if method == 'direct' else prior['methods'][method]['action_dimension']
        learner = PublishedLearner(root, dimension=dimension, direct=method == 'direct',
            seed=42, device='cpu', algorithm=state['algorithm'],
            **{key: state[key] for key in ('critic_layer_norm', 'numerical_amendments') if key in state})
        # Load policy/critics only. Do not restore optimizer or host CUDA RNG.
        learner.learner.agent.load_state_dict(state['agent'])
        agent = learner.learner.agent
        arrays = checkpoint['replay']['arrays']
        terminal = np.flatnonzero(arrays['dones'].reshape(-1) == 1)
        rng = np.random.default_rng(42)
        sample = rng.choice(len(arrays['rewards']), min(4096, len(arrays['rewards'])), replace=False)
        metrics = dict(steps=checkpoint['steps'], updates=state['num_gradient_steps'],
            checkpoint_sha256=sha(frozen), boundary=checkpoint.get('boundary'),
            replay_size=checkpoint['replay']['size'], terminal_count=len(terminal),
            terminal_fraction=float(len(terminal)/checkpoint['replay']['size']),
            alpha=float(state['alpha']), target_entropy=-dimension)

        def qs(obs, actions, target=False):
            if state['algorithm'] == 'cheq':
                return torch.stack([agent.get_q_value(obs, actions, i, target=target).reshape(-1)
                    for i in range(agent.ensemble_size)])
            networks = [agent.qf1_target, agent.qf2_target] if target else [agent.qf1, agent.qf2]
            return torch.stack([network(obs, actions).reshape(-1) for network in networks])

        with torch.no_grad():
            if len(terminal):
                obs = torch.as_tensor(arrays['observations'][terminal])
                actions = torch.as_tensor(arrays['actions'][terminal])
                predicted = qs(obs, actions).numpy()
                reward = arrays['rewards'][terminal].reshape(-1)
                metrics['terminal_reward'] = summary(reward)
                metrics['terminal_q_predictions'] = summary(predicted)
                metrics['terminal_q_absolute_error'] = summary(abs(predicted-reward))
                metrics['terminal_success_bonus_samples'] = int(np.sum(reward > 0))
            obs = torch.as_tensor(arrays['observations'][sample])
            nxt = torch.as_tensor(arrays['next_observations'][sample])
            actions = torch.as_tensor(arrays['actions'][sample])
            current_q = qs(obs, actions)
            next_action, log_pi = agent.get_action_and_log_prob(nxt)
            target_q = qs(nxt, next_action, target=True)[:2].min(dim=0).values
            target = torch.as_tensor(arrays['rewards'][sample].reshape(-1)) + (
                1-torch.as_tensor(arrays['dones'][sample].reshape(-1))) * learner.learner.gamma * (
                target_q-float(state['alpha'])*log_pi.reshape(-1))
            metrics['sampled_td_absolute_error'] = summary(abs(current_q-target).numpy())
            metrics['sampled_q_values'] = summary(current_q.numpy())
            metrics['td_diagnostic_pair'] = 'critics0/1 fixed diagnostic; training samples critic pairs'
            policy_action, policy_log_pi = agent.get_action_and_log_prob(obs)
            low = torch.as_tensor(learner.spaces.action_space.low)
            high = torch.as_tensor(learner.spaces.action_space.high)
            normalized = (policy_action-low)/(high-low)
            metrics['sampled_policy_entropy'] = summary(-policy_log_pi.numpy())
            metrics['near_action_limit_fraction'] = float(((normalized < .01) | (normalized > .99)).float().mean())

        episodes = [row for row in read_rows(folder/'episodes.jsonl') if row['total_steps'] <= checkpoint['steps']]
        optimizer = [row for row in read_rows(folder/'optimizer.jsonl') if row['step'] <= checkpoint['steps']]
        transitions = [row for row in read_rows(folder/'transitions.jsonl') if row['step'] <= checkpoint['steps']]
        components = ('progress', 'occupancy', 'time', 'comfort_torque', 'contact_force',
            'torque_slew', 'penetration', 'peak_torque', 'terminal', 'failure_tail', 'completion_efficiency')
        groups = defaultdict(list)
        for row in transitions:
            groups[row['cycle'], row['condition']].append(row)
        metrics['episodes'] = []
        for episode in episodes:
            rows = groups[episode['cycle'], episode['condition']]
            if len(rows) != episode['steps'] or not rows[-1]['done']:
                raise ValueError('Completed episode lacks matching complete transition evidence')
            value = sum(row['reward'] for row in rows)
            if abs(value-episode['reward']) > 1e-8:
                raise ValueError('Episode return disagrees with transition evidence')
            terms = {name: sum(row['reward_terms'].get(name, 0.) for row in rows) for name in components}
            if abs(sum(terms.values())-value) > 1e-7:
                raise ValueError('Reward components do not sum to episode return')
            metrics['episodes'].append(dict(condition=episode['condition'], cycle=episode['cycle'],
                category=episode['category'], reward=value, reward_terms=terms,
                task_success=episode['task_success'], strict_success=episode['strict_success'],
                final_task_stage=episode['final_task_stage'], abort_reason=episode['abort_reason']))
        metrics['ended_episode_returns'] = summary([e['reward'] for e in episodes])
        metrics['failure_stages'] = dict(Counter(e['final_task_stage'] for e in episodes if not e['strict_success']))
        metrics['recent_optimizer'] = {key: summary([row[key] for row in optimizer[-1000:] if key in row])
            for key in optimizer[-1] if key.startswith('agent_train/')} if optimizer else {}
        report['methods'][method] = metrics
        plot_rows[method] = episodes, optimizer
    (out/'DIAGNOSIS.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 2, figsize=(13, 11), constrained_layout=True)
    for method, (episodes, rows) in plot_rows.items():
        if episodes:
            axes[0, 0].plot([e['total_steps'] for e in episodes], [e['reward'] for e in episodes], '.-', label=method)
        # Nonoverlapping100-update windows. Never smooth across methods/runs.
        for ax, key in zip([axes[0, 1], axes[1, 0], axes[1, 1], axes[2, 0], axes[2, 1]],
                ['q_loss', 'actor_loss', 'actor_entropy', 'entropy_coefficient', 'next_q_values']):
            groups = [rows[i:i+100] for i in range(0, len(rows), 100)]
            valid = [[r for r in group if 'agent_train/'+key in r] for group in groups]
            valid = [group for group in valid if group]
            ax.plot([np.mean([r['step'] for r in group]) for group in valid],
                [np.mean([r['agent_train/'+key] for r in group]) for group in valid], label=method)
            ax.set_title(key+' (100-update means)')
    axes[0, 0].set_title('Ended training episodes; policy changes during collection')
    for ax in axes.flat:
        ax.set_xlabel('Logged transitions (includes recovered replay where registered)')
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    axes[0, 1].set_yscale('log')
    axes[2, 0].set_yscale('log')
    fig.suptitle('Early training diagnostics — no convergence or final-ranking claim')
    fig.savefig(out/'training_diagnostics.png', dpi=150)
    plt.close(fig)
    print(json.dumps({method: {k: data.get(k) for k in ('steps', 'terminal_count',
        'terminal_q_absolute_error', 'sampled_td_absolute_error', 'alpha', 'failure_stages')}
        for method, data in report['methods'].items()}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cycle-archive', type=Path)
    parser.add_argument('--cycle', type=int)
    diagnose(parser.parse_args())
