from pathlib import Path
import json,time,hashlib,math,os
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
os.sched_setaffinity(0,{3});D=Path(__file__).parent;B=D.parents[1];read=lambda p:json.loads(p.read_text())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
assert read(B/'runs/parameter_partial75_recovery_cycle86_review_20261029_v1/FINISHED.json')['completed'];result={}
for m in ['vmc','admittance']:
 T=B/f'runs/{m}_recovery86_terminal_followup_20261029_v1';assert read(T/'FINISHED.json')['completed'] and read(T/'SAVED_VALUES_REVIEW.json')['passed']
 ep=B/f'runs/parameter_partial75_recovery_cycle85_20261029_v1/{m}/train/episodes.jsonl';e=[json.loads(l) for l in ep.read_text().splitlines()];assert len(e)==30
 with np.load(T/'values.npz',allow_pickle=False) as z:v={k:z[k].copy() for k in z.files}
 with np.load(T/'anchor85.npz',allow_pickle=False) as z:a={k:z[k].copy() for k in z.files}
 assert len(a['indices'])==2544 and len(v['indices'])==2574;np.testing.assert_array_equal(a['indices'],v['indices'][:2544]);np.testing.assert_array_equal(a['masks'],v['masks'][:,:2544]);np.testing.assert_array_equal(a['rewards'],v['rewards'][:2544]);np.testing.assert_array_equal(a['q_after'],v['q_before'])
 cases=[]
 for e0 in e:
  idx=e0['total_steps']-1;loc=np.flatnonzero(a['indices']==idx);assert len(loc)==1 and loc[0]>=2514;k=int(loc[0]);mask=v['masks'][:,k].astype(float);reward=float(v['rewards'][k]);qb=v['q_before'][:,k].astype(float);qa=v['q_after'][:,k].astype(float)
  sb=math.fsum(float(mask[c])*(float(qb[c])-reward)**2 for c in range(5));sa=math.fsum(float(mask[c])*(float(qa[c])-reward)**2 for c in range(5));cases.append(dict(condition=e0['condition'],replay_index=idx,task85=e0['task_success'],strict85=e0['strict_success'],reward=reward,masks=mask.tolist(),q85=qb.tolist(),q86=qa.tolist(),sse85=sb,sse86=sa,delta=sa-sb))
 assert len({c['replay_index'] for c in cases})==30
 result[m]=dict(all30_new85=cases,total_sse85=math.fsum(c['sse85'] for c in cases),total_sse86=math.fsum(c['sse86'] for c in cases),increased=sum(c['sse86']>c['sse85'] for c in cases),decreased=sum(c['sse86']<c['sse85'] for c in cases),sources=[ref(T/'values.npz'),ref(T/'anchor85.npz'),ref(ep)])
 for c in cases:assert math.isclose(c['sse86'],math.fsum(c['masks'][k]*(c['q86'][k]-c['reward'])**2 for k in range(5)),rel_tol=1e-12)
r=dict(passed=True,time=time.time(),methods=result,new_physics=0,new_network_forward=0,optimizer_updates=0,limitation='Retrospective descriptive followup of all30 new85 terminal rows per method, including known85 failures; not historical Adam/minibatch causality or a new health gate.')
p=D/'PRIOR85_COHORT86_REVIEW.json'
with p.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
assert read(p)==r
for m,r in result.items():print(m,r['total_sse85'],r['total_sse86'],[(c['condition'],c['sse85'],c['sse86']) for c in r['all30_new85'] if c['condition'] in ['active_short_train_0000','active_short_train_0600']])
