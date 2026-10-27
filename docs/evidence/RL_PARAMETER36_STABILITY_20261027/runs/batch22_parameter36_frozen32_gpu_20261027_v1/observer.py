from pathlib import Path
import json,time,subprocess,os
os.sched_setaffinity(0,{54})
out=Path(__file__).parent
pids=[1584172,2805435,2805436,2805437,2466385,2466386,2466387]
def identity(pid):
 try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:return None
identities={pid:identity(pid) for pid in pids}
assert all(identities.values())
gate=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_capacity_pool30_cycle36_20261026_v1/startup/REVIEW.json')
deadline=time.monotonic()+300
while not gate.exists():
 assert time.monotonic()<deadline,'Startup observation wait expired'
 time.sleep(2)
assert json.loads(gate.read_text())['passed']
direct_gate=gate.parents[2]/'serl_multistep_batch65536_cycle22_20261026_v1/startup/REVIEW.json'
while not direct_gate.exists():
 assert time.monotonic()<deadline,'Direct startup observation wait expired'
 time.sleep(2)
assert json.loads(direct_gate.read_text())['passed']
samples=[];started=time.time()
for i in range(60):
 raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True)
 rows=[[int(x.strip()) for x in line.split(',')] for line in raw.strip().splitlines()]
 samples.append(dict(time=time.time(),gpus=rows,identities_unchanged={pid:identity(pid)==identities[pid] for pid in pids}))
 time.sleep(1)
result=dict(started=started,finished=time.time(),samples=samples,means=[sum(s['gpus'][i][1] for s in samples)/len(samples) for i in range(4)],scope='Mixed Direct22 and parameter36 formal training with frozen32 inference; retains actual transients, not a pure training throughput test or guarantee of instantaneous50%.')
(out/'PROFILE.json').write_text(json.dumps(result,indent=2)+'\n')
