from pathlib import Path
import json,hashlib,time,socket,os,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle94_20261031_v1';TAG='RL_CENSUS94_ONLINE_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
for p in [D/'PREFLIGHT_FINISHED.json',D/'CONTRACT_REVIEW.json',D/'CPU_CONSUMER_REVIEW.json',D/'SOURCE_REVIEW.json',D/'ONLINE_OBSERVATION_REVIEW.json',RUN/'startup/REVIEW.json']:assert rd(p)['passed']
for n,h in rd(D/'SOURCES.json')['files'].items():assert sha(D/n)==h
ob=rd(D/'ONLINE_OBSERVATION_REVIEW.json')
for j in ob['identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start']
assert not list(RUN.rglob('*FAILURE.json')) and not list(D.glob('*FAILURE.json'))
progress={m:rd(RUN/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
for m in progress:assert progress[m]['steps']>=ob['last_steps'][m]
cg=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');G=Path(cg['root']);assert not (G/'STOP').exists();rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress=progress,live_identities=ob['identities'],formal94_running=True,complete94=False,automatic95=False,goal='active'))
files={p for p in D.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.md','.log','.diff'}}
files.update(RUN.glob('*.json'));files.add(RUN/'startup/REVIEW.json');files.add(RUN/'startup.log')
for m in progress:
 for n in ['REGISTRATION.json','CHECK_ONLY_REVIEW.json','INITIAL_STATE_REVIEW.json','CENSUS_EXECUTION.json','check/INITIAL_STATE_REVIEW.json','train/EXECUTION.json']:files.add(RUN/m/n)
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_CENSUS93_NATIVE_COMPATIBILITY_20261031'/n)
files.add(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Finite online94 launch: exact93 migration/99 negative guards/6 native clone updates/CPU consumer/startup real data audit/120s99-identity progress. Training and archive remain live; full94 and convergence pending. Large current checkpoints, startup snapshots, all journals remain shared SSD; not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for p in t.getmembers():assert t.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD small evidence; existing254-byte HDD pointer only, not full HDD/arm1 backup; live94 checkpoints/raw remain SSD');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
footer=f'''

## 来源、GPU与交接保存

实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。本轮实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，继续应用仓库sii-research-sync。原生启动源码 `{D}`，在线目录 `{RUN}`，预计完整归档 `{B}/runs/parameter_census_cycle94_archive_20261031_v1` 尚待原archive进程完成，不提前称已归档。源码/注册/审查与原父来源hash见SCIENTIFIC_DECISION、SOURCES、各REGISTRATION及证据manifest。

独立GPU guard继续，科研结束不退出；保存窗口{gpu['samples']}样本/{gpu['elapsed_s']:.3f}秒，最低{gpu['minimum']}%、低于50{gpu['below50']}、末值{gpu['last']}%。含synthetic guard，不等于科学吞吐或每瞬时保证。旧主机切换时0%记录仍保留，guard不是系统重启服务。

保存瞬间总steps `{ {m:x['steps'] for m,x in progress.items()} }`，三正式与archive及90sampler继续。静态小证据包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`；逐成员字节/AST核验，源diff原件保留。提交字节与实际远端核验收据 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。全部大型checkpoint/replay/raw仅共享SSD，HDD配额满仅原LATEST254字节原地更新回读，非HDD/arm1完整备份。
'''
(R/'docs'/(TAG+'.md')).write_text((D/'REPORT_BODY.md').read_text()+footer)
entry=(D/'ENTRY.md').read_text()+f"\n- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read，实际发布见收据。\n\n"
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:x['steps'] for m,x in progress.items()})))
