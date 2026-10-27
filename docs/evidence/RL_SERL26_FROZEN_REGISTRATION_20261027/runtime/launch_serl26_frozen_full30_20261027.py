from pathlib import Path
import json,hashlib,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=B/'runs/serl_cycle26_frozen_full30_20261027_v1';RT=B/'runtime'/OUT.name
PLAN_SHA='72882a42d0a32a3414363e8f8163f1d7169bb92f10ec8254ffe59e3dd65bf896'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
assert sha(OUT/'PLAN.json')==PLAN_SHA
assert json.loads((OUT/'CHECK_ONLY_COMPLETE.json').read_text())['passed']
assert json.loads((OUT/'PRELAUNCH_REVIEW.json').read_text())['passed']
assert not (OUT/'LAUNCH.json').exists()
# Respect pre-registered CPU53/54 physical-resource ordering.
prior=B/'runs/parameter41_frozen_full30_20261027_v1'
assert json.loads((prior/'REVIEW.json').read_text())['passed']
for job in json.loads((prior/'LAUNCH.json').read_text())['jobs']:assert not Path(f"/proc/{job['pid']}").exists()
assert not Path(f"/proc/{json.loads((prior/'REVIEW_LAUNCH.json').read_text())['pid']}").exists()
plan=json.loads((OUT/'PLAN.json').read_text())
for n,h in plan['source_hashes'].items():assert sha(RT/n)==h
reg=json.loads((OUT/'REGISTRATION.json').read_text())
for item in reg['inputs'].values():assert sha(item['path'])==item['sha256']
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
jobs=[]
for i,job in enumerate(json.loads((OUT/'COMMANDS.json').read_text())['jobs']):
 with (OUT/f'shard{i}.log').open('x') as log:p=subprocess.Popen(job['command'],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 start=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19];jobs.append(dict(**job,pid=p.pid,start=start,time=time.time()))
write(OUT/'LAUNCH.json',dict(jobs=jobs))
with (OUT/'review.log').open('x') as log:p=subprocess.Popen([str(B/'env/bin/python'),str(RT/'review_serl26_frozen_matrix_20261027.py'),'--root',str(OUT)],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
write(OUT/'REVIEW_LAUNCH.json',dict(pid=p.pid,time=time.time()));print(dict(evaluators=[j['pid'] for j in jobs],review=p.pid),flush=True)
