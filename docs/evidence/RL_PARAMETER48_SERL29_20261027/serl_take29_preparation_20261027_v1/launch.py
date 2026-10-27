"""Manual reviewed launch of one complete28 ->29 cycle, never invoked by waiter."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
P=Path(__file__).parent;B=P.parents[1];out=B/'runs/serl_take_cycle29_20261027_v1';rt=B/'runtime'/out.name
review=B/'runs/serl_take_cycle29_review_20261027_v1';archive=B/'runs/serl_take_cycle29_archive_20261027_v1'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
assert read(P/'FINISHED.json')['prepared']
assert read(out/'CHECK_ONLY_REVIEW.json')['passed']
gate=read(out/'PRELAUNCH_REVIEW.json');assert gate['passed'] and gate['registration_sha256']==sha(out/'REGISTRATION.json')
assert gate['monitor_template_review_sha256']==sha(P/'MONITOR_TEMPLATE_REVIEW.json')
assert not (out/'LAUNCH.json').exists() and not Path('/proc/1978250').exists()
manifest=read(P/'MONITOR_TEMPLATE_REVIEW.json');assert manifest['passed']
for name,h in manifest['files'].items():assert sha(P/'templates'/name)==h
review.mkdir();(out/'audit_source').mkdir()
for name in ['review.py','diagnose.py','coordinator.py']:shutil.copyfile(P/'templates'/name,review/name)
shutil.copyfile(P/'templates/startup_review.py',out/'startup_review.py')
shutil.copyfile(P/'templates/audit_serl_take29_replay_20261027.py',out/'audit_source/audit_serl_take29_replay_20261027.py')
(review/'MONITOR_SOURCE_MANIFEST.json').write_text(json.dumps({str(p):sha(p) for p in [out/'startup_review.py',out/'audit_source/audit_serl_take29_replay_20261027.py',*review.glob('*.py')]},indent=2)+'\n')
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(B/'runtime/jax_compilation_cache'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
def start(cmd,log):
 with log.open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 stat=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()
 return dict(pid=p.pid,start_ticks=stat[19],time=time.time(),command=cmd)
job=start(read(out/'COMMAND.json')['command'],out/'driver.log');record=dict(job);record['jobs']=[dict(job,controller='direct')]
(out/'LAUNCH.json').write_text(json.dumps(record,indent=2)+'\n')
mon={}
mon['startup']=start([str(B/'env/bin/python'),str(out/'startup_review.py')],out/'startup_review.log')
mon['archive']=start([str(B/'env/bin/python'),str(rt/'archive_published_cycle_checkpoints_20261025.py'),'--run',str(out),'--output',str(archive)],out/'archive.log')
mon['full_review']=start([str(B/'env/bin/python'),str(review/'coordinator.py')],review/'driver.log')
(out/'MONITORS.json').write_text(json.dumps(mon,indent=2)+'\n');print(json.dumps(dict(learner=job,monitors=mon),indent=2))
