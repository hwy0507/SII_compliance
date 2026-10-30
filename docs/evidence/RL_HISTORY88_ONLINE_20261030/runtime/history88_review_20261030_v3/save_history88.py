from pathlib import Path
import json,time,hashlib,ast,tarfile,socket,subprocess,os
D=Path(__file__).parent;B=D.parents[1];D1=B/'runtime/history88_online_20261030_v1';D2=B/'runtime/history88_online_20261030_v2';R=B/'repository/SII_compliance';RUN=B/'runs/parameter_history_cycle88_20261030_v2';RUN1=B/'runs/parameter_history_cycle88_20261030_v1';W=B/'runs/parameter_history88_90_reward_stability_20261030_v1'
TAG='RL_HISTORY88_ONLINE_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
assert read(D/'ONLINE_OBSERVATION_REVIEW.json')['passed'] and read(RUN/'startup_v3/REVIEW.json')['passed']
assert read(D1/'INTEGRATION_REVIEW.json')['passed'] and read(D2/'LR_RETRY_CONTRACT_REVIEW.json')['passed']
for folder in [D1,D2,D]:
 for name,h in read(folder/'SOURCES.json')['files'].items():assert sha(folder/name)==h
obs=read(D/'ONLINE_OBSERVATION_REVIEW.json');progress={};identities=[]
for j in obs['identities']:
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['start'] and f[0]!='Z';identities.append(j)
for m in ['impedance','admittance','vmc']:
 assert not (RUN/m/'DRIVER_FAILURE.json').exists() and not (RUN/m/'train/FAILURE.json').exists();progress[m]=read(RUN/m/'train/PROGRESS.json')
