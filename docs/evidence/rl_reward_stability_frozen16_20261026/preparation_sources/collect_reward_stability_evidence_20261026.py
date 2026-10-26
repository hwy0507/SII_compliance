from pathlib import Path
import hashlib,json,shutil,time,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';out=R/'docs/evidence/rl_reward_stability_frozen16_20261026';out.mkdir(exist_ok=True)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
sources=[]
def cp(p,rel):
 if not p.exists():return
 dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);sources.append(dict(source=str(p),destination=str(rel),sha256=sha(dest),bytes=dest.stat().st_size))
for name in ['serl_cycles13_16_reward_stability_20261026_v1','serl_cycles13_16_reward_terms_20261026_v1','admittance26_terminal_loss_20261026_v1','parameter_capacity24_26_reward_stability_20261026_v1','parameter_capacity_pool30_cycle26_review_20261026_v1','serl_multistep_batch65536_cycle17_review_20261026_v1']:
 root=B/'runs'/name
 for p in root.rglob('*'):
  if p.is_file() and p.suffix in ['.json','.png','.py'] and '__pycache__' not in str(p):cp(p,Path(name)/p.relative_to(root))
name='serl_cycle16_frozen_full30_20261026_v1';root=B/'runs'/name
for p in root.glob('*.json'):cp(p,Path(name)/p.name)
for shard in ['shard0','shard1']:
 for p in (root/shard).glob('*.json'):cp(p,Path(name)/shard/p.name)
for n in ['evaluate_serl_seeded_multistep_20261026.py','audit_published_episode_20261025.py','summarize_published_episode_audit_20261025.py','replay_published_filter_audit_20261025.py','replay_published_torque_audit_20261025.py','review_serl_frozen_matrix_20261026.py']:cp(B/'runtime'/name/n,Path(name)/'frozen_sources'/n)
for name,methods in [('serl_multistep_batch65536_cycle18_20261026_v1',['direct']),('parameter_capacity_pool30_cycle27_20261026_v1',['impedance','admittance','vmc'])]:
 root=B/'runs'/name
 for p in root.glob('*.json'):cp(p,Path(name)/p.name)
 cp(root/'startup/REVIEW.json',Path(name)/'startup/REVIEW.json')
 for p in (root/'first5000_loss_audit').glob('*.json'):cp(p,Path(name)/'first5000_loss_audit'/p.name)
 for m in methods:
  if m!='direct':
   for p in (root/m).glob('*.json'):cp(p,Path(name)/m/p.name)
  train=root/m if m=='direct' else root/m/'train'
  cp(train/'EXECUTION.json',Path(name)/m/'EXECUTION.json');cp(train/'PROGRESS.json',Path(name)/m/'PROGRESS.json')
  log=(root if m=='direct' else root/m)/'check_only.log'
  if log.exists():
   parsed=[json.loads(l) for l in log.read_text().splitlines() if l.startswith('{')]
   dest=out/name/m;dest.mkdir(parents=True,exist_ok=True);(dest/'CHECK_ONLY_RESULT.json').write_text(json.dumps(dict(source=str(log),sha256=sha(log),results=parsed),indent=2)+'\n')
for pattern in ['*parameter_capacity27*20261026.py','*serl_batch18*20261026.py','collect_reward_stability_evidence_20261026.py','archive_reward_stability_20261026.py','audit_parameter27_first5000_20261026.py','audit_admittance26_terminal_loss_20261026.py','serl18_preparation_cpu_decision.json','assign_serl17_review_released_cpu_20261026.py','assign_serl17_review_released_cpu_LAUNCH.json']:
 for p in (B/'runtime').glob(pattern):cp(p,Path('preparation_sources')/p.name)
live={}
for name,method in [('serl_multistep_batch65536_cycle17_20261026_v1','direct'),('serl_multistep_batch65536_cycle18_20261026_v1','direct')]+[(f'parameter_capacity_pool30_cycle{c}_20261026_v1',m) for c in [26,27] for m in ['impedance','admittance','vmc']]:
 p=B/'runs'/name/method/('PROGRESS.json' if method=='direct' else 'train/PROGRESS.json')
 if p.exists():live[name+'/'+method]=json.loads(p.read_text())
(out/'FINAL_LIVE_STATUS.json').write_text(json.dumps(dict(time=time.time(),progress=live,goal='active',gpu_capture=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv,noheader'],text=True),gpu_scope='instantaneous mixed formal training and frozen16 inference; not a pure formal profile'),indent=2)+'\n')
(out/'SOURCES.json').write_text(json.dumps(sources,indent=2)+'\n');print(len(sources),out)
