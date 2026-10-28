from pathlib import Path
import json,time,os,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=B/'runs/vmc53_finished_guard_20261028_v1';out.mkdir();os.sched_setaffinity(0,{54})
run=B/'runs/parameter_capacity_pool30_cycle53_20261026_v1';j=next(x for x in json.loads((run/'LAUNCH.json').read_text())['jobs'] if x['controller']=='vmc');guard=json.loads((B/'runtime/gpu_util_guard_20261028_v4/LAUNCH.json').read_text())['workers']['3'];uuid=subprocess.check_output(['nvidia-smi','--id=3','--query-gpu=uuid','--format=csv,noheader'],text=True).strip()
assert json.loads((run/'vmc/train/FINISHED.json').read_text())['status']=='stopped_at_complete_cycle';assert not Path(f"/proc/{j['pid']}").exists()
(out/'PLAN.json').write_text(json.dumps(dict(time=time.time(),gpu=3,samples=30,expected_only_gpu3_compute_pid=guard,finished_learner_pid=j['pid'],scope='Independent guard after formal VMC53 completion; zero training onGPU3'),indent=2))
samples=[];t0=time.monotonic()
with (out/'samples.jsonl').open('x',buffering=1) as f:
 for _ in range(30):
  assert not Path(f"/proc/{j['pid']}").exists();assert Path(f'/proc/{guard}').exists()
  u=int(subprocess.check_output(['nvidia-smi','--id=3','--query-gpu=utilization.gpu','--format=csv,noheader,nounits'],text=True))
  raw=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader,nounits'],text=True);pids=[int(l.split(',')[0]) for l in raw.strip().splitlines() if l.split(',')[1].strip()==uuid];assert pids==[guard],pids
  d=dict(time=time.time(),gpu3_utilization=u,gpu3_pids=pids,formal_vmc_exited=True);samples.append(d);f.write(json.dumps(d)+'\n');time.sleep(1)
a=[s['gpu3_utilization'] for s in samples];r=dict(time=time.time(),elapsed_seconds=time.monotonic()-t0,samples=30,mean=sum(a)/len(a),minimum=min(a),maximum=max(a),below50=sum(v<50 for v in a),only_synthetic_guard_on_gpu3=True,formal_vmc_finished=True)
(out/'REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
