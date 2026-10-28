#!/usr/bin/env python3
"""Train paired pure ESN/MLP students while screening only weight decay."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SRC = ROOT / "tools" / "train_esn_mlp_input_scale_screen_20261001.py"
spec = importlib.util.spec_from_file_location("input_train", SRC)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""): h.update(block)
    return h.hexdigest()

def activate(raw):
    return torch.cat((torch.sigmoid(raw[:, :1]), torch.tanh(raw[:, 1:])), dim=1)

def fit_model(x, y, w, vx, vy, vw, kind, seed, decay, epochs):
    torch.set_num_threads(1); torch.manual_seed(seed); rng=np.random.default_rng(seed)
    if kind == "esn": model=nn.Sequential(nn.Linear(176,128), nn.Tanh(), nn.Linear(128,7))
    else: model=nn.Sequential(nn.Linear(48,128), nn.Tanh(), nn.Linear(128,128), nn.Tanh(), nn.Linear(128,7))
    opt=torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=decay)
    tx,ty,tw=torch.from_numpy(x),torch.from_numpy(y),torch.from_numpy(w)
    vx,vy,vw=torch.from_numpy(vx),torch.from_numpy(vy),torch.from_numpy(vw)
    best=float("inf"); best_state=None; hist=[]
    for epoch in range(epochs):
        order=rng.permutation(len(tx)); losses=[]
        for start in range(0,len(order),2048):
            idx=torch.from_numpy(order[start:start+2048]); pred=activate(model(tx[idx]))
            loss=(((pred-ty[idx])**2).mean(1)*tw[idx]).mean()/tw[idx].mean()
            opt.zero_grad(set_to_none=True); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(),5.); opt.step(); losses.append(float(loss.detach()))
        with torch.no_grad():
            pred=activate(model(vx)); raw=((pred-vy)**2).mean(1); val=float((raw*vw).mean()/vw.mean())
        if epoch == 0 or (epoch+1) % 10 == 0: hist.append({"epoch":epoch+1,"train_weighted_mse":float(np.mean(losses)),"val_weighted_mse":val})
        if val < best: best=val; best_state={k:v.detach().numpy().copy() for k,v in model.state_dict().items()}
    model.load_state_dict({k:torch.from_numpy(v) for k,v in best_state.items()})
    with torch.no_grad(): pred=activate(model(vx)).numpy()
    return best_state,hist,best,pred

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--manifest",type=Path,required=True); ap.add_argument("--root",type=Path,required=True); ap.add_argument("--config",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); ap.add_argument("--decay",type=float,required=True); args=ap.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    plan=json.loads(args.config.read_text())
    if args.decay not in plan["weight_decay_values"]: raise ValueError("unregistered decay")
    if sha(args.manifest) != plan["manifest_sha256"]: raise ValueError("manifest hash mismatch")
    args.output.mkdir(parents=True)
    rows,_=mod.weighted.base.load_rows(args.manifest,args.root); train,val=mod.weighted.base.split_rows(rows)
    if len(train)!=7 or len(val)!=2: raise ValueError("unexpected fixed split")
    wm,wv=mod.weighted.weights(train,3.0),mod.weighted.weights(val,3.0)
    y=np.concatenate([r["action"] for r in train]).astype(np.float32); yv=np.concatenate([r["action"] for r in val]).astype(np.float32)
    mean,std,fmean,fstd,fs,res=mod.features(train, int(plan["training_seed"]), .25)
    _,_,_,_,vfs,_=mod.features(val, int(plan["training_seed"]), .25, (mean,std,fmean,fstd))
    x=np.concatenate([(f-fmean)/fstd for f in fs]).astype(np.float32); xv=np.concatenate([(f-fmean)/fstd for f in vfs]).astype(np.float32); w=np.concatenate(wm); wvcat=np.concatenate(wv)
    es,eh,ev,epred=fit_model(x,y,w,xv,yv,wvcat,"esn",int(plan["training_seed"]),args.decay,plan["epochs"])
    ex=np.concatenate([(r["observation"]-mean)/std for r in train]).astype(np.float32); exv=np.concatenate([(r["observation"]-mean)/std for r in val]).astype(np.float32)
    ms,mh,mv,mpred=fit_model(ex,y,w,exv,yv,wvcat,"mlp",int(plan["training_seed"])+1,args.decay,plan["epochs"])
    ep=args.output/"esn_weight_decay.npz"; mp=args.output/"mlp_weight_decay.npz"
    np.savez_compressed(ep,**mod.weighted.pack_esn(es,(mean,std,fmean,fstd),res,int(plan["training_seed"])))
    np.savez_compressed(mp,**mod.weighted.pack_mlp(ms,mean,std,int(plan["training_seed"])+1))
    from current_student_policy_20260921 import load_current
    parity={}
    for kind,path,pred,score in (("esn",ep,epred,ev),("mlp",mp,mpred,mv)):
        actor=load_current(path); replay=[]
        for row in val: actor.reset(); replay.append(np.stack([actor.act(x) for x in row["observation"]]))
        replay=np.concatenate(replay); delta=float(np.max(np.abs(replay-pred))); rs=float(np.average(np.mean((replay-yv)**2,axis=1),weights=wvcat))
        if delta>2e-6 or abs(rs-score)>1e-8: raise ValueError(f"{kind} parity mismatch")
        parity[kind]={"max_abs":delta,"weighted_mse":rs}
    meta={"contract":"VMC_teacher_paired_ESN_MLP_weight_decay_screen_20261001_v1","weight_decay":args.decay,"input_scale":.25,"seed":plan["training_seed"],"mlp_seed":int(plan["training_seed"])+1,"manifest_sha256":sha(args.manifest),"train_fixture_ids":[r["fixture_id"] for r in train],"validation_fixture_ids":[r["fixture_id"] for r in val],"checkpoint_sha256":{"esn":sha(ep),"mlp":sha(mp)},"esn_validation_weighted_mse":ev,"mlp_validation_weighted_mse":mv,"export_parity":parity,"actor_contract":plan["actor_contract"],"forbidden_inputs":plan["forbidden_inputs"],"source_sha256":{str(Path(__file__)):sha(Path(__file__)),str(SRC):sha(SRC)},"teacher_trace_sha256":{r["fixture_id"]:r["trace_sha256"] for r in rows},"teacher_chain_sha256":{r["fixture_id"]:r["execution_chain_sha256"] for r in rows},"invocation":sys.argv}
    (args.output/"TRAINING_COMPLETE.json").write_text(json.dumps(meta,indent=2)+"\n"); (args.output/"training_history.json").write_text(json.dumps({"esn":eh,"mlp":mh},indent=2)+"\n"); print(json.dumps(meta,indent=2))
if __name__ == "__main__": main()
