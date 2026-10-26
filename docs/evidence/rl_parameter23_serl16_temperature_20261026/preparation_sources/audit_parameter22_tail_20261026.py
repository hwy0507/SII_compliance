from pathlib import Path
import json,time,collections,statistics,hashlib,os
os.sched_setaffinity(0,{52})
b=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=b/'runs/parameter_pool30_cycle22_tail_audit_20261026_v1';out.mkdir()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
metrics=['agent_train/q_loss','agent_train/actor_entropy','agent_train/entropy_coefficient','agent_train/next_q_values']
report=dict(time=time.time(),new_physics=0,optimizer_updates=0,methods={},limitation='Saved complete22 tail and first5000 updates of ongoing23. Windows are contiguous in learning state but cover different collected physics; descriptive trends are not causal or convergence evidence. No neural or physical replay.')
for m in ['impedance','admittance','vmc']:
 p=b/'runs/parameter_pool30_cycle22_20261026_v1'/m/'train/optimizer.jsonl'
 with p.open() as f:tail=[json.loads(s) for s in collections.deque(f,maxlen=5000)]
 p23=b/'runs/parameter_pool30_cycle23_20261026_v1'/m/'train/optimizer.jsonl';first=[]
 with p23.open() as f:
  for line in f:
   first.append(json.loads(line))
   if len(first)==5000:break
 assert len(tail)==len(first)==5000 and first[0]['step']==tail[-1]['step']+1
 assert all(right['step']==left['step']+1 for left,right in zip(tail+first,(tail+first)[1:]))
 windows=[]
 for name,rows in [('complete22_last5000',tail),('ongoing23_first5000',first)]:
  for i in range(5):
   v=rows[i*1000:(i+1)*1000]
   windows.append(dict(window=name,index=i,first_step=v[0]['step'],last_step=v[-1]['step'],mean={k:statistics.mean(row[k] for row in v) for k in metrics}))
 health={}
 for c in [21,22]:
  d=json.loads((b/f'runs/parameter_pool30_cycle{c}_review_20261026_v1/health/DIAGNOSIS.json').read_text())['methods'][m]
  health[c]={k:d[k] for k in ['alpha','terminal_q_in_bag_absolute_error','terminal_q_out_of_bag_absolute_error','terminal_q_absolute_error','sampled_td_absolute_error','sampled_q_values','near_action_limit_fraction']}
 report['methods'][m]=dict(windows=windows,health=health,complete22_log=dict(path=str(p),sha256=sha(p)),first5000_23_canonical_sha256=hashlib.sha256(json.dumps(first,sort_keys=True).encode()).hexdigest())
(out/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({m:[w['mean']['agent_train/q_loss'] for w in d['windows']] for m,d in report['methods'].items()},indent=2))
