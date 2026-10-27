from pathlib import Path
import json,time,hashlib,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/serl29_parameter48_gpu_20261027_v1';O.mkdir()
jobs=[]
for n in ['serl_take_cycle29_20261027_v1','parameter_capacity_pool30_cycle48_20261026_v1']:
 r=B/'runs'/n
 for j in json.loads((r/'LAUNCH.json').read_text())['jobs']:
  p=Path(f"/proc/{j['pid']}");s=(p/'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z'
  jobs.append(dict(run=n,controller=j['controller'],pid=j['pid'],start_ticks=s[19]))
code='''from pathlib import Path
import json,time,subprocess,os,statistics
O=Path(__file__).parent;B=O.parents[1];os.sched_setaffinity(0,{54});os.nice(10);plan=json.loads((O/'PLAN.json').read_text())
try:
 limit=time.monotonic()+600
 while True:
  reviews=[B/'runs'/n/'startup/REVIEW.json' for n in ['serl_take_cycle29_20261027_v1','parameter_capacity_pool30_cycle48_20261026_v1']]
  if all(p.exists() for p in reviews):break
  assert time.monotonic()<limit,'Startup reviews not ready within budget'
  time.sleep(3)
 assert all(json.loads(p.read_text())['passed'] for p in reviews)
 start=time.time();samples=[]
 for i in range(plan['samples']):
  identities=[]
  for j in plan['formal_jobs']:
   p=Path(f"/proc/{j['pid']}");s=(p/'stat').read_text().rsplit(')',1)[1].split()
   assert s[0]!='Z' and s[19]==j['start_ticks'] and j['run'].encode() in (p/'cmdline').read_bytes();identities.append(j['pid'])
  output=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True)
  values={int(a):dict(utilization=int(b),memory_mib=int(c)) for a,b,c in [l.split(',') for l in output.splitlines()]};assert set(values)=={0,1,2,3}
  gpu_processes=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],text=True).strip()
  samples.append(dict(time=time.time(),gpus=values,formal_pids=identities,gpu_processes=gpu_processes))
  if i+1<plan['samples']:time.sleep(plan['interval_seconds'])
 means={g:statistics.mean(s['gpus'][g]['utilization'] for s in samples) for g in range(4)}
 result=dict(passed=True,time=time.time(),duration_seconds=time.time()-start,sample_count=len(samples),mean_gpu_utilization_percent=means,all_means_at_least50=all(v>=50 for v in means.values()),samples=samples,scope=plan['scope'])
 (O/'PROFILE.json').write_text(json.dumps(result,indent=2)+'\\n');print(json.dumps(means),flush=True)
except BaseException as e:
 (O/'FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\\n');raise
'''
(O/'observe.py').write_text(code)
plan=dict(time=time.time(),samples=60,interval_seconds=1,formal_jobs=jobs,source_sha256=hashlib.sha256(code.encode()).hexdigest(),scope='One fixed operating window after actual startup; includes ongoing frozen41 inference, not pure training throughput, not every-instant guarantee, and excludes earlier transition idle')
(O/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
cmd=[str(B/'env/bin/python'),str(O/'observe.py')]
with (O/'driver.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(O/'LAUNCH.json').write_text(json.dumps(dict(time=time.time(),pid=p.pid,command=cmd),indent=2)+'\n');print(p.pid)
