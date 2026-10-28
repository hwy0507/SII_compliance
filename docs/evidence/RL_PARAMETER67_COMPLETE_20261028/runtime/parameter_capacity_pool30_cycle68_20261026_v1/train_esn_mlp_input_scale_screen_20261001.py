#!/usr/bin/env python3
"""Pre-registered ESN input-weight scale screen on the locked VMC bank."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'scripts'))
from esn128_proprio48_action7_20260921 import ESN128Proprio48Action7
WEIGHTED=ROOT/'tools'/'train_vmc_teacher_esn_mlp_weighted_20261001.py'; spec=importlib.util.spec_from_file_location('weighted_train',WEIGHTED); weighted=importlib.util.module_from_spec(spec); spec.loader.exec_module(weighted)
SCALES={'low':.25,'baseline':.45,'high':.80}; SEEDS={'low':2026100115,'baseline':2026100116,'high':2026100117}
def sha(p):
 h=hashlib.sha256();
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def features(rows,seed,scale,norm=None):
 if norm is None:
  obs=np.concatenate([r['observation'] for r in rows]); mean=obs.mean(0).astype(np.float32); std=obs.std(0).clip(min=.03).astype(np.float32)
 else: mean,std,fmean,fstd=norm
 actor=ESN128Proprio48Action7(mean,std,seed=seed); actor.win*=scale/.45; fs=[]
 for r in rows:
  actor.reset(); fs.append(np.stack([actor.features(x) for x in r['observation']]).astype(np.float32))
 if norm is None:
  packed=np.concatenate(fs); fmean=packed.mean(0).astype(np.float32); fstd=packed.std(0).clip(min=.03).astype(np.float32)
 return mean,std,fmean,fstd,fs,actor
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--manifest',type=Path,required=True); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--profile',choices=sorted(SCALES),required=True); ap.add_argument('--seed',type=int); ap.add_argument('--epochs',type=int,default=160); a=ap.parse_args(); profile=a.profile; seed=SEEDS[profile] if a.seed is None else a.seed
 if a.output.exists(): raise FileExistsError(a.output)
 a.output.mkdir(parents=True)
 if sha(a.manifest)!='6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3': raise ValueError('Unregistered manifest')
 rows,_=weighted.base.load_rows(a.manifest,a.root); train,val=weighted.base.split_rows(rows); assert len(train)==7 and len(val)==2
 wm,wv=weighted.weights(train,3.0),weighted.weights(val,3.0); y=np.concatenate([r['action'] for r in train]).astype(np.float32); yv=np.concatenate([r['action'] for r in val]).astype(np.float32); scale=SCALES[profile]
 mean,std,fmean,fstd,fs,res=features(train,seed,scale); _,_,_,_,vfs,_=features(val,seed,scale,(mean,std,fmean,fstd)); x=np.concatenate([(f-fmean)/fstd for f in fs]).astype(np.float32); xv=np.concatenate([(f-fmean)/fstd for f in vfs]).astype(np.float32); w=np.concatenate(wm); wvcat=np.concatenate(wv)
 es,eh,ev,epred=weighted.fit_model(x,y,w,xv,yv,wvcat,'esn',seed,a.epochs); ex=np.concatenate([(r['observation']-mean)/std for r in train]).astype(np.float32); exv=np.concatenate([(r['observation']-mean)/std for r in val]).astype(np.float32); ms,mh,mv,mpred=weighted.fit_model(ex,y,w,exv,yv,wvcat,'mlp',seed+1,a.epochs)
 ep,mp=a.output/'esn_input.npz',a.output/'mlp_input.npz'; np.savez_compressed(ep,**weighted.pack_esn(es,(mean,std,fmean,fstd),res,seed)); np.savez_compressed(mp,**weighted.pack_mlp(ms,mean,std,seed+1))
 from current_student_policy_20260921 import load_current
 parity={}
 for kind,path,pred,score in (('esn',ep,epred,ev),('mlp',mp,mpred,mv)):
  actor=load_current(path); replay=[]
  for row in val: actor.reset(); replay.append(np.stack([actor.act(x) for x in row['observation']]))
  replay=np.concatenate(replay); delta=float(np.max(np.abs(replay-pred))); rs=float(np.average(np.mean((replay-yv)**2,axis=1),weights=wvcat)); assert delta<=2e-6 and abs(rs-score)<=1e-8; parity[kind]={'max_abs':delta,'weighted_mse':rs}
 meta={'contract':'VMC_teacher_ESN_input_scale_screen_20261001_v1','profile':profile,'input_scale':scale,'seed':seed,'mlp_seed':seed+1,'manifest_sha256':sha(a.manifest),'train_fixture_ids':[r['fixture_id'] for r in train],'validation_fixture_ids':[r['fixture_id'] for r in val],'checkpoint_sha256':{'esn':sha(ep),'mlp':sha(mp)},'esn_validation_weighted_mse':ev,'mlp_validation_weighted_mse':mv,'export_parity':parity,'forbidden_inputs':['contact truth','object/ball state','event time','task stage','visual/range'],'actor_contract':'canonical48D/action7; pure proprioception','reservoir_width':128,'loss_emphasis':3.0,'source_sha256':{str(Path(__file__)):sha(Path(__file__)),str(WEIGHTED):sha(WEIGHTED),str(ROOT/'scripts'/'esn128_proprio48_action7_20260921.py'):sha(ROOT/'scripts'/'esn128_proprio48_action7_20260921.py')},'teacher_trace_sha256':{r['fixture_id']:r['trace_sha256'] for r in rows},'invocation':sys.argv}
 (a.output/'TRAINING_COMPLETE.json').write_text(json.dumps(meta,indent=2)+'\n'); (a.output/'training_history.json').write_text(json.dumps({'esn':eh,'mlp':mh},indent=2)+'\n'); print(json.dumps(meta,indent=2))
if __name__=='__main__': main()
