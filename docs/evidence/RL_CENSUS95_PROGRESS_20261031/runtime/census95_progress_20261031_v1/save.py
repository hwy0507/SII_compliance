from pathlib import Path
import json,hashlib,time,socket,os,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle95_20261031_v1';T=B/'runs/census95_fixed94_terminal_20261031_v1';TAG='RL_CENSUS95_PROGRESS_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
for p in [D/'OBSERVATION_REVIEW.json']:assert rd(p)['passed']
ob=rd(D/'OBSERVATION_REVIEW.json')
W=B/'runs/parameter_census94_96_reward_stability_20261031_v1'
for n,h in rd(W/'SOURCE_LOCK.json')['files'].items():assert sha(W/n)==h
C=B/'runtime/census95_comparison_20261031_v1'
for n,h in rd(C/'WAIT_PLAN.json')['source_hashes'].items():assert sha(C/n)==h
for j in ob['identities']:live(j)
waiter=rd(T/'LAUNCH.json');live(waiter)
assert not list(RUN.rglob('*FAILURE.json')) and not list(T.glob('*FAILURE*')) and not list(D.glob('*FAILURE*'))
progress={m:rd(RUN/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
for m in progress:assert progress[m]['steps']>=ob['last']['steps'][m]
cg=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');G=Path(cg['root']);assert not (G/'STOP').exists();rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress=progress,live_identities=ob['identities'],terminal_waiter=waiter,comparison_waiter=rd(C/'PROCESS.json'),formal95_running=True,complete95=False,automatic96=False,goal='active'))
files={p for p in D.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.md','.npz','.png','.diff'}};files.add(B/'runtime/census95_window_inputs_20261031_v1/COMPLETE94_BINDING_REVIEW.json')
files.add(C/'PROCESS.json');files.add(T/'LAUNCH.json')
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_CENSUS95_WINDOW_INPUTS_20261031'/n)
files.add(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');files.add(B/'runtime/census95_continuation_20261031_v1/NEXT_REVIEW_NOTES.md')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Bounded600s verified wait: original101 identities and actual95 training growth. Prior94 binding and scientific conclusions unchanged, complete95 pending, no new training or analysis dispatch, no convergence. Large checkpoints/journals remain sharedSSD, not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for p in t.getmembers():assert t.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD small evidence;254-byte HDD pointer only;large95 checkpoints/raw stay SSD,not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)

growth={m:ob['last']['steps'][m]-ob['first']['steps'][m] for m in progress}
entry=f'''## 2026-10-31 — 第95轮原作业持续：十分钟verified wait

- [交接](docs/{TAG}.md)。原101身份连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，三路steps增长{growth}；保存steps{ {m:x['steps'] for m,x in progress.items()} }，完成条件{ {m:x['completed_conditions'] for m,x in progress.items()} }。原三训练/90sampler/archive、固定8443终端和全90比较等待继续，无重启或新训练/消费者。
- 完整95/健康稳定/真实终端增长和两项比较仍待；完整94三组输入已审不等于94–96全九组绑定，原窗口和全部历史失败保持。没有自动96/Direct34；Direct原数值/冻结0/0及指定ESN缺失保持，Goal active，未收敛。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read，发布见收据。

'''
report=f'''# 第95轮十分钟实际进度观察

本轮为verified wait：当前原第95轮仍运行，先逐PID/start确认101个身份真实存活，随后有限观察600秒，未重启训练或重复派发分析。Goal active，未收敛。

实际主机 `{socket.gethostname()}`、共享SSD `{B}`、解释器 `{B}/env/bin/python`。实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`；仓库sii-research-sync流程及非RL并行工作保持。

## 实际进展

原101身份连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，三方法新增{growth}；保存steps{ {m:x['steps'] for m,x in progress.items()} }，已完成条件{ {m:x['completed_conditions'] for m,x in progress.items()} }。全部三训练、90sampler、archive、原固定8443终端/全90比较两个等待器、5个GPU守护身份均核对；未发现新DRIVER/训练/archive/终端或比较失败。观察源与计划、逐次steps及最终保存快照位于 `{D}`。

原正式运行 `{RUN}`，完整归档与review仍待。原固定终端 `{T}`、全条件比较 `{C}` 两个唯一消费者仍在原截止内等待。输入组完整性核验已完成的94不能替代完整95/96；原94–96窗口5%/nearzero1/5000bootstrap/seed2026102861保持。

## 接续路径

等原完整95 FINISHED/review/health/loss和两个消费者结束后，实际查看原loss/health及比较图，核验保存算术；运行 `{C}/check_terminal_population.py --complete` 检查全部95日志和回放done、旧8443终端indices/masks及新30终端/方法。前5000没有新终端不能代替增长证明，在线逐分层tensor没有日志。

依据完整95再决定有限96，没有自动96或Direct34。96可容纳4m，97须单独容量决策，不覆盖旧回放。完整94三组映射在census95_window_inputs目录，最终统计仍须原binder检查全部三轮九组真实输入。

现有I原loss尖峰/actor漂移、A94 short0200丢失成功、原90–92失败和全部历史退化保持。Direct33数值验收与冻结Task/Strict0/0、旧28证据限制及指定ESN缺失保持。若意外中断，保存最新95 partial learner/Adam/RNG/replay/journal并另登记census-aware恢复，不回退94重跑95；MuJoCo物理state未保存。

## GPU及保存

守护 `{G}` 持续运行，科学结束仍保留，不创建STOP，不是主机重启服务。此窗口{gpu['samples']}样本/{gpu['elapsed_s']:.3f}s，最低{gpu['minimum']}%、低于50{gpu['below50']}、末值{gpu['last']}%；含synthetic负载，与实际训练吞吐分列，不声明每瞬时下限或掩盖旧主机切换0%。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐成员字节/AST/JSON通过。发布收据 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD LATEST原地保持254字节，仅交接指针，大checkpoint/raw/replay继续共享SSD，非HDD/arm1全备份。
'''
(R/'docs'/(TAG+'.md')).write_text(report)
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:x['steps'] for m,x in progress.items()})))
