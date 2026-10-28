from pathlib import Path
import json,hashlib,time,tarfile,ast,subprocess,socket
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';OUT=Path(__file__).parent
run=B/'runs/parameter_capacity_pool30_cycle59_20261026_v1'
assert json.loads((run/'startup/REVIEW.json').read_text())['passed']
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def identity(pid,tick):
 p=Path(f'/proc/{pid}/stat');s=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
 return dict(pid=pid,expected_start_ticks=str(tick),actual_start_ticks=s[19] if s else None,state=s[0] if s else None,live=bool(s and s[19]==str(tick) and s[0]!='Z'))
status=dict(time=time.time(),host=socket.gethostname(),parameter59={},frozen55={},identities={},gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu','--format=csv,noheader'],text=True),guard_stop=Path('/tmp/sii_gpu_util_guard_20261028_v5/STOP').exists())
for j in read(run/'LAUNCH.json')['jobs']:
 m=j['controller'];status['parameter59'][m]=read(run/m/'train/PROGRESS.json');status['identities'][m]=identity(j['pid'],j['proc_start_ticks'])
for n in ['MONITOR_LAUNCH.json','STARTUP_LAUNCH.json']:
 j=read(run/n);status['identities'][n]=identity(j['pid'],j['proc_start_ticks'])
for m,pid in [('impedance',1869175),('admittance',1869176),('vmc',1869177)]:
 status['frozen55'][m]=read(B/'runs/parameter55_frozen_full30_20261028_v1'/m/'PROGRESS.json');status['identities']['frozen_'+m]=identity(pid,36428775)
for label,pid,tick in [('frozen_root',1869178,36428775),('guard_supervisor',3256866,37410686),('guard0',3256867,37410690),('guard1',3256868,37410690),('guard2',3256869,37410691),('guard3',3256870,37410693),('window59_61',4067967,37570184),('loss59',4089956,37575729)]:status['identities'][label]=identity(pid,tick)
assert all(v['live'] for k,v in status['identities'].items() if k!='STARTUP_LAUNCH.json') and not status['guard_stop']
(OUT/'LIVE_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
e=R/'docs/evidence/RL_PARAMETER58_COMPLETE_20261028';e.mkdir(exist_ok=False);sources=[]
folders=['runtime/parameter58_publication_20261028_v1','runtime/prepare_parameter59_20261028_v1','runtime/parameter59_loss_preparation_20261028_v1','runs/parameter_capacity_pool30_cycle58_review_20261026_v1','runs/parameter58_loss_20261028_v1','runs/vmc58_terminal_anchor_followup_20261028_v1','runs/parameter_capacity56_58_reward_stability_20261028_v1','runs/parameter_capacity59_61_reward_stability_20261028_v1','runs/parameter59_loss_20261028_v1']
for folder in folders:
 for p in (B/folder).rglob('*'):
  if p.is_file() and p.suffix in {'.json','.py','.diff','.png','.npz'} and p.stat().st_size<3_000_000:sources.append(p)
for p in (B/'runs/parameter_capacity_pool30_cycle58_archive_20261026_v1').rglob('*.json'):sources.append(p)
for n in ['LAUNCH.json','MONITOR_LAUNCH.json','STARTUP_LAUNCH.json','PRELAUNCH_SCIENTIFIC_REVIEW.json','CHECK_ONLY_COMPLETE.json','CHECK_ONLY_EXIT_CODES.json','COMMANDS.json','startup/REVIEW.json','startup_review.py','archive_review.py']:sources.append(run/n)
for m in ['impedance','admittance','vmc']:
 for n in ['REGISTRATION.json','check_only.log']:sources.append(run/m/n)
for n in ['LAUNCH.json','MONITOR_LAUNCH.json','ARCHIVE_REVIEW_FINISHED.json']:sources.append(B/'runs/parameter_capacity_pool30_cycle58_20261026_v1'/n)
manifest=[]
for p in sorted(set(sources)):
 data=p.read_bytes();rel=p.relative_to(B);d=e/rel;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),member=str(rel),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(e/'MANIFEST.json').write_text(json.dumps(dict(time=time.time(),host=socket.gethostname(),files=manifest),indent=2)+'\n')
arc=B/'repository'/('RL_PARAMETER58_COMPLETE_'+time.strftime('%Y%m%d_%H%M%S',time.gmtime()));arc.mkdir();package=arc/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(package,'w:gz') as t:
 for p in sorted(e.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(e)))
with tarfile.open(package,'r:gz') as t:
 members=t.getmembers()
 for m in members:assert t.extractfile(m).read()==(e/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(package),size=package.stat().st_size,sha256=sha(package),members=len(members),all_member_bytes_verified=True,all_python_ast_passed=True,large_artifacts_remain_shared_ssd=True,hdd_or_arm1_full_backup=False)
(R/'docs/RL_PARAMETER58_COMPLETE_SAVE_20261028.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2));print(json.dumps(status,indent=2))
