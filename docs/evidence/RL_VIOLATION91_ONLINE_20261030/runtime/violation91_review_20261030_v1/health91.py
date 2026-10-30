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

from diagnose_published_value_bound_20261025 import soft_upper_bound


AUDITED_REWARD_SOURCES = {
    'spt_rl_reward_20261025.py': 'c63deee3a17318703e17744245986d97d340a741623f03abe73af5aa43ffaebf',
    'training_comparison_metrics_20261025.py': '24ee8166b9ade665290a6883bdf39ecf615e7cbf3f954c1404e1717e7a8b2e07',
}


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


def registered_target_minimum(values, algorithm, count):
    if algorithm not in ('sac', 'cheq') or count not in (2, 5):
        raise ValueError('Unknown diagnostic Bellman rule')
    if algorithm == 'sac' and count != 2:
        raise ValueError('SAC diagnostic requires original pair')
    expected = 5 if algorithm == 'cheq' else 2
    if values.ndim != 2 or values.shape[0] != expected:
        raise ValueError('Diagnostic critic ensemble shape mismatch')
    return values[:count].min(dim=0).values


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
    for name, expected in AUDITED_REWARD_SOURCES.items():
        if sha(root/'source/tools'/name) != expected:
            raise ValueError('Soft bound requires its audited reward/efficiency source: '+name)
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    prior = json.loads((root/'parameter/PRIORS.json').read_text())
    report = dict(captured_unix=time.time(), run=str(args.run.resolve()),
        source_sha256=sha(Path(__file__)), runtime_manifest_sha256=sha(root/'RUNTIME.json'),
        convergence_claim=False, optimizer_updates_performed=0, methods={})
    report.update(cycle_archive=str(args.cycle_archive) if args.cycle_archive else None, cycle=args.cycle)
    report['td_scope']='Unprojected fixed-minimum-pair TD diagnostic; does not reproduce projected targets or the A/V mean estimator. Q calibration and physical returns reported separately.'
    plot_rows = {}
    for method in ('impedance', 'admittance', 'vmc'):
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
        assert state['target_pair_reduction']==dict(version=1,target={'impedance':'minimum','admittance':'mean','vmc':'mean'}[method],actor='minimum',sampled_targets=2)
        dimension = 7 if method == 'direct' else prior['methods'][method]['action_dimension']
        from persisted_history_critic import history_class, marker as history_marker, KEY
        protocol = json.loads((folder.resolve().parent/'REGISTRATION.json').read_text())
        binding = protocol['history_critic_amendment']['binding']
        assert state[KEY] == checkpoint['replay'][KEY] == history_marker(binding)
        from persisted_violation_critic import violation_class, marker as violation_marker, KEY as VK
        bit = protocol['violation_critic_amendment']['binding']
        assert state[VK] == checkpoint['replay'][VK] == violation_marker(bit)
        assert checkpoint['history_critic_amendment'] == execution['history_critic_amendment'] == protocol['history_critic_amendment']
        assert checkpoint['violation_critic_amendment'] == execution['violation_critic_amendment'] == protocol['violation_critic_amendment']
        assert checkpoint['protocol_sha256'] == sha(folder.resolve().parent/'REGISTRATION.json')
        assert execution['replay_observation_dimension'] == 52 and execution['actor_observation_dimension'] == 49
        assert checkpoint['replay']['arrays']['observations'].shape[1] == checkpoint['replay']['arrays']['next_observations'].shape[1] == 52
        learner = violation_class(history_class(PublishedLearner, binding), bit)(root, dimension=dimension, direct=method == 'direct',
            seed=42, device='cpu', algorithm=state['algorithm'],
            **{key: state[key] for key in ('critic_layer_norm', 'numerical_amendments', 'critic_clock') if key in state})
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
            alpha=float(state['alpha']), target_entropy=-dimension, target_pair_reduction=state['target_pair_reduction'])
        restart_receipt = None
        if execution.get('resumed_from'):
            receipt_path = Path(execution['resumed_from']).with_suffix('.json')
            if receipt_path.exists():
                candidate = json.loads(receipt_path.read_text())
                if candidate.get('critic_optimizer_reset'):
                    if (candidate['output_sha256'] != execution['resumed_checkpoint_sha256']
                            or candidate['registration_sha256'] != checkpoint['protocol_sha256']):
                        raise ValueError('Scientific restart receipt mismatch')
                    restart_receipt = candidate
                    metrics['critic_restart'] = dict(receipt=str(receipt_path), receipt_sha256=sha(receipt_path),
                        parent_steps=candidate['parent_cycle_history'][-1]['steps'],
                        parent_checkpoint_sha256=candidate['parent_sha256'],
                        auxiliary_weights_imported=candidate['auxiliary_weights_imported'])

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
                if state['algorithm'] == 'cheq':
                    mask = arrays['masks'][terminal].T.astype(bool)
                    if mask.shape != predicted.shape:
                        raise ValueError('Terminal ensemble mask shape mismatch')
                    error = abs(predicted-reward)
                    metrics['terminal_q_in_bag_absolute_error'] = summary(error[mask])
                    metrics['terminal_q_out_of_bag_absolute_error'] = summary(error[~mask])
                    metrics['terminal_mask_interpretation'] = (
                        'Mask1 rows train that critic; mask0 rows are intentionally withheld from its loss. '
                        'Report fitting and held-out prediction separately; aggregate error mixes them.')
                    if restart_receipt and checkpoint['replay']['size'] == checkpoint['steps']:
                        origin = terminal >= metrics['critic_restart']['parent_steps']
                        metrics['terminal_by_restart_origin'] = {}
                        for label, selection in [('retained_parent', ~origin), ('collected_after_restart', origin)]:
                            selected_error, selected_mask = error[:, selection], mask[:, selection]
                            metrics['terminal_by_restart_origin'][label] = dict(rows=int(selection.sum()),
                                in_bag_mae=summary(selected_error[selected_mask]),
                                out_of_bag_mae=summary(selected_error[~selected_mask]))
                metrics['terminal_error_limitation'] = (
                    ('Critic includes remaining time, causal history and raw violation bit; actor directly receives neither feature. '
                     if state.get('critic_clock', False) else
                     'Observation lacks remaining time; terminal MAE can include hidden-clock aliasing. ') +
                    'It is a diagnostic, not a required zero-error convergence gate.')
                metrics['terminal_success_bonus_samples'] = int(np.sum(reward > 0))
            obs = torch.as_tensor(arrays['observations'][sample])
            nxt = torch.as_tensor(arrays['next_observations'][sample])
            actions = torch.as_tensor(arrays['actions'][sample])
            current_q = qs(obs, actions)
            next_action, log_pi = agent.get_action_and_log_prob(nxt)
            target_count = state.get('bellman_target_count', 2)
            target_q = registered_target_minimum(qs(nxt, next_action, target=True),
                                                 state['algorithm'], target_count)
            target = torch.as_tensor(arrays['rewards'][sample].reshape(-1)) + (
                1-torch.as_tensor(arrays['dones'][sample].reshape(-1))) * learner.learner.gamma * (
                target_q-float(state['alpha'])*log_pi.reshape(-1))
            metrics['sampled_td_absolute_error'] = summary(abs(current_q-target).numpy())
            metrics['sampled_q_values'] = summary(current_q.numpy())
            global_bound = float(soft_upper_bound(float(state['alpha']), learner.learner.gamma,
                1375, learner.spaces.action_space.low, learner.spaces.action_space.high))
            metrics['fixed_alpha_soft_q_global_bound'] = global_bound
            metrics['sampled_q_above_global_bound_fraction'] = float(
                (current_q > global_bound+.01).float().mean())
            metrics['soft_bound_limitation'] = (
                'Necessary bound for frozen checkpoint policy/current alpha and spt_v1; '
                'not a future changing-alpha bound, and satisfying it does not establish calibration.')
            metrics['bellman_target_count'] = target_count
            metrics['td_diagnostic_pair'] = ('all five critics; registered Bellman target rule'
                if target_count == 5 else 'critics0/1 fixed diagnostic; CHEQ training samples critic pairs')
            policy_action, policy_log_pi = agent.get_action_and_log_prob(obs)
            low = torch.as_tensor(learner.spaces.action_space.low)
            high = torch.as_tensor(learner.spaces.action_space.high)
            normalized = (policy_action-low)/(high-low)
            metrics['sampled_policy_entropy'] = summary(-policy_log_pi.numpy())
            metrics['near_action_limit_fraction'] = float(((normalized < .01) | (normalized > .99)).float().mean())

        if learner.learner.num_gradient_steps or any(v.grad is not None for v in agent.parameters()):
            raise AssertionError('Read-only diagnosis performed learning')
        if not all(torch.equal(value, state['agent'][key]) for key, value in agent.state_dict().items()):
            raise AssertionError('Read-only diagnosis changed network tensors')
        metrics['network_state_unchanged'] = True

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
    render_training_plot(out, plot_rows)
    print(json.dumps({method: {k: data.get(k) for k in ('steps', 'terminal_count',
        'terminal_q_absolute_error', 'sampled_td_absolute_error', 'alpha', 'failure_stages')}
        for method, data in report['methods'].items()}, indent=2))


