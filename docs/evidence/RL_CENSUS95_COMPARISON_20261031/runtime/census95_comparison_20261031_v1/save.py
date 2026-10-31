from pathlib import Path
import json,hashlib,time,socket,os,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle95_20261031_v1';T=B/'runs/census95_fixed94_terminal_20261031_v1';TAG='RL_CENSUS95_COMPARISON_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
for p in [D/'COMPARISON_PREFLIGHT.json',D/'PRIOR90_REVIEW.json',D/'CACHE_POPULATION_PREFIX_REVIEW.json',D/'CACHE_POPULATION_NEGATIVE_REVIEW.json',D/'SOURCE_ORDER_REVIEW.json',D/'OBSERVATION_REVIEW.json']:assert rd(p)['passed']
ob=rd(D/'OBSERVATION_REVIEW.json')
for p,h in rd(D/'COMPARISON_PLAN.json')['prior_inputs'].items():assert sha(p)==h
for n,h in rd(D/'WAIT_PLAN.json')['source_hashes'].items():assert sha(D/n)==h
for j in ob['identities']:live(j)
waiter=rd(T/'LAUNCH.json');live(waiter)
assert not list(RUN.rglob('*FAILURE.json')) and not list(T.glob('*FAILURE*')) and not list(D.glob('*FAILURE*'))
progress={m:rd(RUN/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
for m in progress:assert progress[m]['steps']>=ob['last']['steps'][m]
cg=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');G=Path(cg['root']);assert not (G/'STOP').exists();rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress=progress,live_identities=ob['identities'],terminal_waiter=waiter,comparison_waiter=rd(D/'PROCESS.json'),formal95_running=True,complete95=False,automatic96=False,goal='active'))
files={p for p in D.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.md','.npz','.png','.diff'}};files.update(p for p in T.glob('*.json'))
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_CENSUS95_PREFIX_20261031'/n)
files.add(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');files.add(B/'runtime/census95_continuation_20261031_v1/NEXT_REVIEW_NOTES.md')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='All90 full94-to95 descriptive comparison prepared with all90 actual94 raw summaries; fixed prefix population vs journal verified,15 corruptions rejected, actual online growth pending;600s101-identity training progress. No full95 result, no new scientific training, no convergence. Large checkpoints/journals remain sharedSSD, not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for p in t.getmembers():assert t.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD small evidence;254-byte HDD pointer only;large95 checkpoints/raw stay SSD,not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)

comparison=rd(D/'PROCESS.json');growth={m:ob['last']['steps'][m]-ob['first']['steps'][m] for m in progress}
entry=f'''## 2026-10-31 — 第95轮继续；94→95全90比较与终端增长检查准备

- [交接](docs/{TAG}.md)。全90训练条件reward分项/Task/Strict/abort/原抽样loss及所有标签变化比较已登记，真实完整94全90模型/摘要/标签/算术与缺完整95拒绝通过；唯一等待器{comparison['pid']}沿原archive截止。两轮census amendment完全相同，原抽样健康loss两轮同口径；描述比较不替代固定94–96稳定窗口。
- 实际first5000每步terminal_population等于旧8443分路总数加done累计，15损坏输入拒绝；此前缀无新终端，真实增长仍待。完整95全日志/回放done与32分层存档计数检查准备，尚未运行；不声称在线分层tensor已观测。
- 原101身份连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，steps增长{growth}，保存总steps{ {m:x['steps'] for m,x in progress.items()} }；原三训练/archive/固定8443终端与全90比较等待继续。完整95、原loss健康与收敛待，无自动96/Direct34。全部历史失败、Direct原验收/冻结0/0及指定ESN缺失保持，Goal active。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read，发布见收据。

'''
report=f'''# 第95轮全条件比较与终端增长检查准备

第95轮三路原在线训练继续，Goal active，尚未收敛。主机 `{socket.gethostname()}`；共享SSD `{B}`；解释器 `{B}/env/bin/python`。开工实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，无新增RL变更，并行非RL工作保持。应用仓库sii-research-sync流程。

## 已完成的输入与前缀核验

`{D}` 保存COMPARISON_PLAN/WAIT_PLAN以及源码和diff。全部完整94的90条rollout成功标签、abort、stage、模型hash、冻结条件、reward分项和均值/Task/Strict总数已独立复核；完整94 Task/Strict为18/17、15/14、17/17。95协议和94只允许post_interruption_continuation字段变化，conditional_terminal_amendment精确相同；原抽样健康loss均读取agent_train/original_sampled_q_loss，条件估计另列，actor亦单列。缺少真实完整95时前置检查按预期拒绝，不伪造结果。

check_terminal_population.py绑定完整94的全部8443终端indices/masks，来自 `{T}/reference94`；分路2815/2814/2814。实际95 first5000每步terminal_population与父总数加包含本步的done累计相等，原日志字节回读精确，三路无新终端。15个缺更新/错步/错总数/漏增长/错父总数损坏输入被拒绝。check_source_order.py核验29个锁定运行源码及实际trainer，确认add/cache同步在同step更新之前。此前缀没有真实新终端，不能作为增长证明。

## 正在等待的完整95分析

唯一全90条件比较等待器PID{comparison['pid']}/start{comparison['start']}，沿原archive截止 `{comparison['deadline']}`，CPU10，每分析脚本600s上限。在原完整95 REVIEW/health/loss和FINISHED通过后，interpret95.py比较全部90个条件reward、分项、Task/Strict/abort及loss，changed_cases.py绑定所有标签变化的原两轮rollout、穿透和模型hash；保存汇总复算并产生图。实际图仍须查看。等待器的legacy输出键automatic95=False表示不派发训练；其源码没有任何95/96训练启动路径。两轮使用相同估计器，但此描述比较不是因果证明，也不替代固定94–96窗口。

原固定终端等待器PID{waiter['pid']}在 `{T}`，仍等待完整95；其基准是完整94全部8443条、all5/original masks，保留old≤93/new94与历史79/90/92中止及93失败尖峰。两类消费者只有推理/分析，没有优化更新或物理推进。完整95完成后还需运行：

```bash
{B}/env/bin/python {D}/check_terminal_population.py --complete
```

完整模式要求原FINISHED/review、严格完整95 checkpoint校验，全部新日志与全回放done精确，旧indices/masks保持，新30条件终端全部覆盖；报告存档32分层计数。在线逐分层tensor没有日志，不能把存档计数写成在线逐分层观察。**这些完整95结果尚未产生，完整模式尚未运行。**

## 实际持续训练与下一步

原101身份连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，三路新增{growth}；保存steps{ {m:x['steps'] for m,x in progress.items()} }，完成条件{ {m:x['completed_conditions'] for m,x in progress.items()} }。身份包含三learner、90sampler、原archive、两只读等待器与5个GPU守护进程。训练源码、学习率、reward、MJB、actor49/canonical48、critic/replay52和23/47容量标记保持，每方法本轮最多41250新transition。

下一步等待完整95归档，查看原loss/health和两类比较实际图，完成保存算术、全部新terminal增长与完整科学解释，再单独审查有限96。固定94–96统计5%/nearzero1/5000bootstrap/seed2026102861及原登记时序保持，尚无完整输入绑定或统计结果。96可容纳于4m回放；97需另行容量决策，不能覆盖回放。没有自动96或Direct34。

原95 first5000 I重复尖峰/actor上移保持；原94的A short0200成功丢失、原90–92失败及全部历史退化不因新程序抹除。Direct33原数值验收、冻结30例Task/Strict0/0、旧28证据限制和指定ESN缺失保持。数值收敛不能替代Task成功。若中断，保全最新95 partial的learner/Adam/RNG/replay/journal，另登记census-aware部分恢复，不回退94重跑95；MuJoCo物理状态未保存。

## GPU与持久交接

独立guard `{G}` 持续运行，科学完成后仍保留，不创建STOP；它不是系统重启服务。当前窗口{gpu['samples']}样本/{gpu['elapsed_s']:.3f}s，最低{gpu['minimum']}%、低于50{gpu['below50']}，末值{gpu['last']}%。占用包含synthetic guard，不等于科学吞吐，也不是每瞬时下限保证；旧主机切换0%历史保持。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐成员字节与AST/JSON核验。提交字节与实际远端核验另存 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，LATEST交接指针原地保持254字节，大checkpoint/replay/raw仍在共享SSD；这不是HDD/arm1完整备份。
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
