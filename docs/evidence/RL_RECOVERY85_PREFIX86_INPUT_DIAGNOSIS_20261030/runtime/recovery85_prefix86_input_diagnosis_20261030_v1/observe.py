from pathlib import Path
import json,time,os
os.sched_setaffinity(0,{54});D=Path(__file__).parent;B=D.parents[1]
def read(p):return json.loads(Path(p).read_text())
def put(p,r):
 with p.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
plan=read(D/'OBSERVATION_PLAN.json');start=time.monotonic();rows=[]
try:
 with (D/'OBSERVATIONS.jsonl').open('x') as f:
  for n in range(plan['samples']):
   if n:time.sleep(max(0,start+plan['interval_seconds']*n-time.monotonic()))
   states={}
   for j in plan['identities']:
    for p in j['failure_paths']:assert not Path(p).exists(),p
    p=Path(f'/proc/{j["pid"]}/stat');live=False
    if p.exists():
     s=p.read_text().rsplit(')',1)[1].split();live=s[19]==j['proc_start_ticks'] and s[0]!='Z'
    if live:states[j['name']]='live'
    else:
     assert j['terminal_requirements'],j['name']
     for r in j['terminal_requirements']:assert read(r['path'])[r['key']]==r['value']
     states[j['name']]='verified_terminal'
   progress={m:read(B/f'runs/parameter_partial75_recovery_cycle85_20261029_v1/{m}/train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
   for m,x in progress.items():
    assert states[m]=='live'
    if rows:assert x['steps']>=rows[-1]['progress'][m]['steps']
   gpu=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-gpu['time']<20
   row=dict(time=time.time(),elapsed=time.monotonic()-start,states=states,progress=progress,gpu=gpu);rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
 assert [json.loads(l) for l in (D/'OBSERVATIONS.jsonl').read_text().splitlines()]==rows
 put(D/'OBSERVATION_FINISHED.json',dict(passed=True,time=time.time(),samples=len(rows),elapsed=rows[-1]['elapsed'],all26_identities_live_or_verified_terminal=True,all_saved_rows_read_back=True,new_physics=0,optimizer_updates=0))
 print(json.dumps(dict(passed=True,steps={m:x['steps'] for m,x in rows[-1]['progress'].items()})))
except BaseException as e:put(D/'OBSERVATION_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
