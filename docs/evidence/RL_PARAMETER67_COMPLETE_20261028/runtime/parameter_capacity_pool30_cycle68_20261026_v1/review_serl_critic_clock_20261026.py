"""Read-only audit and plot of the registered finite critic-clock comparison."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(root):
    reg = json.loads((root / 'REGISTRATION.json').read_text())
    out = root / 'probe'
    result = json.loads((out / 'FINISHED.json').read_text())
    gate = json.loads((out / 'CLOCK_GATE.json').read_text())
    assert result['passed'] and gate['passed']
    assert result['registration_sha256'] == sha(root / 'REGISTRATION.json')
    assert result['checkpoint_sha256'] == reg['checkpoint']['sha256']
    for name in ['checkpoint', 'review', 'clock']:
        assert sha(reg[name]['path']) == reg[name]['sha256']
    runtime = root.parents[1] / 'runtime' / root.name
    for name, expected in reg['source_hashes'].items():
        assert sha(runtime / name) == expected
    assert gate['new_optimizer_updates'] == 0
    assert gate['initial_critic_max_abs_difference'] == 0
    assert gate['initial_actor_exact'] and gate['actor_invariant_to_clock']
    assert gate['original_full_agent_state_recoverable_exactly']
    assert gate['new_weights_and_moments_zero'] and len(gate['added_paths']) == 8
    assert result['new_physics'] == 0 and not result['auxiliary_weights_saved']
    assert result['auxiliary_critic_updates'] == 32000
    assert result['auxiliary_actor_updates'] == 4000 and result['parent_unchanged']
    arms = {row['arm']: row for row in result['results']}
    assert set(arms) == {'critic_clock', 'original'}
    assert arms['critic_clock']['initial'] == arms['original']['initial']
    assert arms['critic_clock']['sampling_rng_sha256'] == arms['original']['sampling_rng_sha256']
    for name, arm in arms.items():
        assert json.loads((out / (name + '.json')).read_text()) == arm
        assert [row['outer_updates'] for row in arm['curve']] == list(range(100, 2001, 100))
        assert [row['critic_updates'] for row in arm['curve']] == list(range(800, 16001, 800))
        assert arm['parent_unchanged']
        for row in arm['curve']:
            assert all(np.isfinite(value) for value in row['diagnostic'].values())
            assert all(np.isfinite(value) for value in row['metrics'].values())
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
    keys = ['terminal_mae', 'terminal_p95', 'terminal_max', 'replay_q_mean', 'td_mae', 'temperature']
    for ax, key in zip(axes.flat, keys):
        for name, arm in arms.items():
            ax.plot([0] + [r['outer_updates'] for r in arm['curve']],
                    [arm['initial'][key]] + [r['diagnostic'][key] for r in arm['curve']], label=name)
        ax.set_title(key)
        ax.set_xlabel('Outer updates (8 critic : 1 actor)')
        ax.grid(alpha=.25)
    axes.flat[0].legend()
    fig.suptitle('Frozen replay diagnostic: no online episodes or promoted weights')
    fig.savefig(root / 'COMPARISON.png', dpi=150)
    plt.close(fig)
    receipt = dict(passed=True, source_sha256=sha(__file__),
                   registration_sha256=sha(root / 'REGISTRATION.json'),
                   finished_sha256=sha(out / 'FINISHED.json'),
                   gate_sha256=sha(out / 'CLOCK_GATE.json'),
                   plot_sha256=sha(root / 'COMPARISON.png'),
                   checkpoint_verified_unchanged=True, same_initial_diagnostics=True,
                   same_sampling_rng=True, records_per_arm=20,
                   auxiliary_critic_updates=32000, auxiliary_actor_updates=4000,
                   new_review_optimizer_updates=0, new_review_physics=0,
                   final={name: arm['final'] for name, arm in arms.items()},
                   conclusion='Mean terminal error improves modestly; p95 worsens versus control, maximum error and Q bias persist. No online or convergence claim.')
    (root / 'REVIEW.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)
