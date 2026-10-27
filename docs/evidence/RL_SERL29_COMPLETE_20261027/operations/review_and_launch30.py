from pathlib import Path
import json,time,hashlib,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/serl_take_cycle30_20261027_v1';P=B/'runs/serl_take_cycle29_review_20261027_v1';S=B/'runs/serl_take29_saved_review_20261027_v1/REVIEW.json';prep=B/'runs/serl_take30_preparation_20261027_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
r=read(P/'REVIEW.json');h=read(P/'DIAGNOSIS.json');saved=read(S);assert r['passed'] and read(P/'FINISHED.json')['completed'] and saved['passed']
assert h['network_optimizer_rng_unchanged'] and r['methods']['direct']['max_reward_reconstruction_error']==0 and r['methods']['direct']['retained_replay_all_fields_exact']
limit=time.monotonic()+600
while not (prep/'FINISHED.json').exists():
 assert time.monotonic()<limit,'Actual30 bounded restoration not ready'
 assert not (prep/'FAILURE.json').exists() and not (O/'CHECK_ONLY_FAILURE.json').exists()
 time.sleep(2)
assert read(prep/'FINISHED.json')['prepared'];c=read(O/'CHECK_ONLY_REVIEW.json');reg=read(O/'REGISTRATION.json')
assert c['passed'] and c['candidate_vs_original_three_batches_exact'] and c['full_replay_state_and_next_sample_exact'] and c['expanded_restore_next_batch_exact']
assert c['checkpoint_sha256']==r['methods']['direct']['checkpoint_sha256']==h['checkpoint_sha256']==saved['checkpoint_sha256']==reg['recovery_continuation_stage']['checkpoint']['sha256']
assert c['registration_sha256']==sha(O/'REGISTRATION.json') and c['old_pending_preserved']==930
assert reg['recovery_continuation_stage']['parent_cycle']==29 and reg['recovery_continuation_stage']['new_cycle']==30
assert not Path('/proc/241542').exists() and not (O/'LAUNCH.json').exists()
refs=[P/'REVIEW.json',P/'DIAGNOSIS.json',P/'FINISHED.json',S,O/'CHECK_ONLY_REVIEW.json',prep/'MONITOR_TEMPLATE_REVIEW.json']
W=B/'runs/serl_take27_29_reward_stability_20261027_v1';WS=B/'runs/serl27_29_stability_saved_review_20261027_v1/REVIEW.json';F=B/'runs/serl_take29_frozen_full30_20261027_v1'
w=read(W/'REVIEW.json');ws=read(WS);assert w['passed'] and ws['passed'] and ws['five_percent'] and ws['review_sha256']==sha(W/'REVIEW.json')
assert read(F/'PRELAUNCH_REVIEW.json')['passed'] and read(F/'CHECK_ONLY_COMPLETE.json')['passed']
for j in read(F/'LAUNCH.json')['jobs']:
 p=Path(f"/proc/{j['pid']}");assert p.exists() and p.joinpath('stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
refs += [W/'REVIEW.json',WS,F/'PRELAUNCH_REVIEW.json',F/'LAUNCH.json',B/'runs/serl29_saved_history_20261027_v1/REVIEW.json']
review=dict(passed=True,time=time.time(),registration_sha256=sha(O/'REGISTRATION.json'),monitor_template_review_sha256=sha(prep/'MONITOR_TEMPLATE_REVIEW.json'),checks=c,evidence_sha256={str(p):sha(p) for p in refs},parent_cycle=29,new_cycle=30,maximum_new_actions=41250,maximum_physical_substeps=33000000,auxiliary_weights_imported=False,plot_inspected=True,original27_29_five_percent_passed=True,healthy_loss_no_divergence_observed=True,additional_task_success_threshold=False,automatic_followup=False,reason='Complete29 fullreview/health/saved arithmetic and both plots inspected; original27-29 reward stability passes and critic loss shows no divergence. Preserve that result. Frozen29 is running independently at the original fixed checkpoint/seed. Continue one finite30 to observe persistence of the plateau while temperature still evolves and the other methods continue; this is bounded additional training evidence, not a new mandatory convergence threshold or a Task-success requirement. Exact actual29 fullstate/three65536 batches/RNG/reload and930quarantine verified; original algorithm/physics and all history unchanged.',convergence_claim=False)
(O/'PRELAUNCH_REVIEW.json').write_text(json.dumps(review,indent=2)+'\n')
subprocess.run([str(B/'env/bin/python'),str(prep/'launch.py')],check=True)
