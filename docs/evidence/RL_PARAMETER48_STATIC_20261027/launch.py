from pathlib import Path
import json,os,subprocess,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
import hashlib
for relative,expected in json.loads((Path(__file__).parent/'SOURCE_MANIFEST.json').read_text()).items():
 with (Path(__file__).parent/relative).open('rb') as source:assert hashlib.file_digest(source,'sha256').hexdigest()==expected
out=B/'runs/parameter_capacity_pool30_cycle48_20261026_v1'
review=B/'runs/parameter_capacity_pool30_cycle47_review_20261026_v1'
assert json.loads((review/'FINISHED.json').read_text())['completed']
assert json.loads((review/'REVIEW.json').read_text())['passed']
assert json.loads((out/'CHECK_ONLY_COMPLETE.json').read_text())['passed']
assert json.loads((out/'PRELAUNCH_SCIENTIFIC_REVIEW.json').read_text())['passed']
assert not (out/'LAUNCH.json').exists()
parent_jobs=json.loads((B/'runs/parameter_capacity_pool30_cycle47_20261026_v1/LAUNCH.json').read_text())['jobs']
for job in parent_jobs:assert not Path(f"/proc/{job['pid']}").exists()
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
launched=[]
for job in json.loads((out/'COMMANDS.json').read_text())['jobs']:
 with (out/job['controller']/'train.log').open('x') as log:
  proc=subprocess.Popen(job['command'],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 launched.append(dict(**job,pid=proc.pid,time=time.time()))
(out/'LAUNCH.json').write_text(json.dumps(dict(jobs=launched),indent=2)+'\n')
print(json.dumps(launched),flush=True)
subprocess.run([str(B/'env/bin/python'),str(Path(__file__).parent/'setup_monitors.py')],check=True)
