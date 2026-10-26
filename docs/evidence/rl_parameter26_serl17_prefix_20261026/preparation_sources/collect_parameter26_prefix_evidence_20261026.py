from pathlib import Path
import hashlib,json,shutil,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';out=R/'docs/evidence/rl_parameter26_serl17_prefix_20261026';out.mkdir(exist_ok=True)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
sources=[]
def cp(p,rel):
 if not p.exists():return
 dst=out/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst);sources.append(dict(source=str(p),destination=str(rel),sha256=sha(dst),bytes=dst.stat().st_size))
for name in ['serl_cycle16_actor_floor_physical_prefix_20261026_v1','parameter_capacity_pool30_cycle25_review_20261026_v1']:
 root=B/'runs'/name
 for p in root.rglob('*'):
  if p.is_file() and p.suffix in ['.json','.png','.py'] and '__pycache__' not in str(p):cp(p,Path(name)/p.relative_to(root))
 for p in (B/'runtime'/name).glob('*.py'):cp(p,Path(name)/'frozen_sources'/p.name)
for name,methods in [('serl_multistep_batch65536_cycle17_20261026_v1',['direct']),('parameter_capacity_pool30_cycle26_20261026_v1',['impedance','admittance','vmc'])]:
 root=B/'runs'/name
 if not root.exists():continue
 for p in root.glob('*.json'):cp(p,Path(name)/p.name)
 cp(root/'startup/REVIEW.json',Path(name)/'startup/REVIEW.json');cp(root/'startup_review.py',Path(name)/'startup_review.py')
 for m in methods:
  if m!='direct':
   for p in (root/m).glob('*.json'):cp(p,Path(name)/m/p.name)
  run=root/m if m=='direct' else root/m/'train';cp(run/'EXECUTION.json',Path(name)/m/'EXECUTION.json')
  log=(root if m=='direct' else root/m)/'check_only.log'
  if log.exists():
   parsed=[json.loads(l) for l in log.read_text().splitlines() if l.startswith('{')]
   dest=out/name/m;dest.mkdir(parents=True,exist_ok=True);(dest/'CHECK_ONLY_RESULT.json').write_text(json.dumps(dict(source=str(log),sha256=sha(log),results=parsed),indent=2)+'\n')
for n in ['prepare_parameter_capacity26_20261026.py','launch_parameter_capacity26_20261026.py','setup_parameter_capacity26_monitors_20261026.py','wait_prepare_parameter_capacity26_20261026.py','collect_parameter26_prefix_evidence_20261026.py','archive_parameter26_prefix_20261026.py']:
 cp(B/'runtime'/n,Path('preparation_sources')/n)
profile=B/'runs/batch17_parameter26_gpu_profile_20261026_v1'
for p in profile.iterdir():
 if p.suffix in ['.json','.py'] and p.name!='PROFILE.json':cp(p,Path(profile.name)/p.name)
f=profile/'PROFILE.json'
if f.exists():
 d=json.loads(f.read_text());summary={k:v for k,v in d.items() if k!='samples'};summary.update(samples=len(d['samples']),full_profile=dict(path=str(f),sha256=sha(f)),gpu_pid_sets=sorted({tuple(r['gpu_process_ids']) for r in d['samples']}));(out/'GPU_PROFILE_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
(out/'SOURCES.json').write_text(json.dumps(sources,indent=2)+'\n');print(len(sources),out)
