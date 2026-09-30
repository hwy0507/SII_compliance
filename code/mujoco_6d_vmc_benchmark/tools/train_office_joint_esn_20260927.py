"""Train a full-proprioception ESN from executed J1/J3 VMC teacher traces.

The trace action is the VMC request submitted to the unchanged common executor.
The source episode, request and full 48-D observation are retained in the
manifest; no event/stage/contact truth is included in the actor input.
"""
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
import torch
from torch import nn
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from esn128_proprio48_action7_20260921 import ESN128Proprio48Action7
from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def load_case(case, label_mode='saved', teacher_config=None):
    case_path=ROOT/'outputs'/case
    path=case_path/'results'
    candidates=(path/'rollout.npz',case_path/'rollout.npz',case_path/'rollout'/'rollout.npz')
    p=next((candidate for candidate in candidates if candidate.exists()),None)
    if p is None: p=next(path.glob('*/rollout.npz')) if path.is_dir() else None
    if p is None or not p.exists():
        matches=list(path.glob('*/rollout.npz'))
        if len(matches)!=1: raise FileNotFoundError(f'{case}: {matches}')
        p=matches[0]
    with np.load(p,allow_pickle=False) as z:
        obs=z['observation'].astype(np.float32)
        action=z['applied_action'].astype(np.float32)
        stage=z['stage'].astype(np.int16)
    if obs.shape[1] != 48 or action.shape != (len(obs),7): raise ValueError(f'{case} schema')
    if label_mode == 'dagger':
        if teacher_config is None: raise ValueError('teacher config required for dagger labels')
        options=teacher_config.get('options',teacher_config)
        action_scale=float(teacher_config.get('action_scale',1.0))
        teacher=SixDVirtualDynamics(options)
        action=np.asarray([teacher.act(x[39:45],.04)*action_scale for x in obs],dtype=np.float32)
    return dict(case=case,path=str(p),sha256=digest(p),observation=obs,action=action,stage=stage,label_mode=label_mode)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--seed',type=int,default=2026092707)
    ap.add_argument('--train-case',action='append',required=True)
    ap.add_argument('--validation-case',action='append',required=True)
    ap.add_argument('--dagger-case',action='append',default=[])
    ap.add_argument('--teacher-config',type=Path)
    ap.add_argument('--epochs',type=int,default=160)
    ap.add_argument('--steps-per-epoch',type=int,default=48)
    ap.add_argument('--batch-size',type=int,default=2048)
    ap.add_argument('--lr',type=float,default=2e-3)
    ap.add_argument('--wrench-weight',type=float,default=0.0,
                    help='Fixed weighting from actor-visible canonical wrench estimate; zero preserves uniform loss.')
    ap.add_argument('--delta-weight',type=float,default=0.0,
                    help='Temporal derivative matching weight on adjacent teacher actions; zero preserves legacy loss.')
    ap.add_argument('--tau-scale',type=float,default=1.0,
                    help='Fixed multiplier for the three reservoir time constants; 1.0 preserves the default .08/.4/1.6 s.')
    ap.add_argument('--tau-layout', choices=['default3','medium4'], default='default3',
                    help='Fixed matched-budget leak layout: default3=.08/.4/1.6 s, medium4=.04/.16/.64/2.56 s.')
    ap.add_argument('--input-mask',default='all',
                    help='Actor-visible canonical48 mask: all, sensors_only (q,dq,estimated load/wrench), or comma-separated indices.')
    args=ap.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    torch.set_num_threads(1); torch.manual_seed(args.seed); np.random.seed(args.seed)
    teacher_config=json.loads(args.teacher_config.read_text()) if args.teacher_config else None
    train=[load_case(x) for x in args.train_case]
    train += [load_case(x,'dagger',teacher_config) for x in args.dagger_case]
    val=[load_case(x) for x in args.validation_case]
    mean=np.concatenate([x['observation'] for x in train]).mean(0).astype(np.float32)
    std=np.concatenate([x['observation'] for x in train]).std(0).clip(min=.03).astype(np.float32)
    actor=ESN128Proprio48Action7(mean,std,seed=args.seed)
    if args.input_mask == 'all':
        input_mask=np.ones(48,dtype=np.float32)
    elif args.input_mask == 'sensors_only':
        input_mask=np.zeros(48,dtype=np.float32)
        input_mask[:14]=1.0
        input_mask[32:45]=1.0
    else:
        try:
            indices=sorted({int(x) for x in args.input_mask.split(',') if x.strip()})
        except ValueError as exc:
            raise ValueError('input-mask must be all, sensors_only, or comma-separated indices') from exc
        if any(i<0 or i>=48 for i in indices): raise ValueError('input-mask index outside canonical48D')
        input_mask=np.zeros(48,dtype=np.float32); input_mask[indices]=1.0
    actor.input_mask=input_mask
    if args.tau_scale <= 0: raise ValueError('tau-scale must be positive')
    if args.tau_layout == 'medium4':
        base_tau=np.concatenate([np.full(128//4,.04),np.full(128//4,.16),
                                 np.full(128//4,.64),np.full(128-3*(128//4),2.56)])
        actor.leak=1-np.exp(-actor.dt/(base_tau*args.tau_scale))
    elif args.tau_scale != 1.0:
        base_tau=np.concatenate([np.full(128//3,.08),np.full(128//3,.4),np.full(128-2*(128//3),1.6)])
        actor.leak=1-np.exp(-actor.dt/(base_tau*args.tau_scale))
    def feature_rows(rows):
        out=[]
        for row in rows:
            actor.reset()
            out.append(np.stack([actor.features(x) for x in row['observation']]).astype(np.float32))
        return out
    train_f,val_f=feature_rows(train),feature_rows(val)
    fcat=np.concatenate(train_f); fmean=fcat.mean(0).astype(np.float32); fstd=fcat.std(0).clip(min=.03).astype(np.float32)
    train_f=[(x-fmean)/fstd for x in train_f]; val_f=[(x-fmean)/fstd for x in val_f]
    x=np.concatenate(train_f); y=np.concatenate([r['action'] for r in train]).astype(np.float32)
    # The weighting is computed only from the six wrench-estimate channels in
    # canonical48D. It is not contact truth, an event clock, stage, or gate.
    wrench_norm=np.concatenate([np.linalg.norm(r['observation'][:,39:45],axis=1) for r in train]).astype(np.float32)
    if args.wrench_weight:
        scale=max(float(np.percentile(wrench_norm,90)),1e-6)
        sample_weight=(1.0+args.wrench_weight*np.clip(wrench_norm/scale,0.0,3.0)).astype(np.float32)
    else:
        sample_weight=np.ones(len(x),dtype=np.float32)
    pair_i=[]; pair_j=[]; offset=0
    for row in train:
        n=len(row['action'])
        if n>1:
            pair_i.append(np.arange(offset,offset+n-1,dtype=np.int64))
            pair_j.append(np.arange(offset+1,offset+n,dtype=np.int64))
        offset += n
    pair_i=np.concatenate(pair_i) if pair_i else np.empty(0,dtype=np.int64)
    pair_j=np.concatenate(pair_j) if pair_j else np.empty(0,dtype=np.int64)
    xv=np.concatenate(val_f); yv=np.concatenate([r['action'] for r in val]).astype(np.float32)
    model=nn.Sequential(nn.Linear(x.shape[1],128),nn.Tanh(),nn.Linear(128,7))
    opt=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=1e-5)
    tx,ty,tw=torch.from_numpy(x),torch.from_numpy(y),torch.from_numpy(sample_weight)
    tpi,tpj=torch.from_numpy(pair_i),torch.from_numpy(pair_j)
    vx,vy=torch.from_numpy(xv),torch.from_numpy(yv)
    rng=np.random.default_rng(args.seed)
    best=float('inf'); best_state=None; history=[]; t0=time.time()
    def activate(raw):
        return torch.cat((torch.sigmoid(raw[:,:1]),torch.tanh(raw[:,1:])),1)
    for epoch in range(args.epochs):
        model.train(); losses=[]
        for _ in range(args.steps_per_epoch):
            idx=torch.from_numpy(rng.integers(0,len(tx),size=args.batch_size))
            pred=activate(model(tx[idx]))
            loss=(((pred-ty[idx])**2).mean(dim=1)*tw[idx]).sum()/tw[idx].sum()
            if args.delta_weight and len(tpi):
                pidx=torch.from_numpy(rng.integers(0,len(tpi),size=args.batch_size))
                pa=activate(model(tx[tpi[pidx]])); pb=activate(model(tx[tpj[pidx]]))
                target_delta=ty[tpj[pidx]]-ty[tpi[pidx]]
                loss=loss+args.delta_weight*((pb-pa-target_delta)**2).mean()
            opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5.);opt.step();losses.append(float(loss))
        if epoch==0 or (epoch+1)%5==0:
            model.eval()
            with torch.no_grad(): vp=activate(model(vx)); vm=float(((vp-vy)**2).mean())
            rec=dict(epoch=epoch+1,train_mse=float(np.mean(losses)),validation_mse=vm,elapsed_s=time.time()-t0)
            history.append(rec); (args.output/'status.json').write_text(json.dumps(rec,indent=2))
            if vm<best: best=vm; best_state={k:v.detach().numpy().copy() for k,v in model.state_dict().items()}
            print(json.dumps(rec),flush=True)
    model.load_state_dict({k:torch.from_numpy(v) for k,v in best_state.items()})
    checkpoint=dict(contract='proprio48_esn128_action7_v1',seed=np.int64(args.seed),mean=mean,std=std,
        win=actor.win,w=actor.w,leak=actor.leak,input_mask=input_mask,alpha=np.float64(1.0),
        output_gain=np.float64(1.0),fmean=fmean,fstd=fstd,w1=best_state['0.weight'],b1=best_state['0.bias'],
        w2=best_state['2.weight'],b2=best_state['2.bias'])
    np.savez_compressed(args.output/'best.npz',**checkpoint)
    manifest=dict(contract='proprio48_esn128_action7_v1',seed=args.seed,observation_dim=48,action_dim=7,
        reservoir_units=128,teacher='J1/J3 fixed stiff VMC',labels='saved teacher actions plus optional DAgger labels from same VMC on student observations',
        forbidden_inputs=['contact truth','ball state','event time','task stage','visual/range'],train_cases=args.train_case,
        validation_cases=args.validation_case,dagger_cases=args.dagger_case,teacher_config=str(args.teacher_config) if args.teacher_config else None,wrench_weight=args.wrench_weight,delta_weight=args.delta_weight,tau_scale=args.tau_scale,tau_layout=args.tau_layout,input_mask_mode=args.input_mask,input_mask=input_mask.tolist(),train_trace_hashes=[(r['case'],r['sha256'],r['label_mode']) for r in train],
        validation_trace_hashes=[(r['case'],r['sha256']) for r in val],best_validation_mse=best,
        history=history,checkpoint_sha256=digest(args.output/'best.npz'),
        source_sha256={str(Path(__file__)):digest(Path(__file__)),
                       str(Path(__file__).resolve().parents[1]/'scripts/esn128_proprio48_action7_20260921.py'):digest(Path(__file__).resolve().parents[1]/'scripts/esn128_proprio48_action7_20260921.py')})
    (args.output/'TRAINING_COMPLETE.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest),flush=True)

if __name__=='__main__': main()
