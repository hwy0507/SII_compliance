"""Check saved fixed-terminal follow-up arithmetic without neural inference."""
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
    os.sched_setaffinity(0, {52})
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    output = root/'SAVED_VALUE_REVIEW.json'
    assert not output.exists(), 'Do not repeat a completed saved-value review'
    reg = json.loads((root/'REGISTRATION.json').read_text())
    report = json.loads((root/'REVIEW.json').read_text())
    assert report['passed'] and report['agent_weights_and_forward_rng_unchanged']
    assert report['original_anchor_observations_actions_rewards_masks_exact']
    assert report['optimizer_updates'] == report['new_physics'] == report['replay_writes'] == 0
    cycle, previous = reg['cycle'], reg['anchor_cycle']
    count = reg['expected_old_terminal_count']
    assert cycle == previous + 1 and report['cycle'] == cycle
    assert report['fixed_anchor_rows'] == count and report['new_terminal_rows'] == 30
    for ref in reg['inputs'].values():
        assert sha(ref['path']) == ref['sha256']
    path = root/f'terminal{cycle}_values.npz'
    assert sha(path) == report['values_sha256']
    with np.load(reg['inputs']['anchor_values']['path'], allow_pickle=False) as data:
        old = {key: data[key].copy() for key in data.files}
    with np.load(path, allow_pickle=False) as data:
        new = {key: data[key].copy() for key in data.files}
    assert len(old['replay_indices']) == count and len(new['indices']) == count + 30
    np.testing.assert_array_equal(old['replay_indices'], new['indices'][:count])
    np.testing.assert_array_equal(old['rewards'], new['rewards'][:count])
    np.testing.assert_array_equal(old['masks'], new['masks'][:, :count])
    assert new['q'].shape == new['masks'].shape == (5, count + 30)
    assert np.isin(new['masks'], [0, 1]).all()
    assert np.isfinite(new['q']).all() and (new['denominators'] > 0).all()
    old_squared = old['masks'] * (old['q'].astype(np.float64) - old['rewards'][None]) ** 2
    new_squared = new['masks'] * (new['q'].astype(np.float64) - new['rewards'][None]) ** 2
    contributions = sum(128 * new_squared[i] / new['denominators'][i] for i in range(5))
    np.testing.assert_allclose(contributions, new['contributions'], rtol=1e-13, atol=1e-13)
    retained = new_squared[:, :count]
    checks = {
        f'fixed{count}_masked_sse_before': old_squared.sum(),
        f'fixed{count}_masked_sse_after': retained.sum(),
        f'fixed{count}_masked_sse_ratio': retained.sum() / old_squared.sum(),
        'terminal_population_contribution': contributions.sum(),
        f'retained{count}_population_contribution': contributions[:count].sum(),
        'new30_population_contribution': contributions[count:].sum(),
        f'fixed{count}_contribution_using_old{previous}_denominator':
            sum((128 * retained[i] / old['denominators'][i]).sum() for i in range(5)),
    }
    for key, value in checks.items():
        assert np.isclose(value, report[key], rtol=1e-13, atol=1e-13), key
    positions = np.flatnonzero(old['replay_indices'] == reg['focus_replay_index'])
    assert len(positions) == 1
    focus = int(positions[0])
    item = report['focus']
    assert item['replay_index'] == reg['focus_replay_index']
    assert item['reward'] == old['rewards'][focus]
    for key, expected in [('q_before', old['q'][:, focus]), ('q_after', new['q'][:, focus]),
                          ('masks', old['masks'][:, focus])]:
        np.testing.assert_array_equal(item[key], expected)
    for key, value in [('masked_sse_before', old_squared[:, focus].sum()),
                       ('masked_sse_after', retained[:, focus].sum()),
                       ('population_contribution_after', contributions[focus])]:
        assert np.isclose(value, item[key], rtol=1e-13, atol=1e-13), key
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), constrained_layout=True)
    labels = [str(previous), str(cycle)]
    axes[0].bar(labels, [old_squared.sum(), retained.sum()])
    axes[0].set(title=f'Fixed {count} terminal rows', ylabel='Masked squared error sum')
    axes[1].bar(labels, [old_squared[:, focus].sum(), retained[:, focus].sum()])
    axes[1].set(title=f'Fixed focus row {reg["focus_replay_index"]}', ylabel='Masked squared error sum')
    axes[2].bar(labels, [old['contributions'].sum(), contributions[:count].sum()], label='Retained rows')
    axes[2].bar([str(cycle)], [contributions[count:].sum()], bottom=[contributions[:count].sum()], label='30 new rows')
    axes[2].set(title='Frozen terminal contribution', ylabel='Population weighted loss')
    axes[2].legend()
    for axis in axes:
        axis.set_xlabel('Complete checkpoint')
        axis.grid(alpha=.2)
    fig.suptitle('Fixed terminal follow-up; excludes nonterminal TD and historical minibatches')
    plot = root/f'fixed{count}_follow{cycle}.png'
    fig.savefig(plot, dpi=140)
    plt.close(fig)
    result = dict(passed=True, time=time.time(), source_sha256=sha(__file__),
        registration_sha256=sha(root/'REGISTRATION.json'), input_report_sha256=sha(root/'REVIEW.json'),
        values_sha256=sha(path), plot_sha256=sha(plot),
        fixed_anchor_rows=count, retained_sse_ratio=float(retained.sum()/old_squared.sum()),
        focus_sse_before=float(old_squared[:, focus].sum()), focus_sse_after=float(retained[:, focus].sum()),
        checked_scope='All saved row contributions, fixed indices/rewards/masks, aggregate and focus arithmetic; no repeated inference.',
        limitation='Does not explain total online loss or prove convergence; physical frozen evaluation remains separate.',
        new_physics=0, optimizer_updates=0, convergence_claim=False)
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        (args.root/'SAVED_REVIEW_FAILURE.json').write_text(json.dumps(dict(time=time.time(), error=repr(error)))+'\n')
        raise
