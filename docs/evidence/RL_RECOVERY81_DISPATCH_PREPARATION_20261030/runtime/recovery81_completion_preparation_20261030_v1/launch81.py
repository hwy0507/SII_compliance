"""Launch exactly one recovery81 after explicit full80 reviewed decision; never automatic82."""
from pathlib import Path
import json,time,hashlib,subprocess,os,importlib.util
from decision81 import B,D,PREP,OUT,collect,read,sha,ref
assert (D/'DECISION81.json').exists(),'Explicit reviewed DECISION81 required'
assert not (OUT/'LAUNCH.json').exists()
decision=read(D/'DECISION81.json');assert decision['passed'] and decision['plot_inspected'] and not decision['convergence_claim'] and not decision['automatic_followup'] and not decision['configuration_changed'] and decision['parent_cycle']==80 and decision['new_cycle']==81 and decision['new_cycles']==1
assert decision['evidence']==collect()
registrations={}
spec=importlib.util.spec_from_file_location('checked_recovery81',PREP/'resume_recovery80.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
for m in ['impedance','admittance','vmc']:
 p=read(OUT/m/'REGISTRATION.json');st=p['post_interruption_continuation'];assert st['driver_sha256']==sha(PREP/'resume_recovery80.py');driver.validate_protocol(st['parent_registration']['sha256'],p,sha(OUT/m/'REGISTRATION.json'));assert sha(st['checkpoint']['path'])==st['checkpoint']['sha256'];assert not (OUT/m/'train').exists();registrations[m]=sha(OUT/m/'REGISTRATION.json')
def write(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2)+'\n')
write(OUT/'PRELAUNCH_REVIEW.json',dict(passed=True,time=time.time(),registration_hashes=registrations,decision=ref(D/'DECISION81.json'),new_cycles=1,automatic_followup=False))
(OUT/'startup_review.py').write_bytes((PREP/'startup81.py').read_bytes());assert sha(OUT/'startup_review.py')==sha(PREP/'startup81.py')
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');jobs=read(OUT/'COMMANDS.json')['jobs']
for j in jobs:
 with (OUT/(j['controller']+'_driver.log')).open('x') as f:p=subprocess.Popen(j['command'],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 j.update(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time())
write(OUT/'LAUNCH.json',dict(time=time.time(),jobs=jobs,new_cycles=1,automatic_followup=False))
for name,script in [('MONITOR',PREP/'archive81.py'),('STARTUP',OUT/'startup_review.py')]:
 with (OUT/(name.lower()+'.log')).open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(script)],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 write(OUT/(name+'_LAUNCH.json'),dict(time=time.time(),pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],script_sha256=sha(script)))
subprocess.run([str(B/'env/bin/python'),str(D/'deploy_loss81.py')],check=True,env=env)
print('Finite81 science/startup/archive and full loss waiter launched; automatic82 false')
