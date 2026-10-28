"""Bind prepared full67 audits to a reviewed and actually launched67 job."""
from pathlib import Path
import json,hashlib,os,subprocess,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');ROOT=Path(__file__).parent;RUN=B/'runs/parameter_capacity_pool30_cycle67_20261026_v1';OUT=B/'runs/parameter67_loss_20261028_v1';SRC=B/'runtime/parameter67_loss_preparation_20261028_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
assert read(ROOT/'DECISION67.json')['passed'] and read(RUN/'CHECK_ONLY_COMPLETE.json')['passed']
jobs=read(RUN/'LAUNCH.json')['jobs']
for j in jobs:
 s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==j['proc_start_ticks'] and s[0]!='Z'
assert not OUT.exists();review=read(SRC/'SOURCE_REVIEW.json');assert review['passed']
OUT.mkdir();files={}
for x in review['files']:
 name=x['name'];p=SRC/name;assert sha(p)==x['sha256'];data=p.read_bytes();q=OUT/name
 with q.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 assert q.read_bytes()==data;files[name]=sha(q)
plan=dict(time=time.time(),registered_after_training_launch=True,static_prepared_before_training=True,parent_run=str(RUN),jobs=jobs,python=str(B/'env/bin/python'),window='Complete67 actual episode lengths; full descriptive49-67; paired66-67. Original65-67 window unchanged and incomplete; all historical windows retained.',fixed_timeout_seconds=7200,automatic_training=False,convergence_claim=False,files=files,diagnostic_cpu=54)
write(OUT/'PLAN.json',plan);env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
with (OUT/'driver.log').open('x') as log:p=subprocess.Popen([str(B/'env/bin/python'),str(OUT/'wait.py')],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
st=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split();launch=dict(pid=p.pid,proc_start_ticks=st[19],time=time.time(),plan_sha256=sha(OUT/'PLAN.json'));write(OUT/'LAUNCH.json',launch);print(json.dumps(launch,indent=2))
