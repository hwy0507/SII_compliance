from pathlib import Path
import json,time,hashlib,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;R=B/'runs/parameter_partial75_recovery_cycle78_20261029_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
assert not (D/'LAUNCH.json').exists() and not (D/'REGISTRATION.json').exists()
assert read(D/'DRIVER_SOURCE_REVIEW.json')['passed'] and read(D/'CONTRACT_REVIEW.json')['passed'] and read(D/'INCOMPLETE78_REJECTION.json')['passed']
assert sha(D/'resume_recovery78.py')==read(D/'DRIVER_SOURCE_REVIEW.json')['driver_sha256']
plan=dict(time=time.time(),parent_run=str(R),parent_review=str(B/'runs/parameter_partial75_recovery_cycle78_review_20261029_v1'),parent_launch_sha256=sha(R/'LAUNCH.json'),learners=read(R/'LAUNCH.json')['jobs'],monitor=read(R/'MONITOR_LAUNCH.json'),sources={n:sha(D/n) for n in ['resume_recovery78.py','prepare.py','wait_prepare.py']},wait_seconds=14400,automatic_training=False,requires_full78_review_and_original_learners_exit=True,check_only_restores_full_state_and_next65536=True,actual_complete78_restore_pending=True)
for j in plan['learners']+[plan['monitor']]:
 s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==j['proc_start_ticks'] and s[0]!='Z'
assert not (R/'ARCHIVE_REVIEW_FINISHED.json').exists()
write(D/'REGISTRATION.json',plan)
with (D/'driver.log').open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(D/'wait_prepare.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
r=dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),registration_sha256=sha(D/'REGISTRATION.json'),automatic_training=False);write(D/'LAUNCH.json',r);print(json.dumps(r))
