"""Verify saved attribution arithmetic and plot outcome switches; no new rollouts."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import os


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(root):
    os.sched_setaffinity(0, {52})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    report_path = root/'REVIEW.json'
    before = sha(report_path)
    report = json.loads(report_path.read_text())
    reg = json.loads((root/'REGISTRATION.json').read_text())
    assert report['passed'] and report['saved_transitions_verified'] == 371250
    fig, axes = plt.subplots(3, 2, figsize=(12, 9), constrained_layout=True)
    summaries = {}
    for i, (method, value) in enumerate(report['methods'].items()):
        episodes = {}
        for cycle in [27, 28, 29]:
            ref = reg['inputs'][f'{method}:{cycle}:episodes']
            assert sha(ref['path']) == ref['sha256']
            rows = [json.loads(line) for line in Path(ref['path']).read_text().splitlines()]
            episodes[cycle] = {row['condition']: row for row in rows}
            assert len(rows) == len(episodes[cycle]) == 30
        for comparison in value['comparisons']:
            old, new = episodes[comparison['before']], episodes[comparison['after']]
            deltas = {k: new[k]['reward']-old[k]['reward'] for k in old}
            assert math.isclose(math.fsum(deltas.values())/30, comparison['mean_delta'], abs_tol=1e-10)
            switches = [k for k in old if any(old[k][field] != new[k][field]
                        for field in ['task_success', 'strict_success'])]
            assert sorted(switches) == sorted(comparison['switched_conditions'])
            assert math.isclose(math.fsum(deltas[k] for k in switches)/30,
                                comparison['switched_contribution'], abs_tol=1e-10)
            for row in comparison['conditions']:
                assert math.isclose(row['reward_delta'], deltas[row['condition']], abs_tol=1e-10)
                assert math.isclose(math.fsum(row['term_deltas'].values()), row['reward_delta'], abs_tol=1e-8)
        comparison = value['comparisons'][-1]
        switched = [row for row in comparison['conditions'] if row['task_switch'] or row['strict_switch']]
        labels = [row['condition'].replace('active_short_train_', 'short ') for row in switched]+['All other conditions']
        contributions = [row['contribution_to_mean'] for row in switched]+[comparison['unchanged_outcome_contribution']]
        axes[i, 0].bar(labels, contributions)
        axes[i, 0].axhline(0, color='black', linewidth=.7)
        axes[i, 0].set(title=method+': contributions to mean reward change28→29', ylabel='Mean reward contribution')
        peaks = [row['conditions']['active_short_train_0600']['saved_external_penetration_mm'] for row in value['cycles']]
        strict = [row['conditions']['active_short_train_0600']['strict'] for row in value['cycles']]
        axes[i, 1].plot([27, 28, 29], peaks, marker='o')
        axes[i, 1].axhline(.2, color='red', linestyle='--', label='Original0.2mm limit')
        for cycle, peak, success in zip([27, 28, 29], peaks, strict):
            axes[i, 1].annotate('Strict pass' if success else 'Strict fail', (cycle, peak),
                                xytext=(0, 8), textcoords='offset points', ha='center', fontsize=8)
        axes[i, 1].set(title=method+': saved short0600 penetration', ylabel='mm', xticks=[27, 28, 29])
        axes[i, 1].margins(y=.35)
        axes[i, 1].legend(fontsize=8)
        summaries[method] = dict(mean_delta=comparison['mean_delta'], switched_conditions=comparison['switched_conditions'],
            switched_contribution=comparison['switched_contribution'], remainder=comparison['unchanged_outcome_contribution'],
            saved_short0600_penetration_mm=peaks)
    for axis in axes.flat:
        axis.grid(axis='y', alpha=.2)
    fig.suptitle('Saved training outcomes: arithmetic attribution, not a noise or learning causal test')
    plot = root/'outcome_switch_contributions.png'
    fig.savefig(plot, dpi=140)
    plt.close(fig)
    assert sha(report_path) == before
    result = dict(passed=True, source_review_sha256=before, plot_sha256=sha(plot), methods=summaries,
        new_physics=0, optimizer_updates=0, neural_forward_passes=0,
        scope='Independent saved episode-delta and switch arithmetic; saved penetration peaks plotted without rerunning dynamics.')
    (root/'SAVED_VALUE_REVIEW.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)
