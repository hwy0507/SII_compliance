from pathlib import Path
import json,time,os
os.sched_setaffinity(0,{54})
D=Path(__file__).parent;B=D.parents[1]
read=lambda p:json.loads(Path(p).read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
old=read(B/'runtime/recovery85_full_review_20261030_v1/OBSERVATION_PLAN.json');identities=old['identities'];prep=B/'runtime/prepare_recovery87_20261030_v1';j=read(prep/'LAUNCH.json')
identities.append(dict(name='restore87_only',pid=j['pid'],proc_start_ticks=j['proc_start_ticks'],terminal_requirements=[dict(path=str(prep/'FINISHED.json'),key='prepared',value=True)],failure_paths=[str(prep/'FAILURE.json')]))
def state(j):
 for p in j['failure_paths']:assert not Path(p).exists(),p
 p=Path(f'/proc/{j["pid"]}/stat')
 if p.exists():
  s=p.read_text().rsplit(')',1)[1].split()
  if s[19]==j['proc_start_ticks'] and s[0]!='Z':return 'live'
 assert j['terminal_requirements'],j['name']
 for r in j['terminal_requirements']:assert read(r['path'])[r['key']]==r['value']
 return 'verified_terminal'
put(D/'PLAN.json',dict(time=time.time(),identities=identities,samples=11,interval_seconds=30,automatic_training=False))
rows=[];start=time.monotonic()
try:
 with (D/'OBSERVATIONS.jsonl').open('x') as f:
  for i in range(11):
   if i:time.sleep(max(0,start+30*i-time.monotonic()))
   states={j['name']:state(j) for j in identities}
   progress={m:read(B/f'runs/parameter_partial75_recovery_cycle86_20261029_v1/{m}/train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
   if rows:
    for m in progress:assert progress[m]['steps']>=rows[-1]['progress'][m]['steps']
   g=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-g['time']<20
   row=dict(time=time.time(),elapsed=time.monotonic()-start,states=states,progress=progress,gpu=g);rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
 assert [json.loads(l) for l in (D/'OBSERVATIONS.jsonl').read_text().splitlines()]==rows
 put(D/'FINISHED.json',dict(passed=True,time=time.time(),samples=len(rows),identities=len(identities),elapsed_s=rows[-1]['elapsed'],saved_rows_exact=True,automatic_training=False));print('Observation passed',len(identities))
except BaseException as e:put(D/'FAILURE.json',dict(time=time.time(),error=repr(e)));raise
