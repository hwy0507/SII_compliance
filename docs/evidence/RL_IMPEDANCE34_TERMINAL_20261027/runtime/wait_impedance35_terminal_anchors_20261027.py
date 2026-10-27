from pathlib import Path
import json,hashlib,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/impedance35_terminal_anchor_followup_20261027_v1');SOURCE=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/track_impedance35_terminal_anchors_20261027.py')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def main():
 os.sched_setaffinity(0,{52});assert sha(OUT/'PLAN.json')=='7ebaf6bbb056320ba89ee3f27b6ad3d2e030c41a23929bcb4930f8d8051b3ef0'
 plan=json.loads((OUT/'PLAN.json').read_text());assert sha(SOURCE)==plan['source_sha256']
 for item in plan['inputs'].values():assert sha(item['path'])==item['sha256']
 root=B/'runs/parameter_capacity_pool30_cycle35_review_20261026_v1';deadline=time.monotonic()+7200
 while not (root/'FINISHED.json').exists():
  assert time.monotonic()<deadline,'Registered wait expired; no automatic rerun/extension'
  assert not (B/'runs/parameter_capacity_pool30_cycle35_20261026_v1/impedance/train/FAILURE.json').exists()
  time.sleep(5)
 assert json.loads((root/'FINISHED.json').read_text())['completed'] and json.loads((root/'REVIEW.json').read_text())['passed']
 reg=dict(plan);reg['inputs']=dict(plan['inputs'])
 reg['inputs'].update(health35=ref(root/'health/DIAGNOSIS.json'),review35=ref(root/'REVIEW.json'),checkpoint35=ref(B/'runs/parameter_capacity_pool30_cycle35_archive_20261026_v1/impedance/cycle_00035.pt'))
 (OUT/'REGISTRATION.json').write_text(json.dumps(reg,indent=2)+'\n')
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
 subprocess.run([str(B/'env/bin/python'),str(SOURCE),'--root',str(OUT)],check=True,env=env,timeout=600)
if __name__=='__main__':
 try:main()
 except BaseException as error:
  (OUT/'WAIT_FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(error)))+'\n');raise
