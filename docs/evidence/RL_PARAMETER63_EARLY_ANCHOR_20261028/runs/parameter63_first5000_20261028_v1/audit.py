from pathlib import Path
import json,hashlib,time,os,subprocess
os.sched_setaffinity(0,{54})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=Path(__file__).parent

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
try:
 plan=json.loads((out/'PLAN.json').read_text());assert plan['cycle']==63 and plan['prefix_rows']==5000
 assert all(sha(Path(r['path']))==r['sha256'] for r in plan['registration'].values())
 root=B/'runs/parameter_capacity_pool30_cycle63_20261026_v1';jobs=json.loads((root/'LAUNCH.json').read_text())['jobs'];deadline=time.monotonic()+3600;inputs={}
 for job in jobs:
  m=job['controller'];run=root/m/'train';source=run/'optimizer.jsonl'
  while True:
   assert time.monotonic()<deadline,'Fixed first5000 wait expired';assert not (run/'FAILURE.json').exists()
   st=Path(f"/proc/{job['pid']}/stat");assert st.exists() and st.read_text().split(') ')[1].split()[19]==job['proc_start_ticks']
   rows=[]
   if source.exists():
    with source.open() as f:
     for line in f:
      if line.endswith('\n'):rows.append(line)
      if len(rows)==5000:break
   if len(rows)==5000:break
   time.sleep(5)
  p=out/f'{m}_first5000.jsonl'
  with p.open('x') as f:f.writelines(rows)
  inputs[m]=dict(path=str(p),sha256=sha(p))
 import numpy as np
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axes=plt.subplots(3,2,figsize=(12,9),constrained_layout=True);result={}
 for i,m in enumerate(plan['methods']):
  rows=[json.loads(l) for l in Path(inputs[m]['path']).read_text().splitlines()];assert len(rows)==5000 and [r['step'] for r in rows]==list(range(rows[0]['step'],rows[0]['step']+5000));stats={}
  for col,key in enumerate(['agent_train/q_loss','agent_train/actor_loss']):
   v=np.array([r[key] for r in rows]);assert np.isfinite(v).all();stats[key]=dict(first1000=float(v[:1000].mean()),last1000=float(v[-1000:].mean()),maximum=float(v.max()),mean=float(v.mean()),nonfinite=0)
   ax=axes[i,col];ax.plot(v,alpha=.2,lw=.4);ax.plot(np.arange(999,5000),np.convolve(v,np.ones(1000)/1000,mode='valid'));ax.set_title(m+' '+key);ax.grid(alpha=.2)
  result[m]=dict(first_step=rows[0]['step'],last_step=rows[-1]['step'],metrics=stats)
 fig.savefig(out/'loss.png',dpi=120);(out/'REVIEW.json').write_text(json.dumps(dict(time=time.time(),passed=True,methods=result,inputs=inputs,new_physics=0,optimizer_updates=0,convergence_claim=False,scope='Descriptive first5000 of63, registered after training launch; same prefix length as54; original53-55 evidence retained; fixed56-58 evidence and completed59-61 window and preregistered62-64 window unchanged',plot_sha256=sha(out/'loss.png')),indent=2)+'\n')
except BaseException as e:
 (out/'FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e))));raise
