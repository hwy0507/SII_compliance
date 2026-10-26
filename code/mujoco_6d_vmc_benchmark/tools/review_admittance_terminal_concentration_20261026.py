"""Check saved terminal loss arithmetic and plot the frozen25/26 diagnosis."""
from pathlib import Path
import argparse
import hashlib
import json
import os


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(root):
    os.sched_setaffinity(0, {52})
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    reg = json.loads((root/'REGISTRATION.json').read_text())
    report = json.loads((root/'REVIEW.json').read_text())
    assert report['passed'] and report['original_checkpoints_unchanged']
    assert report['optimizer_updates'] == report['new_physics'] == report['replay_writes'] == 0
    for group in reg['inputs'].values():
        for ref in group.values():
            assert sha(ref['path']) == ref['sha256']
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), constrained_layout=True)
    for row in report['cycles']:
        cycle = row['cycle']
        p = root/f'cycle{cycle}_terminal_values.npz'
        assert sha(p) == row['values_sha256'] and row['agent_weights_and_forward_rng_unchanged']
        with np.load(p, allow_pickle=False) as data:
            q, reward, mask, denominator = [data[k] for k in ['q', 'rewards', 'masks', 'denominators']]
            predicted = sum(128*mask[i]*(q[i]-reward)**2/denominator[i] for i in range(5))
            np.testing.assert_allclose(predicted, data['contributions'], rtol=1e-14, atol=1e-14)
            assert np.isclose(predicted.sum(), row['terminal_population_loss_contribution'], rtol=1e-14, atol=1e-14)
            rank = np.argsort(-predicted)
            for k in [1, 5, 10]:
                assert np.isclose(predicted[rank[:k]].sum()/predicted.sum(), row[f'top{k}_fraction'], rtol=1e-14)
            axes[0].plot(np.arange(1, 21), np.cumsum(predicted[rank[:20]])/predicted.sum(), label=f'cycle{cycle}')
            if cycle == 26:
                pair = next(v for v in row['paired_strict_losses'] if v['condition'] == 'active_short_train_0600')
                selected = [np.flatnonzero(data['replay_indices'] == pair[k])[0]
                            for k in ['old_replay_index', 'new_replay_index']]
                for offset, index, label in zip([-.15, .15], selected, ['old25 success', 'new26 failure']):
                    for i in range(5):
                        axes[2].scatter(i+offset, q[i, index], marker='o' if mask[i, index] else 'x',
                                        color='tab:blue' if offset < 0 else 'tab:orange')
                    axes[2].axhline(reward[index], color='tab:blue' if offset < 0 else 'tab:orange',
                                   linestyle='--', label=label+' target')
                assert not pair['exact_critic_input_match']
    axes[0].set(title='Terminal loss concentration', xlabel='Highest-contributing terminal rows', ylabel='Cumulative terminal contribution fraction')
    axes[0].legend()
    totals = [r['terminal_population_loss_contribution'] for r in report['cycles']]
    axes[1].bar(['25', '26'], totals)
    axes[1].set(title='Frozen population terminal contribution', xlabel='Complete checkpoint cycle', ylabel='Sum of weighted critic terms')
    axes[2].set(title='Frozen26 Q: short0600 paired terminals', xlabel='Critic index (x = withheld from that critic)', ylabel='Q and terminal reward')
    axes[2].legend(fontsize=8)
    for axis in axes:
        axis.grid(alpha=.2)
    fig.suptitle('Terminal contributions only: not logged minibatch loss or proof of input aliasing')
    plot = root/'terminal_concentration.png'
    fig.savefig(plot, dpi=140)
    plt.close(fig)
    result = dict(passed=True, source_sha256=sha(__file__), input_report_sha256=sha(root/'REVIEW.json'),
        plot_sha256=sha(plot), terminal_population_contribution_ratio=totals[1]/totals[0],
        independent_scope='Saved-value weighted arithmetic and hash checks. Original CPU inference matched prior health MAE exactly; this reviewer does not rerun inference or dynamics.',
        scientific_decision='No terminal-weight/LR/critic-feature change from this diagnostic. One new failure terminal dominates26 terminal contribution, but old terminal rows also contribute. No exact conflicting critic-input pair was found. Inspect complete27 health and the identified retained rows before deciding whether the mismatch persists.',
        new_physics=0, optimizer_updates=0, convergence_claim=False)
    (root/'SAVED_VALUE_REVIEW.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)
