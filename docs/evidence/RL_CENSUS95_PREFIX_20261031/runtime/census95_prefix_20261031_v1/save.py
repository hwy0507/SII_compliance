from pathlib import Path
import json,hashlib,time,socket,os,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle95_20261031_v1';T=B/'runs/census95_fixed94_terminal_20261031_v1';TAG='RL_CENSUS95_PREFIX_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
for p in [T/'reference94/REVIEW.json',D/'prefix5000/REVIEW.json',D/'ONLINE_OBSERVATION_REVIEW.json',T/'PREFLIGHT_REVIEW.json',T/'PARTIAL_REJECTION_REVIEW.json']:assert rd(p)['passed']
assert rd(D/'PLOT_INSPECTION.json')['actually_viewed'];ob=rd(D/'ONLINE_OBSERVATION_REVIEW.json')
for j in ob['identities']:live(j)
waiter=rd(T/'LAUNCH.json');live(waiter)
assert not list(RUN.rglob('*FAILURE.json')) and not list(T.glob('*FAILURE*')) and not list(D.glob('*FAILURE*'))
progress={m:rd(RUN/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
for m in progress:assert progress[m]['steps']>=ob['last_steps'][m]
cg=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');G=Path(cg['root']);assert not (G/'STOP').exists();rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress=progress,live_identities=ob['identities'],terminal_waiter=waiter,formal95_running=True,complete95=False,automatic96=False,goal='active'))
files={p for p in D.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.md','.npz','.png'}};files.update(p for p in T.rglob('*') if p.is_file() and p.suffix in {'.json','.npz'})
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_CENSUS95_ONLINE_20261031'/n)
files.add(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');files.add(B/'runtime/census95_continuation_20261031_v1/NEXT_REVIEW_NOTES.md')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Fixed first5000 original/conditional/actor loss and actual plot;180s99-identity progress; all8443 fixed94 terminal comparison prepared/preflighted with actual partial95 rejection and one finite wait. No full95 result, no new scientific training, no convergence. Large checkpoints/journals remain sharedSSD, not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for p in t.getmembers():assert t.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD small evidence;254-byte HDD pointer only;large95 checkpoints/raw stay SSD,not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
pr=rd(D/'prefix5000/REVIEW.json');table='| 方法 | 原loss首1000 | 原loss末1000 | 原loss最大 | 条件估计最大 | actor首→末1000 |\n|---|---:|---:|---:|---:|---:|\n'
for m,v in pr['methods'].items():
 s=v['stats'];q=s['agent_train/original_sampled_q_loss'];c=s['agent_train/conditional_terminal_q_loss'];ac=s['agent_train/actor_loss'];table+=f"| {m} | {q['first1000']:.9f} | {q['last1000']:.9f} | {q['maximum']:.9f} | {c['maximum']:.9f} | {ac['first1000']:.6f}→{ac['last1000']:.6f} |\n"
growth={m:ob['last_steps'][m]-ob['first_steps'][m] for m in progress}
entry=f"""## 2026-10-31 — 第95轮前5000已审；全8443固定94终端参考与比较等待

- [交接](docs/{TAG}.md)。固定first5000原始字节/全部metrics/保存算术/实际九栏图通过；原loss最大I3.434/A1.521/V1.133，I反复尖峰和actor上移保持，条件估计平滑不替代原loss健康，前缀没有新terminal，完整95与收敛待。
- 全8443终端完整94 CPU参考完成，全部旧8353预测与保存full94逐值一致、新90终端与原transition/episode绑定；全learner/Adam/replay/RNG不变、保存标量算术通过。全5/original masks/old≤93/new94及原79/90/92中止和93尖峰均纳入，不是95结果或独立泛化。
- 原三实际partial95拒绝完整检查，唯一等待器{waiter['pid']}沿原archive截止等待完整95后比较；无自动96/Direct34。原99身份{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，steps增长{growth}，三训练/archive继续。全部历史失败、Direct原验收/冻结0/0及指定ESN缺失保持，Goal active。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针，非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read，发布见收据。

"""
report=f"""# 第95轮前缀审查与全部94终端比较准备

第95轮原三路训练、90sampler和归档器继续运行；本轮零新增科学训练派发、零物理或optimizer诊断更新，Goal active，尚未收敛。实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。开工实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，沿sii-research-sync保存，不改并行非RL任务。

## 固定first5000原始loss

在读取95 loss数值前锁定各方法前5000；原日志前缀逐字复制并回读一致、step连续/update_index0、所有metrics有限。保存NPZ所有字段精确，独立math.fsum首末1000/均值/极值与NumPy复算通过。原抽样、条件估计、actor三列实际九栏图已查看，收据 `{D}/PLOT_INSPECTION.json`。

{table}

I原loss均值约1.061、曲线均值较平，但反复2–2.5尖峰及3.434最大值仍在；条件最大1.683不替代原loss健康。I actor持续上移27.089→27.252；A/V此前缀原loss较平、actor小幅上移。没有完整95 episode reward或整轮健康证据。原q_loss等于conditional_terminal_q_loss；健康仍使用original_sampled_q_loss。first5000 terminal_population固定2815/2814/2814，未见新terminal，不当作实际新增cache验证。完整94原loss/actor及所有历史失败保持。

## 完整94全部终端参考

先登记 `{T}/REFERENCE_PLAN.json`，固定完整94的全部8443条terminal（I2815/A2814/V2814），CPU11、1200秒有限预算、零optimizer/physics、全部五critic/原masks。从准确完整94 checkpoint严格census-aware恢复，完整learner/Adam/replay/RNG前后digest不变、无梯度，checkpoint前后hash一致。

旧8353条输入/动作/reward/masks与先前固定93终端数据精确，重新forward的full94预测与先前保存的complete94逐元素相等；新90条从94 replay全部剩余done索引取出，与原94 terminal transition的step/condition/reward和全30 episode标签/长度对应，未删行或选低误差样本。旧历史cycle/condition来源保留；新94标签由真实完整94记录绑定。新reference_npz包含全部indices/obs52/actions/rewards/masks/cycles/conditions/initial_prediction，回读逐值及独立标量SSE核验通过。

CPU计算按每方法旧93块与新94块分别forward，后续95消费者使用同样块大小。原known79/90/92安全中止与93放置失败spike3851694都保留；这是已见训练终端参考，不是独立泛化或新的95误差结果。未生成、保存或推广任何辅助拟合权重。参考 `{T}/reference94`。

## 完整95比较准备与拒绝保护

`{T}/PLAN.json` 绑定参考全部hash、95协议、完整94审查和29份95运行源码；消费者 `{D}/terminal95.py`、`wait_terminal95.py`。未来只接受完整95及原全review/health/loss FINISHED，严格加载全state并检验全部保留94 terminal索引/字段；输出全部五critic masked/all-row SSE、≤93旧组/新94组、已知失败、所有逐行预测及退化计数/最大20行。保存结果再独立标量复算；最终图必须实际查看。

完整baseline算术预检通过，缺完整95拒绝；三实际startup95快照通过版本校验、complete=True分别拒绝，未把partial当完成。沿用原111损坏协议/父状态拒绝及三CPU消费者证据，本轮未重复隔离更新。唯一等待器PID{waiter['pid']}/start{waiter['start']}，截止沿原archive启动+14400秒，完成后分析预算1200秒，无自动96或Direct34。**完整95终端比较尚未运行，不能把准备通过当作95改善。**

## 继续与恢复

原99身份连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，steps增长{growth}；保存总steps{ {m:x['steps'] for m,x in progress.items()} }。完整95、全部新terminal缓存/回放对应、全loss实际图/独立算术及94→95全90条件比较待完成。固定94–96/5%/nearzero1/5000bootstrap/seed2026102861保持；意向原登记于94启动后首完整回合返回前，95/96需独立有限决定，不自动队列。原90–92失败、94尖峰/actor漂移、A short0200回归与unmasked退化均保持，不因前缀较平改写结论。

原physics/MJB/Task/Strict/canonical48/filter/actuator/dt5e−5、actor49/critic52、clock/history/rawbit、原LR/reward/masks/terminal128/batch65536/UTD1、census源码/marker与4m append-only/23和47标记未改。中断保全最新95 partial权重/Adam/RNG/replay/journals，另登记census-aware恢复，不回退94或重跑整轮95；MuJoCo物理state未保存。Direct33原数值验收/冻结全30 TaskStrict0/0、旧28memory invariance限制/恢复2证明、指定ESN缺失保持，最终独立对比未完成。

## GPU与保存

独立guard `{G}` 保持，科学全部结束仍运行，不创建STOP，非系统重启服务。窗口{gpu['samples']}样本/{gpu['elapsed_s']:.3f}s，最低{gpu['minimum']}%、低于50{gpu['below50']}、末值{gpu['last']}%；含synthetic guard，不等于科学吞吐或每瞬时保证，旧主机切换0%记录保留。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，全部tar成员/源码AST/JSON核验。含完整first5000原始指标/保存数组/图和全部8443参考数组，全部原checkpoint/raw仅共享SSD；HDD配额满，仅254字节LATEST原地更新，非HDD/arm1全备份。Git字节与实际远端发布收据 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。
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
