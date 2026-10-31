from pathlib import Path
import os,sys,time,json,hashlib,subprocess
B=Path(__file__).resolve().parents[2];D=B/'runtime/census97_terminal_20261031_v1';O=B/'runs/census97_fixed96_terminal_20261031_v1';R=B/'runs/parameter_census_cycle97_20261031_v1';T=B/'runtime/census97_continuation_20261031_v1'
sys.path[:0]=[str(T),str(D)];from driver import read,put,sha,validate_checkpoint
os.sched_setaffinity(0,{11});deadline=time.time()+1200
while not (R/'startup/REVIEW.json').exists():
 assert time.time()<deadline
 for k in ['STARTUP','MONITOR']:
  j=read(R/(k+'_LAUNCH.json'));s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['proc_start_ticks']
 time.sleep(5)
assert read(R/'startup/REVIEW.json')['passed'];import torch
torch.set_num_threads(1);methods={}
for m in ['impedance','admittance','vmc']:
 cp=R/'startup'/(m+'.pt');ck=torch.load(cp,map_location='cpu',weights_only=False,mmap=True);reg=read(R/m/'REGISTRATION.json');validate_checkpoint(ck,reg,complete=False)
 try:validate_checkpoint(ck,reg,complete=True)
 except ValueError as e:assert str(e)=='Complete97 required'
 else:raise AssertionError('Partial accepted as full97')
 methods[m]=dict(steps=ck['steps'],checkpoint_sha256=sha(cp),boundary=ck['boundary'],complete97_rejected=True);del ck
put(O/'PARTIAL_REJECTION_REVIEW.json',dict(passed=True,time=time.time(),methods=methods,new_physics=0,optimizer_updates=0));assert not (O/'WAIT_LAUNCH.json').exists()
with (O/'wait.log').open('x') as log:p=subprocess.Popen([str(B/'env/bin/python'),str(D/'wait_terminal97.py')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=D,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
s=Path('/proc',str(p.pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z'
put(O/'WAIT_LAUNCH.json',dict(time=time.time(),pid=p.pid,proc_start_ticks=s[19],script_sha256=sha(D/'wait_terminal97.py'),wait_deadline_unix=read(O/'PLAN.json')['wait_deadline_unix'],physics_steps=0,optimizer_updates=0))
print('All actual partial97 rejected complete gate; one bounded terminal consumer waiting',p.pid,flush=True)
