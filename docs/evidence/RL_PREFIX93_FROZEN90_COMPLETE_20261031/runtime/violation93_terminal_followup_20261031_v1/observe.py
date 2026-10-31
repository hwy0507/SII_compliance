from pathlib import Path
import hashlib,json,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_violation_cycle93_20261031_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';O=B/'runs/violation93_fixed92_terminal_followup_20261031_v1';P=B/'runtime/violation90_frozen_postprocess_20261030_v1'
read=lambda p:json.loads(Path(p).read_text())
def identity(pid):
 s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z';return dict(pid=pid,start=s[19])
def live(j):
 p=Path('/proc',str(j['pid']),'stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[0]!='Z' and s[19]==str(j.get('start',j.get('proc_start_ticks')))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
try:
 plan=read(D/'OBSERVATION_PLAN.json');assert sha(__file__)==plan['script_sha256']
 jobs=read(R/'LAUNCH.json')['jobs'];ids=jobs+[read(R/'MONITOR_LAUNCH.json'),read(O/'PROCESS.json')]
 for j in jobs:
  children=list(map(int,Path('/proc',str(j['pid']),'task',str(j['pid']),'children').read_text().split()));assert len(children)==30;ids.extend(identity(pid) for pid in children)
 for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]:ids.append(dict(pid=pid,start=start))
 ids=[dict(pid=j['pid'],start=str(j.get('start',j.get('proc_start_ticks')))) for j in ids]
 dynamic=[dict(job=j,finished=str(F/j['controller']/'FINISHED.json'),kind='evaluator',method=j['controller']) for j in read(F/'LAUNCH.json')['jobs']]+[dict(job=read(F/'REVIEW_LAUNCH.json'),finished=str(F/'REVIEW.json'),kind='collector'),dict(job=read(P/'PROCESS.json'),finished=str(P/'FINISHED.json'),kind='postprocessor')]
 start=time.monotonic();rows=[]
 with (D/'OBSERVATIONS.jsonl').open('x') as out:
  while True:
   for j in ids:assert live(j),j
   completed=[];dynamic_live=[]
   for item in dynamic:
    j=item['job']
    if live(j):dynamic_live.append(j['pid'])
    else:
     receipt=Path(item['finished']);record=read(receipt);assert record['passed']
     if item['kind']=='evaluator':assert record['episodes']==30 and record['full_learner_state_unchanged'] and record['full_replay_state_unchanged'] and record['initial_learner_digest']==record['final_learner_digest'] and record['new_optimizer_updates']==0
     completed.append(dict(kind=item['kind'],pid=j['pid'],path=str(receipt),sha256=sha(receipt)))
   assert not (R/'ARCHIVE_REVIEW_FAILURE.json').exists() and not list(O.glob('WAIT_FAILURE_*.json')) and not (F/'REVIEW_FAILURE.json').exists() and not list(P.glob('FAILURE*'))
   steps={};frozen={}
   for m in ['impedance','admittance','vmc']:
    assert not (R/m/'DRIVER_FAILURE.json').exists() and not (R/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
    steps[m]=read(R/m/'train/PROGRESS.json')['steps'];frozen[m]=30 if (F/m/'FINISHED.json').exists() else read(F/m/'PROGRESS.json')['completed_conditions']
   row=dict(time=time.time(),elapsed_s=time.monotonic()-start,steps=steps,frozen=frozen,permanent_identity_count=len(ids),dynamic_live=dynamic_live,completed=completed);rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
   if time.monotonic()-start>=plan['duration_seconds']:break
   time.sleep(plan['interval_seconds'])
 assert all(rows[-1]['steps'][m]>rows[0]['steps'][m] for m in steps)
 with (D/'OBSERVATION_REVIEW.json').open('x') as out:json.dump(dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,samples=len(rows),identities=ids,dynamic=dynamic,first=rows[0],last=rows[-1]),out,indent=2);out.write('\n')
 print('Original training/archive/waiter/samplers/guard identities held; frozen terminal transitions verified; all3 learning streams progressed')
except BaseException as e:
 with (D/'OBSERVATION_FAILURE.json').open('x') as out:json.dump(dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()),out,indent=2)
 raise
