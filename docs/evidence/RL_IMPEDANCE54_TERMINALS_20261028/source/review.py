"""Independently check saved Impedance53/54 terminal arithmetic; no neural rerun."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(root):
    os.sched_setaffinity(0, {0})
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    reg = json.loads((root/'REGISTRATION.json').read_text())
    report = json.loads((root/'REVIEW.json').read_text())
    assert reg['cycles'] == [53, 54] and reg['controller'] == 'impedance'
    assert report['passed'] and report['original_checkpoints_unchanged']
    assert report['optimizer_updates'] == report['new_physics'] == report['replay_writes'] == 0
    for group in reg['inputs'].values():
        for ref in group.values():
            assert sha(ref['path']) == ref['sha256']
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), constrained_layout=True)
    values = []
    for row in report['cycles']:
        cycle = row['cycle']
        path = root/f'cycle{cycle}_terminal_values.npz'
        assert sha(path) == row['values_sha256'] and row['agent_weights_and_forward_rng_unchanged']
        with np.load(path, allow_pickle=False) as data:
            saved = {key: data[key].copy() for key in data.files}
        q, reward, mask, denominator = [saved[key] for key in ['q', 'rewards', 'masks', 'denominators']]
        predicted = sum(128*mask[i]*(q[i]-reward)**2/denominator[i] for i in range(5))
        np.testing.assert_allclose(predicted, saved['contributions'], rtol=1e-14, atol=1e-14)
        assert np.isclose(predicted.sum(), row['terminal_population_loss_contribution'], rtol=1e-14, atol=1e-14)
        rank = np.argsort(-predicted)
        for count in [1, 5, 10]:
            assert np.isclose(predicted[rank[:count]].sum()/predicted.sum(), row[f'top{count}_fraction'], rtol=1e-14)
        axes[0].plot(np.arange(1, 21), np.cumsum(predicted[rank[:20]])/predicted.sum(), label=f'cycle{cycle}')
        values.append(saved)
    old, new = values
    count = len(old['replay_indices'])
    np.testing.assert_array_equal(old['replay_indices'], new['replay_indices'][:count])
    np.testing.assert_array_equal(old['rewards'], new['rewards'][:count])
    np.testing.assert_array_equal(old['masks'], new['masks'][:, :count])
    np.testing.assert_array_equal(old['features'], new['features'][:count])
    old_sse = sum((old['masks'][i]*(old['q'][i]-old['rewards'])**2).sum() for i in range(5))
    new_sse = sum((new['masks'][i, :count]*(new['q'][i, :count]-new['rewards'][:count])**2).sum() for i in range(5))
    old_denominator_new_loss = sum((128*new['masks'][i, :count]*(new['q'][i, :count]-new['rewards'][:count])**2/old['denominators'][i]).sum() for i in range(5))
    tracking = report['cycles'][1]['retained_terminal_tracking']
    for key, actual in [('masked_sse_at53', old_sse), ('masked_sse_at54', new_sse),
                        ('retained_loss_at54_using53_denominators', old_denominator_new_loss),
                        ('retained_loss_at54_using54_denominators', new['contributions'][:count].sum()),
                        ('new54_terminal_loss_contribution', new['contributions'][count:].sum())]:
        assert np.isclose(actual, tracking[key], rtol=1e-14, atol=1e-14), key
    totals = [row['terminal_population_loss_contribution'] for row in report['cycles']]
    axes[0].set(title='Terminal contribution concentration', xlabel='Highest-contributing rows', ylabel='Cumulative fraction')
    axes[0].legend()
    axes[1].bar(['53', '54'], [totals[0], new['contributions'][:count].sum()], label='Retained terminal rows')
    axes[1].bar(['54'], [new['contributions'][count:].sum()], bottom=[new['contributions'][:count].sum()], label='30 new terminal rows')
    axes[1].set(title='Frozen terminal population loss', xlabel='Complete checkpoint', ylabel='Weighted terminal contribution')
    axes[1].legend(fontsize=8)
    axes[2].bar(['53', '54'], [old_sse, new_sse])
    axes[2].set(title=f'Same {count} retained terminal rows', xlabel='Complete checkpoint', ylabel='Masked squared error sum')
    for axis in axes:
        axis.grid(alpha=.2)
    fig.suptitle('Impedance53/54 terminal diagnostics; excludes nonterminal TD and historical minibatches')
    plot = root/'terminal_concentration.png'
    fig.savefig(plot, dpi=140)
    plt.close(fig)
    result = dict(passed=True, time=time.time(), source_sha256=sha(__file__),
        input_report_sha256=sha(root/'REVIEW.json'), plot_sha256=sha(plot),
        terminal_population_contribution_ratio=totals[1]/totals[0],
        retained_masked_sse_ratio=float(new_sse/old_sse),
        new54_terminal_fraction=float(new['contributions'][count:].sum()/totals[1]),
        independent_scope='Saved-value arithmetic and hashes; no repeated neural inference or physics.',
        limitation='Frozen endpoint terminal contribution is not the logged online minibatch loss or its causal attribution. Same-row tracking keeps previous labels/masks fixed; no learner setting change, automatic continuation, or convergence claim.',
        new_physics=0, optimizer_updates=0, convergence_claim=False)
    (root/'SAVED_VALUE_REVIEW.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        (args.root/'SAVED_REVIEW_FAILURE.json').write_text(json.dumps(dict(error=repr(error), time=time.time()))+'\n')
        raise
