from pathlib import Path
import json,hashlib,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=B/'runs/admittance41_terminal_anchor_followup_20261027_v1';SOURCE=B/'runtime/track_admittance41_terminal_anchors_20261027.py'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def main():
 os.sched_setaffinity(0,{52});assert sha(OUT/'PLAN.json')=='383a02964a4ae005569e8e80307e9caa562e36434239937f32e891b7473ff4db'
 plan=json.loads((OUT/'PLAN.json').read_text());assert sha(SOURCE)==plan['source_sha256']
 for item in plan['inputs'].values():assert sha(item['path'])==item['sha256']
 root=B/'runs/parameter_capacity_pool30_cycle41_review_20261026_v1';deadline=time.monotonic()+7200
 while not (root/'FINISHED.json').exists():
  assert time.monotonic()<deadline, 'Registered wait expired; no automatic rerun/extension'
  assert not (B/'runs/parameter_capacity_pool30_cycle41_20261026_v1/admittance/train/FAILURE.json').exists()
  time.sleep(5)
 assert json.loads((root/'FINISHED.json').read_text())['completed']
 assert json.loads((root/'REVIEW.json').read_text())['passed']
 reg=dict(plan);reg['inputs']=dict(plan['inputs'])
 reg['inputs'].update(health41=ref(root/'health/DIAGNOSIS.json'),review41=ref(root/'REVIEW.json'),checkpoint41=ref(B/'runs/parameter_capacity_pool30_cycle41_archive_20261026_v1/admittance/cycle_00041.pt'))
 (OUT/'REGISTRATION.json').write_text(json.dumps(reg,indent=2)+'\n')
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
 subprocess.run([str(B/'env/bin/python'),str(SOURCE),'--root',str(OUT)],check=True,env=env,timeout=600)
 assert sha(plan['saved_review_source']['path'])==plan['saved_review_source']['sha256']
 subprocess.run([str(B/'env/bin/python'),plan['saved_review_source']['path'],'--root',str(OUT)],check=True,env=env,timeout=120)
 print('Complete41 fixed1224 terminal read-only follow-up complete.',flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as error:
  (OUT/'WAIT_FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(error)))+'\n');raise
