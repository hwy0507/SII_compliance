from pathlib import Path
import ast,json,os,socket,hashlib,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];P=B/'runtime/history89_continuation_20261030_v1';R=B/'repository/SII_compliance';T=B/'runs/parameter_history_cycle89_20261030_v1';F=B/'runs/parameter88_history_frozen_full30_20261030_v1';POST=B/'runtime/history88_frozen_postprocess_20261030_v1'
TAG='RL_HISTORY89_ONLINE_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def identity(j):
 f=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert f[0]!='Z' and f[19]==str(j.get('start',j.get('proc_start_ticks')));return dict(pid=j['pid'],start=f[19])
startup=read(T/'startup/REVIEW.json');observed=read(D/'ONLINE_OBSERVATION_REVIEW.json');assert startup['passed'] and observed['passed']
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not (D/'OBSERVATION_FAILURE.json').exists()
identities=[identity(j) for j in read(T/'LAUNCH.json')['jobs']+[read(T/'MONITOR_LAUNCH.json')]]
identities.extend(identity(j) for j in read(F/'LAUNCH.json')['jobs']+[read(F/'REVIEW_LAUNCH.json'),read(POST/'PROCESS.json')])
for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]:identities.append(identity(dict(pid=pid,start=start)))
progress={};frozen={};large=[]
for m in ['impedance','admittance','vmc']:
 assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
 progress[m]=read(T/m/'train/PROGRESS.json');frozen[m]=read(F/m/'PROGRESS.json')
 p=T/'startup'/(m+'.pt');large.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),kind='actual89_startup_snapshot'))
 p=Path(read(T/m/'REGISTRATION.json')['post_interruption_continuation']['checkpoint']['path']);large.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),kind='complete88_parent'))
rows=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines() if l.endswith('}')];rows=[r for r in rows if r['time']>=read(P/'PREFLIGHT_PLAN.json')['time']];assert time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
gpu=dict(samples=len(rows),minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True,scientific_throughput_claim=False)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),goal='active',progress89=progress,frozen88=frozen,identities=identities,gpu=gpu,large_artifacts=large,automatic90=False))
files=set()
def collect(folder):
 for p in folder.iterdir():
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff','.txt'} and p.stat().st_size<10_000_000:files.add(p)
for folder in [P,D,T,T/'startup']:collect(folder)
for m in progress:
 collect(T/m);collect(T/m/'check')
 for name in ['EXECUTION.json','PROGRESS.json']:files.add(T/m/'train'/name)
 for name in ['PROGRESS.json','RESULTS.json','STARTUP_REVIEW.json']:files.add(F/m/name)
for name in ['LAUNCH.json','REVIEW_LAUNCH.json']:files.add(F/name)
for name in ['PROCESS.json','PRE_REGISTRATION.json','PROTOCOL_PAIR_REVIEW.json']:files.add(POST/name)
for name in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_COMPLETE88_FROZEN88_20261030'/name)
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
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,large_artifacts=large,initial_main='aac53b19e38573a5d7dec84f24ffa0d5e80f5620',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD, HDD254-byte pointer only; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 有限history89实际续训；冻结88继续

2026-10-30 UTC，Goal active。根据完整88的全回放/奖励、loss/health、全90训练配对和固定87终端all5证据，本轮独立登记并实际启动唯一有限89；不是自动无限续训，不是新的history架构修改。完整89、reward稳定、最终loss健康仍待。采用仓库sii-research-sync，无子agent。

主机 `{socket.gethostname()}`；共享SSD `{B}`；Python `{B}/env/bin/python`。上一完整88及冻结启动交接：[RL_COMPLETE88_FROZEN88_20261030.md](RL_COMPLETE88_FROZEN88_20261030.md)。

## 决定及恢复

登记/driver `{P}`；三路活动run `{T}`。`SCIENTIFIC_DECISION.json`绑定完整88审查与实际图、loss/health、固定87终端及87→88全90解释。88平均reward均改善、critic首末1000均值均下降；仍保留A short0900 Task/Strict退化、I critic3及A critic2/3原mask内SSE退化、非零soft-bound诊断、actor漂移与全部loss尖峰。不能把一个周期改善当收敛，也不能把训练变化归因于history修订。

唯一改变是从完整88恢复后再运行一个89周期。每方法全部30条件×最多55s、最多41250新transition与更新；batch65536/UTD1、4m append-only、terminal128、原LR/reward/masks、23/47历史标记、actor49/canonical48、物理/MJB/gates/filter/执行器限制/dt5e-5保持。history critic/replay维度51沿用88，历史列50为preaction累计外部穿透p/(p+0.0002)，clock49；直接恢复已学习历史列及Adam状态，不再次零列迁移、不导入离线拟合权重。

三方法全部完整learner/replay/RNG准确恢复，84个协议/父checkpoint/浮点LR负例拒绝；每方法两次原生batch65536副本更新可精确重复，全state与replay恢复，checkpoint hash不变，总6次可丢弃更新/0physics/0正式更新。生成trainer与实际88 trainer逐字比较，仅原两处migrate_parent恢复改为load_state_dict，其余科学循环相同。`driver.py.diff`已按最终源重新生成。完整新launch gate强制所有证据/hash/原进程身份，训练单次派发，不自动90或Direct34。

