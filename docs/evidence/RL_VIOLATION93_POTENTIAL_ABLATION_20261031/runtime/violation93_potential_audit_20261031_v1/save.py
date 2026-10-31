from pathlib import Path
import json,hashlib,ast,time,socket,os,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';O=B/'runs/violation93_potential_audit_20261031_v1';Q=B/'runs/violation93_potential_ablation_20261031_v1';QD=B/'runtime/violation93_potential_ablation_20261031_v1';TAG='RL_VIOLATION93_POTENTIAL_ABLATION_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
for m in ['impedance','admittance','vmc']:
 for folder,name in [(O,m+'_REVIEW.json'),(O,m+'_SAVED_REVIEW.json'),(Q,m+'_REVIEW.json')]:assert rd(folder/name)['passed']
for folder in [O,Q]:assert rd(folder/'FINISHED.json')['passed'] and not list(folder.glob('*FAILURE*'))
assert rd(Q/'SAVED_REVIEW.json')['passed'];raw=rd(O/'LARGE_STORAGE_REVIEW.json');assert raw['passed']
for item in raw['files']:assert sha(item['path'])==item['sha256'] and Path(item['path']).stat().st_size==item['bytes']
for folder,name in [(O,'LAUNCH.json'),(O,'REVIEW_LAUNCH.json'),(Q,'LAUNCH.json')]:
 for j in rd(folder/name)['jobs']:
  p=Path('/proc',str(j['pid']),'stat');s=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
  assert s is None or s[0]=='Z' or s[19]!=j['start']
pi=rd(Q/'PLOT_INSPECTION.json');assert pi['actual_visual_inspection']
for p in pi['plots']:assert p['inspected'] and sha(p['path'])==p['sha256']
for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]:
 s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==start
G=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (G/'STOP').exists() and not (G/'FAILURE.json').exists();rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True);put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,all_new_diagnostics_finished=True,automatic94=False,goal='active'))
files={p for folder in [D,O,QD,Q] for p in folder.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.npz','.png','.md','.log'}}
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_VIOLATION93_PLACEMENT_AUDIT_20261031'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='All11566262 retained full93 rows, independent six-column causal potential reconstruction; full8353 terminal binding; nine disposable critic ablations, fixed256 updates, full original state invariance, saved arithmetic and actual plot. Full555180960-byte sidecars remain shared SSD with verified hashes. No promotion or online change.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for p in tar.getmembers():assert tar.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],large_storage=raw,backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
footer=f"""

## 来源、GPU与保存

实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。本轮实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，首次TLS fetch失败后重试恢复并重读，应用仓库sii-research-sync。审计源码 `{D}`、消融源码 `{QD}`；产物 `{O}`、`{Q}`，各自PLAN/SOURCE_LOCK/LAUNCH及逐输入hash绑定预算、解释器、设备、checkpoint与真实源。全部9进程结束，正式完整93仍为科学父，没有新在线checkpoint。

原GPU guard继续，科学结束不退出；本次保存窗口{gpu['samples']}样本/{gpu['elapsed_s']:.3f}秒，最低{gpu['minimum']}%、低于50{gpu['below50']}、末值{gpu['last']}%。含synthetic guard，不等于科学训练吞吐或每瞬时保证，不是重启服务。

SSD `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，全部成员字节/AST核验。全行sidecar总555180960字节仅SSD、逐hash核验见LARGE_STORAGE_REVIEW；它们不进Git证据包。manifest `docs/evidence/{TAG}/MANIFEST.json`，提交字节及实际push核验收据 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，仅原LATEST254字节原地更新回读，非HDD/arm1完整备份。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
"""
(R/'docs'/(TAG+'.md')).write_text((D/'REPORT_BODY.md').read_text()+footer)
entry=(D/'ENTRY.md').read_text()+f'''\n- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read，实际发布见收据。\n\n'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu)))
