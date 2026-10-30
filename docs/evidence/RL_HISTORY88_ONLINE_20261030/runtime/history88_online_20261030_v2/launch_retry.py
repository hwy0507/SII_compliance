from pathlib import Path
import os,sys,time,json,copy,subprocess
D=Path(__file__).parent;B=D.parents[1];R=B/'runs/parameter_history_cycle88_20261030_v2';R0=B/'runs/parameter_history_cycle88_20261030_v1';OLD=B/'runtime/history88_online_20261030_v1'
sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
from driver import read,put,sha,validate_protocol
assert not (R/'LAUNCH.json').exists() and not (R/'admittance/train').exists()
assert read(D/'LR_RETRY_CONTRACT_REVIEW.json')['passed'] and read(R/'admittance/CHECK_ONLY_REVIEW.json')['passed'] and read(OLD/'INTEGRATION_REVIEW.json')['passed']
for n,h in read(D/'SOURCES.json')['files'].items():assert sha(D/n)==h
plan=read(D/'RETRY_PLAN.json')
for j in plan['replaced_only_readonly_consumers']:
 q=Path(f'/proc/{j["pid"]}/stat')
 if q.exists():f=q.read_text().rsplit(')',1)[1].split();assert f[19]!=j['proc_start_ticks'] or f[0]=='Z'
p=read(R/'admittance/REGISTRATION.json');st=p['post_interruption_continuation'];validate_protocol(st['parent_registration']['sha256'],p);assert sha(st['checkpoint']['path'])==st['checkpoint']['sha256'];assert read(R/'admittance/CHECK_ONLY_REVIEW.json')['registration_sha256']==sha(R/'admittance/REGISTRATION.json')
kept=plan['original_I_V_jobs']
for j in kept:
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
put(R/'PRELAUNCH_REVIEW.json',dict(passed=True,time=time.time(),registration_hashes={m:sha(R/m/'REGISTRATION.json') for m in ['impedance','admittance','vmc']},retry_plan_sha256=sha(D/'RETRY_PLAN.json'),retry_contract_sha256=sha(D/'LR_RETRY_CONTRACT_REVIEW.json'),only_admittance_new_process=True,admittance_original_zero_physics=True,original_I_V_not_restarted=True,automatic_followup=False))
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');j=read(R/'RETRY_COMMAND.json')
with (R/'admittance_driver.log').open('x') as f:p=subprocess.Popen(j['command'],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
j.update(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time());jobs=sorted(kept+[j],key=lambda x:['impedance','admittance','vmc'].index(x['controller']));put(R/'LAUNCH.json',dict(time=time.time(),jobs=jobs,composite_view=True,original_I_V_kept=True,only_admittance_retried_before_physics=True,new_cycles=1,automatic_followup=False))
for name,script in [('MONITOR',D/'archive88.py'),('STARTUP',D/'startup88.py')]:
 with (R/(name.lower()+'.log')).open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(script)],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 put(R/(name+'_LAUNCH.json'),dict(time=time.time(),pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],script_sha256=sha(script)))
print(json.dumps(j))
