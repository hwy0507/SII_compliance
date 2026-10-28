"""Fine-tune feature-matched MLP/RNN controls from registered reservoir parents.

Float64 training/export; identity holdout; parent retained at update zero.
The readout and input matrix learn, and the RNN additionally learns its echo
matrix. This is deliberately labeled MLP/RNN, never a readout-only ESN.
"""
import argparse,copy,json,os,platform,subprocess,sys
from pathlib import Path
import numpy as np
import torch
from optimize_tool_contact_20261002 import ROOT,sha,write,now
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN
from office_context_network_20261003 import OfficeContextNetwork,CONTRACT

class Network(torch.nn.Module):
    def __init__(self,actor,kind,norm):
        super().__init__();self.kind=kind
        self.win=torch.nn.Parameter(torch.tensor(actor.win,dtype=torch.float64))
        self.echo=torch.nn.Parameter(torch.tensor(actor.w,dtype=torch.float64),requires_grad=kind=='rnn')
        self.coeff=torch.nn.Parameter(torch.tensor(actor.weights*norm[:,None],dtype=torch.float64))
        self.register_buffer('leak',torch.tensor(actor.leak,dtype=torch.float64))
        self.register_buffer('context_gate_w',None if actor.context_gate_w is None else torch.tensor(actor.context_gate_w,dtype=torch.float64))
        projection=getattr(actor,'state_context_readout_w',None)
        self.register_buffer('state_context_readout_w',None if projection is None else torch.tensor(projection,dtype=torch.float64))
        self.gate_limits=(.05,2.) if actor.context_gate_limits is None else tuple(actor.context_gate_limits)
        self.register_buffer('norm',torch.tensor(norm,dtype=torch.float64))
        mask=np.ones_like(actor.weights);mask[-12:]=0
        self.register_buffer('mask',torch.tensor(mask,dtype=torch.float64))
        self.coeff.register_hook(lambda grad:grad*self.mask)

    def forward(self,drive,force,cross,context,state=None):
        projection=drive@self.win.T
        leak=self.leak
        if self.context_gate_w is not None:
            low,high=self.gate_limits
            bias=float(np.log((1-low)/(high-1)))
            gate=low+(high-low)*torch.sigmoid((context@self.context_gate_w.T+bias).clamp(-40,40))
            leak=(gate*self.leak).clamp_max(1.)
        if self.kind=='mlp':
            hidden=torch.tanh(projection)*leak
        else:
            if state is None:state=projection.new_zeros((len(projection),128))
            states=[]
            for t in range(projection.shape[1]):
                rate=leak if self.context_gate_w is None else leak[:,t]
                state=state+rate*(torch.tanh(projection[:,t]+state@self.echo.T)-state)
                states.append(state)
            hidden=torch.stack(states,1)
        signed=torch.cat((force,hidden),-1)
        pieces=[signed,signed.abs(),cross]
        if self.state_context_readout_w is not None:
            pieces.append(hidden*torch.tanh(context@self.state_context_readout_w.T))
        features=torch.cat((*pieces,context),-1)
        raw=(features/self.norm)@self.coeff
        return torch.cat((raw[...,:1].clamp(0,1),raw[...,1:].clamp(-1,1)),-1),state

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('checkpoint','parent-metadata','data','metadata','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--kind',choices=('mlp','rnn'),required=True)
    p.add_argument('--seed',type=int,default=2026100302);p.add_argument('--updates',type=int,default=4000)
    p.add_argument('--learning-rate',type=float,default=.0001)
    p.add_argument('--integral-weight',type=float,default=0.)
    a=p.parse_args();assert 0<a.learning_rate<=.001 and 0<a.updates<=12000
    assert 0<=a.integral_weight<=2
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip();assert memory!='max' and int(memory)<=3*1024**3
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    torch.set_num_threads(1);torch.manual_seed(a.seed)
    meta=json.loads(a.metadata.read_text());parent=json.loads(a.parent_metadata.read_text())
    assert sha(a.data)==meta['training_data_sha256']==parent['training_data_sha256']
    assert sha(a.checkpoint)==parent['checkpoint_sha256']
    files=[Path(__file__),ROOT/'scripts/office_context_network_20261003.py',ROOT/'scripts/office_vmc_memory_esn_20260927.py',ROOT/'tools/optimize_tool_contact_20261002.py']
    hashes={str(f.relative_to(ROOT)):sha(f) for f in files}
    subprocess.run(['tar','-czf',str(out/'source_overlay.tar.gz'),*hashes],cwd=ROOT,check=True)
    execution=dict(status='running',started_utc=now(),argv=sys.argv,host=platform.node(),python=sys.executable,
                   source_sha256=hashes,memory_max=memory,torch=torch.__version__,numpy=np.__version__)
    write(out/'execution.json',execution)
    try:
        with np.load(a.data) as z:
            obs,ep,train,weight,y=[z[k].copy() for k in ('observation','episode','train','importance','requested_teacher_action')]
            physical=z['physical_execution'].astype(bool) if 'physical_execution' in z.files else ep>=48
        assert np.any(physical)
        actor=OfficeVMCMemoryESN(a.checkpoint)
        assert actor.position_context and not actor.nonlinear and not actor.axis_separable
        assert actor.readout_activation=='clipped_linear' and actor.reset_at_each_observation==(a.kind=='mlp')
        force=np.clip(obs[:,39:45]/actor.scale,-12,12)
        context=np.c_[np.clip(np.c_[obs[:,14:17]/.06,obs[:,26:29]/.06,obs[:,45:48]],-4,4),np.clip(obs[:,20:23]/.08,-4,4)]
        load=np.c_[force,np.abs(force)];cross=(load[:,:,None]*context[:,None,:]).reshape(len(obs),-1)
        drive=np.c_[load,cross];features=[];previous=None
        for e,o in zip(ep,obs):
            if e!=previous:actor.reset();previous=e
            features.append(actor.features(o))
        norm=np.maximum(np.asarray(features)[train].std(0),.005);del features
        arrays=[drive,force,cross,context,y,weight]
        model=Network(actor,a.kind,norm)
        optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=a.learning_rate,weight_decay=1e-6)
        seq={int(e):np.flatnonzero(ep==e) for e in np.unique(ep)}
        train_ids=np.unique(ep[train]);val_ids=np.unique(ep[~train]);assert not set(train_ids).intersection(val_ids)
        rng=np.random.default_rng(a.seed+2000)
        def predict(ids):
            result={}
            with torch.no_grad():
                for e in ids:
                    index=seq[int(e)]
                    result[int(e)]=model(*[torch.from_numpy(v[index])[None] for v in arrays[:4]])[0][0].numpy()
            return result
        def validate():
            values=predict(val_ids)
            return float(np.mean(np.concatenate([values[int(e)]-y[seq[int(e)]] for e in val_ids])**2))
        best=validate();best_state=copy.deepcopy(model.state_dict());selected=0
        history=[dict(update=0,holdout_mse=best)];schedule=[];update=epoch=0
        while update<a.updates:
            order=rng.permutation(train_ids)
            for begin in range(0,len(order),8):
                group=order[begin:begin+8];length=max(len(seq[int(e)]) for e in group)
                padded=[np.zeros((len(group),length,*v.shape[1:]),np.float64) for v in arrays]
                for i,e in enumerate(group):
                    ids=seq[int(e)]
                    for dest,source in zip(padded,arrays):dest[i,:len(ids)]=source[ids]
                hidden=None
                for offset in range(0,length,64):
                    values=[torch.from_numpy(v[:,offset:offset+64]) for v in padded]
                    prediction,hidden=model(*values[:4],state=hidden);target,importance=values[4:]
                    error=prediction-target
                    loss=(error.square()*importance[...,None]).sum()/(7*importance.sum())
                    pw=torch.minimum(importance[:,1:],importance[:,:-1]);delta=error[:,1:]-error[:,:-1]
                    loss=loss+.25*(delta.square()*pw[...,None]).sum()/(7*pw.sum().clamp_min(1))
                    if a.integral_weight and error.shape[1]>=16:
                        scale=error.new_tensor([0.,.32/.02*.04,.32/.02*.04,.32/.02*.04,.6/.05*.04,.6/.05*.04,.6/.05*.04])
                        integrated=error.unfold(1,16,1).sum(-1)*scale
                        iw=importance.unfold(1,16,1).amin(-1)
                        loss+=a.integral_weight*(integrated.square()*iw[...,None]).sum()/(7*iw.sum().clamp_min(1))
                    assert torch.isfinite(loss)
                    optimizer.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step()
                    if hidden is not None:hidden=hidden.detach()
                    update+=1;schedule.append((epoch,tuple(int(e) for e in group),offset,int((importance>0).sum())))
                    if update%400==0 or update==a.updates:
                        score=validate();history.append(dict(update=update,holdout_mse=score));write(out/'training_progress.json',history[-1])
                        if score<best:best=score;best_state=copy.deepcopy(model.state_dict());selected=update
                    if update>=a.updates:break
                if update>=a.updates:break
            epoch+=1
        model.load_state_dict(best_state)
        with np.load(a.checkpoint) as z:values={k:z[k].copy() for k in z.files}
        values.update(contract=CONTRACT,network_kind=a.kind,win=model.win.detach().numpy(),w=model.echo.detach().numpy(),weights=model.coeff.detach().numpy()/norm[:,None])
        np.testing.assert_array_equal(values['weights'][-12:],0.)
        np.savez_compressed(out/'checkpoint.npz',**values)
        deployed=OfficeContextNetwork(out/'checkpoint.npz');predictions=[];previous=None
        for e,o in zip(ep,obs):
            if e!=previous:deployed.reset();previous=e
            predictions.append(deployed.act(o))
        predictions=np.asarray(predictions);expected=predict(seq)
        maximum=max(float(np.max(abs(predictions[index]-expected[e]))) for e,index in seq.items());assert maximum<5e-5,maximum
        # Same public fields, and zero estimated load cannot create state from rest.
        fields=set(range(14,17))|set(range(20,23))|set(range(26,29))|set(range(39,48))
        deployed.reset();other=OfficeContextNetwork(out/'checkpoint.npz')
        for o in obs[:200]:
            altered=o.copy();altered[sorted(set(range(48))-fields)]=123
            np.testing.assert_array_equal(deployed.act(o),other.act(altered))
        deployed.reset()
        for o in obs[:200]:
            zero=o.copy();zero[39:45]=0;np.testing.assert_array_equal(deployed.act(zero),np.zeros(7))
        np.savez_compressed(out/'exported_replay.npz',prediction=predictions,episode=ep)
        write(out/'history.json',history);write(out/'schedule.json',schedule)
        result=dict(completed_utc=now(),kind=a.kind,checkpoint_sha256=sha(out/'checkpoint.npz'),parent_checkpoint_sha256=sha(a.checkpoint),
                    training_data_sha256=sha(a.data),source_sha256=hashes,lineage=meta['lineage'],seed=a.seed,updates=update,selected_update=selected,
                    width=128,trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad)-12*7,
                    features_matched_to_context_esn=True,learning_rate=a.learning_rate,precision='float64',tbptt_steps=64,
                    fixed_contextual_leak_gate=actor.context_gate_w is not None,gate_weights_trainable=False,
                    fixed_state_context_readout=getattr(actor,'state_context_readout_w',None) is not None,
                    state_context_projection_trainable=False,
                    integral_weight=a.integral_weight,integral_window_steps=16,action_delta_weight=.25,
                    actual_nonpadding_observations=sum(s[3] for s in schedule),schedule_sha256=sha(out/'schedule.json'),
                    holdout_mse=float(np.mean((predictions[~train]-y[~train])**2)),physical_history_mse=float(np.mean((predictions[physical]-y[physical])**2)),
                    validation_split=meta.get('selection_split','legacy whole synthetic identities'),
                    numpy_torch_max_abs=maximum,unused_field_isolation_pass=True,zero_load_equilibrium_pass=True,
                    limitation='Warm-started feature-matched MLP/RNN mechanism control; not parameter/FLOP matched and not an ESN. Fixed base time constants and optional fixed proprioceptive leak modulation; input/recurrent weights learn as declared. Physical success untested.')
        assert all(sha(ROOT/k)==h for k,h in hashes.items())
        write(out/'TRAINING_COMPLETE.json',result);execution.update(status='complete',checkpoint_sha256=result['checkpoint_sha256'])
        print(json.dumps({k:result[k] for k in ('kind','selected_update','holdout_mse','physical_history_mse','numpy_torch_max_abs')}))
    except BaseException as exc:execution.update(status='failed_preserved',error=repr(exc));raise
    finally:execution['ended_utc']=now();write(out/'execution.json',execution)

if __name__=='__main__':main()
