"""Dispatch the one explicitly reviewed history88 trial after all preflight gates."""
from pathlib import Path
import os,sys,json,time,subprocess
D=Path(__file__).parent;B=D.parents[1];R=B/'runs/parameter_history_cycle88_20261030_v1'
sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
from driver import sha,read,put,validate_protocol
assert not (R/'LAUNCH.json').exists() and not (R/'LAUNCH_CLAIM.json').exists()
assert read(R/'CHECK_ONLY_COMPLETE.json')['passed'] and read(D/'INTEGRATION_REVIEW.json')['passed']
decision=read(D/'SCIENTIFIC_DECISION.json');assert decision['parent_cycle']==87 and decision['new_cycle']==88 and decision['new_cycles']==1 and decision['architecture_changed'] and not decision['automatic_followup']
for ref in decision['evidence']:assert sha(ref['path'])==ref['sha256']
for n,h in read(D/'SOURCES.json')['files'].items():assert sha(D/n)==h
registrations={}
for m in ['impedance','admittance','vmc']:
 p=read(R/m/'REGISTRATION.json');st=p['post_interruption_continuation'];validate_protocol(st['parent_registration']['sha256'],p);assert sha(st['checkpoint']['path'])==st['checkpoint']['sha256']
 ck=read(R/m/'CHECK_ONLY_REVIEW.json');assert ck['passed'] and ck['repeat_native_update_full_state_exact'] and ck['registration_sha256']==sha(R/m/'REGISTRATION.json') and ck['checkpoint_sha256']==st['checkpoint']['sha256']
 assert read(R/m/'check/INITIAL_STATE_REVIEW.json')['passed'] and not (R/m/'train').exists();registrations[m]=sha(R/m/'REGISTRATION.json')
put(R/'PRELAUNCH_REVIEW.json',dict(passed=True,time=time.time(),registration_hashes=registrations,decision_sha256=sha(D/'SCIENTIFIC_DECISION.json'),integration_sha256=sha(D/'INTEGRATION_REVIEW.json'),sources_sha256=sha(D/'SOURCES.json'),launcher_sha256=sha(__file__),original87_parent_only=True,offline_fit_weights_imported=False,new_cycles=1,maximum_new_actions_per_method=41250,automatic_followup=False,future88_90_plan_sha256=sha(B/'runs/parameter_history88_90_reward_stability_20261030_v1/PLAN.json')))
put(R/'LAUNCH_CLAIM.json',dict(time=time.time(),pid=os.getpid(),finite_stage=88))
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');jobs=read(R/'COMMANDS.json')['jobs'];started=[]
for j in jobs:
 with (R/(j['controller']+'_driver.log')).open('x') as f:p=subprocess.Popen(j['command'],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 j.update(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time());started.append(j);put(R/(j['controller']+'_LAUNCHED.json'),j)
put(R/'LAUNCH.json',dict(time=time.time(),jobs=started,new_cycles=1,automatic_followup=False))
for name,script in [('MONITOR',D/'archive88.py'),('STARTUP',D/'startup88.py')]:
 with (R/(name.lower()+'.log')).open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(script)],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 put(R/(name+'_LAUNCH.json'),dict(time=time.time(),pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],script_sha256=sha(script)))
print(json.dumps(dict(launched=started,scope='One history88 cycle only; no automatic89')))
