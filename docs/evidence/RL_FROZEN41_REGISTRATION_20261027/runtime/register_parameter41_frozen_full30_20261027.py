from pathlib import Path
import re,ast,hashlib,json,shutil,subprocess,time,os,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';old=B/'runs/parameter32_frozen_full30_20261026_v1';out=B/'runs/parameter41_frozen_full30_20261027_v1';rt=B/'runtime'/out.name
assert not (B/'runs/parameter_capacity_pool30_cycle41_20261026_v1/LAUNCH.json').exists()
assert not (B/'runs/parameter_capacity_pool30_cycle41_archive_20261026_v1').exists()
for pid in [691539,691540,691541]:assert Path(f'/proc/{pid}').exists()
out.mkdir();rt.mkdir()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def adapt(s):
 s=re.sub(r'(parameter|complete|Complete|frozen|Frozen|cycle_000|cycle)32',lambda m:m[1]+'41',s)
 s=re.sub(r"(\['(?:parent_cycle|cycle)'\]\s*==\s*|parent_cycle=)32",lambda m:m[1]+'41',s)
 s=s.replace('parameter41_frozen_full30_20261026_v1','parameter41_frozen_full30_20261027_v1')
 return s
oldplan=json.loads((old/'PLAN.json').read_text());diff=[]
for name,h in oldplan['source_hashes'].items():
 source=Path(oldplan['runtime'])/name;assert sha(source)==h
 if name in ['evaluate_parameter32_frozen_full30_20261026.py','review_parameter32_frozen_full30_20261026.py']:
  s=adapt(source.read_text());ast.parse(s);target=rt/adapt(name);target.write_text(s);diff.extend(difflib.unified_diff(source.read_text().splitlines(True),s.splitlines(True),fromfile=str(source),tofile=str(target)))
  dest=R/'code/mujoco_6d_vmc_benchmark/tools'/target.name;assert not dest.exists();shutil.copyfile(target,dest)
 else:shutil.copyfile(source,rt/name)
plan=dict(oldplan);plan.update(time=time.time(),parent_cycle=41,runtime=str(rt),source_hashes={p.name:sha(p) for p in rt.glob('*.py')},registration_state='Formal40 ongoing, complete41 unavailable and formal41 not launched',reason='Prospective complete41 endpoint of already registered39-41 stability window; compare new frozen policies against completed frozen32 using identical all30 conditions and external action seed. Fixed before41 training regardless of future results; no seed/condition selection.',comparison_frozen32=dict(path=str(old/'REVIEW.json'),sha256=sha(old/'REVIEW.json')),stability_window=dict(path=str(B/'runs/parameter_capacity39_41_reward_stability_20261027_v1'),scope='Frozen41 is the predetermined endpoint; does not alter original stability threshold or stop policy.'))
plan.pop('protocol31');plan['protocol40']={m:dict(path=str(B/'runs/parameter_capacity_pool30_cycle40_20261026_v1'/m/'REGISTRATION.json'),sha256=sha(B/'runs/parameter_capacity_pool30_cycle40_20261026_v1'/m/'REGISTRATION.json')) for m in plan['controllers']}
assert plan['action_seed']==2026102638 and plan['conditions']==oldplan['conditions'] and plan['episodes']==90 and plan['maximum_substeps']==99000000
for m in plan['controllers']:
 reg=json.loads(Path(plan['protocol40'][m]['path']).read_text());assert reg['conditions']==plan['conditions'] and reg['replay_capacity_stage']['parent_cycle']==23
plan['formal40_progress_at_registration']={m:json.loads((B/'runs/parameter_capacity_pool30_cycle40_20261026_v1'/m/'train/PROGRESS.json').read_text()) for m in plan['controllers']}
(out/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n');plan_sha=sha(out/'PLAN.json');entries=[]
for name in ['prepare_parameter32_frozen_full30_20261026.py','launch_parameter32_frozen_full30_20261026.py']:
 source=B/'runtime'/name;target=B/'runtime'/adapt(name);assert not target.exists();s=adapt(source.read_text()).replace('fed53352d96604d5aad339b7ad537d042040e2105646e94e1721d0448a120797',plan_sha);ast.parse(s);target.write_text(s);entries.append(dict(path=str(target),sha256=sha(target)));diff.extend(difflib.unified_diff(source.read_text().splitlines(True),s.splitlines(True),fromfile=str(source),tofile=str(target)))
# All unchanged helper bytes and the native external RNG/action replay are inherited exactly.
for name,h in oldplan['source_hashes'].items():
 if name not in ['evaluate_parameter32_frozen_full30_20261026.py','review_parameter32_frozen_full30_20261026.py']:assert sha(rt/name)==h
s=(rt/'evaluate_parameter41_frozen_full30_20261026.py').read_text();assert "reg['parent_cycle'] == 41" in s and "ck['cycle'] == 41" in s and "reg['action_seed'] == 2026102638" in s
assert "protocol['replay_capacity_stage']['parent_cycle'] == 23" in s
assert 'expected_episodes=30' in s and 'maximum_substeps=33000000' in s
p=B/'runtime/prepare_parameter41_frozen_full30_20261026.py';s=p.read_text();assert 'cycle_00041.pt' in s and 'parent_cycle=41' in s and "reg['runtime']==protocol['runtime']" in s
(out/'SOURCE.diff').write_text(''.join(diff));(out/'STATIC_REVIEW.json').write_text(json.dumps(dict(time=time.time(),passed=True,plan_sha256=plan_sha,entry_scripts=entries,helper_hashes_unchanged=True,actual_parent_restore=False,new_physics=0,optimizer_updates=0,automatic_evaluation=False),indent=2)+'\n')
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
with (out/'preparation.log').open('x') as f:proc=subprocess.Popen([str(B/'env/bin/python'),str(p)],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
(out/'PREPARATION_LAUNCH.json').write_text(json.dumps(dict(pid=proc.pid,time=time.time(),command=str(p),plan_sha256=plan_sha,timeout_seconds=7200,automatic_evaluation=False),indent=2)+'\n');print(proc.pid,plan_sha)