rows=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=read(D1/'PREFLIGHT_PLAN.json')['time']];assert time.time()-rows[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_included=True,historical_dips_preserved=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),goal='active',identities=identities,progress=progress,gpu=gpu,active_composite_run=str(RUN),active_readonly_runtime=str(D),no_automatic89=True))
files=set()
def collect(folder):
 for p in folder.iterdir():
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.txt','.diff','.png','.log'} and p.stat().st_size<10_000_000:files.add(p)
for f in [D1,D2,D,RUN1,RUN,W,RUN/'startup_v3',D1/'health_fixture/health']:collect(f)
for m in ['impedance','admittance','vmc']:
 for f in {RUN1/m,(RUN/m).resolve()}:
  collect(f)
  if (f/'check').exists():collect(f/'check')
  if (f/'train/EXECUTION.json').exists():files.add(f/'train/EXECUTION.json')
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_HISTORY87_PERSISTENT_CRITIC_INTERFACE_20261030'/n)
# Preserve immutable startup snapshots by hash/address, without putting tensors in Git.
large=[]
for p in (RUN/'startup_v3').glob('*.pt'):large.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
put(D/'STARTUP_SNAPSHOT_MANIFEST.json',dict(files=large,scope='Shared SSD, immutable captured startup states; live latest checkpoints remain append-progress sources'))
files.add(D/'STARTUP_SNAPSHOT_MANIFEST.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,large_artifacts=large,scope='Shared SSD, not full HDD/arm1 backup; live log copies are snapshots at collection'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_member_bytes_and_ast_verified=True,inspected_main='628bf1b824520e3f98cfe385c48f6225e163e32d',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',large_artifacts=large,backup_scope='Shared SSD; HDD pointer only, no full HDD or arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
startup=read(RUN/'startup_v3/REVIEW.json');prefix=read(D/'EARLY_PREFIX_STATUS.json');table=[]
for m,p in progress.items():
 n=read(RUN/m/'REGISTRATION.json')['history_critic_amendment']['binding']['rows'];s=startup['methods'][m];q=prefix['methods'][m]
 table.append(f"|{m}|{p['steps']}|{p['steps']-n}|{s['added_steps']}|{q['first1000_mean']:.6f}→{q['last1000_mean']:.6f}|{q['maximum']:.6f}|")
text=f'''# History critic有限88已实际启动；三路状态与数据核验通过

2026-10-30，Goal active。经过完整87准确迁移接口和本轮完整消费链预检，已明确登记并实际启动唯一有限history88模型修订。三路都在采集/更新，正式父均为完整87；当前完整88结果、reward稳定和最终loss健康仍未得到证明，不启动自动89或Direct34。

实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。本轮query/fetch/read main `628bf1b824520e3f98cfe385c48f6225e163e32d`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，收尾没有远端新增；沿用sii-research-sync，无子agent。

## 有限科学修订与入口验证

登记和决定 `{D1}/SCIENTIFIC_DECISION.json`、`AMENDMENT.json`。原85—87稳定性全失败、I/V末段loss上升和历史终端拟合漂移；原87匹配terminal拟合15个critic终点均偏向history，但只有in-sample证据。本次仅测试一个history信息修订，不采用统一half-std/entropy目标调整，不导入离线拟合权重。

critic/replay50→51，索引50为当前动作前累计外穿透 `p/(p+0.0002)`；actor仍49维、clock仍49索引，online/target新增权重和Adam矩初值0，原学习率/reward/masks、terminal128、pair reducer、原上界投影、canonical48/物理/MJB/gate/filter/dt5e−5保持。每方法30条件×最多55s、最多41250新transition，batch65536/UTD1，4m append-only和23/47历史容量标记保留。模型会通过critic不确定性影响CHEQ mixing，不把修改后学习称为始终相同策略。

三路真实完整87恢复、全旧状态及replay/新增history核验、实际65536 batch在可丢弃副本两次恢复重放通过，原生更新全state精确，初次共6次clone update。每方法22个协议/父边界拒绝，共66；真实87不能冒充完整88。完整冻结30 evaluator、三动作gate/native replay、实际health入口均接入；health实际消费原87迁移软件fixture，所有终端统计与原87精确相同，六栏实际图查看保留旧I/V loss上升。该fixture不是新物理评测，冻结88尚未派发。

## 保留的失败与修复

1. 初次复制依赖时旧prepare.py覆盖新同名准备脚本，因缺旧评测输入退出；发生在新run和物理派发之前。保留原log/旧脚本，改独立register88.py并排除旧调度文件复制。
2. 初次实际启动中导纳被新入口的严格浮点相等挡下：原LR `2.9999999999999997e-05`，计算预期 `3e-05`，差 `−3.3881317890172014e-21`。退出位置在训练目录/物理进程创建前，0新物理/正式更新；阻抗和VMC已经运行且未停止。独立v2恢复原有1e−12有限容差，并让check-only执行同一gate，5个错误学习率拒绝和额外2次clone update通过。只重试导纳，没有改学习率或扩大预算。
3. 只读startup/full-review生成器的连续数字替换把旧父cycle87误写成88，startup检查器退出，observer如实记录缺失PID。独立v3只读脚本修正父87/当前88，替换旧startup/archive consumers；三条正式learner未改未重启。修正后实际三路启动快照全部核验通过，所有失败收据保留。

## 当前运行与实际证据

唯一活动汇总入口 `{RUN}`。其中impedance/vmc为原v1方法目录的链接，PID保持3861085/3861087；admittance在v2独立目录，PID见LAUNCH.json。原v1导纳目录保留零物理失败，不能重启它。实际只读归档/检查运行代码 `{D}`；活动只读身份在汇总run的 `REVIEW3_MONITOR_LAUNCH.json`、`REVIEW3_STARTUP_LAUNCH.json`，旧MONITOR/STARTUP收据保留但已替换。

|方法|保存时总steps|本轮新增steps|已审启动快照新增steps|已保存早期prefix q首→末1000均值|该prefix最大q loss|
|---|---:|---:|---:|---|---:|
{chr(10).join(table)}

启动证据 `{RUN}/startup_v3/REVIEW.json`：旧replay每个原字段精确、新增历史列全核、原optimizer超参数/历史标记、30 MJB和sampler affinity、全部捕获的新transition canonical48/context/clock/history/raw-action混合映射及reward重构通过，各方法reward重构最大误差0。保存的只是部分周期，terminal_coverage=False；完整终端/Task/Strict/周期reward仍待结束。

固定早期prefix分别I5932/A2000/V6000条，原行副本和hash在 `{D}`，全部有限但保留32.285/7.902/20.188尖峰；这些不同长度前缀只作运行观察，不作公平方法排序或收敛。随后{obs['elapsed_s']:.3f}秒、{obs['samples']}样本验证{obs['identity_count']}个learner/sampler/monitor/guard身份保持，各路steps实际增加。

v3 archive88会在全部有限作业完成后保存完整88，运行全旧字段和新51维current-next/reward逐行review、完整health及全41250loss/独立标量保存复算和图。实际图仍需结束后查看；不把监控部署当完成。下一步先完成这轮完整科学审查，再决定是否继续训练。冻结88完整30入口已准备，须完整88及对应注册后再派发。

未来88–90稳定性在任何88启动之前登记于 `{W}`：同原近零guard1、相对限5%、5000 bootstrap、seed2026102861，强制三个周期相同history修订。只有方案和源码，没有自动89/90训练或统计结果。所有原失败窗口保留，新旧revision不混算稳定。

## 保存和GPU

本轮{gpu['samples']}次GPU采样最低 `{gpu['minimum']}`%、低于50次数 `{gpu['below50']}`、末值 `{gpu['last']}`%。原v7 supervisor97370和四worker继续，科研结束也保载；包含合成占用，不冒充科学吞吐。历史v7预热0、v6 31/33/44低谷保留，采样不保证每瞬时，守护非重启服务。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐tar成员/AST校验，Git index/commit另核，成功push再实际确认远端之后包外PUBLICATION。当前大checkpoint/新轨迹、软件fixture和启动快照均共享SSD，启动静态快照hash见收据；非HDD/arm1全备份。HDD原LATEST指针254字节原位更新。

Direct33数值阶段接受但冻结30 Task/Strict0/0，28中断缺最终内存证明；指定ESN仍不可用，不替换他主机模型、不重复追问。partial75、74—76不可判、79安全中止、85—87稳定性失败及全部历史结论继续保留。Goal最终仍需四方法reward平稳/loss健康、冻结评测及指定比较。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — History critic有限88三路实际运行

- [交接](docs/{TAG}.md)。完整87为父，单一51维history修订/actor49不变，原LR/reward/物理/30×55/41250/batch65536/UTD1保持。完整链预检66拒绝、实际health/冻结gate/6 clone更新通过，明确有限88，未来88—90统计预登记不授权89/90。
- 初次依赖文件名覆盖、A浮点LR相等误拒、只读父轮号生成错误全部保留。A0physics后v2容差修复5拒绝+2 clone更新，仅A重试；原I/V持续。v3只读修正，三路实际启动全旧字段/历史/30MJB/CPU/新映射/reward0误差通过，{obs['elapsed_s']:.1f}秒{obs['identity_count']}身份观察通过；总steps{ {m:p['steps'] for m,p in progress.items()} }。早期loss下降仍有尖峰，非收敛，完整88审查待。
- 活动汇总 `{RUN}`，只读runtime `{D}`；原guard继续，GPU{gpu['samples']}采样min{gpu['minimum']}%、低于50{gpu['below50']}。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，非HDD/arm1全备份；main628bf1b8/baselinef6e8f8c已fetch/read，发布见收据，无子agent，Goal active。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254
if len(data)<254:data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(receipt));print(json.dumps(dict(progress=progress,gpu=gpu)))
