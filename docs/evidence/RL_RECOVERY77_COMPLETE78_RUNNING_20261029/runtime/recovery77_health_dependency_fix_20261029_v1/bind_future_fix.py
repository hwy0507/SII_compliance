from pathlib import Path
import json,time,hashlib,ast,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;F=B/'runs/parameter_partial75_recovery_cycle78_review_20261029_v1';P=B/'runtime/prepare_recovery78_20261029_v1';C=B/'runtime/recovery78_completion_preparation_20261029_v1';OLD=B/'runs/parameter_partial75_recovery_cycle76_review_20261029_v1';V=B/'runs/parameter_partial75_recovery_cycle77_review_20261029_v1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
name='diagnose_published_value_bound_20261025.py';assert sha(F/name)==sha(OLD/name)==sha(V/name)
item=dict(path=str(F/name),name=name,source=str(OLD/name),parent_sha256=sha(OLD/name),sha256=sha(F/name))
for folder,n in [(F,'SOURCE_REVIEW.json'),(P,'FUTURE_REVIEW_SOURCE_REVIEW.json')]:
 p=folder/n;backup=folder/(n+'.before_dependency_fix');assert not backup.exists();backup.write_bytes(p.read_bytes());j=read(p);j['files'].append(item);j['dependency_fix']=ref(D/'DEPENDENCY_REPAIR.json');write(p,j)
p=C/'decision78.py';old=p.read_text();needle=" assert read(PREP/'FINISHED.json')['prepared'] and read(OUT/'CHECK_ONLY_COMPLETE.json')['passed']";assert needle in old
insert=""" fix=B/'runtime/recovery77_health_dependency_fix_20261029_v1'
 assert read(fix/'HEALTH_RECOVERY_REVIEW.json')['passed']
 completion=read(PARENT/'ARCHIVE_REVIEW_FINISHED.json')
 assert sha(completion['original_failure']['path'])==completion['original_failure']['sha256']
 assert completion['recovery']==ref(fix/'HEALTH_RECOVERY_REVIEW.json')
 for item in read(fix/'DEPENDENCY_REPAIR.json')['destinations']:assert sha(item['path'])==item['sha256']
 for role in ['labels','vmc','admittance','restore78']:assert read(fix/(role+'_RECOVERY_REVIEW.json'))['passed']
"""
new=old.replace(needle,insert+needle);needle=" for m in ['impedance','admittance','vmc']:required['restore_'+m]=OUT/m/'CHECK_ONLY_REVIEW.json'";assert needle in new
new=new.replace(needle," for n in ['DEPENDENCY_REPAIR.json','HEALTH_RECOVERY_REVIEW.json','labels_RECOVERY_REVIEW.json','vmc_RECOVERY_REVIEW.json','admittance_RECOVERY_REVIEW.json','restore78_RECOVERY_REVIEW.json']:required['recovery77_'+n]=fix/n\n"+needle)
ast.parse(new);backup=C/'decision78_before_dependency_fix.py';assert not backup.exists();backup.write_text(old);p.write_text(new);(C/'decision78_dependency_fix.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(backup),tofile=str(p))))
p=C/'LAUNCH_SOURCE_REVIEW.json';backup=C/'LAUNCH_SOURCE_REVIEW_BEFORE_DEPENDENCY_FIX.json';assert not backup.exists();backup.write_bytes(p.read_bytes());j=read(p)
for v in j['files']:
 if v['path']==str(C/'decision78.py'):v['sha256']=sha(C/'decision78.py')
j['files'] += [ref(x) for x in [F/name,V/name,D/'repair_and_health.py',D/'postprocess.py']];j['dependency_fix']=ref(D/'DEPENDENCY_REPAIR.json');j['time']=time.time();write(p,j)
write(D/'FUTURE_BINDING_REVIEW.json',dict(passed=True,time=time.time(),no_decision78=not (C/'DECISION78.json').exists(),source_binding=ref(p),diagnostic_math_unchanged=True,original_failure_retained=True))
print('Future78 helper and explicit recovery evidence bound; no scientific source changes')
