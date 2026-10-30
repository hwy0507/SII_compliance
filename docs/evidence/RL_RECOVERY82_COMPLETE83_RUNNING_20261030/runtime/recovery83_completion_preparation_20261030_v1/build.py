from pathlib import Path
import re,ast,json,time,hashlib,difflib,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;O=B/'runtime/recovery82_completion_preparation_20261030_v1'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def ref(p):return dict(path=str(p),sha256=sha(p))
files=[]
for src,dst in [('decision82.py','decision83.py'),('launch82.py','launch83.py'),('deploy_loss82.py','deploy_loss83.py')]:
 s=(O/src).read_text();n=s
 # Advance only current/parent runtime and artifact identities; preserve original79-81 window and fixed76-78 results.
 n=re.sub(r'(recovery|cycle|DECISION|decision|launch|loss|startup|archive)(81|82)',lambda m:m[1]+{'81':'82','82':'83'}[m[2]],n)
 n=n.replace('COMPLETE80_81','COMPLETE81_82').replace('resume_recovery81.py','resume_recovery82.py')
 n=n.replace("old['parent_cycle']==80 and old['new_cycle']==81","old['parent_cycle']==81 and old['new_cycle']==82")
 n=n.replace("decision['parent_cycle']==81 and decision['new_cycle']==82","decision['parent_cycle']==82 and decision['new_cycle']==83")
 n=n.replace('parent_cycle=81,new_cycle=82','parent_cycle=82,new_cycle=83').replace("r['fixed_anchor_rows']==2394","r['fixed_anchor_rows']==2424")
 n=n.replace("evidence['prior81_decision']","evidence['prior82_decision']").replace("evidence['prior81_'+k]","evidence['prior82_'+k]")
 for a,b in [('full81','full82'),('Full81','Full82'),('Complete81','Complete82'),('Original81','Original82'),('finite82','finite83'),('Finite82','Finite83'),('complete81','complete82'),('exact82','exact83'),('accurate82','accurate83'),('automatic83','automatic84')]:n=n.replace(a,b)
 if src=='decision82.py':
  needle=" assert read(required['completed79_81_result'])['passed']"
  insert=" required['prospective82_84_plan']=B/'runs/parameter_recovery82_84_reward_stability_20261030_v1/PLAN.json'\n assert sha(required['prospective82_84_plan'])=='ec47d7a5d8b3f04f1fcb88f5901888baa1e20931bdee97a12021316b8c8e728c' and read(required['prospective82_84_plan'])['cycles']==[82,83,84]\n"
  assert n.count(needle)==1;n=n.replace(needle,insert+needle)
  n=n.replace('Require full82 interpretation AND completed original76–78 and79–81 statistics','Require full82 interpretation, completed original76–78/79–81 and unchanged prospective82–84')
 ast.parse(n);(D/dst).write_text(n);(D/(dst+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),n.splitlines(True),fromfile=str(O/src),tofile=str(D/dst))))
 files.append(dict(parent=ref(O/src),path=str(D/dst),sha256=sha(D/dst)))
assert "parent_cycle=82,new_cycle=83" in (D/'decision83.py').read_text()
assert "old['parent_cycle']==81 and old['new_cycle']==82" in (D/'decision83.py').read_text()
assert "PREP/'resume_recovery82.py'" in (D/'launch83.py').read_text()
assert "from decision83 import" in (D/'launch83.py').read_text()
prior=json.loads((O/'DECISION82.json').read_text());assert prior['passed']
for r in prior['evidence'].values():assert sha(r['path'])==r['sha256']
write(D/'LAUNCH_SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=files,prior82_evidence_count=len(prior['evidence']),prior82_evidence_rehashed=True,original76_78_and79_81_preserved=True,prospective82_84_exact_plan_bound=True,automatic_training=False))
neg=[]
for name,needle in [('decision83.py','Complete82 archive/review not ready'),('launch83.py','DECISION83 required'),('deploy_loss83.py','LAUNCH.json')]:
 p=subprocess.run([str(B/'env/bin/python'),str(D/name)],capture_output=True,text=True);assert p.returncode!=0 and needle in p.stderr,(name,p.stderr)
 write(D/(name+'.REJECTION.json'),dict(passed=True,time=time.time(),returncode=p.returncode,stderr=p.stderr,source=ref(D/name)));neg.append(name)
assert not (D/'DECISION83.json').exists() and not (B/'runs/parameter_partial75_recovery_cycle83_20261029_v1/LAUNCH.json').exists()
write(D/'PREPARATION_REVIEW.json',dict(passed=True,time=time.time(),missing_prerequisite_rejections=neg,automatic_training=False,actual83_decision=False,actual83_training=False))
print('83 decision/launcher/loss preparation and actual missing prerequisites rejected; no83 launch')
