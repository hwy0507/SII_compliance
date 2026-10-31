from pathlib import Path
import json,hashlib,time,tarfile,ast,socket
D=Path(__file__).resolve().parent;B=D.parents[1];REPO=B/'repository/SII_compliance';V=B/'runs/parameter_census_cycle99_review_20261031_v1';F=B/'runs/census99_fixed98_terminal_20261031_v1';C=B/'runtime/census99_prefix_comparison_20261031_v1';N=B/'runs/census99_new_terminal_diagnosis_20261031_v1';P=B/'runtime/census99_window_completion_preparation_20261031_v1';W=B/'runs/parameter_census97_99_reward_stability_20261031_v1';O=B/'runtime/census99_remaining_watch_20261031_v1'
TAG='RL_CENSUS99_COMPLETE_WINDOW_20261031';A=B/'repository'/TAG;E=REPO/'docs/evidence'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
sci=read(D/'COMPLETE99_SCIENTIFIC_REVIEW.json');assert sci['passed'] and sci['complete99'];watch=read(O/'WATCH_REVIEW.json');assert watch['passed'] and watch['ready_for_full_scientific_review']
for p in [D/'COMPLETION_REVIEW.json',D/'IMPEDANCE_LONG0000_ABORT_REVIEW.json',D/'ABORT_RESIDUAL_LINK_REVIEW.json',W/'BINDING_REVIEW.json',W/'SAVED_ARITHMETIC_REVIEW.json',P/'WINDOW_BOOTSTRAP_SCALAR_REVIEW.json',P/'CAPACITY_ASSERTION_REPAIR_REVIEW.json']:assert read(p)['passed']
win=read(W/'REVIEW.json');assert win['passed'];assert read(W/'PLOT_INSPECTION.json')['actual_visual_inspection'];assert all(not x['descriptive_five_percent_check'] for x in win['methods'].values())
repair=read(P/'CAPACITY_ASSERTION_EXECUTION.json')
for p,h in repair['originals'].items():assert sha(p)==h
assert win['capacity_assertion_repair']['sha256']==sha(P/'CAPACITY_ASSERTION_EXECUTION.json')
assert not (B/'runs/parameter_census_cycle100_20261031_v1/LAUNCH.json').exists()
G=Path('/tmp/sii_gpu_util_guard_20261031_recovery_v1');guard=read(O/'PLAN.json')['guard']
for j in guard['identities']:
 st=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert st[0]!='Z' and st[19]==j.get('start',j.get('proc_start_ticks'))
assert not (G/'STOP').exists() and not (G/'FAILURE.json').exists();samples=[json.loads(x) for x in (G/'samples.jsonl').read_text().splitlines()];samples=[x for x in samples if x['time']>=read(O/'PLAN.json')['time']];assert time.time()-samples[-1]['time']<30
gpu=dict(samples=len(samples),seconds=samples[-1]['time']-samples[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in samples) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_guard_included=True)
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples));put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),gpu=gpu,goal='active',complete99_and_original97_99_reviewed=True,all_science99_finished=True,cycle100_launched=False,guard_kept_after_science=True))
files=set()
for root in [D,V,F,C,N,P,W,O]:
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.json','.jsonl','.png','.npz','.diff','.log'}:files.add(p)
for p in [B/'runtime/census99_continuation_20261031_v1/SOURCES.json',B/'runtime/direct34_dispatch_preparation_20261028_v1/DIRECT_STAGE_DECISION.json',B/'runs/serl_take33_frozen_combined_review_20261030_v3/REVIEW.json']:files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<20*1024**2,(p,len(data))
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Complete99 logs/metrics arrays/context/old8803+new90 terminals/all8893 reference/five actual plots; original97-99 nine inputs and scalar/bootstrap review, transparent stale4m assertion repair, new impedance physical abort evidence. Original sharedSSD checkpoints/raw remain dependencies.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as z:
 for p in sorted(E.rglob('*')):
  if p.is_file():z.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as z:
 assert len(z.getmembers())==len(manifest)+1
 for member in z.getmembers():assert z.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_members_verified=True,initial_main='bddee50322670bc9658e1a08326c0756b1614be9',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='SharedSSD evidence and existing254-byte HDD pointer; not fullHDD/arm1 backup.')
