from pathlib import Path
import json,time,os,socket,hashlib,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];P=D;R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle92_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';N=B/'runs/violation92_fixed87_terminal_followup_20261030_v1';TAG='RL_VIOLATION92_DIAGNOSTICS_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
prefix=read(D/'prefix5000_v2/REVIEW.json');plots=read(D/'prefix5000_v2/PLOT_INSPECTION.json');assert prefix['passed'] and plots['actual_visual_inspection']
for x in plots['plots']:assert x['inspected'] and sha(x['path'])==x['sha256']
fix=read(D/'PREFIX_FAILURE_AND_FIX.json');assert sha(fix['replacement_source'])==fix['replacement_sha256'] and sha(fix['original_source'])==fix['original_sha256']
updated=read(N/'PREFLIGHT_REVIEW.json');observed=read(D/'OBSERVATION_REVIEW.json');assert updated['passed'] and observed['passed'] and read(N/'VALIDATOR_REVIEW.json')['passed']
assert not (N/'FINISHED.json').exists() and not list(N.glob('WAIT_FAILURE_*.json'))
for name,h in read(N/'PLAN.json')['source_hashes'].items():assert sha(D/name)==h
for j in observed['identities']:
 f=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert f[0]!='Z' and f[19]==j['start']
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not (D/'OBSERVATION_FAILURE.json').exists()
for m in updated['methods']:assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
progress={m:read(T/m/'train/PROGRESS.json') for m in updated['methods']};frozen={m:read(F/m/'PROGRESS.json') for m in updated['methods']};rows=[]
for line in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines():
 try:x=json.loads(line)
 except json.JSONDecodeError:continue
 if x['time']>=read(N/'PLAN.json')['time']:rows.append(x)
assert time.time()-rows[-1]['time']<25 and not Path('/tmp/sii_gpu_util_guard_20261030_v7/STOP').exists();(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress92=progress,frozen90=frozen,identities=observed['identities'],goal='active',fixed87_complete92_predictions=False,automatic93=False))
files=set()
for directory in [D,P,N]:
 for p in directory.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff','.png','.npz'} and p.stat().st_size<10_000_000:files.add(p)
for m in progress:
 for n in ['EXECUTION.json','PROGRESS.json']:files.add(T/m/'train'/n)
 for n in ['PROGRESS.json']:files.add(F/m/n)
