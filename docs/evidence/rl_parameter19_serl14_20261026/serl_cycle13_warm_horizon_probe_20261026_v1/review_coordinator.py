from pathlib import Path
import subprocess,time,json,os
out=Path(__file__).parent;b=out.parents[1];os.sched_setaffinity(0,{53});deadline=time.monotonic()+2400
while not (out/'FINISHED.json').exists():
 if time.monotonic()>deadline:raise RuntimeError('Original finite probe deadline; inspect handles')
 time.sleep(3)
subprocess.run([str(b/'env/bin/python'),str(b/'runtime'/out.name/'review_serl_warm_target_horizon_20261026.py'),'--run',str(out)],check=True)
