from pathlib import Path
import json,hashlib,time,socket,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';S=B/'runtime/census97_continuation_20261031_v1';RUN=B/'runs/parameter_census_cycle97_20261031_v1';N=B/'runs/census96_new_terminal_diagnosis_20261031_v1';G=B/'runs/census_capacity6m_full96_20261031_v1'
TAG='RL_CENSUS97_CAPACITY6M_ONLINE_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
assert read(B/'runs/census97_fixed96_terminal_20261031_v1/PARTIAL_REJECTION_REVIEW.json')['passed'] and (B/'runs/census97_fixed96_terminal_20261031_v1/WAIT_LAUNCH.json').exists()
assert read(S/'ONLINE_OBSERVATION_REVIEW.json')['passed'];startup=read(RUN/'startup/REVIEW.json');assert startup['passed']
assert read(N/'SAVED_ARITHMETIC_REVIEW.json')['passed'] and read(G/'REVIEW.json')['passed'];obs=read(S/'ONLINE_OBSERVATION_REVIEW.json')
for j in obs['identities']:
 state=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert state[0]!='Z' and state[19]==j['start']
for n,h in read(S/'SOURCES.json')['files'].items():assert sha(S/n)==h
progress={m:read(RUN/m/'train/PROGRESS.json') for m in startup['methods']}
for m in progress:assert not (RUN/m/'train/FAILURE.json').exists() and not (RUN/m/'DRIVER_FAILURE.json').exists()
g=read(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');root=Path(g['root']);assert not (root/'STOP').exists();begin=read(N/'REFERENCE_PLAN.json')['time'];rows=[json.loads(x) for x in (root/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=begin];assert rows and time.time()-rows[-1]['time']<20
gpu=dict(samples=len(rows),minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],last=[v['utilization'] for v in rows[-1]['gpus']],synthetic_guard_included=True)
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows));put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress=progress,goal='active',identities=obs['identities'],automatic_followup=False))
files=set()
for root,suffixes in [(D,{'.py','.json','.jsonl'}),(S,{'.py','.json','.jsonl','.diff'}),(B/'runtime/census96_new_terminal_diagnosis_20261031_v1',{'.py','.json','.diff'}),(N,{'.json','.npz','.png'}),(B/'runtime/census_capacity6m_full96_20261031_v1',{'.py','.json','.diff'}),(G,{'.json'}),(B/'runtime/census97_terminal_20261031_v1',{'.py','.json','.diff','.txt'}),(B/'runs/census97_fixed96_terminal_20261031_v1',{'.json'}),(B/'runs/parameter_census97_99_reward_stability_20261031_v1',{'.py','.json','.diff'})]:
 files.update(p for p in root.rglob('*') if p.is_file() and p.suffix in suffixes)
files.update(RUN.glob('*.json'));files.add(RUN/'startup/REVIEW.json')
for m in startup['methods']:
 files.update((RUN/m).glob('*.json'));files.update((RUN/m/'check').glob('*.json'));files.add(RUN/m/'trainer_registered.py');files.add(RUN/m/'train/EXECUTION.json')
