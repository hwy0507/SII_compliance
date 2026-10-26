from pathlib import Path
import json,hashlib,subprocess,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
out=B/'runs/parameter_capacity24_26_reward_stability_20261026_v1'
review=B/'runs/parameter_capacity_pool30_cycle26_review_20261026_v1'
limit=time.monotonic()+3600
while not (review/'FINISHED.json').exists():
 assert time.monotonic()<limit
 assert not (review/'FAILURE.json').exists()
 time.sleep(5)
assert json.loads((review/'FINISHED.json').read_text())['completed']
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
source=out/'audit_parameter_reward_stability_20261026.py'
assert sha(source)==json.loads((out/'PLAN.json').read_text())['source_sha256']
reg=dict(cycles=[24,25,26],seed=2026102627,bootstrap_replicates=5000,near_zero_guard=1.,relative_limit=.05,source_sha256=sha(source),inputs={})
for m in ['impedance','admittance','vmc']:
 for c in reg['cycles']:
  run=B/'runs'/f'parameter_capacity_pool30_cycle{c}_20261026_v1'/m
  review=B/'runs'/f'parameter_capacity_pool30_cycle{c}_review_20261026_v1'
  reg['inputs'][f'{m}:{c}']={k:dict(path=str(p),sha256=sha(p)) for k,p in dict(protocol=run/'REGISTRATION.json',review=review/'REVIEW.json',health=review/'health/DIAGNOSIS.json',finished=review/'FINISHED.json',episodes=run/'train/episodes.jsonl',optimizer=run/'train/optimizer.jsonl').items()}
(out/'REGISTRATION.json').write_text(json.dumps(reg,indent=2)+'\n')
subprocess.run([str(B/'env/bin/python'),str(source),'--root',str(out)],check=True)
