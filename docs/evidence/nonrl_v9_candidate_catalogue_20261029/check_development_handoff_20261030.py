"""Saved-history controls for a future finite recovery probe; zero physics."""
import argparse
from pathlib import Path
import numpy as np
from collect_special_scene_actions_20261028 import ROOT,read,sha,write
from current_student_policy_20260921 import load_current
from run_video_reference_coverage_20261029 import make_actor
from development_teacher_handoff_20261030 import DevelopmentTeacherHandoff
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
reg=read(ROOT/'outputs/nonrl_v9_full_grid_eligibility_20261030_v1/REGISTRATION.json')
group=next(g for g in reg['catalogue']['groups'] if g['family']=='mlp_scratch' and g['seed']==2026102802)
c=group['ordered_candidates'][0];checkpoint=Path(c['checkpoint']);assert sha(checkpoint)==c['checkpoint_sha256']
folders=[ROOT/'outputs/special_scene_direction_collection_20261029_v9/rod_00/rod',ROOT/'outputs/nonrl_v9_common_eligibility_20261029_v3/evaluations/mlp_scratch_s2026102802_rank1/rod_00/rod']
rows=[]
for folder in folders:
 q=read(folder/'DEMONSTRATION_QUALIFICATION.json')
 for name,h in q['input_hashes'].items():assert sha(folder/name)==h
 config=read(folder/'teacher.json')
 with np.load(folder/'trajectory.npz',allow_pickle=False) as z:obs=z['observation'].copy()
 teacher=make_actor(config);teacher.reset();student=load_current(checkpoint);student.reset();ta=[];sa=[]
 for o in obs:
  teacher.observe(o.copy());ta.append(teacher.act(o[39:45].copy(),.04));sa.append(student.act(o.copy()))
 ta=np.asarray(ta);sa=np.asarray(sa)
 for count in [0,1,125,175,len(obs)]:
  actor=DevelopmentTeacherHandoff(config,checkpoint,count);pred=[];labels=[];roles=[]
  for o in obs:
   actor.observe(o);pred.append(actor.act(o[39:45],.04));labels.append(actor.last_teacher_action.copy());roles.append(actor.last_behavior_role)
  np.testing.assert_array_equal(labels,ta)
  np.testing.assert_array_equal(pred,np.concatenate([sa[:count],ta[count:]]))
  assert roles==['student_prefix']*count+['executed_teacher_suffix']*(len(obs)-count)
  actor.reset();actor.observe(obs[0]);np.testing.assert_array_equal(actor.act(obs[0,39:45]),sa[0] if count else ta[0])
  rows.append(dict(folder=str(folder),student_steps=count,teacher_suffix_steps=len(obs)-count,exact_independent_history_replay=True,trajectory_sha256=sha(folder/'trajectory.npz'),teacher_config_sha256=sha(folder/'teacher.json')))
config=read(folders[0]/'teacher.json');rejections=[]
for bad in [-1,True,1.5]:
 try:DevelopmentTeacherHandoff(config,checkpoint,bad)
 except ValueError:rejections.append(repr(bad))
 else:raise AssertionError('Bad schedule accepted')
actor=DevelopmentTeacherHandoff(config,checkpoint,125)
for name,operation,error in [('act_without_observe',lambda:actor.act(np.zeros(6)),RuntimeError),('wrong_shape',lambda:actor.observe(np.zeros(49)),ValueError)]:
 try:operation()
 except error:rejections.append(name)
 else:raise AssertionError(name)
actor.observe(np.zeros(48))
for name,operation,error in [('duplicate_observe',lambda:actor.observe(np.zeros(48)),RuntimeError),('wrong_dt',lambda:actor.act(np.zeros(6),.02),ValueError),('wrong_wrench',lambda:actor.act(np.ones(6)),AssertionError)]:
 try:operation()
 except error:rejections.append(name)
 else:raise AssertionError(name)
assert sha(checkpoint)==c['checkpoint_sha256']
write(a.output,dict(status='handoff_saved_history_controls_passed_no_physics',rows=rows,rejections=rejections,checkpoint_sha256=sha(checkpoint),source_sha256={str(x):sha(x) for x in [Path(__file__),ROOT/'tools/development_teacher_handoff_20261030.py']},
 physics_integrations=0,new_demonstrations=0,new_fits=0,final_test_performed=False,
 limitations=['Replay verifies the switch and label provenance only; no recovery dynamics or new training labels are validated.', 'No collector/registration/dispatch yet. Actual suffix safety/task/rejoin must be separately audited before training.', 'Schedule is a data-collection operator, not a manual recovery added to any evaluated method.']))
print(len(rows),len(rejections))
