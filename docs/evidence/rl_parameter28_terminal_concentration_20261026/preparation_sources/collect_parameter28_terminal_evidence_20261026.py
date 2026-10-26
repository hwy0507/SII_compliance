from pathlib import Path
import hashlib,json,shutil,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';out=R/'docs/evidence/rl_parameter28_terminal_concentration_20261026';out.mkdir(exist_ok=True)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
sources=[]
def cp(p,rel):
 if not p.exists():return
 dst=out/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst);sources.append(dict(source=str(p),destination=str(rel),sha256=sha(dst),bytes=dst.stat().st_size))
for name in ['admittance25_26_terminal_concentration_20261026_v1','admittance25_26_terminal_concentration_20261026_v2','admittance27_terminal_anchors_20261026_v1','parameter_capacity_pool30_cycle27_review_20261026_v1']:
 root=B/'runs'/name
 for p in root.rglob('*'):
  if p.is_file() and p.suffix in ['.json','.png','.py','.npz'] and '__pycache__' not in str(p):cp(p,Path(name)/p.relative_to(root))
for name,methods in [('parameter_capacity_pool30_cycle28_20261026_v1',['impedance','admittance','vmc']),('serl_multistep_batch65536_cycle19_20261026_v1',['direct'])]:
 root=B/'runs'/name
 for p in root.glob('*.json'):cp(p,Path(name)/p.name)
 cp(root/'startup/REVIEW.json',Path(name)/'startup/REVIEW.json')
 for m in methods:
  if m!='direct':
   for p in (root/m).glob('*.json'):cp(p,Path(name)/m/p.name)
  train=root/m if m=='direct' else root/m/'train'
  for n in ['EXECUTION.json','PROGRESS.json']:cp(train/n,Path(name)/m/n)
  log=(root if m=='direct' else root/m)/'check_only.log'
  if log.exists():
   parsed=[json.loads(v) for v in log.read_text().splitlines() if v.startswith('{')]
   dst=out/name/m;dst.mkdir(parents=True,exist_ok=True);(dst/'CHECK_ONLY_RESULT.json').write_text(json.dumps(dict(source=str(log),sha256=sha(log),results=parsed),indent=2)+'\n')
name='serl_cycle16_frozen_full30_20261026_v1';root=B/'runs'/name
for p in root.glob('*.json'):cp(p,Path(name)/p.name)
for shard in ['shard0','shard1']:
 for p in (root/shard).glob('*.json'):cp(p,Path(name)/shard/p.name)
for pattern in ['*parameter_capacity28*20261026.py','*serl_batch19*20261026.py','assign_serl18_review_released_cpu_20261026.py','assign_parameter27_review_released_cpu_20261026.py','collect_parameter28_terminal_evidence_20261026.py','archive_parameter28_terminal_20261026.py']:
 for p in (B/'runtime').glob(pattern):cp(p,Path('preparation_sources')/p.name)
for pattern in ['*capacity28_LAUNCH.json','*batch19_LAUNCH.json','assign_serl18*.launch.json','assign_parameter27*.launch.json']:
 for p in (B/'runtime').glob(pattern):cp(p,Path('preparation_sources')/p.name)
live={}
for name,methods in [('parameter_capacity_pool30_cycle27_20261026_v1',['impedance','admittance','vmc']),('parameter_capacity_pool30_cycle28_20261026_v1',['impedance','admittance','vmc']),('serl_multistep_batch65536_cycle18_20261026_v1',['direct'])]:
 for m in methods:
  p=B/'runs'/name/m/('PROGRESS.json' if m=='direct' else 'train/PROGRESS.json')
  if p.exists():live[name+'/'+m]=json.loads(p.read_text())
(out/'FINAL_LIVE_STATUS.json').write_text(json.dumps(dict(time=time.time(),progress=live,goal='active'),indent=2)+'\n')
(out/'SOURCES.json').write_text(json.dumps(sources,indent=2)+'\n');print(len(sources),out)
