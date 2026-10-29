"""No-physics controls for the fixed-model diagnosis dispatch and refusal rules."""
import argparse
import copy
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import diagnose_contact_yield_students_20261030 as runner


def check():
 models=[dict(name=f+'_s'+str(s),family=f,seed=s) for f in runner.FAMILIES for s in runner.SEEDS]
 refs=[dict(id=s+'_00',scene=s,split='train',seed=1,parameters={}) for s in ('rod','ball','corner')]
 cases=runner.make_cases(models,refs);assert len(cases)==27
 rejected=[]
 for name,alter in [('missing_model',lambda m,r:m.pop()),('duplicate_model',lambda m,r:m.__setitem__(1,copy.deepcopy(m[0]))),('duplicate_name',lambda m,r:m[1].update(name=m[0]['name'])),('missing_scene',lambda m,r:r.pop()),('validation_identity',lambda m,r:r[0].update(split='validation')),('wrong_identity',lambda m,r:r[0].update(id='rod_01'))]:
  m=copy.deepcopy(models);r=copy.deepcopy(refs);alter(m,r)
  try:runner.make_cases(m,r)
  except AssertionError:rejected.append(name)
  else:raise AssertionError(name+' accepted')
 with tempfile.TemporaryDirectory(prefix='contact-yield-diagnosis-controls-') as temp:
  base=Path(temp);calls=[]
  def fake(root,case,reg):
   calls.append(case['id']);return dict(id=case['id'],folder=str(root/case['id']),pairing={'synthetic':True},scientific_failure_preserved=True)
  with patch.object(runner,'check_resources'),patch.object(runner,'check'),patch.object(runner,'teacher_pairing'),patch.object(runner,'run_case',side_effect=fake),patch.object(runner.fcntl,'flock'):
   root=base/'complete';root.mkdir();runner.write(root/'REGISTRATION.json',dict(cases=cases))
   runner.run(root);state=runner.read(root/'execution.json')
   assert state['status']=='complete_development_diagnosis_pending_review' and len(state['rows'])==27
   assert calls==[c['id'] for c in cases]
   try:runner.run(root)
   except AssertionError:rejected.append('repeat_dispatch')
   else:raise AssertionError('repeat accepted')
   assert len(calls)==27
  count=[]
  def fail(root,case,reg):
   count.append(case['id'])
   if len(count)==4:raise RuntimeError('synthetic infrastructure error')
   return fake(root,case,reg)
  with patch.object(runner,'check_resources'),patch.object(runner,'check'),patch.object(runner,'teacher_pairing'),patch.object(runner,'run_case',side_effect=fail),patch.object(runner.fcntl,'flock'):
   root=base/'failure';root.mkdir();runner.write(root/'REGISTRATION.json',dict(cases=cases))
   try:runner.run(root)
   except RuntimeError:pass
   else:raise AssertionError('infrastructure error swallowed')
   state=runner.read(root/'execution.json');assert len(count)==4 and len(state['rows'])==3
   assert state['current']==cases[3]['id'] and state['status']=='failed_preserved_no_retry'
  with patch.object(runner,'properties',return_value=dict(ActiveState='active')):
   root=base/'premature'
   try:runner.prepare(root)
   except AssertionError:rejected.append('active_training_or_collection')
   else:raise AssertionError('premature prepare accepted')
   assert not root.exists()
  with patch.object(runner,'check'):
   for n,status in [(26,'complete_development_diagnosis_pending_review'),(27,'running_fixed_student_development_diagnosis')]:
    root=base/('badreview'+str(n));root.mkdir();runner.write(root/'REGISTRATION.json',dict(cases=cases));runner.write(root/'execution.json',dict(status=status,registration_sha256=runner.sha(root/'REGISTRATION.json'),rows=[dict(id=c['id']) for c in cases[:n]]))
    try:runner.review(root,root/'REVIEW.json')
    except AssertionError:rejected.append('incomplete_review_'+str(n))
    else:raise AssertionError('incomplete review accepted')
    assert not (root/'REVIEW.json').exists()
 return dict(status='passed_zero_physics_dispatch_controls',runner_sha256=runner.sha(Path(runner.__file__)),checker_sha256=runner.sha(Path(__file__)),cases=27,rejected=rejected,all27_scientific_failures_retained=True,infrastructure_failure_retains_three_completed_and_fourth_current=True,actual_physics_episodes=0,actual_training_updates=0,unseen_data_read=False,scope='Mocked dispatch/source/resource interfaces only; real registration, physical runs and independent full27 review remain pending all nine new fits.')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();runner.write(a.output,check());print('fixed27 zero-physics controls passed')
