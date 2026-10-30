from pathlib import Path
import ast,json,os,socket,hashlib,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];P=B/'runtime/violation90_online_20261030_v1';R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle90_20261030_v1';F=B/'runs/parameter88_history_frozen_full30_20261030_v1';POST=B/'runtime/history88_frozen_postprocess_20261030_v1'
TAG='RL_VIOLATION90_ONLINE_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def identity(j):
 f=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert f[0]!='Z' and f[19]==str(j.get('start',j.get('proc_start_ticks')));return dict(pid=j['pid'],start=f[19])
startup=read(T/'startup/REVIEW.json');observed=read(D/'ONLINE_OBSERVATION_REVIEW.json');assert startup['passed'] and observed['passed']
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not (D/'OBSERVATION_FAILURE.json').exists()
assert read(D/'ACTUAL_STARTUP_BIT_REVIEW.json')['passed']
identities=[identity(j) for j in read(T/'LAUNCH.json')['jobs']+[read(T/'MONITOR_LAUNCH.json')]]
identities.extend(identity(j) for j in read(F/'LAUNCH.json')['jobs']+[read(F/'REVIEW_LAUNCH.json'),read(POST/'PROCESS.json')])
for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]:identities.append(identity(dict(pid=pid,start=start)))
progress={};frozen={};large=[]
for m in ['impedance','admittance','vmc']:
 assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
 progress[m]=read(T/m/'train/PROGRESS.json');frozen[m]=read(F/m/'PROGRESS.json')
 p=T/'startup'/(m+'.pt');large.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),kind='actual90_startup_snapshot'))
 p=Path(read(T/m/'REGISTRATION.json')['post_interruption_continuation']['checkpoint']['path']);large.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),kind='migrated_complete89_parent'))
rows=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines() if l.endswith('}')];rows=[r for r in rows if r['time']>=read(P/'PREFLIGHT_PLAN.json')['time']];assert time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
gpu=dict(samples=len(rows),minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True,scientific_throughput_claim=False)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),goal='active',progress90=progress,frozen88=frozen,identities=identities,gpu=gpu,large_artifacts=large,automatic91=False))
files=set()
def collect(folder):
 for p in folder.iterdir():
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff','.txt','.log'} and p.stat().st_size<10_000_000:files.add(p)
for folder in [P,D,T,T/'startup',B/'runs/parameter_violation90_92_reward_stability_20261030_v1']:collect(folder)
files.add(B/'runs/parameter_history88_90_reward_stability_20261030_v1/REVISION_BOUNDARY_90.json')
for m in progress:
 collect(T/m);collect(T/m/'check')
 for name in ['EXECUTION.json','PROGRESS.json']:files.add(T/m/'train'/name)
 for name in ['PROGRESS.json','RESULTS.json','STARTUP_REVIEW.json']:files.add(F/m/name)
for name in ['LAUNCH.json','REVIEW_LAUNCH.json']:files.add(F/name)
for name in ['PROCESS.json','PRE_REGISTRATION.json','PROTOCOL_PAIR_REVIEW.json']:files.add(POST/name)
for name in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_HISTORY89_VIOLATION_PIPELINE_20261030'/name)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,large_artifacts=large,scope='Shared SSD dated snapshots. Large live artifacts remain original SSD. Not full HDD/arm1 backup. Original diff context whitespace retained.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for member in tar.getmembers():assert tar.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,large_artifacts=large,initial_main='ef82273834a43c4c37bc8f31c4eeb1cca8889275',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD, HDD254-byte pointer only; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 有限违规位 critic 第90轮实际训练与接续记录

2026-10-30 UTC，Goal active。主机 `{socket.gethostname()}`；共享SSD根 `{B}`；Python `{B}/env/bin/python`。本轮从准确完整89的迁移快照，单独登记并实际启动三个方法的有限90。训练尚未收敛；完整90、reward稳定和loss健康仍待。使用仓库 `skills/sii-research-sync/SKILL.md`，无子agent。

