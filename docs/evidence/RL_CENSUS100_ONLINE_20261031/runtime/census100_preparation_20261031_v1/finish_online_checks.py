from pathlib import Path
import json,time,subprocess,sys,traceback
P=Path(__file__).resolve().parent;B=P.parents[1];R=B/'runs/parameter_census_cycle100_20261031_v1';D=B/'runtime/census100_continuation_20261031_v1';F=B/'runs/census100_fixed99_terminal_20261031_v1';T=B/'runtime/census100_terminal_20261031_v1'
read=lambda p:json.loads(p.read_text())
def check(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['proc_start_ticks']
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
try:
 start=time.time();deadline=read(R/'LAUNCH.json')['time']+2400;jobs=read(R/'LAUNCH.json')['jobs'];watch=read(R/'STARTUP_LAUNCH.json')
 while not (R/'startup/REVIEW.json').exists():
  for j in jobs+[watch,read(R/'MONITOR_LAUNCH.json')]:check(j)
  assert time.time()<deadline
  for m in ['impedance','admittance','vmc']:assert not (R/m/'DRIVER_FAILURE.json').exists() and not (R/m/'train/FAILURE.json').exists()
  time.sleep(5)
 assert read(R/'startup/REVIEW.json')['passed'];print('Actual startup passed; launching fixed8893 read-only consumer',flush=True)
 with (P/'terminal_launch.log').open('x') as f:subprocess.run([str(B/'env/bin/python'),str(T/'launch_wait.py')],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
 assert read(F/'PARTIAL_REJECTION_REVIEW.json')['passed'];check(read(F/'PROCESS.json'))
 while not (D/'ONLINE_OBSERVATION_REVIEW.json').exists():
  assert time.time()<deadline and not (D/'OBSERVATION_FAILURE.json').exists();check(read(R/'OBSERVER_LAUNCH.json'));time.sleep(5)
 assert read(D/'ONLINE_OBSERVATION_REVIEW.json')['passed']
 put(P/'ONLINE_CHECKS_FINISHED.json',dict(passed=True,time=time.time(),elapsed_s=time.time()-start,actual_startup=True,original_observer_passed=True,fixed_terminal_consumer=read(F/'PROCESS.json')));print('Startup, actual partial rejection, terminal waiter,120s observation all passed',flush=True)
except BaseException:
 put(P/'ONLINE_CHECKS_FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc()));raise
