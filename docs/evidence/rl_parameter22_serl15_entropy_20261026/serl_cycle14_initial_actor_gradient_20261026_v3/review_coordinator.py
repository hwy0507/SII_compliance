from pathlib import Path
import os,json,time,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=Path(__file__).parent
os.sched_setaffinity(0,{53});deadline=time.monotonic()+1800
while not (out/'REVIEW.json').exists():
 if (out/'FAILURE.json').exists():raise RuntimeError('Original diagnostic failed; no repeat')
 if time.monotonic()>deadline:raise TimeoutError('Original diagnostic wait expired; inspect original PID')
 time.sleep(2)
source=B/'runtime'/out.name/'review_serl_initial_actor_gradient_20261026.py'
subprocess.run([str(B/'env/bin/python'),str(source),'--run',str(out)],check=True)
(out/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),completed=True,convergence_claim=False))+'\n')
