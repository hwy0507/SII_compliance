"""Plot saved counterfactual evidence; no fitting or physics."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    report = json.loads(a.input.read_text())
    assert report['teacher_replay']['max_abs_error'] == 0
    assert len(report['rows']) == 9
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    colors = {'esn': '#c0392b', 'rnn': '#2471a3', 'mlp': '#148f77'}
    for method in ('esn', 'rnn', 'mlp'):
        rows = [r for r in report['rows'] if f'_{method}_' in r['method']]
        values = [r['comparison']['mse'] for r in rows]
        axes[0].scatter(np.repeat(('esn', 'rnn', 'mlp').index(method), 3), values,
                        color=colors[method], s=50, label=method.upper())
    axes[0].set(xticks=range(3), xticklabels=['ESN', 'RNN', 'MLP'], yscale='log',
                ylabel='Requested-action MSE vs counterfactual VMC',
                title='Condition 000: three seeds, own saved histories')
    point = next(r['first_saturation_comparison'] for r in report['rows']
                 if r['method'] == 'special_esn_ridge_s2026102801')
    x = np.arange(7)
    axes[1].bar(x-.19, point['student_requested'], width=.38, color=colors['esn'], label='ESN seed 01')
    axes[1].bar(x+.19, point['teacher_counterfactual_requested'], width=.38, color='#555555', label='VMC counterfactual')
    axes[1].set(xticks=x, xticklabels=['slow', 'dx', 'dy', 'dz', 'rx', 'ry', 'rz'],
                ylim=(-1.15, 1.15), ylabel='Normalized requested action',
                title=f"First ESN saturation: t={point['time_s']:.2f}s (before rod)")
    axes[1].legend(fontsize=9)
    for ax in axes:
        ax.grid(axis='y', alpha=.2)
        ax.set_axisbelow(True)
    fig.suptitle('Diagnosis only: VMC was not physically executed on student histories', fontsize=11)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.output, dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
