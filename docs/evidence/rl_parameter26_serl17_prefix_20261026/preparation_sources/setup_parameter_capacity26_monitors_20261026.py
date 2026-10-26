from pathlib import Path
import json,os,subprocess,time,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=B/'runs/parameter_capacity_pool30_cycle26_20261026_v1';rt=B/'runtime'/out.name
archive=B/'runs/parameter_capacity_pool30_cycle26_archive_20261026_v1';view=B/'runs'/(archive.name+'_view');view.mkdir();launch=json.loads((out/'LAUNCH.json').read_text())
for m in ['impedance','admittance','vmc']:(view/m).symlink_to(out/m/'train')
(view/'LAUNCH.json').write_text(json.dumps(launch,indent=2)+'\n');oldreview=B/'runs/parameter_capacity_pool30_cycle25_review_20261026_v1';review=B/'runs/parameter_capacity_pool30_cycle26_review_20261026_v1';review.mkdir()
def adapt(s):
 s=s.replace('cycle25','cycle26').replace('cycle_00025','cycle_00026').replace("['cycle']==25","['cycle']==26").replace("'--cycle','25'","'--cycle','26'").replace('Cycle25 archive','Cycle26 archive')
 s=s.replace("old['replay']['capacity']==1_000_000 and 'replay_capacity_extension' not in old['replay']","old['replay']['capacity']==2_000_000 and old['replay']['replay_capacity_extension']==CAPACITY_MARKER")
 return s
for src in oldreview.glob('*.py'):
 s=adapt(src.read_text());ast.parse(s);(review/src.name).write_text(s)
s=adapt((B/'runs/parameter_capacity_pool30_cycle25_20261026_v1/startup_review.py').read_text());ast.parse(s);(out/'startup_review.py').write_text(s)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
def start(cmd,log):
 with log.open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 return dict(pid=p.pid,time=time.time(),command=cmd)
mon={};mon['startup']=start([str(B/'env/bin/python'),str(out/'startup_review.py')],out/'startup_review.log');mon['archive']=start([str(B/'env/bin/python'),str(rt/'archive_published_cycle_checkpoints_20261025.py'),'--run',str(view),'--output',str(archive)],out/'archive.log');mon['review']=start([str(B/'env/bin/python'),str(review/'coordinator.py')],review/'driver.log')
(out/'MONITORS.json').write_text(json.dumps(mon,indent=2)+'\n');print({k:v['pid'] for k,v in mon.items()})
