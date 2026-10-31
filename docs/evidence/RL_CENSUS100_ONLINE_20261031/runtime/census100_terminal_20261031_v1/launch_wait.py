from pathlib import Path
import os,sys,json,time,subprocess
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census100_fixed99_terminal_20261031_v1';T=B/'runtime/census100_continuation_20261031_v1';R=B/'runs/parameter_census_cycle100_20261031_v1'
sys.path.insert(0,str(D));from terminal100 import read,put,sha,inputs
sys.path.insert(0,str(T));from driver import validate_checkpoint
import torch
os.sched_setaffinity(0,{11});torch.set_num_threads(1)
p=inputs(read(O/'PLAN.json'));assert read(R/'startup/REVIEW.json')['passed'];results={}
for m in p['methods']:
 cp=R/'startup'/(m+'.pt');ck=torch.load(cp,map_location='cpu',weights_only=False,mmap=True);reg=read(R/m/'REGISTRATION.json');validate_checkpoint(ck,reg,complete=False)
 try:validate_checkpoint(ck,reg,complete=True)
 except (ValueError,AssertionError):rejected=True
 else:raise AssertionError('Actual partial100 accepted as complete')
 results[m]=dict(actual_partial_rejected=rejected,steps=ck['steps'],snapshot_sha256=sha(cp));del ck
put(O/'PARTIAL_REJECTION_REVIEW.json',dict(passed=True,time=time.time(),methods=results,physics_steps=0,optimizer_updates=0))
assert read(O/'PREFLIGHT_REVIEW.json')['passed'] and not (O/'PROCESS.json').exists()
with (O/'wait.log').open('x') as log:
 proc=subprocess.Popen([str(B/'env/bin/python'),str(D/'wait_terminal100.py')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'),cwd=D)
s=Path('/proc',str(proc.pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z'
put(O/'PROCESS.json',dict(pid=proc.pid,proc_start_ticks=s[19],time=time.time(),command=[str(B/'env/bin/python'),str(D/'wait_terminal100.py')],source_sha256=sha(D/'wait_terminal100.py'),launch_source_sha256=sha(__file__)))
print('Fixed8893 terminal consumer waiting',proc.pid,flush=True)
