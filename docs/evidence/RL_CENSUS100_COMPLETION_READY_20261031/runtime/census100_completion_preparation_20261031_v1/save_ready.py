from pathlib import Path
import json,hashlib,time,socket,tarfile,ast
P=Path(__file__).resolve().parent;B=P.parents[1];C=B/'runtime/census100_completion_20261031_v1';T=B/'runtime/census100_new_terminal_diagnosis_20261031_v1';N=B/'runs/census100_new_terminal_diagnosis_20261031_v1';R=B/'runs/parameter_census_cycle100_20261031_v1';REPO=B/'repository/SII_compliance';TAG='RL_CENSUS100_COMPLETION_READY_20261031';E=REPO/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
for p in [P/'SOURCE_REVIEW.json',P/'OBSERVATION_REVIEW.json',C/'WAIT_PREFLIGHT.json',N/'REPORT_CONTRACT_REVIEW.json',N/'PREFLIGHT_REVIEW.json']:assert rd(p)['passed']
for path,h in rd(C/'WAIT_PLAN.json')['sources'].items():assert sha(path)==h
for name,h in rd(N/'WAIT_PLAN.json')['source_hashes'].items():assert sha(T/name)==h
assert rd(N/'REPORT_CONTRACT_REVIEW.json')['negative_count']==27
obs=rd(P/'OBSERVATION_REVIEW.json');plan=rd(P/'OBSERVATION_PLAN.json');assert obs['elapsed_s']>=120
for j in plan['identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
G=Path('/tmp/sii_gpu_util_guard_20261031_recovery_v1');assert not (G/'STOP').exists() and not (G/'FAILURE.json').exists();samples=[json.loads(x) for x in (G/'samples.jsonl').read_text().splitlines()];samples=[x for x in samples if x['time']>=rd(P/'SOURCE_REVIEW.json')['time']];assert time.time()-samples[-1]['time']<30
gpu=dict(samples=len(samples),seconds=samples[-1]['time']-samples[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in samples) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_guard_included=True)
(P/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples));steps={m:rd(R/m/'train/PROGRESS.json')['steps'] for m in ['impedance','admittance','vmc']};put(P/'SAVE_SNAPSHOT.json',dict(time=time.time(),gpu=gpu,steps=steps,goal='active',full100_pending=True,automatic101=False,guard_after_science=True))
files=set()
for root in [P,C,T,N]:
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.json','.jsonl','.diff','.log'}:files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<20*1024**2
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='New100 terminal/all8983 reference and complete-context/all-loss sources, true prior99 positives/27 negatives/missing100 rejections, finite registered read-only waiters and live observation. No complete100 output; existing large artifacts remain sharedSSD.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as z:
 for p in sorted(E.rglob('*')):
  if p.is_file():z.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as z:
 assert len(z.getmembers())==len(manifest)+1
 for x in z.getmembers():assert z.extractfile(x).read()==(E/x.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_members_verified=True,initial_main=plan['main'],baseline=plan['baseline'],backup_scope='SharedSSD small evidence, HDD existing254-byte pointer only; not fullHDD/arm1 backup.')
