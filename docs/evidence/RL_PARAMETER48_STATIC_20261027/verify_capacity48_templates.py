from pathlib import Path
import ast,json,hashlib,time,sys,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/parameter48_static_preparation_20261027_v1';T=O/'templates';old=B/'runs/parameter_capacity_pool30_cycle46_review_20261026_v1'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
for p in O.rglob('*.py'):ast.parse(p.read_text())
assert not (B/'runs/parameter_capacity_pool30_cycle48_20261026_v1').exists()
assert not (B/'runtime/parameter_capacity_pool30_cycle48_20261026_v1').exists()
assert not (B/'runs/parameter_capacity_pool30_cycle47_20261026_v1/LAUNCH.json').exists()
checks={}
for name in ['diagnose_published_training_20261025.py','diagnose_published_value_bound_20261025.py']:
 assert (T/name).read_bytes()==(old/name).read_bytes();checks[name]=True
for name in ['review.py','startup_review.py']:
 previous=(old/name if name=='review.py' else B/'runs/parameter_capacity_pool30_cycle46_20261026_v1'/name).read_text();current=(T/name).read_text()
 # Every reward/mapping calculation stays byte-identical, with only current-cycle label changed.
 begin='    max_reward_error=0.' if name=='review.py' else ' err=0.'
 end='    assert sha(reg[' if name=='review.py' else " report['methods'][m]="
 a=previous[previous.index(begin):previous.index(end,previous.index(begin))];b=current[current.index(begin):current.index(end,current.index(begin))]
 assert a.replace('cycle_00046','cycle_00048')==b
 assert "x['replay']['capacity']==4_000_000" in current and "old['replay']['capacity']==2_000_000" in current
 assert 'replay_capacity_followup=FOLLOWUP_MARKER' in current and 'current_replay_capacity=4_000_000' in current
 assert "['parent_cycle']==23" in current and "['parent_cycle']==47" in current
 checks[name+'_reward_mapping_exact']=True
 (O/(name+'.diff')).write_text(''.join(difflib.unified_diff(previous.splitlines(True),current.splitlines(True),fromfile='original46/'+name,tofile='candidate48/'+name)))
# Check actual retained baseline files against all three current46 protocols (47 must remain byte-exact).
for m in ['impedance','admittance','vmc']:
 reg=json.loads((B/'runs/parameter_capacity_pool30_cycle46_20261026_v1'/m/'REGISTRATION.json').read_text())
 for name,expected in reg['batch_size_stage']['dependency_hashes'].items():assert sha(B/'runtime/parameter_capacity_pool30_cycle46_20261026_v1'/name)==expected
 for name in ['parameter_replay_capacity4m_20261027.py','resume_cheq_capacity4m_pool30_20261027.py']:assert name not in reg['batch_size_stage']['dependency_hashes']
checks['all46_baseline_dependency_hashes_unchanged']=True
exp=B/'runs/parameter_capacity4m_preparation_20261027_v1'
for name,key,report in [('parameter_replay_capacity4m_20261027.py','helper_sha256','REVIEW.json'),('resume_cheq_capacity4m_pool30_20261027.py','driver_sha256','DRIVER_STATIC_REVIEW.json')]:assert sha(O/'sources'/name)==json.loads((exp/report).read_text())[key]
checks['candidate_sources_match_prior_passed_reviews']=True
s=(O/'prepare.py').read_text()
for value in ["oldname='parameter_capacity_pool30_cycle47_20261026_v1'","name='parameter_capacity_pool30_cycle48_20261026_v1'","'cycle_00047.pt'","trial['parent_cycle']=47","[13,26,39]","entry_replay_digest=digest(s)","set(trial['dependency_hashes'])-set(baseline)=={driver,followup_helper}"]:assert value in s,value
for oldlabel in ['cycle46','cycle_00046','1829718','1829722','1829726']:
 assert all(oldlabel not in (O/name).read_text() for name in ['prepare.py','launch.py','setup_monitors.py'])
files={str(p.relative_to(O)):sha(p) for p in O.rglob('*.py')};write(O/'SOURCE_MANIFEST.json',files)
plan=json.loads((O/'PLAN.json').read_text());plan['source_manifest_sha256']=sha(O/'SOURCE_MANIFEST.json');write(O/'PLAN.json',plan)
write(O/'STATIC_REVIEW.json',dict(passed=True,time=time.time(),source_files=len(files),checks=checks,source_manifest_sha256=sha(O/'SOURCE_MANIFEST.json'),actual_complete47_restore=False,formal_deployment=False,waiter_started=False,optimizer_updates=0,new_physics=0,limitation='AST, label/schema, source hash and unchanged numerical audit blocks only. Exact47 full learner/replay restore and actual48 boundary must still run.'))
print('Static48 PASS',len(files),checks)
