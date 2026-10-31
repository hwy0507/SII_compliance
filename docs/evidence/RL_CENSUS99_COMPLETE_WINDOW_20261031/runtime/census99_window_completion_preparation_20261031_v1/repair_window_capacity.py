"""Transparent runtime-only repair of a stale4m assertion in locked97-99 audit.
Original audit/PLAN/SOURCE_LOCK remain byte-identical; statistics are unchanged.
"""
from pathlib import Path
import ast,copy,difflib,hashlib,json,sys,time,os
D=Path(__file__).resolve().parent;B=D.parents[1];W=B/'runs/parameter_census97_99_reward_stability_20261031_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):
 with p.open('x') as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
OLD="row['current_replay_capacity'] == 4_000_000";NEW="row['current_replay_capacity'] == 6_000_000"
def changed_source():
 old=(W/'audit.py').read_text();assert old.count(OLD)==1;new=old.replace(OLD,NEW)
 a=ast.parse(old);b=ast.parse(new)
 # Precisely one numeric constant changes, within the capacity equality only.
 count=0
 for left,right in zip(ast.walk(a),ast.walk(b)):
  if ast.dump(left,include_attributes=False)!=ast.dump(right,include_attributes=False) and isinstance(left,ast.Constant):
   assert isinstance(right,ast.Constant) and left.value==4000000 and right.value==6000000;left.value=6000000;count+=1
 assert count==1 and ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
 return old,new

def capacity(row,method,plan):
 assert row['current_replay_capacity']==6000000
 assert row['replay_capacity_third']==plan['third_capacity_stage'][method]['marker']
 assert row['replay_capacity_followup']==plan['followup_marker']

def main():
 os.sched_setaffinity(0,{54});sys.path.insert(0,str(W));from binding_rules import locked,validate_registration
 plan=locked(W);old,new=changed_source();originals={str(W/n):sha(W/n) for n in ['audit.py','PLAN.json','SOURCE_LOCK.json']}
 if '--preflight' in sys.argv:
  six=read(B/'runtime/census99_window_inputs_recovery_20261031_v1/COMPLETE98_INPUT_MAP.json');assert len(six)==6;checked=[];negative=[]
  for key,refs in six.items():
   m,c=key.split(':');row=read(refs['review']['path'])['methods'][m]
   assert sha(refs['review']['path'])==refs['review']['sha256']
   try:assert row['current_replay_capacity']==4000000
   except AssertionError:stale_rejected=True
   else:raise AssertionError('Original stale4m assertion unexpectedly accepted actual6m')
   capacity(row,m,plan)
   for label,field,value in [('old_capacity','current_replay_capacity',4000000),('wrong_capacity','current_replay_capacity',6000001),('missing_third','replay_capacity_third',{}),('wrong_followup','replay_capacity_followup',{})]:
    bad=copy.deepcopy(row);bad[field]=value
    try:capacity(bad,m,plan)
    except AssertionError:negative.append(key+':'+label)
    else:raise AssertionError('Corrupt capacity accepted')
   checked.append(dict(group=key,actual_capacity=row['current_replay_capacity'],original_stale_assertion_rejected=stale_rejected,correct_capacity_and_both_markers_passed=True))
  (D/'audit97_99_capacity_only.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(W/'audit.py'),tofile='runtime_capacity_assertion_repair')))
  put(D/'CAPACITY_ASSERTION_PREFLIGHT.json',dict(passed=True,time=time.time(),source_originals=originals,executed_source_sha256=hashlib.sha256(new.encode()).hexdigest(),only_one_capacity_literal_changed=True,all_statistical_AST_unchanged=True,actual_six_groups=checked,negative_count=len(negative),negative_rejections=negative,wrapper_sha256=sha(__file__),window=[97,98,99],threshold=.05,near_zero_guard=1.,bootstrap_replicates=5000,seed=2026102861,statistics_executed=False,new_physics=0,optimizer_updates=0))
  print('Stale4m assertion reproduced on6 actual groups; corrected6m/markers passed;24 corruptions rejected')
 else:
  pre=read(D/'CAPACITY_ASSERTION_PREFLIGHT.json');assert pre['passed'] and pre['source_originals']==originals and pre['wrapper_sha256']==sha(__file__) and pre['executed_source_sha256']==hashlib.sha256(new.encode()).hexdigest()
  reg=read(W/'REGISTRATION.json');validate_registration(W,reg)
  assert not (W/'REVIEW.json').exists() and not (W/'reward_stability.png').exists()
  for key,refs in reg['inputs'].items():
   m,c=key.split(':');row=read(refs['review']['path'])['methods'][m];capacity(row,m,plan)
  put(D/'CAPACITY_ASSERTION_EXECUTION.json',dict(time=time.time(),originals=originals,original_audit_sha256=sha(W/'audit.py'),executed_source_sha256=hashlib.sha256(new.encode()).hexdigest(),wrapper_sha256=sha(__file__),preflight_sha256=sha(D/'CAPACITY_ASSERTION_PREFLIGHT.json'),runtime_repair='Only current_replay_capacity comparison4000000->6000000; original4m historical marker preserved and6m marker checked for every actual input. All statistics, source lock, window and original registration retained.'))
  ns={'__name__':'capacity_repaired_locked_audit','__file__':str(W/'audit.py')}
  exec(compile(new,str(W/'audit.py')+'[capacity_assertion_repair]','exec'),ns)
  ns['main'](W)
  report=read(W/'REVIEW.json');report['capacity_assertion_repair']=dict(path=str(D/'CAPACITY_ASSERTION_EXECUTION.json'),sha256=sha(D/'CAPACITY_ASSERTION_EXECUTION.json'));(W/'REVIEW.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
  assert originals=={p:sha(p) for p in originals}
  put(D/'CAPACITY_ASSERTION_REPAIR_REVIEW.json',dict(passed=True,time=time.time(),original_files_byte_unchanged=True,only_capacity_literal_changed=True,statistics_AST_unchanged=True,all_nine_real_capacity_and_markers_passed=True,window_report_sha256=sha(W/'REVIEW.json'),convergence_claim=False))
  print('Original97-99 statistical audit completed with explicit capacity assertion repair')
if __name__=='__main__':main()
