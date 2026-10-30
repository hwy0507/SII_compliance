from pathlib import Path
import json,hashlib,time,ast,difflib,copy,importlib.util
B=Path(__file__).resolve().parents[2];OLD=B/'runtime/parameter55_frozen_full30_20261028_v1';D=B/'runtime/parameter82_frozen_full30_20261030_v1';O=B/'runs/parameter82_frozen_full30_20261030_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
pre=read(O/'PRE_REGISTRATION.json');assert sha(O/'PRE_REGISTRATION.json')=='baf37d1715635e1d5352deea7434b33e36e666c4c0d3036f43f404b685935b76'
for r in pre['inputs']+pre['basis_sources']:assert sha(r['path'])==r['sha256']
D.mkdir();oldplan=read(B/'runs/parameter55_frozen_full30_20261028_v1/PLAN.json');diffs=[]
for n in oldplan['source_hashes']:
 if n.startswith(('evaluate_parameter55','review_parameter55')):continue
 p=OLD/n;assert sha(p)==oldplan['source_hashes'][n];(D/n).write_bytes(p.read_bytes())
helper='''def validate_recovery(ck, protocol, expected_cycle):
    assert expected_cycle in (81, 82)
    assert ck['cycle'] == expected_cycle and ck['boundary'] == 'complete_condition_cycle'
    assert ck['environment_state_saved'] is False
    assert ck['interruption_recovery'] == protocol['interrupted_episode_recovery']
    assert ck['recovery_continuation'] == protocol['post_interruption_continuation']
    stage = protocol['post_interruption_continuation']
    assert stage['parent_cycle'] == expected_cycle - 1 and stage['new_cycle'] == expected_cycle
    assert stage['new_cycles'] == 1 and stage['maximum_new_actions'] == 41250
    assert stage['automatic_followup'] is False and stage['optimizer_settings_changed'] is False
    assert all(c['cycle'] != 75 for c in ck['cycles']) and ck['cycles'][-1]['cycle'] == expected_cycle


'''
for before,after in [('evaluate_parameter55_frozen_full30_20261028.py','evaluate_parameter82_frozen_full30_20261030.py'),('review_parameter55_frozen_full30_20261028.py','review_parameter82_frozen_full30_20261030.py')]:
 s=(OLD/before).read_text();new=s.replace('complete55','complete82').replace('Complete55','Complete82').replace('frozen55','frozen82').replace('Frozen55','Frozen82').replace('planned55','planned82').replace('validation53','validation81')
 if before.startswith('evaluate'):
  new=new.replace('expected_cycle=55','expected_cycle=82').replace('expected_cycle != 55','expected_cycle != 82').replace('(53, 55)','(81, 82)').replace('choices=[53,55], default=55','choices=[81,82], default=82')
  new=new.replace('def main(',helper+'def main(',1)
  seam="    assert ck['controller'] == reg['controller'] and ck['protocol_sha256'] == sha(reg['training_registration'])\n";assert new.count(seam)==1
  new=new.replace(seam,seam+'    validate_recovery(ck, protocol, expected_cycle)\n')
  # Exact physical/action loop remains byte-for-byte identical.
  assert s[s.index('    results = []'):s.index("    write(output/'FINISHED.json'")] == new[new.index('    results = []'):new.index("    write(output/'FINISHED.json'")]
 else:
  new=new.replace("plan['parent_cycle'] == 55","plan['parent_cycle'] == 82")
  new=new.replace('was chosen before its training began','was chosen before its complete checkpoint and full reviews, with partial progress known')
 ast.parse(new);(D/after).write_text(new);(D/(after+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),new.splitlines(True),fromfile=before,tofile=after)))
 diffs.append(dict(parent=ref(OLD/before),adapted=ref(D/after)))