## 科学决定与边界

上一交接：[完整89迁移与原生预检](RL_HISTORY89_VIOLATION_PIPELINE_20261030.md)。完整89各30×55s/41250步/无abort，I/A/V Task/Strict为18/17、13/12、17/16；A相对88丢4 Strict与3Task，V丢1 Strict，全部critic末段均值上升。原88→89 A/V相邻reward变化130.492%/63.462%，超过5%必要条件，失败不能被新架构覆盖。

匹配52维零输入对照与因果违规位离线拟合总masked loss改善约53.4%/.83%/1.52%，但Icritic0/Acritic1变差、A/V尖峰仍在。仅据这些有限证据和全部恢复检查，登记一个在线90试验；没有导入离线拟合权重、没有宣称架构最终接受或收敛。完整科学决定与证据hash在 `{P}/SCIENTIFIC_DECISION.json`。

新critic/replay52，actor49、canonical48保持；clock49、历史50、违规bit51。bit来自动作前raw累计外穿透严格大于0.0002m；历史仍为p/(p+0.0002)。保留原已学history列、Adam、两种架构marker、完整回放/RNG、23/47容量标记。沿用先计算原51+action点积再加bit贡献的数值布局；不是原先已拒绝的dense插零列布局，也不宣称与离线dense拟合轨迹相同。

每方法唯一30条件×最多55s、最多41250新动作/更新；4m append-only、terminal128、batch65536/UTD1、原LR/reward/masks/Imin+A-Vmean/actor min保持。冻结物理/MJB、Task/Strict、filter、执行器限制、dt5e-5保持。只登记90，无自动91/92或Direct34。

原88—90方案和失败证据全部保留，新增 `runs/parameter_history88_90_reward_stability_20261030_v1/REVISION_BOUNDARY_90.json`。I原同修订三轮窗口未完整，不能将新52维90与旧51维88/89混合。新90—92同修订窗口已在训练前登记，5%/nearzero1/5000 bootstrap/seed2026102861/anchor55不变；这里只是统计方案，不授权91/92训练，未计算不完整全窗口统计。

## 预检、启动与消费者

在线代码 `{P}`，run `{T}`，只读消费者 `{D}`。三方法共93个错误协议/父状态/marker/维度/LR负例拒绝；全部准确完整learner/replay恢复，每方法两次batch65536原生clone更新可逐字重复并恢复，共6次已丢弃更新、0预检物理/正式更新。正式trainer以实际89源码为基础，仅增加bit amendment保存及plateau修订起点88→90；逆变换源码逐字相同，interval消费恰一次。历史migration amendment的preparation-only字段描述原迁移来源，新的在线权限和预算由独立90 continuation决定。

第一版注册脚本误引用不存在的重复PLOT_INSPECTION路径，在创建登记前失败；准确失败源码 `register90_initial.py.txt` 和 `REGISTRATION_INPUT_FAILURE.json`保留。删除这项冗余错误引用后注册成功；真正89的图检查仍绑定，不修改已登记计划或科学证据。

三路训练PID `{ {j['controller']:j['pid'] for j in read(T/'LAUNCH.json')['jobs']} }`，GPU1/2/3，learner CPU13/26/39、各30 sampler共享原12核。实际startup对全旧52维回放前缀、双marker、旧cycle history、优化器超参、30MJB/CPU、新current/next52观测/clock/history/raw bit/动作/奖励进行检查。结果 `{ {m:dict(steps=v['steps'],added=v['added_steps'],retained=v['retained_replay_rows'],reward_error=v['max_reward_reconstruction_error']) for m,v in startup['methods'].items()} }`。新奖励重构误差0；这是部分回合快照，终端由完整消费者另审。另对这些已保存实际startup快照检查：每方法全部10个online/target critic的bit列、5个在线critic的Adam一/二阶矩均有限且非零；只证明新列实际参与了学习，不代表性能改善。

