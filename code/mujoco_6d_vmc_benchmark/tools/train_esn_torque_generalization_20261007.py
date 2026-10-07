#!/usr/bin/env python3
"""Weighted, structurally constrained ESN readout refit; no runtime mixture.

v2 excludes the forbidden context-only columns BEFORE solving and preserves
teacher sample weights. v1 fitted those columns then erased them, so its failed
rollouts cannot isolate the effect of smoothness. All v1 evidence is retained.
Noise regularization is ||(X_noisy-X)W||², not extra teacher-label augmentation.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def write(path, value):
    temp = Path(str(path) + '.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def now(): return datetime.now(timezone.utc).isoformat()


def bounded(raw):
    out = np.clip(raw, -1., 1.)
    out[:, 0] = np.clip(raw[:, 0], 0., 1.)
    return out


def validate_data(data):
    n = len(data['observation'])
    assert data['observation'].shape == (n, 48)
    assert data['requested_teacher_action'].shape == (n, 7)
    assert data['train'].dtype == bool
    assert np.all(data['importance'] > 0)
    assert all(np.isfinite(data[k]).all() for k in
               ('observation', 'requested_teacher_action', 'importance'))
    ep, train = data['episode'], data['train']
    assert not set(ep[train]).intersection(ep[~train]), 'Identity leakage'
    assert len(np.unique(ep[train])) == 20 and len(np.unique(ep[~train])) == 5
    # Each identity must be one ordered contiguous history, without reshuffling.
    changes = np.r_[True, ep[1:] != ep[:-1]]
    assert len(ep[changes]) == len(np.unique(ep)), 'Noncontiguous history'


def features(actor, observations, episodes):
    x = np.empty((len(observations), actor.weights.shape[0]), np.float64)
    previous = None
    for i, (o, ep) in enumerate(zip(observations, episodes)):
        if ep != previous: actor.reset(); previous = ep
        x[i] = actor.features(o)
    return x


def normal_equations(x, y, importance, mask, block=1024):
    gram = np.zeros((x.shape[1], x.shape[1]))
    rhs = np.zeros((x.shape[1], y.shape[1]))
    ids = np.flatnonzero(mask)
    for start in range(0, len(ids), block):
        ix = ids[start:start+block]
        xx = x[ix]; w = importance[ix, None]
        gram += xx.T @ (w * xx)
        rhs += xx.T @ (w * y[ix])
    return gram, rhs


def temporal_gram(x, episodes, importance, train, block=1024):
    gram = np.zeros((x.shape[1], x.shape[1]))
    ids = np.flatnonzero(train[1:] & train[:-1] & (episodes[1:] == episodes[:-1])) + 1
    mass = 0.
    for start in range(0, len(ids), block):
        ix = ids[start:start+block]
        dx = x[ix] - x[ix-1]
        w = np.minimum(importance[ix], importance[ix-1])
        gram += dx.T @ (w[:, None]*dx); mass += w.sum()
    return gram * importance[train].sum()/mass


def fit(gram, rhs, smooth_gram, noise_gram, parent, ridge, smooth, action,
        noise_weight, trust, channels):
    hessian = ((1+trust+action)*gram + ridge*np.eye(len(gram)) +
               smooth*smooth_gram + noise_weight*noise_gram)
    answer = np.linalg.solve(hessian, rhs + trust*gram@parent)
    preserved = sorted(set(range(7))-set(channels))
    answer[:, preserved] = parent[:, preserved]
    return answer


def metrics(pred, target, episodes, mask):
    pair = mask[1:] & mask[:-1] & (episodes[1:] == episodes[:-1])
    delta = np.diff(pred, axis=0)[pair]
    return dict(mse=float(np.mean((pred[mask]-target[mask])**2)),
                delta_energy=float(np.mean(delta**2)),
                action_energy=float(np.mean(pred[mask]**2)),
                peak_delta=float(np.max(np.abs(delta))))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('data', 'parent-checkpoint', 'output'):
        ap.add_argument('--'+name, type=Path, required=True)
    ap.add_argument('--seed', type=int, default=2026100701)
    ap.add_argument('--noise-scale', type=float, default=0.)
    ap.add_argument('--noise-weight', type=float, default=0.)
    ap.add_argument('--ridge', type=float, nargs='+', default=[.1])
    ap.add_argument('--smooth-weight', type=float, nargs='+', default=[0., .003, .01, .03])
    ap.add_argument('--action-weight', type=float, nargs='+', default=[0.])
    ap.add_argument('--parent-trust', type=float, default=0.)
    ap.add_argument('--channels', type=int, nargs='+', default=list(range(7)))
    a = ap.parse_args()
    assert all(os.environ.get(k)=='1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'))
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    mem = (cg/'memory.max').read_text().strip()
    assert mem != 'max' and int(mem) <= 3*1024**3, 'Requires MemoryMax <= 3 GiB'
    assert a.channels and set(a.channels).issubset(range(7))
    assert min(a.ridge+a.smooth_weight+a.action_weight+[a.noise_scale,a.noise_weight,a.parent_trust])>=0
    a.output.mkdir(parents=True, exist_ok=False)
    source_paths = [Path(__file__), ROOT/'scripts/office_vmc_memory_esn_20260927.py']
    hashes = {str(p):sha(p) for p in source_paths}
    snapshot = a.output/'source'; snapshot.mkdir()
    for p in source_paths: (snapshot/p.name).write_bytes(p.read_bytes())
    state = dict(status='running', started_utc=now(), command=sys.argv, seed=a.seed,
                 source_sha256=hashes, host=platform.node(), python=sys.executable,
                 numpy=np.__version__, memory_max=int(mem),
                 training_data_sha256=sha(a.data), parent_checkpoint_sha256=sha(a.parent_checkpoint))
    write(a.output/'execution.json', state)
    try:
        with np.load(a.data, allow_pickle=False) as z: data={k:z[k].copy() for k in z.files}
        validate_data(data)
        actor = OfficeVMCMemoryESN(a.parent_checkpoint)
        assert actor.readout_activation=='clipped_linear' and actor.output_gain==1.
        assert actor.context_dimension==12 and not actor.axis_separable
        assert not actor.nonlinear and not actor.state_delta_readout
        assert actor.w.shape==(128,128)
        full = features(actor, data['observation'], data['episode'])
        n = full.shape[1]-12
        # CRITICAL: forbidden columns are never fitted, not zeroed after fitting.
        x = full[:,:n].copy(); del full
        train=data['train']; y=data['requested_teacher_action']; ep=data['episode']; imp=data['importance']
        scale=np.maximum(x[train].std(axis=0),.005)
        parent_prediction=bounded(x@actor.weights[:n])
        parent=actor.weights[:n]*scale[:,None]; x/=scale
        gram,rhs=normal_equations(x,y,imp,train)
        dg=temporal_gram(x,ep,imp,train)
        ng=np.zeros_like(gram)
        if a.noise_scale and a.noise_weight:
            rng=np.random.default_rng(a.seed)
            obs=data['observation'].copy()
            fields=np.array(sorted(set(range(14,17))|set(range(20,23))|set(range(26,29))|set(range(39,48))))
            amplitude=np.maximum(obs[train][:,fields].std(0),.005)*a.noise_scale
            obs[:,fields]+=rng.normal(size=(len(obs),len(fields)))*amplitude
            noisy=features(actor,obs,ep)[:,:n]/scale; noisy-=x
            ng,_=normal_equations(noisy,np.zeros((len(x),1)),imp,train)
            del noisy,obs
        baseline=dict(train=metrics(parent_prediction,y,ep,train),validation=metrics(parent_prediction,y,ep,~train))
        rows=[]; best=None
        for smooth in a.smooth_weight:
            for action in a.action_weight:
                for ridge in a.ridge:
                    w=fit(gram,rhs,dg,ng,parent,ridge,smooth,action,a.noise_weight,a.parent_trust,a.channels)
                    weights=np.zeros_like(actor.weights);weights[:n]=w/scale[:,None]
                    with np.load(a.parent_checkpoint) as z: values={k:z[k].copy() for k in z.files}
                    values['weights']=weights
                    name=f'ridge{ridge:g}_smooth{smooth:g}_action{action:g}'
                    cp=a.output/(name+'.npz');np.savez_compressed(cp,**values)
                    deployed=OfficeVMCMemoryESN(cp)
                    predictions=np.empty((len(x),7));previous=None
                    for i,(o,e) in enumerate(zip(data['observation'],ep)):
                        if e!=previous:deployed.reset();previous=e
                        predictions[i]=deployed.act(o)
                    parity=float(np.max(np.abs(predictions-bounded(x@w))))
                    assert parity<1e-10, parity
                    np.testing.assert_array_equal(weights[-12:],0.)
                    for key in values:
                        if key!='weights':
                            with np.load(a.parent_checkpoint) as z: np.testing.assert_array_equal(values[key],z[key])
                    val=metrics(predictions,y,ep,~train)
                    row=dict(name=name,ridge=ridge,smooth_weight=smooth,action_weight=action,
                             noise_scale=a.noise_scale,noise_weight=a.noise_weight,parent_trust=a.parent_trust,
                             fitted_channels=a.channels,train=metrics(predictions,y,ep,train),validation=val,
                             parent_action_max_abs=float(np.max(np.abs(predictions-parent_prediction))),
                             export_parity_max_abs=parity,checkpoint_sha256=sha(cp))
                    rows.append(row)
                    if best is None or val['mse']<best['validation']['mse']:best=row
        state.update(status='complete',ended_utc=now(),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        meta=dict(state,contract='ESN_readout_torque_generalization_v2',parent_metrics=baseline,
                  identity_split=dict(train=20,validation=5),candidates=rows,candidate_count=len(rows),
                  offline_mse_best=best,all_candidates_preserved=True,reservoir_frozen=True,
                  context_excluded_before_fit=True,importance_preserved=True,
                  selection_note='Offline replay only. Closed-loop selection must retain task/strict, failures, and full condition denominators.',
                  limitation='Action smoothness is not actuator torque, passivity, or physical generalization. No historical final conditions read.')
        write(a.output/'TRAINING_COMPLETE.json',meta)
        print(json.dumps(dict(output=str(a.output),parent=baseline,candidates=rows)))
    except BaseException as e:
        state.update(status='failed_preserved',error=repr(e),ended_utc=now());raise
    finally:write(a.output/'execution.json',state)


if __name__=='__main__': main()
