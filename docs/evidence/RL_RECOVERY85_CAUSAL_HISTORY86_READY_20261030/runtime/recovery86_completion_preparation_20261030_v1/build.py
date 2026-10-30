from pathlib import Path
import json,hashlib,ast,re,time,difflib,subprocess
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;O=B/'runtime/recovery85_completion_preparation_20261030_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def advance(s):
 s=re.sub(r'(recovery|cycle|DECISION|decision|launch|loss|startup|archive)(84|85)',lambda m:m[1]+{'84':'85','85':'86'}[m[2]],s)
 s=s.replace('COMPLETE83_84','COMPLETE84_85').replace("old['parent_cycle']==83 and old['new_cycle']==84","old['parent_cycle']==84 and old['new_cycle']==85").replace("decision['parent_cycle']==84 and decision['new_cycle']==85","decision['parent_cycle']==85 and decision['new_cycle']==86").replace('parent_cycle=84,new_cycle=85','parent_cycle=85,new_cycle=86').replace("r['fixed_anchor_rows']==2484","r['fixed_anchor_rows']==2514").replace("evidence['prior84_decision']","evidence['prior85_decision']").replace("evidence['prior84_'+k]","evidence['prior85_'+k]")
 for a,b in [('full84','full85'),('Full84','Full85'),('Complete84','Complete85'),('Original84','Original85'),('finite85','finite86'),('Finite85','Finite86'),('complete84','complete85'),('exact85','exact86'),('automatic86','automatic87')]:s=s.replace(a,b)
 return s
helper='''def require_input_followup85(required):
 follow=B/'runs/recovery84_85_fixed_terminal_input_followup_20261030_v1'
 assert sha(follow/'PLAN.json')=='7703cce3f9428f187fdd796df22e540eb945411b55108cf7e8d3aaee70306494'
 assert (follow/'FINISHED.json').exists(),'Complete85 fixed2514 input followup not ready'
 assert read(follow/'FINISHED.json')['passed'] and read(follow/'REVIEW.json')['passed'] and read(follow/'SAVED_REVIEW.json')['passed']
 p=read(follow/'PLAN.json');assert p['fixed_rows']==2514 and p['all_critics']==[0,1,2,3,4] and p['cycles']==[84,85] and p['registered_before_complete85']
 for n in ['PLAN.json','REVIEW.json','SAVED_REVIEW.json','FINISHED.json']:required['fixed2514_input85_'+n]=follow/n
 diag=B/'runs/recovery83_84_terminal_behavior_alignment_20261030_v1'
 for n in ['REVIEW.json','UPDATE_AVAILABILITY_REVIEW.json','INPUT_REVIEW.json','INPUT_SAVED_REVIEW.json','GRADIENT_REVIEW.json','GRADIENT_SAVED_REVIEW.json']:
  assert read(diag/n)['passed'];required['input_gradient84_'+n]=diag/n
 assert read(diag/'PLOT_INSPECTION.json')['actual_image_viewed'];required['input_gradient84_plot']=diag/'PLOT_INSPECTION.json'
 window=B/'runs/parameter_recovery85_87_reward_stability_20261030_v1'
 assert sha(window/'PLAN.json')=='6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e'
 p=read(window/'PLAN.json');assert p['cycles']==[85,86,87] and p['bootstrap_seed']==2026102858
 required['prospective85_87_plan']=window/'PLAN.json'
'''
files=[]
for src,dst in [('decision85.py','decision86.py'),('launch85.py','launch86.py'),('deploy_loss85.py','deploy_loss86.py')]:
 old=(O/src).read_text()
 if src=='decision85.py':
  start=old.index('def require_completed82_84(');end=old.index('def collect():');unchanged=old[start:end]
  new=advance(old[:start])+unchanged+helper+advance(old[end:])
  new=new.replace(' require_completed82_84(required)\n',' require_completed82_84(required)\n require_input_followup85(required)\n')
  new=new.replace('Actual full85, completed82–84 and fixed2454 all5critic interpretation required','Actual full85, completed82–84 and fixed2514 input/gradient followup interpretation required')
  new=new.replace('fixed2454_critic_followup_reviewed=True,evidence=', 'fixed2454_critic_followup_reviewed=True,fixed2514_input_followup85_reviewed=True,evidence=')
  assert unchanged in new
 else:new=advance(old)
 ast.parse(new);(D/dst).write_text(new);(D/(dst+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(O/src),tofile=str(D/dst))));files.append(dict(parent=ref(O/src),path=str(D/dst),sha256=sha(D/dst)))
assert "parent_cycle=85,new_cycle=86" in (D/'decision86.py').read_text()
assert "old['parent_cycle']==84 and old['new_cycle']==85" in (D/'decision86.py').read_text()
assert "PREP/'resume_recovery85.py'" in (D/'launch86.py').read_text() and 'from decision86 import' in (D/'launch86.py').read_text()
prior=json.loads((O/'DECISION85.json').read_text());assert prior['passed']
for r in prior['evidence'].values():assert sha(r['path'])==r['sha256']
put(D/'LAUNCH_SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=files,prior85_evidence_count=len(prior['evidence']),prior85_evidence_rehashed=True,original_completed82_84_helper_byte_identical=True,new_fixed2514_input85_required=True,original_prospective85_87_plan_bound=True,automatic_training=False))
neg=[]
for name,needle in [('decision86.py','Complete85 archive/review not ready'),('launch86.py','DECISION86 required'),('deploy_loss86.py','LAUNCH.json')]:
 p=subprocess.run([str(B/'env/bin/python'),str(D/name)],capture_output=True,text=True);assert p.returncode!=0 and needle in p.stderr,(name,p.stderr)
 put(D/(name+'.REJECTION.json'),dict(passed=True,time=time.time(),returncode=p.returncode,stderr=p.stderr,source=ref(D/name)));neg.append(name)
p=subprocess.run([str(B/'env/bin/python'),'-c','from decision86 import require_input_followup85; require_input_followup85({})'],cwd=D,capture_output=True,text=True);assert p.returncode!=0 and 'Complete85 fixed2514 input followup not ready' in p.stderr
put(D/'INCOMPLETE_INPUT85_REJECTION.json',dict(passed=True,time=time.time(),returncode=p.returncode,stderr=p.stderr,source=ref(D/'decision86.py')))
assert not (D/'DECISION86.json').exists() and not (B/'runs/parameter_partial75_recovery_cycle86_20261029_v1/LAUNCH.json').exists()
put(D/'PREPARATION_REVIEW.json',dict(passed=True,time=time.time(),missing_prerequisite_rejections=neg+['fixed2514_input85'],actual86_decision=False,actual86_training=False,automatic_training=False))
print('86 decision/launch prepared; full85 and fixed2514 input followup required, no launch')
