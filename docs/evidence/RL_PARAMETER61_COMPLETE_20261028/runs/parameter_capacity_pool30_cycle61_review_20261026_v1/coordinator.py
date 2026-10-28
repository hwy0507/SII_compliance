from pathlib import Path
import subprocess,os,json,time
p=Path(__file__).parent;b=p.parents[1]
os.sched_setaffinity(0,{53})
subprocess.run([str(b/'env/bin/python'),str(p/'review.py')],check=True)
subprocess.run([str(b/'env/bin/python'),str(p/'diagnose_published_training_20261025.py'),'--runtime',str(b/'runtime/source_train17_clock'),'--run',str(b/'runs/parameter_capacity_pool30_cycle61_archive_20261026_v1_view'),'--output',str(p/'health'),'--cycle-archive',str(b/'runs/parameter_capacity_pool30_cycle61_archive_20261026_v1'),'--cycle','61'],check=True,env=dict(os.environ,PYTHONPATH=str(b/'runtime/source_train17_clock/source/tools')))
(p/'FINISHED.json').write_text(json.dumps({'time':time.time(),'completed':True,'convergence_claim':False})+'\n')
