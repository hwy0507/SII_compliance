"""Manually invoke only after inspecting complete48 and the fixed46-48 plots/results."""
from pathlib import Path
import json,time,hashlib,subprocess,sys
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/parameter_capacity_pool30_cycle49_20261026_v1';P=B/'runs/parameter_capacity_pool30_cycle48_review_20261026_v1';S=B/'runs/parameter48_saved_review_20261027_v1/REVIEW.json'
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
W=B/'runs/parameter_capacity46_48_reward_stability_20261027_v1';WS=B/'runs/parameter46_48_stability_saved_review_20261027_v1/REVIEW.json';boundary=B/'runs/parameter48_boundary_preparation_20261027_v1/evidence/REVIEW.json'
r=read(P/'REVIEW.json');health=read(P/'health/DIAGNOSIS.json');saved=read(S);assert r['passed'] and saved['passed'] and read(P/'FINISHED.json')['completed']
stat=read(W/'REVIEW.json');ss=read(WS);assert stat['passed'] and ss['passed'] and ss['review_sha256']==sha(W/'REVIEW.json')
assert any(not v['descriptive_five_percent_check'] for v in stat['methods'].values()),'Reward window passes for all methods; reassess health/frozen requirements before further training'
br=read(boundary);assert br['passed'] and all(v['boundary_observed'] for v in br['methods'].values())
assert read(O/'CHECK_ONLY_COMPLETE.json')['passed'] and read(B/'runs/parameter49_preparation_20261027_v1/FINISHED.json')['passed']
sys.path.insert(0,str(B/'runtime'/O.name));from parameter_replay_capacity4m_20261027 import MARKER
checks={}
for m in ['impedance','admittance','vmc']:
 c=json.loads((O/m/'check_only.log').read_text().splitlines()[-1]);a=r['methods'][m];h=health['methods'][m]
 assert c['passed'] and c['full_learner_state_unchanged'] and c['exact_replay_and_next65536']
 assert c['checkpoint_sha256']==a['checkpoint_sha256']==h['checkpoint_sha256']==saved['methods'][m]['checkpoint_sha256']
 assert h['network_state_unchanged'] and a['optimizer_and_network_finite'] and a['retained_replay_all_fields_exact'] and a['max_reward_reconstruction_error']==0
 assert a['current_replay_capacity']==4000000 and a['replay_capacity_followup']==MARKER
 reg=read(O/m/'REGISTRATION.json');previous=read(Path(reg['resume_parent_registration']['path']))
 assert reg['batch_size_stage']['parent_cycle']==48 and reg['batch_size_stage']['checkpoint']['sha256']==a['checkpoint_sha256']
 assert reg['replay_capacity_stage']==previous['replay_capacity_stage'] and reg['replay_capacity_stage']['parent_cycle']==23
 assert reg['replay_capacity_followup_stage']==previous['replay_capacity_followup_stage'] and reg['replay_capacity_followup_stage']['parent_cycle']==47
 assert reg['batch_size_stage']['dependency_hashes']==previous['batch_size_stage']['dependency_hashes'] and c['replay_capacity_followup']==MARKER
 checks[m]=c
assert not (O/'LAUNCH.json').exists()
refs=[P/'REVIEW.json',P/'health/DIAGNOSIS.json',P/'FINISHED.json',S,O/'CHECK_ONLY_COMPLETE.json',O/'SCIENTIFIC_DECISION.json',W/'REVIEW.json',WS,boundary]
record=dict(passed=True,time=time.time(),parent_cycle=48,new_cycle=49,new_cycles=1,capacity_before=4000000,capacity_after=4000000,historical_entries=[23,47],checks=checks,evidence_sha256={str(p):sha(p) for p in refs},plot_inspected=True,reason='Complete48 fullreview/health/saved arithmetic and fixed46-48 window reviewed; not all methods pass the original reward stability check. Exact48 fullstate/next65536 restored, real48 second-capacity crossing verified. Continue one finite49 preserving4m append replay, historicalentry23/47, original learner/physics/gates and all state; no auxiliary weights.',convergence_claim=False)
(O/'PRELAUNCH_SCIENTIFIC_REVIEW.json').write_text(json.dumps(record,indent=2)+'\n')
subprocess.run([str(B/'env/bin/python'),str(B/'runs/parameter49_preparation_20261027_v1/launch.py')],check=True)
