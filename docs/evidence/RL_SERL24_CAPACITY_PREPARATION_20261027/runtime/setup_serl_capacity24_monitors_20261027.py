from pathlib import Path
import json,os,subprocess,time,hashlib,shutil
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=B/'runs/serl_capacity_batch65536_cycle24_20261027_v1';rt=B/'runtime'/out.name
templates=B/'runtime/serl_capacity24_monitor_templates_20261027_v1'
manifest=json.loads((templates/'MANIFEST.json').read_text())
for name,expected in manifest['templates'].items():
 with (templates/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected
archive=B/'runs/serl_capacity_batch65536_cycle24_archive_20261027_v1';view=B/'runs'/(archive.name+'_view');view.mkdir();(view/'direct').symlink_to(out/'direct')
launch=json.loads((out/'LAUNCH.json').read_text())
(view/'LAUNCH.json').write_text(json.dumps(dict(jobs=[dict(controller='direct',**launch)]),indent=2)+'\n')
review=B/'runs/serl_capacity_batch65536_cycle24_review_20261027_v1';review.mkdir()
for name in ['review.py','coordinator.py','diagnose.py']:shutil.copy2(templates/name,review/name)
for name in ['startup_review.py','capacity_boundary_review.py']:shutil.copy2(templates/name,out/name)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(B/'runtime/jax_compilation_cache'))
def start(command,log):
 with log.open('x') as f:p=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 return dict(pid=p.pid,time=time.time(),command=command)
monitors={}
monitors['startup']=start([str(B/'env/bin/python'),str(out/'startup_review.py')],out/'startup_review.log')
monitors['boundary']=start([str(B/'env/bin/python'),str(out/'capacity_boundary_review.py')],out/'capacity_boundary_review.log')
monitors['archive']=start([str(B/'env/bin/python'),str(rt/'archive_published_cycle_checkpoints_20261025.py'),'--run',str(view),'--output',str(archive)],out/'archive.log')
monitors['review']=start([str(B/'env/bin/python'),str(review/'coordinator.py')],review/'driver.log')
(out/'MONITORS.json').write_text(json.dumps(monitors,indent=2)+'\n');print({k:v['pid'] for k,v in monitors.items()},flush=True)
