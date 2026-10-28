"""128-unit pure ESN with fixed per-axis reservoirs and a bounded linear readout.

No runtime virtual dynamics or learned hidden readout. The analytic norm
slowdown couples the six learned outputs using the teacher's action convention.
Candidate selection uses only whole-history synthetic holdout, never physics.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import numpy as np
from optimize_tool_contact_20261002 import ROOT, sha, write, now
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN


def reservoir(seed, rho, input_gain, times, structure='random'):
    rng = np.random.default_rng(seed)
    actor = OfficeVMCMemoryESN.__new__(OfficeVMCMemoryESN)
    actor.scale = np.array([8., 8., 8., 1., 1., 1.])
    actor.win = np.zeros((128, 6)); actor.w = np.zeros((128, 128))
    actor.leak = np.zeros(128)
    actor.linear_units=np.zeros(128,dtype=bool) if structure=='cascaded' else None
    actor.activation_threshold=np.zeros(128) if structure=='cascaded' else None
    blocks = []
    begin = 0
    for axis, width in enumerate((22, 22, 21, 21, 21, 21)):
        ids = np.arange(begin, begin+width); begin += width
        block = rng.normal(size=(width, width))*(rng.random((width, width)) < .2)
        block *= rho/max(np.max(np.abs(np.linalg.eigvals(block))), 1e-12)
        if structure=='diagonal':
            # Generic fixed echo modes, not teacher spring/mass state equations.
            # Signed self recurrence and varied leak/gain span causal filters.
            block=np.diag(np.resize([rho,0.,-rho],width))
        actor.w[np.ix_(ids, ids)] = block
        actor.win[ids, axis] = rng.normal(0, input_gain, width)
        actor.leak[ids] = 1-np.exp(-.04/np.resize(times, width))
        if structure=='diagonal':
            actor.win[ids,axis]=input_gain*np.resize([.5,1.,2.],width)
            actor.leak[ids]=1-np.exp(-.04/np.resize(np.repeat([.02,.04,.08,.12,.24,.48,.96],3),width))
        if structure=='cascaded':
            # A causal triangular ESN: one linear echo unit drives a bank of
            # nonlinear echoes. No virtual mechanics are evaluated at runtime.
            first=ids[0];tail=ids[1:];alpha=1-np.exp(-1.)
            actor.w[np.ix_(ids,ids)]=0.;actor.win[ids,axis]=0.
            actor.win[first,axis]=1.;actor.leak[first]=alpha;actor.linear_units[first]=True
            actor.win[tail,axis]=input_gain*alpha
            actor.w[tail,first]=input_gain*(1-alpha)
            actor.w[tail,tail]=rho*.25
            actor.leak[tail]=1-np.exp(-.04/np.resize(np.repeat([.02,.04,.08,.16],5),len(tail)))
            actor.activation_threshold[tail]=input_gain*np.resize([0.,.01,.025,.05,.1],len(tail))
        blocks.append(np.r_[axis, 6+ids])
    actor.absolute_inputs = actor.context_inputs = False
    actor.reset()
    return actor, blocks


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--metadata', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--seed', type=int, default=2026100201)
    p.add_argument('--target', choices=('requested', 'filtered'), default='requested')
    p.add_argument('--readout-order', type=int, choices=(1,3), default=1)
    p.add_argument('--input-gains', type=float, nargs=3, default=[.08,.25,.6])
    p.add_argument('--activation-threshold-scale',type=float,default=0.)
    p.add_argument('--reservoir-structure',choices=('random','diagonal','cascaded'),default='random')
    p.add_argument('--readout-activation',choices=('tanh','clipped_linear'),default='tanh')
    a = p.parse_args(); out = a.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    assert all(np.isfinite(v) and 0<v<=5 for v in a.input_gains)
    assert np.isfinite(a.activation_threshold_scale) and 0<=a.activation_threshold_scale<=2
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory = (cg/'memory.max').read_text().strip()
    assert memory != 'max' and int(memory) <= 3*1024**3
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'))
    sources = [Path(__file__), ROOT/'scripts/office_vmc_memory_esn_20260927.py', ROOT/'tools/optimize_tool_contact_20261002.py']
    hashes = {str(f.relative_to(ROOT)):sha(f) for f in sources}
    subprocess.run(['tar', '-czf', str(out/'source_overlay.tar.gz'), *hashes], cwd=ROOT, check=True)
    metadata = json.loads(a.metadata.read_text())
    assert sha(a.data) == metadata['training_data_sha256']
    state = dict(status='running', started_utc=now(), argv=sys.argv, host=platform.node(),
                 python=sys.executable, numpy=np.__version__, memory_max=memory, source_sha256=hashes,
                 data_sha256=sha(a.data), metadata_sha256=sha(a.metadata), seed=a.seed, target=a.target)
    write(out/'execution.json', state)
    try:
        with np.load(a.data) as z:
            obs, ep, train, importance, y = [z[k].copy() for k in
                ('observation', 'episode', 'train', 'importance', a.target+'_teacher_action')]
        assert not set(np.unique(ep[train])).intersection(np.unique(ep[~train]))
        assert all(np.isfinite(v).all() for v in (obs, importance, y))
        candidates = []
        best = float('inf'); selected = None
        # Fixed small grid: data, target, sampling weights and width identical.
        for rho in (.3, .7):
            for gain in a.input_gains:
                actor, blocks = reservoir(a.seed, rho, gain, [.04, .08, .2, .6],a.reservoir_structure)
                actor.readout_order=a.readout_order
                if a.reservoir_structure!='cascaded':
                    actor.activation_threshold=(np.resize([0.,0.,.002,.005,.01,.025,.05,.1],128)*a.activation_threshold_scale
                                                if a.activation_threshold_scale else None)
                elif a.activation_threshold_scale:
                    raise ValueError('Cascaded threshold grid is already fixed')
                if a.readout_order==3:
                    blocks=[np.r_[ids,ids+268,ids+402] for ids in blocks]
                features = []; previous = None
                for eid, observation in zip(ep, obs):
                    if previous != eid: actor.reset(); previous = eid
                    features.append(actor.features(observation))
                x = np.asarray(features)
                for ridge in (.0001, .01):
                    weights = np.zeros((x.shape[1], 7))
                    for axis, ids in enumerate(blocks):
                        xx = x[train][:, ids]
                        norm = np.maximum(xx.std(0), 1e-5); xx = xx/norm
                        yy=(y[train,axis+1] if a.readout_activation=='clipped_linear'
                            else np.arctanh(np.clip(y[train, axis+1], -.999, .999)))
                        coef = np.linalg.solve(xx.T@(importance[train, None]*xx)+ridge*np.eye(len(ids)), xx.T@(importance[train]*yy))
                        weights[ids, axis+1] = coef/norm
                    prediction=(np.clip(x@weights,-1.,1.) if a.readout_activation=='clipped_linear' else np.tanh(x@weights))
                    prediction[:, 0] = np.clip(np.linalg.norm(prediction[:, 1:], axis=1)/np.sqrt(6), 0, 1)
                    mse = float(np.mean((prediction[~train]-y[~train])**2))
                    name = f'rho{rho}_gain{gain}_ridge{ridge}'
                    row = dict(name=name, rho=rho, input_gain=gain, ridge=ridge,
                               holdout_mse=mse, train_mse=float(np.mean((prediction[train]-y[train])**2)),
                               real_history_mse=float(np.mean((prediction[ep>=48]-y[ep>=48])**2)))
                    checkpoint = out/(name+'.npz')
                    np.savez_compressed(checkpoint, contract=actor.contract, win=actor.win, w=actor.w,
                        leak=actor.leak, scale=actor.scale, weights=weights, axis_separable=True, output_gain=1.,readout_order=a.readout_order,
                        readout_activation=a.readout_activation,
                        **({'activation_threshold':actor.activation_threshold} if actor.activation_threshold is not None else {}),
                        **({'linear_units':actor.linear_units} if actor.linear_units is not None else {}))
                    row['checkpoint_sha256'] = sha(checkpoint); candidates.append(row)
                    if mse < best:
                        best = mse; selected = row; selected_checkpoint = checkpoint
        import shutil
        shutil.copy2(selected_checkpoint, out/'checkpoint.npz')
        model = OfficeVMCMemoryESN(out/'checkpoint.npz'); model.reset()
        np.testing.assert_array_equal(model.act(np.zeros(48)), np.zeros(7))
        model2 = OfficeVMCMemoryESN(out/'checkpoint.npz')
        rng = np.random.default_rng(a.seed+50000)
        model.reset(); model2.reset()
        for observation in obs[:200]:
            changed = observation.copy(); changed[:39] = rng.normal(size=39); changed[45:] = rng.normal(size=3)
            np.testing.assert_array_equal(model.act(observation), model2.act(changed))
        model.reset(); previous = None; replay = []
        for eid, observation in zip(ep, obs):
            if previous != eid: model.reset(); previous = eid
            replay.append(model.act(observation))
        replay = np.asarray(replay)
        np.savez_compressed(out/'exported_replay.npz', prediction=replay, episode=ep)
        assert abs(float(np.mean((replay[~train]-y[~train])**2))-best) < 1e-12
        result = dict(completed_utc=now(), seed=a.seed, candidates=candidates, selected=selected,
            checkpoint_sha256=sha(out/'checkpoint.npz'), data_sha256=sha(a.data), metadata_sha256=sha(a.metadata),
            source_sha256=hashes, target=a.target, reservoir_width=128, active_axis_units=128,
            learned_hidden_readout_width=0, trainable_readout_coefficients=134*(3 if a.readout_order==3 else 1),
            readout_feature_order=a.readout_order,
            input_gain_candidates=a.input_gains,
            activation_threshold_scale=a.activation_threshold_scale,
            reservoir_structure=a.reservoir_structure,
            readout_activation=a.readout_activation,
            lineage=metadata['lineage'], selection='minimum whole-history synthetic holdout action MSE, no physical outcome',
            actor_inputs='canonical48[39:45] only; encoder-estimated wrench history',
            limitations='Same-data development fit. Norm slowdown is an explicit action-readout constraint, not VMC dynamics. Physical success untested.')
        assert all(sha(ROOT/k) == h for k,h in hashes.items())
        write(out/'TRAINING_COMPLETE.json', result)
        state.update(status='complete', checkpoint_sha256=result['checkpoint_sha256'])
        print(json.dumps(selected))
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc)); raise
    finally:
        state['ended_utc'] = now(); write(out/'execution.json', state)


if __name__ == '__main__':
    main()
