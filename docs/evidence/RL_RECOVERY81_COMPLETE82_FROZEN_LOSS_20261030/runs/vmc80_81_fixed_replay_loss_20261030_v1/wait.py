from pathlib import Path
import hashlib,json,os,subprocess,sys,time,traceback
D=Path(__file__).parent
os.sched_setaffinity(0,{0})
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def live(j):
 p=Path('/proc')/str(j['pid'])/'stat'
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
try:
 pre=read(D/'PRE_REGISTRATION.json')
 for r in pre['sources']+pre['fixed_inputs']:assert sha(r['path'])==r['sha256']
 root=Path(pre['run81']);rev=Path(pre['review81']);term=Path(pre['terminal81'])
 while True:
  for p in [root/'ARCHIVE_REVIEW_FAILURE.json',term/'WAIT_FAILURE.json',rev/'FAILURE.json']:
   assert not p.exists(),str(p)
  if (term/'FINISHED.json').exists() and (root/'ARCHIVE_REVIEW_FINISHED.json').exists():
   assert read(term/'FINISHED.json')['completed'] and read(root/'ARCHIVE_REVIEW_FINISHED.json')['completed']
   assert read(rev/'REVIEW.json')['passed'] and read(rev/'FINISHED.json')['completed']
   assert read(term/'SAVED_VALUES_REVIEW.json')['passed']
   if not any(live(j) for j in pre['learners']):break
  assert time.time()<pre['deadline_unix'],'Finite diagnostic deadline reached; no restart'
  assert live(pre['terminal_waiter']) or (term/'FINISHED.json').exists(),'Terminal waiter disappeared'
  time.sleep(5)
 for r in pre['sources']+pre['fixed_inputs']:assert sha(r['path'])==r['sha256']
 plan=read(pre['prior_plan']);old=plan['inputs']['checkpoint'];plan['cycle']=81
 plan['registration_timing']='Prospectively fixed before complete81; actual immutable checkpoint hashes bound after full81 review'
 plan['inputs'].update(anchor_checkpoint=old,checkpoint=ref(pre['checkpoint81']),registration=ref(root/'vmc/REGISTRATION.json'),full_review=ref(rev/'REVIEW.json'),health=ref(rev/'health/DIAGNOSIS.json'),terminal_values=ref(term/'values.npz'),terminal_review=ref(term/'REVIEW.json'),terminal_saved_review=ref(term/'SAVED_VALUES_REVIEW.json'),prior_indices=ref(Path(pre['prior_plan']).parent/'sample_indices.npy'),prior_batches=ref(Path(pre['prior_plan']).parent/'BATCHES.jsonl'))
 plan['audit_source_sha256']=sha(D/'audit.py');plan['pre_registration_sha256']=sha(D/'PRE_REGISTRATION.json')
 plan['limitation']=pre['limitation'];put(D/'PLAN.json',plan)
 put(D/'DIAGNOSTIC_LAUNCH.json',dict(time=time.time(),plan_sha256=sha(D/'PLAN.json'),automatic_training=False))
 env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 for name in ['audit.py','review_saved.py']:subprocess.run([sys.executable,str(D/name)],env=env,check=True)
 assert read(D/'FINISHED.json')['passed'] and read(D/'SAVED_REVIEW.json')['passed']
 put(D/'WAIT_FINISHED.json',dict(passed=True,time=time.time(),plot_inspected=False,automatic_training=False))
except BaseException as e:
 put(D/'WAIT_FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
