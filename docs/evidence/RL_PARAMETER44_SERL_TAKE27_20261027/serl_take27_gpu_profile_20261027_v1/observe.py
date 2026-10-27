from pathlib import Path
import json,time,hashlib,os,statistics,subprocess
O=Path(__file__).parent;B=O.parents[1];p=json.loads((O/'PLAN.json').read_text());os.sched_setaffinity(0,{54});os.nice(19)
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):return json.loads(path.read_text())
def ident(pid):
 path=Path(f'/proc/{pid}/stat')
 if not path.exists():return None
 s=path.read_text().rsplit(')',1)[1].split();return None if s[0]=='Z' else s[19]
try:
 assert sha(p['baseline_profile']['path'])==p['baseline_profile']['sha256']
 D=B/'runs'/p['direct_run'];P=B/'runs'/p['parameter_run'];F=B/'runs'/p['frozen_run']
 reg=read(D/'REGISTRATION.json');assert reg['recovery_continuation_stage']['new_cycle']==27
 assert read(D/'PRELAUNCH_REVIEW.json')['passed']
 jobs=read(D/'LAUNCH.json')['jobs']+read(P/'LAUNCH.json')['jobs']+read(F/'LAUNCH.json')['jobs']
 identities={str(j['pid']):ident(j['pid']) for j in jobs};assert len(identities)==7 and all(identities.values())
 parent_steps=read(D/'INITIAL_STATE_REVIEW.json')['steps'];deadline=time.monotonic()+p['maximum_wait_seconds']
 while True:
  assert all(ident(int(pid))==s for pid,s in identities.items())
  assert time.monotonic()<deadline,'Post-take startup observation wait expired'
  startup=D/'startup/REVIEW.json'
  if startup.exists() and read(startup)['passed'] and read(D/'direct/PROGRESS.json')['steps']>=parent_steps+p['minimum_new_direct_steps']:break
  time.sleep(2)
 start=time.monotonic();first=read(D/'direct/PROGRESS.json');rows=[]
 with (O/'GPU_SAMPLES.jsonl').open('x',buffering=1) as f:
  for _ in range(p['samples']):
   assert all(ident(int(pid))==s for pid,s in identities.items()),'Registered process changed during measurement'
   raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True)
   procs=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],text=True)
   row=dict(time=time.time(),gpus=[[float(x.strip()) for x in line.split(',')] for line in raw.strip().splitlines()],compute_processes=procs.strip().splitlines(),direct_progress=read(D/'direct/PROGRESS.json'));rows.append(row);f.write(json.dumps(row)+'\n');time.sleep(p['interval_seconds'])
 elapsed=time.monotonic()-start;last=read(D/'direct/PROGRESS.json');means={str(i):statistics.mean(next(g[1] for g in r['gpus'] if int(g[0])==i) for r in rows) for i in range(4)}
 result=dict(passed=True,time=time.time(),plan_sha256=sha(O/'PLAN.json'),identities=identities,samples=len(rows),elapsed_seconds=elapsed,gpu_means=means,all_means_at_least50=all(x>=50 for x in means.values()),direct_first=first,direct_last=last,approximate_direct_steps_per_second=(last['steps']-first['steps'])/elapsed,baseline_gpu_means=read(Path(p['baseline_profile']['path']))['gpu_means'],instantaneous50_guarantee=False,convergence_claim=False,limitation=p['scope'])
 (O/'GPU_PROFILE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
except BaseException as e:
 (O/'FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\n');raise
