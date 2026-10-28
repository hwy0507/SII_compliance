"""Verify actual69 startup and archive selected complete68/launch69 evidence."""
from pathlib import Path
import ast, hashlib, json, math, socket, subprocess, tarfile, time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
R=B/'repository/SII_compliance';HERE=Path(__file__).resolve().parent
TAG='RL_PARAMETER68_COMPLETE_20261028';run=B/'runs/parameter_capacity_pool30_cycle69_20261026_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(j):
    p=Path(f'/proc/{j["pid"]}/stat');s=p.read_text().rsplit(')',1)[1].split()
    assert s[19]==j['proc_start_ticks'] and s[0]!='Z'
    return dict(pid=j['pid'],proc_start_ticks=s[19],state=s[0],live=True)
startup=read(run/'startup/REVIEW.json');assert startup['passed']
learners=[]
for j in read(run/'LAUNCH.json')['jobs']:
    row=identity(j);p=run/j['controller']/'train'
    assert not(p/'FAILURE.json').exists() and not(p/'FINISHED.json').exists()
    row.update(controller=j['controller'],progress=read(p/'PROGRESS.json'));learners.append(row)
watchers={}
for name,p in [('archive',run/'MONITOR_LAUNCH.json'),('loss69',B/'runs/parameter69_loss_20261028_v1/LAUNCH.json'),('window68_70',B/'runs/parameter_capacity68_70_reward_stability_20261028_v1/LAUNCH.json')]:
    watchers[name]=identity(read(p))
for name,pid,ticks in [('guard',3256866,'37410686'),('guard0',3256867,'37410690'),('guard1',3256868,'37410690'),('guard2',3256869,'37410691'),('guard3',3256870,'37410693')]:
    watchers[name]=identity(dict(pid=pid,proc_start_ticks=ticks))
assert not Path('/tmp/sii_gpu_util_guard_20261028_v5/STOP').exists()
assert (B/'runtime/gpu_util_guard_20261028_v4/STOP').exists()
snapshot=dict(time=time.time(),learners=learners,watchers=watchers,gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu','--format=csv,noheader'],text=True),startup_sha256=sha(run/'startup/REVIEW.json'),no_automatic70_training=True)
(HERE/'SNAPSHOT.json').write_text(json.dumps(snapshot,indent=2)+'\n')
start=read(B/'runtime/parameter68_complete_observer_20261028_v1/REVIEW.json')['last_time'];guard=[]
for line in Path('/tmp/sii_gpu_util_guard_20261028_v5/samples.jsonl').read_text().splitlines():
    row=json.loads(line)
    if start<row['time']<=snapshot['time']:guard.append(row)
assert len(guard)>1
(HERE/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in guard))
g={}
for i in range(4):
    values=[next(v['utilization'] for v in row['gpus'] if v['gpu']==i) for row in guard]
    g[str(i)]=dict(minimum=min(values),mean=math.fsum(values)/len(values),below50=sum(v<50 for v in values))
(HERE/'GUARD_REVIEW.json').write_text(json.dumps(dict(samples=len(guard),gpus=g,max_gap_seconds=max(b['time']-a['time'] for a,b in zip(guard,guard[1:])),synthetic_guard_included=True,per_instant_guarantee=False),indent=2)+'\n')
selected=set();suffixes={'.json','.jsonl','.py','.diff','.png','.npz','.log'}
def folder(rel,recurse=False):
    root=B/rel
    for p in (root.rglob('*') if recurse else root.iterdir()):
        if p.is_file() and p.suffix in suffixes:
            assert p.stat().st_size<3_000_000,str(p)
            selected.add(p)
for rel in ['runs/parameter68_loss_20261028_v1','runs/parameter_task_label_audit68_20261028_v1','runs/vmc68_terminal_anchor_followup_20261028_v1','runs/admittance68_terminal_anchor_followup_20261028_v1','runs/vmc68_ranked67_terminal_followup_20261028_v1','runtime/parameter68_complete_observer_20261028_v1','runtime/prepare_parameter69_20261028_v1','runtime/parameter69_loss_preparation_20261028_v1','runtime/parameter_task_label_audit68_20261028_v1','runtime/parameter68_complete_publication_20261028_v1']:
    folder(rel)
folder('runs/parameter_capacity_pool30_cycle68_review_20261026_v1',True)
for p in run.iterdir():
    if p.is_file() and p.suffix in {'.json','.py'}:selected.add(p)
selected.add(run/'startup/REVIEW.json')
for m in ['impedance','admittance','vmc']:
    selected.update(run/m/n for n in ['REGISTRATION.json','check_only.log'])
    selected.add(B/f'runs/parameter_capacity_pool30_cycle68_archive_20261026_v1/{m}/cycle_00068.json')
    selected.add(B/f'runs/parameter_capacity_pool30_cycle68_20261026_v1/{m}/train/FINISHED.json')
for name in read(run/'impedance/REGISTRATION.json')['batch_size_stage']['dependency_hashes']:
    p=B/'runtime/parameter_capacity_pool30_cycle69_20261026_v1'/name
    assert sha(p)==read(run/'impedance/REGISTRATION.json')['batch_size_stage']['dependency_hashes'][name];selected.add(p)
for p in (B/'runs/parameter69_loss_20261028_v1').iterdir():
    if p.is_file() and p.suffix in {'.json','.py'}:selected.add(p)
selected.update(B/rel for rel in ['runs/parameter_capacity_pool30_cycle68_20261026_v1/LAUNCH.json','runs/parameter_capacity_pool30_cycle68_20261026_v1/ARCHIVE_REVIEW_FINISHED.json','runs/parameter_capacity68_70_reward_stability_20261028_v1/PLAN.json','runs/parameter_capacity68_70_reward_stability_20261028_v1/LAUNCH.json'])
dest=R/'docs/evidence'/TAG;dest.mkdir();files=[]
for p in sorted(selected):
    data=p.read_bytes();assert len(data)<3_000_000
    if p.suffix=='.py':ast.parse(data)
    rel=p.relative_to(B);target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(data)
    assert target.read_bytes()==data
    files.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(target)))
(dest/'MANIFEST.json').write_text(json.dumps(dict(time=time.time(),host=socket.gethostname(),files=files,scope='Completed68 small evidence, explicit launch69 dependencies, actual startup and current snapshot. Excludes large checkpoints/replay/raw and unrelated legacy runtime sources.'),indent=2)+'\n')
adir=B/'repository'/f'{TAG}_{time.strftime("%H%M%S",time.gmtime())}';adir.mkdir();archive=adir/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
    for p in sorted(dest.rglob('*')):
        if p.is_file():t.add(p,arcname=str(p.relative_to(dest)))
with tarfile.open(archive) as t:
    members=t.getmembers();assert len(members)==len(files)+1
    for m in members:assert t.extractfile(m).read()==(dest/m.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),members=len(members),bytes=archive.stat().st_size,sha256=sha(archive),all_member_bytes_verified=True,python_ast_verified=True,not_hdd_or_arm1_full_backup=True)
(R/'docs/RL_PARAMETER68_COMPLETE_SAVE_20261028.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(receipt=receipt,snapshot=snapshot,guard=read(HERE/'GUARD_REVIEW.json')),indent=2))
