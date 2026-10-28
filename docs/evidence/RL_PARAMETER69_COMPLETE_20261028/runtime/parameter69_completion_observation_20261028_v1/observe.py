from pathlib import Path
import json,time,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).resolve().parent
os.sched_setaffinity(0,{53});run=B/'runs/parameter_capacity_pool30_cycle69_20261026_v1';start=time.time()
launch=json.loads((run/'LAUNCH.json').read_text());jobs=launch['jobs']
checks={'archive':run/'ARCHIVE_REVIEW_FINISHED.json','loss':B/'runs/parameter69_loss_20261028_v1/FINISHED.json','labels':B/'runs/parameter_task_label_audit69_20261028_v1/FINISHED69.json','vmc_terminal':B/'runs/vmc69_terminal_anchor_followup_20261028_v1/FINISHED.json','admittance_terminal':B/'runs/admittance69_terminal_anchor_followup_20261028_v1/FINISHED.json','restore70':B/'runtime/prepare_parameter70_20261028_v1/parameter_FINISHED.json'}
def live(pid,start=None):
 p=Path(f'/proc/{pid}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[0]!='Z' and (start is None or s[19]==str(start))
for index in range(61):
 row=dict(index=index,time=time.time(),methods={},ready={k:p.exists() for k,p in checks.items()})
 for j in jobs:
  p=run/j['controller']/'train';r=dict(progress=json.loads((p/'PROGRESS.json').read_text()),live=live(j['pid'],j['proc_start_ticks']),finished=(p/'FINISHED.json').exists(),failure=(p/'FAILURE.json').exists());row['methods'][j['controller']]=r
 guard=Path('/tmp/sii_gpu_util_guard_20261028_v5');row['gpu']=json.loads((guard/'samples.jsonl').read_text().splitlines()[-1]);row['guard_live']=all(live(p) for p in range(3256866,3256871))
 failures=[p for p in [run/'ARCHIVE_REVIEW_FAILURE.json',guard/'FAILURE.json',B/'runs/parameter69_loss_20261028_v1/FAILURE.json',B/'runs/vmc69_terminal_anchor_followup_20261028_v1/WAIT_FAILURE.json',B/'runs/admittance69_terminal_anchor_followup_20261028_v1/WAIT_FAILURE.json',B/'runtime/prepare_parameter70_20261028_v1/parameter_FAILURE.json'] if p.exists()];row['failures']=[str(p) for p in failures]
 with (OUT/'samples.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 print(json.dumps(dict(index=index,utc=time.strftime('%H:%M:%S',time.gmtime(row['time'])),steps={m:r['progress']['steps'] for m,r in row['methods'].items()},completed={m:r['progress']['completed_conditions'] for m,r in row['methods'].items()},finished={m:r['finished'] for m,r in row['methods'].items()},ready=row['ready'],failures=row['failures'],guard_live=row['guard_live'],gpu=[g['utilization'] for g in row['gpu']['gpus']])),flush=True)
 assert not failures and row['guard_live'] and not any(r['failure'] for r in row['methods'].values())
 assert all(r['live'] or r['finished'] for r in row['methods'].values()),'Learner disappeared without completion'
 if all(row['ready'].values()):break
 if index<60:time.sleep(30)
(OUT/'OBSERVATION_FINISHED.json').write_text(json.dumps(dict(time=time.time(),samples=index+1,all_ready=all(row['ready'].values()),observer_only=True))+'\n')
