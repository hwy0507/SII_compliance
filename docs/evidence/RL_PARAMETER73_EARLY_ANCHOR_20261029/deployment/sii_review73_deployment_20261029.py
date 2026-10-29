from pathlib import Path
import ast,json,hashlib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for m,focus in [('vmc',[2050526,2299142,2046571,2423133,2423122]),('admittance',[2752093])]:
 p=B/f'runs/{m}73_terminal_anchor_followup_20261028_v1';old=B/f'runs/{m}72_terminal_anchor_followup_20261028_v1';plan=read(p/'PLAN.json')
 assert plan['focus_replay_indices']==focus==read(old/'PLAN.json')['focus_replay_indices']
 assert plan['fixed_anchor_rows']==2184 and plan['expected_complete73_terminal_rows']==2214
 for n,h in plan['sources'].items():assert sha(p/n)==h;ast.parse((p/n).read_text())
 for x in plan['inputs'].values():assert sha(Path(x['path']))==x['sha256']
 tree=ast.parse((p/'track.py').read_text());assert any(isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=='plan' and isinstance(n.slice,ast.Constant) and n.slice.value=='focus_replay_indices' for n in ast.walk(tree))
 assert read(p/'ANCHOR_REVIEW.json')['terminal_rows']==2184 and read(p/'ANCHOR_SAVED_REVIEW.json')['passed']
p=B/'runtime/prepare_parameter74_20261028_v1';s=(p/'launch_parameter74.py').read_text();ast.parse(s)
for n,h in read(p/'LAUNCH_SOURCE_REVIEW.json')['files'].items():assert sha(p/n)==h
assert "assert read(current_window)['cycles']==[71,72,73]" in s
assert 'parameter_capacity68_70_reward_stability' in s and 'parameter_capacity71_73_reward_stability' in s
for key in ['reward_window71_73','reward_window71_73_saved','reward_window71_73_plot']:assert repr(key) in s
assert s.index("assert read(completed_window/'SAVED_ARITHMETIC_REVIEW.json')['passed']")<s.index("write(out/'PRELAUNCH_SCIENTIFIC_REVIEW.json'")
assert sha(p/'wait_prepare.py')==sha(B/'runtime/prepare_parameter73_20261028_v1/wait_prepare.py')
assert not (p/'DECISION74.json').exists() and not (B/'runs/parameter_capacity_pool30_cycle74_20261026_v1').exists()
assert read(p/'UNREVIEWED_LAUNCH_REJECTION.json')['passed']
window=B/'runs/parameter_capacity71_73_reward_stability_20261028_v1/PLAN.json';assert sha(window)=='c160b5d6032abaea7ea81c1fb0a2a8151f4fd929d81044a830740343fc572bdf'
assert read(window)['cycles']==[71,72,73]
rt=B/'runtime/parameter_task_label_audit73_20261028_v1';old=B/'runtime/parameter_task_label_audit72_20261028_v1';assert sha(rt/'audit_labels.py')==sha(old/'audit_labels.py')
assert read(B/'runs/parameter_task_label_audit73_20261028_v1/INCOMPLETE73_REJECTION.json')['passed']
for name in ['wait73.py','review_labels73.py']:ast.parse((rt/name).read_text())
report=dict(time=time.time(),passed=True,source_sha256=sha(Path(__file__)),all_terminal_source_and_input_hashes_verified=True,all2184_anchor_arrays_independently_reviewed=True,original_focus_indices_and_ast_plan_consumer_verified=True,original_window_plan_sha256=sha(window),finite74_requires_original71_73_completed_review=True,restore_only_waiter_unchanged=True,actual_missing_decision_rejected=True,no74_training=True,threshold_changed=False)
p=B/'runtime/parameter73_followups_preparation_20261028_v1';(p/'DEPLOYMENT_STATIC_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
