"""Launch exactly one recovery80 after explicit full78 decision; never automatic80."""
from pathlib import Path
import json,time,hashlib,subprocess,os,importlib.util
from decision80 import B,D,PREP,OUT,collect,read,sha,ref
assert (D/'DECISION80.json').exists(),'Explicit reviewed DECISION80 required'
assert not (OUT/'LAUNCH.json').exists()
decision=read(D/'DECISION80.json');assert decision['passed'] and decision['plot_inspected'] and not decision['convergence_claim'] and not decision['automatic_followup'] and not decision['configuration_changed'] and decision['parent_cycle']==78 and decision['new_cycle']==80 and decision['new_cycles']==1
assert decision['evidence']==collect()
registrations={}
spec=importlib.util.spec_from_file_location('checked_recovery80',PREP/'resume_recovery78.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
for m in ['impedance','admittance','vmc']:
 p=read(OUT/m/'REGISTRATION.json');st=p['post_interruption_continuation'];assert st['driver_sha256']==sha(PREP/'resume_recovery78.py');driver.validate_protocol(st['parent_registration']['sha256'],p,sha(OUT/m/'REGISTRATION.json'));assert sha(st['checkpoint']['path'])==st['checkpoint']['sha256'];assert not (OUT/m/'train').exists();registrations[m]=sha(OUT/m/'REGISTRATION.json')
def write(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2)+'\n')
write(OUT/'PRELAUNCH_REVIEW.json',dict(passed=True,time=time.time(),registration_hashes=registrations,decision=ref(D/'DECISION80.json'),new_cycles=1,automatic_followup=False))
(OUT/'startup_review.py').write_bytes((PREP/'startup80.py').read_bytes());assert sha(OUT/'startup_review.py')==sha(PREP/'startup80.py')
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');jobs=read(OUT/'COMMANDS.json')['jobs']
for j in jobs:
 with (OUT/(j['controller']+'_driver.log')).open('x') as f:p=subprocess.Popen(j['command'],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 j.update(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time())
write(OUT/'LAUNCH.json',dict(time=time.time(),jobs=jobs,new_cycles=1,automatic_followup=False))
for name,script in [('MONITOR',PREP/'archive80.py'),('STARTUP',OUT/'startup_review.py')]:
 with (OUT/(name.lower()+'.log')).open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(script)],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 write(OUT/(name+'_LAUNCH.json'),dict(time=time.time(),pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],script_sha256=sha(script)))
subprocess.run([str(B/'env/bin/python'),str(D/'deploy_loss80.py')],check=True,env=env)
print('Finite80 science/startup/archive and full loss waiter launched; automatic80 false')
