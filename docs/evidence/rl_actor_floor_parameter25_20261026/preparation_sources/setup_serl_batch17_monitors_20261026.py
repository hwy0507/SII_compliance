from pathlib import Path
import ast,json,os,subprocess,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
out=B/'runs/serl_multistep_batch65536_cycle17_20261026_v1'
rt=B/'runtime'/out.name
archive=B/'runs/serl_multistep_batch65536_cycle17_archive_20261026_v1'
view=B/'runs'/(archive.name+'_view');view.mkdir();(view/'direct').symlink_to(out/'direct')
launch=json.loads((out/'LAUNCH.json').read_text())
(view/'LAUNCH.json').write_text(json.dumps(dict(jobs=[dict(controller='direct',**launch)]),indent=2)+'\n')
parent_registration=json.loads((out/'REGISTRATION.json').read_text())
oldreview=Path(parent_registration['reviewed_continuation_stage']['cycle_review']['path']).parent
assert (oldreview/'FINISHED.json').exists()
review=B/'runs/serl_multistep_batch65536_cycle17_review_20261026_v1';review.mkdir()
def adapt(source):
    # Do not replace every standalone13: CPU range(1,13) and figure width13
    # are unrelated to the cycle number and must stay intact.
    return source.replace('cycle_00016','cycle_00017').replace('cycle16','cycle17').replace("['cycle']==16","['cycle']==17").replace('terminal)==510','terminal)==540').replace('terminal_count=510','terminal_count=540').replace('time.monotonic()+3600','time.monotonic()+7200').replace('Cycle16 archive unavailable','Cycle17 archive unavailable')
for path in oldreview.glob('*.py'):
    source=adapt(path.read_text());ast.parse(source);(review/path.name).write_text(source)
source=adapt((B/'runs/serl_multistep_batch65536_cycle16_20261026_v1/startup_review.py').read_text());ast.parse(source)
(out/'startup_review.py').write_text(source)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(B/'runtime/jax_compilation_cache'))
def start(command,log):
    with log.open('x') as f:p=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
    return dict(pid=p.pid,time=time.time(),command=command)
monitors={}
monitors['startup']=start([str(B/'env/bin/python'),str(out/'startup_review.py')],out/'startup_review.log')
monitors['archive']=start([str(B/'env/bin/python'),str(rt/'archive_published_cycle_checkpoints_20261025.py'),'--run',str(view),'--output',str(archive)],out/'archive.log')
monitors['review']=start([str(B/'env/bin/python'),str(review/'coordinator.py')],review/'driver.log')
(out/'MONITORS.json').write_text(json.dumps(monitors,indent=2)+'\n');print({k:v['pid'] for k,v in monitors.items()},flush=True)
