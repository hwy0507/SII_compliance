#!/usr/bin/env python3
"""Pre-registered load-aware readout training for the locked VMC bank.

The actor contract is unchanged: canonical48D proprioception -> action7.  The
training-only weight is a smooth function of the estimated wrench channels
(39:45); it is never exposed as an input or a runtime gate.  ESN and MLP keep
the same 128-unit trainable width and are evaluated on the frozen split.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from esn128_proprio48_action7_20260921 import ESN128Proprio48Action7

BASE = ROOT / "tools" / "train_vmc_teacher_esn_mlp_20261001.py"
spec = importlib.util.spec_from_file_location("base_train", BASE)
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def weights(rows, emphasis=3.0):
    # Smooth estimated-wrench emphasis; no binary contact/event label.
    values = []
    for r in rows:
        w = np.linalg.norm(r["observation"][:, 39:45].astype(np.float64), axis=1)
        values.append((1.0 + emphasis * np.tanh(w / 0.5)).astype(np.float32))
    return values

def esn_features(rows, seed, normalization=None):
    if normalization is None:
        obs = np.concatenate([r["observation"] for r in rows])
        mean = obs.mean(0).astype(np.float32); std = obs.std(0).clip(min=.03).astype(np.float32)
    else:
        mean, std, fmean, fstd = normalization
    actor = ESN128Proprio48Action7(mean, std, seed=seed)
    fs=[]
    for r in rows:
        actor.reset(); fs.append(np.stack([actor.features(x) for x in r["observation"]]).astype(np.float32))
    if normalization is None:
        packed=np.concatenate(fs); fmean=packed.mean(0).astype(np.float32); fstd=packed.std(0).clip(min=.03).astype(np.float32)
    return mean,std,fmean,fstd,fs

def activate(raw):
    # Avoid in-place writes into tanh's autograd result (torch 2.9 checks this).
    return torch.cat((torch.sigmoid(raw[:, :1]), torch.tanh(raw[:, 1:])), dim=1)

def fit_model(x,y,w,val_x,val_y,val_w,kind,seed,epochs=160):
    torch.set_num_threads(1); torch.manual_seed(seed); rng=np.random.default_rng(seed)
    if kind == "esn": model=nn.Sequential(nn.Linear(176,128),nn.Tanh(),nn.Linear(128,7))
    else: model=nn.Sequential(nn.Linear(48,128),nn.Tanh(),nn.Linear(128,128),nn.Tanh(),nn.Linear(128,7))
    opt=torch.optim.AdamW(model.parameters(),lr=2e-3,weight_decay=1e-5)
    tx,ty,tw=torch.from_numpy(x),torch.from_numpy(y),torch.from_numpy(w)
    vx,vy,vw=torch.from_numpy(val_x),torch.from_numpy(val_y),torch.from_numpy(val_w)
    best=float("inf"); best_state=None; hist=[]
    for epoch in range(epochs):
        order=rng.permutation(len(tx)); losses=[]
        for start in range(0,len(order),2048):
            idx=torch.from_numpy(order[start:start+2048]); pred=activate(model(tx[idx]))
            loss=(((pred-ty[idx])**2).mean(1)*tw[idx]).mean()/tw[idx].mean()
            opt.zero_grad(set_to_none=True); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(),5.); opt.step(); losses.append(float(loss.detach()))
        with torch.no_grad():
            pred=activate(model(vx)); raw=((pred-vy)**2).mean(1)
            val=float((raw*vw).mean()/vw.mean()); unweighted=float(raw.mean())
        if epoch==0 or (epoch+1)%10==0:
            hist.append({"epoch":epoch+1,"train_weighted_mse":float(np.mean(losses)),"val_weighted_mse":val,"val_mse":unweighted})
        if val<best:
            best=val; best_state={k:v.detach().numpy().copy() for k,v in model.state_dict().items()}
    model.load_state_dict({k:torch.from_numpy(v) for k,v in best_state.items()})
    with torch.no_grad():
        prediction=activate(model(vx)).numpy()
    return best_state,hist,best,prediction

def pack_esn(state, norm, reservoir, seed):
    mean,std,fmean,fstd=norm
    return dict(contract="proprio48_esn128_action7_v1",seed=np.int64(seed),mean=mean,std=std,
                win=reservoir.win,w=reservoir.w,leak=reservoir.leak,input_mask=reservoir.input_mask,
                alpha=np.float64(1.),output_gain=np.float64(1.),fmean=fmean,fstd=fstd,
                w1=state["0.weight"],b1=state["0.bias"],w2=state["2.weight"],b2=state["2.bias"])

def pack_mlp(state, mean, std, seed):
    return dict(contract="proprio48_action7_mlp_v1",seed=np.int64(seed),mean=mean,std=std,hidden=np.int64(128),
                **{"0.weight":state["0.weight"],"0.bias":state["0.bias"],"2.weight":state["2.weight"],"2.bias":state["2.bias"],"4.weight":state["4.weight"],"4.bias":state["4.bias"]})

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--manifest",type=Path,required=True); ap.add_argument("--root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); ap.add_argument("--seed",type=int,default=2026100102)
    ap.add_argument("--emphasis",type=float,choices=(0.,3.),default=3.)
    ap.add_argument("--epochs",type=int,default=160)
    a=ap.parse_args();
    if a.output.exists(): raise FileExistsError(a.output)
    a.output.mkdir(parents=True)
    if sha(a.manifest)!="6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3":
        raise ValueError("Unregistered teacher manifest")
    for entries in json.loads(a.manifest.read_text())["categories"].values():
        for row in entries:
            folder = a.root/row["folder"]
            if sha(folder/"rollout.npz")!=row["raw_files_sha256"]["rollout.npz"]:
                raise ValueError("Teacher rollout hash mismatch")
            if sha(folder/"execution_chain.npz")!=row["raw_files_sha256"]["execution_chain.npz"]:
                raise ValueError("Teacher execution-chain hash mismatch")
    rows,manifest=base.load_rows(a.manifest,a.root); train,val=base.split_rows(rows)
    if len(train)!=7 or len(val)!=2: raise ValueError("Unexpected split")
    wm,wv=weights(train,a.emphasis),weights(val,a.emphasis); y=np.concatenate([r["action"] for r in train]).astype(np.float32); yv=np.concatenate([r["action"] for r in val]).astype(np.float32)
    mean,std,fmean,fstd,fs=esn_features(train,a.seed)
    _,_,_,_,vfs=esn_features(val,a.seed,(mean,std,fmean,fstd))
    x=np.concatenate([(f-fmean)/fstd for f in fs]).astype(np.float32)
    xv=np.concatenate([(f-fmean)/fstd for f in vfs]).astype(np.float32); w=np.concatenate(wm); wvcat=np.concatenate(wv)
    esn_state,eh,ev,epred=fit_model(x,y,w,xv,yv,wvcat,"esn",a.seed,a.epochs)
    ex=np.concatenate([(r["observation"]-mean)/std for r in train]).astype(np.float32); exv=np.concatenate([(r["observation"]-mean)/std for r in val]).astype(np.float32)
    mlp_state,mh,mv,mpred=fit_model(ex,y,w,exv,yv,wvcat,"mlp",a.seed+1,a.epochs)
    reservoir=ESN128Proprio48Action7(mean,std,seed=a.seed)
    esn=pack_esn(esn_state,(mean,std,fmean,fstd),reservoir,a.seed); mlp=pack_mlp(mlp_state,mean,std,a.seed+1)
    ep=a.output/"esn_weighted.npz"; mp=a.output/"mlp_weighted.npz"; np.savez_compressed(ep,**esn); np.savez_compressed(mp,**mlp)
    meta={"contract":"VMC_teacher_weighted_ESN_MLP_20261001_v1","seed":a.seed,"manifest_sha256":sha(a.manifest),"train_fixture_ids":[r["fixture_id"] for r in train],"validation_fixture_ids":[r["fixture_id"] for r in val],"checkpoint_sha256":{"esn":sha(ep),"mlp":sha(mp)},"esn_validation_weighted_mse":ev,"mlp_validation_weighted_mse":mv,"weight_definition":"1 + 3*tanh(norm(estimated_wrench_channels[39:45])/0.5), training-only","forbidden_inputs":["contact truth","object/ball state","event time","task stage","visual/range"],"actor_contract":"canonical48D/action7; no runtime weight or gate","parameter_count":"ESN trainable readout 23,559 vs MLP 23,687; both 128-unit trainable width; reservoir fixed","source_sha256":{str(BASE):sha(BASE),str(Path(__file__)):sha(Path(__file__)),str(ROOT / "scripts" / "esn128_proprio48_action7_20260921.py"):sha(ROOT / "scripts" / "esn128_proprio48_action7_20260921.py"),str(ROOT / "scripts" / "current_student_policy_20260921.py"):sha(ROOT / "scripts" / "current_student_policy_20260921.py")}}
    from current_student_policy_20260921 import load_current
    parity={}
    for kind,path,prediction,score in (("esn",ep,epred,ev),("mlp",mp,mpred,mv)):
        actor=load_current(path); replay=[]
        for row in val:
            actor.reset(); replay.append(np.stack([actor.act(x) for x in row["observation"]]))
        replay=np.concatenate(replay)
        delta=float(np.max(np.abs(replay-prediction)))
        replay_score=float(np.average(np.mean((replay-yv)**2,axis=1),weights=wvcat))
        if delta>2e-6 or abs(replay_score-score)>1e-8:
            raise ValueError(f"{kind} exported inference differs from selected validation: {delta}, {replay_score}, {score}")
        parity[kind]={"max_abs":delta,"exported_weighted_mse":replay_score,"selected_weighted_mse":score}
    meta.update(contract="VMC_teacher_paired_ESN_MLP_20261001_v2",epochs=a.epochs,
                emphasis=a.emphasis,mlp_seed=a.seed+1,
                weight_definition=f"1 + {a.emphasis}*tanh(norm(estimated_wrench[39:45])/0.5)",
                export_parity=parity,normalization="train only; identical at validation and deployment",
                teacher_trace_sha256={r["fixture_id"]:r["trace_sha256"] for r in rows},
                teacher_chain_sha256={r["fixture_id"]:r["execution_chain_sha256"] for r in rows},
                target_semantics="execution_chain.npz filtered_action; rollout.npz applied_action retained as raw audit field",
                parameter_count={"esn_trainable":sum(v.size for v in esn_state.values()),
                                 "mlp_trainable":sum(v.size for v in mlp_state.values()),
                                 "note":"256 computational units each (128 fixed reservoir +128 readout, versus128+128 MLP); not exact parameter matching"},
                invocation=sys.argv,esn_replay=base.replay(ep,val,"esn"),mlp_replay=base.replay(mp,val,"mlp"))
    (a.output/"TRAINING_COMPLETE.json").write_text(json.dumps(meta,indent=2)+"\n"); (a.output/"training_history.json").write_text(json.dumps({"esn":eh,"mlp":mh},indent=2)+"\n"); print(json.dumps(meta,indent=2))

if __name__=="__main__": main()
