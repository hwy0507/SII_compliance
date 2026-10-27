from pathlib import Path
import json,time,ast,hashlib,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');S=B/'runs/parameter48_saved_review_20261027_v1/review_saved.py';O=B/'runs/parameter49_saved_review_20261027_v1';O.mkdir()
s=S.read_text().replace('cycle48','cycle49').replace('Original48','Original49').replace("['cycle']==48","['cycle']==49");ast.parse(s);(O/'review_saved.py').write_text(s)
plan=dict(time=time.time(),parent_source=str(S),parent_source_sha256=hashlib.sha256(S.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(s.encode()).hexdigest(),cycle=49,wait_seconds=7200,automatic_training=False,new_physics=0,optimizer_updates=0)
(O/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n');cmd=[str(B/'env/bin/python'),str(O/'review_saved.py')]
with (O/'driver.log').open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
(O/'LAUNCH.json').write_text(json.dumps(dict(pid=p.pid,time=time.time(),command=cmd),indent=2)+'\n');print(p.pid)
