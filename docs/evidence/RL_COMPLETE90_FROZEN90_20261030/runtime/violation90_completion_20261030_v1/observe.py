from pathlib import Path
import json,time,os,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];T=B/'runs/parameter_violation_cycle90_20261030_v1';O=B/'runs/parameter_violation_cycle90_review_20261030_v1';F=B/'runs/violation90_fixed87_terminal_followup_20261030_v1'
os.sched_setaffinity(0,{3})
def read(p):return json.loads(p.read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
identities={1096445:'576484307',1096447:'576484307',1096449:'576484307',1096452:'576484307',2283008:'576631374',97370:'570509460',97399:'570509475',97400:'570509475',97401:'570509475',97402:'570509475'}
completed={1096445:T/'impedance/train/FINISHED.json',1096447:T/'admittance/train/FINISHED.json',1096449:T/'vmc/train/FINISHED.json',1096452:O/'FINISHED.json',2283008:F/'FINISHED.json'}
start=time.time();put(D/'OBSERVATION_PLAN.json',dict(time=start,seconds=1800,identities=identities,only_original_processes=True,restarts=False,new_training=False))
try:
 with (D/'OBSERVATIONS.jsonl').open('x',buffering=1) as log:
  while True:
   states={}
   for pid,expected in identities.items():
    p=Path(f'/proc/{pid}/stat');s=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
    if s and s[0]!='Z':assert s[19]==expected;states[pid]=s[0]
    else:
     assert pid in completed and completed[pid].exists(),f'Original{pid} missing without FINISHED'
     done=read(completed[pid]);assert done.get('passed',done.get('completed',done.get('status')=='stopped_at_complete_cycle'));states[pid]='finished'
   assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not list(F.glob('WAIT_FAILURE*'))
   progress={m:read(T/m/'train/PROGRESS.json') for m in ('impedance','admittance','vmc')}
   for m in progress:assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists()
   guard=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (guard/'STOP').exists() and not (guard/'FAILURE.json').exists()
   gpu=json.loads((guard/'samples.jsonl').read_text().splitlines()[-1]);assert time.time()-gpu['time']<25
   v=dict(time=time.time(),states=states,progress=progress,gpu=gpu,full_review=(O/'FINISHED.json').exists(),fixed_followup=(F/'FINISHED.json').exists());log.write(json.dumps(v)+'\n')
   print(json.dumps(dict(time=v['time'],states=states,steps={m:x['steps'] for m,x in progress.items()},completed={m:x['completed_conditions'] for m,x in progress.items()},gpu=[x['utilization'] for x in gpu['gpus']],full_review=v['full_review'],fixed_followup=v['fixed_followup'])),flush=True)
   if v['full_review'] and v['fixed_followup']:
    put(D/'OBSERVATION_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.time()-start,complete90_review_and_followup=True,original_identities=identities));break
   if time.time()-start>=1800:
    put(D/'OBSERVATION_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.time()-start,complete90_review_and_followup=False,observation_only_expired=True,original_identities=identities));break
   time.sleep(45)
except BaseException as exc:
 put(D/'OBSERVATION_FAILURE.json',dict(time=time.time(),error=repr(exc),traceback=traceback.format_exc()));raise
