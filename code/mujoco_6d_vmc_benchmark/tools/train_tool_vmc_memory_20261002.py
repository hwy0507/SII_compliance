"""Zero-equilibrium pure ESN distilled from an explicitly selected VMC.

Real executed teacher traces and counterfactual proprioceptive history labels
are separate. Synthetic held-out histories are not physical generalization.
"""
import argparse
import json
import os
import platform
import subprocess
from pathlib import Path
import sys
import numpy as np
import torch
from torch import nn
from optimize_tool_contact_20261002 import ROOT,ParameterTeacher,sha,write,now
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN
from wbc_velocity_residual_core import VelocityResidualActionFilter,VelocityResidualSafetyConfig

# Frozen office construction explicitly overrides the generic .16 m/s default.
# Never infer deployment units from the teacher's internal action divisor.
FILTER_CONFIG=VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32)

def memory_challenge_history(rng,length):
    """Offline proprioceptive histories; their generator clock is never an input.

    Independent random pulse/quiet-stall/travel/stop durations test conditional
    retention rather than memorizing a common release timestamp. These are
    system-identification signals, not claims of physical task trajectories.
    """
    angle=rng.uniform(-np.pi,np.pi);direction=np.array([np.cos(angle),np.sin(angle),0.])
    speed=rng.uniform(.018,.04);force=rng.uniform(2,12);offset=rng.uniform(.035,.10)
    warm=int(rng.integers(15,50));loaded=warm+int(rng.integers(20,70))
    stalled=loaded+int(rng.integers(100,450));travelled=stalled+int(rng.integers(50,250))
    wrench=np.zeros(6);error_z=0.;result=[]
    for step in range(length):
        forcing=warm<=step<loaded;retaining=loaded<=step<stalled;moving=stalled<=step<travelled
        target=np.r_[-force*direction,np.zeros(3)] if forcing else np.zeros(6)
        wrench+=(1-np.exp(-.04/.12))*(target-wrench)
        previous=error_z;target_error=-offset if forcing or retaining or moving else 0.
        error_z+=(1-np.exp(-.04/.8))*(target_error-error_z)
        command=speed*direction if step<travelled else np.zeros(3)
        command=command.copy();command[2]=np.clip(2*error_z,-.06,.06)
        command*=min(1.,.06/max(np.linalg.norm(command),1e-12))
        actual=command.copy() if moving else np.zeros(3);actual[2]=(previous-error_z)/.04
        obs=np.zeros(48);obs[14:17]=command;obs[20:23]=.015*direction;obs[22]=error_z
        obs[26:29]=command-actual;obs[39:45]=wrench;obs[45:48]=direction;result.append(obs)
    return np.asarray(result)

