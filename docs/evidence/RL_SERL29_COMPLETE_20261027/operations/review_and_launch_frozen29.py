"""Manual entry after exact complete29 checks/results have actually been inspected."""
from pathlib import Path
import json,hashlib,time,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/serl_take29_frozen_full30_20261027_v1';R=B/'runs/serl_take_cycle29_review_20261027_v1';S=B/'runs/serl_take29_saved_review_20261027_v1';W=B/'runs/serl_take27_29_reward_stability_20261027_v1';WS=B/'runs/serl27_29_stability_saved_review_20261027_v1'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
assert not (O/'LAUNCH.json').exists()
assert read(R/'FINISHED.json')['completed'] and read(R/'REVIEW.json')['passed'] and read(S/'REVIEW.json')['passed']
assert read(W/'REVIEW.json')['passed'] and read(WS/'REVIEW.json')['passed'] and read(WS/'REVIEW.json')['review_sha256']==sha(W/'REVIEW.json')
assert read(O/'CHECK_ONLY_COMPLETE.json')['passed'];check=read(O/'check_only/CHECK_ONLY_REVIEW.json')
assert check['passed'] and check['cycle']==29 and check['full_learner_state_exact'] and check['full_replay_state_exact'] and check['external_action_rng_gate']
for k in ['optimizer_updates','new_physics','replay_writes']:assert check[k]==0
rec=check['recovery_state'];assert rec['quarantined_pending']==930 and rec['original_pending_exact'] and rec['original_pending_raw_derived_exact'] and rec['pending_not_mature_or_sampleable'] and not rec['complete25_invented'] and rec['complete_cycles_after_recovery']==[26,27,28,29]
assert rec['original_interrupted_checkpoint_sha256']=='f765ef4a5b256097e3c17365ee4305088d943cbdcdb7447a3edbfbeb24eda6ca'
assert check['checkpoint_sha256']==read(R/'REVIEW.json')['methods']['direct']['checkpoint_sha256']==read(R/'DIAGNOSIS.json')['checkpoint_sha256']
plan=read(O/'PLAN.json');assert plan['action_seed']==2026102626 and plan['maximum_episodes']==30 and plan['maximum_actions']==41250 and plan['maximum_physical_substeps']==33000000
assert read(B/'runs/parameter41_frozen_full30_20261027_v1/REVIEW.json')['passed']
refs=[R/'REVIEW.json',R/'DIAGNOSIS.json',R/'FINISHED.json',S/'REVIEW.json',W/'REVIEW.json',WS/'REVIEW.json',O/'PLAN.json',O/'REGISTRATION.json',O/'CHECK_ONLY_COMPLETE.json',O/'check_only/CHECK_ONLY_REVIEW.json']
record=dict(passed=True,time=time.time(),cycle=29,plan_sha256=sha(O/'PLAN.json'),registration_sha256=sha(O/'REGISTRATION.json'),evidence_sha256={str(p):sha(p) for p in refs},plots_inspected=True,exact_complete29_restore_passed=True,quarantined_pending=930,optimizer_updates=0,replay_writes=0,convergence_claim=False,reason='Execute original prospective frozen29 full30 plan after complete29 fullreview, saved arithmetic, fixed27-29 diagnostics and exact recovery-aware restore; same original frozen16 action seed, all failures retained. Frozen41 finished. No auxiliary weights or learner changes.')
(O/'PRELAUNCH_REVIEW.json').write_text(json.dumps(record,indent=2)+'\n')
subprocess.run([str(B/'env/bin/python'),str(O/'launch.py')],check=True)
