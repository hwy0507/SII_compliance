from pathlib import Path
import json,hashlib,ast,tarfile,time,socket,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';P=Path(__file__).parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat');s=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
 return dict(pid=j['pid'],expected_start_ticks=j['proc_start_ticks'],actual_start_ticks=s[19] if s else None,state=s[0] if s else None,live=bool(s and s[19]==j['proc_start_ticks'] and s[0]!='Z'))
run=B/'runs/parameter_capacity_pool30_cycle61_20261026_v1'
assert read(run/'startup/REVIEW.json')['passed']
status=dict(time=time.time(),host=socket.gethostname(),identities={},parameter61={},gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu','--format=csv,noheader'],text=True),guard_stop=Path('/tmp/sii_gpu_util_guard_20261028_v5/STOP').exists())
for j in read(run/'LAUNCH.json')['jobs']:
 m=j['controller'];status['identities'][m]=live(j);status['parameter61'][m]=read(run/m/'train/PROGRESS.json')
for label,path in [('archive61',run/'MONITOR_LAUNCH.json'),('loss61',B/'runs/parameter61_loss_20261028_v1/LAUNCH.json')]:status['identities'][label]=live(read(path))
for label,pid,tick in [('guard_supervisor',3256866,'37410686'),('guard0',3256867,'37410690'),('guard1',3256868,'37410690'),('guard2',3256869,'37410691'),('guard3',3256870,'37410693'),('window59_61',4067967,'37570184')]:status['identities'][label]=live(dict(pid=pid,proc_start_ticks=tick))
assert all(v['live'] for v in status['identities'].values()) and not status['guard_stop']
(P/'LIVE_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
e=R/'docs/evidence/RL_PARAMETER60_COMPLETE_20261028';e.mkdir(exist_ok=False);selected=set();manifest=[]
for folder in ['runtime/parameter60_complete_publication_20261028_v1','runtime/prepare_parameter61_20261028_v1','runtime/parameter61_loss_preparation_20261028_v1','runs/parameter60_loss_20261028_v1','runs/parameter61_loss_20261028_v1','runs/vmc60_terminal_anchor_followup_20261028_v1','runs/parameter_capacity_pool30_cycle60_review_20261026_v1']:
 for p in (B/folder).rglob('*'):
  if p.is_file() and p.suffix in {'.json','.py','.png','.npz','.diff','.log'}:selected.add(p)
for c in [60,61]:
 root=B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1';selected.update(root.glob('*.json'));selected.update(root.glob('*.py'));selected.update(root.glob('startup/REVIEW.json'))
 for m in ['impedance','admittance','vmc']:
  selected.update((root/m).glob('*.json'));selected.add(root/m/'check_only.log')
  if c==60:selected.update((root/m/'train').glob('FINISHED.json'))
for p in sorted(selected):
 data=p.read_bytes();rel=p.relative_to(B);dest=e/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),member=str(rel),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(e/'MANIFEST.json').write_text(json.dumps(dict(time=time.time(),files=manifest),indent=2)+'\n')
folder=B/'repository'/('RL_PARAMETER60_COMPLETE_'+time.strftime('%Y%m%d_%H%M%S',time.gmtime()));folder.mkdir();pack=folder/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(pack,'w:gz') as t:
 for p in sorted(e.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(e)))
with tarfile.open(pack,'r:gz') as t:
 members=t.getmembers()
 for m in members:assert t.extractfile(m).read()==(e/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(pack),bytes=pack.stat().st_size,sha256=sha(pack),members=len(members),all_member_bytes_verified=True,all_python_ast_passed=True,large_artifacts_remain_shared_ssd=True,hdd_or_arm1_full_backup=False)
(R/'docs/RL_PARAMETER60_COMPLETE_SAVE_20261028.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2));print(json.dumps({k:v for k,v in status.items() if k!='identities'},indent=2))
