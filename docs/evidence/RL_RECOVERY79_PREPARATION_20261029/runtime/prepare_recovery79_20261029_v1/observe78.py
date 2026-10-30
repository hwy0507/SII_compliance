from pathlib import Path
import json,time,os,hashlib
os.sched_setaffinity(0,{3})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;P=B/'runs/parameter_partial75_recovery_cycle78_20261029_v1';F=B/'runs/serl_take33_frozen_full30_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6')
def read(p):return json.loads(p.read_text())
def put(p,j):
 with p.open('x') as f:f.write(json.dumps(j,indent=2)+'\n')
def live(j):
 p=Path('/proc')/str(j['pid'])/'stat'
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
parent=B/'runtime/recovery78_prefix_audit_20261029_v1/OBSERVATION_PLAN.json';jobs=read(parent)['jobs']+[dict(role='prepare79_restore_only',**read(D/'LAUNCH.json'))]
assert len(jobs)==19 and all(live(j) for j in jobs)
terminals={'archive78':(P/'ARCHIVE_REVIEW_FINISHED.json','completed'),'frozen33_review':(F/'REVIEW.json','passed'),'comparison29_33':(F/'COMPARISON_FINISHED.json','completed'),'prepare79_restore_only':(D/'FINISHED.json','prepared')}
for m in ['impedance','admittance','vmc']:terminals['parameter78_'+m]=(P/m/'train/FINISHED.json','status')
for name in ['parameter_recovery78_loss_20261029_v1','parameter_recovery78_task_labels_20261029_v1','vmc_recovery78_terminal_followup_20261029_v1','admittance_recovery78_terminal_followup_20261029_v1']:terminals[name]=(B/'runs'/name/'FINISHED.json','completed')
terminals['parameter_recovery76_78_reward_stability_20261029_v1']=(B/'runs/parameter_recovery76_78_reward_stability_20261029_v1/REVIEW.json',None)
for i in range(2):terminals['frozen33_shard'+str(i)]=(F/f'shard{i}/POLICY_UNCHANGED.json',None)
put(D/'OBSERVATION_PLAN.json',dict(time=time.time(),jobs=jobs,parent_plan_sha256=hashlib.sha256(parent.read_bytes()).hexdigest(),max_samples=21,interval_seconds=30,stop_when_full78_and_restore79_complete=True,scientific_restart_on_expiry=False,new_physics=0,new_updates=0))
rows=[];start=time.monotonic()
try:
 with (D/'OBSERVATIONS.jsonl').open('x') as out:
  for i in range(21):
   states=[]
   for j in jobs:
    active=live(j);terminal=None
    if not active:
     assert j['role'] in terminals,(j,'Missing original process')
     p,key=terminals[j['role']];terminal=read(p)
     if key=='status':assert terminal[key]=='stopped_at_complete_cycle'
     elif key is not None:assert terminal[key] is True
    states.append(dict(role=j['role'],pid=j['pid'],live=active,terminal=terminal))
   failures=[P/'ARCHIVE_REVIEW_FAILURE.json',F/'REVIEW_FAILURE.json',F/'COMPARISON_FAILURE.json',G/'FAILURE.json',D/'FAILURE.json']+list(P.glob('*/train/FAILURE.json'))+list(P.glob('*/DRIVER_FAILURE.json'))
   for name in ['parameter_recovery78_loss_20261029_v1','parameter_recovery78_task_labels_20261029_v1','vmc_recovery78_terminal_followup_20261029_v1','admittance_recovery78_terminal_followup_20261029_v1','parameter_recovery76_78_reward_stability_20261029_v1']:failures.extend((B/'runs'/name).glob('*FAILURE.json'))
   for p in failures:assert not p.exists(),str(p)
   g=json.loads((G/'samples.jsonl').read_text().splitlines()[-1]);assert time.time()-g['time']<20
   progress={m:read(P/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']};shards=[]
   for j in read(F/'LAUNCH.json')['jobs']:
    folder=Path(j['output']);assert not (folder/'FAILURE.json').exists();r=read(folder/'RESULTS.json') if (folder/'RESULTS.json').exists() else None
    shards.append(dict(pid=j['pid'],completed=len(r['episodes']) if r else 0))
   row=dict(time=time.time(),states=states,parameter_progress=progress,frozen_shards=shards,guard=g);rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
   print(json.dumps(dict(sample=i,steps={m:v['steps'] for m,v in progress.items()},completed_conditions={m:v['completed_conditions'] for m,v in progress.items()},frozen_completed=sum(v['completed'] for v in shards),gpu=[x['utilization'] for x in g['gpus']])),flush=True)
   ready=(P/'ARCHIVE_REVIEW_FINISHED.json').exists() and (D/'FINISHED.json').exists()
   if ready or i==20:break
   time.sleep(max(0,start+30*(i+1)-time.monotonic()))
 put(D/'OBSERVATION_FINISHED.json',dict(time=time.time(),passed=True,samples=len(rows),elapsed=time.monotonic()-start,original_identities=len(jobs),all_original_live_or_verified_terminal=True,first=rows[0],last=rows[-1],full78_and_restore79_ready=ready,scientific_restart=False))
except BaseException as e:
 put(D/'OBSERVATION_FAILURE.json',dict(time=time.time(),error=repr(e),scientific_restart=False));raise
