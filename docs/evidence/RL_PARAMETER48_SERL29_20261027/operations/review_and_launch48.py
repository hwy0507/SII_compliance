from pathlib import Path
import json,time,hashlib,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/parameter_capacity_pool30_cycle48_20261026_v1';P=B/'runs/parameter_capacity_pool30_cycle47_review_20261026_v1';S=B/'runs/parameter47_saved_review_20261027_v1/REVIEW.json'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
stability=B/'runs/parameter43_45_stability_saved_review_20261027_v1/REVIEW.json';assert json.loads(stability.read_text())['passed']
r=json.loads((P/'REVIEW.json').read_text());h=json.loads((P/'health/DIAGNOSIS.json').read_text());saved=json.loads(S.read_text());assert r['passed'] and saved['passed']
assert json.loads((P/'FINISHED.json').read_text())['completed']
limit=time.monotonic()+180
while not (O/'CHECK_ONLY_COMPLETE.json').exists():
 assert time.monotonic()<limit,'Actual48 checks not ready within bounded launch observation'
 if (O/'CHECK_ONLY_EXIT_CODES.json').exists():assert all(v==0 for v in json.loads((O/'CHECK_ONLY_EXIT_CODES.json').read_text()).values())
 time.sleep(2)
assert json.loads((O/'CHECK_ONLY_COMPLETE.json').read_text())['passed'];checks={}
import sys
sys.path.insert(0,str(B/'runtime'/O.name))
from parameter_replay_capacity4m_20261027 import MARKER as FOLLOWUP_MARKER
for m in ['impedance','admittance','vmc']:
 c=json.loads((O/m/'check_only.log').read_text().splitlines()[-1]);a=r['methods'][m];health=h['methods'][m]
 assert c['passed'] and c['full_learner_state_unchanged'] and c['exact_replay_and_next65536']
 assert c['checkpoint_sha256']==a['checkpoint_sha256']==health['checkpoint_sha256']==saved['methods'][m]['checkpoint_sha256']
 assert health['network_state_unchanged'] and a['optimizer_and_network_finite'] and a['retained_replay_all_fields_exact'] and a['max_reward_reconstruction_error']==0
 reg=json.loads((O/m/'REGISTRATION.json').read_text());previous=json.loads(Path(reg['resume_parent_registration']['path']).read_text())
 assert c['replay_capacity_followup']==FOLLOWUP_MARKER==reg['replay_capacity_followup_stage']['marker']
 assert reg['replay_capacity_followup_stage']['parent_cycle']==47 and reg['replay_capacity_followup_stage']['entry_checkpoint']['sha256']==a['checkpoint_sha256']
 assert reg['replay_capacity_stage']==previous['replay_capacity_stage'] and reg['replay_capacity_stage']['parent_cycle']==23
 baseline=previous['batch_size_stage']['dependency_hashes'];deps=reg['batch_size_stage']['dependency_hashes']
 assert set(deps)-set(baseline)=={'parameter_replay_capacity4m_20261027.py','resume_cheq_capacity4m_pool30_20261027.py'} and all(deps[k]==v for k,v in baseline.items())
 checks[m]=c
refs=[P/'REVIEW.json',P/'health/DIAGNOSIS.json',S,O/'CHECK_ONLY_COMPLETE.json',O/'SCIENTIFIC_DECISION.json',stability]
assert not (O/'LAUNCH.json').exists()
(O/'PRELAUNCH_SCIENTIFIC_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),parent_cycle=47,new_cycle=48,new_cycles=1,capacity_before=2000000,capacity_after=4000000,historical_entry_cycle=23,actual_crossing_not_yet_observed=True,maximum_new_actions_per_method=41250,checks=checks,evidence_sha256={str(p):sha(p) for p in refs},plot_inspected=True,reason='Complete47 fullstate/next65536 verified; fullreview/health/saved arithmetic inspected. Fixed43-45 failed and prospective46-48 is still pending; no joint healthy convergence claim. Continue one finite48 with registered2m-to4m append capacity expansion, retaining originalentry23 and both markers, all learner/replay/RNG/history and original algorithm; no auxiliary weights or physics/reward/gate changes.',convergence_claim=False),indent=2)+'\n')
subprocess.run([str(B/'env/bin/python'),str(B/'runs/parameter48_static_preparation_20261027_v1/launch.py')],check=True)
