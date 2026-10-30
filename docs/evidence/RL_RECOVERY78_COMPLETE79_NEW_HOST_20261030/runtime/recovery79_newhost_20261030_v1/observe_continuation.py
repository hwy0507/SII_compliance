from pathlib import Path
import json,time,os,socket,hashlib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;P=B/'runs/parameter_partial75_recovery_cycle79_20261029_v1';O=B/'runs/serl_take33_frozen_remaining2_20261030_v2';G=Path('/tmp/sii_gpu_util_guard_20261030_v7')
os.sched_setaffinity(0,{7})
def read(p):return json.loads(p.read_text())
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j.get('start',j.get('proc_start_ticks')) and s[0]!='Z'
def put(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2)+'\n')
jobs=[]
for j in read(P/'LAUNCH.json')['jobs']:jobs.append((j,P/j['controller']/'train/FINISHED.json',P/j['controller']/'train/FAILURE.json'))
for j in read(O/'LAUNCH.json')['jobs']:jobs.append((j,Path(j['output'])/'POLICY_UNCHANGED.json',Path(j['output'])/'FAILURE.json'))
for launch,finished,failed in [('REPLAY_LAUNCH.json','saved28_replay/CHECK_ONLY_REVIEW.json','saved28_replay/FAILURE.json'),('COMBINED_REVIEW_LAUNCH.json','REVIEW.json','COMBINED_REVIEW_FAILURE.json'),('COMPARISON_LAUNCH.json','COMPARISON_FINISHED.json','COMPARISON_FAILURE.json')]:jobs.append((read(O/launch),O/finished,O/failed))
put(D/'CONTINUATION_OBSERVATION_PLAN.json',dict(time=time.time(),jobs=[dict(identity=j,terminal=str(t),failure=str(f)) for j,t,f in jobs],samples=5,interval_s=30,new_physics=0,new_updates=0))
start=time.monotonic();rows=[]
try:
 for i in range(5):
  row=dict(time=time.time(),host=socket.gethostname(),identities=[],parameter={},direct={})
  for j,t,f in jobs:
   assert not f.exists(),str(f)
   status='live' if live(j) else ('terminal_receipt' if t.exists() else 'missing');assert status!='missing',str(j)
   row['identities'].append(dict(pid=j['pid'],start=j.get('start',j.get('proc_start_ticks')),status=status,terminal=str(t)))
  for m in ['impedance','admittance','vmc']:row['parameter'][m]=read(P/m/'train/PROGRESS.json')
  for j in read(O/'LAUNCH.json')['jobs']:
   p=Path(j['output']);row['direct'][p.name]={f.parent.name:read(f) for f in p.glob('*/rollout.progress.json')}
  g=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];assert time.time()-g[-1]['time']<20;row['guard']=g[-1]
  rows.append(row)
  with (D/'CONTINUATION_OBSERVATIONS.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  if i<4:time.sleep(30)
 for m in ['impedance','admittance','vmc']:assert all(a['parameter'][m]['steps']<=z['parameter'][m]['steps'] for a,z in zip(rows,rows[1:]))
 put(D/'CONTINUATION_OBSERVATION_FINISHED.json',dict(passed=True,time=time.time(),samples=len(rows),elapsed=time.monotonic()-start,identities=len(jobs),first_steps={m:rows[0]['parameter'][m]['steps'] for m in rows[0]['parameter']},last_steps={m:rows[-1]['parameter'][m]['steps'] for m in rows[-1]['parameter']},original_identities_live_or_verified_terminal=True,scientific_restart=False))
except BaseException as e:put(D/'CONTINUATION_OBSERVATION_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
