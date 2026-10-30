from pathlib import Path
import json,time,subprocess,os,sys
R=Path(__file__).parent;O=R.parents[1]/'runs'/R.name
sys.path.insert(0,str(R))
from evaluate_parameter86_frozen_switches_20261030 import validate_design,sha,write
plan=json.loads((O/'PLAN.json').read_text());assert time.time()<plan['time']+plan['wall_dispatch_deadline_seconds']
assert json.loads((O/'CHECKS_FINISHED.json').read_text())['passed']
assert not (O/'LAUNCH.json').exists()
for key in plan['groups']:
 d=O/key;validate_design(json.loads((d/'REGISTRATION.json').read_text()))
 assert not (d/'EVALUATION.json').exists() and not (d/'FAILURE.json').exists()
 assert json.loads((d/'CHECK_ONLY_REVIEW.json').read_text())['passed']
 assert not (d/'driver.log').exists()
jobs=[];started=time.time()
for key in plan['groups']:
 d=O/key;command=[sys.executable,str(R/'evaluate_parameter86_frozen_switches_20261030.py'),'--registration',str(d/'REGISTRATION.json')]
 with (d/'driver.log').open('x') as f:p=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 start=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 jobs.append(dict(group=key,pid=p.pid,start=start,command=command))
write(O/'LAUNCH.json',dict(time=started,plan_sha256=sha(O/'PLAN.json'),launch_source_sha256=sha(__file__),review_source_sha256=sha(R/'review.py'),jobs=jobs))
with (O/'review.log').open('x') as f:p=subprocess.Popen([sys.executable,str(R/'review.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
write(O/'REVIEW_LAUNCH.json',dict(time=time.time(),pid=p.pid,start=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],source_sha256=sha(R/'review.py')))
print(json.dumps(jobs))
