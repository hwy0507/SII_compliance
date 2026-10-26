from pathlib import Path
import json,subprocess,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
review=B/'runs/serl_multistep_batch65536_cycle17_review_20261026_v1'
limit=time.monotonic()+7200
while not (review/'FINISHED.json').exists():
 assert time.monotonic()<limit
 assert not (B/'runs/serl_multistep_batch65536_cycle17_20261026_v1/direct/FAILURE.json').exists()
 time.sleep(5)
assert json.loads((review/'FINISHED.json').read_text())['completed']
assert json.loads((review/'REVIEW.json').read_text())['passed']
subprocess.run([str(B/'env/bin/python'),str(B/'runtime/prepare_serl_batch18_20261026.py')],check=True)
print('Prepared18 only. Formal launch requires review inspection.',flush=True)
