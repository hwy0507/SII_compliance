from pathlib import Path
import json,time,os
D=Path(__file__).parent;B=D.parents[1];R=B/'runs/parameter_partial75_recovery_cycle87_20261029_v1';os.sched_setaffinity(0,{54});read=lambda p:json.loads(Path(p).read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
assert read(R/'startup/REVIEW.json')['passed'];assert read(B/'runtime/recovery87_followups_20261030_v1/FINISHED.json')['passed']
jobs={j['controller']:j for j in read(R/'LAUNCH.json')['jobs']};paths={'archive86':R/'MONITOR_LAUNCH.json','loss86':B/'runs/parameter_recovery87_loss_20261029_v1/LAUNCH.json','labels86':B/'runs/parameter_recovery87_task_labels_20261029_v1/LAUNCH.json','vmc_terminal86':B/'runs/vmc_recovery87_terminal_followup_20261029_v1/LAUNCH.json','admittance_terminal86':B/'runs/admittance_recovery87_terminal_followup_20261029_v1/LAUNCH.json'}
def advance(x):
 if isinstance(x,str):return x.replace('cycle86_','cycle87_').replace('recovery86_','recovery87_').replace('COMPLETE85_86','COMPLETE86_87')
 if isinstance(x,list):return [advance(a) for a in x]
 if isinstance(x,dict):return {k:advance(v) for k,v in x.items()}
 return x
identities=[]
for item in read(D/'WATCH_PLAN.json')['identities']:
 name=item['name']
 if name in jobs or name in paths:
  j=jobs[name] if name in jobs else read(paths[name]);item=advance(item);item.update(name=name.replace('86','87'),pid=j['pid'],proc_start_ticks=j['proc_start_ticks'])
 identities.append(item)
def state(j):
 for p in j['failure_paths']:assert not Path(p).exists(),p
 p=Path(f'/proc/{j["pid"]}/stat')
 if p.exists():
  s=p.read_text().rsplit(')',1)[1].split()
  if s[19]==str(j['proc_start_ticks']) and s[0]!='Z':return 'live'
 assert j['terminal_requirements'],j['name']
 for r in j['terminal_requirements']:assert read(r['path'])[r['key']]==r['value']
 return 'verified_terminal'
put(D/'OBSERVATION87_PLAN.json',dict(time=time.time(),identities=identities,samples=7,interval_s=20,automatic_training=False));start=time.monotonic();rows=[]
try:
 with (D/'OBSERVATIONS87.jsonl').open('x') as f:
  for n in range(7):
   if n:time.sleep(max(0,start+20*n-time.monotonic()))
   states={j['name']:state(j) for j in identities};progress={m:read(R/m/'train/PROGRESS.json') for m in jobs}
   for m in progress:
    assert states[m]=='live'
    if rows:assert progress[m]['steps']>=rows[-1]['progress'][m]['steps']
   g=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-g['time']<20
   row=dict(time=time.time(),elapsed=time.monotonic()-start,states=states,progress=progress,gpu=g);rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
 assert [json.loads(l) for l in (D/'OBSERVATIONS87.jsonl').read_text().splitlines()]==rows
 put(D/'OBSERVATION87_FINISHED.json',dict(passed=True,time=time.time(),samples=len(rows),identities=len(identities),elapsed_s=rows[-1]['elapsed'],saved_rows_read_back=True,automatic_training=False));print({m:v['steps'] for m,v in rows[-1]['progress'].items()})
except BaseException as e:put(D/'OBSERVATION87_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
