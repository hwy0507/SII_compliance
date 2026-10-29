from pathlib import Path
import json,hashlib,time,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=lambda p:dict(path=str(p),sha256=sha(p))
root=B/'runtime/prepare_parameter75_20261029_v1';out=B/'runs/parameter_capacity_pool30_cycle75_20261026_v1'
old=read(B/'runtime/prepare_parameter74_20261028_v1/DECISION74.json');evidence={}
for key,x in old['evidence'].items():
 assert sha(Path(x['path']))==x['sha256'];p=x['path']
 if key in ['parent_review','health','health_plot']:p=p.replace('cycle73','cycle74')
 elif key in ['loss','paired_gate','saved_loss','loss_plot']:p=p.replace('parameter73_loss','parameter74_loss')
 elif key=='check_only' or key.startswith('restore_'):p=p.replace('cycle74','cycle75')
 elif key in ['all_labels','all_labels_arithmetic','labels_finished']:
  p=p.replace('audit73_','audit74_').replace('COMPLETE72_73','COMPLETE73_74').replace('FINISHED73','FINISHED74')
 elif key.startswith('vmc_terminal') or key.startswith('admittance_terminal'):p=p.replace('73_terminal','74_terminal')
 if key=='continuation_reason':continue
 evidence[key]=ref(Path(p))
evidence['original68_70_bootstrap_independent']=ref(B/'runtime/parameter68_70_bootstrap_independent_20261028_v1/REVIEW.json')
assert read(Path(evidence['original68_70_bootstrap_independent']['path']))['passed']
assert read(Path(evidence['current_window71_73_plan']['path']))['cycles']==[71,72,73]
window=B/'runs/parameter_capacity71_73_reward_stability_20261028_v1'
for key,name in [('reward_window71_73','REVIEW.json'),('reward_window71_73_saved','SAVED_ARITHMETIC_REVIEW.json'),('reward_window71_73_plot','PLOT_INSPECTION.json')]:evidence[key]=ref(window/name)
assert read(window/'SAVED_ARITHMETIC_REVIEW.json')['passed'] and read(window/'PLOT_INSPECTION.json')['actual_image_viewed']
evidence['original71_73_bootstrap_independent']=ref(B/'runtime/parameter71_73_bootstrap_independent_20261029_v1/REVIEW.json')
assert read(Path(evidence['original71_73_bootstrap_independent']['path']))['passed']
future=B/'runs/parameter_capacity74_76_reward_stability_20261029_v1/PLAN.json'
assert sha(future)=='d8c243d979f43520e34036b5ce7dfb1b5f5712b5e4091dc09f4dacfdb5061703' and read(future)['cycles']==[74,75,76]
evidence['future_window74_76_plan']=ref(future)
parent=B/'runs/parameter_capacity_pool30_cycle74_20261026_v1';reviewroot=B/'runs/parameter_capacity_pool30_cycle74_review_20261026_v1'
review=read(reviewroot/'REVIEW.json');health=read(reviewroot/'health/DIAGNOSIS.json')
assert review['passed'] and read(reviewroot/'FINISHED.json')['completed']
assert read(parent/'ARCHIVE_REVIEW_FINISHED.json')['completed']
assert read(B/'runs/parameter74_loss_20261028_v1/SAVED_REVIEW.json')['passed']
assert read(B/'runs/parameter_task_label_audit74_20261028_v1/COMPLETE73_74_SAVED_REVIEW.json')['passed']
for m,r in review['methods'].items():
 assert r['new_transitions']==41250 and r['retained_replay_all_fields_exact'] and r['max_reward_reconstruction_error']==0 and r['optimizer_and_network_finite']
 assert r['full_horizon_count']==30 and r['aborts']==[] and health['methods'][m]['network_state_unchanged']
 assert r['checkpoint_sha256']==health['methods'][m]['checkpoint_sha256']
 ck=read(out/m/'check_only.log');assert ck['passed'] and ck['full_learner_state_unchanged'] and ck['exact_replay_and_next65536'] and ck['checkpoint_sha256']==r['checkpoint_sha256']
assert read(out/'CHECK_ONLY_COMPLETE.json')['passed'] and all(v==0 for v in read(out/'CHECK_ONLY_EXIT_CODES.json').values())
for m in ['vmc','admittance']:
 p=B/f'runs/{m}74_terminal_anchor_followup_20261028_v1'
 assert read(p/'FINISHED.json')['completed'] and read(p/'SAVED_VALUES_REVIEW.json')['passed']
 assert read(p/'REVIEW.json')['fixed_anchor_rows']==2214 and read(p/'REVIEW.json')['new_terminal_rows']==30
for key in ['health_plot','loss_plot','vmc_terminal_plot','admittance_terminal_plot','reward_window68_70_plot']:
 assert read(Path(evidence[key]['path']))['actual_image_viewed']
for j in read(parent/'LAUNCH.json')['jobs']:
 p=Path(f'/proc/{j["pid"]}/stat')
 if p.exists():
  f=p.read_text().rsplit(')',1)[1].split();assert f[19]!=j['proc_start_ticks'] or f[0]=='Z'
reason_path=B/'runtime/parameter74_completion_preparation_20261029_v1/CONTINUATION_REASON.txt'
reason=reason_path.read_text().strip();assert len(reason)>100
evidence['continuation_reason']=ref(reason_path)
d=dict(time=time.time(),passed=True,parent_cycle=74,new_cycle=75,new_cycles=1,plot_inspected=True,convergence_claim=False,evidence=evidence,reason=reason,automatic_followup=False,configuration_changed=False,direct34=False)
with (root/'DECISION75.json').open('x') as f:f.write(json.dumps(d,indent=2)+'\n')
print('Decision75',sha(root/'DECISION75.json'),'evidence',len(evidence),flush=True)
subprocess.run([str(B/'env/bin/python'),str(root/'launch_parameter75.py')],check=True)
