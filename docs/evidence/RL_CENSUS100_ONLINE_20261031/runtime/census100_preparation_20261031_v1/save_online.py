from pathlib import Path
import json,hashlib,time,tarfile,ast,socket,subprocess
P=Path(__file__).resolve().parent;B=P.parents[1];D=B/'runtime/census100_continuation_20261031_v1';R=B/'runs/parameter_census_cycle100_20261031_v1';W=B/'runs/parameter_census100_102_reward_stability_20261031_v1';T=B/'runtime/census100_terminal_20261031_v1';F=B/'runs/census100_fixed99_terminal_20261031_v1';REPO=B/'repository/SII_compliance';TAG='RL_CENSUS100_ONLINE_20261031';E=REPO/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'));return dict(pid=j['pid'],start=s[19])
for n in ['PREFLIGHT_FINISHED.json','CONTRACT_REVIEW.json','CPU_CONSUMER_REVIEW.json','WINDOW100_102_PROTOCOL_REVIEW.json','RESOURCE_REVIEW.json','LAUNCH_GATE_REVIEW.json','ONLINE_OBSERVATION_REVIEW.json']:assert read(D/n)['passed']
startup=read(R/'startup/REVIEW.json');obs=read(D/'ONLINE_OBSERVATION_REVIEW.json');assert startup['passed'];assert obs['elapsed_s']>=120
for j in obs['identities']:live(j)
for n in ['PREFLIGHT_REVIEW.json','PARTIAL_REJECTION_REVIEW.json']:assert read(F/n)['passed']
live(read(F/'PROCESS.json'))
for n,h in read(D/'SOURCES.json')['files'].items():assert sha(D/n)==h
for n,h in read(W/'SOURCE_LOCK.json')['files'].items():assert sha(W/n)==h
G=Path('/tmp/sii_gpu_util_guard_20261031_recovery_v1');guard=read(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json')
for j in guard['identities']:live(j)
assert not (G/'STOP').exists() and not (G/'FAILURE.json').exists()
samples=[json.loads(x) for x in (G/'samples.jsonl').read_text().splitlines()];samples=[x for x in samples if x['time']>=read(P/'SOURCE_ADAPTATION.json')['time']];assert time.time()-samples[-1]['time']<30
gpu=dict(samples=len(samples),seconds=samples[-1]['time']-samples[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in samples) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_guard_included=True)
(P/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples))
progress={m:read(R/m/'train/PROGRESS.json') for m in startup['methods']};put(P/'SAVE_SNAPSHOT.json',dict(time=time.time(),gpu=gpu,progress=progress,goal='active',guard_kept_after_science=True,online100=True,automatic101=False))
files=set()
for root in [P,D,T,F,W]:
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and (p.suffix in {'.py','.json','.diff'} or p.name in ['GUARD_SAMPLES.jsonl','ONLINE_OBSERVATIONS.jsonl'] or p.name.endswith('.before_fstring_fix')):files.add(p)
for p in R.rglob('*.json'):
 if 'train' not in p.relative_to(R).parts:files.add(p)
for m in startup['methods']:
 for n in ['PROGRESS.json','EXECUTION.json']:
  p=R/m/'train'/n;q=P/(m+'_'+n);q.write_bytes(p.read_bytes());files.add(q)
for p in [B/'runtime/census99_completion_20261031_v1/NEXT_FINITE_DECISION.json',B/'runtime/census99_completion_20261031_v1/COMPLETE99_SCIENTIFIC_REVIEW.json',B/'runs/parameter_census97_99_reward_stability_20261031_v1/REVIEW.json',B/'runtime/direct34_dispatch_preparation_20261028_v1/DIRECT_STAGE_DECISION.json']:files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<20*1024**2
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Finite100 exact99 full-state/native/CPU/negative/protocol/resource/actual startup and observation; prospective100-102 source; fixed8893 terminal consumer; first path-adaptation rejection preserved. Large checkpoints/raw stay original sharedSSD.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as z:
 for p in sorted(E.rglob('*')):
  if p.is_file():z.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as z:
 assert len(z.getmembers())==len(manifest)+1
 for m in z.getmembers():assert z.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_members_verified=True,initial_main='e2f637756ba7ce2736e4eff6e02843473ea34dd8',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='SharedSSD evidence, existing254-byte HDD pointer only; not fullHDD/arm1 backup.')
