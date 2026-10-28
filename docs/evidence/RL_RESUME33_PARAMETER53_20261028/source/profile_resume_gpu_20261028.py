from pathlib import Path
import json,time,os,subprocess,hashlib
b=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=b/'runs/resume_gpu_profile_20261028_v1';out.mkdir();os.sched_setaffinity(0,{54})
jobs=[]
for name in ['serl_take_cycle33_20261027_v1','parameter_capacity_pool30_cycle53_20261026_v1']:
 jobs+=json.loads((b/'runs'/name/'LAUNCH.json').read_text())['jobs']
(out/'PLAN.json').write_text(json.dumps(dict(time=time.time(),samples=60,interval_seconds=1,jobs=jobs,synthetic_guard_included=True,scope='Training33/53 plus separate synthetic utilization guard; not pure-training utilization'),indent=2))
def progress():
 result={}
 for j in jobs:
  run=Path(j['command'][j['command'].index('--output')+1]);result[j['controller']]=json.loads((run/'PROGRESS.json').read_text())
 return result
start=progress();samples=[];t0=time.monotonic()
with (out/'samples.jsonl').open('x',buffering=1) as f:
 for _ in range(60):
  raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True)
  procs=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_gpu_memory','--format=csv,noheader,nounits'],text=True)
  rows=[dict(zip(['gpu','utilization','memory_mib'],[int(x.strip()) for x in l.split(',')])) for l in raw.strip().splitlines()]
  live={j['controller']:Path(f"/proc/{j['pid']}/stat").read_text().split(') ')[1].split()[19]==j['proc_start_ticks'] for j in jobs}
  row=dict(time=time.time(),gpus=rows,learner_identity_live=live,compute_processes=procs);f.write(json.dumps(row)+'\n');samples.append(row);time.sleep(1)
end=progress();elapsed=time.monotonic()-t0;summary={}
for i in range(4):
 a=[next(r['utilization'] for r in s['gpus'] if r['gpu']==i) for s in samples];summary[i]=dict(mean=sum(a)/len(a),minimum=min(a),maximum=max(a),samples_below50=sum(v<50 for v in a))
r=dict(time=time.time(),elapsed_seconds=elapsed,gpus=summary,all_learners_live=all(all(s['learner_identity_live'].values()) for s in samples),start=start,end=end,steps_per_second={k:(end[k]['steps']-start[k]['steps'])/elapsed for k in start},synthetic_guard_included=True)
(out/'REVIEW.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
