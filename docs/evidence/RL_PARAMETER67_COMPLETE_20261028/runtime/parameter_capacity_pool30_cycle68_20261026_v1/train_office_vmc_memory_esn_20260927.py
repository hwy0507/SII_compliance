"""Distill causal VMC on synthetic wrench histories, before office feedback.

No test layout, task phase, ground-truth force or successful-episode selection.
All train and validation histories/labels are saved for reproducibility.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seed',type=int,default=20260927)
    p.add_argument('--development-trace',type=Path,nargs='*',default=[])
    p.add_argument('--reservoir-checkpoint',type=Path,help='Reuse exact frozen reservoir arrays across CPU architectures')
    p.add_argument('--nonlinear-updates',type=int,default=0)
    p.add_argument('--axis-separable',action='store_true');a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    rng=np.random.default_rng(a.seed)
    obj=OfficeVMCMemoryESN.__new__(OfficeVMCMemoryESN)
    obj.scale=np.array([8.,8.,8.,1.,1.,1.])
    obj.win=rng.normal(0,.25,(128,6))
    obj.w=rng.normal(0,1,(128,128))*(rng.random((128,128))<.08)
    obj.w*=.8/np.max(np.abs(np.linalg.eigvals(obj.w)))
    obj.leak=1-np.exp(-.04/np.repeat([.04,.16,.64,2.56],32))
    axis_indices=[]
    if a.axis_separable:
        # Default teacher has diagonal dynamics in the world frame. Preserve
        # that symmetry rather than learning spurious cross-axis coupling.
        obj.win[:]=0;obj.w[:]=0
        for axis,indices in enumerate(np.array_split(np.arange(128),6)):
            obj.win[indices,axis]=rng.normal(0,.4,len(indices))
            block=rng.normal(size=(len(indices),len(indices)))*(rng.random((len(indices),len(indices)))<.2)
            block*=.75/max(np.max(np.abs(np.linalg.eigvals(block))),1e-8)
            obj.w[np.ix_(indices,indices)]=block
            obj.leak[indices]=1-np.exp(-.04/np.geomspace(.02,1.,len(indices)))
            axis_indices.append(np.r_[axis,6+indices])
    reservoir_source=None
    if a.reservoir_checkpoint:
        with np.load(a.reservoir_checkpoint,allow_pickle=False) as z:
            if str(z['contract'])!=obj.contract or bool(z['axis_separable'])!=a.axis_separable:
                raise ValueError('Reservoir contract/axis structure mismatch')
            for key,shape in (('win',(128,6)),('w',(128,128)),('leak',(128,)),('scale',(6,))):
                value=z[key].copy()
                if value.shape!=shape or not np.isfinite(value).all():raise ValueError('Invalid frozen reservoir '+key)
                setattr(obj,key,value)
        reservoir_source=dict(path=str(a.reservoir_checkpoint),sha256=hashlib.sha256(a.reservoir_checkpoint.read_bytes()).hexdigest())
    features=[];labels=[];histories=[];splits=[]
    for ep in range(96):
        teacher=SixDVirtualDynamics({});obj.reset()
        # Validation RNG independent of training draw count.
        erng=np.random.default_rng(a.seed+10000+ep)
        wrench=np.zeros(6);target=np.zeros(6)
        for step in range(400):
            if step%40==0:
                target=erng.normal(0,[8,8,8,.8,.8,.8]) if erng.random()<.7 else np.zeros(6)
            wrench+=(1-np.exp(-.04/float(erng.choice([.04,.12,.4]))))*(target-wrench)
            if step<25 or step>=300:wrench[:]=0
            if step in (60,160,260):wrench+=erng.normal(0,[25,25,25,2,2,2])
            obs=np.zeros(48);obs[39:45]=wrench
            features.append(obj.features(obs));labels.append(teacher.act(wrench,.04));histories.append(wrench.copy())
            splits.append(ep<80)
    synthetic_count=len(features)
    trace_metadata=[]
    for path in a.development_trace:
        with np.load(path,allow_pickle=False) as trace:observations=trace['observation'].copy()
        teacher=SixDVirtualDynamics({});obj.reset()
        for obs in observations:
            features.append(obj.features(obs));labels.append(teacher.act(obs[39:45],.04))
            histories.append(obs[39:45].copy());splits.append(True)
        trace_metadata.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),samples=len(observations)))
    x=np.asarray(features);y=np.asarray(labels);train=np.asarray(splits)
    del features,labels,splits
    target=np.arctanh(np.clip(y,-.98,.98));target[:,0]=y[:,0]
    norm=np.maximum(np.std(x[train],axis=0),.005)
    xt=x[train]/norm
    ridge=.01
    importance=np.ones(len(x));importance[synthetic_count:]=12.
    importance=importance[train]
    if a.axis_separable:
        obj.weights=np.zeros((x.shape[1],7))
        for axis,indices in enumerate(axis_indices):
            block=xt[:,indices]
            obj.weights[indices,axis+1]=np.linalg.solve(block.T@(importance[:,None]*block)+ridge*np.eye(len(indices)),block.T@(importance*target[train,axis+1]))/norm[indices]
    else:
        obj.weights=np.linalg.solve(xt.T@(importance[:,None]*xt)+ridge*np.eye(x.shape[1]),xt.T@(importance[:,None]*target[train]))/norm[:,None]
    del xt,target
    raw=x@obj.weights
    nonlinear_fields={}
    if a.nonlinear_updates:
        import torch
        torch.set_num_threads(1);torch.manual_seed(a.seed)
        hidden=torch.nn.Linear(x.shape[1],96,bias=False)
        output=torch.nn.Linear(96,7,bias=False)
        torch.nn.init.zeros_(output.weight)
        hidden_mask=torch.ones_like(hidden.weight);output_mask=torch.ones_like(output.weight)
        if a.axis_separable:
            hidden_mask[:]=0;output_mask[:]=0
            for axis,indices in enumerate(axis_indices):
                hidden_mask[axis*16:(axis+1)*16,indices]=1
                output_mask[axis+1,axis*16:(axis+1)*16]=1
            with torch.no_grad():hidden.weight.mul_(hidden_mask)
        optim=torch.optim.Adam(list(hidden.parameters())+list(output.parameters()),lr=.002)
        tx=torch.as_tensor(x[train]/norm,dtype=torch.float32)
        ty=torch.as_tensor(y[train],dtype=torch.float32)
        base=torch.as_tensor(raw[train],dtype=torch.float32)
        probabilities=torch.as_tensor(importance/importance.sum(),dtype=torch.float32)
        for iteration in range(a.nonlinear_updates):
            indices=torch.multinomial(probabilities,1024,replacement=True)
            prediction_logits=base[indices]+output(torch.tanh(hidden(tx[indices])))
            signed=torch.tanh(prediction_logits[:,1:])
            slowdown=torch.linalg.vector_norm(signed,dim=1,keepdim=True)/np.sqrt(6) if a.axis_separable else prediction_logits[:,:1]
            pred=torch.cat((slowdown,signed),dim=1)
            loss=torch.mean((pred-ty[indices])**2)
            optim.zero_grad();loss.backward();optim.step()
            if a.axis_separable:
                with torch.no_grad():hidden.weight.mul_(hidden_mask);output.weight.mul_(output_mask)
        nonlinear_fields=dict(feature_scale=norm,hidden_w=hidden.weight.detach().numpy(),output_w=output.weight.detach().numpy())
        raw+=np.tanh((x/norm)@nonlinear_fields['hidden_w'].T)@nonlinear_fields['output_w'].T
    prediction=np.tanh(raw);prediction[:,0]=np.clip(raw[:,0],0,1)
    if a.axis_separable:prediction[:,0]=np.linalg.norm(prediction[:,1:],axis=1)/np.sqrt(6)
    metadata=dict(seed=a.seed,episodes=96,train_episodes=80,steps_per_episode=400,ridge=ridge,
                  reservoir_source=reservoir_source,
                  teacher='SixDVirtualDynamics default options',input='canonical48[39:45] encoder-derived wrench only',
                  train_action_rmse=np.sqrt(np.mean((prediction[train]-y[train])**2,axis=0)).tolist(),
                  validation_action_rmse=np.sqrt(np.mean((prediction[~train]-y[~train])**2,axis=0)).tolist(),
                  development_traces=trace_metadata,development_importance=12.,nonlinear_updates=a.nonlinear_updates,axis_separable=a.axis_separable,
                  development_action_rmse=np.sqrt(np.mean((prediction[synthetic_count:]-y[synthetic_count:])**2,axis=0)).tolist() if a.development_trace else None,
                  claims='VMC distillation on synthetic and declared development histories; office task/safety unvalidated')
    np.savez_compressed(a.output/'model.npz',contract=obj.contract,win=obj.win,w=obj.w,leak=obj.leak,scale=obj.scale,
                        weights=obj.weights,metadata=json.dumps(metadata),axis_separable=a.axis_separable,**nonlinear_fields)
    np.savez_compressed(a.output/'training_data.npz',wrench=np.asarray(histories),teacher_action=y,train=train,
                        prediction=prediction,episode=np.r_[np.repeat(np.arange(96),400),np.full(len(x)-synthetic_count,-1)])
    metadata['hashes']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in a.output.glob('*.npz')}
    metadata['source_hashes']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in
       [Path(__file__),Path(__file__).resolve().parents[1]/'scripts/office_vmc_memory_esn_20260927.py',
        Path(__file__).resolve().parents[1]/'scripts/run_vmc_6d_constrained_push_20260918.py']}
    (a.output/'training_report.json').write_text(json.dumps(metadata,indent=2))
    print(json.dumps(metadata),flush=True)


if __name__=='__main__':main()
