"""Archive only this turn's completed, small evidence and explicit dependencies."""
from pathlib import Path
import ast
import hashlib
import json
import socket
import tarfile
import time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
R=B/'repository/SII_compliance'
TAG='RL_PARAMETER68_WAIT_RANKED67_20261028'
DEST=R/'docs/evidence'/TAG
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
observer=B/'runtime/parameter68_verified_wait_1940_20261028_v1'
assert read(observer/'FINISHED.json')['completed'] and read(observer/'REVIEW.json')['passed']
rank=B/'runs/vmc67_ranked_terminal_diagnosis_20261028_v1'
assert read(rank/'REVIEW.json')['passed'] and read(rank/'SAVED_REVIEW.json')['passed']
assert read(rank/'PLOT_INSPECTION.json')['inspected']
prep=B/'runtime/parameter69_loss_preparation_20261028_v1'
assert read(prep/'DEPLOY_SOURCE_REVIEW.json')['passed']
assert read(prep/'DEPLOY_REJECTION.json')['passed']
sources=[]
for folder in [observer,rank,prep]:
    sources.extend(p for p in folder.iterdir() if p.is_file())
sources.append(Path(__file__).resolve())
sources.append(B/'runtime/parameter68_followup_snapshot_20261028_v1/SNAPSHOT.json')
prior=B/'runs/vmc67_terminal_anchor_followup_20261028_v1'
sources.extend(prior/n for n in ['values.npz','REVIEW.json','SAVED_VALUES_REVIEW.json'])
sources.extend(B/p for p in [
    'runs/parameter_capacity_pool30_cycle68_20261026_v1/LAUNCH.json',
    'runs/parameter68_loss_20261028_v1/PLAN.json',
    'runs/parameter_capacity68_70_reward_stability_20261028_v1/PLAN.json',
    'runtime/parameter68_loss_preparation_20261028_v1/deploy.py',
])
assert len(sources)==len(set(sources))
DEST.mkdir()
files=[]
for p in sorted(sources):
    data=p.read_bytes();assert len(data)<3_000_000
    if p.suffix=='.py':ast.parse(data)
    relative=p.relative_to(B);target=DEST/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(data)
    assert target.read_bytes()==data
    files.append(dict(source=str(p),relative=str(relative),bytes=len(data),sha256=sha(target)))
manifest=dict(time=time.time(),host=socket.gethostname(),files=files,scope='Selected completed small evidence and explicit dependencies; no large model/replay/raw archive.')
(DEST/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive_dir=B/'repository'/f'{TAG}_{time.strftime("%H%M%S",time.gmtime())}'
archive_dir.mkdir();archive=archive_dir/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
    for p in sorted(DEST.rglob('*')):
        if p.is_file():t.add(p,arcname=str(p.relative_to(DEST)))
with tarfile.open(archive) as t:
    members=t.getmembers();assert len(members)==len(files)+1
    for m in members:
        assert t.extractfile(m).read()==(DEST/m.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),members=len(members),bytes=archive.stat().st_size,sha256=sha(archive),all_member_bytes_verified=True,python_ast_verified=True,not_hdd_or_arm1_full_backup=True)
(R/f'docs/{TAG}_SAVE.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
