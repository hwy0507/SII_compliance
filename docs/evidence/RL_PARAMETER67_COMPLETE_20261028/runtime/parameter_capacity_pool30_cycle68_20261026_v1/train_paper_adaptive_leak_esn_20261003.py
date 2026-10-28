"""Train ESN readout and proprioceptive leak gates, keeping echo weights fixed.

This is an adaptive-leak ESN variant, not a claim of readout-only training.
The 128 recurrent neurons, input/echo matrices and base time constants stay
fixed. No model-based recovery law or privileged input runs at deployment.
"""
import argparse,copy,json,os,platform,subprocess,sys
from pathlib import Path
import numpy as np
import torch
from optimize_tool_contact_20261002 import ROOT,sha,write,now
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN


class AdaptiveEcho(torch.nn.Module):
    def __init__(self,actor,norm):
        super().__init__()
        self.register_buffer('echo',torch.tensor(actor.w,dtype=torch.float32))
        self.register_buffer('leak',torch.tensor(actor.leak,dtype=torch.float32))
        self.register_buffer('norm',torch.tensor(norm,dtype=torch.float32))
        self.coeff=torch.nn.Parameter(torch.tensor(actor.weights*norm[:,None],dtype=torch.float32))
        self.gate=torch.nn.Parameter(torch.tensor(actor.context_gate_w,dtype=torch.float32))
        self.register_buffer('active',torch.tensor(actor.weights!=0,dtype=torch.float32))
        self.coeff.register_hook(lambda grad:grad*self.active)
        self.gate_limits=getattr(actor,'context_gate_limits',None)

    def forward(self,projection,force,cross,context,state=None):
        if state is None:state=projection.new_zeros((projection.shape[0],128))
        gate=.05+1.95*torch.sigmoid(context@self.gate.T+np.log(.95))
        if self.gate_limits is not None:
            low,high=self.gate_limits
            gate=low+(high-low)*torch.sigmoid(context@self.gate.T+np.log((1-low)/(high-1)))
        leak=(gate*self.leak).clamp(max=1.)
        output=[]
        for t in range(projection.shape[1]):
            state=state+leak[:,t]*(torch.tanh(projection[:,t]+state@self.echo.T)-state)
            signed=torch.cat((force[:,t],state),-1)
            feature=torch.cat((signed,signed.abs(),cross[:,t],context[:,t]),-1)
            raw=(feature/self.norm)@self.coeff
            output.append(torch.cat((raw[:,:1].clamp(0,1),raw[:,1:].clamp(-1,1)),-1))
        return torch.stack(output,1),state


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--parent-metadata',type=Path,required=True)
    p.add_argument('--data',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--updates',type=int,default=4000)
    p.add_argument('--seed',type=int,default=2026100302)
    p.add_argument('--drift-weight',type=float,default=.25)
    p.add_argument('--readout-lr',type=float,default=.0005);p.add_argument('--gate-lr',type=float,default=.001)
    a=p.parse_args()
    assert 0<=a.drift_weight<=1 and 0<a.readout_lr<=.001 and 0<a.gate_lr<=.001
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip();assert memory!='max' and int(memory)<=3*1024**3
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    torch.set_num_threads(1);torch.manual_seed(a.seed)
    meta=json.loads(a.metadata.read_text());parent=json.loads(a.parent_metadata.read_text())
    assert sha(a.data)==meta['training_data_sha256']==parent['training_data_sha256']
    assert sha(a.checkpoint)==parent['checkpoint_sha256']
    sources=[Path(__file__),ROOT/'scripts/office_vmc_memory_esn_20260927.py',ROOT/'tools/optimize_tool_contact_20261002.py']
    hashes={str(f.relative_to(ROOT)):sha(f) for f in sources}
    subprocess.run(['tar','-czf',str(out/'source_overlay.tar.gz'),*hashes],cwd=ROOT,check=True)
    execution=dict(status='running',started_utc=now(),argv=sys.argv,source_sha256=hashes,host=platform.node(),python=sys.executable,
                   numpy=np.__version__,torch=torch.__version__,memory_max=memory)
    write(out/'execution.json',execution)
    try:
        with np.load(a.data) as z:obs,ep,train,importance,y=[z[k].copy() for k in ('observation','episode','train','importance','requested_teacher_action')]
        actor=OfficeVMCMemoryESN(a.checkpoint)
        assert actor.position_context and actor.context_gate_w is not None and not actor.nonlinear and not actor.axis_separable
        assert actor.readout_activation=='clipped_linear' and actor.w.shape==(128,128)
        x=np.clip(obs[:,39:45]/actor.scale,-12,12)
        context=np.c_[np.clip(np.c_[obs[:,14:17]/.06,obs[:,26:29]/.06,obs[:,45:48]],-4,4),np.clip(obs[:,20:23]/.08,-4,4)]
        drive=np.c_[x,np.abs(x)];cross=(drive[:,:,None]*context[:,None,:]).reshape(len(x),-1)
        projection=np.c_[drive,cross]@actor.win.T
        previous=None;features=[]
        for eid,o in zip(ep,obs):
            if eid!=previous:actor.reset();previous=eid
            features.append(actor.features(o))
        norm=np.maximum(np.asarray(features)[train].std(0),.005);del features
        arrays=[v.astype(np.float32) for v in (projection,x,cross,context,y,importance)]
        model=AdaptiveEcho(actor,norm)
        optimizer=torch.optim.AdamW([dict(params=[model.coeff],lr=a.readout_lr),dict(params=[model.gate],lr=a.gate_lr)],weight_decay=1e-6)
        seq={int(e):np.flatnonzero(ep==e) for e in np.unique(ep)}
        train_ids=np.unique(ep[train]);val_ids=np.unique(ep[~train]);assert not set(train_ids).intersection(val_ids)
        rng=np.random.default_rng(a.seed+2000);proxy=torch.tensor([.32,.32,.32,.6,.6,.6])* .04/torch.tensor([.02,.02,.02,.05,.05,.05])
        def predict(ids):
            result={}
            with torch.no_grad():
                for e in ids:
                    index=seq[int(e)];value=model(*[torch.from_numpy(v[index])[None] for v in arrays[:4]])[0][0]
                    result[int(e)]=value.numpy()
            return result
        def validate():
            values=predict(val_ids);errors=[values[int(e)]-y[seq[int(e)]] for e in val_ids]
            mse=float(np.mean(np.concatenate(errors)**2));windows=[]
            for error in errors:
                windows.extend(np.sum(error[i:i+16,1:],axis=0)*proxy.numpy() for i in range(0,len(error)-15,16))
            integral=float(np.mean(np.asarray(windows)**2));return mse,integral,mse+a.drift_weight*integral
        vm,vd,best=validate();best_state=copy.deepcopy(model.state_dict());selected=0
        history=[dict(update=0,holdout_mse=vm,holdout_integrated_proxy=vd,selection_score=best)]
        update=epoch=0;schedule=[]
        while update<a.updates:
            order=rng.permutation(train_ids)
            for begin in range(0,len(order),8):
                group=order[begin:begin+8];length=max(len(seq[int(e)]) for e in group)
                padded=[np.zeros((len(group),length,*v.shape[1:]),np.float32) for v in arrays]
                for i,e in enumerate(group):
                    ids=seq[int(e)]
                    for dest,source in zip(padded,arrays):dest[i,:len(ids)]=source[ids]
                hidden=None
                for offset in range(0,length,64):
                    values=[torch.from_numpy(v[:,offset:offset+64]) for v in padded]
                    prediction,hidden=model(*values[:4],state=hidden);target,weight=values[4:]
                    error=prediction-target
                    loss=(error.square()*weight[...,None]).sum()/(7*weight.sum())
                    pw=torch.minimum(weight[:,1:],weight[:,:-1]);delta=error[:,1:]-error[:,:-1]
                    loss=loss+.25*(delta.square()*pw[...,None]).sum()/(7*pw.sum().clamp_min(1))
                    if a.drift_weight and prediction.shape[1]>=16:
                        integrated=error[...,1:].unfold(1,16,1).sum(-1)*proxy
                        ww=weight.unfold(1,16,1).amin(-1)
                        loss=loss+a.drift_weight*(integrated.square()*ww[...,None]).sum()/(6*ww.sum().clamp_min(1))
                    assert torch.isfinite(loss)
                    optimizer.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step()
                    hidden=hidden.detach();update+=1;schedule.append((epoch,tuple(int(e) for e in group),offset,int((weight>0).sum())))
                    if update%400==0 or update==a.updates:
                        vm,vd,score=validate();history.append(dict(update=update,holdout_mse=vm,holdout_integrated_proxy=vd,selection_score=score))
                        write(out/'training_progress.json',history[-1])
                        if score<best:best=score;best_state=copy.deepcopy(model.state_dict());selected=update
                    if update>=a.updates:break
                if update>=a.updates:break
            epoch+=1
        model.load_state_dict(best_state)
        with np.load(a.checkpoint) as z:values={k:z[k].copy() for k in z.files}
        values['weights']=model.coeff.detach().numpy()/norm[:,None];values['context_gate_w']=model.gate.detach().numpy()
        values['learned_context_gate']=True
        np.testing.assert_array_equal(values['weights'][actor.weights==0],0.)
        for k in ('w','win','leak'):np.testing.assert_array_equal(values[k],getattr(actor,k))
        np.savez_compressed(out/'checkpoint.npz',**values)
        deployed=OfficeVMCMemoryESN(out/'checkpoint.npz');predictions=[];previous=None
        for eid,o in zip(ep,obs):
            if eid!=previous:deployed.reset();previous=eid
            predictions.append(deployed.act(o))
        predictions=np.asarray(predictions);torch_values=predict(seq)
        maximum=max(float(np.max(abs(predictions[index]-torch_values[e]))) for e,index in seq.items())
        assert maximum<5e-5,maximum
        deployed.reset()
        for o in obs[:200]:
            zero=o.copy();zero[39:45]=0;np.testing.assert_array_equal(deployed.act(zero),np.zeros(7))
        np.savez_compressed(out/'exported_replay.npz',prediction=predictions,episode=ep)
        write(out/'history.json',history);write(out/'schedule.json',schedule)
        result=dict(completed_utc=now(),checkpoint_sha256=sha(out/'checkpoint.npz'),parent_checkpoint_sha256=sha(a.checkpoint),
            training_data_sha256=sha(a.data),source_sha256=hashes,lineage=meta['lineage'],seed=a.seed,updates=update,selected_update=selected,
            reservoir_width=128,learned_hidden_readout_width=0,trained_readout_parameters=int(model.active.sum()),trained_gate_parameters=int(model.gate.numel()),
            drift_weight=a.drift_weight,readout_learning_rate=a.readout_lr,gate_learning_rate=a.gate_lr,
            input_and_recurrent_echo_matrices_frozen=True,base_leaks_frozen=True,numpy_torch_max_abs=maximum,
            holdout_mse=float(np.mean((predictions[~train]-y[~train])**2)),physical_history_mse=float(np.mean((predictions[ep>=48]-y[ep>=48])**2)),
            limitation='Adaptive-leak ESN, not readout-only ESN: proprioceptive gate weights and readout learned. Pure neural deployment without teacher dynamics. Physical success untested.')
        assert all(sha(ROOT/k)==h for k,h in hashes.items())
        write(out/'TRAINING_COMPLETE.json',result);execution.update(status='complete',checkpoint_sha256=result['checkpoint_sha256'])
        print(json.dumps({k:result[k] for k in ('selected_update','holdout_mse','physical_history_mse','numpy_torch_max_abs')}))
    except BaseException as exc:execution.update(status='failed_preserved',error=repr(exc));raise
    finally:execution['ended_utc']=now();write(out/'execution.json',execution)

if __name__=='__main__':main()