def filtered_labels(observations,config):
    teacher=ParameterTeacher(config);filt=VelocityResidualActionFilter(FILTER_CONFIG)
    requests=[];labels=[]
    for o in observations:
        teacher.observe(o)
        raw=teacher.act(o[39:45]);out=filt.filter(raw,.04)
        requests.append(raw)
        labels.append(np.r_[(1-out.wbc_scale)/(1-filt.config.minimum_wbc_scale),
                              out.cartesian_yield_twist/np.r_[np.full(3,filt.config.maximum_linear_yield_mps),np.full(3,filt.config.maximum_angular_yield_radps)]])
    return np.asarray(requests),np.asarray(labels)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--traces',type=Path,nargs='+',required=True)
    p.add_argument('--relabel-traces',type=Path,nargs='*',default=[])
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seed',type=int,default=2026100201)
    p.add_argument('--updates',type=int,default=2400)
    p.add_argument('--ridge',type=float,default=.01)
    p.add_argument('--delta-weight',type=float,default=.25)
    p.add_argument('--real-weight',type=float,default=12.)
    p.add_argument('--absolute-inputs',action='store_true',help='Additional derived magnitude channels within the same 128-unit reservoir')
    p.add_argument('--context-inputs',action='store_true',help='Derived load x commanded/measured motion products; canonical fields unchanged')
    p.add_argument('--position-context',action='store_true',help='Add existing reference-relative translation error to context')
    p.add_argument('--memory-seconds',type=float,nargs=4,default=[.04,.12,.36,1.08])
    p.add_argument('--synthetic-steps',type=int,default=350)
    p.add_argument('--context-leak-gate',action='store_true',help='Fixed random motion-conditioned leak rates, zero-load equilibrium unchanged')
    p.add_argument('--memory-challenges',action='store_true',help='Half the synthetic histories explicitly test unloaded-stall retention and progress-triggered release')
    p.add_argument('--drift-weight',type=float,default=0.,help='Weight on 0.64s integrated translational-action error, normalized by 20mm; imitation proxy only')
    args=p.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    if not 350<=args.synthetic_steps<=1400:raise ValueError('Synthetic history length outside registered resource bound')
    if args.memory_challenges and args.synthetic_steps<1000:raise ValueError('Memory challenges require complete long histories')
    if not np.isfinite(args.drift_weight) or args.drift_weight<0:raise ValueError('Invalid drift-loss weight')
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip()
    assert memory!='max' and int(memory)<=3*1024**3
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    execution=dict(status='running',started_utc=now(),argv=sys.argv,host=platform.node(),
                   python=sys.executable,python_version=platform.python_version(),torch_version=torch.__version__,
                   numpy_version=np.__version__,memory_max=memory,threads=1)
    write(out/'execution.json',execution)
    source_files=[Path(__file__),ROOT/'tools/optimize_tool_contact_20261002.py']+sorted((ROOT/'scripts').glob('*.py'))
    source_hashes={str(p.relative_to(ROOT)):sha(p) for p in source_files}
    subprocess.run(['tar','-czf',str(out/'source_overlay.tar.gz'),*source_hashes],cwd=ROOT,check=True)
    torch.set_num_threads(1);torch.manual_seed(args.seed)
    config=json.loads(args.config.read_text());rng=np.random.default_rng(args.seed)
    actor=OfficeVMCMemoryESN.__new__(OfficeVMCMemoryESN)
    actor.scale=np.array([8.,8.,8.,1.,1.,1.])
    actor.win=rng.normal(0,.25,(128,6))
    actor.w=rng.normal(size=(128,128))*(rng.random((128,128))<.08)
    actor.w*=.8/np.max(np.abs(np.linalg.eigvals(actor.w)))
    if min(args.memory_seconds)<=0:raise ValueError('Positive reservoir time scales required')
    actor.leak=1-np.exp(-.04/np.repeat(args.memory_seconds,32))
    actor.absolute_inputs=args.absolute_inputs
    if args.absolute_inputs:
        # Draw after the recurrent matrix: a paired seed keeps the signed
        # input block, recurrent weights and leak rates exactly identical.
        actor.win=np.c_[actor.win,np.random.default_rng(args.seed+20000).normal(0,.25,(128,6))]
    actor.context_inputs=args.context_inputs
    actor.position_context=args.position_context
    actor.context_dimension=12 if args.position_context else 9
    if args.context_leak_gate and not args.context_inputs:raise ValueError('Context leak gate requires context inputs')
    actor.context_gate_w=np.random.default_rng(args.seed+40000).normal(0,1,(128,actor.context_dimension)) if args.context_leak_gate else None
    if args.position_context and not args.context_inputs:raise ValueError('Position context requires context inputs')
    if args.context_inputs:
        if not args.absolute_inputs:raise ValueError('Use --absolute-inputs with --context-inputs')
        actor.win=np.c_[actor.win,np.random.default_rng(args.seed+30000).normal(0,.25/3,(128,12*actor.context_dimension))]
    observations=[];features=[];targets=[];requests=[];episodes=[];is_train=[];importance=[];lineage=[]
    def append(obs,ep,train,weight,actual=None):
        raw,y=filtered_labels(obs,config)
        if actual is not None:
            np.testing.assert_array_equal(raw,actual)
        actor.reset();features.extend(actor.features(o) for o in obs)
        observations.extend(obs);targets.extend(y);requests.extend(raw)
        episodes.extend([ep]*len(obs));is_train.extend([train]*len(obs));importance.extend([weight]*len(obs))
    for ep in range(48):
        erng=np.random.default_rng(args.seed+10000+ep);wrench=np.zeros(6);target=np.zeros(6);seq=[];translation_error=np.zeros(3)
        if args.memory_challenges and ep%2==0:
            append(memory_challenge_history(erng,args.synthetic_steps),ep,ep<40,1.);continue
        # Entire histories held out, including independent random draws.
        for step in range(args.synthetic_steps):
            if step%35==0:
                target=erng.normal(0,[8,8,8,.8,.8,.8]) if erng.random()<.7 else np.zeros(6)
                direction=np.array([[1,0,0],[.8,-.6,0],[0,0,1],[0,0,-1],[-1,0,0],[0,1,0]])[int(erng.integers(6))]
                command=.04*direction if erng.random()>.15 else np.zeros(3)
                progress_fraction=float(erng.choice([0.,.2,.8,1.]))
                if args.position_context:error_target=erng.normal(0,[.025,.025,.07])
            wrench+=(1-np.exp(-.04/float(erng.choice([.04,.12,.4]))))*(target-wrench)
            if step<25 or step>=args.synthetic_steps-80:wrench[:]=0
            if step in (60,140,220):wrench+=erng.normal(0,[25,25,25,2,2,2])
            obs=np.zeros(48);obs[39:45]=wrench;obs[14:17]=command
            obs[20:23]=.03*direction;obs[26:29]=command*(1-progress_fraction);obs[45:48]=direction;seq.append(obs)
            if args.position_context:
                translation_error+=(1-np.exp(-.04/.4))*(error_target-translation_error)
                obs[20:23]=translation_error
        append(np.asarray(seq),ep,ep<40,1.)
    for i,path in enumerate(args.traces+args.relabel_traces):
        with np.load(path,allow_pickle=False) as z:obs=z['observation'].copy();raw=z['applied_action'].copy()
        actual=i<len(args.traces)
        if actual:
            # Fail before fitting if requested->filtered labels differ from
            # the real execution chain, including physical unit overrides.
            replay_raw,replay_filtered=filtered_labels(obs,config)
            with np.load(path.parent/'execution_chain.npz') as chain:
                np.testing.assert_array_equal(replay_raw,chain['requested_action'])
                executed=np.c_[(1-chain['wbc_scale'])/(1-FILTER_CONFIG.minimum_wbc_scale),
                    chain['yield_twist']/np.r_[np.full(3,FILTER_CONFIG.maximum_linear_yield_mps),np.full(3,FILTER_CONFIG.maximum_angular_yield_radps)]]
                np.testing.assert_allclose(replay_filtered,executed,rtol=0,atol=1e-12)
        append(obs,48+i,True,args.real_weight if actual else args.real_weight/3.,actual=raw if actual else None)
        result=json.loads(path.with_suffix('.json').read_text())
        lineage.append(dict(path=str(path.resolve()),sha256=sha(path),actual_execution_labels=actual,
                            counterfactual_relabel=not actual,task_success=result['task_success'],
                            strict_success=result['strict_success']))
    x=np.asarray(features);y=np.asarray(targets);raw_requests=np.asarray(requests)
    ep=np.asarray(episodes);train=np.asarray(is_train);w=np.asarray(importance)
    del features,targets,requests,episodes,is_train,importance
    norm=np.maximum(x[train].std(0),.005)
    context_dimension=actor.context_dimension
    load_dimension=x.shape[1]-context_dimension if args.context_inputs else x.shape[1]
    xt=x[train,:load_dimension]/norm[:load_dimension];yt=np.arctanh(np.clip(y[train],-.98,.98));yt[:,0]=y[train,0]
    weights=np.zeros((x.shape[1],7))
    weights[:load_dimension]=np.linalg.solve(xt.T@(w[train,None]*xt)+args.ridge*np.eye(load_dimension),xt.T@(w[train,None]*yt))/norm[:load_dimension,None]
    base=x@weights;del xt,yt
    hidden=nn.Linear(x.shape[1],128,bias=False);head=nn.Linear(128,7,bias=False);nn.init.zeros_(head.weight)
    opt=torch.optim.AdamW(list(hidden.parameters())+list(head.parameters()),lr=.002,weight_decay=1e-5)
    tx=torch.tensor(x/norm,dtype=torch.float32);ty=torch.tensor(y,dtype=torch.float32);tb=torch.tensor(base,dtype=torch.float32)
    pool=np.flatnonzero(train);pair_pool=pool[(pool>0)&(ep[pool]==ep[np.maximum(pool-1,0)])]
    prob=w[pool]/w[pool].sum();pair_prob=w[pair_pool]/w[pair_pool].sum()
    window_length=16;window_rng=np.random.default_rng(args.seed+50000)
    window_pool=np.flatnonzero(train[:-window_length+1]&(ep[:-window_length+1]==ep[window_length-1:]))
    window_prob=w[window_pool]/w[window_pool].sum()
    val_window_pool=np.flatnonzero((~train[:-window_length+1])&(ep[:-window_length+1]==ep[window_length-1:]))[::window_length]
    def predict(indices):
        if args.context_inputs:
            context=tx[indices,-context_dimension:]@hidden.weight[:,-context_dimension:].T
            load=tx[indices,:-context_dimension]@hidden.weight[:,:-context_dimension].T
            h=torch.tanh(load+context)-torch.tanh(context)
        else:h=torch.tanh(hidden(tx[indices]))
        logits=tb[indices]+head(h)
        return torch.cat((logits[:,:1].clamp(0,1),torch.tanh(logits[:,1:])),1)
    def drift_loss(starts):
        indices=torch.from_numpy((starts[:,None]+np.arange(window_length)).ravel())
        error=(predict(indices)-ty[indices]).reshape(-1,window_length,7)[:,:,1:4]
        return ((error.sum(1)*(.04*.32)/.02)**2).mean()
    history=[];best=float('inf');best_state=None
    val=np.flatnonzero(~train)
    for step in range(args.updates):
        ids=torch.from_numpy(rng.choice(pool,1024,p=prob));pairs=torch.from_numpy(rng.choice(pair_pool,512,p=pair_prob))
        pred=predict(ids);loss=((pred-ty[ids])**2).mean()
        dloss=(((predict(pairs)-predict(pairs-1))-(ty[pairs]-ty[pairs-1]))**2).mean()
        drift=drift_loss(window_rng.choice(window_pool,64,p=window_prob)) if args.drift_weight else torch.tensor(0.)
        total=loss+args.delta_weight*dloss+args.drift_weight*drift;opt.zero_grad(set_to_none=True);total.backward()
        nn.utils.clip_grad_norm_(list(hidden.parameters())+list(head.parameters()),5.);opt.step()
        if step%100==0 or step==args.updates-1:
            with torch.no_grad():
                validation_mse=float(((predict(val)-ty[val])**2).mean())
                validation_drift=float(drift_loss(val_window_pool)) if args.drift_weight else 0.
                score=validation_mse+args.drift_weight*validation_drift
            history.append(dict(update=step+1,train_mse=float(loss.detach()),delta_mse=float(dloss.detach()),drift_proxy=float(drift.detach()),synthetic_validation_mse=validation_mse,validation_drift_proxy=validation_drift,selection_score=score))
            if score<best:
                best=score;best_state=(hidden.weight.detach().numpy().copy(),head.weight.detach().numpy().copy())
    hidden_w,output_w=best_state
    np.savez_compressed(out/'checkpoint.npz',contract=actor.contract,win=actor.win,w=actor.w,leak=actor.leak,
                        scale=actor.scale,weights=weights,feature_scale=norm,hidden_w=hidden_w,output_w=output_w,
                        axis_separable=False,output_gain=1.,absolute_inputs=args.absolute_inputs,context_inputs=args.context_inputs,position_context=args.position_context,
                        **({'context_gate_w':actor.context_gate_w} if actor.context_gate_w is not None else {}))
    deployed=OfficeVMCMemoryESN(out/'checkpoint.npz');replay=[]
    previous=None
    for eid,o in zip(ep,observations):
        if eid!=previous:deployed.reset();previous=eid
        replay.append(deployed.act(o))
    replay=np.asarray(replay)
    scaled=x/norm
    if args.context_inputs:
        context=scaled[:,-context_dimension:]@hidden_w[:,-context_dimension:].T
        hidden_value=np.tanh(scaled[:,:-context_dimension]@hidden_w[:,:-context_dimension].T+context)-np.tanh(context)
    else:hidden_value=np.tanh(scaled@hidden_w.T)
    expected=base+hidden_value@output_w.T
    expected[:,1:]=np.tanh(expected[:,1:]);expected[:,0]=np.clip(expected[:,0],0,1)
    np.testing.assert_allclose(replay,expected,rtol=0,atol=1e-10)
    deployed.reset();np.testing.assert_array_equal(deployed.act(np.zeros(48)),np.zeros(7))
    np.savez_compressed(out/'training_data.npz',observation=np.asarray(observations),episode=ep,train=train,
                        requested_teacher_action=raw_requests,filtered_teacher_action=y,prediction=replay,importance=w)
    metadata=dict(completed_utc=now(),seed=args.seed,config=config,config_sha256=sha(args.config),
                  checkpoint_sha256=sha(out/'checkpoint.npz'),training_data_sha256=sha(out/'training_data.npz'),
                  source_sha256=source_hashes,source_archive_sha256=sha(out/'source_overlay.tar.gz'),
                  lineage=lineage,reservoir_width=128,readout_width=128,updates=args.updates,delta_weight=args.delta_weight,real_weight=args.real_weight,
                  train_mse=float(np.mean((replay[train]-y[train])**2)),synthetic_validation_mse=float(np.mean((replay[~train]-y[~train])**2)),
                  exact_zero_equilibrium=True,actor_inputs=('canonical48[14:17,20:23,26:29,39:48] estimated wrench and reference-relative motion/error' if args.position_context else 'canonical48[14:17,26:29,39:48] estimated wrench and nominal/measured motion' if args.context_inputs else 'canonical48[39:45] encoder-estimated wrench history only'),
                  absolute_input_channels=args.absolute_inputs,
                  context_input_products=args.context_inputs,
                  position_error_context=args.position_context,memory_seconds=args.memory_seconds,synthetic_steps=args.synthetic_steps,
                  contextual_leak_gate=args.context_leak_gate,extra_fixed_gate_parameters=int(actor.context_gate_w.size) if actor.context_gate_w is not None else 0,
                  synthetic_memory_challenges=args.memory_challenges,
                  drift_weight=args.drift_weight,drift_window_s=window_length*.04,
                  drift_proxy_note='Integrated translational-action discrepancy, not observed robot RMSE; full physical validation required',
                  action_filter_linear_limit_mps=FILTER_CONFIG.maximum_linear_yield_mps,actual_filter_replay_verified=True,
                  closed_loop_validation=False,limitations='Synthetic held-out histories only; physical traces are declared development training identities; no physical generalization claim')
    assert all(sha(ROOT/name)==digest for name,digest in source_hashes.items()),'Training source changed during fit'
    write(out/'TRAINING_COMPLETE.json',metadata);write(out/'training_history.json',history)
    execution.update(status='complete',ended_utc=now(),checkpoint_sha256=metadata['checkpoint_sha256'])
    write(out/'execution.json',execution)
    print(json.dumps(metadata,indent=2))

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path)
        parsed,_=parser.parse_known_args()
        if parsed.output and (parsed.output/'execution.json').is_file():
            path=parsed.output/'execution.json';record=json.loads(path.read_text())
            record.update(status='failed_preserved',ended_utc=now(),error=repr(exc));write(path,record)
        raise
