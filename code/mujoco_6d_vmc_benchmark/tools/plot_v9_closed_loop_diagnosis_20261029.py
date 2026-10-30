"""Plot saved condition000 trajectories, not fabricated training curves."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--diagnosis', required=True, type=Path)
    p.add_argument('--regression', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    assert not a.output.exists()
    d = json.loads(a.diagnosis.read_text())
    fig, axes = plt.subplots(2, 3, figsize=(13, 6), sharex=True)
    for col, suffix in enumerate(('01', '02', '03')):
        for family, color in (('esn_ridge', '#d64b35'), ('rnn_scratch', '#347bb7'), ('mlp_scratch', '#398c50')):
            row = next(r for r in d['rows'] if family in r['method'] and r['method'].endswith(suffix))
            trace = a.regression/'evaluation'/(row['method']+'__'+row['condition'])/'rollout.npz'
            assert hashlib.sha256(trace.read_bytes()).hexdigest() == row['trace_sha256']
            with np.load(trace, allow_pickle=False) as z:
                t = z['time']; visible = t <= 8
                axes[0, col].plot(t[visible], z['task_position_error_m'][visible]*1000, color=color, label=family.split('_')[0].upper())
                axes[1, col].plot(t[visible], np.abs(z['applied_action'][visible, 1:]).max(1), color=color)
        axes[0, col].set_title('Model seed 20261028'+suffix)
        axes[1, col].axhline(1, color='black', ls='--', lw=.8)
        axes[1, col].axvline(2.12, color='#d64b35', ls=':', lw=.8)
        axes[1, col].set_xlabel('Simulation time (s)')
        axes[1, col].set_ylim(-.02, 1.08)
        for ax in axes[:, col]:
            ax.grid(alpha=.2)
    axes[0, 0].set_ylabel('Task tracking error (mm)')
    axes[1, 0].set_ylabel('Max |applied residual action|')
    axes[0, 0].legend()
    fig.suptitle('Saved v9 office transfer condition 000: early ESN saturation\nRod starts at 12.824 s; stage/reference changes contribute to tracking error')
    fig.tight_layout()
    fig.savefig(a.output, dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    main()
