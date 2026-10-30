from pathlib import Path
import json,time,subprocess,sys,os,hashlib
D=Path(__file__).parent;B=D.parents[1];O=B/'runs/parameter86_half_std_paired_20261030_v3';read=lambda p:json.loads(p.read_text())
os.sched_setaffinity(0,{12})
plan=read(O/'PLAN.json');launch=read(O/'LAUNCH.json');review=read(O/'REVIEW_LAUNCH.json');deadline=launch['time']+plan['wall_dispatch_deadline_seconds']
rows=[]
def identity(j):
 s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==str(j['start']) and s[0]!='Z';return s[0]
try:
 with (D/'WAIT_OBSERVATIONS.jsonl').open('x') as f:
  while True:
   states={}
   for j in launch['jobs']:
    d=O/j['group'];assert not (d/'FAILURE.json').exists()
    if (d/'FINISHED.json').exists():assert read(d/'FINISHED.json')['passed'];states[j['group']]='verified_terminal'
    else:states[j['group']]=identity(j)
   assert not (O/'REVIEW_FAILURE.json').exists()
   done=(O/'FINISHED.json').exists()
   if done:assert read(O/'FINISHED.json')['passed'];states['review']='verified_terminal'
   else:states['review']=identity(review)
   gpu=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-gpu['time']<20
   row=dict(time=time.time(),states=states,progress={k:read(O/k/'PROGRESS.json') for k in plan['groups']},gpu=gpu);rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
   if done:break
   assert time.time()<deadline,'Original finite review deadline reached; no restart'
   time.sleep(30)
 assert [json.loads(l) for l in (D/'WAIT_OBSERVATIONS.jsonl').read_text().splitlines()]==rows
 assert not (D/'HALF_STD_RAW_REVIEW.json').exists()
 subprocess.run([sys.executable,str(D/'audit_half_std_raw.py')],check=True)
 (D/'WAIT_FINISHED.json').write_text(json.dumps(dict(passed=True,time=time.time(),samples=len(rows),original_review_finished=True,independent_raw_audit_passed=read(D/'HALF_STD_RAW_SAVED_REVIEW.json')['passed'],no_physics_restarted=True),indent=2)+'\n')
 print('Original16 complete and independent raw audit passed',flush=True)
except BaseException as e:
 (D/'WAIT_FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)),indent=2)+'\n');raise
