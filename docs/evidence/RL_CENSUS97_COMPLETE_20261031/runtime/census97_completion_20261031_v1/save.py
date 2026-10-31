"""Save actual complete97 evidence only after the scientific consolidation passes."""
from pathlib import Path
import json,time,hashlib,tarfile,ast,socket
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';V=B/'runs/parameter_census_cycle97_review_20261031_v1';T=B/'runs/census97_fixed96_terminal_20261031_v1';C=B/'runtime/census97_prefix_comparison_20261031_v1';N=B/'runs/census97_new_terminal_diagnosis_20261031_v1';ND=B/'runtime/census97_new_terminal_diagnosis_20261031_v1';RUN=B/'runs/parameter_census_cycle97_20261031_v1';TAG='RL_CENSUS97_COMPLETE_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
review=read(D/'COMPLETE97_SCIENTIFIC_REVIEW.json');assert review['passed'];obs=read(D/'COMPLETION_REVIEW.json');assert obs['passed'] and obs['all_complete'];assert read(N/'FINISHED.json')['passed']
plan=read(D/'COMPLETION_PLAN.json');guard=Path(plan['guard_root'])
for j in plan['guards']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
assert not (guard/'STOP').exists() and not (guard/'FAILURE.json').exists()
samples=[json.loads(x) for x in (guard/'samples.jsonl').read_text().splitlines()];samples=[x for x in samples if x['time']>=read(N/'WAIT_PLAN.json')['time']];assert samples and time.time()-samples[-1]['time']<20
gpu=dict(samples=len(samples),minimum=[min(x['gpus'][i]['utilization'] for x in samples) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_guard_included=True)
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples));put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,goal='active',full97_complete=True,guard_kept_after_science=True,no_automatic98=True))
files=set()
for root in [D,ND,N,V,T,B/'runtime/census98_preparation_20261031_v1']:
 for p in root.rglob('*'):
  if p.is_file() and p.suffix in ('.py','.json','.jsonl','.npz','.png','.diff') and '__pycache__' not in p.parts:files.add(p)
for n in ['INTERPRETATION.json','INTERPRETATION_SAVED_REVIEW.json','CHANGED_CASES_REVIEW.json','CACHE_POPULATION_FULL_REVIEW.json','COMPARISON_FINISHED.json','FULL97_PLOT_INSPECTION.json','training96_97_all90.png','WAIT_PLAN.json','PROCESS.json']:files.add(C/n)
for p in [RUN/'LAUNCH.json',RUN/'MONITOR_LAUNCH.json',B/'runtime/census97_continuation_20261031_v1/STABILITY_WINDOW_INTENT.json',B/'runs/parameter_census94_96_reward_stability_20261031_v1/REVIEW.json',B/'runs/parameter_census97_99_reward_stability_20261031_v1/PREPARATION_REVIEW.json',B/'runtime/direct34_dispatch_preparation_20261028_v1/DIRECT_STAGE_DECISION.json']:files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2,(p,len(data));rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Complete97 actual scalar/array/plot reviews; all90 condition comparison; all8623 old plus90 new terminal reference/diagnosis; full next-context gap closed. Raw training and checkpoints remainSSD. No convergence or final independent evaluation claim.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for item in t.getmembers():assert t.extractfile(item).read()==(E/item.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_members_verified=True,initial_main='9a8dcac7608b0b75bb3ca27d97effdaf53dc02fb',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='SharedSSD small evidence;254-byte existingHDD pointer only, large checkpoint/replay/raw remainSSD. Not fullHDD/arm1 backup.')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
table=['|方法|完整步数|Task / Strict|回合reward均值|原loss均值 / 最大|原loss末1000均值|','|---|---:|---:|---:|---:|---:|'];terminal=[]
for m,x in review['methods'].items():
 t=x['training'];l=x['loss']['agent_train/original_sampled_q_loss'];table.append(f"|{m}|{t['steps']}|{t['task']} / {t['strict']}|{t['reward_mean']:.9f}|{l['mean']:.6f} / {l['maximum']:.6f}|{l['last1000_mean']:.6f}|");terminal.append(f"- {m}: 旧终端masked SSE变化{x['fixed96_terminal_groups']['all']['relative_change']:.4%}，退化{x['fixed96_regression_rows']}行；新97终端masked SSE {x['new97_terminal_diagnosis']['total_new97_masked_sse']:.9f}；Task新增{x['task_gained']} / 丢失{x['task_lost']}，Strict新增{x['strict_gained']} / 丢失{x['strict_lost']}。")