## 实际89启动和监视

三路PID `{ {j['controller']:j['pid'] for j in read(T/'LAUNCH.json')['jobs']} }`；GPU1/2/3，learner CPU13/26/39，原每组12核/30物理sampler。新只读消费者 `{D}`。startup对真实新增快照核验原完整88全部51维回放字段、全旧cycles/markers、30MJB、CPU、原优化器超参，以及新current/next历史、观测/clock、动作映射和reward。旧历史列直接对完整88逐位比较；未错误使用87 sidecar长度或再次剥除历史列。

启动审查：`{ {m:dict(total=v['steps'],added=v['added_steps'],retained=v['retained_replay_rows'],reward_error=v['max_reward_reconstruction_error']) for m,v in startup['methods'].items()} }`。三路新reward重构最大误差0，启动快照是部分回合，终端覆盖仍由完整审查负责。实际观察{observed['elapsed_s']:.3f}秒/{observed['samples']}样本/{observed['identity_count']}原进程身份保持，三方法steps均增加。保存时总steps `{ {m:p['steps'] for m,p in progress.items()} }`，不等于完整89。

archive监视PID `{read(T/'MONITOR_LAUNCH.json')['pid']}` 等待原训练在唯一完整周期边界正常结束，最长14400s；静态归档目标 `{B}/runs/parameter_history_cycle89_archive_20261030_v1`，完整审查 `{B}/runs/parameter_history_cycle89_review_20261030_v1`。随后全51维回放/奖励映射、health及全部41250 loss复算自动运行，图生成后必须实际查看。health源码与88逐字相同；loss步号基线用完整88rows（历史87 binding rows+41250），无串联轮号替换。任何失败保留，不自动延长/重跑训练。

## 原冻结88与剩余科学目标

原冻结run `{F}`，三evaluator/collector/后处理身份保持，未重启。保存进度 `{ {m:dict(completed=p['completed_conditions'],condition=p['condition'],actions=p['actions']) for m,p in frozen.items()} }`。全部30×3训练条件、固定seed2026102638、0更新的完整结果、最终全learner/replay不变、raw审计和82→88全90配对仍待；前两条件失败不隐去。原后处理 `{POST}` 继续按原deadline等待，无新预算。冻结矩阵是开发同seed评测，非独立训练seed或held-out泛化。

原88—90同history统计方案已登记，但仅88完成、89运行、90未派发；完整89先审再明确决定下一有限阶段，不跨架构拼接旧窗口。Direct33数值阶段接受，冻结30 Task/Strict0/0；Direct28中断缺最终内存不变证明仍披露，不为了GPU负载重启Direct。指定ESN缺失、未替代他主机模型。partial75、74—76不可判、79安全中止、旧稳定性失败（含85—87）、半std失败、所有历史软件失败保留。

## GPU与持久化

用户明确要求科学任务全部结束仍继续GPU保载。原v7 supervisor97370/四worker继续，阈值50%、控制目标70%，不随有限训练结束停止，也不创建STOP。此次{gpu['samples']}样本，各卡最低 `{gpu['minimum']}`%、低于50样本 `{gpu['below50']}`，末值 `{gpu['last']}`%；包含合成守护，不能作为科研吞吐或瞬时保证。历史v7预热0及v6 31/33/44低谷全部保留。当前守护不等于重启后自启服务。

开工及启动前实际query/fetch/read main `aac53b19e38573a5d7dec84f24ffa0d5e80f5620`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新相关协议变更。小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节/SHA256 `{receipt['sha256']}`，tar逐成员及Python AST已核；Git index/commit逐字校验、正常push及实际远端确认后另写包外PUBLICATION。大checkpoint/轨迹仍共享SSD，HDD仅原位更新已有254字节LATEST；不是HDD/arm1完整备份。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 完整88精确恢复；有限history89实际运行

- [交接](docs/{TAG}.md)。完整88含Ashort0900及三critic退化证据后单独登记89，同history51/actor49与全部物理、LR、reward契约；84负例、6原生clone更新重复/恢复、精确全state/replay通过。trainer仅两恢复seam变化，未重置已学history权重/Adam，不自动90/Direct34。
- 真实startup全旧51维回放/30MJB/CPU/新映射/reward0误差通过，{observed['elapsed_s']:.3f}秒/{observed['identity_count']}身份观察保持；总steps{ {m:p['steps'] for m,p in progress.items()} }。唯一archive/full review/health/loss消费者已部署，完整89与稳定性待；原冻结88三路/collector/后处理继续，最终90及raw/配对待。
- GPU{gpu['samples']}采样min{gpu['minimum']}%、低于50{gpu['below50']}，科学完成仍保载，非科研吞吐。共享SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针、非全备份。mainaac53b19/baselinef6e8f8c已query/fetch/read，发布见收据；Goal active，无子agent，所有历史失败保留。

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
