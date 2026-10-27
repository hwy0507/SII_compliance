from pathlib import Path
import json,subprocess,time,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
review=B/'runs/parameter_capacity_pool30_cycle43_review_20261026_v1'
limit=time.monotonic()+7200
while not (review/'FINISHED.json').exists():
 assert time.monotonic()<limit
 for m in ['impedance','admittance','vmc']:
  assert not (B/'runs/parameter_capacity_pool30_cycle43_20261026_v1'/m/'train/FAILURE.json').exists()
 time.sleep(5)
assert json.loads((review/'FINISHED.json').read_text())['completed']
assert json.loads((review/'REVIEW.json').read_text())['passed']
subprocess.run([str(B/'env/bin/python'),str(B/'runtime/prepare_parameter_capacity44_20261026.py')],check=True)
print('Prepared44 only. Formal launch requires review inspection.',flush=True)
