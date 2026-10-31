from pathlib import Path
import json,hashlib,time,socket,os,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle94_20261031_v1';T=B/'runs/census94_fixed93_terminal_20261031_v1';TAG='RL_CENSUS94_COMPARISON_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
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
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress=progress,live_identities=ob['identities'],terminal_waiter=waiter,comparison_waiter=rd(D/'PROCESS.json'),formal94_running=True,complete94=False,automatic95=False,goal='active'))
files={p for p in D.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.md','.npz','.png','.diff'}};files.update(p for p in T.glob('*.json'))
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_CENSUS94_PREFIX_20261031'/n)
files.add(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');files.add(B/'runtime/census94_online_20261031_v1/NEXT_REVIEW_NOTES.md')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='All90 full93-to94 descriptive comparison prepared with all90 actual93 raw summaries; fixed prefix population vs journal verified,15 corruptions rejected, actual online growth pending;600s101-identity training progress. No full94 result, no new scientific training, no convergence. Large checkpoints/journals remain sharedSSD, not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for p in t.getmembers():assert t.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD small evidence;254-byte HDD pointer only;large94 checkpoints/raw stay SSD,not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)

comparison=rd(D/'PROCESS.json');growth={m:ob['last']['steps'][m]-ob['first']['steps'][m] for m in progress}
entry=f"""## 2026-10-31 — 第94轮继续；93→94全90比较与终端增长审查准备

- [交接](docs/{TAG}.md)。全90训练条件reward分项/Task/Strict/abort/原抽样loss及变化rollout比较已登记，真实完整93全90摘要/模型/标签/reward算术和缺完整94拒绝通过；唯一等待器{comparison['pid']}沿原archive截止。条件估计loss单列，跨估计器轮次描述对比不替代94–96稳定窗口。
- 真实first5000每步terminal_population与done累计精确，15损坏输入拒绝；此前缀无新终端，真实增长仍待。完整94全回放dones/全部日志检查脚本已准备，需完成后运行；未提前声称增长或收敛。
- 原101身份连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，steps增长{growth}，总steps{ {m:x['steps'] for m,x in progress.items()} }；三训练/archive/固定8353终端与全90比较等待继续，无重启、自动95/Direct34。全部历史失败/Direct原验收/指定ESN缺失不变，Goal active。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read，发布见收据。

"""
report=f"""# 第94轮全条件比较与终端缓存增长审查准备

原第94轮三路在线训练继续，仍未收敛。本轮没有改训练源码或重启作业。实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`；开工query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，无新RL更新。继续仓库sii-research-sync流程，非RL工作保持。

## 全90条件93→94描述比较

源码 `{D}`，COMPARISON_PLAN/WAIT_PLAN绑定真实完整93 review/health/loss/实际图、三份94注册与STABILITY_WINDOW_INTENT。完整93原90 rollout标签/模型hash/冻结条件/逐回合reward分项/全部均值和Task/Strict计数已经复核；完整93 Task/Strict为I17/16、A15/14、V17/16。对真实缺少完整94输入的前置拒绝通过，脚本AST和差异已核验。

唯一等待器PID{comparison['pid']}/start{comparison['start']}，原archive截止{comparison['deadline']}；CPU10，每脚本最多600s。完整94归档、回放/health/loss审查结束后，interpret94.py比较全部3×30 reward/分项/Task/Strict/abort/原始抽样loss，changed_cases.py绑定所有Task/Strict变化的两轮rollout摘要、穿透及同一model hash；保存结果独立重算汇总，图须后续实际查看。

94的agent_train/q_loss为条件估计器，原健康口径使用original_sampled_q_loss，93则为其原q_loss，条件估计另列。actor两轮也分别列出。注册比较只允许新增census amendment与单轮接续字段，其余科学协议必须相同；新amendment精确绑定。本消费者无physics/optimizer更新，不改变正式权重，不把两轮描述差当因果改善或首次94–96稳定性证明。**完整94结果尚无**。

## 终端缓存总数对齐

check_terminal_population.py绑定全部旧93终端indices/masks和94注册。原trainer先replay.add/cache.sync再同step update；检查每个更新的terminal_population必须等于旧终端数加包含本步的done累计。first5000三路实际日志逐字回读精确，旧总数2785/2784/2784，新增done均0；15个缺更新/错步/错总数/遗漏终端增长/错父总数损坏输入被拒绝。

完整94后需要运行 `{B}/env/bin/python {D}/check_terminal_population.py --complete`。它要求完整review/checkpoint，严格census-aware元数据校验，全94日志和回放done精确，旧终端indices/masks保持、每方法30终端条件均覆盖、逐步总数匹配，并报告存档32个mask分层总数。**前缀无新终端，不证明真实增长；在线每分层tensor内容未日志化，不能把存档派生分层计数称作在线逐分层观察。**完整检查尚未运行，不改原archive消费者。

## 当前训练与续接

原101身份连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，三路增长{growth}；保存总steps{ {m:x['steps'] for m,x in progress.items()} }，完成条件{ {m:x['completed_conditions'] for m,x in progress.items()} }。原三正式/90sampler/archive、固定全部8353终端等待器{waiter['pid']}与本轮全90等待器继续。下一步等待完整94，再完成所有实际图/保存算术/真实缓存增长/两种比较，依据结果单独决定95；无自动95或Direct34。

固定94–96统计意向5%/nearzero1/5000bootstrap/seed2026102861保持，登记在94已启动、首完整回合返回前；实际统计输入绑定仍待，95/96仍需各自有限科学审查登记。历史90–92失败、92→93不稳定、I93后续终端退化和所有旧失败保持，原前5000 I16.365尖峰/actor上移不消失。Direct33原数值验收、冻结0/0与旧28证据限制、指定ESN缺失保持；Goal active。

若中断，保全最新94 partial检查点/Adam/RNG/replay/journal，另登记census-aware partial恢复；不回退93或重跑整轮94，物理state未保存。NEXT_REVIEW_NOTES明确后续命令与原作业身份。

## GPU和交接

独立guard `{G}` 保留，科学结束继续，不创建STOP，不是系统重启服务。当前窗口{gpu['samples']}样本/{gpu['elapsed_s']:.3f}s，最低{gpu['minimum']}%、低于50{gpu['below50']}，末值{gpu['last']}%；含synthetic guard，不等于科学吞吐或每瞬时保证，旧主机切换0%不抹除。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐成员字节及AST/JSON核验；原始.diff上下文空格保留。提交字节/实际远端收据 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满仅原LATEST254字节原地更新，大checkpoint/replay/raw仍共享SSD，不是HDD/arm1全备份。
"""
(R/'docs'/(TAG+'.md')).write_text(report)
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:x['steps'] for m,x in progress.items()})))
