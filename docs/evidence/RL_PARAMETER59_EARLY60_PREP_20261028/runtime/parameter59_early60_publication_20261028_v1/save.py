from pathlib import Path
import json,hashlib,ast,tarfile,time,socket,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';P=Path(__file__).parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def live(pid,tick):
 p=Path(f'/proc/{pid}/stat');s=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
 return dict(pid=pid,expected_start_ticks=str(tick),actual_start_ticks=s[19] if s else None,state=s[0] if s else None,live=bool(s and s[19]==str(tick) and s[0]!='Z'))
run=B/'runs/parameter_capacity_pool30_cycle59_20261026_v1';status=dict(time=time.time(),host=socket.gethostname(),identities={},parameter59={},frozen55={},gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu','--format=csv,noheader'],text=True),guard_stop=Path('/tmp/sii_gpu_util_guard_20261028_v5/STOP').exists())
for j in read(run/'LAUNCH.json')['jobs']:
 m=j['controller'];status['identities'][m]=live(j['pid'],j['proc_start_ticks']);status['parameter59'][m]=read(run/m/'train/PROGRESS.json')
for m,pid in [('impedance',1869175),('admittance',1869176),('vmc',1869177)]:status['frozen55'][m]=read(B/'runs/parameter55_frozen_full30_20261028_v1'/m/'PROGRESS.json');status['identities']['frozen_'+m]=live(pid,36428775)
for label,pid,tick in [('frozen_root',1869178,36428775),('guard_supervisor',3256866,37410686),('guard0',3256867,37410690),('guard1',3256868,37410690),('guard2',3256869,37410691),('guard3',3256870,37410693),('archive59',4084708,37574081),('loss59',4089956,37575729),('window59_61',4067967,37570184),('prepare60',294526,37642076),('anchor59',387806,37657716)]:status['identities'][label]=live(pid,tick)
assert all(x['live'] for x in status['identities'].values()) and not status['guard_stop']
(P/'LIVE_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
e=R/'docs/evidence/RL_PARAMETER59_EARLY60_PREP_20261028';e.mkdir(exist_ok=False);manifest=[]
for folder in ['runtime/parameter59_early60_publication_20261028_v1','runtime/prepare_parameter60_20261028_v1','runs/parameter59_first5000_20261028_v1','runs/vmc59_terminal_anchor_followup_20261028_v1']:
 for p in sorted((B/folder).rglob('*')):
  if not p.is_file() or p.suffix not in {'.json','.jsonl','.py','.png','.npz','.diff'}:continue
  data=p.read_bytes();rel=p.relative_to(B);dst=e/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
  if p.suffix=='.py':ast.parse(data)
  manifest.append(dict(source=str(p),member=str(rel),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(e/'MANIFEST.json').write_text(json.dumps(dict(time=time.time(),files=manifest),indent=2)+'\n')
archive=B/'repository'/('RL_PARAMETER59_EARLY60_PREP_'+time.strftime('%Y%m%d_%H%M%S',time.gmtime()));archive.mkdir();pack=archive/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(pack,'w:gz') as t:
 for p in sorted(e.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(e)))
with tarfile.open(pack,'r:gz') as t:
 members=t.getmembers()
 for m in members:assert t.extractfile(m).read()==(e/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(pack),bytes=pack.stat().st_size,sha256=sha(pack),members=len(members),all_member_bytes_verified=True,all_python_ast_passed=True,large_scientific_artifacts_remain_shared_ssd=True,hdd_or_arm1_full_backup=False)
(R/'docs/RL_PARAMETER59_EARLY60_PREP_SAVE_20261028.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2));print(json.dumps({k:v for k,v in status.items() if k!='identities'},indent=2))