put(A/'RECEIPT.json',receipt);put(REPO/'docs'/(TAG+'_SAVE.json'),receipt)
added={m:x['added_steps'] for m,x in startup['methods'].items()};growth={m:obs['last_steps'][m]-obs['first_steps'][m] for m in added}
report=f'''# 第100轮准确接续上线 — 2026-10-31

Goal active，未收敛。第100轮从三份完整99 checkpoint精确接续，每路仅一轮、最多41250新增动作；三learner/90sampler/归档继续，固定8893终端只读消费者等待完整100。原97–99奖励稳定性三路失败、I新穿透中止及原loss尖峰22.261616、A旧终端误差退化、V尖峰与actor漂移保留；本轮继续学习这些已保留样本，不保证修复或收敛。

准确99全learner/Adam/RNG/完整旧replay恢复通过；120损坏契约拒绝，三路各两次native65536隔离更新逐值相同并恢复，共6次、零正式预检更新；三CPU消费者state/RNG恢复通过。600万容量及历史23/47、entry96/first97保持，健康分析源码与99字节相同，实际trainer仅预算错误文字99→100变化。原physics/MJB/reward/gate/LR/gamma.9995保持。

首轮准备因Python3.12 FSTRING_MIDDLE未适配仍指向98，被真实父checkpoint检查拒绝；未生成登记、未训练。失败和原草稿保留于`{P}/PREPARE_FIRST_FAILURE.json`，修正为实际99后登记及全部预检通过，不覆盖历史source。最终数值token/diff与hash检查见FINAL_SOURCE_STATIC_REVIEW。

启动快照新增{added}；全旧回放/新current-next52/action/reward、全部30MJB/30sampler及next context覆盖通过。共{obs['identity_count']}个进程身份连续{obs['elapsed_s']:.3f}s保持，steps增长{growth}。保存时progress为{ {m:x['steps'] for m,x in progress.items()} }；完整100结果、全loss健康和实际图仍待，启动通过不代表收敛。

启动早期非固定前缀抽查I/A/V为513/507/495条连续更新，原loss最大21.192064/1.484607/1.122497。阻抗尖峰仍存在，尚无采样索引可作因果归因；见EARLY_LIVE_HEALTH_SNAPSHOT.json，不作为完整或固定窗口健康验收。

新100–102非重叠观测意向在100启动前固定，原5%/nearzero1/5000bootstrap/seed2026102861/区间不变；原97–99失败不移为98–100。统计源码只改窗口标签与已证明的6m容量断言，旧4m历史marker保持。101/102必须各自决策、登记、恢复预检，没有自动训练；未来九组输入未齐，未生成最终窗口结果。原audit/PLAN/SOURCE_LOCK保持原样，容量修复出处保留。

固定8893完整99终端诊断已登记，原五critic/mask/块边界与fullstate不变要求保持；实际partial100拒绝和全部baseline保存算术通过。保留所有旧失败、98 V mask0例，新99 I long0000终端step4097929显式跟踪。消费者只等原100归档截止，不进行额外训练，尚无100诊断结果。

GPU保存{gpu['samples']}样本/{gpu['seconds']:.3f}s，最低{gpu['minimum']}%、低于50样本{gpu['below50']}、末值{gpu['last']}%。包含独立保活，不是科研吞吐或每瞬时保证。科学结束仍保留`{G}`，勿创建STOP；当前不是重启自启服务。

Direct33原数值验收与冻结30 Task/Strict0/0保持，不派发Direct34；原28最终memory缺口/恢复2已证及指定ESN、最终共同集合Tref/SPT公平比较仍待。

主机`{socket.gethostname()}`；共享SSD根`{B}`，解释器`{B}/env/bin/python`。运行目录`{R}`，训练/归档/启动PID与start ticks在LAUNCH及*_LAUNCH.json，源码`{D}`。父checkpoint为`{B}/runs/parameter_census_cycle99_archive_20261031_v1/<method>/cycle_00099.pt`；不得重启已完成99。后续先读真实progress/失败/完整边界再行动。

小证据`{archive}`，{receipt['members']}成员/{receipt['bytes']}bytes，SHA256`{receipt['sha256']}`，逐成员回读通过。大checkpoint/replay/raw仍原共享SSD，HDD配额满仅254-byte LATEST指针，非HDD/arm1全备份。开工main e2f63775 / baseline f6e8f8c2已实际query/fetch/read；正常发布收据见`{A}/PUBLICATION.json`。
'''
(REPO/'docs'/(TAG+'.md')).write_text(report)
entry=f'''## 2026-10-31 — 完整99准确恢复，有限100上线；新100–102意向固定

- [交接](docs/{TAG}.md)。三路精确99全state/replay/Adam/RNG恢复，120负例/6隔离native更新恢复/三CPU/资源/协议检查通过；实际trainer仅预算文字，health字节不变。初次fstring路径拒绝及修复证据保留。
- startup新增{added}、旧回放/新52/reward/context/30MJB/30sampler通过；{obs['identity_count']}身份连续{obs['elapsed_s']:.3f}s保持，steps增长{growth}。三正式/archive继续，固定8893原mask终端消费者等待；I99新中止明确跟踪。
- 原97–99三路失败不移窗口，新100–102在100启动前固定，原标准/历史失败保留；101/102仍须独立登记，无自动派发。完整100/联合收敛、指定ESN/最终比较待，Direct33原验收及冻结0/0/历史缺口保持，Goal active。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅指针。开工maine2f63775/baselinef6e8f8c2已query/fetch/read。

'''
for name in ['AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
 p=REPO/name;old=p.read_text();add=entry.replace('(docs/','(') if name.startswith('docs/') else entry
 if name=='AGENTS.md':first,rest=old.split('\n',1);p.write_text(first+'\n\n'+add+rest.lstrip('\n'))
 else:p.write_text(add+old)
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');size=pointer.stat().st_size;data=(str(REPO/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert size==254 and len(data)<size
with pointer.open('r+b') as f:f.write(data+b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data);print(json.dumps(dict(receipt=receipt,gpu=gpu,progress={m:x['steps'] for m,x in progress.items()}),indent=2))