def render_training_plot(out, plot_rows):
    """Plot actual logged quantities; plain SAC does not log next-target Q."""
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
            label = key
            values = rows
            if key == 'next_q_values' and not any('agent_train/'+key in r for r in rows):
                key = 'diagnostic_replay_q_mean'
                label = 'SAC replay Q mean (not next target)'
                values = [dict(r, **{'agent_train/'+key: (
                    r['agent_train/qf1_values']+r['agent_train/qf2_values'])/2})
                    for r in rows if 'agent_train/qf1_values' in r and 'agent_train/qf2_values' in r]
            groups = [values[i:i+100] for i in range(0, len(values), 100)]
            valid = [[r for r in group if 'agent_train/'+key in r] for group in groups]
            valid = [group for group in valid if group]
            ax.plot([np.mean([r['step'] for r in group]) for group in valid],
                [np.mean([r['agent_train/'+key] for r in group]) for group in valid], label=method)
            ax.set_title(('terminal128 projected target q_loss (I=min, A/V=mean)' if label=='q_loss' else label)+' (100-update means)')
    axes[0, 0].set_title('Ended training episodes; policy changes during collection')
    for ax in axes.flat:
        ax.set_xlabel('Logged transitions (includes recovered replay where registered)')
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    axes[0, 1].set_yscale('log')
    axes[2, 0].set_yscale('log')
    fig.suptitle('Training diagnostics — no convergence or final-ranking claim')
    fig.savefig(out/'training_diagnostics.png', dpi=150)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cycle-archive', type=Path)
    parser.add_argument('--cycle', type=int)
    diagnose(parser.parse_args())
