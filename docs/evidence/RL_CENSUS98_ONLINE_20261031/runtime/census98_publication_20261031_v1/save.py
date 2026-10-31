from pathlib import Path
import json,hashlib,time,socket,os,ast,tarfile
P=Path(__file__).resolve().parent;B=P.parents[1];D=B/'runtime/census98_continuation_20261031_v1';T=B/'runtime/census98_terminal_20261031_v1';R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle98_20261031_v1';F=B/'runs/census98_fixed97_terminal_20261031_v1';TAG='RL_CENSUS98_ONLINE_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
for p in [D/'PREFLIGHT_FINISHED.json',D/'CONTRACT_REVIEW.json',D/'CPU_CONSUMER_REVIEW.json',D/'SOURCE_REVIEW.json',D/'WINDOW97_99_PROTOCOL_REVIEW.json',D/'ONLINE_OBSERVATION_REVIEW.json',RUN/'startup/REVIEW.json',F/'PREFLIGHT_REVIEW.json',F/'PARTIAL_REJECTION_REVIEW.json']:assert rd(p)['passed']
for n,h in rd(D/'SOURCES.json')['files'].items():assert sha(D/n)==h
ob=rd(D/'ONLINE_OBSERVATION_REVIEW.json')
for j in ob['identities']:live(j)
live(rd(F/'PROCESS.json'))
assert not list(RUN.rglob('*FAILURE.json')) and not list(D.glob('*FAILURE.json')) and not list(F.glob('*FAILURE*.json'))
progress={m:rd(RUN/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
for m in progress:assert progress[m]['steps']>=ob['last_steps'][m]
cg=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');G=Path(cg['root']);assert not (G/'STOP').exists()
for j in cg['identities']:live(j)
rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(P/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(P/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress=progress,live_identities=ob['identities'],terminal_waiter=rd(F/'PROCESS.json'),formal98_running=True,complete98=False,automatic99=False,goal='active'))
files=set()
for folder in [D,T,P]:files.update(p for p in folder.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.md','.diff','.txt'})
files.update(RUN.glob('*.json'));files.add(RUN/'startup/REVIEW.json');files.update(F.glob('*.json'))
for m in progress:
 for n in ['REGISTRATION.json','CHECK_ONLY_REVIEW.json','INITIAL_STATE_REVIEW.json','CENSUS_EXECUTION.json','check/INITIAL_STATE_REVIEW.json','train/EXECUTION.json']:files.add(RUN/m/n)
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_CENSUS97_COMPLETE_20261031'/n)
for n in ['COMPLETE97_SCIENTIFIC_REVIEW.json','NEXT_FINITE_DECISION.json','FULL_CONTEXT_REVIEW.json','FULL_LOSS_SAVED_REVIEW.json']:files.add(B/'runtime/census97_completion_20261031_v1'/n)
for n in ['STATIC_SOURCE_REVIEW.json','ACTUAL_TRAINER_SOURCE_REVIEW.json','driver.py.diff']:files.add(B/'runtime/census98_preparation_20261031_v1'/n)
files.add(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');files.add(B/'runtime/census97_continuation_20261031_v1/STABILITY_WINDOW_INTENT.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Finite online98 exact full97 restore; unchanged inherited6m; 120 corruptions/6 native65536 restored updates/CPU/state/window/startup52 checks; original97-99 window and prior failures retained. Fixed8713 terminal comparison registered/waiting, not complete. Pre-registration health draft correction preserved. Large assets remain shared SSD; HDD pointer only.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for p in t.getmembers():assert t.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD small evidence; existing254-byte HDD pointer only, not full HDD/arm1 backup; live98 checkpoints/raw remain SSD');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
startup=rd(RUN/'startup/REVIEW.json');added={m:x['added_steps'] for m,x in startup['methods'].items()};growth={m:ob['last_steps'][m]-ob['first_steps'][m] for m in progress};steps={m:x['steps'] for m,x in progress.items()}
body=f'''# 第98轮精确接续与在线状态 — 2026-10-31

Goal active。完整97已审，现从其三份真实最终checkpoint接续一轮98，每方法≤41250新交互、30条件×55s；尚非完整98、健康稳定或联合收敛。无自动99/Direct34。

实际主机 `{socket.gethostname()}`；共享SSD根目录 `{B}`；Python `{B}/env/bin/python`。正式runtime `{D}`，在线目录 `{RUN}`。启动/完整归档/health/loss/有限observer分别登记，准确进程身份见LAUNCH与SAVE_SNAPSHOT，恢复时先核原进程和最新checkpoint，不重启或回退完整97。

## 接续依据与验证

完整97 I/A/V为4017762/4021250/4022250步，Task/Strict18/16、15/15、17/17，reward−4.200142/−6.807197/−2.870847；loss max1.776896/1.620523/1.227645。旧终端masked误差改善但成功与reward退化、I loss/actor漂移及A最后long0100高残差保留。97没有96级V尖峰，不证明历史异常解决。所有科学输入按hash锁定，来自前轮NEXT_FINITE_DECISION。

全97 learner/Adam/RNG/全部回放逐digest精确恢复，容量600万不变；第三容量阶段继续保留entry96/first97，早期23/47标记不变，不重新迁移。实际trainer只有预算异常文字97→98变化。120错误契约/父状态被拒；三GPU各2次真实65536批次更新重复全state/metrics精确，随后恢复，无测试权重导入。三CPU consumer inference后全state/RNG不变。

原预登记97–99协议逐字段检查通过，9个科学字段损坏例拒绝；没有改成98–100。原94–96 A/V稳定失败保留，待完整98和99后才执行原九组绑定与固定统计。原gamma .9995、dt5e-5、MJB、reward、Task/Strict、census与mask、优化器均保持。

静态适配曾误替换health脚本hash/percentile/sample数字，diff审查在登记/执行前发现，health已恢复与97逐字节相同；草稿与PRE_REGISTRATION_CORRECTION保留。没有科学作业使用该草稿。

实际startup新增 `{added}`，旧回放每字段精确、30MJB与30sampler/方法、优化器、current/next52、action和reward重建通过。next context检查包含快照每条尾行所对应的后继日志，不重复旧缺口。连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本观察{ob['identity_count']}原身份保持，steps增长 `{growth}`；保存时总steps `{steps}`。三正式与archive继续，完整98/loss实际图/新终端/全90比较仍待。

## 固定终端比较与后续

`{F}` 已绑定完整97全部8713终端(2905/2904/2904)的原52/action/reward/masks与五critic预测参考，原块边界保持。预检标量算术/输入hash及缺完整98拒绝通过，三份真实partial98也被完整检查拒绝。唯一waiter等待原archive完成后零更新诊断，沿原4h截止；结果与图尚未生成。保留所有旧abort/93失败及97三个最大新残差，禁止只报告改善行。

下一步核原98身份/进度和本轮原loss固定前缀；等待完整归档与8713终端诊断，实际看图、全90变化/新terminal及保存数组独立复核后再作有限99决定。Direct33原数值验收已过，冻结全30 Task/Strict0/0、旧28最终memory证明缺口与恢复2已证保留，不加Direct34；指定ESN与最终SPT/公平比较仍待，远端非RL ESN专题不替代。

## GPU与保存

独立guard `{G}` 保持运行，科研全部完成也不退出。保存窗口{gpu['samples']}样本/{gpu['elapsed_s']:.3f}s，min `{gpu['minimum']}`%、低于50计数 `{gpu['below50']}`、末值 `{gpu['last']}`%。这是含保活的占用，不是科学吞吐；只证明记录样本，不承诺任何瞬时或主机重启后自动恢复。

实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`。小证据归档 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐成员大小/hash/AST核验。Git提交与远端核验见 `{A}/PUBLICATION.json`。大型checkpoint/replay/raw仍在共享SSD；HDD配额满，仅既有254字节LATEST指针原地更新并回读，不是HDD/arm1完整备份。
'''
(R/'docs'/(TAG+'.md')).write_text(body)
entry=f'''## 2026-10-31 — 完整97精确接续，有限98在线；固定8713终端比较已登记

- [交接](docs/{TAG}.md)。真实全97 learner/Adam/RNG/所有回放精确恢复，600万容量及entry96/first97保持；实际trainer仅预算文字97→98。120负例/6原生65536隔离更新并恢复/三CPU消费者/原97–99协议通过，原94–96失败保持。
- 实际startup新增{added}，旧回放/新current-next52/action/reward/30MJB与sampler通过，next context全快照行明确核验。{ob['identity_count']}身份连续{ob['elapsed_s']:.3f}s，steps增长{growth}；三正式/archive继续，完整98与联合收敛未完成，无自动99/Direct34。
- 全8713完整97终端原五critic/mask比较登记，实际partial98拒绝，唯一消费者等待原archive；非独立泛化。静态health批量替换错误于登记前修正为97字节原件，草稿保留。Direct33原验收/冻结0/0、历史缺口与指定ESN/最终比较待保持，Goal active。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学完成仍guard；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针。开工main{remote['main'][:8]}/baseline{remote['baseline'][:8]}，发布见收据。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
paths=[str((E/x['relative']).relative_to(R)) for x in manifest]+[str((E/'MANIFEST.json').relative_to(R)),f'docs/{TAG}.md',f'docs/{TAG}_SAVE.json','AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']
put(A/'TASK_PATHS.json',dict(paths=paths))
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps=steps)))
