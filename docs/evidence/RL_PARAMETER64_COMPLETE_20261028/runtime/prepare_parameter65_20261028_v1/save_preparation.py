from pathlib import Path
import json,hashlib,ast,tarfile,time,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';tag='RL_PARAMETER64_WAIT65_PREP_20261028';out=R/'docs/evidence'/tag
assert not out.exists();out.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=[]
for rel in ['runtime/prepare_parameter65_20261028_v1','runtime/parameter65_loss_preparation_20261028_v1','runs/parameter_capacity65_67_reward_stability_20261028_v1','runs/vmc63_ranked_terminal_diagnosis_20261028_v1','runs/vmc64_ranked63_terminal_followup_20261028_v1','runtime/parameter64_verified_wait_1526_20261028_v1']:
 for p in (B/rel).rglob('*'):
  if p.is_file() and p.suffix in ['.json','.jsonl','.py','.diff','.png','.npz','.log'] and p.stat().st_size<5_000_000:paths.append(p)
entries=[]
for p in sorted(paths):
 data=p.read_bytes();assert data==p.read_bytes(),str(p);rel=p.relative_to(B);q=out/rel;q.parent.mkdir(parents=True,exist_ok=True)
 with q.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 assert q.read_bytes()==data
 if q.suffix=='.py':ast.parse(data)
 entries.append(dict(source=str(p),member=str(rel),bytes=len(data),sha256=sha(q)))
(out/'MANIFEST.json').write_text(json.dumps(dict(time=time.time(),members=entries,all_snapshot_bytes_verified=True,python_ast_passed=True,large_artifacts_remain_shared_ssd=True),indent=2)+'\n')
pack=B/'repository'/(tag+'_'+time.strftime('%H%M%S',time.gmtime()));pack.mkdir();archive=pack/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as f:
 for x in entries:f.add(out/x['member'],arcname=x['member'])
 f.add(out/'MANIFEST.json',arcname='MANIFEST.json')
with tarfile.open(archive) as f:
 for x in entries:
  d=f.extractfile(x['member']).read();assert len(d)==x['bytes'] and hashlib.sha256(d).hexdigest()==x['sha256']
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(entries),all_member_bytes_verified=True,all_python_ast_passed=True,large_artifacts_remain_shared_ssd=True,hdd_or_arm1_full_backup=False)
(R/'docs/RL_PARAMETER64_WAIT65_PREP_SAVE_20261028.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
