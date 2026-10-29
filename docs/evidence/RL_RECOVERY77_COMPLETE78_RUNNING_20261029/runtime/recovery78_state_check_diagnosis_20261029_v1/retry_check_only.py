from pathlib import Path
import json,time,hashlib,subprocess,os,sys
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;P=B/'runtime/prepare_recovery78_20261029_v1';OUT=B/'runs/parameter_partial75_recovery_cycle78_20261029_v1';FIX=B/'runtime/recovery77_health_dependency_fix_20261029_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2)+'\n')
try:
 assert read(D/'diagnose.json')['differences']==[]
 assert [x['path'] for x in read(D/'diagnose_hidden.json')['differences']]==['learner/cuda_rng']
 assert not (OUT/'LAUNCH.json').exists() and not (P/'FINISHED.json').exists()
 for n,h in read(P/'REGISTRATION.json')['sources'].items():assert sha(P/n)==h
 failures=[P/'FAILURE.json',FIX/'restore78_FAILURE.json',FIX/'restore78.log',OUT/'CHECK_ONLY_EXIT_CODES.json']
 for m in ['impedance','admittance','vmc']:
  failures.extend([OUT/m/'CHECK_ONLY_FAILURE.json',OUT/m/'check_only.log']);assert not (OUT/m/'train').exists() and not (OUT/m/'CHECK_ONLY_REVIEW.json').exists()
 preserved=[ref(p) for p in failures];write(D/'ORIGINAL_FAILURES.json',preserved)
 (D/'CHECK_ONLY_EXIT_CODES_before_retry.json').write_bytes((OUT/'CHECK_ONLY_EXIT_CODES.json').read_bytes())
 env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');env.pop('CUDA_VISIBLE_DEVICES',None)
 jobs=read(OUT/'COMMANDS.json')['jobs'];processes={};launch=[]
 for j in jobs:
  cmd=j['command']+['--check-only']
  with (OUT/j['controller']/'check_only_cuda_visible.log').open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env)
  processes[j['controller']]=p;launch.append(dict(controller=j['controller'],pid=p.pid,command=cmd,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
 write(D/'RETRY_JOBS.json',launch)
 codes={m:p.wait() for m,p in processes.items()};write(D/'RETRY_EXIT_CODES.json',codes);assert all(v==0 for v in codes.values()),codes
 for m in codes:
  r=read(OUT/m/'CHECK_ONLY_REVIEW.json');assert r['passed'] and r['full_learner_state_exact'] and r['full_replay_and_next65536_exact'] and r['negative_rejections']==9 and not (OUT/m/'train').exists()
 for x in preserved:assert sha(x['path'])==x['sha256']
 write(D/'RECOVERY_REVIEW.json',dict(passed=True,time=time.time(),root_cause='CUDA_VISIBLE_DEVICES empty hid saved CUDA RNG from state_dict. Only execution environment corrected; full equality assertion and frozen driver unchanged.',original_failures=preserved,prior_exit_codes=ref(D/'CHECK_ONLY_EXIT_CODES_before_retry.json'),visible=ref(D/'diagnose.json'),hidden=ref(D/'diagnose_hidden.json'),sources_unchanged=read(P/'REGISTRATION.json')['sources'],new_physics=0,optimizer_updates=0,scientific_restart=False))
 # Canonical final exit codes reference the successful checks; original nonzero codes retained above.
 (OUT/'CHECK_ONLY_EXIT_CODES.json').write_text(json.dumps(codes,indent=2)+'\n')
 write(OUT/'CHECK_ONLY_COMPLETE.json',dict(passed=True,time=time.time(),new_physics=0,optimizer_updates=0,automatic_training=False,recovery=ref(D/'RECOVERY_REVIEW.json')))
 write(FIX/'restore78_RECOVERY_REVIEW.json',dict(passed=True,time=time.time(),role='restore78',original_failure_preserved=ref(P/'FAILURE.json'),health_recovery=ref(FIX/'HEALTH_RECOVERY_REVIEW.json'),restore_environment_recovery=ref(D/'RECOVERY_REVIEW.json'),new_physics=0,optimizer_updates=0,scientific_restart=False))
 write(P/'FINISHED.json',dict(prepared=True,time=time.time(),automatic_training=False,recovery=ref(FIX/'restore78_RECOVERY_REVIEW.json')))
 print('All three exact78 restores passed; no training')
except BaseException as e:
 write(D/'RETRY_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
