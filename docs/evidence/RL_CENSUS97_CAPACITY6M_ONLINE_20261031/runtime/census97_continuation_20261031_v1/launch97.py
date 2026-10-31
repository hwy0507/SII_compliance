from pathlib import Path
import sys,os,json,time,subprocess,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle97_20261031_v1';O=B/'runs/parameter_census_cycle97_review_20261031_v1'
sys.path.insert(0,str(D));from driver import read,put,sha,validate_protocol

def identity(pid):
 s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z';return s[19]
def gate():
 assert not (R/'LAUNCH.json').exists()
 for n,h in read(D/'SOURCES.json')['files'].items():assert sha(D/n)==h
 assert read(D/'CPU_CONSUMER_REVIEW.json')['passed'] and read(D/'WINDOW97_PROTOCOL_REVIEW.json')['passed']
 assert read(D/'RESOURCE_REVIEW.json')['passed'] and time.time()-read(D/'RESOURCE_REVIEW.json')['time']<3600
 assert read(D/'PREFLIGHT_FINISHED.json')['passed'];contract=read(D/'CONTRACT_REVIEW.json');assert contract['passed'] and sum(x['negative_count'] for x in contract['methods'].values())==120
 for m in contract['methods']:
  assert not (R/m/'train').exists() and not (R/m/'DRIVER_FAILURE.json').exists() and not (R/m/'CHECK_ONLY_FAILURE.json').exists()
  p=read(R/m/'REGISTRATION.json');st=p['post_interruption_continuation'];validate_protocol(st['parent_registration']['sha256'],p);ck=read(R/m/'CHECK_ONLY_REVIEW.json');initial=read(R/m/'check/INITIAL_STATE_REVIEW.json')
  assert ck['passed'] and ck['registration_sha256']==sha(R/m/'REGISTRATION.json') and ck['checkpoint_sha256']==sha(st['checkpoint']['path'])
  assert ck['repeat_native_update_full_state_exact'] and ck['original_state_restored'] and ck['consumer_full_state_exact'] and ck['disposable_restored_clone_updates']==2
  assert initial['passed'] and initial['full_trained96_learner_and_replay_exact']
 guard=read(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json')
 for j in guard['identities']:assert identity(j['pid'])==j['start']
 assert not Path(guard['root'],'STOP').exists()
 for j in read(D/'PREFLIGHT_PROCESSES.json')['jobs'].values():
  f=Path('/proc',str(j['pid']),'stat')
  if f.exists():
   s=f.read_text().rsplit(')',1)[1].split();assert s[0]=='Z' or int(s[19])!=j['start_ticks']
 assert time.time()<read(D/'SCIENTIFIC_DECISION.json')['launch_deadline_unix']
 # Exclude an existing formal96/97 job, checking actual argv rather than old receipts.
 active=[]
 for q in Path('/proc').iterdir():
  if not q.name.isdigit():continue
  try:
   argv=q.joinpath('cmdline').read_bytes().decode().split('\0')
   if any(a in [str(D/'driver.py'),str(B/'runtime/census96_continuation_20261031_v1/driver.py')] for a in argv):active.append(int(q.name))
  except (OSError,UnicodeDecodeError):pass
 assert not active,active
 return dict(passed=True,time=time.time(),registration_hashes={m:sha(R/m/'REGISTRATION.json') for m in contract['methods']},source_manifest_sha256=sha(D/'SOURCES.json'),contract_sha256=sha(D/'CONTRACT_REVIEW.json'),negative_rejections=120,disposable_native_updates=6,automatic_followup=False,new_cycles=1,current_guard=guard)
if __name__=='__main__':
 result=gate()
 if '--check-only' in sys.argv:put(D/'LAUNCH_GATE_REVIEW.json',result);print('Launch gate passed; zero new physics');sys.exit(0)
 assert read(D/'LAUNCH_GATE_REVIEW.json')['passed'];O.mkdir(exist_ok=False);put(R/'PRELAUNCH_REVIEW.json',result)
 jobs=read(R/'COMMANDS.json')['jobs'];env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
 for j in jobs:
  with (R/(j['controller']+'_driver.log')).open('x') as f:p=subprocess.Popen(j['command'],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True,cwd=D)
  j.update(pid=p.pid,proc_start_ticks=identity(p.pid),time=time.time())
 put(R/'LAUNCH.json',dict(time=time.time(),jobs=jobs,new_cycles=1,automatic_followup=False,maximum_new_actions_per_method=41250))
 for name,script in [('MONITOR','archive97.py'),('STARTUP','startup97.py'),('OBSERVER','observe97.py')]:
  with (R/(name.lower()+'.log')).open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(D/script)],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True,cwd=D)
  put(R/(name+'_LAUNCH.json'),dict(time=time.time(),pid=p.pid,proc_start_ticks=identity(p.pid),script_sha256=sha(D/script)))
 print(json.dumps(dict(jobs=jobs,goal='active')),flush=True)
