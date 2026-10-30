from pathlib import Path
import json,time,hashlib,ast,tarfile,socket,os
D=Path(__file__).resolve().parent;B=D.parents[1];P=B/'runtime/violation92_continuation_20261030_v1';R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle92_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';FP=B/'runtime/violation90_frozen_postprocess_20261030_v1'
TAG='RL_VIOLATION92_ONLINE_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
startup=read(T/'startup/REVIEW.json');observed=read(D/'ONLINE_OBSERVATION_REVIEW.json');assert startup['passed'] and observed['passed'] and read(P/'PREFLIGHT_FINISHED.json')['passed'] and read(D/'CONSUMER_PARENT_BOUNDARY_REVIEW.json')['passed']
identities=list(observed['identities'])+read(F/'LAUNCH.json')['jobs']+[read(F/'REVIEW_LAUNCH.json'),read(FP/'PROCESS.json')]
for j in identities:
 fields=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert fields[0]!='Z' and fields[19]==str(j.get('start',j.get('proc_start_ticks')))
for folder in (D,P):
 for name,h in read(folder/'SOURCES.json')['files'].items():assert sha(folder/name)==h
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not (D/'OBSERVATION_FAILURE.json').exists() and not (F/'REVIEW_FAILURE.json').exists() and not list(FP.glob('FAILURE*'))
progress={m:read(T/m/'train/PROGRESS.json') for m in ('impedance','admittance','vmc')};frozen={m:read(F/m/'PROGRESS.json') for m in progress}
for m in progress:assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
guard=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (guard/'STOP').exists()
rows=[json.loads(l) for l in (guard/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=read(P/'SCIENTIFIC_DECISION.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),progress92=progress,frozen90=frozen,identities=identities,gpu=gpu,goal='active',automatic93=False))
files=set()
for directory in (D,P):
 for p in directory.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff'} and p.stat().st_size<10_000_000:files.add(p)
files.add(B/'runtime/build_violation92_20261030.py');files.add(B/'runtime/build_violation92_consumers_20261030.py');files.update(T.glob('*.json'));files.add(T/'startup/REVIEW.json')
for m in progress:
 for n in ('REGISTRATION.json','CHECK_ONLY_REVIEW.json','INITIAL_STATE_REVIEW.json','VIOLATION_EXECUTION.json','trainer_registered.py'):files.add(T/m/n)
 files.add(T/m/'check/INITIAL_STATE_REVIEW.json')
 for n in ('EXECUTION.json','PROGRESS.json'):files.add(T/m/'train'/n)
 for n in ('PROGRESS.json','STARTUP_REVIEW.json'):files.add(F/m/n)
for n in ('LAUNCH.json','REVIEW_LAUNCH.json'):files.add(F/n)
for n in ('PROCESS.json','LAUNCH_BINDING.json'):files.add(FP/n)
for n in ('RECEIPT.json','PUBLICATION.json'):files.add(B/'repository/RL_COMPLETE91_20261030'/n)
for p in [B/'runs/parameter_violation_cycle91_review_20261030_v1/REVIEW.json',B/'runs/parameter_violation_cycle91_review_20261030_v1/loss/REVIEW.json',B/'runs/parameter_violation_cycle91_review_20261030_v1/PLOT_INSPECTION.json',B/'runs/violation91_fixed87_terminal_followup_20261030_v1/REVIEW.json',B/'runtime/violation90_completion_20261030_v1/ABORT_REVIEW.json',B/'runs/parameter_violation90_92_reward_stability_20261030_v1/PLAN.json']:files.add(p)
files.add(B/'runs/parameter_violation90_92_reward_stability_20261030_v1/EARLY_WINDOW_FAILURE_91.json');files.add(B/'runtime/violation91_completion_20261030_v1/ADJACENT90_91_REVIEW.json');files.add(B/'runtime/violation91_completion_20261030_v1/CHANGED_CASES_REVIEW.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Finite same52 continuation92 from exact learned91. Original90-92 I/A necessary-condition failures retained.108 negative guards,6 restored native clone updates, actual startup/full old replay/new mappings and120s identities. Complete92 pending; frozen90 and guard continue.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for item in tar.getmembers():assert tar.extractfile(item).read()==(E/item.name).read_bytes()
remote=read(P/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 完整91精确恢复；同52协议有限92实际训练

2026-10-30 UTC。Goal active，尚未达到全部方法reward平稳及loss健康。本轮根据完整91证据单独登记并启动第92轮；每方法只新增一轮、30×55s、最多41,250新transition，不自动93。原第90轮冻结评测及其唯一后处理继续。前序结果：[完整91](RL_COMPLETE91_20261030.md)。

主机 `{socket.gethostname()}`；共享SSD `{B}`，解释器 `{B}/env/bin/python`。开工实际query/fetch/read main `{remote['main']}` 和baseline `{remote['baseline']}`，遵循 [sii-research-sync](../skills/sii-research-sync/SKILL.md)，无子agent。新运行源码 `{P}`；消费者 `{D}`；训练 `{T}`。解释器/库版本、seed、源/MJB hash沿各实际REGISTRATION和EXECUTION，无变更依赖或模型。完整父快照 `{B}/runs/parameter_violation_cycle91_archive_20261030_v1/<method>/cycle_00091.pt`。

## 科学决定与验收边界

完整91各30完整55s、0abort，Task/Strict I18/17、A14/13、V17/17。相对90，I reward与固定87终端masked SSE改善，A reward/Strict与终端masked SSE退化，V reward/标签接近且masked SSE改善；loss仍有尖峰、I尾部升高、actor均值漂移。这些混合方向发生在raw violation52启用后的前两个完整在线周期，尚不足以支持再改LR、奖励或架构。选择从所有已学91权重/Adam/replay/RNG再接续一个相同协议的有限92，观察改善/退化是否持续，并补齐原90–92描述性分析所需第三端点。

原90→91 I42.5116%、A20.8292%已违反原5%相邻必要条件，92不能修复这个事实。原PLAN、EARLY_WINDOW_FAILURE_91和全部旧失败保持；不能通过换窗口或删除中止来宣布收敛。V首相邻.09648%仅未违反该条件，仍需完整92/首尾/第二相邻及loss健康证据。当前没有完整92或完整窗口统计。新启动不等于收敛，也不是因GPU占用而无限延长训练。完整92 review/loss/health审查后才能决定下一有限阶段。

## 恢复、接口与启动验证

driver只更新准确完整父91/新92边界与证据绑定；trainer_registered.py与实际91逐字相同。历史plateau修订floor仍90，history首次88、violation首次90；interval消费一次、两架构marker不变。准确父steps I3770950/A3773750/V3774750，用前轮真实steps+实际新增绑定，保留90 I安全中止后的真实行数；不从原89迁移绑定直接加一个周期推算91。

三方法各36负例、共108拒绝通过，覆盖错误周期/partial/seed/steps、预算/自动后续/协议改写、架构marker缺失、旧51维current/next、cursor/capacity/优化器计数及LR。实际batch65536每方法两次可丢弃原生clone更新，共6次；相同batch重复metrics与完整state精确，之后learner及replay RNG恢复，0正式更新/physics，未推广clone权重。原已学history/violation及Adam均保留。

实际startup三路新增步数 `{ {m:x['added_steps'] for m,x in startup['methods'].items()} }`。全部旧回放52列及其他字段逐位精确保留；新增current/next原始bit、连续history、clock、raw→mixed动作及reward逐条核验，最大reward重建误差 `{ {m:x['max_reward_reconstruction_error'] for m,x in startup['methods'].items()} }`。每方法30冻结MJB、30sampler与原CPU配置通过。仅根据原interval journal重建reward，不声称独立动力学重跑。

实际启动后观察 `{observed['elapsed_s']:.3f}`秒，{observed['identity_count']}个原进程身份、{observed['samples']}样本通过，三路steps增长。保存时steps `{ {m:x['steps'] for m,x in progress.items()} }`。完整91父state和实际正式INITIAL_STATE_REVIEW分别核验，不能用check-only替代真实启动。

原critic/replay52、actor49/canonical48信息、clock49/history50/rawbit51、terminal128、batch65536、UTD1、原LR/reward/masks、append-only4m replay及23/47历史marker、Adam/RNG不改。冻结物理/MJB、Task/Strict门、filter、执行器限制与dt5e-5不改；所有历史安全中止、partial75、74–76不可评估、halfstd否决和软件失败保留。

startup/full review/archive/loss消费者绑定新92，loss首步为I3770951/A3773751/V3774751，上限分别3812200/3815000/3816000；health算法与91逐字相同。完整结果由唯一archive消费者等待正常FINISHED后复制和hash核验，再执行全回放/所有新reward、health和全loss审计。该消费者有限等待14400秒，不会自动启动93；新完整图仍须实际查看。

## 持续运行与后续

保持本轮三训练进程、唯一archive/review/health/loss、startup与observer的实际身份，已完成的preflight不重跑。具体命令、PID/start ticks在 `{T}/LAUNCH.json`、MONITOR/STARTUP/OBSERVER_LAUNCH。首先读取这些实际进程与结果，避免重复派发。

原冻结90 `{F}`，evaluator283421/283428/283430、collector283433及postprocessor292743仍存活，保存完成数 `{ {m:x['completed_conditions'] for m,x in frozen.items()} }`。原seed2026102638、0updates、全90及raw/88→90配对仍待；保持原launch+21600秒截止，不延长、不重复派发。本轮未新增冻结91/92。

Direct33数值收敛已接受；冻结33全30 Task/Strict0/0、旧28动作精确但最终内存证明缺失、恢复后2条完整不变性通过均保留。不把任务成功增加为数值收敛要求，不为占用训练Direct34。指定ESN仍缺，不重复询问或替用其他主机模型。接续完整92/原冻结90，原90–92统计在真实输入齐全后按原方案计算，保留已知I/A失败；Goal active。

## GPU与保存

原guard supervisor97370、workers97399–97402持续运行，用户明确要求科研完成后仍保载。threshold50%、target70%、min duty.7、CPU4–6；不创建STOP。守护当前并非重启自启服务。

从本轮科学登记起{gpu['samples']}样本、跨度{gpu['elapsed_s']:.3f}秒，四卡最低{gpu['minimum']}%、低于50次数{gpu['below50']}，末值{gpu['last']}%。包含合成保载，不等于纯科研吞吐或每瞬时保证；历史warmup0与旧低谷记录保持。

小证据 `{archive}`，{receipt['members']}成员、{receipt['bytes']}字节、SHA256 `{receipt['sha256']}`，逐tar成员/AST核验。清单 `docs/evidence/{TAG}/MANIFEST.json`；收据 [{TAG}_SAVE.json]({TAG}_SAVE.json)。Git index/commit逐字核验和正常push/实际远端确认记入包外 `{A}/PUBLICATION.json` 与 `GIT_BYTES_REVIEW.json`。大checkpoint/replay/raw保留共享SSD；HDD配额满，仅原位更新254字节LATEST指针，非HDD/arm1全备份。
'''
with (R/'docs'/(TAG+'.md')).open('x') as f:f.write(text)
entry=f'''## 2026-10-30 — 完整91精确恢复；同52协议有限92已启动

- [交接](docs/{TAG}.md)。依据完整91混合结果单独登记92，各方法一轮/最多41250新增，trainer与实际91逐字相同，原52/actor49/history/violation/Adam/RNG及全部协议保持。原90–92 I/A相邻5%必要条件失败保持，无自动93/Direct34，未收敛。
- 108负例、6次真实batch65536 clone重复恢复与准确91边界通过；实际startup全旧回放/新current-next52/action/reward0误差、30MJB/30sampler通过。{observed['elapsed_s']:.3f}s/{observed['identity_count']}身份保持，steps{ {m:x['steps'] for m,x in progress.items()} }；完整92及健康稳定审查待。
- 原冻结90/后处理继续，完成数{ {m:x['completed_conditions'] for m,x in frozen.items()} }，最终全90/raw/paired待。GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍守护；全部旧失败及指定ESN缺失保持。
- SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}逐成员核验，HDD仅254字节指针，非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read，正常发布见收据。Goal active，无子agent。

'''
for name in ('UPDATE_LOG.md','HANDOFF.md'):
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:x['steps'] for m,x in progress.items()},frozen={m:x['completed_conditions'] for m,x in frozen.items()})))
