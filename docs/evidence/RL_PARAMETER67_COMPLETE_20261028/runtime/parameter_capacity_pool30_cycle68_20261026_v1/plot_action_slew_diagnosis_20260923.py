"""Plot saved action replay evidence; no simulation or policy changes."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    evidence = json.loads(args.evidence.read_text())
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True, layout='constrained')
    for ax, method, seed in zip(axes, ('esn','mlp'), (9301,9302)):
        row = next(r for r in evidence['rows'] if r['method'] == method and r['fixture']['seed'] == seed)
        replay = row['last_1s_action_execution_replay']
        time = np.array([r['pre_step_time_s'] for r in replay])
        raw = np.array([r['raw_yield_twist'][0] for r in replay])
        filtered = np.array([r['slew_filtered_yield_twist'][0] for r in replay])
        ax.step(time, raw, where='post', color='#487fb6', lw=1.6, label='Raw x-yield request')
        ax.step(time, filtered, where='post', color='#c45436', lw=2, label='After shared slew limiter (replay)')
        ax.axhline(0, color='#777777', lw=.7)
        ax.axhline(raw.mean(), color='#487fb6', ls=':', lw=1)
        ax.axhline(filtered.mean(), color='#c45436', ls=':', lw=1)
        ax.set_title(f'{method.upper()} / fixture {seed}: raw mean {raw.mean():+.5f}, slew mean {filtered.mean():+.5f} m/s', loc='left', fontsize=11)
        ax.set_ylabel('Requested x-yield (m/s)')
        ax.grid(alpha=.2)
        ax.legend(loc='upper right', fontsize=8)
    axes[-1].set_xlabel('Action time (s), before the 40 ms control step')
    fig.suptitle('Alternating policy output can acquire a directional bias under a stateful slew limit', fontsize=12)
    fig.supxlabel('Offline replay of recorded actions; these are requests before joint/torque projection, not measured end-effector velocity.', fontsize=8)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=170)
    plt.close(fig)
    print(args.output)


if __name__ == '__main__':
    main()
