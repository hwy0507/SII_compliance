from pathlib import Path
import json,hashlib,time,subprocess,sys,os,traceback
D=Path(__file__).parent;os.sched_setaffinity(0,{54})
def read(p):return json.loads(Path(p).read_text())
def ref(p):
 with Path(p).open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),sha256=h)
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
try:
 pre=read(D/'PRE_REGISTRATION.json');root=Path(pre['window'])
 for r in pre['inputs']:assert ref(r['path'])==r
 while True:
  for n in ['FAILURE.json','WAIT_FAILURE.json']:assert not (root/n).exists(),n
  alive=live(pre['original_waiter'])
  if (root/'SAVED_ARITHMETIC_REVIEW.json').exists() and not alive:
   assert read(root/'SAVED_ARITHMETIC_REVIEW.json')['passed'] and read(root/'REVIEW.json')['passed'];break
  assert alive,'Original window waiter absent without successful complete outputs'
  assert time.time()<pre['original_deadline_unix'],'Original window wait deadline reached; no extension'
  time.sleep(5)
 for r in pre['inputs']:assert ref(r['path'])==r
 plan=dict(time=time.time(),registered_after_original_results=True,prospective_supplement_pre_registration=ref(D/'PRE_REGISTRATION.json'),windows={'85_87':str(root)},inputs=[ref(root/n) for n in ['PLAN.json','REGISTRATION.json','REVIEW.json','SAVED_ARITHMETIC_REVIEW.json']]+[ref(D/'audit.py')],original_seed=2026102858,original_replicates=5000,limitation=pre['limitation'])
 put(D/'PLAN.json',plan);subprocess.run([sys.executable,str(D/'audit.py')],check=True)
 assert read(D/'REVIEW.json')['passed'];put(D/'FINISHED.json',dict(passed=True,time=time.time(),new_physics=0,optimizer_updates=0,automatic_training=False))
except BaseException as e:put(D/'FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
