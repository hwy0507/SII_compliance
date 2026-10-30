from pathlib import Path
import json,time,os,traceback,hashlib
D=Path(__file__).parent;os.sched_setaffinity(0,{54})
def read(p):return json.loads(Path(p).read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
try:
 plan=read(D/'PLAN.json');start=time.monotonic();rows=[]
 with (D/'OBSERVATIONS.jsonl').open('x') as log:
  while True:
   states={}
   for item in plan['identities']:
    for p in item['failure_paths']:assert not Path(p).exists(),p
    if live(item):states[item['name']]='live'
    else:
     assert item['terminal_requirements'],item['name']+' original identity missing'
     for spec in item['terminal_requirements']:assert read(spec['path'])[spec['key']]==spec['value'],item['name']
     states[item['name']]='verified_terminal'
   progress={m:read(Path(plan['run'])/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
   if rows:
    for m,p in progress.items():assert p['steps']>=rows[-1]['progress'][m]['steps']
   g=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-g['time']<20
   row=dict(time=time.time(),elapsed=time.monotonic()-start,states=states,progress=progress,gpu=g);rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
   if all(states[n]=='verified_terminal' for n in plan['completion_names']):break
   assert time.monotonic()-start<3600,'Finite completion observation expired; inspect original handles, no restart'
   time.sleep(30)
 saved=[json.loads(l) for l in (D/'OBSERVATIONS.jsonl').read_text().splitlines()];assert saved==rows
 put(D/'FINISHED.json',dict(passed=True,time=time.time(),elapsed=rows[-1]['elapsed'],samples=len(rows),all_original_live_or_verified_terminal=True,all_saved_rows_read_back=True,automatic_training=False,new_physics=0,optimizer_updates=0))
except BaseException as e:put(D/'FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
