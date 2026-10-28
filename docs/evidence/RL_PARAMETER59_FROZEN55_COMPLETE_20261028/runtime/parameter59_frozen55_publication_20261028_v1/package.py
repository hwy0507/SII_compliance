from pathlib import Path
import json, hashlib, ast, tarfile, time, socket, subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
R=B/'repository/SII_compliance'; P=Path(__file__).parent
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def live(pid,tick):
 p=Path(f'/proc/{pid}/stat'); s=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
 return dict(pid=pid,expected_start_ticks=str(tick),actual_start_ticks=s[19] if s else None,state=s[0] if s else None,live=bool(s and s[19]==str(tick) and s[0]!='Z'))
run=B/'runs/parameter_capacity_pool30_cycle60_20261026_v1'
status=dict(time=time.time(),host=socket.gethostname(),identities={},parameter60={},gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu','--format=csv,noheader'],text=True),guard_stop=Path('/tmp/sii_gpu_util_guard_20261028_v5/STOP').exists())
for j in read(run/'LAUNCH.json')['jobs']:
 m=j['controller']; status['identities'][m]=live(j['pid'],j['proc_start_ticks']); status['parameter60'][m]=read(run/m/'train/PROGRESS.json')
for name,ref in [('archive60',run/'MONITOR_LAUNCH.json'),('loss60',B/'runs/parameter60_loss_20261028_v1/LAUNCH.json'),('prepare61',B/'runtime/prepare_parameter61_20261028_v1/parameter_LAUNCH.json')]:
 j=read(ref);status['identities'][name]=live(j['pid'],j['proc_start_ticks'])
for label,pid,tick in [('guard_supervisor',3256866,37410686),('guard0',3256867,37410690),('guard1',3256868,37410690),('guard2',3256869,37410691),('guard3',3256870,37410693),('window59_61',4067967,37570184)]:status['identities'][label]=live(pid,tick)
assert all(x['live'] for x in status['identities'].values()) and not status['guard_stop']
assert read(run/'startup/REVIEW.json')['passed']
assert read(B/'runs/parameter41_55_frozen_comparison_20261028_v2/REVIEW.json')['passed']
(P/'LIVE_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
e=R/'docs/evidence/RL_PARAMETER59_FROZEN55_COMPLETE_20261028';e.mkdir(exist_ok=False)
manifest=[]; selected=set()
folders=['runtime/parameter59_frozen55_publication_20261028_v1','runtime/prepare_parameter60_20261028_v1','runtime/prepare_parameter61_20261028_v1','runtime/parameter60_loss_preparation_20261028_v1','runs/parameter59_loss_20261028_v1','runs/parameter60_loss_20261028_v1','runs/vmc59_terminal_anchor_followup_20261028_v1','runs/parameter_capacity_pool30_cycle59_review_20261026_v1','runs/parameter41_55_frozen_comparison_20261028_v1','runs/parameter41_55_frozen_comparison_20261028_v2']
for folder in folders:
 for p in (B/folder).rglob('*'):
  if p.is_file() and p.suffix in {'.json','.py','.png','.npz','.diff','.log'}:selected.add(p)
for cycle in [59,60]:
 root=B/f'runs/parameter_capacity_pool30_cycle{cycle}_20261026_v1'
 selected.update(p for p in root.glob('*.json'))
 selected.update(root.glob('*.py'))
 selected.update(root.glob('startup/REVIEW.json'))
 for m in ['impedance','admittance','vmc']:
  selected.update((root/m).glob('*.json'));selected.add(root/m/'check_only.log')
  if cycle==59:selected.update((root/m/'train').glob('FINISHED.json'))
root=B/'runs/parameter55_frozen_full30_20261028_v1'
selected.update(root.glob('*.json'));selected.update(root.glob('*.png'));selected.update(root.glob('*.diff'))
for m in ['impedance','admittance','vmc']:
 selected.update((root/m).glob('*.json'));selected.update((root/m).glob('*/rollout.json'))
for p in sorted(selected):
 data=p.read_bytes();rel=p.relative_to(B);dst=e/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),member=str(rel),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(e/'MANIFEST.json').write_text(json.dumps(dict(time=time.time(),files=manifest),indent=2)+'\n')
archive=B/'repository'/('RL_PARAMETER59_FROZEN55_COMPLETE_'+time.strftime('%Y%m%d_%H%M%S',time.gmtime()));archive.mkdir();pack=archive/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(pack,'w:gz') as t:
 for p in sorted(e.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(e)))
with tarfile.open(pack,'r:gz') as t:
 members=t.getmembers()
 for m in members:assert t.extractfile(m).read()==(e/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(pack),bytes=pack.stat().st_size,sha256=sha(pack),members=len(members),all_member_bytes_verified=True,all_python_ast_passed=True,large_scientific_artifacts_remain_shared_ssd=True,hdd_or_arm1_full_backup=False)
(R/'docs/RL_PARAMETER59_FROZEN55_COMPLETE_SAVE_20261028.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2));print(json.dumps(status,indent=2))
