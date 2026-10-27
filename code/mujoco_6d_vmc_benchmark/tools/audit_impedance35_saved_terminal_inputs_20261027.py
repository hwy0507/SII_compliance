"""Explore saved impedance terminal inputs and per-critic error transfer; no inference."""
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
    reg = json.loads((root/'REGISTRATION.json').read_text())
    assert sha(__file__) == reg['source_sha256']
    assert reg['cycles'] == [34, 35] and reg['controller'] == 'impedance'
    assert not (root/'REVIEW.json').exists()
    for ref in reg['inputs'].values():
        assert sha(ref['path']) == ref['sha256']
    def read(key):
        return json.loads(Path(reg['inputs'][key]['path']).read_text())
    with np.load(reg['inputs']['anchor_values']['path'], allow_pickle=False) as data:
        old = {k: data[k].copy() for k in data.files}
    with np.load(reg['inputs']['follow_values']['path'], allow_pickle=False) as data:
        new = {k: data[k].copy() for k in data.files}
    follow, difference = read('follow_review'), read('row_differences')
    assert follow['passed'] and difference['passed'] and follow['fixed_anchor_rows'] == 1045
    assert sha(reg['inputs']['follow_values']['path']) == follow['values_sha256']
    features = old['features'].astype(np.float64)
    assert features.shape == (1045, 55) and np.isfinite(features).all()
    np.testing.assert_array_equal(old['replay_indices'], new['indices'][:1045])
    np.testing.assert_array_equal(old['rewards'], new['rewards'][:1045])
    np.testing.assert_array_equal(old['masks'], new['masks'][:, :1045])
    masks, reward = old['masks'], old['rewards']
    before = masks * (old['q'] - reward[None]) ** 2
    after = masks * (new['q'][:, :1045].astype(np.float64) - reward[None]) ** 2
    assert np.isclose(before.sum(), follow['fixed1045_masked_sse_before'], rtol=1e-13)
    assert np.isclose(after.sum(), follow['fixed1045_masked_sse_after'], rtol=1e-13)
    unique, inverse, counts = np.unique(features, axis=0, return_inverse=True, return_counts=True)
    duplicate_groups = [np.flatnonzero(inverse == group) for group in np.flatnonzero(counts > 1)]
    conflicts = [v for v in duplicate_groups if len(np.unique(reward[v])) > 1]
    metadata = {}
    for key in ['transitions11', 'transitions31', 'transitions34']:
        with Path(reg['inputs'][key]['path']).open() as stream:
            for line in stream:
                row = json.loads(line)
                if row['done']:
                    metadata[row['step']-1] = row
    assert difference['top10_increases'][0]['replay_index'] == 484123
    assert difference['top10_increases'][1]['replay_index'] == 1306248
    assert follow['focus']['replay_index'] == 1432256
    specifications = [(484123, 4, 'Largest saved fixed-row SSE increase'),
                      (1306248, 1, 'Second-largest saved fixed-row SSE increase'),
                      (1432256, 4, 'Previously registered focus and its formerly dominant in-bag critic')]
    pairs = []
    for index, critic, reason in specifications:
        i = int(np.flatnonzero(old['replay_indices'] == index)[0])
        assert masks[critic, i] == 1
        eligible = np.flatnonzero((np.sign(reward) != np.sign(reward[i])) & (masks[critic] == 1))
        distance = np.linalg.norm(features[eligible] - features[i], axis=1)
        j = int(eligible[np.argmin(distance)])
        neighbor = int(old['replay_indices'][j])
        entries = []
        for position in [i, j]:
            idx = int(old['replay_indices'][position])
            item = metadata[idx]
            assert np.float32(item['reward']) == reward[position]
            entries.append(dict(replay_index=idx, cycle=item['cycle'], condition=item['condition'],
                reward=float(reward[position]), task_success=item['reward_terms']['task_success'],
                strict_success=item['reward_terms']['strict_success'],
                terminal_bonus=item['reward_terms']['terminal'],
                completion_efficiency=item['reward_terms']['completion_efficiency'],
                masks=masks[:, position].tolist(), q34=old['q'][:, position].tolist(),
                q35=new['q'][:, position].astype(float).tolist()))
        pairs.append(dict(focus_index=index, critic=critic, selection=reason,
            opposite_label_inbag_neighbor=neighbor, eligible_count=len(eligible),
            full_input_l2=float(distance.min()), observation50_l2=float(np.linalg.norm(features[i, :50]-features[j, :50])),
            raw_action5_l2=float(np.linalg.norm(features[i, 50:]-features[j, 50:])),
            maximum_absolute_coordinate_difference=float(np.max(np.abs(features[i]-features[j]))),
            entries=entries))
    per_before, per_after = before.sum(axis=1), after.sum(axis=1)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    x = np.arange(5)
    axes[0].bar(x-.18, per_before, width=.36, label='34')
    axes[0].bar(x+.18, per_after, width=.36, label='35')
    axes[0].set(title='Same 1045 terminal rows', xlabel='Critic index', ylabel='In-bag squared error sum', xticks=x)
    axes[0].legend()
    axes[1].bar(x, per_after-per_before)
    axes[1].axhline(0, color='black', linewidth=.7)
    axes[1].set(title='Change in saved terminal error', xlabel='Critic index', ylabel='SSE(35) minus SSE(34)', xticks=x)
    for axis in axes:
        axis.grid(alpha=.2)
    fig.suptitle('Exploratory saved-value diagnosis; no causal or irreducible-error claim')
    plot = root/'per_critic_terminal_transfer.png'
    fig.savefig(plot, dpi=140)
    plt.close(fig)
    for ref in reg['inputs'].values():
        assert sha(ref['path']) == ref['sha256']
    result = dict(passed=True, time=time.time(), source_sha256=sha(__file__),
        terminal_count=1045, unique_full_inputs=len(unique), duplicate_input_groups=len(duplicate_groups),
        exact_duplicate_groups_with_different_rewards=len(conflicts),
        per_critic_masked_sse34=per_before.tolist(), per_critic_masked_sse35=per_after.tolist(),
        per_critic_sse_change=(per_after-per_before).tolist(), pairs=pairs, plot_sha256=sha(plot),
        new_neural_inference=0, new_physics=0, optimizer_updates=0, replay_writes=0,
        limitation='Exploratory selection after complete35. Distances use the existing normalized observation50 plus raw action5 without new rescaling; Euclidean proximity is not learned-network distance or proof of indistinguishability. No exact duplicate conflict in this finite saved set would not rule out partial observability or approximation limits. Different conditions, actions and historical outcomes remain distinct. Terminal-row observations precede the last action interval; these are not final physical-state observations. Excludes ordinary TD loss and historical GPU batch dynamics. No new reward, feature, learning-rate or gate changes.',
        convergence_claim=False)
    (root/'REVIEW.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        (args.root/'FAILURE.json').write_text(json.dumps(dict(time=time.time(), error=repr(error)))+'\n')
        raise
