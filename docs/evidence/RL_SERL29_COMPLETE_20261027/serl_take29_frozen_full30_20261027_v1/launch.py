from pathlib import Path
import json,hashlib,time,subprocess,os
O=Path(__file__).parent;B=O.parents[1];PLAN_SHA='0bcdf58d087370c424801b7f1037131638ee20a56c1c0305f43101163397b7dd';FREEZE_SHA='c32a88ba3b18f86d8b4fe7c390e5192a212798d2e92c136fa2fd0087cf0effb0'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
assert sha(O/'PLAN.json')==PLAN_SHA and sha(O/'SOURCE_FREEZE.json')==FREEZE_SHA
assert json.loads((O/'CHECK_ONLY_COMPLETE.json').read_text())['passed']
assert json.loads((O/'PRELAUNCH_REVIEW.json').read_text())['passed']
assert not (O/'LAUNCH.json').exists()
prior=B/'runs/parameter41_frozen_full30_20261027_v1'
assert json.loads((prior/'REVIEW.json').read_text())['passed']
for job in json.loads((prior/'LAUNCH.json').read_text())['jobs']:assert not Path(f"/proc/{job['pid']}").exists()
assert not Path(f"/proc/{json.loads((prior/'REVIEW_LAUNCH.json').read_text())['pid']}").exists()
freeze=json.loads((O/'SOURCE_FREEZE.json').read_text());rt=Path(freeze['evaluation_runtime'])
for n,h in freeze['source_hashes'].items():assert sha(rt/n)==h
reg=json.loads((O/'REGISTRATION.json').read_text())
for item in reg['inputs'].values():assert sha(item['path'])==item['sha256']
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
jobs=[]
for i,job in enumerate(json.loads((O/'COMMANDS.json').read_text())['jobs']):
 with (O/f'shard{i}.log').open('x') as log:p=subprocess.Popen(job['command'],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 start=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19];jobs.append(dict(**job,pid=p.pid,start=start,time=time.time()))
write(O/'LAUNCH.json',dict(jobs=jobs))
with (O/'review.log').open('x') as log:p=subprocess.Popen([str(B/'env/bin/python'),str(rt/'review_serl29_recovery_frozen_matrix_20261027.py'),'--root',str(O)],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
write(O/'REVIEW_LAUNCH.json',dict(pid=p.pid,time=time.time()));print(dict(evaluators=[j['pid'] for j in jobs],review=p.pid),flush=True)
