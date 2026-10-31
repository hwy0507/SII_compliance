from pathlib import Path
import subprocess,json,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_gradient_diagnosis_20261031_v1'
try:
 for name,budget in [('probe.py',960),('neighbors.py',330)]:
  with (O/(name+'.log')).open('xb') as f:subprocess.run([str(B/'env/bin/python'),str(D/name)],check=True,stdout=f,stderr=subprocess.STDOUT,timeout=budget)
 assert json.loads((O/'REVIEW.json').read_text())['passed'] and json.loads((O/'NEIGHBOR_REVIEW.json').read_text())['passed']
 with (O/'FINISHED.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),optimizer_updates=0,new_physics=0,saved_review_and_plot_inspection_pending=True),f,indent=2);f.write('\n')
except BaseException as e:
 with (O/'RUN_FAILURE.json').open('x') as f:json.dump(dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()),f,indent=2);f.write('\n')
 raise
