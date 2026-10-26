"""Independently check saved policy arithmetic and render the observed regression."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(root, terms_root):
    os.sched_setaffinity(0, {53})
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    report = json.loads((root/'REVIEW.json').read_text())
    terms = json.loads((terms_root/'REVIEW.json').read_text())
    assert report['passed'] and terms['passed']
    assert sha(root/'fixed_inputs.npz') == report['fixed_inputs_sha256']
    assert sha(root/'policy_values.npz') == report['policy_values_sha256']
    with np.load(root/'policy_values.npz', allow_pickle=False) as z:
        values = {k: z[k].astype(np.float64) for k in z.files}
    with np.load(root/'fixed_inputs.npz', allow_pickle=False) as z:
        unique = {name: len(np.unique(z[name+'_observations'], axis=0)) for name in ['initial', 'uniform']}
    assert unique == {'initial': 1, 'uniform': 4094}
    for first, last in [(16, 17), (17, 18), (16, 18)]:
        for name in ['initial', 'uniform']:
            a = {k: values[f'{first}_{name}_{k}'] for k in ['loc', 'scale', 'mode', 'sample']}
            b = {k: values[f'{last}_{name}_{k}'] for k in a}
            squared_ratio = (a['scale']/b['scale'])**2
            mean_ratio = ((a['loc']-b['loc'])/b['scale'])**2
            kl = .5*np.sum(squared_ratio+mean_ratio-1-2*np.log(a['scale']/b['scale']), axis=1)
            checks = dict(raw_mode_abs_delta=np.abs(b['mode']-a['mode']),
                public0_mode_abs_delta=.5*np.abs(b['mode'][:, 0]-a['mode'][:, 0]),
                coupled_sample_abs_delta=np.abs(b['sample']-a['sample']),
                latent_gaussian_kl_old_to_new=kl)
            expected = report['drifts'][f'{first}_to_{last}'][name]
            for metric, array in checks.items():
                actual = dict(mean=array.mean(), p95=np.percentile(array, 95), maximum=array.max())
                for stat, value in actual.items():
                    np.testing.assert_allclose(value, expected[metric][stat], rtol=1e-12, atol=1e-10)
    old, new = terms['cycles']
    assert old['cycle'] == 17 and new['cycle'] == 18
    ids = sorted(old['per_condition'])
    assert len(ids) == 30 and set(ids) == set(new['per_condition'])
    components = list(terms['mean_term_deltas'])
    matrix = np.asarray([[new['per_condition'][case][k]-old['per_condition'][case][k]
                          for k in components] for case in ids])
    np.testing.assert_allclose(matrix.mean(axis=0), list(terms['mean_term_deltas'].values()), rtol=0, atol=1e-12)
    delta = matrix.sum(axis=1)
    penetration = matrix[:, components.index('penetration')]
    np.testing.assert_allclose(delta.mean(), terms['sum_of_mean_term_deltas'], rtol=0, atol=1e-12)
    penetration_share = float(penetration.mean()/delta.mean())
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), constrained_layout=True)
    x = np.arange(len(ids))
    labels = [({'passive': 'P', 'active_short': 'S', 'active_long': 'L'}[
        'passive' if case.startswith('passive') else '_'.join(case.split('_')[:2])])+case.split('_')[-1] for case in ids]
    axes[0, 0].bar(x-.18, delta, .36, label='Total reward change')
    axes[0, 0].bar(x+.18, penetration, .36, label='Penetration term change')
    axes[0, 0].set(title='Complete17 to18: saved per-condition reward terms', ylabel='Reward change')
    axes[0, 0].set_xticks(x, labels, rotation=90, fontsize=7)
    axes[0, 0].legend(fontsize=8)
    cycles = [16, 17, 18]
    public0 = [float(((values[f'{c}_initial_mode'][:, 0]+1)/2).mean()) for c in cycles]
    axes[0, 1].plot(cycles, public0, marker='o')
    axes[0, 1].set(title='Same initial input: public0 = (raw0 + 1) / 2',
        xlabel='Frozen cycle', ylabel='Larger values slow nominal WBC', ylim=(.90, 1.005), xticks=cycles)
    pairs = ['16_to_17', '17_to_18', '16_to_18']
    for offset, name in [(-.18, 'initial'), (.18, 'uniform')]:
        axes[1, 0].bar(np.arange(3)+offset,
            [report['drifts'][p][name]['raw_mode_abs_delta']['mean'] for p in pairs], .36, label=name)
        axes[1, 1].bar(np.arange(3)+offset,
            [report['drifts'][p][name]['latent_gaussian_kl_old_to_new']['mean'] for p in pairs], .36, label=name)
    axes[1, 0].set(title='Mean absolute raw mode change (7 channels)', ylabel='Raw action units')
    axes[1, 1].set(title='Mean latent diagonal-normal KL, old to new', ylabel='KL (log scale)', yscale='log')
    for ax in axes[1]:
        ax.set_xticks(np.arange(3), ['16→17', '17→18', '16→18']); ax.legend()
    for ax in axes.flat:
        ax.grid(alpha=.2, axis='y')
    fig.suptitle('Frozen-input diagnostics: initial510 rows = 1 unique input; uniform4096 = 4094 unique\n'
                 'P/S/L: passive / active short / active long. Saved arithmetic only; no causal or convergence claim.')
    fig.savefig(root/'policy_drift_and_reward.png', dpi=150)
    plt.close(fig)
    result = dict(passed=True, time=time.time(), unique_inputs=unique,
        mean_reward_delta=float(delta.mean()), penetration_delta=float(penetration.mean()),
        penetration_share_of_net_reward_decline=penetration_share,
        worse_conditions=int((delta < 0).sum()), better_conditions=int((delta > 0).sum()),
        plot_sha256=sha(root/'policy_drift_and_reward.png'),
        review_inputs={str(p): sha(p) for p in [root/'REVIEW.json', terms_root/'REVIEW.json',
            root/'fixed_inputs.npz', root/'policy_values.npz']},
        optimizer_updates=0, new_physics=0, forward_inference_calls=0,
        limitation='Independent saved-value arithmetic/hash review, not an independent neural forward or dynamics replay. Initial cohort is one unique observation, not510 independent conditions. Latent KL and action differences do not establish causal effects on penetration or task success. No numerical stationarity threshold or automatic stop.')
    (root/'SAVED_VALUE_REVIEW.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--terms-root', type=Path, required=True)
    args = parser.parse_args()
    main(args.root, args.terms_root)