for n in ['LAUNCH.json','MONITOR_LAUNCH.json']:files.add(T/n)
for n in ['LAUNCH.json','REVIEW_LAUNCH.json']:files.add(F/n)
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_VIOLATION92_ONLINE_20261030'/n)
files.add(B/'runs/violation91_fixed87_terminal_followup_20261030_v1/REVIEW.json')
files.add(B/'runs/violation91_fixed87_terminal_followup_20261030_v1/PLOT_INSPECTION.json')
files.add(B/'runtime/build_violation92_terminal_20261030.py')
files.add(B/'runs/parameter_violation90_92_reward_stability_20261030_v1/EARLY_WINDOW_FAILURE_91.json')
files.add(B/'runs/parameter_violation90_92_reward_stability_20261030_v1/PLAN.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Cycle92 fixed first5000 loss prefix with raw bytes, saved scalar verification and actual plot. Fixed87 all7813 terminals/all5/masks followup92 registered; saved87-91 arithmetic and52 raw inputs exact, actual partial92 rejects complete boundary. Full92 predictions pending; original92/frozen90/guard continue. Prefix v1 path failure preserved.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for item in tar.getmembers():assert tar.extractfile(item).read()==(E/item.name).read_bytes()
remote=read(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD; HDD existing254-byte pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
lossrows='\n'.join(f"| {m} | {x['stats']['agent_train/q_loss']['first1000']:.9f} → {x['stats']['agent_train/q_loss']['last1000']:.9f} | {x['stats']['agent_train/q_loss']['maximum']:.9f} | {x['stats']['agent_train/actor_loss']['first1000']:.9f} → {x['stats']['agent_train/actor_loss']['last1000']:.9f} |" for m,x in prefix['methods'].items())
text=f'''# 第92轮前5000 loss审查与固定87终端跟踪登记

2026-10-30 UTC，Goal active，未达到整体reward平稳及loss健康。原第92轮三路训练、唯一归档和原冻结90评测继续；本轮完成固定前5000更新审查，并登记完整92后固定旧终端诊断，没有额外训练周期/新物理派发，不自动93/Direct34。前序：[第92轮实际启动](RL_VIOLATION92_ONLINE_20261030.md)。

主机 `{socket.gethostname()}`；共享SSD根 `{B}`；解释器 `{B}/env/bin/python`。开工实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`；沿用 [sii-research-sync](../skills/sii-research-sync/SKILL.md)，无子agent。分析源码 `{D}`，终端诊断run `{N}`。原训练源码/版本/MJB/seed继续由 `{B}/runtime/violation92_continuation_20261030_v1`、`{T}/<method>/REGISTRATION.json` 与 `train/EXECUTION.json` 固定；本轮未变更依赖或训练器。

## 固定前5000 loss结果

在读取当前loss值之前沿用固定first5000方案；数据来自每方法optimizer.jsonl最前5000原始完整行，核验完整91真实父steps、连续步号、每步update_index0、所有指标有限及critic非负。保存原字节及NPZ，再用math.fsum独立复算每项首1000、末1000、全5000均值/极值，回读训练文件确认前缀未变。实际六栏图已查看，`prefix5000_v2/PLOT_INSPECTION.json` 固定图hash；原REVIEW内plot_viewed=false是检查前状态，不覆盖后续实际查看收据。

| 方法 | critic首1000→末1000 | critic最大值 | actor首1000→末1000 |
|---|---:|---:|---:|
{lossrows}

阻抗critic仍反复出现约12的密集尖峰，最大20.756，actor平滑均值持续上移；其critic前缀末段均值低于首段不能证明健康。导纳critic有较小尖峰和均值起伏，actor前段近似平坦。VMC约第2000次附近出现一组critic尖峰，最大4.629，actor略上移。全部尖峰和退化保留；这只是固定早期窗口，不能推断完整92 reward稳定、loss健康、任务成功或因果改善。

首版prefix92.py在脚本生成时因顺序文本替换把父91 review路径改成了尚未完成的92 review，读取父文件时FileNotFoundError退出1。失败发生在读取任何本轮loss值之前，仅生成空prefix5000目录。原源码、PREFIX_PLAN和空目录保留；PREFIX_FAILURE_AND_FIX记录原因/hash，prefix92_v2.py仅把两处父review路径改回91并使用独立prefix5000_v2输出，原first5000选择与数值方法不变。修复后完成上述核验，原训练未重启或受影响。

## 固定原87全部终端跟踪完整92

继续使用原87全部7813终端：I2605、A2604、V2604；all5 critic、原masks、全部先前87/88/89/90/91预测保持。源来自已完整审计的91跟踪NPZ，原masked SSE/MSE、all-row SSE和分母逐项复算精确，52维保存观测与原51特征和raw preaction>.0002m位重新逐位核验，不替换旧观测。各方法bit分布 `{ {m:x['bit_counts'] for m,x in updated['methods'].items()} }`。真实缺完整92入口已拒绝，当前0新增neural forward/physics/optimizer update。

专用validate_architecture92/validate_recovery92按准确完整91累计步数验证，父91又绑定真实90 steps+实际新增，保留90 I安全中止造成的非整轮行数。原history首次88、violation首次90、双marker、52维current/next、seed/controller/registration、4m cursor/size、continuation及partial75排除保持；原冻结90恢复模块不改。三份实际不可变startup92快照通过架构检查，均拒绝完整轮次边界；27项错误cycle/seed/protocol/controller/旧89步数/cursor/capacity/缺marker/next51测试全部拒绝。没有伪造未来完整92状态来证明恢复。

统计与input hash函数AST与原91相同；实际原生restore、all5 forward以及全learner/replay/RNG检查关键代码保持。新增第六个端点complete92，并保留全部五个旧端点；绘图仅为六组柱调整位置与宽度，数值统计不变。SOURCE_REVIEW和VALIDATOR_REVIEW分别记录源码与实际状态核验。旧91的check路径类型失败与修复保留在历史记录；本次使用已修复的Path读取。

唯一等待器PID `{read(N/'PROCESS.json')['pid']}`、start `{read(N/'PROCESS.json')['start']}`，绑定原92 archive463623；等待截止Unix `{read(N/'PLAN.json')['wait_deadline_unix']}`，即原92 launch+14400s，没有延长原预算。完整92的REVIEW、FINISHED、health、loss全部到齐且checkpoint hash一致后，才读取 `{B}/runs/parameter_violation_cycle92_archive_20261030_v1/<method>/cycle_00092.pt`，计算同一批终端all5预测并检查全state/RNG/checkpoint不变。分析预算1800秒；实际图查看另行完成。当前没有92完整终端预测结果。

这是已见旧终端拟合与保留诊断，不是安全、策略性能、泛化或收敛门槛。完整91 masked SSE相对90 I改善32.96%、A退化25.48%、V改善60.72%及所有单critic退化仍保留。第92轮自身新终端由原全回放health审查负责。

## 持续运行与未完成项

原92三learner463617/463619/463621、90个sampler、archive463623、冻结90原三evaluator/collector/postprocessor、guard及新等待器经过{observed['elapsed_s']:.3f}秒、{observed['samples']}样本、{len(observed['identities'])}个身份检查，三路steps增长。保存累计steps `{ {m:x['steps'] for m,x in progress.items()} }`；冻结90完成 `{ {m:x['completed_conditions'] for m,x in frozen.items()} }`，每方法总30。原startup/启动observer已正常完成，不重跑；本轮观察完成后也不重启。

继续原92每方法30×55秒/最多41250新transition和唯一归档消费者；完整92 reward/全loss/health/固定87跟踪仍待。原90冻结seed2026102638、全90/0updates及raw/88→90配对仍待，保持原21600秒截止，不重复或延长。没有新冻结91/92任务。

原90–92窗口I/A在90→91已经违反5%相邻必要条件，仍保留原PLAN及EARLY_WINDOW_FAILURE_91；92不能消除该失败。V仅一个相邻未违反，仍待完整第三端点/首尾与第二相邻及loss健康判断。原5%/nearzero1/bootstrap设置不改，当前没有完整窗口统计，不更换窗口隐去失败。

原物理/MJB、Task/Strict、filter、执行器、dt5e-5、actor49/canonical48、critic/replay52、clock49/history50/rawbit51、4m历史23/47 marker、terminal128、batch65536、UTD1、原LR/reward/masks、已学权重/Adam/RNG保持；没有离线权重晋升。partial75、74–76不可判、79/90安全中止、halfstd否决、旧失败窗口及所有软件失败保留。Direct33原数值验收保持，冻结33全30 Task/Strict0/0、旧28最终内存证明缺失与恢复后2条完整不变性通过保持；不额外训练Direct34。指定ESN仍缺，不重复询问或用其他主机模型替代。

## GPU与保存

原GPU guard97370、97399–97402持续，用户要求科研结束也保载；threshold50%、target70%、min duty.7、CPU4–6，不创建STOP。本轮{gpu['samples']}样本最低{gpu['minimum']}%、低于50次数{gpu['below50']}、末值{gpu['last']}%。包含合成保载，不等于科学吞吐或每瞬时保证；旧低值保留，当前守护不是重启自启服务。

共享SSD证据包 `{archive}`，{receipt['members']}成员、{receipt['bytes']}字节、SHA256 `{receipt['sha256']}`，全部tar成员及Python AST核验。清单 `docs/evidence/{TAG}/MANIFEST.json`，收据 [{TAG}_SAVE.json]({TAG}_SAVE.json)。Git index/commit逐字核验及正常push/真实远端确认记入包外 `{A}/GIT_BYTES_REVIEW.json` 和 `PUBLICATION.json`。大checkpoint/replay/raw仍共享SSD，HDD配额已满，仅原位更新254字节LATEST指针，不是HDD/arm1全备份。Goal active。
'''
with (R/'docs'/(TAG+'.md')).open('x') as f:f.write(text)
entry=f'''## 2026-10-30 — 第92轮前5000已审；固定87终端跟踪92已登记

- [交接](docs/{TAG}.md)。固定first5000原字节/保存标量/实际六栏图通过；critic首末I1.953316→1.872588、A1.121138→1.135406、V.747855→.770665，最大20.756/2.490/4.629。I密集尖峰与actor上移保持，仅早期证据，非收敛；prefix首版父路径错误原件保留，v2仅路径修复。
- 原7813终端/all5/原masks，87–91保存算术与52 raw输入精确；三份实际startup92架构/partial拒绝和27负例通过。唯一等待器{read(N/'PROCESS.json')['pid']}沿原archive截止等待，无新forward/physics/update；完整92终端结果待，无自动93/Direct34。
- 原92/冻结90继续，{observed['elapsed_s']:.3f}s/{len(observed['identities'])}身份保持，steps{ {m:x['steps'] for m,x in progress.items()} }，冻结完成{ {m:x['completed_conditions'] for m,x in frozen.items()} }。完整92及冻结全90/raw/paired仍待；原90–92 I/A必要条件失败与所有历史失败保留。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍守护；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read，发布见收据；Goal active，无子agent，指定ESN仍缺。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:v['steps'] for m,v in progress.items()},frozen={m:v['completed_conditions'] for m,v in frozen.items()})))
