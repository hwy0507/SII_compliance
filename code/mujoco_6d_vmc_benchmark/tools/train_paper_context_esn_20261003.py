"""Pure 128-unit context-conditioned ESN; only a linear action readout learns.

Context comes from existing reference-relative proprioception. The zero-load,
zero-state equilibrium is exact; no phase/event/contact/world state is read.
"""
import argparse,json,os,platform,shutil,subprocess,sys
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import ROOT,sha,write,now
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--seed',type=int,default=2026100302)
    p.add_argument('--leak-gate',action='store_true')
    p.add_argument('--memory-reset',action='store_true',help='Fit a matched-width memoryless ablation, resetting before every observation')
    p.add_argument('--gate-minimum',type=float,default=.05);p.add_argument('--gate-maximum',type=float,default=2.)
    a=p.parse_args()
    assert 0<=a.gate_minimum<1<a.gate_maximum<=100
    if not a.leak_gate and (a.gate_minimum!=.05 or a.gate_maximum!=2.):raise ValueError('Gate limits require gate')
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip();assert memory!='max' and int(memory)<=3*1024**3
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    metadata=json.loads(a.metadata.read_text());assert metadata['position_error_context']
    assert sha(a.data)==metadata['training_data_sha256']
    sources=[Path(__file__),ROOT/'scripts/office_vmc_memory_esn_20260927.py',ROOT/'tools/optimize_tool_contact_20261002.py']
    hashes={str(f.relative_to(ROOT)):sha(f) for f in sources}
    subprocess.run(['tar','-czf',str(out/'source_overlay.tar.gz'),*hashes],cwd=ROOT,check=True)
    state=dict(status='running',started_utc=now(),argv=sys.argv,source_sha256=hashes,host=platform.node(),
               python=sys.executable,numpy=np.__version__,memory_max=memory,seed=a.seed,leak_gate=a.leak_gate)
    write(out/'execution.json',state)
    try:
        with np.load(a.data) as z:obs,ep,train,importance,y=[z[k].copy() for k in ('observation','episode','train','importance','requested_teacher_action')]
        assert not set(ep[train]).intersection(ep[~train])
        rng=np.random.default_rng(a.seed)
        base_w=rng.normal(size=(128,128))*(rng.random((128,128))<.08)
        base_w/=max(np.max(abs(np.linalg.eigvals(base_w))),1e-12)
        base_win=rng.normal(size=(128,156));base_win[:,12:]/=3.
        candidates=[];best=float('inf');selected=None
        for rho in (.5,.8):
            for gain in (.08,.25,.6):
                actor=OfficeVMCMemoryESN.__new__(OfficeVMCMemoryESN)
                actor.scale=np.array([8.,8.,8.,1.,1.,1.]);actor.w=rho*base_w;actor.win=gain*base_win
                actor.leak=1-np.exp(-.04/np.repeat([.04,.12,.5,2.],32))
                actor.absolute_inputs=actor.context_inputs=actor.position_context=True;actor.context_dimension=12
                actor.reset_at_each_observation=a.memory_reset
                actor.context_gate_w=np.random.default_rng(a.seed+40000).normal(0,1,(128,12)) if a.leak_gate else None
                actor.context_gate_limits=(np.array([a.gate_minimum,a.gate_maximum]) if a.gate_minimum!=.05 or a.gate_maximum!=2. else None)
                actor.reset();features=[];previous=None
                for eid,o in zip(ep,obs):
                    if eid!=previous:actor.reset();previous=eid
                    features.append(actor.features(o))
                x=np.asarray(features);del features
                n=x.shape[1]-12;norm=np.maximum(x[train,:n].std(0),.005)
                xx=x[train,:n]/norm;weighted=importance[train,None]*xx
                gram=xx.T@weighted;rhs=xx.T@(importance[train,None]*y[train])
                for ridge in (.001,.1):
                    weights=np.zeros((x.shape[1],7));weights[:n]=np.linalg.solve(gram+ridge*np.eye(n),rhs)/norm[:,None]
                    prediction=np.clip(x@weights,-1,1);prediction[:,0]=np.clip(prediction[:,0],0,1)
                    mse=float(np.mean((prediction[~train]-y[~train])**2))
                    name=f'rho{rho}_gain{gain}_ridge{ridge}'
                    checkpoint=out/(name+'.npz')
                    np.savez_compressed(checkpoint,contract=actor.contract,scale=actor.scale,w=actor.w,win=actor.win,leak=actor.leak,
                        weights=weights,absolute_inputs=True,context_inputs=True,position_context=True,axis_separable=False,
                        readout_activation='clipped_linear',output_gain=1.,
                        reset_at_each_observation=a.memory_reset,
                        **({'context_gate_w':actor.context_gate_w} if actor.context_gate_w is not None else {}),
                        **({'context_gate_limits':actor.context_gate_limits} if actor.context_gate_limits is not None else {}))
                    row=dict(name=name,rho=rho,input_gain=gain,ridge=ridge,holdout_mse=mse,
                        physical_history_mse=float(np.mean((prediction[ep>=48]-y[ep>=48])**2)),checkpoint_sha256=sha(checkpoint))
                    candidates.append(row)
                    if mse<best:best=mse;selected=row;selected_checkpoint=checkpoint
        shutil.copy2(selected_checkpoint,out/'checkpoint.npz')
        actor=OfficeVMCMemoryESN(out/'checkpoint.npz');previous=None;replay=[]
        for eid,o in zip(ep,obs):
            if eid!=previous:actor.reset();previous=eid
            replay.append(actor.act(o))
        replay=np.asarray(replay);assert abs(float(np.mean((replay[~train]-y[~train])**2))-best)<1e-12
        fields=set(range(14,17))|set(range(20,23))|set(range(26,29))|set(range(39,48))
        other=OfficeVMCMemoryESN(out/'checkpoint.npz');actor.reset()
        for o in obs[:200]:
            changed=o.copy();changed[sorted(set(range(48))-fields)]=123.
            np.testing.assert_array_equal(actor.act(o),other.act(changed))
        actor.reset()
        for o in obs[:200]:
            zero=o.copy();zero[39:45]=0.;np.testing.assert_array_equal(actor.act(zero),np.zeros(7))
        np.savez_compressed(out/'exported_replay.npz',prediction=replay,episode=ep)
        result=dict(completed_utc=now(),checkpoint_sha256=sha(out/'checkpoint.npz'),training_data_sha256=sha(a.data),
            lineage=metadata['lineage'],source_sha256=hashes,seed=a.seed,candidates=candidates,selected=selected,
            reservoir_width=128,learned_hidden_readout_width=0,trainable_readout_coefficients=int((actor.weights.shape[0]-12)*7),
            fields=sorted(fields),contextual_leak_gate=a.leak_gate,readout_activation='clipped_linear',
            gate_multiplier_limits=[a.gate_minimum,a.gate_maximum] if a.leak_gate else None,
            independent_slowdown_readout=True,selection='Whole-history synthetic holdout requested-action MSE only',
            reset_at_each_observation=a.memory_reset,
            limitation='New recovery-teacher dataset and context architecture; not isolated memory comparison. No runtime VMC, extra learned hidden layer, contact truth, event time, task phase or object state. Physical success untested.')
        assert all(sha(ROOT/k)==h for k,h in hashes.items())
        write(out/'TRAINING_COMPLETE.json',result);state.update(status='complete',checkpoint_sha256=result['checkpoint_sha256'])
        print(json.dumps(selected))
    except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
    finally:state['ended_utc']=now();write(out/'execution.json',state)

if __name__=='__main__':main()
