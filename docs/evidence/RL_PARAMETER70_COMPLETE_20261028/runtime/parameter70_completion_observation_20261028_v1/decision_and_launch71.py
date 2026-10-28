from pathlib import Path
import json,hashlib,time,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ref=lambda p:dict(path=str(p),sha256=sha(p))
for m in ['vmc','admittance']:
 p=B/f'runs/{m}70_terminal_anchor_followup_20261028_v1'
 assert read(p/'FINISHED.json')['completed'] and read(p/'SAVED_VALUES_REVIEW.json')['passed']
 obs=('Full2094 scatter viewed; total old SSE4074.470065->3907.730986 improves4.0923percent. Focus2050526 improves120.416201->22.919670; otherfour worsen. New30 contribution.344597 exceeds old2094 .195669. Several focus labels overlap near origin; exact values independently checked in saved JSON. No causal or convergence claim.' if m=='vmc' else 'Full2094 scatter viewed; total old SSE1244.926690->2183.538874 worsens75.3950percent. Original66short0600/index2752093 worsens55.213166->69.519956; new30 contribution.318841 exceeds old2094 .109326. Both improved and worsened rows retained, no causal or convergence claim.')
 (p/'PLOT_INSPECTION.json').write_text(json.dumps(dict(time=time.time(),actual_image_viewed=True,plot_sha256=sha(p/'follow70.png'),axes_and_data_readable=True,observations=obs,convergence_claim=False),indent=2)+'\n')
root=B/'runtime/prepare_parameter71_20261028_v1';out=B/'runs/parameter_capacity_pool30_cycle71_20261026_v1';old=read(B/'runtime/prepare_parameter70_20261028_v1/DECISION70.json')
evidence={}
for key,x in old['evidence'].items():
 assert sha(Path(x['path']))==x['sha256'];p=x['path']
 if key in ['parent_review','health','health_plot']:p=p.replace('cycle69','cycle70')
 elif key in ['loss','paired_gate','saved_loss','loss_plot']:p=p.replace('parameter69_loss','parameter70_loss')
 elif key=='check_only' or key.startswith('restore_'):p=p.replace('cycle70','cycle71')
 elif key in ['all_labels','all_labels_arithmetic','labels_finished']:
  p=p.replace('audit69_','audit70_').replace('COMPLETE68_69','COMPLETE69_70').replace('FINISHED69','FINISHED70')
 elif key.startswith('vmc_terminal') or key.startswith('admittance_terminal'):p=p.replace('69_terminal','70_terminal')
 if key=='future_window68_70':key='original_window68_70_plan'
 evidence[key]=ref(Path(p))
w=B/'runs/parameter_capacity68_70_reward_stability_20261028_v1'
for key,name in [('reward_window68_70','REVIEW.json'),('reward_window68_70_saved','SAVED_ARITHMETIC_REVIEW.json'),('reward_window68_70_plot','PLOT_INSPECTION.json')]:evidence[key]=ref(w/name)
evidence['future_window71_73']=ref(B/'runs/parameter_capacity71_73_reward_stability_20261028_v1/PLAN.json')
review=read(B/'runs/parameter_capacity_pool30_cycle70_review_20261026_v1/REVIEW.json');health=read(B/'runs/parameter_capacity_pool30_cycle70_review_20261026_v1/health/DIAGNOSIS.json')
assert review['passed'] and read(B/'runs/parameter_capacity_pool30_cycle70_review_20261026_v1/FINISHED.json')['completed']
assert read(B/'runs/parameter_capacity_pool30_cycle70_20261026_v1/ARCHIVE_REVIEW_FINISHED.json')['completed']
assert read(B/'runs/parameter70_loss_20261028_v1/SAVED_REVIEW.json')['passed']
assert read(B/'runs/parameter_task_label_audit70_20261028_v1/COMPLETE69_70_SAVED_REVIEW.json')['passed']
assert read(w/'SAVED_ARITHMETIC_REVIEW.json')['passed']
for m,r in review['methods'].items():
 assert r['new_transitions']==41250 and r['retained_replay_all_fields_exact'] and r['max_reward_reconstruction_error']==0 and r['optimizer_and_network_finite']
 assert r['full_horizon_count']==30 and r['aborts']==[] and health['methods'][m]['network_state_unchanged']
 assert r['checkpoint_sha256']==health['methods'][m]['checkpoint_sha256']
 ck=read(out/m/'check_only.log');assert ck['passed'] and ck['full_learner_state_unchanged'] and ck['exact_replay_and_next65536'] and ck['checkpoint_sha256']==r['checkpoint_sha256']
assert read(out/'CHECK_ONLY_COMPLETE.json')['passed'] and all(v==0 for v in read(out/'CHECK_ONLY_EXIT_CODES.json').values())
window=read(w/'REVIEW.json');assert not window['methods']['impedance']['descriptive_five_percent_check'] and not window['methods']['admittance']['descriptive_five_percent_check']
for key in ['health_plot','loss_plot','vmc_terminal_plot','admittance_terminal_plot','reward_window68_70_plot']:assert read(Path(evidence[key]['path']))['actual_image_viewed']
for j in read(B/'runs/parameter_capacity_pool30_cycle70_20261026_v1/LAUNCH.json')['jobs']:
 p=Path(f'/proc/{j["pid"]}/stat')
 if p.exists():
  f=p.read_text().rsplit(')',1)[1].split();assert f[19]!=j['proc_start_ticks'] or f[0]=='Z'
reason='Complete70 all3 naturally completed30x55s/41250new/noabort, all69 replay/history retained, all new reward reconstruction0, finite networks/optimizers and full41250 loss independently checked with actual plots. I/A/V reward-.570128980/-6.801950887/-4.596284873, TaskStrict18/18,16/15,17/16. Full180labels/90rewardpairs: A long0900 regainsTaskStrict while short0600 losesStrict at.203333mm; physical-valid30/29/29 of30, no Task-only omissions. Original68-70 complete independently reviewed: I nearzero guard and large68->69 change; A adjacent19.4496percent then.9014percent, endpoint20.1757percent fails; V adjacent.3573/.5249percent, endpoint.1695percent passes descriptive reward only. Overall reward not stable; complete70 late critic increases and finite maxima17.623672/25.071531/24.854301 retained. A/V actor drift; no overall convergence. Full2094 V old SSE4074.470065->3907.730986 improves4.0923percent but fourfocus worsen; focus2050526 improves120.416201->22.919670. A old SSE1244.926690->2183.538874 worsens75.395percent, original66short0600 55.213166->69.519956. New30 contributions.344597/.318841 exceed old.195669/.109326; all savedvalues/actualplots reviewed, no causal or zero-error criterion. Exact70 fullstate/replay/next65536 restore allpassed. Continue one unchanged finite71, with preregistered71-73 plan fixed before71; no automatic72. Keep all old failures/passes, markers23/47,4m append,terminal128,batch65536,UTD1,LR,masks,physics,gates; no resets or auxiliaryweights. Direct34false.'
d=dict(time=time.time(),passed=True,parent_cycle=70,new_cycle=71,new_cycles=1,plot_inspected=True,convergence_claim=False,evidence=evidence,reason=reason,automatic_followup=False,configuration_changed=False,direct34=False)
with (root/'DECISION71.json').open('x') as f:f.write(json.dumps(d,indent=2)+'\n')
print('Decision71',sha(root/'DECISION71.json'),'evidence',len(evidence),flush=True)
subprocess.run([str(B/'env/bin/python'),str(root/'launch_parameter71.py')],check=True)