report=f'''# 第97轮完整训练、终端诊断与原loss审查

**Goal active，尚未宣称参数RL收敛或最终公平评测完成。** 原97三路有限训练及归档/比较/新终端只读任务已完成；不重启已完成97，不回退96。未自动派发98；后继仍须根据实际结果单独登记并从完整97精确恢复。科学结束仍保留GPU guard。

## 完整97

{chr(10).join(table)}

完整旧回放和历史元数据保持、新reward按原journal逐条重建、实际600万容量与历史marker保留；完整原loss日志/全部NPZ/独立标量复算通过。所有已登记loss、health、全90比较、固定8623终端及新90终端图均实际查看；各PLOT_INSPECTION记录内容与SHA。数值健康判断仍以original_sampled_q_loss为准，不能用条件估计器loss替代。

本轮将上一轮识别的next context证据缺口补齐到全部新97数据：非终端全部52维next与同条件下一current精确，全部current context绑定原日志，30终端/方法的next context符合原终端复制规则；所有新行覆盖，不再有快照尾部未配对项。原线上代码/checkpoint未修改。

## 条件与终端

{chr(10).join(terminal)}

新增90个终端全部保留，包括失败；8713总终端CPU参考完整保存，旧8623完整97预测逐值复现既有消费者。全部5critic与原mask均保留，learner/Adam/replay/RNG/checkpoint不变。新终端残差、short0600跨96/97任务事件与奖励分项、最大原loss时序均记录；实际采样索引未保存，时序相邻不证明因果。线上每次更新的总终端人口与done累计精确、最终32分层计数已核；线上逐分层tensor内容未记录。

原94–96 A/V reward不稳定及V96 loss尖峰8.7554保留。前瞻97–99规则保持，仍缺完整98、99，不能用本轮完成代替稳定性。Direct33原训练数值验收保留，不因冻结Task/Strict0/0追加34；原28最终内存证明缺口/恢复2证明与指定ESN缺失保持，最终独立公平比较尚待。

## 恢复与保存

98仅静态候选已准备：`{B}/runtime/census98_preparation_20261031_v1`，继承原第三容量stage，trainer只改有限预算标签，replay恢复期望与完整97逐值相同。尚未实际恢复、验证native下一更新或启动98；必须先单独登记有限决定及完整恢复/消费者/启动审查。

主机`{socket.gethostname()}`，共享SSD根`{B}`，Python`{B}/env/bin/python`。最新父为`{B}/runs/parameter_census_cycle97_archive_20261031_v1/{{method}}/cycle_00097.pt`，完整SHA见`{V}/REVIEW.json`。完整科学审查`{D}/COMPLETE97_SCIENTIFIC_REVIEW.json`；新增终端`{N}`。旧96/原97/有限消费者已完成勿重跑。

原进程有限观察{obs['elapsed_seconds']:.3f}s/{obs['samples']}样本。新增终端binder将总报告passed误用于方法报告，推理前KeyError导致原observer结束；原源码/失败/日志保持。只读修复改为总passed加方法记录逐字一致、state/checkpoint/values哈希核验，随后完成原登记诊断；所有完成标记另行复核，未重跑训练。完整比较图收据与原前5000收据重名被拒绝，已另存FULL97收据，旧记录未覆盖。GPU{gpu['samples']}采样最低{gpu['minimum']}%、低于50次数{gpu['below50']}，末{gpu['last']}%；含合成guard非科学吞吐，不是每瞬时保证。guard`{guard}`继续，勿创建STOP，非重启自启服务。

远端main9a8dcac7/baselinef6e8f8c2已实际query/fetch/read。SSD小证据`{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256`{receipt['sha256']}`，逐成员字节/JSON/AST核验。大checkpoint/replay/raw仍SSD，HDD仅既有254-byte LATEST指针，非HDD/arm1全备份。实际发布核验见`{A}/PUBLICATION.json`。
'''
(R/'docs'/(TAG+'.md')).write_text(report)
counts={m:dict(task=x['training']['task'],strict=x['training']['strict'],reward=x['training']['reward_mean'],original_loss_max=x['loss']['agent_train/original_sampled_q_loss']['maximum']) for m,x in review['methods'].items()}
entry=f'''## 2026-10-31 — 完整97/全部终端与loss已审，next context全行证据补齐

- [交接](docs/{TAG}.md)。完整97旧回放/新奖励/600万容量、全部loss数组/标量及五张实际图通过；结果{counts}。原loss口径保持，不以阶段完成宣称收敛。
- 固定8623旧终端全5critic/原mask与新增90完整诊断通过，全部8713参考及learner/Adam/replay/RNG不变。全90条件成功退化和short0600时序保留；无采样索引，不作尖峰因果推断。每次线上总终端计数/最终32分层精确，线上逐分层tensor未记录。
- 新终端binder字段错误及原observer停止记录保留；推理前只读修复后完成原诊断，完整比较图另存收据保留旧前缀。
- next context缺口已补到每条新97：全52非终端连续、所有日志current context及30终端原复制规则精确，无尾部遗漏。原三训练/archive/消费者完成勿重启；无自动98，原94–96失败/前瞻97–99未完成/Direct33原验收与冻结0/0/指定ESN缺失保持，Goal active。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254-byte指针、非全备份。

'''
for name in ['AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
 p=R/name;old=p.read_text();add=entry.replace('(docs/','(') if name.startswith('docs/') else entry
 if name=='AGENTS.md':first,rest=old.split('\n',1);p.write_text(first+'\n\n'+add+rest.lstrip('\n'))
 else:p.write_text(add+old)
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();size=pointer.stat().st_size;assert len(data)<size
with pointer.open('r+b') as f:f.write(data+b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data)
print(json.dumps(dict(receipt=receipt,gpu=gpu,results=counts)))
