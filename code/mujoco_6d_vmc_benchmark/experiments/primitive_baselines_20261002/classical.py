"""Equal registered parameter-search budget, global parameters across four fixtures."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002')
def dump(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=Path(str(p)+'.tmp');tmp.write_text(json.dumps(v,indent=2,allow_nan=False));tmp.replace(p)
def candidates():
 out=[]
 for method,ks in [('admittance',[60.,150.,300.]),('impedance',[300.,600.,1000.])]:
  for k in ks:
   for z in [.8,1.4]:
    out.append(dict(id=f'{method}_k{k:g}_z{z:g}',method=method,parameters=dict(stiffness=k,rot_stiffness=k/20 if method=='impedance' else 4*k/95,zeta=z,mass=1. if method=='impedance' else .55,inertia=.08 if method=='impedance' else .065)))
 return out
def run(f,c,out,save=True):
 req=dict(fixture=f,method=c['method'],parameters=c['parameters'],output=str(out),save_substeps=save)
 path=out.parent/(out.name+'_request.json');dump(path,req)
 with (out.parent/(out.name+'_process.log')).open('w') as log:
  p=subprocess.run([sys.executable,str(HERE/'worker.py'),'--request',str(path)],stdout=log,stderr=subprocess.STDOUT,timeout=600,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 if p.returncode:
  error=(out/'ERROR.txt').read_text() if (out/'ERROR.txt').exists() else 'no worker error record'
  initial=('Initial robot/obstacle overlap' in error or 'Randomized initial state overlaps' in error)
  if not initial:raise RuntimeError(f'Execution error in {out}: {error[-1200:]}')
  return dict(fixture_id=f['id'],scene=f['scene'],initial_state_rejected=True,method=c['method'],candidate=c['id'],error=error)
 row=json.loads((out/'result.json').read_text());row['candidate']=c['id'];return row

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 fs=json.loads((ROOT/'FIXTURES.json').read_text());scenes=['ball','push','corner','table_corner'];train=[f for f in fs if f['split']=='train' and f['index'] in [0,1]];cs=candidates()
 dump(a.output/'PROTOCOL.json',dict(candidates=cs,fixtures=[f['id'] for f in train],selection='Global parameters, paired complete candidate prefix only; maximize valid task successes, then intended-contact task successes, then physical-valid count, then scene-balanced normalized raw metric sum. No validation/test selection.',registered_rollouts=len(cs)*len(train),deadline_epoch=a.deadline))
 rows=[]
 # Interleave method and all scenes for each matched candidate index.
 for ci in range(6):
  for f in train:
   for method in ['admittance','impedance']:
    if time.time()>=a.deadline:dump(a.output/'PARTIAL.json',dict(rows=len(rows),reason='deadline'));return
    c=[c for c in cs if c['method']==method][ci];out=a.output/'search'/c['id']/f['id'];row=run(f,c,out,save=False);rows.append(row);dump(a.output/'ROWS.json',rows);dump(a.output/'STATE.json',dict(completed=len(rows),total=96,latest=dict(method=method,fixture=f['id'],candidate=c['id'])));print(json.dumps(dict(completed=len(rows),method=method,fixture=f['id'],task=row.get('task_success'),physical=row.get('physical_valid'))),flush=True)
 # Verify physically paired initial models before selecting.
 for f in train:
  hashes={r['model_sha256'] for r in rows if r['fixture_id']==f['id'] and not r.get('initial_state_rejected')}
  if len(hashes)>1:raise RuntimeError(f"Model mismatch {f['id']}")
 selected={};scores={}
 for method in ['admittance','impedance']:
  scores[method]=[]
  for c in [c for c in cs if c['method']==method]:
   rr=[r for r in rows if r['candidate']==c['id']];valid=[r for r in rr if not r.get('initial_state_rejected')]
   score=dict(candidate=c,valid_task=sum(r['task_success'] and r['physical_valid'] for r in valid),contact_task=sum(r['strict_success'] for r in valid),physical=sum(r['physical_valid'] for r in valid),metric=float(np.mean([r['rmse_m']/.12+r['peak_torque_nm']/87+r['peak_speed_mps']/.5 for r in valid])) if valid else 1e9,initial_rejected=len(rr)-len(valid));scores[method].append(score)
  scores[method].sort(key=lambda s:(-s['valid_task'],-s['contact_task'],-s['physical'],s['metric'],s['candidate']['id']));selected[method]=scores[method][0]['candidate']
 dump(a.output/'SELECTION.json',dict(selected=selected,scores=scores));dump(a.output/'COMPLETE.json',dict(rollouts=len(rows),selection='SELECTION.json'))
if __name__=='__main__':main()
