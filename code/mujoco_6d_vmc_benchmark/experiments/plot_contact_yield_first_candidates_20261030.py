"""Audited first-candidate learning diagnostics; no selection or test access."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read, sha, write
from office_mlp_rnn_20261002 import OfficeMLPRNN
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN

TRAINING = ROOT/'outputs/contact_yield_scrape_retrain_20261030_v1'
DATA_SHA = '67c01021964857020a039a644a9ff6a5b67735c034d45bb7cc5c84b53cf0691b'
SEED = 2026102801


def build(prefix):
    paths = [Path(str(prefix)+ext) for ext in ('.png', '.pdf', '.json')]
    assert not any(p.exists() for p in paths)
    data = TRAINING/'data/training_data.npz'
    assert sha(data) == DATA_SHA
    state = read(TRAINING/'execution.json')
    metadata = read(TRAINING/'data/DATA_COMPLETE.json')
    assert metadata['training_data_sha256'] == DATA_SHA
    sources = read(TRAINING/'FITTING_SOURCE.json')['source_hashes']
    for name in ('office_mlp_rnn_20261002.py', 'office_vmc_memory_esn_20260927.py'):
        assert sources['scripts/'+name] == sha(ROOT/'scripts'/name)
    with np.load(data, allow_pickle=False) as z:
        obs, target, episodes, train = [z[k].copy() for k in (
            'observation', 'requested_teacher_action', 'episode', 'train')]
    assert obs.shape == (15750, 48) and target.shape == (15750, 7)
    scene = np.empty(len(episodes), dtype='U6')
    for item in metadata['lineage']:
        scene[episodes == item['episode']] = item['scene']
    fixed = [('ESN', f'esn_ridge_s{SEED}'),
             ('RNN', f'rnn_scratch_s{SEED}_candidate00'),
             ('MLP', f'mlp_scratch_s{SEED}_candidate00')]
    rows, inputs, histories = [], {}, {}
    for label, name in fixed:
        fit = next(f for f in state['fits'] if f['name'] == name)
        assert fit['status'] == 'complete', name
        out = Path(fit['output'])
        files = ['TRAINING_COMPLETE.json', 'checkpoint.npz', 'exported_replay.npz']
        if label != 'ESN':
            files.append('history.json')
        bound = {str(out/n): sha(out/n) for n in files}
        info = read(out/'TRAINING_COMPLETE.json')
        assert sha(out/'checkpoint.npz') == fit['checkpoint_sha256'] == info['checkpoint_sha256']
        assert sha(out/'TRAINING_COMPLETE.json') == fit['metadata_sha256']
        assert info.get('data_sha256', info.get('training_data_sha256')) == DATA_SHA
        with np.load(out/'exported_replay.npz', allow_pickle=False) as z:
            prediction = z['prediction'].copy()
            np.testing.assert_array_equal(z['episode'], episodes)
        actor = (OfficeVMCMemoryESN if label == 'ESN' else OfficeMLPRNN)(out/'checkpoint.npz')
        actual, previous = [], None
        for ep, observation in zip(episodes, obs):
            if previous != int(ep):
                actor.reset(); previous = int(ep)
            actual.append(actor.act(observation))
        np.testing.assert_array_equal(np.asarray(actual), prediction)
        error = (prediction-target)**2
        mse = float(np.mean(error[~train]))
        expected = info['selected']['holdout_mse'] if label == 'ESN' else info['groups']['real_identity_validation']['action_mse']
        assert abs(mse-expected) < 1e-12
        if label != 'ESN':
            assert info['updates'] == info['selected_update'] == 32000
            history = read(out/'history.json')
            updates = np.asarray([h['update'] for h in history])
            assert np.all(np.diff(updates) > 0) and updates[-1] == 32000
            assert abs(history[-1]['validation_mse']-mse) < 1e-12
            assert abs(history[-1]['full_train_deployed_mse']-float(np.mean(error[train]))) < 1e-12
            histories[label] = history
        rows.append(dict(label=label, fixed_candidate=name, validation_mse=mse,
                         train_mse=float(np.mean(error[train])), actor_replay_max_abs=0,
                         validation_channel_rmse=np.sqrt(error[~train].mean(axis=0)).tolist(),
                         validation_scene_mse={s: float(np.mean(error[(~train)&(scene == s)]))
                                               for s in ('rod', 'ball', 'corner')}))
        for name, digest in bound.items():
            assert sha(Path(name)) == digest
        inputs.update(bound)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, label in zip(axes[0], ('RNN', 'MLP')):
        h = histories[label]
        ax.semilogy([x['update'] for x in h], [x['validation_mse'] for x in h], label='Development validation')
        measured = [x for x in h if 'full_train_deployed_mse' in x]
        ax.semilogy([x['update'] for x in measured], [x['full_train_deployed_mse'] for x in measured], label='Full training data')
        ax.set(title=label+' candidate00: deployed action MSE', xlabel='Optimizer updates', ylabel='Normalized action MSE')
        ax.grid(alpha=.2); ax.legend(fontsize=8)
    colors = ['#0072B2', '#009E73', '#D55E00']
    for i, row in enumerate(rows):
        axes[1, 0].bar(np.arange(3)+(i-1)*.24,
                       list(row['validation_scene_mse'].values()), .24, label=row['label'], color=colors[i])
        axes[1, 1].bar(np.arange(7)+(i-1)*.24,
                       row['validation_channel_rmse'], .24, label=row['label'], color=colors[i])
    axes[1, 0].set(yscale='log', xticks=np.arange(3), xticklabels=['Rod', 'Ball', 'Corner'],
                   ylabel='Normalized action MSE', title='Fixed candidates: development validation by scene')
    axes[1, 1].set(xticks=np.arange(7), xticklabels=['slow', 'vx', 'vy', 'vz', 'wx', 'wy', 'wz'],
                   ylabel='Normalized action RMSE', title='Fixed candidates: development validation by channel')
    for ax in axes[1]:
        ax.legend(fontsize=8); ax.grid(axis='y', alpha=.2)
    fig.suptitle('New contact-yield teacher data | seed 2026102801 | offline diagnosis only', fontsize=12)
    fig.text(.5, .015, 'ESN: analytical ridge; no gradient loss curve. Neural candidate00 is fixed, not the final grid winner. No closed-loop/test claim.',
             ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .035, 1, .96))
    prefix.parent.mkdir(parents=True, exist_ok=True)
    for path in paths[:2]:
        fig.savefig(path, dpi=180)
    plt.close(fig)
    assert sha(data) == DATA_SHA
    for name, digest in inputs.items():
        assert sha(Path(name)) == digest
    write(paths[2], dict(status='verified_fixed_first_candidate_offline_diagnostic',
                        dataset_sha256=DATA_SHA, plotter_sha256=sha(Path(__file__)),
                        input_sha256=inputs, rows=rows,
                        figure_sha256={str(p): sha(p) for p in paths[:2]},
                        model_reselection=False, test_inputs_read=False,
                        scope='First registered candidate00 and ESN seed01 only. Full deployed MSE, not last minibatch loss. No convergence criterion or physical success inferred. Entire grid and closed-loop diagnosis remain pending.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-prefix', type=Path, required=True)
    args = parser.parse_args(); build(args.output_prefix.resolve())
