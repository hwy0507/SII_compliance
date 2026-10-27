from pathlib import Path
import json,time,subprocess,os
os.sched_setaffinity(0,{54})
out=Path(__file__).parent
pids=[46632,2463296,2463297,2463300,2466385,2466386,2466387]
def identity(pid):
 try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:return None
identities={pid:identity(pid) for pid in pids}
assert all(identities.values())
samples=[];started=time.time()
for i in range(60):
 raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True)
 rows=[[int(x.strip()) for x in line.split(',')] for line in raw.strip().splitlines()]
 samples.append(dict(time=time.time(),gpus=rows,identities_unchanged={pid:identity(pid)==identities[pid] for pid in pids}))
 time.sleep(1)
result=dict(started=started,finished=time.time(),samples=samples,means=[sum(s['gpus'][i][1] for s in samples)/len(samples) for i in range(4)],scope='Mixed Direct20 and parameter33 formal training with frozen32 inference; retains actual transients, not a pure training throughput test or guarantee of instantaneous50%.')
(out/'PROFILE.json').write_text(json.dumps(result,indent=2)+'\n')
