from pathlib import Path
import json,time,hashlib,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'runs/parameter_partial75_recovery_cycle79_20261029_v1';L=B/'runs/parameter_recovery79_loss_20261029_v1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
launch=read(R/'LAUNCH.json');assert not (L/'LAUNCH.json').exists() and not (L/'PLAN.json').exists()
for x in read(L/'SOURCE_REVIEW.json')['files']:assert sha(L/x['name'])==x['sha256']
for j in launch['jobs']:
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
p=dict(time=time.time(),parent_run=str(R),jobs=launch['jobs'],python=str(B/'env/bin/python'),sources={n:sha(L/n) for n in ['audit.py','paired_gate.py','review_saved.py','wait.py']},automatic_training=False)
(L/'PLAN.json').write_text(json.dumps(p,indent=2)+'\n')
with (L/'driver.log').open('x') as f:c=subprocess.Popen([str(B/'env/bin/python'),str(L/'wait.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
j=dict(time=time.time(),pid=c.pid,proc_start_ticks=Path(f'/proc/{c.pid}/stat').read_text().rsplit(')',1)[1].split()[19],plan_sha256=sha(L/'PLAN.json'),automatic_training=False);(L/'LAUNCH.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(j))
