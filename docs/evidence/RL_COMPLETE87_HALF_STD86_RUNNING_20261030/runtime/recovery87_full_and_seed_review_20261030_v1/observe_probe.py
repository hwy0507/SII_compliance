from pathlib import Path
import json,time,os
D=Path(__file__).parent;B=D.parents[1];O=B/'runs/parameter86_half_std_paired_20261030_v3'
read=lambda p:json.loads(Path(p).read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def state(j):
 for p in j['failure_paths']:assert not Path(p).exists(),p
 try:
  s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split()
  if s[19]==str(j['proc_start_ticks']) and s[0]!='Z':return 'live'
 except FileNotFoundError:pass
 assert j['terminal_requirements'],j['name']
 for q in j['terminal_requirements']:assert read(q['path'])[q['key']]==q['value']
 return 'verified_terminal'
os.sched_setaffinity(0,{12})
identities=read(D/'PLAN.json')['identities']
for j in read(O/'LAUNCH.json')['jobs']:
 d=O/j['group'];identities.append(dict(name='half_std_'+j['group'],pid=j['pid'],proc_start_ticks=j['start'],failure_paths=[str(d/'FAILURE.json')],terminal_requirements=[dict(path=str(d/'FINISHED.json'),key='passed',value=True)]))
j=read(O/'REVIEW_LAUNCH.json');identities.append(dict(name='half_std_review',pid=j['pid'],proc_start_ticks=j['start'],failure_paths=[str(O/'REVIEW_FAILURE.json')],terminal_requirements=[dict(path=str(O/'FINISHED.json'),key='passed',value=True)]))
put(D/'PROBE_OBSERVATION_PLAN.json',dict(time=time.time(),identities=identities,samples=7,interval_s=30,automatic_training=False))
rows=[];start=time.monotonic()
try:
 with (D/'PROBE_OBSERVATIONS.jsonl').open('x') as f:
  for n in range(7):
   if n:time.sleep(max(0,start+30*n-time.monotonic()))
   states={j['name']:state(j) for j in identities}
   progress={k:read(O/k/'PROGRESS.json') for k in read(O/'PLAN.json')['groups']}
   if rows:
    for k,v in progress.items():assert (v['completed_episodes'],v['actions'])>=(rows[-1]['progress'][k]['completed_episodes'],rows[-1]['progress'][k]['actions'])
   gpu=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-gpu['time']<20
   row=dict(time=time.time(),elapsed_s=time.monotonic()-start,states=states,progress=progress,gpu=gpu);rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
 assert [json.loads(l) for l in (D/'PROBE_OBSERVATIONS.jsonl').read_text().splitlines()]==rows
 put(D/'PROBE_OBSERVATION_FINISHED.json',dict(passed=True,time=time.time(),samples=len(rows),identities=len(identities),elapsed_s=rows[-1]['elapsed_s'],saved_rows_read_back=True,initial_progress=rows[0]['progress'],final_progress=rows[-1]['progress'],automatic_training=False))
 print('PROBE OBSERVATION PASSED')
except BaseException as e:put(D/'PROBE_OBSERVATION_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
