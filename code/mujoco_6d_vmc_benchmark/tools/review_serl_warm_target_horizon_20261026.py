"""Check paired warm-target probe receipts and render the full registered budget."""
from pathlib import Path
import argparse
import hashlib
import json
import math


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main(args):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out = args.run
    reg = json.loads((out/'REGISTRATION.json').read_text())
    report = json.loads((out/'REVIEW.json').read_text())
    assert report['passed'] and report['formal_state_unchanged']
    assert report['checkpoint'] == reg['checkpoint']
    assert sha(reg['checkpoint']['path']) == reg['checkpoint']['sha256']
    assert report['new_physics'] == 0 and report['weights_saved'] is False
    assert not list(out.rglob('*.pt')) and not list(out.rglob('*.pkl'))
    assert report['total_critic_updates'] == 32000 and report['total_actor_updates'] == 4000
    arms = report['results']; assert [a['horizon'] for a in arms] == [32, 1]
    for key in ['initial', 'initial_learner_digest', 'initial_replay_digest', 'sampled_rows_sha256', 'final_sample_rng_digest']:
        assert arms[0][key] == arms[1][key]
    for a in arms:
        assert a == json.loads((out/f"horizon{a['horizon']}_RESULT.json").read_text())
        progress = json.loads((out/f"horizon{a['horizon']}_PROGRESS.json").read_text())
        assert progress == dict(initial=a['initial'], points=a['points'])
        assert a['outer_updates'] == 2000 and a['critic_updates'] == 16000 and a['actor_updates'] == 2000
        assert a['sampled_rows'] == 65536*2000 and a['weights_saved'] is False
        assert [p['outer_updates'] for p in a['points']] == list(range(100, 2001, 100))
        for p in [a['initial']]+a['points']:
            for k, v in p.items():
                values = v if isinstance(v, list) else [v]
                assert all(math.isfinite(x) for x in values), k
            assert len(p['mode_q_gradient_abs_mean']) == 7
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    keys = ['terminal_mae', 'td1_mae', 'td32_mae', 'q_mean', 'last100_critic_loss', 'mode_public0_mean']
    for ax, key in zip(axes.flat, keys):
        for a in arms:
            points = a['points']
            ax.plot([p['outer_updates'] for p in points], [p[key] for p in points], label=f"horizon {a['horizon']}")
        ax.set_title(key); ax.set_xlabel('Auxiliary outer updates'); ax.grid(alpha=.2); ax.legend()
    fig.suptitle('Formal13 warm start: identical replay draws; no physical task result or weight promotion')
    fig.tight_layout(); fig.savefig(out/'comparison.png', dpi=150); plt.close(fig)
    result = dict(passed=True, report_sha256=sha(out/'REVIEW.json'), checkpoint=reg['checkpoint'], source_sha256=sha(__file__), expected_budget_verified=True, identical_initial_states_and_row_draws_verified=True, final={str(a['horizon']):a['points'][-1] for a in arms}, plot_sha256=sha(out/'comparison.png'), limitation='Receipt consistency and finite diagnostics reviewed; does not independently rerun numerical training or verify physical policy improvement. Visual inspection remains a separate step.', new_physics=0, optimizer_updates=0)
    (out/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    main(p.parse_args())
