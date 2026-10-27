"""Paired complete-cycle reward audit; descriptive evidence, no automatic stop."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(registration, output):
    os.sched_setaffinity(0, {52})
    import numpy as np
    reg = json.loads(registration.read_text())
    assert reg['cycles'] == [26, 27, 28, 29] and reg['stability_window'] == [27, 28, 29]
    assert reg['bootstrap_seed'] == 2026102746 and reg['bootstrap_replicates'] == 5000
    assert reg['relative_change_limit'] == .05 and reg['near_zero_guard'] == 1.
    assert sha(Path(__file__)) == reg['source_sha256']
    for group in reg['inputs'].values():
        for ref in group.values():
            assert sha(ref['path']) == ref['sha256']
    protocols, summaries, episode_maps = [], [], []
    losses = []
    for cycle in reg['cycles']:
        refs = reg['inputs'][str(cycle)]
        def read(key):
            return json.loads(Path(refs[key]['path']).read_text())
        protocol = read('protocol')
        report, health = read('review'), read('health')
        assert report['passed'] and read('finished')['completed']
        method = report['methods']['direct']
        assert method['checkpoint_sha256'] == health['checkpoint_sha256']
        assert method['optimizer_and_network_finite'] and health['network_optimizer_rng_unchanged']
        assert protocol['batch_size_stage']['batch_size'] == 65536
        if protocols:
            for key in ['conditions', 'reference_plan_sha256', 'upstream_commit', 'source_adapter_hashes',
                        'observation', 'action', 'terminal_adaptation', 'control_adaptation',
                        'critic_updates_per_outer_step', 'actor_updates_per_outer_step',
                        'multistep_stage', 'critic_clock_stage', 'batch_size_stage']:
                assert protocol[key] == protocols[0][key], key
            assert protocol['gather_stage']['marker'] == protocols[0]['gather_stage']['marker']
            for name in ['serl_multistep_state_adapter_20261026.py',
                         'serl_multistep_replay_gather_20261026.py', 'serl_multistep_batch_transfer_20261026.py']:
                assert protocol['gather_stage']['source_hashes'][name] == protocols[0]['gather_stage']['source_hashes'][name]
        capacity = protocol['replay_capacity_stage']
        assert capacity['marker'] == reg['capacity_marker']
        assert capacity['parent_cycle'] == 23 and capacity['old_capacity'] == 1_000_000
        assert capacity['new_capacity'] == 2_000_000 and capacity['auxiliary_weights_imported'] is False
        assert method['replay_capacity']['passed'] and method['replay_capacity']['new_capacity'] == 2_000_000
        assert method['replay_capacity']['marker'] == reg['capacity_marker']
        multi = method['multistep_replay']
        assert multi['passed'] and multi['quarantined_old_pending_rows'] == 930
        assert multi['new_pending_rows'] == 0 and multi['all_new_derived_targets_exact']
        assert method['retained_replay_all_fields_exact'] and method['max_reward_reconstruction_error'] == 0
        if protocols:
            assert capacity == protocols[0]['replay_capacity_stage']
            assert protocol['interrupted_stream_recovery'] == protocols[0]['interrupted_stream_recovery']
        if cycle == 26:
            assert 'recovery_continuation_stage' not in protocol
        else:
            stage = protocol['recovery_continuation_stage']
            assert stage['parent_cycle'] == cycle-1 and stage['new_cycle'] == cycle
            assert stage['new_cycles'] == 1 and stage['quarantined_pending'] == 930
            assert stage['active_streams'] == list(range(30,60))
            assert stage['optimizer_settings_changed'] is False and stage['auxiliary_weights_imported'] is False
            assert stage['checkpoint']['sha256'] == summaries[-1]['checkpoint_sha256']
            assert stage['parent_registration'] == reg['inputs'][str(cycle-1)]['protocol']
            for key in ['gather_gate','gather_saved_review']:
                ref=stage[key]; assert sha(ref['path']) == ref['sha256']
                assert json.loads(Path(ref['path']).read_text())['passed']
            if cycle > 27:
                for key in ['gather_gate','gather_saved_review','gather_sha256']:
                    assert stage[key] == protocols[1]['recovery_continuation_stage'][key]
        protocols.append(protocol)
        episodes = [json.loads(line) for line in Path(refs['episodes']['path']).read_text().splitlines()]
        assert len(episodes) == 30 and all(e['cycle'] == cycle for e in episodes)
        by_id = {e['condition']: e for e in episodes}
        expected = {c['id']: c for c in protocol['conditions']}
        assert len(by_id) == len(expected) == 30 and by_id.keys() == expected.keys()
        for key, e in by_id.items():
            assert e['model_sha256'] == expected[key]['model_sha256']
        if episode_maps:
            assert by_id.keys() == episode_maps[0].keys()
        assert sum(e['task_success'] for e in episodes) == method['task']
        assert sum(e['strict_success'] for e in episodes) == method['strict']
        rewards = np.asarray([e['reward'] for e in episodes])
        assert np.isfinite(rewards).all()
        assert np.isclose(rewards.mean(), method['reward_mean'], rtol=0, atol=1e-10)
        optimizer = [json.loads(line) for line in Path(refs['optimizer']['path']).read_text().splitlines()]
        assert len(optimizer) == method['new_transitions'] == sum(e['steps'] for e in episodes)
        assert [r['step'] for r in optimizer] == list(range(method['steps']-len(optimizer)+1, method['steps']+1))
        assert all(np.isfinite(v) for r in optimizer for v in r.values() if isinstance(v, (float, int)))
        loss = np.asarray([r['serl/critic/critic_loss'] for r in optimizer])
        alpha = np.asarray([r['serl/actor/temperature'] for r in optimizer])
        assert (loss >= 0).all() and (alpha > 0).all()
        losses.append(loss)
        summaries.append(dict(cycle=cycle, reward_mean=float(rewards.mean()), task=method['task'],
            strict=method['strict'], full_horizon=method['full_horizon_count'], aborts=method['aborts'],
            checkpoint_sha256=method['checkpoint_sha256'], optimizer_records=len(optimizer),
            critic_loss_first1000=float(loss[:1000].mean()), critic_loss_last1000=float(loss[-1000:].mean()),
            critic_loss_mean=float(loss.mean()), critic_loss_maximum=float(loss.max()),
            alpha_first1000=float(alpha[:1000].mean()), alpha_last1000=float(alpha[-1000:].mean()),
            terminal_mae=health['terminal_q_absolute_error']['mean'],
            td32_mae=health['sampled_multistep_td_absolute_error']['mean'], finite_logs=True))
        episode_maps.append(by_id)
    ids = sorted(episode_maps[0])
    matrix = np.asarray([[e[key]['reward'] for key in ids] for e in episode_maps])
    means = matrix.mean(axis=1)
    last = means[1:]
    denominators = np.abs(last[:-1])
    near_zero = bool((np.abs(last) < reg['near_zero_guard']).any())
    adjacent = np.abs(np.diff(last))/denominators if not near_zero else None
    endpoint = float(abs(last[-1]-last[0])/abs(last[0])) if not near_zero else None
    delta = matrix[-1]-matrix[0]
    # Resample condition identities within each category, keeping the full time
    # series together. These are sensitivity intervals, not independent seeds.
    rng = np.random.default_rng(reg['bootstrap_seed'])
    categories = sorted({episode_maps[0][key]['category'] for key in ids})
    draws = []
    for category in categories:
        positions = np.asarray([i for i, key in enumerate(ids) if episode_maps[0][key]['category'] == category])
        assert len(positions) == 10
        draws.append(rng.choice(positions, size=(5000, 10), replace=True))
    selected = np.concatenate(draws, axis=1)
    bootstrap_means = matrix[:, selected].mean(axis=2)
    changes = bootstrap_means[-1]-bootstrap_means[0]
    x = np.asarray([27., 28., 29.]); x -= x.mean()
    slopes = (bootstrap_means[1:]*x[:, None]).sum(axis=0)/(x*x).sum()
    paired = [dict(condition=key, category=episode_maps[0][key]['category'],
        rewards=matrix[:, i].tolist(), baseline26_to29_delta=float(delta[i])) for i, key in enumerate(ids)]
    result = dict(passed=True, time=time.time(), registration_sha256=sha(registration),
        cycles=summaries, paired_conditions=paired, baseline_cycle=26, stability_window=[27, 28, 29],
        baseline26_to29_mean_delta=float(delta.mean()),
        improved_conditions=int((delta > 0).sum()), worsened_conditions=int((delta < 0).sum()),
        bootstrap_condition_sensitivity95_delta=np.quantile(changes, [.025, .975]).tolist(),
        last3_mean_slope=float((last*x).sum()/(x*x).sum()),
        bootstrap_condition_sensitivity95_slope=np.quantile(slopes, [.025, .975]).tolist(),
        near_zero_mean_guard_triggered=near_zero,
        adjacent_relative_mean_changes=None if adjacent is None else adjacent.tolist(),
        last3_endpoint_relative_change=endpoint,
        descriptive_five_percent_check=bool(not near_zero and (adjacent <= .05).all() and endpoint <= .05),
        capacity_marker=reg['capacity_marker'], capacity_change_between_baseline_and_window=False,
        new_physics=0, optimizer_updates=0, automatic_stop=False, convergence_claim=False,
        limitation='Fixed27-29 window registered while27 had zero completed conditions and28-29 were not launched. Complete26 is an already observed paired baseline. All four retain identical2m capacity, historical entry23, original interrupted25 lineage and930 quarantined pending rows. Exact-equivalent take gather deployed at27 is disclosed with its gate; baseline deltas cannot isolate implementation from policy/time effects. Original5percent and nearzero1 criteria retained. Condition bootstrap measures composition sensitivity, not independent training seeds or frozen-policy performance. Safety failures remain in all30 denominators and actual episode lengths are checked. Finite logs and5percent alone do not declare convergence or automatically stop training. Frozen validation and other methods remain separate requirements.')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(25, 4), constrained_layout=True)
    axes[0].plot(reg['cycles'], means, marker='o'); axes[0].set(title='Complete-cycle reward means', xlabel='Cycle')
    axes[1].bar(range(30), delta); axes[1].axhline(0, color='grey'); axes[1].set(title='Paired reward change:29 minus26', xlabel='Fixed condition index')
    for cycle, loss in zip(reg['cycles'], losses):
        count = len(loss)//1000
        axes[2].plot(np.arange(count), loss[:count*1000].reshape(count, 1000).mean(axis=1), label=str(cycle))
    axes[2].set(title='Critic loss,1000-update block means', xlabel='Within-cycle block'); axes[2].legend()
    for axis in axes: axis.grid(alpha=.2)
    fig.suptitle('Direct SERL: training reward stability is separate from task success and frozen validation')
    plot = output/'reward_stability.png'; fig.savefig(plot, dpi=140); plt.close(fig)
    result['plot_sha256'] = sha(plot)
    for group in reg['inputs'].values():
        for ref in group.values(): assert sha(ref['path']) == ref['sha256']
    (output/'REVIEW.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.registration, args.output)
    except BaseException as error:
        (args.output/'FAILURE.json').write_text(json.dumps(dict(time=time.time(), error=repr(error)))+'\n')
        raise
