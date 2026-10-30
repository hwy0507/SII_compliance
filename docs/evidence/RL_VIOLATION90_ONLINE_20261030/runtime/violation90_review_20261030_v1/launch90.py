from pathlib import Path
import sys,os,json,time,subprocess,hashlib,ast
D=Path(__file__).resolve().parent;B=D.parents[1];P=B/'runtime/violation90_online_20261030_v1';R=B/'runs/parameter_violation_cycle90_20261030_v1';O=B/'runs/parameter_violation_cycle90_review_20261030_v1'
sys.path[:0]=[str(P),str(B/'runtime/source_train17_clock/source/tools')]
from driver import read,put,sha,validate_protocol

def identity(pid):
 f=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();assert f[0]!='Z';return f[19]
def gate():
 assert not (R/'LAUNCH.json').exists()
 for directory in [P,D]:
  for n,h in read(directory/'SOURCES.json')['files'].items():assert sha(directory/n)==h
 assert read(P/'PREFLIGHT_FINISHED.json')['passed']
 contracts=read(P/'CONTRACT_REVIEW.json');assert contracts['passed'] and sum(v['negative_count'] for v in contracts['methods'].values())==93
 for m in ['impedance','admittance','vmc']:
  assert not (R/m/'train').exists() and not (R/m/'DRIVER_FAILURE.json').exists() and not (R/m/'CHECK_ONLY_FAILURE.json').exists()
  p=read(R/m/'REGISTRATION.json');st=p['post_interruption_continuation'];validate_protocol(st['parent_registration']['sha256'],p)
  ck=read(R/m/'CHECK_ONLY_REVIEW.json');initial=read(R/m/'check/INITIAL_STATE_REVIEW.json')
  assert ck['passed'] and ck['registration_sha256']==sha(R/m/'REGISTRATION.json') and ck['checkpoint_sha256']==st['checkpoint']['sha256']==sha(st['checkpoint']['path'])
  assert ck['repeat_native_update_full_state_exact'] and ck['original_state_restored'] and ck['disposable_restored_clone_updates']==2 and ck['new_physics']==ck['actual_formal_updates']==0
  assert initial['passed'] and initial['full_migrated89_learner_and_replay_exact'] and initial['learned_history_weights_and_adam_retained']
 for pid,tick in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475'),(2675653,'575369491'),(2675660,'575369492'),(2675662,'575369492'),(2675665,'575369492'),(2713409,'575376596')]:assert identity(pid)==tick
 assert not Path('/tmp/sii_gpu_util_guard_20261030_v7/STOP').exists()
 for j in read(P/'PREFLIGHT_PROCESSES.json')['jobs'].values():
  q=Path('/proc',str(j['pid']),'stat')
  if q.exists():
   f=q.read_text().rsplit(')',1)[1].split();assert f[0]=='Z' or int(f[19])!=j['start_ticks']
 return dict(passed=True,time=time.time(),registration_hashes={m:sha(R/m/'REGISTRATION.json') for m in contracts['methods']},contract_sha256=sha(P/'CONTRACT_REVIEW.json'),negative_rejections=93,disposable_native_updates=6,consumer_sources_sha256=sha(D/'SOURCES.json'),scientific_decision_sha256=sha(P/'SCIENTIFIC_DECISION.json'),automatic_followup=False,new_cycles=1)
if __name__=='__main__':
 result=gate()
 if '--check-only' in sys.argv:put(D/'LAUNCH_GATE_REVIEW.json',result);print('Launch gate passed; zero new physics');sys.exit(0)
 assert read(D/'LAUNCH_GATE_REVIEW.json')['passed'];O.mkdir(exist_ok=False)
 put(R/'PRELAUNCH_REVIEW.json',result)
 env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');jobs=read(R/'COMMANDS.json')['jobs']
 for j in jobs:
  with (R/(j['controller']+'_driver.log')).open('x') as f:p=subprocess.Popen(j['command'],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True,cwd=P)
  j.update(pid=p.pid,proc_start_ticks=identity(p.pid),time=time.time())
 put(R/'LAUNCH.json',dict(time=time.time(),jobs=jobs,new_cycles=1,automatic_followup=False,maximum_new_actions_per_method=41250))
 for name,script in [('MONITOR','archive90.py'),('STARTUP','startup90.py'),('OBSERVER','observe90.py')]:
  with (R/(name.lower()+'.log')).open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(D/script)],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True,cwd=D)
  put(R/(name+'_LAUNCH.json'),dict(time=time.time(),pid=p.pid,proc_start_ticks=identity(p.pid),script_sha256=sha(D/script)))
 print(json.dumps(jobs,indent=2))
