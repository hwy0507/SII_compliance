"""Fixed capacity74-76 training stability; never an automatic stop gate."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')

def main(root):
    os.sched_setaffinity(0, {54})
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    reg = json.loads((root/'REGISTRATION.json').read_text())
    assert reg['cycles'] == [74, 75, 76] and reg['seed'] == 2026102855
    assert reg['bootstrap_replicates'] == 5000 and reg['near_zero_guard'] == 1.
    assert reg['relative_limit'] == .05 and sha(__file__) == reg['source_sha256']
    for group in reg['inputs'].values():
        for ref in group.values():
            assert sha(ref['path']) == ref['sha256']
    results = {}
    fig, axes = plt.subplots(3, 2, figsize=(12, 10), constrained_layout=True)
    for mi, method in enumerate(['impedance', 'admittance', 'vmc']):
        anchor_ref = reg['anchor_protocol55'][method]
        assert sha(anchor_ref['path']) == anchor_ref['sha256']
        anchor = json.loads(Path(anchor_ref['path']).read_text())
        protocols, maps, summaries = [anchor], [], []
        for cycle in reg['cycles']:
            refs = reg['inputs'][f'{method}:{cycle}']
            def read(key):
                return json.loads(Path(refs[key]['path']).read_text())
            p, review, health = read('protocol'), read('review'), read('health')
            assert review['passed'] and read('finished')['completed']
            row, h = review['methods'][method], health['methods'][method]
            assert row['checkpoint_sha256'] == h['checkpoint_sha256']
            assert row['optimizer_and_network_finite'] and h['network_state_unchanged']
            assert row['replay_capacity_extension']['capacity'] == 2000000
            assert p['replay_capacity_stage']['parent_cycle'] == 23
            if protocols:
                for key in ['conditions', 'runtime_sha256', 'reference_plan_sha256', 'physics_dt_s',
                            'actor_period_s', 'horizon_s', 'actor', 'reward', 'critic_clock',
                            'learner_batch_size', 'learner_updates_per_transition', 'critic_layer_norm',
                            'numerical_amendments', 'terminal_weight_stage', 'target_projection_stage',
                            'exact_pipeline_stage', 'pair_reduction_stage', 'sampler_pool',
                            'shared_sampler_stage', 'replay_capacity_stage']:
                    assert p[key] == protocols[0][key], (method, key)
                for key in ['projection', 'weight', 'reduction']:
                    assert p['batch_size_stage'][key] == protocols[0]['batch_size_stage'][key], key
                for key in ['actor_learning_rate_factor', 'parent_actor_learning_rates', 'bellman_target_count']:
                    assert p['completed_stage_continuation'][key] == protocols[0]['completed_stage_continuation'][key]
            baseline_deps = protocols[0]['batch_size_stage']['dependency_hashes'] if protocols else p['batch_size_stage']['dependency_hashes']
            deps = p['batch_size_stage']['dependency_hashes']
            followup = p['replay_capacity_followup_stage']
            assert followup['parent_cycle'] == 47 and followup['historical_entry_cycle'] == 23
            assert followup['old_capacity'] == 2_000_000 and followup['new_capacity'] == 4_000_000
            assert followup['marker'] == reg['followup_marker']
            assert not followup['auxiliary_weights_imported'] and not followup['optimizer_settings_changed']
            assert row['replay_capacity_followup'] == followup['marker'] and row['current_replay_capacity'] == 4_000_000
            assert deps == baseline_deps
            if protocols:
                assert followup == protocols[0]['replay_capacity_followup_stage']
            for evidence_key in ['preparation_review','malformed_state_review']:
                ref=followup[evidence_key]; assert sha(ref['path'])==ref['sha256']
                assert json.loads(Path(ref['path']).read_text())['passed']
            entry=followup['entry_checkpoint']
            assert sha(entry['path']) == entry['sha256']
            historical_review = B/'runs/parameter_capacity_pool30_cycle47_review_20261026_v1/REVIEW.json'
            historic=json.loads(historical_review.read_text()); assert historic['passed']
            assert entry['sha256'] == historic['methods'][method]['checkpoint_sha256']
            assert deps['parameter_replay_capacity4m_20261027.py'] == followup['helper_sha256']
            assert deps['resume_cheq_capacity4m_pool30_20261027.py'] == p['batch_size_stage']['driver_sha256']
            protocols.append(p)
            episodes = [json.loads(line) for line in Path(refs['episodes']['path']).read_text().splitlines()]
            by_id = {e['condition']: e for e in episodes}
            conditions = {c['id']: c for c in p['conditions']}
            assert len(episodes) == len(by_id) == len(conditions) == 30
            assert by_id.keys() == conditions.keys() and all(e['cycle'] == cycle for e in episodes)
            assert all(e['model_sha256'] == conditions[e['condition']]['model_sha256'] for e in episodes)
            rewards = np.asarray([e['reward'] for e in episodes])
            assert np.isfinite(rewards).all() and np.isclose(rewards.mean(), row['reward_mean'], rtol=0, atol=1e-10)
            assert sum(e['task_success'] for e in episodes) == row['task']
            assert sum(e['strict_success'] for e in episodes) == row['strict']
            optimizer = [json.loads(line) for line in Path(refs['optimizer']['path']).read_text().splitlines()]
            assert len(optimizer) == row['new_transitions'] == sum(e['steps'] for e in episodes)
            assert all(0 < e['steps'] <= 1375 for e in episodes)
            assert sum(e['steps'] == 1375 for e in episodes) == row['full_horizon_count']
            assert [v['step'] for v in optimizer] == list(range(row['steps']-row['new_transitions']+1, row['steps']+1))
            assert all(np.isfinite(v) for record in optimizer for v in record.values() if isinstance(v, (float, int)))
            loss = np.asarray([v['agent_train/q_loss'] for v in optimizer])
            alpha = np.asarray([v['agent_train/entropy_coefficient'] for v in optimizer])
            assert (loss >= 0).all() and (alpha > 0).all()
            summaries.append(dict(cycle=cycle, reward_mean=float(rewards.mean()), task=row['task'], strict=row['strict'],
                full_horizon=row['full_horizon_count'], aborts=row['aborts'], checkpoint_sha256=row['checkpoint_sha256'],
                q_loss_first1000=float(loss[:1000].mean()), q_loss_last1000=float(loss[-1000:].mean()),
                q_loss_maximum=float(loss.max()), q_loss_mean=float(loss.mean()),
                alpha_last1000=float(alpha[-1000:].mean()), terminal_mae=h['terminal_q_absolute_error']['mean'],
                terminal_inbag_mae=h['terminal_q_in_bag_absolute_error']['mean'],
                q_mean=h['sampled_q_values']['mean'], td_mae=h['sampled_td_absolute_error']['mean']))
            maps.append(by_id)
            n = len(loss)//1000
            axes[mi, 1].plot(np.arange(n), loss[:n*1000].reshape(n, 1000).mean(axis=1), label=str(cycle))
        ids = sorted(maps[0])
        matrix = np.asarray([[m[k]['reward'] for k in ids] for m in maps])
        means = matrix.mean(axis=1)
        near_zero = bool((np.abs(means) < reg['near_zero_guard']).any())
        adjacent = None if near_zero else (np.abs(np.diff(means))/np.abs(means[:-1])).tolist()
        endpoint = None if near_zero else float(abs(means[-1]-means[0])/abs(means[0]))
        rng = np.random.default_rng(reg['seed']+mi)
        positions = [[i for i, k in enumerate(ids) if maps[0][k]['category'] == category]
                     for category in sorted({maps[0][k]['category'] for k in ids})]
        assert [len(v) for v in positions] == [10, 10, 10]
        draws = np.concatenate([rng.choice(v, size=(5000, 10), replace=True) for v in positions], axis=1)
        boot = matrix[:, draws].mean(axis=2)
        delta = matrix[-1]-matrix[0]
        results[method] = dict(cycles=summaries, near_zero_guard_triggered=near_zero,
            absolute_range_of_cycle_means=float(np.ptp(means)),
            adjacent_absolute_mean_changes=np.abs(np.diff(means)).tolist(),
            adjacent_relative_mean_changes=adjacent, endpoint_relative_mean_change=endpoint,
            descriptive_five_percent_check=bool(not near_zero and max(adjacent+[endpoint]) <= .05),
            paired74_to76_mean_delta=float(delta.mean()), improved_conditions=int((delta > 0).sum()),
            worsened_conditions=int((delta < 0).sum()), slope=float((means[-1]-means[0])/2),
            bootstrap_condition_sensitivity95_delta=np.quantile(boot[-1]-boot[0], [.025, .975]).tolist(),
            bootstrap_condition_sensitivity95_slope=np.quantile((boot[-1]-boot[0])/2, [.025, .975]).tolist(),
            paired_conditions=[dict(condition=k, rewards=matrix[:, i].tolist()) for i, k in enumerate(ids)])
        axes[mi, 0].plot(reg['cycles'], means, marker='o')
        axes[mi, 0].set(title=method+' complete-cycle reward', xlabel='Cycle')
        axes[mi, 1].set(title=method+' critic loss:1000-update blocks', xlabel='Within-cycle block')
        axes[mi, 1].legend()
    for axis in axes.flat:
        axis.grid(alpha=.2)
    fig.suptitle('Capacity74-76: reward stability and optimizer diagnostics')
    plot = root/'reward_stability.png'
    fig.savefig(plot, dpi=144)
    plt.close(fig)
    for group in reg['inputs'].values():
        for ref in group.values():
            assert sha(ref['path']) == ref['sha256']
    result = dict(passed=True, time=time.time(), methods=results, plot_sha256=sha(plot),
        new_physics=0, optimizer_updates=0, automatic_stop=False, convergence_claim=False,
        limitation='Fixed74-76 window on30 registered training conditions, chosen while74-76 were not launched. All74-76 outcomes are future at registration; first74 protocol is also compared against frozen55 scientific settings. Capacity4m throughout, with immutable historicalentry23/47 and identical dependencies. Original5percent/nearzero1/5000 condition bootstrap and real episode lengths retained. Online policies change; paired intervals measure condition-composition sensitivity, not independent training seeds or frozen-policy performance. Finite losses and5percent alone do not declare healthy convergence or unlock test.')
    (root/'REVIEW.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        (args.root/'FAILURE.json').write_text(json.dumps(dict(error=repr(error), time=time.time()))+'\n')
        raise
