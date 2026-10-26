from pathlib import Path
import json,os,subprocess,time,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
name='parameter_pool30_cycle21_20261026_v1';out=B/'runs'/name;rt=B/'runtime'/name
archive=B/'runs/parameter_pool30_cycle21_archive_20261026_v1';view=B/'runs'/(archive.name+'_view');view.mkdir()
launch=json.loads((out/'LAUNCH.json').read_text())
for m in ['impedance','admittance','vmc']:(view/m).symlink_to(out/m/'train')
(view/'LAUNCH.json').write_text(json.dumps(launch,indent=2)+'\n')
oldreview=B/'runs/parameter_pool30_cycle20_review_20261026_v1';review=B/'runs/parameter_pool30_cycle21_review_20261026_v1';review.mkdir()
def adapt(s):
 return s.replace('cycle20','cycle21').replace('cycle_00020','cycle_00021').replace("['cycle']==20","['cycle']==21").replace("'--cycle','20'","'--cycle','21'").replace('Cycle20 archive','Cycle21 archive')
for src in oldreview.glob('*.py'):
 s=adapt(src.read_text());ast.parse(s);(review/src.name).write_text(s)
s=(B/'runs/parameter_pool30_cycle20_20261026_v1/startup_review.py').read_text()

s=adapt(s).replace("/'startup_v2';OUT.mkdir","/'startup';OUT.mkdir")
ast.parse(s);(out/'startup_review.py').write_text(s)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
def start(cmd,log):
 with log.open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 return dict(pid=p.pid,time=time.time(),command=cmd)
monitors={}
monitors['startup']=start([str(B/'env/bin/python'),str(out/'startup_review.py')],out/'startup_review.log')
monitors['archive']=start([str(B/'env/bin/python'),str(rt/'archive_published_cycle_checkpoints_20261025.py'),'--run',str(view),'--output',str(archive)],out/'archive.log')
monitors['review']=start([str(B/'env/bin/python'),str(review/'coordinator.py')],review/'driver.log')
(out/'MONITORS.json').write_text(json.dumps(monitors,indent=2)+'\n');print({k:v['pid'] for k,v in monitors.items()})
