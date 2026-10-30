from pathlib import Path
import json,time,hashlib,ast,re,difflib,subprocess
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;O=B/'runtime/recovery86_completion_preparation_20261030_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def advance(s):
 s=re.sub(r'(recovery|cycle|DECISION|decision|launch|loss|startup|archive)(85|86)',lambda m:m[1]+{'85':'86','86':'87'}[m[2]],s)
 s=s.replace('COMPLETE84_85','COMPLETE85_86').replace("old['parent_cycle']==84 and old['new_cycle']==85","old['parent_cycle']==85 and old['new_cycle']==86").replace("decision['parent_cycle']==85 and decision['new_cycle']==86","decision['parent_cycle']==86 and decision['new_cycle']==87").replace('parent_cycle=85,new_cycle=86','parent_cycle=86,new_cycle=87').replace("r['fixed_anchor_rows']==2514","r['fixed_anchor_rows']==2544").replace("evidence['prior85_decision']","evidence['prior86_decision']").replace("evidence['prior85_'+k]","evidence['prior86_'+k]")
 for a,b in [('full85','full86'),('Full85','Full86'),('Complete85','Complete86'),('Original85','Original86'),('finite86','finite87'),('Finite86','Finite87'),('complete85','complete86'),('exact86','exact87'),('automatic87','automatic88')]:s=s.replace(a,b)
 return s
helper='''def require_fixed_followup86(required):
 follow=B/'runs/recovery84_86_fixed_terminal_critic_followup_20261030_v1'
 assert sha(follow/'PLAN.json')=='2f7c719eb64c36ce20b8135ca5d18748c0683bb4bf45d6e44a2f953ce44e5041'
 assert (follow/'FINISHED.json').exists(),'Complete86 fixed2514 followup not ready'
 for n in ['FINISHED.json','REVIEW.json','SAVED_REVIEW.json']:
  assert read(follow/n)['passed'];required['fixed2514_84_86_'+n]=follow/n
 p=read(follow/'PLAN.json');assert p['fixed_rows']==2514 and p['all_critics']==[0,1,2,3,4] and p['checkpoint_cycles']==[84,85,86] and p['registered_before_complete86']
 required['fixed2514_84_86_plan']=follow/'PLAN.json'
 plot=follow/'PLOT_INSPECTION.json'
 assert plot.exists() and read(plot)['actual_image_viewed'],'Actual fixed2514 84-86 plot inspection required'
 required['fixed2514_84_86_plot']=plot
'''
files=[]
for before,after in [('decision86.py','decision87.py'),('launch86.py','launch87.py'),('deploy_loss86.py','deploy_loss87.py')]:
 old=(O/before).read_text()
 if before=='decision86.py':
  i=old.index('def require_completed82_84(');j=old.index('def collect():');unchanged=old[i:j]
  new=advance(old[:i])+unchanged+helper+advance(old[j:])
  new=new.replace(' require_input_followup85(required)\n',' require_input_followup85(required)\n require_fixed_followup86(required)\n')
  new=new.replace('fixed2514_input_followup85_reviewed=True,evidence=', 'fixed2514_input_followup85_reviewed=True,fixed2514_84_86_reviewed=True,evidence=')
  assert unchanged in new and ' require_fixed_followup86(required)' in new
 else:new=advance(old)
 ast.parse(new);(D/after).write_text(new);(D/(after+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(O/before),tofile=str(D/after))));files.append(dict(parent=ref(O/before),path=str(D/after),sha256=sha(D/after)))
assert "PREP/'resume_recovery86.py'" in (D/'launch87.py').read_text()
assert "old['parent_cycle']==85 and old['new_cycle']==86" in (D/'decision87.py').read_text()
prior=json.loads((O/'DECISION86.json').read_text());assert prior['passed']
for r in prior['evidence'].values():assert sha(r['path'])==r['sha256']
put(D/'LAUNCH_SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=files,prior86_evidence_count=len(prior['evidence']),prior86_evidence_rehashed=True,original_historical_helpers_byte_identical=True,new_fixed2514_84_86_required=True,original85_87_plan_preserved=True,automatic_training=False))
for name,needle in [('decision87.py','Complete86 archive/review not ready'),('launch87.py','DECISION87 required'),('deploy_loss87.py','LAUNCH.json')]:
 p=subprocess.run([str(B/'env/bin/python'),str(D/name)],capture_output=True,text=True);assert p.returncode!=0 and needle in p.stderr,(name,p.stderr)
 put(D/(name+'.REJECTION.json'),dict(passed=True,time=time.time(),returncode=p.returncode,stderr=p.stderr,source=ref(D/name)))
p=subprocess.run([str(B/'env/bin/python'),'-c','from decision87 import require_fixed_followup86; require_fixed_followup86({})'],cwd=D,capture_output=True,text=True);assert p.returncode!=0 and 'Complete86 fixed2514 followup not ready' in p.stderr,p.stderr
put(D/'INCOMPLETE_FIXED86_REJECTION.json',dict(passed=True,time=time.time(),returncode=p.returncode,stderr=p.stderr,source=ref(D/'decision87.py')))
assert not (D/'DECISION87.json').exists() and not (B/'runs/parameter_partial75_recovery_cycle87_20261029_v1/LAUNCH.json').exists()
put(D/'PREPARATION_REVIEW.json',dict(passed=True,time=time.time(),missing_prerequisite_rejections=4,actual87_decision=False,actual87_training=False,automatic_training=False));print('87 decision/launch prepared; no decision/training')
