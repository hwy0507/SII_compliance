from pathlib import Path
import ast,difflib,json,time,hashlib,re,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runtime/recovery77_completion_preparation_20261029_v1';PREP=B/'runtime/prepare_recovery78_20261029_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
paths={
'prepare_recovery77_20261029_v1':'prepare_recovery78_20261029_v1',
'parameter_partial75_recovery_cycle76_20261029_v1':'parameter_partial75_recovery_cycle77_20261029_v1',
'parameter_partial75_recovery_cycle77_20261029_v1':'parameter_partial75_recovery_cycle78_20261029_v1',
'parameter_partial75_recovery_cycle76_review_20261029_v1':'parameter_partial75_recovery_cycle77_review_20261029_v1',
'parameter_recovery76_loss_20261029_v1':'parameter_recovery77_loss_20261029_v1',
'parameter_recovery77_loss_20261029_v1':'parameter_recovery78_loss_20261029_v1',
'parameter_recovery76_task_labels_20261029_v1':'parameter_recovery77_task_labels_20261029_v1',
'_recovery76_terminal_followup_20261029_v1':'_recovery77_terminal_followup_20261029_v1'}
pattern=re.compile('|'.join(map(re.escape,paths)))
for oldname,newname in [('decision77.py','decision78.py'),('launch77.py','launch78.py'),('deploy_loss77.py','deploy_loss78.py')]:
 s=(OLD/oldname).read_text();v=pattern.sub(lambda m:paths[m[0]],s)
 for a,b in [('full76','full77'),('Full76','Full77'),('Complete76','Complete77'),('Original76','Original77'),('exact77','exact78'),('Exact77','Exact78'),('recovery77 after','recovery78 after'),('automatic78','automatic79'),('Finite77','Finite78'),('decision77','decision78'),('DECISION77','DECISION78'),('deploy_loss77','deploy_loss78'),('checked_recovery77','checked_recovery78'),('resume_recovery76.py','resume_recovery77.py'),('startup77.py','startup78.py'),('archive77.py','archive78.py'),('COMPLETE74_76','COMPLETE76_77'),("r['fixed_anchor_rows']==2244","r['fixed_anchor_rows']==2274"),('parent_cycle=76,new_cycle=77','parent_cycle=77,new_cycle=78'),("decision['parent_cycle']==76 and decision['new_cycle']==77","decision['parent_cycle']==77 and decision['new_cycle']==78")]:v=v.replace(a,b)
 if newname=='decision78.py':
  oldloop="for prefix,path in [('historical75_',B/'runtime/prepare_parameter75_20261029_v1/DECISION75.json'),('recovery76_',B/'runtime/parameter75_interruption_recovery_20261029_v1/DECISION_RECOVERY76.json')]:"
  assert oldloop in v;v=v.replace(oldloop,"for prefix,path in [('prior77_',B/'runtime/recovery77_completion_preparation_20261029_v1/DECISION77.json')]:")
 ast.parse(v);(D/newname).write_text(v);(D/(newname+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True),fromfile=str(OLD/oldname),tofile=str(D/newname))))
# Bind the complete review/dispatch sources, but do not write a scientific decision.
files=[D/n for n in ['decision78.py','launch78.py','deploy_loss78.py']]+[PREP/n for n in ['resume_recovery77.py','prepare.py','wait_prepare.py','startup78.py','archive78.py']]
for d in [B/'runs/parameter_recovery78_loss_20261029_v1',B/'runs/parameter_partial75_recovery_cycle78_review_20261029_v1']:
 for x in json.loads((d/'SOURCE_REVIEW.json').read_text())['files']:files.append(d/x['name'])
write(D/'LAUNCH_SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=[ref(p) for p in files],automatic_training=False,actual78_not_started=True))
expected={'decision78.py':'Complete77 archive/review not ready','launch78.py':'Explicit reviewed DECISION78 required','deploy_loss78.py':'LAUNCH.json'}
for name,reason in expected.items():
 r=subprocess.run([str(B/'env/bin/python'),str(D/name)],capture_output=True,text=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 assert r.returncode!=0 and reason in r.stderr,(name,r.stderr)
 write(D/(name+'.REJECTION.json'),dict(passed=True,time=time.time(),returncode=r.returncode,stderr=r.stderr,required_reason=reason,no_new_training=True))
assert not (D/'DECISION78.json').exists() and not (B/'runs/parameter_partial75_recovery_cycle78_20261029_v1').exists()
assert "'57b3d6be84b8b384922a35879ddfd5cd1c6e7a6b71b35ca5652c2ddfc8cd4e85'" in (D/'decision78.py').read_text()
write(D/'PREPARATION_REVIEW.json',dict(passed=True,time=time.time(),source_checks=True,actual_incomplete77_refused=True,missing_decision78_refused=True,missing_launch78_refused=True,no_decision=True,no_training=True,scientific_protocol_unchanged=True))
print('78 dispatcher sources ready; three missing-evidence refusals passed; no decision/training')
