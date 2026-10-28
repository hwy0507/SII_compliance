from pathlib import Path
import json,time,hashlib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
r=B/'runs/parameter_capacity_pool30_cycle64_review_20261026_v1';loss=B/'runs/parameter64_loss_20261028_v1';term=B/'runs/vmc64_terminal_anchor_followup_20261028_v1';labels=B/'runs/parameter_task_label_audit64_20261028_v1';window=B/'runs/parameter_capacity62_64_reward_stability_20261028_v1';run=B/'runs/parameter_capacity_pool30_cycle65_20261026_v1';ranked=B/'runs/vmc64_ranked63_terminal_followup_20261028_v1'
assert read(r/'FINISHED.json')['completed'] and read(r/'REVIEW.json')['passed']
assert read(loss/'FINISHED.json')['completed'] and read(loss/'SAVED_REVIEW.json')['passed']
assert read(term/'FINISHED.json')['completed'] and read(term/'SAVED_VALUES_REVIEW.json')['passed']
assert read(labels/'FINISHED64.json')['completed'] and read(labels/'COMPLETE63_64_SAVED_REVIEW.json')['passed']
assert read(window/'REVIEW.json')['passed'] and read(window/'SAVED_ARITHMETIC_REVIEW.json')['passed']
assert read(ranked/'FINISHED.json')['completed'] and read(ranked/'SAVED_REVIEW.json')['passed']
assert read(OUT/'parameter_FINISHED.json')['prepared'] and read(run/'CHECK_ONLY_COMPLETE.json')['passed']
assert all(v==0 for v in read(run/'CHECK_ONLY_EXIT_CODES.json').values())
for p,field in [(loss,'actually_viewed'),(term,'actually_viewed'),(window,'actually_viewed'),(r/'health','actual_image_inspected')]:assert read(p/'PLOT_INSPECTION.json')[field]
for m,v in read(r/'REVIEW.json')['methods'].items():
 check=read(run/m/'check_only.log');assert check['passed'] and check['full_learner_state_unchanged'] and check['exact_replay_and_next65536'] and check['checkpoint_sha256']==v['checkpoint_sha256']
 assert v['new_transitions']==41250 and v['full_horizon_count']==30 and not v['aborts'] and v['optimizer_and_network_finite'] and v['retained_replay_all_fields_exact'] and v['max_reward_reconstruction_error']==0
 assert read(r/'health/DIAGNOSIS.json')['methods'][m]['network_state_unchanged']
paths=dict(parent_review=r/'REVIEW.json',health=r/'health/DIAGNOSIS.json',health_plot=r/'health/PLOT_INSPECTION.json',loss=loss/'REVIEW.json',paired_gate=loss/'PAIRED_GATE_REVIEW.json',saved_loss=loss/'SAVED_REVIEW.json',loss_plot=loss/'PLOT_INSPECTION.json',check_only=run/'CHECK_ONLY_COMPLETE.json',vmc_terminal=term/'REVIEW.json',vmc_terminal_arithmetic=term/'SAVED_VALUES_REVIEW.json',vmc_plot=term/'PLOT_INSPECTION.json',all_labels=labels/'COMPLETE63_64.json',all_labels_arithmetic=labels/'COMPLETE63_64_SAVED_REVIEW.json',reward_window62_64=window/'REVIEW.json',reward_window62_64_arithmetic=window/'SAVED_ARITHMETIC_REVIEW.json',reward_window62_64_plot=window/'PLOT_INSPECTION.json',future_window65_67=B/'runs/parameter_capacity65_67_reward_stability_20261028_v1/PLAN.json',ranked1914_followup=ranked/'REVIEW.json',ranked1914_arithmetic=ranked/'SAVED_REVIEW.json',ranked1914_plan=ranked/'PLAN.json')
# Keep original historic evidence and launcher-required compatibility binding.
for span in ['56_58','59_61']:
 w=B/f'runs/parameter_capacity{span}_reward_stability_20261028_v1'
 for suffix,name in [('', 'REVIEW.json'),('_arithmetic','SAVED_ARITHMETIC_REVIEW.json'),('_plot','PLOT_INSPECTION.json')]:paths[f'reward_window{span}{suffix}']=w/name
for m in ['impedance','admittance','vmc']:paths['restore_'+m]=run/m/'check_only.log'
reason='Complete64 each30x55/41250new/noabort, full63 replay/history/optimizer retained, reward reconstruction0, networks/optimizersfinite. I reward-.542027/18Task18Strict, A-8.512810/14/14 improve; V-4.607564/17/16 regresses asshort0600 penetration.223143mm losesStrict. Ishort0600 recoversStrict; Ashort0000/0900 recoverTask/Strict andshort0100 recoversStrict. All180 labels/90rewards independentlychecked, noTask-only omissions. ActorI continuesdown,A/Vrise; Vcriticdense lateburst/tail1.041694 versusfirst.741988; finite spikes are not a newthreshold. Original62-64 allfaildescriptive5percent: Inearzero, Aadjacent59.9168/37.9135percent andV38.0798/61.2875percent despite closeendpoints. Full1914 VfixedSSE9786.920510->6539.575075 decreases33.1805percent, but543rowsimprove/1371worsen, originalfocus2423122 .300759->1159.197633 worsens andnew30contribution.344211 increasesallterminalcontributionto.701903. Former63worsttwo improve2238.586046->57.427672 and2139.275917->3.492563, not general convergence. OriginalI56-58/V53-55 passes and59-61failures retained;65-67futurewindow registered beforetraining. Exact64fullstate/replay/next65536 checks passedall3. Continue one unchanged finite65; noauto66, noreset/auxweights/learnerconfigchanges, nozero-terminal-errorgate.'
d=dict(time=time.time(),passed=True,parent_cycle=64,new_cycle=65,new_cycles=1,plot_inspected=True,convergence_claim=False,evidence={k:ref(p) for k,p in paths.items()},reason=reason,automatic_followup=False,configuration_changed=False,direct34=False)
p=OUT/'DECISION65.json';assert not p.exists();p.write_text(json.dumps(d,indent=2)+'\n');print('Complete64 independently reviewed; DECISION65 bound',len(paths),'evidence files')