for name in ['GATE_AND_TIMING_REVIEW.json','SYSTEM_PYTHON_ATTEMPT.json']:files.add(B/'runtime/census96_new_terminal_diagnosis_20261031_v1'/name)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='New96 terminal reference/diagnosis, exact full96 capacity GPU equivalence, finite97 source/protocol/preflight/startup and observation; excludes large state/raw'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for e in t.getmembers():assert t.extractfile(e).read()==(E/e.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_members_verified=True,initial_main='a0962d6739d5c075df46a5a5b533f90a81318a7a',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='SharedSSD small evidence; existing HDD254-byte pointer only. Large checkpoints/raw SSD,not full HDD or arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/f'{TAG}_SAVE.json',receipt)
added={m:v['added_steps'] for m,v in startup['methods'].items()};steps={m:v['steps'] for m,v in progress.items()};growth={m:obs['last_steps'][m]-obs['first_steps'][m] for m in steps}
entry=f'''## 2026-10-31 — 完整96新终端已诊断；600万容量精确接续，有限97运行

- [交接](docs/{TAG}.md)。全8623终端参考及90新96逐行绑定通过，旧8533预测逐值复现、全state/RNG不变；新终端masked SSE I10.704/A31.640/V2.884。A short0600晚到终端占69.82%；V该例原mask0的critic1残差单列，原loss尖峰在终端后32更新但无抽样索引，不作因果归因。原gate/reward未改。
- 实际完整96旧4m/新6m/重复6m三路GPU9次隔离更新精确，全部设备镜像/8623终端/32分层/批次/metrics/Adam/RNG通过并恢复，无权重导入。正式97驱动再6次隔离更新、120错误协议/父状态拒绝、三CPU消费者与前瞻97–99意向通过。
- 准确全96父续每路一轮≤41250，新增第三容量标记保留23/47历史；startup新增{added}，旧回放/新52/action/reward精确、30MJB/30sampler，gamma .9995。{obs['identity_count']}身份连续{obs['elapsed_s']:.3f}s保持、steps增长{growth}；当前三正式及archive继续，完整97/实际跨4m审查/统计待，无自动98/Direct34。
- 原94–96 A/V失败、V loss尖峰/actor漂移及历史失败保持，Direct原验收/冻结0/0、旧28缺口/恢复2与指定ESN缺失保持，Goal active。GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}；科学结束仍guard。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅指针。

'''
report=f'''# 有限97与600万容量接续

**Goal active，未收敛。** 三路第97轮已从准确完整96 checkpoint启动，每路仅一轮、最多41250新增动作，30条件×55秒；不自动98/Direct34。原94–96窗口A/V失败保留。科学任务结束后GPU guard仍运行。

## 已完成诊断

完整96回放包含I2875/A2874/V2874共8623个终止样本。严格消费者建立全96参考，旧8533预测逐值复现，90个新96终端逐行绑定原transition/episode/reward/rollout；完整learner/Adam/replay/RNG及原checkpoint不变。保存数组算术独立复核并实际查看六栏图。所有五critic和原mask保留，新增终端masked SSE分别10.704156、31.639694、2.884097；全部历史失败仍在参考中。这是已见训练数据，不是独立泛化。

导纳short0600从第95轮成功变为完整55秒仍carry：carry进入时间约8.0→26.6秒，没有release，physical_valid仍true。终端step3979999，为本轮倒数第二条transition；该条在完整96下masked SSE22.091993，占新终端69.8237%。VMC同例Task仍成功，完成约29.76秒，但外穿透.207453711mm超过原.2mm，Strict失败；原terminal奖励由+25变−25。它的terminal step3975451，原loss尖峰3975483在后32更新。未保存抽样索引，时间先后不是具体抽样因果证据。

V该terminal的critic1预测−1.862406而reward−28.414473，但原mask为0；该分支的大残差保留在all5报告中，不能替代真实masked训练loss。V新增30终端all5 SSE714.804882而masked SSE2.884097；未改mask或据此声称健康。A/V行为退化、原loss尖峰和actor漂移继续保留。

## 容量与正式续训

真实完整96的旧4m/新6m/重复6m，在GPU0共9次隔离65536批次更新。全部retained设备镜像、8623终端与32分层、采样及RNG、metrics、更新后完整learner/Adam/RNG逐值相同；随后恢复全部状态，无权重保存。旧2m/4m容量标记不变，新增`replay_capacity_third`；准确去除架构标记后的完整96 replay digest绑定首次迁移。此前跨4m及满6m拒绝测试保留。

正式97协议、checkpoint、execution、startup及fullreview贯穿第三容量阶段，旧23/47历史保持，6m显式构造，禁止覆盖旧行。驱动120错误协议/父状态拒绝、3CPU完整消费者、6次隔离重复GPU更新及全state恢复通过。实际trainer仅改变预算报错轮次和两处容量元数据；原physics/MJB/gates/canonical48/actor49/critic52/filter/执行器限制/dt5e-5、reward/LR/terminal128/原mask/census/65536/UTD1不变。原96只读消费者gamma .9996错误原件保留，新97消费者核对真实.9995。

实际startup新增{added}，全旧回放精确保留，新current/next52、raw/mixed action与reward重建误差0，30模型和30sampler/方法均核验。{obs['identity_count']}身份连续{obs['elapsed_s']:.3f}秒，steps增加{growth}，保存时总steps{steps}。全8623固定96终端的97只读比较已预检、实际partial97拒绝完整检查，沿原archive截止等待；没有新增训练。完整97、真实跨4m旧行保留、终端增长、全loss和实际图仍待，不把startup当完成。

前瞻97–99窗口意向在首97派发之前登记，5%/nearzero1/5000bootstrap/seed2026102861保持，原94–96失败不替换。新窗口binder已准备，统计kernel逆向身份/文字替换后逐字节相同、错误容量及缺九组拒绝；全部九组结果仍待，97只派一轮，不自动授权98/99。Direct33原数值验收/冻结30 Task/Strict0/0、旧Direct28 memory证明缺口与恢复2已证不变；指定ESN和最终独立公平评测仍缺。

## 恢复和保存

主机`{socket.gethostname()}`，共享SSD根`{B}`，Python`{B}/env/bin/python`。正式run `{RUN}`，源码`{S}`；新终端`{N}`，实际96容量GPU证据`{G}`。原96训练及消费者已完成，勿重启；97中断须保全最新partial，不回退96。MuJoCo物理状态未保存。

启动PID以`{RUN}/LAUNCH.json`为准并重验/proc start ticks；archive/startup/observer有独立收据。原guard五身份保留、未创建STOP，非系统重启服务。保存窗口{gpu['samples']}个样本min{gpu['minimum']}%、低于50次数{gpu['below50']}，末{gpu['last']}；包含synthetic guard，非科学吞吐或每瞬时保证。

本轮准备脚本输出路径断言失败一次（写源/计划前），系统Python缺numpy导致独立复核首次导入失败一次，随后使用冻结env通过；97终端消费者预检后发现旧分组截止仍94，在实际推理/等待器启动前修为≤95，原源/计划/预检保留并重做全部分组覆盖检查；原件记录，未更新正式state。开工实际查询/fetch/read main a0962d67与baseline f6e8f8c2，无子agent。

小证据`{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，所有成员逐字节验证。大型checkpoint/replay/raw仍共享SSD；HDD仅既有254字节LATEST指针，不是HDD/arm1完整备份。实际Git发布见`{A}/PUBLICATION.json`。
'''
(R/'docs'/f'{TAG}.md').write_text(report)
for name in ['AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
 p=R/name;old=p.read_text();add=entry.replace('(docs/','(') if name.startswith('docs/') else entry
 if name=='AGENTS.md':first,rest=old.split('\n',1);p.write_text(first+'\n\n'+add+rest.lstrip('\n'))
 else:p.write_text(add+old)
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/f'{TAG}.md')+'\nGoal active; SSD assets.\n').encode();size=pointer.stat().st_size;assert len(data)<size
with pointer.open('r+b') as f:f.write(data+b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data)
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps=steps)))