# Validate metadata rejection independently of costly checkpoint loads.
ns={};exec(helper,ns);validate=ns['validate_recovery'];tests=[]
for m in pre['controllers']:
 p=read(B/f'runs/parameter_partial75_recovery_cycle82_20261029_v1/{m}/REGISTRATION.json')
 ck=dict(cycle=82,boundary='complete_condition_cycle',environment_state_saved=False,interruption_recovery=copy.deepcopy(p['interrupted_episode_recovery']),recovery_continuation=copy.deepcopy(p['post_interruption_continuation']),cycles=[dict(cycle=81),dict(cycle=82)])
 validate(ck,p,82)
 for label,mutate in [('wrong_cycle',lambda c,q:c.update(cycle=81)),('boundary',lambda c,q:c.update(boundary='partial')),('environment',lambda c,q:c.update(environment_state_saved=True)),('interruption',lambda c,q:c.update(interruption_recovery={})),('continuation',lambda c,q:c.update(recovery_continuation={})),('partial75_complete',lambda c,q:c['cycles'].insert(0,dict(cycle=75))),('last_cycle',lambda c,q:c['cycles'][-1].update(cycle=81)),('parent',lambda c,q:q['post_interruption_continuation'].update(parent_cycle=80)),('extra_cycle',lambda c,q:q['post_interruption_continuation'].update(new_cycles=2)),('budget',lambda c,q:q['post_interruption_continuation'].update(maximum_new_actions=82500)),('auto_followup',lambda c,q:q['post_interruption_continuation'].update(automatic_followup=True)),('optimizer_change',lambda c,q:q['post_interruption_continuation'].update(optimizer_settings_changed=True))]:
  c,q=copy.deepcopy(ck),copy.deepcopy(p);mutate(c,q)
  if label in ['parent','extra_cycle','budget','auto_followup','optimizer_change']:c['recovery_continuation']=copy.deepcopy(q['post_interruption_continuation'])
  try:validate(c,q,82)
  except AssertionError:tests.append(dict(method=m,case=label,rejected=True))
  else:raise AssertionError(label)
put(D/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=diffs,unchanged_dependency_files=len(oldplan['source_hashes'])-2,physical_action_loop_byte_identical=True,metadata_positive_methods=3,negative_rejections=tests,physics=0,optimizer_updates=0))
sources={p.name:sha(p) for p in D.glob('*.py')}
plan=dict(time=time.time(),preregistration=ref(O/'PRE_REGISTRATION.json'),parent_cycle=82,controllers=pre['controllers'],case_ids=pre['case_ids'],conditions=pre['conditions'],action_seed=pre['action_seed'],episodes=90,maximum_actions=123750,maximum_substeps=99000000,maximum_episode_seconds=55,physics_dt_s=5e-5,actor_period_s=.04,runtime=str(D),source_hashes=sources,cpu_mapping=pre['cpu_by_method'],gpu_mapping={m:0 for m in pre['controllers']},new_optimizer_updates=0,formal_replay_writes=0,review_wait_seconds=21600,no_budget_extension=True,source_review=ref(D/'SOURCE_REVIEW.json'),reason=pre['selection_timing'],limitations=pre['limitation'],comparison_frozen55=pre['inputs'][1],replay_capacity=4000000,historical_entry_cycle=23,followup_entry_cycle=47,automatic_evaluation=False)
put(O/'PLAN.json',plan);commands=[]
review=B/'runs/parameter_partial75_recovery_cycle82_review_20261029_v1/REVIEW.json';full=read(review);assert full['passed']
for m in pre['controllers']:
 parent=B/f'runs/parameter_partial75_recovery_cycle82_20261029_v1/{m}/REGISTRATION.json';protocol=read(parent);assert protocol['conditions']==pre['conditions']
 ck=B/f'runs/parameter_partial75_recovery_cycle82_archive_20261029_v1/{m}/cycle_00082.pt';h=sha(ck);assert h==full['methods'][m]['checkpoint_sha256']
 journal=parent.parent/'train/cycle_00082/active_short_train_0600/actor_intervals.jsonl'
 reg=read(B/f'runs/parameter55_frozen_full30_20261028_v1/{m}/REGISTRATION.json');reg.update(parent_cycle=82,audit_runtime=str(D),checkpoint=str(ck),checkpoint_sha256=h,training_registration=str(parent),training_registration_sha256=sha(parent),required_review=str(review),required_review_sha256=sha(review),gate_observations=str(journal),gate_observations_sha256=sha(journal),source_hashes=sources)
 assert reg['cpu']==pre['cpu_by_method'][m] and reg['device']=='cuda:0' and reg['case_ids']==pre['case_ids'] and reg['runtime']==protocol['runtime']
 dest=O/m;dest.mkdir();put(dest/'REGISTRATION.json',reg);commands.append(dict(controller=m,command=[str(B/'env/bin/python'),str(D/'evaluate_parameter82_frozen_full30_20261030.py'),'--registration',str(dest/'REGISTRATION.json')]))
put(O/'COMMANDS.json',dict(jobs=commands));print('Frozen82 code/protocol registered,36 metadata negatives passed; no physics or restore yet')
