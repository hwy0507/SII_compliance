"""Optimize only an ESN's existing linear readout with temporal imitation loss.

The fixed reservoir, neuron count, inputs and common deployment filter do not
change. Integrated action discrepancy is a proxy, never observed robot error.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import numpy as np
import torch
from optimize_tool_contact_20261002 import ROOT,sha,write,now
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--checkpoint-metadata',type=Path,required=True)
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--data-metadata',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seed',type=int,default=2026100301)
    p.add_argument('--updates',type=int,default=4000)
    p.add_argument('--drift-weight',type=float,default=.25)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip()
    assert memory!='max' and int(memory)<=3*1024**3
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    assert 0<=a.drift_weight<=2 and 0<a.updates<=20000
    torch.set_num_threads(1);torch.manual_seed(a.seed)
    metadata=json.loads(a.checkpoint_metadata.read_text());data_metadata=json.loads(a.data_metadata.read_text())
    assert sha(a.checkpoint)==metadata['checkpoint_sha256']
    assert sha(a.data)==data_metadata['training_data_sha256']
    sources=[Path(__file__),ROOT/'scripts/office_vmc_memory_esn_20260927.py',ROOT/'tools/optimize_tool_contact_20261002.py']
    hashes={str(f.relative_to(ROOT)):sha(f) for f in sources}
    subprocess.run(['tar','-czf',str(out/'source_overlay.tar.gz'),*hashes],cwd=ROOT,check=True)
    execution=dict(status='running',started_utc=now(),argv=sys.argv,host=platform.node(),python=sys.executable,
                   memory_max=memory,source_sha256=hashes,torch_version=torch.__version__,numpy_version=np.__version__)
    write(out/'execution.json',execution)
    try:
        with np.load(a.data) as z:obs,ep,train,importance,y=[z[k].copy() for k in ('observation','episode','train','importance','requested_teacher_action')]
        actor=OfficeVMCMemoryESN(a.checkpoint)
        assert not actor.nonlinear
        features=[];previous=None
        for eid,o in zip(ep,obs):
            if previous!=eid:actor.reset();previous=eid
            features.append(actor.features(o))
        x=np.asarray(features);norm=np.maximum(x[train].std(0),1e-5)
        tx=torch.tensor(x/norm,dtype=torch.float32);ty=torch.tensor(y,dtype=torch.float32)
        coeff=torch.nn.Parameter(torch.tensor(actor.weights*norm[:,None],dtype=torch.float32))
        active=torch.tensor(actor.weights!=0,dtype=torch.float32)
        coeff.register_hook(lambda grad:grad*active)
        optimizer=torch.optim.AdamW([coeff],lr=.0005,weight_decay=1e-6)
        rng=np.random.default_rng(a.seed)
        length=16
        pool=np.flatnonzero(train);prob=importance[pool]/importance[pool].sum()
        windows=np.flatnonzero(train[:-length+1]&(ep[:-length+1]==ep[length-1:]))
        window_prob=importance[windows]/importance[windows].sum()
        val=np.flatnonzero(~train)
        val_windows=np.flatnonzero((~train[:-length+1])&(ep[:-length+1]==ep[length-1:]))[::length]
        physical_scale=torch.tensor([.32,.32,.32,.6,.6,.6],dtype=torch.float32)
        error_scale=torch.tensor([.02,.02,.02,.05,.05,.05],dtype=torch.float32)
        def predict(ids):
            raw=tx[ids]@coeff
            residual=(raw[:,1:].clamp(-1,1) if actor.readout_activation=='clipped_linear' else torch.tanh(raw[:,1:]))
            slowdown=(torch.linalg.vector_norm(residual,dim=1,keepdim=True)/np.sqrt(6)
                      if actor.axis_separable else raw[:,:1].clamp(0,1))
            return torch.cat((slowdown,residual),1)
        def drift(starts):
            indices=torch.from_numpy((starts[:,None]+np.arange(length)).ravel())
            delta=(predict(indices)-ty[indices]).reshape(-1,length,7)[:,:,1:]
            return ((delta.sum(1)*.04*physical_scale/error_scale)**2).mean()
        def validate():
            with torch.no_grad():
                mse=float(((predict(val)-ty[val])**2).mean());integrated=float(drift(val_windows))
            return mse,integrated,mse+a.drift_weight*integrated
        vm,vd,best=validate();best_coeff=coeff.detach().numpy().copy();selected=0
        history=[dict(update=0,holdout_mse=vm,holdout_integrated_proxy=vd,selection_score=best)]
        for step in range(a.updates):
            ids=torch.from_numpy(rng.choice(pool,1024,p=prob))
            loss=((predict(ids)-ty[ids])**2).mean()
            starts=rng.choice(windows,64,p=window_prob)
            indices=torch.from_numpy((starts[:,None]+np.arange(length)).ravel())
            prediction=predict(indices).reshape(-1,length,7);target=ty[indices].reshape(-1,length,7)
            delta=(((prediction[:,1:]-prediction[:,:-1])-(target[:,1:]-target[:,:-1]))**2).mean()
            integral=(((prediction-target)[:,:,1:].sum(1)*.04*physical_scale/error_scale)**2).mean()
            total=loss+.25*delta+a.drift_weight*integral
            optimizer.zero_grad(set_to_none=True);total.backward();torch.nn.utils.clip_grad_norm_([coeff],5.);optimizer.step()
            if step%100==0 or step==a.updates-1:
                vm,vd,score=validate()
                history.append(dict(update=step+1,train_mse=float(loss.detach()),holdout_mse=vm,holdout_integrated_proxy=vd,selection_score=score))
                if score<best:best=score;best_coeff=coeff.detach().numpy().copy();selected=step+1
        with np.load(a.checkpoint) as z:values={k:z[k].copy() for k in z.files}
        values['weights']=best_coeff/norm[:,None]
        np.testing.assert_array_equal(values['weights'][~active.numpy().astype(bool)],0.)
        np.savez_compressed(out/'checkpoint.npz',**values)
        final=OfficeVMCMemoryESN(out/'checkpoint.npz');previous=None;replay=[]
        for eid,o in zip(ep,obs):
            if previous!=eid:final.reset();previous=eid
            replay.append(final.act(o))
        replay=np.asarray(replay);coeff.data.copy_(torch.from_numpy(best_coeff))
        with torch.no_grad():expected=predict(np.arange(len(x))).numpy()
        maximum=float(np.max(np.abs(replay-expected)));assert maximum<5e-5,maximum
        final.reset();np.testing.assert_array_equal(final.act(np.zeros(48)),np.zeros(7))
        np.savez_compressed(out/'exported_replay.npz',prediction=replay,episode=ep)
        write(out/'history.json',history)
        result=dict(completed_utc=now(),checkpoint_sha256=sha(out/'checkpoint.npz'),parent_checkpoint_sha256=sha(a.checkpoint),
            training_data_sha256=sha(a.data),lineage=data_metadata['lineage'],seed=a.seed,updates=a.updates,selected_update=selected,
            drift_weight=a.drift_weight,delta_weight=.25,window_s=.64,readout_active_parameters=int(active.sum()),
            reservoir_width=128,learned_hidden_readout_width=0,source_sha256=hashes,numpy_torch_max_abs=maximum,
            readout_activation=actor.readout_activation,
            independent_slowdown_readout=not actor.axis_separable,
            train_mse=float(np.mean((replay[train]-y[train])**2)),holdout_mse=float(np.mean((replay[~train]-y[~train])**2)),
            physical_history_mse=float(np.mean((replay[ep>=48]-y[ep>=48])**2)),target='requested',
            limitation='Only existing readout coefficients trained; integrated action discrepancy is an imitation proxy, not observed robot error. Model selected on synthetic identity holdout; physical success untested.')
        assert all(sha(ROOT/k)==h for k,h in hashes.items())
        write(out/'TRAINING_COMPLETE.json',result);execution.update(status='complete',checkpoint_sha256=result['checkpoint_sha256'])
        print(json.dumps({k:result[k] for k in ('selected_update','train_mse','holdout_mse','physical_history_mse','checkpoint_sha256')}))
    except BaseException as exc:
        execution.update(status='failed_preserved',error=repr(exc));raise
    finally:
        execution['ended_utc']=now();write(out/'execution.json',execution)


if __name__=='__main__':main()
