from pathlib import Path
import json,time,hashlib,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/serl_take_cycle29_20261027_v1';P=B/'runs/serl_take_cycle28_review_20261027_v1';S=B/'runs/serl_take28_saved_review_20261027_v1/REVIEW.json';prep=B/'runs/serl_take29_preparation_20261027_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
r=read(P/'REVIEW.json');h=read(P/'DIAGNOSIS.json');saved=read(S);assert r['passed'] and read(P/'FINISHED.json')['completed'] and saved['passed']
assert h['network_optimizer_rng_unchanged'] and r['methods']['direct']['max_reward_reconstruction_error']==0 and r['methods']['direct']['retained_replay_all_fields_exact']
limit=time.monotonic()+600
while not (prep/'FINISHED.json').exists():
 assert time.monotonic()<limit,'Actual29 bounded restoration not ready'
 assert not (prep/'FAILURE.json').exists() and not (O/'CHECK_ONLY_FAILURE.json').exists()
 time.sleep(2)
assert read(prep/'FINISHED.json')['prepared'];c=read(O/'CHECK_ONLY_REVIEW.json');reg=read(O/'REGISTRATION.json')
assert c['passed'] and c['candidate_vs_original_three_batches_exact'] and c['full_replay_state_and_next_sample_exact'] and c['expanded_restore_next_batch_exact']
assert c['checkpoint_sha256']==r['methods']['direct']['checkpoint_sha256']==h['checkpoint_sha256']==saved['checkpoint_sha256']==reg['recovery_continuation_stage']['checkpoint']['sha256']
assert c['registration_sha256']==sha(O/'REGISTRATION.json') and c['old_pending_preserved']==930
assert reg['recovery_continuation_stage']['parent_cycle']==28 and reg['recovery_continuation_stage']['new_cycle']==29
assert not Path('/proc/1978250').exists() and not (O/'LAUNCH.json').exists()
refs=[P/'REVIEW.json',P/'DIAGNOSIS.json',P/'FINISHED.json',S,O/'CHECK_ONLY_REVIEW.json',prep/'MONITOR_TEMPLATE_REVIEW.json']
review=dict(passed=True,time=time.time(),registration_sha256=sha(O/'REGISTRATION.json'),monitor_template_review_sha256=sha(prep/'MONITOR_TEMPLATE_REVIEW.json'),checks=c,evidence_sha256={str(p):sha(p) for p in refs},parent_cycle=28,new_cycle=29,maximum_new_actions=41250,maximum_physical_substeps=33000000,auxiliary_weights_imported=False,plot_inspected=True,reason='Complete28 fullreview/health/saved arithmetic and plot inspected; all old raw/derived/history and930quarantine retained, reward0error and finite native state. Fixed27-29 remains incomplete; no healthy task convergence claim. Exact actual28 fullstate/three65536 batches/RNG/reload verified; one finite29 preserves original algorithm/physics.',convergence_claim=False)
(O/'PRELAUNCH_REVIEW.json').write_text(json.dumps(review,indent=2)+'\n')
subprocess.run([str(B/'env/bin/python'),str(prep/'launch.py')],check=True)
