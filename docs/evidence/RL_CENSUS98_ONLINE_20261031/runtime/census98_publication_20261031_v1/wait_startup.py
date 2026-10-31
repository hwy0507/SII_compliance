from pathlib import Path
import time,json,sys
P=Path(__file__).resolve().parent;B=P.parents[1];R=B/'runs/parameter_census_cycle98_20261031_v1';D=B/'runtime/census98_continuation_20261031_v1'
rd=lambda p:json.loads(p.read_text())
start=time.monotonic();jobs=rd(R/'LAUNCH.json')['jobs']+[rd(R/'MONITOR_LAUNCH.json')];guard=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');jobs+=guard['identities'];rows=[]
while not (R/'startup/REVIEW.json').exists():
 for j in jobs+[rd(R/'STARTUP_LAUNCH.json')]:
  s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
 assert not Path(guard['root'],'STOP').exists() and time.monotonic()-start<900
 assert not list(R.rglob('*FAILURE*.json'))
 row=dict(time=time.time(),steps={m:rd(R/m/'train/PROGRESS.json')['steps'] for m in ['impedance','admittance','vmc']});rows.append(row);print(json.dumps(row),flush=True);time.sleep(15)
assert rd(R/'startup/REVIEW.json')['passed']
with (P/'STARTUP_WAIT_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,samples=rows,scope='Bounded real identity/guard/progress wait until original startup passed'),f,indent=2);f.write('\n')
print('Original startup passed',flush=True)