put(A/'RECEIPT.json',receipt);put(REPO/'docs'/(TAG+'_SAVE.json'),receipt)
growth={m:obs['last_steps'][m]-obs['first_steps'][m] for m in steps};deadline=rd(C/'WAIT_PLAN.json')['deadline'];assert deadline==rd(N/'WAIT_PLAN.json')['deadline_unix']
report=f'''# 第100轮完整审查等待已接上 — 2026-10-31

Goal active，未收敛。原第100轮三训练/90sampler/归档、固定8893旧终端和全90条件对照继续；本轮仅新增两只读等待器，不重启科学作业、不派发101。

新增终端诊断等待原core、固定8893旧终端、全90/终端计数三项完成后绑定真实100 checkpoint/全部30条件终端/episodes。使用原预测块边界、全部五critic和原mask，要求8893旧预测逐值一致，再构建8983全终端参考并分析90新终端。完整learner/Adam/replay/RNG不变、保存数组/独立标量审查、失败/中止保留。当前只有准备与预检通过，未执行100完整终端推理，未生成完整结果。

真实完整99三方法固定报告schema正例与27损坏报告拒绝通过，原fixed_report_contract逐字保持；已有8893参考保存统计逐值复算通过。缺完整100的ready门明确拒绝。历史97 binder错误/修复与所有失败记录仍绑定，未重写。

完整context/loss等待器只等原100 core完成后运行：全新增52维非终端衔接、每行current context/全部terminal复制规则；完整原optimizer JSONL→全部保存metrics数组→独立scalar均值/极值与原loss尖峰。原97 continuity helper保持，实际完整99父绑定通过；context/loss/consolidate三程序均实际拒绝缺完整100，未产生通过报告。最终合并仍需固定旧终端、新90、全90与五张实际图，不能以自动程序结束代替人工实际图检查。

两个等待器均沿原archive截止unix {deadline}，没有延长训练预算；新终端PID{rd(N/'LAUNCH.json')['pid']}、完整context/loss PID{rd(C/'PROCESS.json')['pid']}，均记录/proc启动ticks。注册source/hash锁和逐项token/diff检查完成；除了轮次标签和总终端数，数值常量不变。新100–102前瞻意向及原97–99三路失败被正确保留，未来101/102仍须分别科学决策和登记。

原103身份连续{obs['elapsed_s']:.3f}s/{obs['samples']}样本保持，steps增长{growth}；保存时累计步数{steps}。完整100及reward稳定/loss健康尚未完成。上一轮发现的I反复loss约19–21、99新中止拟合缓慢改善但92旧失败退化、V旧11样本退化均保持；本轮无新的收敛结论。Direct33原数值验收/冻结30 Task与Strict0/0、不追加34，原28memory缺口/恢复2与指定ESN/最终公平比较及共同Tref/SPT仍待。

GPU{gpu['samples']}样本/{gpu['seconds']:.3f}s，最低{gpu['minimum']}%、低于50{gpu['below50']}、末{gpu['last']}%；含独立保活，非科研吞吐或每瞬时保证。科学任务完成仍保留`{G}`，勿创建STOP，非重启自启。

主机`{socket.gethostname()}`；解释器`{B}/env/bin/python`；正式`{R}`；新终端源码`{T}`/登记与输出`{N}`；完整审查`{C}`；准备和观察`{P}`。后续先核原PID、进度/完成/失败标记，不能因一次观察超时重启作业。

小证据`{archive}`，{receipt['members']}成员/{receipt['bytes']}bytes，SHA256`{receipt['sha256']}`，逐成员回读通过。大checkpoint/replay/raw仍共享SSD，HDD配额满仅254-byte LATEST指针，非完整HDD/arm1备份。开工main3660db00/baselinef6e8f8c2已实际query/fetch/read，发布见`{A}/PUBLICATION.json`。
'''
(REPO/'docs'/(TAG+'.md')).write_text(report)
entry=f'''## 2026-10-31 — 第100轮新增终端与完整context/loss审查已登记等待

- [交接](docs/{TAG}.md)。真实99报告schema正例/27损坏拒绝、旧8893保存统计复算及缺完整100拒绝通过；新增只读任务等待原core/固定8893/全90后构建8983参考与90新terminal诊断，全state/原mask/块边界不变要求保持。
- 完整100全context/全loss保存审查与最终五图合并来源准备通过，原97helper不变、真实99父绑定；三脚本实际缺完整100拒绝。两新等待器沿原archive截止，不延长预算、不派发101。
- 原103身份连续{obs['elapsed_s']:.3f}s保持、steps增长{growth}；原训练/归档/四消费者继续。原97–99失败/新100–102意向、I尖峰与旧样本退化、Direct33结论及指定ESN待保持，Goal active，完整100/联合收敛仍待。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅指针。开工main3660db00/baselinef6e8f8c2已核。

'''
for name in ['AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
 p=REPO/name;old=p.read_text();add=entry.replace('(docs/','(') if name.startswith('docs/') else entry
 if name=='AGENTS.md':first,rest=old.split('\n',1);p.write_text(first+'\n\n'+add+rest.lstrip('\n'))
 else:p.write_text(add+old)
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');size=pointer.stat().st_size;data=(str(REPO/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert size==254 and len(data)<size
with pointer.open('r+b') as f:f.write(data+b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data);print(json.dumps(dict(receipt=receipt,gpu=gpu,steps=steps),indent=2))
