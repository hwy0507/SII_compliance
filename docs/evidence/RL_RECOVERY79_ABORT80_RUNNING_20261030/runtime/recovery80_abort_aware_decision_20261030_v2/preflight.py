from pathlib import Path
import os,json,copy,time,importlib.util,ast,subprocess
from decision80 import B,D,PREP,OUT,REV,read,sha,ref,validate_cycle
full=read(REV/'REVIEW.json');diag=read(B/'runs/impedance_recovery79_abort_review_20261030_v1/FINAL_REVIEW.json');rejected=[]
for m,r in full['methods'].items():validate_cycle(m,r,diag)
for m,key,value in [('impedance','new_transitions',41250),('impedance','full_horizon_count',30),('impedance','aborts',[]),('impedance','aborts',full['methods']['impedance']['aborts']*2),('impedance','checkpoint_sha256','wrong'),('impedance','retained_replay_all_fields_exact',False),('impedance','max_reward_reconstruction_error',1e-4),('impedance','optimizer_and_network_finite',False),('impedance','task',18),('impedance','steps',3277148),('admittance','aborts',full['methods']['impedance']['aborts']),('vmc','new_transitions',40550)]:
 r=copy.deepcopy(full['methods'][m]);r[key]=value
 try:validate_cycle(m,r,diag)
 except AssertionError:rejected.append(dict(method=m,key=key))
 else:raise RuntimeError('Invalid fixture accepted')
def write(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
write(D/'RULE_TESTS.json',dict(passed=True,time=time.time(),actual_three_positive=True,negative_refusals=rejected,original_no_abort_refusal=ref(B/'runtime/recovery80_completion_preparation_20261030_v1/COMPLETE79_ABORT_REJECTION.json'),new_physics=0,new_updates=0))
# Read and import the exact real driver; no trainer/check-only execution.
spec=importlib.util.spec_from_file_location('exact80_driver',PREP/'resume_recovery79.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
commands=read(OUT/'COMMANDS.json')['jobs'];assert len(commands)==3;verified=[]
for j in commands:
 m=j['controller'];cmd=j['command'];assert cmd[:2]==[str(B/'env/bin/python'),str(PREP/'resume_recovery79.py')]
 reg=read(OUT/m/'REGISTRATION.json');st=reg['post_interruption_continuation'];assert st['driver_sha256']==sha(cmd[1]);driver.validate_protocol(st['parent_registration']['sha256'],reg,sha(OUT/m/'REGISTRATION.json'))
 assert sha(st['checkpoint']['path'])==st['checkpoint']['sha256']==full['methods'][m]['checkpoint_sha256']
 assert cmd[cmd.index('--resume')+1]==st['checkpoint']['path'] and cmd[cmd.index('--registration')+1]==str(OUT/m/'REGISTRATION.json')
 assert set(map(int,cmd[cmd.index('--cpus')+1].split(',')))<=os.sched_getaffinity(0)
 assert cmd[cmd.index('--workers')+1]=='30' and not (OUT/m/'train').exists()
 verified.append(dict(controller=m,command=cmd,registration=ref(OUT/m/'REGISTRATION.json'),driver=ref(cmd[1]),checkpoint=st['checkpoint']))
assert 52 in os.sched_getaffinity(0) and 53 in os.sched_getaffinity(0)
launch=(D/'launch80.py').read_text();ast.parse(launch)
assert "decision['parent_cycle']==79" in launch and 'resume_recovery78.py' not in launch and launch.count('resume_recovery79.py')==2
assert os.environ.get('CUDA_VISIBLE_DEVICES')!=''
for x in read(D/'LAUNCH_SOURCE_REVIEW.json')['files']:assert sha(x['path'])==x['sha256']
p=subprocess.run([str(B/'env/bin/python'),str(D/'launch80.py')],capture_output=True,text=True);assert p.returncode!=0 and 'Explicit reviewed DECISION80 required' in p.stderr and not (OUT/'LAUNCH.json').exists()
write(D/'PREFLIGHT.json',dict(passed=True,time=time.time(),three_actual_registrations_and_commands_validated=verified,missing_decision_refusal=dict(returncode=p.returncode,stderr=p.stderr),source_references_correct=True,original_v1_wrong_parent78_and_driver78_preserved=True,new_physics=0,new_updates=0))
print('Three actual80 driver/registration/command preflights;12 refusal fixtures; missing decision refusal passed.')
