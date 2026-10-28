"""Train a width-matched 48D/7D MLP on the same teacher replay as ESN.

This is a fairness control: the MLP sees the same canonical48D observations,
the same repeated hard/shifted teacher and DAgger traces, and the same
wrench-weighted action loss.  It receives no stage, event, contact, geometry,
or simulator truth.  The output contract is the existing pure MLP adapter.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
import torch
from torch import nn

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics

def digest(path):
    h=hashlib.sha256();
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def trace_path(case):
    root=ROOT/'outputs'/case
    candidates=[root/'rollout.npz',root/'rollout'/'rollout.npz',root/'results'/'rollout.npz',*sorted((root/'results').glob('*/rollout.npz'))]
    p=next((x for x in candidates if x.exists()),None)
    if p is None:raise FileNotFoundError(case)
    return p

def load_case(case, teacher_config=None):
    p=trace_path(case)
    with np.load(p,allow_pickle=False) as z:
        obs=np.asarray(z['observation'],dtype=np.float32)
        action=np.asarray(z['applied_action'],dtype=np.float32)
    if obs.ndim!=2 or obs.shape[1]!=48 or action.shape!=(len(obs),7):raise ValueError(case)
    mode='saved'
    if teacher_config is not None:
        teacher=SixDVirtualDynamics(teacher_config.get('options',teacher_config))
        scale=float(teacher_config.get('action_scale',1.0))
        action=np.asarray([teacher.act(row[39:45],.04)*scale for row in obs],dtype=np.float32)
        mode='dagger'
    return dict(case=case,path=p,sha256=digest(p),obs=obs,action=action,mode=mode)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--seed',type=int,default=2026092931)
    ap.add_argument('--train-case',action='append',required=True);ap.add_argument('--validation-case',action='append',required=True)
    ap.add_argument('--dagger-case',action='append',default=[]);ap.add_argument('--teacher-config',type=Path,required=True)
    ap.add_argument('--epochs',type=int,default=160);ap.add_argument('--wrench-weight',type=float,default=3.0)
    a=ap.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    a.output.mkdir(parents=True)
    torch.set_num_threads(1);torch.manual_seed(a.seed);np.random.seed(a.seed)
    cfg=json.loads(a.teacher_config.read_text())
    train=[load_case(x) for x in a.train_case]+[load_case(x,cfg) for x in a.dagger_case]
    val=[load_case(x) for x in a.validation_case]
    mean=np.concatenate([r['obs'] for r in train]).mean(0).astype(np.float32)
    std=np.concatenate([r['obs'] for r in train]).std(0).clip(min=.03).astype(np.float32)
    x=np.concatenate([(r['obs']-mean)/std for r in train]).astype(np.float32)
    y=np.concatenate([r['action'] for r in train]).astype(np.float32)
    xv=np.concatenate([(r['obs']-mean)/std for r in val]).astype(np.float32)
    yv=np.concatenate([r['action'] for r in val]).astype(np.float32)
    wrench=np.concatenate([np.linalg.norm(r['obs'][:,39:45],axis=1) for r in train])
    scale=max(float(np.percentile(wrench,90)),1e-6)
    weights=(1+a.wrench_weight*np.clip(wrench/scale,0,3)).astype(np.float32)
    model=nn.Sequential(nn.Linear(48,128),nn.Tanh(),nn.Linear(128,128),nn.Tanh(),nn.Linear(128,7))
    opt=torch.optim.AdamW(model.parameters(),lr=2e-3,weight_decay=1e-5)
    tx,ty,tw=torch.from_numpy(x),torch.from_numpy(y),torch.from_numpy(weights)
    vx,vy=torch.from_numpy(xv),torch.from_numpy(yv)
    rng=np.random.default_rng(a.seed);best=float('inf');best_state=None;history=[]
    def activate(raw):return torch.cat((torch.sigmoid(raw[:,:1]),torch.tanh(raw[:,1:])),1)
    for ep in range(a.epochs):
        order=rng.permutation(len(tx));losses=[]
        for st in range(0,len(order),2048):
            idx=torch.from_numpy(order[st:st+2048]);pred=activate(model(tx[idx]));diff=(pred-ty[idx])**2
            loss=(diff.mean(1)*tw[idx]).sum()/tw[idx].sum();opt.zero_grad();loss.backward();nn.utils.clip_grad_norm_(model.parameters(),5.);opt.step();losses.append(float(loss.detach()))
        if ep==0 or (ep+1)%5==0:
            with torch.no_grad():val_mse=float(((activate(model(vx))-vy)**2).mean())
            rec={'epoch':ep+1,'train_mse':float(np.mean(losses)),'validation_mse':val_mse};history.append(rec);(a.output/'status.json').write_text(json.dumps(rec,indent=2))
            if val_mse<best:best=val_mse;best_state={k:v.detach().numpy().copy() for k,v in model.state_dict().items()}
    ck=dict(contract='proprio48_action7_mlp_v1',seed=np.int64(a.seed),mean=mean,std=std,hidden=np.int64(128),**best_state)
    np.savez_compressed(a.output/'best.npz',**ck)
    meta=dict(contract=ck['contract'],seed=a.seed,architecture='48-128-128-7',teacher='J1/J3 fixed stiff VMC',train_cases=a.train_case,dagger_cases=a.dagger_case,validation_cases=a.validation_case,wrench_weight=a.wrench_weight,forbidden_inputs=['contact truth','ball state','event time','task stage','visual/range'],train_trace_hashes=[(r['case'],r['sha256'],r['mode']) for r in train],validation_trace_hashes=[(r['case'],r['sha256']) for r in val],best_validation_mse=best,checkpoint_sha256=digest(a.output/'best.npz'),source_sha256={str(Path(__file__)):digest(Path(__file__))})
    (a.output/'TRAINING_COMPLETE.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2))

if __name__=='__main__':main()
