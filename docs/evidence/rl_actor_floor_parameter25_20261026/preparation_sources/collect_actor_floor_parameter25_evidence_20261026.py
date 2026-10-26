from pathlib import Path
import hashlib,json,shutil,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';out=R/'docs/evidence/rl_actor_floor_parameter25_20261026';out.mkdir(exist_ok=True)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
sources=[]
def cp(p,relative):
 if not p.exists():return
 dst=out/relative;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
 sources.append(dict(source=str(p),destination=str(dst.relative_to(out)),sha256=sha(dst),bytes=dst.stat().st_size))
for name in ['serl_cycle15_actor_entropy_floor_gate_20261026_v1','serl_cycle15_actor_entropy_floor_probe_20261026_v1','parameter_capacity_pool30_cycle24_review_20261026_v1','parameter_cycles19_24_summary_20261026_v1']:
 root=B/'runs'/name
 for p in root.rglob('*'):
  if p.is_file() and p.suffix in ('.json','.png','.py') and '__pycache__' not in str(p):cp(p,Path(name)/p.relative_to(root))
 if 'actor_entropy_floor' in name:
  for p in (B/'runtime'/name).glob('*.py'):cp(p,Path(name)/'frozen_sources'/p.name)
for name,methods in [('parameter_capacity_pool30_cycle24_20261026_v1',['impedance','admittance','vmc']),('serl_multistep_batch65536_cycle16_20261026_v1',['direct'])]:
 root=B/'runs'/name
 assert json.loads((root/'startup/REVIEW.json').read_text())['passed']
 for p in root.glob('*.json'):cp(p,Path(name)/p.name)
 for p in root.glob('startup_review*.py'):cp(p,Path(name)/p.name)
 cp(root/'startup/REVIEW.json',Path(name)/'startup/REVIEW.json')
 cp(root/'capacity_boundary/REVIEW.json',Path(name)/'capacity_boundary/REVIEW.json')
 cp(root/'capacity_boundary_review.py',Path(name)/'capacity_boundary_review.py')
 for m in methods:
  if m!='direct':
   for p in (root/m).glob('*.json'):cp(p,Path(name)/m/p.name)
  run=root/m if m=='direct' else root/m/'train';cp(run/'EXECUTION.json',Path(name)/m/'EXECUTION.json')
  log=(root if m=='direct' else root/m)/'check_only.log';parsed=[json.loads(l) for l in log.read_text().splitlines() if l.startswith('{')]
  dest=out/name/m;dest.mkdir(exist_ok=True,parents=True)
  (dest/'CHECK_ONLY_RESULT.json').write_text(json.dumps(dict(source=str(log),sha256=sha(log),results=parsed),indent=2)+'\n')
for name in ['prepare_parameter_capacity25_20261026.py','setup_parameter_capacity25_monitors_20261026.py','launch_parameter_capacity25_20261026.py','wait_prepare_parameter_capacity25_20261026.py','prepare_serl_batch17_20261026.py','launch_serl_batch17_20261026.py','setup_serl_batch17_monitors_20261026.py','wait_prepare_serl_batch17_20261026.py','collect_actor_floor_parameter25_evidence_20261026.py','archive_actor_floor_parameter25_20261026.py']:
 cp(B/'runtime'/name,Path('preparation_sources')/name)
profile=B/'runs/batch16_parameter25_gpu_profile_20261026_v1'
for p in profile.iterdir():
 if p.suffix in ['.json','.py'] and p.name!='PROFILE.json':cp(p,Path(profile.name)/p.name)
if (profile/'PROFILE.json').exists():
 f=profile/'PROFILE.json';d=json.loads(f.read_text());summary={k:v for k,v in d.items() if k!='samples'};summary.update(samples=len(d['samples']),full_profile=dict(path=str(f),sha256=sha(f)),gpu_pid_sets=sorted({tuple(r['gpu_process_ids']) for r in d['samples']}));(out/'GPU_PROFILE_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
live=dict(time=time.time(),methods={})
for name in ['parameter_capacity_pool30_cycle25_20261026_v1','serl_multistep_batch65536_cycle16_20261026_v1']:
 root=B/'runs'/name;launch=json.loads((root/'LAUNCH.json').read_text());jobs=launch['jobs'] if 'jobs' in launch else [dict(controller='direct',**launch)]
 for job in jobs:
  m=job['controller'];pid=job['pid'];run=root/m if m=='direct' else root/m/'train';proc=Path(f'/proc/{pid}/cmdline')
  live['methods'][m]=dict(pid=pid,proc_cmdline=proc.read_bytes().replace(b'\0',b' ').decode() if proc.exists() else None,progress=json.loads((run/'PROGRESS.json').read_text()),failure=(run/'FAILURE.json').exists())

root=B/'runs/parameter_capacity_pool30_cycle25_20261026_v1'
if root.exists():
 for p in root.glob('*.json'):cp(p,Path(root.name)/p.name)
 for m in ['impedance','admittance','vmc']:
  for p in (root/m).glob('*.json'):cp(p,Path(root.name)/m/p.name)
  cp(root/m/'train/EXECUTION.json',Path(root.name)/m/'EXECUTION.json')
  log=root/m/'check_only.log'
  if log.exists():
   parsed=[json.loads(l) for l in log.read_text().splitlines() if l.startswith('{')]
   dest=out/root.name/m;dest.mkdir(exist_ok=True,parents=True)
   (dest/'CHECK_ONLY_RESULT.json').write_text(json.dumps(dict(source=str(log),sha256=sha(log),results=parsed),indent=2)+'\n')
 cp(root/'startup/REVIEW.json',Path(root.name)/'startup/REVIEW.json')

(out/'LIVE_STATUS.json').write_text(json.dumps(live,indent=2)+'\n');(out/'SOURCES.json').write_text(json.dumps(sources,indent=2)+'\n');print(len(sources),out)
