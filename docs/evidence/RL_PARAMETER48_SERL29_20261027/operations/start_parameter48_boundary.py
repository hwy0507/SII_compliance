from pathlib import Path
import os,json,hashlib,time,subprocess,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
O=B/'runs/parameter48_boundary_preparation_20261027_v1';R=B/'runs/parameter_capacity_pool30_cycle48_20261026_v1'
assert (R/'LAUNCH.json').exists() and not (O/'LAUNCH.json').exists() and not (O/'evidence').exists()
ast.parse((O/'audit.py').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
jobs=json.loads((R/'LAUNCH.json').read_text())['jobs'];identities={}
for j in jobs:
 p=Path(f"/proc/{j['pid']}");s=(p/'stat').read_text().rsplit(')',1)[1].split()
 assert s[0]!='Z' and R.name.encode() in (p/'cmdline').read_bytes()
 identities[j['controller']]=dict(pid=j['pid'],start_ticks=s[19])
plan=dict(time=time.time(),source_sha256=sha(O/'audit.py'),formal_launch_sha256=sha(R/'LAUNCH.json'),identities=identities,threshold=2001000,wait_seconds_per_method=7200,methods=['impedance','admittance','vmc'],new_physics=0,optimizer_updates=0,scope='Read-only actual48 checkpoint crossing observation; saved RNG clone is not a live sampling trace')
(O/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
cmd=['nice','-n','15',str(B/'env/bin/python'),str(O/'audit.py')]
with (O/'driver.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
receipt=dict(time=time.time(),pid=p.pid,command=cmd,start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19])
(O/'LAUNCH.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
