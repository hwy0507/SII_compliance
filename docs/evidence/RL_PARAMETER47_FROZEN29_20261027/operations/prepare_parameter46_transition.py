from pathlib import Path
import json,hashlib,shutil,subprocess,os,time,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
def identity(pid):
 p=Path(f'/proc/{pid}');s=(p/'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z';return dict(start_ticks=s[19],command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def launch(cmd,out):
 with (out/'driver.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 write(out/'LAUNCH.json',dict(pid=p.pid,time=time.time(),command=cmd,identity=identity(p.pid)));return p.pid
O=B/'runs/parameter46_transition_20261027_v1';O.mkdir();old=B/'runs/parameter45_serl27_transition_20261027_v1/observe.py';shutil.copyfile(old,O/'observe.py')
parents=[1829718,1829722,1829726];review=1829785;ids={str(pid):identity(pid) for pid in parents+[review]}
for pid in parents:assert 'parameter_capacity_pool30_cycle46_20261026_v1/resume_' in ids[str(pid)]['command']
assert 'parameter_capacity_pool30_cycle46_review_20261026_v1/coordinator.py' in ids[str(review)]['command']
g=dict(name='parameter46_to47',parents=parents,review_pid=review,review_run='parameter_capacity_pool30_cycle46_review_20261026_v1',cpu=13,next_run='parameter_capacity_pool30_cycle47_20261026_v1',identities=ids)
write(O/'PLAN.json',dict(time=time.time(),groups=[g],budget_seconds=1800,interval_seconds=2,automatic_training=False,action='Only original complete review processes may move to releasedCPU13 after all original46 learners exit; formal/frozen jobs unchanged.',source_sha256=hashlib.sha256(old.read_bytes()).hexdigest()))
observer=launch([str(B/'env/bin/python'),str(O/'observe.py')],O)
S=B/'runs/parameter46_saved_review_20261027_v1';S.mkdir();s=(B/'runs/parameter45_saved_review_20261027_v1/review_saved.py').read_text().replace('cycle45','cycle46').replace("['cycle']==45","['cycle']==46").replace('Original45','Original46');ast.parse(s);(S/'review_saved.py').write_text(s)
reviewer=launch([str(B/'env/bin/python'),str(S/'review_saved.py')],S)
print(dict(observer=observer,saved_review=reviewer))
