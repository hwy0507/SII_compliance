from pathlib import Path
import json,time,hashlib,subprocess,os,ast,sys
os.sched_setaffinity(0,{53})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runs/parameter_partial75_recovery_cycle76_review_20261029_v1';REV=B/'runs/parameter_partial75_recovery_cycle77_review_20261029_v1';RUN=B/'runs/parameter_partial75_recovery_cycle77_20261029_v1';FUT=B/'runs/parameter_partial75_recovery_cycle78_review_20261029_v1';ARC=B/'runs/parameter_partial75_recovery_cycle77_archive_20261029_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2)+'\n')
def ended(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if p.exists():
  f=p.read_text().rsplit(')',1)[1].split();assert f[19]!=j['proc_start_ticks'] or f[0]=='Z'
try:
 for j in read(RUN/'LAUNCH.json')['jobs']+[read(RUN/'MONITOR_LAUNCH.json')]:ended(j)
 assert (RUN/'ARCHIVE_REVIEW_FAILURE.json').exists() and not (REV/'health').exists()
 review=read(REV/'REVIEW.json');assert review['passed']
 evidence=dict(failure=ref(RUN/'ARCHIVE_REVIEW_FAILURE.json'),failure_log=ref(RUN/'monitor.log'),complete_review=ref(REV/'REVIEW.json'),complete_archive=ref(ARC/'FINISHED.json'))
 for x in read(REV/'SOURCE_REVIEW.json')['files']:assert sha(REV/x['name'])==x['sha256']
 helper=OLD/'diagnose_published_value_bound_20261025.py';expected=next(x['sha256'] for x in read(OLD/'SOURCE_REVIEW.json')['files'] if x['name']==helper.name);assert sha(helper)==expected=='2a5b04c7a4036d78775a7abb87170660a0e3b6b0111846f24d4a9245dc268245'
 repairs=[]
 for dest in [REV,FUT]:
  q=dest/helper.name;assert not q.exists();q.write_bytes(helper.read_bytes());assert sha(q)==expected;ast.parse(q.read_text());repairs.append(ref(q))
 for m,r in review['methods'].items():
  cp=ARC/m/'cycle_00077.pt';assert sha(cp)==r['checkpoint_sha256'];assert r['new_transitions']==41250 and r['retained_replay_all_fields_exact'] and r['max_reward_reconstruction_error']==0
 env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(B/'runtime/source_train17_clock/source/tools'))
 # Import the unchanged diagnostic and ensure its missing helper resolves from the reviewed directory.
 smoke="import sys,importlib;sys.path.insert(0,sys.argv[1]);m=importlib.import_module('diagnose_published_training_20261025');h=importlib.import_module('diagnose_published_value_bound_20261025');assert h.__file__==sys.argv[1]+'/diagnose_published_value_bound_20261025.py';print(h.__file__)"
 for folder in [REV,FUT]:subprocess.run([sys.executable,'-c',smoke,str(folder)],check=True,env=env)
 write(D/'DEPENDENCY_REPAIR.json',dict(passed=True,time=time.time(),source=ref(helper),destinations=repairs,unchanged_diagnostic_sha256=sha(REV/'diagnose_published_training_20261025.py'),prior_failures_preserved=True,imports_passed=True,new_physics=0,optimizer_updates=0,evidence=evidence))
 cmd=[str(B/'env/bin/python'),str(REV/'diagnose_published_training_20261025.py'),'--runtime',str(B/'runtime/source_train17_clock'),'--run',str(B/'runs/parameter_partial75_recovery_cycle77_archive_20261029_v1_view'),'--output',str(REV/'health'),'--cycle-archive',str(ARC),'--cycle','77']
 subprocess.run(cmd,check=True,env=env)
 health=read(REV/'health/DIAGNOSIS.json')
 for m,r in review['methods'].items():assert health['methods'][m]['checkpoint_sha256']==r['checkpoint_sha256'] and health['methods'][m]['network_state_unchanged']
 for k,v in evidence.items():assert sha(v['path'])==v['sha256']
 evidence['health']=ref(REV/'health/DIAGNOSIS.json');evidence['repair']=ref(D/'DEPENDENCY_REPAIR.json')
 write(D/'HEALTH_RECOVERY_REVIEW.json',dict(passed=True,time=time.time(),evidence=evidence,new_physics=0,optimizer_updates=0,science_restarted=False,review_not_recomputed=True))
 write(REV/'FINISHED.json',dict(completed=True,time=time.time(),convergence_claim=False,recovery=ref(D/'HEALTH_RECOVERY_REVIEW.json')))
 write(RUN/'ARCHIVE_REVIEW_FINISHED.json',dict(completed=True,time=time.time(),review=str(REV),recovery=ref(D/'HEALTH_RECOVERY_REVIEW.json'),original_failure=ref(RUN/'ARCHIVE_REVIEW_FAILURE.json')))
 print('Health-only continuation finished; original scientific review/checkpoints and failure unchanged')
except BaseException as e:write(D/'FAILURE.json',dict(time=time.time(),error=repr(e)));raise
