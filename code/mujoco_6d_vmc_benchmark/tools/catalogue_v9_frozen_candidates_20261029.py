"""Verify all existing v9 fits and catalogue validation-only candidate ranks.

No fitting, checkpoint changes, physics, or final model selection. The catalogue
can support a prospective common closed-loop eligibility rule after review.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


DATA_SHA = '120173888964ee0545393cd0d2685c794f7aa261626463fa7c10fc981b9c6407'
FAMILIES = ('esn_ridge', 'rnn_scratch', 'mlp_scratch')
SEEDS = (2026102801, 2026102802, 2026102803)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def build(training):
    execution_path = training/'execution.json'
    state = read(execution_path)
    assert state['status'] == 'complete' and len(state['fits']) == 75
    data = training/'data/training_data.npz'
    assert sha(data) == DATA_SHA
    data_meta = read(training/'data/DATA_COMPLETE.json')
    assert data_meta['training_data_sha256'] == DATA_SHA
    assert len(data_meta['training_identities']) == 24
    assert len(data_meta['validation_identities']) == 6
    assert not set(data_meta['training_identities']) & set(data_meta['validation_identities'])
    lock = read(training/'MODEL_LOCK.json')
    assert len(lock['models']) == 9 and lock['training_data_sha256'] == DATA_SHA
    candidates = []
    seen_jobs = set()
    for job in state['fits']:
        assert job['name'] not in seen_jobs and job['status'] == 'complete'
        seen_jobs.add(job['name'])
        family, seed = job['family'], job['seed']
        assert family in FAMILIES and seed in SEEDS
        folder = Path(job['output'])
        assert folder.parent == training/'learning'
        meta_path = folder/'TRAINING_COMPLETE.json'
        assert sha(meta_path) == job['metadata_sha256']
        meta = read(meta_path)
        assert meta['seed'] == seed
        assert sha(folder/'checkpoint.npz') == job['checkpoint_sha256'] == meta['checkpoint_sha256']
        assert meta.get('training_data_sha256', meta.get('data_sha256')) == DATA_SHA
        entries = meta['candidates'] if family == 'esn_ridge' else [dict(
            name=job['name'], holdout_mse=meta['groups']['real_identity_validation']['action_mse'],
            checkpoint_sha256=meta['checkpoint_sha256'])]
        if family == 'esn_ridge':
            assert len(entries) == 12
        else:
            assert meta['updates'] == meta['selected_update'] == 32000
        for entry in entries:
            checkpoint = folder/(entry['name']+'.npz') if family == 'esn_ridge' else folder/'checkpoint.npz'
            assert sha(checkpoint) == entry['checkpoint_sha256']
            score = entry['holdout_mse']
            assert isinstance(score, (int, float)) and math.isfinite(score) and score >= 0
            candidates.append(dict(id=job['name']+'/'+entry['name'], family=family, seed=seed,
                validation_mse=score, checkpoint=str(checkpoint), checkpoint_sha256=sha(checkpoint),
                metadata=str(meta_path), metadata_sha256=sha(meta_path),
                hyperparameters=({k: entry[k] for k in ('rho', 'input_gain', 'ridge')}
                    if family == 'esn_ridge' else
                    {k: meta[k] for k in ('learning_rate', 'weight_decay', 'updates')})))
    assert len(candidates) == 108 and len({r['id'] for r in candidates}) == 108
    groups = []
    for family in FAMILIES:
        for seed in SEEDS:
            group = sorted((r for r in candidates if r['family'] == family and r['seed'] == seed),
                           key=lambda r: (r['validation_mse'], r['id']))
            assert len(group) == 12
            selected = next(m for m in lock['models'] if m['family'] == family and m['seed'] == seed)
            assert selected['validation_mse'] == group[0]['validation_mse']
            assert selected['checkpoint_sha256'] == group[0]['checkpoint_sha256']
            for rank, row in enumerate(group, 1):
                row['validation_rank'] = rank
            groups.append(dict(family=family, seed=seed, existing_candidates=12,
                original_selected_checkpoint_sha256=selected['checkpoint_sha256'],
                ordered_candidates=group))
    return dict(status='verified_existing_candidate_catalogue_not_new_model_selection',
        data_sha256=DATA_SHA, execution_sha256=sha(execution_path),
        model_lock_sha256=sha(training/'MODEL_LOCK.json'),
        data_metadata_sha256=sha(training/'data/DATA_COMPLETE.json'),
        source_sha256=sha(Path(__file__)), fits=75, candidates=108,
        train_identities=data_meta['training_identities'],
        validation_identities=data_meta['validation_identities'], groups=groups,
        limitations=['Ranks reproduce the existing teacher-history validation MSE rule only.',
            'No candidate was newly fit, deployed, or declared physically qualified.',
            'Any revised closed-loop eligibility rule needs prospective common registration.',
            'Neither office test outcomes nor unseen final-test inputs are read.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--training', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Preserve previous evidence'
    result = build(args.training.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(result['status'], result['candidates'])
