from pathlib import Path
import json,time,subprocess,os
os.sched_setaffinity(0,{54})
root=Path(__file__).parent
plan=json.loads((root/'REGISTRATION.json').read_text())
def identity(pid):
 try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:return None
try:
 deadline=time.monotonic()+3600
 while any(identity(pid) is not None for pid in plan['original_frozen_pids']):
  assert time.monotonic()<deadline,'Original frozen exit wait expired; no retry'
  assert all(identity(int(pid))==v for pid,v in plan['learner_identities'].items())
  time.sleep(2)
 samples=[];started=time.time()
 for i in range(60):
  raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True)
  rows=[[int(v.strip()) for v in row.split(',')] for row in raw.strip().splitlines()]
  processes=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True)
  gpu_pids=sorted(set(int(x.strip()) for x in processes.splitlines() if x.strip()))
  assert gpu_pids==sorted(plan['learner_pids']),('Unexpected GPU process',gpu_pids)
  preserved={pid:identity(int(pid))==v for pid,v in plan['learner_identities'].items()};assert all(preserved.values())
  samples.append(dict(time=time.time(),gpus=rows,gpu_pids=gpu_pids,identities_unchanged=preserved))
  time.sleep(1)
 result=dict(started=started,finished=time.time(),samples=samples,means=[sum(s['gpus'][i][1] for s in samples)/len(samples) for i in range(4)],scope='One fixed pure formal24/39 window after all original frozen32 evaluator processes exit; no repeat for favorable means, no guarantee at every instant or outside window.')
 (root/'PROFILE.json').write_text(json.dumps(result,indent=2)+'\n')
except BaseException as error:
 (root/'FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(error)))+'\n');raise
