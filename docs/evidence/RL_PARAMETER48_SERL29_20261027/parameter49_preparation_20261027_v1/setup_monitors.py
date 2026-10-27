from pathlib import Path
import json,os,subprocess,time,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=B/'runs/parameter_capacity_pool30_cycle49_20261026_v1';rt=B/'runtime'/out.name
import hashlib
for relative,expected in json.loads((Path(__file__).parent/'SOURCE_MANIFEST.json').read_text()).items():
 with (Path(__file__).parent/relative).open('rb') as source:assert hashlib.file_digest(source,'sha256').hexdigest()==expected
archive=B/'runs/parameter_capacity_pool30_cycle49_archive_20261026_v1';view=B/'runs'/(archive.name+'_view');view.mkdir();launch=json.loads((out/'LAUNCH.json').read_text())
for m in ['impedance','admittance','vmc']:(view/m).symlink_to(out/m/'train')
(view/'LAUNCH.json').write_text(json.dumps(launch,indent=2)+'\n');oldreview=B/'runs/parameter_capacity_pool30_cycle48_review_20261026_v1';review=B/'runs/parameter_capacity_pool30_cycle49_review_20261026_v1';review.mkdir()
templates=Path(__file__).parent/'templates'
for src in templates.glob('*.py'):
 dest=out/src.name if src.name=='startup_review.py' else review/src.name
 content=src.read_text();ast.parse(content);dest.write_text(content)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
def start(cmd,log):
 with log.open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 return dict(pid=p.pid,time=time.time(),command=cmd)
mon={};mon['startup']=start([str(B/'env/bin/python'),str(out/'startup_review.py')],out/'startup_review.log');mon['archive']=start([str(B/'env/bin/python'),str(rt/'archive_published_cycle_checkpoints_20261025.py'),'--run',str(view),'--output',str(archive)],out/'archive.log');mon['review']=start([str(B/'env/bin/python'),str(review/'coordinator.py')],review/'driver.log')
(out/'MONITORS.json').write_text(json.dumps(mon,indent=2)+'\n');print({k:v['pid'] for k,v in mon.items()})
