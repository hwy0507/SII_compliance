"""Summarize six completed formal cycles from existing audited reports only."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import statistics
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(base, output):
    os.sched_setaffinity(0, {53})
    output.mkdir(exist_ok=False)
    sources, methods = [], {m: [] for m in ['impedance', 'admittance', 'vmc']}
    previous = {}
    for cycle in range(19, 25):
        prefix = 'parameter_capacity_pool30' if cycle == 24 else 'parameter_pool30'
        root = base/'runs'/f'{prefix}_cycle{cycle}_review_20261026_v1'
        data = {}
        for name in ['FINISHED.json', 'REVIEW.json', 'health/DIAGNOSIS.json']:
            path = root/name
            data[name] = json.loads(path.read_text())
            sources.append(dict(path=str(path), sha256=sha(path)))
        assert data['FINISHED.json']['completed'] and data['REVIEW.json']['passed']
        for method in methods:
            r = data['REVIEW.json']['methods'][method]
            h = data['health/DIAGNOSIS.json']['methods'][method]
            assert r['checkpoint_sha256'] == h['checkpoint_sha256']
            assert r['optimizer_and_network_finite'] and h['network_state_unchanged']
            episodes = {e['condition']: e for e in h['episodes']}
            assert len(episodes) == len(h['episodes']) == r['conditions'] == 30
            assert all(e['cycle'] == cycle for e in episodes.values())
            assert sum(e['task_success'] for e in episodes.values()) == r['task']
            assert sum(e['strict_success'] for e in episodes.values()) == r['strict']
            assert math.isclose(statistics.mean(e['reward'] for e in episodes.values()), r['reward_mean'], abs_tol=1e-10)
            changes = {}
            if method in previous:
                old = previous[method]
                assert episodes.keys() == old.keys()
                for field in ['task_success', 'strict_success']:
                    changes[field] = dict(
                        gained=sorted(k for k in episodes if episodes[k][field] and not old[k][field]),
                        lost=sorted(k for k in episodes if old[k][field] and not episodes[k][field]))
            point = dict(cycle=cycle, steps=r['steps'], reward_mean=r['reward_mean'],
                task=r['task'], strict=r['strict'], aborts=r['aborts'],
                q_loss_last1000=h['recent_optimizer']['agent_train/q_loss']['mean'],
                terminal_mae=h['terminal_q_absolute_error']['mean'],
                inbag_terminal_mae=h['terminal_q_in_bag_absolute_error']['mean'],
                q_mean=h['sampled_q_values']['mean'], changes=changes)
            assert all(math.isfinite(v) for v in point.values() if isinstance(v, float))
            methods[method].append(point)
            previous[method] = episodes
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    keys = ['reward_mean', 'strict', 'q_loss_last1000', 'terminal_mae', 'inbag_terminal_mae', 'q_mean']
    for method, points in methods.items():
        for axis, key in zip(axes.flat, keys):
            axis.plot([p['cycle'] for p in points], [p[key] for p in points], marker='o', label=method)
            axis.set(title=key, xlabel='Formal cycle')
            axis.axvline(23.5, color='grey', linestyle='--', alpha=.6)
            axis.grid(alpha=.25)
    axes[0, 0].legend()
    fig.suptitle('Audited online training; dashed boundary: replay capacity 1m to 2m')
    plot = output/'parameter_cycles19_24.png'
    fig.savefig(plot, dpi=140)
    plt.close(fig)
    summary = {}
    for method, points in methods.items():
        summary[method] = {key: dict(minimum=min(p[key] for p in points), maximum=max(p[key] for p in points),
            mean=statistics.mean(p[key] for p in points), population_std=statistics.pstdev(p[key] for p in points))
            for key in ['reward_mean', 'strict', 'q_loss_last1000', 'inbag_terminal_mae']}
    report = dict(passed=True, time=time.time(), methods=methods, summary=summary, sources=sources,
        source_sha256=sha(Path(__file__)), plot_sha256=sha(plot), new_physics=0, optimizer_updates=0,
        convergence_claim=False,
        scope='Arithmetic checks and plots of saved, previously audited reports. Six sequential online cycles are dependent observations, not independent seeds or frozen-policy evaluation. No significance test or post-hoc convergence threshold. Cycle24 retains rows beyond original1m and therefore changes replay sampling distribution relative to ring overwrite.')
    (output/'REVIEW.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.base, args.output)
