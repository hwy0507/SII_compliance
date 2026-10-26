from pathlib import Path
import json,hashlib,subprocess,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
out=B/'runs/admittance27_terminal_anchors_20261026_v1';review=B/'runs/parameter_capacity_pool30_cycle27_review_20261026_v1'
limit=time.monotonic()+3600
while not (review/'FINISHED.json').exists():
 assert time.monotonic()<limit
 assert not (B/'runs/parameter_capacity_pool30_cycle27_20261026_v1/admittance/train/FAILURE.json').exists()
 time.sleep(5)
assert json.loads((review/'FINISHED.json').read_text())['completed']
def ref(p):
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),sha256=h)
reg=json.loads((out/'PLAN.json').read_text());source=out/'track_admittance27_terminal_anchors_20261026.py'
assert ref(source)['sha256']==reg['source_sha256']
anchor=B/'runs/admittance25_26_terminal_concentration_20261026_v2'
reg['inputs']={k:ref(p) for k,p in dict(anchor_values=anchor/'cycle26_terminal_values.npz',anchor_registration=anchor/'REGISTRATION.json',anchor_review=anchor/'SAVED_VALUE_REVIEW.json',health27=review/'health/DIAGNOSIS.json',review27=review/'REVIEW.json',checkpoint27=B/'runs/parameter_capacity_pool30_cycle27_archive_20261026_v1/admittance/cycle_00027.pt').items()}
(out/'REGISTRATION.json').write_text(json.dumps(reg,indent=2)+'\n')
subprocess.run([str(B/'env/bin/python'),str(source),'--root',str(out)],check=True)
