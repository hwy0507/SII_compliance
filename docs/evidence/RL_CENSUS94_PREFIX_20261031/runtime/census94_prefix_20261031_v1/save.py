from pathlib import Path
import json,hashlib,time,socket,os,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle94_20261031_v1';T=B/'runs/census94_fixed93_terminal_20261031_v1';TAG='RL_CENSUS94_PREFIX_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
for p in [D/'prefix5000/REVIEW.json',D/'ONLINE_OBSERVATION_REVIEW.json',T/'PREFLIGHT_REVIEW.json',T/'PARTIAL_REJECTION_REVIEW.json']:assert rd(p)['passed']
assert rd(D/'PLOT_INSPECTION.json')['actually_viewed'];ob=rd(D/'ONLINE_OBSERVATION_REVIEW.json')
for j in ob['identities']:live(j)
waiter=rd(T/'LAUNCH.json');live(waiter)
assert not list(RUN.rglob('*FAILURE.json')) and not list(T.glob('*FAILURE*')) and not list(D.glob('*FAILURE*'))
progress={m:rd(RUN/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
for m in progress:assert progress[m]['steps']>=ob['last_steps'][m]
cg=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');G=Path(cg['root']);assert not (G/'STOP').exists();rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress=progress,live_identities=ob['identities'],terminal_waiter=waiter,formal94_running=True,complete94=False,automatic95=False,goal='active'))
files={p for p in D.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.md','.npz','.png'}};files.update(p for p in T.glob('*.json'))
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_CENSUS94_ONLINE_20261031'/n)
files.add(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');files.add(B/'runtime/census94_online_20261031_v1/NEXT_REVIEW_NOTES.md')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Fixed first5000 original/conditional/actor loss and actual plot;180s99-identity progress; all8353 fixed93 terminal comparison prepared/preflighted with actual partial94 rejection and one finite wait. No full94 result, no new scientific training, no convergence. Large checkpoints/journals remain sharedSSD, not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for p in t.getmembers():assert t.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD small evidence;254-byte HDD pointer only;large94 checkpoints/raw stay SSD,not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
pr=rd(D/'prefix5000/REVIEW.json');table='| 方法 | 原抽样首1000均值 | 原抽样末1000均值 | 原抽样最大 | 条件估计最大 | actor首→末1000 |\n|---|---:|---:|---:|---:|---:|\n'
for m,v in pr['methods'].items():
 s=v['stats'];q=s['agent_train/original_sampled_q_loss'];c=s['agent_train/conditional_terminal_q_loss'];ac=s['agent_train/actor_loss'];table+=f"| {m} | {q['first1000']:.9f} | {q['last1000']:.9f} | {q['maximum']:.9f} | {c['maximum']:.9f} | {ac['first1000']:.6f}→{ac['last1000']:.6f} |\n"
entry=f'''## 2026-10-31 — 第94轮前5000已审；固定93全部终端比较等待

- [交接](docs/{TAG}.md)。固定first5000原始字节/全部metrics/保存算术/实际九栏图通过；原抽样loss最大I16.365/A1.537/V1.152，I尖峰与actor上移仍保留。新q_loss是条件估计，不替代原抽样健康口径；前缀无新terminal，完整94/真实cache增长和收敛均待。
- 全8353固定93终端/all5/原masks比较准备完成，使用initial_prediction不使用隔离拟合结果；全来源/算术及三实际partial94拒绝通过。唯一只读等待器{waiter['pid']}沿原archive截止，完整94后strict census恢复，0update/physics，无自动95/Direct34。原99身份{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，steps增长{ {m:ob['last_steps'][m]-ob['first_steps'][m] for m in progress} }。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read。全部历史失败/Direct原验收/指定ESN缺失保留；Goal active，无子agent。

'''
report=f'''# 第94轮固定前缀与完整93终端跟踪准备

第94轮原三路正式训练和归档进程继续，没有重启或改写训练。尚未收敛。实际主机 `{socket.gethostname()}`；共享SSD `{B}`，解释器 `{B}/env/bin/python`。开工实际查询、fetch并读取main `{remote['main']}` 与baseline `{remote['baseline']}`；远端无新RL变更，非RLfinal108仍0/108，不启动非RL作业。

## 固定前5000更新

沿上轮NEXT_REVIEW_NOTES规定恰取前5000，不选最优片段；三路原日志前缀逐字回读，步号连续/update_index0，所有指标有限，保存NPZ逐字段精确及math.fsum/NumPy均值一致。实际查看九栏图见 `{D}/PLOT_INSPECTION.json`。

{table}

I原抽样尖峰密集但幅度逐渐缩小，16.365尖峰保留；条件估计更平滑不证明原异常解决，actor上移仍在。A/V仅此前缀较平，没有完整周期reward或稳定证据。agent_train/q_loss=conditional_terminal_q_loss；原健康比较始终使用original_sampled_q_loss。此前缀terminal_population仍2785/2784/2784，不能证明实际新terminal缓存增长。

## 固定完整93终端的94跟踪

登记 `{T}/PLAN.json`，源码 `{D}/terminal94.py`、`wait_terminal94.py`，来源/28运行源码hash、父完整93checkpoint identity和原注册锁定。固定8353条（2785/2784/2784），使用 `{B}/runs/violation93_potential_ablation_20261031_v1/*_values.npz` 的 **initial_prediction**。全部五critic/原masks/all-row、old≤92/new93、原79/90/92中止与93放置失败大误差行保留；保存全部逐行预测并报告退化和最大20行。无辅助权重推广、不增加物理或optimizer更新。

实际baseline来源/全8353算术预检通过；三实际startup94 checkpoint可通过架构校验且拒绝complete=True，沿用已通过99负例和CPU严格恢复。唯一等待器PID{waiter['pid']}/start{waiter['start']}等待原archive完整94/全部review FINISHED，再用原driver.restore_consumer严格CPU恢复完整learner/Adam/RNG；前后digest不变，所有保存预测独立标量复算。已启动等待，但**尚无完整94终端结果**，未来输出图仍需实际查看，准备检查不冒充完成科学结果。

## 当前运行与继续事项

原99身份连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本稳定，保存总steps `{ {m:x['steps'] for m,x in progress.items()} }`，完成条件 `{ {m:x['completed_conditions'] for m,x in progress.items()} }`；三训练/90sampler/archive继续。完整94、真实新增terminal缓存与全部回放对应、全loss实际图与独立算术、93→94全90条件reward/Task/Strict/abort/标签比较仍待。首次census窗口94–96沿已登记意向，明确为94启动后完整回合返回前登记，统计绑定仍待；95/96需分别审查登记，无自动队列。

中断先保全最新94 partial权重/Adam/RNG/replay/journal，另登记census-aware恢复；不回退完整93、不重跑整轮94；MuJoCo物理state未保存。全部历史失败、Direct33原数值验收与冻结0/0、旧28不完整不变性证据及指定ESN缺失保持；最终冻结独立评估仍待，Goal active。

## GPU与保存

按用户新要求，科研全部结束后也保留独立guard；保活root `{G}`，身份见CURRENT_GUARD，不创建STOP，不是系统重启服务。窗口{gpu['samples']}样本/{gpu['elapsed_s']:.3f}s，最低{gpu['minimum']}%、低于50{gpu['below50']}、末值{gpu['last']}%；含synthetic guard，不等于科学吞吐或每瞬时保证，原主机切换0%记录保留。

小证据包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐成员和AST/JSON已核验；提交字节与发布收据 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，只原地更新254字节LATEST指针；大checkpoint/replay/raw仅共享SSD，非HDD/arm1完整备份。
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
