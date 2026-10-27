from pathlib import Path
import os,json,time,subprocess,statistics
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=Path(__file__).parent
os.sched_setaffinity(0,{54});os.nice(19)
def ident(pid):
 p=Path(f'/proc/{pid}/stat')
 if not p.exists():return None
 s=p.read_text().rsplit(')',1)[1].split()
 return None if s[0]=='Z' else s[19]
D=B/'runs/serl_interrupted25_recovery26_20261027_v1';P=B/'runs/parameter_capacity_pool30_cycle42_20261026_v1';F=B/'runs/parameter41_frozen_full30_20261027_v1'
jobs=[{'controller':'direct',**json.loads((D/'LAUNCH.json').read_text())}]+json.loads((P/'LAUNCH.json').read_text())['jobs']
ids={str(j['pid']):ident(j['pid']) for j in jobs};assert all(ids.values())
plan=dict(time=time.time(),samples=60,interval_seconds=1,wait_for_direct_minimum_new_steps=2000,maximum_wait_seconds=600,training_pids=ids,frozen_evaluator_pids=[j['pid'] for j in json.loads((F/'LAUNCH.json').read_text())['jobs']],scope='four formal learners plus three frozen41 evaluators; mixed utilization not pure formal attribution')
(O/'GPU_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
deadline=time.monotonic()+600
while True:
 assert all(ident(int(pid))==start for pid,start in ids.items()),'Training process exited before window'
 assert time.monotonic()<deadline,'Direct progress wait expired'
 p=D/'direct/PROGRESS.json'
 if p.exists() and json.loads(p.read_text())['steps']>=1041290:break
 time.sleep(2)
rows=[];start=time.monotonic()
with (O/'GPU_SAMPLES.jsonl').open('x',buffering=1) as f:
 for i in range(60):
  assert all(ident(int(pid))==s for pid,s in ids.items()),'Original training identity changed'
  raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True)
  cp=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],text=True)
  row={'time':time.time(),'gpus':[[float(x.strip()) for x in line.split(',')] for line in raw.strip().splitlines()],'compute_processes':cp.strip().splitlines()};rows.append(row);f.write(json.dumps(row)+'\n');time.sleep(1)
result={'passed':True,'time':time.time(),'samples':60,'elapsed_seconds':time.monotonic()-start,'gpu_means':{str(i):statistics.mean(next(g[1] for g in r['gpus'] if int(g[0])==i) for r in rows) for i in range(4)},'plan':plan,'instantaneous_50_percent_guarantee':False,'scientific_convergence_claim':False}
(O/'GPU_PROFILE.json').write_text(json.dumps(result,indent=2)+'\n')
