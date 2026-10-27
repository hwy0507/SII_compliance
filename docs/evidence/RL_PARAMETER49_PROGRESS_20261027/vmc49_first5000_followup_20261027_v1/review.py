from pathlib import Path
import os,json,time,statistics,hashlib,math
O=Path(__file__).parent;B=O.parents[1];os.sched_setaffinity(0,{52});os.nice(10);plan=json.loads((O/'PLAN.json').read_text());run=B/'runs/parameter_capacity_pool30_cycle49_20261026_v1/vmc/train'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 assert sha(Path(__file__))==plan['source_sha256'];limit=time.monotonic()+900;target=plan['optimizer_rows']
 while True:
  assert time.monotonic()<limit and not (run/'FAILURE.json').exists()
  proc=Path(f"/proc/{plan['pid']}");st=(proc/'stat').read_text().rsplit(')',1)[1].split();assert st[0]!='Z' and st[19]==plan['start_ticks']
  raw=[]
  with (run/'optimizer.jsonl').open('rb') as f:
   for _ in range(target):
    line=f.readline()
    if not line.endswith(b'\n'):break
    raw.append(line)
  if len(raw)==target:break
  time.sleep(5)
 data=b''.join(raw);rows=[json.loads(l) for l in raw];assert [r['step'] for r in rows]==list(range(2018251,2023251))
 assert all(math.isfinite(v) for r in rows for v in r.values() if isinstance(v,(int,float)))
 def summary(rs):return dict(first_step=rs[0]['step'],last_step=rs[-1]['step'],count=len(rs),mean_q_loss=statistics.mean(r['agent_train/q_loss'] for r in rs),maximum_q_loss=max(r['agent_train/q_loss'] for r in rs),actor_entropy_mean=statistics.mean(r['agent_train/actor_entropy'] for r in rs),alpha_range=[min(r['agent_train/entropy_coefficient'] for r in rs),max(r['agent_train/entropy_coefficient'] for r in rs)])
 (O/'FIRST5000.jsonl').write_bytes(data)
 result=dict(passed=True,time=time.time(),summary=summary(rows),blocks=[summary(rows[i:i+1000]) for i in range(0,5000,1000)],loss_counts=dict(over10=sum(r['agent_train/q_loss']>10 for r in rows),over50=sum(r['agent_train/q_loss']>50 for r in rows),over100=sum(r['agent_train/q_loss']>100 for r in rows)),prefix_sha256=sha(O/'FIRST5000.jsonl'),plan_sha256=sha(O/'PLAN.json'),new_physics=0,optimizer_updates=0,convergence_claim=False,scope='Fixed first5000 optimizer logs registered while49 had fewer than5000 new steps; partial49 diagnostic only, not whole-cycle health or convergence. No auxiliary weights or optimizer changes.')
 (O/'REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
except BaseException as e:
 (O/'FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\n');raise
