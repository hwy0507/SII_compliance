"""Bounded, read-only-data check of fixed-reservoir ESN optimization gaps."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--fit', type=Path, action='append', default=[])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Preserve previous audit'
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    parent = args.parent.resolve()
    sys.path.insert(0, str(parent/'source/scripts'))
    from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN
    ridge_dir = parent/'learning/esn_ridge_s2026101301_lrNone'
    candidates = [ridge_dir, parent/'learning/esn_gradient_s2026101301_lr1e-05'] + [p.resolve() for p in args.fit]
    metadata = json.loads((parent/'data/DATA_COMPLETE.json').read_text())
    data = parent/'data/training_data.npz'
    assert sha(data) == metadata['training_data_sha256']
    with np.load(data) as z:
        obs, episode, train, importance, target = [z[k].copy() for k in
            ('observation','episode','train','importance','requested_teacher_action')]
    assert not set(episode[train]) & set(episode[~train])
    with np.load(ridge_dir/'initialization.npz') as z:
        norm = z['norm'].copy()
    reference = OfficeVMCMemoryESN(ridge_dir/'checkpoint.npz')
    entries = []
    for directory in candidates:
        meta = json.loads((directory/'TRAINING_COMPLETE.json').read_text())
        cp = directory/'checkpoint.npz'
        assert sha(cp) == meta['checkpoint_sha256']
        assert meta['training_data_sha256'] == sha(data)
        assert meta['family'] in ('esn_gradient','esn_ridge') and meta['seed'] == 2026101301
        with np.load(directory/'initialization.npz') as z:
            np.testing.assert_array_equal(norm, z['norm'])
        actor = OfficeVMCMemoryESN(cp)
        for name in ('w','win','scale','leak','state_context_readout_w'):
            np.testing.assert_array_equal(getattr(reference,name),getattr(actor,name))
        assert np.all(actor.weights[-12:] == 0)
        entries.append(dict(directory=str(directory), checkpoint_sha256=sha(cp),
                            completion_sha256=sha(directory/'TRAINING_COMPLETE.json'),
                            selected_update=meta['selected_update'],
                            coeff=actor.weights[:-12]*norm[:-12,None],
                            train_sse=0., train_mass=0., train_clip_sse=0., train_n=0,
                            validation_sse=0., validation_n=0))
    gram = np.zeros((540,540)); rhs = np.zeros((540,7)); weighted_y2 = 0.; mass = 0.
    # Per-episode accumulation bounds memory; all fits share the same frozen features.
    for eid in np.unique(episode):
        ids = np.flatnonzero(episode == eid)
        reference.reset()
        features = np.asarray([reference.features(o) for o in obs[ids]])[:, :-12]/norm[None,:-12]
        y = target[ids]; w = importance[ids]
        is_train = bool(train[ids[0]])
        assert np.all(train[ids] == is_train)
        if is_train:
            gram += features.T @ (w[:,None]*features)
            rhs += features.T @ (w[:,None]*y)
            weighted_y2 += float(np.sum(w[:,None]*y*y)); mass += float(w.sum())
        for entry in entries:
            raw = features @ entry['coeff']
            clipped = np.c_[np.clip(raw[:,:1],0,1), np.clip(raw[:,1:],-1,1)]
            if is_train:
                entry['train_sse'] += float(np.sum(w[:,None]*(raw-y)**2))
                entry['train_mass'] += float(w.sum())
                entry['train_clip_sse'] += float(np.sum((clipped-y)**2)); entry['train_n'] += y.size
            else:
                entry['validation_sse'] += float(np.sum((clipped-y)**2)); entry['validation_n'] += y.size
    hessian = gram + .1*np.eye(540)
    optimum = np.linalg.solve(hessian,rhs)
    optimal_obj = float((weighted_y2-2*np.sum(optimum*rhs)+np.sum(optimum*(hessian@optimum)))/(7*mass))
    for entry in entries:
        coeff = entry.pop('coeff')
        obj = (entry.pop('train_sse') + .1*float(np.sum(coeff*coeff)))/(7*entry.pop('train_mass'))
        delta = coeff-optimum
        gap = float(np.sum(delta*(hessian@delta))/(7*mass))
        np.testing.assert_allclose(obj-optimal_obj, gap, atol=1e-10,rtol=1e-6)
        entry.update(full_train_objective=obj, optimum_objective=optimal_obj,
                     objective_gap=gap, objective_relative_gap=gap/optimal_obj,
                     normal_equation_relative_residual=float(np.linalg.norm(hessian@coeff-rhs)/np.linalg.norm(rhs)),
                     train_clipped_mse=entry.pop('train_clip_sse')/entry.pop('train_n'),
                     validation_clipped_mse=entry.pop('validation_sse')/entry.pop('validation_n'))
    assert entries[0]['normal_equation_relative_residual'] < 1e-9
    assert entries[0]['objective_relative_gap'] < 1e-9
    report = dict(status='passed', data_sha256=sha(data), source_sha256=sha(Path(__file__)),
        feature_source_sha256=sha(parent/'source/scripts/office_vmc_memory_esn_20260927.py'),
        definition='sum_train importance*||raw_action-target||^2/(7*mass) + 0.1*||normalized_coeff||^2/(7*mass)',
        scope='Fixed reservoir and seed only. Ridge is analytic global optimum for raw linear objective; does not prove closed-loop success or generalization. No checkpoint modification.',
        methods=entries)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
