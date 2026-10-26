from pathlib import Path
import json,os,subprocess,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
out=B/'runs/parameter_pool30_cycle21_20261026_v1'
review=B/'runs/parameter_pool30_cycle20_review_20261026_v1'
assert json.loads((review/'FINISHED.json').read_text())['completed']
assert json.loads((review/'REVIEW.json').read_text())['passed']
assert json.loads((out/'CHECK_ONLY_COMPLETE.json').read_text())['passed']
assert not (out/'LAUNCH.json').exists()
for pid in [1127927,1127928,1127929]:assert not Path(f'/proc/{pid}').exists()
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
launched=[]
for job in json.loads((out/'COMMANDS.json').read_text())['jobs']:
 with (out/job['controller']/'train.log').open('x') as log:
  proc=subprocess.Popen(job['command'],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 launched.append(dict(**job,pid=proc.pid,time=time.time()))
(out/'LAUNCH.json').write_text(json.dumps(dict(jobs=launched),indent=2)+'\n')
print(json.dumps(launched),flush=True)
subprocess.run(['python',str(B/'runtime/setup_parameter_pool21_monitors_20261026.py')],check=True)
