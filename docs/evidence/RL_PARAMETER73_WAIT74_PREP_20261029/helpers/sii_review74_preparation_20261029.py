from pathlib import Path
import ast,json,hashlib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');P=B/'runtime/parameter74_loss_preparation_20261029_v1';W=B/'runs/parameter_capacity74_76_reward_stability_20261029_v1';OLD=B/'runs/parameter_capacity71_73_reward_stability_20261028_v1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for review in ['SOURCE_REVIEW.json','DEPLOY_SOURCE_REVIEW.json']:
 for item in read(P/review)['files']:
  assert sha(P/item['name'])==item['sha256'] and sha(Path(item['parent']))==item['parent_sha256'];ast.parse((P/item['name']).read_text())
t=ast.parse((P/'audit.py').read_text());hist=[ast.literal_eval(n.iter) for n in ast.walk(t) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='cycle' and isinstance(n.iter,ast.List)];assert hist==[list(range(49,75))],hist
s=(P/'review_saved.py').read_text();assert 'for c in [73,74]' in s and "v['reward73']" in s and "v['reward74']" in s
s=(P/'deploy.py').read_text()
for key in ['parameter_capacity65_67','parameter_capacity68_70','parameter_capacity71_73','parameter_capacity74_76']:assert key in s
assert "for name in ['REVIEW.json', 'SAVED_ARITHMETIC_REVIEW.json', 'PLOT_INSPECTION.json']" in s
assert "assert read(future_plan_path)['cycles'] == [74, 75, 76]" in s
assert str(W/'PLAN.json').replace(str(B)+'/','') in s
assert 'parameter_capacity74_76_reward_stability_20261029_v1/REVIEW.json' not in s
for item in read(W/'SOURCE_REVIEW.json')['files']:
 assert sha(W/item['name'])==item['sha256'] and sha(Path(item['parent']))==item['parent_sha256'];ast.parse((W/item['name']).read_text())
a=read(OLD/'PLAN.json');z=read(W/'PLAN.json');assert a['cycles']==[71,72,73] and z['cycles']==[74,75,76]
for k in ['bootstrap_seed','replicates','near_zero_guard','relative_limit','anchor_protocol55','followup_marker','wait_deadline_seconds','automatic_training','automatic_stop']:assert a[k]==z[k],k
assert sha(OLD/'PLAN.json')=='c160b5d6032abaea7ea81c1fb0a2a8151f4fd929d81044a830740343fc572bdf'
assert sha(W/'PLAN.json')=='d8c243d979f43520e34036b5ce7dfb1b5f5712b5e4091dc09f4dacfdb5061703'
assert z['previous_plan']==dict(path=str(OLD/'PLAN.json'),sha256=sha(OLD/'PLAN.json'))
assert read(P/'UNREVIEWED_DEPLOY_REJECTION.json')['passed']
assert not (W/'LAUNCH.json').exists() and not (W/'REGISTRATION.json').exists() and not (W/'REVIEW.json').exists()
assert not (B/'runtime/prepare_parameter74_20261028_v1/DECISION74.json').exists() and not (B/'runs/parameter74_loss_20261028_v1').exists()
for cycle in [74,75,76]:assert not (B/f'runs/parameter_capacity_pool30_cycle{cycle}_20261026_v1/LAUNCH.json').exists()
j=read(OLD/'LAUNCH.json');f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
r=dict(time=time.time(),passed=True,history_cycles=hist[0],paired_cycles=[73,74],parent_and_prepared_hashes_exact=True,all_ast_valid=True,original_windows_retained=True,original71_73_plan_sha256=sha(OLD/'PLAN.json'),future74_76_plan_sha256=sha(W/'PLAN.json'),formula_threshold_seed_bootstrap_anchor55_unchanged=True,future_window_no_waiter=True,no74_training_or_loss_run=True,original71_73_waiter_live=j,source_sha256=sha(Path(__file__)),limitation='Static preparation and actual missing-decision rejection; positive deployment requires full73/original71-73 review, exact restore and actual74 launch.')
(P/'INDEPENDENT_STATIC_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
