from pathlib import Path
import json,time,ast,subprocess,os,hashlib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');S=B/'runs/serl29_parameter48_pure_gpu_20261027_v1/observe.py';O=B/'runs/serl30_parameter49_frozen29_gpu_20261027_v1';O.mkdir()
s=S.read_text().replace('serl_take_cycle29_20261027_v1','serl_take_cycle30_20261027_v1').replace('parameter_capacity_pool30_cycle48_20261026_v1','parameter_capacity_pool30_cycle49_20261026_v1').replace('Unexpected GPU process; not a pure formal window','Unexpected GPU process outside registered four formal learners and two frozen29 evaluators');ast.parse(s);(O/'observe.py').write_text(s)
jobs=[]
for n in ['serl_take_cycle30_20261027_v1','parameter_capacity_pool30_cycle49_20261026_v1','serl_take29_frozen_full30_20261027_v1']:
 for j in json.loads((B/'runs'/n/'LAUNCH.json').read_text())['jobs']:
  p=Path(f"/proc/{j['pid']}");st=(p/'stat').read_text().rsplit(')',1)[1].split();assert st[0]!='Z' and n.encode() in (p/'cmdline').read_bytes();jobs.append(dict(pid=j['pid'],run=n,start_ticks=st[19]))
plan=dict(time=time.time(),samples=60,interval_seconds=1,formal_jobs=jobs,source_sha256=hashlib.sha256(s.encode()).hexdigest(),scope='Mixed four formal learners Direct30/parameter49 and two original frozen29 evaluators. Exact GPU PID set verified each sample. Mean during this fixed window only, not every instant and not transition idle or pure training throughput.',new_physics=0,optimizer_updates=0)
(O/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n');cmd=[str(B/'env/bin/python'),str(O/'observe.py')]
with (O/'driver.log').open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
(O/'LAUNCH.json').write_text(json.dumps(dict(pid=p.pid,time=time.time(),command=cmd),indent=2)+'\n');print(p.pid)
