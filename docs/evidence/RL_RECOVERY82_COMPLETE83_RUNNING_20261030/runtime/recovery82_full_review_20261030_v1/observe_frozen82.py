from pathlib import Path
import json,time,os,hashlib
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;O=B/'runs/parameter82_frozen_full30_20261030_v1';os.sched_setaffinity(0,{3})
def read(p):return json.loads(p.read_text())
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==str(j.get('proc_start_ticks',j.get('start'))) and s[0]!='Z'
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
refs=[O/'LAUNCH.json',O/'REVIEW_LAUNCH.json',O/'comparison55_82/LAUNCH.json',B/'runs/parameter_partial75_recovery_cycle83_20261029_v1/LAUNCH.json',B/'runs/parameter_recovery82_84_reward_stability_20261030_v1/LAUNCH.json',B/'runs/recovery82_84_bootstrap_scalar_review_20261030_v1/LAUNCH.json']
jobs=[]
for p in refs:
 r=read(p);jobs.extend(r['jobs'] if 'jobs' in r else [r])
jobs.append(dict(pid=97370,proc_start_ticks='570509460'))
put(D/'FROZEN82_OBSERVATION_PLAN.json',dict(time=time.time(),samples=4,interval_s=20,jobs=jobs,refs=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in refs]))
rows=[];start=time.monotonic()
for n in range(4):
 if n:time.sleep(max(0,start+20*n-time.monotonic()))
 assert all(live(j) for j in jobs)
 progress={}
 for m in ['impedance','admittance','vmc']:
  assert read(O/m/'STARTUP_REVIEW.json')['passed'] and not (O/m/'FAILURE.json').exists()
  progress[m]=read(O/m/'PROGRESS.json');cpu=read(O/m/'REGISTRATION.json')['cpu']
  assert os.sched_getaffinity(progress[m]['physics_pid'])=={cpu}
  assert os.sched_getaffinity(next(j['pid'] for j in read(O/'LAUNCH.json')['jobs'] if j['controller']==m))=={cpu}
  if rows:assert (progress[m]['completed_conditions'],progress[m]['actions'])>=(rows[-1]['progress'][m]['completed_conditions'],rows[-1]['progress'][m]['actions'])
 g=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-g['time']<20
 rows.append(dict(time=time.time(),elapsed=time.monotonic()-start,progress=progress,identities_live=True,gpu=g))
 with (D/'FROZEN82_OBSERVATIONS.jsonl').open('a') as f:f.write(json.dumps(rows[-1])+'\n')
assert [json.loads(l) for l in (D/'FROZEN82_OBSERVATIONS.jsonl').read_text().splitlines()]==rows
assert all(rows[-1]['progress'][m]['actions']>rows[0]['progress'][m]['actions'] or rows[-1]['progress'][m]['completed_conditions']>rows[0]['progress'][m]['completed_conditions'] for m in progress)
put(D/'FROZEN82_OBSERVATION_FINISHED.json',dict(passed=True,time=time.time(),samples=4,elapsed=rows[-1]['elapsed'],all_identities_verified=True,actual_cpu_affinity_verified=True,all_saved_rows_read_back=True,finite_evaluation_ongoing=True,full90_results_pending=True,final_state_invariance_pending=True))
print('Frozen82 actual running observation passed', {m:r['actions'] for m,r in progress.items()})
