from pathlib import Path
import os,json,hashlib,tarfile,time,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/user_shutdown_pause_20261027_v1';os.sched_setaffinity(0,{52})
paths=set()
for name in ['source_train17_clock','serl_state_adapter_20261026_v1','serl_capacity_batch65536_cycle25_20261027_v1','parameter_capacity_pool30_cycle41_20261026_v1','parameter41_frozen_full30_20261027_v1','serl_cycle26_frozen_full30_20261027_v1','admittance39_40_terminal_concentration_20261027_v1','serl_capacity26_monitor_templates_20261027_v1']:
 root=B/'runtime'/name
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and '.git' not in p.parts:paths.add(p)
paths.update((B/'runtime').glob('*.py'));paths.add(B/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json')
upstream=json.loads((B/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json').read_text())
for name,h in upstream['files'].items():
 p=B/'runtime/serl_upstream_1fa2af7'/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==h;paths.add(p)
paths.update(p for p in (B/'runs/cohort30_v2').rglob('*') if p.is_file() and p.suffix in ['.json','.mjb','.xml'])
# All existing registrations/plans needed by strict historical-chain checks.
raw=subprocess.check_output(['rg','--files','-g','REGISTRATION.json','-g','PLAN.json',str(B/'runs')],text=True)
paths.update(Path(p) for p in raw.splitlines())
for name in ['serl_capacity_batch65536_cycle24_review_20261027_v1','serl_capacity_batch65536_cycle25_20261027_v1','parameter_capacity_pool30_cycle40_review_20261026_v1','parameter_capacity_pool30_cycle41_review_20261026_v1','parameter_capacity_pool30_cycle41_20261026_v1','parameter_capacity39_41_reward_stability_20261027_v1','serl_capacity24_26_reward_stability_20261027_v1','parameter41_frozen_full30_20261027_v1','serl_cycle26_frozen_full30_20261027_v1','admittance41_terminal_anchor_followup_20261027_v1','parameter41_42_transition_20261027_v1']:
 root=B/'runs'/name
 for p in root.rglob('*'):
  if p.is_file() and (p.suffix in ['.json','.py','.png'] or p.name in ['episodes.jsonl','optimizer.jsonl','transitions.jsonl','STOP_REQUESTED','train.log','driver.log','wait.log']):paths.add(p)
archive=O/'FROZEN_SOURCES_AND_KEY_RESULTS.tar.gz';records=[]
with tarfile.open(archive,'w:gz',compresslevel=1) as tar:
 for p in sorted(paths):
  data=p.read_bytes();name=str(p.relative_to(B));tar.add(p,arcname=name,recursive=False);records.append(dict(name=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
with tarfile.open(archive,'r:gz') as tar:
 assert len(tar.getmembers())==len(records)
 for row in records:
  data=tar.extractfile(row['name']).read();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
with archive.open('rb') as f:archive_sha=hashlib.file_digest(f,'sha256').hexdigest()
receipt=dict(passed=True,time=time.time(),archive=str(archive),archive_sha256=archive_sha,archive_bytes=archive.stat().st_size,member_count=len(records),members=records,scope='Frozen runtimes, upstream manifest/source, fixtures/MJB, registrations/plans and selected latest results/logs. Checkpoints copied separately. Raw full-history trajectories, environments and all historical diagnostic inputs are not fully duplicated; keep entire original sharedSSD B tree.')
(O/'DEPENDENCY_ARCHIVE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='members'},indent=2))
