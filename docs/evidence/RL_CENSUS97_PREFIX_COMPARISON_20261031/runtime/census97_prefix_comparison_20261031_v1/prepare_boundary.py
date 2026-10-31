from pathlib import Path
import json,hashlib,time,ast,sys,copy,subprocess,os
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census97_capacity_boundary_20261031_v1';R=B/'runs/parameter_census_cycle97_20261031_v1';S=B/'runtime/census97_continuation_20261031_v1';O.mkdir()
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
from boundary import audit_arrays
import numpy as np
old=dict(rewards=np.array([[1],[2],[3]],np.float32),dones=np.array([[0],[0],[1]],np.float32),observations=np.arange(6,dtype=np.float32).reshape(3,2),masks=np.ones((3,5),np.float32));arr={k:np.concatenate([v,v[:2]]) for k,v in old.items()};ts=[dict(step=4,reward=1.,done=False),dict(step=5,reward=2.,done=False)];assert audit_arrays(arr,old,5,ts)==3
rejected=[]
for case in ['old_overwrite','wrong_new_reward','wrong_new_done','nonfinite_observation','nonbinary_mask','missing_field','wrong_shape','wrong_step']:
 a=copy.deepcopy(arr);t=copy.deepcopy(ts)
 if case=='old_overwrite':a['observations'][0,0]+=1
 elif case=='wrong_new_reward':a['rewards'][3,0]+=1
 elif case=='wrong_new_done':a['dones'][3,0]=1
 elif case=='nonfinite_observation':a['observations'][4,1]=np.nan
 elif case=='nonbinary_mask':a['masks'][4,0]=.5
 elif case=='missing_field':a.pop('masks')
 elif case=='wrong_shape':a['observations']=a['observations'][:4]
 elif case=='wrong_step':t[-1]['step']+=1
 try:audit_arrays(a,old,5,t)
 except (ValueError,AssertionError):rejected.append(case)
 else:raise AssertionError('Corruption accepted: '+case)
methods={};jobs=read(R/'LAUNCH.json')['jobs']
for j in jobs:
 m=j['controller'];reg=R/m/'REGISTRATION.json';p=read(reg);st=p['post_interruption_continuation'];assert st['parent_steps']<4000000<st['parent_steps']+41250;assert read(R/m/'train/PROGRESS.json')['steps']<4000000
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['proc_start_ticks'];methods[m]=dict(process=j,registration=ref(reg),parent_checkpoint=st['checkpoint'],parent_steps=st['parent_steps'])
ast.parse((D/'boundary.py').read_text());p=dict(time=time.time(),source_sha256=sha(D/'boundary.py'),runtime=str(S),runtime_sources=read(S/'SOURCES.json')['files'],methods=methods,boundary=4000000,deadline_unix=min(j['time'] for j in jobs)+14400,snapshot_limit_per_method=1,physics_steps=0,optimizer_updates=0,scope='Read-only actual4m boundary retention audit, registered before every method reaches4m; no training/restart/overwrite.')
put(O/'PLAN.json',p);put(O/'PREFLIGHT_REVIEW.json',dict(passed=True,time=time.time(),original_prefix_and_new_rows_accepted=True,rejected=rejected,negative_count=len(rejected),all_three_current_steps_below4m=True,source_sha256=sha(D/'boundary.py'),physics_steps=0,optimizer_updates=0))
with (O/'wait.log').open('x') as f:proc=subprocess.Popen([str(B/'env/bin/python'),str(D/'boundary.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,cwd=D,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
s=Path('/proc',str(proc.pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z';put(O/'LAUNCH.json',dict(time=time.time(),pid=proc.pid,proc_start_ticks=s[19],source_sha256=sha(D/'boundary.py'),deadline_unix=p['deadline_unix']));print('Finite boundary audit waiting',proc.pid)
