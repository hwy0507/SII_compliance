from pathlib import Path
import json,copy,time,subprocess,os,sys,hashlib,ast
R=Path(__file__).parent; O=R.parents[1]/'runs'/R.name
sys.path.insert(0,str(R))
from evaluate_parameter86_half_std_20261030 import validate_design,validate_recovery,sha,write
plan=json.loads((O/'PLAN.json').read_text());jobs=[];checks=[]
for group in plan['groups']:
 regpath=O/group/'REGISTRATION.json';reg=json.loads(regpath.read_text());validate_design(reg)
 cases={'seed':[1,2,3,4],'parent':85,'case':['active_short_train_0337'],'cpu':54,'device':'cuda:3','checkpoint_hash':'0'*64,'source_hash':{},'gate':'wrong','plan_hash':'0'*64,'std_factor':1.0}
 keymap={'seed':'action_seeds','parent':'parent_cycle','case':'case_ids','cpu':'cpu','device':'device','checkpoint_hash':'checkpoint_sha256','source_hash':'source_hashes','gate':'gate_case_id','plan_hash':'plan_sha256','std_factor':'pre_tanh_std_factor'}
 for name,value in cases.items():
  bad=copy.deepcopy(reg);bad[keymap[name]]=value
  try:validate_design(bad)
  except (AssertionError,KeyError,ValueError):checks.append(dict(group=group,mutation=name,rejected=True))
  else:raise AssertionError((group,name,'accepted'))
 protocol=json.loads(Path(reg['training_registration']).read_text())
 ck=dict(cycle=86,boundary='complete_condition_cycle',environment_state_saved=False,interruption_recovery=protocol['interrupted_episode_recovery'],recovery_continuation=protocol['post_interruption_continuation'],cycles=[{'cycle':86}])
 validate_recovery(ck,protocol,86)
 for name,key,value in [('partial_boundary','boundary','interrupted'),('wrong_parent','cycle',85),('environment_saved','environment_state_saved',True),('partial75_in_history','cycles',[{'cycle':75},{'cycle':86}])]:
  bad=copy.deepcopy(ck);bad[key]=value
  try:validate_recovery(bad,protocol,86)
  except AssertionError:checks.append(dict(group=group,mutation=name,rejected=True))
  else:raise AssertionError(name)
 assert not (regpath.parent/'EVALUATION.json').exists()
 command=[sys.executable,str(R/'evaluate_parameter86_half_std_20261030.py'),'--registration',str(regpath),'--check-only']
 with (regpath.parent/'check_only.log').open('x') as f:
  p=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 jobs.append((group,p,command))
write(O/'DESIGN_NEGATIVE_REVIEW.json',dict(passed=True,tests=checks,negative_count=len(checks),new_physics=0,new_optimizer_updates=0,plan_sha256=sha(O/'PLAN.json')))
write(O/'CHECK_LAUNCH.json',dict(time=time.time(),jobs=[dict(group=g,pid=p.pid,command=c) for g,p,c in jobs]))
for group,p,c in jobs:
 code=p.wait();assert code==0,(group,code)
 result=json.loads((O/group/'CHECK_ONLY_REVIEW.json').read_text());assert result['passed'] and result['full_replay_restored_exact'] and result['full_learner_state_unchanged']
 assert not (O/group/'EVALUATION.json').exists()
write(O/'CHECKS_FINISHED.json',dict(passed=True,time=time.time(),groups=list(plan['groups']),new_physics=0,new_optimizer_updates=0,negative_tests=len(checks)))
print('ALL FOUR CHECKS PASSED')
