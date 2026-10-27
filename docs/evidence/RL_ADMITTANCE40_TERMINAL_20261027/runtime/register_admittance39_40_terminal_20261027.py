from pathlib import Path
import json,re,ast,hashlib,time,subprocess,os,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';out=B/'runs/admittance39_40_terminal_concentration_20261027_v1';runtime=B/'runtime/admittance39_40_terminal_concentration_20261027_v1'
out.mkdir(exist_ok=False);runtime.mkdir(exist_ok=False)
os.sched_setaffinity(0,{52})
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
diffs=[]
for prefix in ['audit','review']:
 old=R/f'code/mujoco_6d_vmc_benchmark/tools/{prefix}_vmc37_38_terminal_concentration_20261027.py';s=old.read_text()
 s=re.sub('37|38',lambda m:{'37':'39','38':'40'}[m[0]],s).replace('VMC','Admittance').replace("'vmc'","'admittance'").replace('{39:1134,40:1164}','{39:1194,40:1224}')
 ast.parse(s);name=f'{prefix}_admittance39_40_terminal_concentration_20261027.py';p=runtime/name;p.write_text(s);(R/'code/mujoco_6d_vmc_benchmark/tools'/name).write_text(s)
 diffs+=list(difflib.unified_diff(old.read_text().splitlines(True),s.splitlines(True),fromfile=str(old),tofile=str(p)))
 assert 'VMC' not in s and "'vmc'" not in s and not re.search('37|38',s)
 subprocess.run([str(B/'env/bin/python'),str(p),'--help'],check=True,stdout=subprocess.DEVNULL)
old=json.loads((B/'runs/vmc37_38_terminal_concentration_20261027_v1/REGISTRATION.json').read_text());reg={k:v for k,v in old.items() if k not in ['inputs','source_sha256','saved_review_source']}
reg.update(time=time.time(),cycles=[39,40],controller='admittance',expected_terminal_counts=[1194,1224],reason='Posthoc complete39/40 diagnostic: admittance terminal MAE .858953 to1.134465 and inbag MAE .396187 to.721100 despite lower logged loss. One CPU evaluation of all terminal rows distinguishes retained-row fitting drift from30 new rows. No optimization, physics, replay writes or weight promotion.',source_sha256=sha(runtime/'audit_admittance39_40_terminal_concentration_20261027.py'),saved_review_source=dict(path=str(runtime/'review_admittance39_40_terminal_concentration_20261027.py'),sha256=sha(runtime/'review_admittance39_40_terminal_concentration_20261027.py')),inputs={})
for oldcycle,newcycle in [(37,39),(38,40)]:
 refs={}
 for k,v in old['inputs'][str(oldcycle)].items():
  p=Path(v['path'].replace(f'cycle{oldcycle}',f'cycle{newcycle}').replace(f'cycle_000{oldcycle}',f'cycle_000{newcycle}').replace('/vmc/','/admittance/'))
  refs[k]=dict(path=str(p),sha256=sha(p))
 h=json.loads(Path(refs['health']['path']).read_text())['methods']['admittance'];assert h['terminal_count']=={39:1194,40:1224}[newcycle] and h['checkpoint_sha256']==refs['checkpoint']['sha256'];reg['inputs'][str(newcycle)]=refs
(out/'REGISTRATION.json').write_text(json.dumps(reg,indent=2)+'\n');(out/'SOURCE.diff').write_text(''.join(diffs))
coordinator='''from pathlib import Path
import subprocess,json,time,os,hashlib
os.sched_setaffinity(0,{52})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
r=B/'runs/admittance39_40_terminal_concentration_20261027_v1';s=B/'runtime/admittance39_40_terminal_concentration_20261027_v1'
try:
 for prefix,limit in [('audit',600),('review',120)]:
  script=s/f'{prefix}_admittance39_40_terminal_concentration_20261027.py'
  reg=json.loads((r/'REGISTRATION.json').read_text());expected=reg['source_sha256'] if prefix=='audit' else reg['saved_review_source']['sha256']
  assert hashlib.sha256(script.read_bytes()).hexdigest()==expected
  subprocess.run([str(B/'env/bin/python'),str(script),'--root',str(r)],check=True,timeout=limit,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 (r/'FINISHED.json').write_text(json.dumps(dict(completed=True,time=time.time()))+'\\n')
except BaseException as e:
 (r/'COORDINATOR_FAILURE.json').write_text(json.dumps(dict(error=repr(e),time=time.time()))+'\\n');raise
'''
ast.parse(coordinator);(runtime/'coordinator.py').write_text(coordinator)
with (out/'driver.log').open('x') as log:p=subprocess.Popen([str(B/'env/bin/python'),str(runtime/'coordinator.py')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
(out/'LAUNCH.json').write_text(json.dumps(dict(pid=p.pid,time=time.time(),coordinator_sha256=sha(runtime/'coordinator.py'),audit_limit_seconds=600,saved_review_limit_seconds=120),indent=2)+'\n');print('Original diagnostic coordinator',p.pid)
