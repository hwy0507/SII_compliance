from pathlib import Path
import json,time,hashlib,tarfile,ast,socket
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle97_20261031_v1';BOUND=B/'runs/census97_capacity_boundary_20261031_v1';TAG='RL_CENSUS97_PREFIX_COMPARISON_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
obs=read(D/'ONLINE_OBSERVATION_REVIEW.json');assert obs['passed'];prefix=read(D/'prefix5000/REVIEW.json');assert prefix['passed'] and read(D/'PLOT_INSPECTION.json')['actual_visual_inspection']
for n in ['PRIOR90_REVIEW.json','COMPARISON_PREFLIGHT.json','CACHE_POPULATION_PREFIX_REVIEW.json','CACHE_POPULATION_NEGATIVE_REVIEW.json','SOURCE_ORDER_REVIEW.json','CAPACITY_COMPARISON_REVIEW.json']:assert read(D/n)['passed']
assert read(BOUND/'PREFLIGHT_REVIEW.json')['passed']
for j in obs['identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start']
assert not list(D.glob('COMPARISON_FAILURE*')) and not list(BOUND.glob('FAILURE*'))
progress={m:read(RUN/m/'train/PROGRESS.json') for m in prefix['methods']};g=read(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');guard=Path(g['root']);assert not (guard/'STOP').exists();begin=read(D/'PREFIX_PLAN.json')['time'];rows=[json.loads(x) for x in (guard/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=begin];assert rows and time.time()-rows[-1]['time']<20
gpu=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),progress=progress,gpu=gpu,goal='active',previous_turn_classification='progress',boundary_complete=(BOUND/'REVIEW.json').exists(),complete97=(B/'runs/parameter_census_cycle97_review_20261031_v1/FINISHED.json').exists()))
files={p for p in D.rglob('*') if p.is_file() and p.suffix in ('.py','.json','.jsonl','.npz','.png','.diff')};files.update(BOUND.glob('*.json'))
for p in [B/'runtime/census97_continuation_20261031_v1/SCIENTIFIC_DECISION.json',B/'runtime/census97_continuation_20261031_v1/SOURCES.json',B/'runtime/census97_continuation_20261031_v1/STABILITY_WINDOW_INTENT.json',RUN/'MONITOR_LAUNCH.json',RUN/'LAUNCH.json',B/'runs/census97_fixed96_terminal_20261031_v1/WAIT_LAUNCH.json',B/'runtime/direct34_dispatch_preparation_20261028_v1/DIRECT_STAGE_DECISION.json',B/'runs/serl_take33_frozen_combined_review_20261030_v3/REVIEW.json']:files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Fixed first5000 actual97 raw metrics/saved arithmetic/actual plot, full96 prior90 comparison inputs and bounded consumer, prospective actual4m boundary checker, original Direct scope recheck, continuous102 identities; no complete97 claim.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for e in t.getmembers():assert t.extractfile(e).read()==(E/e.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_members_verified=True,initial_main='fd272610a93e3c53ba75127d18b1c88580754097',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='SharedSSD small evidence; existing HDD254-byte pointer only; large checkpoints/raw remainSSD,not fullHDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/f'{TAG}_SAVE.json',receipt)
growth={m:obs['last_steps'][m]-obs['first_steps'][m] for m in progress};steps={m:v['steps'] for m,v in progress.items()}
entry=f'''## 2026-10-31 — 第97轮固定前5000已审；全90比较与实际4m跨界检查已登记

- [交接](docs/{TAG}.md)。固定first5000原日志/全部保存数组/独立标量及实际九栏图通过，原loss最大I1.478/A1.513/V1.197；均值.951526/1.040172/.725520，actor小幅变化保留。该前缀没有新终端，不作reward稳定或收敛结论。
- 全96→97的90条件比较及真实终端计数消费者已登记，原全96模型/标签/奖励算术与缺完整97拒绝通过；仅允许显式4m→6m容量阶段差异，18错误协议拒绝。前缀总终端2875/2874/2874逐更新精确，15损坏计数拒绝，原32分层线上tensor未记录。
- 实际跨4m只读审查在三路均未过4m前登记，8损坏数组/日志拒绝；等待每路一个真实边界快照检查完整旧回放及边界两侧52/action，尚无跨界通过结论。原三正式/archive/固定8623终端/全90比较与边界等待继续，{obs['identity_count']}身份连续{obs['elapsed_s']:.3f}s保持、steps增长{growth}。
- 重新核对Direct原决定：33训练数值阶段已验收，不追加34；冻结全30 Task/Strict0/0、旧28最终memory缺口/恢复2已证保留。参数收敛与指定ESN/最终比较仍待，Goal active。GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}；科学结束仍guard。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅指针。

'''
table=['|方法|原loss首1000均值|末1000均值|前5000均值|最大|','|---|---:|---:|---:|---:|']
for m,v in prefix['methods'].items():
 q=v['stats']['agent_train/original_sampled_q_loss'];table.append(f"|{m}|{q['first1000']:.9f}|{q['last1000']:.9f}|{q['mean']:.9f}|{q['maximum']:.9f}|")
report=f'''# 第97轮前缀、完整比较与实际容量边界准备

**Goal active，参数RL尚未收敛。** 上一轮是真实进展：准确全96续训97及6m实际接入。本轮不重启这些作业；完成固定前5000健康检查，登记完整97后的全90比较、实际跨4m保留检查，并连续核验现有进程。

## 固定前5000

{chr(10).join(table)}

固定范围在读取loss值之前确定，原5000行字节前后精确，全部metrics与NPZ逐值一致，首/末/全均值和极值用math.fsum独立复算。实际查看九栏图；三原loss和条件估计的250-update均线大体平缓，actor有小幅上移。原health口径是original_sampled_q_loss，不以conditional loss替代。完整96的V尖峰8.7554、actor漂移和全部失败保持，前缀不证明它们已解决。

前5000所有更新terminal_population与原2875/2874/2874加inclusive done计数精确；实际没有新terminal，不能证明真实增长。15个损坏日志/计数例拒绝。已锁census/trainer源顺序为add/cache同步→step→transition日志→update→optimizer日志，线上逐分层tensor未保存，不宣称观察。

## 完整比较与容量边界

已读真实全96三路×30条件的模型身份、Task/Strict/abort/阶段与reward分项/总值，全部通过。新97比较只允许显式新增第三容量阶段，其他科学字段与96相同；真实协议接受，18个物理/条件/容量/父checkpoint/估计器损坏输入拒绝。消费者等待原97 archive完整review/health/loss后比较全部90条件、保留全部标签退化，再核验每条在线terminal计数与完整6m checkpoint中的done/mask/32分层。缺完整97检查已拒绝；无未来结果、无自动98。

实际跨4m观察在每方法仍<4m时登记；每路仅一份实际>4m checkpoint快照，逐块比较完整96的所有回放数组字段，核验新增日志reward/done与原mask，边界两侧5行与原actor journal的current/next52、raw到mixed动作逐值绑定。8个覆盖旧行/新reward/done/NaN/mask/schema/shape/step损坏例拒绝。当前只是在等待真实跨界，不能用先前合成边界或full96兼容测试当作实际跨界证据。原checkpoint/source/训练不修改，零physics/optimizer。路径`{BOUND}`，沿原97预算截止；失败保留并检查原因，不重启训练。

原固定8623终端比较等待器继续，没有重复创建。原三正式、90sampler、archive、三个只读等待器和五guard共{obs['identity_count']}身份连续{obs['elapsed_s']:.3f}s/ {obs['samples']}样本保持，steps增加{growth}，保存总steps{steps}。完整97、真实跨界、真实终端增长、完整loss/实际图及前瞻97–99全九组仍待；原94–96 A/V失败保留。

## Direct范围与恢复

再次读取并逐hash核验原DIRECT_STAGE_DECISION及其7项证据，Direct33已经满足原训练数值标准，保留33，不因冻结任务失败或GPU占用追加34。最新冻结33组合审查全30 Task/Strict0/0；原28最终内存不变性无法证明、全部28保存动作重放精确、新2完整state不变性已证。没有把这些局限抹去，也不把成功率事后新增为原数值收敛门槛。整体Goal仍需参数reward平稳/loss健康，以及指定ESN与最终独立公平比较。

主机`{socket.gethostname()}`；共享SSD根`{B}`，Python`{B}/env/bin/python`。正式run`{RUN}`，当前检查/等待源码`{D}`；精确97启动和6m恢复见上一交接RL_CENSUS97_CAPACITY6M_ONLINE_20261031。中断须保全最新97 partial，不回退96；旧96已完成勿重启。MuJoCo物理状态未保存。进程按LAUNCH/PROCESS的PID与start_ticks重验，不依据旧进度重启。

## 保存

实际query/fetch/read main fd272610、baseline f6e8f8c2；无子agent。GPU保存窗口{gpu['samples']}样本最低{gpu['minimum']}%、低于50次数{gpu['below50']}、末{gpu['last']}。含synthetic guard，非科学吞吐或每瞬时保证；科学全部结束后仍guard，非重启自启服务。

小证据`{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256`{receipt['sha256']}`，逐成员字节/JSON/AST核验。大型checkpoint/replay/raw仍共享SSD，HDD仅既有254字节LATEST指针，不是HDD/arm1全备份。实际发布收据`{A}/PUBLICATION.json`。
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
