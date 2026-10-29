from pathlib import Path
import json,hashlib,time,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=lambda p:dict(path=str(p),sha256=sha(p))
root=B/'runtime/prepare_parameter73_20261028_v1';out=B/'runs/parameter_capacity_pool30_cycle73_20261026_v1'
old=read(B/'runtime/prepare_parameter72_20261028_v1/DECISION72.json');evidence={}
for key,x in old['evidence'].items():
 assert sha(Path(x['path']))==x['sha256'];p=x['path']
 if key in ['parent_review','health','health_plot']:p=p.replace('cycle71','cycle72')
 elif key in ['loss','paired_gate','saved_loss','loss_plot']:p=p.replace('parameter71_loss','parameter72_loss')
 elif key=='check_only' or key.startswith('restore_'):p=p.replace('cycle72','cycle73')
 elif key in ['all_labels','all_labels_arithmetic','labels_finished']:
  p=p.replace('audit71_','audit72_').replace('COMPLETE70_71','COMPLETE71_72').replace('FINISHED71','FINISHED72')
 elif key.startswith('vmc_terminal') or key.startswith('admittance_terminal'):p=p.replace('71_terminal','72_terminal')
 evidence[key]=ref(Path(p))
evidence['original68_70_bootstrap_independent']=ref(B/'runtime/parameter68_70_bootstrap_independent_20261028_v1/REVIEW.json')
assert read(Path(evidence['original68_70_bootstrap_independent']['path']))['passed']
assert read(Path(evidence['current_window71_73_plan']['path']))['cycles']==[71,72,73]
parent=B/'runs/parameter_capacity_pool30_cycle72_20261026_v1';reviewroot=B/'runs/parameter_capacity_pool30_cycle72_review_20261026_v1'
review=read(reviewroot/'REVIEW.json');health=read(reviewroot/'health/DIAGNOSIS.json')
assert review['passed'] and read(reviewroot/'FINISHED.json')['completed']
assert read(parent/'ARCHIVE_REVIEW_FINISHED.json')['completed']
assert read(B/'runs/parameter72_loss_20261028_v1/SAVED_REVIEW.json')['passed']
assert read(B/'runs/parameter_task_label_audit72_20261028_v1/COMPLETE71_72_SAVED_REVIEW.json')['passed']
for m,r in review['methods'].items():
 assert r['new_transitions']==41250 and r['retained_replay_all_fields_exact'] and r['max_reward_reconstruction_error']==0 and r['optimizer_and_network_finite']
 assert r['full_horizon_count']==30 and r['aborts']==[] and health['methods'][m]['network_state_unchanged']
 assert r['checkpoint_sha256']==health['methods'][m]['checkpoint_sha256']
 ck=read(out/m/'check_only.log');assert ck['passed'] and ck['full_learner_state_unchanged'] and ck['exact_replay_and_next65536'] and ck['checkpoint_sha256']==r['checkpoint_sha256']
assert read(out/'CHECK_ONLY_COMPLETE.json')['passed'] and all(v==0 for v in read(out/'CHECK_ONLY_EXIT_CODES.json').values())
for m in ['vmc','admittance']:
 p=B/f'runs/{m}72_terminal_anchor_followup_20261028_v1'
 assert read(p/'FINISHED.json')['completed'] and read(p/'SAVED_VALUES_REVIEW.json')['passed']
 assert read(p/'REVIEW.json')['fixed_anchor_rows']==2154 and read(p/'REVIEW.json')['new_terminal_rows']==30
for key in ['health_plot','loss_plot','vmc_terminal_plot','admittance_terminal_plot','reward_window68_70_plot']:
 assert read(Path(evidence[key]['path']))['actual_image_viewed']
for j in read(parent/'LAUNCH.json')['jobs']:
 p=Path(f'/proc/{j["pid"]}/stat')
 if p.exists():
  f=p.read_text().rsplit(')',1)[1].split();assert f[19]!=j['proc_start_ticks'] or f[0]=='Z'
reason_path=B/'runtime/parameter72_completion_observation_driver_20261028_v1/CONTINUATION_REASON.txt'
reason=reason_path.read_text().strip();assert len(reason)>100
evidence['continuation_reason']=ref(reason_path)
d=dict(time=time.time(),passed=True,parent_cycle=72,new_cycle=73,new_cycles=1,plot_inspected=True,convergence_claim=False,evidence=evidence,reason=reason,automatic_followup=False,configuration_changed=False,direct34=False)
with (root/'DECISION73.json').open('x') as f:f.write(json.dumps(d,indent=2)+'\n')
print('Decision73',sha(root/'DECISION73.json'),'evidence',len(evidence),flush=True)
subprocess.run([str(B/'env/bin/python'),str(root/'launch_parameter73.py')],check=True)