put(A/'RECEIPT.json',receipt);put(REPO/'docs'/(TAG+'_SAVE.json'),receipt)
table=['|方法|新增步|Task / Strict / 30|平均reward|原loss均值 / 最大|','|---|---:|---:|---:|---:|'];wtable=['|方法|97 / 98 / 99 reward均值|相邻相对变化|端点相对变化|原5%检查|','|---|---|---|---|---|']
for m,v in sci['methods'].items():
 t=v['training'];l=v['loss']['agent_train/original_sampled_q_loss'];table.append(f"|{m}|{t['new_transitions']}|{t['task']} / {t['strict']}|{t['reward_mean']:.9f}|{l['mean']:.6f} / {l['maximum']:.6f}|")
 x=win['methods'][m];means=' / '.join(f"{c['reward_mean']:.6f}" for c in x['cycles']);adj=' / '.join(f'{a*100:.4f}%' for a in x['adjacent_relative_mean_changes']);wtable.append(f"|{m}|{means}|{adj}|{x['endpoint_relative_mean_change']*100:.4f}%|失败|")
report=f'''# 第99轮完整审查及原97–99窗口完成 — 2026-10-31

**Goal active，未收敛。原第99轮三训练/归档/四诊断全部正常结束，不能重启这些已完成进程。原97–99窗口三路均未通过5%奖励稳定性检查；阻抗新物理中止与原loss尖峰明确保留。尚无100派发，下一阶段须依据本轮失败诊断独立登记和完整恢复预检。GPU guard继续。**

{chr(10).join(table)}

I为29完整55秒+1中止，A/V各30完整55秒。I `active_long_train_0000`在40.28s/1007动作触发`global_penetration_exceeded_2mm`，较完整回合少368动作；Task/Strict均失，仍留30分母。原记录全局穿透87.091390mm、最坏对凸边/目标物体，外部穿透仅.066886mm，不能混淆。与98同MJB；独立核805600原物理子步、dt5e-5/终止时刻及float32 torque峰值，接触深度本身未原样逐子步记录，未声称独立重建穿透。

完整99旧replay/history/violation精确保留，全部新52/action/reward/30模型按原检查核验；只读诊断前后learner/Adam/RNG不变，逐条奖励误差0。全新增context补充覆盖无尾部排除。原loss全部123382更新的原JSONL/保存数组/独立标量通过，五实际图已检查。I末1000原loss1.386599较首1.106786上升，最高22.261616；actor从约27.54降26.38，明显漂移。A原loss约1.029但旧终端拟合退化，V末段尖峰2.861036；有限值不是健康通过。

固定8803旧终端原mask SSE变化I−15.8621%、A+46.1728%、V−1.3001%；退化行1307/1959/1256均保留，五critic与未mask误差分列。新增90及全部8893终端参考逐条绑定、旧8803预测复现、全learner/Adam/replay/RNG不变。新99 masked SSE为8913.966721/6.094042/2.710804。

阻抗新long0000终端reward−36.681351，五critic仍预测约5.15至5.95，全mask为1，SSE8909.666519占全部新I误差99.9518%；原violation bit0保留。原loss最大点在其终端后30更新；无抽样索引，只有时序关联，不作样本因果解释。A尽管平均reward变化很小，Strict获得short0100/long0200、失short0600/long0500，Task获得long0200、失long0500。V Task/Strict集合不变。全部成功退化/失败保留。

## 原97–99窗口

{chr(10).join(wtable)}

恰九组真实checkpoint/父链/日志/原loss/两核心图绑定通过。原5%/nearzero1/5000bootstrap/seed2026102861与.025/.975区间保持，原始标量及同抽样下独立均值/线性分位数复算通过；bootstrap仅条件组成敏感性，非独立seed或冻结评测。不移窗口到98–100，原94–96失败保持。

发现原锁定audit仍有`current_replay_capacity == 4000000`旧断言，与已登记96→97扩到600万及实际九checkpoint不符。原audit/PLAN/SOURCE_LOCK逐字保留；独立`repair_window_capacity.py`执行时仅把该断言常量改为6000000，并额外检查所有九组原4m历史标记与6m标记。实际97/98六组复现旧断言拒绝、正确检查通过，24损坏容量/标记拒绝；AST证明统计逻辑无变化，执行源码hash/修复收据显式绑定最终报告。不是阈值或窗口放宽，详见`{P}/CAPACITY_ASSERTION_REPAIR_REVIEW.json`。

## 运行与恢复

完成监视{watch['elapsed_s']:.3f}s/{watch['samples']}样本，八原作业均已核成功终态；无重启。GPU保存{gpu['samples']}样本/{gpu['seconds']:.3f}s，min{gpu['minimum']}%、低于50{gpu['below50']}、末{gpu['last']}%。包含保活负载，不是科研吞吐或每瞬时保证；科学结束仍保留`{G}`，勿创建STOP，非开机自启服务。

直接动作分支保持原Direct33数值验收与冻结30 Task/Strict0/0，不追加34；原28最终memory缺口/恢复2已证、指定ESN缺失、最终共同集合Tref/SPT和公平冻结比较仍待。参数下一有限阶段还须按99失败及完整97–99结果决策、准确最新99全state恢复；不以阶段完成/有限loss代替联合收敛。

主机`{socket.gethostname()}`；共享SSD根`{B}`；解释器`{B}/env/bin/python`；三最终checkpoint位于`{B}/runs/parameter_census_cycle99_archive_20261031_v1/<method>/cycle_00099.pt`，hash见核心REVIEW。全部99审查`{D}/COMPLETE99_SCIENTIFIC_REVIEW.json`，原窗口`{W}`。

小证据包`{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256`{receipt['sha256']}`逐成员回读通过。依赖先前97/98/99启动归档和原共享SSD大checkpoint/replay/raw；HDD配额满，仅254-byte LATEST指针更新，非HDD/arm1全备份。开工mainbddee503/baselinef6e8f8c2实际query/fetch/read，发布见`{A}/PUBLICATION.json`。
'''
(REPO/'docs'/(TAG+'.md')).write_text(report)
entry=f'''## 2026-10-31 — 完整99与原97–99已审：三路稳定性失败，阻抗新中止与loss尖峰保留

- [交接](docs/{TAG}.md)。原99全部作业正常完成；I40882新步/29完整+1中止、A/V各41250/30完整，Task/Strict17/16、15/14、17/16。全部旧回放/新52/reward/context、123382 loss行/数组/算术与五实际图通过，原loss最大22.261616/1.626923/2.861036，非健康收敛。
- I long0000全局穿透中止40.28s、同MJB/805600物理子步与torque峰值复核；新terminal全5critic SSE8909.6665，占新I99.9518%，最大loss在后30更新，无抽样索引不作因果。旧8803 masked SSE−15.862%/+46.173%/−1.300%，全部8893参考/state不变，成功退化与所有失败保留。
- 原97–99九组绑定/原5%与5000bootstrap/独立标量区间审查完成，三路奖励稳定性均失败，不移98–100。旧audit误留4m断言已透明单常量6m修复，原source/PLAN/LOCK不改，实际六组与24负例通过、统计AST不变。
- Goal active，无100/Direct34派发；Direct33原验收/冻结0/0、历史缺口及指定ESN/最终比较待。八作业{watch['elapsed_s']:.3f}s观察全完成；GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅指针；mainbddee503/baselinef6e8f8c2已核。

'''
for name in ['AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
 p=REPO/name;old=p.read_text();add=entry.replace('(docs/','(') if name.startswith('docs/') else entry
 if name=='AGENTS.md':first,rest=old.split('\n',1);p.write_text(first+'\n\n'+add+rest.lstrip('\n'))
 else:p.write_text(add+old)
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');size=pointer.stat().st_size;data=(str(REPO/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert size==254 and len(data)<size
with pointer.open('r+b') as f:f.write(data+b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data);print(json.dumps(dict(receipt=receipt,gpu=gpu),indent=2))
