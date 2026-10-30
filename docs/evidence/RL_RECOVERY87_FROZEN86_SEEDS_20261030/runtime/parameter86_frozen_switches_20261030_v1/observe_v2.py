from pathlib import Path
import json,time,os
R=Path(__file__).parent;B=R.parents[1];O=B/'runs'/R.name
read=lambda p:json.loads(Path(p).read_text())
def write(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
os.sched_setaffinity(0,{12})
identities=read(B/'runtime/recovery86_full_review_20261030_v1/OBSERVATION87_PLAN.json')['identities']
launch=read(O/'LAUNCH.json')
for j in launch['jobs']:
 d=O/j['group'];identities.append(dict(name=j['group'],pid=j['pid'],proc_start_ticks=j['start'],terminal_requirements=[dict(path=str(d/'FINISHED.json'),key='passed',value=True)],failure_paths=[str(d/'FAILURE.json')]))
j=read(O/'REVIEW_LAUNCH.json');identities.append(dict(name='frozen86_review',pid=j['pid'],proc_start_ticks=j['start'],terminal_requirements=[dict(path=str(O/'FINISHED.json'),key='passed',value=True)],failure_paths=[str(O/'REVIEW_FAILURE.json')]))
def state(j):
 for p in j['failure_paths']:assert not Path(p).exists(),p
 try:
  s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split()
  if s[19]==str(j['proc_start_ticks']) and s[0]!='Z':return 'live'
 except FileNotFoundError:pass
 assert j['terminal_requirements'],j['name']
 for q in j['terminal_requirements']:assert read(q['path'])[q['key']]==q['value']
 return 'verified_terminal'
write(O/'OBSERVATION_V2_PLAN.json',dict(time=time.time(),identities=identities,samples=7,interval_s=30,automatic_training=False))
start=time.monotonic();rows=[]
try:
 with (O/'OBSERVATIONS_V2.jsonl').open('x') as f:
  for n in range(7):
   if n:time.sleep(max(0,start+30*n-time.monotonic()))
   states={j['name']:state(j) for j in identities}
   progress={m:read(B/f'runs/parameter_partial75_recovery_cycle87_20261029_v1/{m}/train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
   if rows:
    for m in progress:assert progress[m]['steps']>=rows[-1]['progress87'][m]['steps']
   frozen86={k:{p.stem:read(O/k/p) for p in [Path('STARTUP_REVIEW.json'),Path('EVALUATION.json'),Path('CURRENT_PHYSICS.json'),Path('PROGRESS.json')] if (O/k/p).exists()} for k in read(O/'PLAN.json')['groups']}
   frozen82={}
   for m in ['impedance','admittance','vmc']:
    d=B/f'runs/parameter82_frozen_full30_20261030_v1/{m}';p=d/('FINISHED.json' if (d/'FINISHED.json').exists() else 'PROGRESS.json');frozen82[m]=dict(path=str(p),data=read(p))
   g=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-g['time']<20
   row=dict(time=time.time(),elapsed=time.monotonic()-start,states=states,progress87=progress,frozen86=frozen86,frozen82=frozen82,gpu=g);rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
 assert [json.loads(l) for l in (O/'OBSERVATIONS_V2.jsonl').read_text().splitlines()]==rows
 for group,v in rows[-1]['frozen86'].items():
  assert v['STARTUP_REVIEW']['passed'] and v['EVALUATION']['optimizer_updates']==0
  assert v['PROGRESS']['actions']>=100
  pid=v['CURRENT_PHYSICS']['pid'];assert Path(f'/proc/{pid}').exists()
 write(O/'OBSERVATION_V2_FINISHED.json',dict(passed=True,time=time.time(),samples=len(rows),identities=len(identities),elapsed_s=rows[-1]['elapsed'],actual_frozen86_actions={k:v['PROGRESS']['actions'] for k,v in rows[-1]['frozen86'].items()},steps87={k:v['steps'] for k,v in rows[-1]['progress87'].items()},saved_rows_read_back=True,automatic_training=False))
 print('OBSERVATION PASSED')
except BaseException as e:write(O/'OBSERVATION_V2_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
