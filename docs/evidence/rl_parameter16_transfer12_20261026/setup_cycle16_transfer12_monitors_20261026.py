from pathlib import Path
import json,subprocess,os,shutil,re,time,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(B/'runtime/jax_compilation_cache'))
def launch(cmd,log):
 with log.open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 return dict(pid=p.pid,command=cmd,time=time.time())
def adapt(s,old,new,kind):
 s=s.replace(f'cycle_{old:05}',f'cycle_{new:05}').replace('cycle'+str(old),'cycle'+str(new))
 s=re.sub(r'\b'+str(old)+r'\b',str(new),s)
 if kind=='direct':s=s.replace('serl_multistep_gather_cycle12','serl_multistep_transfer_cycle12').replace('terminal)==360','terminal)==390').replace('terminal_count=360','terminal_count=390')
 return s
for kind,old,new,oldname,name,oldarchive,archive,methods in [
 ('parameter',15,16,'parameter_batch65536_cycle15_20261026_v1','parameter_batch65536_cycle16_20261026_v1','parameter_batch65536_cycle15_archive_20261026_v1','parameter_batch65536_cycle16_archive_20261026_v1',['impedance','admittance','vmc']),
 ('direct',11,12,'serl_multistep_gather_cycle11_20261026_v1','serl_multistep_transfer_cycle12_20261026_v1','serl_multistep_gather_cycle11_archive_20261026_v1','serl_multistep_transfer_cycle12_archive_20261026_v1',['direct'])]:
 out=B/'runs'/name;rt=B/'runtime'/name;view=B/'runs'/(archive+'_view');view.mkdir()
 launch_data=json.loads((out/'LAUNCH.json').read_text())
 for m in methods:(view/m).symlink_to(out/m/'train' if kind=='parameter' else out/m)
 if kind=='direct':launch_data=dict(jobs=[dict(controller='direct',**launch_data)])
 (view/'LAUNCH.json').write_text(json.dumps(launch_data,indent=2)+'\n')
 oldreview=B/'runs'/oldarchive.replace('_archive_','_review_');review=B/'runs'/archive.replace('_archive_','_review_');review.mkdir()
 for src in oldreview.glob('*.py'):
  s=adapt(src.read_text(),old,new,kind);ast.parse(s);(review/src.name).write_text(s)
 s=adapt((B/'runs'/oldname/'startup_review.py').read_text(),old,new,kind);ast.parse(s);(out/'startup_review.py').write_text(s)
 monitors={}
 monitors['startup']=launch([str(B/'env/bin/python'),str(out/'startup_review.py')],out/'startup_review.log')
 monitors['archive']=launch([str(B/'env/bin/python'),str(rt/'archive_published_cycle_checkpoints_20261025.py'),'--run',str(view),'--output',str(B/'runs'/archive)],out/'archive.log')
 monitors['review']=launch([str(B/'env/bin/python'),str(review/'coordinator.py')],review/'driver.log')
 (out/'MONITORS.json').write_text(json.dumps(monitors,indent=2)+'\n');print(kind,{k:v['pid'] for k,v in monitors.items()},flush=True)
