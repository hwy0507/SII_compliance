#!/usr/bin/env python3
"""Fixed-reservoir/readout-seed decomposition for the pure ESN candidate."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('input_train',ROOT/'tools'/'train_esn_mlp_input_scale_screen_20261001.py'); inp=importlib.util.module_from_spec(spec); spec.loader.exec_module(inp)
WEIGHTED=ROOT/'tools'/'train_vmc_teacher_esn_mlp_weighted_20261001.py'; ws=importlib.util.spec_from_file_location('weighted_train',WEIGHTED); weighted=importlib.util.module_from_spec(ws); ws.loader.exec_module(weighted)
def sha(p):
 h=hashlib.sha256();
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--manifest',type=Path,required=True); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--readout-seed',type=int,required=True); ap.add_argument('--reservoir-seed',type=int,default=2026100101); ap.add_argument('--epochs',type=int,default=160); a=ap.parse_args()
 if a.output.exists(): raise FileExistsError(a.output)
 a.output.mkdir(parents=True)
 if sha(a.manifest)!='6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3': raise ValueError('Unregistered manifest')
 rows,_=weighted.base.load_rows(a.manifest,a.root); train,val=weighted.base.split_rows(rows); assert len(train)==7 and len(val)==2
 wm,wv=weighted.weights(train,3.0),weighted.weights(val,3.0); y=np.concatenate([r['action'] for r in train]).astype(np.float32); yv=np.concatenate([r['action'] for r in val]).astype(np.float32)
 mean,std,fmean,fstd,fs,res=inp.features(train,a.reservoir_seed,.25); _,_,_,_,vfs,_=inp.features(val,a.reservoir_seed,.25,(mean,std,fmean,fstd)); x=np.concatenate([(f-fmean)/fstd for f in fs]).astype(np.float32); xv=np.concatenate([(f-fmean)/fstd for f in vfs]).astype(np.float32); w=np.concatenate(wm); wvcat=np.concatenate(wv)
 es,eh,ev,epred=weighted.fit_model(x,y,w,xv,yv,wvcat,'esn',a.readout_seed,a.epochs); ex=np.concatenate([(r['observation']-mean)/std for r in train]).astype(np.float32); exv=np.concatenate([(r['observation']-mean)/std for r in val]).astype(np.float32); ms,mh,mv,mpred=weighted.fit_model(ex,y,w,exv,yv,wvcat,'mlp',a.readout_seed+1,a.epochs)
 ep,mp=a.output/'esn_fixed.npz',a.output/'mlp_fixed.npz'; np.savez_compressed(ep,**weighted.pack_esn(es,(mean,std,fmean,fstd),res,a.reservoir_seed)); np.savez_compressed(mp,**weighted.pack_mlp(ms,mean,std,a.readout_seed+1))
 from current_student_policy_20260921 import load_current
 parity={}
 for kind,path,pred,score in (('esn',ep,epred,ev),('mlp',mp,mpred,mv)):
  actor=load_current(path); replay=[]
  for row in val: actor.reset(); replay.append(np.stack([actor.act(x) for x in row['observation']]))
  replay=np.concatenate(replay); delta=float(np.max(np.abs(replay-pred))); rs=float(np.average(np.mean((replay-yv)**2,axis=1),weights=wvcat)); assert delta<=2e-6 and abs(rs-score)<=1e-8; parity[kind]={'max_abs':delta,'weighted_mse':rs}
 meta={'contract':'VMC_teacher_ESN_fixed_reservoir_20261001_v1','reservoir_seed':a.reservoir_seed,'readout_seed':a.readout_seed,'mlp_seed':a.readout_seed+1,'input_scale':.25,'manifest_sha256':sha(a.manifest),'train_fixture_ids':[r['fixture_id'] for r in train],'validation_fixture_ids':[r['fixture_id'] for r in val],'checkpoint_sha256':{'esn':sha(ep),'mlp':sha(mp)},'esn_validation_weighted_mse':ev,'mlp_validation_weighted_mse':mv,'export_parity':parity,'forbidden_inputs':['contact truth','object/ball state','event time','task stage','visual/range'],'actor_contract':'canonical48D/action7; pure proprioception','reservoir_width':128,'loss_emphasis':3.0,'source_sha256':{str(Path(__file__)):sha(Path(__file__)),str(ROOT/'tools'/'train_esn_mlp_input_scale_screen_20261001.py'):sha(ROOT/'tools'/'train_esn_mlp_input_scale_screen_20261001.py'),str(WEIGHTED):sha(WEIGHTED)},'teacher_trace_sha256':{r['fixture_id']:r['trace_sha256'] for r in rows},'invocation':sys.argv}
 (a.output/'TRAINING_COMPLETE.json').write_text(json.dumps(meta,indent=2)+'\n'); (a.output/'training_history.json').write_text(json.dumps({'esn':eh,'mlp':mh},indent=2)+'\n'); print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
