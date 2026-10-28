from pathlib import Path
import json,hashlib,shutil,tarfile,ast,time,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance'
TAG='RL_PARAMETER63_COMPLETE_20261028';dest=R/'docs/evidence'/TAG
assert not dest.exists();dest.mkdir(parents=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
paths=set()
for rel in ['runs/parameter63_loss_20261028_v1','runs/parameter_capacity_pool30_cycle63_review_20261026_v1','runs/vmc63_terminal_anchor_followup_20261028_v1','runs/parameter_task_label_audit63_20261028_v1','runtime/prepare_parameter64_20261028_v1','runtime/parameter63_verified_wait_1429_20261028_v1','runs/parameter64_loss_20261028_v1','runs/vmc63_new62_terminal_followup_20261028_v1']:
    for p in (B/rel).rglob('*'):
        if 'partial_evidence' not in p.parts and p.is_file() and p.suffix in {'.json','.jsonl','.py','.diff','.png','.npz','.log'} and '__pycache__' not in p.parts and p.stat().st_size<5_000_000:paths.add(p)
for cycle in [63,64]:
    root=B/f'runs/parameter_capacity_pool30_cycle{cycle}_20261026_v1'
    for p in root.glob('*'):
        if 'partial_evidence' not in p.parts and p.is_file() and p.suffix in {'.json','.py'}:paths.add(p)
    for m in ['impedance','admittance','vmc']:
        for name in ['REGISTRATION.json','check_only.log','train/FINISHED.json']:
            p=root/m/name
            if p.exists():paths.add(p)
    for p in (root/'startup').glob('*.json'):paths.add(p)
for name in ['PLAN.json','LAUNCH.json']:
    paths.add(B/'runs/parameter_capacity62_64_reward_stability_20261028_v1'/name)
entries=[]
for p in sorted(paths):
    rel=p.relative_to(B);q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True)
    data=p.read_bytes()
    assert data==p.read_bytes(), f'source changed during snapshot: {p}'
    with q.open('xb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    assert data==q.read_bytes(), f'snapshot verification failed: {q}'
    if p.suffix=='.py':ast.parse(q.read_text())
    entries.append(dict(source=str(p),member=str(rel),bytes=q.stat().st_size,sha256=sha(q)))
manifest=dict(time=time.time(),members=entries,large_artifacts_excluded=True,all_python_ast_passed=True)
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
pack=B/'repository'/('RL_PARAMETER63_COMPLETE_20261028_'+time.strftime('%H%M%S',time.gmtime()));pack.mkdir()
archive=pack/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tf:
    for x in entries:tf.add(dest/x['member'],arcname=x['member'])
    tf.add(dest/'MANIFEST.json',arcname='MANIFEST.json')
with tarfile.open(archive) as tf:
    for x in entries:
        data=tf.extractfile(x['member']).read();assert len(data)==x['bytes'] and hashlib.sha256(data).hexdigest()==x['sha256']
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(entries),all_member_bytes_verified=True,all_python_ast_passed=True,large_artifacts_remain_shared_ssd=True,hdd_or_arm1_full_backup=False)
(R/'docs/RL_PARAMETER63_COMPLETE_SAVE_20261028.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
