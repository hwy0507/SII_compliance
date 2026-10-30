from pathlib import Path
import json,hashlib,ast,re,time,difflib,subprocess
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;O=B/'runtime/recovery84_completion_preparation_20261030_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
files=[];fixed=B/'runs/recovery82_84_fixed_terminal_critic_followup_20261030_v1/PLAN.json';fixed_sha=sha(fixed)
for src,dst in [('decision84.py','decision85.py'),('launch84.py','launch85.py'),('deploy_loss84.py','deploy_loss85.py')]:
 s=(O/src).read_text();n=re.sub(r'(recovery|cycle|DECISION|decision|launch|loss|startup|archive)(83|84)',lambda m:m[1]+{'83':'84','84':'85'}[m[2]],s)
 n=n.replace('COMPLETE82_83','COMPLETE83_84').replace('resume_recovery83.py','resume_recovery84.py')
 n=n.replace("old['parent_cycle']==82 and old['new_cycle']==83","old['parent_cycle']==83 and old['new_cycle']==84")
 n=n.replace("decision['parent_cycle']==83 and decision['new_cycle']==84","decision['parent_cycle']==84 and decision['new_cycle']==85")
 n=n.replace('parent_cycle=83,new_cycle=84','parent_cycle=84,new_cycle=85').replace("r['fixed_anchor_rows']==2454","r['fixed_anchor_rows']==2484")
 n=n.replace("evidence['prior83_decision']","evidence['prior84_decision']").replace("evidence['prior83_'+k]","evidence['prior84_'+k]")
 for a,b in [('full83','full84'),('Full83','Full84'),('Complete83','Complete84'),('Original83','Original84'),('finite84','finite85'),('Finite84','Finite85'),('complete83','complete84'),('exact84','exact85'),('automatic85','automatic86')]:n=n.replace(a,b)
 if src=='decision84.py':
  helper='''def require_completed82_84(required):
 window=B/'runs/parameter_recovery82_84_reward_stability_20261030_v1'
 assert sha(window/'PLAN.json')=='ec47d7a5d8b3f04f1fcb88f5901888baa1e20931bdee97a12021316b8c8e728c'
 assert (window/'REVIEW.json').exists(),'Original82-84 complete result not ready'
 for key,name in [('result','REVIEW.json'),('saved','SAVED_ARITHMETIC_REVIEW.json'),('plot','PLOT_INSPECTION.json')]:required['completed82_84_'+key]=window/name
 assert read(required['completed82_84_result'])['passed'] and read(required['completed82_84_saved'])['passed']
 assert read(required['completed82_84_plot'])['actual_image_viewed']
 scalar=B/'runs/recovery82_84_bootstrap_scalar_review_20261030_v1'
 assert read(scalar/'FINISHED.json')['passed'] and read(scalar/'REVIEW.json')['passed']
 required['completed82_84_scalar']=scalar/'REVIEW.json';required['completed82_84_scalar_finished']=scalar/'FINISHED.json'
 follow=B/'runs/recovery82_84_fixed_terminal_critic_followup_20261030_v1'
 assert sha(follow/'PLAN.json')=='__FIXED_SHA__'
 plan=read(follow/'PLAN.json');assert plan['fixed_rows']==2454 and plan['all_critics']==[0,1,2,3,4] and plan['checkpoint_cycles']==[82,83,84] and plan['registered_before_complete84']
 assert read(follow/'FINISHED.json')['passed'] and read(follow/'REVIEW.json')['passed'] and read(follow/'SAVED_REVIEW.json')['passed']
 for key,name in [('plan','PLAN.json'),('result','REVIEW.json'),('saved','SAVED_REVIEW.json'),('finished','FINISHED.json')]:required['fixed2454_82_84_'+key]=follow/name
 required['old83_population']=B/'runs/recovery82_83_old_terminal_population_20261030_v1/REVIEW.json'
 required['old83_population_saved']=B/'runs/recovery82_83_old_terminal_population_20261030_v1/SAVED_REVIEW.json'
 assert read(required['old83_population'])['passed'] and read(required['old83_population_saved'])['passed']
'''.replace('__FIXED_SHA__',fixed_sha)
  assert n.count('def collect():')==1;n=n.replace('def collect():',helper+'def collect():')
  needle=' for k,p in required.items():evidence[k]=ref(p)';assert n.count(needle)==1;n=n.replace(needle,' require_completed82_84(required)\n'+needle)
  n=n.replace('Actual full84, original76–78 and completed79–81 interpretation required','Actual full84, completed82–84 and fixed2454 all5critic interpretation required')
  n=n.replace('original79_81_window_completed_and_reviewed=True,evidence=', 'original79_81_window_completed_and_reviewed=True,original82_84_window_completed_and_reviewed=True,fixed2454_critic_followup_reviewed=True,evidence=')
 ast.parse(n);(D/dst).write_text(n);(D/(dst+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),n.splitlines(True),fromfile=str(O/src),tofile=str(D/dst))));files.append(dict(parent=ref(O/src),path=str(D/dst),sha256=sha(D/dst)))
assert "parent_cycle=84,new_cycle=85" in (D/'decision85.py').read_text()
assert "old['parent_cycle']==83 and old['new_cycle']==84" in (D/'decision85.py').read_text()
assert "PREP/'resume_recovery84.py'" in (D/'launch85.py').read_text() and 'from decision85 import' in (D/'launch85.py').read_text()
assert "parameter_recovery82_84_reward_stability_20261030_v1" in (D/'decision85.py').read_text()
prior=json.loads((O/'DECISION84.json').read_text());assert prior['passed']
for r in prior['evidence'].values():assert sha(r['path'])==r['sha256']
put(D/'LAUNCH_SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=files,prior84_evidence_count=len(prior['evidence']),prior84_evidence_rehashed=True,original76_78_and79_81_preserved=True,completed82_84_required=True,completed82_84_scalar_required=True,fixed2454_all5critic_followup_required=True,fixed_plan_sha256=fixed_sha,automatic_training=False))
neg=[]
for name,needle in [('decision85.py','Complete84 archive/review not ready'),('launch85.py','DECISION85 required'),('deploy_loss85.py','LAUNCH.json')]:
 p=subprocess.run([str(B/'env/bin/python'),str(D/name)],capture_output=True,text=True);assert p.returncode!=0 and needle in p.stderr,(name,p.stderr)
 put(D/(name+'.REJECTION.json'),dict(passed=True,time=time.time(),returncode=p.returncode,stderr=p.stderr,source=ref(D/name)));neg.append(name)
p=subprocess.run([str(B/'env/bin/python'),'-c','from decision85 import require_completed82_84; require_completed82_84({})'],cwd=D,capture_output=True,text=True);assert p.returncode!=0 and 'Original82-84 complete result not ready' in p.stderr
put(D/'INCOMPLETE82_84_REJECTION.json',dict(passed=True,time=time.time(),returncode=p.returncode,stderr=p.stderr,source=ref(D/'decision85.py')))
assert not (D/'DECISION85.json').exists() and not (B/'runs/parameter_partial75_recovery_cycle85_20261029_v1/LAUNCH.json').exists()
put(D/'PREPARATION_REVIEW.json',dict(passed=True,time=time.time(),missing_prerequisite_rejections=neg+['completed82_84'],automatic_training=False,actual85_decision=False,actual85_training=False))
print('85 decision/dispatch prepared: complete84 and original82-84, scalar and fixed2454 followup required; no launch')
