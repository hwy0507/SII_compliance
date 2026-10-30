from pathlib import Path
import ast,json,hashlib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=B/'runtime/parameter75_followups_preparation_20261029_v1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for m,focus in [('vmc',[2050526,2299142,2046571,2423133,2423122]),('admittance',[2752093])]:
 p=B/f'runs/{m}75_terminal_anchor_followup_20261028_v1';old=B/f'runs/{m}74_terminal_anchor_followup_20261028_v1';plan=read(p/'PLAN.json')
 assert plan['focus_replay_indices']==focus==read(old/'PLAN.json')['focus_replay_indices']
 assert plan['fixed_anchor_rows']==2244 and plan['expected_complete75_terminal_rows']==2274
 for n,h in plan['sources'].items():assert sha(p/n)==h;ast.parse((p/n).read_text())
 for x in plan['inputs'].values():assert sha(Path(x['path']))==x['sha256']
 tree=ast.parse((p/'track.py').read_text());assert any(isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=='plan' and isinstance(n.slice,ast.Constant) and n.slice.value=='focus_replay_indices' for n in ast.walk(tree))
 assert read(p/'ANCHOR_REVIEW.json')['terminal_rows']==2244 and read(p/'ANCHOR_SAVED_REVIEW.json')['passed']
p=B/'runtime/prepare_parameter76_20261029_v1';s=(p/'launch_parameter76.py').read_text();ast.parse(s)
for item in read(p/'SOURCE_REVIEW.json')['files']:
 assert sha(p/item['name'])==item['sha256'] and sha(Path(item['parent']))==item['parent_sha256'];ast.parse((p/item['name']).read_text())
for n,h in read(p/'LAUNCH_SOURCE_REVIEW.json')['files'].items():assert sha(p/n)==h
for term in ["assert read(current_window)['cycles']==[71,72,73]",'parameter_capacity68_70_reward_stability','parameter_capacity71_73_reward_stability',"['cycles']==[74,75,76]",'future_window74_76_plan']:
 assert term in s
for key in ['reward_window71_73','reward_window71_73_saved','reward_window71_73_plot']:assert repr(key) in s
assert s.index("assert read(completed_window/'SAVED_ARITHMETIC_REVIEW.json')['passed']")<s.index("write(out/'PRELAUNCH_SCIENTIFIC_REVIEW.json'")
assert sha(p/'wait_prepare.py')==sha(B/'runtime/prepare_parameter75_20261029_v1/wait_prepare.py')
assert not (p/'DECISION76.json').exists() and not (B/'runs/parameter_capacity_pool30_cycle76_20261026_v1').exists()
assert read(p/'UNREVIEWED_LAUNCH_REJECTION.json')['passed']
window=B/'runs/parameter_capacity74_76_reward_stability_20261029_v1/PLAN.json';assert sha(window)=='d8c243d979f43520e34036b5ce7dfb1b5f5712b5e4091dc09f4dacfdb5061703';assert read(window)['cycles']==[74,75,76]
original=B/'runs/parameter_capacity71_73_reward_stability_20261028_v1';assert sha(original/'PLAN.json')=='c160b5d6032abaea7ea81c1fb0a2a8151f4fd929d81044a830740343fc572bdf';assert read(original/'SAVED_ARITHMETIC_REVIEW.json')['passed'] and read(original/'PLOT_INSPECTION.json')['actual_image_viewed']
rt=B/'runtime/parameter_task_label_audit75_20261028_v1';old=B/'runtime/parameter_task_label_audit74_20261028_v1';assert sha(rt/'audit_labels.py')==sha(old/'audit_labels.py')
assert read(B/'runs/parameter_task_label_audit75_20261028_v1/INCOMPLETE75_REJECTION.json')['passed']
for n in ['wait75.py','review_labels75.py']:ast.parse((rt/n).read_text())
report=dict(time=time.time(),passed=True,source_sha256=sha(Path(__file__)),all_terminal_source_and_input_hashes_verified=True,all2244_anchor_arrays_independently_reviewed=True,original_focus_indices_and_ast_plan_consumer_verified=True,original_window_plan_sha256=sha(original/'PLAN.json'),current_window_plan_sha256=sha(window),finite76_requires_original71_73_completed_review_and_original74_76_plan=True,future_window_results_required=False,restore_only_waiter_unchanged=True,actual_missing_decision_rejected=True,no76_training=True,threshold_changed=False)
(D/'DEPLOYMENT_STATIC_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
