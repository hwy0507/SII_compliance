from pathlib import Path
import os,json,hashlib,time,statistics,math,shutil
os.sched_setaffinity(0,{54})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/vmc48_saved_spike_20261027_v1';O.mkdir();run=B/'runs/parameter_capacity_pool30_cycle48_20261026_v1/vmc/train'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
op=run/'optimizer.jsonl';ep=run/'episodes.jsonl';tr=run/'transitions.jsonl';inputs={str(p):sha(p) for p in [op,ep,tr]}
rows=[json.loads(l) for l in op.read_text().splitlines()];episodes=[json.loads(l) for l in ep.read_text().splitlines()];transitions=[json.loads(l) for l in tr.read_text().splitlines()];assert len(rows)==len(transitions)==41250 and len(episodes)==30
losskey='agent_train/q_loss';idx=max(range(len(rows)),key=lambda i:rows[i][losskey]);peak=rows[idx];step=peak['step'];assert transitions[idx]['step']==step and peak[losskey]==132.71499633789062
assert all(math.isfinite(v) for row in rows for v in row.values() if isinstance(v,(int,float)))
def summary(rs):
 return dict(first_step=rs[0]['step'],last_step=rs[-1]['step'],count=len(rs),q_loss_mean=statistics.mean(r[losskey] for r in rs),q_loss_max=max(r[losskey] for r in rs),entropy_mean=statistics.mean(r['agent_train/actor_entropy'] for r in rs),entropy_range=[min(r['agent_train/actor_entropy'] for r in rs),max(r['agent_train/actor_entropy'] for r in rs)],alpha_range=[min(r['agent_train/entropy_coefficient'] for r in rs),max(r['agent_train/entropy_coefficient'] for r in rs)])
windows={}
for n in [100,1000]:
 assert idx>=n and idx+n<len(rows);windows[f'before{n}']=summary(rows[idx-n:idx]);windows[f'after{n}']=summary(rows[idx+1:idx+1+n])
windows['last1000']=summary(rows[-1000:]);windows['first1000']=summary(rows[:1000]);near=[e for e in episodes if abs(e['total_steps']-step)<=2000]
paired=json.loads((B/'runs/parameter47_48_saved_outcomes_20261027_v1/REVIEW.json').read_text());changes=[x for x in paired['methods']['vmc']['conditions'] if x['success_changed']]
for p,h in inputs.items():assert sha(Path(p))==h
report=dict(passed=True,time=time.time(),peak=peak,peak_index=idx,transition_at_peak=transitions[idx],windows=windows,terminal_events_within2000_steps=near,changed_success_conditions=changes,loss_counts=dict(over10=sum(r[losskey]>10 for r in rows),over50=sum(r[losskey]>50 for r in rows),over100=sum(r[losskey]>100 for r in rows)),inputs=inputs,all_saved_optimizer_numbers_finite=True,new_physics=0,optimizer_updates=0,convergence_claim=False,limitation='Posthoc saved temporal description around the largest loss, not a replay-batch log, causal terminal attribution, or a hyperparameter intervention. The transition logged at the same step need not be the row responsible for sampled loss. Fixed future49 first5000 follow-up is separate.')
(O/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');shutil.copyfile(__file__,O/'audit.py');print(json.dumps({k:v for k,v in report.items() if k not in ['inputs','changed_success_conditions','transition_at_peak']},indent=2))
