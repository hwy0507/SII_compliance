from pathlib import Path
import re,ast,json,time,hashlib,difflib,subprocess
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;O=B/'runtime/recovery83_completion_preparation_20261030_v1'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def ref(p):return dict(path=str(p),sha256=sha(p))
files=[]
for src,dst in [('decision83.py','decision84.py'),('launch83.py','launch84.py'),('deploy_loss83.py','deploy_loss84.py')]:
 s=(O/src).read_text();n=re.sub(r'(recovery|cycle|DECISION|decision|launch|loss|startup|archive)(82|83)',lambda m:m[1]+{'82':'83','83':'84'}[m[2]],s)
 # Restore exact original prospective82-84 path after current-cycle substitution.
 n=n.replace('parameter_recovery83_84_reward_stability','parameter_recovery82_84_reward_stability')
 n=n.replace('COMPLETE81_82','COMPLETE82_83').replace('resume_recovery82.py','resume_recovery83.py')
 n=n.replace("old['parent_cycle']==81 and old['new_cycle']==82","old['parent_cycle']==82 and old['new_cycle']==83")
 n=n.replace("decision['parent_cycle']==82 and decision['new_cycle']==83","decision['parent_cycle']==83 and decision['new_cycle']==84")
 n=n.replace('parent_cycle=82,new_cycle=83','parent_cycle=83,new_cycle=84').replace("r['fixed_anchor_rows']==2424","r['fixed_anchor_rows']==2454")
 n=n.replace("evidence['prior82_decision']","evidence['prior83_decision']").replace("evidence['prior82_'+k]","evidence['prior83_'+k]")
 for a,b in [('full82','full83'),('Full82','Full83'),('Complete82','Complete83'),('Original82','Original83'),('finite83','finite84'),('Finite83','Finite84'),('complete82','complete83'),('exact83','exact84'),('automatic84','automatic85')]:n=n.replace(a,b)
 if src=='decision83.py':
  needle=" for k,p in required.items():evidence[k]=ref(p)"
  extra=" required['original76_81_scalar_bootstrap']=B/'runs/recovery76_81_bootstrap_scalar_review_20261030_v1/REVIEW.json'\n assert read(required['original76_81_scalar_bootstrap'])['passed']\n required['frozen82_preregistration']=B/'runs/parameter82_frozen_full30_20261030_v1/PRE_REGISTRATION.json'\n assert sha(required['frozen82_preregistration'])=='baf37d1715635e1d5352deea7434b33e36e666c4c0d3036f43f404b685935b76'\n"
  assert n.count(needle)==1;n=n.replace(needle,extra+needle)
 ast.parse(n);(D/dst).write_text(n);(D/(dst+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),n.splitlines(True),fromfile=str(O/src),tofile=str(D/dst))))
 files.append(dict(parent=ref(O/src),path=str(D/dst),sha256=sha(D/dst)))
assert "parent_cycle=83,new_cycle=84" in (D/'decision84.py').read_text()
assert "old['parent_cycle']==82 and old['new_cycle']==83" in (D/'decision84.py').read_text()
assert "PREP/'resume_recovery83.py'" in (D/'launch84.py').read_text()
assert "from decision84 import" in (D/'launch84.py').read_text()
assert "parameter_recovery82_84_reward_stability_20261030_v1" in (D/'decision84.py').read_text()
prior=json.loads((O/'DECISION83.json').read_text());assert prior['passed']
for r in prior['evidence'].values():assert sha(r['path'])==r['sha256']
put(D/'LAUNCH_SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=files,prior83_evidence_count=len(prior['evidence']),prior83_evidence_rehashed=True,original76_78_and79_81_preserved=True,prospective82_84_exact_plan_bound=True,frozen82_separate_registered_validation_retained=True,automatic_training=False))
neg=[]
for name,needle in [('decision84.py','Complete83 archive/review not ready'),('launch84.py','DECISION84 required'),('deploy_loss84.py','LAUNCH.json')]:
 p=subprocess.run([str(B/'env/bin/python'),str(D/name)],capture_output=True,text=True);assert p.returncode!=0 and needle in p.stderr,(name,p.stderr)
 put(D/(name+'.REJECTION.json'),dict(passed=True,time=time.time(),returncode=p.returncode,stderr=p.stderr,source=ref(D/name)));neg.append(name)
assert not (D/'DECISION84.json').exists() and not (B/'runs/parameter_partial75_recovery_cycle84_20261029_v1/LAUNCH.json').exists()
put(D/'PREPARATION_REVIEW.json',dict(passed=True,time=time.time(),missing_prerequisite_rejections=neg,automatic_training=False,actual84_decision=False,actual84_training=False))
print('84 explicit decision and dispatch prepared; missing complete83, decision and launch correctly refused')
