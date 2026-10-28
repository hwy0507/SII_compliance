from pathlib import Path
import json, hashlib, shutil, subprocess, os, time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
old='parameter_capacity_pool30_cycle55_20261026_v1'; name='parameter_capacity_pool30_cycle56_20261026_v1'
OUT=B/'runs'/name; RT=B/'runtime'/name
oldrun=B/'runs'/old; oldarc=B/'runs/parameter_capacity_pool30_cycle55_archive_20261026_v1'; prevreview=B/'runs/parameter_capacity_pool30_cycle55_review_20261026_v1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
 return h.hexdigest()
def ref(p): return {'path':str(p),'sha256':sha(p)}
def write(p,d): Path(p).write_text(json.dumps(d,indent=2)+'\n')
assert not OUT.exists(), OUT
assert json.loads((prevreview/'FINISHED.json').read_text())['completed']
assert json.loads((prevreview/'REVIEW.json').read_text())['passed']
assert json.loads((oldrun/'CHECK_ONLY_COMPLETE.json').read_text())['passed']
shutil.copytree(B/'runtime'/old, RT, ignore=shutil.ignore_patterns('__pycache__'))
OUT.mkdir()
# Scientific gate for one unchanged finite cycle.
decision=OUT/'SCIENTIFIC_DECISION.json'
write(decision, {'parent_cycle':55,'new_cycles':1,'learner_settings_unchanged':True,'capacity_before':4000000,'capacity_after':4000000,'auxiliary_weights_imported':False,'reason':'Continue latest complete55 for one finite cycle56, retaining 4m append replay and all persisted state/historical markers; no auxiliary weights or convergence claim.','required_review':ref(prevreview/'REVIEW.json'),'required_health':ref(prevreview/'health/DIAGNOSIS.json')})

commands=[]
oldjobs=json.loads((oldrun/'LAUNCH.json').read_text())['jobs']
for job in oldjobs:
 m=job['controller']; dest=OUT/m; dest.mkdir()
 parentreg=oldrun/m/'REGISTRATION.json'; p=json.loads(parentreg.read_text())
 p['resume_parent_registration']=ref(parentreg)
 p['completed_stage_continuation']['parent_cycle']=55
 p['completed_stage_continuation']['review']=ref(decision)
 trial=p['batch_size_stage']; trial['parent_cycle']=55
 cp=oldarc/m/'cycle_00055.pt'; assert cp.exists()
 trial['checkpoint']=ref(cp)
 trial['cycle_review']=ref(prevreview/'REVIEW.json'); trial['health_review']=ref(prevreview/'health/DIAGNOSIS.json')
 trial['reason']='Latest complete55 fullstate; retain4m replay, all rows/RNG/history and learner settings; finite cycle56.'
 write(dest/'REGISTRATION.json',p)
 cmd=list(job['command'])
 cmd[1]=str(RT/'resume_cheq_capacity4m_pool30_20261027.py')
 for flag,value in [('--registration',dest/'REGISTRATION.json'),('--resume',cp),('--output',dest/'train')]: cmd[cmd.index(flag)+1]=str(value)
 commands.append({'controller':m,'command':cmd})
write(OUT/'COMMANDS.json',{'jobs':commands})
# Static exact restore checks, one CPU per learner.
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
procs=[]
for cpu,job in zip([13,26,39],commands):
 log=(OUT/job['controller']/'check_only.log').open('w')
 procs.append((job['controller'],subprocess.Popen(['taskset','-c',str(cpu)]+job['command']+['--check-only'],stdout=log,stderr=subprocess.STDOUT,env=env)))
status={m:p.wait() for m,p in procs}; write(OUT/'CHECK_ONLY_EXIT_CODES.json',status)
if any(v!=0 for v in status.values()): raise SystemExit(status)
write(OUT/'CHECK_ONLY_COMPLETE.json',{'passed':True,'new_optimizer_updates':0,'time':time.time()})
write(OUT/'PREPARATION_REVIEW.json',dict(passed=True,time=time.time(),parent_cycle=55,new_cycle=56,convergence_claim=False,plot_inspected=False,checks='Complete55 replay/reward review and health diagnosis; exact56 restore check-only passed',check_only=ref(OUT/'CHECK_ONLY_COMPLETE.json')))
print(json.dumps({'out':str(OUT),'status':status,'jobs':commands},indent=2))
