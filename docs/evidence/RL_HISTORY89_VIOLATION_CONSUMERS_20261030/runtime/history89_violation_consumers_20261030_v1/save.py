from pathlib import Path
import ast,json,os,socket,hashlib,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';F=B/'runs/parameter88_history_frozen_full30_20261030_v1';I=B/'runtime/history89_violation_interface_20261030_v2'
TAG='RL_HISTORY89_VIOLATION_CONSUMERS_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
cache=read(D/'CACHE_SAVED_REVIEW.json');full=read(D/'CONSUMER_REVIEW.json');observations=[read(D/(s+'_OBSERVATION_REVIEW.json')) for s in ('CACHE','CONSUMER')]
assert cache['passed'] and full['passed'] and all(x['passed'] for x in observations)
for pid,start in observations[-1]['original_identities'].items():
 s=Path('/proc',pid,'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==start
frozen={m:read(F/m/'PROGRESS.json') for m in full['methods']};rows=[]
for line in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines():
 try:r=json.loads(line)
 except json.JSONDecodeError:continue
 if r['time']>=read(D/'CACHE_PLAN.json')['time']:rows.append(r)
assert rows and time.time()-rows[-1]['time']<25 and not Path('/tmp/sii_gpu_util_guard_20261030_v7/STOP').exists()
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows));gpu=dict(samples=len(rows),minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),frozen=frozen,gpu=gpu,original_identities=observations[-1]['original_identities'],goal='active',training90=False))
files=set(p for p in D.iterdir() if p.is_file() and p.suffix in ('.py','.json','.jsonl','.log','.diff') and p.stat().st_size<10_000_000)
for m in frozen:files.add(F/m/'PROGRESS.json');files.add(I/(m+'_BINDING.json'))
for n in ('PLAN.json','LAUNCH.json','REVIEW_LAUNCH.json'):files.add(F/n)
for n in ('PLAN.json','REVIEW.json','AFFINE_REVIEW.json','NUMERICAL_LAYOUT_CORRECTION.json'):files.add(I/n)
for n in ('RECEIPT.json','PUBLICATION.json'):files.add(B/'repository/RL_HISTORY89_VIOLATION_INTERFACE_20261030'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Complete89 full52 disk/cache and complete recorded consumer verification; full snapshots remain SSD; no online90 or physical evaluation launched'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for item in tar.getmembers():assert tar.extractfile(item).read()==(E/item.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_query_main='72d318a5a3a9cdbc94744da4b3c5964f670d3817',fetched_read_main='cea807d81619e8ceba3f3b9e963aebcb91d5bc1f',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD; HDD254-byte pointer only; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 完整89违规位52维全量保存、GPU缓存与冻结消费者核验

2026-10-30 UTC，Goal active。本轮承接[持久化初始接口](RL_HISTORY89_VIOLATION_INTERFACE_20261030.md)，完成三份完整89的全量52维learner/replay磁盘快照、实际GPU cache和完整记录轨迹消费者验证。0正式optimizer更新、0新物理步；无在线90/Direct34派发，不能视为reward改善或收敛。

实际主机 `{socket.gethostname()}`；共享SSD根 `{B}`；解释器 `{B}/env/bin/python`。本轮源码、登记和检查 `{D}`；完整迁移快照 `{B}/runs/history89_violation_interface_snapshots_20261030_v1`。每个snapshot标记 `interface_only_no_online_approval`，不是cycle90科学checkpoint。

## 全量保存与真实缓存

CACHE_PLAN在运行前绑定源码、恢复依赖、实际完整89 checkpoint、原始历史/bit sidecar、v2迁移learner及审查hash，CPU11/cuda:2/1800秒上限。实际{cache['elapsed_s']:.3f}秒完成；独立删除索引51恢复10个critic和所有Adam矩后，全部原learner字段/RNG逐digest精确；删除replay新增bit及新marker后，原51维所有字段和原history/23/47标记精确。全部11072448旧行保留。

三份full snapshot实际写盘、重新加载、完整digest核验；真实4m×52 GPU DeviceReplayCache下一65536条采样及RNG与CPU一致。每方法仅在可丢弃副本追加1条合成transition，精确核验原Bernoulli mask draw、GPU行刷新、全部旧prefix，随后恢复原状态；未向科学回放添加合成数据。另有mask拒绝与fallback两调用fixture。对所有终端和4096均匀行的raw bit作独立标量检查；原checkpoint hash保持。

| 方法 | 保留行 | 完整快照字节 | SHA256 |
|---|---:|---:|---|
'''
for m,x in cache['methods'].items():text+=f"| {m} | {x['rows']} | {x['snapshot']['bytes']} | `{x['snapshot']['sha256']}` |\n"
text+=f'''
## 1375动作与terminal消费者

新增 `violation_consumers.py` 显式要求原history与新bit双marker，恢复构造为history51上再包violation52。观测事件先消费刚完成interval一次，再动作；terminal仅消费最后interval。actor49、clock49、history50、bit51及原projection保持。候选使用v2 `PreservedHistoryLinear`，保留原51+action点积后加bit项；初版dense单行CUDA归约失败不删除，未放宽精度。

CONSUMER_PLAN在运行前绑定全部快照与三条完整89 `active_short_train_0600` journal/TERMINAL哈希，seed2026102638、CPU12/cuda:1/1800秒上限。三例均实际跨raw穿透.0002门。原history51和新52都消费全部1375 interval并使用相同外部动作RNG；前51观测、raw/mixed动作、CHEQ context、clock、terminal观测和外部RNG序列逐位完全一致。完整learner/host及GPU RNG均保持；新full replay和原89 checkpoint hash保持。原始记录的输入被重放给当前完整89模型，这不是重新执行物理轨迹，也不是新policy性能结果。

每方法额外原生/外部RNG三动作gate、不同seed变化及2种非法seed拒绝通过；新consumer每方法缺history或bit marker的两种实际恢复拒绝也通过。全部7993个真实终端的5个online和5个target Q与原51模型精确一致；bit移除后的clock projection与原50入口精确一致。实际consumer检查{full['elapsed_s']:.3f}秒。

| 方法 | 记录动作 | 动作前bit=1行数 | 首次bit=1动作索引（0起） | 终端health行 |
|---|---:|---:|---:|---:|
'''
for m,x in full['methods'].items():text+=f"| {m} | {x['recorded_observation_events']} | {x['preaction_violation_rows']} | {x['first_violation_action']} | {x['terminal_health_rows']} |\n"
text+=f'''
## 正在运行和下一步

原冻结88 `{F}` 完成数 `{ {m:x['completed_conditions'] for m,x in frozen.items()} }`；原三evaluator2675653/2675660/2675662、collector2675665、postprocessor2713409身份保持，仍按原21600秒截止。最终全90、全state不变、raw子步及82→88全90配对待；不要重复启动。

本轮cache/consumer有界supervisor观察均成功，合计{sum(x['identity_observations'] for x in observations)}次原进程身份核验。初次shell后台尝试未留下进程/启动收据且空log，随后唯一显式有界supervisor实际运行，记录见BACKGROUND_LAUNCH_OBSERVATION，未重复计算。GPU guard原97370/97399–97402持续，用户再次明确要求科学全部结束也继续保载。阈值50%、目标70%，本轮{gpu['samples']}样本min `{gpu['minimum']}`%、低于50 `{gpu['below50']}`，末值 `{gpu['last']}`%；含合成占用，非科研吞吐/每瞬时保证；历史预热与低谷保留，非重启服务。

下一步接入完整trainer、正式evaluation和health调度，验证52维状态/全replay与新采集current-next观测、双marker、旧历史保留及原生更新的准确恢复，再依据完整89退化及离线对照证据单独决定/登记有限在线90。未把本轮接口通过当成科学接受或自动授权90。需要新的修订内稳定性窗口，原88—90 A/V失败窗口保持，不将不同revision混合宣称收敛。

原协议30条件×55秒、每方法每周期41250新transition、append-only4m、terminal128、batch65536/UTD1、原LR/reward/masks、物理/MJB/gates/filter/dt5e-5保持。Direct33数值阶段接受但冻结30条件Task/Strict0/0，Direct28缺最终内存证明仍披露；指定ESN缺失，不替换成另一主机模型。partial75、不可判74–76、79安全中止、半std拒绝及全部历史失败保留。Goal active，完整reward稳定/loss健康与最终对比仍未达到。

## 归档和发布

开工真实query main72d318a5，随后fetch/read maincea807d8与baselinef6e8f8c，已fast-forward保留另一主机非RL final108登记/资源受阻记录；无更改本机冻结runtime，无子agent。使用仓库sii-research-sync技能。

共享SSD `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节/SHA256 `{receipt['sha256']}`，逐tar成员及Python AST核验。Git index/commit逐字节与正常push/真实ls-remote核验见包外PUBLICATION。HDD配额满，仅原位更新254字节LATEST；三份大快照及raw sidecars仍共享SSD，非HDD/arm1全备份。
'''
(R/'docs'/(TAG+'.md')).write_text(text.rstrip()+'\n')
entry=f'''## 2026-10-30 — 完整89违规位全量保存、GPU cache及完整消费者通过

- [交接](docs/{TAG}.md)。三份52维full snapshot磁盘重载、11072448旧行/learner/Adam逆迁移精确、实际4m GPU cache下一65536/RNG、可丢弃append/mask/fallback通过；大快照SSD、非在线90 checkpoint。
- 同完整89三条short0600各1375+terminal，原51与新52的观测/raw/mixed/context/clock/terminal/外部RNG精确，全部learner/RNG/replay不变；全部7993终端all5 online/target及原projection精确。真实跨bit门，0physics/正式update。trainer/eval/health正式调度和有限90仍待，原失败窗口保持，未收敛。
- 原冻结88完成数{ {m:x['completed_conditions'] for m,x in frozen.items()} }，原评测/后处理继续。GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}；用户明确科研结束也继续守护。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，非HDD/arm1全备份。main72d318a5→cea807d8/baselinef6e8f8c已query/fetch/read/ff，正常发布见收据，无子agent，Goal active。

'''
for name in ('UPDATE_LOG.md','HANDOFF.md'):
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.read_bytes()==data and p.stat().st_size==254
print(json.dumps(dict(receipt=receipt,gpu=gpu,frozen={m:x['completed_conditions'] for m,x in frozen.items()})))
