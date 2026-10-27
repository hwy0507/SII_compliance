from pathlib import Path
import json,time,hashlib,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/parameter_capacity_pool30_cycle46_20261026_v1';P=B/'runs/parameter_capacity_pool30_cycle45_review_20261026_v1';S=B/'runs/parameter45_saved_review_20261027_v1/REVIEW.json'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
stability=B/'runs/parameter43_45_stability_saved_review_20261027_v1/REVIEW.json';assert json.loads(stability.read_text())['passed']
r=json.loads((P/'REVIEW.json').read_text());h=json.loads((P/'health/DIAGNOSIS.json').read_text());saved=json.loads(S.read_text());assert r['passed'] and saved['passed']
assert json.loads((P/'FINISHED.json').read_text())['completed']
limit=time.monotonic()+180
while not (O/'CHECK_ONLY_COMPLETE.json').exists():
 assert time.monotonic()<limit,'Actual46 checks not ready within bounded launch observation'
 if (O/'CHECK_ONLY_EXIT_CODES.json').exists():assert all(v==0 for v in json.loads((O/'CHECK_ONLY_EXIT_CODES.json').read_text()).values())
 time.sleep(2)
assert json.loads((O/'CHECK_ONLY_COMPLETE.json').read_text())['passed'];checks={}
for m in ['impedance','admittance','vmc']:
 c=json.loads((O/m/'check_only.log').read_text().splitlines()[-1]);a=r['methods'][m];health=h['methods'][m]
 assert c['passed'] and c['full_learner_state_unchanged'] and c['exact_replay_and_next65536']
 assert c['checkpoint_sha256']==a['checkpoint_sha256']==health['checkpoint_sha256']==saved['methods'][m]['checkpoint_sha256']
 assert health['network_state_unchanged'] and a['optimizer_and_network_finite'] and a['retained_replay_all_fields_exact'] and a['max_reward_reconstruction_error']==0
 checks[m]=c
refs=[P/'REVIEW.json',P/'health/DIAGNOSIS.json',S,O/'CHECK_ONLY_COMPLETE.json',O/'SCIENTIFIC_DECISION.json',stability]
assert not (O/'LAUNCH.json').exists()
(O/'PRELAUNCH_SCIENTIFIC_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),parent_cycle=45,new_cycle=46,new_cycles=1,maximum_new_actions_per_method=41250,checks=checks,evidence_sha256={str(p):sha(p) for p in refs},plot_inspected=True,reason='Complete45 fullstate/next65536 verified; fullreview/health/saved arithmetic inspected. Fixed43-45 reward check does not establish joint healthy convergence. Continue one finite46 with unchanged2m capacity, all learner/replay/RNG/history and original algorithm; no auxiliary weights or physics/reward/gate changes.',convergence_claim=False),indent=2)+'\n')
subprocess.run([str(B/'env/bin/python'),str(B/'runtime/launch_parameter_capacity46_20261026.py')],check=True)
