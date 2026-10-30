from pathlib import Path
import subprocess,json,time,hashlib,os
B=Path(__file__).resolve().parents[2];D=B/'runs/parameter_recovery85_87_reward_stability_20261030_v1';R=B/'runs/parameter_partial75_recovery_cycle85_20261029_v1'
read=lambda p:json.loads(p.read_text())
assert not (D/'LAUNCH.json').exists();plan=read(D/'PLAN.json');launch=read(R/'LAUNCH.json');assert plan['time']<launch['time'] and plan['cycles']==[85,86,87] and plan['bootstrap_seed']==2026102858
for j in launch['jobs']:
 s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==j['proc_start_ticks'] and s[0]!='Z'
for r in read(D/'SOURCE_REVIEW.json')['files']:assert hashlib.sha256(Path(r['source']['path']).read_bytes()).hexdigest()==r['source']['sha256']
with (D/'driver.log').open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(D/'wait_register_and_audit.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
(D/'LAUNCH.json').write_text(json.dumps(dict(time=time.time(),pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],plan_sha256=hashlib.sha256((D/'PLAN.json').read_bytes()).hexdigest(),automatic_training=False),indent=2)+'\n');print('Original85-87 waiter launched with original4h budget; no training dispatch')
