from pathlib import Path
import json,subprocess,time,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
review=B/'runs/serl_multistep_batch65536_cycle23_review_20261026_v1'
limit=time.monotonic()+7200
while not (review/'FINISHED.json').exists():
 assert time.monotonic()<limit
 assert not (B/'runs/serl_multistep_batch65536_cycle23_20261026_v1/direct/FAILURE.json').exists()
 time.sleep(5)
assert json.loads((review/'FINISHED.json').read_text())['completed']
assert json.loads((review/'REVIEW.json').read_text())['passed']
subprocess.run([str(B/'serl_env/bin/python'),str(B/'runtime/prepare_serl_capacity24_20261027.py')],check=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
print('Prepared24 only. Formal launch requires review inspection.',flush=True)