启动后{observed['elapsed_s']:.3f}秒/{observed['samples']}观察，{observed['identity_count']}个进程身份保持，三方法步数均增加。保存时总steps `{ {m:p['steps'] for m,p in progress.items()} }`。archive监视PID `{read(T/'MONITOR_LAUNCH.json')['pid']}`，最长14400s，等待原唯一完整90边界后归档并运行full review/health/loss。完整检查包含全部新current/next52及terminal raw bit、奖励、旧前缀和30条件。loss步号以完整89 bit binding rows为基准，实际连续长度≤41250，保留abort短回合，不硬写满预算。

health用violation_class(history_class(PublishedLearner))恢复双marker，检查实际90 execution/protocol hash；不拿只允许原89元数据的preparation validator验证已训练90。原unprojected固定minimum-pair TD诊断语义不变，仍不等同线上投影或A/V mean目标。完整90消费者已部署但尚未完成，生成图必须实际查看后才解释结果。

## 原冻结任务与其余目标

原冻结88 `{F}` 三evaluator/collector/后处理保持原身份和21600s截止，未重启/延长。当前 `{ {m:dict(completed=p['completed_conditions'],condition=p['condition'],actions=p['actions']) for m,p in frozen.items()} }`，完整90回合结果、全state不变、raw复算及82→88配对仍待。固定seed2026102638，0更新；属于训练条件开发评估，不是held-out泛化或独立训练seed。

Direct33数值阶段接受，冻结33全30 Task/Strict0/0；Direct28缺最终内存不变证明仍披露。指定ESN仍不可用，不替代其他主机模型。partial75、74—76不可判、79安全abort、所有旧稳定性失败/halfstd拒绝和软件失败保留。Goal仍active。

## GPU守护与持久化

按用户明确要求，即使科学任务全部完成也保持GPU保载。原v7 supervisor97370及worker97399–97402继续，阈值50%、目标70%；没有STOP，也不与有限科学任务同停。本轮{gpu['samples']}样本，各卡最低{gpu['minimum']}%，低于50样本{gpu['below50']}，末值{gpu['last']}%。这些数值包含合成守护，不能称为科学吞吐或所有瞬时保证。原v7预热0及v6低谷31/33/44仍保留；守护不是重启后自动服务。

已实际query/fetch/read main `ef82273834a43c4c37bc8f31c4eeb1cca8889275` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新相关冻结协议变化。小证据 `{archive}`：{receipt['members']}成员/{receipt['bytes']}字节/SHA256 `{receipt['sha256']}`，全部tar成员和Python AST已验证；Git index/commit核验、正常push和实际远端确认后另写包外PUBLICATION。大checkpoint/轨迹仍共享SSD，HDD配额满仅原位更新已有254字节指针，不是HDD/arm1完整备份。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 违规位 critic 有限90实际训练

- [交接](docs/{TAG}.md)。完整89退化与原88—90 A/V失败均保留；单独登记一个52维违规位在线90，不导入离线权重，保持已学history/Adam/双marker、actor49及原全部科学协议。93负例/6原生clone重复恢复通过；新90—92仅统计预登记，不自动91/92/Direct34。
- 实际startup全部旧52维前缀/新current-next bit/30MJB/CPU/reward0误差通过；{observed['elapsed_s']:.3f}秒/{observed['identity_count']}身份保持，总steps{ {m:p['steps'] for m,p in progress.items()} }。完整archive/review/health/loss消费者继续，未收敛。首次注册路径错误原件保留。
- 原冻结88完成数{ {m:p['completed_conditions'] for m,p in frozen.items()} }继续，最终全90/raw/paired待。GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束仍保载；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，非HDD/arm1全备份。mainef822738/baselinef6e8f8c已query/fetch/read，发布见收据；无子agent，Goal active。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254
data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:p['steps'] for m,p in progress.items()},frozen=frozen)))
