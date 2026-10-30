from pathlib import Path
import json,time,hashlib,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat');s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
rows=[]
for name in ['parameter_recovery79_task_labels_20261029_v1','vmc_recovery79_terminal_followup_20261029_v1','admittance_recovery79_terminal_followup_20261029_v1']:
 p=B/'runs'/name;plan=read(p/'PLAN.json');launch=read(p/'LAUNCH.json');assert live(launch) and sha(p/'PLAN.json')==launch['plan_sha256'];assert not (p/'FAILURE.json').exists()
 for n,h in plan['sources'].items():assert sha(p/n)==h;ast.parse((p/n).read_text())
 for x in plan.get('inputs',{}).values():assert sha(x['path'])==x['sha256']
 if name.startswith('parameter'):assert plan['cycles']==[78,79]
 else:
  old=read(B/'runs'/name.replace('79','78')/'PLAN.json');assert plan['focus_replay_indices']==old['focus_replay_indices'];assert plan['fixed_anchor_rows']==2334 and plan['expected_complete79_terminal_rows']==2364
  assert read(p/'ANCHOR_REVIEW.json')['passed'] and read(p/'ANCHOR_SAVED_REVIEW.json')['passed']
 rows.append(dict(path=str(p),pid=launch['pid'],start=launch['proc_start_ticks'],plan_sha256=sha(p/'PLAN.json')))
p=B/'runs/parameter_recovery79_81_reward_stability_20261030_v1';plan=read(p/'PLAN.json');old=read(B/'runs/parameter_recovery76_78_reward_stability_20261029_v1/PLAN.json')
for k in ['bootstrap_seed','replicates','near_zero_guard','relative_limit','anchor_protocol55']:assert plan[k]==old[k]
assert plan['cycles']==[79,80,81] and plan['time']<read(B/'runs/parameter_partial75_recovery_cycle79_20261029_v1/LAUNCH.json')['time']
for x in read(p/'SOURCE_REVIEW.json')['files']:
 assert sha(p/x['name'])==x['sha256'];assert sha(x['parent']['path'])==x['parent']['sha256']
 a=ast.parse(Path(x['parent']['path']).read_text());z=ast.parse((p/x['name']).read_text());an=[n.value for n in ast.walk(a) if isinstance(n,ast.Constant) and type(n.value) in (int,float)];zn=[n.value for n in ast.walk(z) if isinstance(n,ast.Constant) and type(n.value) in (int,float)];assert len(an)==len(zn);assert all(y=={76:79,77:80,78:81}.get(x,x) for x,y in zip(an,zn))
for k in ['previous_plan','previous_result','previous_saved_arithmetic']:assert sha(plan[k]['path'])==plan[k]['sha256']
launch=read(p/'LAUNCH.json');assert live(launch);rows.append(dict(path=str(p),pid=launch['pid'],start=launch['proc_start_ticks']))
(D/'DEPLOYMENT_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),jobs=rows,all_sources_and_inputs_hashed=True,terminal_focus_preserved=True,prospective_registration_before79=True,numeric_constants_only_cycles_changed=True,original76_78_retained=True,new_physics=0,new_updates=0),indent=2)+'\n');print('All4 followups verified')
