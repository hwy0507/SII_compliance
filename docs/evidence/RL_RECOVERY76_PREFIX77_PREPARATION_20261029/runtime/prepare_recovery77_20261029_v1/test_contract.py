"""Small metadata fixtures test validators; not an actual full76 restore."""
from pathlib import Path
import json,time,copy,hashlib,importlib.util,subprocess,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;T=D/'contract_fixtures';T.mkdir(exist_ok=False);RUN=B/'runs/parameter_partial75_recovery_cycle76_20261029_v1'
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
spec=importlib.util.spec_from_file_location('test_recovery77',D/'resume_recovery76.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
results={}
for method in ['impedance','admittance','vmc']:
 parent=RUN/method/'REGISTRATION.json';previous=json.loads(parent.read_text());h='fixture-only-not-real-checkpoint-'+method
 review=T/(method+'_review.json');health=T/(method+'_health.json');write(review,dict(fixture_only=True,passed=True,methods={method:dict(checkpoint_sha256=h,steps=123)}));write(health,dict(fixture_only=True,methods={method:dict(checkpoint_sha256=h)}))
 st=dict(parent_cycle=76,new_cycle=77,new_cycles=1,maximum_new_actions=41250,environment_state_saved=False,old_window_continuity_claim=False,automatic_followup=False,optimizer_settings_changed=False,parent_registration=ref(parent),checkpoint=dict(path='fixture_only_no_file',sha256=h),cycle_review=ref(review),health_review=ref(health),controller=method,recovery_driver=ref(B/'runtime/parameter75_interruption_recovery_20261029_v1/resume_partial75.py'))
 p=copy.deepcopy(previous);p['post_interruption_continuation']=st;assert mod.validate_protocol(sha(parent),p,'')==previous
 rejected=[]
 mutations=[('learner_batch_size',256),('learner_updates_per_transition',2),('critic_clock',False)]
 for k,v in mutations:
  bad=copy.deepcopy(p);bad[k]=v
  try:mod.validate_protocol(sha(parent),bad,'')
  except ValueError:rejected.append(k)
  else:raise AssertionError(k)
 for k,v in [('parent_cycle',75),('new_cycle',76),('new_cycles',2),('maximum_new_actions',82500),('environment_state_saved',True),('old_window_continuity_claim',True),('automatic_followup',True),('optimizer_settings_changed',True)]:
  bad=copy.deepcopy(p);bad['post_interruption_continuation'][k]=v
  try:mod.validate_protocol(sha(parent),bad,'')
  except ValueError:rejected.append(k)
  else:raise AssertionError(k)
 for field in ['checkpoint','cycle_review','health_review','parent_registration','recovery_driver']:
  bad=copy.deepcopy(p);bad['post_interruption_continuation'][field]['sha256']='wrong'
  try:mod.validate_protocol(sha(parent),bad,'')
  except ValueError:rejected.append(field)
  else:raise AssertionError(field)
 bad=copy.deepcopy(p);bad['interrupted_episode_recovery']['old_window_continuity_claim']=True
 try:mod.validate_protocol(sha(parent),bad,'')
 except ValueError:rejected.append('historical_recovery')
 else:raise AssertionError('historical recovery mutation accepted')
 ck=dict(cycle=76,boundary='complete_condition_cycle',environment_state_saved=False,steps=123,seed=20261025,cycles=[dict(cycle=74),dict(cycle=76)],interruption_recovery=previous['interrupted_episode_recovery'])
 mod.validate_parent(ck,st)
 badparents=[]
 for key,val in [('cycle',75),('boundary','partial_episode_valid_replay_reset_environment_on_resume'),('environment_state_saved',True),('steps',124),('seed',0),('cycles',[dict(cycle=74),dict(cycle=75),dict(cycle=76)]),('interruption_recovery',{})]:
  bad=copy.deepcopy(ck);bad[key]=val
  try:mod.validate_parent(bad,st)
  except ValueError:badparents.append(key)
  else:raise AssertionError(key)
 results[method]=dict(protocol_positive_fixture=True,protocol_negative_rejections=rejected,parent_positive_fixture=True,parent_negative_rejections=badparents)
cmd=[str(B/'env/bin/python'),str(D/'prepare.py')];r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode!=0 and 'Incomplete recovery76' in r.stderr and not (B/'runs/parameter_partial75_recovery_cycle77_20261029_v1').exists();write(D/'INCOMPLETE76_REJECTION.json',dict(passed=True,time=time.time(),command=cmd,returncode=r.returncode,stderr=r.stderr,no77_output=True))
write(D/'CONTRACT_REVIEW.json',dict(passed=True,time=time.time(),methods=results,fixture_only=True,actual_full76_restore=False,new_physics=0,optimizer_updates=0,source_sha256=sha(Path(__file__))))
for p in D.glob('*.py'):ast.parse(p.read_text())
print('3 metadata positive protocol/parent fixtures; per method17 protocol +7 boundary negatives; actual incomplete76 rejected')
