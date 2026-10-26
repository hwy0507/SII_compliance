"""Plot completed, independently reviewed paired prefix diagnostics."""
from pathlib import Path
import argparse
import hashlib
import json


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(run):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    review_path = run / 'INDEPENDENT_REVIEW.json'
    review = json.loads(review_path.read_text())
    assert review['passed'] and json.loads((run / 'FINISHED.json').read_text())['completed']
    assert review['report_sha256'] == sha(run / 'REVIEW.json')
    modes = ['independent', 'episode_constant']
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), layout='constrained')
    for i, mode in enumerate(modes):
        result = review['summaries'][mode]
        rate = result['left_initial_approach'] / result['trials']
        lower, upper = result['wilson95_interval_for_prefix_exit']
        axes[0].errorbar(i, rate * 100, yerr=[[max(0., rate-lower)*100],
            [max(0., upper-rate)*100]], fmt='o', capsize=6)
        axes[0].annotate(f"{result['left_initial_approach']}/{result['trials']}",
            (i, upper*100), xytext=(0, 8), textcoords='offset points', ha='center')
    axes[0].set_xticks([0, 1], ['Independent', 'Constant base noise'])
    axes[0].set_xlim(-.5, 1.5)
    axes[0].set_ylim(bottom=-.3)
    axes[0].margins(y=.3)
    axes[0].set_ylabel('Left initial approach by 0.24 s (%)')
    axes[0].set_title('Observed frequency and Wilson 95% interval')
    actions = np.asarray([t['first_action'] for t in review['trials']
        if t['mode'] == 'independent'])
    assert actions.shape == (128, 7)
    axes[1].boxplot(actions, tick_labels=['WBC', 'dx', 'dy', 'dz', 'rx', 'ry', 'rz'])
    axes[1].set_ylabel('Public action channel value')
    axes[1].set_title('128 shared first actions (both modes identical)')
    for ax in axes:
        ax.grid(axis='y', alpha=.25)
    fig.suptitle('Frozen formal13: one condition, 128 paired prefixes; not task success')
    target = run / 'prefix_noise_results.png'
    assert not target.exists(), 'Do not overwrite an existing result'
    fig.savefig(target, dpi=160)
    plt.close(fig)
    (run / 'PLOT_RECEIPT.json').write_text(json.dumps(dict(
        review=dict(path=str(review_path), sha256=sha(review_path)),
        plot=dict(path=str(target), sha256=sha(target)), source_sha256=sha(Path(__file__)),
        new_physics=0, optimizer_updates=0), indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    main(parser.parse_args().run)
