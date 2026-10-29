from pathlib import Path
import ast,json,hashlib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');P=B/'runtime/parameter75_loss_preparation_20261029_v1';W=B/'runs/parameter_capacity74_76_reward_stability_20261029_v1';OLD=B/'runs/parameter_capacity71_73_reward_stability_20261028_v1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['SOURCE_REVIEW.json','DEPLOY_SOURCE_REVIEW.json']:
 for item in read(P/name)['files']:
  assert sha(P/item['name'])==item['sha256'] and sha(Path(item['parent']))==item['parent_sha256'];ast.parse((P/item['name']).read_text())
t=ast.parse((P/'audit.py').read_text());hist=[ast.literal_eval(n.iter) for n in ast.walk(t) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='cycle' and isinstance(n.iter,ast.List)];assert hist==[list(range(49,76))],hist
s=(P/'review_saved.py').read_text();assert 'for c in [74,75]' in s and "v['reward74']" in s and "v['reward75']" in s
s=(P/'deploy.py').read_text()
for key in ['parameter_capacity65_67','parameter_capacity68_70','parameter_capacity71_73','parameter_capacity74_76','prepare_parameter75_20261029_v1','COMPLETE73_74','parameter74_loss_20261028_v1','parameter75_loss_20261028_v1']:assert key in s,key
assert "assert read(current_plan_path)['cycles']" not in s
assert "current_plan['cycles'] == [71, 72, 73]" in s
assert "assert read(future_plan_path)['cycles'] == [74, 75, 76]" in s
assert "read(original_window / 'SAVED_ARITHMETIC_REVIEW.json')['passed']" in s
assert "read(original_window / 'PLOT_INSPECTION.json')['actual_image_viewed']" in s
assert 'parameter_capacity74_76_reward_stability_20261029_v1/REVIEW.json' not in s
assert sha(W/'PLAN.json')=='d8c243d979f43520e34036b5ce7dfb1b5f5712b5e4091dc09f4dacfdb5061703'
assert sha(OLD/'PLAN.json')=='c160b5d6032abaea7ea81c1fb0a2a8151f4fd929d81044a830740343fc572bdf'
assert read(OLD/'SAVED_ARITHMETIC_REVIEW.json')['passed'] and read(OLD/'PLOT_INSPECTION.json')['actual_image_viewed']
assert read(P/'UNREVIEWED_DEPLOY_REJECTION.json')['passed']
assert not (B/'runtime/prepare_parameter75_20261029_v1/DECISION75.json').exists() and not (B/'runs/parameter75_loss_20261028_v1').exists()
assert not (B/'runs/parameter_capacity_pool30_cycle75_20261026_v1/LAUNCH.json').exists()
j=read(W/'LAUNCH.json');f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
r=dict(time=time.time(),passed=True,history_cycles=hist[0],paired_cycles=[74,75],parent_and_prepared_hashes_exact=True,all_ast_valid=True,original_windows_retained=True,original71_73_plan_sha256=sha(OLD/'PLAN.json'),current74_76_plan_sha256=sha(W/'PLAN.json'),future74_76_results_not_required=True,formula_threshold_seed_bootstrap_anchor55_unchanged=True,no75_training_or_loss_run=True,original74_76_waiter_live=j,source_sha256=sha(Path(__file__)),limitation='Static preparation and actual missing-decision rejection; deployment requires full74 review, exact restore, original71-73 complete review, original74-76 PLAN and actual75 launch.')
(P/'INDEPENDENT_STATIC_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
