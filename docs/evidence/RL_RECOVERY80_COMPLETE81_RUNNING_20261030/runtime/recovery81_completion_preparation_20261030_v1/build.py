from pathlib import Path
import ast,json,time,hashlib,difflib,re,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;PREP=B/'runtime/prepare_recovery81_20261030_v1';OLD=B/'runtime/recovery80_completion_preparation_20261030_v1';ACTUAL=B/'runtime/recovery80_abort_aware_decision_20261030_v2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
s=(OLD/'decision80.py').read_text()
# Only named current/parent paths and labels change; old76-78 and prospective79-81 stay exact.
replacements={
'runtime/prepare_recovery80_20261029_v1':'runtime/prepare_recovery81_20261030_v1',
'parameter_partial75_recovery_cycle80_20261029_v1':'parameter_partial75_recovery_cycle81_20261029_v1',
'parameter_partial75_recovery_cycle79_20261029_v1':'parameter_partial75_recovery_cycle80_20261029_v1',
'parameter_partial75_recovery_cycle79_review_20261029_v1':'parameter_partial75_recovery_cycle80_review_20261029_v1',
'parameter_recovery79_loss_20261029_v1':'parameter_recovery80_loss_20261029_v1',
'parameter_recovery79_task_labels_20261029_v1':'parameter_recovery80_task_labels_20261029_v1',
'runtime/recovery79_completion_preparation_20261029_v1/DECISION79.json':'runtime/recovery80_abort_aware_decision_20261030_v2/DECISION80.json',
"evidence['prior79_decision']":"evidence['prior80_decision']", "evidence['prior79_'+k]":"evidence['prior80_'+k]",
'COMPLETE78_79':'COMPLETE79_80','_recovery79_terminal_followup_':'_recovery80_terminal_followup_',"r['fixed_anchor_rows']==2334":"r['fixed_anchor_rows']==2364",
'Complete79':'Complete80','Original79':'Original80','full79':'full80','Full79':'Full80','exact80':'exact81',
'parent_cycle=79,new_cycle=80':'parent_cycle=80,new_cycle=81',"(D/'DECISION80.json')":"(D/'DECISION81.json')"
}
for a,z in replacements.items():assert a in s,a;s=s.replace(a,z)
s=s.replace("assert old['passed'];evidence", "assert old['passed'] and old['parent_cycle']==79 and old['new_cycle']==80 and old['decision_rule_version']==2 and old['prior_safety_abort_preserved'];evidence")
assert "'5cf5efb87a63b432091276c3b96a3b16126c2ab891a2e195b6c857e93cf110a0'" in s and "['cycles']==[79,80,81]" in s
assert "'57b3d6be84b8b384922a35879ddfd5cd1c6e7a6b71b35ca5652c2ddfc8cd4e85'" in s and "['cycles']==[76,77,78]" in s
assert "r['new_transitions']==41250" in s and "r['aborts']==[]" in s
launch=(ACTUAL/'launch80.py').read_text();launch=re.sub('79|80|81',lambda m:{'79':'80','80':'81','81':'82'}[m[0]],launch);launch=launch.replace('explicit full80 version2 decision','explicit full80 reviewed decision')
loss=(ACTUAL/'deploy_loss80.py').read_text().replace('80','81')
files=[]
for name,src,parent in [('decision81.py',s,OLD/'decision80.py'),('launch81.py',launch,ACTUAL/'launch80.py'),('deploy_loss81.py',loss,ACTUAL/'deploy_loss80.py')]:
 ast.parse(src);(D/name).write_text(src);(D/(name+'.diff')).write_text(''.join(difflib.unified_diff(parent.read_text().splitlines(True),src.splitlines(True),fromfile=str(parent),tofile=str(D/name))));files.append(dict(**ref(D/name),parent=ref(parent)))
# Catch the prior stale launcher-reference bug before any real decision exists.
assert "decision['parent_cycle']==80" in launch and "decision['new_cycle']==81" in launch
assert launch.count('resume_recovery80.py')==2 and 'resume_recovery79.py' not in launch and (PREP/'resume_recovery80.py').exists()
for n in ['resume_recovery80.py','startup81.py','archive81.py']:files.append(ref(PREP/n))
put(D/'LAUNCH_SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=files,original76_78_complete_results_required=True,prospective79_81_exact_plan_required=True,prior80_version2_and_known79_abort_bound=True,full80_and_four_actual_plots_required=True,accurate81_restore_required=True,full80_no_abort_guard=True,automatic_training=False))
results=[]
for name,expected in [('decision81.py','Complete80 archive/review not ready'),('launch81.py','Explicit reviewed DECISION81 required'),('deploy_loss81.py','LAUNCH.json')]:
 p=subprocess.run([str(B/'env/bin/python'),str(D/name)],capture_output=True,text=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
 assert p.returncode!=0 and expected in p.stderr,(name,p.returncode,p.stderr)
 row=dict(passed=True,time=time.time(),source=ref(D/name),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,expected=expected,new_physics=0,new_updates=0);put(D/(name+'.REJECTION.json'),row);results.append(name)
assert not (D/'DECISION81.json').exists() and not (D/'CONTINUATION_REASON.txt').exists() and not (B/'runs/parameter_partial75_recovery_cycle81_20261029_v1').exists()
put(D/'PREPARATION_REVIEW.json',dict(passed=True,time=time.time(),actual_missing_prerequisites_rejected=results,actual_complete80_not_available=True,source_reference_checks=True,decision_written=False,training81=False,configuration_changed=False,original_failed79_preserved=True,full80_aborts_if_any_require_explicit_review_not_silent_guard_change=True))
print('81 decision/launcher/loss dispatch prepared;3 actual missing prerequisites rejected, no81 outputs.')
