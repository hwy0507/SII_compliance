"""Check saved actor-gradient arithmetic and plot the fixed conditional cohorts.

This reviewer does not re-run neural inference or claim independent dynamics.
It checks the saved exact-objective gradient decomposition, source/parent/row
bindings, cohort coverage and independently recomputes all norms/cosines.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(run):
    os.sched_setaffinity(0, {53})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    reg = json.loads((run/'REGISTRATION.json').read_text())
    report = json.loads((run/'REVIEW.json').read_text())
    assert report['passed'] and report['full_network_optimizer_rng_unchanged']
    assert report['initial_learner_digest'] == report['final_learner_digest']
    assert report['replay_unchanged'] and report['weights_saved'] is False
    assert report['optimizer_updates'] == report['new_physics'] == report['replay_writes'] == 0
    for key in ['checkpoint', 'training_registration', 'cycle_review', 'health_review']:
        assert sha(reg[key]['path']) == reg[key]['sha256']
    for ref in reg['sources'].values():
        assert sha(ref['path']) == ref['sha256']
    assert sha(run/'selected_rows.npz') == report['selected_rows_sha256']
    assert sha(run/'actor_gradients.npz') == report['actor_gradients_sha256']
    failed = reg.get('failed_diagnostic')
    if failed:
        for key in ['registration', 'failure', 'source', 'selected_rows']:
            assert sha(failed[key]['path']) == failed[key]['sha256']
        with np.load(failed['selected_rows']['path']) as old, np.load(run/'selected_rows.npz') as new:
            assert set(old.files) == set(new.files)
            for key in old.files:
                np.testing.assert_array_equal(old[key], new[key])
    ck = torch.load(reg['checkpoint']['path'], map_location='cpu', weights_only=False)
    clock = ck['replay']['arrays']['observations'][:, 48]
    initial = np.flatnonzero(clock == 1)
    early = np.flatnonzero(clock >= np.float32((1375-31)/1375))
    assert len(initial) == report['initial_population'] == 450
    assert len(early) == report['early32_population'] == 14400
    assert len(clock) == report['replay_rows']
    groups = ['initial', 'early32', 'uniform']
    with np.load(run/'selected_rows.npz') as selected:
        for name in groups:
            rows = selected[name]
            result = report['cohorts'][name]
            assert len(rows) == result['sample_count'] == 8192
            assert hashlib.sha256(rows.tobytes()).hexdigest() == result['row_ids_sha256']
            assert len(np.unique(rows)) == result['unique_rows']
            assert np.all((rows >= 0) & (rows < len(clock)))
            assert np.sum(clock[rows] == 1) == result['initial_rows_sampled']
            assert np.sum(clock[rows] >= np.float32((1375-31)/1375)) == result['early_rows_sampled']
            if name == 'initial':
                assert np.isin(rows, initial).all()
            elif name == 'early32':
                assert np.isin(rows, early).all() and len(np.unique(rows)) == 8192
            else:
                assert len(np.unique(rows)) == 8192
            assert result['official_loss_exact_formula_verified']
            np.testing.assert_allclose(result['q_loss_term']+result['entropy_loss_term'],
                result['actor_loss'], rtol=2e-6, atol=2e-6)
            np.testing.assert_allclose(-report['temperature']*result['sampled_entropy'],
                result['entropy_loss_term'], rtol=2e-6, atol=2e-6)
    gradients = dict(np.load(run/'actor_gradients.npz'))
    norms = {k: float(np.linalg.norm(v)) for k, v in gradients.items()}
    assert all(np.isfinite(v).all() for v in gradients.values())
    for name in groups:
        difference = gradients[name+'_q']+gradients[name+'_entropy']-gradients[name+'_official']
        np.testing.assert_allclose(gradients[name+'_q']+gradients[name+'_entropy'],
            gradients[name+'_official'], rtol=2e-4, atol=2e-6)
        assert float(np.max(np.abs(difference))) == report['cohorts'][name]['gradient_sum_max_error']
    for name, norm in norms.items():
        np.testing.assert_allclose(norm, report['gradient_norms'][name], rtol=1e-12)
    cosines = {}
    for a, av in gradients.items():
        for b, bv in gradients.items():
            if a < b:
                denominator = norms[a]*norms[b]
                value = float(np.dot(av, bv)/denominator) if denominator else None
                cosines[a+'__'+b] = value
                if value is not None:
                    np.testing.assert_allclose(value, report['gradient_cosines'][a+'__'+b], rtol=1e-12, atol=1e-12)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout='constrained')
    entropy = [report['cohorts'][g]['sampled_entropy'] for g in groups]
    axes[0, 0].bar(groups, entropy)
    axes[0, 0].set_ylabel('Sampled differential entropy (raw action)')
    axes[0, 0].set_title('State-conditional exploration; frozen formal14')
    for g in groups:
        axes[0, 1].plot(range(7), report['cohorts'][g]['pre_tanh_std']['mean'], 'o-', label=g)
    axes[0, 1].set_xticks(range(7), ['WBC', 'dx', 'dy', 'dz', 'rx', 'ry', 'rz'])
    axes[0, 1].set_yscale('log')
    axes[0, 1].set_ylabel('Mean underlying Gaussian standard deviation')
    axes[0, 1].set_title('Pre-tanh scale; not transformed stddev helper')
    axes[0, 1].legend()
    x = np.arange(3)
    for offset, component in [(-.25, 'q'), (0, 'entropy'), (.25, 'official')]:
        axes[1, 0].bar(x+offset, [norms[g+'_'+component] for g in groups], width=.25, label=component)
    axes[1, 0].set_xticks(x, groups)
    axes[1, 0].set_yscale('log')
    axes[1, 0].set_ylabel('Actor-parameter gradient L2 norm')
    axes[1, 0].set_title('Q term + entropy term = official actor gradient')
    axes[1, 0].legend()
    matrix = np.eye(3)
    for i, a in enumerate(groups):
        for j, b in enumerate(groups):
            if i != j:
                keys = sorted([a+'_official', b+'_official'])
                matrix[i, j] = cosines['__'.join(keys)]
    im = axes[1, 1].imshow(matrix, vmin=-1, vmax=1, cmap='coolwarm')
    axes[1, 1].set_xticks(x, groups)
    axes[1, 1].set_yticks(x, groups)
    for i in range(3):
        for j in range(3):
            axes[1, 1].text(j, i, f'{matrix[i,j]:.3f}', ha='center', va='center')
    axes[1, 1].set_title('Sampled gradient cosine; not an Adam update')
    fig.colorbar(im, ax=axes[1, 1])
    fig.suptitle('Read-only 8192-row cohorts: no optimizer updates or new physics')
    plot = run/'initial_actor_gradients.png'
    assert not plot.exists()
    fig.savefig(plot, dpi=150)
    plt.close(fig)
    result = dict(time=time.time(), passed=True, report_sha256=sha(run/'REVIEW.json'),
        source_sha256=sha(Path(__file__)), gradient_norms=norms, gradient_cosines=cosines,
        selected_rows_sha256=sha(run/'selected_rows.npz'),
        actor_gradients_sha256=sha(run/'actor_gradients.npz'), plot_sha256=sha(plot),
        failed_attempt_preserved=bool(failed), identical_cohorts_to_failed_attempt=bool(failed),
        new_physics=0, optimizer_updates=0, convergence_claim=False,
        limitation='Independent saved-gradient arithmetic, selected-row/parent/source verification and plot; no neural-model re-inference, fresh gradient computation or dynamics rerun. Exact official objective equivalence and state preservation were checked by the diagnostic itself. Fixed sampled Euclidean gradients do not predict an actual Adam update or task improvement.')
    (run/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(entropy=dict(zip(groups, entropy)), cosine=matrix.tolist()), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    main(parser.parse_args().run)
