"""Post-main diagnostic: only target entropy changes; matched 60k controls."""
from datetime import datetime, timezone
import hashlib,json,os,signal,subprocess,time
from pathlib import Path
STUDY=Path('/home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001')
OUT=STUDY/'entropy_diagnostic_02'
SRC=STUDY/'frozen_main_01/code/mujoco_6d_vmc_benchmark'
PY='/home/arm1/vmc_mujoco_runtime/reward_study_20260930/venv_gpu/bin/python'
TRAIN=SRC/'experiments/simba_reward_20260930/train.py'
EVAL=SRC/'experiments/simba_behavior_20261001/evaluate_shared.py'
MANIFEST=SRC/'experiments/simba_behavior_20261001/final_manifest.json'
CUTOFF=datetime.fromisoformat('2026-10-01T12:45:00+00:00').timestamp()
DEADLINE=datetime.fromisoformat('2026-10-01T13:41:00+00:00').timestamp()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj):
 p=OUT/name;q=p.with_suffix(p.suffix+'.tmp')
 q.write_text(json.dumps(obj,indent=2)+'\n');q.replace(p)
def pool(tasks,phase):
 pending=list(tasks);running=[];done=[];slots=['5,6','7,8','15,16','17,18']
 while pending or running:
  for r in list(running):
   rc=r['proc'].poll()
   if rc is not None:
    r['log'].close();slots.append(r['cpu']);running.remove(r)
    done.append(dict(id=r['id'],returncode=rc,command=r['command'],elapsed_s=time.time()-r['start']))
  while pending and slots:
   item=pending.pop(0);cpu=slots.pop(0)
   log=(OUT/'logs'/(item['id']+'.log')).open('w')
   env=dict(os.environ,STUDY_CANONICAL_ROOT=str(SRC),STUDY_DENSE_PROGRESS='1')
   proc=subprocess.Popen(['taskset','-c',cpu]+item['command'],env=env,stdout=log,stderr=subprocess.STDOUT)
   running.append(dict(**item,proc=proc,cpu=cpu,log=log,start=time.time(),stop_sent=False))
  if phase=='training' and time.time()>=CUTOFF:
   for r in running:
    if not r['stop_sent']:
     r['proc'].send_signal(signal.SIGUSR1);r['stop_sent']=True
  write('STATE.json',dict(phase=phase,updated_utc=time.time(),running=[
   dict(id=r['id'],pid=r['proc'].pid,cpu=r['cpu'],stop_sent=r['stop_sent']) for r in running],
   pending=[r['id'] for r in pending],completed=done))
  if pending or running:time.sleep(15)
 write(phase.upper()+'_STATUS.json',done)
 if any(x['returncode']!=0 for x in done):raise RuntimeError(phase+' failed; evidence preserved')
 return done
def main():
 OUT.mkdir(exist_ok=False);(OUT/'logs').mkdir()
 specs=[dict(reward=r,seed=s,id=r+'_seed'+str(s)) for s in (61001,61002) for r in ('office_task','metric')]
 write('PROTOCOL.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),
  classification='post-main exploratory training diagnostic; evaluation fixtures already observed; not independent confirmation',
  changed_factor='target_entropy_per_dimension: -0.5 -> -2.0',
  source=str(SRC),source_commit='e71a512e6fe01eb4e0456c3dfb7d6c6b88afcb54',
  driver_sha256=sha(Path(__file__)),train_sha256=sha(TRAIN),eval_sha256=sha(EVAL),
  manifest_sha256=sha(MANIFEST),training_steps=60000,lr_schedule_budget=100000,
  gamma=.9995,initial_temperature=.01,warmup_std=.02,warmup_steps=5000,utd=2,
  control_source=str(STUDY/'campaign_01'),control_steps='same common periodic step, at most60000',
  train_cutoff_utc=CUTOFF,deadline_utc=DEADLINE,selection='largest common periodic checkpoint of all new and existing paired runs; no test selection',
  specs=specs))
 tasks=[]
 for s in specs:
  tasks.append(dict(id='train_'+s['id'],command=[PY,str(TRAIN),'--output',str(OUT/s['id']),
   '--reward',s['reward'],'--seed',str(s['seed']),'--steps','100000','--stop-after-step','60000',
   '--wall-seconds','5000','--checkpoint-every','10000','--gamma','.9995','--warmup-std','.02',
   '--entropy-coef','-2','--terminal-objective','task_physical','--initial-temperature','.01']))
 pool(tasks,'training')
 steps=[]
 for base in (OUT,STUDY/'campaign_01'):
  for s in specs:
   steps.append({int(p.name.rsplit('_',1)[1]) for p in (base/s['id']).glob('checkpoint_step_*') if int(p.name.rsplit('_',1)[1])<=60000})
 common=set.intersection(*steps)
 if not common:raise RuntimeError('no common periodic checkpoint; do not compare unequal budgets')
 step=max(common);write('COMMON_BUDGET.json',dict(step=step))
 (OUT/'evaluation').mkdir();tasks=[]
 for label,base in (('standard',STUDY/'campaign_01'),('low_entropy',OUT)):
  for s in specs:
   rid=label+'_'+s['id']
   tasks.append(dict(id='eval_'+rid,command=[PY,str(EVAL),'--method','rl','--checkpoint',
    str(base/s['id']/('checkpoint_step_%07d'%step)),'--manifest',str(MANIFEST),
    '--output',str(OUT/'evaluation'/rid)]))
 pool(tasks,'evaluation')
 write('STATE.json',dict(phase='complete',updated_utc=time.time(),common_step=step,
  note='Needs separate diagnostic report; do not merge with main100k',running=[],pending=[]))
if __name__=='__main__':
 try:main()
 except Exception as e:
  if OUT.exists():write('FAILED.json',dict(error=repr(e),utc=time.time()))
  raise
